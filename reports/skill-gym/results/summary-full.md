# skill-gym results — phase `full`

_Generated 2026-08-07 16:14; model(s): claude-opus-4-8; 56 runs. Prices used for est-cost: per-model table in analyze.py._

## Headline — per condition (all tasks)

| condition | solved | est $/run | **est $/solved** | output tok/run | Δ out | cache-read tok/run | Δ | wall s/run |
|---|---|---|---|---|---|---|---|---|
| baseline | 10/14 | 0.528 | **0.740** (+0%) | 5.8k | +0% | 461.9k | +0% | 96 |
| caveman | 10/14 | 0.367 | **0.514** (-30%) | 3.4k | -42% | 308.0k | -33% | 60 |
| headroom | 10/14 | 0.431 | **0.604** (-18%) | 6.7k | +15% | 254.3k | -45% | 148 |
| both | 10/14 | 0.369 | **0.516** (-30%) | 4.9k | -16% | 236.0k | -49% | 98 |

## Where the tokens went (mean per run, across tasks)

| condition | out:reasoning | out:answer-text | out:tool/code | in:fresh | in:cache-write | in:cache-read | tool-result chars fed back |
|---|---|---|---|---|---|---|---|
| baseline | 3.8k | 1.1k | 953 | 21 | 24.3k | 461.9k | 24.3k |
| caveman | 2.2k | 590 | 605 | 1.6k | 19.5k | 308.0k | 19.9k |
| headroom | 4.5k | 1.1k | 1.1k | 32 | 21.8k | 254.3k | 26.7k |
| both | 3.3k | 670 | 977 | 1.6k | 19.2k | 236.0k | 22.7k |

## Per task

### C1

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 2 | 0.417 | 10 | 9 | 49 | 2.9k | 1.7k | 538 | 673 | 19 | 319.2k | 8.1k |
| caveman | 2 | 2 | 0.251 | 8 | 6 | 34 | 1.7k | 1.1k | 163 | 427 | 1.6k | 251.5k | 10.0k |
| headroom | 2 | 2 | 0.182 | 9 | 8 | 57 | 2.4k | 1.4k | 379 | 564 | 17 | 76.4k | 7.8k |
| both | 2 | 2 | 0.182 | 10 | 10 | 55 | 2.2k | 1.4k | 176 | 629 | 1.6k | 115.3k | 9.6k |

### C2

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 2 | 0.436 | 8 | 8 | 70 | 4.4k | 2.9k | 469 | 968 | 16 | 342.8k | 12.5k |
| caveman | 2 | 2 | 0.459 | 10 | 8 | 69 | 3.5k | 2.3k | 245 | 934 | 1.6k | 399.0k | 14.4k |
| headroom | 2 | 2 | 0.260 | 9 | 8 | 53 | 3.3k | 2.0k | 586 | 676 | 17 | 150.0k | 12.4k |
| both | 2 | 2 | 0.530 | 16 | 16 | 124 | 7.4k | 5.1k | 450 | 1.9k | 1.6k | 365.4k | 14.0k |

### C3

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 2 | 1.053 | 25 | 24 | 195 | 11.2k | 8.3k | 728 | 2.2k | 49 | 1170.3k | 8.5k |
| caveman | 2 | 2 | 0.335 | 9 | 8 | 55 | 2.5k | 1.6k | 199 | 622 | 1.6k | 336.0k | 10.1k |
| headroom | 2 | 2 | 0.948 | 34 | 34 | 475 | 14.5k | 10.4k | 952 | 3.2k | 68 | 793.5k | 8.1k |
| both | 2 | 2 | 0.613 | 26 | 26 | 207 | 8.0k | 5.8k | 356 | 1.9k | 1.6k | 528.9k | 9.6k |

### C4

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 2 | 1.039 | 26 | 25 | 180 | 11.0k | 5.0k | 4.6k | 1.3k | 34 | 945.1k | 7.3k |
| caveman | 2 | 2 | 0.878 | 25 | 24 | 143 | 8.7k | 4.6k | 3.0k | 1.1k | 1.6k | 778.6k | 8.9k |
| headroom | 2 | 2 | 0.901 | 30 | 28 | 208 | 11.7k | 5.6k | 4.8k | 1.3k | 94 | 581.7k | 6.9k |
| both | 2 | 2 | 0.818 | 26 | 26 | 176 | 9.9k | 5.3k | 3.2k | 1.4k | 1.6k | 538.8k | 8.3k |

### O1

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 0 | 0.207 | 6 | 4 | 38 | 2.4k | 1.5k | 294 | 534 | 10 | 166.2k | 7.3k |
| caveman | 2 | 0 | 0.162 | 4 | 3 | 25 | 1.6k | 1.1k | 84 | 359 | 1.6k | 111.7k | 8.9k |
| headroom | 2 | 0 | 0.151 | 6 | 4 | 38 | 2.6k | 1.9k | 311 | 452 | 10 | 40.0k | 6.7k |
| both | 2 | 0 | 0.114 | 4 | 4 | 30 | 1.6k | 1.2k | 67 | 334 | 1.6k | 35.8k | 8.4k |

