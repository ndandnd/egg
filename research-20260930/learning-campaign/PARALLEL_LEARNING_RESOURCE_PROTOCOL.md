# Parallel label collection and exploratory route-learning pilot

## 1 October 2026 prospective extension

The original label and training pilots below are historical. The 128-group TRAIN
pool and v6 graph study are complete. Two versioned follow-ups are authorized
under the standing campaign budget, with source review and input freezing before
submission:

- v7 physical proposal comparison: 16 independent timetable tasks, at most four
  concurrent, one requested CPU and 8 GB each, 30 minutes each; eight requested
  CPU-hours maximum.
- v8 graph training-budget extension: 12 fold/seed tasks, at most four concurrent,
  one requested CPU and 8 GB each, one hour each; 12 requested CPU-hours maximum.

They may overlap, using at most eight requested CPUs and 64 GB, with at most four
training tasks. This fits the standing 12-CPU/96-GB ceiling. Both pin
`unicorn-cpu-75`, exclude `scaglione-compute-01`, use one native thread, preserve
failed work, and prohibit automatic retries or requeue. Their own protocols
define stricter stage and task caps. No new label shard is part of this extension.
Requested ceilings are not actual allocations or measurements; report those from
accounting after execution. A launch guard must reconcile any other active EGG
array before submitting either study.

These are exploratory TRAIN follow-ups. v7 tests whether saved held-out model
scores yield useful physical fleets after measured decoding, charging and replay.
v8 changes the optimization budget while holding graph mathematics and grouped
selection fixed; its 300-epoch anchor must reproduce v6 before later results can
be interpreted. Neither protocol opens development or sealed-test outcomes.

This protocol records the user's authorization for a bounded increase in compute for physical route labels and an exploratory model pilot. It supersedes the earlier wait-for-32-groups-before-any-fit rule. It does not open development or sealed-test cases, fit on their outcomes, or treat observed incumbents as optimal edge labels.

## Training-only label shards

Shard index 1 is already running on base groups 10008–10015. Launch the next seven immutable attempts, shard indices 2–8, covering training groups 10016–10071. Each shard contains eight independent base timetables and the frozen 64-cell design: two native source-market route solves and six fixed-source target charging labels per group. Keep the original case generator, source and target tariffs, physical replay, label semantics, source hashes, and no-retry behavior unchanged. Development IDs 20000–20031, sealed-test IDs 30000–30031, and historical reserved seeds 2004, 2005, 2020, and 2021 remain untouched.

Each label job requests one CPU, 8 GB, and two hours; caps numerical/native solver threads at one; has no requeue; and excludes `scaglione-compute-01`. Do not exceed eight concurrent label jobs, including shard 1 while it remains active. For the seven additional shards, the maximum requested allocation is 14 CPU-hours. At eight-way label concurrency, the requested label capacity is at most eight CPUs and 64 GB. Record requested resources and actual scheduler allocation separately because Slurm may round CPU allocations upward. Preserve each shard's own manifest, receipts, failures/censors, accounting, and immutable attempt path; never merge partial attempts by retrying an unreceipted child.

The scheduler snapshot used for the combined ceiling showed 224 eligible nodes on `default_partition` after excluding node 01 and nodes in down, drain, fail, or maintenance states, with 7,956 idle scheduler logical CPUs overall. Of these, 83 were CPU-only nodes with 1,315 idle logical CPUs. The `nc437/scaglione` association returned no configured `MaxJobs`, `MaxSubmit`, `MaxTRES`, or `GrpTRES` values; this is not a guarantee that requested capacity is reserved or immediately available. The combined requested ceiling below is 12 CPUs and 96 GB, including up to eight labels and four training tasks at once.

## Exploratory eight-group model pilot

In parallel with label collection, run the NumPy linear and small nonlinear route/edge scorer on only the already admitted eight-group shard-0 dataset and its 16 replayed source fleets. This is an explicitly exploratory pilot at eight independent training groups, not a promotion gate or a claim that eight groups suffice. Edge labels mean that a movement appears in a physically replayed incumbent; they do not mean the edge is globally or curved-cost optimal. Keep source solver status, physical feasibility, target costs, and any bounds out of training labels unless the frozen trainer contract explicitly uses them as separate training-only supervision.

Use four-fold grouped cross-validation by base timetable, with three declared random seeds per fold (12 independent training tasks). Each fold holds out entire base groups; all rows, candidate edges, markets, sources, and correlated labels from one base group stay on one side of the fold. Train preprocessing, feature selection, and model parameters on the fold's training groups only. Build numeric edge features from generator-defined pre-solve timetable, movement, energy, battery, and charging-availability attributes. Route membership in an observed incumbent is the label, never a feature; do not leak a held-out source plan's selected-edge set into that fold's predictors. Exclude IDs and split labels as predictive features, target outcomes/costs, solver status, bounds, failure and censor fields, replay outcomes, and paid times. Any serialized dataset or fold artifact must name the exact training and held-out base groups, seed, source dataset receipt/hash, feature schema/version, label definition, model configuration, and source-code hashes. A training input may contain labels only for its training groups; keep held-out labels in a scoring-only partition and join them only after predictions for that fold are saved. Do not reuse folds across seeds with changed group membership.

Each training task requests one CPU, 8 GB, and 30 minutes, uses one numerical thread, and has no automatic retry. Run no more than four training tasks concurrently, for a maximum of 12 tasks and six requested CPU-hours total. Limit combined label and training concurrency to 12 tasks, or at most 12 requested CPUs and 96 GB; report actual allocations from scheduler accounting. Training tasks are CPU work and do not use a GPU. A failed task or missing fold remains a failed/incomplete receipt, not a score imputed into the comparison.

## Interpretation and next checkpoints

Report fold-level and seed-level metrics alongside pooled metrics, with base groups as the independent resampling unit. Compare the linear scorer with the small nonlinear scorer and simple frozen baselines on held-out training groups. Describe results as exploratory out-of-group cross-validation; they are not independent development/test performance or validated deployment or route-cost gains. No model is used to select or relabel the concurrent shards. Preserve model/dataset versions and evaluate source-label completeness, topology diversity, and censoring as the shards arrive.

The current admitted eight groups support this small pilot because the user explicitly requested parallel model training. Continue collecting independent training groups. Revisit pooled learning curves at the predetermined registry prefixes of 32 groups (10000–10031), 64 groups (10000–10063), and 128 groups (10000–10127), with grouped splits and training-only hyperparameter choices. Do not substitute whichever later groups finish first for an incomplete or censored group inside a prefix; report incomplete groups and their label eligibility separately. Keep the 32 development groups sealed until a separate development protocol is frozen, and keep the 32 test groups sealed until the final architecture, thresholds, and analysis are frozen. The maximum registry remains 128 training groups; these are staged future checkpoints, not completed samples. Shard 1 plus shards 2–8 extend collection from the admitted first eight to at most 72 training groups.
