# Frozen-model transfer to independent timetables

This prospectively frozen development campaign tests the existing stage-2
EdgePrior on two independent synthetic timetables. New seeds 2018 and 2019
have 20 and 28 services, respectively, with fresh physical and market
identities. They are absent from stage-2 training and development labels.
The old reserved test groups 2004/2005 remain untouched; seeds 2020
(20 services) and 2021 (28 services) are additionally reserved for future
size-matched tests, without materializing their cases, features, tariffs,
or labels here. No A6, B3, protected, private, or held-out data enter
this attempt. The exclusive output is
`result/learning_campaign/20260930-transfer-attempt1`.

The serial order is fixed before execution. Both groups' `source0` and
`source1` native cells run first (four cells). One CPU-only inference call
then loads the exact frozen stage-2 model and reads only those source
catalog rows plus the frozen target market/case design. It writes two
immutable replayed proposals and a receipt before *any* target cell
launches. There is no fit, label update, or dev cold target read. A failed,
timed-out, or interrupted inference is receipted and never retried after
target outcomes. Only the projected `learned` native arm requires a
successful proposal receipt with a matching output hash; independent
native controls still run. The shared learned repair arm uses the valid
frozen EdgePrior directly and does not depend on source-pool projection. Then,
for each group in seed order, five target native arms run:
`cold`, `retained`, `nearest_price`, `cheapest_bill`, `learned`.
Two shared-interval route-repair arms follow: `shared_cost_only` and
`shared_cost_learned`. This is 9 cells per group, 18 total.

Native source and target cells use the same 70-second GRB hull budget,
one thread, oracle, and QP policy as stage 2. Cold imports no fleet.
Retained imports all independently replayed source columns. Nearest-price,
cheapest-bill, and learned use the same one-best-plan-per-source pool.
Cheapest-bill compares exact nonlinear target objectives; learned predicts
edge topology and projects onto a same-case replayed source fleet.
The proposed fleet is imported as a feasible-pool candidate, with a
fresh target-native certificate. Source bounds never transfer to the
target market. The model and source pool acquisition have distinct
receipts and timing from online inference and native target solving.

The repair arms use the same frozen EdgePrior for `shared_cost_learned`;
`shared_cost_only` performs no model-logit inference. One 30-second
HiGHS cover jointly limits route SOC, individual charging windows, and
shared interval grid energy. A cover is still a proposal: fixed-route
GRB charging/SOC and independent native physical replay are mandatory.
New replayed fleets enter a fresh one-column target hull check. Failed
repair falls back only to the independently replayed pre-target cheapest
source fleet and skips a redundant hull; it never uses a target cold or
learned final incumbent as its fallback. Both control outcomes are
read only for comparative reporting after their own target runs.

Every cell preserves its raw result, status, bounds, feasible plan, exact
cost, elapsed time, failure type, and immutable child receipt. The
append-only catalog records all 18 outcomes; a replayed incumbent after
a time-limited or failed solver remains feasible but its optimality is
unknown. Inference failure is receipted and does not suppress cold or
other native controls. Acquisition, inference, direct source-plan replay
and exact target rescoring, selection, cover,
charging, independent replay, pool preparation, and native hull times
remain separate. Primary endpoints are exact target costs and bounds,
new repaired-plan feasibility, and fully paid online time against cold,
retained, nearest, and cheapest controls. Two development groups are
transfer evidence, not a general ML speedup or test-set claim.

Fourteen native cells have 100-second hard child caps, four repair cells
have 240-second caps, and frozen-model inference has a 45-second hard cap.
The sum of child caps is 2,360 seconds, below the 3,000-second controller
launch guard; the external shell cap is 3,300 seconds. The Slurm request
is one CPU, 8 GB, 60 minutes, one solver thread, no requeue, and exclusion
of `scaglione-compute-01`. Requested and allocated CPU counts are both
receipted. The exclusive controller lock and immutable per-cell receipts
permit safe skipping of completed cells; an interrupted unreceipted cell
halts automatic resume. Freeze pins execution commit, source hashes,
stage-2 model/catalog/receipts and source selections, exact group split,
case/market identities, witnesses, order, budgets, and runtime/native
probe. Scientific admission remains pending independent review.

Pure local checks use synthetic case replay and mocks, without a native
optimization run:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_transfer_campaign.py src/tests/test_learning_campaign_stage2.py src/tests/test_route_repair_pilot.py
bash -n src/cluster/transfer_campaign.sbatch
```
