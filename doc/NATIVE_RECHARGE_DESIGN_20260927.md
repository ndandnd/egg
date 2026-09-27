# Native terminal recharge: minimal isolated research design

27 September 2026. **Design only: no new implementation, scientific solve or
cluster job has been executed for this note.** This public design contains only
generic model facts and proposed resource budgets; private source identities,
rows, locations and hashes are intentionally outside it.

## Recommendation and scope

Implement a separate research module with its own versioned input, physical
witness and column schemas. One shared feasible-set builder serves both complete
fleet pricing and the physical planner; only their objectives differ. Initially
support one depot, homogeneous buses/charging limits, continuous lossless
charging, known directed movements, explicit native terminal availability,
piecewise-constant shared power, and preemptive finite connectors. Allow
non-hour-aligned charging windows exactly. Keep service trips indivisible and
mandatory, and require every used bus to start and finish full.

Do not change the existing `Instance`, `solve_evsp`, `validate_solution`, regime
functions, B2/A6 column schema, replay-policy constants, or checkpoint identities.
An opt-in production extension is premature: current `soc_end_kwh` applies
**on pull-in**, while the new target applies **after native depot recharge**;
these represent different feasible sets even if the numeric field matches.
The existing charge record also assumes an inter-trip arc with both trip IDs.
A default-off boolean would not resolve the schema and checkpoint distinctions.
After qualification, a deliberate later migration can expose a production API.

This is a bounded operational microcase adapter, not general multidepot/tapering
charging software. Historical vehicle blocks are optional feasibility references,
not mandatory trip assignments or evidence of optimality. Source service energy
may be retained, but deadhead energy needs an explicitly declared conversion if
only distance is available. Supply curvature, charging efficiency and vehicle
physics must be declared research assumptions wherever the source does not
identify them. Do not infer a tariff or objective weights from solved blocks.

## Why the existing adapter cannot simply be switched on

- `evsp.solve_evsp` charges only on selected inter-trip depot arcs. Its terminal
  inequality demands the terminal SOC before any terminal charging can occur.
- `slot_overlaps` correctly computes the **individual** energy limit of a
  partial charging window. Adding one shared energy cap per original market
  slot would not enforce simultaneous shared power when windows only partly
  overlap.
- Existing replay groups charging by the inter-trip pair and uses the old
  terminal inequality. New terminal ownership, plug scheduling, direction/time
  checks and aggregate-resource replay need a separate witness validator.
- The physical qualification models component-wise shared caps but deliberately
  admits only aligned hourly events. It is a useful control, not a qualified
  implementation of the proposed arbitrary-window extension.
- Existing `Instance` movement lookups are directed and raise on absent keys.
  Preserve that fail-closed principle; do not introduce silent zero, reverse,
  reference-place or nearest-location substitutes.

## Small concrete interfaces

Proposed names illustrate contracts, not a requirement to build a new framework:

```text
NativeCaseV1
  trips: mandatory service records with stable local IDs, exact times and energy
  depot; max_used_vehicles; battery_kwh; reserve_kwh
  initial_soc_kwh = terminal_target_kwh = battery_kwh
  terminal_open_min; recharge_deadline_min
  movement_modes: verified directed, time-resolved candidate movements
  resources: breakpoints with common per-bus kW, grid kW and connector count
  market_period_edges_min
  semantics: departure/waiting policy, preemptive connectors, efficiency = 1

compile_case(case) -> ValidatedNativeCase, candidate-arc ledger, event grid
build_feasible_model(validated_case, backend) -> physical variables/constraints
solve_pricing(validated_case, prices, budget) -> NativeOracleResult
solve_planner(validated_case, convex_market, budget) -> NativePlannerResult
replay_native(validated_case, NativePlan) -> physical/economic replay report
```

`NativePlan` contains used-bus service sequences, selected directed movement
modes, exact depot arrival/departure times, and charging segments with vehicle,
resource/connector, start, end, grid energy and owner. Owner is either an
inter-trip depot visit or `terminal_after(last_trip)`; **no service marker** is
created. Store full-precision event energy and reconstructed market-period
loads. A complete-fleet column is `(intrinsic_cost, grid_load_vector, NativePlan,
case_identity, replay_version)`. Its cost excludes electricity transfers.

Use a separate identity covering the complete physical input, movement policy,
event grid, boundary policy, resource limits and replay semantics. A tariff-only
change may preserve physical columns; a terminal deadline, grid cap, connector,
reserve, travel or efficiency change does not. Legacy columns are not implicitly
importable. Reuse only market algebra/statistics containers whose meaning is
unchanged; do not pass native records through old terminal replay or disguise
them as old `Solution`/checkpoint records.

