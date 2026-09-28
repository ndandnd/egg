# A numerical proposal for the restricted fleet master

The matched pilot's reused public pools both stopped when repeated rational
pairwise updates reached the arithmetic bit limit. The proposed remedy is a
separate numerical master policy: solve over the existing complete-fleet columns,
round the weights to a declared fixed denominator, and replay the resulting
mixture. This package integrates the existing proposal helper; it does not
change the completed pilot or measure performance on a new timetable.

For fixed columns with costs $c_j$ and hourly loads $L_j$, the restricted problem
is

$$
\min_{\lambda\geq0,\;\mathbf{1}^\top\lambda=1}
\sum_j c_j\lambda_j+F\!\left(\sum_j\lambda_jL_j\right).
$$

SLSQP supplies a candidate. The coordinator must replay every physical column,
check an exactly nonnegative rational simplex, and recompute the stored-number
mixture objective and restricted-pool gap. Neither SciPy's termination flag nor
its numerical residual supplies a global bound. The resulting convex mixture
is also not a single executable fleet schedule.

## Explicit policy

The coordinator and compact-pricing wrapper expose
`master_policy="numerical_qp_proposal"`, with declared defaults
`qp_denominator=1_000_000_000` and `qp_maxiter=500`. These controls enter the
opt-in state identity and events. The default `native_lp` path adds no new
identity or output fields. One numerical proposal consumes one master call.

## Acceptance and stopping

The numerical policy replaces the native linear master and repeated pairwise
polishing for that call. It does not silently fall back to those methods. A
finite proposal can remain useful even when SLSQP reports non-success; its
status and diagnostic residual stay visible. Proposer failures or malformed
weights produce an explicit `proposal_failed` result retaining previously
admitted bounds and mixture; they cannot certify. Physical column validation
errors still fail closed. Time and bit-limit exits remain budget-exhausted.

A positive restricted-pool residual need not prevent a fresh physical pricing
call. Prices from a feasible mixture still define a valid physical pricing
problem and a Fenchel global lower bound. Certification depends on the replayed
feasible upper and a valid full-space lower, with fresh target-state pricing
still required. If pricing returns a duplicate column while the global gap
remains open, the bounded/stalled result must remain visible.

Numerical optimization, rounding, physical replay, residual checking and failed
attempts all consume work and time. Fixed-denominator weights limit repeated
arithmetic growth; they do not waive the existing rational-bit, pool, master-call
or wall-budget checks. A cooperative numerical time check is not a guarantee
that an in-process SciPy call can be forcibly interrupted; the future experiment
runner must preserve its independent whole-child deadline and any overshoot.

## Scope and next comparison

This opt-in policy must coexist with retained feasible plans and the separately
implemented physical pricing-bound cache. Default behavior, source identities
and completed frozen outcomes remain unchanged. No cluster experiment or new
learning claim belongs to this implementation package.

After focused tests, independent review and full CI, declare a new matched
comparison on the existing development cases. Include reserve-cold and
feasible-plan baselines, explicit numerical-master and cached-bound factors,
complete preparation/target wall time, final bounds and every failure. Compare
time to common quality only where achieved. A stronger baseline is needed
before testing whether retrieved or learned proposals provide additional value.

A candidate next screening design is an ordered four-arm comparison: reserve
cold, reserve with retained feasible plans, numerical master with retained plans,
and numerical master with retained plans plus pricing-bound reuse. This tests
incremental additions rather than a full factorial interaction model. Exact
cases, caps, source pins and paid accounting must be frozen before launch; this
note is a design candidate, not the frozen execution protocol or a launch receipt.

## Validation status

The focused numerical-master, pricing-cache and feasible-reuse suite passed
37 tests. Checks include malformed-weight failure with prior bounds retained,
non-success finite proposals, late return, arithmetic caps, hard physical replay
failures, missing numerical dependencies, and default-policy compatibility.
Independent source review and full CI are pending. No performance result is
implied by these checks.
