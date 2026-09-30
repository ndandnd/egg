# ML warm-start training-data emission — specification

Status: **engineering-tier data generation.** This produces training data
for a future machine-learning experiment; it is **never scientific
evidence**. The ML model's outputs (predicted duals, pricing-network
reductions, pricing-value regressions) are **never a certificate** — the
exact certified oracle (`egglab.b2a2.certified_cg`) remains the sole
certifier. Nothing here authorizes, replaces, or annotates any scientific
population.

Producer: `src/experiments/emit_cg_training_data.py`. Tests:
`src/tests/test_cg_training_data.py`.

## 1. Purpose

Warm-starting the certified column-generation negotiation across the
price-feedback loop is textbook **parametric reoptimization** (same
instance, shifting prices). The published literature reports ~2x speedups
to a *certified* gap when predicted duals seed the stabilization center.
Every candidate ML target — dual prediction, pricing-network reduction,
pricing-value regression — is trainable from the **same solve logs**, so
the **logging schema is the real deliverable**, not the instance count.

## 2. Hard constraints

- **Seed namespace.** Seeds `0-15` (B2/B3 populations), `16-31` (A6
  holdout), `32-37` (frozen B3 confirmation), and `38-47` (reserved) are
  each committed to a scientific population. This driver generates
  **exclusively from seeds `>= 10000`** and refuses any lower seed by name.
- **Isolation.** It reads no `runs/b3_factor_pilot` outcome and no A6 path,
  writes only under the supplied `--out` (never a default under `result/`
  or the pilot tree), and edits no decision log or research-status file.
- **Solver.** Tests run on CBC (do not set `EGGLAB_REQUIRE_GRB`); nothing
  is launched.

## 3. Grid (stratified)

`n_trips ∈ {8, 10, 12, 16}` × `b ∈ {0.0, 0.01, 0.05}` × `battery_kwh ∈
{45, 60, 90}` × `charge_power_kw ∈ {75, 150, 300}` (battery/charge reuse
the frozen B3 screen levels) × seeds `{--seed-base .. --seed-base+--count-1}`
(`--seed-base >= 10000`). That is **108 cells per seed**. All other
generator arguments are the frozen held-fixed family (`soc_*_frac`,
`trip_energy_range`, day window, `max_vehicles`).

A first tranche should be **bounded** (order 1,000-2,000 instances at
`n_trips <= 16`), not open-ended; `--dry-run` prints the exact cell list
and an estimated CPU-hour cost before any solve.

## 4. Per-solve JSONL schema (`record.jsonl`, one record per cell)

```
schema, evidence_tier, code_commit
identity:            instance_hash, market_hash, seed, n_trips, b,
                     battery_kwh, charge_power_kw, epsilon, tol_d, budget,
                     solver{backend, mip_gap}
posted_prices:       full posted price vector
posted_prices_sha256
iterations[]:        index, terminal, master_objective (z_rmp_model),
                     convexity_dual (sigma), incumbent_ub (ub_ch),
                     certified_lb (lb_best), iteration_lb_ch,
                     min_reduced_cost_lb, min_reduced_cost_ub,
                     pricing_solve_id, pricing_dual_bound, pricing_incumbent
rmp_duals_canonical: method, n_samples, pi[], sigma, z_model, ub,
                     pi_sample_spread
dual_canonicalization: method, n_samples
columns[]:           column_key, load[], ops_cost, reduced_cost_final,
                     margin_to_pool_min, replay_ok
column_pool_min_margin
certificate:         ub_ch, lb_best, gap, certified, outcome_type,
                     oracle_calls_total, oracle_calls_clean
dictator:            z_d_ub, z_d_lb, gap, converged, status  (or null)
time_limit_s, incomplete, incomplete_reason
```

Every numeric field is re-derivable: a consumer can recompute each
column's reduced cost from `load`, `ops_cost`, and the canonical duals
(`rc = ops_cost - pi·load - sigma`) and recompute the certificate gap
(`ub_ch - lb_best`); the tests do exactly this.

## 5. Two load-bearing label-quality rules

1. **Canonicalize the duals.** Raw last-iterate simplex duals are the
   noisiest possible label because the LP dual optimum is typically a face,
   not a point. The driver emits an **optimal-face representative** — the
   mean of the RMP duals over several deterministic optimal-face samples
   (column rotations), method
   `optimal_face_average_over_column_rotations`, recorded per record with
   the sample count and the observed `pi_sample_spread`. The raw last
   simplex iterate is **never** emitted alone. (Rationale: a
   barrier/interior solution without crossover is the ideal representative;
   python-mip's CBC backend does not expose one, so the documented fallback
   — averaging over optimal-face samples — is used.)
2. **Emit margins, not just argmins.** For each accepted column the record
   carries its reduced cost and `margin_to_pool_min`, and the record
   carries `column_pool_min_margin` (the separation between the best and
   second-best column in the final pool). This is the direct answer to the
   project's own measurement that degenerate tie changes outnumbered
   economically meaningful switches 2,559 to 92: downstream training can
   apply **margin filtering** to drop degenerate labels.

## 6. Driver shape and resumability

Standard `run_*.py` conventions: `argparse` parser `ap`; hyphenated flags
with snake_case `dest`; `--list`, `--cell K`, `--all`, `--out` (default
under `runs/`), `ap.error(...)` when no mode is given. Additional flags:
`--seed-base` (`>= 10000`), `--count`, `--time-limit-s` (per-cell wall
cap; a cell that exceeds it is marked `incomplete`, never silently
truncated), `--with-dictator`, `--per-cell-cpu-h-estimate`, and
`--dry-run`.

Each cell's certified CG state is atomically checkpointed
(`egglab.checkpoint`), so a tranche resumes; the emitted record is a
**deterministic function of the committed checkpoint** (no wall-clock
timing is embedded), so a resumed emission is byte-identical.

## 7. Non-goals

No cluster commands, no launching, no reading of pilot outcomes or any A6
path, no `result/` writes, and no scientific claim of any kind. The only
deliverable is the schema and the logs it defines.
