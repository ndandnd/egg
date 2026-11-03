# Recovery feature and outcome audit

Source-only review; no checkpoints, training data, cases or numerical runs opened. These are measurement proposals, not execution authorization or findings about model quality.

## What the frozen scorers receive

Graph-v8 and CatBoost receive the target market's **linear price vector `a`**. The campaign passes `market.a` to both delegates ([campaign worker](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_local_campaign.py:195)). Graph inference constructs `edge_features(case, prices)` before applying frozen preprocessing/model inference ([graph delegate](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_local_campaign.py:153)); CatBoost uses the same features with fit-only normalization ([classical delegate](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_train_classical.py:51)). This establishes input availability, not learned sensitivity.

The17 features include charging-window mean/minimum price, market mean and market spread, alongside movement/time/energy indicators ([feature inventory](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:19)). Depot/pullin window features use interval overlaps; other movement types receive global price summaries ([window computation](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:67), [feature construction](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:85)). Neither delegate receives quadratic curvature `b` or a tariff-name category. The native planner receives both `a` and `b` ([solver call](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_local_campaign.py:250)).

The frozen nonlearned score is price-blind: `-travel_minutes - .1*intertrip_gap + .1*depot_dwell`, computed from `case` alone ([heuristic](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_offline_rank.py:12)). Target-market native charging can nevertheless make its final bill tariff-responsive.

## Contrasts that identify price response

The current study compares sources/modes and40/80-trip cohorts, without a paired price intervention. Size gains or lower day-tariff bills alone cannot identify tariff responsiveness.

A separately frozen extension could pair each unchanged timetable/seed/budget with an original cheap window and a shifted window. Preserve the linear-price multiset, market interval boundaries, curvature `b`, physical resources and feasible movement set; only relocate cheap prices. This holds global mean/spread fixed while changing local charging opportunities. Choose shifts by identity/time rules before outcomes; report each size separately.

At each target tariff compare fresh target-price scoring against scoring with the original-price vector, while both native planners/completions optimize the same target tariff. Pair that score-input contrast within static and recovery, then compare its size across graph/CatBoost and the price-blind heuristic. This separates ranking response from native charging and recovery. Freeze rank/retained-graph hashes and tie rules. A `b`-only perturbation with fixed `a` is a useful input limitation control: these frozen scorers have no direct curvature channel. Changed terminal bills would measure solver/charging response, not scorer price response. Any extra cells require their own prospective design and budget.

## Outcomes needed for attribution

For every matched prefix/terminal pair, retain exact total bill and its fleet, deadhead/other operating, linear electricity and quadratic electricity components; vehicle count; grid energy and interval load; charging times, location/connector and peak load. Report components in currency, not only percentage savings. Separate fixed-route target-market charging improvements from route/vehicle changes; equal-vehicle comparisons are descriptive because conditioning on an achieved vehicle count can select outcomes.

Record attempted/valid/no-plan/replay-rejected/infrastructure-failed/censored/undispatched denominators. Both-valid bill comparisons cannot replace failure-aware comparisons. Pair every physical witness with original-case replay and recomputed target-market bill.

Distinguish three claims: **direct prediction**—logit/rank/retained-edge changes, coverage and score cost, with provisional incumbent labels identified as such; **repair/search assistance**—prefix feasibility, lift/completion success, fallback retention, start processing, time to valid plan and terminal improvement; **global certification**—only a replay-valid physical upper paired with an admitted full unrestricted lower bound. Restricted/fixed-route bounds and accepted starts do not establish a global certificate. These distinctions support a useful tie to decision-focused prediction and algorithm configuration: predictive sensitivity matters only when its added computation improves feasible decisions under the same clock, beyond fleet construction and native charging.
