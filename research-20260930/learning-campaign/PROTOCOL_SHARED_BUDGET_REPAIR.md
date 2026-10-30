# Shared-interval cover time-budget study

This fixed, two-cell development study changes one budget: the shared
interval HiGHS route-cover cap rises from 5 to 30 seconds for the frozen
28-service 2017 timetable. The prior shared-interval attempt produced
replayed four-bus repairs on both 20-service arms, but neither 28-service
arm returned an integral cover at five seconds. Both became archived
source fallbacks. No-incumbent at that cap is time censoring, not evidence
that a physical route is infeasible. The earlier shared-interval result
manifest and cell CSV are source-pinned as the prospective basis.

The exclusive output is
`result/learning_repair/20260930-shared-budget-attempt1`. The serial order
preserves the prior crossed order: `learning_s2017_n28/cost_learned`, then
`learning_s2017_n28/cost_only`. The frozen stage-2 model, its training
groups, development case and target market, cover objectives and all
physical constraints are unchanged. `cost_only` performs no model
inference; `cost_learned` uses the same fixed EdgePrior logit perturbation.
There is no refit, reserved-test access, cold retry, or new route repair
heuristic. The shared cover keeps interval-indexed charging allocation,
per-interval grid sums, route SOC, depot and terminal conditions. This
approaches a coupled fleet MILP, so a 30-second cap may still yield a
time-limited incumbent or no incumbent. Status, gap, nodes, route count,
and elapsed cover time must remain visible; an incumbent is not a proved
minimum unless the solver reports one.

Any integral cover goes through the unchanged fixed-route native GRB
charging/SOC solve and independent physical replay. A new replayed fleet
receives the usual one-column target hull check and exact nonlinear
target-cost calculation. A failure uses the independently replayed
archived pre-target source plan with typed provenance and skips a
redundant native hull; historical bounds are references only. The
falsifiable comparison is whether either 28-service arm now returns an
integral cover and independently replayed new plan, and its exact target
cost relative to the five-second attempt and archived stage-2 controls.
Cover time, model inference, charging/replay, independent replay, pool
preparation, and native hull time are all separate. Any online-time
assessment includes the full repair and verification cost; these two
unreplicated arms cannot support a speedup or general learning claim.

Only the cover cap changes. The GRB charging phase/wall caps remain
45/55 seconds and fresh target hull cap remains 70 seconds. Each child
has a 240-second hard cap; the controller has a 1,500-second launch
guard and external shell cap 1,650 seconds. Slurm requests one CPU,
8 GB, 30 minutes, one thread per solver, no requeue, and excludes
`scaglione-compute-01`. The exclusive lock and immutable receipts
preserve interruptions without automatic retry. Freeze binds the exact
execution commit, source/test/protocol and prior-result evidence hashes,
stage-2 model/catalog/source-selection identities, native/runtime probe,
case/market identities, two-cell order, and all budgets. Historical
profiles retain four cells and their five-second cap.

Local checks use small HiGHS fixtures and archived input reads; they run
no local GRB or new full-fleet optimization:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_shared_budget_repair_pilot.py src/tests/test_shared_interval_repair_pilot.py src/tests/test_shared_charging_cover.py src/tests/test_route_repair_pilot.py
bash -n src/cluster/shared_budget_repair.sbatch
```
