# Analytical robustness assessment and proposed fixed qualification design

27 September 2026. Independent analytical review of the four-period model
frozen at `7bf913a`, described in
[`CYCLIC_GAP_PROTOCOL_20260927.md`](CYCLIC_GAP_PROTOCOL_20260927.md).
This document contains arguments and a proposed prospective design. **No new
parameter grid, native optimization, cluster job or scientific result file
was executed or changed.** One exact arithmetic substitution checked the
fractions in the joint constructive example below.

## Assessment

The original positive gap is **not robust to adding reserve or charging losses
while keeping its binding early charger at 10 kW and its battery at 20 kWh**.
Either change removes the one-bus structure. When the remaining two-bus
structure is feasible, its projected charging set is convex and its planning
gap is zero. This is a physical change in the feasible set, not a numerical
failure.

A **single 30 kW terminal connector does preserve the original result** under
the stated lossless, continuous-power, zero-switch-time assumptions. The two
buses can charge consecutively while aggregate terminal power stays constant.
Connector count and connector power must be stated separately.

A nearby explicitly modified model has a positive reserve, charging loss,
finite single connector and strict early power headroom simultaneously:
capacity 20 kWh, reserve 1 kWh, efficiency 19/20, early individual/shared limit
12 kW and one 30 kW terminal connector. Its exact planning gap is
`94249/28880 ≈ 3.2634695291`. This is a new analytical construction with
disclosed changes, not evidence that the unchanged original hardware tolerates
those perturbations. Strict inequalities below establish an open neighborhood
of this new construction with a positive gap.

## Common conventions and generalized physical projection

Keep the frozen timetable: service A in [0,1], service B in [2,3], an early
charging window [1,2] and a terminal window [3,4]. Each service consumes
15 kWh **at the battery**. Every used bus starts and finishes full at capacity
`C=20`; each used bus serves at least one mandatory service. There are at most
two identical buses, no deadheads, discharge, idle consumption or charging
outside the two declared windows. A service remains on its assigned bus.

For the actual perturbations, let:

- `r` be a minimum battery reserve in kWh, with `0 ≤ r ≤ 5`;
- `η ∈ (0,1]` be a constant grid-to-battery charging efficiency, identical in
  both windows; service consumption already includes battery-side driving
  energy and is not divided by η;
- `P_E` be both the early individual grid-power limit and the early shared
  grid-power limit, in kW;
- `K` be the terminal connector's grid-power limit, with one connector and
  vehicle acceptance at least `K`; the proposed design has `K ≤ 30`;
- `x` be early **grid** energy, and `z` be terminal grid energy, in kWh.

Both windows last one hour, so their numerical energy limits are `P_E` and
`K`. This equivalence would require duration factors for different windows.
Switching is instantaneous; buses are present for the entire terminal window;
charging may use any nonnegative power up to the stated limit; there is no
taper, setup energy, minimum session duration or switching fee.

Replenishment implies, for both fleet structures,

`η(x+z)=30`, hence `T:=x+z=30/η` and `z=T−x`.

There is no extra initial-energy subsidy from using two buses: each returns
its own initial battery inventory. Define

`ℓ=max(0,T−K)`, `u=min(P_E,15/η)`,

and the one-bus reserve threshold

`h₀=(10+r)/η`, `h=max(ℓ,h₀)`.

The **complete two-bus projected set** is

`x ∈ [ℓ,u], c=2f`,

provided `ℓ≤u`. A's bus receives early battery energy `ηx` and terminal grid
energy `15/η−x`; B's bus receives terminal grid energy `15/η`. The upper
bound `ηx≤15` prevents A from overfilling before the terminal window. Both
buses reach battery SOC 5 after their service, so `r≤5` is necessary and
sufficient for their service-side reserve condition.

The **complete one-bus projected set** is

`x ∈ [h,u], c=f`,

provided `h≤u`. Its battery trajectory at event boundaries is

`20 → 5 → 5+ηx → ηx−10 → 20`.

The reserve before terminal charging gives `ηx≥10+r`; the early overfill
condition gives `ηx≤15`. The common terminal cap gives the same lower bound
`x≥ℓ` as in the two-bus case. All intervening charge trajectories are monotone,
so these boundary and rate constraints suffice. There are exactly these two
unlabeled service partitions; no missing assignment can rescue an infeasible
one-bus branch.

If only the two-bus branch survives, its aggregate set `[ℓ,u]` with fixed
intrinsic cost `2f` is already convex. Convexifying complete schedules cannot
improve its optimum. If `ℓ>u`, neither branch is feasible; report infeasibility,
not a zero or undefined objective silently replaced by zero.

