# Continuous-cardinality shortcut: independent counterexample

**REFUTED in general, even when every integer cardinality is feasible.** The proposed convex relaxation need not equal the convexified efficient set or preserve monotone convex planning values. This is symbolic analysis of the current `lossy.tex` formulas only; no data, numerical execution, imports, tests, hashes or other agent's candidate were used.

## A one-pair rational instance

Take n=1, complete allowed graph, B=1, a=b=3/4, charging efficiency alpha=1/2, discharging efficiency delta=1, early gross budget K=2, terminal budget H=3, and fee f=2. All other common-window assumptions are those of the theorem. Then

`S=3/2`, `P=3/4`, `kappa=1`, `nu=1`, `r_0=0`, `r_1=1/2`, `U=3/2`.

Both actual cardinalities have nonempty physical frontier intervals. Substituting into the reviewed threshold formula gives

- m=0: `t_0=0`, `L_0(E)=3−E`, `0<=E<=3/2`, operating cost4;
- m=1: `t_1=1`, `L_1(E)=3−E`, `1<=E<=3/2`, operating cost2.

At m=0 the terminal cap removes the negative-E/export piece. At m=1 the single paired bus has positive mandatory early battery exchange1/2, so its grid purchase is at least1 and the remaining segment likewise has no export. These are the entire reduced cardinality frontiers, not chosen points. The existing dominance theorem extends nonnegative-price bounds from them to the full physical set, including any dominated cyclic allocations.

For the coordinatewise strictly increasing convex objective `F(E,L)=3E+L`, the operating-plus-supply cost on these two segments is respectively

`7+2E >=7`, and `5+2E >=7`.

Their endpoints `(E,L,c)=(0,3,4)` and `(1,2,2)` both attain7. Because this objective is linear in joint coordinates, the same inequality holds throughout their complete convex hull. Thus the exact physical and hull planning values are both7.

## What the proposed relaxation adds

Interpolate `r(m)=m/2` on0<=m<=1 and put N=2−m. Its proposed lower endpoint becomes

`t(m)=max{3m/2−1/2, 2m−2, 0, m/2}`.

At m=1/2 this is1/4. The proposed terminal epigraph is

`L >= max{3−E, 3+m−2E}`.

Consequently the relaxation admits

`m=1/2`, `E=1/4`, `L=3`, `c=3`.

It respects t(m)<=E<=U, the least-terminal formula, and L<=H, yet its total objective is `3+3/4+3=27/4<7`. Thus it improves strictly on the true convexified planning value. In fact27/4 is the relaxed optimum: the objective increases with E on each terminal piece; at its lower endpoint t(m), it is7−m/2 for0<=m<=1/2 and13/2+m/2 for1/2<=m<=1.

The failure is not caused by an empty integer branch, insufficient graph completeness, irrational data, negative prices, or a merely dominated point. A strictly increasing linear functional separates the added point from the true hull's coordinatewise upper closure. Therefore it also refutes equality for monotone-objective purposes.

It is not dependent on zero curvature either. For `F(E,L)=3E+L+(E^2+L^2)/100`, the true hull cost is at least7, while the same relaxed point has cost `27/4+145/1600<7`. This objective has positive definite Hessian and positive coordinate derivatives on the admitted nonnegative load domain.

## Why convexity of r_m does not make this exact

At fixed fractional m=1/2, any actual mixture has equal total weights on the m=0 and m=1 branches. Since their minimum early loads are0 and1, its early load must be at least1/2. More generally the true hull in this example requires `E>=m`. The proposed nonlinear threshold instead permits `E=1/4` at that fractional cardinality. It evaluates the maximum of affine physical restrictions AFTER averaging the cardinality data, whereas actual mixtures average complete feasible schedules. A maximum can lie strictly below the chord joining its integer samples.

This shortcut is nevertheless a valid outer relaxation in the joint coordinates when f>0 identifies m from cost. Linear interpolation of convex r_m is convex; every threshold component is a nonnegative multiple of that interpolation plus an affine term. Hence t(m) is convex. The proposed terminal lower function is also convex in(m,E), its epigraph intersected with L<=H is convex, and the remaining domain restrictions are convex. This set contains each integer frontier segment, therefore contains their convex hull. Convexity establishes the relaxation direction, not reverse inclusion or attainability.

For f=0 the cost coordinate no longer identifies m, but that does not rescue the universal assertion: the positive-fee counterexample already satisfies the theorem's hypotheses. Exactness in a special case would need a constructive decomposition of every fractional feasible point into actual integer-cardinality segments, or a separate complete facet proof. Discrete convexity of r_m alone is insufficient.

The existing finite endpoint/kink hull construction remains exact. A general exact extended formulation may keep mixture weights per generating record, or use disaggregated perspective copies of each nonempty cardinality's affine pieces. That is an ordinary finite-hull formulation; it is not the proposed single continuously interpolated matching-cardinality description.
