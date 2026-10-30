# Charging-cap attempt: fixed-cover failure diagnosis

All four saved candidates pass fresh physical replay and exact target-cost
recalculation. Three candidates are archived source fallbacks; the 2017
cost-learned candidate is a new replayed repair.

Each selected cover passes an optimistic per-route charging-window sweep.
A small continuous LP also finds a charging schedule for every cover when
each bus gets its own interval capacity. Adding the shared interval grid
limit makes the three failed covers infeasible; the replayed 2017 cover
remains feasible. This isolates shared charging competition in the fixed
covers, consistent with the saved native fixed-charge statuses.

| Case | Cover | Buses | Cover status | Native fixed-charge | Separate routes | Shared intervals | Minimum added grid energy (kWh) |
|---|---|---:|---|---|---|---|---:|
| learning_s2016_n20 | cost_only | 4 | optimal | INFEASIBLE | feasible | infeasible | 5.189 |
| learning_s2016_n20 | cost_learned | 5 | time-limit incumbent | INFEASIBLE | feasible | infeasible | 1.922 |
| learning_s2017_n28 | cost_only | 4 | optimal | INFEASIBLE | feasible | infeasible | 70.822 |
| learning_s2017_n28 | cost_learned | 8 | time-limit incumbent | OPTIMAL | feasible | feasible | 0.000 |

The [JSON diagnosis](CHARGING_CAP_FAILURE_DIAGNOSIS.json) records
the compiled interval overloads, statuses, source hashes, and limits of
this numerical comparison. [Independent replay](INDEPENDENT_REPLAY_CHARGING_CAP.json)
records the exact cost and plan identity checks. Reproduce both with:

```sh
PYTHONPATH=src python3 research-20260930/learning-campaign/diagnose_charging_cap_failures.py --check
```

The added-grid values come from numerical LPs; they are diagnostic
estimates, not exact infeasibility certificates. No global fleet solve was
run, and these results do not rule out other feasible covers.
