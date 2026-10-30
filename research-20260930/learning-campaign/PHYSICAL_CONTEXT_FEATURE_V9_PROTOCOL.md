# Physical context features v9 — input-only prospective package

This package appends 21 physical/market columns to the unchanged 17 movement
features, giving 38 columns. It creates no model, training CLI, solver call,
campaign, or submission. v3–v8 sources/results remain unchanged. The motivation
is missing explicit battery/reserve/resource inputs, independent of outcomes
from the queued physical-proposal and training-budget studies.

## Allowed inputs and boundaries

`physical_context_features_v9.edge_features(NativeCase, Market)` validates the
declared case and known prospective market, then returns float64 rows in
`case.movements` order. It accepts no catalog, split, source label, plan, loads,
SOC trajectory, incumbent, solver status/objective or fitted transform. Names
and IDs contribute no numeric feature; trip IDs serve only as endpoint keys.
All movements/windows come from the complete declared input graph, never a
source plan's chosen topology. Input validation checks declared physical
constraints and reachability without optimizing or asserting fleet feasibility.

`battery_kwh` is the operational stored-energy ceiling U, not necessarily physical
nameplate capacity. R is reserve, S=U−R>0 the usable span, eta the grid-to-battery
efficiency. Neither actual incoming SOC nor a fleet occupancy state is available.
No such state is inferred. Existing features are an exact call to
`learned_proposals.edge_features(case, market.a)`; its historical horizon/battery
clamps are preserved, including below 1 kWh. New ratios use S without a clamp,
and neither consumption nor capacity ratios are clipped at one.

For a depot movement, W=[inbound-leg arrival, outbound-leg departure]; the
validated `depot_split` partitions legs. For a pullin, W=[max(last arrival,
terminal_open), deadline]. Pullout/direct have no W. Let E be total movement-leg
energy, B/A the preceding/following service-trip energy (zero if absent). A
charging movement's pre-window burst is B plus legs before W; its post-window
burst is legs after W plus A. Pullin places all its legs before W. Other modes
have zero burst columns, while E+A still represents their local consumption.
These bursts have unknown entering SOC and are local context, not an assertion
that a route is feasible or that a particular amount must be charged.

## Appended columns, in order

Minutes are the case's existing time unit. Energy is kWh, power kW, a is
objective currency/kWh, and b is quadratic objective currency/kWh² under
`sum(a*L + 0.5*b*L²)`. b is supplied market curvature, not an observed price or
load. For positive-duration W, d_r is its overlap in minutes with resource r.
All mean quantities below use duration weighting, not a mean of intervals.

| Column | Exact derivation and unit |
| --- | --- |
| battery_upper_kwh | U, kWh |
| usable_span_kwh | U−R, kWh |
| reserve_fraction | R/U, dimensionless |
| charging_efficiency | eta, dimensionless |
| movement_energy_over_usable | E/S, dimensionless |
| movement_and_next_trip_over_usable | (E+A)/S, dimensionless; depot includes both sides of W |
| before_trip_energy_over_usable | B/S, dimensionless |
| after_trip_energy_over_usable | A/S, dimensionless |
| before_window_burst_over_usable | pre-window burst/S, dimensionless |
| after_window_burst_over_usable | post-window burst/S, dimensionless |
| window_enabled_fraction | sum(d_r where connectors>0 and both powers>0)/duration(W) |
| window_connector_hours | sum(connectors_r*d_r)/60, connector-hours, regardless of power |
| window_per_bus_kw_mean | sum(per_bus_kw_r*d_r)/duration(W), declared kW even during connector outage |
| window_grid_kw_mean | sum(grid_kw_r*d_r)/duration(W), declared kW even during connector outage |
| window_isolated_stored_kwh | eta*sum(min(per_bus_kw_r,grid_kw_r)*d_r where connectors>0)/60, kWh |
| window_isolated_span_ratio | isolated stored kWh/S, dimensionless |
| window_other_candidate_overlap_mean | sum(overlap(W,other declared charging window))/duration(W), excluding this movement |
| window_curvature_mean | duration-weighted b over W, currency/kWh² |
| window_curvature_min | minimum b on positive overlaps with W, currency/kWh² |
| market_curvature_mean | duration-weighted b over [0,deadline], currency/kWh² |
| market_curvature_spread | max(b)−min(b) over [0,deadline], currency/kWh² |

Absent/zero-duration W produces zero resource/overlap/window-curvature columns.
Its consumption bursts remain defined. The isolated stored-energy quantity
assumes one bus can use all offered resource capacity throughout W; it does not
subtract shared occupancy or account for actual SOC/headroom. It can exceed S.
Other candidate windows include mutually exclusive alternatives, even where
power is unavailable; their overlap counts structural alternatives, never
realized fleet charging demand. Resource validation currently permits zero or
one connector only; this extension does not generalize that physical contract.

