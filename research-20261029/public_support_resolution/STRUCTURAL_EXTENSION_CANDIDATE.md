# A structural extension beyond identical services and dominated movements

Status: analytical candidate with a complete proof below; not independently
implemented or numerically qualified. Source-only theoretical development
using the focused ownership/proof sections and the declared public-case scope.
No actual timetable data, backend, import, numerical run, hash or new agent
was used. The small rational example is a mathematical construction, not an
empirical case or a discovered favorable public instance.

## 1. What the existing replication already includes

The original aggregate construction has n simultaneous identical A copies
and n simultaneous identical B copies. A complete plan can pair ANY A copy
with ANY B copy. Every such matching with cardinality m has identical energy
projection [10m,10n] and cost14n-7m. Thus the reduction to m already covers
all cross-service matchings; it is not a restriction to prescribed A_i/B_i
duties. Labels add no non-dominated projected outcomes in that identical case.

The later reserved-pair ownership institution is different. Its fixed pairs
are an explicit ownership restriction, and the corrected paper reimplements
the same aggregate projected outcome with those pairs. That step is valid
because the copies are identical. It cannot silently be carried over to
heterogeneous copies.

The next theorem permits heterogeneous energies and complete crossmatching.
Its additions are not merely energy-wasting routes dominated by old plans:
which services are paired changes the minimum charge needed between batches.

## 2. A heterogeneous two-batch fleet class

There are n mandatory depot-to-depot services A_i in [0,1], with energy a_i,
and n mandatory services B_j in [2,3], with energy b_j. Assume

    0<a_i<=20, 0<b_j<=20, and a_i+b_j<=30 for every i,j.

Every A-to-B pairing is allowed. At most2n identical buses may be used; each
has capacity20, starts full, ends full by hour4, and has operating fee f>0.
There are n early connectors of10kW in [1,2] and n terminal connectors of
30kW in [3,4], with the corresponding per-bus acceptance limits. There is
no charging elsewhere, reserve, loss, auxiliary consumption, movement energy,
switching time or taper. These resources are the original replication
policy, with explicit sufficient terminal adequacy for all heterogeneous pairs.

No bus can serve two simultaneous A services or two simultaneous B services.
Consequently a complete fleet is exactly a partial bipartite matching M:
matched edges use one bus each; unmatched A and B services use separate buses.
This exhausts service assignments, up to vehicle labels. Define

    S=sum_i a_i+sum_j b_j,
    u_i=min(a_i,10), U=sum_i u_i,
    r_ij=max(0,a_i+b_j-20),
    r_m=min{sum_(i,j in M) r_ij : M a matching of size m}, r_0=0,
    c_m=f(2n-m), m=0,...,n.

The r_m optimization retains every crossmatching. It can be interpreted as
standard minimum-cost cardinality matching; neither that algorithm nor its
integrality is claimed as new here.

### Theorem 1: exact complete-fleet projection

For a particular matching M, every feasible load has total energy S and
early energy E in [R(M),U], where R(M)=sum_M r_ij. Every point in that
interval is physically realizable. Therefore the COMPLETE physical projection is

    union_(m=0)^n { (E,S-E,c_m): r_m<=E<=U }.

Proof. After A_i, its bus has inventory20-a_i. It can accept x_i in[0,u_i]
early. If paired with B_j, completing that service requires
x_i>=a_i+b_j-20, hence x_i>=r_ij. An unmatched A has lower bound zero;
an unmatched B starts full and cannot charge early. Each paired lower bound
is no greater than u_i: b_j<=20 gives r_ij<=a_i, and a_i+b_j<=30 gives
r_ij<=10. The sum of these independent closed intervals is exactly
[R(M),U], with n connectors available to the n A buses. SOC headroom and
nonnegativity follow directly from these bounds.

At the terminal, a paired bus needs a_i+b_j-x_i<=30 kWh and can take one
connector. Group each unmatched A with any unmatched B; their combined
terminal demand a_i-x_i+b_j<=30 can be served serially on one connector.
There are m paired groups and n-m unmatched groups, hence n connectors
suffice. Individual replenishment is physical and restores each bus to20.
Full replenishment gives total purchases S. All matchings of a fixed m have
the same operating cost and the same upper endpoint U. Their interval union
is therefore [min_M R(M),U]=[r_m,U]. This proves necessity and sufficiency.

