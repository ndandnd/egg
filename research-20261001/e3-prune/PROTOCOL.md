# E3 protocol: learned pruning vs LP pruning vs cold, at equal wall time

Declared 2026-10-01 at launch of the bank phase (job 759091). Driver
`src/experiments/claude_e3_prune.py`; scores `src/experiments/claude_score_v8.py`.

- Scores: v8 graph-attention models (selected at INNER loss). Bank groups use the seed-17
  model of the fold where the group is OUTER; scaled cases use fold 0 / seed 17.
  Scores use the target (`day`) tariff's price features.
- Arms, all GRB 1 thread, curved planner (tangent rounds, max 8), total wall T:
  `cold` (full case); `learned` (keep top 30% of direct/depot movements by v8 logit);
  `lp` (same ranking by full LP-relaxation x of the linear-price MIP, LP time charged);
  `random` (seeded random ranking; pruning-only control). Every trip keeps >= 3
  incoming and >= 3 outgoing direct/depot options; pullouts/pullins always kept.
- Plans are replayed on the full case and billed exactly under `day`.
- Phase 1 (bank, 16 TRAIN groups 10064-10079): T in {10, 30} s.
  Phase 2 (scaled claude-scale-v1 50000-50003 x {40, 60, 80} trips): T in {60, 300} s,
  launched after E2 shows where cold is slow.
- Primary metric: bill relative to the best bill found by any arm/budget for that case.
  Go (learned pruning useful): learned beats both lp and cold at the same T on >= 70%
  of phase-2 cases. A failed/infeasible pruned arm counts as a loss.

## Phase 2 launch, 06:25 UTC

Launched on 12/18 E2 cells (cold at 600 s leaves 2-79% gaps at 60-80 trips; go).
Cases scale:50000-50003 x {40, 60, 80} trips, arms cold / cold4 / learned / lp /
random (cold4 added after the bank launch to separate route quality from extra
tangent rounds), T in {60, 300} s, keep 30%, 16 GB. 120 runs, throttled to fit the
Gurobi concurrency cap. Primary metric and go criterion unchanged.

## learned4 supplement, 06:35 UTC

First E5 rows showed the single-budget `cold` arm stalls in its first tangent round
on public-scale cases (Hildenbrand 15: 548.04 at both 180 and 600 s) while `cold4`
reaches 507.49, so the round split matters as much as pruning. Added arm `learned4`
(learned pruning + the cold4 four-round split) as dependent supplements that start
after the main arrays: bank (32 runs), scale (24 runs), public (6 runs). Reported
comparisons: learned vs cold (same single-budget policy) and learned4 vs cold4 (same
four-round policy). No earlier result is discarded or re-labelled.

## Harness correction, 07:30 UTC (after reading bank results)

Bank analysis found 6 cells failing with `TimeoutError: Native remaining-time budget
exhausted`: `solve_planner` started a further tangent round with no time left and the
exception discarded the plan already found in earlier rounds. This is a measurement
artifact of the harness, not a solver outcome. From code ad7d912 onward the driver
replaces a no-time round with a `HARNESS_NO_TIME_LEFT` status so the planner returns
its best plan (solver math unchanged). The 6 affected bank cells are rerun once under
`-hfix` output names; the original failed rows are kept and reported. The same rule
applies to any later artifact failures in the scale/public phases. Extraction
refusals ("charge projection exceeds roundoff budget") are genuine failures and are
not rerun.
