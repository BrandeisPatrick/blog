# skill-gym

Sandbox-isolated benchmark answering one question: **which Claude Code token-saving
add-on actually saves tokens, which *kind* of tokens, and at what quality cost?**

First matchup: **caveman** vs **headroom** — which turn out to attack opposite sides
of the ledger:

| | [caveman](https://github.com/JuliusBrussee/caveman) | [headroom](https://github.com/headroomlabs-ai/headroom) |
|---|---|---|
| what it is | Claude Code plugin/skill: terse caveman-speak replies | local compression proxy: rewrites requests in flight |
| attacks | **output** tokens (answer prose) | **input** tokens (tool results, logs, JSON, history) |
| claimed | ~65% output reduction (chat-style) | 20% (coding) … 60–95% (JSON/logs) |
| cost | +1–1.5k input tokens/turn of skill prompt | proxy hop latency |

Conditions: `baseline` · `caveman` · `headroom` · `both` (stacked).

## Tasks — lifted from real benchmarks, not toys

| ID | Source | Task | Gate (deterministic, runs outside the agent) |
|---|---|---|---|
| C1 | SWE-bench Verified | `pylint-dev__pylint-6903` | official FAIL_TO_PASS green, PASS_TO_PASS stay green, tests untouched |
| C2 | SWE-bench Verified | `pytest-dev__pytest-7490` | same |
| C3 | SWE-bench Verified | `sphinx-doc__sphinx-10323` (verbose-output repo → input pressure) | same |
| C4 | docwork | contributor onboarding doc on the pylint checkout (output pole) | keyword rubric vs real API names |
| O1 | SpreadsheetBench | `59055` — lookup/match formula task | cell-level checker at answer_position, 3/3 workbooks |
| O2 | SpreadsheetBench | `13894` — unique-code formula task | same |
| O3 | SpreadsheetBench | `55392` — 2.7MB workbooks (input pole) | same |

Quality is first-class: the headline metric is **tokens per solved task** — savings
that break the fix are worthless.

## How measurement works

Every run is a nested `claude -p --output-format stream-json` whose full event log
is captured. From it:

- **Exact** (API `usage` fields, per assistant message + final result event):
  uncached input, cache writes, cache reads, output tokens, cost, turns, duration.
- **Derived split of output** per message: `text` and `tool_use` estimated from
  visible chars (~3.8 chars/tok), anchored to the exact per-message
  `output_tokens`; **reasoning = the residual** (robust to hidden/summarized
  thinking). Exact totals, approximate split; ratio error cancels across
  conditions.
- Extras: per-tool output split (Edit/Write ≈ generated code), tool_result chars
  fed back (headroom's target), first-request context (skill overhead), turns,
  wall time.

`analyze.py` cross-checks per-message sums against the result event and flags
mismatches.

## Isolation model

| Layer | Mechanism |
|---|---|
| filesystem | fresh throwaway workspace per run under `results/runs/…`; agent cwd is the sandbox |
| config | `--setting-sources ""` → no user/project settings, hooks, plugins, model prefs |
| context | fresh dir ⇒ no CLAUDE.md, no auto-memory; `--no-session-persistence` ⇒ no `/resume` pollution |
| tools | pinned `--tools "Bash,Edit,Write,Read,Grep,Glob"`, no web, no MCP |
| condition injection | caveman via session-scoped `--plugin-dir` (never installed); headroom via per-subprocess `ANTHROPIC_BASE_URL` |
| env | child env scrubbed of `ANTHROPIC*`/`CLAUDE*`/`HEADROOM*`; caches redirected into `.cache/` |
| caps | `--max-turns`, per-kind wall timeouts, rate-limit backoff + resume |

Host footprint is this directory only (`.venv`, `.cache` for HF weights / uv / repo
mirrors, `results/`), plus one caveat: caveman's SessionStart hook writes
`~/.claude/.caveman-active` (a 20-byte flag, inert without the plugin); the runner
deletes it after each caveman run. Auth is your normal keychain OAuth —
runs bill your subscription; no API keys anywhere.

## Run it

```bash
python3 fetch_tasks.py            # pin/refresh benchmark instances
python3 gym.py smoke              # auth + activation checks (haiku, tiny)
python3 gym.py run --phase pilot  # 3 conditions × (C1,O1) × 1 trial, opus
python3 gym.py run --phase full   # 4 conditions × 7 tasks × 2 trials, opus
python3 analyze.py pilot          # → results/summary-pilot.md + results.json
```

Custom slices: `python3 gym.py run --conditions baseline,caveman --tasks C4 --trials 3 --model sonnet`.

Runs are resumable (completed cells skipped). Interleaved condition order within
each task keeps prompt-cache warmth fair.

## Caveats

- N is small; treat deltas under ~15% as noise unless trials agree.
- Output split is derived (see above); input classes and totals are exact.
- SWE-bench envs are recreated natively (no Docker) — fine for token measurement;
  don't quote the pass rates as official SWE-bench scores.
- Headroom compresses between CLI and API, so event logs show original tool
  results while `usage` shows compressed input — that difference is the measurement.
- `both` tests composition; savings are not assumed additive.

## Credits / licenses

- caveman © Julius Brussee, vendored at pinned commit under `vendor/` (see its LICENSE)
- headroom © Headroom Labs, installed from PyPI into `.venv`
- SWE-bench Verified (Princeton NLP / OpenAI-verified subset) via HuggingFace
- SpreadsheetBench (RUC KBReasoning); `bin/ssb_check.py` ports its value-comparison
  logic — credit to the original authors
