# Devin vs Cursor — Comparison Test Plan

> Status: **DRAFT v2 — planning phase only.** Research pass complete (2026-08-04); no test runs yet.
> Research details: [research/cursor-semantic-layer.md](research/cursor-semantic-layer.md) · [research/devin-semantic-layer.md](research/devin-semantic-layer.md) · [research/benchmark-precedents.md](research/benchmark-precedents.md)

## 1. Goals

1. **Verdict:** which tool is better for real engineering work, with evidence.
2. **Deep dive:** understand each tool's **semantic layer** — how it indexes, retrieves, and "understands" a codebase.

Non-goal: comparing raw LLMs. This is a **product-level** comparison: semantic layer + agent harness + model, together.

**Why this is worth doing:** the research pass found *no rigorous quantitative head-to-head exists* — published comparisons are informal single-run tests, philosophy pieces, or roundups that misattribute foundation-model scores to the products. Even a small, controlled pilot would be ahead of everything published on this pairing. (Blog post candidate.)

## 2. Background: two opposite bets on the semantic layer

The research pass revealed the comparison is architecturally cleaner than expected — the two companies made **opposite bets**:

### 2.1 Cursor: trained embedding index + hybrid grep

- Local AST/syntactic chunking → **custom embedding model trained on agent session traces** (an LLM ranks which content would have helped at each step; embeddings align to that, not generic code similarity)
- **Merkle-tree sync** (SHA-256): only changed subtrees re-embed; client re-checks ~every 10 min; embeddings + obfuscated paths server-side, chunks encrypted with client keys (2026)
- Query time: semantic search + **Instant Grep** (custom engine, claims to beat ripgrep) + **Explore subagent** (own context, faster model, parallel search)
- Cursor's own eval: semantic search adds **~12.5% QA accuracy** over grep-only agents
- Levers for us: `.cursorignore` / `.cursorindexingignore`; must **pin model** (avoid Auto routing)

### 2.2 Devin: generated wiki + RL agentic search (explicitly anti-embedding)

- **Two different semantic layers depending on surface:**
  - **Devin Cloud**: repos auto-index "every couple hours" into **Devin Wiki** (architecture diagrams, source-linked pages; steerable via `.devin/wiki.json`) + **Knowledge** system (trigger-gated notes recalled mid-session) + undisclosed "advanced code search"
  - **Devin Desktop** (ex-Windsurf): local whole-codebase RAG index ("M-Query" retrieval, internals unpublished) increasingly routed through **Fast Context** — a subagent powered by **SWE-grep**, RL-trained retrieval models doing ≤8 parallel grep/read/glob calls/turn, ≤4 turns, precision-weighted reward, ~2,800 tok/s on Cerebras
- Cognition's published position (Riptide → SWE-grep): embedding search breaks down at scale; agentic/LLM search wins
- SWE-1.6/1.7 models are post-trained to delegate retrieval to Fast Context rather than explore sequentially
- Levers for us: `.devin/wiki.json`, Knowledge seeding — Devin's layer is *steerable* in ways Cursor's isn't

### 2.3 What prior comparisons did (and got wrong)

