# Independent physical qualification design review

Date: 2026-09-21. Scope: source review and analytic fixture derivation before the new local physical qualification. No protected data, seeds, cluster access, or native solver execution was used for this review. Production source was not edited.

Reviewed source: `aggregation-research-work/src/egglab/{enumerate_tiny,evsp,instance,market,solver}.py` and the frozen failed `review-20260921/physical-probe/{probe.py,report.md}`. This report supplies an independent mathematical target for the new standalone adapter; it is not a report of completed physical solves.

## Assessment and smallest defensible qualification

The production tiny enumerator already treats charging as continuous. A fleet structure consists of a trip partition into vehicle chains and a fixed direct/depot kind for each connecting arc. The charging amounts and SOC variables remain continuous within that structure. The master uses a homogenized, lambda-scaled charging polytope for each entire fleet structure. That is a defensible formulation of the convex hull of these physical charging possibilities, provided all complete structures are present and the solver and replay checks succeed.

The new adapter should preserve this construction while exposing primal charging events, structure weights, lower bounds and feasible true-cost evaluations. It should remain separate from production code until independently reviewed. The eight seed-free, slot-aligned controls below cover linear cost, a positive continuous-physics gap, removal of the integer alternative, correct shared-capacity convexification, a closed-energy terminal construction, infeasibility, and an active capacity constraint involving two simultaneously charging buses. None establishes realistic operational performance or an asymptotic aggregation result.

## Eight analytic targets

All trips are at depot D; all deadhead times and energy are zero; slots are 60 minutes; there are four slots; base load is zero. Monetary units are arbitrary. Charging is allowed only in slots 1 and 2, between the real trips or between a real trip and an explicitly constructed terminal marker.

For controls 1–4, trips are `[0,60]` and `[180,240]`, each consuming 15 kWh. Battery and starting SOC are 20 kWh, minimum and terminal SOC are zero, charging power is 10 kW, and vehicle fixed cost is 7. Unless specified otherwise, at most two vehicles are available and the linear market coefficient is 0.1 in every slot.

| Control | Modification | Physical optimum D | CH optimum | Gap | Analytic witness |
|---|---|---:|---:|---:|---|
| 1. Linear split | Supply slope b=0 | 8 | 8 | 0 | One bus, 10 kWh total between the trips; any split across slots 1/2 is optimal. |
| 2. Convex split | b=0.2 | 13 | 61/5 = 12.2 | 4/5 = 0.8 | Physical one-bus load 5/5; CH one-bus weight 3/5, two-bus weight 2/5, aggregate load 3/3. |
| 3. Forced one bus | b=0.2, max vehicles 1 | 13 | 13 | 0 | One depot chain, load 5/5. |
| 4. Capacity changes feasible structures | b=0.2, per-slot shared capacities 4/4 kWh | 14 | 14 | 0 | A one-bus chain needs 10 kWh but can receive only 8; only two separate uncharged buses remain feasible. |
| 5. Closed-energy marker | One bus, battery/start/terminal SOC 1; real trip energy 1; explicit terminal-marker trip energy 0; power 1 kW, fixed cost 0, a=0, b=2 | 1/2 | 1/2 | 0 | Replenish exactly 1 kWh, split 1/2 and 1/2. |
| 6. Infeasible closed-energy marker | Control 5 with shared capacities 0.4/0.4 kWh | Infeasible | Infeasible | Undefined | Required replenishment 1 exceeds available 0.8 kWh. |
| 7. Two-bus shared power | Two simultaneous first trips `[0,60]`, two simultaneous second trips `[180,240]`; each 15 kWh; otherwise control 2 with max vehicles 2; shared capacities 8/12 kWh | 184/5 = 36.8 | 184/5 = 36.8 | 0 | Both buses require 10 kWh. Each can receive 4 then 6, giving aggregate 8/12. |
| 8. Uncapped two-bus comparator | Control 7 without the aggregate capacity row | 36 | 36 | 0 | Each bus receives 5 then 5, giving aggregate 10/10. |

