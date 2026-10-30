# Claude takeover summary (1 Oct 05:15 UTC – 2 Oct 05:30 UTC)

Paused at the user's request on 2 October ~05:30 UTC; the project passes to GPT
(`doc/GPT_HANDOFF_20261002.md`). Claude's hourly heartbeat, the scheduled wrap-up and the
5-minute cluster yield loop are stopped. Branch `claude/research-20261001`; the Codex
branch was never modified.

## What was run

13 experiments (E0-E11 plus collecting Codex's v8), each with a protocol written before
launch and a results file. About 1,000 cluster runs; all failures and harness artifacts
are recorded (see each results file). Results index: `doc/GPT_HANDOFF_20261002.md`
Section 2.

## Main findings

1. **Learned pruning accelerates complete-fleet scheduling.** Keeping only the movements a
   graph-attention scorer ranks highest (plus a per-trip floor) and solving the reduced
   MIP beats unpruned solving at equal wall time beyond ~40 trips (E3, E6), on the public
   Hildenbrand and 105-service Eberbach networks (E5), and robustly across Gurobi seeds
   (E11 interim: 17-18/18 seed-paired wins). Learned scores beat LP-relaxation and random
   rankings decisively, so the gain is not just problem shrinkage.
2. **How much to keep depends on size and distribution shift** (E6, E8); a per-trip top-m
   rule (m = 5-8) adapts without tuning (E10).
3. **Tariff-diverse labels make learned routes price-responsive** (E4) but the gain does
   not transfer to public networks (E7).
4. **Price support:** 4/16 bank timetables have certified positive physical-minus-hull
   gaps (E0, <= 0.1% of the bill). Learned plans tighten hull enclosures at 40-80 trips
   (E9) but certification there still needs a stronger pricing oracle.
5. **Reliability risk:** native solutions occasionally fail exact replay or the charge-
   projection roundoff check, most often on long pruned Eberbach solves (E10).

## Still on the cluster

- `798833` (E11, `egg-claude-e11`): 24 of 96 runs pending (seed 3 remainder), held at
  `Nice=10000` and throttle 1 so it always yields; nothing of Claude's is running.
  Outputs: `~/egg-claude-20261001/runs/e11-seeds-20261001/out/`. To finish the analysis:
  `python research-20261001/e11-seeds/summarize.py <out dir>`. Cancel with
  `scancel 798833` if no longer wanted.
- `~/egg-claude-20261001/yield_check.sh` remains available but is no longer run
  automatically.

## Recommended next steps

1. GPT: post `GOOGLE_DOC_PENDING.md` (six updates) to the research log; complete the SOTA
   review (handoff Section 5).
2. Replay-robustness study (tolerances / repair) before scaling pruning further.
3. Predict-and-search style fixing with recovery, and a model trained on public-like
   synthetic variants, to fix the synthetic-to-public transfer gap.
4. A stronger pricing oracle (charging-aware labeling / branch-and-price) for hull
   certification at 40+ trips.
5. Then a pre-registered evaluation on the sealed DEV groups and additional public
   networks.
