#!/usr/bin/env python3
"""skill-gym — sandbox-isolated token-savings benchmark for Claude Code add-ons.

Phases:
  python3 gym.py smoke                 # auth + activation checks (haiku, tiny)
  python3 gym.py run --phase pilot     # 3 conditions x 2 tasks x 1 trial (opus)
  python3 gym.py run --phase full      # 4 conditions x 7 tasks x 2 trials (opus)
  python3 gym.py run --conditions baseline,caveman --tasks C1 --trials 1

Isolation per run (see README):
  fresh sandbox workspace | --setting-sources "" | --no-session-persistence |
  pinned --tools | scrubbed env | session-scoped --plugin-dir | per-subprocess
  ANTHROPIC_BASE_URL for the headroom proxy.

Every run writes results/runs/<phase>/<task>/<condition>/t<N>/
  events.jsonl  (full stream-json event log = the measurement)
  meta.json     (cmd, timing, exit, attempts)
  gate.json     (task quality gate verdict)
Resumable: completed cells (gate.json present) are skipped.
"""
import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, ".venv")
CACHE = os.path.join(ROOT, ".cache")
RUNS = os.path.join(ROOT, "results", "runs")
CAVEMAN_FLAG = os.path.expanduser("~/.claude/.caveman-active")

CONDITIONS = {
    "baseline": {"args": [], "env": {}},
    "caveman": {"args": ["--plugin-dir", os.path.join(ROOT, "vendor", "caveman")], "env": {}},
    "headroom": {"args": [], "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"}, "proxy": True},
    "both": {
        "args": ["--plugin-dir", os.path.join(ROOT, "vendor", "caveman")],
        "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"},
        "proxy": True,
    },
}

BATTERY = {
    "C1": "swebench/pylint-dev__pylint-6903",
    "C2": "swebench/pytest-dev__pytest-7490",
    "C3": "swebench/sphinx-doc__sphinx-10323",
    "C4": "docwork/pylint-onboarding",
    "O1": "ssb/59055",
    "O2": "ssb/13894",
    "O3": "ssb/55392",
    # hard tier — SWE-bench Verified difficulty "1-4 hours" (H1-H3), ">4 hours" (H4)
    "H1": "swebench/pylint-dev__pylint-8898",
    "H2": "swebench/pytest-dev__pytest-10356",
    "H3": "swebench/sphinx-doc__sphinx-11510",
    "H4": "swebench/sphinx-doc__sphinx-7590",
}
PHASES = {
    "pilot": {"conditions": ["baseline", "caveman", "headroom"], "tasks": ["C1", "O1"],
              "trials": 1, "model": "opus"},
    "full": {"conditions": ["baseline", "caveman", "headroom", "both"],
             "tasks": ["C1", "C2", "C3", "C4", "O1", "O2", "O3"], "trials": 2, "model": "opus"},
    "hard": {"conditions": ["baseline", "caveman", "headroom", "both"],
             "tasks": ["H1", "H2", "H3", "H4"], "trials": 2, "model": "opus"},
}
TIMEOUTS = {"swebench": 2700, "ssb": 1500, "docwork": 1200, "smoke": 300}
MAX_TURNS = {"swebench": 80, "ssb": 40, "docwork": 25, "smoke": 3}
TOOLS = "Bash,Edit,Write,Read,Grep,Glob"
RATE_LIMIT_PAT = re.compile(r"rate.?limit|429|overloaded|usage limit", re.I)


