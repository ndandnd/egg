## A feasible fleet as a solver starting point — 28 September 2026

Physical pricing remains the main measured computational cost. We are adding a
simple baseline before pursuing learned routes: give the solver an already
checked feasible fleet as its starting suggestion. The solver still chooses
charging and checks the result; the suggestion itself proves no optimality.

The opt-in core passed 40 focused tests. A small CBC functional check also
returned a validated numerical solution; this does not establish performance
on Gurobi or the public cases. The code records hint submission separately from
solver acceptance, keeps invalid inputs explicit, and includes checking and
preparation in the pricing time budget.

The planned diagnostic compares 16 fixed-price calls across the existing four
development cases, with identical time limits and counterbalanced call order.
Both arms retain the same known feasible-plan baseline when interpreting
quality. We will report native incumbents and bounds, complete online time,
start preparation, and the original source-generation cost separately. The
two public depots share one timetable. This tests the pricing bottleneck and
does not by itself establish faster iterative solving or a learning benefit.

No cluster pilot has launched. The next step is to implement and freeze its
runner and exact inputs, then execute the prospective single-job comparison.

[Checked starting-point implementation](https://github.com/ndandnd/egg/blob/d0df8d7440d026aabe236bafa3c8031b31b14bc9/research-20260928/pricing-start/README.md) · [Prospective pilot protocol](https://github.com/ndandnd/egg/blob/d0df8d7440d026aabe236bafa3c8031b31b14bc9/doc/PRICING_START_PILOT_PROTOCOL_20260928.md).
