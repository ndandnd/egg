# Shard 09 admission

The replay-only physical-learning adapter admitted shard 09 once into `result/physical_learning/20260930-shard09-dataset-v1`. It contains eight TRAIN timetable groups (base IDs 10072–10079), with 16/16 source-fleet replays returned and 48/48 target-label replays admitted. All eight groups have both source variants and all three target tariff pairs; 24/24 target pairs are eligible. There are zero censored labels, source-pair exclusions, or target-pair exclusions.

Source solver status remains mixed: 4/16 source plans are certified and 12/16 have `budget_exhausted` status. The saved target-label native statuses are `OPTIMAL` for all 48 rows; this describes those target LP solves, not a global curved-cost fleet optimum. The adapter did no model fit or new native optimization.

The wrapper receipt for job 715490 reports successful completion in 606 seconds, no timeout, one requested and allocated CPU, and 8 GB. Machine-readable counts and receipt hashes are in [PHYSICAL_SHARD09_ADMISSION.json](PHYSICAL_SHARD09_ADMISSION.json). The admitted dataset pointer is `result/physical_learning/20260930-shard09-dataset-v1/dataset_receipt.json` (SHA-256 `798d580efb066f93ec2df78e69f61b5b23cab68dab7c0a9ca74eec0700b34132`).