- **Trickle (Jul 2025)**: only real hands-on test — 4 tasks, single-run, informal. Cursor fast on routine work; Devin 15+ min and looping on complex debugging.
- **Builder.io**: philosophy only ("co-editing vs async handoff"), no metrics.
- **Comparison sites**: recycle stale pricing and misattribute model SWE-bench scores to products (e.g. crediting Cursor with Claude Opus 4.5's 80.9%). We will not repeat this mistake.
- **Answer.AI's Devin month (Jan 2025)**: 3/20 tasks usable — but that was Devin 1.x; the product has been rebuilt twice since.

## 3. Hypotheses (pre-registered, from the architecture)

Writing these down *before* running keeps us honest:

| # | Hypothesis | Derived from |
|---|-----------|--------------|
| H1 | Cursor wins **synonym/concept** probes (embeddings bridge vocabulary gaps; grep needs the right string) | Cursor semsearch training; SWE-grep is grep-based |
| H2 | Devin cites **fewer, more precise** files; Cursor higher recall on **split-logic** probes | SWE-grep's precision-weighted reward |
| H3 | Devin's **wiki goes stale** between reindex cycles and can mislead it; Cursor's ~10-min Merkle sync makes it fresher | Documented reindex cadences (~2h vs ~10min) |
| H4 | Devin wins **architecture-level** questions ("how does auth flow work here?") — the wiki pre-computes exactly this | Devin Wiki design |
| H5 | Cursor wins on **wall-clock** for interactive tasks; Devin more competitive on long autonomous tasks | Trickle findings; product shapes |
| H6 | Seeding Devin's Knowledge/wiki.json measurably improves its scores (no Cursor equivalent) | Knowledge system docs |

## 4. Test design

Two tracks, one shared **private, freshly written** trap repo (contamination control), identical prompts.

### Track A — Semantic layer probes (retrieval, known ground truth)

Trap repo ~40–60 files. Probe categories, now mapped to hypotheses:

| # | Probe | Tests | Hypothesis |
|---|-------|-------|------------|
| A1 | **Synonym trap** — code says `throttle`, ask about "rate limiting"; decoy `rate_limiter.py` does something else | Embedding vs string match | H1 |
| A2 | **Stale docs trap** — README contradicts code | Prose vs code as truth | — |
| A3 | **Split logic** — one behavior across 3 unrelated-named files | Multi-hop recall | H2 |
| A4 | **Dead ringer** — near-identical functions, one dead, one live | Call-graph vs text similarity | H2 |
| A5 | **Cross-language link** — YAML config drives Python behavior | Non-code indexing | — |
| A6 | **Impact question** — "what breaks if I change this enum?" | Reference tracing | H2 |
| A7 | **Recency probe** — ask about code added post-indexing, at T+2min and T+30min | Index freshness | H3 |
| A8 | **Wiki-staleness trap** (Devin-specific timing) — let wiki generate, change the code, ask a question the stale wiki answers wrongly | Does Devin re-ground in code? | H3 |
| A9 | **Architecture question** — "walk me through the request lifecycle" | Pre-computed understanding | H4 |

**Scoring** (borrowed from ContextBench + DeepCodeBench):
- **Retrieval**: file-level precision/recall/F1 vs ground-truth file set; decoy avoidance (binary)
- **Answer quality**: fact-recall — enumerate discrete facts in the gold answer, check each in the tool's answer
- **Hallucination count**: phantom files/APIs cited

### Track B — End-to-end tasks (does it ship?)

| # | Task | Tests |
|---|------|-------|
| B1 | Bug fix with failing test provided | Diagnosis + minimal change |
| B2 | Feature spanning 2–3 files | Planning + style consistency |
| B3 | Repo-wide rename/refactor (~15 touch points) | Whole-repo recall, nothing missed |

Tests must be strong enough to catch wrong fixes (SWE-bench lesson: weak tests pass bad patches). Scoring: tests pass (binary), rubric 1–5, wall time, $ cost, intervention count.

### Optional Track C — Steerability ablation (H6)

Re-run 3 probes on Devin with seeded Knowledge + `.devin/wiki.json` notes vs bare. Measures the value of Devin's steerable layer. Run only if pilot results are close.

### Run protocol

- Fresh session per task; identical prompts verbatim.
- **3 runs per task** (upgraded from 2 — the nondeterminism literature shows single/double runs can flip rankings). Report ranges, not points.
- **Pass 1** no hints (autonomy); **Pass 2** on failures, one standardized nudge (recoverability).
- **Setup parity**: let Cursor finish indexing; let Devin generate its wiki — each tool at its documented best before the clock starts.
- **Pin & record**: pin Cursor's model (no Auto); Devin picks internally — record what it used. Log product versions per run. Complete all runs in a **short window** (≤1 week) to dodge silent product updates.
- Log everything: transcripts, files cited/opened, diffs, timestamps, $ per task (accuracy-cost Pareto in the report, per "AI Agents That Matter").
- Trap repo stays **private forever** (never pushed public).

## 5. Deliverables

1. ✅ `research/` — semantic-layer writeups + methodology precedents (done, 2026-08-04)
2. `trap-repo/` — the testbed (build phase)
3. `tasks/` — prompts + ground-truth answer keys + fact lists for scoring
4. `results/` — transcripts, scores, cost log
5. `REPORT.md` — verdict + evidence (blog post candidate — this would genuinely be the first rigorous head-to-head)

## 6. Open decisions (need Patrick)

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Which Devin?** ← new, important | Cloud (wiki+knowledge, autonomous) vs Desktop (local RAG+Fast Context, IDE) vs both | **Cloud** for the flagship fight — it's "the Devin" people mean; Desktop as optional third arm later. Note they have different semantic layers. |
| Testbed language/domain | Python / TS / match your real work | Python web service + YAML config + small TS frontend (enables A5) |
| Verdict lens | Semantic layer vs end-to-end vs equal | Equal weight, two scored dimensions |
| Scale | Pilot: 9 probes + 3 tasks × 3 runs × 2 tools = **72 runs** | Pilot first; Track C and Desktop arm only if close |
| Accounts/budget | Devin Pro $20 (opaque allowance, may need top-ups) + Cursor Pro $20 (~$20 usage incl.) — **pilot ballpark $50–250 total** | You set up both accounts; I can't create accounts or enter payment |
| Claude Code as third arm? | Yes / No | **Yes** — same probes at marginal cost, and it's the no-index control group (pure agentic search, nothing pre-computed) |

## 7. Phases

1. **Planning** ✅ — this doc + research (done 2026-08-04)
2. **Build** — trap repo, prompts, answer keys + fact lists, scoring sheets
3. **Dry run** — neutral agent sanity-checks tasks are solvable/unambiguous
4. **Run** — 72 runs, ≤1 week window
5. **Score & report** — REPORT.md, accuracy-cost Pareto, hypothesis scorecard
