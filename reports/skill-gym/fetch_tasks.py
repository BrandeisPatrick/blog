#!/usr/bin/env python3
"""Fetch and pin benchmark task instances for skill-gym.

Sources:
  - SWE-bench Verified (princeton-nlp/SWE-bench_Verified) via the HF
    datasets-server REST API (no heavy deps).
  - SpreadsheetBench sample_data_200 tarball (already downloaded to
    .cache/ssb by scaffold step; this script extracts the pinned instances).

Everything is pinned by instance ID so runs are reproducible.
"""
import json
import os
import shutil
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(ROOT, "tasks")
SSB_SRC = os.path.join(ROOT, ".cache", "ssb", "sample_data_200")

# ---------------------------------------------------------------- SWE-bench
# Pinned instances (small pure-Python repos, feasible natively on macOS).
# python/setup verified by verify_swebench.sh; adjust there if an env breaks.
SWEBENCH_IDS = {
    # C1: classic small bugfix loop
    "pylint-dev__pylint-6903": {
        "python": "3.9",
        "install": ["pip install -e .", "pip install pytest<8 py>=1.11"],
    },
    # C2: pytest fixing itself (no external pytest — the repo IS pytest)
    "pytest-dev__pytest-7490": {"python": "3.9", "install": ["pip install -e ."]},
    # C3: verbose-output repo (input-token pressure)
    "sphinx-doc__sphinx-10323": {
        "python": "3.9",
        "install": ["pip install -e .[test]", "pip install pytest<8"],
    },
    # Backups (not in default battery; verified on demand)
    "pylint-dev__pylint-7277": {
        "python": "3.9",
        "install": ["pip install -e .", "pip install pytest<8 py>=1.11"],
    },
    "pytest-dev__pytest-7982": {"python": "3.9", "install": ["pip install -e ."]},
    # HARD TIER (SWE-bench Verified difficulty "1-4 hours" / ">4 hours")
    "pylint-dev__pylint-8898": {
        "python": "3.9",
        "install": ["pip install -e .", "pip install pytest<8 py>=1.11"],
        "max_turns": 120, "timeout": 3600,
    },
    "pylint-dev__pylint-4551": {
        "python": "3.9",
        "install": ["pip install -e .", "pip install pytest<8 py>=1.11"],
        "max_turns": 120, "timeout": 3600,
    },
    "pytest-dev__pytest-10356": {
        "python": "3.9", "install": ["pip install -e ."],
        "max_turns": 120, "timeout": 3600,
    },
    "pytest-dev__pytest-6197": {
        "python": "3.9", "install": ["pip install -e ."],
        "max_turns": 120, "timeout": 3600,
    },
    "sphinx-doc__sphinx-9461": {
        "python": "3.9",
        "install": ["pip install -e .[test]", "pip install pytest<8 setuptools<70"],
        "max_turns": 120, "timeout": 3600,
    },
    "sphinx-doc__sphinx-11510": {
        "python": "3.9",
        "install": ["pip install -e .[test]", "pip install pytest<8"],
        "max_turns": 120, "timeout": 3600,
    },
    "sphinx-doc__sphinx-7590": {  # the ">4 hours" monster; sphinx 3.x-era pins
        "python": "3.9",
        "install": ["pip install -e .[test]",
                    "pip install pytest<8 markupsafe<2.1 jinja2<3.1 alabaster<0.7.14 setuptools<70 roman docutils<0.18"],
        "max_turns": 150, "timeout": 4500,
    },
}

