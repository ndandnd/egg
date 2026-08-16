# Fine-boundary certified snapshot

- Snapshot UTC: `20260816T180507Z`
- Campaign UTC: `20260815T033012Z`
- Source run root: Unicorn `~/egg/src/runs/overnight/20260815T033012Z/boundary_fine`
- Submission commit: `7a70500bcb05e32d75386a384dff82b55f3cf865`
- Collection code: `7ee9ed04a8deba67f037cd857c52b94dee3e7e87`
- Grid: eight seeds, 8/12 trips, slots 8/12/16/20, delta -1.5 to 1.5 by 0.01
- Expected/complete: 64/64 sweeps, including margin checks
- Records: 19,264, all `GRB` / `OPTIMAL`
- Replay: 19,264 raw-valid; zero unresolved

`records.csv` is the canonical scalar table. `SUMMARY.md` is the gated audit
verdict. `checkpoints/` preserves switch classifications, margins, and
completion state. `CAMPAIGN_MANIFEST.txt` records the original Slurm design.
Raw JSONL is intentionally not committed.
