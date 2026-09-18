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
import concurrent.futures
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, ".venv")
CACHE = os.path.join(ROOT, ".cache")
RUNS = os.path.join(ROOT, "results", "runs")
CAVEMAN_FLAG = os.path.expanduser("~/.claude/.caveman-active")

CONDITIONS = {
    "baseline": {"args": [], "env": {}},
    "caveman": {"args": ["--plugin-dir", os.path.join(ROOT, "vendor", "caveman")], "env": {}},   # v1 path; v2 repoints below
    "headroom": {"args": [], "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"}, "proxy": True},
    "both": {
        "args": ["--plugin-dir", os.path.join(ROOT, "vendor", "caveman")],
        "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"},
        "proxy": True,
    },
}

# ---- v2 tool arms (each injected per run; nothing is installed globally) ----
# ponytail: plugin whose SessionStart hook injects the ruleset — without the hook
# it never self-activates (JetBrains measured 0 of 10). Its hook writes two flags
# under ~/.claude; HOST_FLAGS lists them so the runner removes them afterwards.
# The "nudged" flag is pre-created: on a machine with no statusline configured the
# hook otherwise appends a one-time "offer to set up the statusline" instruction,
# which a real user sees once but a flag-cleaning benchmark would see every run.
PLUG_ROOT = os.path.expanduser("~/Library/Caches/pyplug")    # neutral name on purpose


def neutral_tools():
    """Copy the tools under test out of the harness tree. Their paths reach the agent
    (plugin roots, the rtk hook command, PATH); a path into this tree is a signpost to
    tasks/*/instance.json, which holds the held-out tests."""
    for name in ("caveman", "ponytail"):
        dst = os.path.join(PLUG_ROOT, name)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(os.path.join(ROOT, "vendor", name), dst, symlinks=True)
    os.makedirs(os.path.join(PLUG_ROOT, "bin"), exist_ok=True)
    src = os.path.join(CACHE, "bin", "rtk")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(PLUG_ROOT, "bin", "rtk"))


CONDITIONS["ponytail"] = {
    "args": ["--plugin-dir", os.path.join(PLUG_ROOT, "ponytail")],
    "env": {"PONYTAIL_DEFAULT_MODE": "full"},
}
# rtk: what `rtk init -g` installs, minus the global install — the PreToolUse hook
# that rewrites Bash commands to `rtk <cmd>`, and the RTK.md awareness text.
RTK_BIN_DIR = os.path.join(PLUG_ROOT, "bin")
_RTK_MD = os.path.join(ROOT, "vendor", "rtk", "RTK.md")
CONDITIONS["rtk"] = {
    "args": ["--settings", json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": os.path.join(RTK_BIN_DIR, "rtk") + " hook claude"}]}]}}),
             "--append-system-prompt", open(_RTK_MD).read() if os.path.exists(_RTK_MD) else ""],
    "env": {}, "path_prepend": [RTK_BIN_DIR],
}
CONDITIONS["caveman-v1"] = CONDITIONS["caveman"]
CONDITIONS["caveman"] = {"args": ["--plugin-dir", os.path.join(PLUG_ROOT, "caveman")], "env": {}}
HOST_FLAGS = {   # plugin family -> files its hooks leave under ~/.claude
    "caveman": [CAVEMAN_FLAG],
    "ponytail": [os.path.expanduser("~/.claude/.ponytail-active"),
                 os.path.expanduser("~/.claude/.ponytail-statusline-nudged")],
}
PRE_FLAGS = {"ponytail": [os.path.expanduser("~/.claude/.ponytail-statusline-nudged")]}
FAMILY = {"caveman": "caveman", "both": "caveman", "ponytail": "ponytail"}

# The effort arms are the native yardstick:
# what turning Claude Code's own dial buys, with no add-on at all.
CONDITIONS["effort-high"] = {"args": [], "env": {}, "effort": "high"}
CONDITIONS["effort-low"] = {"args": [], "env": {}, "effort": "low"}

