# Selected-cover energy feasibility diagnosis

Each selected route violates a necessary battery bound. Between charging opportunities,
service plus movement energy cannot exceed battery capacity minus reserve,
which is **80 kWh** in both frozen cases. I allow a full battery at every depot
departure, making this check optimistic about charging time, grid power, and
connector availability. Pull-in charging starts only after the final movement,
so it cannot repair an earlier deficit.

| Case | Cover | Bus | Violating segment | Energy (kWh) | Excess over 80 (kWh) |
|---|---|---:|---|---:|---:|
| learning_s2016_n20 | cost_only | 0 | initial→terminal | 200.35 | 120.35 |
| learning_s2016_n20 | cost_only | 1 | initial→terminal | 162.60 | 82.60 |
| learning_s2016_n20 | cost_only | 2 | initial→terminal | 122.75 | 42.75 |
| learning_s2016_n20 | cost_learned | 0 | initial→terminal | 176.74 | 96.74 |
| learning_s2016_n20 | cost_learned | 1 | initial→terminal | 144.05 | 64.05 |
| learning_s2016_n20 | cost_learned | 2 | initial→terminal | 156.12 | 76.12 |
| learning_s2017_n28 | cost_only | 0 | initial→terminal | 216.72 | 136.72 |
| learning_s2017_n28 | cost_only | 1 | initial→terminal | 149.70 | 69.70 |
| learning_s2017_n28 | cost_only | 2 | initial→terminal | 189.31 | 109.31 |
| learning_s2017_n28 | cost_only | 3 | initial→terminal | 125.47 | 45.47 |
| learning_s2017_n28 | cost_learned | 0 | initial→terminal | 241.63 | 161.63 |
| learning_s2017_n28 | cost_learned | 1 | depot departure→terminal | 97.45 | 17.45 |
| learning_s2017_n28 | cost_learned | 2 | initial→terminal | 191.57 | 111.57 |
| learning_s2017_n28 | cost_learned | 3 | initial→terminal | 91.33 | 11.33 |

The [JSON certificate](ENERGY_FEASIBILITY_DIAGNOSIS.json) lists each route's
trip and movement IDs, splits at depot visits, component energy sums,
source hashes, and case identities. The table displays two decimal places;
the JSON keeps sums of the serialized numeric spellings. Recompute it with:

```sh
python3 research-20260930/learning-campaign/diagnose_energy_feasibility.py --check
```

The native fixed-charge LP reported `INFEASIBLE` for all four selected covers.
These route-level violations independently explain infeasibility of those
particular covers. They do not prove that the complete fleet problem or its
minimum-bus-count family is infeasible; other structural covers may differ.
