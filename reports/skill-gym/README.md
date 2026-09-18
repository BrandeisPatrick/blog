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

## v2 — tasks that can move, more tools (in progress)

v1's verdict was a tie on quality because its tasks could not show anything else: the
three SWE-bench tasks are solved by 7–9 of 10 public frontier agents, and the two
failing spreadsheet tasks failed identically everywhere over a blank-vs-`#N/A`
convention. [`PLAN.md`](PLAN.md) is the v2 design; what changed in the harness:

| | v1 | v2 |
|---|---|---|
| tasks | 7, picked by hand | 19 SWE-bench Verified candidates in the 20–70% band of public frontier results, then **calibrated**: baseline × 3, keep the 10 that pass sometimes but not always; list frozen before any tool runs |
| model | `opus` alias (resolved to `claude-opus-4-8`) | `claude-opus-5` pinned, `--effort xhigh` |
| arms | baseline · caveman · headroom · both | baseline · caveman · **ponytail** · **rtk** · headroom · **effort-high** · **effort-low** (no stacks) |
| quality | one bit per run | resolved + partial credit + P2P regressions + tests-after-last-edit + repeated calls + patch size |
| env recipes | hand-written | ported from the official SWE-bench specs, `--exclude-newer 2024-08-01`, and **verified against the gold patch** (`bin/verify_swebench.py`): red at base, green with the reference fix, in this environment |
| statistics | means | task-clustered bootstrap CIs, task-paired deltas, sign test |

```bash
python3 fetch_tasks.py swebench --gold      # pin instances (+ answer keys, for verification only)
for t in tasks/swebench/*; do python3 bin/verify_swebench.py "$(basename $t)"; done
rm -rf .cache/gold                          # the answer key must not be on disk while agents run
sh bin/fetch_rtk.sh                         # pinned rtk binary, checksum-verified
python3 gym.py run --phase calib --jobs 2   # 19 tasks x baseline x 3
python3 analyze_v2.py calib                 # calibration table + tasks/v2_frozen.json
python3 gym.py run --phase v2 --jobs 2      # 5 treatment arms on the frozen tasks
python3 gym.py run --phase v2-high --jobs 2 # second native yardstick
python3 analyze_v2.py report
```

### Four leaks v2 had to close before its first real run

Opus 5 at `xhigh` is resourceful, and a benchmark it can shortcut measures nothing.

1. **Account connectors.** One smoke run in two loaded the account's claude.ai MCP
   connectors (Drive, Calendar, a brokerage) into the nested agent: ~75k tokens of tool
   schemas, and live account access under `--dangerously-skip-permissions`. Now
   `--strict-mcp-config`, and the runner refuses to gate any run whose init event shows a
   tool or MCP server beyond the pinned six.
2. **Future commits.** A plain clone carries every branch and tag, so `git log --all`
   contains the real fix. Workspaces now fetch only the base commit's ancestry, plus the
   tags that already precede it (setuptools_scm needs them).
3. **The released fix.** The first calibration run did
   `pip download pylint==2.11.1 --no-binary :all:` and diffed the fixed release against
   its checkout. The agent's shell is now offline (proxy variables aimed at a dead port,
   `NO_PROXY` for the API), the prompt forbids consulting other copies, and every run is
   audited for network, bypass and outside-the-workspace lookups (`audit` in `gate.json`).
4. **The harness itself.** v1 workspaces sat inside this tree, next to
   `tasks/*/instance.json` — which holds the held-out tests — under a path that named the
   condition. v2 workspaces live under `~/Library/Caches/pyws/<opaque id>/`, the agent's
   environment no longer points here, and gold patches are deleted before agents run.

And one bug that would have stolen a verdict, as the stale-bytecode one nearly did in v1:
with two runs in parallel, **every pytest-repo task failed its gate** in the first
calibration round — including a patch byte-identical to the gold fix (0/10 target tests,
16/16 "regressions"). pytest garbage-collects its numbered temp dirs under
`$TMPDIR/pytest-of-<user>/`; concurrent sessions of one user race on that cleanup, and
pytest's own suite escalates the resulting `rm_rf` warning to an error. Every agent and
every gate now gets a private `TMPDIR`; re-gating the same patch passed 10/10 with no
regressions (`python3 gym.py regate <task>/<arm>/t<N>` rebuilds a workspace from the
saved `patch.diff` and scores it again). The three affected runs were discarded and
re-run, since the agents had seen the spurious errors too.

Two things the host machine taught us. **Crash dialogs:** left to itself `uv` builds 3.9
environments on Xcode's Python, an app bundle; pytest's suite aborts subprocesses on
purpose (faulthandler tests), and every abort of an app bundle raises a "Python quit
unexpectedly" dialog — 29 on the author's screen before `UV_PYTHON_PREFERENCE=only-managed`
went in. All 19 environments were re-verified on the managed interpreter (3.9.25); 13
baseline runs scored before the switch ran on Xcode's 3.9.6 and are kept (`venv_python`
in `meta.json` from then on). **Disk:** the host had ~4 GB free, so the runner refuses to
start a run below 2 GB free, aborts below 1 GB, and removes workspaces with a
permission-fixing delete — pytest's own permission tests leave `chmod 0` directories that
a plain `rmtree` silently skips.

Host footprint in v2: `~/.claude/.ponytail-active` and `.ponytail-statusline-nudged`
(ponytail's hook; removed after each run), `~/Library/Application Support/rtk/` (rtk's
command history), `~/Library/Caches/pyws/` (workspaces; emptied after each gate).

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
- ponytail © Dietrich Gebert (MIT), vendored at v4.10.0 under `vendor/ponytail` (see `PINNED`)
- rtk © rtk-ai (Apache-2.0), v0.49.0 release binary fetched by `bin/fetch_rtk.sh`;
  only its generated `RTK.md` is vendored
- headroom © Headroom Labs, installed from PyPI into `.venv`
- SWE-bench Verified (Princeton NLP / OpenAI-verified subset) via HuggingFace
- SpreadsheetBench (RUC KBReasoning); `bin/ssb_check.py` ports its value-comparison
  logic — credit to the original authors