## One connector: an explicit continuous-time realization

For a two-bus point `x∈[ℓ,u]`, set

`q_A=15/η−x`, `q_B=15/η`, `q=q_A+q_B=T−x`.

Run the terminal connector at constant aggregate power `q≤K` throughout the
one-hour window. Charge A first for `q_A/q` hours and B next for `q_B/q` hours.
Each bus has one uninterrupted charging session; no simultaneous plug use or
preemption is required. A full bus may wait until time 4 after its session.
Its battery increases monotonically to 20, and B does likewise. For one bus,
charge at power `T−x≤K` for the whole terminal hour. Early charging is at
constant power `x≤P_E` on A's bus only.

Thus every point in the intervals above has a connector-feasible realization.
The aggregate power is constant in each one-hour charging window. The frozen
quadratic cost in window energy also equals the corresponding integral of
quadratic aggregate power under this realization; sequentializing the buses
does not secretly introduce an aggregate power spike.

In the original nominal model (`η=1, r=0, P_E=10, K=30`), the hull's two-bus
supporting point `x=0` charges A at 30 kW from 3 to 3.5 and B at 30 kW from
3.5 to 4. The one-bus point charges 20 kWh at 20 kW over [3,4]. All projected
sets, objectives, prices and the gap `169/80` are unchanged.

This construction does not cover positive plug-switching time. A nonzero
switching delay invalidates the saturated two-bus `x=0` schedule at 30 kW in a
one-hour window. A subsequent model must include that delay and, if using a
time-resolved supply cost, recompute the cost of the resulting power profile.
Likewise, a single connector rated **10 kW**, instead of the specified 30 kW,
makes the original one-hour terminal window infeasible: even with 10 early
kWh, at least 20 terminal kWh are required.

## Exact reserve translation versus fixed-capacity reserve

An SOC translation gives a valid but narrower identity. Replace battery
capacity and initial/terminal SOC 20 by `20+r`, set reserve to `r`, and add `r`
to every original SOC trace. Retain the original service demands, charging
energy/rates and all costs. This is a bijection between the original feasible
schedules and the translated schedules. The physical and convexified values,
including the positive gap, are exactly unchanged.

It increases installed battery capacity; it does **not** establish robustness
to imposing reserve on a fixed 20 kWh battery. At fixed `C=20`, `η=1` and
`P_E=10`, any `r>0` requires one-bus early energy `x≥10+r>10`, so that branch
is infeasible. For `0<r≤5`, the two-bus branch remains feasible and has zero
planning gap. For `r>5`, neither bus can complete even one 15 kWh service from
full charge while respecting the reserve, so the whole model is infeasible.

Increasing only the **shared** early limit is insufficient if the individual
bus limit remains 10 kW. A constructive positive-reserve perturbation must
increase both limits, increase the charging duration, or change another
explicit physical assumption. Those are different models and must be labeled.

## Losses: accounting identity versus fixed grid hardware and tariffs

With fixed `C=20, r=0, P_E=10`, any efficiency `η<1` gives at most `10η<10`
early battery kWh. The one-bus branch is therefore infeasible for arbitrarily
small positive loss. At `K=30`, the two-bus interval is

`x ∈ [max(0,30/η−30),10]`.

It remains nonempty for `η≥3/4`; for `3/4≤η<1` its gap is zero. For `η<3/4`,
the maximum 40 grid kWh across the two windows cannot supply the required
30 battery kWh, so the entire model is infeasible. These conclusions also
hold with any fixed reserve `0≤r≤5`, except that at `η=1,r=0` the original
one-bus branch is present.

A change of coordinates must not be reported as a fixed-tariff robustness
test. If `y=ηx` and `w=ηz` denote battery-side energies, the original feasible
set in `(y,w)` is preserved by increasing grid limits to `10/η` and `30/η`.
The original cost is also preserved only if the grid-side coefficients are
transformed consistently:

`F_η(x,z)=4ηx + η²(x²+z²)/10 = 4y+(y²+w²)/10`.

Together with the SOC translation above, this gives an exact isomorphism of
the model, not evidence about unchanged charger ratings or unchanged grid
tariffs. If instead the grid-side supply function stays

`F(x,z)=4x+(x²+z²)/10`,

the battery-coordinate cost becomes

`4y/η + (y²+w²)/(10η²)`.

The objectives, minimizing loads and gap must then be recomputed even if
hardware is enlarged to keep the same battery-side feasible set. Reporting
30 grid kWh after adding losses would violate cyclic energy balance; the
correct total is `30/η` for every used-fleet structure.