# v2 model pin — the `opus` alias moves between CLI releases; v1 resolved it to
# claude-opus-4-8. Every v2 phase names the full ID. Baseline and every tool arm
# run at xhigh effort: the most token-hungry setting is where a token saver has
# the most to cut, and the most to break.
V2_MODEL = "claude-opus-5"
V2_EFFORT = "xhigh"

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
V2_POOL = [
    "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277",
    "pylint-dev__pylint-6386", "pylint-dev__pylint-8898",
    "pytest-dev__pytest-5787", "pytest-dev__pytest-10356", "pytest-dev__pytest-7205",
    "sphinx-doc__sphinx-8548", "sphinx-doc__sphinx-8056", "sphinx-doc__sphinx-8595",
    "sphinx-doc__sphinx-9711", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10673",
    "psf__requests-5414", "psf__requests-6028", "psf__requests-2931",
    "pydata__xarray-6938", "pydata__xarray-4687",
]
V2B_POOL = [   # reserve: solved by <=1 of 10 public submissions (see fetch_tasks.V2B_IDS)
    "pylint-dev__pylint-4551", "pylint-dev__pylint-4604", "pylint-dev__pylint-4661",
    "pylint-dev__pylint-7080", "pytest-dev__pytest-5840",
    "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-11510", "sphinx-doc__sphinx-7590",
    "sphinx-doc__sphinx-7748", "sphinx-doc__sphinx-9229", "sphinx-doc__sphinx-7462",
    "sphinx-doc__sphinx-7985", "sphinx-doc__sphinx-9461", "sphinx-doc__sphinx-9602",
    "pydata__xarray-6599", "pydata__xarray-6992", "pydata__xarray-7229",
]
for _iid in V2_POOL + V2B_POOL:   # alias = short id, e.g. "pylint-4970"
    BATTERY[_iid.split("__")[1]] = "swebench/" + _iid

PHASES = {
    "pilot": {"conditions": ["baseline", "caveman", "headroom"], "tasks": ["C1", "O1"],
              "trials": 1, "model": "opus"},
    "full": {"conditions": ["baseline", "caveman", "headroom", "both"],
             "tasks": ["C1", "C2", "C3", "C4", "O1", "O2", "O3"], "trials": 2, "model": "opus"},
    "hard": {"conditions": ["baseline", "caveman", "headroom", "both"],
             "tasks": ["H1", "H2", "H3", "H4"], "trials": 2, "model": "opus"},
    # v2: `calib` = baseline only over the whole pool; its runs ARE the baseline
    # arm of `v2` (same cells, same protocol), so nothing is run twice.
    "calib": {"conditions": ["baseline"], "tasks": [i.split("__")[1] for i in V2_POOL],
              "trials": 3, "model": V2_MODEL, "effort": V2_EFFORT, "runs_as": "v2"},
}
# Reserve pool, screened with 2 trials: 1/2 is in the band for certain, whatever a third says.
_B_DROPPED = {"pylint-4661", "sphinx-10614", "sphinx-11510"}   # gold patch does not go green natively
PHASES["calib-b"] = {"conditions": ["baseline"],
                     "tasks": [i.split("__")[1] for i in V2B_POOL if i.split("__")[1] not in _B_DROPPED],
                     "trials": 2, "model": V2_MODEL, "effort": V2_EFFORT, "runs_as": "v2"}
# Main pool after round 1 (18/19 passed): second trials only where a first run failed or
# took the most turns (top 9) — the rest are at the ceiling for this model.
PHASES["calib-a2"] = {"conditions": ["baseline"], "trials": 2, "model": V2_MODEL,
                      "effort": V2_EFFORT, "runs_as": "v2",
                      "tasks": ["pytest-10356", "pylint-6386", "sphinx-8548", "sphinx-10673", "pylint-4970",
                                "pylint-6528", "pylint-8898", "sphinx-10435", "xarray-6938", "sphinx-8056"]}
# Treatment arms run only on the task list frozen by `analyze_v2.py calib`.
_FROZEN = os.path.join(ROOT, "tasks", "v2_frozen.json")
if os.path.exists(_FROZEN):
    _v2 = {"tasks": json.load(open(_FROZEN))["tasks"], "trials": 3, "model": V2_MODEL,
           "effort": V2_EFFORT, "runs_as": "v2"}
    # baseline is listed so its third trial runs interleaved with the arms (t1/t2 are done)
    PHASES["v2"] = {**_v2, "conditions": ["baseline", "caveman", "ponytail", "rtk", "headroom", "effort-low"]}
    PHASES["v2-high"] = {**_v2, "conditions": ["effort-high"]}   # last: cuttable without side effects
