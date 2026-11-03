# Native path-flow V2: a valid aggregate-energy band

27 September 2026. Prospective formulation
`egg-native-pathflow-v2-energy-band`; proof-ledger policy
`stored-row-and-physical-conservation-band-v1`. This adds two inequalities,
no variables, no objective changes and no numerical-tolerance changes. The V1
compact gate at `ebb146e`, compact-hull gate at `72a1f715` and first public pilot
at `282e00b` remain unchanged. Source/protocol preflight, a new freeze and separate
qualification attempts are required before this version is used scientifically.

## Ideal physical conservation

For the fixed homogeneous model, every used bus starts and ends with the same
full battery inventory. Telescoping every selected path gives

`eta * sum_(m,k) z_mk = sum_t e_t + sum_m E_m y_m`,

where grid energy is z, eta is the fixed common charging efficiency, every
mandatory service occurs once, and E_m is the sum of all energy in the selected
movement's legs. Pullouts, direct travel, each depot visit and pullins all
contribute exactly their represented energy. Multiple depot visits cause no
extra boundary term. Waiting/auxiliary legs are included once; depot auxiliary
off is represented by zero consumption, not by an extra adjustment. Unused
vehicle slots/modes contribute nothing. The proof requires full replenishment
and represented fixed consumption; it does not apply unchanged to terminal
reserve-only, unmodeled self-discharge, varying efficiency or export models.

The current model forms `Ebar_m = float sum(leg energies)` per mode. The new
rows must use those same coefficients, not a differently ordered global sum.
All exact quantities below use `Fraction` on the finite stored input numbers.
Let `S=sum_t Q(e_t)` and `d_m=sum_legs Q(e_leg)-Q(Ebar_m)`. Exact physical
conservation implies

`G := eta*sum(z)-sum_m Ebar_m*y_m = S+sum_m d_m*y_m`.

A feasible integer service cover has N mandatory trips and K nonempty used
paths, hence N+K selected modes with K<=N. At most 2N modes are selected.
Let `Dlo` be the sum of the smallest negative d values, taking at most 2N,
and `Dhi` the sum of the largest positive d values, also at most 2N. A valid
physical projection band is `[S+Dlo,S+Dhi]`. This envelope deliberately ignores
additional graph restrictions; that makes it conservative, not invalid.

## Why the stored native matrix needs its own envelope

A literal aggregate equality need not be redundant in the exact matrix of
binary floating coefficients. Existing selected SOC rows include precomputed
`B-Ebar`, `B+Ebar` and subsequent floating expression-constant combinations.
The new implementation therefore separately bounds the existing matrix's
assembly defects rather than claiming they vanish.

Write the existing residual as `phi+C`, with stored float big-M value M.
The source-expression constants are:

| Mode | Stored C | Ideal C for the same stored Ebar |
|---|---|---|
| Pullout | `-fl(B-Ebar)` | `-Q(B)+Q(Ebar)` |
| Direct or depot | `Ebar` | `Q(Ebar)` |
| Pullin | `fl(-Ebar-B)` | `-Q(B)-Q(Ebar)` |

Python-MIP's comparison normalization forms constants `fl(C-M)` and
`fl(C+M)` in the two big-M rows. At y=1 their exact matrix implies

`Q(C)+Q(M)-Q(fl(C+M)) <= phi+Q(C)`
`<= Q(C)-Q(M)-Q(fl(C-M))`.

Subtract `D=Q(C)-C_ideal` from both endpoints to bound the intended residual
for that same stored Ebar. Nonterminal residuals enter telescoping positively;
terminal residuals enter negatively, so reverse and negate their intervals.
Sum the smallest negative signed lower endpoints up to 2N to obtain Amin,
and the largest positive signed upper endpoints up to 2N to obtain Amax.
Service SOC equalities are exact on their stored single coefficients. Therefore
an integer point in the exact old normalized matrix satisfies

`S+sum_m Ebar_m*y_m-eta*sum(z) in [Amin,Amax]`,

so G lies in `[S-Amax,S-Amin]`.

