# Certified measurement closeout — 2026-08-16

This snapshot closes the synthetic measurement-hardening stage. All three run
roots pass expected-count completeness gates; every solve is `GRB` / `OPTIMAL`;
all 181 legacy replay failures were independently re-solved as
`certified_equivalent`; no replay failure remains unresolved.

| Campaign | Records | Completeness | Raw replay failures | Unresolved | Verdict |
|---|---:|---|---:|---:|---|
| Phase 1 | 4,131 | 128 cells and loops | 18 | 0 | PASS |
| Damping frontier | 26,598 | 288 cells and loops | 163 | 0 | PASS |
| Fine boundary | 19,264 | 64 sweeps with margins | 0 | 0 | PASS |

## Measurement-level findings

- The undamped cycle result survives corrected price-state detection.
- Damping is not a universal cure. At `b=0.05`, no tested cell reached a fixed
  point. Small damping primarily converted certified cycles into long
  `max_iters` transients; it did not establish convergence.
- At `b=0.01`, every damping value had one fixed-point cell, while the remaining
  cells were mostly cycles once alpha reached 0.15. The stability boundary is
  instance-dependent rather than a single global damping threshold.
- The fine boundary campaign found 92 economic switches in 43 of 64 cells.
  Their median L1 load jump was 35.5 kWh and the maximum was 195.8 kWh. The
  audit separately retained 2,559 degenerate ties and 89 margin-tied events.
- Measured LP-to-MIP absolute gaps remain material: median 127.401 in Phase 1,
  301.255 in the damping frontier, and 84.842 in the boundary campaign.

These are certified synthetic findings, not yet external-validity claims. The
next scientific implementation gate is B2 stabilized price negotiation,
followed by comparison against these unchanged baselines. Real-data evaluation
still depends on receiving and freezing the GIRO subset.

## Canonical inputs for analysis

- [`phase1/20260816T180507Z`](phase1/20260816T180507Z/)
- [`damping_frontier/20260816T180507Z`](damping_frontier/20260816T180507Z/)
- [`boundary_fine/20260816T180507Z`](boundary_fine/20260816T180507Z/)

Use `records.csv` for scalar analysis and `checkpoints/` for terminal outcomes,
cycle metadata, and switch details. Use `replay_effective_ok`, never a rewritten
raw flag, when filtering certified records. `SUMMARY.md` is the authoritative
audit verdict for each root.
