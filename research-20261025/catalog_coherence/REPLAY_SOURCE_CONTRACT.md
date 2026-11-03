# Catalog coherence: unchanged physical replay contract

Source-only review, 2026-10-25. No data, row/receipt values, plans, charges, loads or costs were read. No imports, hashes, replay, tests or solver calls were executed. This closes the proposed replay-field dependency; parent still freezes actual inputs, sources and command. Scope remains **80 fixed FIT groups / 79 pairs / 159 source witnesses**, with `physical_v2_s10037` source1 only, no replacement.

## Minimal call and source closure

Construct the case from its stored fields using `nr.Trip`, `nr.Leg`, `nr.Movement`, `nr.Resource`, `nr.NativeCase`, preserving numeric types, order and values. Convert nested arrays to tuples of the corresponding dataclasses; retain all remaining keyword fields unchanged and let declared defaults apply. Reject unexpected keys rather than silently dropping them. For example, replace raw `trips`, `movements[*].legs`, `movements`, `resources`, and `market_edges_min` with their typed/tuple equivalents before `nr.NativeCase(**fields)`. Do not call a generator or import the learned feature adapter just to reconstruct a case. All constructor fields/defaults and the case identity are [here](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:31).

Call **`nr.replay_native(case, original_source_plan)`**, without mutation, repair, projection or `prices`. The optional `prices` argument adds only a linear `pricing_objective`, which is not the required quadratic planner objective. The function validates the case and replays sessions directly; it does not call the compiler, decoder or optimizer [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:237).

Minimal project source paths to bind once in the prospective run (in addition to the new collector/protocol/launch inputs) are:

- `src/egglab/__init__.py` — only package docstring/version.
- `src/egglab/native_recharge.py` — dataclasses, identity, validation, replay.
- `src/egglab/native_hull.py` — `Market`, market validation, rational supply valuation.
- `src/egglab/physical_learning_cases.py` — pure source-kind market mapping and, if needed, pure assignment metadata checks; **no generation calls**.

Their module headers use only stdlib and these modules themselves: [recharge header](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:8), [hull header](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:6), [market helper header](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:2). Solver imports occur inside unrelated builders/solve paths; these pure calls do not enter them. No NumPy, sklearn, python-mip or Gurobi is needed for this call chain. This is a static closure, not a runtime import trace or a claim about external import hooks. Avoid full training loaders/dataset adapters. No source hashing was performed for this note.

## Exact plan fields consumed

| Path | Replay meaning |
|---|---|
| `schema`, `case_identity` | Must equal native recharge schema and reconstructed case identity |
| `vehicles[*].vehicle` | Non-bool integer IDs exactly `0..n−1` in list order; `1≤n≤max_vehicles` |
| `vehicles[*].trips`, `.movements` | Nonempty service path; movement count is trip count+1; correct pullout/direct-or-depot/pullin endpoints; mandatory trips covered exactly once |
| `charges[*].vehicle`, `.movement` | Charge must belong to a selected vehicle/movement pair |
| `charges[*].connector` | Non-bool integer **0**, not an arbitrary connector index |
| `charges[*].start_min`, `.end_min`, `.grid_kwh` | Finite nonnegative times/energy, positive duration and energy; continuous charge timestamps are allowed |
| `load` | Mandatory stored vector, correct length, finite nonnegative, within energy tolerance of recomputed per-period loads |
| `ops_cost` | Mandatory finite nonnegative stored scalar, within energy tolerance of recomputed intrinsic operations |

`charges` defaults to an empty list; missing load/ops fails the consistency checks. There is **no consumed charge `resource` field**: availability and active resources are independently derived from movement/case time windows. Extra plan fields remain in the canonical full-plan hash, but replay does not read `raw_solver_load`, `raw_charge_load`, nested `replay`, `roundoff` or separate row `source_replay`. Pass the unmodified original dictionary so identity and stored assertions are preserved. Relevant source: [ownership/paths](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:240), [charge fields/windows](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:275), [stored assertions](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:347).

## Physical checks and unchanged tolerances

`validate_case` checks policy/physics, unique trips/modes, half-minute source-time lattice, chronological directed legs, depot splits, source/sink reachability, and contiguous resources covering the horizon with zero/one connector. Reachability alone is not fleet feasibility. See [policy/time/resource validation](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:132) and [movement validation](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:167).

