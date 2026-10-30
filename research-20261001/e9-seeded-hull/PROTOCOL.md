# E9 protocol: learned plans as seeds for complete-fleet hull certification at scale

Declared 2026-10-01 14:35 UTC. Connects the learning results back to the paper's
question (physical cost D, hull cost CH, gap, own-price regret).

- Cases: scale 50000-50003 x {40, 60} trips (8) + 50000/80 and 50003/80 (stretch), `day`.
- Per case: cold hull (no seeds) vs hull seeded with the replayed plans of the learned
  300 s runs (learned4 keep 0.15, learned4 keep 0.30, learned keep 0.30; routes from
  E3/E6, charging re-optimized by the fixed-route charging LP and replayed). Hull: GRB,
  1 thread, 500 s phase / 600 s wall, 32 pricing calls, QP master, feasible-pool reuse.
  Own-price response at the cheapest seed plan (E0 response budget).
- D upper = cheapest replayed seed plan; D lower = best FULL-case planner lower bound
  among the cold/cold4 E3 runs (pruned-run bounds are not valid and are never used),
  tightened by D >= CH-lower. Gap = [max(0, D_lo - CH_up), D_up - CH_lo].
- Report per case: both hulls' status and bounds, gap interval, regret of the best seed,
  failures. 10 tasks, <= 2 concurrent, 16 GB, 30 min each.
