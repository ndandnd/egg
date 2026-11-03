# Complete graph v6 experiment backup

These 36 lossless gzip tar archives contain all 12,770 collected files from array
722841: both models' saved epochs, selected NPZ weights, predictions, curves,
provenance, native probes and completion receipts. Raw artifacts remain locally
and in `/home/nc437/egg-route-graph-20260930-v6` on Unicorn.

Archives are divided by task and model arm, with a metadata archive for each task.
They contain 1,348,963,777 original bytes in 805,271,829 compressed bytes. Every
archived member was read back and checked against the original size and SHA256;
the manifest also checks complete, nonduplicated member coverage. No scientific
artifact was removed or replaced by a selected subset.

To restore one archive, from the repository root run:

```sh
tar -xzf result/physical_learning/20260930-route-model128-graph-v6-backup/task00_metadata.tar.gz
```

Restore all three archives per task for a complete replay. Paths are relative to
the repository root. Check restored files against
`research-20260930/learning-campaign/RESULT_MANIFEST_ROUTE_GRAPH_V6.json`.
The packaging and byte-verification script is
`research-20260930/learning-campaign/archive_route_graph_v6.py`.

External Slurm stderr files are included in `slurm_logs`; the separate log receipt
preserves hashes and locations of complete stdout/stderr logs. Scientific runtime
probe output is already inside the task metadata archives.