This is more informative than total-energy dominance: all assignments have
the SAME total service energy, while their intermediate energy obligations
can differ. No physical alternative was removed to obtain the projection.

## 3. Exact hull geometry from cardinality matching

The sequence r_m is nondecreasing and discretely convex:

    0<=r_1-r_0<=r_2-r_1<=...<=r_n-r_(n-1).

To prove monotonicity, delete an edge from an optimal larger matching.
For convexity, express cardinality matching as unit-capacity bipartite
minimum-cost flow. Its linear relaxation is integral at each integer flow
value m, and its optimal value as a function of the flow requirement is
convex (the dual represents it as a supremum of affine functions of that
requirement). Thus its integer values satisfy
2r_m<=r_(m-1)+r_(m+1). This is standard flow/convex-value reasoning, not a
new general matching theorem.

Let m0 be the largest m with r_m=0. The points with m<m0 are projected-cost
dominated by m0; they remain physical alternatives. For j=m0+1,...,n put
d_j=r_j-r_(j-1)>0. Discrete convexity implies the d_j are nondecreasing.

### Theorem 2: complete hull and support criterion

The hull's lowest operating cost as a function of E is the piecewise affine
interpolant through

    (r_m,c_m), m=m0,...,n,

followed by the horizontal segment c_n for E in[r_n,U]. Its successive
slopes are -f/d_j, which are nondecreasing, followed by zero. Collinear
intermediate points may be retained without affecting the statement.

Proof. Each projected physical branch is horizontal from r_m to U, with
cost c_m. On [r_m,r_(m+1)), the cheapest physical branch is m, and the
proposed affine interpolant lies no higher than its cost. Nondecreasing
slopes make the interpolant convex. Its defining endpoints are physical,
so its graph belongs to the complete-plan hull. Conversely every physical
point is on or above this convex graph, so every convex combination is
also on or above it. This proves equality with the lower hull boundary.

Use the same scaled quadratic supply as the original replication:

    F_n(E,L)=4E+(E^2+L^2)/(10n),
    g(E)=F_n(E,S-E), E0=(S-20n)/2.

Then g'(E)=2(E-E0)/(5n). If E* is the unique minimizer of lower-hull
operating cost plus g(E), the physical-hull gap is zero exactly when

    E* in {r_m:m=m0,...,n} union [r_n,U].

It is strictly positive exactly when E* lies strictly inside one of the
interpolation intervals (r_(j-1),r_j).

Proof. Strict convexity of g and convexity of the operating boundary make
the hull minimizing load unique. At a threshold or on the final horizontal
piece, a physical branch attains that boundary, proving equality. Strictly
inside an interpolation interval, the boundary operating cost is strictly
between c_(j-1) and c_j, while the cheapest physical branch costs c_(j-1).
No physical point attains the hull-optimal projected point. Every other load
has strictly greater hull objective. Compactness of the finite union of
closed physical segments then gives an attained strictly positive gap.
Classical price-support equivalence translates equality/failure into support.

This criterion includes weak support at every boundary. Equivalently, at an
intermediate threshold r_m with m0<m<n, support at that threshold holds iff

    f/d_(m+1) <= g'(r_m) <= f/d_m.

Endpoint/final-horizontal cases are handled by the minimizer-set criterion,
without pretending every threshold is optimal.

### Explicit objective formulas

There is no nonlinear fleet-oracle search remaining in this declared class:

    D=min_m [c_m+g(clamp(E0,r_m,U))].

For each interpolation edge j, evaluate its affine operating cost plus g at

    h_j=clamp(E0+5nf/(2d_j), r_(j-1), r_j).

Also evaluate c_n+g(clamp(E0,r_n,U)) on the final horizontal piece. The
minimum of these finitely many expressions is CH. If m0=n, only the final
horizontal piece is needed and D=CH. These formulas are exact consequences
of the projection; no finite fleet bank is being substituted for the class.

When every a_i+b_j>20, edge costs are additive a_i+b_j-20, so r_m also
equals the sum of the m smallest A energies and the m smallest B energies
minus20m. This special case makes pairing identities immaterial once the
selected services are chosen. Allowing zero r_ij is therefore important for
the broader complete-crossmatching statement: the positive-part costs can
make actual matching choices consequential.

