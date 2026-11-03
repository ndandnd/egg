# Independent review: heterogeneous batches with one shared connector per window

29 October 2026. Source-only mathematical review of the parent's conjecture. No numerical execution, case data, native packet, import, hash or implementation was used.

**Conclusion:** the proposed projection and lower-hull characterization are correct under the stated common-window/common-power assumptions. The zero-gap criterion must explicitly include the new clipped threshold L and start its final horizontal piece at `max(L,r_mmax)`. Upper clipping must discard infeasible cardinalities, not invent endpoints for them. With those qualifications this is a real strengthening: the theorem no longer requires n scaled connectors or the earlier pair-sum terminal-adequacy restriction.

## 1. Exact physical projection with fixed shared resources

Assume n>=1, battery B>0, `0<a_i,b_j<=B`, nonnegative connector powers K,H, positive used-bus fee f, and exactly the declared two simultaneous service batches. Early charging occurs only in [1,2], with one connector whose power and every bus's acceptance are K; terminal charging occurs only in [3,4], with one connector and uniform acceptance H. All buses start and end full, and there is no reserve, loss, movement consumption, auxiliary draw, switching time or extra charging access. At most 2n buses are used and every A-to-B pairing is permitted.

A complete service assignment is exactly a partial bipartite matching M. Matched services share one bus; unmatched services use their own buses. This exhausts alternatives rather than selecting favorable pair duties.

For the bus performing A_i, let x_i be early charge. Initial full inventory and A consumption give headroom `0<=x_i<=a_i`. If paired to B_j, nonnegative inventory after B requires

`x_i >= r_ij = max(0,a_i+b_j-B)`.

Because b_j<=B, this lower bound is at most a_i. An unmatched B bus remains full before its service and cannot accept positive early charge. For a fixed M the independent x_i intervals therefore realize exactly all early sums in `[R(M),sum_i a_i]`, where `R(M)=sum_M r_ij`.

The early shared connector adds **exactly** `E<=K`: when K>0, serialize each x_i at power K, using total duration E/K<=1. Every A bus is at the depot for the entire window, and each stays within its headroom. No separate x_i<=K condition is missing, since nonnegativity and E<=K imply it automatically. At K=0, only E=0 is permitted and the zero-energy schedule needs no division.

Terminal demands are `a_i+b_j-x_i` on paired buses, `a_i-x_i` on unmatched A buses and b_j on unmatched B buses. Each is nonnegative and at most B. Every bus is present at the depot at hour 3. Their total is S-E, where `S=sum_i a_i+sum_j b_j`. For H>0 they can be serialized at power H exactly when `S-E<=H`. Individual acceptance causes no extra restriction because each demand is no larger than the nonnegative total. Full replenishment is per bus, not an aggregate inventory balance. At H=0, all terminal demands would have to vanish; with positive B-service energies this cannot occur.

Thus, for this fixed matching, the **necessary and sufficient** early interval is

`[max(0,S-H,R(M)), min(sum_i a_i,K)]`,

when its endpoints are ordered. It has cost `f(2n-|M|)` and late purchase S-E. No assumption `a_i+b_j<=30` or `<=H` is needed; common terminal release and aggregate serialization replace the old connector-group argument.

For cardinality m define r_m as the minimum R(M) over **all** m-matchings, with r_0=0. The finite minimum is attained. Since all matching intervals share the same upper endpoint, their union is exactly

`[max(L,r_m),U]`, where `L=max(0,S-H)` and `U=min(sum_i a_i,K)`,

provided r_m<=U and L<=U. There is always an unmatched m=0 candidate with r_0=0. Hence the entire model is infeasible **if and only if L>U**. This iff is valid only with the stated positive energies and nonnegative resources; it is not an assertion about negative-power parameters.

## 2. Exact lower hull after truncation

Standard bipartite min-cost cardinality matching gives a nondecreasing, discretely convex sequence r_m. The reason is nonnegative edge costs for monotonicity and the convex fixed-flow-value function of an integral bipartite flow LP for convexity. These are classical matching facts, not new pricing machinery.

Suppose L<=U. Let `mmax=max{m:r_m<=U}` and `m0=max{m:r_m<=L}`. Both exist and m0<=mmax. Positive f makes all earlier branches with threshold at or below L more expensive than cardinality m0. They remain physical but cannot define the lower frontier.

