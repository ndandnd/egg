# Charging-window diagnosis of selected energy-aware covers

All four energy-aware route covers were optimal in the cover MILP, then the
fixed-route charging LP reported `INFEASIBLE`. A route-by-route upper bound
on delivered charging energy rejects each selected cover even if every bus
gets exclusive access to the charger during each depot visit.

| Case | Cover | Individually rejected routes | First witness | Maximum SOC after service | Reserve |
|---|---|---:|---|---:|---:|
| learning_s2016_n20 | cost_only | 3/3 | service T08 | 18.25 | 20.00 |
| learning_s2016_n20 | cost_learned | 3/3 | service T08 | 18.25 | 20.00 |
| learning_s2017_n28 | cost_only | 3/4 | service T16 | 15.40 | 20.00 |
| learning_s2017_n28 | cost_learned | 3/4 | service T08 | 5.29 | 20.00 |

The [JSON certificate](CHARGING_WINDOW_DIAGNOSIS.json) records every
route, depot window, optimistic charge cap, and first violated reserve
or terminal refill bound. Table values are rounded for display; the JSON
keeps sums of serialized source numbers. Reproduce with:

```sh
python3 research-20260930/learning-campaign/diagnose_charging_windows.py --check
```

This explains why these four selected covers fail without invoking shared
charger competition. It does not determine feasibility of other covers or
the complete fleet problem.
