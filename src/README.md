# src

Phase 0/1/2 experiment infrastructure for the price-maker EVSP
(execution plan: `../ref/RESEARCH_DIRECTIONS.md` Section 4; idea catalog:
`../ref/BRAINSTORM_20260814.md`).

## What's here

```
egglab/            the library
  instance.py      EVSP instances + synthetic generator (+ GIRO-subset loader stub)
  market.py        affine price formation p_t = a_t + b_t (U_t + L_t); welfare accounting
  solver.py        MILP backend (Gurobi via python-mip if licensed, else CBC) + stats
  evsp.py          the EVSP MILP oracle + replay validation
  regimes.py       uncontrolled / taker / strategic (B9) / dictator solves
  loops.py         Phase-1 price fixed-point iteration, cycle detection
  boundary.py      Phase-2 switch-boundary sweeps (economic vs tie-flip switches)
  records.py       Phase-0 logging contract (JSONL + provenance)
  checkpoint.py    atomic checkpoints (preemption-safe restart)
  collect.py       JSONL -> CSV aggregation
experiments/       CLI drivers (cell-indexed for Slurm arrays, resumable)
cluster/           Slurm submit scripts + results sync
tests/             smoke tests (CBC, seconds)
```

## The model (Phase-1 physics, documented choices)

Vehicle-indexed connection MILP: binary arcs chain compatible trips directly
or **via the depot**, where hourly charging variables live in the dwell
window. Vehicles start full; SOC tracked exactly along chains (big-M linking);
terminal policy: SOC after pull-in >= `soc_end_kwh` (explicit knob — see the
terminal-energy discussion in `../ref/context/`). Charging only at the depot;
no V2G yet (Chapter IV extensions). All energy regimes are MILPs:

- **taker**: linear cost `sum p_t L_t` at posted prices;
- **strategic (B9)** and **dictator**: convex separable quadratics (bill /
  true system-cost integral) represented by epigraph tangents (default 16
  segments; records carry both the model objective and the exactly recomputed
  objective, so PWL error is always visible);
- **uncontrolled**: flat-price schedule + charge-on-arrival policy.

Every solve is certified for the stated model (`exact-milp` tier): the
records include root-LP value, MIP bound, gap, sizes, wall times, backend —
so the LP/MIP integrality gap is measured on every oracle call (relevant to
B10/B37). `evsp.validate_solution` replays every solution against the
instance physics independently of the MILP.

## Datasets

Synthetic first (`instance.synthetic_instance`: two terminals + depot; tight
battery so midday charging is mandatory and price-responsive). A frozen,
simplified GIRO subset comes later via `instance.load_frozen_subset` — the
freeze must follow `../ref/context/GIRO_DATASET_HANDOFF_20260814.md` (variant
choice, deadhead fidelity disclosure, manifest, hashes).

## Run locally

```bash
cd src
pip install -r requirements.txt          # CBC bundled; Gurobi auto-detected
python3 -m pytest tests/ -q              # smoke (~5 s)
python3 experiments/run_phase1.py --list # enumerate cells
python3 experiments/run_phase1.py --cell 0 --out runs/phase1
python3 experiments/run_phase2.py --cell 0 --out runs/phase2
python3 -m egglab.collect runs -o runs/all.csv
```

## Run on the Unicorn cluster (Slurm + Gurobi)

1. Clone the repo and install `src/requirements.txt` in your env. On Unicorn,
   the submitted jobs source `cluster/unicorn_env.sh`, which activates the
   `/home/nc437/evsp_env` conda prefix, uses the shared
   `/share/apps/software/gurobi/gurobi.lic`, and requires Gurobi rather than
   silently falling back to CBC. `egglab.solver.backend()` prints the active
   backend.
2. Submit from the current interactive Unicorn login shell with
   `bash cluster/launch_phase12.sh`. The launcher verifies that `sbatch` is
   available and that Phase 1 contains exactly 128 hardened cells before it
   submits both arrays. Do not SSH from a Unicorn login node back into itself:
   that nested non-interactive shell does not expose the Slurm client path.
3. **Preemption safety:**
   jobs are `--requeue`; every driver checkpoints after each work unit
   (regime solve, loop iteration, grid point) with atomic writes, and rerunning
   the same command resumes — a preempted task loses at most one in-flight
   MILP solve. Both submit scripts request Slurm `END`, `FAIL`, and `REQUEUE`
   email notifications to `nc437@cornell.edu`. No time limits needed on solves
   (set `--time-limit` only if you want anytime behavior; the gap is recorded
   either way).
