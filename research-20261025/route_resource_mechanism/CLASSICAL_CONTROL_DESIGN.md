# Classical routing control for a one-axis resource mechanism study

Prospective static design, 25 October 2026. Read the next-resource decision and
only necessary candidate/construction APIs in density_control, matching_pool,
classical_controls, native_pathflow, constructive_charging and recovery_lift.
No rows, plans, shards, outcomes or model values were opened; no imports,
computations, hashes, tests, replay, solves or training ran. No old source was
edited. This is a scientific design outline, not a source/command manifest.

## Control choice: generate routes, then optimize their charging

Use a **full-declared-graph conventional routing search followed by direct
charging QP** as the primary adaptive control. A fixed teacher pair is a two-route
catalog, not a competent complete routing policy: neither route can acquire a
new depot visit/connection when resource restrictions make that necessary.
Matching cover IDs and CA1 scores alone are candidate sets/rankings, not feasible
electric fleets. The old density run's native objective is pure fleet count;
calling that an integrated economic route optimizer would also be misleading.

The thinnest competent economic construction is bounded target-cost tangent
routing followed by the unchanged direct QP on its admitted route. Freeze a
small fixed routing-round cap (for example two), rather than selecting a search
depth after outcomes. Retain an admitted route incumbent through later ordinary
failure and pay its final direct charging solve inside the same endpoint.
This remains a conventional bounded economic heuristic, not the globally best
integrated routing algorithm or a replication of GRASP/decomposition literature.
No learned score, model, teacher-label retrieval or new family is needed.

For a clean route-opportunity question, fix the same prespecified fleet quantity
N across reference/fixed-route/adaptive policies and resource levels. Otherwise
allowing fleet to change introduces a separate fleet-acquisition mechanism and
must be reported as such, not called pure charging opportunity. The existing
high-level planner does not expose an exact-fleet argument; adding only a
max_vehicles ceiling is **not** an equality. The fixed-N version therefore needs
a thin future caller composing the existing full physical builder/objective/
optimizer/extractor APIs and adding `sum(pullout x)==N`, without monkeypatching
the old builder. It is a new narrowly reviewed composition, not already qualified
code. The full graph avoids making an arbitrary density quota the mechanism.

## Exact useful APIs and reuse limits

| Existing API | Sound unchanged reuse / constraint |
|---|---|
| `cc.ca1_score(case,a,b)`; `cc.select_connections(case,scores)` | Generic validated NativeCase ranking/selection; no20/28 size ban. Preserves boundaries/common B/exact K. Useful optional pool diagnostic, not a route constructor or physical bound. Its local capacity proxy ignores shared contention and accumulated SOC. |
| `density_control.selector.select(case,a,b,arm,*,cover_function,check)` | CA1 branch can compose the generic score/selector. CoverCA1 requires a compatible cover_function. A cover union exceeding unchanged K is a design failure, not permission to enlarge K. |
| `matching_pool.pool.candidate_pool(case,*,check)` | **Not unchanged-compatible:** it explicitly accepts only40/80 trips. Do not call it on20/28 or remove its guard in the frozen file. Its three global maximum-cardinality route-only covers retain parallel modes, but certify neither electric feasibility nor economic optimality. |
| `pf.build_feasible_model(case,backend='CBC')`, `pf.attach_objective(built,'tangents',rows)`, `pf._optimize_once(built,budget,deadline)`, `pf._extract(case,built,record=None,round_index=0)` | Generic original-physics routing primitives; GRB explicit for the proposed comparison. Density run demonstrates model construction, candidate upper-bound masking, seed readback, extraction and NR replay. Reuse those operations, not its fixture-generation/asset/runner logic or pure-fleet objective. A fixed-fleet equality and bounded tangent composition need a fresh thin caller. |
| `pf.solve_planner(case,a,b,budget,record=None,*,completion=False,start_plan=None,start_case=None,deadline=None)` | Generic bounded tangent routing policy, with `budget.max_rounds` and a common deadline; useful unchanged **only if its fleet policy is acceptable**. It has no exact-N argument. `start_plan=None,completion=False` avoids old-witness recovery and optional completion solves. |
| `pf.solve_pricing(case,prices,budget,record=None,start_plan=None,*,completion=False,deadline=None,start_case=None)` | One linear integrated-cost MIP constructor plus extraction/replay when completion=False; works without a feasible old prior. Its pricing bound concerns the linear model, not the final quadratic objective. Useful paid bootstrap under changed resources. It exposes neither exact-fleet nor native-seed arguments; use the builder composition if those must be set/read back. |
| `recovery_lift.lift_plan(source_case,full_case,source_plan,*,a,b)` | Pure restricted→full identity lift with independent replay. Requires identical non-name/non-trip/non-movement physics and exactly equal trip/movement physics on the subset. Copies paths/sessions unchanged and recomputes assertions. It cannot lift an old90kW case into a45kW case. |
| Unchanged `qp_control.solve(case,a,b,prior_plan,seed,native_deadline,admission_deadline,check,record=None)` | Direct one-QP recourse after a replay-valid prior exists on the **current** resource variant. Keeps its original fallback/admission/numerical scope. No guarantee of runtime compatibility or ideal objective-gap bound follows from this design. |

