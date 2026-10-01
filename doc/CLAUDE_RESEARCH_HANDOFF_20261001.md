# EGG research: independent-review handoff to Claude

Prepared 1 October 2026, approximately 05:15 UTC. This is a handoff, not a claim of independent scientific validation. The user has paused Codex's scheduled work to obtain a fresh perspective and conserve tokens. Manuscript drafting was already deferred in favor of computational and machine-learning research.

## Suggested opening request

> Please independently assess this research. Read this handoff and the accompanying evidence before accepting the previous assistant's interpretation. Separate established findings, plausible explanations and untested plans. Are we asking a valuable question, measuring the right things, and allocating effort sensibly? Identify the strongest contribution, the most serious weaknesses or bias, and three decisive next experiments with stop/go criteria. Consider simpler methods and changes of direction. Do not assume that more training, a GNN, or the already-prepared next experiment is the best answer. Start with assessment; do not launch new computation or open reserved evaluation data just to perform the review.

## 1. Research question and intended contribution

EGG studies electric-bus scheduling and charging when fleet decisions affect electricity supply costs and prices. A complete feasible fleet plan includes discrete bus assignments and continuous charging. The central theoretical question is whether a physically efficient fleet is supported by marginal electricity prices: after a price is posted at that fleet's load, would the operator prefer another feasible plan?

The existing draft develops an exact two-service counterexample and a robustness neighborhood; a replication family where the physical-versus-convexified planning gap decreases while whole-operator price-taking regret remains nonzero along a specified subsequence; and a distinction between a single operator controlling the fleet and small operators with separately reserved charging rights. It also adds convex generation dispatch with ramp constraints, nonsmooth price selection, and a dual-coordination illustration.

Scope matters. Whole-operator regret treats a posted price as fixed when the fleet deviates. It is not a solved strategic equilibrium in which that operator anticipates its own price impact. Convexified averages need not be executable daily schedules. The replication rate is established for a particular construction, not a general theorem about all shared-charger fleets. The Shapley–Folkman interpretation and generation-side literature need independent assessment for novelty and relevance.

The latest historical manuscript is `output/pdf/egg-journal-v0.10-coauthor-draft.pdf`; its source is `paper/latex/`. It predates the current physical-learning campaign and must not be treated as a report of the newest ML results. The short theory/readability review notes in the bundle identify important theorem and tolerance qualifications. For example, the 20,000-call analytic dual run approaches but does not meet a strict 1e-6 dual-error threshold; the three-pricing-call hull run uses a different oracle and certificate target. These are not matched runtime comparisons.

The computational goal is to obtain useful route or whole-fleet proposals that reduce the work of repeated fleet optimization. A successful learning result must improve feasible cost or matched end-to-end work, including repair, charging and verification. Better edge prediction alone is insufficient. Whether this ML direction strengthens the original pricing paper or should become a separate project is an open strategic question.

## 2. What has actually been trained

The current synthetic bank has **128 independent TRAIN timetable groups and 255 observed feasible source fleets**. One source for timetable 10037 is censored and remains missing. Edge labels identify movements used by observed solver incumbents; they do not establish optimal routes, and an unselected edge is not necessarily infeasible or undesirable.

The full-bank design uses four grouped folds, with 80 FIT, 16 INNER and 32 OUTER timetables per fold, and seeds 17/29/43. All variants and source plans of a timetable stay together. Preprocessing uses FIT only; checkpoints/configuration/policy selection use INNER. Each timetable receives equal weight in reported averages. Seeds, variants and thousands of edges do not increase the number of independent timetables.

These are **exploratory cross-validation results within the TRAIN bank**. Researchers have repeatedly inspected its OUTER results and adapted later experiments, even though each run prevents label leakage during fitting. The 32 DEV groups and 32 final-test groups remain unopened. The protected A6/B3/confirmation outcomes and private GIRO data are outside this campaign.

