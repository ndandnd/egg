# Model-family comparison: supervised edge scoring, then structured routing

## Scope

The admitted bank has 128 synthetic TRAIN timetables and 255 observed feasible-source fleets. The target is whether a movement appears in a saved feasible incumbent. An unselected movement is not known to be infeasible, suboptimal, or a bad route. This is incumbent-edge imitation; there is not yet evidence of a learned reduction in feasible-fleet cost or solver work. The model comparison should test whether a different scorer predicts this observed signal under the same group-safe protocol, not claim route quality from classification alone.

## Small, controlled model menu

Keep the current logistic, 32-unit MLP, and scikit-learn HistGradientBoosting models as anchors. Compare a narrowly fixed family set on the same four timetable-grouped folds and three seeds, using the existing fit/inner/outer partitions (80/16/32 groups for each 128-prefix task), same TRAIN-only feature table, and same equal timetable → observed fleet → movement sample weights.

| Family | Prospective candidates | Role and implementation controls |
|---|---|---|
| XGBoost classifier | `max_depth` 3 or 6; `n_estimators` cap 800; learning rate 0.05; inner early stopping after 50 rounds | Add regularization/subsampling only if fixed before the run; set `objective="binary:logistic"`, `eval_metric="logloss"`, `tree_method="hist"`, `n_jobs=1`, and the task seed. Pass fit weights as `sample_weight` and inner weights as `sample_weight_eval_set`. Use the single inner set for stopping; save `best_iteration`/`best_score`, and verify inference uses the selected iteration. |
| CatBoost classifier | depth 4 or 6; iterations cap 800; learning rate 0.05; inner early stopping after 50 rounds | Explicitly set binary Logloss, `thread_count=1`, seed, and `use_best_model=True`. Give `fit` the training weights; construct a weighted `Pool` for the inner `eval_set` so its stopping loss follows the same group/fleet/movement weighting. Save `best_iteration_`, `tree_count_`, and validation history; confirm the deployed prediction uses the selected trees. |
| ExtraTrees classifier | 300 trees; `min_samples_leaf` 5 or 20 | A non-boosted randomized-tree comparator. Use a fixed criterion and `max_features`, `random_state`, `n_jobs=1`, and the same `sample_weight`. There is no boosting early stop; select between the two leaf sizes using inner log loss only, or report them as two predeclared arms without choosing a winner from outer scores. Avoid automatic class balancing on top of the existing sample weights. |

These are candidate settings, not asserted optima. Pin exact XGBoost and CatBoost versions and capture constructor/fit configuration because early-stopping APIs have changed across library releases. For XGBoost, the sklearn API exposes both training and evaluation sample weights and uses `best_iteration` for prediction after early stopping; its documentation notes that the last evaluation set and last metric govern stopping when several are supplied. CatBoost exposes per-row training weights, weighted `Pool` inputs, a best-iteration attribute, and `use_best_model`; its documented default for trimming depends on the validation labels, so set it explicitly. ExtraTrees accepts `sample_weight`, and its `n_jobs` controls parallel tree operations. [XGBoost API](https://xgboost.readthedocs.io/en/stable/python/python_api.html), [CatBoost classifier fit API](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier_fit), [CatBoost classifier reference](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier), [scikit-learn ExtraTreesClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html).

## Selection and overfitting controls

Persist all candidate configurations and the selected inner iteration/tree count before accessing outer labels. Do not refit on the inner groups after stopping. The outer fold is a single evaluation of the inner-selected candidate. Report results per observed fleet and average within timetable first, then across the timetable groups; seeds are repeat fits, not additional independent cases. Keep the missing-source censor and denominators visible.

Use weighted log loss for the prespecified early-stop/inner selection rule. Report Brier score and calibration alongside average precision/PR-oriented metrics, fixed-threshold positive and negative recall, and input-trip-count top-k recall. The existing bank has sparse positive movement labels, so accuracy at 0.5 is especially uninformative; do not tune a threshold on outer labels. Report any threshold selected on inner data as part of the model. Do not use class reweighting that changes the target population unless it is a separately declared arm; preserve the existing timetable/fleet/edge sample weights.

Family or depth selection from outer results would reuse the evaluation data. Either make a single family/configuration choice from the inner sets within each training task, or publish each candidate as a separate predeclared arm and do not call the lowest outer score a selected model. A later locked test set or new generator/profile is needed to support a distribution-shift or generalization claim. No edge classifier, including these, establishes that selected edges form a feasible fleet; evaluate proposed scores with the route/charging decoder and report feasible plans, exact nonlinear costs, native solver status, and compute separately.

## Graph/attention direction after this comparison

After the tabular baselines, a useful neural step is a time-expanded movement graph encoder (message passing or attention over compatible trip/deadhead arcs), with edge scores passed to the existing constrained path-cover and charging stages. Keep timetable groups intact across folds, use only pre-solve case/market inputs as model features, and train only against clearly typed observed feasible-incumbent labels. Measure the full proposal → feasibility/charging → target-solve chain, including acquisition and inference cost. The graph model should demonstrate added value against the boosted-tree and constant/prior controls before expanding it.

RouteFinder is a relevant architecture reference: it uses a transformer encoder and attribute representations across 48 vehicle-routing variants, with multi-variant training and adaptation. Its results concern VRP-solving policies and rewards, not this supervised movement-membership task or EV timetable path-cover with fixed charging and a downstream optimizer. Treat it as design inspiration, not evidence of state-of-the-art performance here. [RouteFinder paper](https://arxiv.org/abs/2406.15007), [authors' project/code page](https://ai4co.github.io/routefinder/).

## Primary method references

- Chen and Guestrin, “XGBoost: A Scalable Tree Boosting System,” KDD 2016. [ACM DOI](https://doi.org/10.1145/2939672.2939785).
- Prokhorenkova et al., “CatBoost: Unbiased Boosting with Categorical Features,” NeurIPS 2018. [Proceedings](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html).
- Geurts, Ernst, and Wehenkel, “Extremely randomized trees,” *Machine Learning* 63, 3–42 (2006). [Springer DOI](https://doi.org/10.1007/s10994-006-6226-1).