## Directed and time-dependent movement admission

Represent each admitted movement mode with directed endpoints, legal departure
condition, departure/arrival time, duration, distance/energy provenance and
intrinsic cost. Preserve service-day elapsed time above midnight; apply daily
periodicity only when expressly established. Exact same-location travel may be
zero; string similarity is not location equivalence.

Use a three-way intake ledger: known, explicitly forbidden, and unknown.
Default publication admission fails if a potentially relevant movement is
unknown. A separately declared *known-arcs-only diagnostic* may omit unknown
arcs, but its bounds then concern that restricted graph, not the unknown full
transportation opportunity set. Missing return-to-depot movements or inability
to cover any mandatory service are hard admission failures. Missing energy is
not filled by copying a travel time.

The smallest well-defined waiting policy fixes post-service deadhead departure
at service completion and allows waiting at the destination. For depot departures
before the next service, enumerate the relevant travel-profile modes rather
than evaluating all legs at one common hour. If duration, energy and cost are
constant within a departure band, use its latest feasible departure: this
maximizes available charging without worsening those quantities. Retain all
non-dominated bands because a different band can trade charging opportunity
against movement duration/energy/cost. Apply the same treatment to pull-outs.

This reduction requires a specified departure-time lattice or attained closed
band endpoint. If arbitrary continuous departure, non-FIFO profiles, ambiguous
band endpoints or variable energy/cost defeat that dominance argument, stop
admission; do not silently flatten the source profile. A frozen static-travel
sensitivity can be a later explicitly labeled model, but is not faithful
implementation of a time-dependent source. This policy is part of the common
planner/pricing feasible set and limits any claim of equivalence to the original
operator's scheduling problem.

## Native physical formulation

Use the current vehicle-indexed path structure conceptually: trip assignment,
pull-out, pull-in, direct/depot connection and used-bus binaries. Every service
is covered exactly once. Every used bus has one nonempty acyclic service chain,
one pull-out and one last-service pull-in. No empty bus can contribute stored
energy or occupy a fictitious service. Precheck positive service duration and
chronological candidate arcs; reject malformed cycles rather than depending
on extraction to discover them.

Let q be an admitted depot visit (including a selected terminal pull-in), v a
vehicle, and k an elementary charging interval of duration delta_k hours. A
visit has selection binary x_vq and availability window [arrival_q, departure_q].
For a terminal visit ending at the common recharge deadline, arrival is the
later of depot return and terminal opening. Depot-return energy is consumed
**before** terminal charging, and arrival SOC must meet the reserve.

The event grid contains every admitted visit arrival/departure, terminal
opening/deadline, market-period edge and resource breakpoint. No interval
straddles a change in availability, price period or resource limit. Add charging
energy e_vqk only when the whole elementary interval lies in visit q:

```text
0 <= e_vqk <= P_k * delta_k * x_vq
sum_q x_vq over visits covering k <= used_v <= 1
E_vk = sum_q e_vqk
sum_v E_vk <= min(grid_kW_k, connectors_k * P_k) * delta_k
```

P_k is the common effective vehicle/connector power limit. The sparse per-visit
energy representation has direct ownership and simple replay; avoid a compact
but difficult-to-audit aggregate that can attribute charging to the wrong
visit. Compile/report dimensions before admitting a solve.

Service and movement SOC equations follow the selected chain. Charge increments
are the sum of its visit energies; enforce reserve on depot arrival, before
and after each service/movement, and battery capacity after charging. Charging
is nonnegative and SOC increases monotonically during a depot interval, so
endpoint bounds plus the event schedule cover intermediate charging SOC. Gate
inactive assignment SOC and derive finite valid big-M constants from actual
bounds; do not assume the existing blanket 2B is adequate for arbitrary new
travel data. Indicator constraints may be used where the chosen backend and
cross-backend qualification support them.

For a selected last service i, require:

```text
arrival_SOC = after_service_SOC - directed_return_energy >= reserve
arrival_SOC + sum(native_terminal_charge_energy) = battery_capacity
```

All terminal energy lies after physical return and before the common deadline.
There is no charging beyond the represented horizon. An unused bus has no
charging and no operating cost. Market load L_t is the sum of grid energy in
event intervals belonging to market period t. Thus F(L) is explicitly a
**period-energy** cost; it is not an unmodeled integral of instantaneous power
cost. With efficiency one and full replenishment, grid purchases equal total
service plus selected deadhead energy; different schedules can still have
different deadhead energy.

### Finite connectors without hidden overlap

The inequalities above are exact for the stated **homogeneous, preemptive,
zero-switching-time** connector semantics, provided the implementation also
constructs an explicit within-interval schedule. They are not a claim that
all buses charge simultaneously at their average power.

