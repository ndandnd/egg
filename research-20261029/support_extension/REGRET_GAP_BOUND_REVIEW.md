# Independent analytical review: planning gap versus own-price regret

Reviewed REGRET_GAP_BOUND_CANDIDATE.md and the current ownership calculation. No data, numerical tools, imports, execution, hashes, native work, new cases or paper edits were used.

**Main quantitative bound and Bregman argument PASS. One optional-identity qualification should be made explicit before integration.** This is classical convex analysis, not a new generic aggregation theorem.

## Main proof and edge cases

First-order optimality of c+F(u) on the convex hull gives the supporting linear functional c+q·u with value c*+q·u*. Since linear minimization over the original compact projected set and its hull agrees, equation (1) is exact. The Bregman term is nonnegative, and its subtraction from Δ is a nonnegative fixed-q regret. Strong convexity therefore gives the stated distance estimate without any assumption that intrinsic cost is convex or uniquely determined by load.

The inequality V(p)≥V(q)+min_v(p−q)·v has the correct direction. Combining it with (1), then applying the support-function/diameter bound and tangential gradient Lipschitz bound, yields exactly the displayed upper estimate. The lower estimate follows from the own-load tangent bound. No monotonicity or nonnegative tariffs are needed for these mathematical regret inequalities over the unchanged complete-plan set.

The planner-optimum restriction is essential. If a higher-cost plan shares a cheaper plan's load, its regret can be positive even when planner gap is zero; replacing Δ by that plan's excess ε is the appropriate generalization. Singleton loads, zero gap, tied physical optima and tied hull representations behave as stated. Zero curvature does not permit the distance division; affine supply is separately benign. Nonsmooth supply does not provide a Lipschitz bound for arbitrarily chosen subgradients. None of these statements supplies admissibility of a tariff under additional economic restrictions.

## Relative gradients versus the optional Fenchel identity

The main proof is invariant to normal gradient components because all feasible load differences are tangent to the load affine hull. Equation (4), however, uses the conjugate of a specified global F and needs **p to be an actual global subgradient of that F at u**. An arbitrary tangential projection/normal representative is not interchangeable inside F*.

Exact counterexample to an unqualified reading of (4): take loads (t,1), 0≤t≤1, all intrinsic costs zero, and global F(x,y)=x²+y². The physical set is already convex, D=CH=1, and its planner load is (0,1). The relative/tangential gradient is p=(0,0), giving regret zero. But the original global conjugate has F*(0)=0 and V(0)=0, so the right-hand side of (4) would be 1. Using the actual ambient gradient (0,2), or the conjugate of F restricted to the affine load hull and extended by +∞, restores the identity.

The candidate already introduces (4) as an optional global-domain interpretation, so the needed repair is a precise sentence rather than a change to the main bound: “For this identity use an ambient representative p∈∂F(u) of the specified proper closed global F; alternatively use the conjugate of its affine-hull restriction. Regret and the preceding tangent-space bounds are unchanged by normal components, but F* is not.” A proper closed global domain alone does not supply that representative if p was defined only relatively.

## Replication scaling

The two-coordinate Hessian is (1/(5n)) times the identity, so both strong-convexity and gradient-Lipschitz constants on the feasible line are 1/(5n). Early load spans [0,10n], with late load 30n−E; its Euclidean diameter is 10√2 n. Substituting the declared Δ_n=20δ²/n gives the stated 40|δ| correction. Physical optimum points lie on the hull's operating-cost edge, so their fixed-q score gap is zero and B_F=Δ_n. Retaining that cancellation gives r_n≤40|δ|, consistent with both exact ownership branches and their ties.

Thus vanishing Δ forces vanishing regret on a family with uniform positive curvature, bounded smoothness and bounded diameter; the replication family deliberately does not have those uniform constants. There is no contradiction or claim that the bound identifies the exact regret. The participant remains the complete-fleet owner, not an individual bus or an unspecified shared-charger institution.

## Integration recommendation

A short explanatory proposition beside ownership is justified after the optional global-conjugate clarification. Retain the physical-planner condition, one fixed norm, tangential constants and tariff admissibility caveat. State the scaling explicitly so the result explains rather than obscures the nonvanishing whole-owner example. No new numerical qualification or ML claim follows.
