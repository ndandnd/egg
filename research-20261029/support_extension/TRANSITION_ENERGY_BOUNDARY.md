# Why transition energy defeats the minimum-requirement statistic

Analytical counterexample only; no code, instance search, data, runtime or new qualification. This is a classical boundary of the paper's zero-transition-energy reduction, not a new hardness or empirical claim.

## A physically consistent abstract timetable

There are two A services of energies (13,1), two B services of energies (13,1), identical batteries of capacity20, zero reserve, unit charging efficiency and full initial/final inventory. This counterexample is charge-only: early exports are disabled. All four A-to-B edges are allowed, with transition energies

    t = [[0,6], [6,0]].

Transition monetary costs are zero. Within each batch the services overlap, so a bus serves at most one service from each batch. Give A services the interval [0,1], a common early charging interval [1,2] at a single depot, a separate transit interval [2,3], and B services [3,4]. All buses are available for the early interval; shared early energy/power budget is14, with one connector of power14. The terminal interval is [4,5], with one connector of power40 and shared budget40. Acceptance powers are at least those connector powers. Nonservice consumption other than the declared transitions is zero.

Each paired duty travels for one positive time unit during [2,3], consuming its specified transition energy nonnegatively, before its B service. This avoids treating a positive-energy transition as a zero-duration charging opportunity. Zero-energy edges over positive duration are allowed by this abstract model; no universal positive traction/auxiliary lower bound is imposed. Services consume nonnegatively, for example uniformly during their intervals. A-only/B-only duties need no such interservice transition. Access legs to the common early/terminal resources consume zero under the original idealized common-window assumptions. This is a service-dependent allowed-transition model; it is not asserted to come from one common metric distance/time/auxiliary law. A transition may be viewed as a mandatory duty leg/task, not an optional excursion that can be omitted to evade its consumption.

Charging is continuous, may be serially allocated, and has no minimum sessions. Since all buses share each charging window and acceptance is adequate, the total early/terminal budgets suffice for serial realization. There is no charging during transit or B service. No idle bus can replenish another bus's battery.

## Full matchings: the statistic loses a feasible efficient branch

For a paired bus with A energy a, transition t and B energy b, early battery purchase x must satisfy

    max(0,a+t+b−20) <= x <= a.

The lower bound is necessary to reach the next charging opportunity after B; the upper bound is early capacity after A. Nonnegative consumption makes the complete transit/B prefix feasible whenever the final inventory is nonnegative. Terminal refill is a+t+b−x.

The identity matching has total transition energy0, total duty consumption28 and summed minimum early requirement R=6. Its load segment is

    (E,L) = (E,28−E),  6 <= E <= 14.

The cross matching has total transition energy12, total consumption40 and R=0. Its load segment is

    (E,L) = (E,40−E),  0 <= E <= 14.

Both segments satisfy the terminal budget40. At E=6 the identity has terminal purchase22 while the cross has34. The identity point is Pareto efficient even against the entire cross segment: a cross point with early purchase at most6 has terminal purchase at least34. Thus selecting only the matching with minimum R discards an efficient branch of the cost-labelled load set even within the fixed two-bus layer. A minimum-R statistic cannot reconstruct the common total-consumption term, which has become assignment-dependent.

For the fixed coordinatewise strictly increasing convex objective F(E,L)=E+L, the full-layer physical value is 2f+28, achieved by every identity-segment point. Retaining only the minimum-R cross matching instead gives 2f+40. Linear F is convex and differentiable; strict convexity is unnecessary for this failure. The point is not numerical optimality tolerance: the two exact constant totals differ.

## Optional whole-problem version, including singletons

Suppose the original fleet choice permits unmatched services as standalone duties and charges the same fixed fee f>0 per counted bus. With zero matching edges there are four buses, no transitions, consumption28 and early interval [0,14]. With one matching edge there are three buses. Either identity edge leaves consumption28, while a cross edge gives34. Pairing the two small services has R=0, so the minimum-R three-bus choice can retain a consumption28 branch. With two edges the only matchings are the two already analyzed. Every stated interval admits charging within the budgets, including the feasible identity two-bus schedule.

The true optimum for F(E,L)=E+L is 2f+28: it has minimum fleet size and the minimum possible total consumption. A procedure retaining only a minimum-R matching per cardinality—even giving it the best choice among the tied one-edge minimizers—can attain no less than

    min(2f+40, 3f+28, 4f+28)
      = 2f+28 + min(12,f) > 2f+28.

Hence the failure is not rescued by allowing singletons or charging a common positive fee. At f=0 the whole-problem scalar objective can tie a standalone/partial alternative, so the strict whole-problem statement intentionally requires f>0. The fixed-cardinality branch loss remains regardless of fee.

## Scope of the obstruction

One would need at least the interaction between early requirement and assignment-dependent total energy, not merely the smallest R, to preserve all relevant branches. This example does not prove that two statistics always suffice or propose a replacement algorithm. It explains exactly why the paper fixes zero transition energy: under that assumption mandatory energy is assignment-independent, enabling one cardinality matching statistic to determine the efficient frontier. It does not claim failure under every positive-transition model, under a metric movement model, or in the public timetable.