The lower boundary starts at `(L,c_m0)`, visits `(r_m,c_m)` for m0<m<=mmax, and then stays at cost c_mmax through U, where `c_m=f(2n-m)`. If m0=mmax, it is simply horizontal on the whole interval [L,U]. In general its final horizontal piece is

`[max(L,r_mmax),U]`.

The first positive horizontal increment is `r_(m0+1)-L`, no larger than the old increment `r_(m0+1)-r_m0`. Every later increment is an original matching increment and no smaller. Therefore the successive negative slopes `-f/increment` are nondecreasing, followed by zero: the proposed graph is convex. Its endpoints are physical, so every interpolated segment belongs to the hull. Every physical horizontal branch lies on or above the graph, so every mixture does as well. This proves it is exactly the complete-plan lower frontier.

An essential upper-end qualification is already present in the conjecture: discard m>mmax. Do not replace their infeasible threshold r_m by U. For example, one A and one B each consuming15 with B=20,K=5,H=30 have U=5 and r_1=10. The one-bus assignment is infeasible. Clipping its threshold down to5 would fabricate a bus that completes B with negative inventory.

## 3. Gap and support criterion

Let G(E)=F(E,S-E) be finite and strictly convex on [L,U], with the regularity needed to attain its minimum (the intended quadratic satisfies it). Adding the convex lower operating frontier gives a unique hull minimizing load E*.

For f>0, the gap is zero exactly when E* belongs to

`{L} union {r_m:m0<m<=mmax} union [max(L,r_mmax),U]`.

At those points a physical branch attains the lower boundary. Strictly between two adjacent retained thresholds, the interpolated cost is strictly below the cheapest physical step. No physical plan attains the hull minimizing projection; strict convexity and compactness then give a strictly positive attained planning gap. Keep physical intermediate thresholds even when several frontier edges are collinear: the relative interior of a merged maximal face is **not** a valid positive-gap test.

The new boundary L must not be omitted. For example, n=1,a=b=15,B=20,K=10,H=25 gives L=5,U=10 and original thresholds0,10. Take f=7 and `F(E,z)=E^2`. The hull objective increases from its left endpoint, so E*=5 and the gap is zero, although5 is not an original r_m and is not on the final flat piece. It is the physically attained clipped threshold L.

The gap geometry uses convexity only along the fixed-total-energy line. To translate it into admissible own-load price support, retain the framework's separate assumptions on convex F, a marginal subgradient/gradient and dual attainment/admissible-price qualification. Strict convexity of G alone is not a substitute for that support qualification.

## 4. Boundary cases and scope

* **K=0:** feasible exactly when H>=S. Only E=0 is possible. The cheapest feasible cardinality is the largest m with r_m=0; the hull is a single projected point and the gap is zero.
* **H=0:** infeasible for the declared strictly positive B-service energies: E<=sum A<S, so S-E cannot vanish. The formula detects this as L>U.
* **L=U:** every admitted assignment has that fixed early total. The cheapest feasible cardinality physically attains the single lower projection, so the gap is zero.
* **f=0:** handle separately. Whenever feasible, the m=0 branch covers all of [L,U] at zero operating cost, hence D=CH for every convex supply. The positive-fee strict-interior criterion fails at zero fee. With n=1,a=b=15,B=20,K=10,H=30 and `F(E,z)=4E+(E^2+z^2)/10`, the optimum E=5 lies strictly between thresholds0,10 but is physically feasible at cost0.

This theorem uses fixed shared equipment rather than n-fold scaling, but feasibility itself imposes energy-throughput restrictions as n or service energy grows. It is not an asymptotic feasibility claim for indefinitely many positive-energy services on fixed chargers.

Uniform acceptance equal to connector power, common complete charging windows and zero switching time are substantive. Bus-specific smaller acceptance, staggered depot arrival, parked auxiliary consumption or switching overhead invalidate the simple aggregate serialization iff and need new constraints. The zero-travel, two-batch setting still excludes the varied-time public timetable. Nevertheless the strengthened projection handles genuine heterogeneous complete crossmatching with one shared connector in each window; it is more than a repetition of dominance under energy-wasting movements. No implementation qualification or operational prevalence claim follows from this proof review.