## A sufficient positive-gap proposition for genuine perturbations

Keep the grid-side cost fixed at

`G_T(x)=a x + [x²+(T−x)²]/10`,

and let `k=1/5`, `m=T/2−5a/2`. Then

`G_T(x)=G_T(m)+k(x−m)²`.

Suppose both branches exist and

`ℓ < m < h ≤ u`, `f>0`, and `f < 2k(h−ℓ)(h−m)`.

Write `d=h−ℓ`. At fixed aggregate `x∈[ℓ,h]`, the largest feasible one-bus
weight is `(x−ℓ)/d`: the one-bus component must have early energy at least `h`
and the two-bus component at least `ℓ`. This bound is attained by mixing the
two physical endpoint schedules `h` and `ℓ`. Since `f>0`, this maximizes the
cheap one-bus weight and gives the lower boundary of the **complete** hull:

`c_min(x)=2f−f(x−ℓ)/d` for `ℓ≤x≤h`,

`c_min(x)=f` for `h≤x≤u`.

The physical two-bus optimum is `m`, and the one-bus optimum is `h`. The hull
optimum lies strictly between `m` and `h` at

`x*=m+f/(2kd)`, `λ*=(x*−ℓ)/d`.

The complete values are

`D=G_T(m)+min{f+k(h−m)²,2f}`,

`CH=G_T(m)+2f−f(m−ℓ)/d−f²/(4kd²)`.

Consequently,

`D−CH=min{k(h−x*)², f(m−ℓ)/d+f²/(4kd²)}>0`.

Every mixture component satisfies the reserve, loss and connector constraints
**before** convexification. The averaged point is a planning relaxation, not
a dispatchable fractional bus fleet. The proposition is sufficient; it is
not claimed to characterize every positive-gap parameter combination.

For strict physical headroom, require `h<u` as well. All these inequalities
are strict at the joint example below, with `0<r<5` and `0<η<1`. Their
continuity establishes a neighborhood of actual reserve/loss/power
perturbations with a positive gap. The original zero-reserve, binding-power
point does not itself satisfy this headroom condition.

## Joint positive-reserve, lossy, one-connector example

Fix `C=20`, `r=1`, `η=19/20`, `P_E=12`, `K=30`, `f=7`, `a=4`.
Initial and terminal SOC remain exactly 20 for each used bus. Keep both
services and the four original unit periods unchanged. Then

`T=600/19`, `ℓ=30/19`, `h=220/19`, `u=12`, `d=10`,

`m=110/19`, `x*=573/76`, `λ*=453/760`.

In particular, `h<u` leaves `8/19` grid kWh of early headroom. The relevant
threshold is `2kd(h−m)=440/19>7`. All sufficient inequalities hold.

The physical one-bus optimum buys early `220/19` grid kWh, delivering 11
battery kWh, and buys 20 terminal grid kWh, delivering 19 battery kWh. Its
SOC trace is

`20 → 5 → 16 → 1 → 20`.

The hull's two-bus supporting endpoint buys early `30/19` grid kWh on A's bus,
delivering `3/2` battery kWh. A's SOC goes from 20 to 5 to `13/2`, then back
to 20 with terminal grid charge `270/19`. B ends its service at 5 and buys
`300/19` terminal grid kWh. The terminal sum is exactly 30. A uses the single
30 kW connector for `9/19` hour and B for `10/19` hour. Both respect reserve 1.

The independent physical two-bus optimum instead uses early `110/19` grid
kWh and terminal `490/19` grid kWh; it is feasible by the same connector
construction. Exact objectives are:

| Quantity | Exact value |
|---|---:|
| One-bus physical objective | `38527/361` |
| Two-bus physical objective | `38634/361` |
| Physical optimum D | `38527/361` |
| Complete-hull optimum CH | `2987911/28880` |
| Planning gap | `94249/28880` |

The one-bus physical solution beats the best two-bus solution by `107/361`.
The hull mixes the physical one-bus endpoint with weight `453/760` and the
physical two-bus endpoint with weight `307/760`. Its aggregate grid loads are
`(573/76,1827/76)`, summing to `600/19`. These arithmetic values describe a
construction, not an estimated prevalence or a calibrated operational case.

## An exact terminal-power threshold with one connector

For an additional reviewer control, keep the original `C=20,r=0,η=1,P_E=10`,
`f=7,a=4`, but vary the single terminal connector's power `K≤30`. Vehicle
acceptance remains 30 kW, so `K` is the binding terminal resource.

