# Claude takeover state (read this first on every wake-up)

Updated: 2026-10-01 ~05:45 UTC. Branch claude/research-20261001. Assessment: doc/CLAUDE_ASSESSMENT_20261001.md

## Cluster
- v8 array 738226: all 12 COMPLETED, collected 06:10 UTC.
- My jobs (all under ~/egg-claude-20261001/runs on unicorn2; code at ~/egg-claude-20261001/current):
  - E0 support: smoke 758455 done; array 758495 (15 groups) — runs/e0-support-20261001
  - E2 scale profile: array 758967 (18 cells, %2; raise to %3-4 when E0 done) — runs/e2-scale-20261001
  - E4 labels: smoke 759065 (g10000); full array (128 groups) NOT yet submitted — runs/e4-labels-20261001/cmds.txt
  - v8 scoring for E3: 759080 (graph env, no Gurobi) -> runs/e3-prune-20261001/scores_v8_day.json
- Gurobi concurrency rule: (#E0 + #E2 + #E3 + #E4lab running) <= 6.
- Limits: <=6 concurrent Gurobi processes; exclude scaglione-compute-01; never touch rvS*/tpmR*/537227 or other jobs.

## Queue of work (in order)
1. [x] Collect v8 -> research-20261001/v8-collection/V8_RESULTS.md (anchors pass; attention logloss 0.0543 vs v6 0.0719)
2. [x] E0 -> research-20261001/e0-support/E0_RESULTS.md (14/16 hulls certified; 4/16 certified positive gap, <=0.1% of bill)
3. [x] E1 -> research-20261001/e1-topology/E1_RESULTS.md (topology changes 14/16, bus count 16/16 fixed; cold fast)
4. [~] E2 cold time-to-quality profile (running 758967). Smoke: n=40 at 60 s -> 2.4% gap.
5. [ ] E3 predict-and-prune (driver claude_e3_prune.py; arms cold/learned/lp/random; keep 0.3; T=10,30 s bank; 60,300 s scale) after scores + E2
6. [ ] E4 tariff-diverse labels -> retrain (claude_e4_train.py, bank2 vs multi8, 4 folds) -> day eval + physical decode
7. [ ] v9 (Codex-prepared physical-context training) — optional; v8 showed epoch budget matters more; decide after E4
8. [ ] Google Doc: no Google Docs editor connector in this session; pending text in research-20261001/GOOGLE_DOC_PENDING.md

## Log
- 05:45 assessment committed.
- 06:10 v8 collected (anchors verified, big held-out gain). E0 launched (758495). E1 computed from saved v7 data (see research-20261001/e1-topology).
