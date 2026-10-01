# E0 protocol: price-support evidence on the v7 TRAIN groups

Declared 2026-10-01 before launch. Driver: `src/experiments/claude_e0_support.py`.

- Groups: TRAIN 10064-10079 (the v7 pilot), market `day` (cheap 10:00-14:00 at 0.10,
  else 0.30, curvature 1/900 per hour). Exploratory TRAIN only; DEV/TEST sealed.
- Purpose: obtain physical cost D, hull cost CH, gap D-CH and own-price regret of the
  v7 cold incumbent. v7's hull controls all failed on the `pool_tol` keyword typo;
  this is a new attempt identity, not a retry of v7 (v7 failures stay in its ledger).
- Stages per group: cold hull, retained hull (seeded with the two admitted source
  fleets), own-price response at the cold incumbent's marginal prices a + b*load.
- Budgets (sized, not v7's): hull GRB 1 thread, 150 s phase / 180 s wall, 16 pricing
  calls, 64 masters, pool cap 48, 8192 rational bits, 20 s polish, QP master,
  feasible-pool reuse. Response: 50 s phase / 60 s wall, one round.
- D interval: v7 cold planner bounds (reused, native tolerance-qualified), tightened
  by D >= CH lower. CH upper also capped by D upper. All intervals reported as
  computed; no stage is retried; failures are reported.
- Resources: one array of 16 tasks, <=4 concurrent, 1 CPU / 8 GB / 20 min each,
  excluding scaglione-compute-01. Expected ~0.5 CPU-hours.
- Reporting: per-group D, CH, gap, regret, statuses and wall times, and how many
  groups certify a strictly positive gap or a zero gap.
