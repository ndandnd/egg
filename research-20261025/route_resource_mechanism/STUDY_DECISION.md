# Selected next study direction — one grid-power restriction

25 October 2026. Parent scientific integration after the static source analysis.
This selects a small development design and implementation scope. It is NOT an
executable source/input/command manifest and launches no computation. Do not
repeat this design exercise next wake; implement the narrow caller, review it,
freeze exact admission/command, then run the one new attempt if coherent.

## Operational question and selection

Test whether route adaptation has useful additional charging recourse when
shared grid power is halved, with fleet quantity held fixed. This studies a
classical operational mechanism first, not whether a new favorable ML regime
can be found. Preserve the previous negative learned-margin result.

Use four already exposed FIT groups:10001(20,different membership),10006(20,same),
10009(28,different),10005(28,same). Rule: first base ID within each of the four
size×membership strata of the CLOSED eight-group cohort. These IDs' outcomes
are already known; this is not unseen selection/confirmation. The rule uses no
cost magnitude and does not choose the favorable10018 contrast. No replacement.

The sole physical axis is resource.grid_kw=90 versus45. Keep per_bus_kw90,
connectors1, resource start/end, charging availability, timetable/movements,
battery/reserve, efficiency, prices and per-group fleet quantity unchanged.
The factor1/2 is chosen from the declared90kW source setting, not a cap search.
No second restriction, alternative cap or expanded fleet follows if it fails.
Counterbalance resource order by the fixed group index:90/45 for even indices,
45/90 for odd indices. Arm order alternates within tariff blocks. This changes
only prospective task ordering, not group membership or resource definitions.
Source0/source1 tariffs retain original a and b. Source1 cheap-window capacity
changes from360 to180kWh; common12h terminal capacity from1080 to540kWh. These
are source-derived capacities, not claims about actual required group energy.

## Two active policies and honest acquisition

The primary fixed reference is ALWAYS original source0's topology, not the
cheaper historical route at each target. Set N to its original used-vehicle
count, a feasible historical reference quantity rather than a proven optimum.
The adaptive classical policy may use all declared movement modes but MUST
satisfy the exact SAME N at both resource levels; max_vehicles alone is not
that equality. Preserve all original physical rows and independently replay.

For each group×resource (8 assignments), acquire one FRESH feasible charging
witness on that fixed reference topology under current physics. Prefer a thin
composition of the generic full physical builder with all movement binaries
fixed to the source0 IDs, one zero-price feasibility/operations solve and
unchanged extraction/replay. This preserves the full movement-universe rows and
avoids conflating a restricted compiler's status with original fixed-route
infeasibility. If a restricted-case constructor is used instead, unchanged
lift_plan is valid only restricted-current→full-SAME-current physics. The choice
and exact one-call contract must be frozen in the implementation manifest.
There is no old90→45 recovery lift, old-plan retiming, charge clipping or repair.

Grid restriction may invalidate the old timed charging witness while the same
routes remain feasible. The direct QP helper requires a replay-valid current-case
fallback. Therefore pay acquisition before QP, and never equate failed original
replay or constructor timeout/extraction failure with route infeasibility. Keep
native statuses and their fixed-model numerical scope. All failed acquisition
assignments remain; do not silently drop or replace their group.

Per group×resource×tariff (16 blocks), the two active policies are:

1. **Fixed-route charging:** unchanged direct Method0/seed17 QP on the newly
   admitted reference witness. One QP optimize, same original physics/decoder.
2. **Full-graph classical routing plus charging:** target-cost tangent MIP on the
   original full declared graph with exact N, then one unchanged direct QP on
   its admitted best route. Prospectively cap routing at TWO native tangent
   calls, no completion solve or adaptive extra call. Zero and common-prior-load
   tangents may initialize the objective where the common prior exists; exact
   tangent/admission conventions are frozen before execution. Retain a valid
   prior operationally without claiming native start processing or route search
   success. The high-level planner lacks an exact-N parameter, so this requires
   a small explicit builder composition; no monkeypatch or old source edit.

If reference acquisition fails, preserve the fixed-route endpoint as missing;
allow the preassigned adaptive arm to attempt cold fixed-N routing without a
fictional common fallback. Finding a feasible adaptive plan then is an operational
endpoint, not proof that the reference route is infeasible. Conversely, no adaptive
incumbent is construction failure/unresolved, not infeasibility. QP qualification,
route-search admission and operational retention remain separate flags. All
16 blocks/32 active decisions plus8 acquisition assignments stay in denominators.

