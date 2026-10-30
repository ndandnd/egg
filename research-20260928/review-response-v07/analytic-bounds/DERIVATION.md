# Exact energy-floor bounds and public development-screen comparison

`compute_bounds.py` uses only frozen case/market metadata, the independently
reviewed cardinality-flow summary, the already reviewed original-market
analytic result, and curated `result.json` assessments, saved response
prices, and scalar analysis from the September 28 development screen. It
imports no optimizer or EGG model code and performs no solve. Run
`python3 compute_bounds.py --repo /path/to/journal-research-work > bounds.json`
to reproduce the accompanying JSON. Its input hashes are recorded there.

## Model identity and derivation

Both full 37-service case dictionaries and case identities in the frozen
development screen equal their corresponding cases in the independently
reviewed cardinality-flow freeze, byte-value for byte-value after JSON
decoding. Each has a 30-hour finite horizon, unit charging efficiency, full
400-kWh terminal inventory, used-bus cost `f=100`, and **zero monetary
deadhead cost**. Movement energy remains physical consumption. The exact
flow bound at the stored flat coefficient `a₀` therefore gives, for every
two-bus physical plan,

`E ≥ Emin = (Lflow − 2f)/a₀`,

where `E` is total grid kWh. This inference uses full replenishment and
efficiency one; it is not a generic conversion of a cost bound into energy.
The independently reviewed one-bus obstruction applies to both identical
case graphs. The sum of mandatory-service energies is exactly
`250264333071608593/281474976710656 ≈ 889.117519` kWh, and all movement
energies are nonnegative. The energy floors are about `1024.621199` kWh
for depot 15 and `1071.972346` kWh for depot 16.

For either 30-period market with stored coefficients `a_t` and common
positive quadratic coefficient `b`, use a **uniform test price** `p`.
All optimal test prices below exceed every `a_t`, so the nonnegative-load
Fenchel inequality has the interior form

`a_t L_t + b L_t²/2 ≥ p L_t − (p−a_t)²/(2b)`.

For two buses, `c+pE ≥ 2f+p Emin`. For three or more buses,
`c+pE ≥ 3f+p Eservice`, because `p>0` and all energy is nonnegative. At the
chosen price the latter exceeds `2f+p Emin` by the strictly positive margins
in the table. Thus **all fleet cardinalities** obey the same linear lower
bound: one bus is infeasible, exactly two use the flow floor, and three or
more use the service-energy floor. Convex mixtures preserve it. Applying
Fenchel to the mean load gives

`CH ≥ 2f+p Emin − Σ_t (p−a_t)²/(2b)`.

The maximizing uniform price in this interior region is
`p* = mean(a_t)+b Emin/30`. The frozen original market has `a_t=0.2` for
all periods; the changed market has fifteen `0.18` periods followed by
fifteen `0.22` periods. Both use the same stored binary `b` near `1/900`.
All calculations treat those stored binary coefficients and the exact
flow fractions as rational inputs. No decimal coefficient is silently
rationalized. The depot-15 original-market result exactly matches the
independently reviewed prior certificate, not merely its rounded display.

| Depot | Market | `p*` | Three-plus-bus margin | Exact ideal `CH` lower, decimal display |
|---|---|---:|---:|---:|
| 15 | Original | 0.2379489333 | 67.7570439 | 424.365880667204 |
| 15 | Changed | 0.2379489333 | 67.7570439 | **418.965880667204** |
| 16 | Original | 0.2397026795 | 56.1692081 | 435.674556453753 |
| 16 | Changed | 0.2397026795 | 56.1692081 | **430.274556453753** |

The symmetric intercept change lowers this particular uniform-price bound
by approximately 5.4 units, despite an unchanged mean intercept. The
reviewer's 418.97 and 430.27 calculations are correct at two-decimal
precision. The alternative 423.27 figure substitutes a retrospective,
solver-tolerance-qualified *native* flat optimum for an exact ideal-model
two-bus flow lower bound. The separate flat round-0 reconciliation supports
that native numerical optimum, but not an exact ideal lower certificate.
We therefore do **not** admit 423.27 as an exact hull lower bound.

## Distinct computational evidence

The following are from **one September 28 development screen**, not the
later ordered solver-baseline campaign. `D` is its bounded physical planner;
`CH` is its cold complete-fleet hull. The response is priced at the
**named planner incumbent's own gradient**, verified exactly against the
stored `response/prices.json` vector under the source's binary64 arithmetic.
The largest discrepancy between a saved price and the mathematical gradient
evaluated exactly on the stored binary64 coefficients/load is below
`4.1e-16` across all eight cases. Thus the price is a machine-rounded
own-price query, not an exact real-number gradient certificate. The script
also checks each curated assessment's complete-evidence flag and exact
saved bound fraction against the scalar analysis before combining them.
Regret subtracts the response bounds from that incumbent's posted private
bill, reconstructed exactly from the stored binary64 prices and load.
All numerical endpoints retain native solver/replay qualifications. Every
two-decimal interval below is generated from the saved fractions by
flooring its lower endpoint and ceiling its upper endpoint. The analytic
column is an exact ideal lower bound displayed downwards.

