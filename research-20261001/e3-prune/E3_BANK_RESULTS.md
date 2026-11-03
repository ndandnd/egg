# E3 bank phase: learned pruning on 16 TRAIN timetables (20-28 trips), `day` tariff

Arrays 759091 (cold/learned/lp/random), 759672 (cold4), 761834 (learned4); 192 runs,
all completed, collected 07:30 UTC. Cells show the bill relative to the best bill
found by any arm/budget for that timetable (0.00% = best). "fail" = no replayed plan.
Scores: v8 attention, OUTER-fold model per timetable (never fitted on it).

| Case | T s | cold | cold4 | learned | learned4 | lp | random |
|---|---:|---:|---:|---:|---:|---:|---:|
| bank:10064 | 10 | 0.35% | 0.32% | 0.00% | 0.03% | 0.55% | 19.91% |
| bank:10065 | 10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 40.76% |
| bank:10066 | 10 | 0.32% | fail | 0.00% | 0.02% | 15.72% | 29.81% |
| bank:10067 | 10 | 0.00% | 0.01% | 0.00% | 0.01% | 0.00% | 48.62% |
| bank:10068 | 10 | 0.00% | 0.01% | fail | fail | 0.00% | 20.25% |
| bank:10069 | 10 | 1.05% | 13.67% | 0.10% | 0.10% | 39.63% | 29.15% |
| bank:10070 | 10 | 0.16% | 0.02% | 0.01% | 0.02% | 2.60% | 20.80% |
| bank:10071 | 10 | fail | 0.01% | 0.00% | 0.00% | 0.00% | 59.87% |
| bank:10072 | 10 | 0.11% | 0.11% | 0.33% | 0.34% | 1.00% | 58.18% |
| bank:10073 | 10 | 0.00% | 0.00% | 0.00% | 0.03% | 0.00% | 26.17% |
| bank:10074 | 10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 65.04% |
| bank:10075 | 10 | 0.79% | 0.79% | 0.12% | fail | 41.30% | 38.76% |
| bank:10076 | 10 | fail | 0.01% | 0.00% | 0.01% | 0.00% | 34.44% |
| bank:10077 | 10 | fail | 0.00% | 0.00% | 0.00% | 0.00% | 52.96% |
| bank:10078 | 10 | 0.09% | fail | 0.09% | 0.10% | 32.84% | 17.96% |
| bank:10079 | 10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.55% | 62.59% |
| bank:10064 | 30 | 0.00% | 0.00% | 0.00% | 0.03% | 0.55% | 19.91% |
| bank:10065 | 30 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 40.76% |
| bank:10066 | 30 | 0.00% | 0.03% | 0.00% | 0.02% | 15.72% | 29.81% |
| bank:10067 | 30 | 0.00% | 0.01% | 0.00% | 0.01% | 0.00% | 48.62% |
| bank:10068 | 30 | 0.00% | 0.01% | fail | fail | 0.00% | 20.25% |
| bank:10069 | 30 | 1.12% | 0.79% | 0.00% | 0.00% | 39.33% | 29.07% |
| bank:10070 | 30 | 0.04% | 0.04% | 0.00% | 0.01% | 2.59% | 20.80% |
| bank:10071 | 30 | 0.00% | 0.01% | 0.00% | 0.00% | 0.00% | 59.80% |
| bank:10072 | 30 | 0.00% | 0.00% | 0.33% | 0.34% | 0.99% | 58.18% |
| bank:10073 | 30 | 0.00% | 0.00% | 0.00% | 0.03% | 0.00% | 26.17% |
| bank:10074 | 30 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 65.04% |
| bank:10075 | 30 | 0.24% | 0.16% | 0.00% | 0.01% | 40.75% | 38.76% |
| bank:10076 | 30 | 0.00% | 0.01% | 0.00% | 0.01% | 0.00% | 34.44% |
| bank:10077 | 30 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 52.96% |
| bank:10078 | 30 | 0.02% | 0.00% | 0.09% | 0.10% | 32.83% | 17.96% |
| bank:10079 | 30 | 0.00% | 0.00% | 0.00% | 0.00% | 0.55% | 62.59% |

Pairwise (win/tie/loss; failures count as losses; mean % bill difference over both-successful pairs)
learned vs cold @ 10s: 9/4/3  mean diff -0.183%  median -0.001%
learned vs cold @ 30s: 6/7/3  mean diff -0.066%  median -0.000%
learned vs lp @ 10s: 8/7/1  mean diff -6.664%  median -0.546%
learned vs lp @ 30s: 8/7/1  mean diff -6.646%  median -0.546%
learned vs random @ 10s: 15/0/1  mean diff -27.789%  median -27.847%
learned vs random @ 30s: 15/0/1  mean diff -27.796%  median -27.934%
learned4 vs cold4 @ 10s: 5/5/6  mean diff -0.998%  median +0.000%
learned4 vs cold4 @ 30s: 5/5/6  mean diff -0.033%  median +0.000%
learned4 vs cold @ 10s: 7/1/8  mean diff -0.129%  median +0.001%
learned4 vs cold @ 30s: 3/0/13  mean diff -0.056%  median +0.003%
cold4 vs cold @ 10s: 5/3/8  mean diff +1.122%  median +0.001%
cold4 vs cold @ 30s: 3/1/12  mean diff -0.021%  median +0.002%
lp vs cold @ 10s: 5/3/8  mean diff +10.038%  median +0.550%
lp vs cold @ 30s: 0/8/8  mean diff +8.211%  median +0.275%

## Failures (all kept; none reinterpreted)

- `TimeoutError: Native remaining-time budget exhausted` (harness artifact; a late
  tangent round discarded earlier plans): 10066 cold4, 10071 cold, 10075 learned4,
  10076 cold, 10077 cold, 10078 cold4 - all at T=10 s. Harness fixed (code 0cd5da5);
  these 6 cells are rerun once as `-hfix` (job 765335) and reported separately.
- `Whole-incumbent charge projection exceeds roundoff budget` (native extraction
  refusal; genuine): 10068 learned and learned4 at both budgets.

## Reading

- **Scores carry real information.** Learned pruning beats random pruning (same 30%
  keep rule) on 15/16 timetables by ~28% of the bill.
- **Learned ranking beats LP-relaxation ranking**: 8 wins / 7 ties / 1 loss at both
  budgets; LP ranking is badly wrong on some instances (+15-41%). LP x-values are a
  poor pruning signal here.
- **Against cold at the same single-budget policy**: 9/4/3 at 10 s (mean -0.18%) and
  6/7/3 at 30 s (mean -0.07%). The gains concentrate on the two hard timetables:
  10069 (cold +1.05% / +1.12%, learned +0.10% / 0.00%) and 10075 (cold +0.79% / +0.24%,
  learned +0.12% / 0.00%). Losses: 10072 and 10078 (+0.33% / +0.09% vs best; pruning
  removed a movement the best plan uses) and the 10068 extraction refusals.
- **With the four-round split** (learned4 vs cold4) the result is a wash (5/5/6).
- At this size the solver is already near-optimal within 10-30 s, so differences are
  mostly < 0.5%; the decisive test is the 40-80-trip phase (761781) where E2 shows
  cold leaves 2-79% gaps.
