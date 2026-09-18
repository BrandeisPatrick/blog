# skill-gym v2 — calibration (baseline only)

_Generated 2026-09-18 17:02; 37 runs; model(s): claude-opus-5._

| task | public prior (n/10) | baseline pass | f2p partial | turns | wall s | cost $ | out tok | audit |
|---|---|---|---|---|---|---|---|---|
| pylint-4551 | 0 | 1/1 | 1.00 | 45 | 469 | 2.90 | 35.9k | clean |
| pylint-4604 | 0 | 0/1 | 0.00 | 32 | 245 | 1.10 | 11.0k | clean |
| pylint-4970 | 3 | 2/2 | 1.00 | 46 | 405 | 1.97 | 20.2k | clean |
| pylint-6386 | 5 | 2/2 | 1.00 | 53 | 506 | 2.36 | 24.1k | clean |
| pylint-6528 | 4 | 2/2 | 1.00 | 40 | 408 | 1.47 | 17.6k | clean |
| pylint-7080 | 0 | 1/1 | 1.00 | 34 | 256 | 1.60 | 13.6k | clean |
| pylint-7277 | 4 | 2/2 | 1.00 | 22 | 182 | 0.65 | 9.6k | 1 flagged |
| pylint-8898 | 2 | 2/2 | 1.00 | 32 | 351 | 1.30 | 19.0k | clean |
| pytest-10356 | 2 | 0/2 | 0.00 | 30 | 287 | 1.01 | 16.4k | clean |
| pytest-5787 | 5 | 1/1 | 1.00 | 21 | 347 | 0.94 | 12.0k | clean |
| pytest-5840 | 0 | 0/1 | 0.00 | 49 | 725 | 2.11 | 28.8k | clean |
| pytest-7205 | 7 | 1/1 | 1.00 | 23 | 304 | 0.69 | 11.0k | clean |
| requests-2931 | 7 | 1/1 | 1.00 | 24 | 116 | 0.61 | 9.0k | clean |
| requests-5414 | 6 | 1/1 | 1.00 | 18 | 203 | 0.48 | 7.9k | clean |
| requests-6028 | 6 | 1/1 | 1.00 | 20 | 117 | 0.58 | 7.7k | 1 flagged |
| sphinx-10435 | 2 | 1/1 | 1.00 | 30 | 319 | 0.99 | 14.3k | clean |
| sphinx-10673 | 7 | 1/1 | 1.00 | 59 | 486 | 3.13 | 34.1k | clean |
| sphinx-7462 | 1 | 0/1 | 0.50 | 15 | 78 | 0.43 | 6.1k | clean |
| sphinx-7590 | 0 | 1/1 | 1.00 | 42 | 415 | 1.84 | 23.4k | clean |
| sphinx-7748 | 0 | 1/1 | 1.00 | 47 | 679 | 3.30 | 48.2k | clean |
| sphinx-7985 | 1 | 1/1 | 1.00 | 30 | 254 | 1.51 | 20.3k | clean |
| sphinx-8056 | 6 | 1/1 | 1.00 | 25 | 134 | 0.75 | 10.5k | clean |
| sphinx-8548 | 4 | 1/1 | 1.00 | 62 | 862 | 4.33 | 57.1k | clean |
| sphinx-8595 | 6 | 1/1 | 1.00 | 19 | 92 | 0.45 | 6.1k | clean |
| sphinx-9229 | 0 | 1/1 | 1.00 | 43 | 348 | 1.64 | 21.0k | clean |
| sphinx-9461 | 1 | 1/1 | 1.00 | 55 | 559 | 2.99 | 40.9k | clean |
| sphinx-9602 | 1 | 0/1 | 0.00 | 23 | 208 | 0.82 | 11.0k | clean |
| sphinx-9711 | 6 | 1/1 | 1.00 | 15 | 60 | 0.35 | 4.7k | clean |
| xarray-4687 | 5 | 1/1 | 1.00 | 22 | 199 | 0.76 | 11.5k | clean |
| xarray-6599 | 0 | 1/1 | 1.00 | 25 | 209 | 0.98 | 15.8k | clean |
| xarray-6938 | 4 | 1/1 | 1.00 | 29 | 283 | 0.79 | 10.5k | clean |

**Rule** (PLAN.md §2, fixed before the reserve pool was run): a task is *in band* if the baseline passes some but not all of its trials. Take in-band tasks first (nearest 50%, then most turns); if fewer than 10, top up with always-pass tasks that took the most turns — the ones with the most to lose. Never-pass tasks are dropped: a floor shows nothing. Excluded: requests-6028 (see analyze_v2.py).

In band: 0 · always-pass: 5 · never-pass (dropped): 1 · chosen: 5

| chosen task | baseline | why |
|---|---|---|
| pylint-6386 | 2/2 | top-up (most turns) |
| pylint-4970 | 2/2 | top-up (most turns) |
| pylint-6528 | 2/2 | top-up (most turns) |
| pylint-8898 | 2/2 | top-up (most turns) |
| pylint-7277 | 2/2 | top-up (most turns) |