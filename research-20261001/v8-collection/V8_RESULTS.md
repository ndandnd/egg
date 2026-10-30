# v8 longer graph training: collected once, 1 October 2026

Array 738226 (submitted by Codex before the handoff; recovery attempt of v8, source
commit a19f0acc). All 12 fold/seed tasks COMPLETED with exit 0 on unicorn-cpu-75,
1 CPU / 8 GB each, 1609-2500 s per task (about 7.5 CPU-hours total). Collected once;
nothing retried. Raw weights stay on the cluster
(`~/egg-route-graph-budget-20261001-v8-recovery1/result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1`).

## Anchor verification (required before interpretation)

Every task reports `both300_anchors_verified = true`: for both arms, all 300 shared
epochs reproduce the v6 losses, strict-improvement decisions and saved probabilities
with maximum difference 0.0 (tolerance 1e-10). Longer-training results are admissible.

## Training behaviour

| Arm | Completed epochs (12 tasks) | Inner-selected epoch |
|---|---|---|
| graph attention | 900 in 10 tasks; 673 and 606 (patience stop, seed 43) | 576-899; within 4 epochs of the end in 9 tasks |
| mean message | 660-900 | 630-900 |

Attention was INNER-promoted in all 12 tasks. Most selected epochs are again at the
cap, so the attention model is probably still undertrained at 900 epochs.

## Held-out (OUTER) fold metrics, equal weight per timetable, mean of 3 seeds

| Model | Log loss | Average precision | Trip-count top-k recall |
|---|---:|---:|---:|
| v6 graph policy (300 epochs) | 0.071888 | 0.842573 | 0.739570 |
| v8 mean message (<= 900) | 0.056748 | 0.891239 | 0.759632 |
| **v8 graph attention = INNER policy (<= 900)** | **0.054297** | **0.899126** | **0.764452** |
| CatBoost v5 (best tree) | 0.069298 | 0.826484 | 0.697748 |

Longer training lowers log loss by 24% relative to v6 and now beats every tree model
on all three metrics. Scope: the same repeatedly inspected 128-timetable TRAIN bank
(exploratory cross-validation, DEV/TEST still sealed); labels are feasible
incumbents under the `source0`/`source1` tariffs, not optima. Better edge ranking has
not yet been shown to give cheaper fleets (v7). The v8 models are the score source for
the E3 predict-and-fix experiment.
