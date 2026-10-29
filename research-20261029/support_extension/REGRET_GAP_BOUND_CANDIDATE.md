# Planning gap and own-price regret: a classical quantitative bound

Source-only bounded derivation using the framework and ownership sections. No numerical work, evidence/data reads, imports, hashes, native calls, agents or commits. No originality claim: this is an explanatory consequence of classical convex analysis.

## Statement and assumptions

Let S={(u(x),c(x)):x in X} be a nonempty compact projected complete-plan set, K its load projection, and H=conv(S). Intrinsic costs can be nonconvex and can differ between plans with the same load. Let F be convex and differentiable on a relative neighborhood of conv(K) in its affine hull A. Use one fixed Euclidean/Hilbert norm on the tangent space of A, and assume F is mu-strongly convex and has L-Lipschitz tangential gradient there, with0<mu<=L. Write diameter R=diam(K)=diam(conv(K)). No monotone-supply or nonnegative-price assumption is needed for this bound on the ORIGINAL complete-plan set.

Take ANY physical planner optimum z=(u,c), with c+F(u)=D. Let z*=(u*,c*) minimize c+F(u) on H. Strong convexity gives unique u*, and then its optimal c* is unique, although plans and mixture representations can tie. Put Delta=D−CH, p=grad F(u), q=grad F(u*). Normal components of gradients on a lower-dimensional affine hull add the same amount to every bill and do not affect regret; all differences/norms below can be taken in its tangent space.

Then the proposed bound is correct:

    Delta <= r(z;p)
          <= Delta + L*R*sqrt(2*Delta/mu).

The lower inequality is the framework's classical hull bound. The upper requires z to be a physical PLANNER optimum. For an arbitrary physical plan replace Delta everywhere by its excess epsilon=c+F(u)−CH; a large-cost plan at the same load is an immediate counterexample to using the planner gap for arbitrary plans.

## Exact Bregman identity and proof

Define B_F(u,u*)=F(u)−F(u*)−q·(u−u*). First-order optimality at the hull optimum gives

    c_y+q·u_y >= c*+q·u*  for every y in X,
    V(q)=c*+q·u*.

The equality follows because a linear functional has the same minimum on S and its convex hull. Thus the exact fixed-q score gap of the physical planner is

    c+q·u−V(q) = Delta−B_F(u,u*) >= 0.                 (1)

This is the sharper explanatory statement: some or all of the planning gap is the supply Bregman distance rather than an incentive gap at the hull price. Strong convexity immediately gives

    ||u−u*|| <= sqrt(2*Delta/mu).                       (2)

For d=p−q, compactness and the definition of V imply

    V(p) >= V(q)+min_{v in K} d·v.

Combining with(1) yields the useful directional bound

    r(z;p) <= Delta−B_F(u,u*) + max_{v in K} d·(u−v)
           <= Delta−B_F(u,u*) + R*||p−q||
           <= Delta−(mu/2)||u−u*||^2+L*R*||u−u*||.     (3)

Dropping the nonpositive Bregman term and applying(2) proves the advertised upper. A more geometry-sensitive result retains the support-function term in the first line of(3), or its actual load distance rather than replacing it by the worst-case square root. All maxima/minima exist by compactness. The proof does not identify a unique response or require unique operating cost at a load.

An exact alternative interpretation, when F is placed in the framework's proper closed convex global domain, is

    r(z;p)=Delta+[CH−(V(p)−F*(p))].                    (4)

Here p must be an actual global subgradient of the globally defined F, not an arbitrary representative of its tangential gradient. Alternatively use the conjugate of F restricted to the affine hull with consistent coordinates. Independent review supplies an exact counterexample to omitting this qualification. Under it, Fenchel equality holds at u. The bracket is the loss from using the planner's own price rather than an attained hull-dual price. Equation(4) is not a new duality theorem, and is not needed for the direct proof above.

## Degenerate cases and support qualifications

- Delta0 implies B_F0, u=u* and r0 for each physical planner optimum. This is consistent with the classical support criterion, provided the gradient tariff is admissible.
- If K is a singleton, R0, the planner merely minimizes operating cost, D=CH and r0. The zero-dimensional case can be handled directly; no artificial positive curvature assumption is necessary.
- Nonunique physical planner optima are all covered. Their loads lie in the ball(2), but may have different own prices and regrets. Nonunique convex-mixture representations of z* are irrelevant.
- If mu0, the displayed distance estimate is unavailable; do not divide by zero or claim this particular bound. For an affine supply objective the own price is constant and every physical planner is supported, so that separate case is benign.
- Differentiability and the selected marginal-price convention matter. With nonsmooth supply, an arbitrary chosen subgradient need not vary Lipschitzly, and this proof does not supply a bound uniform over all such choices. A further economic price restriction may exclude p or q even when the mathematical inequality remains valid. No tariff-reset equilibrium, individual-bus incentive or convergence result follows.

## Consistency with the replication calculation

In the paper's TWO-load Euclidean coordinates, F_n(E,L)=4E+(E^2+L^2)/(10n) has mu_n=L_n=1/(5n), while the feasible load line has diameter R_n=10*sqrt(2)*n. With Delta_n=20*delta^2/n, the displayed bound becomes

    r_n <= Delta_n+40*|delta|.

It allows bounded nonvanishing whole-owner regret while Delta_n tends to zero: the load diameter grows and curvature shrinks. This is not a fixed-(mu,L,R) family. In fact the replication planner points lie on the hull's operating-cost edge, so(1) has zero score gap at q and B_F=Delta_n. Keeping that term in(3) gives the sharper r_n<=40*|delta|, consistent with the exact two branches in ownership.tex. For a fixed model class with mu bounded away from0, L bounded and load diameter bounded, the bound DOES force planner own-price regret to vanish with Delta. The replication example does not contradict that quantitative statement.

## Recommendation

Useful as a short explanatory proposition beside the ownership result, with(1) and the explicit mu/L/diameter scaling. It corrects a possible reading that planning gap and incentive can be unrelated even on a uniformly bounded, uniformly curved family. It should be labelled a classical convex-analysis bound, not a new aggregation theorem. No experiment is needed for this conclusion.