4. Ship results back:

```bash
bash cluster/sync_results.sh phase1   # aggregates runs/phase1 -> result/phase1/<stamp>/
                                      # (records.csv + checkpoint summaries) and git push
```

Raw `runs/` stays on the cluster (gitignored); only distilled results enter
git, so analysis here always has the CSVs + outcome summaries.

### Targeted overnight suite

`cluster/launch_overnight.sh` submits two checkpointed campaigns: a 288-cell
loop-only damping frontier and a 64-cell fine Phase-2 boundary map. To queue
them behind an active job:

```bash
EGG_AFTER_JOB=51417 bash cluster/launch_overnight.sh
```

The launcher caps concurrency at 24 and 16 respectively and writes a stamped
manifest under `runs/overnight/`. See
`doc/OVERNIGHT_EXPERIMENTS.md` for hypotheses, grids, resource bounds, and
decision rules.

## Statistics collected per solve (Phase-0 contract)

instance hash/name/size, price vector, regime, oracle tier, schedule hash,
load vector + hash, fleet, deadhead minutes, energy, ops/energy cost split,
model objective, solver backend/status/objective/bound/MIP-gap/root-LP
value/LP-vs-MIP gap/wall times/variable-constraint-integer counts, PWL
segment count, git commit, host, Slurm job/array/restart IDs, timestamp.

## Correctness hardening (2026-08-15 patch, reviewer-specified)

After the first Unicorn screen (2,410 GRB solves, snapshot
`result/*/20260814T233530Z`), the measurement layer was hardened:

1. **State-correct detection** (`loops.py`): the dynamical state is the price
   vector. Fixed point requires `p^{k+1} ~= p^k`; a cycle requires the price
   state to recur (j <= k-2). Repeated loads/schedules at different prices
   are recorded as recurrences, never as convergence. Full price history is
   checkpointed; price/load residuals and schedule/response recurrences are
   logged per iteration. (For alpha=1 the old response-recurrence test was
   provably equivalent; the damped runs are the ones being reclassified.)
2. **Certified adaptive convex approximation** (`regimes.py`): strategic and
   dictator objectives are solved by iterated tangent refinement — MILP lower
   bound, true-objective upper bound at the incumbent, add tangents at the
   incumbent, repeat to tolerance (default 1e-2). Records carry
   lb/ub/gap/rounds; `obj_true` is the certified feasible value.
3. **Replay validation on every production solve**: `replay_ok` +
   `replay_violations` in every record; drivers fail the cell on violation.
4. **Hardened Phase-2 classification** (`boundary.py`): -0.0-safe hashing;
   explicit 1 kWh material-load threshold; switch kinds `degenerate_tie` /
   `charging_only` / `duty_change` / `fleet_change`; and a **margin test**
   (re-realize schedule B's trip partition at A's prices via the
   fixed-sequence oracle `evsp.solve_fixed_sequences`) that separates strict
   preference changes from alternative optima (`tie_margin`).
5. **Self-describing outputs**: records carry seed/shape/b/alpha/residuals;
   `experiments/audit_runs.py` writes a completion audit + `SUMMARY.md`
   (loop-outcome tables, switch classification, adaptive gaps, replay
   status) and exits nonzero on replay failures; `sync_results.sh` runs it
   automatically.

First rerun with the hardened detector (CBC, seed 0, 8 trips, b=0.05):
alpha=1 -> certified price-state **cycle**; alpha=0.5 -> still a certified
cycle (damping at 0.5 genuinely fails here); alpha=0.25 -> reclassified to
**max_iters** (slow transient) — hence the default iteration budget is now
120. Adaptive strategic/dictator gaps closed to <= 0.005 in <= 7 rounds; all
solves replay-valid.

## Earlier sanity results (2026-08-14, pre-hardening)

- Undamped taker iteration (alpha=1, b=0.05) found a 2-cycle at iteration 3.
- Phase-2 sweep found 2 material switches; welfare ladder ordered as theory
  predicts. (Superseded by the hardened measurement above; the Unicorn
  screen snapshot under `result/` predates this patch — rerun before drawing
  conclusions.)
