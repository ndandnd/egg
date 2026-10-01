# E5 results (interim, 09:25 UTC): learned pruning on public timetables

Arrays 759670 (Hildenbrand depots 15/16, 20 runs) and 759671 (Eberbach, 10 runs), all
completed; learned4 supplement 765341 still running. Bank `day` tariff, curvature 1/900,
v8 attention scores from a model trained only on the synthetic 20-28-trip bank (all
public cases are out of distribution). Cells: bill relative to the best bill found by
any arm for that case.

| Case | T s | cold | cold4 | learned | learned4 | lp | random |
|---|---:|---:|---:|---:|---:|---:|---:|
| public:hildenbrand15 | 180 | 11.68% | 3.42% | 3.80% | 0.00% | 18.76% | 86.59% |
| public:hildenbrand16 | 180 | 3.40% | 3.26% | 2.26% |  | 23.52% | fail |
| public:eberbach | 600 | 2.82% | 310.23% | 0.00% |  | 5.92% | 34.28% |
| public:hildenbrand15 | 600 | 11.68% | 0.53% | 3.80% |  | 18.01% | 74.33% |
| public:hildenbrand16 | 600 | 1.53% | 0.00% | 2.26% |  | 17.72% | fail |
| public:eberbach | 1800 | 0.48% | 2.08% | 0.00% |  | 5.92% | 31.02% |

## Eberbach (105 services, 10,359 movements; never solved before)

| Arm | T=600 s | T=1800 s |
|---|---|---|
| cold | 1300.6 (7 buses) | 1271.0 (7) |
| cold4 | 5189.1 (44) | 1291.2 (7) |
| **learned** (3,255 movements kept) | **1264.9 (7)** | **1264.9 (7)** |
| lp (LP time 98-105 s) | 1339.7 (7) | 1339.7 (7) |
| random | 1698.6 (10) | 1657.3 (10) |

## Reading

- **Eberbach:** learned pruning gives the best plan of any arm, and at 600 s already
  beats cold at 1800 s (1264.9 vs 1271.0); at equal 600 s it is 2.7% cheaper than cold
  and 76% cheaper than the four-round cold4 split (which finds only a 44-bus plan in
  150 s rounds). LP pruning loses ~100 s to the LP and ranks worse; random pruning
  costs 3 extra buses. A model trained on synthetic 20-28-trip timetables transfers to
  a real 105-service network.
- **Hildenbrand (37 services):** learned beats single-budget cold in 3 of 4 cells
  (-4%), but the four-round cold4 split is best at 600 s on both depots; the matching
  learned4 comparison is still running.
- One run each, three public cases, synthetic tariff: descriptive evidence, not a
  statistical test. No arm's plan is certified optimal.
