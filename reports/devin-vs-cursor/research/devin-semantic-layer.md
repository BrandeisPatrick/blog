# Devin's Semantic Layer (as of Aug 2026)

> Confidence tags: **[D]** documented (official Cognition source) · **[R]** reported (credible third party) · **[S]** speculative

## Architecture in one paragraph

Cognition runs a **two-track** context strategy. Cloud Devin auto-indexes connected repos every couple of hours into **Devin Wiki / DeepWiki** (architecture diagrams, source-linked pages) which — plus "advanced code search" — grounds Ask Devin and the Interactive Planning step; a separate **Knowledge** system stores trigger-gated org/repo notes retrieved mid-session. Devin Desktop (ex-Windsurf) keeps a local whole-codebase RAG index (M-Query retrieval) but increasingly routes retrieval through the **Fast Context subagent powered by SWE-grep** — RL-trained retrieval models doing up to 8 parallel grep/read/glob calls per turn. Cognition's published philosophy is explicitly **anti-embedding**: agentic/LLM search over vector similarity. Devin's bet: **generated wiki + agentic search**.

## Cloud Devin: Wiki + Knowledge + code search

- **[D]** **Devin Wiki** (Devin 2.0, Apr 2025): auto-indexes repos "every couple hours" → wikis with architecture diagrams, source links; Devin Search does cited codebase Q&A; Interactive Planning surfaces relevant files + a plan at session start ([blog/devin-2](https://cognition.com/blog/devin-2))
- **[D]** **DeepWiki** = free public Devin Wiki (swap github.com → deepwiki.com); 50k+ public repos indexed; DeepWiki MCP server exists ([blog/deepwiki](https://cognition.com/blog/deepwiki))
- **[D]** Wiki is used as the semantic layer: "Ask Devin will use information in the Wiki to better understand and find the relevant context in your codebase." Steerable via `.devin/wiki.json` (repo_notes ≤100 notes × 10k chars; ≤30 pages, 80 enterprise) ([docs/deepwiki](https://docs.devin.ai/work-with-devin/deepwiki))
- **[D]** **Knowledge system**: items = trigger description + content; "retrieves Knowledge when relevant, not all at once" — trigger-gated mid-session recall, scoped none/repo/all-repos, org→enterprise promotion, `!identifier` macros ([docs/knowledge](https://docs.devin.ai/product-guides/knowledge)). Devin proposes items from session feedback; 2026: sessions can CRUD knowledge directly, 300-item enterprise cap
- **[D]** In-session search mechanism is officially **vague**: "advanced code search capabilities" with citations; no official disclosure of embeddings, vector DBs, or repo maps
- **[S]** Third-party claims that the cloud index is embedding-based are inference, not documentation — and Cognition's own retrieval publications argue **against** embedding search at scale

## The anti-embedding retrieval lineage

- **[D]** **Riptide** (Windsurf era): LLM-based search "through millions of lines in seconds with 3x better accuracy than SOTA embedding-based systems" — massively parallel relevance calls instead of static embeddings ([windsurf-launch](https://devin.ai/blog/windsurf-launch))
- **[D]** **SWE-grep / SWE-grep-mini** (Oct 2025): multi-turn RL retrieval models; reward = weighted F1 on file- and line-level retrieval (precision-weighted); ≤8 parallel grep/read/glob calls per turn, ≤4 turns (3 explore + 1 answer); 2,800+ tok/s (mini) on Cerebras; up to 20x faster retrieval. Motivation: agents spent 60%+ of first turn on retrieval ([blog/swe-grep](https://cognition.com/blog/swe-grep))
- **[D]** **Fast Context subagent** ships in Devin Desktop: auto-triggers on code-search queries, returns file lists + line ranges to the main agent, preserving its context budget ([docs/fast-context](https://docs.devin.ai/desktop/context-awareness/fast-context))

## Devin Desktop (ex-Windsurf)

- **[D]** Rebranded June 2, 2026 (OTA update). Agent Command Center default surface; supports open **Agent Client Protocol** (Codex, Claude Agent, etc. run inside); **Spaces** share context objects across sessions/agents ([blog/introducing-devin-desktop](https://cognition.com/blog/introducing-devin-desktop))
- **[D]** **Devin Local** replaced Cascade (Rust rewrite, ~30% more token-efficient, subagents; Cascade EOL July 1, 2026)
- **[D]** Context engine: "the entire local codebase is indexed (including files that are not open)" — optimized RAG; open files prioritized; Teams/Enterprise remote repo indexing; context pinning; "M-Query retrieval" named but internals unpublished ([docs/context-awareness](https://docs.devin.ai/desktop/context-awareness/overview)). **[S]** Third-party specifics like "768-dim embeddings" are unverified.

## Models trained for the context system

- **[D]** **SWE-1.6**: post-trained for parallel tool calling and delegation to Fast Context over shell exploration; 950 tok/s paid (Cerebras); zero-credit in Desktop ([blog/swe-1-6](https://cognition.com/blog/swe-1-6))
- **[R]** **SWE-1.7** (July 2026): current recommended model, ~1,000 tok/s; reportedly Kimi K2.7 base + "self-compaction" (summarizes working state to extend horizons) ([docs/models](https://docs.devin.ai/desktop/models))

## 2026 semantic-layer changes (release notes)

Wiki v2 with agentic page writers + per-generation ACU costs (Apr 2026) · wiki effort levels (Apr 2026) · DeepWiki indexing improvements (June 2026) · Ask/Plan modes (Feb 2026) · recency-based repo search ordering (May 2026) · @repos file picker (June 2026) · "Devin Manages Devins" child-session orchestration (Mar 2026)

> **[S]** Caveat: third-party retrospectives conflict on Windsurf acquisition date/price (mid-2025 vs Dec 2025/$250M) — cross-check before quoting.

## Implications for our test

1. **The core contrast is architectural**: Cursor = trained embedding index; Devin = generated wiki + RL agentic grep. Our probes should discriminate exactly this (synonym traps stress embeddings' strength / grep's weakness; precision traps stress the reverse).
2. **Which Devin?** Cloud Devin (wiki + knowledge + autonomous sessions) and Devin Desktop (local RAG + Fast Context, IDE) have *different* semantic layers. Must decide which arm(s) to test — the apples-to-apples IDE fight is Cursor vs Devin Desktop; the flagship fight is Cursor vs Devin Cloud.
3. **Wiki staleness is a testable surface**: wiki regenerates "every couple hours" — change code post-wiki, ask a question the stale wiki answers wrongly, see if Devin re-grounds in code.
4. SWE-grep is precision-weighted by design — predict: fewer files cited, higher precision, possibly lower recall on split-logic probes (A3).
5. `.devin/wiki.json` and Knowledge give Devin a *steerable* semantic layer Cursor lacks — worth a probe arm where we test with/without seeded knowledge.