- If `K<20`, the complete physical model is infeasible.
- At `K=20`, both structures can only have `x=10`; the one-bus option is
  cheaper and the gap is zero.
- For `20<K≤30`, the two-bus interval begins at `ℓ=30−K`, the one-bus point
  remains `h=10`, and `d=K−20`. The physical optimum remains 97.

On the sloping hull boundary the unconstrained minimizer is
`x*=5+35/[2(K−20)]`. Its derivative at the left endpoint is negative for
every `d>0`, because `2−(2/5)d−7/d<0` (the associated quadratic has negative
discriminant). Therefore the hull optimum leaves `x=10` exactly when
`K>47/2=23.5`. The exact gap is

`0` for `20≤K≤47/2`,

`[5−35/(2(K−20))]²/5` for `47/2<K≤30`.

For example, one 24 kW connector gives gap `5/64`; one 30 kW connector
recovers `169/80`. Finite-connector robustness is therefore a conditional
power/horizon claim, not an assertion that any single charger suffices.

## Proposed prospective qualification: 16 unique physical cases

Before execution, freeze a new protocol, its physical implementation, an
independent exact oracle/replay specification and a new exclusive output
directory. Do not relabel the original construction or edit its results.
All cases below retain the two services, `C=20`, full initial/terminal SOC,
`f=7`, the same grid-side cost `F(x,z)=4x+(x²+z²)/10`, one-hour windows and
one terminal connector. Reserve, efficiency and capacities are the only
declared changes.

**Reserve/loss/early-headroom block:** the full Cartesian product

`r ∈ {0,1}`, `η ∈ {1,19/20}`, `P_E ∈ {10,11,12}`, with `K=30`.

This has 12 cases and contains unchanged-hardware negative controls,
boundary cases and the joint positive example. Preserve every case. The
analytical projection predicts eight positive-gap and four zero-gap cases;
the zero-gap cases lose the one-bus branch but retain feasible two-bus
schedules. These are prospective algebraic predictions, not observed solver
outcomes. A disagreement must be investigated, not silently repaired.

**Terminal-power block:** retain `r=0,η=1,P_E=10` and use

`K ∈ {10,20,47/2,24,30}`.

The `K=30` case already occurs in the 12-case block, so execute only the four
new cases. This adds one global infeasibility control, two zero-gap controls
and one small positive-gap case. The combined 16-case design therefore
predicts nine positive gaps, six zero gaps and one infeasible case, with all
classifications retained in the report.

Use exact rational parameters and independently enumerate both physical
partitions. The oracle can minimize a scalar quadratic over each complete
physical interval and over the complete hull boundary; it must not replace
continuous charging by a sampled menu. Independently replay grid-to-battery
energy conversion, every SOC event, both power limits, final replenishment
and explicit nonoverlapping terminal plug intervals for each positive-weight
component. A connector count checked only after mixing is insufficient.

Save one-bus/two-bus feasibility separately; the physical and hull values;
loads and mixture weights; all endpoint/supporting schedules; the analytical
minimum reserve and power margins; and model-side units for every input and
output. An infeasible physical model has no reported numerical gap. A
one-bus-infeasible case can still have a valid zero gap through its complete
two-bus branch. Do not clip an infeasible charge to a cap and retain its cost.

If a native implementation is also compared, use the same predeclared
numerical acceptance rules and fixed resource caps; preserve unresolved
statuses, bounds, tracebacks and accounting. Exact analytical feasibility
does not authorize reclassifying a failed native solve. No data selection,
training, cluster allocation or large solver campaign is needed to establish
the analytical claims in this document.

As nonexperimental identity checks, verify separately that adding a common
SOC offset while increasing capacity, and consistently changing grid/battery
coordinates with transformed costs/caps, reproduce the original model.
Report these as implementation identities, not as additional evidence of
fixed-hardware or fixed-tariff robustness.

## Manuscript claims supported by these arguments

Supported now: the original construction can use one 30 kW terminal connector;
its positive gap is fragile to positive reserve or losses at unchanged early
power; and a fully specified alternative construction has positive reserve,
5% charging loss, one finite connector and a positive exact gap with early
power headroom. The general sufficient proposition explains which physical
and economic inequalities produce that gap.

Not yet supported: a real-bus reserve/taper model, nonzero connector switching
time, uncertain or nonlinear efficiency, a calibrated supply curve, typical
operating conditions, or empirical prevalence. The reserve level and
efficiency values here are transparent synthetic parameters, not estimates.
These elementary deductions require no additional literature attribution
beyond the original model and its existing convexification references.
