# All-declared-mode capacity outer cuts — frozen attempt01

Prospective parent decision: execute one reviewed analytical attempt, after its source/protocol/manifest backup is pushed. No artifact values, data, imports, compilation, hashes, tests, replay or solves were accessed/performed while writing/reviewing these files. The earlier capacity diagnostic and resource packages are CLOSED and cannot be repeated under this namespace.

## Exact eight-file authority and binding

The only future artifact inputs are `external-receipt.json` and `spec.json` in each of:

- `resource_recourse/attempt01/001-acquisition`: group10001,20 services,p90,ordinal1;
- `resource_recourse/attempt01/004-acquisition`: group10006,20 services,p90,ordinal4;
- `resource_recourse/attempt01/005-acquisition`: group10009,28 services,p90,ordinal5;
- `resource_recourse/attempt01/008-acquisition`: group10005,28 services,p90,ordinal8.

All are below the fixed `research-20261025` worktree path. Never follow a data-provided path. In the future metered batch, read/hash each external receipt once and project only `spec_sha256,folder,task_id,ordinal,phase,group,base_id,services,grid_kw`. Do not inspect worker/native statuses, cost/bound fields or artifacts it references. Check the fixed metadata. Then read/hash that folder's spec buffer once, require its SHA256 matches the external binding, and only then decode/project the spec.

Require the projected trip-list length to equal the fixed service metadata. Retain `expected_case_identity` in `group_bindings` as an inherited token only, without recomputing it. Binding/projection failures preserve their permitted exception type/message so missing/schema/integrity problems remain diagnosable.

Permitted spec semantics are `root,task_id,phase,group,base_id,services,grid_kw,fleet_N,expected_case_identity,case`. Within case, inspect only depot/schema graph context, trip `id,start_min,end_min,energy_kwh`; movement `id,kind,before,after,depot_split`, leg `origin,destination,depart_min,arrive_min,energy_kwh`; battery/reserve/efficiency; terminal opening/deadline/market horizon; resource intervals, powers and connectors. Full JSON decoding is transiently allowed for this exact projection. Never inspect reference-selected IDs, original/acquisition plans, charges/loads, prices, operations/vehicle/deadhead costs, models or other files. In particular, **do not reconstruct/hash a whole case identity** by reading excluded costs. The validated case identity/provenance is inherited from the bound closed spec; only its metadata syntax and authorized structural fields are checked here.

Trip/movement IDs are local incidence keys only; no ID/route/window vectors are exported. Output only four group contexts at90/45, scalar counts, energy lower bounds/capacities/exact margins, assumptions and unknowns. Missing incidence/start/end minima remain structural-unavailable, not invented finite values or a global feasibility claim. Independent minima do not prove a fixed-N complete route cover exists; universal bound statements are conditional on the inherited declared full-coverage model.

## Frozen algebra and assumptions

Use nonnegative individual trip/leg energies exactly as represented. Validate declared kind/before/after incidence and chronological leg/service timing; retain every parallel mode.

`Fraction(float)` means exact arithmetic on the stored binary floating-point coefficient. It does not recover an intended decimal/rational parameter or remove stored-model/replay numerical qualifications. Compute:

`L_in=sum_trip min incoming_mode_energy + N*min pullin_energy`,

`L_out=sum_trip min outgoing_mode_energy + N*min pullout_energy`,

`D_LB=sum trip_energy + max(L_in,L_out)`.

Never sum both movement bounds: they partition the same selected route movements in two ways. N is positive canonical bound-spec metadata, not inferred from costs/plans or claimed minimal.

From every declared depot mode's valid split, clip its window to[0,1080), union all windows once, including mutually incompatible alternatives, and integrate shared capacity over actual resource intersections. Do not multiply by N or sum overlapping window capacities. Source p90 per-bus90/one-connector resources are retained, with only grid changed to90/45. Post-opening capacity integrates the entire[1080,declared deadline] horizon, not only terminally available buses.

Assume full initial/terminal batteries, reserve at opening, nonnegative unmodeled-free consumption, constant eta in(0,1] and no terminal charging before1080. With K=B−reserve>0, total grid demand is at least D_LB/eta. The lower bound `max(0,D_LB/eta−C_post)` does **not** require all demand before opening. The full SOC term `max(0,(D_LB−N*K)/eta)` applies only if every mandatory trip end and every declared leg arrival is≤1080. Otherwise use only completed mandatory service energy S_h in that SOC expression, conditional on the explicit reserve-at-opening assumption. If that assumption is unset, retain the total-energy term and mark the SOC term unknown. No custom movement-prefix, subset, matching/mincostflow or optimization expansion is included.

Compare C_pre with the maximum of the justified SOC and total-energy terms. Exact negative margins exclude the **stated ideal assumptions at fixed N in the admitted declared movement universe**; they are not tolerance-qualified stored-model/native/unrestricted-EVSP certificates. Nonnegative margins leave feasibility unresolved. Do not relabel INF_OR_UNBD, invalidate an old accepted witness, relax tolerances, add fleet/modes, change caps, repair a plan or infer ML/optimality value. Preserve discrepancies/unknowns and all8 paired controls.

## New resource package and gate

Separate allowance30CPU/60wall, body25CPU/50wall plus publication/exit5CPU/10wall; one isolated standard-library process/thread, no children/native/project imports. Parent adopts the retained tracking prefix19811.37 and this new allowance (reservation end19841.37), preserving the separate legacy conditional guard2546.091499549272 and UNKNOWN historical actual review CPU. It is not charged to/reopened from a closed resource package. Manifest is FROZEN/PASS; the script still denies before artifact input for an unreviewed/unfunded state. Existing external receipts at closed backup13de4822 bind the literal spec buffers; their SHA256 checks occur only once in this metered attempt.

Exact command, from the worktree:

```sh
/usr/bin/time -p -o research-20261025/all_mode_capacity/process-time.txt .venv-local/bin/python -I -S -B research-20261025/all_mode_capacity/run.py > research-20261025/all_mode_capacity/stdout.txt 2> research-20261025/all_mode_capacity/stderr.txt
```

The existing body check also limits the observed self RSS high-water to5GiB. `ru_maxrss` is recorded in bytes on macOS, with KiB converted to bytes on other platforms. This is a self-observation/check, not a memory-containment claim or a new monitor.

Fresh exclusive `attempt01` and false placeholder preserve any failure without retry. Source/protocol/manifest plus the eight fixed buffers are each hashed once within the future metered batch; no old-source hash audit. Output `attempt01/receipt.json` and stdout only. Prepublication resource observations leave startup/write/exit acceptance and actual cumulative charge to the external meter/parent. No automatic numerical execution follows from implementation or an ideal-cut sign.
