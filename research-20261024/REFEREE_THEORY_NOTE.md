# Bounded mathematical referee note

This note uses only the supplied finite-schedule formulation. It does not establish any empirical property of EGG or any particular implementation. The facts below are standard finite optimization and convex analysis, not novelty claims.

## Model and conventions

Let X be a nonempty finite set of feasible, complete schedules. Schedule x has intrinsic cost c_x in R and load L_x in R^d. Given price p in R^d, let

    C_x(p) = c_x + p^T L_x,
    T(p) in argmin_{x in X} C_x(p),
    p_x = a + B L_x.

T is a specified deterministic tie-breaking selection. The update is

    F_alpha(p) = (1-alpha)p + alpha p_{T(p)},   0 < alpha <= 1.

B need not be symmetric for the fixed-point and two-cycle identities below. The convex optimization statement later assumes symmetric positive semidefinite B. A strict best response means a unique minimizer over all of X. Alpha = 0 is excluded: then every price is mechanically fixed, irrespective of consistency.

## Exact pure fixed-point criterion

A schedule x and its consistent price p_x form a pure fixed point if and only if

    c_z - c_x + p_x^T(L_z-L_x) >= 0   for every z in X,

and T(p_x) = x. If all displayed inequalities are strict for z != x, tie-breaking is immaterial. For any alpha > 0 these are exactly the fixed points of the damped update: F_alpha(p) = p implies p = a + B L_{T(p)}, and the converse is immediate.

The inequalities alone certify membership in the best-response set; with ties, they do not certify that a particular deterministic selection chooses x. Distinct schedules may have identical consistent prices, so existence of a fixed price should not be confused with selection of every schedule having that price.

## Exact strict two-schedule cycle, without damping

Take distinct schedules x,y, write

    delta = L_y-L_x,
    g = c_y-c_x + p_x^T delta,
    Q = delta^T B delta.

The undamped map has the strict cycle p_x -> p_y -> p_x, with y then x as unique global best responses, if and only if p_x != p_y and

    C_y(p_x) < C_z(p_x)   for all z != y,
    C_x(p_y) < C_z(p_y)   for all z != x.

These are the full, global conditions. Their x-versus-y portions reduce exactly to

    -Q < g < 0.

Proof: C_y(p_x)-C_x(p_x) = g, whereas
C_y(p_y)-C_x(p_y) = g + delta^T B delta = g+Q.
Thus y strictly beats x at p_x and x strictly beats y at p_y exactly when g < 0 < g+Q. This also forces Q > 0 and hence p_x != p_y. If X = {x,y}, this scalar interval is necessary and sufficient for the strict cycle. If there are other schedules, their global comparisons above remain necessary; pairwise comparisons or adjacency in a schedule hull do not suffice.

Equivalently, defining

    h = c_y-c_x + [a + B(L_x+L_y)/2]^T delta,

one has h = g+Q/2, so the two-schedule criterion is |h| < Q/2. Boundary equalities are ties and require the specified T; they are not strict cycles.

Dimensional check: p has units cost/load, B has units cost/load^2, and g and Q both have units cost. For scalar B=bI, Q=b||delta||^2. The expression b||delta|| has units price, so comparing it directly with an objective-cost margin is generally dimensionally wrong. A price-distance margin can be used only after defining that distance and its relation to the objective differences precisely. A reference to a margin between adjacent vertices is not an exact theorem without those definitions and the global best-response checks.

## Damping does not imply a long-period orbit

Here is a strict counterexample for every 0 < alpha <= 1. There are two schedules:

    L_x = 0, c_x = 1/2;
    L_y = 1, c_y = 0;
    a = 0, B = 1.

The unique best response is y when p < 1/2 and x when p > 1/2. Consequently

    F_alpha(p) = (1-alpha)p + alpha,   p < 1/2;
    F_alpha(p) = (1-alpha)p,           p > 1/2.

Put r=1-alpha and define

    p_low = r/(1+r),   p_high = 1/(1+r).

For every alpha > 0, p_low < 1/2 < p_high, and direct substitution gives

    F_alpha(p_low) = p_high,
    F_alpha(p_high) = p_low.

Thus the damped system still has a strict period-two orbit, however small the positive damping parameter. Both intrinsic costs are nonnegative. The undamped pair satisfies g=-1/2 and Q=1, strictly inside the exact cycle interval. For 0 < alpha < 1 the two-step map has slope r^2 < 1 in a neighborhood that follows these two strict branches, so this cycle is locally attracting. At alpha=1 the two prices are 0 and 1.

This refutes a universal conclusion that damping of an undamped strict two-cycle produces a long-period orbit. It does not rule out longer periods in other examples. Any claimed longer period requires additional hypotheses and a proof about the specified map, step size, tie-breaking, and initial-condition regime.