Keep the unchanged original timed source0 schedule as a no-solve reference ONLY
if it independently replays under the resource variant. Counterfactual evaluation
may copy only its physical identity into the declared changed case while paths,
charges and stored assertions remain unchanged; preserve original whole-plan
identity. This is declared changed-physics evaluation, not a recovery-lift proof
or repair. Invalid references stay inapplicable/missing and are never fallbacks.

The CoverCA1 builder rejects20/28 and cannot be relabeled an unchanged-compatible
control. Its size guard remains untouched. The generic CA1 selector alone is not
an electric-fleet constructor; the old density driver minimizes fleet count, not
integrated economic cost. The full-graph conventional policy here must earn its
reported reliability; no globally best/strongest-classical-method claim follows.

## Endpoint and funding direction to freeze concretely

Select a NEW prospective envelope4500CPU/7200wall, dispatch4140/reserve360; no
reuse/refund of the closed pilot. Forty possible workers×90CPU conservative
funding leaves540CPU before dispatch for preflight/parent handling; closure360
includes finalization120CPU/180wall. One serial native thread and observed worker
RSS<=5GiB. Own+waited-child CPU is cumulative, children are not added twice.
Reserve unresolved children conservatively and stop onward dispatch.

Each acquisition/active decision uses parent-before-Popen native52/final60,
including cold imports/build/search/copy/extraction/replay/publication/parent-read.
For the adaptive worker, routing has absolute cutoff35 seconds from parent anchor;
one final QP may use the remaining time to52, admission60. Its two MIP calls
share that35s and never reset it: first-call cutoff17.5, second-call cutoff35.
Initialize tangent points at zero plus the admitted common-prior load if present;
use an admitted first-round physical load for any new second-round tangents.
Skip the second call if no admitted first candidate/new tangent exists; do not
restart an identical failed search. Retain every intermediate candidate/failure.
Fixed-reference acquisition is separately paid
and reported; this is a shared-incumbent operational study, not cold speedup.
No training/model assets or new timing framework. Reuse the thin closed-pilot
worker/receipt pattern; no old qualification matrices or controller expansions.

Before any native job: exact input/field allowlist (four source0 groups only),
pins, task IDs/order, case-variant convention, resource changes, source/import
closure, prior/acquisition/tangent/QP policy, scoped bounds, numerical evidence,
failure/accounting rules and fresh command/namespace must be frozen after one
focused source review. Whole mixed TRAIN byte access/routing transient decode
must remain explicit if those tables are used. Owned old specs/plans are not
implicitly admitted alternatives. No automatic retry or outcome replacement.

## What will answer the question

Record ideal route energy/operations separately from period loads and economic
components; common-terminal no-midday-SOC sufficient condition and cheap-window
capacity provide ex-ante mechanism diagnostics, not feasibility certificates.
Check actual source timing/profile/resource assumptions on admitted inputs.
Source-valued original and newly generated plans remain distinct.

Report adaptive-versus-fixed operational feasible-cost contrasts at each resource
and their resource interaction within each group/tariff. Retain all failures and
planned denominators; no available-only average or significance claim. Fleet is
held fixed, but route energy can change: a cheaper lower-energy route is a
quantity channel, not timing flexibility. Prices see integrated system cost,
not atomic payment. Source0 flat-price positive curvature can reward optional
daytime spreading even when no midday charge is required for SOC.

Absolute generator cost units and energy/components are primary. If normalizing,
use a single fixed E_ref: the original unchanged source0 witness's mean electricity
cost under the two original tariffs at90kW. It is computed before new outcomes,
remains identical across both resource levels/arms and is not the earlier
four-witness Ebar or warm E0. Missing/nonpositive E_ref gives null ratios, not
a substituted denominator. This diagnostic has no learned-family promotion gate.

A power reduction cannot lower an individual ideal fixed-route optimum, but the
route advantage need not increase. Failure of the predicted resource interaction,
energy/operations explaining all differences, or competent conventional recourse
resolving the effect are reasons to concede/narrow the ML motivation. No cap
retuning, extra resource axis or model fit follows. Numerical native OPTIMAL and
finite ObjBound attrs remain distinct from a justified exact physical objective-
gap certificate; no invented point±epsilon intervals or unrestricted bounds.

This four-group exposed development study is not independent generalization,
market calibration, teacher optimality or publication readiness. Positive
classical route flexibility would justify a later decision-value target, not
establish that learning is needed. Missing/weak outcomes can justify stopping
this learning direction. No journal narrative is precommitted to a positive result.
