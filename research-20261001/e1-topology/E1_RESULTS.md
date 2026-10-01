# E1: does route topology respond to the tariff? (no new computation)

Data: saved v7 outputs for TRAIN groups 10064-10079 (array 728823). For each group,
the two admitted source fleets (incumbents solved under `source0`, flat 0.20, and
`source1`, cheap 18:00-22:00) and the v7 cold planner incumbent under `day`
(cheap 10:00-14:00). All are time-limited native incumbents, not certified optima.
Rows: `e1_rows.json`. Computed 1 October 2026 from files pulled read-only.

| Quantity (16 groups) | Result |
|---|---|
| Same bus count under all three tariffs | 16 / 16 |
| Movement set differs between `day` and both source tariffs | 14 / 16 |
| Median movements swapped, `day` vs `source0` / `source1` | 5.5 / 4.0 (of 23-33 selected) |
| Median depot (charging) visits, `day` / `source0` / `source1` | 3 / 2 / 1.5 |
| Mean energy bought 10:00-14:00 (kWh), `day` / `source0` / `source1` | 118.2 / 56.6 / 41.1 |
| Cold `day` planner wall time, median; groups finished <= 30 s | 8.5 s; 13 / 16 |
| Cold relative bound gap (%) | 0.012-0.109 in 14 groups; 0.84 (10075); 6.19 (10069) |

Findings:

1. **Fleet size never responds to these tariffs**, but **routing does**: under the
   midday-cheap tariff the cold solver re-routes buses through extra depot visits and
   roughly doubles midday charging. The indivisible choice that matters on this
   generator is the depot-visit/connection structure, not the number of buses.
2. This explains v7: edge models trained on `source0`/`source1` incumbents, without
   tariff inputs, reproduce those topologies and forgo the midday discount (graph arm:
   -17.1 kWh in cheap periods). Route learning for price response has a real target,
   but it needs tariff-aware inputs **and** labels that span tariffs.
3. Cold solving is already fast and near-optimal at 20-28 trips. ML-for-speed has
   little room here except on hard groups like 10069/10075. E2 measures larger sizes.

Stop/go (from the assessment): "stop route-for-price learning if topology rarely
changes" -> **go**: topology changes in 14/16 groups.
