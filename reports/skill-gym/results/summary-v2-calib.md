# skill-gym v2 — calibration (baseline only)

_Generated 2026-09-18 17:41; 58 runs; model(s): claude-opus-5._

| task | public prior (n/10) | baseline pass | f2p partial | turns | wall s | cost $ | out tok | audit |
|---|---|---|---|---|---|---|---|---|
| pylint-4551 | 0 | 2/2 | 1.00 | 40 | 439 | 2.56 | 33.2k | clean |
| pylint-4604 | 0 | 0/2 | 0.00 | 36 | 325 | 1.38 | 14.8k | clean |
| pylint-4970 | 3 | 2/2 | 1.00 | 46 | 405 | 1.97 | 20.2k | clean |
| pylint-6386 | 5 | 2/2 | 1.00 | 53 | 506 | 2.36 | 24.1k | clean |
| pylint-6528 | 4 | 2/2 | 1.00 | 40 | 408 | 1.47 | 17.6k | clean |
| pylint-7080 | 0 | 2/2 | 1.00 | 38 | 282 | 1.74 | 16.4k | clean |
| pylint-7277 | 4 | 2/2 | 1.00 | 22 | 182 | 0.65 | 9.6k | 1 flagged |
| pylint-8898 | 2 | 2/2 | 1.00 | 32 | 351 | 1.30 | 19.0k | clean |
| pytest-10356 | 2 | 0/2 | 0.00 | 30 | 287 | 1.01 | 16.4k | clean |
| pytest-5787 | 5 | 1/1 | 1.00 | 21 | 347 | 0.94 | 12.0k | clean |
| pytest-5840 | 0 | 0/2 | 0.00 | 41 | 624 | 1.82 | 26.9k | clean |
| pytest-7205 | 7 | 1/1 | 1.00 | 23 | 304 | 0.69 | 11.0k | clean |
| requests-2931 | 7 | 1/1 | 1.00 | 24 | 116 | 0.61 | 9.0k | clean |
| requests-5414 | 6 | 1/1 | 1.00 | 18 | 203 | 0.48 | 7.9k | clean |
| requests-6028 | 6 | 1/1 | 1.00 | 20 | 117 | 0.58 | 7.7k | 1 flagged |
| sphinx-10435 | 2 | 2/2 | 1.00 | 28 | 222 | 0.84 | 11.7k | clean |
| sphinx-10673 | 7 | 2/2 | 1.00 | 61 | 564 | 3.50 | 39.1k | clean |
| sphinx-7462 | 1 | 0/2 | 0.50 | 19 | 98 | 0.52 | 7.3k | clean |
| sphinx-7590 | 0 | 2/2 | 1.00 | 38 | 377 | 1.69 | 22.4k | clean |
| sphinx-7748 | 0 | 1/2 | 0.50 | 40 | 586 | 2.65 | 40.8k | clean |
| sphinx-7985 | 1 | 2/2 | 1.00 | 28 | 272 | 1.49 | 20.8k | clean |
| sphinx-8056 | 6 | 2/2 | 1.00 | 30 | 207 | 0.95 | 12.2k | clean |
| sphinx-8548 | 4 | 2/2 | 1.00 | 58 | 749 | 3.83 | 50.1k | clean |
| sphinx-8595 | 6 | 1/1 | 1.00 | 19 | 92 | 0.45 | 6.1k | clean |
| sphinx-9229 | 0 | 2/2 | 1.00 | 41 | 365 | 1.76 | 23.8k | clean |
| sphinx-9461 | 1 | 2/2 | 1.00 | 52 | 615 | 3.05 | 44.3k | clean |
| sphinx-9602 | 1 | 0/2 | 0.00 | 24 | 227 | 0.88 | 12.7k | clean |
| sphinx-9711 | 6 | 1/1 | 1.00 | 15 | 60 | 0.35 | 4.7k | clean |
| xarray-4687 | 5 | 1/1 | 1.00 | 22 | 199 | 0.76 | 11.5k | clean |
| xarray-6599 | 0 | 2/2 | 1.00 | 28 | 219 | 1.07 | 15.3k | clean |
| xarray-6938 | 4 | 2/2 | 1.00 | 28 | 276 | 0.76 | 10.6k | clean |
| xarray-6992 | 0 | 1/2 | 0.50 | 44 | 721 | 2.60 | 38.3k | clean |
| xarray-7229 | 0 | 1/2 | 0.50 | 31 | 391 | 1.26 | 20.1k | clean |

**Rule** (PLAN.md §2, fixed before the reserve pool was run): a task is *in band* if the baseline passes some but not all of its trials. Take in-band tasks first (nearest 50%, then most turns); if fewer than 10, top up with always-pass tasks that took the most turns — the ones with the most to lose. Never-pass tasks are dropped: a floor shows nothing. Excluded: requests-6028 (see analyze_v2.py).

In band: 3 · always-pass: 17 · never-pass (dropped): 5 · chosen: 10

| chosen task | baseline | why |
|---|---|---|
| xarray-6992 | 1/2 | in band |
| sphinx-7748 | 1/2 | in band |
| xarray-7229 | 1/2 | in band |
| sphinx-10673 | 2/2 | top-up (most turns) |
| sphinx-8548 | 2/2 | top-up (most turns) |
| pylint-6386 | 2/2 | top-up (most turns) |
| sphinx-9461 | 2/2 | top-up (most turns) |
| pylint-4970 | 2/2 | top-up (most turns) |
| sphinx-9229 | 2/2 | top-up (most turns) |
| pylint-4551 | 2/2 | top-up (most turns) |