# Claude takeover state (read this first on every wake-up)

Updated: 2026-10-01 ~05:45 UTC. Branch claude/research-20261001. Assessment: doc/CLAUDE_ASSESSMENT_20261001.md

## Cluster
- v8 array 738226 (Codex, pre-handoff): tasks 0-8 COMPLETED, 9-11 RUNNING at 05:40 UTC. Collect once when all done; no retries.
- My jobs: none yet.
- Limits: <=6 concurrent Gurobi processes; exclude scaglione-compute-01; never touch rvS*/tpmR*/537227 or other jobs.

## Queue of work (in order)
1. [ ] Collect v8; verify 300-epoch anchor; write research-20261001/V8_COLLECTION.md
2. [ ] E0 hull-control rerun (typo fix) on v7 groups 10064-10079
3. [ ] E1 topology-response diagnostic (cold incumbents under source0/source1/day)
4. [ ] E2 cold time-to-quality profile at larger sizes
5. [ ] E3 predict-and-fix vs LP-score fixing vs cold, matched time
6. [ ] v9 training launch (after v8 anchor check)

## Log
- 05:45 assessment committed.
