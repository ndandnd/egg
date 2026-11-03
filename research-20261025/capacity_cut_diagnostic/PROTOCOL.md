# Necessary preterminal capacity diagnostic — DRAFT

This is a separate prospective analytical package. The resource-recourse package and its compact readout are CLOSED; they are not reopened, rerun or renamed. No actual input read, hashes, imports, compilation, test or computation has been performed during this implementation.

The sole future numerical input is the fixed owned `research-20261025/resource_recourse/READOUT.json`. Standard JSON decoding transiently materializes that file; semantic analysis is restricted to the projection below. No case/spec/plan files, original TRAIN tables, charge sessions, loads, cost fields, scores, model assets or cached nested diagnostics may be accessed. No project imports, child processes or native optimizer/replay calls occur.

## Projection and denominators

- Eight reference records: `variants[*]` context `group,services,grid_kw`; original no-solve validity flag only; its direct `opportunity_diagnostics`. Reference acquisition context comes from `acquisitions[*]` admission/missing flags and native status labels only.
- Sixteen planned adaptive records: `active[*]` where `phase=adaptive`, context `group,base_id,services,grid_kw,target_source`, parent endpoint/physical/operational source/route-change/search/QP status and missing labels. Read only direct `operational_opportunity_diagnostics` when the parent accepted a worker's valid retained physical endpoint. An acquired-prior fallback is labelled and retained as a record but is **not substituted for an unavailable new-method topology**. An accepted unchanged route stays explicitly unchanged; it is not evidence of a new topology.
- Within each opportunity: `available`; `per_vehicle` local-join `vehicle`, `total_consumption_exact`, `ideal_grid_kwh_exact`, `no_midday_soc_margin_kwh_exact`, `last_pullin_return_min_exact`; `selected_depot_windows` local-join `vehicle`, `lo_min_exact`, `hi_min_exact`; `all_return_by_terminal_open`, `common_terminal_start_min_exact`, `common_terminal_capacity_grid_kwh_exact`, `total_ideal_grid_kwh_exact`. Movement IDs are never read. Missing/unavailable projection remains unknown.

Fixed metadata cohort is10001/10006 (20 services),10009/10005 (28); resource levels90/45; two target labels source0/source1. Always output all8 reference/16 adaptive records, including missing. Vehicles appear only as anonymous per-record ordinals. Do not output raw movement/window/vehicle-ID vectors or window endpoints. Resource/tariff copies remain grouped within four exposed groups, not independent observations. No available-only effect estimate or performance gate is introduced.

## Exact necessary cuts

Assume full initial batteries, reserve at final arrival, constant efficiency, nonnegative consumption, no draw after return, no terminal charging before `h=1080`, all returns by h, and the declared constant bus90/grid90-or45/one-serial-connector resources. These ideal assumptions are inherited from the previously admitted study, not newly verified by reopening cases.

For each bus use `D=total_consumption`, `E=ideal_grid`, `m=usable_battery−D`. If D>0, reconstruct eta=D/E in(0,1] and `ell=E*max(0,−m)/D`. Positive-demand buses must share eta and all buses the implied usable battery D+m. For D=E=0 with nonnegative m, ell=0; inconsistent/missing joins, zero/negative demand cases or assumptions produce unavailable, not a guess. Verify exported total E equals the bus sum; all per-bus returns must be≤1080 and exported common terminal start exactly1080.

Clip selected depot windows to[0,1080), union overlaps/touching intervals **within each bus**, then union again **across buses**. Do not sum overlapping capacities. With effective rate `p=min(90,grid_kw)`, each capacity is `p*union_minutes/60`. Necessary conditions are every `ell_v≤C(W_v)` and

`max(sum ell_v, totalE−exported_terminal_capacity,0)≤C(union W_v)`.

Output exact Fraction strings for lower bounds, capacities, signed margins and overlap durations/counts; negative margins are ideal necessary-cut violations. No epsilon is applied or relabelled as a physical tolerance. Nonnegative margins prove neither feasibility nor cause: headroom, earlier SOC prefixes and subset conflicts are not resolved. A violation beside an accepted witness preserves a discrepancy requiring assumptions/represented-scope interpretation; it does not revoke prior admission or repair anything. Reference cuts do not settle full-graph INF_OR_UNBD, global feasibility, route optimality, price causality or ML value.

## Fresh package and freeze

NEW total allowance20CPU/45wall, body15CPU/35wall, reserve5CPU/10wall, one stdlib process/thread, no children. The actual external meter includes startup/publication/exit and is authoritative for final acceptance/accounting. The script reports prepublication use and leaves external acceptance pending; an overrun/failure is preserved without retry. Parent prospectively charges this new allowance against the current cumulative tracking prefix; no historical budget reset/refund follows.

`LAUNCH.json` remains DRAFT/PENDING with tracking prefix unset. The script refuses before numerical input unless modeFROZEN/review_dispositionPASS, exact budgets/input and a parent-frozen prefix are present. Parent reviews source/projection and freezes one exact command. A fresh exclusive `attempt01` prevents reuse. Source/protocol/launch and the single consumed input byte stream are hashed once within that future metered batch; no original-source/asset hash loop. An optional preexisting expected input digest may be frozen, otherwise the consumed-byte digest is recorded without a second hash pass.

The only result is `attempt01/receipt.json` plus compact stdout. Unknown assumptions are findings, not failed scientific gates; administrative failure and complete planned denominators remain explicit. No automatic launch, retries, solver, subset enumeration, cap scan, prefix-cut expansion, refit or extra data admission follows.

## Parent version and funding freeze

The permitted READOUT.json is the immutable artifact committed at13de4822. No
preexisting raw SHA256 pin was available without a duplicate preflight pass;
record its consumed-byte SHA256 once inside this metered diagnostic. The exact
path/version, policy, projection and cohort are frozen here; no other artifact
may be substituted. Current closed prefix is19811.11 displayedCPU /
20406.06elapsed-sum /19811.31 retained trackingCPU. Reserve this separate20CPU/
45wall package prospectively; actual external time and rounding-aware retained
charge will be appended once after exit. The legacy conditional guard and
unknown old actual review CPU remain separate, without refund/reset.

The projection also admits only source policy/receipt-complete metadata for
artifact-kind validation. Context keys are checked against the fixed four groups,
two grid levels and two adaptive targets before opportunity projection; duplicate
keys are administrative errors. Missing planned records stay unknown. Process
exit0 requires administrative body completion, not all cuts available/nonnegative.