The saved response call supplies another same-screen hull lower bound.
For its saved price vector $p$, the script computes the nonnegative-supply
conjugate from the exact binary representations of $a_t,b_t,p_t$:
`F*(p)=Σ [p_t−a_t]_+²/(2b_t)` when `b_t>0`. If `b_t=0`, its term is zero
for `p_t≤a_t` and infinite otherwise; the script rejects an infinite
conjugate. Since `V_lower≤V(p)`, `V_lower−F*(p)≤CH` under the same
conditional native-bound qualification. The **native-combined** screen
uses `CH_L=max(raw CH_L,V_lower−F*(p))`,
`CH_U=min(raw CH_U,D_U)`, and `D_L=max(raw D_L,CH_L)`.
Its nonnegative gap enclosure is then
`[max(0,D_L−CH_U), D_U−CH_L]`. For public cases, the displayed mixed
gap also raises `CH_L` by the separately proved exact ideal energy floor.
This is postprocessing of saved evidence, not an added algorithmic step or
a runtime result.

| Depot | Market | Screen `D` | Screen `CH` | Screen response `V(p_x)` | Analytic `CH` lower | Conditional gap interval | Named-incumbent own-price regret |
|---|---|---:|---:|---:|---:|---:|---:|
| 15 | Original | [408.53, 547.61] | [408.53, 552.36] | [337.73, 413.36] | 424.36 | [0.00, 123.24] | [266.10, 341.73] |
| 15 | Changed | [339.35, 517.33] | [339.35, 547.47] | [379.41, 424.07] | 418.96 | [0.00, 98.37] | [190.43, 235.09] |
| 16 | Original | [423.15, 530.66] | [423.15, 530.66] | [405.94, 433.75] | 435.67 | [0.00, 94.99] | [204.41, 232.22] |
| 16 | Changed | [377.65, 547.88] | [377.65, 549.70] | [377.65, 430.86] | 430.27 | [0.00, 117.61] | [215.95, 269.16] |

The raw signed screen gap lower is negative in every public row; the
mathematical nonnegative lower bound is zero. The mixed upper uses the
exact analytic floor alongside same-screen native bounds, so it remains
conditional on the native physical upper witness. Positive regret here
belongs to a **time-limited
feasible incumbent**, not to a proven planner optimum. It cannot establish
that an optimal public fleet lacks own-price support. The screen's hull
stages were budget exhausted; no positive public gap was certified.
For depot 15's original market, the separately reviewed exact witness and
analytic bound give the stronger ideal gap cap 88.41; the screen's 123.24
is only its own native-screen/analytic-floor postprocessing cap.

The same reconstruction on the two small synthetic cases gives:

| Case | Market | Screen `D` | Screen `CH` | Screen response `V(p_x)` | Same-screen conditional gap | Named-incumbent own-price regret |
|---|---|---:|---:|---:|---:|---:|
| Cyclic | Original | [96.99, 97.01] | [94.88, 94.89] | [133.99, 134.01] | [2.11, 2.12] | [12.99, 13.01] |
| Cyclic | Changed | [98.99, 99.01] | [97.98, 97.99] | [139.99, 140.01] | [1.01, 1.02] | [8.99, 9.01] |
| Multivisit | Original | [84.45, 84.47] | [80.39, 84.47] | [124.26, 124.27] | [0.00, 0.10] | [0.09, 0.10] |
| Multivisit | Changed | [84.71, 84.73] | [81.17, 86.05] | [124.51, 124.52] | [0.00, 0.10] | [0.09, 0.10] |

Only the cyclic cells have a positive lower gap at screen tolerance; the
separate exact two-service construction already proves its nominal gap.
The multivisit planner incumbents show small positive own-price regret,
but their hull intervals still cross the zero-gap threshold. The
response-Fenchel lower bounds are approximately 84.370324 and 84.622956,
which reduce the two multivisit gap uppers from approximately 4.073 and
3.548 to 0.098686 each. At the saved prices, supplier LOC computed from
the stored binary values is below `7.4e-31` units in either multivisit
case. Hence the named incumbent's cost above its response-Fenchel lower
differs from its regret upper by only that negligible arithmetic amount;
the native planner upper adds about `10^{-6}` of objective guard. The
saved price is nevertheless a machine-rounded gradient, and the response
lower is native conditional. None of these intervals replaces the exact
physical-model proofs or proves multivisit optimum regret.

The same screen's posthoc two-column mixture replay gives changed-market
hull uppers of approximately 492.21 (depot 15) and 510.13 (depot 16),
outside the frozen run budget. Even paired with their same-screen planner
lowers, signed gap lowers remain negative (about −152.86 and −132.47).
The mixture is not an executable fleet. It must not be credited as a
timed baseline or treated as a fresh global lower bound.

For context, the **separate later ordered solver-baseline campaign** reports
changed-market QP-plus-pool-plus-cache hull intervals
`[405.83,471.52]` at depot 15 and `[420.45,491.46]` at depot 16 after
outward display rounding. The exact analytic floors exceed those campaigns'
stored lower endpoints by about 13.13 and 9.82 units, respectively. These
later hull endpoints are scalar summaries from their own campaign; they
are not merged with the September 28 screen's planner or response intervals,
nor used for a cross-campaign time or speed claim. The published scalar
summary does not itself expose a frozen case dictionary for an independent
identity check, so its same-model comparison rests on the reviewed
manuscript's declared public cases and market definition.

The audit scope is mathematical and archival. The exact lower bounds apply
to the ideal stored-input physical model under the reviewed one-bus
obstruction and flow relaxation. Development-screen bounds are
solver-conditional. Neither set proves a strictly positive public
physical-versus-hull gap, an exact public physical optimum, or an
own-price regret statement about an optimal public fleet.