## Prospective controlled ablation, not authorization to fit

Retain the exact128 TRAIN pool manifest
`d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`,
the 80 fit/16 inner/32 outer grouped folds and seeds 17,29,43. All tariff/source
variants of a timetable remain in one fold; labels remain imitation of observed
feasible incumbent movement edges, without an optimal-route claim. No bank or
reserved DEV/TEST data was read for this package.

A controlled first comparison is a NEW matched baseline with the original 17
columns padded with 21 zeros against all 38 columns, using the same declared graph width32/two layers and
initialization, optimizer, weights, batch order and inner stopping rules. Keep
mean message passing and graph attention as the same bounded architecture menu.
Fit transformations on fit groups only; the first17 transformation must match
between feature arms, and padded baseline columns must remain zero. Zero-variance
columns get unit scale and zero centered values. Preserve raw column order,
normalization statistics, every epoch's scalar curves, inner selections,
selected weights/predictions, failure evidence and separate feature-extraction,
training, inference and persistence time. Features, checkpoint and architecture
selection use only fit/inner groups; outer labels stay sealed until all declared
arms are saved. Report all feature/architecture arms rather than select by outer
scores. PyTorch fan-in initialization changes with input dimension, including
active weights, so this new baseline is not historical v6 training reproduced.
Historical 17-dimensional v6/v8 models/scores are contextual references only,
neither the feature-effect comparator nor an epoch anchor for this ablation.

At D=38, v6-shaped node input is 2D+2=78, edge input D=38, and decoder input
3*32+D=134. Additional parameters are 4*32*(38−17)=2688: mean message passing
20545 and graph attention 20673, versus 17857/17985 at D=17. The old18000 ceiling
is invalid here. Zero-padding makes both feature arms share these declared tensor
dimensions/counts, but 2688 baseline input weights are inactive: 672 in the edge
embedding,1344 in the node embedding,672 in the decoder. This does not equate
active information capacity or effective input degrees of freedom. A new parameter/time budget and
fit-fold input-range receipt must be prospectively frozen before any training.
The v8 stopping/optimizer controls can be retained, but four feature/architecture
arms cannot silently reuse a two-arm fold time allowance. This package supplies
no training implementation or launch budget.

Generator definitions show three operational battery/reserve profiles (U=100,
232.32,261.36; S=80,174.24,232.32 kWh), so those inputs can vary. Efficiency .9,
per-bus/grid power90 kW, one connector, and source/target b=1/900 in every period
are constant in this generator; b does not vary across its declared source0,
source1, flat, day or late markets. Window duration/candidate overlap/capacity
still vary with the timetable/movement. No current-bank range claim is made.
Before a future ablation, inventory raw values, variance, min/max and missingness
on each fit fold only; mark constant columns and flag prospective target input
values outside those fit ranges without inspecting target outcomes. Constant
source features cannot teach a response to changed curvature, efficiency or
charger ratings. A separate controlled input generator would be needed to learn
those responses; it must not invent actual fleet states or use target outcomes.

## Checks and source identity

`PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_context_features_v9.py`
passed 14 tiny fixtures in 0.42 s locally (Python3.12, NumPy1.26.4). Checks cover
exact prefix/schema, label-free API, source-label/name/ID invariance, row-order
equivariance, irregular resource/market overlaps, bus/grid bottlenecks, outages,
efficiency, zero windows, negative a/zero b, static alternatives, sub-1-kWh scale,
unclipped stress/capacity and invalid physical/market inputs. No fit or solve ran.
Runtime qualification of future training remains separate.

SHA256 source identities at feature-package completion:

| File | SHA256 |
| --- | --- |
| src/egglab/physical_context_features_v9.py | a83c629902a6e704010b02c0c3b22e0ebbdb99351126af20fa78055ee208c33f |
| src/tests/test_physical_context_features_v9.py | 216d94a13682d8ef101cd45cd6f8b249e85492447c83e657a6867e3d80db1e1d |
| src/egglab/learned_proposals.py | 5b58b9495ccb401bf7a865ba4058a81838b575f517268e76bad40f0b7dcbd479 |
| src/egglab/native_recharge.py | 0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3 |
| src/egglab/native_hull.py | dc8f04bfeab01fb6aaa4afca61c97887993b4e6181be8cabfa76858265051ffd |
| src/egglab/physical_learning_cases.py | 85f832c80526e02a4531bd0b4a70ed398eb46ae9a6cae2834da163ef3c0c8f1b |

The next bounded options are a fit-fold input-only range inventory followed by a
newly budgeted padded-baseline/context ablation, or a separate physically valid
generator extension that varies charger/curvature inputs. Existing queued
studies need no source change to support either future decision.