## Finite mixtures, menus, and indivisibility

Caratheodory's theorem says that any load in conv{L_x:x in X} can be represented using at most d+1 schedules. For an arbitrary mixture whose expected cost must also be preserved, apply it to (L_x,c_x) in R^(d+1), obtaining at most d+2 schedules. The bound depends on dimension; it is not a guarantee for any chosen top-K menu.

For clarity, if B is symmetric positive semidefinite, the convexified problem is

    minimize over w_x >= 0, sum_x w_x=1:
        sum_x w_x c_x + a^T Lbar + (1/2)Lbar^T B Lbar,
    where Lbar = sum_x w_x L_x.

A minimizer exists. Its first-order optimality conditions say that every positive-weight schedule minimizes c_x+p^T L_x globally at p=a+B Lbar. Conversely, those support and consistency conditions imply optimality by convexity. This is a convexified equilibrium. At that price the supporting schedules satisfy c_x+p^T L_x=m for a common m; therefore compressing their load mixture to at most d+1 supporting schedules also preserves its expected intrinsic cost. These statements are standard and do not require a new theorem.

A convexified equilibrium is not automatically an implementable pure equilibrium of indivisible schedules. In the damping counterexample the convexified optimum mixes x and y equally, yielding Lbar=p=1/2, whereas neither pure schedule is a fixed point. Sampling a supporting schedule implements its realized load, not the average load used to set that price. An interpretation in expected loads or randomized allocations must be stated explicitly.

A top-K or column-generation menu closes a relevant convexified gap only with appropriate evidence: its columns must be feasible original schedules; its restricted solution must have a global optimality certificate against omitted schedules (for example an exact pricing oracle reporting no improving column); and its asserted support bound must use the correct dimension and preserved quantities. Merely retaining K high-ranked or adjacent schedules does not establish those properties. Caratheodory guarantees an existential support after the target point is known; it does not show that a particular generation or truncation rule finds that support.

If columns are partial or local schedules, the claimed support additionally needs a feasible lift to complete joint schedules that respects all coupling constraints. An indivisible pure implementation needs a feasible complete schedule x with the required realized load and x=T(a+B L_x), or an explicit integral allocation of the actual agents satisfying their equilibrium conditions. A fractional decomposition or bounded support by itself supplies neither integrality nor this lift. Any approximate gap claim should name its objective, tolerance, oracle guarantees, and implementation notion.

## Safe scope for a revised claim

The exact two-schedule result can be stated as the interval -delta^T B delta < g < 0, with global dominance conditions when X has more than two schedules. The damping behavior can be reported as an observed or separately proved property of the particular instance family. A bounded-menu statement can concern representation or certified convexified optimality under its stated assumptions; pure implementability requires a separate argument. None of these elementary criteria alone proves a broad dynamic or menu-closure theorem for EGG.

## Same-total-energy two-hour variant and complete-menu gap

Take X={x,y}, L_x=(1,0), L_y=(0,1), c_x=c_y=0, a=0, and B=I. Both schedules use total energy one. The social objective above is J(L)=(1/2)||L||^2. Each pure schedule has J=1/2, while the half mixture has load (1/2,1/2) and J=1/4, the convexified minimum. Thus the integrality gap is 1/4 even when the menu contains every feasible schedule. The complete two-column menu closes its menu approximation gap but leaves this physical convexification gap unchanged.

For r=1-alpha, the two prices

    (1/(1+r), r/(1+r)) and (r/(1+r), 1/(1+r))

are exchanged by F_alpha. At each price, the unique best response loads the cheaper hour. These comparisons are strict for every 0<alpha<=1, so this equal-energy example also retains a strict period-two orbit under every positive damping step. As before, its two-step slope is r^2 on the strict response branches.

## Effective price dimension

Fix a reference schedule x_0 and put S=span{L_x-L_{x_0}:x in X}. Then

    C_x(p)-C_{x_0}(p) = c_x-c_{x_0} + (P_S p)^T(L_x-L_{x_0}),

where P_S is the orthogonal projection onto S. Hence the entire best-response set depends on price only through P_S p, and dim(S)<=min(d,|X|-1). The selected response has the same property under a fixed-priority tie-breaking rule; an arbitrary rule that inspects discarded price coordinates need not. Under such a projection-compatible selection, projecting the price update gives a closed response-driving system on S. Adding nominal time coordinates that are redundant linear combinations of existing load coordinates does not increase this rank. Therefore increasing nominal horizon or price-vector size alone guarantees neither greater active price dimension nor a computational speedup. These are elementary linear-algebra facts, not novelty claims.
