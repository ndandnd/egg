# Independent proof review: lossless single-window V2G extension

Source-only mathematical review of the parent's stated candidate. No numerical execution, imports, tests, hashes, actual public data, native calls, commits or literature search. **The proposed interval and threshold classification are valid under the explicit signed-energy and gross-throughput assumptions below.** No numerical qualification or V2G novelty claim is supplied.

## Required interpretation

One early connector has charging/discharging power magnitude K during a common unit window, accepts every assigned bus, permits zero-overhead serial switching, and satisfies gross throughput `sum |q_bus| <= K`. Each bus may realize its chosen net q by a single action of that sign. All buses start full, all services/movements are those stated, capacity is B, reserve is zero, efficiency is one, and the terminal connector charges only, with power H during a common unit window. No extra parked full batteries may be introduced beyond the buses assigned to services. Otherwise the fleet count and discharging opportunities change.

Net early energy E may be negative. A supply/tariff model must explicitly permit export or incorporate fixed background demand large enough to keep total grid demand in its admitted domain. The old nonnegative-fleet-demand framework cannot simply be reused verbatim. Prices apply to net signed electricity, so exports receive the same linear rate; asymmetric buy/sell settlement is a different objective. If exports are prohibited, add `E>=0` explicitly and clip all lower thresholds at zero.

## Fixed-matching raw intervals

Let M have m pairs, using N=2n-m assigned buses. Signed early purchases have intervals:

- paired `(a_i,b_j)`: `[a_i+b_j-B, a_i]`;
- A-only: `[a_i-B, a_i]`;
- B-only: `[b_j-B, 0]`.

These follow from early headroom and enough remaining inventory to complete B, or nonnegative inventory for A-only. Monotone charging/discharging inside the window stays within the boundary inventories. Every bus's terminal need is its assigned service consumption minus q, between zero and B. B-only buses must be included: initially full does not prevent discharge before their service.

Put `R=sum_paired [a_i+b_j-B]_+`, `P=sum A_i`, and `T=S-N*B`. All upper endpoints are nonnegative. The sum of positive lower endpoints is exactly R; the sum of all lower endpoints is T. Thus the total available negative excursion is `Nminus=R-T`, and the independent signed boxes project onto `[T,P]` before the connector budget.

## Gross-throughput lemma and exact interval

For any admissible q with sum E, mandatory positive coordinates require total positive charge at least R. Hence

`sum |q| >= max(E, 2R-E)`.

This lower is attainable for every E in `[T,P]`. If E>=R, set negative coordinates to zero and distribute positive energy among their independent intervals, whose total spans `[R,P]`; gross equals E. If E<R, fix mandatory positive coordinates at their lower endpoints, all other positive charges at zero, and distribute negative energy of magnitude R-E among the independent negative intervals. This is possible exactly when E>=T, and gross equals `2R-E`. Ties and zero endpoints do not require a separate argument.

Consequently the shared early gross budget is exactly `E<=K` and `E>=2R-K`, combined with `[T,P]`. Terminal refill demands sum to S-E; serial charging at H is possible exactly when `S-E<=H`. Therefore the claimed interval is exact:

`[ max(S-H, S-(2n-m)B, 2R(M)-K), min(sum A,K) ]`,

when nonempty. At K=0 the inequalities force R=0 and E=0, so every bus has q=0; no division by zero occurs. At H=0, terminal demands must all vanish; this would force E=S. With a nonempty positive B batch, `E<=sum A<S`, so the whole model is infeasible. This is correctly detected by the interval.

## Matching union and hull

For fixed m, only R(M) varies, monotonically in its lower endpoint. An attained minimum R is the old cardinality matching value r_m. Since every matching has the same upper endpoint U, its cardinality union is exactly `[t_m,U]` for

`t_m=max(S-H, S-(2n-m)B, 2r_m-K)`.

The sequence t_m is nondecreasing. It is discretely convex: linearly interpolate the convex sequence r_m, then take the maximum of the resulting convex function times two minus K, the affine function `S-(2n-m)B`, and the constant S-H. The maximum is convex, and its integer samples are t_m. Feasible cardinalities form an initial segment; **the whole model is feasible iff t_0<=U, equivalently the old charge-only L<=U** under the maintained assumptions. Indeed `S-2nB<=0`, `-K<=0` and `U>=0`, so `t_0<=U` is equivalent to `S-H<=U`, hence to `max(0,S-H)<=U`. This corrects the initial review's overly cautious feasibility distinction. The V2G left endpoint t_0 may nevertheless be negative, so the physical projection can change despite unchanged overall feasibility.

