# Prospective compact native orphan-charge extraction

27 September 2026. Design for independent review; **not implemented or
qualified**. The frozen energy-band source `66b7054510a8b90471d6abe07d32a9f7f509182d`
and `result/native_pathflow/20260927-attempt2` remain unchanged. That attempt is
**failed, 19/20**, and its joint-planner second round supplies a diagnostic only.
The eight compact-hull V2 controls and public pilot 2 remain held.

## Failure and scope

The saved second joint-planner incumbent is reported `OPTIMAL` by CBC and has
exactly binary saved movement selections. `in_A` is unselected (`x=0.0`), but
its grid-energy variable for elementary interval 1 is
`1.2214110437041203e-12` kWh. The existing policy keeps every strictly
positive energy, then correctly refuses to assign that charge to a vehicle.
The independent read-only audit found a `2.129631312241243e-12` kWh aggregate
energy-row residual, a `3.2933655802480644e-12` maximum raw constraint
residual, and native objective/bound reconstructions within the frozen numerical
guards. There was no negative-charge correction. These facts indicate a
solver-tolerance artifact in this saved incumbent; they do not make its
physical extraction valid or retrospectively pass the cell.

This design changes only **compact path-flow extraction** after native solve.
It does not alter the physical case, energy-band rows, solver feasibility or
optimality tolerances, selected-path recovery, session rules, replay tolerances,
the shared indexed `native_recharge` extraction policy, or any old result. Give
the prospective compact extraction its own policy identity, for example
`native-pathflow-orphan-projection-v1`, in raw incumbent records, result plans,
qualification metadata and the compact-hull oracle identity. Do not present a
changed extractor under the frozen V2 policy string.
The current compact-hull adapter sets `ORACLE_ID = pathflow.FORMULATION` and
requires the result and plan formulation tags to match it; the prospective
change must update that identity and those tags together, while disclosing
that the native constraint matrix itself is still the energy-band V2 matrix.

## Candidate policies

The minimal policy is to project tiny positive charge on an **unselected** mode
to zero, with a disclosed exact correction ledger and one incumbent-wide
budget. Such charge has no legal vehicle owner. A positive charge on a selected
mode is always preserved; no threshold rounds it to zero. Positive orphan
energy above the shared budget, ambiguous path recovery, or a failed physical
replay still rejects the incumbent.

Moving orphan charge to another selected mode is less suitable as the default.
The saved round already fills the interval-1 selected depot mode's 12 kWh
capacity; any transfer there exceeds its stored upper bound. Transfer to a
different time or movement changes route SOC and the market load, and would
require a separately specified fixed-route feasibility/repair problem and
another optimizer. That may be a later prospective fallback if bounded
projection cannot qualify, but it is outside this repair. Silent zeroing,
per-variable thresholds and retrying the frozen failed attempt are excluded.

## Projection and whole-incumbent budget

Recover the selected paths and their unique movement owners exactly as now.
Read every saved charge and load as a finite float and retain its original
`repr`. Use `Q(v)=Fraction.from_float(float(v))` for all correction sums. For
charge variable `i=(mode, interval)` with raw value `z_i`, define

- `N = sum_i max(0, -Q(z_i))`: negative-to-zero correction, as in the shared
  policy;
- `O = sum_(i: mode not selected) max(0, Q(z_i))`: positive orphan-to-zero
  correction;
- projected `r_i = z_i` only when `z_i>0` and its mode is selected, and zero
  otherwise. Thus `sum_i |Q(r_i)-Q(z_i)| = N+O` exactly.

First require `N+O <= Q(1e-8 kWh)` using the existing fixed roundoff budget
value. Do not call the shared normalizer and then reset its budget: its negative
correction is part of this same total. A compact-specific wrapper can reuse
its negative normalization, then add the orphan projection and charge the
combined total. Keep the indexed shared normalizer's behavior unchanged.

For each market period, form exact raw-charge sum `R_t` from `Q(z_i)`, exact
projected-charge sum `P_t` from `Q(r_i)`, saved native load `L_t`, and the
materialized plan load `H_t`. The ledger records all four, plus
`Q(L_t)-R_t`, `P_t-R_t`, and `Q(H_t)-P_t` and their absolute sums. It records
every changed key with mode, interval, selection, raw and projected energy,
reason, and before/after period. This makes the load change auditable even
when the native load row itself has a small residual.

