# Phase 1 certified snapshot

- Snapshot UTC: `20260816T180507Z`
- Source run root: Unicorn `~/egg/src/runs/phase1`
- Collection code: `7ee9ed04a8deba67f037cd857c52b94dee3e7e87`
- Solve commits represented in records: `cebe909` (2,983), `fe2f229` (1,148)
- Expected/complete: 128/128 cells, 128/128 loops, four static regimes per cell
- Records: 4,131, all `GRB` / `OPTIMAL`
- Replay: 18 raw legacy failures; 18 `certified_equivalent`; zero unresolved

`records.csv` is the canonical scalar table produced by the hardened collector.
`SUMMARY.md` is the gated audit verdict. `checkpoints/` preserves loop outcomes
and completion state; `revalidation/` preserves exact-line-hash sidecars and the
revalidation manifest. Raw JSONL is intentionally not committed.
