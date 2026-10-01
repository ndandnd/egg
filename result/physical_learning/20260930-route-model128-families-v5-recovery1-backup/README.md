# XGBoost / CatBoost / ExtraTrees recovery backup

These nine gzip tar archives contain all 405 collected files from array 722702,
including models, predictions, learning curves, source identities, runtime probes
and completion receipts. All archive members were read back and their byte sizes
and SHA256 hashes checked against the collected originals. The original files
remain locally and in `/home/nc437/egg-route-families-20260930-v5-recovery1` on Unicorn.

The raw files total 1,147,974,327 bytes; the archives total 455,084,392 bytes. This
lossless packaging avoids adding a second uncompressed copy of the large tree
models to Git. It does not change any model or scientific result.

From the repository root, restore an individual task with:

```sh
tar -xzf result/physical_learning/20260930-route-model128-families-v5-recovery1-backup/task00.tar.gz
```

Repeat for the other listed archives to run the full combined-cohort replay.
Paths inside the archives are relative to the repository root. Compare restored
files with `research-20260930/learning-campaign/RESULT_MANIFEST_ROUTE_FAMILIES_V5_RECOVERY1.json`.
The reproducible packaging and byte-verification script is
`research-20260930/learning-campaign/archive_route_families_v5_recovery.py`.

This recovery supplies tasks 0, 1, 4, 5, 6, 7, 8, 9 and 11. Original successful
tasks 2, 3 and 10 remain in `20260930-route-model128-families-v5`; original failed
attempts and their spent time are retained separately.
