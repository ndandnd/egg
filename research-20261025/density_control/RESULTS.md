# A conventional control reaches the exposed-case fleet targets

25 October 2026. The frozen four-decision density control completed once. All
four witnesses independently replay on the original full physical cases and
were durably recorded within their120-second clocks. No retry, quota change,
additional solve, learned asset or chosen historical plan was used.

| Case | Arm | Flexible K/M | Valid buses | Restricted native bound/status | Native solve | Whole decision | Evaluated system cost |
|---|---|---:|---:|---|---:|---:|---:|
|50685:40|CA1|429/1427|4|4 / OPTIMAL|0.344s|1.750s|778.166741|
|50685:40|Cover+CA1|429/1427|3|3 / OPTIMAL|0.197s|1.557s|655.818497|
|50605:80|Cover+CA1|1765/5882|5|5 / OPTIMAL|8.685s|20.393s|1293.759812|
|50605:80|CA1|1765/5882|5|5 / OPTIMAL|9.545s|20.888s|1287.147095|

Objective was vehicle count only. Costs in the last column are exact integrated
system costs evaluated afterward, not optimized bills; their differences do not
show economic or tariff-learning superiority. Each native result has a numerical
OPTIMAL status with the displayed arm-restricted fleet bound. These are not
unrestricted full-problem certificates or independently exact optimality proofs.

Both arms use the same original model and common backbone, exactly429/1765
flexible modes, all80/160 boundaries, native seed17, one native thread, original
SOC/shared charging physics, independently measured scoring/construction time
and unchanged replay. The original matrices contain20669/177958 columns and
23773/190037 rows. Only excluded movement upper bounds changed.

The cover arm preserves three fixed global covers then fills with CA1. Compared
with ordinary CA1 it substitutes47 of429 flexible modes on40 trips and only6
of1765 on80. Both count/common-contract and receipt comparisons passed. At40,
the different equal-size pools have different numerical restricted optima, so
candidate identity can matter beyond candidate count. This does not isolate one
cover component or identify the uniquely important movements.

**Competence:** Cover+CA1 meets both prespecified exposed targets of<=3/5 buses.
CA1 misses40 (4 buses) and meets80 (5). Consequently the aggregate all-four gate
is false, as preserved in summary.json, while a conventional arm is now eligible
for the next separately frozen comparison. This is a development competence
gate on two already exposed cases and one seed, not a robust classical benchmark,
independent generalization result, new algorithm, or learned-model comparison.

**What changed scientifically:** the sparse80-trip matching pool's24-bus result
cannot support a claim that conventional candidate generation is intrinsically
weak or learning is necessary. Matching covers plus predetermined fill now admit
five buses at the common30% quota; ordinary charging-aware scoring also admits
five. Different historical seeds/objectives remain unmatched, so no timing gain
against the old GNN or full-solver runs is estimated. Existing apparent ML gains
must now survive these competent conventional controls under a prospective
matched policy, shared feasible fallback and complete end-to-end accounting.

Whole native process:45.32s elapsed and43.51CPU seconds. Finalization/archive:
1.96s elapsed and1.89CPU seconds. Package45.40CPU seconds, peak observed native
process RSS501497856 bytes; within720CPU/600wall and separate60CPU/90wall budgets.
Cumulative measured reset numerical-process CPU206.31s. The separate historical
conditional guard stays2546.091499549272s and its actual review CPU staysUNKNOWN.
No whole-session exact CPU claim. All outcomes and original artifacts are retained;
large inventories/captures have lossless gzip archives and original stream hashes.

Read summary.json and RESOURCE_RECEIPT.json for compact details, not raw captures.
Next freeze a matched comparison protocol; do not immediately launch a sweep or
select a policy using independent evaluation outcomes.
