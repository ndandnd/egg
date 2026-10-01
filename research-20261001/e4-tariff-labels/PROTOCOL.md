# E4 protocol: tariff-diverse labels for price-responsive route scoring

Declared 2026-10-01 before launch. Motivation: E1 (topology changes with tariff in
14/16 groups) and the v7 diagnosis (learned routes forgo the midday discount). The
models already see window-price features, but each timetable has labels under only
two tariffs. Hypothesis: labels spanning many tariffs make edge scores respond to an
unseen tariff pattern.

Step 1, labels (`src/experiments/claude_e4_labels.py`): for each TRAIN timetable
10000-10127, cold curved planner (v7 cold budget: GRB, 1 thread, 55 s phase, 70 s
wall, 4 rounds) under 6 deterministic training tariffs (k=0 flat 0.15-0.30; k=1..5
one cheap window of 3-5 h at 0.05-0.15 over a 0.25-0.35 base, never >= 2 cheap hours
inside 10:00-14:00) plus the bank `day` tariff for evaluation only. Labels are time-
limited incumbents, not optima. 128 tasks, <= 4 concurrent Gurobi processes.

Step 2, training (`src/experiments/claude_e4_train.py`, graph environment): graph
attention, v6/v8 architecture/optimizer, <= 900 epochs, patience 30, FIT-only
preprocessing, INNER-only checkpoint selection. Arms: `bank2` (v8 data) vs `multi8`
(pool + 6 E4 labels). Four folds x seed 17 = 8 tasks (no Gurobi).

Evaluation (decided now, before any result):
- primary: OUTER-group average precision and log loss against the held-out `day_eval`
  cold incumbents, equal weight per timetable;
- secondary: physical decode on v7 groups 10064-10079 with each arm's day logits
  through the v7 repair + fixed-route charging + replay pipeline; bill vs v7 source
  policy and vs cold. Report all failures.
Go criterion for "price-responsive learning works": multi8 beats bank2 on day AP in
>= 3 of 4 folds AND lowers the mean physical bill gap to the cold incumbent.
DEV/TEST timetables remain sealed; everything here is TRAIN cross-validation.

## Trainer validation note, 07:35 UTC

bank2 (my trainer, attention, seed 17) vs the Codex v8 seed-17 attention runs:
fold 2 identical (selected epoch 897, inner 0.048746, outer 0.063661); fold 1 same
epoch 896, inner 0.050167 vs 0.050166, outer 0.041714 vs 0.041709; fold 3 epoch 893 vs
899, inner 0.056476 vs 0.056450. Differences are at the 1e-5 level and consistent with
different CPU nodes (v8 ran pinned to unicorn-cpu-75). The trainer reproduces v8.
