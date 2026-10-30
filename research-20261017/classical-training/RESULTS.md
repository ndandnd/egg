# Classical baselines — completed initial bounded run

Newly trained comparators, not recovered historical v5 models. The exact TRAIN128 manifest passed strict admission; 255 observed source fleets across128 timetables (127 full pairs) were admitted. v8 task00 grouped split is80 fit/16 inner/32 outer; fit-only preprocessing matches the saved v8 values within1e-12. All source variants share a timetable partition.

| Arm | Selected inner setting | Fit log loss | Inner log loss | Exploratory outer log loss | Outer AP |
|---|---|---:|---:|---:|---:|
| logistic | {'C': 1.0} | 0.105716 | 0.099892 | 0.125602 | 0.591343 |
| catboost | {'depth': 6} | 0.055617 | 0.060034 | 0.078680 | 0.824320 |

Only inner weighted loss selected candidates. CatBoost depth6 selected266 trees; depth4 selected591. Their inner losses differ by only0.000012, so depth selection should not be interpreted as meaningful superiority. Logistic convergence warnings: none. Both arms selected/saved before any outer diagnostics. No refit, arm promotion, outcome-dependent expansion, or solver calls.

Outer is reused historical TRAIN-bank cross-validation and one fold/seed; it is not an independent benchmark. Labels imitate feasible observed source plans and do not identify optimal or uniquely good edges. Table metrics are timetable-balanced via equal group/source/edge weights. Per-group and macro metrics are preserved. Neither AP nor log loss establishes downstream pruning value. No comparison to v8 outer metrics on different fold mixtures is valid.

Training wall 20.687 seconds; CPU 19.397 seconds, CPU thread1. The complete candidate menu was bounded before execution; all four models/metrics retained, no training failures.

Selected inference roots:

- `attempt1/logistic/model.joblib`
- `attempt1/catboost/model.cbm`

Each selected folder has `metadata.json` (model and training-source SHA256), `preprocessing.json` (feature names, numeric fit-only values, complete split), and model. Root receipt includes pool hashes, pinned versions, all candidate config/loss/curves, sample eligibility, limits and runtime. `outer_exploratory_predictions.json` retains movement-aligned scores; no test data used.

Inference: `from experiments.codex_train_classical import score_case`; call `score_case(case, prices, model_dir, arm)` with model_dir=`research-20261017/classical-training/attempt1`, arm=`logistic` or `catboost`. Returns case_identity, movement_ids, finite raw logits, total cold score_seconds, cold_load_seconds (feature preparation plus model load), inference_seconds, model_metadata. Cold-library import time is charged in total scoring. Inference smoke on existing exploratory scale50000:40 produced aligned finite vectors for both arms; no scale labels read. Results retained in `attempt1/inference_smoke_scale50000_40.json`.

Reproduce into a fresh output directory:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=src .venv-local/bin/python -m experiments.codex_train_classical --pool /Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3 --split /Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/fit_only_preprocessing_and_groups.json --output research-20261017/classical-training/new-attempt
```
