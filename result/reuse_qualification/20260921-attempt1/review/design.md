# Minimal runnable reuse qualification

Prepared 2026-09-21, before executing the reuse trajectory. The parent task
authorized implementation after the initial design read. This note documents
the engineering decision; the versioned protocol in the worktree is the
prospective experiment specification.

Sources inspected: PR53 `doc/REOPTIMIZATION_PILOT_DESIGN.md`, production
`src/egglab/b2a2.py`, `b2a345.py`, `checkpoint.py`, `evsp.py`, `regimes.py`,
`instance.py`, `solver.py`, `market.py`, existing A2 tests, and the September 21
optimization literature review. No raw research outcomes, protected seed
files, private benchmark data or cluster experiments were opened or run.

## Decision

Build an isolated, small driver using clean A2 helper APIs rather than editing
production checkpoint identities. A2's normal checkpoint deliberately binds
the market hash, solver settings and tolerances. A changed tariff is a new
optimization problem; resuming the old checkpoint would carry invalid bounds,
dual state and histories. The fresh-state driver imports physical columns
explicitly, while resetting all numerical optimization state.

Owned implementation files in `physical-reuse-qualification-work`:

- `src/experiments/reuse_qualification.py`
- `src/tests/test_reuse_qualification.py`
- `doc/REUSE_QUALIFICATION_PROTOCOL_20260921.md`

No production module is modified. The adapter calls
`b2a2.solve_rmp(inst, market, columns, tangent_points, pwl_tol=...)` for an
ordinary clean master, `regimes.solve_taker` for complete physical pricing,
`b2a2.canonicalize_pricing_solution` for physical load/objective reconstruction,
`column_from_solution` for checked projected columns, and `pricing_incumbent`
for the cost of the exact retained column. The certificate is recomputed as
`z_model + min(0, pricing_bound - sigma)`, with exact quadratic upper evaluation.
No stabilized price, proposal incumbent, or past-state bound enters that
formula. `b2a345.theta_cert` is intentionally unnecessary in this qualification;
there is no extra dual-bound route to audit.

## Deliberately small workload

A hand-authored one-bus instance has two 15-kWh trips separated by two charging
hours, a 20-kWh starting battery, and 10-kW charging. It therefore needs 10 kWh
distributed continuously between the two hours. No random seed or protected
experiment identity is needed. The trajectory is flat tariff, unchanged tariff,
positive two-slot tilt, negative tilt. It is a three-state tariff trajectory
with an inserted zero-change control, four states in total.

The independent analytic optimum is explicit: charging loads (5,5), (5,5),
(4,6), (6,4), with total objectives 18,18,17.8,17.8. That oracle audits the
finished bounds only. It never enters the optimization as a column, price,
tangent, initial bound or future-state cache.

Three arm trajectories each pay for their own cold state zero:

1. Cold A2-style clean CG at every state.
2. The immediately preceding certified physical pool from the same arm.
3. The same reuse policy, plus exactly one full pricing call at the arm's own
   previous final clean price plus the tariff change.

The control with no tariff change is consequential: the third arm still pays
for its proposal, even when it repeats or duplicates an existing column.
This is the low-cost baseline a learner would need to improve on eventually.
The one-bus fixture can be solved by two extreme charging columns, so strong
reuse may already certify with one final clean pricing call. That outcome is
an informative negative control, not evidence that learning is useless in
larger or combinatorially harder settings.

## Isolation and physical evidence

Every state runs in a separate subprocess. Reuse accepts only the same arm's
immediately preceding certified state with matching configuration, instance
and previous market identity. It returns only a deep copy of checked columns.
The analytic arm separately reads its own previous clean price. Each state
has empty tangent points, fresh negative-infinite lower bound, fresh duals,
fresh event streams and fresh retry state. Cold states receive no predecessor.
The protocol never resumes or rewrites a production checkpoint.

Production `solve_rmp` checks load dimensions, signs and finite costs; it is
not sufficient to authenticate imported physical schedules. The adapter
therefore checks instance identity, exact trip coverage, fleet/arc shapes,
charge ownership, aggregate energy per arc/slot against the charging window,
stored load against summed charge events, intrinsic operating cost rebuilt
from fleet/deadhead, and the full projected column hash. Then it calls the
ordinary independent replay for SOC/timing and verifies the original oracle
status/bound-presence/reconstruction policy. Stored `replay_ok=true` is never
accepted as a substitute for recomputation.

Every novel column is retained, including a terminal pricing column. The
common pool cap 96 equals four states times 24 calls; there is no eviction within
this qualification. Reaching the cap fails explicitly. In a larger pilot,
eviction and duplicate policies need their own prospective freeze; copying
this qualification's no-eviction assumption would be inappropriate.

## Cost, bounds and failure handling

Each state allows 24 pricing calls including seed/proposal, a 40-second hard
subprocess limit, and 10 seconds per native solve. The complete twelve-cell
grid has a 300-second admission budget, runs sequentially and uses one CBC
thread. LP-first optimization is also capped through `model.max_seconds`.
The supervisor kills an overrun process group and leaves evidence. A failed
predecessor prevents dependent reuse states from running; cold states remain
independent. There are no automatic retries or expansions.

All arms use epsilon 0.01 and tangent tolerance 0.001. Each final interval must
contain the independent analytic optimum. The driver records full master
evidence, native solver statuses/objectives/bounds, pricing vectors and cost
intervals, reduced costs, proposal novelty, replay cost, worker CPU, solver
wall time, and complete subprocess elapsed time. Complete elapsed time covers
interpreter startup, dependency imports, data input and output; it is the
primary time measure. Twelve tiny cells in a fixed order cannot establish
a statistically useful speedup. Only correctness and costs on this fixture
are claimed.

Runtime provenance includes exact source hashes and commit, Python executable,
mip/cbcbox/numpy versions, and the actual loaded CBC native library path/hash.
The first run must follow a source/protocol freeze by the parent task. Output
roots are exclusive, preserving failures and avoiding accidental overwrites.

## Before native execution

Fifteen tests pass with fabricated physical solutions and fake native oracles.
They test analytic optimum/price translation, cross-arm/future/changed-market
rejection, corrupt physical evidence despite a true stored replay flag,
isolated copies, and exclusion of a stale bound 1e9 and proposal bound -99999
from the clean certificate. These are adapter unit tests, not a native-solver
qualification. The restored solver was separately qualified by another agent.

## Remaining risks and follow-on workload

The original Instance/EVSP has no shared charger or grid capacity field. This
driver qualifies reuse under its fixed original physics. The parent task's
separate continuous physical adapter addresses shared capacity; changing that
capacity would change feasible-column identities and must not reuse this
fixed-physics contract implicitly.

The one-dimensional trajectory is intentionally elementary; the optimum price
is nearly constant while charging quantities move. It does not stress dual
prediction, multiple fleet structures, degenerate optimal faces, or hard MILP
pricing. After correctness passes, the next useful step is a separately frozen
small, richer fixed-physics workload with more trips and competing structures.
Retained columns and the analytic proposal must still be charged equally and
finish through the same certificate. Only evidence of avoidable discovery cost
would justify an ML data-generation campaign.

PR53's 24-base seed-allocated training/validation/test pilot remains untouched.
Its 448 CPU-hour proposed ceiling excludes engineering qualification and is not
needed for this local check. No Utrecht schema translation is necessary here:
the public dataset is a later operational-relevance lead, and its units and
charging-capacity assumptions need a separate import/replay review.
