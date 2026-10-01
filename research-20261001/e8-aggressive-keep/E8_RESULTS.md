# E8 results: how aggressive can learned pruning be?

Array 782210 (66 runs: public keep 5/10/15%, scaled keep 5/10%; harness-fixed code,
v8 scores fold 0 / seed 17, learned4 policy), all completed, collected 16:25 UTC,
combined with E3/E5/E6 rows for cold, cold4 and keep 15/30/50%. Cells: bill relative
to the best of any listed arm for that case.

## Scaled synthetic cases (40-80 trips)

| Case | T s | cold | cold4 | learned4_k5 | learned4_k10 | learned4_k15 | learned4_k30 | learned4_k50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| scale:50000:40 | 60 | 1.08% | 0.85% | 0.87% | 0.05% | 0.00% | 0.51% | 0.85% |
| scale:50001:40 | 60 | 0.81% | 0.52% | 0.41% | 0.39% | 0.64% | 1.31% | 1.02% |
| scale:50002:40 | 60 | 0.78% | 0.49% | 0.82% | 0.75% | 0.08% | 0.10% | 0.52% |
| scale:50003:40 | 60 | 0.37% | 0.37% | 2.23% | 2.15% | 0.25% | 0.00% | 1.99% |
| scale:50000:60 | 60 | 2.97% | 170.92% | 0.91% | 0.89% | 0.00% | 1.42% | 1.21% |
| scale:50001:60 | 60 | 261.87% | 261.87% | 0.43% | 0.41% | 2.52% | 12.78% | 81.79% |
| scale:50002:60 | 60 | 4.65% | 142.52% | 0.09% | 0.00% | 0.53% | 11.35% | 2.04% |
| scale:50003:60 | 60 | 9.34% | 145.68% | 0.04% | 0.36% | 0.32% | 1.20% | 3.29% |
| scale:50000:80 | 60 | 270.47% | fail | 0.15% | 1.24% | 2.23% | 2.02% | 12.08% |
| scale:50001:80 | 60 | 275.37% | fail | 0.48% | 11.07% | 2.74% | 91.61% | 183.93% |
| scale:50002:80 | 60 | 286.61% | fail | 0.03% | 5.42% | 10.21% | 25.38% | 121.25% |
| scale:50003:80 | 60 | 323.12% | fail | 2.03% | 1.01% | 2.21% | 9.95% | 29.58% |
| scale:50000:40 | 300 | 0.21% | 0.50% | 0.87% | 0.05% | 0.00% | 0.20% | 0.02% |
| scale:50001:40 | 300 | 0.52% | 0.12% | 0.41% | 0.39% | 0.43% | 0.00% | 0.26% |
| scale:50002:40 | 300 | 0.17% | 0.00% | 0.82% | 0.75% | 0.08% | 0.10% | 0.29% |
| scale:50003:40 | 300 | 0.36% | 0.02% | 2.23% | 2.15% | 0.21% | 0.02% | 0.07% |
| scale:50000:60 | 300 | fail | 2.75% | 0.98% | 0.56% | 0.94% | 0.95% | 1.27% |
| scale:50001:60 | 300 | 24.18% | 261.87% | 0.43% | fail | 0.00% | 0.48% | 2.00% |
| scale:50002:60 | 300 | 4.66% | 4.66% | 0.09% | 0.19% | 0.26% | 0.38% | 1.43% |
| scale:50003:60 | 300 | 8.75% | 9.34% | 1.05% | 3.48% | 0.15% | 2.02% | 0.00% |
| scale:50000:80 | 300 | 7.37% | 19.75% | 0.00% | 0.54% | 0.03% | 1.14% | 3.59% |
| scale:50001:80 | 300 | 275.37% | 260.44% | 0.50% | 0.22% | 0.00% | 14.40% | 133.01% |
| scale:50002:80 | 300 | 286.61% | 194.81% | 0.00% | 2.18% | 4.83% | 9.20% | 9.62% |
| scale:50003:80 | 300 | 26.26% | 305.68% | 0.00% | 0.40% | 0.82% | 1.66% | 1.60% |