## 4. A heterogeneous complete-crossmatching counterexample

Take n=2, f=7, A energies(5,15), B energies(14,15), with all the resources
and every crossmatching specified above. The intermediate-recharge matrix is

    r = [[0,0],[9,10]].

Thus r_0=r_1=0 and r_2=9, while S=49 and U=15. The preferred full matching
pairs A5 with B15 and A15 with B14. The alternative full matching instead
requires10 early energy. Both are admitted; the better assignment is obtained
by the complete matching calculation rather than excluded competitors.

The physical projected branches are

    m=0: E in[0,15], c=28;
    m=1: E in[0,15], c=21;
    m=2: E in[9,15], c=14.

The m=0 branch is dominated but retained physically. Here

    g(E)=2401/20 -(9/10)E + E^2/10, E0=9/2.

The physical optimum is m2 at E=9, with

    D=2681/20.

The lower hull joins (0,21) to (9,14), then is flat. Its unique minimizer
on the sloping edge is E*=151/18, strictly between0 and9. Therefore

    CH=434201/3240,
    D-CH=121/3240 > 0.

These equalities are hand-derived symbolic consequences of the displayed
quadratics, not outcomes of a new numerical run. A prospective independent
verification should enumerate both physical partitions/partial matchings,
all continuous charging choices, and exact hull faces from raw SOC constraints.

Physical witnesses for the relevant hull endpoints are explicit. At E=0,
pair A5/B14 on one bus and use separate buses for A15 and B15; terminal
demands19,15,15 fit two connectors by sharing the latter two. At E=9,
pair A5/B15 and A15/B14; the second bus buys9 early and both buses buy20
terminally. All buses start and end at20. The hull mixture weights are
11/162 on the zero-early endpoint and151/162 on the nine-early endpoint. This also gives
an exact primal hull witness independently of any numerical optimizer.

The physical optimum's marginal prices are (49/10,4). Its bill plus operating
cost is2181/10, while the m=1 zero-early complete fleet costs217. Thus its
own-price regret is11/10>0. This is a fixed-price whole-fleet comparison,
not an anticipated tariff-reset bill or an independent-owners equilibrium.

## 5. Ownership qualification becomes substantive here

The identical-copy reimplementation is not harmless under heterogeneous
fixed pairs. If ownership fixes A5/B14 and A15/B15, the all-paired outcome
requires10 rather than9 early energy. The efficient crossmatched aggregate
outcome cannot simply be relabeled into that ownership institution.
Thus the generalization above is for one owner with complete crossmatching.
It does NOT carry over the identical-pair20/n individual-regret bound or the
identity between individual and whole-owner regret without a new resource
and assignment-rights theorem. This clarifies why ownership assumptions are
part of the mathematical feasible set rather than an interpretation appended
after optimization.

## 6. What this would add, and what it would not

This is stronger than the dominated-movement theorem: it characterizes an
entire heterogeneous complete-assignment class through a matching threshold
sequence and gives a necessary-and-sufficient support criterion, including
zero-cost matching edges and nontrivial match changes. It connects battery
feasibility to discrete convex matching values and then to complete-plan hull
geometry. The old identical replication is recovered by a_i=b_j=15,
r_m=10m. The theorem can replace an impression that replication relies on
artificially fixed pair duties, and the heterogeneous ownership caveat is
scientifically material.

Its restrictions must be prominent. Services occur in two simultaneous
batches; every crossmovement is feasible without travel; resources suffice
for independent early decisions and a simple terminal serial construction.
The public37-service timetable has varied timing, movement/waiting energy
and one shared connector, so it is not covered by this theorem. This is not
a scalable algorithm for general EVSP, an operational prevalence result, an
ML claim or new general convex-hull pricing machinery. Standard matching and
support theory require attribution. Originality against heterogeneous
indivisible-load/assignment constructions still needs targeted prior-art
review. A meaningful structural result is present, but significance and
submission readiness cannot be inferred from its proof alone.

Before integrating into the main theorem hierarchy, request an adversarial
source-only proof review, then one newly frozen independent exact qualification
if the parent judges its scientific value sufficient. No such qualification
was performed in this task.
