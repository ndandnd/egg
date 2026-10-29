# Independent analytical review: V2G losses

Reviewed `V2G_LOSSES_ASSESSMENT.md` analytically. No numerical tool calculation, imports, execution, tests, new cases or source changes were used. This is not numerical qualification.

**Assessment: valid under its stated ideal common-window assumptions.** The accounting identity, counterexample and restricted cycle-elimination argument support the claimed limitation. They do not establish a new lossy threshold theorem.

## Energy accounting and counterexample

With grid purchases C and exports D, battery exchange is ηc C−D/ηd. Full initial/final inventory requires terminal battery replacement S−ηc C+D/ηd. Dividing by terminal charging efficiency and substituting E=C−D gives exactly

    L=S/ηc−E+(1/(ηcηd)−1)D.

The total net grid purchase E+L therefore includes the stated positive exported-throughput loss term under strict round-trip loss. It is not fixed by service energy alone.

The two standalone-bus example is feasible. Each begins at 2; after A, its bus holds 1. Its early grid purchase 1/2 adds battery energy 1/4, leaving 5/4. The B bus exports 1/2 grid unit before its service, losing 1 battery unit and moving from 2 to 1; its service then leaves 0. All intermediate inventories stay in [0,2]. The two early actions each require half an hour at grid power 1 and can be serialized. Terminal grid purchases 3/2 and 4 restore the respective battery deficits 3/4 and 2. Their sum 11/2 fits in the terminal unit window at power 6 and can be serialized. Without early action each terminal grid demand is 2, totaling 4. Both plans have net early load zero and the same bus count but distinct terminal loads. The complete joint projection cannot lie on the lossless fixed-total-energy line.

That second point can be dominated when terminal supply cost is nondecreasing. This does not invalidate it as a counterexample to equality of the full physical projection; it does mean the example alone does not show that loss-induced extra dimensions change an efficient frontier or a support outcome. The assessment appropriately makes that distinction.

## Cycle removal

Reducing C_v by δ and D_v by ηcηdδ preserves battery exchange exactly. Taking δ=min(C_v,D_v/(ηcηd)) eliminates one direction. Both gross connector use and net early grid purchase weakly decrease, while terminal demand and all service-window endpoint inventories remain unchanged.

Physical implementation needs the stated common early availability, no intervening service during that window, continuous controllable charging, and no minimum-power/duration obligations. A monotone charge or discharge from the original starting inventory to the unchanged feasible ending inventory remains within the SOC interval and uses no more connector time. Reserializing all such actions preserves the shared-connector constraint. The proof need not preserve an arbitrary old within-window trajectory, only supply a feasible replacement with the same relevant endpoints.

Economic dominance requires equal-rate net settlement and nonnegative posted early price, or a planner objective nondecreasing in early grid load at the unchanged terminal load. The objective must be defined on the replacement's admitted signed load. A strictly positive price, or strictly increasing objective over the removed-load interval, gives strict improvement under strict loss. Zero prices can retain tied cycles. Negative prices, asymmetric tariffs, subsidies, time-varying within-window prices, different availability windows or intervening SOC requirements are outside this reduction.

The cycle-free boxes and sign-pattern formulation are sound: a nonnegative battery exchange determines C_v=x_v/ηc and a negative one determines D_v=ηd(−x_v). Shared gross grid throughput and the terminal grid constraint are then the displayed expressions. For rational data, fixed sign patterns yield rational polyhedra with the bounded inventory/throughput conditions giving polytopes. Aggregating positive and negative variables without preserving each bus's sign would enlarge this reduced set improperly. No discrete-convex matching characterization follows merely from this union representation.

## Suggested concise manuscript limitation

> The V2G classification assumes lossless exchange and equal purchase/export settlement. With charging and discharging efficiencies ηc,ηd, full replenishment instead gives terminal grid energy L=S/ηc−E+(1/(ηcηd)−1)D, where E is early net grid load and D early exported energy. Thus net load alone no longer determines terminal demand, and the lossless one-dimensional matching-threshold classification does not transfer directly. Under common-window physics and nonnegative prices or marginal supply costs, within-bus cycles can be removed for optimal values; a general support classification with losses remains open.

This remark should be presented as analytical scope, not an efficiency-robustness theorem or a public/empirical V2G result.
