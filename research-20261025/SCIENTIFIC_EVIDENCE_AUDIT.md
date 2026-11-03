# Scientific evidence audit — 25 October2026

**Judgment:** there is a real development result about finite-budget feasible
schedule quality. There is not yet an identified price-learning mechanism,
strong-baseline superiority, market implementation result or submission-ready
contribution. More engineering passes do not close those scientific gaps.

This audit reads the named development summaries/current objective code only.
No protected DEV/TEST/A6/B3/confirmation/GIRO outcomes, computation, inference,
solver, test, import, hash audit, cluster operation or commit was performed.
Numbers below are reported evidence, not newly reproduced estimates.

## 1. Established findings, with scope and denominators

| Finding | Actual sample/evidence | What it supports |
| --- | --- | --- |
| Completed ranking-source screen |20 synthetic development timetables,10 each at40/80 trips;3 paired seeds;6 arms;360 decisions. Valid endpoints: graph60/60, new CatBoost60/60, cheap heuristic60/60, random59/60, full4 44/60, cold59/60. `research-20261017/screen-analysis-v3-final/{SUMMARY.md,summary.json}`; primary compact receipts under `local-screen-v3`; exact grouping/arms in `LOCAL_CAMPAIGN_PROTOCOL.md`. | A complete finite-budget comparison, not independent final validation.16 full4 no-plans are not infeasibility proofs; random has one unresolved extraction/replay outcome and cold one censored endpoint. |
| Large regime-specific graph effect | Median of timetable-level medians versus cheap heuristic:0.4702% at40 and68.3622% at80; versus new CatBoost approximately−0.0021% and44.3742%. Each principal comparison has30 paired seed cells/10 timetable groups per size. `research-20261017/REVIEWER_HANDOFF_20261017.md`; `screen-analysis-v3-final/summary.json`, comparisons.*.median_gain_by_size. | Graph's saved plans have lower declared objective on these finite-budget development cases. Pooled33.03% masks two different regimes. Seeds are repeats, not60 independent timetables. |
| Most large-case gain is vehicle-count cost | Independent compact check:120 graph/heuristic endpoints,360 compact files;30 pairs/10 groups per size. At80, fleet component68400 of74415.49487672 summed savings =91.9163409627%; median vehicles4 versus27.5, median paired reduction23. At40, all30 pairs have equal vehicle counts. `research-20261023/BILL_MECHANISM_INDEPENDENT_CHECK.md`; `bill-mechanism/{RESULTS.md,decomposition.json}`. | Strong route-construction/search explanation.91.916% is a ratio of summed components, NOT a decomposition of the68.36% median relative gain. Electricity residuals can reflect energy/routing changes, not price responsiveness. |
| Classical prediction is viable | TRAIN128:128 timetable groups/255 observed source fleets;80 fit/16 inner/32 exploratory historical outer. CatBoost outer log loss0.078680/AP0.824320; logistic0.125602/AP0.591343. `research-20261017/classical-training/RESULTS.md` and `attempt1` metadata/receipts. | A newly trained comparator and imitation-label accuracy. One historical fold/seed, not independent generalization or downstream optimality. Screen machine ID catboost_v5 denotes this new model, not recovered historicalv5. |
| Public-plan edge recall has severe reference dependence |2 public networks, one locally available feasible reference plan each; random averaged over20 seeds. `research-20261017/offline-ranking/{RESULTS.md,attempt3.json}`. | Exploratory retention diagnostics only. Eberbach reference was itself generated using graph top5, so perfect graph top5 recall is circular evidence. |
| Recovery mechanics can work on specified engineering examples |6 handcrafted native primitive tasks;2 full ordinary cases have physical objectives59.5/67 and numerical lower bounds59.499999/66.999999. `research-20261023/RECOVERY_NATIVE_RESULTS.md`, `native-primitive-v1/`, `native-primitive-lock-v1.json`. Later8 V7 tasks span only2 engineering timetables,1 per size, seed17/day/nonlearned. `RECOVERY_PHASE1_V7_RESULTS.md`, corresponding `accounting.json`/terminal receipts. | Native start/fallback/replay paths on those examples, tolerance-qualified bounds, not exact proofs or learned performance. At80, recovery3628.91/27 vehicles was worse than cold3386.20/24 vehicles; at40 recovery658.68 approximately tied cold658.71. The80 recovery lower bound−1e100 is uninformative. |
| CF1's intended larger-case mechanism remains unexercised |1 inspected50999/80 CF1 task, seed17/day. Model/inventory preparation exhausted its fixed6s completion window before CF1 optimization. Cold fallback24 vehicles/objective3386.2012021947876 was independently replay-valid. `research-20261023/CF1_PREPARATION_NATIVE_RESULTS.md`, `cf1-preparation-native-v2/accounting.json`. | Attributable acquisition/preparation timeout and a valid cold fallback, not charging infeasibility or CF1 quality. Symbolic CA1/CF1/pipeline passes of31/31/54 tests (`RECOVERY_CLASSICAL_CONTROLS_RESULTS.md`, `RECOVERY_CF1_RESULTS.md`, `RECOVERY_COMPARISON_PIPELINE_RESULTS.md`) are zero comparative-performance observations. |

## 2. A material objective/institution mismatch

The saved field called `bill` is
`ops_cost + native_hull.supply(market, load)` in
`src/experiments/codex_local_campaign.py:264`. The actual evaluator in
`src/egglab/native_hull.py:105` is

`F(L)=c+sum_t(a_t L_t + b_t L_t²/2)`.