### O2

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 2 | 0.167 | 4 | 2 | 32 | 2.1k | 1.4k | 428 | 253 | 6 | 93.4k | 7.8k |
| caveman | 2 | 2 | 0.154 | 4 | 2 | 21 | 1.3k | 846 | 169 | 235 | 1.6k | 93.7k | 9.4k |
| headroom | 2 | 2 | 0.114 | 4 | 3 | 29 | 2.1k | 1.4k | 350 | 258 | 5 | 22.9k | 7.4k |
| both | 2 | 2 | 0.122 | 3 | 2 | 27 | 1.4k | 919 | 224 | 255 | 1.6k | 22.6k | 8.8k |

### O3

| condition | n | solved | est $ | turns | tool calls | dur s | out total | reasoning | text | tool | in fresh | cache r | first-ctx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 0 | 0.378 | 6 | 5 | 107 | 6.8k | 5.6k | 501 | 715 | 11 | 196.3k | 7.1k |
| caveman | 2 | 0 | 0.333 | 6 | 5 | 75 | 4.3k | 3.5k | 224 | 559 | 1.6k | 185.5k | 9.0k |
| headroom | 2 | 0 | 0.464 | 8 | 8 | 172 | 10.5k | 8.6k | 566 | 1.3k | 16 | 115.8k | 6.8k |
| both | 2 | 0 | 0.202 | 4 | 4 | 67 | 3.7k | 3.0k | 243 | 459 | 1.6k | 45.0k | 8.6k |

## Per-run detail

