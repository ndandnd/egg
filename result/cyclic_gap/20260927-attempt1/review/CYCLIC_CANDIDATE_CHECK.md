# Independent analytical check of the proposed cyclic witness

27 September 2026. This analytical check was drafted from a candidate sent by
the parent researcher before this reviewer read the execution output. The algebra
below is exact. A subsequent independent reconstruction of the frozen driver's
output passed: see [CYCLIC_INDEPENDENT_REVIEW.md](CYCLIC_INDEPENDENT_REVIEW.md).
The proof plus that audit support the specified reference model, not a claim
about the production EVSP adapter or an operational timetable.

## Required complete physical layout

Two sequential mandatory services consume 15 kWh each. All used buses have
battery capacity20 kWh and initial/terminal SOC20. At most two buses may be used;
each used bus must cover at least one service. There are no deadheads, losses,
V2G, pre-service charging needs or extra charge windows. Zero deadheads and unit
efficiency are disclosed synthetic assumptions, not operational estimates.

An early window lies after service1 and before service2; only the bus that has
completed service1 has battery space then. A common native terminal window lies
after both services and is available to every used bus. Individual early-window
capacity is at least10 kWh, and the shared early limit is10. Individual terminal
capacity is at least20 kWh, and shared terminal capacity is30. If windows are an
hour long, these energy limits can be realized by constant powers in kW. Enough
connectors are assumed; a shared power limit alone does not model plug counts.

Every service is covered exactly once, with no interruption/switching buses.
Charging has no intrinsic cost beyond the common supply function, and a used
bus costs7. Because every used bus returns to its own initial SOC, **both fleet
structures buy exactly30 kWh**. Additional buses do not donate free net energy.

## Physical branches and complete hull

Let `x` be early energy and `30−x` terminal energy. The supply cost is

`G(x) = 4x + [x²+(30−x)²]/10 = 90−2x+x²/5`.

For one bus, SOC goes `20 -> 5 -> 5+x -> x−10 -> 20`. Nonnegative SOC before
terminal charging forces `x>=10`; the early cap forces `x<=10`. Hence the only
one-bus aggregate load is `(10,20)`, with intrinsic cost7 and total cost97.

For two buses, give service1 to A and service2 to B. A has post-service SOC5,
receives early `x`, and terminal `15−x`; B receives terminal15 after its service.
All `0<=x<=10` are feasible under the stated individual/shared limits. This is
the entire two-bus aggregate-load segment, with intrinsic cost14. Its physical
objective `14+G(x)` is minimized at `x=5`, costing99. The physical optimum is
therefore **D=97**.

Let `lambda` denote one-bus weight in a convex combination. The full hull in
`(c,x)` is exactly

`0<=lambda<=1, 10lambda<=x<=10, c=14−7lambda`.

Necessity follows by mixing `x=10` with a two-bus point in `[0,10]`. For
`lambda<1`, sufficiency follows from the physical two-bus point
`x_B=(x−10lambda)/(1−lambda)`; for `lambda=1`, `x=10`. Thus this is the complete
projected hull, not just a relaxation inferred from sample schedules.

At fixed `x`, the hull objective decreases with `lambda`, so
`lambda=x/10`. The reduced convex objective is

`104−27x/10+x²/5 = 7591/80 + (x−27/4)²/5`.

It has its minimum at `x*=27/4=6.75`, `lambda*=27/40=.675`. Consequently

`CH=7591/80=94.8875`, and `D−CH=169/80=2.1125`.

A transparent realizing mixture is weight27/40 on the physical one-bus
`(10,20)` schedule and weight13/40 on the physical two-bus `(0,30)` schedule.
Every component is cyclic and respects the shared constraints before mixing.

## Economic interpretation useful for a figure

At the physical optimum `(10,20)`, the own marginal prices are `(6,4)`.
Its private objective is147. At those posted prices the best physical response
is two buses with `(0,30)`, private objective134: **own-price fleet regret13**.
Supplier LOC at that own gradient is zero. This does not mean social cost would
fall by13 after a deviation; the posted-price regret holds prices fixed.

At the common CH prices `(107/20,93/20)=(5.35,4.65)`, both hull-supporting
physical components have private objective307/2=153.5. The physical planner
optimum therefore has fleet LOC0. For nonnegative supply loads,
`F*(p)=[(p_early−4)²+p_late²]/.4=4689/80=58.6125`, so supplier LOC is
`90−146.5+58.6125=169/80=2.1125`, exactly the planning gap.

Randomizing the two supporting schedules on different days costs
`.675*97+.325*104=99.275` in expectation, not94.8875. This distinction makes a
clear illustration of cost at the mean load versus mean realized cost.

## Implementation obligations and remaining scope

An implementation must enumerate the two assignment structures completely,
represent native terminal windows without extra service obligations, charge
used-bus costs consistently, and independently replay every positive hull
component. Verify its window and power conventions admit the trajectories above.
This proof covers no partial-window chronology, nonlinear charging losses,
finite plugs, operational calibration, independent operators or strategic
price anticipation. Solver output should be compared to the exact fractions;
the proof is not permission to reinterpret an unrelated fixture as this model.
The later audit verified these obligations against all saved schedules from the
frozen four-period experiment; the listed wider-model limitations remain.
