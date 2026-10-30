# Physical training shard 0: admitted result

The v2 composite adapter admitted the completed continuation and the archived preempted parent as one **TRAIN-only** shard. Its immutable [dataset receipt](../../result/physical_learning/20260930-shard00-composite-v2/dataset_receipt.json) hashes the two attempts, their receipts and evidence, the adapter policy, and the five output tables. The [health report](../../result/physical_learning/20260930-shard00-composite-v2/health.json) and [compact derived counts](PHYSICAL_SHARD00_DERIVED.json) support the figures below. No model was fit and no development or test case was opened.

| Evidence | Count |
|---|---:|
| Independent TRAIN timetable groups | 8 |
| Replayed source fleets | 16/16 |
| Replayed target charging plans | 47/48 |
| Interrupted unreceipted target cell, censored | 1/48 |
| Groups with all three complete paired tariffs | 7/8 |
| Eligible source0–source1 charging comparisons | 23/24 |
| Ties within the prespecified exact-cost tolerance, 0.000001 | 20/23 |
| Non-ties (source0 / source1) | 2 / 1 |

Fourteen ties have exactly zero cost margin; six have a nonzero margin below the tolerance. All three meaningful margins arise in **one** control-80, 28-service group (`10003`): source0 wins late by about 0.9750, source1 wins day by 1.4635, and source0 wins flat by 0.5859. The other seven groups offer no resolved source-choice supervision at this tolerance. Price response in group 10003 is descriptive, not evidence that a learned selector transfers.

The two source full plans differ in all eight groups; their selected movement topology is identical in five groups. There are 11 distinct replayed source topologies across 16 fleets. All 16 source solves returned feasible plans; 13 ended `budget_exhausted` and three reported native `certified`. All 47 receipted charging LPs report `OPTIMAL` for their *linear* tariff procedure. Their saved plans pass independent physical replay and are scored with the exact curved tariff; neither the LP status nor source solver status certifies a curved-cost or global physical optimum. Source-market bounds remain separate from target labels.

Job 703461 was PREEMPTED after 713 Slurm seconds. It preserved 40 receipted cells (667.82 paid child seconds), including 16 sources and 24 target plans; the next launched target had no child receipt or usable label. Continuation job 709011 completed in 155 Slurm seconds, with a 149-second wrapper and 107.67 paid child seconds, and produced all 23 previously never-launched target plans. Across the admitted shard, receipted source children used 558.80 seconds and target children 216.69 seconds. Parent allocation time is reported separately; none is imputed to the interrupted cell. The continuation requested one CPU and 8 GB, though Slurm allocated two logical CPUs; its peak RSS was 184,868 KiB.

**Next prospective step:** run unchanged training shard index 1, base IDs `10008–10015`, under the already frozen physical generator and 64-cell source-plus-three-tariff label protocol. Keep the one-CPU, 8-GB, one-thread, two-hour, no-requeue/exclude-01 request and preserve any preemption as a new censored event rather than retrying a launched cell. This expands independent timetables and physical regimes before fitting a model; eight groups with only one informative source-choice group cannot support a credible adaptive selector. The useful next implementation is pooled **route/edge-proposal training from source-fleet supervision**, not another selector adjustment to these nearly tied target pairs. Retain the existing 32-group pooled-fit checkpoint, keep groups intact, and evaluate any learned route proposal on independent development groups. No trainer is implemented or fit in this result package.
