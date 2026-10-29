# Candidate: exact efficient load–cost projection with common losses

Source-only independent derivation after reading the current lossless V2G section and V2G_LOSSES_ASSESSMENT/REVIEW. No numerical cases, execution, imports, tests, literature expansion or paper edits. This needs independent proof review before integration. It is an efficient-frontier theorem, NOT equality of the complete physical projection or the old lossless threshold/support classification.

## Model and notation

Keep the same two batches, fixed allowed bipartite graph, singleton options, capacity B, full initial/final inventory, zero reserve/travel/auxiliary/switching time, common early availability of ALL service-assigned buses, one early connector and one terminal charging-only connector. Every bus accepts the connector's grid-side power; K,H denote grid energy deliverable over their unit windows. Early charging/discharging magnitudes share power K, so gross GRID throughput C+D<=K. Use common constant charging efficiency 0<eta_c<=1 in both windows and discharging efficiency0<eta_d<=1. Same posted rate settles signed net exports. Initially allow no idle buses; an optional efficient-value corollary is below. Used-bus cost is fN, f>0. Supply must be defined on admitted signed loads.

Write alpha=eta_c, delta=eta_d, kappa=1/(alpha*delta)−1>=0, P=sum A, S=sum A+sum B. A fixed matching M of size m uses N=2n−m buses. Its battery-coordinate early exchanges x_v have exactly the old boxes:

    paired: [a_i+b_j−B,a_i]; A-only:[a_i−B,a_i]; B-only:[b_j−B,0].

Put R=sum_M[a_i+b_j−B]+ and T=S−NB. The sum of positive lower endpoints is R, the sum of all lower endpoints T, the sum of upper endpoints P. Negative battery headroom has total R−T. Set r_m=min size-m allowedmatching R, for m=0,…,nu. These are the SAME classical matching values as in the lossless theorem.

## Fixed-matching efficient curve

For early GRID net energy E define

    d_R(E)=[R/alpha−E]+,
    L_R(E)=S/alpha−E+kappa*d_R(E),
    e_min(R,N)=(1/alpha−delta)*R+delta*(S−NB),
    U=min(P/alpha,K).

Define the exact lower threshold

    t(R,N)=max{
        e_min(R,N),
        2R/alpha−K,
        S/alpha−H,
        [S/alpha+kappa*R/alpha−H]/(1+kappa)
    }.

**Lemma.** Among cycle-free allocations for this matching, the feasible net-early projection is exactly[t(R,N),U], when nonempty. At each such E, L_R(E) is the minimum feasible terminal grid load. A physical allocation attains it, with C=E+d_R(E), D=d_R(E). Every other cycle-free allocation at that E has terminal load at least L_R(E). Thus the displayed piecewise-affine curve is its complete coordinatewise efficient load frontier at this fixed vehicle cost.

**Proof.** Cycle-free purchases/exports obey C_v=(x_v)+/alpha and D_v=delta*(−x_v)+. Mandatory positive coordinates give C>=R/alpha, hence D=C−E>=[R/alpha−E]+. Total accounting gives L=S/alpha−E+kappa*D, so L>=L_R(E).

If E>=R/alpha, choose no negative x and distribute alpha*E positive battery exchange through the independent intervals, whose attainable positive totals fill[R,P]. This attains D0,C=E for R/alpha<=E<=P/alpha.

If E<R/alpha, fix mandatory positive x at their lower bounds, set all other positive exchanges zero and distribute negative battery amount(R/alpha−E)/delta among the negative intervals. This is possible exactly when this amount<=R−T, equivalently E>=e_min(R,N). It attains C=R/alpha,D=R/alpha−E. Since T<=R, the lower regime joins the upper one without a gap.

Necessity of the raw lower E endpoint also follows for an arbitrary cycle-free allocation: C>=R/alpha while D<=delta*(R−T). Its raw upper endpoint is E<=C<=P/alpha. On the minimizing construction gross throughput is E+2d_R(E)=max(E,2R/alpha−E); therefore the gross constraint is equivalent to E<=K and E>=2R/alpha−K. Any other allocation at E has at least this gross throughput and cannot rescue an excluded E. Every terminal bus refill is nonnegative and at most B/alpha grid units. The common-window connector serializes all early actions if C+D<=K and all terminal refills if L<=H. At zero power use zero required energy without division.

Finally L_R(E)=max(S/alpha−E,S/alpha+kappa*R/alpha−(1+kappa)*E). Both affine pieces must be<=H, yielding exactly the last two threshold terms. This proves necessity and attainment. L_R is strictly decreasing in E (slopes−1 and−(1+kappa)), so no distinct point on this fixed-cost curve coordinatewise dominates another. QED.

At strict round-trip loss kappa>0, larger D gives strictly larger L at fixed E. At kappa0, the same minimum curve remains attainable and all extra export at that E has the same terminal load; degeneracy does not invalidate the frontier statement.