For one interval, let Q=min(grid_kW, mP). The average-rate vector lies in
`0<=r_v<=P, sum r_v<=Q`. Every vertex of that polytope has at most
ceil(Q/P)<=m positive components (with zero case handled separately), since
at most one component can be strictly between its bounds. Each vertex is
therefore a physically allowable instantaneous charging configuration.
Decomposing an average vector into a finite convex combination of vertices
and assigning their weights as durations constructs a schedule with no more
than m simultaneous occupied connectors and no instantaneous grid violation.
The single-connector case is simply serial charging at effective power
min(P,grid_kW), with idle time as needed. Within an event interval there are
no intermediate service deadlines or availability changes to invalidate the
construction.

The witness must include the resulting subintervals and connector assignment;
independent replay checks them by sweeping all interval endpoints. This is
what makes the interval-energy formulation a physical model rather than an
unwitnessed average relaxation. Reject heterogeneous charger/vehicle power,
compatibility restrictions, nonpreemptive charging, setup time or idle-connected
plug blocking in V1: the simple polytope is not justified for those policies.
Those are later models, not optional flags whose semantics can be ignored.

## Objectives, bounds and common-set certificates

Complete-fleet pricing minimizes `c(s)+p.L(s)` over the entire native case,
not one independently chosen vehicle duty. The physical planner minimizes
`c(s)+F(L(s))` over exactly that set. Use one shared builder and a deterministic
constraint fingerprint, excluding only objective/epigraph differences. All
power/connector limits belong inside every complete physical plan before any
convexification. Retain the same travel modes, used-bus rule and native terminal
policy for fixed-sequence reference solves too.

For the first implementation, a tangent-MILP planner permits the same CBC/local
and Gurobi/cluster model and preserves transparent lower/upper accounting.
Every tangent is globally valid for the declared convex F. A native bound for
the tangent relaxation is a planner lower bound; replay plus the true F gives
a physical upper bound. Constant curvature must be nonnegative and input
ranges explicit; do not add a nonnegative epigraph lower bound when the allowed
cost function can be negative. Direct MIQP is unnecessary for this first step.

A small isolated clean master can use the same algebra as the qualified driver,
but native column replay/identity remains separate. Only fresh clean-master
prices plus complete native pricing bounds update the hull lower bound:
`LB_CH = z_clean + min(0, pricing_LB - sigma)`. A replay-feasible mixture gives
UB_CH. Positive `LB_D-UB_CH` can already establish a gap without fully closing
both optimizations; never substitute the restricted master value for LB_CH.

Freeze a **new** bound-aware termination contract prospectively. An OPTIMAL
clean master is needed for its duals. A pricing/planner time-limit status with
a replay-valid incumbent and a trustworthy finite global lower bound can
produce an interval without falsely claiming optimizer optimality; the final
objective-width test decides certification. Record status and interval even
when unresolved. Error/numeric-invalid/no-valid-bound states cannot certify.
This is not a retrospective change to the previous frontier's OPTIMAL rule.
Record solver feasibility tolerances and conservative bound allowances; only
the hand-derived controls below have exact rational targets.

## Independent replay and minimal qualification ladder

The replayer must not use model variables, selection flags as proof, or the
builder's precomputed charging capacities. Recompute travel from the frozen
movement ledger and selected times, coverage, visit ownership, physical return,
full SOC trajectory and terminal equality. Sweep every actual charging
subinterval endpoint to check vehicle/connector concurrency and total grid
power. Reconstruct period load, total purchased energy, intrinsic movement/fleet
cost, and the objective at the posted prices. Check aggregate solver load only
as a diagnostic against reconstructed load. Do not round positive events away
before replay. Freeze separate numerical tolerances with the new schema;
report residual maxima rather than changing historical policy constants.

| Gate | Smallest useful controls and expected checks |
|---|---|
| 0: no optimizer | Directed missing/unknown/reversed movement rejection; midnight/override boundaries; no invalid weekday union; schema identities; event-grid coverage; exact price and physics identity separation |
| 1: local native physics | One real service with native terminal recharge; insufficient deadline infeasibility; late return and low arrival SOC rejected; no charging for unused vehicle; full battery conservation including return energy |
| 2: resource semantics | Two simultaneous half-hour windows inside one hour, each needing 5 kWh at 10 kW, with 10 kW shared cap: infeasible although an hourly 10 kWh aggregate cap would accept it. Disjoint half-hour windows with the same demands: feasible. Serial one-plug witness, corrupted overlapping witness rejection, and market-boundary load reconstruction |
| 3: common-set/economics | Reproduce the archived native two-service construction and its exact targets using both pricing and planner; compare tiny enumerated complete structures to the master; positive reserve and one-plug controls below; terminal-disabled/unlimited-resource compatibility check against legacy feasible physics without importing old checkpoints |
| 4: local microcase admission | Validate private extraction and directed movement coverage; compile dimensions; replay a supplied historical reference only if its physical events survive the new policy. Do not assume source block feasibility proves charging feasibility. Freeze physics, market, resource budgets and unknown-arc policy before solves |
| 5: one bounded Gurobi job | One microcase/one declared market: cold complete pricing, physical planner and a bounded clean-column diagnostic. Save every failure/bound and stop at budget. No learner or tariff campaign until this gate and non-author replay pass |

