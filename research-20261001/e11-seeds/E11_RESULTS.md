# E11 results (interim, 72/96 runs; 00:25 UTC 2 Oct): solver-seed robustness

Array 798833 (code 711c3d7). Gurobi seeds 1-2 complete, seed 3 partial; the remaining
24 runs are paused while the user's evspv2g stochastic jobs have cluster priority.
Cases: scale 50000-50003 x {60, 80} trips, `day`, T = 60 s. Seeds verified to change
solver behaviour (e.g. cold on 50000/60: 790.42 vs 786.71). Script `summarize.py`.

| Case | cold min/med/max (n) | cold4 min/med/max (n) | learned4_k15 min/med/max (n) | learned4_k30 min/med/max (n) |
|---|---|---|---|---|
| scale:50000:60 | 786.7 / 788.6 / 790.4 (2/3) | 2002.3 / 2005.7 / 2009.4 (3/3) | 736.5 / 742.3 / 751.0 (3/3) | 741.9 / 744.5 / 744.8 (3/3) |
| scale:50001:60 | 3198.2 / 3199.9 / 3201.6 (2/2) | 3198.2 / 3198.2 / 3198.2 (1/2) | 898.2 / 939.9 / 981.6 (2/2) | 909.0 / 916.3 / 923.6 (2/2) |
| scale:50002:60 | 1048.0 / 1054.5 / 1060.9 (2/2) | 2235.9 / 2237.7 / 2239.4 (2/2) | 932.3 / 932.3 / 932.3 (1/2) | 950.1 / 992.4 / 1034.7 (2/2) |
| scale:50003:60 | 807.0 / 808.4 / 809.8 (2/2) | fail / - / - (0/2) | 749.2 / 753.1 / 757.0 (2/2) | 751.1 / 753.3 / 755.5 (2/2) |
| scale:50000:80 | 3276.6 / 3279.5 / 3295.5 (3/3) | fail / - / - (0/3) | 887.1 / 889.1 / 896.1 (3/3) | 904.3 / 940.0 / 940.9 (3/3) |
| scale:50001:80 | 4091.0 / 4091.0 / 4091.0 (1/2) | fail / - / - (0/2) | 1116.8 / 1119.2 / 1121.6 (2/2) | 2035.9 / 2071.5 / 2107.1 (2/2) |
| scale:50002:80 | 4480.0 / 4485.8 / 4491.6 (2/2) | fail / - / - (0/2) | 1261.4 / 1268.2 / 1274.9 (2/2) | 1342.7 / 1372.6 / 1402.5 (2/2) |
| scale:50003:80 | 3857.8 / 3857.8 / 3857.8 (1/2) | fail / - / - (0/2) | 923.7 / 925.1 / 926.5 (2/2) | 935.0 / 952.7 / 970.4 (2/2) |

Paired by seed (wins/ties/losses; failure = loss):
- learned4_k15 vs cold: 17/0/1
- learned4_k15 vs cold4: 17/0/1
- learned4_k30 vs cold: 18/0/0
- learned4_k30 vs cold4: 18/0/0

Failures (genuine, not harness): cold4 found no plan within its four 15 s rounds in 12
runs (every 80-trip and 50003/60 run, plus one 50001/60 seed) and cold in 2; one cold and one learned4 run hit
the native charge-projection roundoff refusal.

## Reading (interim)

- **The main result is robust to the solver seed.** Paired by seed, learned pruning
  beats unpruned cold in 17/18 (keep 15%) and 18/18 (keep 30%) comparisons, and cold4 in
  17/18 and 18/18. Seed-to-seed spread is small relative to the effect: e.g. 80 trips,
  50000: cold 3276.6-3295.5 vs learned keep-15% 887.1-896.1.
- The learned-arm spread across seeds is larger on 60-trip cases (e.g. 50001/60 keep 15%:
  898-982), so single-run differences of a few percent between learned variants (E6-E10)
  should not be over-read.
