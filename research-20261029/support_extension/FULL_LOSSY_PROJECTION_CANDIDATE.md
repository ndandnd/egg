# Complete common-loss projection with finite neutral cycles

**Status: PROVED under the stated full-action physical model, pending independent review.** Analytical source-only work; no data, execution, imports, tests, hashes or implementation qualification. The interval aggregation and convex-hull constructions used below are classical. The physical claim is that shared-resource serialization and finite battery-neutral cycles make these aggregate polygons exact.

## Precise premises

Retain lossy.tex's two fixed service batches, finite allowed bipartite graph, n>=1, 0<a_i,b_j<=B with B>0, zero reserve, no transition/auxiliary energy, full initial/final batteries and assigned fleet N=2n−m. Every bus is available throughout the early window, including B-only buses. Charging efficiency alpha and discharging efficiency delta are common in (0,1]; terminal charging has efficiency alpha. Early charging AND discharging may occur multiple times on the same bus, with no minimum action, taper, switching delay/cost or cycle/degradation restriction. Each direction may use the common connector power, within per-bus acceptance; all actions can be serialized. Shared early GROSS grid-energy budget is K, terminal purchase budget H, with the original common-window/power interpretation. These multiple-action assumptions are essential; one-direction-per-bus or a finite session cap would invalidate the proof as stated.

Set S=sum a+sum b, P=sum a, kappa=1/(alpha*delta)−1. For a fixed matching M, let R=sum_M[a_i+b_j−B]_+, T=S−NB. Total early grid purchases and exports are C,X; net grid purchase E=C−X, net early BATTERY increment Q=alpha*C−X/delta. Fee is fN. No claim about a different public model, individual efficiencies, negative consumptions or additional access follows.

## Exact fixed-matching polygon

The FULL projected (C,X) set is exactly

    C >= R/alpha,   X >= 0,
    T <= alpha*C−X/delta <= P,
    C+X <= K,
    L=(S−alpha*C+X/delta)/alpha <= H.

L>=0 is automatic because Q<=P<S. The image in (E,L,c) uses the affine equations E=C−X,c=fN. These are complete load/cost projections, not efficient envelopes. They include schedules whose extra early cycles are economically undesirable at nonnegative prices. K,H are finite; the polygon is compact when nonempty.

**Necessity.** For each bus, let x_v be its net early battery increment. Paired/A-only/B-only buses have endpoint boxes

    [a_i+b_j−B,a_i], [a_i−B,a_i], [b_j−B,0].

These constraints hold regardless of how many early actions occur. Their lower sum is T and upper sum P, giving the Q bounds. For every positive lower endpoint l_v, alpha*C_v−X_v/delta>=l_v implies C_v>=l_v/alpha. Summing yields C>=R/alpha. Nonnegative export, shared gross use and exact full-terminal battery accounting give the other inequalities. Individual terminal purchases are nonnegative, since each box upper endpoint is at most that bus's preceding service consumption, and any B consumption remains to be replaced.

**Sufficiency: first realize a minimum-throughput exchange.** Fix an admissible Q in[T,P]. The boxes admit a vector x of sum Q whose positive parts sum exactly A=max(R,Q). If Q>=R, start with mandatory positive lower endpoints and zero elsewhere, then distribute Q−R among positive headrooms up to total P. If Q<R, retain those mandatory positives and distribute the required negative sum Q−R over negative lower intervals, whose total lower capacity is T−R. Every box has upper endpoint >=0, so these allocations are feasible, including boundary/zero cases.

Execute each positive x_v by charging once and each negative x_v by discharging once. Totals are

    C0=A/alpha,   X0=delta*(A−Q).

The proposed polygon implies alpha*C>=R and alpha*C>=Q (the latter follows from X>=0). Hence C>=C0. Exact accounting gives

    C−C0 = z >=0,   X−X0=alpha*delta*z.

These residuals are a battery-neutral cycle: battery charge alpha*z equals battery discharge (X−X0)/delta.

**Sufficiency: realize the residual with FINITELY many cycles.** Choose any existing bus before its one-direction exchange, with initial early SOC s in[0,B]. If s<=B/2, choose charge-then-discharge cycles of battery depth at most B−s; if s>B/2, choose discharge-then-charge cycles of depth at most s. The permitted positive depth is at least B/2. Split total residual battery throughput alpha*z into finitely many such depths, with one smaller final cycle if necessary. Each cycle returns exactly to s and stays in[0,B]; its grid totals are depth/alpha and delta*depth. Thus the desired residual totals are attained without a Zeno limit, reserve credit or extra battery. If z=0 no cycle is used.

