# Tree-family comparison on 128 TRAIN timetables

XGBoost and CatBoost are competitive with the existing histogram-boosted model,
with small improvements in the full-cohort averages. ExtraTrees does not improve
the main scores consistently. The prospectively defined inner-validation family
selector also provides no clear advantage over the existing baseline. These are
movement-classification results; they do not establish cheaper feasible fleets or
less online solving.

| Model, full 128 timetables | Log loss ↓ | Average precision ↑ | Trip-count top-k recall ↑ |
|---|---:|---:|---:|
| Logistic, v3 | 0.11071 | 0.66402 | 0.60366 |
| MLP32, extended budget v4 | 0.084204 | 0.747740 | 0.673704 |
| Histogram boosting, v3 | 0.069894 | 0.824254 | 0.691360 |
| Histogram boosting, extended budget v4 | 0.070373 | 0.825155 | 0.696634 |
| XGBoost, v5 | 0.069417 | 0.828270 | 0.696686 |
| CatBoost, v5 | 0.069298 | 0.826484 | 0.697748 |
| ExtraTrees, v5 | 0.070502 | 0.822407 | 0.692599 |
| Inner-selected family policy, v5 | 0.070127 | 0.826256 | 0.693924 |

Each timetable receives equal weight after averaging seeds and its observed source
fleets. The 12 fold/seed tasks are not 12 independent datasets. All methods use the
same frozen 128-group pool with 255 source fleets, the same 17 features, and the
same grouped fit/inner/outer partitions. One source for timetable 10037 remains
censored; it was not replaced or imputed. Labels identify movements in observed
feasible incumbents, not optimal-route membership. Top-k uses the number of input
trips; it is a ranking diagnostic, not a route decoder.

The original-32 subgroup gives the same broad picture rather than a uniformly
better family: XGBoost/CatBoost/ExtraTrees log losses are
0.069411/0.069074/0.069532 and top-k recalls are
0.703658/0.698303/0.694823. The original histogram model gives
0.069285 and 0.700663 on this subgroup. These are descriptive comparisons within
a repeatedly explored TRAIN bank, not a final independent test.

Configuration and family promotion used inner weighted log loss only. XGBoost
depths 3/6 were selected in 3/9 tasks, CatBoost depths 4/6 in 3/9, and ExtraTrees
leaf size 20 in all 12. The frozen family selector chose XGBoost in nine tasks and
ExtraTrees in three. CatBoost's slightly better full-cohort outer mean does not
change that selection rule. No outer-based winner is promoted by this report.

The [saved-model replay](ROUTE_FAMILIES_V5_REPLAY.json) checks 72 candidate models
against their fit/inner records, and 36 selected models against outer predictions.
It verifies source lineage, folds, preprocessing, weights, candidate choice and
family promotion without fitting models or opening development/final-test data.
XGBoost uses its explicit best-iteration range, CatBoost its retained tree count.
There is a documented numerical qualification: local macOS XGBoost probabilities
differ from saved Linux probabilities by at most two float32 ULPs (1.19e-7), so
they are not bitwise identical. Complete source rankings, fixed-half decisions and
the inner choices remain unchanged. Saved-prediction metrics are independently
recomputed to a 1e-12 tolerance. CatBoost differs by at most 1.11e-16 and ExtraTrees
reproduces probabilities exactly. The verifier and JSON preserve the initial
1e-8 check failure and the subsequent numerical diagnostics.

Original array 720831 supplied successful tasks 2, 3 and 10; all nine other tasks
failed with SIGILL before candidate training. Recovery 722702 kept the scientific
configuration and all 18 original source hashes, and completed precisely those
nine tasks on unicorn-cpu-75. Native import and tiny-fit probes passed before
training. The original offending library/CPU instruction remains unproven. All
failures and time are retained: original plus recovery totals are 1,784 elapsed
task-seconds and 1,973 allocated CPU-seconds, including 79 failed-task seconds.
Requested and allocated CPUs are separate; one original task was allocated two.

All 405 recovery files remain locally and remotely. Their
[lossless archive manifest](RESULT_MANIFEST_ROUTE_FAMILIES_V5_RECOVERY1.json)
records byte-for-byte verification of the Git backup; no original result was
overwritten. [Runtime and result review](ROUTE_FAMILIES_V5_RESULT_REVIEW.md) records
the independent checks. Baseline results come from
[v3](ROUTE_MODEL128_RESULTS.md) and [v4](ROUTE_MODEL128_BUDGET_V4_RESULTS.md), with
hash-pinned per-timetable comparisons in the replay JSON.

The next scientific question is whether these scorers or the pending graph models
produce useful physical fleet proposals. Evaluate prediction, decoding/repair,
charging and global verification separately against cold solving, retained plans,
retrieval and exact rescoring. Prior matched charging erased the apparent gains in
the small decoder pilot, so improved edge scores alone are insufficient. Explicit
battery/SOC and charger-context features remain a versioned follow-up: current
models, including the graph pilot, inherit a feature set without that context.
