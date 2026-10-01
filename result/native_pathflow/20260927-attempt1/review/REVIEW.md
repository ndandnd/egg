# Independent compact path-flow first-attempt audit

**PASS for all 20 prospectively frozen synthetic qualification controls.** The
16 feasible controls have independently checked certificates; four controls
are independently infeasible. This audit imported no author model, adapter,
pricing or replay module and executed no optimizer. It reconstructed the
compact matrix and selected-path ownership from raw variable snapshots, then
used the previously independently authored fixture/physical-replay core.

The compact module was authored by the principal researcher; this audit was
performed by the native-hull implementation agent. That agent authored the
older vehicle-indexed native model, so the older-model equivalence argument is
an author-consistency review. The copied independent physical/fixture core was
written by the separate independent reviewer and remains unchanged. This is
not a claim of independence from every earlier part of the project.

## Provenance and reproducibility

- Frozen compact source: `ebb146e9de01d0c6aa13b03eb2348337a1d0b3f0`.
- Raw manifest SHA-256: `2ab225a5b79cf278c5ef55c834ba835a65126f09f370b9b967e5fac8a2f5327d`.
- Compact auditor: `audit_native_pathflow.py`, SHA-256 `766b14a5bfc26f6cad13648521521508f70fa8ca454faab4938407c618df9424`.
- Unchanged independent core: `independent_fixture_core.py`, SHA-256 `823eb1e19ca4795c9fe057448913467110bb9c6234adf9e84bcb2ade1d860729`.
- Detailed report: `audit-report.json`, SHA-256 `560caf8d0e48789a7b76749f6ba422d64a118d30a38edd79e84a9074db6a4de8`.

All 142 original raw files match their manifest size/hash before and after the
audit, and no unmanifested original evidence file is present. The short frozen
label matches the full manifest commit. Every declared source dependency was
read from that commit and checked against its frozen hash. All original 19
case/objective/target definitions exactly match the preserved timing gate; the
new three-service control is checked separately. The audit writes its execution
report to an exclusively new temporary path; only copies/review notes are
placed in this `review` subdirectory.

To repeat the read-only audit, use the local research Python with the script
path and an unused `--out /tmp/...json` filename. The helper imports only the
standard library and its colocated independent core. It uses read-only Git
object access for frozen source verification. There is no native solve.

## Checks and results

| Quantity | Audited value |
|---|---:|
| Preserved controls | 20 |
| Certified controls | 16 |
| Independently infeasible controls | 4 |
| Native starts/returns | 35 / 35 |
| Native statuses | 31 OPTIMAL; 4 INFEASIBLE |
| Independently minimized native objectives, including planner tangent rounds | 31 |
| Complete raw incumbent snapshots | 31 |
| Raw variable values reconstructed | 589 |
| Physical witness instances | 31 |
| Charging sessions independently checked | 68 |
| SOC events independently checked | 252 |
| Deliberate corrupted copies rejected | 25 |

For every raw incumbent, the auditor checks all flat variable mappings and
bounds, binary integrality, one incoming/outgoing movement per service, fleet
path cap, matching pullout/pullin counts, service SOC equalities, every active
and inactive big-M movement row, depot arrival reserve/charged inventory,
terminal reserve/full restoration, activation of each eligible mode-interval
energy variable, fleet-wide interval capacity and market aggregation. Native
physical/objective row counts, integer/continuous dimensions and the raw native
objective are reconstructed. The largest measured raw row/bound residual is
`4.134470543704083e-12`, below the fixed `1e-8` raw audit tolerance.

The selected graph is independently traversed from each pullout; all mandatory
services and selected modes belong to exactly one recovered path. The recovered
paths must equal the extracted plan. Every strictly positive charge is attached
to its selected mode's recovered path. The normalization and cumulative-energy
endpoint construction are recomputed using exact binary rational arithmetic,
including every interval/session capacity residual and objective change.

There are no corrected negative energy variables in this attempt. Five
incumbents have a nonzero materialized capacity-roundoff ledger; the largest
combined correction is `7.105427357601002e-15` kWh, below the declared `1e-8`
kWh fleet budget. The independent physical checks enforce native availability,
strict single-connector session nonoverlap, resource energy, service/movement
exclusion, complete service coverage, grid/battery conservation and full
replenishment. The maximum SOC residual is `1.4210854715202004e-14` kWh.
These remain numerical feasibility statements under the stated tolerances,
not an assertion of exact physically repaired floating witnesses.

Each planner tangent snapshot is checked against the exact saved tangent
history, and the fixture-specific PWL objective is independently minimized over
the complete analytically derived feasible branches. The native lower bounds
and primal values agree with those minima within the fixed audit tolerance.
The pricing objectives are independently minimized over the same complete
physical branches. Every successful final enclosure contains that exact
stored-coefficient fixture optimum. Certificate widths range from
`1.9999867078013267e-6` to `2.0199999983816497e-6`, below the unchanged `1e-4`
criterion. No incumbent is substituted for a global lower bound.

## New multi-visit control

The one-bus cap and declared graph force the path
`out_A → depot_AB → depot_BC → in_C`. All three services are mandatory. The
selected legs consume 12 kWh and the services consume 24 kWh, so total battery
energy is 36 kWh. Driving-leg time is 60 minutes. Under the protocol's exact
decimal efficiency 19/20, full restoration requires 720/19 grid kWh; intrinsic
cost is `7 + 0.5*60 = 37`, and flat-price objective is `1423/19`.

A separate constructive allocation (10 grid kWh in the first depot visit, 10 in
the second, and the remaining terminal energy) proves feasibility within the
stated SOC/resource limits. All feasible one-bus schedules have the same total
energy and intrinsic cost at flat prices, proving global optimality without a
second optimization. The binary-float efficiency stored in the case is used in
exact audit arithmetic; its objective differs from the declared decimal target
only at ordinary representation scale and is enclosed by the native certificate.
This control exercises one physical path with two multileg depot visits,
positive reserve, efficiency below one and nonzero movement-time cost.

## Limits

This is a software/physics/certificate qualification on fixed synthetic
controls. It does not establish full 37-service runtime, public-timetable
optimality, economic realism, better solver performance than the indexed
formulation, or journal-level operational evidence. Integer-set equivalence is
supported by the separate proof; identical LP relaxations or runtime were never
claimed. The compact algorithm is now eligible for a separately frozen bounded
public-input admission protocol, preserving all services and declared modes.
