# Independent native hull preflight review

27 September 2026. Reviewer: independent research audit agent; no author module
was edited and no native optimizer was executed during this review.

**Disposition: ready for the prospectively fixed eight-cell qualification after
the principal researcher freezes the source snapshot below.** This is a source,
mathematical and pure-test preflight, not evidence that any native hull solve has
succeeded. The failed-predecessor admission defect identified below was repaired
and independently rechecked before this disposition.

## Mathematical and feasible-set scope

The target is the convex hull of the projections of **complete feasible fleets**.
Each constituent fleet must satisfy shared charging resources before entering the
pool. A convex mixture is a planning relaxation; it is not a dispatchable average
fleet. The native feasible-set builder and its tolerance-conditional physical
replay are dependencies, not independently reimplemented by this hull module.
The qualified native model has a fixed directed movement graph, full terminal
recharge, one finite connector, and the stated vehicle and charging constraints.
The pricing MILP must retain that same feasible set.

For nonnegative aggregate load and separable convex quadratic supply cost, the
implemented conjugate is correct: positive curvature contributes
`max(p-a,0)^2/(2b)`; zero curvature contributes zero for `p<=a` and infinity
otherwise. A finite native **global pricing lower bound** minus this conjugate
is a global lower bound on the stated convex-hull objective. A feasible pricing
incumbent alone cannot provide this lower bound. The source keeps that
 distinction and uses the actual serialized floating price, not an idealized
analytic price, in the exact bound subtraction.

A retained nonnegative simplex gives the upper bound
`sum(lambda*c)+F(sum(lambda*e))`. It is correct to use the cost of aggregate load
rather than the mixture of each column's supply costs. The master raw weights
are archived, clipped only within the fixed negative-mass budget, and normalized
using exact rational arithmetic on their stored floating values. All positive
weights survive, including very small values, and physical replay is applied to
whole columns without dividing schedules by weights. Every stored column,
including one with zero current weight, is replayed.

The restricted-pool stopping quantity
`UB-[min_j(c_j+p*e_j)-F_+*(p)]` is valid for the actual stored price. It bounds
restricted-pool suboptimality and includes any rounded-gradient Fenchel
residual. A small tangent slack is not substituted for this quantity. The outer
certificate retains the best fresh lower bound and best feasible mixture upper
bound within the current state. An exact negative interval width fails.

The LP tangent rounding is conservative on the current pool load box. If a
rounded slope exceeds its exact value, the intercept is reduced by that slope
error times the box upper endpoint, then rounded downward. The resulting line
lies below the ideal tangent everywhere in the nonnegative box. These rows are
rebuilt when the column pool changes, so a larger pool cannot invalidate an old
rounding pad. The exact ideal tangent lies below the convex supply function.
The global certificate does not depend on master duals, LP bounds or an LP
objective being a true nonlinear upper bound.

The source uses an OPTIMAL-only, zero-integer-variable master policy, checks
raw simplex, load links, epigraph rows and reconstructed native objective, and
preserves raw master variable mappings and column order before interpretation.
Pricing FEASIBLE status remains usable only with an admitted finite global
bound and replayed physical incumbent under the native module's policy. A novel
pricing column is added when the global gap remains open; an exact duplicate
with an open gap terminates as `stalled_bounded`, not as convergence.

## Defect found and repaired before the first hull attempt

The initial candidate's retained-state worker checked a predecessor's saved
result status and assessment, but did not check its controller receipt or
independently re-count its native trace. A predecessor could write a certified
result and then exit nonzero or time out, or have an incomplete but parseable
trace. Its controller correctly marked the cell failed, yet the next retained
state could still import it. An independent pure reproducer supplied a certified
result with a failed timeout receipt and a native start without a corresponding
return; the successor reached its certificate routine.

The repaired `admitted_predecessor` requires the expected cell identity, accepted
certified receipt, exact integer return code zero, no timeout or evidence issues,
complete nonzero independent native accounting, and exact type/value agreement
between the receipt's counts/timing and the saved trace. Missing or malformed
receipts fail closed. The result must also remain accepted and certified; normal
pool import then verifies the expected state identity, retained arm/index,
physical identity, extraction policy, distinct keys and every physical witness.
The original independent reproducer now returns `blocked_by_predecessor` before
reaching the certificate routine. No pricing, master or physical-native code was
changed to repair this bookkeeping defect.

## Independent checks performed

- All 46 pure/fake tests passed in an independent process with imports of `mip`
  and `gurobipy` explicitly blocked: 35 original tests and 11 new predecessor
  admission controls. The new controls include missing/malformed/failed receipts,
  wrong cell, nonzero return, timeout, incomplete/empty trace, count disagreement,
  malformed accounting, and a valid matching predecessor.
- The original independently constructed failed-predecessor reproducer was run
  again and confirmed blocked before the certificate routine.
- 500 deterministic independently sampled one-dimensional cases checked both
  endpoints of the affine rounding-error function using exact rational
  arithmetic, establishing the implemented tangent weakening on each sampled
  pool box. The same cases checked nonnegative exact Fenchel residuals for the
  actual rounded gradient. This supplements the analytical argument; it is not
  a substitute for it or a native numerical experiment.
- Reviewed all eight prospective controls, analytical hull targets, cold/retained
  dependency graph, actual-price arithmetic, complete-pool replay, raw evidence
  order, cumulative pricing/master/pool/time budgets, per-worker cap, outer
  process-group termination, immutable attempt creation, prefix-preserving
  evidence parsing, independent-cell continuation and source hash coverage.

## Evidence and interpretation limits

The ordinary master and pricing algorithms are classical convex-hull/column
 generation machinery. This qualification does not establish a new optimization
method, learned-price advantage, runtime advantage, operational generality or
journal novelty. The eight small controls test exact known geometries and a
fixed tariff path. Aggregate load errors are descriptive; target acceptance
requires a valid narrow objective enclosure, not arbitrary equality of an
alternative supporting decomposition.

Exact fractions certify arithmetic on stored projections and prices. They do
not turn a tolerance-accepted floating physical witness into an exact feasible
schedule, nor prove a native global bound without its solver/numerical
assumptions. Native recharge attempt 1 failures remain failures; the subsequent
qualified source and separate successful archives are the relevant dependency.
No optimization was launched by this reviewer. Each executed hull attempt must
receive a separate independent audit of raw pricing evidence, complete columns,
master snapshots, simplex corrections, native lower bounds and Fenchel intervals
before a result is presented as qualified.

## Reviewed freeze-ready source snapshot

| File | SHA-256 |
|---|---|
| `src/egglab/native_hull.py` | `8c23f3e3b304c7cfc531fbe8fea02f64841138d9b1358912b521f87ea014f21b` |
| `src/experiments/native_hull_qualification.py` | `7ec49e89768af19847580244c0b8924f2ef9406bb25ba99bed5b10ff76df7fcb` |
| `src/tests/test_native_hull.py` | `32f1e98407c66540aebc17d11a1783dcc6b5e380fbf01d06556a0cb00f35b665` |
| `doc/NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md` | `6cf0d22aa3cd369016a372fb872c42b10ee550a239773cef3564f97b0d7f5c40` |
| `doc/NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md` | `5dd2c2c01f6fa3ab0078e2adac52cab9fce8a345bee73318a113513239cbc819` |
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/experiments/native_recharge_qualification.py` | `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e` |

The principal researcher must freeze this complete source/dependency state before
executing the prospective protocol. A later source change requires a new review
or a scoped documented delta; the preflight document itself is derived evidence.