learned4_k5 vs cold @60s: 10/0/2  median -6.43%
learned4_k5 vs cold @300s: 9/0/3  median -6.86%
learned4_k5 vs cold4 @60s: 9/0/3  median -29.42%
learned4_k5 vs cold4 @300s: 8/0/4  median -5.97%
learned4_k10 vs cold @60s: 11/0/1  median -6.32%
learned4_k10 vs cold @300s: 9/0/3  median -4.56%
learned4_k10 vs cold4 @60s: 10/0/2  median -29.78%
learned4_k10 vs cold4 @300s: 8/0/4  median -4.27%
learned4_k15 vs cold @60s: 12/0/0  median -6.09%
learned4_k15 vs cold @300s: 12/0/0  median -6.83%
learned4_k15 vs cold4 @60s: 11/0/1  median -29.69%
learned4_k15 vs cold4 @300s: 9/0/3  median -6.30%
learned4_k30 vs cold @60s: 10/0/2  median -4.47%
learned4_k30 vs cold @300s: 12/0/0  median -5.80%
learned4_k30 vs cold4 @60s: 11/0/1  median -27.24%
learned4_k30 vs cold4 @300s: 11/0/1  median -5.39%
learned4_k50 vs cold @60s: 10/0/2  median -4.01%
learned4_k50 vs cold @300s: 11/0/1  median -3.51%
learned4_k50 vs cold4 @60s: 8/0/4  median -24.88%
learned4_k50 vs cold4 @300s: 9/0/3  median -5.81%

## Public cases (bill, and % above the best listed arm)

| Case | T s | cold | cold4 | learned4_k5 | learned4_k10 | learned4_k15 | learned4_k30 |
|---|---:|---:|---:|---:|---:|---:|---:|
| public:eberbach | 600 | 1300.61 (3.90%) | 5189.14 (314.54%) | 1471.78 (17.58%) | 1275.66 (1.91%) | 1253.99 (0.18%) | 1252.17 (0.03%) |
| public:eberbach | 1800 | 1271.00 (1.54%) | 1291.24 (3.15%) | 1475.27 (17.86%) | 1275.34 (1.88%) | 1255.20 (0.27%) | 1251.77 (0.00%) |
| public:hildenbrand15 | 180 | 548.04 (12.14%) | 507.49 (3.84%) | 505.00 (3.33%) | 506.42 (3.62%) | 501.23 (2.56%) | 490.72 (0.41%) |
| public:hildenbrand15 | 600 | 548.04 (12.14%) | 493.32 (0.94%) | 505.00 (3.33%) | 506.42 (3.62%) | 501.23 (2.56%) | 488.71 (0.00%) |
| public:hildenbrand16 | 180 | 551.11 (4.36%) | 550.37 (4.23%) | 625.77 (18.50%) | 631.98 (19.68%) | 548.98 (3.96%) | 528.06 (0.00%) |
| public:hildenbrand16 | 600 | 541.17 (2.48%) | 533.01 (0.94%) | 625.77 (18.50%) | 631.98 (19.68%) | 548.98 (3.96%) | 528.06 (0.00%) |

## Findings

1. **The best keep fraction depends on size and on distribution shift.**
   - Synthetic: at 80 trips keep 5% is best at 60 s (within 0.03-2.0% of the best plan);
     at 40 trips it is slightly worse (up to 2.2%). Keep 15% is the most robust synthetic
     setting (12/12 vs cold at both budgets).
   - Public (out of distribution): keep 30% is best in all 6 cells; keep 5% is 17-19%
     worse on Eberbach and Hildenbrand 16. Consistent with E7, the model's ranking is
     less reliable off-distribution, so pruning needs a wider margin there.
2. A fixed global fraction is therefore the wrong control. The kept count that works
   on synthetic cases (~300 movements: 15% at 40 trips, 5% at 80) suggests a per-trip
   or absolute-count rule; E10 tests a per-trip top-m rule with no global fraction.
