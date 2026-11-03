# Native path-flow equivalence and preflight review — 2026-09-27

**Design verdict: the compact formulation preserves the complete integer feasible physical projection of the existing native model, under its current validated assumptions.** The proposed removal of the vehicle index is an exact reformulation of the same finite movement graph, not a restriction of the service set or an approximation of shared charging. No counterexample was found in the implementation read-through. This is a proof/design and pure-test review, not evidence that a native solver has qualified the new formulation.

Reviewed candidate `src/egglab/native_pathflow.py` SHA-256:
`45864e08bffb81dc29b27774449f944fd074cb6654a593ab0d482abdad935c7d`.
Reviewed dependency `src/egglab/native_recharge.py` SHA-256:
`0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`.
The root author owns the compact source. This reviewer authored the older native model, so the compact-code review is independent of its implementation author but should be read as an author-consistency review of the old model. The separate independent native audit remains necessary.

## Exact domain of the claim

The case is a fixed, directed movement-mode graph with homogeneous buses, one selected charging depot, battery capacity B, reserve r, efficiency eta in (0,1], positive-duration mandatory service trips, nonnegative service/leg energy, and no charging except the declared depot-split and terminal windows. Every used bus starts full and must finish full. An interservice mode's last arrival is no later than the next service's start and its first departure is no earlier than the prior service's end. Multiple directed legs and parallel direct/depot modes remain distinct.

The compiler divides time at all resource, market and native availability boundaries. Each interval has at most one homogeneous connector and rate R=min(per-bus, shared-grid power), or zero when disconnected. Every eligible native visit covers the whole elementary interval. These are the same assumptions as the existing model; the compact formulation does not extend them.

The equivalence concerns feasible real-valued mathematical schedules and their complete-fleet `(intrinsic cost, market energy)` projection. It is not a claim that the two MIP relaxations, branch-and-bound trees, numerical incumbents, certificate widths or run times are identical. Materialized floating schedules remain subject to the declared native normalization, strict representability checks and replay tolerances.

## Compact constraints

For every movement mode m introduce binary y_m. For each service i introduce SOC immediately before/after the service, s_i and t_i in [r,B]. Let e_i be its service energy. Require:

- Exactly one selected mode entering i and exactly one leaving i.
- `t_i = s_i - e_i`.
- The selected pullout count K is at most the original vehicle cap V. The selected pullin count equals K (also implied by summing service flow conservation).

For every eligible mode/elementary-interval pair (m,k) introduce grid energy z_mk with `0 <= z_mk <= R_k Delta_k y_m`, where Delta is hours. Require shared capacity `sum_m z_mk <= R_k Delta_k` and define market load by summing z over intervals in that market period. Modes with no positive-capacity availability have no charging variables. Define q_m as the sum of its owned grid energy and E_m as the sum of all its leg energies.

When y_m=1, impose exactly the original selected-mode constraints:

| Mode | Required SOC relations |
|---|---|
| Pullout ending at j | `s_j = B - E_m` |
| Direct i→j | `s_j = t_i - E_m` |
| Depot detour i→j | Arrival `A_m=t_i-E_in >= r`; after all charging `A_m+eta q_m <= B`; `s_j=t_i-E_m+eta q_m` |
| Pullin from i | Arrival `A_m=t_i-E_m >= r`; full terminal restoration `A_m+eta q_m=B` |

For the depot mode, E_in is the sum of **every** leg before the declared depot split; E_m includes both sides. Because all leg energies are nonnegative, SOC decreases monotonically along each side. Arrival reserve and the next service's before-SOC lower bound enforce reserve after every intermediate leg. Charging increases SOC monotonically during the gap, so its final upper bound protects the entire gap. The same endpoint argument protects multileg pullouts, direct movements and pullins.

The candidate uses the same inactive-mode relaxation `M_m=B+E_m` for these rows. This is sufficient even though compact SOC variables always belong to a mandatory service rather than being zero for an unassigned bus: all before/after SOCs lie in [r,B], q_m=0 when inactive, and E_in<=E_m. In particular, the potentially most negative inactive pullin residual is `r-E_m-B >= -M_m`. The depot arrival/reserve and postcharge/battery rows are likewise redundant when inactive. No vehicle-dependent bound or cost is lost because the fleet is homogeneous.

