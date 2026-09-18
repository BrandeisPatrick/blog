#!/usr/bin/env python3
"""skill-gym v2 analyzer — quality is graded, arms are compared pairwise by task.

  python3 analyze_v2.py calib [--freeze]   # baseline-only table; --freeze writes the task list
  python3 analyze_v2.py report    # every arm, on the frozen tasks only

Reads results/runs/v2/<task>/<arm>/t<N>/. Token accounting is v1's (analyze.parse_run);
what is new here is the quality side and the statistics:

  resolved          all FAIL_TO_PASS green, verified PASS_TO_PASS held, tests untouched
  f2p_frac          partial credit
  verified_last     the agent ran tests AFTER its final edit
  repeat_calls      identical tool calls issued more than once (the re-read tax)
  audit             lookups outside the workspace (see gym.audit_run)

Statistics are clustered by task (trials of one task are not independent): bootstrap
resamples tasks, then trials within a task. Arm-vs-baseline differences are paired by
task. `cost` is the CLI's own total_cost_usd (it prices the Haiku side-calls too).
"""
import glob
import json
import os
import random
import sys
import time
from collections import defaultdict
from math import comb

from analyze import parse_run, fmt_k
from gym import audit_run

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "results", "runs", "v2")
FROZEN = os.path.join(ROOT, "tasks", "v2_frozen.json")
ARMS = ["baseline", "caveman", "ponytail", "rtk", "headroom", "effort-high", "effort-low"]
N_TASKS = 10
# difficulty prior: how many of 10 public frontier submissions resolve the instance
PRIOR = {"pylint-4970": 3, "pylint-6528": 4, "pylint-7277": 4, "pylint-6386": 5, "pylint-8898": 2,
         "pytest-5787": 5, "pytest-10356": 2, "pytest-7205": 7,
         "sphinx-8548": 4, "sphinx-8056": 6, "sphinx-8595": 6, "sphinx-9711": 6,
         "sphinx-10435": 2, "sphinx-10673": 7,
         "requests-5414": 6, "requests-6028": 6, "requests-2931": 7,
         "xarray-6938": 4, "xarray-4687": 5,
         # reserve pool (<=1 of 10)
         "pylint-4551": 0, "pylint-4604": 0, "pylint-7080": 0, "pytest-5840": 0, "sphinx-7590": 0,
         "sphinx-7748": 0, "sphinx-9229": 0, "sphinx-7462": 1, "sphinx-7985": 1, "sphinx-9461": 1,
         "sphinx-9602": 1, "xarray-6599": 0, "xarray-6992": 0, "xarray-7229": 0}
# requests-6028 is about proxy handling, and the offline shell works by setting proxy
# variables: the task's subject and the harness's mechanism collide. Never selected.
EXCLUDED = {"requests-6028"}
random.seed(20260918)


def behaviour(cell):
    """Process metrics from the event log."""
    calls, last_edit, last_test = [], -1, -1
    for line in open(os.path.join(cell, "events.jsonl")):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for b in ev["message"].get("content", []):
            if b.get("type") != "tool_use":
                continue
            sig = b.get("name", "") + json.dumps(b.get("input", {}), sort_keys=True)
            calls.append((sig, b.get("name")))
            i = len(calls) - 1
            if b.get("name") in ("Edit", "Write"):
                last_edit = i
            cmd = (b.get("input", {}) or {}).get("command", "") if b.get("name") == "Bash" else ""
            if any(k in cmd for k in ("pytest", "tox ", "unittest")):
                last_test = i
    sigs = [c for c, _ in calls]
    return {"verified_last": last_edit >= 0 and last_test > last_edit,
            "edited": last_edit >= 0,
            "repeat_calls": len(sigs) - len(set(sigs))}


