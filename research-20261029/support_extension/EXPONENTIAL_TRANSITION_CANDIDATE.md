# Exponentially many efficient physical transition branches

Analytical source-only check; no numerical run, data, imports, tests, hashes or paper edits. **The corrected construction works:** it has2^k distinct efficient physical branches at ONE matching cardinality. It does not establish exponentially many hull vertices, distinct linear-price regimes, hardness, or an unavoidable exponential symbolic representation.

## Exact model and capacity correction

Let k>=1, w_i=2^i for i=0,...,k−1, W=Σ_i w_i and common battery capacity B>=20 max_i w_i (e.g. equality). There are2k simultaneous A services and2k simultaneous B services. In block i, both batches have energies

    (B/2+3w_i, w_i).

The allowed graph is the disjoint union of k complete2×2 blocks. In each block, identity edges have compulsory transition energy0 and cross edges6w_i. No interblock edge, alternate route, removable transition task, V2G or other charging is allowed. Tasks occupy a common positive-duration noncharging interval. For example A[0,1], early[1,2], task[2,3], B[3,4], terminal[4,5]. All buses start/end full, reserve0, unit efficiency, nonnegative consumption and no other draw or switching time.

Cap the total fleet at2k and charge any common fixed fee f>=0. Since each batch has2k simultaneous services, exactly2k buses are necessary; every bus must serve one A and one B. Singletons or idle buses cannot occur under that cap. Thus every feasible fleet chooses a perfect matching in each allowed block, and each block has exactly the two identity/cross possibilities.

**B>=10 max w is insufficient.** For a cross edge, the total A+transition+B demand is B/2+10w_i; making its early requirement zero needs B>=20w_i. This stronger condition also guarantees b_j+transition<=B, individual service feasibility and all paired boxes being nonempty. A separate post-early feasibility condition alone would only require B>=18w_i and would not justify the claimed zero cross requirement.

Use one early connector with grid-energy budget/power

    K=Σ A=kB/2+4W,

and one terminal connector with H=S_max=kB+20W. Every bus accepts the corresponding power. These are finite resources within each instance; their magnitudes grow with this family, so this is not an assertion of unlimited throughput at one uniformly bounded power.

## Complete fixed-matching projection

Identity in block i has minimum early purchase6w_i: the big/big edge requires6w_i and the small/small edge0. Its total consumption is S_i=B+8w_i. Cross matching has minimum early purchase0 and total consumption S_i+12w_i. Let I be the identity blocks and

    R=6Σ_{i in I}w_i,     S=S_max−2R.

All early headrooms sum to K independently of matching. Charge-only interval allocation therefore gives the ENTIRE branch

    (E,L,c)=(E,S_max−2R−E,2kf),     R<=E<=K.

The interval is nonempty: in every block6w_i<=B/2+4w_i, so R<=K. All terminal needs are nonnegative and total at most H. Every early allocation can be serialized on the shared early connector, and every full terminal refill on the terminal connector; each bus's valid endpoint SOC and nonnegative task/service consumption preserve intermediate inventory. No extra early charge outside this interval or terminal inventory credit is available. Consequently the union over the2^k perfect matchings is the complete physical projection under the declared model.

Binary subset sums are distinct. Hence there are exactly2^k values R, namely6t for integer0<=t<=W. Their corners are

    z_R=(R,S_max−3R,2kf).

No corner is dominated by another physical point. Indeed any point from a branch indexed by R' with E<=R satisfies R'<=E and

    L=S_max−2R'−E >= S_max−3E >= S_max−3R.

Equality in both coordinates forces E=R'=R. Fixed fleet cost is identical. More strongly, if R_next is the next value, each branch contributes the nonempty efficient portion R<=E<R_next; the final branch contributes R_max<=E<=K. Earlier branches have larger terminal load at the same or smaller E; later branches require greater E. At E=R_next the preceding branch is dominated by the new corner. Thus the claim concerns2^k actual efficient pieces, not merely2^k syntactic matchings with identical projections.

## Every corner is a unique convex-planner optimum

Fix a corner R* and choose epsilon=1/(2 max{K,1}). On E,L>=0 define

    F_R*(E,L)=3E+L+epsilon(E−R*)².

This is convex. Its E derivative is at least3−2epsilon R*>=2, and its L derivative is1, so it is strictly increasing in each coordinate throughout the nonnegative domain. On branch R,

    F_R*(E,L)=S_max+2(E−R)+epsilon(E−R*)² >= S_max.

Equality holds only at E=R=R*. Hence z_R* is the unique optimum in the PROJECTED load/cost coordinates for this monotone convex objective. Literal schedules with the same loads can still have allocation/order symmetries, so “unique fleet schedule” would overclaim. If joint strict convexity is desired, add a sufficiently small positive term eta(L−L*)² with eta<=1/(4 max{S_max,1}); the same lower-bound argument and positive derivatives remain valid.

## Limits of the consequence

All corners lie on the same line L=S_max−3E. Their common supporting posted price is(3,1), at which they all tie. Therefore this example does NOT show2^k distinct linear-price regions or2^k hull vertices. Its hull lower boundary can collapse the collinear corners to one edge, followed by the final physical segment. The quadratic supply term selects a unique point on that edge; it is not a claim that different prices uniquely expose all corners.

Weights and B have exponentially growing numerical magnitude. With ordinary explicit binary encoding the input has polynomial size in k (indeed order k² for the repeated service-energy numbers), whereas explicit physical-branch enumeration has2^k pieces. This establishes no polynomial bound on that output count in binary input length, but not2^{Omega(input bits)}, a strong-hardness result or a magnitude-independent obstruction. The integer parameter R=6t,0<=t<=W also provides a compact SYMBOLIC description; exponential branch count does not exclude such compression or easy optimization for this special family.

The valid boundary message is narrow: arbitrary edge-dependent compulsory transition energy can require many efficient load/total-energy branches even at one fixed fleet count, so keeping only one minimum-requirement matching per cardinality is not generally sufficient. The ingredients are familiar independent-choice/multiobjective constructions with an explicit feasible bus realization; no generic Pareto-complexity or multiobjective novelty claim is made.
