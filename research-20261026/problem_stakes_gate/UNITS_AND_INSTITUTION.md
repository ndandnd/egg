# Units and institutional objective — source-only gate

> **Scope correction, 26 October 2026:** the implemented objective discussed
> here is the recent native-pilot path. EGG also has `AffineMarket` and separate
> strategic/system solve paths in `src/egglab/market.py` and `regimes.py`, including
> background load. The period-energy dimensional analysis remains valid; a
> project-wide absence of a price-maker model does not follow. See
> `../EVSPDR_CONTEXT_CORRECTION.md` for the source-backed correction.

The implemented objective is **integrated supply/system cost plus intrinsic fleet operations**, in synthetic generator cost units. It is not established to be a fleet's electricity payment under a uniform clearing-price market. The source gives coherent dimensional conventions, but neither monetary calibration nor an observed market institution. This note uses only the current handoff/decision and narrow source definitions; no rows, plans, receipts, metadata values, model assets, replay or computation were accessed. No current coefficients are changed and no experiment follows automatically.

## What the objective actually values

The worker evaluates the recomputed physical witness as `rational(replay['ops_cost']) + supply(market,replay['load'])` ([worker.py:186](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261026/economic_recourse_pilot/worker.py:186)). `native_hull.supply` implements

\[
F=c+\sum_t\left(a_tL_t+\tfrac12 b_tL_t^2\right),\qquad
p_t=\partial S/\partial L_t=a_t+b_tL_t.
\]

The integral and its marginal-price formula are explicit ([native_hull.py:105](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:105), [native_hull.py:222](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:222)). `rational` preserves represented binary floating coefficients; it is not recovery of empirically exact decimal prices ([native_hull.py:64](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:64)).

If an atomic fleet instead pays the endogenous uniform price on all its own energy, with no background load, its payment is \(p_t(L_t)L_t=a_tL_t+b_tL_t^2\), whose marginal payment is \(a_t+2b_tL_t\). That is a different objective. Conversely, an exogenous posted energy price gives a linear payment \(p_tL_t\). An integrated increasing-block procurement rule could charge \(\int_0^{L_t}p_t(q)dq\), but such a rule must be specified; a formula alone does not establish it. No wholesale settlement, bids, strategic suppliers, other fleets/background demand or transfer rule appears in the `Market(name,a,b)` payload ([native_hull.py:23](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:23)). Thus “planner/system procurement cost” is a defensible mathematical interpretation; “atomic strategic fleet bill,” market equilibrium, consumer welfare or actual tariff savings are unsupported without a new institutional model. Existing names such as `bill` or `source tariff` do not change the implemented algebra.

## Time, energy, power and curvature

| Quantity | Source-supported meaning |
|---|---|
| Trip/leg/session timestamps and durations | Minutes on a model horizon; distinct from the worker's elapsed wall-clock seconds. Dataclass fields name minutes ([native_recharge.py:31](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:31)). |
| Service/movement energy, battery/reserve | kWh at the battery; charging efficiency is dimensionless. |
| Session `grid_kwh` and \(L_t\) | Grid-side kWh. Replay calculates session kW as `energy*60/(end-start)`, then adds `rate*overlap/60` to period load. Returned `grid_kwh=sum(load)` confirms energy, not power ([native_recharge.py:289](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:289), [native_recharge.py:354](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:354)). |
| Resource `per_bus_kw`, `grid_kw` | Instantaneous kW limits, separately checked along with connector count ([native_recharge.py:317](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:317)). |
| \(a_t\), marginal price \(p_t\) | Generator cost units per grid kWh, if \(F\) is in generator cost units. |
| \(b_t\) | Generator cost units per grid kWh squared; not a power-slope coefficient without period-duration conversion. |

For period duration \(\Delta_h\) hours and period-average power \(P_t=L_t/\Delta_h\), a physical marginal-cost curve \(m_t(P)=\alpha_t+\beta_tP\) yields