def collect():
    rows = []
    for cell in sorted(glob.glob(os.path.join(RUNS, "*", "*", "t*"))):
        if not os.path.exists(os.path.join(cell, "gate.json")):
            continue
        r = parse_run(cell)
        if not r:
            continue
        parts = cell.split(os.sep)
        gate = json.load(open(os.path.join(cell, "gate.json")))
        r.update(task=parts[-3], arm=parts[-2], trial=parts[-1], **behaviour(cell))
        r["f2p_frac"] = gate.get("f2p_passed", 0) / max(1, gate.get("f2p_total", 1))
        r["p2p_regressions"] = gate.get("p2p_regressions", 0)
        r["tests_modified"] = len(gate.get("tests_modified") or [])
        r["lines_added"] = gate.get("lines_added", 0)
        r["lines_removed"] = gate.get("lines_removed", 0)
        r["files_changed"] = gate.get("files_changed", 0)
        audit = audit_run(os.path.join(cell, "events.jsonl"))   # recomputed: rules may have tightened
        r["audit_clean"] = audit["clean"]
        r["audit"] = {k: v for k, v in audit.items() if k != "clean" and v}
        rows.append(r)
    return rows


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def by_task(rows, arm, key):
    d = defaultdict(list)
    for r in rows:
        if r["arm"] == arm:
            d[r["task"]].append(r[key] if not callable(key) else key(r))
    return d


def boot(tasks, fn, n=4000):
    """Clustered bootstrap: resample tasks; fn(sample_of_tasks) -> statistic."""
    if not tasks:
        return (0.0, 0.0)
    vals = sorted(fn([random.choice(tasks) for _ in tasks]) for _ in range(n))
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def pct(new, base):
    return f"{(new - base) / base * 100:+.0f}%" if base else "—"


# ------------------------------------------------------------------ calib
def cmd_calib(rows):
    base = [r for r in rows if r["arm"] == "baseline"]
    tasks = sorted({r["task"] for r in base})
    L = ["# skill-gym v2 — calibration (baseline only)\n",
         f"_Generated {time.strftime('%Y-%m-%d %H:%M')}; {len(base)} runs; model(s): "
         f"{', '.join(sorted({r['model'] for r in base if r['model']}))}._\n",
         "| task | public prior (n/10) | baseline pass | f2p partial | turns | wall s | cost $ | out tok | audit |",
         "|---|---|---|---|---|---|---|---|---|"]
    stat = {}
    for t in tasks:
        rs = [r for r in base if r["task"] == t]
        stat[t] = {"n": len(rs), "k": sum(r["passed"] for r in rs), "turns": mean([r["num_turns"] for r in rs])}
        dirty = sum(not r["audit_clean"] for r in rs)
        L.append(f"| {t} | {PRIOR.get(t, '?')} | {stat[t]['k']}/{stat[t]['n']} | {mean([r['f2p_frac'] for r in rs]):.2f} |"
                 f" {stat[t]['turns']:.0f} | {mean([r['duration_s'] for r in rs]):.0f} |"
                 f" {mean([r['cost_usd'] for r in rs]):.2f} | {fmt_k(mean([r['cats']['out_total'] for r in rs]))} |"
                 f" {'clean' if not dirty else f'{dirty} flagged'} |")
    done = [t for t in tasks if stat[t]["n"] >= 2 and t not in EXCLUDED]
    # In band = passed some but not all of its baseline trials. With two trials, 1/2 is in
    # the band for certain (a third can only make it 1/3 or 2/3).
    band = sorted([t for t in done if 0 < stat[t]["k"] < stat[t]["n"]],
                  key=lambda t: (abs(stat[t]["k"] / stat[t]["n"] - 0.5), -stat[t]["turns"]))
    chosen = band[:N_TASKS]
    if len(chosen) < N_TASKS:      # top up: always-pass tasks that took the most turns
        rest = sorted([t for t in done if stat[t]["k"] == stat[t]["n"] and t not in chosen],
                      key=lambda t: -stat[t]["turns"])
        chosen += rest[:N_TASKS - len(chosen)]
    floor = [t for t in done if stat[t]["k"] == 0]
    L += ["", f"**Rule** (PLAN.md §2, fixed before the reserve pool was run): a task is *in band* if the baseline "
              f"passes some but not all of its trials. Take in-band tasks first (nearest 50%, then most turns); "
              f"if fewer than {N_TASKS}, top up with always-pass tasks that took the most turns — the ones with "
              f"the most to lose. Never-pass tasks are dropped: a floor shows nothing. "
              f"Excluded: {', '.join(sorted(EXCLUDED))} (see analyze_v2.py).",
          "", f"In band: {len(band)} · always-pass: {sum(stat[t]['k'] == stat[t]['n'] for t in done)} · "
              f"never-pass (dropped): {len(floor)} · chosen: {len(chosen)}", "",
          "| chosen task | baseline | why |", "|---|---|---|"]
    for t in chosen:
        L.append(f"| {t} | {stat[t]['k']}/{stat[t]['n']} | {'in band' if t in band else 'top-up (most turns)'} |")
    md = "\n".join(L)
    open(os.path.join(ROOT, "results", "summary-v2-calib.md"), "w").write(md)
    print(md)
    if "--freeze" in sys.argv:
        json.dump({"frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tasks": chosen,
                   "baseline_at_freeze": {t: f"{stat[t]['k']}/{stat[t]['n']}" for t in chosen},
                   "in_band": band[:N_TASKS]},
                  open(FROZEN, "w"), indent=1)
        print(f"\nfrozen -> {FROZEN}")
    else:
        print("\n(not frozen; pass --freeze once every candidate has its trials)")


