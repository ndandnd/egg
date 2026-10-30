# Standalone restricted-QP proposal

`src/egglab/restricted_qp_proposal.py` accepts fixed complete-fleet operating
costs, nonnegative hourly load vectors and a finite convex quadratic market.
SciPy SLSQP proposes simplex weights with an analytic gradient. Deterministic
largest-remainder rounding puts them on a caller-declared integer denominator;
the returned rational weights are nonnegative and sum exactly to one. The
helper reports the numerical solver's status, wall time, numeric simplex
diagnostics, rounded objective/gradient/load, and rounding time.

This is only a restricted-pool weight proposal. The rounded objective and
directional residual are floating diagnostics, not exact replays or bounds.
Any later integration must replay physical columns and rational mixture cost,
check the restricted-pool residual, then obtain fresh complete-fleet pricing
and a supply-conjugate lower bound before making a global hull claim. A
`success=True` field means only that SLSQP met its own termination rule.

The helper is not imported by the frozen computational screen or native hull.
The first screen, its source pins, and archived runs remain unchanged. Focused
tests use analytic, duplicate-column, linear and invalid-input examples;
they do not start a native MIP or a cluster job. Integration, algorithm caps,
and any matched comparison await baseline results and independent review.