At positive bus fee f, collapse equal initial thresholds by keeping the cheapest feasible cardinality at their shared left endpoint. Later positive threshold increments are nondecreasing, so frontier slopes `-f/increment` are nondecreasing. Thus the same physical joint-frontier interpolation and strictly-convex-supply attainment criterion hold, with the new thresholds and possible negative early endpoint. All retained physical thresholds, including collinear ones, and the final horizontal physical interval must remain in the zero-gap criterion. Fee zero again requires separate handling.

## Nominal mechanism and limits

For the stated A=(5,15), B-services=(14,15), battery20, K15,H49, algebra gives r=(0,0,9), and the proposed thresholds remain `(0,0,9)`. The late capacity implies E>=S-H=0. V2G enlarges individual charging/discharging allocations but not this cost-labelled projection, so the previously established ideal-model gap survives analytically under the same objective. This is an algebraic consequence, not a new numerical qualification.

This result isolates why enabling bidirectional charging alone need not remove assignment-induced support failure: gross connector usage and required terminal replacement still constrain its useful net load. It does not establish a first V2G/bus/grid coupling, realistic degradation economics, asymmetric settlement, lossy round-trip feasibility or practical prevalence. A manuscript extension must update signed-load/supply-domain assumptions and separately qualify its implementation before any runtime claim.

## Independent restoration-example check

Read the restoration paragraph in `paper/focused-theory-20261029/v2g.tex`; the following is exact hand algebra, without execution or numerical qualification. For A=(1,1,19), B-services=(2,10,19), capacity20, complete matching gives `(r_0,r_1,r_2,r_3)=(0,0,0,1)`: the full opposite pairing has sums20,11,21, and the two-smallest subproblem has no positive deficit. S=52, K2, H52 and fee1 imply charge-only branches with cheapest operating cost4 before E1 and3 from E1 to2. With G=E²+52/5, branch minima both equal72/5. Hull edge4-E has minimum at E1/2, giving `4-1/2+1/4+52/5=283/20` and gap1/4.

For V2G, each throughput threshold is zero: terminal clip is0, capacity terms52-(6-m)20 are negative through m3, and2r_m-2<=0. Thus three buses realize every E in[0,2]. The displayed pairing(1,19),(1,10),(19,2) with q=(0,-1,1) is feasible: terminal demands are20,12,20; after A and early action the inventories are19,18,2, and after B they are0,8,0. Discharge/charge each use half an hour at power2, fitting one serial connector; terminal totals52 fit H52. NetE0 yields D=CH=3+52/5=67/5. Gradient(1/5,1/5) gives every plan the same net-energy bill52/5, and three is the minimum bus count, so the plan is supported. No arithmetic or physical counterexample found.

## Paid idle buses: exact removal of the cap restriction

The parent's dominance argument is valid under the same lossless common-window availability, identical batteries/fees, and full replenishment for every paid idle bus. An idle bus has q in[-B,0]. For matching size m and k idles, N=2n-m+k, positive mandatory charge remains R(M), raw lower-sum becomes S-NB and upper remains P. The same gross lemma and terminal serialization therefore give the proposed interval with N in place of2n-m.

If N<=2n then k<=m. Delete any k matched edges, retaining only allowed edges, to obtain M' of size m-k. Its all-assigned fleet has exactly N buses and the same fee Nf. Splitting a pair lowers or preserves R because every removed positive deficit disappears; consequently its interval contains the old idle-fleet interval at exactly the same projected operating cost. Every idle-fleet projected point is thus realized by an all-assigned fleet, and the reverse inclusion is immediate. **The complete joint projection is unchanged when all paid used buses, including idles, are capped at2n.** This argument works for an arbitrary fixed allowed successor graph because deleting edges preserves allowedness; it does not need complete crossmatching.

For either displayed anchor H=S, allowing N>2n also cannot improve the relevant frontier: terminal capacity forces E>=0, every fleet still has E<=U, and the all-2n-standalone fleet realizes every E in[0,U] because R0=0 and S-2nB<=0. At f>0 it has strictly smaller operating cost than N>2n. Thus all such extra-idle fleets are pointwise dominated, preserving D, CH and every fixed-price response value/support conclusion. **Their extra high-cost layers do enlarge the literal complete joint projection**, so only frontier/value/support invariance should be claimed when dropping the cap entirely. With H>S, negative E can make extra idle storage useful; the anchor dominance must not be generalized silently.

These arguments permit removing the “no idle buses” restriction with the stated cap, or using the anchor-specific domination statement without a cap. They do not permit free/unpriced storage or a separate class of batteries with different availability, capacity, fees or replenishment requirements.
