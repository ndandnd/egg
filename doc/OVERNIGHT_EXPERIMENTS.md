# Overnight experiment suite

This suite is the next synthetic evidence pass after the hardened 128-cell
Phase-1 and 32-cell Phase-2 rerun. It is designed to run behind the current
array and answer two questions that the original grid cannot resolve.

## A. Damping stability frontier

Primary question: how does the certified price-state outcome change with
damping as market slope increases?

- 288 cells: 16 seeds, `n_trips=12`, `b in {0.01, 0.05}`, and
  `alpha in {1, .75, .5, .35, .25, .2, .15, .1, .05}`.
- Loop-only execution with 240 iterations. Static uncontrolled/taker/
  strategic/dictator regimes are deliberately skipped because they are
  invariant to alpha and are already measured by the main hardened run.
- Array concurrency is capped at 24 to limit Gurobi-token and node pressure.
- Output: `runs/overnight/<stamp>/damping_frontier/`.

Primary summaries:

1. fixed-point/cycle/max-iteration frequency by `(b, alpha)`;
2. iterations and terminal price residuals conditional on outcome;
3. cycle lengths and the empirical critical-alpha interval by seed;
4. LP-vs-MIP gap distributions near and away from the stability boundary.

Decision rule: proceed to B2 stabilized negotiation if instability remains
material at moderate damping or if small alpha converts cycles into long
transients rather than reliable convergence. Treat an apparently monotone
alpha frontier as a hypothesis to prove, not as a theorem.

## B. Fine Phase-2 boundary replication

Primary question: do material switches and their four-way classification
survive a finer price grid and new seeds?

- 64 cells: 8 seeds, `n_trips in {8, 12}`, slots `{8, 12, 16, 20}`.
- Delta range `[-1.5, 1.5]` with step `0.01` (301 points per cell), with the
  hardened fixed-sequence margin test enabled.
- Array concurrency is capped at 16.
- Output: `runs/overnight/<stamp>/boundary_fine/`.

Primary summaries:

1. counts of `degenerate_tie`, `charging_only`, `duty_change`, and
   `fleet_change` switches;
2. load-jump distribution and switch density by size/slot;
3. agreement of coarse-grid switch intervals with fine-grid locations;
4. LP-vs-MIP gap around material switches versus smooth regions.

Decision rule: retain the boundary/uplift atlas only if material switch rates
and jump sizes survive margin testing and additional seeds. Fine-grid-only
micro-switches below the 1 kWh threshold remain non-economic.

## Resource and reproducibility policy

The two arrays contain 352 cells total, with maximum concurrent occupancy of
40 tasks. Phase 1 can perform at most 69,120 loop oracle calls; Phase 2 has
19,264 base grid points plus re-realization margin tests. Both use 24-hour
Slurm limits, atomic checkpoints, `--requeue`, Gurobi-only preflight, and email
notifications.

Every launch receives one UTC stamp and writes
`runs/overnight/<stamp>/MANIFEST.txt` containing the Git commit, Slurm IDs,
dependency, grids, and concurrency limits. Raw runs remain gitignored.

Submit from an interactive Unicorn login shell after the current Phase-1 job:

```bash
EGG_AFTER_JOB=51417 bash cluster/launch_overnight.sh
```

Omit `EGG_AFTER_JOB` to submit immediately. After completion, audit each suite:

```bash
python experiments/audit_runs.py runs/overnight/<stamp>/damping_frontier
python experiments/audit_runs.py runs/overnight/<stamp>/boundary_fine
```
