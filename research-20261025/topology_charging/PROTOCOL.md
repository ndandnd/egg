# Frozen stored-topology charging pilot — 25 October 2026

This is one exposed FIT qualification/diagnostic, not training or a new model
comparison. Separate route choice from charging by optimizing each of two original
route systems under each of two original tariffs. Original witnesses, physics,
accuracy, helper and fallback remain unchanged. No clipping, repair, completion,
relabeling, outcome replacement, extra solve or automatic retry is permitted.

## Fixed assignments and data authority

COHORT.json was materialized once, before QP outcomes, by the closed metadata-only
selection in COHORT_SELECTION_PROTOCOL.md. Ordered bases are10001,10002,10018,
10006 (20 trips), then10009,10010,10015,10005 (28 trips). Each size has three
changed-membership groups and one same-membership control. Names are
physical_v2_s<base>. Selection used ascending IDs within strata, not costs. Exact
32 task IDs/order are in COHORT.json: route0/target0, route0/target1,
route1/target0, route1/target1, rotated left by group index modulo4 and reversed
for odd floor(group index/4). Do not remove control calls if routes agree.
Shortage, identity/profile/size mismatch or invalid original witness stops
without substitution. Preserve8/32 planned denominators,6 changed/2 controls.

Original data access is limited to these two literal TRAIN tables:

- /Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl
  SHA256 faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6
- /Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl
  SHA256 7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5

Whole mixed TRAIN bytes are read/hashed once in the metered main preflight. Full
json.loads transient decoding for routing is explicitly permitted: read top-level
base_group and immediately discard nonselected rows, without semantic analysis.
This is byte access to the entire table, not identifier-only parsing. Selected
semantic access is ONLY the eight frozen FIT groups. No other row/shard path,
non-FIT analysis, model outer performance, weights, fitting, scoring, generation,
sealed data or cluster operation is admitted.

Selected case fields: base_group,base_id,split,generator,case_identity,
physical_profile (complete declared assignment for exact comparison),case. Case
expansion is exactly NativeCase fields name,trips,movements,resources,
market_edges_min,depot,max_vehicles,battery_kwh,reserve_kwh,terminal_open_min,
recharge_deadline_min,vehicle_cost,deadhead_cost_per_min,efficiency,graph_scope;
Trip id/start_min/end_min/start_place/end_place/energy_kwh; Movement
id/kind/before/after/legs/depot_split; Leg
origin/destination/depart_min/arrive_min/energy_kwh; Resource
start_min/end_min/per_bus_kw/grid_kw/connectors. Defaults are unchanged.

Selected source fields: base_group,base_id,source,case_identity,market_kind,
market_identity,source_plan_hash,selected_movements,source_plan. Whole source_plan
is hashed unchanged for identity; permitted semantic plan fields are schema,
case_identity,vehicles (vehicle,trips,movements),charges (vehicle,movement,
connector,start_min,end_min,grid_kwh),load,ops_cost. Cached load/ops are only original
replay consistency guards, never authoritative valuation; cached source_replay or
stored objectives are not used. No nested field expansion beyond the unchanged
case/plan/helper APIs is authorized. Stored selected rows are copied into only
their owned child specs for the same admitted operations.

Other main inputs are COHORT.json,PREPARATION_ACCOUNTING.json,PROTOCOL.md and
LAUNCH.json. Main consumes the already frozen lineage backreference/F/Ebar in
COHORT, not old raw receipts again. StageA accounting is carried once. Actual
stored assignment/trip count, profile/resources/grid, case/market/whole-plan
identities and movement universe must match. Source tariffs derive from unchanged
physical_learning_cases.market: source0 flat a=.20; source1 a=.10 at periods18–21
and .30 elsewhere; b=1/900. Pure assignment/market validation is permitted; no
physical case is generated. Independently replay16 original witnesses once during
admission and verify fixed F/Ebar against the already published baseline.

## Source and launch freeze

Main source closure: topology_charging/run.py and worker.py;
warm_replication/qp_control.py; src/egglab/__init__.py,native_recharge.py,
native_hull.py,native_pathflow.py,physical_learning_cases.py. Paths are relative
to the literal worktree in LAUNCH.json. Hash these eight sources once in the
metered main preflight; no shell hash audit. Existing paid backend library
fingerprinting/imports inside the unchanged build API remain paid work. Actual
module paths must match this tree. No full campaign/scorer/asset import.

Use only unchanged generic qp_control.solve(case,a,b,prior_plan,17,
native_deadline,admission_deadline,check,record). One optimize per cell: Method0,
seed17,Threads1,NonConvex0,FeasibilityTol1e-9,OptimalityTol1e-9,BarConvTol1e-10;
copy/readback/objective/extraction/replay guards unchanged. No test matrix or
separate native primitive precedes this actual stored-case pilot. Static review
is INTEGRATION_REVIEW.md; launch requires its PASS disposition and a pushed source
commit. Source/helper/protocol/cohort/tables stay frozen while children run.

