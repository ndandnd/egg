# Claude takeover state (read this first on every wake-up)

Updated: 2026-10-01 ~05:45 UTC. Branch claude/research-20261001. Assessment: doc/CLAUDE_ASSESSMENT_20261001.md

## Cluster
- v8 array 738226: all 12 COMPLETED, collected 06:10 UTC.
- My jobs: E0 smoke 758455 (done, g10074); E0 array 758495 (15 groups, %4).
- Limits: <=6 concurrent Gurobi processes; exclude scaglione-compute-01; never touch rvS*/tpmR*/537227 or other jobs.

## Queue of work (in order)
1. [x] Collect v8 -> research-20261001/v8-collection/V8_RESULTS.md (anchors pass; attention logloss 0.0543 vs v6 0.0719)
2. [ ] E0 hull-control rerun (typo fix) on v7 groups 10064-10079
3. [x] E1 -> research-20261001/e1-topology/E1_RESULTS.md (topology changes 14/16, bus count 16/16 fixed; cold fast)
4. [ ] E2 cold time-to-quality profile at larger sizes
5. [ ] E3 predict-and-fix vs LP-score fixing vs cold, matched time
6. [ ] v9 training launch (after v8 anchor check)

## Log
- 05:45 assessment committed.
- 06:10 v8 collected (anchors verified, big held-out gain). E0 launched (758495). E1 computed from saved v7 data (see research-20261001/e1-topology).
