# Physical training shard 1: admitted result

The existing v1 adapter admitted completed training shard index 1 (`10008–10015`) in one pass, with no adapter or execution-code changes. The immutable [dataset receipt](../../result/physical_learning/20260930-shard01-dataset-v1/dataset_receipt.json) hashes the frozen attempt, cell receipts, adapter policy and output tables. Its [health report](../../result/physical_learning/20260930-shard01-dataset-v1/health.json) and [compact derived evidence](PHYSICAL_SHARD01_DERIVED.json) support the counts below. This is an eight-independent-group **TRAIN-only** label bank; the already running route-model pilot remains frozen to shard 0.

| Evidence | Shard 1 |
|---|---:|
| Independent timetable groups | 8 |
| Replayed source fleets | 16/16 |
| Replayed fixed-route charging plans | 48/48 |
| Complete source0–source1 target-tariff pairs | 24/24 |
| Ties at exact-cost tolerance 0.000001 | 9 |
| Resolved source0 / source1 wins | 9 / 6 |
| Distinct source movement topologies | 14 across 16 fleets |
| Groups with identical source topology / full source plan | 2/8 / 0/8 |

Fifteen resolved comparisons occur across five groups (`10009`, `10010`, `10011`, `10012`, `10015`), with approximate paired margins from 0.360 to 9.112 cost units. Groups `10009` and `10011` switch their winning source fleet across target tariffs. Six of the nine ties are exactly equal; three have nonzero margins below tolerance. The three other groups have only tied paired costs. Each tariff variant shares its timetable, so this is **eight**, not 24, independent groups.

All 16 source solves returned feasible fleets: 11 ended `budget_exhausted` and five reported native `certified`. All 48 fixed-route charging solves report `OPTIMAL` for the pinned **linear-tariff LP**, with independent physical replay and exact curved-tariff scoring of their returned plans. These are observed procedure costs, not minima for the curved tariff or global physical optima. Source-market bounds remain separate from target outcomes.

The successful Slurm wrapper for job 711779 records 878 seconds, one allocated CPU, 8 GB, and zero return codes for freeze, preflight and controller; Slurm elapsed time was 881 seconds. Receipted source children used 588.26 seconds and charging children 203.40 seconds. The difference from allocation time covers setup, checks, replay and orchestration; it is not assigned to a particular label.

The increased topology and paired-cost variation is useful future source-fleet supervision, but it does not change the running eight-group route-model pilot or justify a learned selector claim. A later pooled route/edge fit can combine completed independent TRAIN shards with grouped validation and preserve the planned 32/64/128-group checkpoints. No new model was trained in this shard-1 admission step, and no development or reserved test cases were materialized.
