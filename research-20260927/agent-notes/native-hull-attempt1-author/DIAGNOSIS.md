# Author diagnosis of preserved native hull V1 attempt

This is a read-only diagnosis of `result/native_hull/20260927-attempt1`, frozen
source `f549100`. No optimizer was executed, no raw receipt was modified and no
failed result is reclassified. Independent result audit is separate. Detailed
per-cell comparisons are in `trace-diagnosis.json`.

The eight-cell run has two certified cells, four master-budget failures and two
correctly blocked retained successors. All six attempted independent states
have complete native accounting. The four failures each used 64 master calls
and two pricing calls (one seed), with only 0.28–0.35 seconds total native solve
time; the binding resource was the master call cap, not elapsed time. The full
run was 14.09 seconds, including a roughly ten-second pricing phase in the
certified tilted case. All 280 native starts have matching returns: 266 master
and 14 pricing phases.

## Cause: tangent-LP precision is not first-order pool stationarity

Nominal base master calls 17–63 repeat exactly the same early load
`6.75018310538372`, with restricted-pool gap
`0.0004943979470712689 > 1e-6`. The last true mixture objective is
`94.88750000670554`; it is about 6.7e-9 above the exact minimum of that saved
two-column pool. One earlier saved point is even better (`94.88750000298026`).
The maximum exact violation of a saved final epigraph inequality at the raw
LP primal is about 9.31e-9. Appending the same tangent therefore keeps returning
a native `OPTIMAL` LP under its numerical tolerances without closing the much
more demanding first-order gap.

The joint case similarly repeats near early load `7.4684576738` for 47 late
master calls (32 copies of one stored point and 15 of a nearby point). Its final
pool gap is `0.0005599893611356335`; maximum saved tangent epigraph deficit is
about 1.01e-8. These values are numerical LP evidence, not a global-model error.
The source's independent primal check allowed its frozen tolerance, while its
stricter pool test correctly refused to advance to pricing.

For a quadratic on a fixed segment, true-objective error is second order in
load error, whereas the restricted-pool first-order gap is generally first
order. An objective approximation accurate to around 1e-8 need not produce a
1e-6 first-order gap. Raising the master cap alone would merely repeat the same
point and tangent. Loosening the pool/final criteria would change the quality
requirement rather than address this progress defect.

The joint saved two-column minimum is **not** its complete-fleet CH target:
its retained pool is incomplete and requires another clean pricing call after
restricted-pool refinement. The diagnostic JSON's closed-form segment minimum
uses only saved column projections and stored coefficients; it is a restricted
arithmetic check, not a retrospective global certificate or a new native solve.

## Secondary reporting defect: useful upper bounds did not reach final state

V1 updates `best_mixture` only after its inner restricted-master routine returns.
On a master cap, the raw `master_replay` events preserve improved feasible upper
bounds, but the terminal result still reports the seed bound: nominal 104 and
joint 110.56509695290865. The best saved joint master upper is
103.62710280497646. Streaming every replayed mixture to the state-level upper
bound is sound because any feasible convex mixture supplies an upper bound,
whether or not its pool has converged. It cannot provide a missing global lower
bound or retroactively certify a failed cell.

## Prospective V2 correction

Retain the same eight scientific inputs, target values, solver status/bound
admission, 1e-6 pool criterion, 1e-4 global criterion and native caps. Use one
ordinary native LP per pool, followed by generic exact-rational pairwise
simplex line searches. A step moves mass from a positive-weight maximum-score
column to a minimum-score column, clipped at the available away mass. The
quadratic along that direction supplies the exact minimizer; a beneficial
zero-curvature direction takes the full away mass. Each accepted step preserves
nonnegative exact weights with total one, retains every positive rational
weight, and verifies its exact objective-decrease equation. Actual serialized
price/Fenchel calculations still determine pool and global acceptance.

Prospectively limit each state to 256 accepted transfers, five cumulative
polishing seconds and 8,192-bit checked rational numerators/denominators,
inside its unchanged total deadline. These resource caps must preserve a
bounded/failure result if unmet; no finite-convergence or general performance
claim follows. Log every step, phase, exact weight, objective equation and all
upper-bound improvements. Do not reseed with known analytical supports or
use the old scientific outcomes as replacement evidence.

V2 is a new master algorithm/protocol and must be independently reviewed and
frozen before a distinct attempt. The V1 source/results remain intact. Pure
regression tests may model this observed numerical plateau; such tests are not
an optimizer rerun or evidence that the V2 scientific gate has passed.