For controls 1, 2 and 4, complete enumeration contains three structures: one direct chain, one depot chain, and two separate single-trip chains. The direct chain is SOC-infeasible. In control 4 the depot chain is also infeasible. Control 3 and each marker control contain two structures, with the direct chain infeasible. Control 6 has no feasible structure. Controls 7 and 8 have eight structures: two possible pairings of the simultaneous trip groups, each with four combinations of arc kinds. Only the two all-depot structures are SOC-feasible. These are exact combinatorial predictions, not counts measured from a solver.

### Derivation of the positive gap

Each one-bus depot chain must charge at least `30 - 20 = 10` kWh. With a positive marginal cost it charges exactly 10. Symmetric quadratic cost distributes this evenly across the two available slots. Its true cost is `7 + 0.1*10 + 0.1*(5^2 + 5^2) = 13`. Two separately started buses require no charging and cost 14. Thus D=13.

If lambda is the weight of the one-bus structure, the convexified load is `(5*lambda, 5*lambda)` and the weighted operating cost is `14 - 7*lambda`. The CH objective is `14 - 6*lambda + 5*lambda^2`, minimized on [0,1] at lambda=3/5. Its value is 61/5 and the gap is 4/5. Because each structure's charging domain is retained continuously, this is not a gap induced by a sampled finite charging menu. It is nevertheless specific to the stated depleted-terminal policy and inventory supplied to each additional vehicle.

For the two-bus controls, simultaneous first and second trip groups force exactly two buses. Both buses must charge 10 kWh. Without capacity restriction, the optimal aggregate split is 10/10, with cost `14 + 0.1*20 + 0.1*(10^2 + 10^2) = 36`. With capacities 8/12 the sum of capacities equals the required energy, forcing aggregate 8/12 and cost `14 + 2 + 0.1*(8^2 + 12^2) = 36.8`. Every feasible structure has the same cost and projected charging region, so convexification changes neither value.

## Shared capacity: where the constraint belongs

Each structure represents an **entire fleet**, not an independent vehicle. Consequently a shared slot-energy capacity C_t must be added inside every physical structure block:

```
sum(charge events of structure s in slot t) <= C_t * lambda_s.
```

The dictator has lambda=1. The CH master has one such row for every structure and slot. A further aggregate row is redundant after these scaled rows. Adding the cap only to the aggregate CH load represents `conv(unconstrained physical fleet) intersect capacity`, which can strictly contain `conv(capacity-feasible physical fleet)`.

Control 4 detects exactly this error. The unconstrained CH point has load 3/3, so it satisfies an aggregate-only cap of 4/4 and retains the erroneous-for-this-purpose CH value 12.2. No capacity-feasible one-bus structure exists. Correctly imposing the cap inside each block gives CH=14. A gap of 1.8 under the aggregate-only formulation would be a gap against a weaker relaxation, not the desired physical convex-hull gap.

This capacity extension can be implemented locally in an instrumented structure builder and corresponding master without modifying the production model. Production CG, pricing and replay would not thereby gain capacity awareness. A clean A2 comparison on these capped fixtures must therefore wait for a consistent pricing/physical-model extension; running the present production A2 and treating it as the same model would be invalid.

These aligned fixtures admit a constant-power realization on each full hour. Hence slot-energy limits translate directly to instantaneous aggregate kW limits. They model shared charging power, not a limit on the number of simultaneously occupied plugs. With arbitrary partially overlapping depot windows, a slot-total energy inequality alone is generally insufficient to certify an instantaneous power limit: event-grid rate variables or a separate interval-level scheduling/replay certificate would be required.

## Terminal SOC and energy accounting

Controls 1–4, 7 and 8 intentionally allow end-of-day battery depletion. Their total starting inventory increases with the number of vehicles. Report the initial and terminal policy adjacent to their results; do not describe the result as a fully replenished or cyclic bus-fleet finding.

Production source has no charging before the first trip or after the last trip. Simply setting terminal SOC equal to a full starting battery makes a positive-energy last trip infeasible. Control 5 therefore introduces an explicit, zero-energy terminal marker at the depot. The gap before this marker supplies a replenishment window; the marker is a modeling device, not a real service observation or native post-service charging feature. Because it consumes no energy, exact replenishment to 1 is possible within the battery bound. A state reconstruction should verify start=1, after real service=0, after charging=1 and final=1. In control 6 the maximum charge is 0.8, proving infeasibility independently of any solver status.