| Model or predeclared INNER-selected policy | Log loss ↓ | Average precision ↑ | Trip-count top-k recall ↑ |
|---|---:|---:|---:|
| Logistic | 0.11071 | 0.66402 | 0.60366 |
| MLP32, extended budget | 0.08420 | 0.74774 | 0.67370 |
| Histogram boosting, original budget | 0.06989 | 0.82425 | 0.69136 |
| XGBoost | 0.06942 | 0.82827 | 0.69669 |
| CatBoost | 0.06930 | 0.82648 | 0.69775 |
| ExtraTrees | 0.07050 | 0.82241 | 0.69260 |
| Tree-family policy | 0.07013 | 0.82626 | 0.69392 |
| Mean-message graph network | 0.07300 | 0.83382 | 0.73323 |
| Graph-attention network | 0.07187 | 0.84309 | 0.73989 |
| Graph policy | 0.07189 | 0.84257 | 0.73957 |

Sources: `ROUTE_FAMILIES_V5_RESULTS.md` and `ROUTE_GRAPH_V6_RESULTS.md` in `research-20260930/learning-campaign/` (the campaign directory below). Top-k uses the input trip count; it is a ranking diagnostic, not a decoder. Policy menus and training costs differ, so this table does not isolate message passing as the cause of improvement.

The graph models are small task-specific two-layer networks with roughly 18,000 parameters and 17 edge features, not exact reproductions of published GraphSAGE/GAT architectures. Explicit battery/SOC and charger context were absent. All graph arms reached the 300-epoch ceiling; selected checkpoints were at epochs 297–300. That motivated a longer-budget study but does not prove undertraining or immunity to overfitting. Saved v6 predictions were independently recomputed numerically; v6 consumed 2.87 allocated CPU-hours. This is still a modest pilot, not months of large-scale training or evidence of state-of-the-art performance.

## 3. Most important result: better ranking has not yielded better fleets

Physical pilot v7 used 16 fixed TRAIN timetables, 10064–10079, the `day` tariff and seed-17 models from their held-out folds. Its reference policy was the predeclared cheapest direct or recharged plan in each timetable's existing two-source bank. This is within-timetable reuse; it is not nearest-neighbor transfer to a new timetable. Source acquisition and recharge costs are recorded separately.

| Primary proposal | Feasible/replayed | Mean extra bill on the common 15 successful groups |
|---|---:|---:|
| Tabular | 16/16 | +0.480 |
| Tree-family | 15/16 | +2.832 |
| Graph | 15/16 | +4.600 |
| Cost-only decoder | 15/16 | +21.617 |

Positive means worse than source reuse. Tabular's mean across **all 16** is +7.570: on timetable 10069 it uses one extra bus and costs +113.915. Tree-family, graph and cost-only cover solvers hit their five-second limit without an integral incumbent on that timetable. The common-15 table is conditional on success and must not erase these failures.

Raw argmax topology was invalid in **46 of 48** diagnostics; the primary evaluated learned proposals rely on repair. All 143 saved plan bills replayed exactly. This physical replay did not independently rerun the v7 model scoring itself; saved-model numerical replay is documented separately for v5/v6. Only one of the 15 successful graph proposals was cheaper by more than 0.01 cost units; that descriptive tolerance was post-hoc and does not alter selection rules.

On the common 15, learned methods use the same number of buses as their reference, so the extra graph bill is entirely charging/supply cost. Its mean total grid energy rises by only 1.66 kWh, but cheap-period charging falls by 17.10 kWh. An exact accounting decomposition assigns +3.42 cost units to the lost cheap-period discount, +0.50 to extra energy at the high-tariff reference, and +0.68 to supply curvature. This is an identity of saved outcomes, not proof that a particular routing feature caused the loss.

**A material integration failure remains unresolved:** all 32 v7 hull-control children failed before optimization because the call used `pool_tol` instead of `pool_tolerance`. Consequently v7 supplies no global hull bounds or mixture results. Slurm completion was not complete scientific success. Cold physical incumbents also use a different multi-round budget; there is no established matched online speedup or physical optimality result. Preserve all failed stages and their time when assessing performance.

## 4. Prepared work versus results

**Longer training v8:** an already-submitted recovery array is finishing a maximum-900-epoch study on the same 128-group bank. It must reproduce the original 300-epoch anchor behavior before longer-training results are accepted. No complete batch result has yet been collected or scientifically reviewed. The original attempt failed all 12 tasks during shell startup, before fitting; its 12 allocated CPU-seconds remain recorded. The recovery changed startup handling, not the scientific design.

