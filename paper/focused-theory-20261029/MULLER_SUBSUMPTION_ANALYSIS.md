# Technical subsumption comparison: Müller et al. and minimum-requirement replacement

**Decision: substantial aggregation and cost-disaggregation tools are already supplied by Müller et al.; direct subsumption of the assignment-replacement identity is not established. An extended formulation can represent our problem, but that representability does not prove the scalar reduction. This is not a novelty clearance.**

Scope: current related work, core theorem and complete common-loss proof, the earlier targeted prior-art note, and the primary [Müller, Szabó, Sundström and Lygeros author version, arXiv:1705.02815v1](https://arxiv.org/pdf/1705.02815v1), Sections IV–V, equations (10)–(17). No other literature or numerical evidence was inspected.

## Verified prior result and objects

Section IV defines aggregate feasibility as a Minkowski sum of supplied resource sets (10); common-generator zonotopes aggregate by adding centers and generator bounds (11). Section V formulates minimum-cost disaggregation for a prescribed aggregate trajectory (12)–(13). Its specialized construction uses generator-separable piecewise-linear convex costs (14), their constrained infimal convolution (15), and a separable aggregate cost (16). Equation (17) selects aggregate generator coordinates consistent with the requested trajectory. The resource population is supplied, but Section IV explicitly allows updating its aggregate when resources are added, removed or changed. Thus “fixed population” must not be read as an inability to handle different supplied populations. These results already establish cost-aware aggregation and optimal disaggregation under their stated representation assumptions. [Primary source, Sections IV–V](https://arxiv.org/pdf/1705.02815v1).

## Applying the machinery to one matching

Fix a matching M and its actual used duties. Our bus battery-exchange boxes are intervals [l_v,u_v]. In the lossless endpoint-exchange description, these intervals are one-dimensional zonotopes with a common generator. Their sum [sum l_v,sum u_v] is a direct elementary specialization of common-generator aggregation. A constant total fleet fee can be added without affecting disaggregation; common affine costs are also compatible with standard cost aggregation. The paper should concede this overlap explicitly.

The complete lossy model needs more than this net-increment interval. Keep bus totals C_v,X_v and q_v=alpha C_v−X_v/delta. A convenient fixed-duty relaxation is

    C_v>=0, X_v>=0, l_v<=q_v<=u_v.

The shared connector and terminal constraints are imposed on sums, not separately chosen independent bus budgets. These sets are generally not the bounded common-generator zonotopes assumed by the specialized construction. Allocating a fixed connector share to each bus before aggregation can exclude valid schedules; allowing every bus the full share before summing can admit invalid totals unless the shared constraint is restored. Generic product-space aggregation followed by those aggregate cuts remains entirely classical.

One still must show that feasible integrated totals correspond to finite serial actions within each battery. Our proof establishes this with one-direction exchanges and finite neutral cycles. An aggregate algebraic relaxation alone does not establish that physical realization. Müller et al.'s generic optimization formulation may be used once the correct resource sets and costs have been supplied; it does not remove the need to justify those sets for our action law.

## The exact bridge beyond a supplied matching

For matching M of cardinality m, define R(M)=sum_(i,j in M)[a_i+b_j−B]_+. Our claimed physical identity is

    P(M) = image{ C>=R(M)/alpha, X>=0, C+X<=K,
                  max(S−N_m B,S−alpha H)<=alpha C−X/delta<=P },

where the image retains E=C−X, L=(S−Q)/alpha and c=fN_m. The substantive replacement step is

    union_(|M|=m) P(M) = P(M_m),

for any M_m attaining the minimum r_m of R(M). It follows because every other parameter of these polygons is invariant at fixed m, while their only matching-dependent inequality weakens as R falls. Proving this requires identifying the positive lower-endpoint statistic, proving purchase/export allocation and cycle attainability, and showing that no further matching-dependent shared-resource condition survives. Standard minimum-cost matching then computes r_m. Neither adding centers/bounds for one supplied population nor optimizing its cost proves this cross-population containment identity.

A direct net-interval substitution also loses information: two lists of exchange intervals can have equal summed endpoints but different sums of positive lower endpoints. For example [1,2],[-1,0] and [0,1],[0,1] both sum to [0,2], but their mandatory positive sums are 1 and 0. Under losses and separate purchase/export budgets this distinction matters. This is an analytical warning about using only the net interval, not a counterexample to Müller et al.'s full framework or to arbitrary extended formulations.

## What an extended formulation can and cannot settle

Yes: enumerate matchings, retain their exact fixed-duty descriptions, then use a discrete union for physical planning and standard disjunctive convexification for its hull. Alternatively, duty-selection variables with service-cover constraints encode endogenous matching and fleet cost. These are ordinary classical formulations. Treating every possible duty as an independently selectable resource in a Minkowski sum without cover constraints would instead duplicate services or omit exclusivity. Adding those coupling constraints changes the independent-resource hypothesis; convexifying the resulting union changes physical feasibility unless integrality is retained.

Such formulations can reproduce the desired answer without our theorem, potentially at a larger representation size. They do not by themselves establish the existence of one dominating matching per cardinality or the five-halfspace reduction. Conversely, failure of a literal specialization is not evidence that another known theorem cannot derive that reduction. The precise remaining claim is this restricted physical replacement identity and its constructive realization, not cost aggregation, convex optimization, disaggregation, matching integrality or convex-hull pricing. Its originality and significance still require expert assessment against broader resource-allocation theory; this single comparison neither proves nor disproves them.