## Conservative numerical enclosures and unresolved statuses

For each feasible structure s, retain a valid solved tangent-model lower value l_s, the independently recomputed exact quadratic value u_s at a replayed feasible charging plan, and solver status/bound metadata. For complete enumeration, use:

```
D_lower = min_s l_s; D_upper = min_s u_s.
CH_lower = valid complete-master lower bound.
CH_upper = true quadratic objective of a replayed feasible CH decomposition.
gap in [D_lower - CH_upper, D_upper - CH_lower].
```

The ordinary `structure_true_value` drops the PWL lower value; its returned point is insufficient for the interval. The ordinary `_solve_pwl_true` maps every non-OPTIMAL solver status to `None`, which the dictator loop skips. The adapter must instead distinguish proven numerical infeasibility from timeout, numerical failure, interrupted solve, unboundedness, or another unresolved status. Any unresolved structure prevents a complete dictator certificate; any unresolved master prevents a CH certificate. An empty feasible-structure list requires an explicit infeasibility outcome, not a minimum over an empty list or a fabricated zero objective.

All bound arithmetic must retain full precision. Compute operating cost from the structure weights and quadratic energy cost from reconstructed loads, rather than deriving a true objective solely by subtracting epigraph variables from the solver objective. Record the final observed PWL slack. A configured tolerance is not evidence of actual convergence. Validate finite values, the direction and width of each interval, and objective/bound consistency. These are solver-conditional numerical certificates with declared feasibility and optimality tolerances; they are not exact rational-arithmetic bounds merely because the independent analytic targets are rational. The production nonnegative epigraph lower bound is valid for these fixtures because marginal costs are nonnegative; a future negative-price fixture requires reexamining it.

## Independent feasible replay and mutation rejection

Replay must not call the structure builder to decide feasibility. It should reconstruct timing, physical load and SOC from saved instance data and charge events. Minimum checks are:

1. Every expected trip is covered exactly once; vehicle counts, chain/kind lengths and identifiers are consistent. All travel and trip times are compatible.
2. Every charge event belongs to the stated vehicle's actual depot arc, has a valid slot and finite nonnegative energy, and lies in the depot dwell window. Direct arcs cannot carry charging.
3. Recompute overlap minutes directly from interval endpoints. Check each bus's charge-energy ceiling from power and availability, and each shared capacity from the sum of physical charge events.
4. Reconstruct SOC after pull-out, each deadhead, depot arrival, charging, subsequent service and pull-in. Enforce minimum, battery maximum and terminal policy throughout. Check depot arrival before adding energy; end-of-window capacity is sufficient here because charge is nonnegative and there is no interim consumption.
5. Recompute per-slot load, total energy, vehicle/deadhead operating cost and true system objective independently. Stored aggregate variables and reported objective must agree within declared audit tolerances.
6. For a CH witness, check nonnegative finite weights summing to one, scaled constraint residuals and charge reconstruction. Positive-weight components must represent feasible normalized physical structures. Do not silently discard small positive weights if doing so changes the represented point; normalization near zero needs explicit numerical handling because it amplifies residuals.

Useful deliberately corrupted witnesses must be rejected: duplicate/missing trips; a charge attached to a direct arc or absent connection; a charge moved to an unavailable slot; overcharging or insufficient terminal replenishment; negative or nonfinite charge; individual power excess; shared-capacity excess; forged aggregate load; forged objective; and an incomplete enumeration presented as complete. Status-handling checks should force a timeout/unknown result and verify that it cannot become an infeasibility or optimality certificate. Control 4 also rejects the especially subtle mistake of applying capacity only after convexification.

The positive-gap control qualifies the physical construction, and the active two-bus controls qualify the capacity row. They should precede any retained-column or learned-price comparison. There is no reason to expend model-training effort before these physical and numerical prerequisites pass.