# ---------------------------------------------------------------- v2 pool
# Candidates chosen by MEASURED difficulty (see PLAN.md §2): solved by 2-7 of
# 10 public frontier submissions in swe-bench/experiments. Env recipes port the
# official SWE-bench specs (harness/constants/python.py @ v4.1.0): same python,
# same pins, expressed as install-time constraints instead of sed edits to
# setup.py so the checkout stays clean. --exclude-newer freezes the package
# universe to the era the benchmark's own images were built in.
EXCLUDE_NEWER = "2024-08-01"
V2_IDS = [
    "pylint-dev__pylint-4970", "pylint-dev__pylint-6528", "pylint-dev__pylint-7277",
    "pylint-dev__pylint-6386", "pylint-dev__pylint-8898",
    "pytest-dev__pytest-5787", "pytest-dev__pytest-10356", "pytest-dev__pytest-7205",
    "sphinx-doc__sphinx-8548", "sphinx-doc__sphinx-8056", "sphinx-doc__sphinx-8595",
    "sphinx-doc__sphinx-9711", "sphinx-doc__sphinx-10435", "sphinx-doc__sphinx-10673",
    "psf__requests-5414", "psf__requests-6028", "psf__requests-2931",
    "pydata__xarray-6938", "pydata__xarray-4687",
]
# Reserve pool: solved by at most 1 of the 10 public submissions. Added when the first
# calibration round showed Opus 5 at xhigh passing 15 of 16 — the main pool sits nearer
# the ceiling for this model than its public priors suggested.
V2B_IDS = [
    "pylint-dev__pylint-4551", "pylint-dev__pylint-4604", "pylint-dev__pylint-4661",
    "pylint-dev__pylint-7080", "pytest-dev__pytest-5840",
    "sphinx-doc__sphinx-10614", "sphinx-doc__sphinx-11510", "sphinx-doc__sphinx-7590",
    "sphinx-doc__sphinx-7748", "sphinx-doc__sphinx-9229", "sphinx-doc__sphinx-7462",
    "sphinx-doc__sphinx-7985", "sphinx-doc__sphinx-9461", "sphinx-doc__sphinx-9602",
    "pydata__xarray-6599", "pydata__xarray-6992", "pydata__xarray-7229",
]
V2_IDS = V2_IDS + V2B_IDS
_PYTEST_PINS = {
    "5.1": "atomicwrites==1.4.1 attrs==23.1.0 more-itertools==10.1.0 packaging==23.1 pluggy==0.13.1 py==1.11.0 wcwidth==0.2.6",
    "5.4": "py==1.11.0 packaging==23.1 attrs==23.1.0 more-itertools==10.1.0 pluggy==0.13.1",
    "7.2": "attrs==23.1.0 iniconfig==2.0.0 packaging==23.1 pluggy==0.13.1 py==1.11.0 tomli==2.0.1",
}
_SPHINX_OLD = ("Jinja2<3.0 sphinxcontrib-applehelp<=1.0.7 sphinxcontrib-devhelp<=1.0.5 "
               "sphinxcontrib-qthelp<=1.0.6 alabaster<0.7.12 markupsafe<=2.0.1 "
               "sphinxcontrib-htmlhelp<=2.0.4 sphinxcontrib-serializinghtml<=1.1.9")


# Instance-level deviations from the per-version recipe, each found by
# bin/verify_swebench.py failing and explained here.
V2_OVERRIDES = {
    # pyproject pins setuptools~=62.6, which predates PEP 660 editable hooks; pip
    # falls back to `setup.py develop`, uv does not -> build against the venv's setuptools
    "pylint-dev__pylint-7277": {"install": [
        "pip install setuptools<70 wheel",
        "pip install --no-build-isolation -e . pytest<8 py>=1.11"]},
    # 1470 of the 1717 PASS_TO_PASS tests live in test_units.py, which needs pint
    "pydata__xarray-4687": {"extra": " pint"},
}


def v2_recipe(repo, version):
    """Native env recipe for a (repo, version), ported from the official specs."""
    r = {"max_turns": 120, "timeout": 3600, "exclude_newer": EXCLUDE_NEWER}
    if repo == "pylint-dev/pylint":
        r.update(python="3.9", install=["pip install -e . pytest<8 py>=1.11 setuptools<70"])
    elif repo == "pytest-dev/pytest":
        r.update(python="3.9", install=["pip install -e . " + _PYTEST_PINS.get(version, "")])
    elif repo == "sphinx-doc/sphinx":
        old = tuple(int(x) for x in version.split(".")) <= (4, 4)
        pins = (_SPHINX_OLD if old else "Jinja2==3.0.3") + " pytest<8 setuptools<70"
        r.update(python="3.9", install=["pip install -e .[test] " + pins])
    elif repo == "psf/requests":
        r.update(python="3.9", install=["pip install -e . pytest<8"])
    elif repo == "pydata/xarray":
        r.update(python="3.10", install=[
            "pip install -e . numpy==1.23.0 packaging==23.1 pandas==1.5.3 pytest==7.4.0 "
            "python-dateutil==2.8.2 pytz==2023.3 six==1.16.0 scipy==1.11.1 "
            "setuptools==68.0.0 dask==2022.8.1"])
    else:
        raise SystemExit(f"no v2 recipe for {repo}")
    return r


