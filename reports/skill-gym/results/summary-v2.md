# skill-gym v2 results

_Generated 2026-09-19 02:19; 210 runs on 10 frozen tasks; model(s): claude-opus-5._

## Headline

| arm | solved | pass rate [95% CI] | Δ vs baseline [95% CI] | tasks better/worse/tie (sign p) | $/run | Δ | $/solved | Δ |
|---|---|---|---|---|---|---|---|---|
| baseline | 25/30 | 83% [63%, 100%] | — | — | 2.52 | +0% | 3.02 | +0% |
| caveman | 24/30 | 80% [57%, 97%] | -3 pts [-23, +13] | 1/2/7 (p=1.00) | 1.44 | -43% | 1.80 | -40% |
| ponytail | 22/30 | 73% [47%, 93%] | -10 pts [-27, +7] | 0/3/7 (p=0.25) | 1.67 | -34% | 2.27 | -25% |
| rtk | 24/30 | 80% [60%, 97%] | -3 pts [-27, +20] | 2/2/6 (p=1.00) | 2.83 | +12% | 3.54 | +17% |
| headroom | 28/30 | 93% [77%, 100%] | +10 pts [-3, +30] | 2/0/8 (p=0.50) | 3.05 | +21% | 3.27 | +8% |
| effort-high | 20/30 | 67% [47%, 87%] | -17 pts [-37, +3] | 0/5/5 (p=0.06) | 1.63 | -35% | 2.45 | -19% |
| effort-low | 18/30 | 60% [33%, 83%] | -23 pts [-50, -3] | 0/5/5 (p=0.06) | 0.57 | -77% | 0.95 | -68% |

## Cost, paired by task

| arm | cost vs baseline [95% CI] | cheaper on (tasks) | sign p |
|---|---|---|---|
| caveman | -43% [-50%, -36%] | 10/10 | 0.002 |
| ponytail | -34% [-41%, -25%] | 9/10 | 0.021 |
| rtk | +12% [+0%, +27%] | 3/10 | 0.344 |
| headroom | +21% [+5%, +44%] | 2/10 | 0.109 |
| effort-high | -35% [-45%, -21%] | 8/10 | 0.109 |
| effort-low | -77% [-82%, -71%] | 10/10 | 0.002 |

## Against the free dial

The effort arms are what Claude Code gives away: xhigh -> high -> low. For each tool, the pass rate the dial delivers at the same cost per run (linear between the native points).

| tool | $/run | pass rate | the dial at that cost | tool minus dial |
|---|---|---|---|---|
| caveman | 1.44 | 80% | 65% | +15 pts |
| ponytail | 1.67 | 73% | 67% | +6 pts |
| rtk | 2.83 | 80% | — costs more than the top of the dial | — |
| headroom | 3.05 | 93% | — costs more than the top of the dial | — |

caveman vs effort-high, the closest pair on price: caveman better on 4 tasks, worse on 0, tie 6 (sign p=0.125).

## Graded quality and process (mean per run)

| arm | f2p partial credit | P2P regressions | tests modified | test commands | Bash share of tool calls | repeated tool calls | lines added | audit-flagged runs |
|---|---|---|---|---|---|---|---|---|
| baseline | 0.83 | 0.00 | 0.00 | 11.6 | 99% | 0.1 | 50 | 0/30 |
| caveman | 0.80 | 0.00 | 0.00 | 7.8 | 100% | 0.0 | 46 | 0/30 |
| ponytail | 0.76 | 0.00 | 0.00 | 8.5 | 100% | 0.0 | 43 | 0/30 |
| rtk | 0.83 | 0.00 | 0.00 | 14.0 | 99% | 0.0 | 55 | 0/30 |
| headroom | 0.99 | 0.00 | 0.00 | 12.0 | 97% | 0.0 | 54 | 0/30 |
| effort-high | 0.72 | 0.00 | 0.00 | 8.9 | 99% | 0.0 | 49 | 0/30 |
| effort-low | 0.60 | 0.00 | 0.00 | 5.7 | 100% | 0.0 | 35 | 0/30 |

## Where the tokens went (mean per run)

| arm | out:reasoning | out:answer-text | out:tool/code | in:fresh | in:cache-write | in:cache-read | tool-result chars | first-request ctx | turns | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 26.3k | 782 | 5.3k | 85 | 67.8k | 2058.0k | 72.4k | 8.9k | 47 | 531 |
| caveman | 13.2k | 476 | 3.5k | 62 | 46.1k | 1096.2k | 53.3k | 10.5k | 34 | 296 |
| ponytail | 17.4k | 490 | 3.3k | 63 | 53.0k | 1207.5k | 56.6k | 10.8k | 35 | 371 |
| rtk | 29.9k | 771 | 6.0k | 92 | 72.0k | 2377.7k | 75.7k | 9.1k | 51 | 571 |
| headroom | 28.9k | 768 | 5.6k | 185 | 92.8k | 2457.2k | 81.2k | 8.4k | 53 | 604 |
| effort-high | 15.9k | 677 | 3.6k | 70 | 49.5k | 1256.9k | 58.1k | 8.9k | 37 | 368 |
| effort-low | 4.7k | 323 | 1.9k | 38 | 21.6k | 357.6k | 24.9k | 8.9k | 19 | 136 |

## Pass counts per task

| task | baseline | caveman | ponytail | rtk | headroom | effort-high | effort-low |
|---|---|---|---|---|---|---|---|
| xarray-6992 | 1/3 | 1/3 | 1/3 | 2/3 | 1/3 | 1/3 | 0/3 |
| sphinx-7748 | 1/3 | 1/3 | 0/3 | 2/3 | 3/3 | 1/3 | 1/3 |
| xarray-7229 | 2/3 | 3/3 | 2/3 | 2/3 | 3/3 | 2/3 | 1/3 |
| sphinx-10673 | 3/3 | 2/3 | 3/3 | 1/3 | 3/3 | 2/3 | 2/3 |
| sphinx-8548 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| pylint-6386 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| sphinx-9461 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| pylint-4970 | 3/3 | 2/3 | 2/3 | 3/3 | 3/3 | 2/3 | 0/3 |
| sphinx-9229 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| pylint-4551 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 2/3 | 2/3 |

## Caveats

- 30 runs per arm detects pass-rate differences of roughly 20 points; it cannot certify a 5-point loss.
- CIs are clustered bootstraps over tasks; with 10 tasks they are wide by construction.
- The reasoning/text/tool split of output tokens is derived (see analyze.py); totals are exact.
- Native macOS environments verified against gold patches, not the official Docker images: do not quote these pass rates as SWE-bench scores.