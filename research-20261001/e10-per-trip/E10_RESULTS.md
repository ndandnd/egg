# E10 results (interim, 87/90 runs; 20:25 UTC): per-trip top-m pruning

Array 795026 (harness-fixed code, v8 scores fold 0 / seed 17, learned4 policy). Three
m=8 runs (Hildenbrand 16 at 600 s, Eberbach at 600/1800 s) were still queued behind the
user's other cluster jobs. Rule: keep each trip's m best incoming and m best outgoing
direct/depot movements, no global fraction. Columns kN = global keep N% (E3/E5/E6/E8);
mN = per-trip top-N. Cells: bill relative to the best of any listed arm for that case.

| Case | T s | cold | cold4 | k5 | k15 | k30 | m3 | m5 | m8 | kept m3/m5/m8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| public:hildenbrand15 | 180 | 12.14% | 3.84% | 3.33% | 2.56% | 0.41% | 3.38% | 0.05% | 0.31% | 200/293/370 |
| public:hildenbrand16 | 180 | 4.36% | 4.23% | 18.50% | 3.96% | 0.00% | 18.50% | 1.78% | 0.76% | 179/275/369 |
| public:eberbach | 600 | 3.90% | 314.54% | 17.58% | 0.18% | 0.03% | 24.64% | fail |  | 585/838/- |
| public:hildenbrand15 | 600 | 12.14% | 0.94% | 3.33% | 2.56% | 0.00% | 3.38% | 0.05% | 0.31% | 200/293/370 |
| public:hildenbrand16 | 600 | 2.48% | 0.94% | 18.50% | 3.96% | 0.00% | 18.50% | 1.78% |  | 179/275/- |
| public:eberbach | 1800 | 1.54% | 3.15% | 17.86% | 0.27% | 0.00% | fail | fail |  | 585/838/- |
| scale:50000:40 | 60 | 1.12% | 0.89% | 0.91% | 0.04% | 0.55% | 0.91% | 0.17% | 0.12% | 210/291/396 |
| scale:50001:40 | 60 | 0.81% | 0.52% | 0.41% | 0.64% | 1.31% | 0.41% | 0.22% | 0.49% | 217/298/397 |
| scale:50002:40 | 60 | 0.78% | 0.49% | 0.82% | 0.08% | 0.10% | 0.82% | 0.23% | 0.26% | 211/300/408 |
| scale:50003:40 | 60 | 0.54% | 0.54% | 2.41% | 0.43% | 0.17% | 2.41% | 0.37% | 0.15% | 213/293/391 |
| scale:50000:40 | 300 | 0.26% | 0.54% | 0.91% | 0.04% | 0.24% | 0.91% | 0.17% | 0.00% | 210/291/396 |
| scale:50001:40 | 300 | 0.52% | 0.12% | 0.41% | 0.43% | 0.00% | 0.41% | 0.24% | 0.04% | 217/298/397 |
| scale:50002:40 | 300 | 0.17% | 0.00% | 0.82% | 0.08% | 0.10% | 0.82% | 0.23% | 0.19% | 211/300/408 |
| scale:50003:40 | 300 | 0.53% | 0.19% | 2.41% | 0.38% | 0.19% | 2.41% | 0.17% | 0.00% | 213/293/391 |
| scale:50000:60 | 60 | 3.17% | 171.45% | 1.11% | 0.20% | 1.62% | 1.18% | 0.89% | 0.32% | 323/442/619 |
| scale:50001:60 | 60 | 261.87% | 261.87% | 0.43% | 2.52% | 12.78% | 0.45% | 0.28% | 1.89% | 337/463/625 |
| scale:50002:60 | 60 | 4.68% | 142.60% | 0.12% | 0.56% | 11.38% | 0.06% | 0.34% | 0.14% | 322/457/631 |
| scale:50003:60 | 60 | 9.34% | 145.68% | 0.04% | 0.32% | 1.20% | 1.19% | 0.06% | 0.80% | 317/444/606 |
| scale:50000:60 | 300 | fail | 2.95% | 1.18% | 1.14% | 1.14% | 1.18% | 0.63% | 0.00% | 323/442/619 |
| scale:50001:60 | 300 | 24.18% | 261.87% | 0.43% | 0.00% | 0.48% | 0.45% | 0.03% | 0.15% | 337/463/625 |
| scale:50002:60 | 300 | 4.69% | 4.69% | 0.12% | 0.29% | 0.42% | 0.06% | 0.00% | 0.00% | 322/457/631 |
| scale:50003:60 | 300 | 8.75% | 9.34% | 1.05% | 0.15% | 2.02% | 1.52% | 0.50% | 0.35% | 317/444/606 |
| scale:50000:80 | 60 | 270.82% | fail | 0.24% | 2.33% | 2.12% | 0.79% | 2.24% | 2.13% | 432/588/833 |
| scale:50001:80 | 60 | 276.01% | fail | 0.65% | 2.92% | 91.93% | 0.65% | 0.47% | 11.40% | 452/625/843 |
| scale:50002:80 | 60 | 288.36% | fail | 0.48% | 10.71% | 25.95% | 0.33% | 1.07% | 11.16% | 431/607/855 |
| scale:50003:80 | 60 | 323.88% | fail | 2.22% | 2.39% | 10.15% | 0.75% | 0.79% | 1.19% | 421/588/810 |
| scale:50000:80 | 300 | 7.47% | 19.86% | 0.09% | 0.12% | 1.24% | 0.00% | 2.07% | 3.58% | 432/588/833 |
| scale:50001:80 | 300 | 276.01% | 261.05% | 0.67% | 0.17% | 14.59% | 0.65% | 0.00% | 2.28% | 452/625/843 |
| scale:50002:80 | 300 | 288.36% | 196.15% | 0.45% | 5.30% | 9.70% | 0.19% | 0.00% | 0.14% | 431/607/855 |
| scale:50003:80 | 300 | 26.49% | 306.42% | 0.18% | 1.00% | 1.84% | 1.27% | 0.00% | 1.52% | 421/588/810 |

