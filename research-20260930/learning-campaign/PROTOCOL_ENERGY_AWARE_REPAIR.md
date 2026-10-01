# Energy-aware route-cover development pilot

This prospective pilot reuses only the frozen stage-2 development cases
`learning_s2016_n20` and `learning_s2017_n28`, and its unchanged frozen
EdgePrior. It does not refit the model, inspect reserved test groups, or
modify earlier attempts. The exclusive output is
`result/learning_repair/20260930-energy-aware-attempt1`.

The four serial cells and their crossed order are fixed:

| Order | Case | Cover policy |
| ---: | --- | --- |
| 1 | 2016, 20 services | `cost_only` |
| 2 | 2016, 20 services | `cost_learned` |
| 3 | 2017, 28 services | `cost_learned` |
| 4 | 2017, 28 services | `cost_only` |

Both policies use one bounded HiGHS path-cover solve with a necessary
energy-feasibility relaxation with a 5-second cover cap. It constrains route
energy between declared depot charging opportunities to usable battery
capacity and permits an optimistic full battery reset only where a compiled
charging interval has positive rate times duration. It checks that some
positive charging capacity exists but ignores how much energy actually fits
and competition between vehicles, and omits terminal refill in the cover
relaxation. It does not model the target tariff in the cover solve. Passing
the cover constraint is therefore
not a physical-feasibility certificate. A cover may still fail the fixed
route charging subproblem or independent physical replay. Failed covers are
retained with solver status and a typed stage; no second cover solve or
extra vehicle is silently introduced.

`cost_only` does not evaluate model logits and minimizes pullouts.
`cost_learned` applies the unchanged EdgePrior logits as a normalized
perturbation to the same pullout objective, with scale
`1 / (4 * max(1, sum(abs(logits))))`. At an exact cover optimum, one more
pullout cannot beat a lower-pullout cover on that perturbation alone.
Neither objective includes the charging supply bill or guarantees the
least total fleet cost. Both use fixed movement input order, HiGHS seed 0,
and one thread; these controls do not guarantee a unique tie resolution.
Timed cover incumbents are not called proved minima.

For every returned cover, all native route binaries are fixed and one
bounded GRB linear-tariff charging/SOC solve runs with a 45-second phase
and 55-second wall cap. The complete plan must
pass independent native physical replay, and its nonlinear target bill is
computed exactly after replay. A new feasible repaired plan enters a
one-column native target-hull check with a fresh 70-second wall cap; its
native lower bound and candidate upper cost remain distinct. If repair
fails, the runner independently replays the archived pre-target cheapest
source fleet with exact plan identity and target objective checks. Because
that is the same already-verified historical candidate, this pilot skips a
redundant new hull solve on this fallback, records `hull_assessment={}` and
zero hull time, and cites archived stage-2 bounds only as historical
references. It makes no fresh bound claim for a fallback.

The primary falsifiable comparison is whether the necessary energy filter
increases the rate of independently replayed *new* repaired fleets from
zero in the earlier cost-aware attempt, and whether `cost_learned` changes
feasibility or exact target cost relative to `cost_only` on each case.
Cover gaps, pullouts, repair failures, exact cost, and new hull evidence are
all reported; four cells with no replication do not establish a speedup or
a learning advantage. Archived stage-2 outcomes and source acquisition
times remain historical development controls, not matched runtimes.

Freeze pins the execution commit, source files and tests including shared
evaluator and repair module, diagnosis program/results, stage-2 frozen
model/catalog/results and per-case source selection, physical cases and
target markets, and native/runtime identities. The wrapper requests one
CPU, 8 GB, 30 minutes, no requeue, and excludes
`scaglione-compute-01`. HiGHS and GRB use one thread. Each child has a
240-second hard cap, the controller a 1,500-second launch guard, and the
shell a 1,650-second external cap. An interrupted unreceipted cell is
preserved and halts automatic resume. Requested and allocated CPUs are
receipted separately.

Local checks use small SciPy/HiGHS cover fixtures, mocked pipeline calls and
physical replay of archived plans. No local GRB fleet optimization is run:

```sh
PYTHONPATH=src python3 -m unittest src.tests.test_energy_aware_repair_pilot
PYTHONPATH=src python3 -m pytest -q src/tests/test_energy_cover.py src/tests/test_route_fixed_repair.py src/tests/test_route_repair_pilot.py
bash -n src/cluster/energy_aware_repair.sbatch
```