The intrinsic objective is exactly `vehicle_cost*K + deadhead_cost_per_min*sum_m y_m*sum_leg(arrive-depart)`. Preserve the actual existing leg-duration definition, including explicitly encoded stationary-wait legs; replacing it with a newly interpreted travel-only cost would change the model when that cost coefficient is nonzero.

## Why paths, ownership and one-bus visits are recovered exactly

For an interservice mode i→j, positive service duration gives:

`t.start_i < t.end_i <= first_depart_m <= last_arrive_m <= t.start_j`.

Therefore service start time strictly increases on every interservice arc. This is a DAG even if a movement is instantaneous or has zero energy. With one selected incoming and outgoing mode per mandatory service, follow predecessors: a finite acyclic graph must reach a selected pullout. Follow successors: it must reach a selected pullin. No two paths can merge or branch because each service has degree one. The selected arcs thus partition all services into K nonempty depot-to-depot paths, with K<=V. A disconnected circulation cannot exist. Distinct direct/depot choices are parallel arc alternatives and are not collapsed.

Along one recovered bus path, a depot visit before service j ends no later than j's start. Any later depot visit on the same path begins no earlier than j's end, which is strictly later. A terminal visit occurs only after the path's last service and pullin. Hence two visits on one bus cannot share a positive-duration elementary interval, including the case where a bus makes multiple depot visits during its day. Endpoint touching creates no simultaneous occupancy. This proves that the old per-vehicle row `sum_selected_eligible_visits <= used_vehicle` is redundant for integer path covers; its removal does not authorize a bus to charge at two visits at once.

In interval k, all active positive z_mk belong to visits containing that whole interval, and their total is at most R_k Delta_k. Serve them consecutively on the single connector in any fixed order. A convenient representation allocates the full interval in proportion to energy; its common rate is total energy / Delta_k <= R_k. Each session lies wholly in its owner's availability window. The recovered movement→path mapping supplies vehicle ownership to the existing serial decoder. Same-path nonoverlap and the monotone SOC argument above make independent interval serialization valid globally. This claim would require a new proof for heterogeneous connectors/rates, nonpreemptive session-duration rules, or multiple connectors.

## Projection and lifting proof

**Original to compact.** From any integer vehicle-indexed feasible solution, each service is assigned to exactly one used vehicle. Set y_m to the sum of its vehicle-indexed selections and z_mk to the sum of its owned energies. A mode cannot be selected by two vehicles because it has an incident mandatory service with unique ownership. Thus y remains binary. Set service SOC to the unique owner's values. All flow, SOC, capacity and load equations remain valid; the number of selected pullouts is the used-vehicle count. Costs and market loads are unchanged.

**Compact to original.** Recover the K nonempty DAG paths and assign them arbitrarily to K of the V vehicle labels, in the old required used-label prefix order. Set used=1 on these labels, assignment=1 on their path services, and movement selection=1 on their path modes. Assign each compact z to its unique owning path. Copy compact SOC to that service's owner; set unassigned SOC and other variables to zero. All old selected rows follow from the compact equations, and its inactive rows have the same valid big-M relaxation. The old per-vehicle visit-overlap rows follow from the ordering proof above. Shared interval energy, market loads and both objective components are identical. Unused labels have zero variables. Consequently both models produce the same physical cost/load projection, up to irrelevant vehicle relabeling and charging serialization.

Since complete-fleet columns use that projection, a later hull method may use the qualified compact pricing oracle without redefining the hull. It must still record the formulation/runtime dependency hashes and receive fresh native global pricing bounds; old numerical bounds cannot be inherited as if a reformulation had already been qualified.

## Candidate-source findings and gates

