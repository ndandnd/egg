# Cost-aware route-cover ablation

This prospective four-cell development run uses the stage-2 frozen model and
the two existing development timetables, `learning_s2016_n20` and
`learning_s2017_n28`. It does not refit, inspect reserved test groups, or
change the original route-repair attempt. Its separate exclusive output is
`result/learning_repair/20260930-cost-aware-attempt1`.

The crossed serial order is fixed before execution:

| Order | Physical case | Cover policy |
| ---: | --- | --- |
| 1 | 2016, 20 services | `cost_only` |
| 2 | 2016, 20 services | `cost_learned` |
| 3 | 2017, 28 services | `cost_learned` |
| 4 | 2017, 28 services | `cost_only` |

`cost_only` sends no prior to the repair API and performs no model/logit
inference. Its single bounded HiGHS MILP minimizes pullout count within
declared route-cover constraints. This cover objective excludes charging
and supply costs and does not guarantee the least overall fleet cost even
when charging repair succeeds. `cost_learned` scores routes with the
unchanged stage-2 EdgePrior, then minimizes pullouts with a normalized
learned-logit perturbation scaled by
`1 / (4 * max(1, sum(abs(logits))))`. At an exact optimum this scale
cannot make one extra pullout preferable to a lower-pullout cover. The
actual bounded solver result and its status, gap, nodes, timing, seed 0,
and one-thread setting are recorded; a time-limited incumbent is never
called a proved minimum. Input movement order and solver seed are fixed;
they do not guarantee a unique mathematical tie resolution. Neither policy
claims globally optimal fleet operation.

Each selected cover then follows the existing repair pipeline: all native
movement binaries are fixed, a 55-second linear target-tariff charging/SOC
subproblem runs on one GRB thread, the complete plan is independently
replayed, and the exact nonlinear target cost is computed. No infeasible
cover receives a second cover solve, more vehicles, or a hidden cold solve.
On typed repair fallback, the experiment independently replays the
archived pre-target cheapest source plan and records its provenance and
selection time. Both repaired and source-fallback candidates enter a
new one-column feasible-pool target hull run with a 70-second wall budget;
the target solver must generate its own lower certificate. Raw prediction,
cover, charge/replay, independent replay, pool preparation, target hull,
all failures, and elapsed time are retained separately.

Archived stage-2 learned and cheapest target-arm outcomes are historical
development controls. Source acquisition is reported separately from this
new job. Four serial cells in one allocation provide a small ablation,
with crossed order but no replication; they do not justify a matched-runtime
speedup claim. A replayed fleet is a feasible incumbent, not an optimal
label. Scientific admission remains pending independent review.

Freeze pins the execution commit, all source files including the shared
evaluator and repair module, stage-2 frozen model/catalog/results and
per-case cheapest-source selection hashes, physical and target market
identities, cell order, policies, and runtime/native probe. The wrapper
requests one CPU, 8 GB, 30 minutes, no requeue, and excludes
`scaglione-compute-01`; native and cover solvers each use one thread.
Each child has a 240-second hard cap, the controller a 1,500-second
launch guard, and the shell a 1,650-second external cap. The requested
and actual allocated CPU counts are both receipted. An interrupted
unreceipted cell is preserved and stops automatic resume.

Pure checks, with no local native optimization:

```sh
PYTHONPATH=src python3 -m unittest src.tests.test_cost_aware_repair_pilot
PYTHONPATH=src python3 -m pytest -q src/tests/test_route_fixed_repair.py src/tests/test_route_repair_pilot.py
bash -n src/cluster/cost_aware_repair.sbatch
```
