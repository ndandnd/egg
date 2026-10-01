# Reviewed-premise two-path exact matching relaxation

27 September 2026. Prospective mathematical design only; no matching solver,
native optimizer, result calculation or implementation was run for this note.
The original exact flat-price matching attempt at
`result/sistig_matching/20260927-attempt1` remains immutable. Its independently
audited ideal stored-input lower bounds are approximately 301.31534 and
305.63381, each attained by one *relaxed* path. These do not establish a
physically feasible one-bus schedule. The separate post-pilot argument in
`SISTIG_ONE_BUS_OBSTRUCTION_20260927.md` proves one bus impossible in each
declared 37-service graph by forced chronology and an energy deficit. Its
independent proof review **passed** at
`research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md`,
checking the frozen input and all forced transitions with exact fractions.
This admits the at-least-two-buses premise for the stated ideal physical
graphs; the new optimization and certificate remain prospective.

## Validity and exact cost scope

Retain the existing `flat_energy_relaxation.path_cover_problem` reduction and
all 37 mandatory services, every declared directed connection alternative,
declared endpoint modes, exact binary-stored input values, price, efficiency,
vehicle and movement costs. For each ordered service pair, the cheapest
declared parallel mode supplies its exact edge cost, as in V1. Forbidden arcs
stay forbidden. The ideal full-recharge price objective remains

`baseline + sum_(selected real successor edges) a_ij`,

where `a_ij = w(i,j)-h(i)-o(j)-f` and baseline includes all service energy,
one vehicle per service and its cheapest pullout/pullin. Charging energy equals
total represented consumption divided by efficiency only in the intended
fully replenished physical model. Battery SOC, charging opportunities, serial
resource capacity and the maximum-fleet restriction remain relaxed. A path
count here is still a relaxation path count, never a physically feasible bus
count.

Any physical schedule with `K` used buses maps to `n-K` selected real
successor edges: each of its `K` paths with `s` services has `s-1` such edges.
The separately reviewed structural proof establishes `K>=2` for each frozen
public graph. Hence every ideal physical schedule maps to a matching with at
most `n-2=35` real edges. Therefore minimizing over those matchings is a valid
lower bound on the **ideal stored-input** flat-price physical objective. The
new feasible matching set is a subset of V1's matching set, so its exact
minimum is weakly higher than the old exact matching bound; strict improvement
is a future empirical question. The independently replayed two-bus native
witnesses establish physical nonemptiness under the declared numerical policy,
but do not turn this exact ideal lower bound into an exact physical optimum.

## Integral min-cost-flow construction

Do not append a bare cardinality row to the rectangular assignment solver and
assume its old dual still applies. Construct a directed capacitated flow
network for `n=37` and fixed flow value `n`:

1. Source `s` to each predecessor row node `R_i`: capacity 1, cost 0.
2. Each allowed real connection `i→j`: `R_i→C_j`, capacity 1, cost exact
   `a_ij`. No arc exists for a missing declared connection.
3. Each row has `R_i→t`, capacity 1, cost 0, representing its own unmatched
   dummy choice. Multiple unmatched rows can use these separate arcs.
4. Each real successor column has `C_j→g`, capacity 1, cost 0, enforcing at
   most one predecessor for service `j`.
5. Gate `g→t` has capacity `n-2=35`, cost 0. Thus no more than 35 real
   connections are selected.

Supply is `b_s=n`, demand `b_t=-n`, and all other node balances are zero. Each
row receives and sends exactly one unit. A real column can receive at most one
unit, while the gate caps their total. Conversely every allowed matching with
at most 35 real edges routes all 37 units through this network, using each
row's unmatched arc otherwise. The validated service chronology makes the
real-edge graph acyclic, so selected edges form disjoint paths and the gate
implies at least two relaxed paths. A 37-unmatched-edge flow proves the network
is feasible even if no connection edge exists.

This is an ordinary directed-network flow polytope: its node-arc incidence
matrix is totally unimodular and capacities/supplies are integers. An optimal
basic flow can therefore be integral even though costs are signed exact
rationals. Scale costs by their exact common denominator if an integer-cost
algorithm is used. Negative connection costs must remain negative; use a
method valid for signed costs, such as Bellman-Ford-initialized augmenting paths
or exact negative-cycle cancellation. No optimizer backend is required by the
mathematical design.

## Exact primal/dual certificate

Archive every arc, capacity, rational cost and integral flow, plus rational
node potentials `pi_v` normalized by `pi_t=0`. An independent verifier checks
arc bounds, source/sink and every intermediate conservation row, the count of
real and unmatched edges, decoded movement IDs and exact agreement of path
cost with `baseline + sum a_ij f_ij`. It then forms the reduced cost
`r_a = c_a - pi_tail(a) + pi_head(a)` for every original arc. A forward
residual arc exists if `f_a<u_a` and must have `r_a>=0`; a reverse residual arc
exists if `f_a>0` and must have `-r_a>=0`. These conditions forbid every
negative-cost residual cycle and imply optimality at fixed total flow, even
with negative original costs.

For an independently checkable dual objective, use

`D = sum_v b_v*pi_v + sum_a u_a*min(0,r_a)`.

The verifier requires exact equality between `D` and the primal network cost.
Weak duality follows by writing each arc's cost as `r_a + pi_tail-pi_head`
and minimizing `r_a*f_a` over `0<=f_a<=u_a`; residual reduced-cost signs make
the actual integral flow attain those minima. All values are exact fractions;
an outward-rounded display is optional and cannot replace the fraction.
Corruption controls should change a real-edge count, flow conservation, a
forbidden edge, a capacity, one potential or one objective fraction and require
the verifier to reject each.

## Prospective gate and interpretation

Pin the passed independent one-bus proof review and its exact input and proof
hashes. Then obtain independent reduction/certificate preflight, including
small signed sparse graphs with brute-force minima, empty real-edge graphs,
negative edges, parallel-mode ties and cases where the cardinality gate binds
or does not bind. Freeze source, inputs, protocol, budget and exclusive new
attempt path before either public calculation. Independently reconstruct both
public certificates without importing the author algorithm. Preserve all
failures and compare the new exact values with the original matching values
without modifying them.

Report any result as a post-pilot ideal stored-input lower
bound. It must stay separate from the archived native solver lower endpoints
and tolerance-conditional physical witnesses. The rounded native SOC/movement
matrix and replay allowances have not been proved identical to the ideal
stored-input model; their values cannot silently be combined into an exact
gap or substituted into the original numerical pilot. Nothing here establishes
the nonlinear planner, complete-fleet hull or own-price regret on the public
case.
The one-bus proof could motivate a separate native minimum-fleet cut, but this
note does not propose one: stored-row roundoff and solver/replay tolerances
would need their own prospective validity analysis before adding a native row.
