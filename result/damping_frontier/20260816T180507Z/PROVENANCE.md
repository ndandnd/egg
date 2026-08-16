# Damping-frontier certified snapshot

- Snapshot UTC: `20260816T180507Z`
- Campaign UTC: `20260815T033012Z`
- Source run root: Unicorn `~/egg/src/runs/overnight/20260815T033012Z/damping_frontier`
- Submission commit: `7a70500bcb05e32d75386a384dff82b55f3cf865`
- Collection code: `7ee9ed04a8deba67f037cd857c52b94dee3e7e87`
- Solve commits represented in records: `7a70500` (21,778), `fe2f229` (4,820)
- Grid: 16 seeds, 12 trips, `b in {0.01, 0.05}`, nine damping values, 240 iterations
- Expected/complete: 288/288 cells and 288/288 loops
- Records: 26,598, all `GRB` / `OPTIMAL`
- Replay: 163 raw legacy failures; 163 `certified_equivalent`; zero unresolved

`records.csv` is the canonical scalar table. `SUMMARY.md` is the gated audit
verdict. `checkpoints/` preserves outcomes and completion state;
`revalidation/` preserves exact-line-hash sidecars. `CAMPAIGN_MANIFEST.txt`
records the original Slurm design. Raw JSONL is intentionally not committed.
