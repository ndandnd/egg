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