TIMEOUTS = {"swebench": 2700, "ssb": 1500, "docwork": 1200, "smoke": 300}
MAX_TURNS = {"swebench": 80, "ssb": 40, "docwork": 25, "smoke": 3}
TOOLS = "Bash,Edit,Write,Read,Grep,Glob"
# v2 "offline" tasks: the agent's shell cannot reach the internet. Found the hard way —
# the first v2 calibration run `pip download`ed the already-fixed upstream release and
# diffed it against the checkout. Proxy variables point every well-behaved client
# (pip, curl, wget, git, requests, urllib) at a dead port; NO_PROXY keeps the CLI's own
# API traffic (and the local headroom proxy) working. A determined agent could unset
# them — audit_run() flags that, and any other lookup, after the fact.
_DEAD = "http://127.0.0.1:9"
_NO_PROXY = "127.0.0.1,localhost,::1,.anthropic.com,anthropic.com,.claude.ai,claude.ai,.claude.com,claude.com"
OFFLINE_ENV = {**{k: _DEAD for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                                     "http_proxy", "https_proxy", "all_proxy")},
               "NO_PROXY": _NO_PROXY, "no_proxy": _NO_PROXY,
               "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
               "UV_OFFLINE": "1", "GIT_TERMINAL_PROMPT": "0"}
# v2 workspaces live OUTSIDE the harness tree, under an opaque id: the tree holds the
# held-out tests (tasks/*/instance.json), and v1's path even spelled out the condition.
WS_ROOT = os.path.expanduser("~/Library/Caches/pyws")   # neutral name on purpose
KEEP_WS = bool(os.environ.get("GYM_KEEP_WS"))   # default: purge swebench workspaces after the gate
_LOCK = threading.Lock()
_ACTIVE = {}    # plugin family -> live run count
RATE_LIMIT_PAT = re.compile(r"rate.?limit|429|overloaded|usage limit|limit reached|hit your limit|"
                            r"limit will reset|out of extra usage", re.I)


MIN_FREE_GB = 2.0      # never start a run below this; the host disk is nearly full
ABORT_FREE_GB = 1.0


def force_rmtree(path):
    """rmtree that survives read-only trees (pytest's permission tests leave chmod-0
    directories behind; a silent failure here would leak disk run after run)."""
    if os.path.isdir(path):
        subprocess.run(["chmod", "-R", "u+rwX", path], capture_output=True)
        shutil.rmtree(path, ignore_errors=True)
        if os.path.isdir(path):
            log(f"WARNING could not fully remove {path}")


def wait_for_disk():
    waited = 0
    while True:
        free = shutil.disk_usage(ROOT).free / 1e9
        if free >= MIN_FREE_GB:
            return
        if free < ABORT_FREE_GB:
            raise RuntimeError(f"disk critically low ({free:.2f} GB free); refusing to run")
        if waited % 600 == 0:
            log(f"DISK LOW: {free:.2f} GB free < {MIN_FREE_GB} GB; pausing before next run")
        time.sleep(60)
        waited += 60


