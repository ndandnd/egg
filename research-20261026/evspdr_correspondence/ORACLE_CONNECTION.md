# Oracle connection and smallest useful synthetic seam

26 October 2026. Source-only interface note. No inputs, metadata, outcomes,
plans, generators, project imports, tests, hashes, replay or solvers were run.
No sibling file changed. This proposes a design for parent selection; it is not
an execution/input/source/resource manifest or an experiment authorization.
The parent's selected `STUDY_DECISION.md` supersedes the provisional three-context
count below with four contexts/twelve assignments, including a b=0 common-objective
control. It selects an explicitly identified movement-subset view, followed by
independent full-case replay; no identity change is hidden or treated as a lift.

## What is actually connected

The inherited EVSP-DR architecture is a valid foundation: adjacent price-taking
oracle, fixed-duty re-realization, then broader pricing with explicit certificate
scope (`ref/context/HANDOFF_PRICE_MAKER_20260814.md:742–753,801–850`). But the
inspected EGG implementation is **not an executable adapter to the adjacent
solver**. `src/egglab/evsp.py:439–450` calls its own fixed-sequence solver the
EVSP-DR re-realization *analogue*. `instance.load_frozen_subset(path)` reads an
`Instance.canonical()` JSON schema and describes the GIRO freeze as pending
(`instance.py:137–148`). It neither invokes EVSP-DR nor translates its current
station/column interfaces. No better actual adjacent adapter was found in the
inspected EGG oracle path. A real adjacent bridge would be a separate integration
task, not something the recent native helper has already accomplished.

## Existing APIs: two different physical representations

### Older `Instance` / MILP / tiny enumeration path

- `instance.synthetic_instance(seed=0,n_trips=10,battery_kwh=60.,
  soc_min_frac=.10,soc_end_frac=.10,charge_power_kw=150.,
  trip_energy_range=(14.,22.),day_start_min=300,day_end_min=1320,
  max_vehicles=None,name=None)` is a public source-defined synthetic constructor
  (`instance.py:73–134`). `Instance` has explicit start/reserve/end SOC,
  directed deadheads,28 hourly slots by default, maximum fleet and nonzero
  vehicle/deadhead coefficients (`:30–47`). No original-data input is required.
- `evsp.solve_evsp(inst,energy_cost,max_mip_gap=1e-6,time_limit_s=None)` accepts
  `('linear',posted_prices)` or `('pwl',per_slot_segments)` (`evsp.py:207–215`).
  It covers service exactly once (`:253–255`), chooses fleet up to the cap,
  and charges only on depot gaps. It has no shared grid/plug field and no
  post-pull-in full-recharge policy (`:1–10,276–303`).
- `evsp.solve_fixed_sequences(inst,sequences,energy_cost,
  max_mip_gap=1e-6,time_limit_s=None)` fixes ordered passenger-trip chains,
  **not direct/depot movement choices**. Those remain binary where both are
  compatible (`:439–450,469–486`). It returns `Solution` or `None`; it is a
  fixed-duty charging/rerouting control, not an all-movements-fixed QP.
  `validate_solution(inst,sol)` independently checks the returned plan, including
  exact-once coverage (`:628–643`).
- `regimes.solve_taker(inst,prices,**kw)`, `solve_strategic(inst,market,...)`
  and `solve_dictator(inst,market,...)` already distinguish posted, private
  strategic and system objectives (`regimes.py:24–28,116–153`). Adaptive convex
  wrappers use true-cost upper values and native dual lower bounds, but call
  the full `solve_evsp` directly (`:31–113`). There is no public fixed-sequence
  counterpart to these two adaptive wrappers.
- `enumerate_tiny.enumerate_structures(inst)` enumerates partitions **and fixed
  arc kinds**, capped at2000 structures (`enumerate_tiny.py:41–103`).
  `enumerated_dictator`/`structure_true_value` currently implement the system
  objective, not a generic three-lens callable (`:219–253`). Returned scalar
  value/structure is not a replayed physical `Solution`. These are tiny-model
  enumeration tools, not an EVSP-DR adapter or a drop-in bounded duty oracle.

The old path can already compare full versus fixed duties at posted prices.
For nonlinear strategic/system fixed duties it needs a narrow fixed-solver
callback in the existing refinement composition, rather than relabeling one
finite PWL approximation an exact charging optimum. It also needs a prospective
total-request deadline: `solver.optimize` performs an uncapped root-LP solve
before applying `time_limit_s` to the MIP (`solver.py:88–123`), and the adaptive
wrapper repeats the per-solve limit. That argument is not an end-to-end clock.
No execution of this older path is proposed merely because its functions exist.

### Recent `NativeCase` / path-flow / direct quadratic path

`native_recharge.py:1–6` explicitly separates this schema from `Instance/Solution`.
Its `NativeCase` contains source-resolved movements, piecewise bus/grid power,
connectors, efficiency, reserve, terminal opening/deadline and market edges
(`:31–85`); terminal pull-in charging and resource-aware replay are native
(`:124–129,237–342`). There is no automatic semantics-preserving
`Instance`↔`NativeCase` conversion. In particular, full terminal recharge versus
an end-SOC floor, shared resources, movement availability and operating costs
must not be silently changed.

Actual reusable native APIs are:

- `native_pathflow.build_feasible_model(case,backend='CBC')` and
  `recover_paths(case,selected_ids)` (`native_pathflow.py:109–175`).
- `warm_replication/qp_control.solve(case,a,b,prior_plan,seed,native_deadline,
  admission_deadline,check,record=None)`: existing fixed-**movement** direct QP.
