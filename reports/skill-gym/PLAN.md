# skill-gym v2 — evaluation plan

_Drafted 2026-09-18, approved the same day. Decisions taken with the author: no
combined "stack" arm; benchmark model is **Opus 5 at `xhigh` effort**. Status at the
time of writing: all 19 candidate environments verified against their gold patches
(§2); calibration not yet run. Task list freezes — and this file gets committed —
before any treatment arm runs._

## 1. What v1 could not see

v1 (56 Opus runs) found every condition solving the same 10 of 14 runs. That is not
evidence that token savers are free; it is a benchmark with no resolution:

| v1 task | how often 10 public frontier agents solve it | what that means |
|---|---|---|
| C1 `pylint-6903` | 9/10 | ceiling — everyone passes, nothing can show |
| C2 `pytest-7490` | 7/10 | near ceiling |
| C3 `sphinx-10323` | 9/10 | ceiling |
| O1, O3 spreadsheets | failed in all 4 conditions for the same reason (blank vs `#N/A`) | floor — a grading convention, not difficulty |

The "hard tier" pinned in August (H1–H4, picked by SWE-bench's human-time labels) has
the opposite problem: those tasks are solved by 2/10, 2/10, **0/10 and 0/10** of the
same agents. Running them would produce 0/2 everywhere — a floor instead of a ceiling.

**The goal is not harder tasks, it is discriminating tasks**: ones the baseline solves
*some* of the time, so that a tool which costs capability moves the pass rate.

## 2. Tasks

### Tier A — SWE-bench Verified, selected by measured difficulty (main evidence)

Difficulty prior = fraction of 10 public frontier submissions on the SWE-bench
leaderboard that resolve each instance (`swe-bench/experiments`: OpenHands, Sonar and
live-SWE-agent with Opus 4.5; mini-SWE-agent with Opus 4.5-high, Opus 4.6,
Sonnet 4.5-high, GPT-5.2-high, GLM-5, Kimi K2.5, Gemini 3.5 Flash).

Across all 500 instances: 57 never solved · 29 under 30% · **66 in the 30–70% band** ·
348 above 70%. Restricted to repos this harness can build natively (pure Python,
pytest-driven), the candidates in the 20–70% band are:

| repo | candidates (solved by n/10) |
|---|---|
| pylint | `4970` (3) · `6528` (4) · `7277` (4) · `6386` (5) · `8898` (2) |
| pytest | `5787` (5) · `10356` (2) · `7205` (7) |
| sphinx | `8548` (4) · `8056` (6) · `8595` (6) · `9711` (6) · `10435` (2) · `10673` (7) |
| requests | `5414` (6) · `6028` (6) · `2931` (7) |
| xarray | `6938` (4) · `4687` (5) |

19 candidates. On these, mini-SWE-agent + Opus 4.6 resolves 7/19 and Opus 4.5-high
9/19 — the middle of the range, which is where a benchmark has the most resolution.
They cost ~1.9× the v1 tasks in that public data ($0.66 vs $0.35 mean).

**Calibration step (ours, because the public data is from older models):** run
baseline × 3 on all 19 with the pinned model. Keep the 10 tasks whose baseline pass
rate is strictly between 0 and 1. If fewer than 10 qualify, top up with the
always-pass tasks that took the most turns. The task list is then frozen and committed
*before any treatment arm runs*.

**Amendment, 2026-09-18, after calibration round 1 and before any reserve-pool run.**
Opus 5 at `xhigh` passed **18 of 19** on the first try: public priors from Opus 4.5-era
agents overstate the difficulty for this configuration, and the pool sits at the
ceiling again. With the author's agreement the remaining calibration budget moves:

- A **reserve pool** of 17 instances solved by at most 1 of the 10 public submissions
  was pinned; 14 verify natively (dropped: `pylint-4661`, `sphinx-10614`, `sphinx-11510`
  — their gold patches do not go green in this environment). Each gets 2 baseline trials.
- In the main pool, second trials go only to tasks whose first run failed or took the
  most turns (top 9); the rest are treated as ceiling and not re-run.
- **Selection rule (replaces the one above):** a task is *in band* if the baseline passes
  some but not all of its trials — with two trials, 1/2 is in band for certain. Take
  in-band tasks first (nearest 50%, then most turns). If fewer than 10, top up with
  always-pass tasks that took the most turns: they have the most to lose to a token
  saver. Never-pass tasks are dropped. Selected tasks then get a third baseline trial.
- `requests-6028` is excluded whatever it scores: the bug is about proxy handling, and
  the offline shell works by setting proxy variables.

**Frozen 2026-09-18 17:41** after 58 baseline runs (`tasks/v2_frozen.json`,
`results/summary-v2-calib.md`): 3 tasks in band (`xarray-6992`, `sphinx-7748`,
`xarray-7229`, each 1/2), 17 always-pass, 5 never-pass (dropped). The seven top-ups are
the always-pass tasks with the most turns: `sphinx-10673`, `sphinx-8548`, `pylint-6386`,
`sphinx-9461`, `pylint-4970`, `sphinx-9229`, `pylint-4551`. Opus 5 at `xhigh` turned out
close to deterministic per task — almost everything is 2/2 or 0/2 — so the main test is
whether a tool makes an always-solved hard task start failing. The baseline's third trial
runs interleaved with the tool arms.

sympy (11 in band) and django (26) are excluded for now: their test runners are not
pytest-ID based and would need a gate adapter.

### Tier B — stress tasks aimed at what each tool deletes (second milestone)

Hand-built on the existing checkouts, deterministic gates, reported separately and
never pooled with Tier A.

| task | built to stress | design | gate |
|---|---|---|---|
| B1 needle in the log | rtk, headroom, pxpipe | the only clue to the bug is one line deep inside a multi-thousand-line test log | hidden test |
| B2 exact transcription | pxpipe, headroom | values (hashes, versions, identifiers) must be copied from tool output into config | exact match |
| B3 under-building trap | ponytail | small feature whose spec lists edge cases (empty input, unicode, invalid values) | ~20 hidden edge-case tests, graded 0–1 |
| B4 prose is the deliverable | caveman | root-cause report / migration guide | coverage of ~20 required facts, graded 0–1 |

## 3. Arms

One arm per class of token, plus native yardsticks. Everything is injected per run;
nothing is installed globally (v1's isolation model is kept).

**Model: `claude-opus-5` at `--effort xhigh`, for the baseline and every tool arm.**
Extra-high effort is the most token-hungry way to run Opus 5 — known to be redundant —
so it is where a token saver has the most to cut and the most to break.

| # | arm | tokens it attacks | how it is injected | failure mode to look for |
|---|---|---|---|---|
| 0 | baseline | — | `claude-opus-5`, `--effort xhigh` | — |
| 1 | caveman | output · answer prose | `--plugin-dir vendor/caveman` (as v1) | facts dropped from written deliverables |
| 2 | ponytail (full) | output · generated code | `--plugin-dir vendor/ponytail` + `PONYTAIL_DEFAULT_MODE`; smoke test asserts the SessionStart hook fired (it never self-activates without it) | under-building: missing edge cases, validation |
| 3 | rtk | input · shell output | `--settings` JSON carrying the PreToolUse hook (`rtk hook claude`); binary under `.cache/bin` | decisive line hidden → extra turns, re-reads, wrong fix |
| 4 | headroom | input · whole request at the API boundary | `ANTHROPIC_BASE_URL` proxy (as v1) | lossy tool results / history |
| 5 | effort-high | native · reasoning | `--effort high` (one notch down) | **yardstick**: the free way to spend fewer tokens |
| 6 | effort-low | native · reasoning | `--effort low` | **yardstick**, far end of the dial |

No combined "stack" arm (v1's `both` is dropped too): every tool is measured on its
own, so each effect has one cause and the run budget goes to trials, not combinations.

Optional: a Sonnet arm (one more point on the yardstick curve);
`pxpipe` (renders context as PNGs — proxy; risk: misread exact strings);
`context-mode` (MCP sandbox — changes the toolset, so it breaks the same-tools
control and needs its own baseline).

Excluded: claude-mem, OpenWiki (cross-session memory — invisible in isolated one-shot
runs); Graphify, Serena, claude-context (retrieval/indexing — they change what gets
read rather than compress it; closer to the Devin-vs-Cursor report's question).

## 4. Measurement

**Cost side — exact, from API `usage` events (as v1):** fresh input, cache writes,
cache reads, output; est. $; turns; wall time; output split into reasoning / answer
text / tool-code. New: lines of code written (ponytail's target), shell-output chars
before vs after (rtk's target), first-request context (each tool's prompt tax).

**Quality side — upgraded from one bit:**

| metric | what it catches |
|---|---|
| resolved (all FAIL_TO_PASS green, PASS_TO_PASS held, tests untouched) | the official verdict |
| partial credit: fraction of FAIL_TO_PASS passing, count of PASS_TO_PASS regressions | near-misses; more signal per run than pass/fail |
| verified-before-finish: did the agent run the relevant tests before stopping | process shortcuts a terse/lazy prompt may induce |
| re-read tax: repeated reads/commands after a compressed result | the rtk/headroom failure JetBrains measured as +13.8% turns |
| patch size vs the gold patch; files touched | over- and under-building |
| root-cause summary correct (blind LLM judge vs gold patch; secondary, labelled as judged) | what caveman compresses |

**Headline:**
1. Pass rate per arm with a bootstrap CI, and the task-paired difference vs baseline
   (paired bootstrap + sign test). Non-inferiority margin declared up front: −10 points.
2. Cost per solved task — v1's headline, now meaningful because pass rates can differ.
3. **The frontier plot**: x = cost per run relative to baseline, y = pass rate. The
   native arms (xhigh → high → low) trace what you get for free by turning a dial. An add-on above that line is a real efficiency gain; on it,
   it is equivalent to lowering effort; below it, it is worse than the free option.

**Power, stated honestly:** 10 tasks × 3 trials = 30 paired runs per arm detects
pass-rate drops of roughly 20 points or more. It cannot certify a 5-point loss; that
needs several hundred pairs (JetBrains reached the same conclusion at 80 tasks).
Partial credit and the cost metrics are more sensitive than pass/fail.

## 5. Harness

**Recommended: extend skill-gym** (native macOS, `uv` envs, nested `claude -p`,
subscription billing). Its per-class token ledger is the report's distinctive
measurement and its isolation model already works. Changes needed:

1. Arm injectors: `--plugin-dir`, `--settings` hooks, `--effort`, full model
   ID pinned (the `opus` alias has moved since v1).
2. Graded gates (§4) and a saved `patch.diff` per run.
3. Disk: this Mac has ~5.8 GB free. One prepared template workspace per task,
   APFS-cloned per run, deleted after the gate; keep only logs, patch and verdict.
4. `calibrate` phase + the freeze rule in §2.
5. Analysis: paired bootstrap, sign test, frontier plot, the new metrics.
6. Optional: two parallel slots to halve wall-clock.

**Not recommended now: Harbor + Docker** (JetBrains' setup). It would unlock
Terminal-Bench 2.0 and SkillsBench and make results directly comparable to theirs,
but it needs tens of GB of images, bills an API key inside containers instead of the
subscription, and rtk/proxy arms need extra plumbing there. Good candidate for a
later replication.

### Protocol, as frozen before the calibration that counts

Every arm shares all of this; an arm differs only in what it injects (§3).

- `claude -p --model claude-opus-5 --effort xhigh`, tools pinned to
  `Bash,Edit,Write,Read,Grep,Glob`, `--setting-sources ""`, `--strict-mcp-config`,
  `--no-session-persistence`, 120 turns / 60 min cap.
- One prompt per task for all arms: the issue text plus five rules (source only, no test
  edits, **work only from this checkout — no other copy or later version of the
  project**, verify before finishing, summarise the root cause).
- Workspace = the base commit's ancestry only (no future commits, only ancestor tags),
  venv built from the ported official recipe and **activated** on `PATH`, located under
  `~/Library/Caches/pyws/<opaque id>/`, shell offline.
- A run is gated only if its init event shows exactly the six pinned tools and no MCP
  server. Every run is audited for network, bypass and outside-workspace lookups; flagged
  runs are read by hand and reported, not silently kept.

An earlier calibration was started and **discarded after two runs** when the first one
fetched the fixed upstream release with `pip download` (README, "Four leaks"). Nothing
from it is used.

## 6. Budget

| stage | runs | est. API-equivalent | wall-clock (serial) |
|---|---|---|---|
| smoke (haiku, activation checks) | ~7 | < $1 | 10 min |
| calibration: 19 tasks × baseline × 3 | 57 | $60–85 | 4–5 h |
| matrix: 10 tasks × 6 treatment arms × 3 (baseline reuses calibration) | 180 | $200–270 | 10–18 h |
| Tier B (4 tasks × 7 arms × 3), later | 84 | $60–100 | 4–6 h |

These figures were estimated at default effort; `xhigh` reasons longer, so expect the
real numbers toward or above the top of each range. `effort-high` runs last, so it
can be cut without touching anything else.

Runs bill subscription usage, not dollars; the runner already backs off on usage
limits and resumes, so expect this to spread over several usage windows.

## 7. Third-party code this needs

| tool | source | pin |
|---|---|---|
| ponytail | `github.com/DietrichGebert/ponytail` (MIT), vendored like caveman | commit hash |
| rtk | `github.com/rtk-ai/rtk` release binary `rtk-aarch64-apple-darwin.tar.gz` (Apache-2.0), into `.cache/bin` | version + SHA-256 |
| headroom | PyPI, into `.venv` (as v1) | exact version |
| pxpipe (optional) | npm `pxpipe-proxy` | exact version |

The two proxies (headroom, pxpipe) sit between the CLI and the API and therefore see
the auth token on every request. Pin exact versions and read their header-handling
code before the first run.

## 8. Prior art

JetBrains ran caveman, rtk and ponytail through SkillsBench (Sonnet 5, 80–86 paired
tasks): caveman −8.5% code vs −65% advertised; rtk **+7.6% cost**; ponytail −10.3%
cost (p = 0.004); no quality difference detected in any — with the explicit caveat
that the run was not powered to prove equivalence. v2's contribution is the part
they left open: tasks chosen to sit where quality *can* move, stress tasks aimed at
each tool's blind spot, and a native-effort yardstick to compare against.
