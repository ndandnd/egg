# E7 results: pruning with tariff-aware (multi8) vs v8 scores

Arrays 781865 (scoring) and 781866 (30 learned4 runs, keep 0.30), all completed;
collected 14:25 UTC. Each multi8 run is paired with the v8-scored learned4 keep-0.30
run of the same case and budget (E3 phase 2 / E5). Script `pair.py`.

| Case | T s | v8 bill (buses) | multi8 bill (buses) | diff % |
|---|---:|---:|---:|---:|
| public:hildenbrand15 | 180 | 490.72 (2) | 516.48 (2) | +5.25 |
| public:hildenbrand16 | 180 | 528.06 (2) | 533.28 (2) | +0.99 |
| public:eberbach | 600 | 1252.17 (7) | 1264.49 (7) | +0.98 |
| public:hildenbrand15 | 600 | 488.71 (2) | 507.56 (2) | +3.86 |
| public:hildenbrand16 | 600 | 528.06 (2) | 529.69 (2) | +0.31 |
| public:eberbach | 1800 | 1251.77 (7) | 1265.61 (7) | +1.11 |
| scale:50000:40 | 60 | 598.39 (4) | 597.26 (4) | -0.19 |
| scale:50000:60 | 60 | 746.98 (4) | 741.83 (4) | -0.69 |
| scale:50000:80 | 60 | 900.92 (4) | 906.73 (4) | +0.65 |
| scale:50001:40 | 60 | 690.37 (4) | 686.50 (4) | -0.56 |
| scale:50001:60 | 60 | 997.31 (5) | 891.53 (4) | -10.61 |
| scale:50001:80 | 60 | 2083.56 (12) | 1960.56 (11) | -5.90 |
| scale:50002:40 | 60 | 714.87 (4) | 718.20 (4) | +0.47 |
| scale:50002:60 | 60 | 1028.91 (5) | 949.62 (4) | -7.71 |
| scale:50002:80 | 60 | 1459.20 (6) | 1278.24 (5) | -12.40 |
| scale:50003:40 | 60 | 553.28 (3) | 554.39 (3) | +0.20 |
| scale:50003:60 | 60 | 748.46 (4) | 744.75 (4) | -0.50 |
| scale:50003:80 | 60 | 1006.07 (4) | 961.62 (4) | -4.42 |
| scale:50000:40 | 300 | 596.52 (4) | 596.45 (4) | -0.01 |
| scale:50000:60 | 300 | 743.48 (4) | 744.44 (4) | +0.13 |
| scale:50000:80 | 300 | 893.14 (4) | 884.52 (4) | -0.97 |
| scale:50001:40 | 300 | 681.44 (4) | 681.63 (4) | +0.03 |
| scale:50001:60 | 300 | 888.49 (4) | 887.60 (4) | -0.10 |
| scale:50001:80 | 300 | 1243.99 (5) | 1214.11 (5) | -2.40 |
| scale:50002:40 | 300 | 714.90 (4) | 714.73 (4) | -0.02 |
| scale:50002:60 | 300 | 927.62 (4) | 929.51 (4) | +0.20 |
| scale:50002:80 | 300 | 1270.95 (5) | 1273.88 (5) | +0.23 |
| scale:50003:40 | 300 | 553.38 (3) | 553.28 (3) | -0.02 |
| scale:50003:60 | 300 | 754.58 (4) | 751.68 (4) | -0.38 |
| scale:50003:80 | 300 | 930.17 (4) | 945.52 (4) | +1.65 |

multi8 vs v8 (same case/T/keep 0.30/learned4): 16 better / 0 tie / 14 worse; median -0.01%, mean -1.03%

## Findings

- **No uniform improvement.** Overall 16 better / 14 worse, median -0.01%.
- **Scaled synthetic cases:** multi8 helps most where the budget is short and the case
  is large: at 60 s it is 4.4-12.4% cheaper on four of the eight 60-80-trip cases
  (and uses one fewer bus on three). At 300 s the arms are within ~2.4%.
- **Public cases: multi8 is worse on all 6** (+0.3% to +5.3%; Hildenbrand 15 worst).
  The tariff-diverse model improves ranking within the synthetic generator's
  distribution (E4) but that gain does not transfer to the out-of-distribution public
  networks; v8 remains the better scorer there.
- Practical consequence: keep v8 scores for public-case pruning; whether a model trained
  on both (or on public-like synthetic data) transfers better is open.
- One run per cell, 30 cells; descriptive.
