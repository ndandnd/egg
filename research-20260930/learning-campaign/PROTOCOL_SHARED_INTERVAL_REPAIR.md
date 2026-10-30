# Shared-interval charging cover pilot

This prospective four-cell development pilot tests one omitted constraint
from the charging-window-cap cover: competition for energy within each
compiled charging interval. The prior cap-aware job produced one new
physically replayed fleet, an eight-bus 2017 learned cover costing about
980.999, above the archived stage-2 development control of about 689.474.
The other three covers failed the fixed-route charging solve. A separate
numerical isolation exercise found each fixed cover feasible when visits
could use individual capacities independently, then infeasible for those
three when shared interval sums were imposed; the eight-bus cover remained
feasible. The reported aggregate capacity shortfalls were 1.922222 kWh
(2016 learned), 5.188889 kWh (2016 cost-only), and 70.822222 kWh (2017
cost-only). These numerical LP/GRB diagnostics explain the selected
covers; they are not global infeasibility certificates for the physical
cases or proof that a five-second coupled cover will find a better one.

The attempt is exclusively
`result/learning_repair/20260930-shared-interval-attempt1`. It uses the
same frozen stage-2 model, six training groups, development cases and
markets, crossed order, and archived pre-target source fallback as the
charging-cap pilot. The serial cells are 2016/20 services `cost_only`,
2016/20 `cost_learned`, 2017/28 `cost_learned`, 2017/28 `cost_only`.
There is no refit or reserved-test access. `cost_only` performs no model
inference; `cost_learned` uses the unchanged normalized logit perturbation
of the pullout objective. Neither cover objective includes the target
charging bill or guarantees minimum full-fleet cost.

The `shared_charging=True` profile requires the existing necessary route
SOC and individual charging-window caps. It adds continuous grid-kWh
variables for each depot or terminal pull-in movement and compiled
charging interval. Each variable is bounded by interval capacity and the
selected movement; the sum across visits cannot exceed that interval's
grid capacity. Conditional equalities tie selected depot SOC transitions
and terminal full-battery refill to efficiency times their allocated
grid energy.
This screen is closer to a coupled fleet MILP and may consume its entire
five-second HiGHS cap or return no incumbent. Any time-limited cover is
recorded with status, gap, nodes, timing, and route count; no solver
minimum is inferred from an incumbent. The cover still is not a native
physical plan: fixed-route GRB charging/SOC and independent native replay
remain mandatory. No fallback retries, enlarged vehicle count, or hidden
cold solve occur.

The primary falsifiable comparison is whether adding shared interval
coupling changes the number and exact target cost of independently
replayed new fleets relative to the four cap-aware cells. A new repaired
candidate receives a fresh target hull assessment. Failed repair uses the
same independently replayed archived source candidate and explicitly
skips a redundant target hull, with empty new hull assessment and zero
new hull time. Archived bounds are historical references only. Record
model inference, cover, fixed-route charging, independent replay,
fallback selection, pool preparation, hull, and total elapsed time
separately. The four unreplicated cells do not support speedup or
generalization claims, and a no-incumbent cover under five seconds does
not establish inferiority of either objective.

Resources and caps remain fixed: one CPU, 8 GB, 30-minute Slurm allocation,
one thread for each solver, no requeue, exclude `scaglione-compute-01`;
five-second cover, GRB charging 45-second phase/55-second wall, native
target hull 70-second wall, 240-second child hard cap, 1,500-second
controller launch guard, and 1,650-second shell cap. The exclusive
controller lock and immutable per-cell receipts preserve interruption
evidence. Freeze binds the execution commit, source/test/protocol hashes,
independent replay and shared-capacity diagnosis, stage-2 inputs and
per-case archived source selection, runtime/native identity, case/market
identities, flags, order, and budgets. The historical profiles default
to `shared_charging=False`.

Local checks use small SciPy/HiGHS fixtures, fixed-cover diagnostic LPs,
and archived replay; they run no local GRB or new full-fleet optimization:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_shared_charging_cover.py src/tests/test_shared_interval_repair_pilot.py src/tests/test_charging_cap_cover.py src/tests/test_charging_cap_repair_pilot.py src/tests/test_energy_aware_repair_pilot.py
python3 research-20260930/learning-campaign/diagnose_charging_cap_failures.py --check
bash -n src/cluster/shared_interval_repair.sbatch
```