Read-only inspection finds the candidate implements the constraints above: degree-one flow, pullout cap/equal pullin count, service SOC, native big-M movement relations, owned grid-energy activation, shared interval capacity, market sums and unchanged intrinsic cost. `recover_paths` explicitly rejects unknown/duplicate modes, missing coverage, branching, repeated services/modes, too many paths and disconnected selected components. Flat raw variable mappings are captured before extraction. Every positive normalized charge must map to a selected mode. Existing native normalization, serial decoding, replay, backend identity and bound-admission functions are reused.

The linear and tangent-planner drivers preserve the existing status/global-bound policy; the builder, owner reconstruction and raw index mapping are the intended changed parts. The final trace should identify the compact formulation even for infeasible or unresolved cells that have no plan; current raw/status runtime provenance and frozen source hashes support identification, but a top-level formulation field would make such results easier to audit. This is a reporting improvement, not a correctness blocker.

An external meta-path blocker rejecting any `mip`/`gurobipy` import was used to run the candidate pure/fake tests: 19 passed in 0.04 seconds at the reviewed snapshot, including one count-only test the author planned to remove. The meaningful controls include all cyclic combinatorial path covers, invalid graphs, backward-arc rejection, owned one/two-bus charge replay, nonfinite selection, unselected positive charge, correction budget, aggregate mismatch, FEASIBLE pricing-bound admission and immutable planner tangent snapshots. No solver was imported or executed.

Before optimization qualification, keep the following specific controls in the prospective gate:

1. Reuse all 15 fixed native controls and caps, with complete raw mappings and failure preservation. Independently reconstruct the compact rows and replay incumbents; compare analytical targets, not only agreement with the old implementation.
2. Add a multi-service single path with **two** charging visits, nonzero multileg inbound/outbound energy, positive reserve and efficiency below one. This tests the ownership/endpoint argument not exercised by the simple two-service topology. Include competing direct/depot modes on the same service pair and a binding vehicle cap.
3. Include exact half-minute availability and a partial market-period terminal window using the same resource compiler. The model must keep full replenishment and zero opportunity charging outside declared visits.
4. Preserve the shared-connector contention/infeasibility control. Do not substitute separate per-path capacities for the interval fleet sum.

After those pass and independent audit agrees, assess the full 37-service input under a new fixed bounded protocol. The public schema counts predict a reduction from 751,914 to 20,322 charge variables (depot 15), or 705,294 to 19,062 (depot 16), before counting other rows/variables. Those are dimension comparisons only; they do not establish native runtime, numerical robustness or a guaranteed solve budget. The reformulation is the principled way to retain all 37 services and all admitted movement modes while reducing redundant vehicle labels.

## Additional independent pure multi-visit extraction control

After the initial read-through, this reviewer constructed a three-service fake
incumbent without importing either native optimizer. A single recovered bus
serves A at 30–60, B at 120–150, and C at 210–240 minutes, each from P to Q and
consuming 6 kWh. Battery is 20, reserve 2, efficiency 0.8, fleet cap 1, vehicle
cost 7, leg-time cost 0.5 per minute, and one 60 kW connector is available over
0–300. Market edges are 0,60,120,180,240,300.

The pullout D→P at 0–10 consumes 2 kWh; pullin Q→D at 240–250 consumes 2.
For each earlier service end t in {60,150}, the four-leg depot mode is
Q→X at t…t+5, X→D at t+5…t+10, D→Y at t+50…t+55, and Y→P at t+55…t+60;
each leg consumes 1 kWh and the depot split is after leg two. Thus native
visits are 70–110 and 160–200, followed by terminal availability 250–300.

The fabricated selected path has 8 grid kWh in the first visit, 8 in the first
compiled interval of the second visit, and 21.5 terminal kWh. Compact
`_extract` maps all three sessions to the same recovered path; unchanged native
replay passes with market load `[0,8,8,0,21.5]`, total grid energy 37.5,
intrinsic cost 37, flat-price objective 74.5, and final SOC 20. This is an
extraction/ownership and arithmetic control with a manually supplied feasible
incumbent, **not** a solve, native matrix check or optimality claim.