| task | condition | trial | pass | est $ | out tok | in fresh | cache r | turns | dur s | note |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | baseline | t1 | ✅ | 0.521 | 2.7k | 19 | 302.9k | 10 | 48.2 |  |
| C1 | baseline | t2 | ✅ | 0.313 | 3.1k | 19 | 335.4k | 10 | 49.0 |  |
| C1 | both | t1 | ✅ | 0.152 | 1.7k | 1.6k | 93.9k | 9 | 46.5 |  |
| C1 | both | t2 | ✅ | 0.212 | 2.8k | 1.6k | 136.7k | 12 | 62.7 |  |
| C1 | caveman | t1 | ✅ | 0.204 | 1.3k | 1.6k | 189.8k | 6 | 31.6 |  |
| C1 | caveman | t2 | ✅ | 0.297 | 2.0k | 1.6k | 313.2k | 9 | 36.2 |  |
| C1 | headroom | t1 | ✅ | 0.219 | 2.5k | 17 | 70.8k | 9 | 69.1 |  |
| C1 | headroom | t2 | ✅ | 0.144 | 2.3k | 17 | 82.0k | 9 | 45.4 |  |
| C2 | baseline | t1 | ✅ | 0.414 | 4.1k | 15 | 316.8k | 8 | 56.8 |  |
| C2 | baseline | t2 | ✅ | 0.459 | 4.7k | 17 | 368.8k | 9 | 83.2 |  |
| C2 | both | t1 | ✅ | 0.587 | 8.7k | 1.6k | 393.8k | 17 | 137.0 |  |
| C2 | both | t2 | ✅ | 0.473 | 6.1k | 1.6k | 337.0k | 16 | 110.5 |  |
| C2 | caveman | t1 | ✅ | 0.570 | 4.8k | 1.6k | 528.5k | 12 | 99.0 |  |
| C2 | caveman | t2 | ✅ | 0.348 | 2.3k | 1.6k | 269.6k | 7 | 38.1 |  |
| C2 | headroom | t1 | ✅ | 0.227 | 2.6k | 15 | 127.9k | 8 | 46.0 |  |
| C2 | headroom | t2 | ✅ | 0.292 | 3.9k | 19 | 172.2k | 10 | 60.4 |  |
| C3 | baseline | t1 | ✅ | 1.244 | 13.0k | 63 | 1471.5k | 32 | 240.2 |  |
| C3 | baseline | t2 | ✅ | 0.863 | 9.5k | 35 | 869.0k | 18 | 150.3 |  |
| C3 | both | t1 | ✅ | 0.903 | 12.2k | 1.7k | 819.5k | 37 | 340.1 |  |
| C3 | both | t2 | ✅ | 0.322 | 3.8k | 1.6k | 238.4k | 16 | 74.1 |  |
| C3 | caveman | t1 | ✅ | 0.465 | 3.7k | 1.6k | 482.1k | 12 | 82.2 |  |
| C3 | caveman | t2 | ✅ | 0.206 | 1.2k | 1.6k | 190.0k | 6 | 28.5 |  |
| C3 | headroom | t1 | ✅ | 1.082 | 16.7k | 69 | 910.9k | 35 | 724.5 |  |
| C3 | headroom | t2 | ✅ | 0.815 | 12.3k | 67 | 676.1k | 34 | 225.7 |  |
| C4 | baseline | t1 | ✅ | 1.023 | 10.2k | 37 | 997.8k | 25 | 182.1 |  |
| C4 | baseline | t2 | ✅ | 1.054 | 11.8k | 31 | 892.5k | 27 | 177.1 |  |
| C4 | both | t1 | ✅ | 0.875 | 10.3k | 1.6k | 613.1k | 28 | 195.3 |  |
| C4 | both | t2 | ✅ | 0.762 | 9.5k | 1.6k | 464.4k | 25 | 156.9 |  |
| C4 | caveman | t1 | ✅ | 0.975 | 9.1k | 1.6k | 889.5k | 25 | 154.8 |  |
| C4 | caveman | t2 | ✅ | 0.781 | 8.3k | 1.6k | 667.8k | 25 | 131.6 |  |
| C4 | headroom | t1 | ✅ | 0.850 | 11.4k | 33 | 528.4k | 28 | 179.6 |  |
| C4 | headroom | t2 | ✅ | 0.953 | 11.9k | 156 | 635.0k | 31 | 236.5 |  |
| O1 | baseline | t1 | ❌ | 0.214 | 2.5k | 11 | 183.0k | 6 | 35.6 |  |
| O1 | baseline | t2 | ❌ | 0.201 | 2.2k | 9 | 149.4k | 5 | 39.8 |  |
| O1 | both | t1 | ❌ | 0.105 | 1.5k | 1.6k | 30.4k | 4 | 32.4 |  |
| O1 | both | t2 | ❌ | 0.122 | 1.8k | 1.6k | 41.2k | 5 | 27.4 |  |
| O1 | caveman | t1 | ❌ | 0.160 | 1.4k | 1.6k | 112.6k | 4 | 21.6 |  |
| O1 | caveman | t2 | ❌ | 0.164 | 1.8k | 1.6k | 110.7k | 4 | 28.8 |  |
| O1 | headroom | t1 | ❌ | 0.166 | 2.6k | 9 | 30.3k | 5 | 37.7 |  |
| O1 | headroom | t2 | ❌ | 0.136 | 2.6k | 11 | 49.7k | 6 | 38.6 |  |
| O2 | baseline | t1 | ✅ | 0.154 | 1.9k | 7 | 109.5k | 4 | 27.9 |  |
| O2 | baseline | t2 | ✅ | 0.180 | 2.3k | 5 | 77.4k | 3 | 36.6 |  |
| O2 | both | t1 | ✅ | 0.127 | 1.4k | 1.6k | 26.7k | 3 | 22.7 |  |
| O2 | both | t2 | ✅ | 0.117 | 1.4k | 1.6k | 18.5k | 3 | 30.7 |  |
| O2 | caveman | t1 | ✅ | 0.141 | 1.3k | 1.6k | 74.1k | 3 | 20.8 |  |
| O2 | caveman | t2 | ✅ | 0.168 | 1.2k | 1.6k | 113.2k | 4 | 21.6 |  |
| O2 | headroom | t1 | ✅ | 0.130 | 2.1k | 5 | 25.3k | 4 | 30.2 |  |
| O2 | headroom | t2 | ✅ | 0.099 | 2.0k | 5 | 20.5k | 4 | 28.7 |  |
| O3 | baseline | t1 | ❌ | 0.367 | 6.8k | 11 | 191.1k | 6 | 103.8 |  |
| O3 | baseline | t2 | ❌ | 0.389 | 6.9k | 11 | 201.4k | 6 | 110.7 |  |
| O3 | both | t1 | ❌ | 0.213 | 3.8k | 1.6k | 54.5k | 5 | 69.0 |  |
| O3 | both | t2 | ❌ | 0.191 | 3.7k | 1.6k | 35.4k | 4 | 65.1 |  |
| O3 | caveman | t1 | ❌ | 0.342 | 3.9k | 1.6k | 167.6k | 5 | 66.7 |  |
| O3 | caveman | t2 | ❌ | 0.324 | 4.7k | 1.6k | 203.5k | 7 | 83.0 |  |
| O3 | headroom | t1 | ❌ | 0.360 | 8.2k | 15 | 96.4k | 8 | 137.4 |  |
| O3 | headroom | t2 | ❌ | 0.568 | 12.8k | 17 | 135.2k | 9 | 207.4 |  |

## Caveats

- output split (reasoning/text/tool) is derived: text+tool estimated from visible chars at ~3.8 chars/tok, anchored to the exact per-message output_tokens; reasoning is the residual. Exact totals; approximate split.
- with <3 trials, treat deltas smaller than ~15% as noise.
- est-cost uses public per-MTok prices; subscription runs bill usage, not dollars.