# ------------------------------------------------------------------ report
def cmd_report(rows):
    frozen = json.load(open(FROZEN))["tasks"]
    rows = [r for r in rows if r["task"] in frozen]
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    P = {a: by_task(rows, a, "passed") for a in arms}
    C = {a: by_task(rows, a, "cost_usd") for a in arms}
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "tasks": frozen, "arms": {}}
    L = ["# skill-gym v2 results\n",
         f"_Generated {out['generated']}; {len(rows)} runs on {len(frozen)} frozen tasks; model(s): "
         f"{', '.join(sorted({r['model'] for r in rows if r['model']}))}._\n",
         "## Headline\n",
         "| arm | solved | pass rate [95% CI] | Δ vs baseline [95% CI] | tasks better/worse/tie (sign p) |"
         " $/run | Δ | $/solved | Δ |", "|---|---|---|---|---|---|---|---|---|"]
    b_rate = lambda ts: mean([mean(P["baseline"][t]) for t in ts])  # noqa: E731
    base_cost = mean([mean(C["baseline"][t]) for t in frozen if C["baseline"].get(t)])
    base_solved = sum(sum(P["baseline"][t]) for t in frozen)
    base_n = sum(len(P["baseline"][t]) for t in frozen)
    base_cps = base_cost * base_n / base_solved if base_solved else float("inf")
    for a in arms:
        ts = [t for t in frozen if P[a].get(t) and P["baseline"].get(t)]
        rate = mean([mean(P[a][t]) for t in ts])
        lo, hi = boot(ts, lambda s, a=a: mean([mean(random.choices(P[a][t], k=len(P[a][t]))) for t in s]))
        d = rate - b_rate(ts)
        dlo, dhi = boot(ts, lambda s, a=a: mean([mean(random.choices(P[a][t], k=len(P[a][t])))
                                                 - mean(random.choices(P["baseline"][t], k=len(P["baseline"][t])))
                                                 for t in s]))
        better = sum(mean(P[a][t]) > mean(P["baseline"][t]) for t in ts)
        worse = sum(mean(P[a][t]) < mean(P["baseline"][t]) for t in ts)
        cost = mean([mean(C[a][t]) for t in ts])
        solved = sum(sum(P[a][t]) for t in ts)
        n = sum(len(P[a][t]) for t in ts)
        cps = cost * n / solved if solved else float("inf")
        out["arms"][a] = {"solved": solved, "n": n, "pass_rate": rate, "ci": [lo, hi], "delta": d,
                          "delta_ci": [dlo, dhi], "cost": cost, "cost_per_solved": cps,
                          "better": better, "worse": worse}
        L.append(f"| {a} | {solved}/{n} | {rate:.0%} [{lo:.0%}, {hi:.0%}] |"
                 + (" — | — |" if a == "baseline" else
                    f" {d * 100:+.0f} pts [{dlo * 100:+.0f}, {dhi * 100:+.0f}] |"
                    f" {better}/{worse}/{len(ts) - better - worse} (p={sign_test(better, worse):.2f}) |")
                 + f" {cost:.2f} | {pct(cost, base_cost)} | {cps:.2f} | {pct(cps, base_cps)} |")

    L += ["\n## Graded quality and process (mean per run)\n",
          "| arm | f2p partial credit | P2P regressions | tests modified | ran tests after last edit |"
          " repeated tool calls | lines added | audit-flagged runs |", "|---|---|---|---|---|---|---|---|"]
    for a in arms:
        rs = [r for r in rows if r["arm"] == a]
        out["arms"][a].update(f2p=mean([r["f2p_frac"] for r in rs]),
                              verified_last=mean([r["verified_last"] for r in rs]),
                              repeat_calls=mean([r["repeat_calls"] for r in rs]),
                              lines_added=mean([r["lines_added"] for r in rs]))
        L.append(f"| {a} | {mean([r['f2p_frac'] for r in rs]):.2f} | {mean([r['p2p_regressions'] for r in rs]):.2f} |"
                 f" {mean([r['tests_modified'] for r in rs]):.2f} | {mean([r['verified_last'] for r in rs]):.0%} |"
                 f" {mean([r['repeat_calls'] for r in rs]):.1f} | {mean([r['lines_added'] for r in rs]):.0f} |"
                 f" {sum(not r['audit_clean'] for r in rs)}/{len(rs)} |")

    L += ["\n## Where the tokens went (mean per run)\n",
          "| arm | out:reasoning | out:answer-text | out:tool/code | in:fresh | in:cache-write | in:cache-read |"
          " tool-result chars | first-request ctx | turns | wall s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        rs = [r for r in rows if r["arm"] == a]
        c = {k: mean([r["cats"].get(k, 0) for r in rs]) for k in
             ["out_reasoning", "out_text", "out_tool", "in_fresh", "in_cache_write", "in_cache_read"]}
        out["arms"][a]["cats"] = c
        out["arms"][a].update(turns=mean([r["num_turns"] for r in rs]), wall=mean([r["duration_s"] for r in rs]),
                              toolres=mean([r["tool_result_chars"] for r in rs]),
                              first_ctx=mean([r["first_msg_context_tokens"] for r in rs]))
        L.append("| " + a + " | " + " | ".join(fmt_k(c[k]) for k in c) +
                 f" | {fmt_k(out['arms'][a]['toolres'])} | {fmt_k(out['arms'][a]['first_ctx'])} |"
                 f" {out['arms'][a]['turns']:.0f} | {out['arms'][a]['wall']:.0f} |")

    L += ["\n## Pass counts per task\n", "| task | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for t in frozen:
        L.append(f"| {t} | " + " | ".join(
            f"{sum(P[a][t])}/{len(P[a][t])}" if P[a].get(t) else "—" for a in arms) + " |")

    flagged = [r for r in rows if not r["audit_clean"]]
    if flagged:
        L += ["\n## Audit flags (read the transcript before trusting these runs)\n"]
        for r in flagged:
            L.append(f"- {r['task']} / {r['arm']} / {r['trial']}: " +
                     "; ".join(f"{k}: {v[0][:140]}" for k, v in r["audit"].items()))
    L += ["\n## Caveats\n",
          "- 30 runs per arm detects pass-rate differences of roughly 20 points; it cannot certify a 5-point loss.",
          "- CIs are clustered bootstraps over tasks; with 10 tasks they are wide by construction.",
          "- The reasoning/text/tool split of output tokens is derived (see analyze.py); totals are exact.",
          "- Native macOS environments verified against gold patches, not the official Docker images:"
          " do not quote these pass rates as SWE-bench scores."]
    md = "\n".join(L)
    open(os.path.join(ROOT, "results", "summary-v2.md"), "w").write(md)
    json.dump({"summary": out, "runs": [{k: v for k, v in r.items() if k != "tools"} for r in rows]},
              open(os.path.join(ROOT, "results", "results-v2.json"), "w"), indent=1)
    print(md)


if __name__ == "__main__":
    rows = collect()
    if not rows:
        sys.exit("no gated v2 runs yet")
    {"calib": cmd_calib, "report": cmd_report}[sys.argv[1] if len(sys.argv) > 1 else "calib"](rows)
