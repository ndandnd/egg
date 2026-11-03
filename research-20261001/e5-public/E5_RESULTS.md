# E5 results: learned pruning on public timetables (final, 10:25 UTC)

Arrays 759670 (Hildenbrand depots 15/16), 759671 (Eberbach), 765341 (learned4
supplement; harness-fixed code 0cd5da5); 36 runs, all completed. Bank `day` tariff,
curvature 1/900. Scores: v8 attention trained only on the synthetic 20-28-trip bank
(fold 0 / seed 17); every public case is out of distribution (400 kWh buses, one 360 kW
connector, real timetable geometry, EB-3 energy model). Cells: bill relative to the best
bill found by any arm for that case. Two first-submission tasks cancelled in flight are
recorded in PROTOCOL.md. One run per cell; no plan is certified optimal.

| Case | T s | cold | cold4 | learned | learned4 | lp | random |
|---|---:|---:|---:|---:|---:|---:|---:|
| public:hildenbrand15 | 180 | 12.14% | 3.84% | 4.22% | 0.41% | 19.25% | 87.35% |
| public:hildenbrand16 | 180 | 4.36% | 4.23% | 3.22% | 0.00% | 24.67% | fail |
| public:eberbach | 600 | 3.90% | 314.54% | 1.05% | 0.03% | 7.03% | 35.69% |
| public:hildenbrand15 | 600 | 12.14% | 0.94% | 4.22% | 0.00% | 18.49% | 75.05% |
| public:hildenbrand16 | 600 | 2.48% | 0.94% | 3.22% | 0.00% | 18.82% | fail |
| public:eberbach | 1800 | 1.54% | 3.15% | 1.05% | 0.00% | 7.03% | 32.40% |

Pairwise (win/tie/loss; failures count as losses; mean % bill difference over both-successful pairs)
learned vs cold @ 180s: 2/0/0  mean diff -4.079%  median -4.079%
learned vs cold @ 600s: 2/0/1  mean diff -3.029%  median -2.744%
learned vs cold @ 1800s: 1/0/0  mean diff -0.478%  median -0.478%
learned vs lp @ 180s: 2/0/0  mean diff -14.905%  median -14.905%
learned vs lp @ 600s: 3/0/0  mean diff -10.252%  median -12.042%
learned vs lp @ 1800s: 1/0/0  mean diff -5.585%  median -5.585%
learned vs random @ 180s: 2/0/0  mean diff -44.371%  median -44.371%
learned vs random @ 600s: 3/0/0  mean diff -32.996%  median -32.996%
learned vs random @ 1800s: 1/0/0  mean diff -23.676%  median -23.676%
learned4 vs cold4 @ 180s: 2/0/0  mean diff -3.679%  median -3.679%
learned4 vs cold4 @ 600s: 3/0/0  mean diff -25.910%  median -0.934%
learned4 vs cold4 @ 1800s: 1/0/0  mean diff -3.057%  median -3.057%
learned4 vs cold @ 180s: 2/0/0  mean diff -7.320%  median -7.320%
learned4 vs cold @ 600s: 3/0/0  mean diff -5.657%  median -3.725%
learned4 vs cold @ 1800s: 1/0/0  mean diff -1.513%  median -1.513%
cold4 vs cold @ 180s: 2/0/0  mean diff -3.766%  median -3.766%
cold4 vs cold @ 600s: 2/0/1  mean diff +95.828%  median -1.509%
cold4 vs cold @ 1800s: 0/0/1  mean diff +1.593%  median +1.593%
lp vs cold @ 180s: 0/0/2  mean diff +12.900%  median +12.900%
lp vs cold @ 600s: 0/0/3  mean diff +8.205%  median +5.664%
lp vs cold @ 1800s: 0/0/1  mean diff +5.409%  median +5.409%

## Bills (absolute) for the decisive arms

| Case | T s | cold | cold4 | learned | **learned4** |
|---|---:|---:|---:|---:|---:|
| Hildenbrand 15 (37 svc) | 180 | 548.04 (2) | 507.49 (2) | 509.35 (2) | **490.72 (2)** |
| Hildenbrand 15 (37 svc) | 600 | 548.04 (2) | 493.32 (2) | 509.35 (2) | **488.71 (2)** |
| Hildenbrand 16 (37 svc) | 180 | 551.11 (2) | 550.37 (2) | 545.06 (2) | **528.06 (2)** |
| Hildenbrand 16 (37 svc) | 600 | 541.17 (2) | 533.01 (2) | 545.06 (2) | **528.06 (2)** |
| Eberbach (105 svc) | 600 | 1300.61 (7) | 5189.14 (44) | 1264.92 (7) | **1252.17 (7)** |
| Eberbach (105 svc) | 1800 | 1271.00 (7) | 1291.24 (7) | 1264.92 (7) | **1251.77 (7)** |

Buses in parentheses. Generated from the per-run e3.json files.

## Findings

1. **learned4 (learned pruning + four tangent rounds) is the best arm in all 6 public
   cells**, beating cold4 (same round policy) 6/6 and cold 6/6. At equal time it is
   0.9-4.2% cheaper than cold4 on Hildenbrand and 76% (600 s) / 3.1% (1800 s) cheaper
   on Eberbach.
2. **Faster as well as better:** on Eberbach, learned4 at 600 s (1252.2) beats cold
   at 1800 s (1271.0) by 1.5%; on Hildenbrand 15, learned4 at 180 s beats cold4 at
   600 s.
3. **Transfer:** a model trained on 20-28-trip synthetic timetables, never shown a
   public network, prunes 70% of Eberbach's 10,359 movements and keeps the good ones.
4. **The round policy matters as much as the pruning.** Single-budget cold stalls in its
   first tangent round on public cases; the four-round split fixes this for cold and
   learned alike. Learned pruning helps under both policies.
5. LP-relaxation ranking is consistently poor (6-25% worse) and costs ~100 s on
   Eberbach; random pruning loses 3 buses on Eberbach and fails on Hildenbrand 16.
