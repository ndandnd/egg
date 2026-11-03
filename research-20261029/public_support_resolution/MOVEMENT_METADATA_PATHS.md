# Public rich-metadata path discovery

Bounded source/path discovery only. No original timetable/OD values, plans, actual rich JSON contents, hashes, imports, rebuilds, tests or native work were consumed. Reads were narrow writer/adapter/launch source, the earlier compact source-admission manifest and Git path/revision metadata.

## Available candidate public input

The existing rich public artifact is:

    data/public/sistig_26088190_v1/hildenbrand_native_cases.json

Git path metadata confirms it exists at the earlier public-support source revision `2f386362aa241a8a4f197a88a50fa150b6d47d9c`, together with its constructor `src/experiments/sistig_native_case.py`. The last path-changing commit reported by narrow Git metadata is `f549100587cdf561c978e145e73e86dbadc9f27e`. A prospective freeze may use the former exact revision/path pair, conditional on paid byte admission; this note has not read or compared that committed content.

The earlier source-defined worker input pin and compact `research-20261029/public_support_resolution/attempt01/source_admission.json` agree on this public file's recorded size8046032 bytes and SHA256 `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`. These are transcribed existing metadata, not newly computed hashes. That historical worker checked the input hash, not its input Git revision. Future admission must therefore bind the chosen exact commit bytes and this prior input identity rather than assume path existence proves equality.

No original archive, spreadsheet, private input, sealed bank or unrelated operator input is needed for the proposed metadata extraction. The old raw witness path listed beside this file in historical admission is unrelated and must not be consumed.

## Source-defined retained fields

Constructor `src/experiments/sistig_native_case.py` retains these relevant paths in the rich JSON:

| Required field group | Exact schema path / writer |
|---|---|
| Complete location/OD order | `source_data.deadhead_stop_order_source`; public source parser builds the matrix-stop order. |
| Full directed OD arcs | `source_data.deadhead_arcs_directed_row_major[]` with `origin_stop_id`, `destination_stop_id`, `distance_m_source`, `time_sec_source`, `height_difference_m_source`; parser loops over every ordered matrix pair. |
| Location/depot flags | `source_data.stops[]`, including source ID and `b_depot`; `build_depot_variant` uses these flags and selected depot identity. |
| Native service mapping | Unique depot15 entry in `native_cases[]`, selector `selected_depot_id==15`, with `trips[].native` and source/modeled service provenance. |
| Modes and leg provenance | That selected variant's `movement_modes[]` and `movement_provenance[]`; latter includes leg role/source distance, source arc references and canonical departure/depot-gap policy. |
| Energy and charging assumptions | Selected variant `energy_model`, `charging_model`, `resource_policy`, `cost_policy`, `initial_inventory_policy`, `terminal_policy`. |
| Explicit horizon/timing | Selected variant `availability_horizon_sec`, `time_representation`, `market_edges_min`; top-level `modeling_assumptions.time_horizon`, `terminal_open_sec`, `departure_policies`, `depot_idle_auxiliary`, `direct_wait_policy`. |
| Public origin/units | Top-level `dataset`, `source_archive_provenance`, `source_field_semantics`; writer labels public adapted data and synthetic energy/cost fields. |

`json_ready_source` removes only internal lookup indexes and parsing scratch timing/native-ID fields; it retains matrix order/arcs and stops. `build_document` places that result under `source_data` and all declared variants under `native_cases`. `build_depot_variant` writes the richer per-mode provenance, energy model and availability fields. The public-support adapter then intentionally strips these when forming NativeCase/asdict; this explains their absence from the smaller certified descriptor without implying they are unavailable in the archived public input.

## Prospective scope and stop conditions

Parent may separately freeze one metadata-only consumer of the exact public file plus its constructor/policy source and the already admitted depot15 descriptor. Decode the complete cached buffer only once, select shared public OD/location metadata and the unique depot15 variant, and project only the required fields. Do not inspect depot16 variant data, unrelated operators, retained plans or source archive bytes. Never follow paths embedded in the rich data. The constructor/schema finding is not proof that all actual fields are present or satisfy any property.

Require the frozen buffer identity, unique depot15 selector, complete field/ID mappings and exact numeric semantics before triangle/coverage/window predicates are attempted. Missing required fields or inconsistent mapping is UNKNOWN/FAILED, not an inferred triangle or a regenerated mode. This path discovery identifies a viable archived PUBLIC metadata source; whether it passes OD triangle dominance, canonical completeness or exact stored-energy comparisons remains entirely unexamined. Execution/resources/command and any mathematical scope extension still require parent review and separate freeze.