Serial decoding retains its exact cumulative endpoint construction. Let `I`
be its sum of positive interval-capacity excesses and `J` the sum of positive
materialized-session capacity excesses, both already computed exactly. The
new **single whole-incumbent** admission is conservatively

`E = N + O + sum_t |Q(L_t)-R_t| + sum_t |Q(H_t)-P_t| + I + J <= Q(1e-8 kWh)`.

The two capacity terms can reflect the same rounding at different stages;
counting both is deliberately conservative. Use exact fractions for the test
and log its exact numerator/denominator, float rendering, every component,
and the remaining budget. Pass `N+O` as decoding's prior correction, then
apply the final combined check; a shared decoder that cannot accept this
prior must be extended without changing its old call sites. Reject nonfinite
values, unknown keys, malformed intervals or any budget excess. The present
`1e-6` kWh native-load and physical-replay checks remain independent hard
checks and are not relaxed by this budget.

After decoding, independently replay the returned physical plan. Denote its
recomputed per-period loads by `T_t`; record them and
`sum_t |Q(T_t)-Q(H_t)|`; require
that additional discrepancy together with `E` fit the same budget. The
existing replay must still establish valid selected ownership, legal charging
windows, connector and power limits, SOC reserve/capacity, full terminal
replenishment, fleet energy conservation and objective inputs. Never repair a
failed replay by silently changing route, time, or energy. The returned
`roundoff` object must include this complete ledger, not only the old negative
and serial-decoding subledgers.

## Objective and bound consequences

The raw native incumbent and global bound belong to the unchanged native
model. An admitted projection supplies a **different physical feasible
witness**; its load and objective must be recomputed from the returned plan.
Keep the qualified lower endpoint `native_global_bound - BOUND_GUARD` and use
`physical_replayed_objective + BOUND_GUARD` for an upper endpoint only after
full replay and all objective-admission checks. Do not replace the lower bound
with the native incumbent or label the raw positive orphan as physical energy.
These remain tolerance-conditional numerical enclosures, not exact physical
or exact MILP certificates.

For linear pricing, log and check the load correction
`Delta_t = Q(T_t)-Q(L_t)` and its exact objective effect
`sum_t Q(price_t)*Delta_t`. For the planner, evaluate the saved tangent
envelope and the true quadratic cost on both raw native loads and replayed
physical loads; record their deltas, round and tangent snapshot. A deterministic
cross-check can bound each true-cost change by
`(|a_t| + |b_t|*max(|L_t|,|T_t|))*|Delta_t|`, summed over periods,
with stored-number arithmetic and outward rounding. The existing incumbent
versus reconstructed tangent/linear objective guards and native lower/bound
ordering checks must still pass. If the projection raises the physical upper
bound, keep the larger value; if it lowers it, do not improve the native lower
bound. The best-plan update and convergence decision must use the replayed
upper bound and the retained guarded lower bound, with no new epsilon or
surrogate success label.

The correction can make an exact stored-matrix solution fail the new physical
interpretation; it earns admission solely through the prospective budget and
unchanged replay. The aggregate energy band remains the same model constraint.
Its mathematical redundancy claim for exact integer feasible points is
unchanged, while floating solve status alone never proves exact conservation.

## Implementation and qualification gate

1. Add a path-flow-specific pure projection helper and versioned ledger. Keep
   all raw values and mapping intact in `native_incumbent` before projection.
   Emit the correction record even if a later budget, decoding, load, objective
   or replay check rejects the candidate.
2. Add no-optimizer controls for the saved numerical pattern on a synthetic
   incumbent, several positive orphans whose **sum** exceeds the budget,
   combined negative/orphan/capacity/load residuals, a positive selected
   charge below the orphan size that must survive, an unavailable selected
   interval, and a projection that fails terminal SOC. Verify objective-delta
   accounting and that the shared indexed policy still rejects positive
   unowned charge according to its own rules.
3. Obtain independent source/preflight review. Freeze the extractor, tests,
   exact 20 controls, version strings, runner, and per-phase budgets at a new
   source commit. Run one new compact qualification attempt into a distinct
   immutable directory, manifest all files including failures, and independently
   audit every raw incumbent, correction ledger, replay and bound. A second
   failure is a result, not a reason to patch and rerun in place.
4. Only after the compact gate passes, separately version, review and execute
   the eight compact-hull controls with the new oracle identity. Public pilot 2
   needs its own later frozen protocol and cannot inherit a control pass as an
   operational claim.

No optimizer call, frozen raw-artifact mutation or new qualification is part of
this design checkpoint.