DS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=princeton-nlp%2FSWE-bench_Verified&config=default&split=test"
    "&offset={off}&length=100"
)

SWE_PROMPT = """You are working in a checkout of {repo} at commit {commit}.
The project's virtualenv is at .venv (already installed, editable). Use
.venv/bin/python and .venv/bin/pytest for everything.

Below is a real GitHub issue for this repository. Fix it.

Rules:
- Modify source code only. Do NOT modify any test files.
- Verify your fix by running relevant tests before finishing.
- When done, summarize the root cause and your change.

<issue>
{problem}
</issue>
"""


# v2: the venv is ACTIVATED (PATH + VIRTUAL_ENV set by the runner), the way a
# developer's shell normally is. Besides being the realistic setup, it keeps the
# comparison fair: shell-output tools such as rtk rewrite `pytest ...` but not
# `.venv/bin/pytest ...`, so v1's "use .venv/bin/python" wording would have
# hidden most test output from them.
SWE_PROMPT_V2 = """You are working in a checkout of {repo} at commit {commit}.
The project's virtualenv (.venv) is installed (editable) and already activated:
`python` and `pytest` on PATH are the project's own.

Below is a real GitHub issue for this repository. Fix it.

Rules:
- Modify source code only. Do NOT modify any test files.
- Work only from this checkout. Do NOT download, install or consult any other copy
  or later version of this project (no pip/curl/git fetches of upstream code), and
  do not read files outside this directory apart from your own scratch files.
- Verify your fix by running relevant tests before finishing.
- When done, summarize the root cause and your change.

<issue>
{problem}
</issue>
"""


def fetch_swebench():
    wanted = dict(SWEBENCH_IDS)
    for iid in V2_IDS:            # recipe filled in once the row's version is known
        wanted.setdefault(iid, None)
    found = {}
    for off in range(0, 500, 100):
        data = None
        for attempt in range(5):
            try:
                with urllib.request.urlopen(DS_URL.format(off=off), timeout=60) as r:
                    data = json.load(r)
                break
            except Exception as e:  # transient 5xx from datasets-server
                print(f"  fetch offset={off} attempt {attempt+1} failed ({e}); retrying")
                import time as _t
                _t.sleep(5 * (attempt + 1))
        if data is None:
            sys.exit(f"datasets-server unavailable at offset {off}")
        for row in data["rows"]:
            row = row["row"]
            iid = row["instance_id"]
            if iid in wanted:
                found[iid] = row
    missing = set(wanted) - set(found)
    if missing:
        sys.exit(f"missing SWE-bench rows: {missing}")
    gold_dir = os.path.join(ROOT, ".cache", "gold")
    if "--gold" in sys.argv:
        os.makedirs(gold_dir, exist_ok=True)
    for iid, row in found.items():
        if iid in V2_IDS:     # v2 pool always uses the ported official recipe
            wanted[iid] = v2_recipe(row["repo"], row.get("version") or "")
            ov = V2_OVERRIDES.get(iid, {})
            if "install" in ov:
                wanted[iid]["install"] = ov["install"]
            if "extra" in ov:
                wanted[iid]["install"][-1] += ov["extra"]
        # gold patch: only for bin/verify_swebench.py, only on request (`--gold`), and
        # deleted again before agents run — it is the answer key
        if "--gold" in sys.argv:
            with open(os.path.join(gold_dir, iid + ".patch"), "w") as f:
                f.write(row["patch"])
        d = os.path.join(TASKS, "swebench", iid)
        os.makedirs(d, exist_ok=True)
        inst = {
            "instance_id": iid,
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "environment_setup_commit": row.get("environment_setup_commit"),
            "version": row.get("version"),
            "FAIL_TO_PASS": json.loads(row["FAIL_TO_PASS"]),
            "PASS_TO_PASS": json.loads(row["PASS_TO_PASS"]),
            # applied by the gate (never shown to the agent), per official harness
            "test_patch": row["test_patch"],
            "python": wanted[iid]["python"],
            "install": wanted[iid]["install"],
        }
        for k in ("max_turns", "timeout", "exclude_newer"):
            if wanted[iid].get(k):
                inst[k] = wanted[iid][k]
        if iid in V2_IDS:
            inst["activate"] = True
            inst["offline"] = True
        prompt = (SWE_PROMPT_V2 if iid in V2_IDS else SWE_PROMPT).format(
            repo=row["repo"], commit=row["base_commit"][:12],
            problem=row["problem_statement"].strip())
        for name, text in (("instance.json", json.dumps(inst, indent=1)), ("prompt.md", prompt)):
            path = os.path.join(d, name)   # rewrite only on change: a run may be reading it
            if not os.path.exists(path) or open(path).read() != text:
                with open(path, "w") as f:
                    f.write(text)
        print(f"pinned swebench {iid} ({row['repo']} @ {row['base_commit'][:8]})")


