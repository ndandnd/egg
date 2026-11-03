# All-mode outer cuts: two fixed-fleet ideal exclusions

The single source-bound attempt01 closed with exit0 after freeze c2b2006b was
pushed. All four external/spec bindings and all eight resource controls were
admitted. No solver, replay, original TRAIN, plan, cost, price or model was used.
No retry or extra formatting/export pass occurred. Exact fractions in
attempt01/receipt.json are primary; the figures below are rounded descriptions.

| Group | Trips | Fixed N | All-mode early union, minutes | Capacity at45, kWh | Required early grid lower bound at45 | Finding |
|---|---:|---:|---:|---:|---:|---|
|10001|20|3|274|205.5|0|No detected violation|
|10006|20|5|233|174.75|about77.5|No detected violation|
|10009|28|4|399|299.25|about390.4|Ideal shortfall about91.1kWh|
|10005|28|3|395|296.25|about326.0|Ideal shortfall about29.7kWh|

All declared trip and leg consumption completes by opening1080 in every admitted
projection. The SOC-at-opening lower bound controls10009/45; total minimum demand
minus the entire post-opening resource capacity controls10005/45. Both use the
maximum of two movement-energy partition lower bounds, not their sum. Every
declared depot mode contributes to the charging-window union, even if mutually
incompatible with other modes. Thus the cut gives route choices more freedom
than a real route collection, while using an optimistic demand lower bound.

The exact capacity-minus-required margins for the two violations are:

- 10009/45: -5910524150961036721/64851834634135144 kWh;
- 10005/45: -481614944151000139/16212958658533786 kWh.

All four90kW controls have no detected violation. Neither known feasible45kW
control (10001 and10006) is contradicted. There are four exposed physical groups,
not eight independent cases or repeated tariffs as independent replications.

Under the stated ideal assumptions, neither failed28-trip case can be rescued
merely by choosing another collection of declared routes at its frozen fleet N.
This is stronger than failure of the original topology or a bounded search. It
does not reclassify the recorded native INF_OR_UNBD, certify the native tolerance
model, exclude additional buses/modes/resources, or prove unrestricted EVSP
infeasibility. Exact binary-coefficient arithmetic does not establish numerical
robustness outside that ideal scope. Passing the outer cut is not feasibility;
the existing operational witnesses remain separate evidence for the controls.

The earlier10006 result remains the useful routing-access witness: the reference
topology violates its selected-window cut, while independently replayed rerouting
restores operation despite greater energy use. The two new exclusions explain
why that contrast cannot be generalized to every reference failure. No complete
resource-cost mean is recovered; the earlier mean remainsNULL. No learning gain,
new theorem, population result or model promotion follows.

External meter:0.07 displayed CPU/0.09wall seconds, retained phase charge0.09CPU
for rounding; one isolated stdlib process, observed self peak23,658,496bytes.
See FINAL_RESOURCE_RECEIPT.json. This package is CLOSED and must not be rerun.
