# Frozen one-axis resource-recourse diagnostic — 25 October 2026

One exposed development experiment asks whether conventional route adaptation
adds useful recourse when shared charging power is halved. It is not a learned
model comparison, population test, new theorem or unrestricted certificate. Read
route_resource_mechanism/STUDY_DECISION.md for the selected mechanism and competing
explanations. This protocol resolves implementation choices before any new data
access, case construction or numerical dispatch. No automatic retry.

## Assignments and physical intervention

Four FIXED groups: physical_v2_s10001(20 trips,different prior membership),
physical_v2_s10006(20,same),physical_v2_s10009(28,different),
physical_v2_s10005(28,same). These are already exposed FIT groups, selected as
first ID per metadata stratum, not unseen confirmation or a selection of10018.
No group replacement, cap scan, new axis, fleet relaxation or model fit.

Only grid_kw changes,90 versus45. Retain per_bus_kw90,connectors1,resource0–1800,
all trips/movements/battery/reserve/efficiency, terminal opening/deadline and
source tariffs. Variant name appends '-resource-grid-90' or '-resource-grid-45'
for identity; all other case fields remain original. Exact N is the used-vehicle
count of the unchanged original source0 plan and is held equal across arms and
levels; it is not a proven minimum or day-economic optimum. Resource order is
90/45 in even group indices,45/90 in odd indices. Arm order alternates within
fixed tariff blocks. All40 task IDs/ordinals are frozen in LAUNCH.json.

Eight acquisition assignments precede32 active decisions:4groups×2resources,
then4groups×2resources×2tariffs×(fixed,adaptive). Preserve all40 assignments,
failed/late/unattempted states and spend. No acquired reference means fixed QP
is explicitly missing; adaptive remains cold eligible. Missing constructor output
or old-schedule rejection is NOT fixed-route infeasibility. Native statuses retain
their original-matrix/fixed-N/fixed-topology numerical scope.

## Exact data authority before new plan access

ONLY these original mixed TRAIN tables are admitted:

- /Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl
  SHA256 faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6
- /Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl
  SHA256 7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5

Read/hash each whole byte stream ONCE within the metered process. Full transient
json.loads is explicitly permitted for routing. Nonselected base_group records,
and SOURCE1 records even in selected groups, are immediately discarded without
semantic plan/label analysis. Routing fields are base_group and source. This is
whole-table byte access and transient decoding, not identifier-only parsing.
No other table/shard/outcome/model/weight path, non-FIT semantics or sealed bank.

Selected case fields: base_group,base_id,split,generator,physical_profile,
case_identity,case. physical_profile is compared to the unchanged pure assignment.
case expands exactly NativeCase name,trips,movements,resources,market_edges_min,
depot,max_vehicles,battery_kwh,reserve_kwh,terminal_open_min,recharge_deadline_min,
vehicle_cost,deadhead_cost_per_min,efficiency,graph_scope. Trips expand
id/start_min/end_min/start_place/end_place/energy_kwh; movements
id/kind/before/after/legs/depot_split; legs
origin/destination/depart_min/arrive_min/energy_kwh; resources
start_min/end_min/per_bus_kw/grid_kw/connectors. Preserve numeric values/defaults.

Selected SOURCE0 fields: base_group,base_id,source,case_identity,market_kind,
market_identity,source_plan_hash,selected_movements,source_plan. Whole original
plan is hashed unchanged for identity. Permitted semantic plan fields are
schema,case_identity,vehicles(vehicle,trips,movements),charges(vehicle,movement,
connector,start_min,end_min,grid_kwh),load,ops_cost. Stored load/ops are only
unchanged physical replay assertions, not authoritative economic values. No
cached source_replay/objectives are used. No SOURCE1 teacher plan is admitted.

The preflight validates four original cases/plans, unique selected membership,
canonical recovered paths and exact N, then independently replays the four
original source0 witnesses. Target tariffs are unchanged pure
physical_learning_cases.market(case,'source0'/'source1'): source0 flat .20;
source1 .10 at periods18–21/.30 otherwise; b=1/900. Pure market and assignment
calls are allowed; physical make_case/generator is NOT called.

Eight no-solve counterfactual references keep the exact original timed schedule,
copying only case_identity into the explicitly changed variant, then replay.
This is declared changed-physics evaluation, not an old90→45 recovery lift.
Rejection is reported invalid/inapplicable and NEVER becomes a fallback or
proof of route infeasibility. No clipping, retiming, repair or tolerance change.

E_ref is frozen before worker outcomes: original unchanged source0 witness mean
electricity cost across the two original tariffs at90. It stays identical across
resource levels/arms. It is NOT the prior four-witness Ebar, warm E0, total bill
or energy. Missing/nonpositive E_ref yields null ratios, not a new denominator.

## Source/import binding and native algorithms

Bind once in paid preflight the ten SOURCE_FILES in run.py: NEW run.py,worker.py,
classical.py; unchanged topology_charging/worker.py pure-helper library;
warm_replication/qp_control.py; egglab __init__,native_recharge,native_hull,
native_pathflow,physical_learning_cases. Also bind STUDY_DECISION.md,this protocol
and LAUNCH.json. Worker loads explicit paths only; no old campaign/controller,
scorer, model asset or arbitrary dataset adapter. The pure old worker's main is
never called. Existing backend-library fingerprinting inside the physical build
API is paid work, not a new duplicate audit. Freeze all consumed sources/inputs
while workers run. Source/protocol commit must be pushed before launch.