## Matching and global efficient projection theorem

Let N_m=2n−m and

    t_m=t(r_m,N_m),    L_m(E)=L_{r_m}(E),    c_m=fN_m.

**Theorem (efficient reduction).** The union of physical curves

    Z= union over m=0,…,nu with t_m<=U
       {(E,L_m(E),c_m): t_m<=E<=U}

is a subset of the complete physical joint projection. Every cycle-free physical point is componentwise dominated (or matched) by a point of Z with the SAME E and operating cost, and no larger L. Consequently every coordinatewise nondominated cycle-free physical point belongs to Z, although some points of Z can be dominated across cardinalities. Pareto-pruning this explicit finite union gives the exact efficient frontier. It is not legitimate to claim all of Z is globally Pareto efficient without that pruning.

**Proof.** At a fixed cardinality, e_min(R,N),2R/alpha−K and the terminal second-piece threshold are nondecreasing in R, because1/alpha−delta>=0 and kappa>=0. The remaining threshold is independent of R. L_R(E) is also nondecreasing in R. Therefore a matching attaining r_m has a threshold no larger and an attainable terminal load no larger than any other size-m matching at any original feasible E. The lemma constructs the dominating point, with unchanged fee. All such minima exist in the finite allowed matching set. QED.

For completeness, t_m is nondecreasing and discretely convex: each threshold term is an affine nondecreasing transformation of the linearly interpolated convex r_m plus an affine nondecreasing inventory term, or a constant. Their maximum is convex and nondecreasing. Feasible cardinalities form an initial segment. The empty matching covers all cycle-free feasible early E; nevertheless cost and L together matter. This convexity statement ALONE does not establish the old cost-versus-E hull interpolation, because the curves for different m need not share the same L at a given E.

Each nonempty curve has at most two affine pieces, split at E=r_m/alpha if that point lies inside[t_m,U]. Thus Z is explicitly a finite union of line segments in(E,L,c), determined by thresholds, endpoints and at most one kink per cardinality. Its convex hull is the convex hull of those finitely many segment endpoints/kinks. This is a clear finite-dimensional convex planning reduction; it does not require enumerating service-specific sign patterns after r_m is known.

## Within-bus cycles and economic scope

For a general feasible early allocation, reducing C_v by epsilon and D_v by alpha*delta*epsilon preserves battery exchange while weakly reducing connector use and early net grid purchase, keeping terminal load and fee fixed. Common-window monotone reconstruction makes this replacement physically feasible. Iterating removes all within-bus cycles. Therefore every physical point, including cyclic ones, has a cycle-free point with weakly smaller E and the same L,c, then a point of Z with weakly smaller E,L and the same c. The exact Pareto frontier of the FULL physical set is consequently obtained by Pareto-pruning Z too. It is not the complete projection: dominated cycles add other loads.

For a supply objective nondecreasing separately in E and L over these signed loads, physical planning may be restricted to Z without changing value. The same holds for fixed posted nonnegative early and terminal prices. At zero prices dominated allocations may tie, so this is not a claim to enumerate EVERY price response. Negative prices or different settlement require retaining additional physical points. For convex coordinatewise nondecreasing F, hull planning may also use conv(Z): replace each component in any whole-plan mixture by its dominating Z point and apply monotonicity at the mean. Therefore D and CH reduce to Z and conv(Z) in this economic class. Standard support theory then applies, but a new universal scalar threshold-location criterion has NOT been proved.

This requires monotonicity on the signed domain or declared background loads; it cannot be presumed merely from convexity. Exact global support failure/success with a nonmonotone F cannot be inferred from this efficient reduction.

## Optional capped identical idle buses

With k identical paid idle buses and N=2n−m+k<=2n, deleting k allowed matching edges gives an all-assigned matching with the same N and fee, smaller R and identical T. Its threshold is no larger and L_R no larger at the same E. Thus capped paid idles cannot improve the coordinatewise frontier or monotone physical/hull values. Unlike losslessness, this only proves domination at equal cost, not equality of the literal joint projection: the replacement can have a strictly smaller terminal load. No uncapped claim follows when negative E is valuable.

## What this resolves and does not

The earlier counterexample remains valid: fixed E and vehicle cost can have different L. The new theorem does not contradict it; it identifies the least L and removes only dominated opportunities. Common losses require two load coordinates, but the efficient frontier still depends on cardinality matching values instead of exponentially many sign patterns. This is stronger than an accounting caveat while preserving the material limits: common efficiencies/windows, grid-side symmetric early power, ideal serial switching, no travel/extra service during windows, full replenishment, and monotone supply/price restrictions for optimal-value reduction. No empirical, practical-magnitude, new-literature novelty, numerical implementation or public37V2G claim is made.