def log(msg):
    print(f"[gym {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sh(cmd, **kw):
    kw.setdefault("check", True)
    return subprocess.run(cmd, **kw)


def scrubbed_env(extra=None):
    env = {
        k: v
        for k, v in os.environ.items()
        if not (k.startswith("ANTHROPIC") or k.startswith("CLAUDE") or k.startswith("HEADROOM"))
    }
    env["UV_CACHE_DIR"] = os.path.join(CACHE, "uv")
    env["HF_HOME"] = os.path.join(CACHE, "hf")
    # Apple's CLT Python caches bytecode in a SHARED system location
    # (~/Library/Caches/com.apple.python/...) keyed by (mtime-second, size).
    # A size-preserving edit within the same second as a prior compile
    # executes STALE bytecode — this false-failed caveman's correct C3 fixes
    # (its speed made same-second edits likely). Redirect the cache per
    # process tree so gates and agents always execute current source.
    env["PYTHONPYCACHEPREFIX"] = os.path.join(CACHE, "pycache")
    if extra:
        env.update(extra)
    return env


# ------------------------------------------------------------ proxy manager
class Proxy:
    def __init__(self):
        self.proc = None

    def ensure(self):
        if self.proc and self.proc.poll() is None:
            return
        logf = open(os.path.join(ROOT, "results", "headroom-proxy.log"), "ab")
        self.proc = subprocess.Popen(
            [os.path.join(VENV, "bin", "headroom"), "proxy", "--port", "8787"],
            stdout=logf, stderr=logf, env=scrubbed_env(), start_new_session=True,
        )
        for _ in range(60):
            try:
                socket.create_connection(("127.0.0.1", 8787), timeout=1).close()
                log("headroom proxy up on :8787")
                return
            except OSError:
                if self.proc.poll() is not None:
                    raise RuntimeError("headroom proxy died on startup; see results/headroom-proxy.log")
                time.sleep(0.5)
        raise RuntimeError("headroom proxy did not open :8787")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            self.proc.wait(timeout=15)
            log("headroom proxy stopped")


PROXY = Proxy()


# ------------------------------------------------------------ sandbox setup
def mirror_repo(repo):
    dest = os.path.join(CACHE, "repos", repo.replace("/", "__") + ".git")
    if not os.path.isdir(dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        log(f"mirroring {repo} (one-time)")
        sh(["git", "clone", "--quiet", "--bare", f"https://github.com/{repo}.git", dest])
    return dest


def setup_swebench(task_dir, ws):
    ws = os.path.abspath(ws)
    inst = json.load(open(os.path.join(task_dir, "instance.json")))
    mirror = mirror_repo(inst["repo"])
    sh(["git", "clone", "--quiet", mirror, ws])
    sh(["git", "-C", ws, "checkout", "--quiet", inst["base_commit"]])
    env = scrubbed_env()
    sh(["uv", "venv", "--quiet", "--seed", "--python", inst["python"], os.path.join(ws, ".venv")], env=env)
    py = os.path.join(ws, ".venv", "bin", "python")
    for cmd in inst["install"]:
        args = cmd.split()
        assert args[0] == "pip", f"unsupported install cmd {cmd}"
        sh(["uv", "pip", "install", "--quiet", "--python", py] + args[2:], cwd=ws, env=env)
    return inst


def setup_ssb(task_dir, ws):
    inst = json.load(open(os.path.join(task_dir, "instance.json")))
    os.makedirs(ws, exist_ok=True)
    for i in (1, 2, 3):
        src = [f for f in os.listdir(task_dir) if f.startswith(f"{i}_") and f.endswith("_input.xlsx")]
        assert src, f"missing input {i} in {task_dir}"
        shutil.copy2(os.path.join(task_dir, src[0]), os.path.join(ws, f"{i}_input.xlsx"))
    env = scrubbed_env()
    sh(["uv", "venv", "--quiet", "--seed", "--python", "3.13", os.path.join(ws, ".venv")], env=env)
    py = os.path.join(ws, ".venv", "bin", "python")
    sh(["uv", "pip", "install", "--quiet", "--python", py, "openpyxl"], env=env)
    return inst


def setup_docwork(task_dir, ws):
    inst = json.load(open(os.path.join(task_dir, "instance.json")))
    ref = json.load(open(os.path.join(ROOT, "tasks", "swebench", inst["from_instance"], "instance.json")))
    mirror = mirror_repo(inst["repo"])
    sh(["git", "clone", "--quiet", mirror, ws])
    sh(["git", "-C", ws, "checkout", "--quiet", ref["base_commit"]])
    return inst


def setup_smoke(task_dir, ws):
    os.makedirs(ws, exist_ok=True)
    return {}


SETUP = {"swebench": setup_swebench, "ssb": setup_ssb, "docwork": setup_docwork, "smoke": setup_smoke}


# ------------------------------------------------------------ gates
def gate_swebench(task_dir, ws, cell, inst):
    py = os.path.join(ws, ".venv", "bin", "python")
    changed = subprocess.run(
        ["git", "-C", ws, "diff", "--name-only", "HEAD"], capture_output=True, text=True
    ).stdout.split()
    patch_files = set(re.findall(r"^\+\+\+ b/(.+)$", inst.get("test_patch", "") or "", re.M))

    def is_test_path(p):
        parts = p.lower().split("/")
        return (any(d in ("tests", "testing", "test") for d in parts[:-1])
                or parts[-1].startswith("test_") or parts[-1].endswith("_test.py"))
    tests_touched = [p for p in changed if is_test_path(p) and p not in patch_files]
    # apply the held-out test patch (official SWE-bench protocol); the agent
    # never sees it — FAIL_TO_PASS tests are typically added by this patch.
    # Idempotent so gates can be re-run: skip if already applied.
    if inst.get("test_patch"):
        already = subprocess.run(["git", "-C", ws, "apply", "--reverse", "--check", "-"],
                                 input=inst["test_patch"], capture_output=True, text=True)
        if already.returncode != 0:
            pr = subprocess.run(["git", "-C", ws, "apply", "--whitespace=nowarn", "-"],
                                input=inst["test_patch"], capture_output=True, text=True)
            if pr.returncode != 0:
                return {"passed": False, "tests_modified": tests_touched,
                        "detail": f"test_patch failed to apply: {pr.stderr[-500:]}"}
    # fresh bytecode prefix per gate: guarantees tests execute current source,
    # immune to (mtime-second, size) pyc invalidation misses
    gate_env = scrubbed_env({"PYTHONPYCACHEPREFIX": os.path.join(cell, ".pycache-gate")})

    def run_tests(ids, timeout=900):
        if not ids:
            return True, ""
        r = subprocess.run([py, "-m", "pytest", "-q", "--no-header", *ids],
                           cwd=ws, capture_output=True, text=True, timeout=timeout,
                           env=gate_env)
        return r.returncode == 0, (r.stdout + r.stderr)[-4000:]
    try:
        f2p_ok, f2p_out = run_tests(inst["FAIL_TO_PASS"])
        p2p_ok, p2p_out = run_tests(inst["PASS_TO_PASS"][:20])
    except subprocess.TimeoutExpired:
        return {"passed": False, "detail": "pytest timeout"}
    passed = f2p_ok and p2p_ok and not tests_touched
    return {
        "passed": passed,
        "fail_to_pass_ok": f2p_ok,
        "pass_to_pass_ok": p2p_ok,
        "tests_modified": tests_touched,
        "detail": "" if passed else f"f2p:{f2p_ok} p2p:{p2p_ok} touched:{tests_touched}\n{f2p_out[-1500:]}",
    }


def gate_ssb(task_dir, ws, cell, inst):
    r = subprocess.run(
        [os.path.join(VENV, "bin", "python"), os.path.join(ROOT, "bin", "ssb_check.py"),
         task_dir, ws, inst["answer_position"]],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"passed": False, "detail": f"checker error: {r.stderr[-500:]}"}


def final_text(events_path):
    txt = []
    for line in open(events_path):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for b in ev["message"].get("content", []):
                if b.get("type") == "text":
                    txt.append(b["text"])
    return "\n".join(txt)


def gate_docwork(task_dir, ws, cell, inst):
    text = final_text(os.path.join(cell, "events.jsonl"))
    hits = [pat for pat in inst["rubric"] if re.search(pat, text, re.I)]
    passed = len(hits) >= inst["rubric_pass_min"]
    return {"passed": passed, "rubric_hits": len(hits), "rubric_total": len(inst["rubric"]),
            "detail": f"{len(hits)}/{len(inst['rubric'])} rubric hits"}


def gate_smoke(task_dir, ws, cell, inst):
    return {"passed": True, "detail": "smoke"}


GATE = {"swebench": gate_swebench, "ssb": gate_ssb, "docwork": gate_docwork, "smoke": gate_smoke}


# ------------------------------------------------------------ claude runner
def run_claude(cell, ws, prompt, condition, model, kind, attempt,
               max_turns=None, timeout=None):
    max_turns = max_turns or MAX_TURNS[kind]
    timeout = timeout or TIMEOUTS[kind]
    cond = CONDITIONS[condition]
    cmd = [
        "claude", "-p", "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "", "--no-session-persistence",
        "--tools", TOOLS,
        "--dangerously-skip-permissions",
        "--max-turns", str(max_turns),
        *cond["args"],
    ]
    env = scrubbed_env(cond["env"])
    meta = {
        "condition": condition, "model": model, "cmd": cmd, "attempt": attempt,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    events = os.path.join(cell, "events.jsonl")
    stderr_p = os.path.join(cell, "stderr.log")
    t0 = time.time()
    with open(events, "wb") as out, open(stderr_p, "wb") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                cwd=ws, env=env, start_new_session=True)
        try:
            proc.communicate(prompt.encode(), timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()
            meta["timeout"] = True
    meta["exit_code"] = proc.returncode
    meta["wall_s"] = round(time.time() - t0, 1)
    meta["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if condition in ("caveman", "both") and os.path.exists(CAVEMAN_FLAG):
        os.remove(CAVEMAN_FLAG)
        meta["caveman_flag_cleaned"] = True
    return meta


def has_result_event(events_path):
    if not os.path.exists(events_path):
        return False
    ok = False
    with open(events_path) as f:
        for line in f:
            if '"type":"result"' in line or '"type": "result"' in line:
                ok = True
    return ok


def looks_rate_limited(cell):
    for name in ("stderr.log", "events.jsonl"):
        p = os.path.join(cell, name)
        if os.path.exists(p):
            tail = open(p, "rb").read()[-8000:].decode("utf-8", "replace")
            if RATE_LIMIT_PAT.search(tail):
                return True
    return False


def run_cell(phase, alias, task_rel, condition, trial, model):
    kind, _, _ = task_rel.partition("/")
    task_dir = os.path.join(ROOT, "tasks", task_rel) if kind != "smoke" else ""
    cell = os.path.join(RUNS, phase, alias, condition, f"t{trial}")
    gate_path = os.path.join(cell, "gate.json")
    if os.path.exists(gate_path):
        log(f"skip {alias}/{condition}/t{trial} (done)")
        return
    ws = os.path.join(cell, "workspace")
    events = os.path.join(cell, "events.jsonl")

    if CONDITIONS[condition].get("proxy"):
        PROXY.ensure()

    inst = None
    if not has_result_event(events):
        if os.path.isdir(cell):
            shutil.rmtree(cell)
        os.makedirs(cell, exist_ok=True)
        log(f"setup {alias}/{condition}/t{trial}")
        inst = SETUP[kind](task_dir, ws)
        if kind == "smoke":
            prompt = "Reply with exactly one word: ok"
        else:
            prompt = open(os.path.join(task_dir, "prompt.md")).read()
        with open(os.path.join(cell, "prompt.md"), "w") as f:
            f.write(prompt)
        for attempt in range(1, 7):
            log(f"run  {alias}/{condition}/t{trial} attempt {attempt} (model={model})")
            meta = run_claude(cell, ws, prompt, condition, model, kind, attempt,
                              max_turns=(inst or {}).get("max_turns"),
                              timeout=(inst or {}).get("timeout"))
            with open(os.path.join(cell, "meta.json"), "w") as f:
                json.dump(meta, f, indent=1)
            if has_result_event(events):
                break
            if looks_rate_limited(cell):
                wait = min(900 * attempt, 3600)  # survive usage-window resets
                log(f"rate-limited; backing off {wait}s")
                time.sleep(wait)
                continue
            log(f"no result event (exit={meta['exit_code']}); see {cell}/stderr.log")
            break

    if not has_result_event(events):
        with open(gate_path + ".error", "w") as f:
            f.write("claude run produced no result event")
        log(f"ERROR {alias}/{condition}/t{trial}: no result event; cell marked errored")
        return

    if inst is None:
        inst = json.load(open(os.path.join(task_dir, "instance.json"))) if kind != "smoke" else {}
    log(f"gate {alias}/{condition}/t{trial}")
    verdict = GATE[kind](task_dir, ws, cell, inst)
    with open(gate_path, "w") as f:
        json.dump(verdict, f, indent=1)
    log(f"gate {alias}/{condition}/t{trial}: {'PASS' if verdict.get('passed') else 'FAIL'}")


# ------------------------------------------------------------ phases
def cmd_run(args):
    phase = args.phase or "custom"
    spec = PHASES.get(args.phase, {})
    conditions = (args.conditions.split(",") if args.conditions else spec.get("conditions", ["baseline"]))
    tasks = (args.tasks.split(",") if args.tasks else spec.get("tasks", ["C1"]))
    trials = args.trials or spec.get("trials", 1)
    model = args.model or spec.get("model", "opus")
    cells = []
    for t in range(1, trials + 1):
        for alias in tasks:
            for cond in conditions:  # interleaved: condition round-robin within task
                cells.append((alias, cond, t))
    log(f"phase={phase} model={model} cells={len(cells)}")
    try:
        for alias, cond, t in cells:
            run_cell(phase, alias, BATTERY[alias], cond, t, model)
    finally:
        PROXY.stop()
    log("run complete. Next: python3 gym.py analyze  (via analyze.py)")


def cmd_smoke(args):
    model = args.model or "haiku"
    try:
        for cond in ["baseline", "caveman", "headroom"]:
            run_cell("smoke", f"smoke-{cond}", "smoke/x", cond, 1, model)
            cell = os.path.join(RUNS, "smoke", f"smoke-{cond}", cond, "t1")
            ok = has_result_event(os.path.join(cell, "events.jsonl"))
            note = ""
            if cond == "caveman":
                meta = json.load(open(os.path.join(cell, "meta.json")))
                note = " hook-fired=" + str(bool(meta.get("caveman_flag_cleaned")))
            log(f"SMOKE {cond}: {'OK' if ok else 'FAILED'}{note}")
    finally:
        PROXY.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--phase", choices=list(PHASES))
    p_run.add_argument("--conditions")
    p_run.add_argument("--tasks")
    p_run.add_argument("--trials", type=int)
    p_run.add_argument("--model")
    p_run.set_defaults(fn=cmd_run)
    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--model")
    p_smoke.set_defaults(fn=cmd_smoke)
    args = ap.parse_args()
    os.makedirs(RUNS, exist_ok=True)
    args.fn(args)
