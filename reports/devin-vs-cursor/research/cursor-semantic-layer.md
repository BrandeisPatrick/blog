# Cursor's Semantic Layer (as of Aug 2026)

> Confidence tags: **[D]** documented (official Cursor source) · **[R]** reported (credible third party) · **[S]** speculative

## Architecture in one paragraph

Cursor chunks code locally into syntactic/AST-based units, embeds them with a **custom embedding model trained on agent session traces**, and syncs via a **Merkle tree** of SHA-256 file hashes so only changed subtrees are re-uploaded. Embeddings + obfuscated paths live server-side (reportedly Turbopuffer); as of 2026, code chunks are encrypted with client-held keys and decrypted client-side at search time. At query time the agent mixes semantic search with **"Instant Grep"** (custom exact-match engine) and can spawn an **"Explore" subagent** for broad parallel search. Cursor's bet: **embedding index + hybrid grep**.

## Indexing pipeline

- **[D]** Files split into "syntactic chunks" → embeddings; cached by chunk content hash so re-indexing similar codebases is fast ([blog/secure-codebase-indexing](https://cursor.com/blog/secure-codebase-indexing))
- **[R]** Chunk granularity: functions/classes or ~500-token blocks via AST/tree-sitter-style parsing; exact sizes unpublished ([ZenML case study](https://www.zenml.io/llmops-database/enhancing-ai-coding-agent-performance-with-custom-semantic-search))
- **[D]** **Custom embedding model** (Nov 2025): trained from agent session traces — an LLM retrospectively ranks which content would have helped at each step; embeddings align to those rankings, "rather than relying on generic code similarity" ([blog/semsearch](https://cursor.com/blog/semsearch)). Supersedes old speculation about OpenAI/voyage embeddings.
- **[D]** **Merkle-tree sync**: SHA-256 tree over all valid files; sync traverses only diverging branches. 50k-file repo ≈ 3.2 MB of hashes. **[R]** Client re-checks hashes ~every 10 minutes ([blog](https://cursor.com/blog/secure-codebase-indexing))
- **[D]** Perf (Jan 2026): time-to-first-query median 7.87s → 525ms; p99 4.03h → 21s, via cache reuse + shared team indexes
- **[D]** Shared team indexes with Merkle ownership proofs — server filters search results against the client's own file-hash tree

## Storage & privacy

- **[D]** Plaintext never stored server-side; held in memory during indexing, then discarded. Persists: embedding vectors + obfuscated path/line metadata ([docs](https://cursor.com/docs/context/codebase-indexing))
- **[D]** 2026: encrypted chunks, client-side decryption at search time; user-supplied path key via `.cursor/keys`
- **[R]** Path obfuscation: per-segment encryption, key derived from recent commit hashes (enables teammate index sharing); directory *shape* visible to server ([Engineer's Codex](https://read.engineerscodex.com/p/how-cursor-indexes-codebases-fast))
- **[R]** Vector DB: Turbopuffer (was on official security page; vendor no longer named there)
- **[D]** Privacy Mode still indexes server-side; the guarantee is no-training/no-plaintext-retention, not no-server-index ([security](https://cursor.com/security))

## Query-time retrieval

- **[D]** Semantic search tool for natural-language queries + regex grep; combination beats either alone. **Cursor Context Bench: semantic search adds ~12.5% QA accuracy avg (6.5–23.5% across models)** vs grep-only; removing it → +2.2% dissatisfied follow-ups in A/B ([blog/semsearch](https://cursor.com/blog/semsearch))
- **[D]** **Instant Grep** (2026): custom exact-match/regex engine, claims to beat ripgrep on large codebases; auto-triggers for exact matches ([docs/agent/tools/search](https://cursor.com/docs/agent/tools/search))
- **[D]** **Explore subagent** (2026): own context window, faster model, broad parallel search, returns summaries not raw files; invoked automatically
- **[D]** Composer (Oct 2025) RL-trained with production tools incl. codebase-wide semantic search; per-step tool choice is the model's, no disclosed rerank stage. Old @codebase "scan→rerank→reason" flow is gone.

## Limits & controls

- **[D]** `.cursorignore` (blocks indexing + AI access), `.cursorindexingignore` (indexing only), `.gitignore` auto-respected, big default ignore list. Caveat: terminal/MCP tools can't be blocked by `.cursorignore`
- **[R]** ~100k-file indexing cap on Pro (forum-reported, no staff confirmation)

## 2025–26 timeline

Custom semsearch model (Nov 2025) → Composer RL agent (Oct 2025) → shared team indexes + perf (Jan 2026) → encrypted chunks + Instant Grep + Explore (2026 docs) → **Continue.dev acqui-hire (June 2026)** — repo read-only, no statement on their role in the context engine **[S]**. (Same reporting mentions a SpaceX ~$60B agreement to acquire Anysphere, announced ~June 16 2026 — verify before quoting.)

## Implications for our test

1. Synonym/concept queries should be Cursor's **strength** (purpose-trained embeddings) — probe A1 is a direct test of their 12.5% claim.
2. Index freshness: Merkle re-check ~10 min → recency probe (A7) should test inside and outside that window.
3. `.cursorignore` gives us a lever to create controlled blind spots if we want an ablation.
4. Pin the model in Cursor (avoid Auto routing) or the comparison confounds with model selection.
