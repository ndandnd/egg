# Candidate restricted-master improvement

This is an engineering hypothesis for development after the first computational
screen, not a change to the frozen baseline or a new certificate. The old public
run stopped after three columns because exact pairwise polishing exhausted its
work limit. Larger route-search capacity alone cannot resolve that stopping rule.

For fixed complete-fleet columns `(c_j, L_j)`, the restricted problem is a convex
quadratic program on the simplex:

`min sum_j lambda_j c_j + F(sum_j lambda_j L_j)`,
`lambda >= 0`, `sum lambda = 1`.

A numerical QP can propose weights without recursively growing exact rational
denominators. Convert the proposal to a nonnegative rational simplex with a
declared denominator and normalization rule, then use the existing physical
column replay, exact mixture objective and restricted-pool residual check. Record
QP time, projection/replay time, denominator size and the achieved residual.
The numeric solver's success flag is not the certificate. If rounding does not
close the requested pool residual, refine within a budget or keep the result as
a feasible bounded proposal; never silently increase a declared tolerance.

The restricted-pool residual is useful for finding good pricing points. However,
the global lower bound comes from **fresh complete-fleet pricing** and the supply
conjugate. For any posted price `p`, `V_lower(p) - F*(p)` is a valid lower bound
under the existing oracle's stated qualifications. Therefore restricted-pool
optimality is not itself necessary for bound validity. A later algorithm may
continue global pricing from an incompletely polished feasible mixture if it
records that choice and terminates only on the genuine global enclosure. It
must handle repeated columns/open gaps honestly and preserve all work limits.

The current first screen keeps the core unchanged. A separate offline probe on
the three archived columns tests whether this candidate is worth implementing.
If supported by the screen/probe, use focused tests for simplex validity,
projection/objective replay, singular/duplicate columns, open residuals and the
unchanged global-bound stopping rule. Reuse existing physical qualification;
do not launch another broad physical audit merely because a master proposal
algorithm changes. Compare the new master with the frozen baseline on the same
development cases before expanding the dataset or attributing gains to ML.
