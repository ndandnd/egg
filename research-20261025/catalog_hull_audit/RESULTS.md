# Finite-catalog convexification diagnostic — completed 25 October 2026

120 predetermined cells: 20 observed minimum-fleet banks × day/late tariffs × curvature multipliers 0/1/5. Eighty one-start continuous SLSQP optimizations; 40 zero-curvature exact vertex controls. No route/charging reoptimization, learning or unrestricted fleet solve.

Overall process pass flag: **False**; all 120 cells completed, and all 120 independently rationalized primal/dual bounds satisfy the frozen numerical catalog tolerance. Optimizer status is preserved separately. No attempt was repeated.

| Tariff | Curvature multiplier | Cells | Strictly positive gap lower bound (>1e-6) | Median pure-minus-catalog-hull gap (% of best pure cost), interval | Maximum gap upper bound (%) |
|---|---:|---:|---:|---|---:|
| day | 0 | 20 | 0 | [0.000000, 0.000000] | 0.000000 |
| day | 1 | 20 | 15 | [0.025455, 0.025455] | 1.021835 |
| day | 5 | 20 | 16 | [0.225830, 0.225830] | 1.841982 |
| late | 0 | 20 | 0 | [0.000000, 0.000000] | 0.000000 |
| late | 1 | 20 | 10 | [0.000040, 0.000040] | 0.846063 |
| late | 5 | 20 | 16 | [0.148038, 0.148039] | 2.874742 |

All zero-curvature controls have exactly zero gap. Positive-curvature multipliers are sensitivity conditions on the same physical bank, not new datasets or calibrated market forecasts.

Optimizer/non-pass cells: 1. Their exact feasible-mixture, lower-bound, decomposition and tolerance checks remain separately recorded; they have not been relabelled as optimizer successes.
- scale:50730:40 / late / multiplier 5: Positive directional derivative for linesearch; exact catalog optimization gap 1.091265815e-09.

The observed 30-period load-difference banks require a median 2.5 singular directions to explain 95% of squared variation (range 0–6). This is a bank-dependent descriptor, not the dimension of the full feasible set.

Interpretation guard: fixed fleet cost dilutes gaps reported as a percentage of
total cost. Absolute and electricity-cost-normalized gaps should accompany a
subsequent economic assessment; a small total-cost percentage alone does not
establish that electricity coordination is unimportant. With m distinct profiles,
centered rank is mechanically at most min(m-1,30), so the observed low rank also
reflects the limited bank cardinality. Neither statistic is an intrinsic property
of the whole feasible set.

Every cell checks with exact rational arithmetic: nonnegative mixture weights summing to one; primal/dual order; the pure-cost minus dual-bound = linear opportunity loss + curvature-weighted load distance identity; and the Jensen weighted-variance identity. The optimizer only proposes weights; these checks qualify the finite-bank bounds independently.

The relaxation mixes whole physical schedules. Its fractional load is not an executable fractional fleet. Missing schedules and missing reoptimized charging can change both the best pure solution and the convex relaxation; the measured gap is neither a lower nor an upper bound on the original full-problem integrality gap. Minimum-fleet restriction and original-day candidate generation further limit inference.

Scientific implication: use these measured magnitudes to decide whether full-space price-support work is worthwhile. Do not promote an elementary convexity identity, an SVD descriptor or a catalog calculation into a novel theorem, strategic equilibrium, ML improvement or global certificate.
