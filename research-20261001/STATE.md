# Claude takeover state (read this first on every wake-up)

Updated: 2026-10-01 ~05:45 UTC. Branch claude/research-20261001. Assessment: doc/CLAUDE_ASSESSMENT_20261001.md

## Cluster (unicorn2; runs under ~/egg-claude-20261001/runs; code ~/egg-claude-20261001/current)
- DONE: v8 738226 (collected); E0 758455+758495 (written up); scoring 759080 (bank+scale), 759399 (public).
- RUNNING/QUEUED (check with: sacct -j <id> -X -o JobID,State,Elapsed):
  - E2 scale profile 758967 (18 cells, %2) -> runs/e2-scale-20261001/out/*/e2.json
  - E3 bank prune 759091 (128 runs, %2) -> runs/e3-prune-20261001/out/*/e3.json
  - E4 labels 759102 (g10001-10127, %2; g10000 done by 759065) -> runs/e4-labels-20261001/out/g*/labels.jsonl
  - E4 train bank2 759111 (4 folds, graph env, no Gurobi) -> runs/e4-train-20261001/runs/bank2-f*
  - E5 public 759411 (Hildenbrand 16 runs, throttled %1) and 759412 (Eberbach 8 runs, %1, 32G)
- Gurobi rule: <= 8 of my Gurobi processes at once; exclude scaglione-compute-01; never touch other users'/projects' jobs.
- Deploy new code with scratchpad deploy.sh (ships src/ at HEAD; data/public already at ~/egg-claude-20261001/data).

## Queue of work (in order)
1. [x] Collect v8 -> research-20261001/v8-collection/V8_RESULTS.md (anchors pass; attention logloss 0.0543 vs v6 0.0719)
2. [x] E0 -> research-20261001/e0-support/E0_RESULTS.md (14/16 hulls certified; 4/16 certified positive gap, <=0.1% of bill)
3. [x] E1 -> research-20261001/e1-topology/E1_RESULTS.md (topology changes 14/16, bus count 16/16 fixed; cold fast)
4. [~] E2 cold time-to-quality profile (running 758967). Smoke: n=40 at 60 s -> 2.4% gap.
5. [~] E3 predict-and-prune (bank phase running 759091; early: learned < cold on 3/3 at 10 s, random far worse) (driver claude_e3_prune.py; arms cold/learned/lp/random; keep 0.3; T=10,30 s bank; 60,300 s scale) after scores + E2
6. [ ] E4 tariff-diverse labels -> retrain (claude_e4_train.py, bank2 vs multi8, 4 folds) -> day eval + physical decode
6b. [ ] E5 learned pruning on public Hildenbrand 15/16 + Eberbach (scores 759399; protocol research-20261001/e5-public)
7. [ ] v9 (Codex-prepared physical-context training) — optional; v8 showed epoch budget matters more; decide after E4
8. [ ] Google Doc: no Google Docs editor connector in this session; pending text in research-20261001/GOOGLE_DOC_PENDING.md

## Log
- 05:45 assessment committed.
- 06:10 v8 collected (anchors verified, big held-out gain). E0 launched (758495). E1 computed from saved v7 data (see research-20261001/e1-topology).
- 08:15 E0 written up; E2/E3/E4/E5 running.
## Next actions for the heartbeat
1. When 759111 (bank2) finishes AND 759102 labels finish: submit E4 multi8 training (same cmd file pattern, --arm multi8, time 4h), then claude_e4_eval.py for bank2+multi8 (graph env), then claude_decode.py on v7 groups 10064-10079 with each arm's day_logits.json.
2. When 759091 finishes: summarize E3 bank (per case/T: bill per arm; wins vs cold/lp/random) -> research-20261001/e3-prune/E3_BANK_RESULTS.md.
3. When 758967 finishes: summarize E2 (time to first incumbent, to 0.5%/0.1% of own best, final gap, by size) -> research-20261001/e2-scale/E2_RESULTS.md; then submit E3 phase 2 on scale cases 50000-50003 x {40,60,80}, T {60,300}, %2 (scores already in runs/e3-prune-20261001/scores_v8_day.json).
4. When E5 finishes: summarize -> research-20261001/e5-public/E5_RESULTS.md (compare to paper bounds: depot15 D<=512.77 exact witness at flat a=0.2 — note E5 uses day tariff, so compare arms to each other).
5. Keep GOOGLE_DOC_PENDING.md updated at milestones.
