# Claude takeover state (read this first on every wake-up)

Updated: 2026-10-01 05:48 UTC. Branch claude/research-20261001. Assessment: doc/CLAUDE_ASSESSMENT_20261001.md

## Cluster (unicorn2; runs under ~/egg-claude-20261001/runs; code ~/egg-claude-20261001/current)
- DONE: v8 738226 (collected); E0 758455+758495 (written up); scoring 759080 (bank+scale), 759399 (public).
- RUNNING/QUEUED (check with: sacct -j <id> -X -o JobID,State,Elapsed):
  - E2 scale profile 758967 (18 cells, %2; 12 done, interim results written) -> runs/e2-scale-20261001/out/*/e2.json
  - E3 phase 2 (scale 40-80 trips, 120 runs incl cold4, %1) 761781
  - learned4 supplements: bank 761834 DONE; scale 765340 (after 761781), public 765341 (after 759670+759671) [resubmitted on harness-fixed code 0cd5da5; 761835/761836 cancelled while pending]
  - E3 bank harness-fix rerun 765335 (6 cells)
  - E3 bank prune 759091 (128 runs, %2) -> runs/e3-prune-20261001/out/*/e3.json
  - E4 labels 759102 (g10001-10127, %2; g10000 done by 759065) -> runs/e4-labels-20261001/out/g*/labels.jsonl
  - E4 train bank2 759111 (4 folds, graph env, no Gurobi) -> runs/e4-train-20261001/runs/bank2-f*
  - E5 public 759670 (Hildenbrand 20 runs incl. cold4, %1) and 759671 (Eberbach 10 runs, %1, 32G); first submission cancelled (see e5-public/PROTOCOL.md amendment)
  - E3 bank cold4 supplement 759672 (32 runs, %1)
- Gurobi rule: <= 8 of my Gurobi processes at once; exclude scaglione-compute-01; never touch other users'/projects' jobs.
- Deploy new code with scratchpad deploy.sh (ships src/ at HEAD; data/public already at ~/egg-claude-20261001/data).

## Queue of work (in order)
1. [x] Collect v8 -> research-20261001/v8-collection/V8_RESULTS.md (anchors pass; attention logloss 0.0543 vs v6 0.0719)
2. [x] E0 -> research-20261001/e0-support/E0_RESULTS.md (14/16 hulls certified; 4/16 certified positive gap, <=0.1% of bill)
3. [x] E1 -> research-20261001/e1-topology/E1_RESULTS.md (topology changes 14/16, bus count 16/16 fixed; cold fast)
4. [x] E2 final (18/18) -> research-20261001/e2-scale/E2_RESULTS.md: GO; cold MIP gaps 2-79% at 60-80 trips
5. [x] E3: bank DONE; scale DONE -> e3-prune/E3_SCALE_RESULTS.md (learned beats cold 10/2 @60s, 9/1/2 @300s; beats lp/random 12/12; ceiling effect at keep 30%); -> e3-prune/E3_BANK_RESULTS.md (learned >> random, > lp; vs cold small wins, big on hard 10069/10075); hfix rerun 765335; scale phase 761781 running (36/120) (driver claude_e3_prune.py; arms cold/learned/lp/random; keep 0.3; T=10,30 s bank; 60,300 s scale) after scores + E2
6. [ ] E4 tariff-diverse labels -> retrain (claude_e4_train.py, bank2 vs multi8, 4 folds) -> day eval + physical decode
6b. [x] E5 FINAL -> e5-public/E5_RESULTS.md: learned4 best in 6/6 public cells (beats cold4 6/6). E5 on public Hildenbrand 15/16 + Eberbach (scores 759399; protocol research-20261001/e5-public)
7. [ ] v9 (Codex-prepared physical-context training) — optional; v8 showed epoch budget matters more; decide after E4
8. [ ] Google Doc: no Google Docs editor connector in this session; pending text in research-20261001/GOOGLE_DOC_PENDING.md

## Log
- 05:45 assessment committed.
- 05:30 v8 collected (anchors verified, big held-out gain). E0 launched (758495). E1 computed from saved v7 data (see research-20261001/e1-topology).
- 05:48 E0 written up; E2/E3/E4/E5 running.
## Next actions for the heartbeat
1. [submitted 775356, dependency afterany:759102] E4 multi8 training (same cmd file pattern, --arm multi8, time 4h), then claude_e4_eval.py for bank2+multi8 (graph env), then claude_decode.py on v7 groups 10064-10079 with each arm's day_logits.json.
2. When 759091 finishes: summarize E3 bank (per case/T: bill per arm; wins vs cold/lp/random) -> research-20261001/e3-prune/E3_BANK_RESULTS.md.
3. When 758967 finishes: summarize E2 (time to first incumbent, to 0.5%/0.1% of own best, final gap, by size) -> research-20261001/e2-scale/E2_RESULTS.md; then submit E3 phase 2 on scale cases 50000-50003 x {40,60,80}, T {60,300}, %2 (scores already in runs/e3-prune-20261001/scores_v8_day.json).
4. When E5 finishes: summarize -> research-20261001/e5-public/E5_RESULTS.md (compare to paper bounds: depot15 D<=512.77 exact witness at flat a=0.2 — note E5 uses day tariff, so compare arms to each other).
5. Keep GOOGLE_DOC_PENDING.md updated at milestones.
6. [x] E4 bank2 reproduces v8 seed-17 (folds 1-3 within 1e-5; see e4 PROTOCOL note). multi8 waits for labels (43/128 at 07:20).
7. E5/E2: report build_seconds; on Eberbach the per-round model rebuild may dominate cold time.
8. When E2 (758967) finishes: raise E4 labels throttle back: scontrol update JobId=759102 ArrayTaskThrottle=2
- 06:25 heartbeat: E2 interim written; E3 phase 2 submitted (761781); E4 labels throttle back to 2 (10/128 done).
- 06:35 E5 first rows: single-budget cold stalls in round 1 (H15: 548.04 at 180 and 600 s), cold4 507.49, learned 509.35 -> added learned4 arm + dependent supplements.
- 07:30 heartbeat: E2 final; E3 bank results; harness fix (TimeoutError lost plans) + 6-cell rerun; scale/public learned4 resubmitted on fixed code. Scale main array 761781 runs on pre-fix code: rerun its TimeoutError cells with -hfix when it finishes.
- 08:25 heartbeat: E5 Hildenbrand done (learned beats cold 3/4; cold4 best at 600 s; learned4 pending 765341); hfix bank reruns done (all produced plans); E3 scale interim at 60 s: learned >> cold at 60-80 trips; GOOGLE_DOC_PENDING update 2 written. Throttles raised: E3 scale %2, E4 labels %3.
- 09:25 heartbeat: E5 Eberbach done -> E5_RESULTS.md interim; multi8 training queued (775356) after labels.
- 10:25 heartbeat: E4 labels done (879/896 replayed plans, 6.9 CPU-h); multi8 training running (775356); bank2 day-eval + decode submitted (779104); E5 final (learned4 best 6/6).
- 11:25 heartbeat: E3 scale written up; 2 cold4 artifact cells rerun (781391); multi8 trained (4 folds); bank2 day-eval+decode done; multi8 eval+decode submitted (781389).
