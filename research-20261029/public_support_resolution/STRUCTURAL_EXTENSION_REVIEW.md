# Heterogeneous two-batch extension: adversarial mathematical review

29 October 2026. Source-only review of `STRUCTURAL_EXTENSION_CANDIDATE.md`. All arithmetic below is direct hand algebra on the displayed rational construction. No module import, test, numerical run, source hash or actual timetable data was used.

## Conclusion

**Scoped mathematical PASS for the stated f>0, zero-travel, two-batch class.** I found no counterexample to the physical projection, matching convexity, lower-hull construction or positive-gap criterion under those assumptions. The n=2 rational example and regret arithmetic agree by hand. This is a materially more useful structural extension than preservation under dominated movements, but it is not a general EVSP theorem or a novelty clearance.

Before integration, make the total resource powers explicit and keep the strictly positive fee assumption attached to the gap criterion. A zero-fee extension of that criterion would be false. The theorem remains unimplemented/unqualified by independent execution; this review supplies proof criticism, not a numerical pass.

## 1. Physical projection

For each A_i bus, early purchase x_i is bounded by battery headroom a_i and the individual10kWh early limit, hence 0≤x_i≤u_i=min(a_i,10). If paired to B_j, the nonnegative inventory after B imposes x_i≥max(0,a_i+b_j−20). The assumptions b_j≤20 and a_i+b_j≤30 imply this lower bound is at most both a_i and10. Thus every matching is feasible at its lower endpoint and admits all intermediate sums through independent interval choices.

There are exactly n buses that perform an A service, irrespective of matching cardinality. Give each its own early10kW connector for the full one-hour window. This realizes every individual x_i simultaneously. **State aggregate early grid power≥10n kW explicitly:** n physical connectors alone does not guarantee this if an additional smaller shared-grid ceiling is allowed. Similarly terminal power must permit all n30kW connectors simultaneously, or the group proof must be revised. The declared intention is the original scaled-resource policy, so this is clarification rather than a discovered contradiction.

Terminal connector feasibility is stronger than the candidate's loose paired bound suggests. A paired bus needs a_i+b_j−x_i≤20kWh by its feasibility lower bound; it therefore fits alone on one30kW connector. Each unmatched A consumes a_i−x_i terminal kWh; each unmatched B consumes b_j. There are equally many unmatched As and Bs. Pair them arbitrarily for terminal resource allocation: every such sum is≤a_i+b_j≤30. Serially replenish them on one connector. Exactly m+(n−m)=n connector groups suffice, and all buses are present at the depot at terminal opening3. Their individual demands are≤20, matching battery capacity. No aggregate-inventory shortcut is used.

The model exhausts the assignment possibilities because positive-duration simultaneous A services preclude two As on one bus, and likewise for Bs. Every bus covers one A, one B or both, and unused buses need not enter cost/energy. Unmatched B buses cannot accept useful early energy because they start full and have no previous consumption. Full refill gives total grid purchase S for every plan.

For fixed m the matching intervals all share upper endpoint U. Their union is exactly [r_m,U], with the minimum attained since there are finitely many matchings. This argument would fail if different pairings introduced travel energy, unavailable crosslinks or different early windows; the theorem properly excludes those changes.

## 2. Matching thresholds and hull

Nonnegative edge costs give r_m≥r_(m−1): delete an edge from an optimal m-matching and compare with the optimum of size m−1. The convex-value argument is valid: fixed-cardinality bipartite matching is an integral unit-capacity min-cost flow at integer cardinalities, while its continuous RHS value function is convex by LP duality. Therefore 2r_m≤r_(m−1)+r_(m+1). Do not claim the same sequence property for arbitrary nonbipartite/resource-coupled assignment problems without proof.