Paired (wins/ties/losses; a failure counts as a loss; median % over both-successful):
- m3 vs cold: 21/0/9, median -5.54%
- m3 vs cold4: 19/0/11, median -1.72%
- m3 vs k15: 11/0/19, median +0.48%
- m3 vs k30: 16/0/14, median -0.03%
- m5 vs cold: 27/0/3, median -5.02%
- m5 vs cold4: 25/0/5, median -3.00%
- m5 vs k15: 20/0/10, median -0.23%
- m5 vs k30: 19/0/11, median -0.43%
- m8 vs cold: 26/0/1, median -6.10%
- m8 vs cold4: 26/0/1, median -3.40%
- m8 vs k15: 15/0/12, median -0.15%
- m8 vs k30: 20/0/7, median -0.39%

Failures: Eberbach m3 at 1800 s ("Replayed SOC violates reserve or battery capacity")
and m5 at 600 and 1800 s ("Used bus did not finish fully replenished") - the native
solver returned a plan that the independent exact replay rejects. Counted as losses;
the same replay refusals occur elsewhere in the campaign (E4 labels, E2) and look more
frequent on pruned Eberbach models; a numerical-tolerance investigation is warranted.

## Reading

- **m=5 and m=8 are the most robust rules so far**: they beat unpruned cold on 27/30
  and 26/27 cells (median -5.0% / -6.1%) and the four-round cold4 on 25/30 and 26/27.
  Unlike any single global fraction, m=5 stays within 0.05-1.8% of the best on
  Hildenbrand (where k5/k15 lose 2.6-18.5%) and within 2.3% on every synthetic cell.
- The kept count grows with the number of trips (~5 x trips for m=5), which is the
  size-adaptive behaviour the E8 analysis suggested.
- m=3 is too tight on Hildenbrand 16 (+18.5%, same as k5) and on Eberbach.
- Against the best global fraction per regime, m5/m8 are roughly even (vs k15: 20/10,
  15/12; vs k30: 19/11, 20/7) without needing regime-specific tuning.
