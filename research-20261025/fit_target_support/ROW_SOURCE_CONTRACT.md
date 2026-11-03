# FIT target-support row source contract

25 October 2026. Static schema trace only, using the existing provenance/next-FIT
decision notes and the named exporter/loader APIs, with narrow identity and plan
encoding references. No actual JSON asset, table, row, label or outcome was read;
no imports, tests, hashes, generation, replay, inference or solver calls ran.
This specifies a prospective collector, not its execution or historical truth.

## Two exact tables and their joins

The existing pool writer copies `cases.jsonl` and `source_inputs.jsonl` as JSONL,
one JSON object per line. It writes source rows without flattening their nested
plans or reencoding fields into a different schema
([pool writer](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:100)).
Its validation keys are top-level `base_group`, `base_id`, and for source rows
`source`; source kind is restricted to source0/source1 and `(base_group,source)`
must be unique ([join checks](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:63)).
Do not derive routing IDs by searching a line for a substring or nested plan
field. Source rows do **not** contain a required top-level `split` field; join
them to the admitted case's TRAIN identity.

| Table | Source-defined top-level fields |
|---|---|
| `cases.jsonl` | `base_group`, `base_id`, `split`, `generator`, `case_identity`, `physical_profile`, `case`, `witness_hash` |
| `source_inputs.jsonl` | `key`, `base_group`, `base_id`, `case_identity`, `market_identity`, `market_kind`, `source`, `source_plan_hash`, `selected_movements`, `source_plan`, `source_replay` |

The ordinary exporter defines those fields at
[case emission](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:145),
[common source identity](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:200)
and [source emission](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:248).
The composite shard00 exporter adds `origin_attempt`, `origin_job_id` and
`evidence_class` to source rows
([composite emission](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_composite.py:151)).
They are not necessary for target-support analysis and should not broaden access
or cause rejection merely for being extra fields. No referenced path is followed.

## Stored case: the common physical universe

`case` is the stored dataclass dictionary. Its complete identity-bearing fields
are `name`, `trips`, `movements`, `resources`, `market_edges_min`, `depot`,
`max_vehicles`, `battery_kwh`, `reserve_kwh`, `terminal_open_min`,
`recharge_deadline_min`, `vehicle_cost`, `deadhead_cost_per_min`, `efficiency`,
`graph_scope`. Each trip has `id,start_min,end_min,start_place,end_place,energy_kwh`;
each movement has `id,kind,before,after,legs,depot_split`; each leg has
`origin,destination,depart_min,arrive_min,energy_kwh`; each resource has
`start_min,end_min,per_bus_kw,grid_kw,connectors`
([dataclasses](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:31)).

The checked inverse reader defaults only absent `depot_split=None`,
`deadhead_cost_per_min=0.0`, `efficiency=1.0` and
`graph_scope='declared-movement-modes-only'`; its Resource constructor also has
`connectors=1`. Preserve stored number types/values and ordering when reproducing
its dictionary identity, rather than coercing every number to float
([inverse API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:28)).
The actual candidate universe is the unique ordered `case.movements[].id`, with
its `kind` (direct/depot are flexible; pullout/pullin are boundaries). Neither
`selected_movements` nor the plan is a full candidate universe. Use that same
universe for both sources, and validate top-level group/base/case identity joins.
Stored `physical_profile.base_id/split` can be checked for internal agreement;
no call to regenerate a case/assignment is needed or authorized here.

## Plan membership and exact stored identities

The source plan's `vehicles` list has records containing `vehicle`, `trips` and
`movements`. The membership target is the flattened vehicle movement IDs.
`selected_movements` is independently stored as a sorted flattened list
([topology helper](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:41)).
Require unique selected IDs, membership in the stored case universe, and exact
set agreement with flattened plan membership; do not silently deduplicate a
malformed repeated movement. A source plan also contains charges/load/ops and
possibly formulation, extraction, roundoff, replay and raw-load fields
([plan encoding example](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:402)).
Those values are not needed for cost/energy analysis and must not be exported or
analyzed in this audit. `source_replay` is present but unnecessary: do not inspect
it as a teacher quality or feasibility certificate.

The exact shared digest convention is
`sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()`:
Python defaults for separators/ASCII must remain, not compact JSON or a new
canonicalizer ([digest](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:101)).
`case_identity` hashes `{'schema':'egg-native-recharge-v1','case':asdict(case)}`
([case identity](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:87)).
`source_plan_hash` covers the **whole stored source_plan**, including any extra
identity-bearing plan fields, not a membership-only whitelist projection. Its
byte serialization is only for a declared digest check; it does not authorize
semantic inspection of charges/replay/costs. The original loader performs these
identity and membership comparisons
([source reader](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:63)).
These checks establish internal stored-contract consistency, not physical replay,
optimality or actual historical generator/teacher execution.

## Tariff fields that are absent, and the bounded identity check

`source_inputs.jsonl` contains `market_identity` and `market_kind`, but **no stored
numeric market a/b arrays**. The loader reconstructs the source market and checks
that identity; source names alone are insufficient. The existing Market identity
hashes `{'name':case.name+'-'+source,'a':a,'b':b}`
([Market identity](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:22)).
The source API defines30 a/b periods: source0 a=.20 throughout; source1 a=.10 in
zero-based periods18–21 and .30 otherwise; both b=1/900 throughout
([fixed market API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191)).
Require `market_kind==source`, the expected grid length, and the canonical
identity match before reporting source-bound a-difference/b-equality. Constructing
this fixed market dictionary is not regenerating a physical case or solving a
teacher. The stored identity binds to the source-defined market; it is not a
new observation of an explicitly stored numeric tariff or a real-world market.

## One-pass access and denominator contract

The two selected tables are mixed TRAIN: a whole-file SHA256 admission pass reads
all TRAIN bytes, including non-FIT lines. It must not be described as FIT-only
byte access. Recommend **one streamed pass per table**, hashing original line
bytes once and using the same line buffers for selection, with file/line caps
and resource checks fixed by the parent before execution.

An ordinary `json.loads` transiently decodes the whole row before its top-level
group can be consulted. Parent must explicitly authorize that routing decode.
For non-FIT rows, consult only the allowed top-level routing IDs and immediately
discard the object; no semantic inspection, comparison, export or persistent
retention of non-FIT case/plan/label values. Do not add a custom partial parser,
index, extra scan or substring routing framework. Do not analyze or publish FIT
results unless the completed original-byte stream matches its prebound digest.
Partial findings on failure stay marked incomplete, not admitted support.

The fixed design remains80 FIT groups,79 expected complete source pairs,
159 sources, with10037/source1 only. The two selected FIT lists must agree;
do not select their intersection after seeing differences. Preserve missing,
duplicate, foreign or inconsistent rows as contract findings without replacement.
Group-level disagreement summaries use the79 expected paired groups, keep the
one missing comparison separate, and never treat all movement rows as independent
replications. IDs/membership are the allowed target information; do not score,
fit, replay, regenerate labels or fetch teacher outcomes.

Parent's provision direction is one process, observed5GiB, at most5 CPU minutes/
10 wall minutes inclusive; actual body/publication/closure limits and exact
command remain parent freeze items. This source contract is not launch clearance.
