# Prospective native input authority — frozen scope

This fixes `data_authority`, `environment` and `mixed_integer_parameters` under NATIVE_ADOPTION_DECISION.md. Row access/dispatch is STILL denied until source preparation closes and parent commits FROZEN/PASS main control with accepted actual preparation costs. NATIVE_PREPARATION_FROZEN/SOURCE_PINNED do not run main. No tables, cases, plans or outcomes were read to prepare this authority; no import, replay, test or solve was executed. Selected identities come only from the completed metadata-only receipt.

The fixed selected groups, in order, are `physical_v2_s10007` (20), `physical_v2_s10013` (20), `physical_v2_s10017` (28), `physical_v2_s10021` (28). No replacement. Both target contexts use the same original physical case and source0 fleet count/plan; source1 is a target tariff derived from the unchanged pure market mapping, not a second teacher-plan input.

## Literal files and byte/routing scope

Only these two TRAIN streams may supply original numerical inputs:

| File | Existing declared whole-byte SHA256 |
|---|---|
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl` | `faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6` |
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl` | `7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5` |

These are copied declarations from [the earlier source protocol](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/catalog_coherence/PROTOCOL.md:10), not a new verification. Future owner preflight hashes each stream's bytes once while streaming it, checks the pin and stable file metadata before physical admission, and uses its existing 512-MiB file/16-MiB line bounds. Whole-byte access necessarily includes nonselected/source1 bytes. `json.loads` transiently decodes each complete line; only top-level `base_group` and, for source-input routing, `source` are consulted before nonselected or non-source0 objects are discarded. Do not inspect, retain, export or compare their nested semantics. No referenced path is followed. This is selective semantic access, not selected-only byte/decode access. See [literal reader](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261026/economic_recourse_pilot/run.py:218).

Selected `cases` top-level whitelist is exactly `base_group,base_id,split,generator,physical_profile,case_identity,case`; selected `source_inputs` whitelist is exactly `base_group,base_id,source,case_identity,market_kind,market_identity,source_plan_hash,source_plan`. The owner's descriptor has exactly `path,sha256,fields`; nested authority is defined below, not by adding unsupported descriptor keys.

## Selected stored case and context

`case` is the complete original NativeCase physics and economic coefficients: `name,trips,movements,resources,market_edges_min,depot,max_vehicles,battery_kwh,reserve_kwh,terminal_open_min,recharge_deadline_min,vehicle_cost,deadhead_cost_per_min,efficiency,graph_scope`.

- `trips[*]`: `id,start_min,end_min,start_place,end_place,energy_kwh`.
- `movements[*]`: `id,kind,before,after,legs,depot_split`; each `legs[*]`: `origin,destination,depart_min,arrive_min,energy_kwh`.
- `resources[*]`: `start_min,end_min,per_bus_kw,grid_kw,connectors`.
- `physical_profile`: `base_id,split,services,profile,consumption_kwh_per_km,depot_min_gap_minutes,duty_start_stride_minutes,speed_kmh,idle_kw,depot_dwell_idle_kw,resource_grid_kw,resource_bus_kw,terminal_open_min,deadline_min,efficiency`; nested `profile`: `name,nameplate_kwh,upper_kwh,reserve_kwh,operating_span_kwh`.

Use the owner's stored-dataclass constructor, preserving array order, represented coefficients and declared defaults; unexpected constructor fields fail. Validate rather than generate: original case identity, pure `physical.assignment(base_id)` profile and actual 20/28 trip count, TRAIN/generator identity, exactly the original resource `(0,1800,90.,90.,1)`, and grid edges `0..1800` by60. No name, battery, resource, timing, coefficient or horizon modification. Source definitions: [NativeCase and nested dataclasses](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:31), [profile and constructor reader](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261026/economic_recourse_pilot/run.py:249).

The selected source0 row must join the case/base identity, declare `market_kind=source0`, match the pure source0 market identity and whole source-plan digest, and pass full physical replay/canonical path recovery. Derive targets only using unchanged `physical.market(stored_case, source0/source1)`: source0 `.20` all30 periods; source1 `.10` at18–21 and `.30` otherwise; both curvature `1/900` and stored-case grid. No generation and no source1 teacher-plan read. See [pure tariff mapping](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191).

## Original source0 physical plan, not cached outcomes

Retain the original whole `source_plan` dictionary unmodified for canonical digest, physical witness input and protected fallback. Whole-plan hash-only traversal may include auxiliary fields; a reduced projection would not reproduce `source_plan_hash`. Semantic physical reads are limited to `schema,case_identity`, `vehicles[*].vehicle/trips/movements`, `charges[*].vehicle/movement/connector/start_min/end_min/grid_kwh`, `load`, and `ops_cost`.

Here `load` and `ops_cost` are mandatory stored **consistency assertions** checked by unchanged replay against recomputed load and operations; they are not accepted as cached outcome values. Charge/resource/SOC/service coverage, per-period loads and cost are independently recomputed under unchanged tolerances. Preserve the original witness; do not erase assertions or alter sessions. Missing/mismatched fields reject admission, not repair. See [unchanged replay](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:240). Extra `source_plan` fields such as `raw_solver_load`, `raw_charge_load`, nested `replay` or `roundoff` remain opaque except for whole-plan hashing/transport. Exclude separate row `selected_movements`, `source_replay`, cached cost/load/outcome/native/performance fields; obtain selected IDs only from the physical vehicle paths. No source1 plan, labels, weights, old performance, outcome tables, DEV/TEST/sealed data or raw native rows enter this pilot.

## Existing local runtime and parameters

The prospective owner and child use the existing worktree `.venv-local/bin/python`; exact parent command is separately frozen, and children use that owner's `sys.executable`. No `-S` is proposed for solver work. The literal owner environment contract contains exactly `OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS,VECLIB_MAXIMUM_THREADS,NUMEXPR_NUM_THREADS,BLIS_NUM_THREADS`, each string `"1"`; runtime path is not an extra environment-map key. Native Threads1/Seed17 and parent-before-Popen52/60 clocks remain unchanged.

`mixed_integer_parameters` is copied manually from new `miqp_control.PARAMETERS`: Threads1, Seed17, Method0, NodeMethod0, NonConvex0, MIPFocus0, FeasibilityTol/IntFeasTol/OptimalityTol each1e-9, BarConvTol1e-10, MIPGap1e-9, MIPGapAbs1e-6. The worker requires exact dictionary equality before spec read. API/parameter readback can still fail at the first native composition and must stop without retries; these declarations do not establish installed compatibility, optimizer precision or any physical/global certificate.