Corruption tests must include wrong terminal owner, recharge before arrival,
charge beyond deadline, duplicate trip, swapped directed leg, missing energy,
SOC overfill, insufficient terminal SOC, overlapping use of one connector,
shared-power violation, and a forged aggregate load. A fake-oracle trace test
must retain the snapshot-mutation regression. Separate physical correctness
from the existence of a positive economic gap: zero and infeasible cases are
successful controls when correctly classified.

## Two analytical controls to freeze, not newly executed results

The existing two-service construction has 15 kWh per service, 20 kWh battery,
early shared limit 10 kWh, terminal shared limit 30 kWh, and one-hour windows.
The one-bus schedule uses early/terminal energies (10,20); the two-bus family
uses (x,30−x), 0<=x<=10. At the stated f=7 and a=4 costs, its known targets are
D=97, CH=94.8875 and gap=2.1125.

**One finite terminal connector preserves this feasible family.** Give it
30 kW. The two buses need terminal energies 15−x and 15, so serial sessions
last (15−x)/30 and 15/30 hours, totaling at most one hour. Both are available
through the terminal window. At x=0 the sessions occupy consecutive half-hours;
there is no overlap or hidden simultaneous charging. One bus needs only 20/30
hours. Early charging involves only the bus that served the first service.
Thus even contiguous per-bus terminal sessions suffice for this particular
control, although the general V1 connector model allows preemption.

**Positive reserve preserves the construction if usable capacity is preserved.**
For reserve r>0, set battery/start/end energy to 20+r. Add r to every SOC in
the original witness; all charge quantities, supply loads and intrinsic costs
are unchanged. For example, r=1 gives trajectory 21→6→16→1→21. Combine it with
the one-connector witness above as a prospective native control. This changes
battery capacity along with reserve; it is not robustness at fixed capacity.

**Fixed-capacity negative control:** retaining a 20 kWh battery while adding
positive reserve requires one-bus early charge at least 10+r, contradicting
the 10 kWh early cap. For 0<r<=5 the two single-service buses remain feasible,
so the one-bus branch disappears and this particular positive-gap mechanism
is lost. Report that distinction rather than claiming reserves are harmless.
These statements are direct analytical derivations; no new experiment has
been run to validate an implementation against them.

## Resource admission and stopping

Local controls: one CBC thread, 10 seconds per native phase, hard 30-second
control subprocesses and a fixed five-minute total qualification allowance.
Set model time limits **before** any LP-first phase; the existing wrapper's
MIP-only time argument by itself does not cap that preliminary solve. Native
startup, replay and serialization count in process wall time. Freeze source
and protocol before the first optimizer control.

First operational-size admission: at most 30 services and a declared two-bus
cap, with no automatic fleet expansion. Admit only if compiled dimensions are
at most 50,000 variables, 10,000 binaries, 100,000 constraints and 500 elementary
intervals; otherwise inspect the formulation rather than silently pruning
arcs or rounding times. These are proposed conservative engineering caps, not
claims about actual input/model size.

After local gates pass and the queue permits, submit **one** ordinary-priority
Unicorn Gurobi job: 1 CPU, 4 GB, 15-minute scheduler wall limit; 12-minute hard
worker limit, 30 seconds per native phase, at most six planner refinement
rounds and twelve complete pricing attempts, with at most 5 seconds per clean
master LP and a shared remaining-time budget. No arrays, opportunistic CPU
expansion, automatic retries or interference with other research jobs. Backend
and license failure stop the job without fallback changing the experiment.
If the cluster's allowed partition/resource policy differs, freeze the revised
resource envelope before submission rather than guessing a partition here.

Successful completion requires common-set/physical validation and the declared
certificate width; a budget-exhausted interval is still a useful recorded
outcome. Increase resources or amend a policy only in a separately frozen
follow-up with the original attempt preserved. Private data and lineage remain
local/private; publish only approved generic model code and derived artifacts
that do not disclose source records.
