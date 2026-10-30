# Common transition energy: an efficient-frontier extension

Prospective proof only; no data, code, runtime or implementation qualification. The extension is valid under the conditions below. It is an abstract service-transition-task model, not a metric road-network claim or a generic novelty claim.

## Model and fixed-matching reduction

Retain the common-loss model: n positive-energy A services a_i and n B services b_j, each individually <= battery capacity B; all counted buses start and finish full, reserve/nonservice draw otherwise zero; all are available during one early charging/discharging window, with charging efficiency alpha in (0,1], discharging efficiency delta in (0,1], signed early grid purchase E and shared gross grid-energy budget K. Terminal charging is charge-only with efficiency alpha and shared grid-energy budget H. Common windows, adequate acceptance and serial realization assumptions are unchanged. Supply F(E,L) is coordinatewise nondecreasing on the declared signed-load domain. A fixed fee f is paid per bus.

Every matched A-to-B duty performs a compulsory transition task consuming the SAME energy d>=0 in a common positive-duration NONCHARGING interval after the early window and before B. Its consumption is nonnegative throughout. Restrict the fixed allowed graph to edges satisfying b_j+d<=B, so a full battery can complete that post-early portion. Unmatched services do not perform the task. No other move can substitute away its consumption. Zero-time/energy access to the common charging windows remains an explicit abstract assumption; arbitrary locations, road metrics, timing choices or alternative routes are not covered.

For a fixed matching of size m, put N=2n−m, S=sum_i a_i+sum_j b_j, S_m=S+md and P=sum_i a_i. Let x_v denote a bus's net early BATTERY-energy increment. Paired, A-only and B-only buses respectively have boxes

    [a_i+b_j+d−B, a_i], [a_i−B,a_i], [b_j−B,0].

These follow directly from early capacity after A and nonnegative SOC after the unchanged post-early tasks. The edge condition makes every box nonempty. Their upper endpoints sum to P; lower endpoints sum to T=S_m−NB; positive lower endpoints sum to

    R = sum_matched [a_i+b_j+d−B]_+.

All standalone lower endpoints are nonpositive. Thus the independent interval allocation proof applies with exactly these R,T,P: minimum early grid export at net purchase E is

    D_R(E)=[R/alpha−E]_+.

Writing kappa=1/(alpha*delta)−1, the resulting minimum terminal load is

    L_R(E)=S_m/alpha−E+kappa D_R(E).

This accounts for transition energy in terminal refill as well as in the battery lower bounds; replacing R alone would be wrong.

## Exact feasible interval and attainment

The cycle-free efficient curve is attained for E in [t(R,m),U], where U=min(P/alpha,K) and

    t(R,m)=max{
      (1/alpha−delta)R+delta(S_m−NB),
      2R/alpha−K,
      S_m/alpha−H,
      (S_m/alpha+kappa R/alpha−H)/(1+kappa)
    }.

If t>U the matching is infeasible. The four lower bounds express available negative battery exchange, shared early gross throughput and the two linear branches of L<=H. The upper endpoint includes E<=K from the early gross budget, including when K<P/alpha. No interval may be retained merely because its lower endpoint is small.

For E>=R/alpha distribute positive battery increments over their interval ranges, with no export. For E<R/alpha retain mandatory positive lower increments and distribute negative increments over negative interval ranges; the first lower bound is exactly their sufficient capacity. This gives minimum export, gross throughput E+2D_R(E)<=K and the displayed terminal load. Execute early exchanges serially at their admitted signs, then the nonnegative transition/B consumptions, then terminal refill serially. Early box bounds ensure both capacity and final preterminal SOC; all intermediate SOC constraints follow by monotonic consumption during the transition and service. Every point of the segment, including endpoints and flat/degenerate cases, is attained. Additional early cycles weakly increase terminal energy at fixed E and gross throughput; under monotone F they are dominated, not removed from the literal feasible set.

## Cardinality reduction and convex thresholds

Let r_m be minimum size-m matching cost with edge weights [a_i+b_j+d−B]_+, for m=0,...,nu of the restricted graph. For fixed m, S_m,N and P are assignment-independent. L_R and every term in t are nondecreasing in R, since 1/alpha−delta>=0 and kappa>=0. A matching attaining r_m therefore contains the feasible E interval of every other size-m matching and weakly lowers L at each such E. Its curve has at most two segments. Physical and convexified planning under monotone F reduce to these finitely many cardinality curves by the same dominance and componentwise-mixture replacement argument as in the original theorem. Nonnegative posted-price VALUE queries likewise reduce; zero-price response ties need not all be represented. This is not a new full-projection theorem or a negative-price oracle.

Classical minimum-cost cardinality matching makes r_m a discrete convex sequence. S_m−N_mB=S−2nB+m(d+B) is affine in m. Each expression in the threshold maximum is consequently discrete convex; their maximum is discrete convex (use convex piecewise-linear interpolants and restrict their maximum to integer m). Hence t_m=t(r_m,m) is discrete convex. The fixed upper endpoint U=min(P/alpha,K) gives a contiguous feasible-cardinality sublevel set, possibly empty. Clipping must preserve infeasible cardinalities and duplicate/collinear records honestly. The maximum itself need not have its linear interpolant equal to the maximum of the individual interpolants; only convexity of its sampled sequence is used.

## Paid idle buses: dominance survives, equality does not

Allow k paid idle buses with total N=2n−m+k<=2n, all available early. They have box [-B,0]. Since k<=m, delete any k matching edges and replace each deleted pair plus one idle bus by its two singleton services. The fleet N and fee are unchanged. Total consumption drops by kd, P is unchanged and R weakly decreases. Each of the four threshold expressions weakly decreases: in the first both R and S_m−NB decrease, in the others the coefficients of R and S_m are nonnegative. At the same E the new minimum terminal load also weakly decreases. Thus the no-idle frontier dominates every such idle alternative under monotone economics. This extends the efficient VALUE reduction, not equality of load sets; removed transition consumption makes that distinction especially important.

No uncapped-idle claim follows. Nor does the argument cover varying edge energies: then both R and S_m depend on the matching, exactly the obstruction in TRANSITION_ENERGY_BOUNDARY.md. The common-d extension explains a genuine scope boundary, but it uses the original physical interval-allocation proof and classical matching facts, not a new generic scheduling algorithm. It has not received numerical implementation qualification.