def log(msg):
    print(f"[gym {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sh(cmd, **kw):
    kw.setdefault("check", True)
    return subprocess.run(cmd, **kw)


def scrubbed_env(extra=None):
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("ANTHROPIC", "CLAUDE", "HEADROOM", "PONYTAIL", "RTK", "VIRTUAL_ENV"))
    }
    env["UV_CACHE_DIR"] = os.path.join(CACHE, "uv")
    # uv-managed CPython only. Left to itself uv picks Xcode's 3.9, an app bundle
    # (Python.app): pytest's suite aborts subprocesses on purpose (faulthandler tests),
    # and every abort of an app bundle raises a "Python quit unexpectedly" dialog on
    # the user's screen — 29 of them before this line existed.
    env["UV_PYTHON_PREFERENCE"] = "only-managed"
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
        with _LOCK:
            self._ensure()

    def _ensure(self):
        if self.proc and self.proc.poll() is None:
            return
        # v1's log is published evidence; v2 appends to its own file
        logf = open(os.path.join(ROOT, "results", "headroom-proxy-v2.log"), "ab")
        self.proc = subprocess.Popen(
            # telemetry is opt-in and HEADROOM_* is scrubbed; the flag makes it explicit
            [os.path.join(VENV, "bin", "headroom"), "proxy", "--port", "8787", "--no-telemetry"],
            stdout=logf, stderr=logf, env=scrubbed_env(), start_new_session=True,
        )
        for _ in range(60):
            try:
                socket.create_connection(("127.0.0.1", 8787), timeout=1).close()
                log("headroom proxy up on :8787")
                return
            except OSError:
                if self.proc.poll() is not None:
                    raise RuntimeError("headroom proxy died on startup; see results/headroom-proxy-v2.log")
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
    # Fetch ONLY the base commit's ancestry into a fresh repo. A plain clone carries
    # every branch and tag, so `git log --all` would hand the agent the real fix
    # (the known SWE-bench future-commit leak). After this: no refs, no newer objects.
    sh(["git", "init", "--quiet", ws])
    # ...plus the tags that are already ancestors of base, so `git describe` and
    # setuptools_scm (pytest, xarray) still see a real version. 224 tags -> the 143
    # that predate the task, for pytest-10356.
    tags = subprocess.run(["git", "--git-dir", mirror, "tag", "--merged", inst["base_commit"]],
                          capture_output=True, text=True, check=True).stdout.split()
    sh(["git", "-C", ws, "fetch", "--quiet", "--no-tags", mirror, inst["base_commit"],
        *[f"refs/tags/{t}:refs/tags/{t}" for t in tags]])
    sh(["git", "-C", ws, "checkout", "--quiet", "--detach", inst["base_commit"]])
    env = scrubbed_env()
    sh(["uv", "venv", "--quiet", "--seed", "--python", inst["python"], os.path.join(ws, ".venv")], env=env)
    py = os.path.join(ws, ".venv", "bin", "python")
    frozen = ["--exclude-newer", inst["exclude_newer"]] if inst.get("exclude_newer") else []
    for cmd in inst["install"]:
        args = cmd.split()
        assert args[0] == "pip", f"unsupported install cmd {cmd}"
        sh(["uv", "pip", "install", "--quiet", "--python", py] + frozen + args[2:], cwd=ws, env=env)
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
def is_test_path(p):
    parts = p.lower().split("/")
    return (any(d in ("tests", "testing", "test") for d in parts[:-1])
            or parts[-1].startswith("test_") or parts[-1].endswith("_test.py"))


def run_graded(py, ws, ids, env, timeout=1800):
    """Run the test FILES that hold `ids` (official SWE-bench style) and return
    the set of node ids reported PASSED. Grading by file + `-rA` avoids shell
    quoting of parametrized ids. The official log parser keeps only the first
    whitespace token of an id, so both spellings are recorded."""
    files = sorted({i.split("::")[0] for i in ids})
    if not files:
        return set(), ""
    r = subprocess.run([py, "-m", "pytest", "-rA", "--tb=no", "-p", "no:cacheprovider", *files],
                       cwd=ws, capture_output=True, text=True, timeout=timeout, env=env)
    passed = set()
    for line in r.stdout.splitlines():
        if line.startswith("PASSED "):
            rest = line[7:].strip()
            passed.add(rest)
            passed.add(rest.split()[0] if rest.split() else rest)
    return passed, (r.stdout + r.stderr)[-3000:]


