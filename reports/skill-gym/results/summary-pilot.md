# skill-gym results — phase `pilot`

_Generated 2026-08-06 22:57; model(s): claude-opus-4-8; 6 runs. Prices used for est-cost: per-model table in analyze.py._

## Headline — per condition (all tasks)

| condition | solved | cost/run (est $) | output tok/run | Δ output vs base | input-fresh tok/run | Δ | cache-read tok/run | Δ |
|---|---|---|---|---|---|---|---|---|
| baseline | 1/2 | 0.323 | 2.5k | +0% | 12 | +0% | 182.9k | +0% |
| caveman | 1/2 | 0.224 | 1.7k | -30% | 1.6k | +13167% | 208.9k | +14% |
| headroom | 1/2 | 0.149 | 2.5k | +0% | 13 | +8% | 57.6k | -68% |

## Where the tokens went (mean per run, across tasks)

| condition | out:reasoning | out:answer-text | out:tool/code | in:fresh | in:cache-write | in:cache-read | tool-result chars fed back |
|---|---|---|---|---|---|---|---|
| baseline | 1.8k | 316 | 375 | 12 | 27.2k | 182.9k | 2.1k |
| caveman | 1.2k | 82 | 396 | 1.6k | 10.9k | 208.9k | 4.0k |
| headroom | 1.7k | 326 | 485 | 13 | 9.3k | 57.6k | 4.4k |

## Per task

### C1

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1 | 1 | 0.449 | 8 | 7 | 49 | 2.0k | 1.3k | 334 | 346 | 15 | 221.2k | 8.4k |
| caveman | 1 | 1 | 0.256 | 8 | 7 | 33 | 1.5k | 1.0k | 100 | 376 | 1.6k | 270.0k | 10.0k |
| headroom | 1 | 1 | 0.156 | 8 | 7 | 48 | 2.1k | 1.2k | 326 | 518 | 15 | 67.3k | 8.0k |

### O1

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1 | 0 | 0.198 | 5 | 4 | 44 | 3.0k | 2.3k | 298 | 403 | 9 | 144.6k | 7.2k |
| caveman | 1 | 0 | 0.192 | 5 | 4 | 35 | 1.9k | 1.5k | 64 | 416 | 1.6k | 147.8k | 8.8k |
| headroom | 1 | 0 | 0.142 | 6 | 5 | 42 | 2.9k | 2.1k | 326 | 451 | 11 | 47.9k | 6.8k |

## Per-run detail

| task | condition | trial | pass | est $ | out tok | in fresh | cache r | turns | dur s | note |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | baseline | t1 | ✅ | 0.449 | 2.0k | 15 | 221.2k | 8 | 49.4 |  |
| C1 | caveman | t1 | ✅ | 0.256 | 1.5k | 1.6k | 270.0k | 8 | 33.4 |  |
| C1 | headroom | t1 | ✅ | 0.156 | 2.1k | 15 | 67.3k | 8 | 48.0 |  |
| O1 | baseline | t1 | ❌ | 0.198 | 3.0k | 9 | 144.6k | 5 | 44.0 |  |
| O1 | caveman | t1 | ❌ | 0.192 | 1.9k | 1.6k | 147.8k | 5 | 35.0 |  |
| O1 | headroom | t1 | ❌ | 0.142 | 2.9k | 11 | 47.9k | 6 | 41.8 |  |

## Caveats

- output split (reasoning/text/tool) is derived: text+tool estimated from visible chars at ~3.8 chars/tok, anchored to the exact per-message output_tokens; reasoning is the residual. Exact totals; approximate split.
- with <3 trials, treat deltas smaller than ~15% as noise.
- est-cost uses public per-MTok prices; subscription runs bill usage, not dollars.