- `economic_recourse_pilot/miqp_control.solve(case,a,b,prior_plan,seed,
  native_deadline,admission_deadline,check,record=None,*,fleet_N)`: one full
  declared-graph MIQP with free routing binaries and an exact-N row
  (`miqp_control.py:92–108,165–181`).
- `native_recharge.replay_native(case,plan)` and
  `native_hull.supply(Market,loads)` for physical admission and represented
  quadratic value (`native_hull.py:23–29,64–69,105–108`).

The old campaign worker enforces TRAIN/profile identities and is not the worker
for a new toy fixture. Reuse narrow solver/decoder APIs and existing bounded
ownership patterns; do not call an old campaign or replay its inputs.

## Recommendation: a thin native fixed-duty/economics diagnostic first

For the parent's immediate common-model question, use the native path, not an
unfinished adjacent adapter or a cross-schema conversion. Compare three nested
opportunity sets on **one NEW source-defined, one-depot synthetic fixture**:

1. Fixed movements, charging reoptimized by the existing QP.
2. Fixed ordered passenger-trip duties, but all declared compatible direct/depot
   modes for consecutive trips remain available, solved as MIQP.
3. Full declared graph at the same exact N, solved as MIQP.

The middle control is the missing meaningful seam. In a NEW research-local
composition, use the same original case/matrix and add restrictions excluding
cross-duty/nonconsecutive transitions and invalid starts/ends. Preserve allowed
direct/depot alternatives, exact service coverage and N. Do not fix all movement
IDs, delete a feasible alternative, change case identity to disguise a lift,
modify the sibling solver or replace the physical decoder. The existing full
MIQP helper has no fixed-duty-mask parameter today; a narrowly reviewed local
mode restriction is required before this experiment is executable. Existing
fixed-QP and full-MIQP sources remain immutable. This is not a new framework.

The precise synthetic input authority should be one future literal fixture
module in this NEW namespace, not a data-root path or `physical_learning_cases`
TRAIN ID: its complete `NativeCase` trips/movement legs/resources/market edges,
one predeclared reference trip partition and movement realization, exact N, and
literal economic arrays `a,b,U,p_post` and slot durations. Parent must choose
and freeze those literals before generation or solving. No file or fixture is
created by this note. No GIRO/Partille, old TRAIN, saved source plan, model asset,
metadata-selected favorable timetable or sealed data is admitted. Do not tune
the fixture until the middle/full control wins: a null difference is a valid
interface diagnostic. This is distinct from the existing documented
`synthetic_instance(...)` authority above, which returns the older schema.

Run each of the three controls under each of three explicitly named objectives
(nine prospective control/objective assignments, plus any separately paid common
reference admission). The native supply form is
`ops + sum(alpha_t L_t + .5 beta_t L_t**2)`:

| Objective optimized | alpha | beta |
|---|---|---|
| Posted-price cost | explicit `p_post` | 0 |
| Strategic own payment | `a+b*U` | `2*b` |
| Incremental integrated system cost | `a+b*U` | `b` |

Use `alpha=a+bU` for posted prices only if the parent explicitly declares that
posted vector. A fleet's endogenous price at its solution is not automatically
its exogenous posted comparator. The mappings follow `market.py:1–21,41–55`;
evaluate every returned endpoint under all three **true institutions** separately
(`regimes.evaluate`, `regimes.py:200–215`, documents the accounting). Preserve
original `a,b,U,p_post` alongside transformed native coefficients. Native
`Market` itself has no U field: folding U into alpha does not mean background
load disappeared. L is period grid kWh; changing slot duration requires the
corresponding power-slope conversion. All coefficients here are synthetic,
without a monetary calibration or empirical price-impact claim.

For each objective use the same physically admitted reference, then a paid
objective-charged QP incumbent protected by both MIQPs. Report acquisition,
fixed-duty and full search latency/cost separately. Use the same backend,
seed/thread policy, total paid per-request provision and physical/source admission
for the competing MIQPs. If a later pipeline inherits an earlier optimized plan,
charge that acquisition explicitly rather than claiming equal cold budgets.
No repeated solve, free retry, pre-polish screening or stale fallback across
objective institutions. All deadlines/calls/environment/resources must be
prospectively frozen; none is granted by this note.

Retain all nine planned assignments, prerequisite failure, unknown/late endpoint,
operational fallback, strict candidate status, native optimum/bound scope and
route/duty/mode-change labels. A numerical failure is not infeasibility; a valid
fallback is not fresh optimization success. Missing operands give null paired
cost contrasts, not zero or an available-only mean. Compare charging-only versus
mode-choice gain separately from passenger-duty reassignment. Report fleet,
operations, movement/grid energy and linear/quadratic cost without claiming
causal identification. One toy fixture has no population or ML-value implication.

## What a later actual EVSP-DR bridge still requires

A real adjacent adapter needs a separately pinned source/version and explicit
translation of trip/day/group identities, fixed-duty versus exact-N/fleet-cap
semantics, exactly-once versus covering, station rates/plugs versus aggregate
grid power, SOC/terminal energy, and economic/price units. Its result contract
must distinguish physical witness, fixed-duty response, finite-pool integer
optimum and completed discretized pricing certificate. These are model
correspondence requirements, not a reason to demand a new named customer or to
pretend no operational foundation exists.

The thin native diagnostic first answers a narrower confound: whether a strong
fixed-duty control already captures what the all-movements-fixed control calls
“routing value,” under correct economic lenses. It neither establishes
multistation EVSP-DR equivalence nor replaces the eventual bridge if the intended
scientific claim uses that model. No old gate changes, neural fitting, numerical
experiment or additional source/identity/controller audit follows automatically.
