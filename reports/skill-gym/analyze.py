#!/usr/bin/env python3
"""skill-gym analyzer — token decomposition + report.

Reads results/runs/<phase>/<task>/<condition>/t<N>/{events.jsonl,gate.json,meta.json}
Writes results/results.json and results/summary.md.

Token accounting:
  EXACT (from API usage fields): input_tokens (uncached), cache_creation,
  cache_read, output_tokens, total_cost_usd, num_turns, duration.
  DERIVED (within each assistant message): output split into
  text / tool_use / reasoning. text+tool estimated from visible chars
  (CHARS_PER_TOK), capped at the message's exact output_tokens; reasoning is
  the residual, so hidden/summarized thinking is still counted. Ratio error
  is identical across conditions and cancels in comparisons.
"""
import glob
import json
import os
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "results", "runs")
CHARS_PER_TOK = 3.8

# $/MTok: (input, output); cache write = 1.25x input, cache read = 0.1x input
PRICES = {"opus": (5.0, 25.0), "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0), "fable": (10.0, 50.0)}


def price_for(model):
    m = (model or "").lower()
    for k, v in PRICES.items():
        if k in m:
            return v
    return PRICES["opus"]


def block_chars(block):
    t = block.get("type")
    if t == "text":
        return "text", len(block.get("text", ""))
    if t == "thinking":
        return "thinking", len(block.get("thinking", "") or "")
    if t == "tool_use":
        return "tool:" + block.get("name", "?"), len(json.dumps(block.get("input", {})))
    return None, 0


def tool_result_chars(content):
    if isinstance(content, str):
        return len(content)
    n = 0
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "tool_result":
                    n += tool_result_chars(b.get("content", ""))
                elif b.get("type") == "text":
                    n += len(b.get("text", ""))
    return n


def parse_run(cell):
    ev_path = os.path.join(cell, "events.jsonl")
    if not os.path.exists(ev_path):
        return None
    # The CLI emits one assistant event per content BLOCK (same message.id
    # repeated); usage on those events is an early-stream snapshot whose
    # output_tokens is not final. So: input classes come from per-id usage
    # (constant across an id's events), output total comes from the result
    # event (authoritative), and the text/tool/reasoning split is anchored
    # at run level.
    msg_usage = {}      # message.id -> usage dict (first seen)
    order = []
    blocks = []         # all content blocks in arrival order
    seen_tool_ids = set()
    result = None
    model = None
    toolres_chars = 0
    for line in open(ev_path):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            model = ev.get("model")
        elif t == "assistant":
            m = ev.get("message", {})
            mid = m.get("id")
            if mid not in msg_usage:
                order.append(mid)
                msg_usage[mid] = m.get("usage") or {}
            for b in m.get("content", []):
                if b.get("type") == "tool_use":
                    bid = b.get("id")
                    if bid in seen_tool_ids:
                        continue
                    seen_tool_ids.add(bid)
                blocks.append(b)
        elif t == "user":
            m = ev.get("message", {})
            toolres_chars += tool_result_chars(m.get("content", []))
        elif t == "result":
            result = ev
    if result is None:
        return None

    cats = defaultdict(float)
    tools_count = defaultdict(int)
    n_tool_calls = 0
    first_msg_context = None
    for mid in order:
        u = msg_usage[mid]
        inp = u.get("input_tokens", 0) or 0
        cw = u.get("cache_creation_input_tokens", 0) or 0
        cr = u.get("cache_read_input_tokens", 0) or 0
        cats["in_fresh"] += inp
        cats["in_cache_write"] += cw
        cats["in_cache_read"] += cr
        if first_msg_context is None:
            first_msg_context = inp + cw + cr

    text_c = tool_c = think_c = 0
    for b in blocks:
        kind, c = block_chars(b)
        if kind == "text":
            text_c += c
        elif kind == "thinking":
            think_c += c
        elif kind and kind.startswith("tool:"):
            tool_c += c
            tools_count[kind[5:]] += 1
            n_tool_calls += 1

    ru = result.get("usage") or {}
    out_total = ru.get("output_tokens", 0) or 0
    text_est = text_c / CHARS_PER_TOK
    tool_est = tool_c / CHARS_PER_TOK
    if text_est + tool_est > out_total and (text_est + tool_est) > 0:
        scale = out_total / (text_est + tool_est)
        text_est *= scale
        tool_est *= scale
    cats["out_text"] = text_est
    cats["out_tool"] = tool_est
    cats["out_reasoning"] = max(0.0, out_total - text_est - tool_est)
    cats["out_total"] = out_total
    cats["thinking_chars_visible"] = think_c

    # cross-check the input side: per-id sums vs the result event totals
    mismatch = None
    r_in = (ru.get("input_tokens", 0) or 0)
    if r_in and abs(r_in - cats["in_fresh"]) > max(50, 0.10 * r_in):
        mismatch = f"in_fresh per-msg={cats['in_fresh']:.0f} vs result={r_in}"

    inp_price, out_price = price_for(model)
    est_cost = (
        cats["in_fresh"] / 1e6 * inp_price
        + cats["in_cache_write"] / 1e6 * inp_price * 1.25
        + cats["in_cache_read"] / 1e6 * inp_price * 0.10
        + cats["out_total"] / 1e6 * out_price
    )

    gate = {}
    gp = os.path.join(cell, "gate.json")
    if os.path.exists(gp):
        gate = json.load(open(gp))
    meta = {}
    mp = os.path.join(cell, "meta.json")
    if os.path.exists(mp):
        meta = json.load(open(mp))

    return {
        "model": model,
        "passed": bool(gate.get("passed")),
        "gate_detail": gate.get("detail", ""),
        "cost_usd": result.get("total_cost_usd"),
        "est_cost_usd": round(est_cost, 4),
        "num_turns": result.get("num_turns"),
        "duration_s": round((result.get("duration_ms") or 0) / 1000, 1),
        "wall_s": meta.get("wall_s"),
        "n_tool_calls": n_tool_calls,
        "tools": dict(tools_count),
        "tool_result_chars": toolres_chars,
        "first_msg_context_tokens": first_msg_context,
        "mismatch": mismatch,
        "cats": {k: round(v, 1) for k, v in cats.items()},
    }


def collect(phase):
    out = []
    for cell in sorted(glob.glob(os.path.join(RUNS, phase, "*", "*", "t*"))):
        parts = cell.split(os.sep)
        trial, cond, task = parts[-1], parts[-2], parts[-3]
        r = parse_run(cell)
        if r:
            r.update({"task": task, "condition": cond, "trial": trial})
            out.append(r)
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def agg(runs):
    """(task, condition) -> aggregated metrics"""
    g = defaultdict(list)
    for r in runs:
        g[(r["task"], r["condition"])].append(r)
    out = {}
    for key, rs in g.items():
        cats = {c: mean([r["cats"].get(c, 0) for r in rs]) for c in
                ["in_fresh", "in_cache_write", "in_cache_read",
                 "out_reasoning", "out_text", "out_tool", "out_total"]}
        out[key] = {
            "n": len(rs),
            "solved": sum(1 for r in rs if r["passed"]),
            "cats": cats,
            "cost": mean([r["cost_usd"] for r in rs]),
            "est_cost": mean([r["est_cost_usd"] for r in rs]),
            "turns": mean([r["num_turns"] for r in rs]),
            "tool_calls": mean([r["n_tool_calls"] for r in rs]),
            "duration_s": mean([r["duration_s"] for r in rs]),
            "toolres_chars": mean([r["tool_result_chars"] for r in rs]),
            "first_ctx": mean([r["first_msg_context_tokens"] for r in rs]),
            "runs": rs,
        }
    return out


def pct(new, base):
    if not base:
        return "—"
    d = (new - base) / base * 100
    return f"{d:+.0f}%"


def fmt_k(x):
    return f"{x/1000:.1f}k" if x >= 1000 else f"{x:.0f}"


def render(phase, runs, aggd):
    tasks = sorted({t for t, _ in aggd})
    conds = [c for c in ["baseline", "caveman", "headroom", "both"]
             if any(c == cc for _, cc in aggd)]
    models = sorted({r["model"] for r in runs if r["model"]})
    L = []
    L.append(f"# skill-gym results — phase `{phase}`")
    L.append(f"\n_Generated {time.strftime('%Y-%m-%d %H:%M')}; model(s): {', '.join(models)};"
             f" {len(runs)} runs. Prices used for est-cost: per-model table in analyze.py._\n")

    # headline: per condition across all tasks
    L.append("## Headline — per condition (all tasks)\n")
    L.append("| condition | solved | est $/run | **est $/solved** | output tok/run | Δ out |"
             " cache-read tok/run | Δ | wall s/run |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    base_tot = {}
    for cond in conds:
        rows = [aggd[(t, cond)] for t in tasks if (t, cond) in aggd]
        tot = {
            "solved": sum(r["solved"] for r in rows),
            "n": sum(r["n"] for r in rows),
            "est_cost": mean([r["est_cost"] for r in rows]),
            "out": mean([r["cats"]["out_total"] for r in rows]),
            "cache_r": mean([r["cats"]["in_cache_read"] for r in rows]),
            "dur": mean([r["duration_s"] for r in rows]),
        }
        tot["per_solved"] = (tot["est_cost"] * tot["n"] / tot["solved"]) if tot["solved"] else float("inf")
        if cond == "baseline":
            base_tot = tot
        L.append(
            f"| {cond} | {tot['solved']}/{tot['n']} | {tot['est_cost']:.3f} |"
            f" **{tot['per_solved']:.3f}** ({pct(tot['per_solved'], base_tot.get('per_solved'))}) |"
            f" {fmt_k(tot['out'])} | {pct(tot['out'], base_tot.get('out'))} |"
            f" {fmt_k(tot['cache_r'])} | {pct(tot['cache_r'], base_tot.get('cache_r'))} |"
            f" {tot['dur']:.0f} |"
        )

    # category decomposition
    L.append("\n## Where the tokens went (mean per run, across tasks)\n")
    L.append("| condition | out:reasoning | out:answer-text | out:tool/code | in:fresh |"
             " in:cache-write | in:cache-read | tool-result chars fed back |")
    L.append("|---|---|---|---|---|---|---|---|")
    for cond in conds:
        rows = [aggd[(t, cond)] for t in tasks if (t, cond) in aggd]
        c = {k: mean([r["cats"][k] for r in rows]) for k in
             ["out_reasoning", "out_text", "out_tool", "in_fresh", "in_cache_write", "in_cache_read"]}
        trc = mean([r["toolres_chars"] for r in rows])
        L.append(f"| {cond} | {fmt_k(c['out_reasoning'])} | {fmt_k(c['out_text'])} |"
                 f" {fmt_k(c['out_tool'])} | {fmt_k(c['in_fresh'])} | {fmt_k(c['in_cache_write'])} |"
                 f" {fmt_k(c['in_cache_read'])} | {fmt_k(trc)} |")

    # per-task tables
    L.append("\n## Per task\n")
    for t in tasks:
        L.append(f"### {t}\n")
        L.append("| condition | n | solved | est $ | turns | tool calls | dur s |"
                 " out total | reasoning | text | tool | in fresh | cache r | first-ctx |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for cond in conds:
            if (t, cond) not in aggd:
                continue
            a = aggd[(t, cond)]
            c = a["cats"]
            L.append(
                f"| {cond} | {a['n']} | {a['solved']} | {a['est_cost']:.3f} | {a['turns']:.0f} |"
                f" {a['tool_calls']:.0f} | {a['duration_s']:.0f} | {fmt_k(c['out_total'])} |"
                f" {fmt_k(c['out_reasoning'])} | {fmt_k(c['out_text'])} | {fmt_k(c['out_tool'])} |"
                f" {fmt_k(c['in_fresh'])} | {fmt_k(c['in_cache_read'])} | {fmt_k(a['first_ctx'])} |"
            )
        L.append("")

    # per-run detail for variance eyeballing
    L.append("## Per-run detail\n")
    L.append("| task | condition | trial | pass | est $ | out tok | in fresh | cache r |"
             " turns | dur s | note |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in runs:
        c = r["cats"]
        note = r["mismatch"] or ""
        L.append(f"| {r['task']} | {r['condition']} | {r['trial']} |"
                 f" {'✅' if r['passed'] else '❌'} | {r['est_cost_usd']:.3f} |"
                 f" {fmt_k(c['out_total'])} | {fmt_k(c['in_fresh'])} |"
                 f" {fmt_k(c['in_cache_read'])} | {r['num_turns']} | {r['duration_s']} | {note} |")

    L.append("\n## Caveats\n")
    L.append("- output split (reasoning/text/tool) is derived: text+tool estimated from visible"
             " chars at ~3.8 chars/tok, anchored to the exact per-message output_tokens;"
             " reasoning is the residual. Exact totals; approximate split.")
    L.append("- with <3 trials, treat deltas smaller than ~15% as noise.")
    L.append("- est-cost uses public per-MTok prices; subscription runs bill usage, not dollars.")
    return "\n".join(L)


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    runs = collect(phase)
    if not runs:
        sys.exit(f"no completed runs found under results/runs/{phase}/")
    aggd = agg(runs)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "results.json"), "w") as f:
        json.dump(runs, f, indent=1)
    md = render(phase, runs, aggd)
    out = os.path.join(ROOT, "results", f"summary-{phase}.md")
    with open(out, "w") as f:
        f.write(md)
    print(md)
    print(f"\nwritten: {out} and results/results.json")
