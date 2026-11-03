# Fixed allowed-successor graphs in the shared-connector theorem

29 October 2026. Independent mathematical/source-only assessment. No new numerical qualification, data, execution, imports, hashes or agents.

**Conclusion:** yes. The fixed shared K/H projection, clipped frontier and support criterion extend to an arbitrary fixed allowed bipartite successor graph G, with cardinalities restricted to0,...,nu, where nu is its maximum matching size. Completeness is needed for the sorted-smallest/opposite-pairing corollary, not for the physical projection or matching-value convexity.

## Exact assumptions

Keep the original two simultaneous batches, homogeneous battery B, `0<a_i,b_j<=B`, full initial/terminal inventories, fee f>=0, and at most2n buses. Keep one early connector of power K and one terminal connector of power H, with identical per-bus acceptance, complete windows [1,2] and [3,4], and no other charging, auxiliary draw, transition consumption, transition time, taper or switching time.

The only change is that an A_i/B_j shared-bus assignment is permitted iff `(i,j) in G`. Every individual A and every individual B still has its original standalone service plan. G is a fixed declared operational compatibility restriction; it is not an outcome-selected duty bank or a heuristic subset claimed to represent all physically allowed successors. Removing standalone options or reducing the available fleet cap requires a different feasibility statement.

Let nu be the maximum matching cardinality of G. Put

`r_ij=max(0,a_i+b_j-B)` on allowed edges,

`r_m=min{sum_(i,j in M) r_ij : M subset G, |M|=m}`, `r_0=0`, `0<=m<=nu`.

Every such cardinality exists by deleting edges from a maximum matching; no larger cardinality exists. Define S, L=max(0,S-H) and U=min(sum A,K) exactly as before.

## Projection proof

A complete fleet is exactly an allowed partial matching, with one bus for each matched edge and one for every unmatched service. A bus cannot cover two simultaneous A services or two simultaneous B services. This exhausts the declared set.

For any allowed matching M, the A_i bus's early charge belongs to `[r_ij,a_i]` when matched and `[0,a_i]` otherwise. The lower endpoint is no larger than a_i because b_j<=B. Unmatched B buses remain full before service and cannot buy early energy. Therefore early sums fill the entire interval `[R(M),sum A]`, where R(M) is the edge-weight sum. This argument does not use a missing or forbidden crossedge.

All A buses are present throughout the early window, so one connector implements those allocations serially iff E<=K. All used buses are present throughout the terminal window, each terminal requirement is nonnegative and at most B, and their total is S-E. One common-power connector implements them serially iff S-E<=H. These are exactly the original physical arguments; restricting G changes neither the individual inventory equations nor charging access.

Thus M permits `[max(L,R(M)),U]` when nonempty, at cost `f(2n-|M|)`. For each allowed cardinality m the finite minimum r_m is attained and all intervals share U, so their union is

`{(E,S-E,f(2n-m)): max(L,r_m)<=E<=U}`,

provided r_m<=U and L<=U. The complete physical projection is the union over0<=m<=nu. When L<=U the empty matching supplies a feasible standalone fleet; when L>U even that total-energy requirement is impossible. Hence global feasibility remains **iff L<=U**, including nu=0 and graphs with isolated vertices.

## Matching convexity and clipped hull

Nonnegative edge costs imply r_m is nondecreasing: delete an edge from an optimal m-matching and compare with the optimum of size m-1. For convexity, construct the standard unit-capacity network source->A->B->sink using only allowed edges and their costs. Its fixed-flow-value LP is integral at every integer flow m, and its continuous optimal value is convex in the prescribed flow requirement by LP duality. Consequently

`2r_m <= r_(m-1)+r_(m+1)` for1<=m<nu.

Neither integrality nor convexity requires a complete bipartite graph. Missing edges merely change this finite sequence and its maximum feasible domain.

For f>0 and L<=U define

`mmax=max{m<=nu:r_m<=U}`, `m0=max{m<=nu:r_m<=L}`.

Both exist because r_0=0. The lower cost frontier starts at `(L,c_m0)`, visits `(r_m,c_m)` for m0<m<=mmax, and is horizontal at c_mmax until U, where `c_m=f(2n-m)`. Its final flat domain is `[max(L,r_mmax),U]`.

The first positive clipped increment is `r_(m0+1)-L`, no larger than its original increment. The remaining increments are original nondecreasing matching increments. Hence the negative slopes are nondecreasing, followed by zero. The graph is convex, consists of mixtures of actual allowed-matching endpoints, and lies below every physical branch. The same two-sided frontier proof therefore applies verbatim.

Discard cardinalities m>nu as nonexistent and m>mmax as resource-infeasible. Do not assign them fictitious upper-clipped endpoints. If m0=mmax, including the empty-graph case, the entire relevant frontier is a physical horizontal segment.

## Support and qualifications

For finite strictly convex G(E)=F(E,S-E) on the feasible interval, with attained minimum, let E* be the unique hull minimizing load. For f>0 the gap is zero exactly on

`{L} union {r_m:m0<m<=mmax} union [max(L,r_mmax),U]`.

At these points an allowed physical matching attains the frontier. Strictly between adjacent retained thresholds, the frontier cost is strictly below every physical branch at that load; strict convexity and compactness give a positive gap. Collinear intermediate thresholds remain physical and must not disappear from this test. Classical own-load support equivalence additionally retains the original convex-supply, dual-attainment and admissible-price qualifications.

At f=0, the empty-matching branch has zero operating cost over all [L,U], so D=CH whenever feasible. K=0, H=0 and singleton-interval cases have precisely the same previously stated interpretations. For nu=0 all plans have the same used-bus count2n and the projection is already convex, so its planning gap is zero.

## What does not extend

The sorted-smallest/opposite-pairing shortcut cannot be applied to arbitrary G. For the already used A energies(5,15), B energies(14,15), battery capacity20, a graph containing only the two corresponding-index edges has full-matching recharge threshold10, whereas the complete graph's crossed matching achieves9. The sorted corollary would invent a forbidden edge if used unchanged. This hand illustration concerns the corollary's scope, not a new run or a selected empirical instance.

Matching-dependent transition energy would also change total consumption from the common S, and nonzero transition time can remove part of a supposedly common charging window. Then the one-dimensional fixed-total-energy projection is generally lost; simply inserting the directed timetable graph into this theorem is invalid. Staggered service/depot windows, smaller bus-specific acceptance or switching time likewise need new resource constraints.

This extension therefore strengthens the analytical assignment class to fixed heterogeneous compatibility graphs without claiming arbitrary EVSP coverage. The fourteen completed shared-connector implementation cases remain **complete-graph** qualifications; no allowed-sparse-graph implementation qualification is claimed by this proof. Its new statement should receive independent proof criticism before integration, with any future computation separately justified and frozen.