This is an integrated supply-cost/planner objective. It is not automatically a
fleet's payment at the uniform clearing price `p_t(L)=a_t+b_t L_t`. An atomic
fleet paying that price on every unit pays
`c+sum_t(a_t L_t+b_t L_t²)`, whose marginal outlay is `a+2bL`.
With base load U, replace a by a+bU in both expressions. A genuinely posted,
exogenous tariff instead gives `c+p_post' L`. A nonlinear contract charging the
integral could make F a procurement payment, but that institution must be stated;
its marginal rate is not its average all-units clearing payment.

The repository already makes this distinction explicitly in
`src/egglab/market.py`: bill/system_cost_delta/marginal_outlay are separate.
Therefore preserve historical numbers/receipt field names, but describe the
screen's endpoint as **planner resource cost** in new scientific writing.
It does not establish strategic fleet payments, equilibrium welfare, an
implementable market or truthfulness. If the intended paper studies atomic
clearing-price payments, change/justify the objective prospectively and re-solve;
rescoring existing plans cannot identify decisions optimized for that other
objective. This mismatch is a substantive rejection risk, not a wording detail.

## 3. Claims to withdraw or narrow

- A strong baseline challenge has not been met. The comparator is a frozen cheap
  travel/gap/dwell score; graph/trees see linear prices while it does not.
  Rank-specific coverage unions also produce different retained cardinalities.
  Cold/full4 outcomes do not exhaust strong full-graph, LP-informed,
  charging-aware or route-neighborhood search.
- There is no demonstrated tariff-aware learning effect: one day regime,
  no counterfactual price-input intervention in the completed screen. At fixed
  vehicle count, lower electricity cost can still mean less energy or different
  routing. Graph's new CatBoost comparison is more informative than random wins.
-40/80 differences are not a causal size experiment: different timetable groups
  occupy the sizes. All share synthetic physics/borrowed TRAIN profiles; no
  external/sealed confirmation was performed. Endpoint failures/unknowns must
  retain fixed denominators, not be silently dropped or scored as opponent wins.
- Generic GNN electric-bus arc pruning is not a safe novelty claim. The existing
  `research-20261023/FT50_RESEARCH_STRATEGY.md` identifies direct prior art; this
  audit does not independently clear novelty. Recovery safety, classification
  AP and source-test counts are not substitutes for a methodological advantage.
- `research-20261024/REFEREE_ASSESSMENT.md` rejects the historical stabilization
  acceleration headline, unconditional3–5x scaling forecasts and sparse-menu ⇒
  zero-indivisibility-gap reasoning. Its historical/theory summaries are inherited
  here, not re-audited against protected outcomes. Price-support and implementable
  pure schedules remain distinct from convexified bounds.

Submitted now, the likely objections are underidentified mechanism, weak
classical competition, mismatched economic objective and limited independent
generalization. A credible contribution must survive those objections; journal
aspiration and further harness work supply no evidence that it will.

## 4. One decisive experiment: fleet-controlled ranking swap with full recovery

Freeze a **new8-base80-trip development study**,3 paired seeds,4 methods and2
fleet conditions:192 assigned decisions. Primary methods are frozen graph,
frozen new CatBoost, a credible classical charging-aware/LP-informed or
route-improvement proposal selected using TRAIN/inner evidence only, and tuned
unrestricted-from-start search. The classical proposal needs demonstrated
physical competence; the currently source-only CA1 label is not that evidence.
This targets the existing dominant80-trip result, not a new claim about size.

The two conditions allow free fleet choice or impose the SAME independently
replayed feasible vehicle count N for all arms on a base. Obtain N without any
compared ranker's scores and account for that preparation identically; retain
bases whose preparation fails. Do not condition on equal vehicle counts observed
after the methods run. Fixed N removes the dominant100-per-vehicle component by
construction; retain the free-fleet condition to measure whether that is the
only practical benefit.

For ranking arms use one common price-blind backbone and EXACT retained K, common
physics, incumbent admission, solver/round limits and a predeclared switch restoring
ALL original connections. Charge cold loading, scoring, construction, repair,
replay and finalization inside the same60s clock; preserve an identical feasible
fallback where specified. Cold search gets the same total allowance without
paying fictitious scoring cost. Interleave paired method order. Use the planner
F objective above; do not call this a strategic-payment experiment.

Record availability/unknowns first, then per-base paired cost trajectories,
time-to-feasibility, vehicle count, energy, linear/quadratic electricity costs,
retained-plan coverage and full/restored versus restricted bound provenance.
Treat3 seeds as within-base nuisance replication;8 bases support a discriminating
development decision, not broad population inference. No case replacement or
outcome-selected tariff/arm/timelimit. Existing `RECOVERY_ANALYSIS_CONTRACT.md`
supplies the useful integrity/failure precedence; the old192-cell addendum is
prospective, not completed evidence or this experiment's launch manifest.

**Decision rule:** if a strong classical method or cold search erases graph's
advantage, concede the ML/architecture anchor. If graph helps only free-fleet
early search, claim finite-budget fleet construction/search, not price learning.
If an advantage survives fixed N, equal K, strong classical/trees and full
restoration under paid end-to-end time, pursue that narrower decision-quality
mechanism. Equal K does not eliminate topology/search difficulty; useful learned
search guidance is a possible result, not an independent optimum difference.
Even this positive experiment would still need a separate price-input/tariff
intervention before claiming tariff-responsive learning. A new scientific budget,
qualification/endpoint contract and exact manifest are required; this audit
authorizes no run and borrows no engineering/shutdown reserve.