Perform these cycles first, then all one-direction exchanges. Total grid throughput is exactly C+X<=K, so finite serial actions fit the early common window at the admitted connector power. Their ordering changes neither service access nor inventory. If K=0 all actions are zero, so no division by a zero connector power is required. The resulting endpoint boxes ensure post-service SOC is feasible. Refill each bus to B serially in the terminal window: total grid purchases are exactly L<=H. No intermediate battery violation occurs during monotone service consumption or terminal charging. This proves physical attainment of EVERY polygon point, not just its vertices or a limit.

## Minimum matching requirement now preserves the complete set

At fixed m, N,T,P,S and fee are independent of the chosen matching. Its polygon depends on the matching ONLY through C>=R/alpha. A matching attaining r_m therefore has a polygon containing the entire polygon of every other size-m matching, and all those added aggregate points are themselves physically attained on that minimum-r matching by the construction above. Consequently the COMPLETE physical (E,L,c) projection is the union, over m=0,...,nu, of the affine images of these r_m polygons. No monotonicity, convexity or sign assumption on an economic objective is needed to minimize it over this equal set, provided the objective is defined on the declared signed-load domain and depends on the projected quantities. In particular, posted-price value queries may have negative prices; this is still a complete-fleet price-taking model, not strategic tariff resetting.

Each polygon has at most five effective halfspaces: C>=r_m/alpha, X>=0, Q>=max(T,S−alpha*H), Q<=P, C+X<=K. A bounded planar polygon has at most five vertices (with fewer in degenerate/empty cases). Thus at most5(nu+1) aggregate generator records suffice for the exact complete-plan convex hull. For alpha*delta<1 the map (C,X)->(E,L) is invertible with determinant kappa>0; when alpha=delta=1 it collapses to the familiar fixed-total-load line, without invalidating the construction. Standard vertex weights or disaggregated polygon weights give an exact continuous hull formulation. Replacing m by a scalar and merely interpolating r_m remains a different relaxation and is not justified by this result.

This strengthens the previous monotone efficient reduction rather than contradicting it: deleting a neutral cycle keeps Q and L fixed but lowers E by (1−alpha*delta)z. Monotone objectives could discard those extra points; arbitrary or negative-price economics cannot. The full projection retains them explicitly. It does not assert every literal schedule is represented uniquely, remove common-window/acceptance assumptions, or establish a new generic storage-aggregation theorem. Any manuscript integration should clearly distinguish this proved continuum claim from the older finite one-direction qualification; no new polygon/cycle implementation has been numerically qualified here.

## Common compulsory transition task: extension check

PASS. For a common nonnegative transition consumption d on every matched pair, performed in a positive-duration noncharging interval AFTER early exchange and BEFORE B, use the fixed allowed graph restricted by b_j+d<=B. Retain all full-action/common-window/acceptance assumptions above. At cardinality m set S_m=S+md, N_m=2n−m and r_m=min sum[a_i+b_j+d−B]_+. Then the complete polygon holds verbatim with S replaced by S_m:

    C>=r_m/alpha, X>=0, C+X<=K,
    max(S_m−N_mB,S_m−alpha*H)<=Q=alpha*C−X/delta<=P,
    (E,L,c)=(C−X,(S_m−Q)/alpha,fN_m).

The paired box becomes [a_i+b_j+d−B,a_i]; standalone boxes are unchanged. Its upper endpoint remains a_i because the task occurs AFTER the early window. The edge restriction makes it nonempty. Box lower sums are S_m−N_mB, upper sum is P, positive lower sum is the matching requirement. The finite neutral cycles occur entirely before the task, return to the starting SOC, and hence introduce no new post-early battery violation. Nonnegative task/B consumption makes endpoint feasibility sufficient. At fixed m, S_m is assignment-independent, so r_m again contains the COMPLETE polygons of other matchings. The union and <=5vertices/cardinality hull consequence therefore retain their unrestricted projected-objective scope. This does not cover edge-dependent d_ij, charging during the task, metric-road alternatives or a shifted resource/access policy.

Paid-idle elimination for common d must remain a MONOTONE-value dominance claim, not a full-projection claim. With k idle buses and total fleet<=2n, deleting k matching edges and replacing each pair+idle by its two singletons keeps fleet/fee and P, lowers R and reduces total consumption by kd. The same C,X remains feasible in the new polygon, but terminal purchase becomes L−kd/alpha at the same E. This proves domination under monotone economics; it does not preserve the literal (E,L,c) point or justify dropping idle alternatives for arbitrary objectives. No general literal-set equality or negative-price idle elimination is inferred. The zero-d specialization has no such consumption change, but no additional idle theorem is needed for this common-d check.