## Resource, ownership and timing policy

A new practical package is3600CPU/7200wall seconds, dispatch stop3240CPU and
closure360CPU. Preflight120CPU includes the closed StageA charge. Finalization
120CPU/180wall is inside closure/total, not added. Before every child require
StageA retained charge + own CPU + waited children CPU + unresolved child reserve
+ next hard90CPU <=3240; remaining wall must fit next60+cleanup3+final180. All
imports, parsing, hashing, original replay, build/copy, search, extraction,
candidate replay, independent retained replay, artifact writes, observation and
finalization count. External whole-process time includes the write/exit suffix.
Do not add child diagnostics again to cumulative waited-child measurements.

One serial native worker, one computation thread, observed peak RSS<=5GiB per
worker; parent separately reported. Sampling/ru_maxrss is not instantaneous
containment. Child anchor is before Popen: native cutoff52, complete receipt read
by parent60. Hard worker CPU90 is funding/containment, not permission for late
admission. Native start processing is not implied by keeping a physical fallback.
Direct owned unreaped children only receive bounded TERM/KILL/reap cleanup3s;
unresolved child retains90CPU reserve and stops onward dispatch. No replacement
monitor or historical PID signaling. Latched failure state remains latched.
Finalization and publication have total/final wall timers; an expired allowance
can leave the owned incomplete receipt rather than publish a successful packet.

Any source/input/path/resource fatal stops onward. New-domain original_model or
copy_contract non-timeout failure before native calls, or an unexpected helper
interface exception, is a fatal qualification/bootstrap discrepancy. Ordinary
solver/extraction/timeout failures retain their truthful failed/provisional
outcome and valid fallback if possible, with no retry. Every attempted,
unattempted, failed, late, crash and unresolved assignment remains in the ledger.

## Cost, topology and numerical evidence

Integrated system cost is nh.rational(recomputed replay.ops_cost)+nh.supply(
validated market,recomputed load), i.e. c+a'L+.5L'BL, not atomic payment. Preserve
fleet/deadhead/electricity/energy components and generator units. Fixed F is the
unchanged original-witness cost; original Ebar is the mean of four original
witness×tariff electricity values. F−U and normalization use that SAME Ebar,
including when fallback is retained. No winner-specific normalization.

Canonical route identity is the sorted multiset of ordered (trips,movements)
paths, ignoring vehicle-label permutation only. Validate original versus unique
pf.recover_paths result. Direct candidate path comparison is used only if its
plan is exposed. If fallback retained but fresh candidate admitted, the frozen
ROUTE_IDENTITY_INFERENCE.md guards may establish source_guarded_unique_path_inference:
passing copy/admission/no-failure contract, exact selected-ID equality/physical
replay by the unchanged helper and independently verified unique paths. This is
NOT a caller replay/observation of an unreturned candidate plan.

Keep candidate C, original fallback B, retained U, native point N, attempted native
bound/quality attributes separate. Null unsupported values remain null. A cell
qualifies only with timely NEW physical candidate, native OPTIMAL/qp_success,
copy/settings/objective/replay/route guards, exactly one optimize, parent timely
admission and no optimal-candidate-versus-fallback discrepancy. Operational valid
fallback/endpoint is separate from numerical qualification. Campaign passed is
not the same flag as32 qualified cells.

NUMERICAL_QUALIFICATION_CONTRACT.md defines the source point agreement envelope
using the source binary-float OBJECTIVE_TOL and conversion residuals. This is not
an optimization-gap bound; the earlier decimal1e-6 fixed-column reporting band
is not QP accuracy evidence. If C exceeds already feasible B beyond that envelope,
flag discrepancy/unqualified; do not call the retained B an optimal candidate.
Unsupported ObjBound is null; finite native attributes alone do not certify
exact physical or full-space values. Native OPTIMAL and OptimalityTol are not a
mathematical objective-gap bound. Ideal route ordering remains UNRESOLVED in this
pilot; no automatic point±epsilon interval/certificate is constructed.

Report all16 target route point contrasts when qualified, alongside original F
contrasts and every missing comparison. Same canonical routes have a common ideal
value: above-envelope point differences are unresolved numerical findings, not
route preference. Control discrepancies must be reviewed explicitly, not hidden
by fallback retention. Findings concern only exposed FIT witnesses, not learned
information value, teacher global optimality, significance, population transfer,
new theorem or a publication-ready contribution. No automatic refit/full79 study
follows. Preserve the negative warm learned-margin result and prior charges.