ACQUISITION: build the full declared current-physics model, add exact
sum(pullout x)==N, fix ALL movement x bounds to original source0 membership,
attach zero-price linear objective (fixed operations), one seed17/Threads1
native call. Unchanged extraction and independent replay must preserve fixed
canonical ordered paths/N. No old witness fallback, completion or extra solve.
The fresh plan must pass parent artifact-read/hash/replay/path/cost admission
within the same inclusive60s before becoming a shared current-resource prior.

FIXED: one unchanged Method0 direct QP on that admitted current-resource prior.
No prior means no numerical QP, recorded missing endpoint.

ADAPTIVE: full original movement universe and same exact N, with at most TWO
target-cost tangent MIPs. Initial tangents are zero plus common-prior load if
available; cold starts use zero only. First native cutoff17.5 from parent anchor,
second35, with all routing build/extraction/replay sharing absolute35. First
physical admission may finish after17.5 but before35. A second call is permitted
only if the admitted first candidate adds a new tangent; no identical failed
restart or completion solve. Rebuild physical rows unchanged plus exact-N and
explicit tangent rows. Rank prior and admitted routes by exact replayed integrated
cost, retain earlier endpoint on ties/failure, then one unchanged QP before52.
No native MIP-start hint or start-processing claim is made. Actual round return
and overrun are recorded; never reset the clock after a slow call.

A QP uses the unchanged helper's original matrix/copy/Method0/seed17/thread1/
NonConvex0/accuracy/extraction/replay policy. Every cold import/build/search/copy/
extraction/replay/write is paid. Candidate C, entry fallback B, retained U, native
point N and nullable bound/quality attributes remain distinct. Two-stage method
success, QP qualification, admitted route candidate and retained topology change
are separate flags; a fresh candidate need not improve/change the common route.

## Physical/economic/structural evidence

Integrated system cost is nh.rational(recomputed ops)+nh.supply(validated market,
recomputed load), c+a'L+.5L'BL, NOT atomic payment. Keep fleet/deadhead/linear and
quadratic electricity/grid energy/consumption and period loads. Fixed fleet does
not fix movement energy. Absolute costs are primary; optional ratios use E_ref.

The pure opportunity diagnostic uses admitted paths/current resources, NOT charges
or old case_identity, to report per-bus service+movement energy, ideal grid demand,
B-reserve-D margin, terminal return/common opening, selected depot windows and
common-terminal/cheap-period capacities. Missing assumptions give unavailable or
conditional null, not a feasibility claim. Actual source-timing conditions are
measured, not inferred from the generator. No physical tolerance is added.
Optional daytime charging can lower quadratic cost even without SOC necessity.
Neither capacity binding nor a larger window union proves routing value.

Canonical paths are sorted multisets of ordered (trips,movements), ignoring only
vehicle labels. For an exposed QP candidate compare directly. A helper-admitted
but unreturned candidate may use ONLY the previously reviewed unique-path source
inference with all copy/admission/no-failure guards; never call fallback replay a
caller replay of that candidate. Candidate/fallback beyond-source-envelope
inconsistency leaves qualification false. Source point agreement/OptimalityTol
and the old decimal1e-6 fixed-column band are NOT optimization-gap bounds. Finite
native bound attributes are retained without inventing exact physical intervals
or unrestricted certificates. Ideal route ordering remains UNRESOLVED.

## Resource and receipt rules

NEW total4500CPU/7200wall,dispatch4140/closure360. Preflight120CPU and finalization
120CPU/180wall are inside totals; at most one subsequent compact readout60CPU/
90wall may be frozen within the remaining reserve, never added to totals. Before
each child require own+waited-child CPU+unresolved reserve+next90 <=4140 and
remaining wall for60+cleanup3+final180. Forty potential hard90 workers leave
funding for preparation/parent/finalization. Per-task deltas are not added twice.
One native worker/thread at a time, observed worker RSS<=5GiB, parent separately
reported. Peak observations are not instantaneous containment guarantees.

Anchor precedes Popen; native cut52, complete parent endpoint read60. Acquisition
artifact read/hash/independent parent replay/components are inside60. Direct
unreaped OWNED child only, bounded TERM/KILL/reap cleanup3. Unresolved child
retains90CPU reserve and stops onward. Fatal input/source/path/physical-composition
or resource failures stop onward; ordinary missing incumbent/extraction/time/QP
failures remain recorded with any valid acquired/earlier operational endpoint.
No automatic retry or free prewrite timestamps. External owner time includes
write/exit and waited children. Historical closed prefix and unknown-review guard
remain separate; no reset/refund/restored old compliance.

Owner and worker require LAUNCH modeFROZEN/review_dispositionPASS before admitted
work. Administrative passed means ledger/accounting closure, NOT all40 attempted,
all8 priors, all32 QPs or all methods succeeded. Retained acquired-prior fallback
may exist operationally for a failed/unattempted method; its flags/source remain
explicit. Do not promote that fallback to method success.

## Readout and stopping

Report all16 resource×tariff blocks and8 tariff-specific interactions. Per-block
adaptive gain=operational fixed cost minus operational adaptive cost; resource
interaction=gain45 minus gain90. Group mean requires both planned tariffs;
overall mean requires ALL8 interactions. Missing operands give undefined values;
no available-only rescue. Report strict method/QP/route-change reliability beside
operational effects and all40 assignment states. A finite operational contrast
alone does not establish an intrinsic ideal route gap or causal timing channel.

Concede if the fixed restriction does not produce the predicted mechanism,
energy/operations explains the contrasts, a conventional policy resolves the
value, or missing/uncertain endpoints prevent interpretation. No cap tuning,
extra cohort, all79 expansion, model fit, relabeling or journal narrative follows.
Four exposed groups are development, not independent population/generalization.
Preserve the separate warm study's DO_NOT_CONTINUE for both learned families.