def gate_swebench(task_dir, ws, cell, inst):
    py = os.path.join(ws, ".venv", "bin", "python")
    changed = subprocess.run(
        ["git", "-C", ws, "diff", "--name-only", "HEAD"], capture_output=True, text=True
    ).stdout.split()
    patch_files = sorted(set(re.findall(r"^\+\+\+ b/(.+)$", inst.get("test_patch", "") or "", re.M)))
    tests_touched = [p for p in changed if is_test_path(p) and p not in patch_files]

    # the agent's patch is the evidence: keep it, the workspace is disposable
    diff = subprocess.run(["git", "-C", ws, "diff", "HEAD"], capture_output=True, text=True).stdout
    with open(os.path.join(cell, "patch.diff"), "w") as f:
        f.write(diff)
    untracked = subprocess.run(["git", "-C", ws, "ls-files", "--others", "--exclude-standard"],
                               capture_output=True, text=True).stdout.split()
    stat = {"files_changed": len(changed),
            "lines_added": sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")),
            "lines_removed": sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")),
            "untracked": [u for u in untracked if not u.startswith(".venv")][:20]}

    # official protocol: held-out test files are reset to base, then the test
    # patch is applied (the agent never sees it). Idempotent for re-gating.
    if inst.get("test_patch"):
        already = subprocess.run(["git", "-C", ws, "apply", "--reverse", "--check", "-"],
                                 input=inst["test_patch"], capture_output=True, text=True)
        if already.returncode != 0:
            tracked = [p for p in patch_files if subprocess.run(
                ["git", "-C", ws, "cat-file", "-e", f"HEAD:{p}"], capture_output=True).returncode == 0]
            if tracked:
                subprocess.run(["git", "-C", ws, "checkout", "HEAD", "--", *tracked], capture_output=True)
            pr = subprocess.run(["git", "-C", ws, "apply", "--whitespace=nowarn", "-"],
                                input=inst["test_patch"], capture_output=True, text=True)
            if pr.returncode != 0:
                return {"passed": False, "tests_modified": tests_touched, **stat,
                        "detail": f"test_patch failed to apply: {pr.stderr[-500:]}"}
    # fresh bytecode prefix per gate: guarantees tests execute current source,
    # immune to (mtime-second, size) pyc invalidation misses
    gate_tmp = os.path.join(os.path.dirname(ws), "g") + os.sep      # see TMPDIR note in run_claude
    os.makedirs(gate_tmp, exist_ok=True)
    gate_env = scrubbed_env({"PYTHONPYCACHEPREFIX": os.path.join(cell, ".pycache-gate"),
                             "TMPDIR": gate_tmp})

    f2p = inst["FAIL_TO_PASS"]
    vpath = os.path.join(task_dir, "verify.json")
    if os.path.exists(vpath):      # v2: P2P tests proven green in THIS env at base and with gold
        p2p = json.load(open(vpath))["p2p_verified"]
    else:                          # v1 behaviour
        p2p = inst["PASS_TO_PASS"][:20]
    try:
        passed_ids, tail = run_graded(py, ws, f2p + p2p, gate_env)
    except subprocess.TimeoutExpired:
        return {"passed": False, "detail": "pytest timeout", **stat}
    f2p_ok = [t for t in f2p if t in passed_ids]
    p2p_bad = [t for t in p2p if t not in passed_ids]
    resolved = len(f2p_ok) == len(f2p) and not p2p_bad and not tests_touched
    return {
        "passed": resolved,
        "fail_to_pass_ok": len(f2p_ok) == len(f2p),
        "pass_to_pass_ok": not p2p_bad,
        "f2p_passed": len(f2p_ok), "f2p_total": len(f2p),
        "p2p_regressions": len(p2p_bad), "p2p_total": len(p2p),
        "p2p_regressed_ids": p2p_bad[:20],
        "tests_modified": tests_touched,
        **stat,
        "detail": "" if resolved else f"f2p:{len(f2p_ok)}/{len(f2p)} p2p_regressions:{len(p2p_bad)} touched:{tests_touched}\n{tail[-1500:]}",
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
               max_turns=None, timeout=None, effort=None, activate=False, offline=False):
    max_turns = max_turns or MAX_TURNS[kind]
    timeout = timeout or TIMEOUTS[kind]
    cond = CONDITIONS[condition]
    cmd = [
        "claude", "-p", "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "", "--no-session-persistence",
        # no MCP at all: without this the account's claude.ai connectors (Drive,
        # Calendar, brokerage...) load into the nested agent — ~75k tokens of tool
        # schemas and, under skip-permissions, real account access. v2 smoke caught it.
        "--strict-mcp-config",
        "--tools", TOOLS,
        "--dangerously-skip-permissions",
        "--max-turns", str(max_turns),
        *cond["args"],
    ]
    effort = cond.get("effort") or effort      # an effort arm overrides the phase's level
    if effort:
        cmd += ["--effort", effort]
    env = scrubbed_env(cond["env"])
    if offline:
        env.update(OFFLINE_ENV)
        for k in ("UV_CACHE_DIR", "HF_HOME"):      # harness-only; they point into this tree
            env.pop(k, None)
        env["PYTHONPYCACHEPREFIX"] = os.path.join(os.path.dirname(ws), ".pyc")
        # Private temp root per run. pytest keeps its numbered dirs under
        # $TMPDIR/pytest-of-<user>/ and garbage-collects them; concurrent sessions of one
        # user race on that cleanup, and pytest's own suite turns the resulting rm_rf
        # warning into an error. With jobs=2 that failed every pytest-repo gate in the
        # first calibration round — including a patch identical to the gold fix.
        env["TMPDIR"] = os.path.join(os.path.dirname(ws), "t") + os.sep
        os.makedirs(env["TMPDIR"], exist_ok=True)
    path = list(cond.get("path_prepend", []))
    if activate:                       # v2: the project venv is activated for every arm
        path.insert(0, os.path.join(ws, ".venv", "bin"))
        env["VIRTUAL_ENV"] = os.path.join(ws, ".venv")
    if path:
        env["PATH"] = os.pathsep.join(path + [env.get("PATH", "")])
    meta = {
        "condition": condition, "model": model, "effort": effort, "cmd": cmd,
        "attempt": attempt, "cli_version": CLI_VERSION,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    fam = FAMILY.get(condition)
    if fam:
        with _LOCK:
            _ACTIVE[fam] = _ACTIVE.get(fam, 0) + 1
            for f in PRE_FLAGS.get(fam, []):
                if not os.path.exists(f):
                    open(f, "w").close()
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
    pyv = os.path.join(ws, ".venv", "pyvenv.cfg")
    if os.path.exists(pyv):
        meta["venv_python"] = " ".join(l.strip() for l in open(pyv) if l.startswith(("home", "version")))
    meta["disk_free_gb"] = round(shutil.disk_usage(ROOT).free / 1e9, 2)
    meta["exit_code"] = proc.returncode
    meta["wall_s"] = round(time.time() - t0, 1)
    meta["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if fam:
        with _LOCK:
            _ACTIVE[fam] -= 1
            # the first flag is the hook's own "active" marker: proof it fired
            meta[f"{fam}_flag_seen"] = os.path.exists(HOST_FLAGS[fam][0])
            if _ACTIVE[fam] == 0:          # never pull a flag from under a live run
                for f in HOST_FLAGS[fam]:
                    if os.path.exists(f):
                        os.remove(f)
                meta[f"{fam}_flag_cleaned"] = True
    return meta


def has_result_event(events_path):
    """True only for a run that actually ran. A session cut off by a usage limit can
    still emit a result event (is_error + a limit message); gating that would record a
    token saver's "failure" that is really the plan's quota."""
    if not os.path.exists(events_path):
        return False
    last = None
    with open(events_path) as f:
        for line in f:
            if '"type":"result"' in line or '"type": "result"' in line:
                try:
                    last = json.loads(line)
                except json.JSONDecodeError:
                    pass
    if last is None:
        return False
    if last.get("is_error") and RATE_LIMIT_PAT.search(json.dumps(last.get("result") or "")):
        return False
    return True


_AUDIT = {
    # reaching for the network / another copy of the project
    # (verbs and package hosts only: a bare URL is usually a docstring being edited)
    "net": re.compile(r"\b(pip3?|uv)\s+(download|install)\b|\bcurl\b|\bwget\b|"
                      r"\bgit\s+(clone|fetch|pull|ls-remote|remote\s+add)\b|urlretrieve|urlopen\(|"
                      r"pypi\.org|pythonhosted\.org|githubusercontent\.com"),
    # trying to defeat the offline environment
    "bypass": re.compile(r"unset\s+\w*proxy|\bno_proxy=|\bNO_PROXY=|https?_proxy=|HTTPS?_PROXY=|"
                         r"env\s+-u|PIP_NO_INDEX=|UV_OFFLINE=|--index-url|--proxy", re.I),
    # other copies on this machine, or the harness itself
    "outside": re.compile(r"/opt/homebrew|/usr/local/lib/python|/Library/Python|\.cache/uv|"
                          r"skill-gym/(tasks|\.cache|results|bin|vendor)|instance\.json|\.cache/gold"),
}


_SITE_PKG = re.compile(r"(/[\w.@+-]+)+/site-packages")   # a PATH, not the word in a grep filter


def audit_run(events_path, ws=None):
    """Flag tool calls that look up the answer instead of deriving it. Heuristic and
    deliberately noisy: a hit is a reason to read the transcript, not a verdict.
    Recomputed from the event log by analyze_v2.py, so the rules can be tightened
    without re-running anything."""
    hits = {k: [] for k in _AUDIT}
    for line in open(events_path):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init" and not ws:
            ws = ev.get("cwd")
        if ev.get("type") != "assistant":
            continue
        for b in ev["message"].get("content", []):
            if b.get("type") != "tool_use":
                continue
            text = json.dumps(b.get("input", {}))
            for k, pat in _AUDIT.items():
                if pat.search(text):
                    hits[k].append(f"{b.get('name')}: {text[:200]}")
            for m in _SITE_PKG.finditer(text):     # another installed copy of a library
                if not (ws and m.group(0).startswith(ws)):
                    hits["outside"].append(f"{b.get('name')}: {text[:200]}")
                    break
    return {"clean": not any(hits.values()), **{k: v[:10] for k, v in hits.items()}}


def isolation_breach(events_path):
    """The nested agent must see exactly the pinned built-in tools and no MCP
    server. Returns a description of the breach, or None."""
    for line in open(events_path):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            extra = sorted(set(ev.get("tools", [])) - set(TOOLS.split(",")))
            mcp = [m.get("name") for m in ev.get("mcp_servers", [])]
            if extra or mcp:
                return f"extra tools={extra[:5]}{'...' if len(extra) > 5 else ''} mcp={mcp}"
            return None
    return "no init event"


def looks_rate_limited(cell):
    for name in ("stderr.log", "events.jsonl"):
        p = os.path.join(cell, name)
        if os.path.exists(p):
            tail = open(p, "rb").read()[-8000:].decode("utf-8", "replace")
            if RATE_LIMIT_PAT.search(tail):
                return True
    return False


def run_cell(phase, alias, task_rel, condition, trial, model, effort=None):
    kind, _, _ = task_rel.partition("/")
    task_dir = os.path.join(ROOT, "tasks", task_rel) if kind != "smoke" else ""
    cell = os.path.join(RUNS, phase, alias, condition, f"t{trial}")
    gate_path = os.path.join(cell, "gate.json")
    if os.path.exists(os.path.join(RUNS, phase, "STOP")):   # `touch results/runs/v2/STOP`: finish
        log(f"STOP file present; not starting {alias}/{condition}/t{trial}")   # in-flight runs, start no more
        return
    if os.path.exists(gate_path):
        log(f"skip {alias}/{condition}/t{trial} (done)")
        return
    ws = os.path.join(cell, "workspace")
    if kind == "swebench" and phase == "v2":
        import hashlib
        opaque = hashlib.sha1(f"{alias}/{condition}/{trial}".encode()).hexdigest()[:10]
        ws = os.path.join(WS_ROOT, opaque, task_rel.split("__")[-1].rsplit("-", 1)[0])
    events = os.path.join(cell, "events.jsonl")

    if CONDITIONS[condition].get("proxy"):
        PROXY.ensure()

    inst = None
    if not has_result_event(events):
        if os.path.isdir(cell):
            shutil.rmtree(cell)
        os.makedirs(cell, exist_ok=True)
        if ws.startswith(WS_ROOT):
            force_rmtree(os.path.dirname(ws))
            os.makedirs(os.path.dirname(ws), exist_ok=True)
        wait_for_disk()
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
                              timeout=(inst or {}).get("timeout"), effort=effort,
                              activate=bool((inst or {}).get("activate")),
                              offline=bool((inst or {}).get("offline")))
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
    breach = isolation_breach(events)
    if breach:   # never gate a contaminated run; delete the cell dir to re-run it
        with open(gate_path + ".error", "w") as f:
            f.write("isolation breach: " + breach)
        log(f"ERROR {alias}/{condition}/t{trial}: isolation breach ({breach}); not gated")
        force_rmtree(os.path.dirname(ws) if ws.startswith(WS_ROOT) else ws)
        return

    if inst is None:
        inst = json.load(open(os.path.join(task_dir, "instance.json"))) if kind != "smoke" else {}
    log(f"gate {alias}/{condition}/t{trial}")
    verdict = GATE[kind](task_dir, ws, cell, inst)
    if kind == "swebench":
        verdict["audit"] = audit_run(events, ws)
        if not verdict["audit"]["clean"]:
            log(f"AUDIT {alias}/{condition}/t{trial}: " + ", ".join(
                f"{k}={len(v)}" for k, v in verdict["audit"].items() if k != "clean" and v))
    with open(gate_path, "w") as f:
        json.dump(verdict, f, indent=1)
    log(f"gate {alias}/{condition}/t{trial}: {'PASS' if verdict.get('passed') else 'FAIL'}")
    if kind == "swebench" and not KEEP_WS:
        # logs + patch.diff + verdict are the record; the workspace is rebuildable
        force_rmtree(os.path.dirname(ws) if ws.startswith(WS_ROOT) else ws)
        force_rmtree(os.path.join(cell, ".pycache-gate"))


# ------------------------------------------------------------ phases
def cmd_run(args):
    spec = PHASES.get(args.phase, {})
    phase = spec.get("runs_as") or args.phase or "custom"
    conditions = (args.conditions.split(",") if args.conditions else spec.get("conditions", ["baseline"]))
    tasks = (args.tasks.split(",") if args.tasks else spec.get("tasks", ["C1"]))
    trials = args.trials or spec.get("trials", 1)
    model = args.model or spec.get("model", "opus")
    effort = args.effort or spec.get("effort")
    cells = []
    for t in range(1, trials + 1):
        for alias in tasks:
            for cond in conditions:  # interleaved: condition round-robin within task
                cells.append((alias, cond, t))
    neutral_tools()
    log(f"phase={phase} model={model} effort={effort} cells={len(cells)} jobs={args.jobs}")
    try:
        if args.jobs > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
                futs = [ex.submit(run_cell, phase, a, BATTERY[a], c, t, model, effort) for a, c, t in cells]
                for f in concurrent.futures.as_completed(futs):
                    if f.exception():
                        log(f"cell crashed: {f.exception()!r}")
        else:
            for alias, cond, t in cells:
                run_cell(phase, alias, BATTERY[alias], cond, t, model, effort)
    finally:
        PROXY.stop()
    log("run complete. Next: python3 gym.py analyze  (via analyze.py)")


def cmd_regate(args):
    """Forensics: rebuild <task>/<arm>/t<N> from its saved patch.diff in a fresh
    workspace and gate it again. The old verdict is kept as gate.json.prev."""
    alias, condition, trial = args.cell.split("/")
    task_rel = BATTERY[alias]
    task_dir = os.path.join(ROOT, "tasks", task_rel)
    cell = os.path.join(RUNS, "v2", alias, condition, trial)
    ws = os.path.join(WS_ROOT, "regate-" + alias, task_rel.split("__")[-1].rsplit("-", 1)[0])
    shutil.rmtree(os.path.dirname(ws), ignore_errors=True)
    os.makedirs(os.path.dirname(ws))
    inst = setup_swebench(task_dir, ws)
    patch = os.path.join(cell, "patch.diff")
    if os.path.getsize(patch):
        sh(["git", "-C", ws, "apply", "--whitespace=nowarn", patch])
    verdict = gate_swebench(task_dir, ws, cell, inst)
    verdict["audit"] = audit_run(os.path.join(cell, "events.jsonl"))
    verdict["regated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    gp = os.path.join(cell, "gate.json")
    if os.path.exists(gp):
        os.replace(gp, gp + ".prev")
    with open(gp, "w") as f:
        json.dump(verdict, f, indent=1)
    log(f"regate {args.cell}: {'PASS' if verdict['passed'] else 'FAIL'} "
        f"(f2p {verdict.get('f2p_passed')}/{verdict.get('f2p_total')}, regressions {verdict.get('p2p_regressions')})")
    force_rmtree(os.path.dirname(ws))
    force_rmtree(os.path.join(cell, ".pycache-gate"))


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
                note = " hook-fired=" + str(bool(meta.get("caveman_flag_seen")))
            log(f"SMOKE {cond}: {'OK' if ok else 'FAILED'}{note}")
    finally:
        PROXY.stop()


def _cli_version():
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:
        return "unknown"


CLI_VERSION = None

if __name__ == "__main__":
    CLI_VERSION = _cli_version()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--phase", choices=list(PHASES))
    p_run.add_argument("--conditions")
    p_run.add_argument("--tasks")
    p_run.add_argument("--trials", type=int)
    p_run.add_argument("--model")
    p_run.add_argument("--effort", help="low|medium|high|xhigh|max (phase default if omitted)")
    p_run.add_argument("--jobs", type=int, default=1, help="cells run concurrently")
    p_run.set_defaults(fn=cmd_run)
    p_re = sub.add_parser("regate")
    p_re.add_argument("cell", help="<task>/<arm>/t<N>, e.g. pytest-7205/baseline/t1")
    p_re.set_defaults(fn=cmd_regate)
    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--model")
    p_smoke.set_defaults(fn=cmd_smoke)
    args = ap.parse_args()
    os.makedirs(RUNS, exist_ok=True)
    args.fn(args)
