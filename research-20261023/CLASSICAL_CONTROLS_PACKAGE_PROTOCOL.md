# Prospective classical-controls implementation and unit gate

24 October2026. Advance the common connection selector and charging-aware CA1
control after native-v7 qualified. This bounded package performs **no native
solve, timetable generation, model inference/training or comparison**. Do not
rerun the213-case/native matrix merely because another wake occurs. Preserve
the qualified coordinator, runner, physical/replay code, models and old evidence.

## Frozen design choices

Implement new `egglab.classical_controls` under the baseline specification and
current learned-value study addendum. These remain **unvalidated candidate
classical controls**, not established strong/optimal methods.

- Flexible movements F are direct/depot intertrip links. All pullout/pullin
  boundaries stay outside the count and are preserved in original order.
- The common price-blind backbone B takes up to three incoming and outgoing
  flexible links per trip using the existing frozen heuristic and movement-ID
  ties. Each arm/tariff variant uses the same B. Exact
  K=min(M,max((3*M+9)//10,|B|)), M=|F|. Fill F minus B by the arm's descending
  finite scores, ties by movement ID. Preserve M=0 and zero-exposure outcomes.
- Return deterministic identities, original/retained/backbone IDs, mask, counts,
  exposure and hashes. A common application helper filters a fresh NativeCase
  in original movement order, preserving every other field and the original.
  Common edge counts do not equalize topology, search difficulty or feasibility.
- CA1 uses usable battery C=battery-reserve, efficiency, declared service/leg
  energies and exactly the depot_split charging window. Grid-kWh capacity uses
  resource/market intersections, zero connectors and min(per-bus,grid) power.
  Depot pre/post-service residuals and D-U use binary64/fsum/tau1e-6 as specified.
  Borderline and stress are ranking diagnostics, never deletion/proof rules.
- Proportional-fill cost uses a*q+.5*b*q*q, not marginal price. Movement-time
  cost uses all leg durations. Positive demand with zero capacity keeps the
  specified zero proxy plus shortfall diagnostic; do not clip demand to capacity.
  The objective proxy is neither realized fleet bill nor lower bound.
- Flexible CA1 rank becomes descending integer scores in original movement
  order; boundary score0 is preserved/unranked. Validate dimensions, finite a,
  nonnegative finite b and physical schema; reject nonfinite computed features.
- Keep scalar feature/proxy/residual/window/totals and a capacity-by-period hash
  rather than every full capacity vector. Frozen inputs and module version
  permit deterministic reconstruction; document this ledger convention and
  actual complexity. CA1 sees a,b while current learned scorers see a only;
  a later comparison is of deployable methods, not equal-information learning.

No CF1 decoder/native helper is included yet. Scoring and common selection will
be charged inside each later arm's shared clock; no free cached labels, model
scores, reference plans or feasibility oracle is used here.

## One source-bound solver-free check

Use fresh `classical-controls-checks/attempt01` only after parent/static source
and test review. `classical-controls-checks/command.json` records exact argv,
executed tests, dependencies and source hashes. New tests use explicit symbolic
NativeCase fixtures, not a real dataset, generator or protected asset. Guard
native imports. Cover exact cardinality/common backbone, score and ID ties,
order/permutation identities, boundaries/zero exposure, application immutability,
charging-window/resource/market units, efficiency/reserve, tariff sensitivity,
borderline/stress conventions and counterexamples to feasibility/bill claims.

This targeted test result is a **control-unit gate**, not a replacement native
qualification receipt. Reuse v7 evidence for unchanged core sources transparently.
If old qualified test sources appear in the hash closure, distinguish them from
tests actually executed. Any later core/60s-clock/native helper change requires
appropriate affected-source tests and its own prospective native preflight;
the current30s gate does not establish60s behavior.

Carry **1293.1124853401802 charged seconds** from
`recovery-phase1-v7/accounting.json`, with all prior failures/conservative charges.
ADMIN0: shared20s is already carried. Approved1800 hard /1620 dispatch /180
shutdown reserve remain, one single-thread numerical worker and5GiB owned-tree
RSS. Budget one check40s including supervision (32.5s external allocation plus
7.5s provision): prospective cumulative1333.1124853401802. This is a planning
allowance, not a longer worker limit or guarantee. Actual complete charges count.

Use reviewed unchanged sampling/ownership/cleanup/accounting helper bodies:
30s work,32.5s absolute cleanup,0.05s target and0.25s completed-sample policy.
Verify inherited evidence, freeze exact sources/test/argv before Popen, preserve
all owned identities, unknown probe states, first/secondary failures and outputs.
Require complete accounting and confirmed absence/reap, not pytest exit alone.
Count elapsed/child allocation maximum plus supervisor CPU; monitor costs already
inside total child observations are not charged twice. No retries on failure.

Only parent may execute the one explicit command after source stability:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_classical_controls_checks.py
```

After the check, review complete receipts, preserve failures and update handoff.
Passing establishes implementation checks only; no scoring experiment, native
credibility, speedup, ML advantage, generalization or novelty follows. No new
Google Doc entry is warranted for routine unit-test preparation/pass alone.
