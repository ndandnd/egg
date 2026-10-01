# E2 results: cold time-to-quality of the fleet pricing MIP vs size (final, 18 cells)

Array 758967 (code 4403c30), all 18 tasks completed, collected 07:30 UTC 1 October.
One cold Gurobi solve (1 thread, 600 s cap) of the fleet pricing MIP V(p) at the `day`
tariff's linear prices. Scaled cases `claude-scale-v1` (ids 50000-50003; connector
power 90*ceil(n/28) kW) plus bank groups 10069/10075. "0.5% s" = first time the
incumbent is within 0.5% of that run's own final incumbent (not the optimum). Gap =
final (incumbent - bound)/incumbent. Rows: `e2_rows.json`; script `summarize.py`.

| Cell | Trips | Movements | Build s | Status (600 s) | Incumbent | Gap % | 1st inc s | 0.5% s | 0.1% s | Buses |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| s50000_n20 | 20 | 325 | 1.4 | OPTIMAL | 528.51 | 0.00 | 0.2 | 0.2 | 0.2 | 4 |
| s50001_n20 | 20 | 349 | 1.5 | OPTIMAL | 549.56 | 0.00 | 0.2 | 0.6 | 0.6 | 4 |
| s50002_n20 | 20 | 332 | 1.4 | OPTIMAL | 582.05 | 0.00 | 0.2 | 0.5 | 1.3 | 4 |
| s50003_n20 | 20 | 325 | 1.4 | OPTIMAL | 415.17 | 0.00 | 0.2 | 0.2 | 0.2 | 3 |
| bank10069 | 28 | 670 | 1.8 | OPTIMAL | 733.15 | 0.00 | 0.7 | 24.8 | 24.8 | None |
| bank10075 | 28 | 670 | 1.7 | OPTIMAL | 551.19 | 0.00 | 0.6 | 5.7 | 10.0 | 4 |
| s50000_n40 | 40 | 1438 | 2.1 | OPTIMAL | 526.78 | 0.00 | 2.0 | 128.1 | 128.1 | 4 |
| s50001_n40 | 40 | 1478 | 2.1 | FEASIBLE | 611.47 | 2.09 | 2.7 | 9.8 | 225.4 | 4 |
| s50002_n40 | 40 | 1444 | 2.2 | OPTIMAL | 637.93 | 0.00 | 2.1 | 24.2 | 26.9 | 4 |
| s50003_n40 | 40 | 1437 | 2.4 | FEASIBLE | 523.50 | 1.56 | 2.8 | 283.5 | 283.5 | 3 |
| s50000_n60 | 60 | 3345 | 4.0 | FEASIBLE | 644.67 | 10.06 | 9.5 | 138.3 | 157.1 | 4 |
| s50001_n60 | 60 | 3408 | 4.0 | FEASIBLE | 868.83 | 21.43 | 13.7 | 424.9 | 424.9 | 5 |
| s50002_n60 | 60 | 3354 | 3.9 | FEASIBLE | 772.49 | 2.94 | 11.6 | 257.9 | 291.3 | 4 |
| s50003_n60 | 60 | 3351 | 4.1 | FEASIBLE | 668.08 | 15.88 | 12.1 | 52.9 | 52.9 | 4 |
| s50000_n80 | 80 | 6062 | 7.4 | FEASIBLE | 764.98 | 10.03 | 28.2 | 470.4 | 470.4 | 4 |
| s50001_n80 | 80 | 6142 | 7.3 | FEASIBLE | 3781.45 | 78.94 | 46.0 | 46.0 | 46.0 | 30 |
| s50002_n80 | 80 | 6068 | 6.9 | FEASIBLE | 966.53 | 5.71 | 34.3 | 465.8 | 465.8 | 4 |
| s50003_n80 | 80 | 6065 | 7.5 | FEASIBLE | 895.13 | 22.99 | 43.9 | 255.9 | 255.9 | 4 |

bank10069: optimal value found, but extracting the incumbent failed the native charge-
projection roundoff check ("Whole-incumbent charge projection exceeds roundoff
budget"), so no replayed plan or bus count. The same refusal hit 10069's cold hull in
E0 and the learned arm on 10068 in E3. A tight extraction tolerance on some instances
is now a recurring infrastructure issue worth separate attention.

## Findings

1. **Cold solving is trivial at the training-bank size** (20-28 trips: optimal in
   0.2-25 s) and degrades sharply with size: at 40 trips 2 of 4 instances are not
   optimal after 600 s (gaps 1.6-2.1%); at 60 trips gaps are 2.9-21%; at 80 trips
   5.7-79%.
2. **Incumbent quality, not only bounds, fails at scale.** On 50001/80 the best plan
   after 10 minutes uses 30 buses (3781 vs ~765-967 for comparable instances). Time to
   reach the final incumbent's 0.5% band is 50-470 s at 60-80 trips.
3. **Model construction is not the bottleneck**: <= 7.5 s at 80 trips (6,000+
   movements, ~4 buses).
4. **Stop/go: go.** The stop condition (< 30 s to 0.5% at the largest size) fails on
   every 60/80-trip instance. ML acceleration has a real target on this generator
   beyond ~40 trips. E3 phase 2 tests it.
