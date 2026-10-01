# E9 results: learned plans as seeds for complete-fleet hull certification

Array 785526 (10 cases), all completed, collected 16:25 UTC. Hulls: GRB, 1 thread,
500 s phase / 600 s wall, 32 pricing calls, QP master; seeds are the routes of the
learned 300 s runs (learned4 keep 15% and 30%, learned keep 30%) with charging
re-optimized by the fixed-route LP and replayed. D lower: best full-case cold planner
bound (pruned bounds never used), tightened by D >= CH lower. Native, tolerance-
qualified enclosures. Status `budget_exhausted` = interval valid but not closed.

| Case | cold hull [L, U] (width) | seeded hull [L, U] (width) | D interval | gap D-CH | regret of best seed |
|---|---|---|---|---|---|
| scale:50000:40 | [587.71, 596.23] (8.53) budget_exhausted | [594.14, 594.84] (0.70) budget_exhausted | [594.14, 594.95] | [0.00, 0.81] | [-0.38, 6.55] |
| scale:50001:40 | [646.32, 684.46] (38.14) budget_exhausted | [671.14, 681.90] (10.76) budget_exhausted | [671.14, 682.84] | [0.00, 11.70] | [5.00, 58.15] |
| scale:50002:40 | [713.32, 713.64] (0.32) budget_exhausted | [713.59, 713.59] (0.00) certified | [713.59, 714.31] | [0.00, 0.72] | [2.06, 6.84] |
| scale:50003:40 | [513.72, 554.90] (41.17) budget_exhausted | [526.04, 551.99] (25.94) budget_exhausted | [529.32, 552.89] | [0.00, 26.85] | [-4.51, 34.89] |
| scale:50000:60 | [577.30, 748.28] (170.98) budget_exhausted | [685.19, 738.34] (53.15) budget_exhausted | [703.62, 747.38] | [0.00, 62.18] | [-1232.17, 650.02] |
| scale:50001:60 | [732.59, 957.70] (225.11) budget_exhausted | [777.04, 891.16] (114.12) budget_exhausted | [777.04, 907.55] | [0.00, 130.51] | [-405.35, 196.16] |
| scale:50002:60 | [804.42, 935.38] (130.96) budget_exhausted | [877.19, 925.47] (48.28) budget_exhausted | [877.19, 931.46] | [0.00, 54.27] | [-1312.84, 877.39] |
| scale:50003:60 | [561.98, 764.06] (202.08) budget_exhausted | [625.13, 741.67] (116.54) budget_exhausted | [627.39, 759.67] | [0.00, 134.54] | [68.93, 164.51] |
| scale:50000:80 | [685.68, 1063.95] (378.26) budget_exhausted | [749.40, 892.93] (143.54) budget_exhausted | [815.40, 914.16] | [0.00, 164.76] | [-2120.89, 857.76] |
| scale:50003:80 | [689.24, 1050.77] (361.53) budget_exhausted | [723.17, 921.22] (198.05) budget_exhausted | [723.17, 955.08] | [0.00, 231.91] | [-2657.55, 898.97] |

## Findings

1. **Seeding with learned plans tightens the hull enclosure on 10/10 cases**:
   width ratios seeded/cold are 0.08, 0.28, 0.63 at 40 trips (plus one case certified
   only when seeded: 50002/40), 0.31-0.58 at 60 trips, 0.38-0.55 at 80 trips. Both the
   global lower bound and the mixture upper bound improve.
2. Only one hull certifies; every gap interval still contains zero. At 60-80 trips the
   enclosures remain tens to hundreds of units wide after 600 s.
3. The own-price response (60 s) is not solved at 60-80 trips, so those regret
   intervals are uninformative (lower ends far below zero; mathematically regret >= 0).
   50003/60 has a strictly positive regret interval [68.9, 164.5] for its seed plan,
   which includes that plan's own excess over the optimum.
4. Implication for the paper: learned plans make the price-support computation
   materially cheaper (tighter bounds in equal time), but certifying D - CH at 60+ trips
   still needs a stronger pricing oracle or longer budgets.