Replay derives charging windows from depot gaps or terminal arrival/deadline; rejects charging on other modes, outside availability/horizon, or overlapping vehicle service/movement. It sweeps **actual session/resource endpoints**, rejecting excess simultaneous sessions/vehicle use and individual/shared power. Power is compared as energy over each sweep segment. SOC starts full, consumes service/movement energy at arrival/end times, adds efficiency×grid energy at charge end, and must remain inside reserve/capacity and finish full. At equal timestamps, charge energy is applied before consumption. Aggregate energy conservation and stored load/ops checks also apply. See [session sweep](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:289), [SOC/conservation](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:331).

Keep `TIME_TOL_MIN=1e−7` minutes and `ENERGY_TOL=1e−6` exactly unchanged [constants](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:20). The implementation also uses `ENERGY_TOL` numerically for stored ops-cost agreement; describe that source behavior without redefining its units. Do not replace these checks with a new aggregate tolerance, snap timestamps, remove small charges, recompute stored assertions to make them pass, or invoke a repair/decoder/QP. `BOUND_GUARD`/extraction roundoff allowances are not new replay permissions.

Rejection means the unchanged replay did not validate that stored witness under this source contract. Preserve the exception and identity; distinguish malformed shape/type errors from a specific physical `ValueError`. Neither rejection nor success identifies why the original teacher produced the plan. Do not assign a rejected witness zero cost or silently omit it from denominators.

## Returned values and component accounting

On success the dictionary contains:

- `replay_ok=True`;
- `load`: list of floats, recomputed by session rate×period overlap; `grid_kwh=sum(load)`;
- `ops_cost`: recomputed Python numeric scalar (int/float depending on stored case numeric types);
- `consumption_kwh`: float, service+movement consumption; `max_grid_kw`: float;
- `soc_trajectories`: per-vehicle lists of `{time_min, soc_kwh, kind}` events.

There is **no returned fleet-count or deadhead field** [return block](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:354). Derive fleet count as `len(plan['vehicles'])` only after successful replay. Derive deadhead minutes by traversing each validated vehicle's selected movements and summing every stored leg's `arrive_min−depart_min`, exactly the movement-travel definition used by replay—not dwell or service time. Vehicle cost is `case.vehicle_cost*n`; deadhead cost uses `case.deadhead_cost_per_min`. Replay initializes operations with vehicle cost then adds each leg's deadhead contribution sequentially [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:249). Different summation orders or exact component arithmetic can leave a small represented-value residual; retain replay's operations as the valued scalar and expose a residual rather than silently changing that scalar or inventing a new rejection rule. Do not export full SOC trajectories or raw sessions in the compact report.

## Market valuation and reporting tolerance

Construct the two source markets via `physical.market(stored_case, kind)`; it only maps name/a/b and does not generate a case [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191). `Market.identity()` hashes its dataclass dictionary. Call `nh.validate_market(case, market)` before valuation: it validates dimensions, finite `a`, finite nonnegative `b`, and a nonempty market name [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:89). `supply` itself checks load/a dimension but zips b, so this prior validation is necessary.

`nh.supply(market, replay['load'])` returns `Fraction`, computing `Σ rational(a)*rational(L) + rational(b)*rational(L)²/2`. `rational` preserves a supplied Fraction; otherwise it uses `Fraction.from_float(float(value))` after finite-number validation [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:64). Value the full schedule as **`nh.rational(replay['ops_cost']) + nh.supply(market, replay['load'])`**. This is exact arithmetic on replay's represented numbers, not an exact real-physics or global-optimality certificate. Linear/quadratic component reports must use the same conversions; do not substitute decimal-string Fractions, `nr.true_cost`'s float accumulation, atomic payments, or the replay's optional linear objective. See [supply](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:105).

The proposed **cost-sign classification τ=`Fraction('0.000001')` generator cost units** is distinct from physical feasibility tolerances: it labels a four-valuation difference as positive/negative/numerical tie, with exact differences retained. Its magnitude aligns with existing objective-tolerance constants but is an explicit prospective descriptive choice, not a physical allowance or useful-effect threshold. Parent freezes that convention separately; no tolerance or original code changes are needed.
