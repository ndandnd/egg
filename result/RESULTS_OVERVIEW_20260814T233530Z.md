# Unicorn results overview — 2026-08-14 snapshot

This is the analysis landing page for the complete Unicorn pilot/full-array
run. Open this file first in Cursor, then follow the phase-specific snapshot
README files.

## Snapshot map

| Experiment | Records | Checkpoints | Snapshot |
|---|---:|---:|---|
| Phase 1 loops | 458 | 64 cells | [phase1/20260814T233530Z](phase1/20260814T233530Z/) |
| Phase 2 boundary sweeps | 1,952 | 32 sweeps | [phase2/20260814T233530Z](phase2/20260814T233530Z/) |

All recorded solves used `GRB` and reported `OPTIMAL`. The largest recorded
MIP gaps are below `8e-8` in Phase 1 and below `3e-7` in Phase 2; inspect the
CSV columns beginning with `solver_` for the full per-solve statistics.

## First readout

- Phase 1 has 32 cycle outcomes and 32 fixed-point outcomes across the 64
  cells. Of the cycle outcomes, 27 have length 2; the remaining lengths are
  3, 5, 7, and 11.
- The `s0_n8_slot12` Phase 2 sweep reproduces the two genuine load-jump
  switches at 14 and 57 kWh. Tie-flip switches are retained in the checkpoint
  data and should remain separate from the economic-switch statistic.
- The full Phase 2 array contains 32 completed sweep checkpoints. Use
  `n_switches`, `n_economic_switches`, and the `switches` list in each
  `sweep.ckpt.json` as the authoritative boundary summary.

## Suggested analysis order

1. Group `phase1/.../records.csv` by seed, fleet size, depth, damping, and
   `x_outcome_type`; use checkpoint JSON to verify one outcome per cell.
2. Group Phase 2 checkpoint summaries by seed, trip count, and slot count;
   report economic switches and tie flips separately.
3. Summarize the per-solve `solver_lp_obj`, `solver_obj`, `solver_bound`, and
   `solver_lp_mip_gap_abs` fields before making any claims about B10/B37.
4. Only then make figures/tables and start the next implementation PR.

Raw JSONL remains in gitignored `src/runs/`; the committed CSVs and small
checkpoint summaries are the reproducible handoff for analysis.
