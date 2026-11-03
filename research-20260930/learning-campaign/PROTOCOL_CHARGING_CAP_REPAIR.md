# Charging-window-cap route-cover pilot

This four-cell prospective development pilot tests one specific failure of
the energy-aware route cover: all four prior covers had HiGHS optimal route
assignments but failed fixed-route native charging. Independent diagnosis
found that each cover contains routes that cannot maintain reserve even
at their individual charging limits, before shared competition is considered. The new
exclusive output is `result/learning_repair/20260930-charging-cap-attempt1`.
The earlier energy-aware and cost-aware attempts remain immutable.

The frozen stage-2 EdgePrior, its six training groups, the two development
cases, markets, and archived source fallback are unchanged. Reserved test
groups are untouched and there is no refit. The serial crossed order is
2016/20 services `cost_only`, 2016/20 `cost_learned`, 2017/28
`cost_learned`, 2017/28 `cost_only`. Both modes retain the prior cover
objectives and one bounded HiGHS solve. `cost_only` performs no model-logit
inference; `cost_learned` adds the same normalized logit perturbation to
pullout minimization. The cover objective omits charging cost and is not a
global physical or economic optimum.

The new `charging_caps=True` cover includes the prior necessary SOC
constraints and limits the maximum usable energy gain at each selected
depot movement to efficiency times the sum of `rate_kw × interval_hours`
over its compiled charging window. It also requires enough terminal
pull-in charging capacity to refill the battery. The compiled rate is the
smaller of per-bus and grid power when a connector exists. The cover uses
no interval-indexed charging variables and ignores competition among
buses, so passing it remains only a necessary screen. The fixed-route GRB
charging/SOC solve and independent native replay decide physical
feasibility. There is no hidden retry, second cover, or extra-bus repair.

The primary falsifiable comparison is whether this screen produces a new
independently replayed feasible fleet on either development case, versus
zero of four in the energy-aware attempt, and whether the learned
perturbation changes that rate or exact target cost relative to cost-only.
Record cover status/gap/pullouts, charge outcome and failure stage, exact
replayed target bill, and fresh native hull assessment for every new
repaired plan. If repair fails, independently replay the same archived
pre-target cheapest source plan with exact identity and provenance. A
fallback has no new physical candidate, so no redundant hull solve runs;
its empty hull assessment and zero hull time are explicit, while archived
stage-2 bounds remain historical references rather than new bounds.

The 5-second HiGHS cover, 45-second GRB phase/55-second GRB wall charging
subproblem, and 70-second native target hull caps are unchanged. Each
cell runs as a child with a 240-second hard cap; the serial controller has
a 1,500-second launch guard and the shell a 1,650-second cap. Slurm
requests one CPU, 8 GB, and 30 minutes, with one thread per solver,
`--no-requeue`, and exclusion of `scaglione-compute-01`. The wrapper
receipts requested and allocated CPUs. An interrupted unreceipted cell is
preserved, with no automatic retry. Four cells without replication cannot
establish runtime speedup or a general learning advantage.

Freeze binds the exact execution commit, runtime/native probe, stage-2
model/catalog/results and per-case source selection, new charging-window
diagnosis program/data, cover implementation/tests, shared runner and
protocol, case/market identities, order, caps, and source hashes. This
runner is an explicit profile of the energy-aware controller; that older
profile retains its historical defaults and output path.

Local checks use small SciPy/HiGHS fixtures and replay of archived feasible
plans; no local GRB fleet optimization is run:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_charging_cap_cover.py src/tests/test_energy_cover.py src/tests/test_route_fixed_repair.py src/tests/test_route_repair_pilot.py src/tests/test_energy_aware_repair_pilot.py src/tests/test_charging_cap_repair_pilot.py
python3 research-20260930/learning-campaign/diagnose_charging_windows.py --check
bash -n src/cluster/charging_cap_repair.sbatch
```
