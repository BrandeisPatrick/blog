#!/usr/bin/env python3
"""Verify one SWE-bench instance runs natively: env builds, test_patch applies,
FAIL_TO_PASS is red pre-fix, PASS_TO_PASS sample is green. Prints one JSON line.

Usage: python3 bin/verify_swebench.py <instance_id>
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
from gym import setup_swebench, scrubbed_env  # noqa: E402

iid = sys.argv[1]
task_dir = os.path.join(ROOT, "tasks", "swebench", iid)
ws = os.path.abspath(os.path.join(ROOT, ".cache", "verify", iid, "workspace"))
out = {"instance": iid, "install_ok": False, "patch_ok": False,
       "f2p_red": False, "p2p_green": False, "notes": ""}
t0 = time.time()
try:
    if os.path.isdir(ws):
        shutil.rmtree(ws)
    os.makedirs(os.path.dirname(ws), exist_ok=True)
    inst = setup_swebench(task_dir, ws)
    out["install_ok"] = True
except subprocess.CalledProcessError as e:
    out["notes"] = f"install failed: {(e.stderr or e.stdout or str(e))[-300:] if hasattr(e, 'stderr') else str(e)[:300]}"
    print(json.dumps(out)); sys.exit(0)
except Exception as e:
    out["notes"] = f"setup error: {e}"[:300]
    print(json.dumps(out)); sys.exit(0)

env = scrubbed_env({"PYTHONPYCACHEPREFIX": os.path.join(ws, ".pycache-verify")})
pr = subprocess.run(["git", "-C", ws, "apply", "--whitespace=nowarn", "-"],
                    input=inst["test_patch"], capture_output=True, text=True)
out["patch_ok"] = pr.returncode == 0
if not out["patch_ok"]:
    out["notes"] = "test_patch: " + pr.stderr[-200:]
    print(json.dumps(out)); sys.exit(0)

py = os.path.join(ws, ".venv", "bin", "python")
try:
    r1 = subprocess.run([py, "-m", "pytest", "-q", "--no-header", *inst["FAIL_TO_PASS"]],
                        cwd=ws, capture_output=True, text=True, timeout=900, env=env)
    out["f2p_red"] = r1.returncode != 0 and ("failed" in r1.stdout or "error" in r1.stdout.lower())
    r2 = subprocess.run([py, "-m", "pytest", "-q", "--no-header", *inst["PASS_TO_PASS"][:10]],
                        cwd=ws, capture_output=True, text=True, timeout=900, env=env)
    out["p2p_green"] = r2.returncode == 0
    if not out["f2p_red"]:
        out["notes"] = "f2p tail: " + (r1.stdout + r1.stderr)[-250:]
    elif not out["p2p_green"]:
        out["notes"] = "p2p tail: " + (r2.stdout + r2.stderr)[-250:]
except subprocess.TimeoutExpired:
    out["notes"] = "pytest timeout"
out["seconds"] = round(time.time() - t0)
out["verified"] = out["install_ok"] and out["patch_ok"] and out["f2p_red"] and out["p2p_green"]
print(json.dumps(out))
