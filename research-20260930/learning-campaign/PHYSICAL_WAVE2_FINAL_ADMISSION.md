# Physical-learning wave 2 final admission

Shards 10–15 were admitted once each from their collected attempts by the existing replay-only adapter. All six dataset receipts are complete TRAIN-only admissions. No training fit or native optimization was run. The exact 128-group pool was then created once by the v3 pool builder, which reads only the admitted receipts and case/source-input tables.

| Shard | Base IDs | Job | Wrapper s | Source native status (certified / budget-exhausted) | Source replay | Target replay/status | Target censors / pair exclusions |
|---:|---|---:|---:|---|---:|---|---|
| 10 | 10080–10087 | 715491 | 769 | 7 / 9 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |
| 11 | 10088–10095 | 715492 | 799 | 4 / 12 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |
| 12 | 10096–10103 | 715493 | 849 | 4 / 12 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |
| 13 | 10104–10111 | 715494 | 799 | 4 / 12 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |
| 14 | 10112–10119 | 715495 | 911 | 3 / 13 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |
| 15 | 10120–10127 | 715496 | 704 | 4 / 12 | 16/16 returned | 48/48 (OPTIMAL 48) | 0 / 0 |

Across this wave, 48 timetable groups produced 96/96 returned source fleets and 288/288 target-label replays. Source native statuses were 26 certified and 70 budget-exhausted; target-label native status was OPTIMAL for all 288 labels. That OPTIMAL status describes the target-label LP solves, not a global curved-cost fleet optimum. The wave had zero censored labels or pair exclusions. Per-job wrapper receipts show return code 0, preflight/controller/freeze return codes 0, no timeout, one requested and allocated CPU, and 8192 MB; the displayed times are per-job wrapper elapsed seconds, not campaign wall time. Their sum (4831 seconds) is not elapsed campaign time.

The exact pool is `result/physical_learning/20260930-route-pool128-v3` with manifest SHA-256 `d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`. It preserves all 128 registry groups: 128 groups have at least one observed source and 127 have both. There are 255/256 observed/intended source fleets. The sole missing fleet is source0 for base 10037; its observed source1 remains available for observed-source supervision, and the known dependent target censors remain represented in the shard-04 provenance. No missing source label was imputed and no registry group was dropped.

The pool exports only cases and source inputs; target outcome tables were not included. It does not replay plans, fit a model, or run an optimizer. Receipt paths, hashes, per-shard counts/statuses, and pool eligibility are in [PHYSICAL_WAVE2_FINAL_ADMISSION.json](PHYSICAL_WAVE2_FINAL_ADMISSION.json).