Zero increments form an initial block because increments are nonnegative and nondecreasing. Taking m0 as the last zero threshold therefore eliminates all repeated-threshold ambiguity; subsequent d_j are strictly positive. Since f>0, earlier zero-threshold branches are strictly more expensive and may be ignored only for the lower frontier, not erased from physical response reporting.

The interpolant slopes −f/d_j are nondecreasing and its last slope0 is no smaller. Each interpolant segment is a convex combination of physical endpoints. Every physical point lies on or above this convex graph, including branches with smaller m. Consequently it is precisely the lower operating-cost boundary of the whole-plan hull. Collinear adjacent segments cause no problem: an intermediate r_m remains a physically attained threshold, so the gap criterion must use intervals between adjacent thresholds as written, not the relative interior of a merged maximal face.

## 3. Support criterion and zero-fee caveat

The supply derivative is g'(E)=2(E−E0)/(5n), with E0=(S−20n)/2. Strict convexity gives a unique hull minimizing E*. A threshold or final-horizontal point has a physical plan attaining the boundary. Inside an adjacent positive-length interval, f>0 makes the interpolated cost strictly below the cheapest physical step. No other load can attain the hull objective, and compactness turns nonattainment at E* into a strictly positive minimum gap. The intermediate-threshold subgradient condition has the correct order:

    f/d_(m+1) ≤ g'(r_m) ≤ f/d_m.

The minimizer formulas follow by setting derivative zero on each affine segment and clamping to its endpoints. If m0=n, the entire economically relevant frontier is physical and flat; gap0 follows.

**Do not extend the strict-interior iff positive-gap statement to f=0.** For example n=1,a=b=15 has thresholds0,10 and E0=5. At f=0 the physical two-bus branch realizes every E∈[0,10] at the same operating cost0, so D=CH even though E*=5 lies strictly inside the threshold interval. If zero fee is included later, handle it separately: the zero-matching branch has cost0 across [0,U], so the gap is always0. The present f>0 hypothesis avoids this counterexample.

## 4. Exact n=2 example: hand check

For A=(5,15), B=(14,15), the recharge matrix is [[0,0],[9,10]]. Thus r0=r1=0,r2=9,S=49,U=15 and m0=1. The g polynomial is

    2401/20 − (9/10)E + E²/10.

The m2 minimum occurs at E9 and gives14+2401/20=2681/20. The m1 minimum at E9/2 gives5561/40, which is larger; m0 is larger by7 at the same best load. The hull edge objective is

    2821/20 − (151/90)E + E²/10,

with minimizer151/18. Completing the square gives CH=434201/3240. Converting D to the same denominator gives434322/3240, hence gap121/3240. The hull weights11/162 and151/162 produce the stated early load and operating interpolation.

At E9, p=(49/10,4). The m2 bill plus fee is2181/10. Its best old m1 zero-early alternative is21+4×49=217, and m0 is dearer. Every m2 alternative has E≥9 and the positive price difference penalizes higher E. Therefore own-price regret11/10 is the full-set response difference, not just a selected alternative's gain.

The endpoint witnesses fit the terminal groups: at E0 the paired19 and two separate15 demands use one connector plus one serially shared connector; at E9 both paired buses need20 terminally. All start and finish at20. These witnesses use the same resources and full refill.

## 5. Ownership and claim discipline

The heterogeneous ownership caveat is essential and correct. Fixed pairs (A5,B14),(A15,B15) need total early10 for full pairing, whereas crossed pairs need9. Identical-copy relabeling cannot implement the efficient heterogeneous outcome under those fixed rights. No20/n individual-regret conclusion or sum-of-individual-regrets identity follows automatically.

Integrate this as a theorem about exhaustive heterogeneous complete crossmatching and its projected frontier, explicitly attributing standard matching convexity and support machinery. It addresses a substantive assignment class; it does not cover the public varied-time one-connector case, realistic deadheads or operational prevalence. The next independent exact qualification should reconstruct raw SOC/connector feasibility rather than merely compare formulas copied from this reduction.