\[
\Delta_h\bigl(\alpha_tP_t+\tfrac12\beta_tP_t^2\bigr)
=\alpha_tL_t+\tfrac12(\beta_t/\Delta_h)L_t^2.
\]

Under this period-average/constant-power cost interpretation, \(a_t=\alpha_t\) and **\(b_t=\beta_t/\Delta_h\)**; \(\beta_t\) has cost-unit/(kWh·kW) dimensions. The current generator fixes hourly edges `range(0,1801,60)` ([physical_learning_cases.py:33](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:33)). Increasing slot count while holding `b` unchanged can therefore change the economic model, even if physical energy and power are unchanged. If the intended physical cost instead integrates instantaneous squared power for nonconstant within-period charging, period energy alone is insufficient to reproduce that integral. The source objective values period-energy aggregates; it does not price every instantaneous session rate or peak.

## Declared constants, not empirical calibration

The physical generator declares 20/28 services; three battery profiles with `(upper,reserve)` values `(100,20)`, `(232.32,58.08)`, `(261.36,29.04)` kWh, while the latter profiles separately retain nameplate290.4kWh. Battery model upper bound is `upper_kwh`, not automatically nameplate. It declares consumption `(1.20,1.45,1.70)` kWh/km, speed36km/h, direct-wait auxiliary draw1.2kW, depot dwell draw0; depot-gap thresholds `(0,15,30)` minutes and duty strides25/30 minutes. These are direct source constants, not estimates or newly evaluated assignments ([physical_learning_cases.py:15](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:15), [physical_learning_cases.py:52](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:52)). Distance and drive energy are explicitly `minutes*SPEED_KMH/60` and distance×consumption; waiting energy is `IDLE_KW*waiting_minutes/60` ([physical_learning_cases.py:78](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:78), [physical_learning_cases.py:123](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:123)).

Original cases declare one connector, both shared/per-bus90kW, horizon0..1800 minutes, terminal opening1080, deadline1800, efficiency.9, vehicle coefficient100.0 and movement-duration coefficient0.0 ([physical_learning_cases.py:140](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:140)). Source0 has `a=.20` in all30 periods; source1 has `.10` at indices18–21 and `.30` otherwise; both have `b=1/900` throughout ([physical_learning_cases.py:191](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191)). These numbers are not validated dollars, a measured grid response or evidence of realistic material stakes.

Operations are \(c=\text{vehicle_cost}\times N+\text{deadhead_cost_per_min}\times\sum\text{selected leg durations}\). The duration sum includes stationary waiting legs, so the label “deadhead minutes” is broader than driving time; coefficient units must be cost units per represented movement-leg minute ([native_pathflow.py:242](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:242), [native_recharge.py:249](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:249)). With exact N and the declared zero duration coefficient, intrinsic operations are constant across this pilot's alternatives; there is no direct driver/labor/deadhead-money reward, although route energy can differ. No source defines whether100 is daily ownership cost, amortized capital or a dispatch penalty. Full end replenishment and grid/battery conservation are enforced; unpriced initial energy is not a free route-dependent depletion benefit ([native_recharge.py:344](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:344)).

## What the stakes gate still needs

A credible next target needs an identified decision maker and settlement/procurement rule, a common monetary/time horizon for fleet and energy coefficients, and external justification for supply curvature, base prices, background demand and operational resource assumptions. Driver time, wear/degradation, demand charges, reliability penalties, infrastructure costs and service-value consequences cannot be inferred from these coefficients. Renaming cost units dollars, increasing curvature/scarcity until a gain appears, or changing time resolution without consistent \(b\) scaling would not supply calibration. The pilot protocol already labels the output uncalibrated and descriptive ([PROTOCOL.md:136](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261026/economic_recourse_pilot/PROTOCOL.md:136)). Until institution and material decision value are defensible, the source supports a synthetic convex system-cost tradeoff, not a demonstrated important learning opportunity or real fleet-payment saving.
