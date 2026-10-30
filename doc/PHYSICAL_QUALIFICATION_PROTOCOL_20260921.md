# Tiny continuous-charging qualification — 21 September 2026

Prospective deterministic engineering qualification, separate from the failed
earlier probe and every protected population. Freeze this protocol and code in
Git before the first experimental run. Use CBC locally, one thread, no seeds,
at most 32 enumerated structures per fixture, eight fixtures, ten seconds per
LP call, 40 seconds per fixture, and a 240-second process-group watchdog.

Enumerate complete trip-chain/arc structures. Each retains continuous charging
and SOC propagation. Solve physical structures individually and the convexified
master with lambda-scaled structure polytopes. Retain tangent-model lower bounds
and exact-quadratic evaluations of replayed feasible solutions, with a declared
operand-scaled numerical allowance. Reject all unresolved statuses rather than
classifying them as infeasible. The gap interval is D_lower−CH_upper through
D_upper−CH_lower. These are numerical solver-conditional bounds, not exact
rational proofs or formal floating-point certification.

Shared capacity means **aggregate depot power** with full-hour availability;
it is enforced inside every scaled fleet structure. It is not a count of plugs.
All fixture event times align with slots, so constant power within each slot
gives an implementable profile. Reject off-grid fixture times in this adapter.
An independent replay recomputes coverage, chronological travel, energy, SOC,
charging limits, aggregate load, intrinsic operating cost and capacity from
recorded charges, without reading optimization constraints.

Two depot trips [0,60] and [180,240] each use 15 kWh, battery/start SOC20,
minimum/terminal0, charging10 kW, fixed bus cost7, a=.1, U=0:

| Fixture | Changes | Expected D | Expected CH |
|---|---|---:|---:|
| linear_split | b=0, at most two buses | 8 | 8 |
| convex_split | b=.2, at most two buses | 13 | 12.2 |
| forced_one_bus | b=.2, one bus | 13 | 13 |
| capacity_filters_structure | b=.2, two buses, charging-slot caps4/4 kWh | 14 | 14 |

The two-bus alternative has additional initial stored energy. These cases
explicitly allow battery depletion and cannot establish cyclic-fleet economics.
For the positive-gap case, CH uses one-bus weight .6, two-bus weight .4 and
load3/3. The cap4/4 case rejects that one-bus structure before convexification;
an average-only cap would incorrectly preserve the relaxed12.2 alternative.

A separate replenishment control has one real trip [0,60] using1 kWh and an
explicit zero-energy terminal marker [180,240], one bus, initial/battery/
terminal SOC1, power1, operating cost0, a=0,b=2,U=0:

| Fixture | Changes | Expected D / CH |
|---|---|---|
| replenished_terminal | no shared cap | .5 / .5; load .5/.5 |
| replenished_infeasible | charging-slot caps .4/.4 | both infeasible |

The terminal marker permits post-service charging within the existing inter-trip
model. It is an explicit modeling device, not an ordinary passenger trip or a
claim that production already models unrestricted overnight charging.

Finally, duplicate each real trip in the depleted-terminal model: two simultaneous
first trips and two simultaneous last trips, exactly two buses, b=.2:

| Fixture | Shared charging-slot caps | Expected D / CH |
|---|---|---|
| two_bus_uncapped | none | 36 / 36; load10/10 |
| two_bus_shared_power | 8/12 kWh | 36.8 / 36.8; load8/12 |

Record all successes, infeasible structures and failures. Do not tune fixtures,
budgets or tolerances after viewing outcomes. A defect correction requires a
new version and a preserved failed attempt. Advancement requires analytical
agreement, replay success, and independent non-author code/result review.
