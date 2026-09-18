# Benchmark Precedents & Pitfalls (as of Aug 2026)

> Confidence tags: **[D]** documented · **[R]** reported · **[S]** speculative

## The gap we'd fill

**[S/R]** No rigorous quantitative Devin-vs-Cursor head-to-head exists. What's out there:

- **[R]** [Trickle (July 2025)](https://trickle.so/blog/devin-ai-or-cursor) — closest to a real test: 4 task types, informal, single-run. Found Cursor <3s on routine tasks vs Devin 15+ min and looping on complex debugging. Its "Devin 13.86%" accuracy figure is just Cognition's 2024 SWE-bench number recycled.
- **[D]** [Builder.io (updated Jan 2026)](https://www.builder.io/blog/devin-vs-cursor) — explicit philosophy piece ("modes, not features": co-editing vs async handoff), zero metrics.
- **[R]** Comparison-site roundups **misattribute model scores to products** — e.g. Neuronad credits Cursor with "80.9% SWE-bench," which is Claude Opus 4.5's *model* score. A pitfall to avoid and to call out in the writeup.

## Methodology worth borrowing

| Source | What to borrow |
|--------|---------------|
| **[D]** [Answer.AI Devin month (Jan 2025)](https://www.answer.ai/posts/2025-01-08-devin.html) | 20 real tasks, 4 categories, judged "usable without extensive rework"; result 3✓/14✗/3?. Categorized real-work tasks + per-task documented outcomes beat synthetic benchmarks for credibility. |
| **[D]** [DeepCodeBench (Qodo)](https://www.qodo.ai/blog/deepcodebench-real-world-codebase-understanding-by-qa-benchmarking/) | **Fact-recall scoring** (TREC 2003 QA): extract discrete verifiable facts from the gold answer, LLM-check each in the candidate. DEEP (single block) vs BROAD (cross-file) question labels. |
| **[D]** [RepoQA](https://arxiv.org/abs/2406.06025) | **Needle-function search**: find a function from its NL description only. Cleanest retrieval ground truth; adapt to a private repo. |
| **[D]** [ContextBench](https://arxiv.org/html/2602.05892v3) | Gold-context annotation (trace dependencies from ground-truth patch); score retrieval at file/AST-block/line granularity with P/R/F1. Also found agents *retrieve* gold context but fail to *use* it — score both. |
| **[R]** SWE-bench lessons | Fail-to-pass tests as ground truth, but: ~1/3 of issues leak the solution in issue text, ~1/3 have weak tests. Write our own tests strong enough to catch wrong fixes. |

## Pitfalls (each maps to a control in the plan)

1. **[D]** **Nondeterminism flips rankings** ([arxiv 2602.07150](https://arxiv.org/pdf/2602.07150)) → **3+ runs per task**, report ranges not point estimates.
2. **[D]** **Contamination** ([SWE-rebench](https://arxiv.org/abs/2505.20411)) → private, freshly written repo; include a memorization probe (ask about recently changed code).
3. **[D]** **Cost-blind evals** ([AI Agents That Matter, arxiv 2407.01502](https://arxiv.org/abs/2407.01502)) → log $ and wall-clock per task; report accuracy-cost Pareto, not accuracy alone.
4. **[R]** **Silent product updates / harness conflation** ([arxiv 2601.01743](https://arxiv.org/pdf/2601.01743)) → pin models where the UI allows (Cursor: avoid Auto; Devin selects internally — record what it used), log product versions per run, complete all runs in a short window.
5. **[R]** **Leaderboard contamination** (MindStudio: ~12% memorized fixes on SWE-bench Pro) → never use public-benchmark deltas as product evidence.

## Pricing & pilot budget (Aug 2026)

- **[D]** **Devin**: Free $0 / **Pro $20/mo** / Max $200/mo / Teams $80 + $40/seat. ACUs retired; plans have opaque daily/weekly "usage allowance," extra usage at API pricing ([devin.ai/pricing](https://devin.ai/pricing)). **[R]** Old prior: small fix <$2, medium feature $5–15.
- **[D]** **Cursor**: Hobby free / **Pro $20/mo** (~$20 included API-rate agent usage) / Pro+ $60 / Ultra $200; token passthrough at model API rates, ~$0.04 per typical agent request ([Vantage breakdown](https://www.vantage.sh/blog/cursor-pricing-explained))
- **[S]** **Pilot ballpark** (~20–40 tasks × 2 tools × 3 runs): Cursor $20–100; Devin $20 with real risk of needing more given per-task costs. **Total $50–250.** Devin's opaque allowance is the main budgeting risk.
