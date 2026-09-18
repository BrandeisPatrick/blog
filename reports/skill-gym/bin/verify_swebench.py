#!/usr/bin/env python3
"""Verify one SWE-bench instance natively, against its gold patch. No agent, no tokens.

  base + test_patch  -> every FAIL_TO_PASS test must NOT pass   (the bug is real here)
  + gold patch       -> every FAIL_TO_PASS test must pass       (the gate is winnable here)
  PASS_TO_PASS       -> kept only if green BOTH times           (p2p_verified)

A task is `verified` only if all three hold, so by construction the gate fails the
unfixed repo and passes the reference fix in THIS environment. Writes
tasks/swebench/<id>/verify.json (tracked: it is the evidence the env is sound) and
prints one JSON line. The gold patch lives in .cache/gold/, outside tasks/.

Usage: python3 bin/verify_swebench.py <instance_id> [--keep]
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from gym import setup_swebench, scrubbed_env, run_graded  # noqa: E402

iid = sys.argv[1]
keep = "--keep" in sys.argv
task_dir = os.path.join(ROOT, "tasks", "swebench", iid)
ws = os.path.abspath(os.path.join(ROOT, ".cache", "verify", iid, "workspace"))
gold = os.path.join(ROOT, ".cache", "gold", iid + ".patch")
out = {"instance": iid, "verified": False, "install_ok": False, "patch_ok": False,
       "gold_ok": False, "f2p_red": False, "f2p_green": False, "notes": ""}
t0 = time.time()


def finish():
    out["seconds"] = round(time.time() - t0)
    slim = {k: v for k, v in out.items() if k != "p2p_verified"}
    print(json.dumps(slim), flush=True)
    if out.get("install_ok"):
        with open(os.path.join(task_dir, "verify.json"), "w") as f:
            json.dump(out, f, indent=1)
    if not keep:
        from gym import force_rmtree
        force_rmtree(os.path.dirname(ws))
    sys.exit(0)


try:
    if os.path.isdir(ws):
        shutil.rmtree(ws)
    os.makedirs(os.path.dirname(ws), exist_ok=True)
    inst = setup_swebench(task_dir, ws)
    out["install_ok"] = True
except subprocess.CalledProcessError as e:
    out["notes"] = f"install failed: {e}"[:400]
    finish()
except Exception as e:  # noqa: BLE001
    out["notes"] = f"setup error: {e}"[:400]
    finish()

py = os.path.join(ws, ".venv", "bin", "python")
f2p, p2p = inst["FAIL_TO_PASS"], inst["PASS_TO_PASS"]
out.update(f2p_total=len(f2p), p2p_total=len(p2p),
           env={"python": inst["python"], "install": inst["install"],
                "exclude_newer": inst.get("exclude_newer")})

pr = subprocess.run(["git", "-C", ws, "apply", "--whitespace=nowarn", "-"],
                    input=inst["test_patch"], capture_output=True, text=True)
out["patch_ok"] = pr.returncode == 0
if not out["patch_ok"]:
    out["notes"] = "test_patch: " + pr.stderr[-300:]
    finish()

try:
    tmp = os.path.join(os.path.dirname(ws), "t") + os.sep      # private TMPDIR, as the gate has
    os.makedirs(tmp, exist_ok=True)
    env = scrubbed_env({"PYTHONPYCACHEPREFIX": os.path.join(ws, ".pycache-verify-base"), "TMPDIR": tmp})
    base_pass, base_tail = run_graded(py, ws, f2p + p2p, env)
    out["f2p_passing_at_base"] = [t for t in f2p if t in base_pass]
    out["f2p_red"] = not out["f2p_passing_at_base"]

    gp = subprocess.run(["git", "-C", ws, "apply", "--whitespace=nowarn", gold],
                        capture_output=True, text=True)
    out["gold_ok"] = gp.returncode == 0
    if not out["gold_ok"]:
        out["notes"] = "gold patch: " + gp.stderr[-300:]
        finish()
    env = scrubbed_env({"PYTHONPYCACHEPREFIX": os.path.join(ws, ".pycache-verify-gold"), "TMPDIR": tmp})
    gold_pass, gold_tail = run_graded(py, ws, f2p + p2p, env)
    out["f2p_failing_with_gold"] = [t for t in f2p if t not in gold_pass]
    out["f2p_green"] = not out["f2p_failing_with_gold"]
    out["p2p_verified"] = [t for t in p2p if t in base_pass and t in gold_pass]
    out["p2p_verified_n"] = len(out["p2p_verified"])
    if not out["f2p_green"]:
        out["notes"] = "gold tail: " + gold_tail[-400:]
    elif not out["f2p_red"]:
        out["notes"] = "base tail: " + base_tail[-400:]
except subprocess.TimeoutExpired:
    out["notes"] = "pytest timeout"
    finish()

out["verified"] = bool(out["f2p_red"] and out["f2p_green"]
                       and out["p2p_verified_n"] >= 0.8 * len(p2p))
finish()