**Physical-context v9:** a new implementation and prospective protocol are reviewed and committed, but **not deployed, fitted or submitted**. It compares 17 old features padded with 21 zeros against 38 inputs including battery, charging opportunities and market context, for both mean-message and attention models. Paired arms have matched shapes/initialization; equal nominal dimensions do not imply equal effective capacity. The plan is 12 fold/seed tasks, up to 900 epochs, four concurrent CPU workers and a 24 requested CPU-hour cap. Prepared code is not a reason by itself to run it.

The FIT-only input inventory shows useful battery/window variation but narrow equipment assumptions: efficiency 0.9, 90-kW chargers, one connector and fixed quadratic supply coefficient. Local charging-capacity proxies are optimistic and do not guarantee fleet feasibility. No broad hardware, supply-regime or real-world transfer claim is justified.

## 5. Questions we particularly want an independent reviewer to challenge

1. Is edge imitation of a few feasible incumbents aligned with low-cost, price-responsive fleet construction? Would cost-sensitive labels, multiple solutions, structured decoding or optimizer guidance be more appropriate?
2. Does the cheap-reuse reference exploit information unavailable in the intended deployment, and have its offline acquisition costs been fairly separated/amortized? What is the right comparison against cold solving, retained columns, new-timetable retrieval and exact rescoring?
3. Is failure dominated by the learner, the repair formulation/budget, charging optimization or missing physical inputs? Which intervention can distinguish these explanations with the least computation?
4. Are 128 synthetic groups, repeated TRAIN comparisons and fixed equipment enough to justify additional architecture exploration? Which independent regimes and learning curves would actually test generalization?
5. Is the pricing theory novel and useful beyond the exact construction? Does learning contribute to answering that question, or are we drifting into a loosely connected optimization project?

Please distinguish a reproducible computation from a strong scientific result. Codex and its Sol/Luna subagents produced the implementation and internal checks; those checks are not external peer review. We deliberately include negative physical results, incomplete controls and sunk work so the review can recommend a pivot or stopping a line of work.

## 6. Operational handoff and pause

All three local Codex schedules are **PAUSED**: `advance-egg-journal-research`, `overnight-usage-and-reset-check`, and `unicorn-evsp-dr-research-progress`. The latter two were already paused. Codex will not launch the prepared next study or resume scheduled monitoring unless the user resumes it. Existing jobs were not cancelled.

At the last read-only snapshot, approximately **05:06 UTC on 1 October**, array **738226** had tasks 9–11 running on `unicorn-cpu-75` (one CPU/8 GB each); tasks 0–8 were recorded completed with exit 0. This is a timestamped status, not a claim they remain running when you read this. Full scientific results remain unreviewed.

- SSH alias: `unicorn2`; source `/etc/profile.d/slurm.sh` before scoped Slurm queries.
- Remote checkout: `/home/nc437/egg-route-graph-budget-20261001-v8-recovery1`.
- Relative results: `result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1`.
- Launch receipt: campaign `LAUNCH_738226.json`; execution commit `a19f0acc08adf4743cf24c9c82d0f4951f2f0bf3`.
- For a user-authorized takeover, collect the complete batch, accounting and failures once; verify anchors and saved models before interpreting outcomes. Do not automatically retry missing or interrupted attempts.
- Do not alter other projects or held jobs, use `scaglione-compute-01`, open sealed data, publish private GIRO data, merge a PR, submit a paper or redeem reset credits.

Local repository: `/Users/nadan/Documents/ChatGPT/egg/journal-research-work`.
GitHub: <https://github.com/ndandnd/egg>, branch `codex/journal-research-20260927`.
Pre-handoff HEAD: `40a58218d0ef7250e8d4ada18d5db4cc77f99f84`.
Prepared v9 execution candidate: `987cff55253477ca532c2832187f483c76f6ba2e`.
Original research log: <https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg/edit>.

Start with this handoff, the v7 results/cost diagnosis and v6 results. Read the historical PDF for theory. Then inspect v9 and v8 protocols only if relevant to your recommendation. The portable bundle preserves repository paths and includes a SHA-256 contents manifest; it intentionally omits bulky raw models/data. Full receipts, source, saved evidence and history remain in the repository and cluster. The newest pause checkpoint and `PAUSE_AND_CLAUDE_HANDOFF_20261001.json` override earlier instructions to continue automatically.