# ---------------------------------------------------- SpreadsheetBench
SSB_IDS = ["59055", "13894", "55392"]  # O1, O2, O3 (55392 = 2.7MB input pole)

SSB_PROMPT = """You are given a spreadsheet manipulation request from a real user,
plus three test-case workbooks: 1_input.xlsx, 2_input.xlsx, 3_input.xlsx
(same structure, different data).

Apply the request to EACH input workbook and save the results as
1_output.xlsx, 2_output.xlsx, 3_output.xlsx in the working directory.
Python with openpyxl is available at .venv/bin/python. Compute final VALUES
in the answer cells (formulas are also acceptable only if openpyxl would
show cached values; when in doubt, write computed values).

Do not modify the input files. Answers will be checked at position: {position}

<request>
{instruction}
</request>
"""


def fetch_ssb():
    with open(os.path.join(SSB_SRC, "dataset.json")) as f:
        dataset = {str(r["id"]): r for r in json.load(f)}
    for sid in SSB_IDS:
        row = dataset[sid]
        d = os.path.join(TASKS, "ssb", sid)
        os.makedirs(d, exist_ok=True)
        srcdir = os.path.join(SSB_SRC, row["spreadsheet_path"])
        for fn in os.listdir(srcdir):
            shutil.copy2(os.path.join(srcdir, fn), os.path.join(d, fn))
        with open(os.path.join(d, "instance.json"), "w") as f:
            json.dump(row, f, indent=1)
        with open(os.path.join(d, "prompt.md"), "w") as f:
            f.write(
                SSB_PROMPT.format(
                    position=row["answer_position"], instruction=row["instruction"]
                )
            )
        print(f"pinned ssb {sid} ({row['instruction_type']}, pos {row['answer_position']})")


# ------------------------------------------------------------- C4 doc task
C4_PROMPT = """You are in a checkout of pylint-dev/pylint. Write a contributor
onboarding document (ONBOARDING.md is NOT to be created — reply in chat only)
explaining, for a new contributor:

1. How a lint run flows end to end: entry point, how PyLinter is constructed,
   how checkers are registered and invoked, and how messages are emitted.
2. The role of these specific pieces: pylint/lint/pylinter.py, the checkers/
   package, message definitions and message IDs, and the functional test
   framework under tests/functional.
3. How to add a brand-new checker with one new message, step by step.

Ground every claim in the actual code you read. Reply in chat with the
document; do not write files.
"""


def write_c4():
    d = os.path.join(TASKS, "docwork", "pylint-onboarding")
    os.makedirs(d, exist_ok=True)
    meta = {
        "kind": "docwork",
        "repo": "pylint-dev/pylint",
        # same checkout as C1 so the mirror is reused
        "base_commit": None,  # filled from pylint-6903 instance at setup
        "from_instance": "pylint-dev__pylint-6903",
        # deterministic rubric: response must mention these (case-insensitive)
        "rubric": [
            "PyLinter",
            "pylinter.py",
            "register_checker|register_plugins|register_checkers",
            "msgs|message.id|message-id|msgid",
            "tests/functional",
            "BaseChecker|BaseRawFileChecker|BaseTokenChecker",
            "visit_|leave_",
        ],
        "rubric_pass_min": 5,
    }
    with open(os.path.join(d, "instance.json"), "w") as f:
        json.dump(meta, f, indent=1)
    with open(os.path.join(d, "prompt.md"), "w") as f:
        f.write(C4_PROMPT)
    print("pinned docwork pylint-onboarding")


if __name__ == "__main__":
    os.makedirs(TASKS, exist_ok=True)
    fetch_swebench()
    if "swebench" not in sys.argv[1:]:   # `fetch_tasks.py swebench [--gold]` skips the SSB tarball
        fetch_ssb()
        write_c4()
    print("done.")
