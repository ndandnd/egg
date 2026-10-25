# FIT paired-target audit: identity and source contract

Static source map, 2026-10-25. No tables, metadata, weights or outcomes were opened; no imports, hashes, tests or solver calls were run. This specifies a prospective collector contract, not permission to execute it. The denominator remains **80 fixed FIT groups, 79 expected complete pairs, one incomplete group**; no new quality gate or replacement group is introduced.

## Canonical identities

`native_recharge.digest(value)` is exactly:

```python
hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
```

It uses default JSON separators (including spaces), default `ensure_ascii=True`, UTF-8 encoding and lowercase SHA256 hex. Sort dictionary keys only; preserve array order and parsed numeric types. Do not compact JSON, stringify numbers, round, convert every number to float, normalize signed zero, or apply tolerance. JSON encodes tuples/lists as arrays, but `1` and `1.0` have different serialized representations. This is a **semantic-object digest**, distinct from the SHA256 of whole JSONL file bytes. See [digest](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:101).

| Identity | Exact payload |
|---|---|
| Physical case | `{"schema": "egg-native-recharge-v1", "case": asdict(case)}` |
| Market | `asdict(Market(name, a, b))`, hence exactly `name`, `a`, `b`; **no hull schema or grid in this payload** |
| Source plan | Entire stored `source_plan` dictionary, unmodified, including any auxiliary/replay/roundoff fields already present |

Case and market methods are [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:70) and [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:22). The training loader explicitly compares `source_plan_hash` with `nr.digest(plan)` [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:69). Hashing a reduced plan projection cannot reproduce that contract. Hash-only traversal of the whole FIT plan is necessary; semantic inspection can remain restricted below.

## Stored case and source-kind market

Construct `nr.NativeCase` and its nested dataclasses from the stored case without regenerating trips, movements or resources. Preserve array order and numeric values. Exact dataclass fields are [defined here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:31):

- Case: `name, trips, movements, resources, market_edges_min, depot, max_vehicles, battery_kwh, reserve_kwh, terminal_open_min, recharge_deadline_min, vehicle_cost, deadhead_cost_per_min, efficiency, graph_scope`.
- Trip: `id, start_min, end_min, start_place, end_place, energy_kwh`.
- Movement: `id, kind, before, after, legs, depot_split`; Leg: `origin, destination, depart_min, arrive_min, energy_kwh`.
- Resource: `start_min, end_min, per_bus_kw, grid_kw, connectors`.

Defaults are `Movement.depot_split=None`, `Resource.connectors=1`, case `deadhead_cost_per_min=0.0`, `efficiency=1.0`, `graph_scope="declared-movement-modes-only"`. Reconstructing through these dataclasses makes default insertion explicit; do not simply hash an arbitrary raw case dictionary with omitted defaults or ignored extra fields. Unexpected fields/schema should be reported, not silently discarded.

`physical_learning_cases.market(stored_case, kind)` does not regenerate a case. For source kinds only:

- `source0`: `a=(.20,)*30`.
- `source1`: `a[h]=.10` for `18 <= h < 22`, `.30` otherwise, `h=0..29`.
- Both: `b=(1/900,)*30`, market name `stored_case.name + "-" + kind`.

Use the same Python float expressions; decimal strings or rational conversions would change the identity representation. See [market mapping](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191). The declared physical grid is `tuple(range(0,1801,60))`, separately [defined here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:33). Require the stored case grid to match and have 31 edges for these 30 coefficients; the market digest alone does not bind a grid. Compare each source's canonical market digest and physical-case digest with its stored identities. No `make_case`, `make_witness`, late/day/flat market evaluation or solver is needed.

## Exact prospective semantic field whitelist

Transient `json.loads` of mixed TRAIN lines is explicitly allowed **only for routing**; inspect `base_group` (and `base_id` if needed), then immediately discard non-FIT objects without semantic inspection/export. Whole-file byte hashing, if separately admitted, necessarily reads non-FIT bytes and must be labelled accordingly. Only the fixed two candidate files from the parent decision are in scope; no referenced paths are followed.

| FIT row | Semantically inspect |
|---|---|
| `cases.jsonl` | `base_group, base_id, split, generator, case_identity, physical_profile, case` with the nested fields above; exclude `witness_hash` |
| `source_inputs.jsonl` | `key, base_group, base_id, case_identity, market_identity, market_kind, source, source_plan_hash, selected_movements`; inside `source_plan`, only `schema, case_identity, vehicles[*].vehicle, vehicles[*].trips, vehicles[*].movements` for identity/membership/path-shape checks |

The complete `source_plan` object is additionally available to the canonical **hash-only** operation; do not inspect/export its charges, loads, costs, raw variables, nested replay or roundoff diagnostics. Exclude the separate `source_replay` field entirely from semantic analysis. No source/target outcome table, health file, native status, bound, objective or paid-time field is needed. The writer's case/source dictionaries are [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:145), [common keys](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:200), and [source export](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:249).

Require `base_group=f"physical_v2_s{base_id}"`, `split="train"`, `generator="physical-fleet-learning-v2-full-factorial"`, matching case/source IDs and unique `(base_group, source)`. The case's `physical_profile` is an assignment dictionary with `base_id, split, services, profile, consumption_kwh_per_km, depot_min_gap_minutes, duty_start_stride_minutes, speed_kmh, idle_kw, depot_dwell_idle_kw, resource_grid_kw, resource_bus_kw, terminal_open_min, deadline_min, efficiency`; `profile` contains `name, nameplate_kwh, upper_kwh, reserve_kwh, operating_span_kwh`. `physical.assignment(base_id)` is a pure registry lookup/calculation and can compare that profile without generating a case [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:52). Restrict its input to the already frozen FIT IDs.

The writer's `selected_movements` is a **sorted flattened list**, not a deduplicated set: `_source_topology` sorts every vehicle's movement list [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:41). The training loader later compares sets [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:76). The audit should explicitly detect duplicates, unknown movement IDs and list/plan disagreement before producing positive-set metrics. Preserve the original movement ordering for any binary vector; do not treat distinct parallel modes as one trip-pair label. Plan schema/case identity checks do not establish charge feasibility or exact service coverage; that would require separate replay, which is outside this support audit.

## Minimal existing APIs and limits

Static imports in `native_recharge`, `native_hull` and `physical_learning_cases` are stdlib plus those modules themselves. Their dataclass constructors, `digest`, identity methods, `market` and `assignment` are the small pure API set. `mip` imports in native modules occur inside solver functions, not these paths; no direct NumPy/Gurobi import is present in their module headers. This is source inspection, not a runtime import trace or a guarantee about external import hooks.

Do **not** reuse `physical_route_model_v3.load_pool`: it imports NumPy/sklearn, hashes/loads the full TRAIN pool and calls `make_case`. Do not import the dataset adapter merely for `_source_topology`: its header imports learned features, pathflow and benchmark/campaign modules. These are provenance references, not minimal collector dependencies. Their headers and loader behavior are [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:12) and [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:11). No generic parser/controller framework is warranted.

Unknown until admitted table checks: actual row shapes, canonical identity agreement, paired target differences and any mismatches with declared source availability. Even a passing support audit will not establish matched teacher randomness/search budgets, label optimality, tariff causality or proposal information value, nor repair missing GNN pool lineage. Preserve all findings and the one incomplete group; parent freezes actual input pins, field contract, code and command separately.