Sources: [cover size guard](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/matching_pool/pool.py:15),
[density selector](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/density_control/selector.py:10),
[generic CA1](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/classical_controls.py:150),
[pricing](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:599),
[planner](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:709),
[lift](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/recovery_lift.py:21).

## Changed resources require fresh feasible acquisition

A candidate grid restriction90→45 is one possible axis, **not selected by this
note**. It may reject existing90kW sessions even if the same routes admit a new
schedule. The frozen QP helper validates its fallback before solving; a failed
old-plan replay cannot be reported as fixed-route infeasibility or as failure of
charging optimization.

Pay a fresh conventional constructor for each resource variant where a prior is
needed. For the fixed-route control, build a restricted case containing exactly
the predeclared selected movements, preserving all changed-variant physics and
original movement objects. `pf.solve_pricing` with no start and completion=False
can construct a new schedule; unique path coverage prevents a different topology.
Lift that newly constructed restricted-variant witness into the full **same
changed variant** via the unchanged lift API, then pass it to direct QP. This
does not clip, retime or repair the old witness. The lift refuses differing
resources and independently replays both representations.

For the adaptive control, search the full changed variant before direct QP.
No valid prior/no incumbent means unresolved construction, not zero cost or a
proof of physical infeasibility. A restricted/native model's INFEASIBLE status
must retain that model's scope; extraction failure/time limit does not certify
infeasibility. If exact full-matrix fixed-route infeasibility is essential, use
the full builder with binaries explicitly fixed rather than claiming a
movement-restricted compiler's result is an unrestricted physical certificate.
The existing `complete_topology(case,selected_ids,a,b,budget,*,deadline,
record=None,clock=time.monotonic)`
is another fixed-route constructor, but makes up to three calls; it cannot be
called a one-call bootstrap, and its repair flags authorize nothing here.

## Small prospective mechanism experiment

Hypothesis: route adaptation has incremental value when a route-dependent charge
opportunity intersects a binding common resource; plentiful common recourse can
make different memberships economically interchangeable. Competing explanation:
the routes mainly differ in energy requirement or imperfect teacher schedules,
and charging recourse alone explains the apparent context effect. Equal point
values at two tariffs do not establish equal/dominating feasible-load sets.

Before new rows, choose a small deterministic derived-metadata cohort: for
example the first complete group by base ID in each20/28 × changed/same stratum,
using the already frozen strata and no cost fields. Freeze four IDs and grouping
then; do not favor10018 or replace a later failure. Use baseline and one
source-justified constrained level of **only grid power**, retaining per-bus
power, connector count, availability, SOC, efficiency, trips/movements, prices
and fleet policy. No cap scan, altered terminal window or simultaneous battery
restriction. Static source suggests substantial common terminal access, but
stored timing/resource truth must be admitted later, not assumed from a default.

Minimal active policies are (1) one prespecified fixed reference topology,
freshly scheduled and QP-charged under each variant, and (2) the full conventional
fixed-N routing+tangent/QP policy above. Choose the fixed reference by a declared
rule, not the cheaper old route at each target. Retain the old whole schedule as
a no-solve reference only where it replays in the variant; invalid reference
is missing/inapplicable, not an operational fallback. With four groups, two
levels, two tariffs and two active policies this is32 prospective decisions,
not32 independent populations. Keeping both teacher topologies or adding a
density arm would be a larger separately funded design, not an automatic extra.

A possible **new** funding envelope is3600CPU/7200wall with conservative32×90
worker funding,360CPU closure, paid preflight/finalization and one serial thread/
observed5GiB. It is not the already closed pilot's remaining budget. Freeze
within-worker constructor/tangent/QP call counts and suballowances under one
inclusive endpoint before implementation; fresh prior acquisition is not free
preprocessing. No start/solver/capture/replay/publication time is omitted. A
budget-fit calculation and focused source qualification remain required; this
outline supplies no numerical launch or reservation.

## Falsification and stopping

- If the restriction does not create the predicted opportunity/binding contrast,
  report that failed manipulation; do not search another cap until it works.
- If charging-only control matches the adaptive conventional points within the
  justified numerical/economic resolution, the proposed incremental routing
  mechanism is unsupported in that regime. A missing objective-gap bound makes
  ideal ordering unresolved, not a new exact tie or a falsified theorem.
- If adaptive benefit is explained by fleet quantity or grid-energy requirement,
  concede that channel rather than labeling it pure timing-opportunity value.
- Constructor/qualification failures make comparisons missing/inconclusive.
  Preserve all planned cells and scoped native statuses without repair, retries,
  fleet/quota relaxation or outcome-chosen replacement.
- If competent conventional recourse resolves the operational question, stop
  there. A load-set identity/dominance observation is classical diagnosis, not
  new theorem/ML novelty. This design is not a route to a favorable ML regime;
  the negative warm learned-margin result remains unchanged.