The implementation logs every per-mode source and normalized constant, exact
aggregation/constant defect, selected residual interval, sign-reversed interval,
service float-sum defect, both aggregate envelopes and their union. During model
construction it compares the actual `residual.const` and actual generated
big-M constraint constants to the predicted values. Any expression-assembly
mismatch fails closed before optimization. This is stronger than silently
assuming a backend representation from an algebraic formula.
The actual service-row constants, aggregate variable coefficients and normalized
aggregate endpoints are checked too. Python-MIP can elide constants smaller
than its internal EPS; unsupported elision therefore rejects model construction
rather than silently extending the stored-matrix equivalence claim to those
inputs. Pure fake-expression controls exercise these failure paths.

## Materialization and validity claims

Take the interval union of the physical and stored-matrix envelopes. Convert
its lower endpoint downward and upper endpoint upward to finite floats using
exact comparisons and, if necessary, one `nextafter` step. The two added rows
are simply

`lower_rhs <= eta*sum(z)-sum_m Ebar_m*y_m <= upper_rhs`.

No service term or other constant is hidden in the left expression; every
charge variable has its stored eta coefficient once and each mode binary has
its stored negative Ebar coefficient once. The two row indices and complete
ledger are included in every raw incumbent snapshot. Physical row counts
increase by two; the original variable set/order and all objectives are
preserved. The rows contain the intended physical conservation projection and
are redundant for integer feasible points of the old **exact normalized stored
matrix**. Their fractional relaxation can be stronger.

This does not claim identical floating solver behavior or that every point
within V1's per-row feasibility tolerances will remain within the new rows'
feasibility tolerances. Numerical acceptance still uses the existing native
1e-8 feasibility setting, qualified bound guard, charge-normalization budget,
physical replay and objective checks. The new interval is a derived coefficient
assembly bound, not a new empirical or user-chosen tolerance. Requalification
is mandatory. No exact physical or exact MILP certificate is inferred from
floating results, and the old pilot's weak bounds are not retrospectively
reclassified as errors.

## Meaningful pure qualification controls

All twenty fixed synthetic cases have zero-width physical and stored-matrix
bands: the two rows become the same ideal energy equality. The unchanged
three-service control includes two depot visits, positive movement costs,
reserve and eta19/20. The unchanged nineteen earlier controls include directed
multi-leg movement, half-minute timestamps, partial windows and four expected
infeasibilities. All control definitions, targets and execution budgets are
compared exactly with the frozen V1 input before execution.

An independently supplied fractional nominal cyclic witness establishes actual
relaxation strengthening. Set movement selections

`out_A=1, in_A=1/4, out_B=1/4, in_B=1, depot_AB=direct_AB=3/8`,

SOC `(before_A,after_A,before_B,after_B)=(20,5,17.5,2.5)` and only terminal
in_B charge17.5kWh. It satisfies every V1 LP row and variable bound after
integrality is relaxed. Mandatory battery consumption is30kWh, so it violates
the new aggregate lower row by12.5kWh. A fake expression/model builder checks
all rows with exact rational evaluation; no native optimizer is called.

The full public cases are used only for pure arithmetic profile checks in this
preflight, not optimizer runs. Independent derivation gives both union endpoints

`[250264333071608001/281474976710656, 250264333071609185/281474976710656]`.

These lie at `S ± 37/17592186044416` kWh before outward float materialization.
The stored-row envelope dominates the physical per-leg aggregation envelope.
The materialized band is approximately
`[889.1175194193863,889.1175194193906]` battery kWh. The independent check and
fractional witness are documented in `NATIVE_ENERGY_ROW_PREFLIGHT_CRITERIA_20260927.md`.

After independent review, run a new twenty-cell compact qualification attempt
and audit every added row, ledger, physical witness and unchanged target. Only
then run the separately versioned eight-cell compact-hull attempt, retaining
all definitions/caps and using the new oracle identity. The shared hull proof,
master/polishing, indexed default and retained-boundary checks are unchanged;
V1 retained states are rejected because their oracle identity differs. Any
new public optimization requires its own prospective protocol, not a rerun or
replacement of the first pilot.
