# EGG handoff to GPT — 16 October 2026, 17:48 EDT (Claude stopping for usage reset)

Read with: `research-20261016/STATE_MAP_20261016.json` (five structured reader reports:
state+priorities, protocol specs, ML quality, replay root cause, prior art — produced today
by parallel readers over the SOTA review, protocols, E0-E11 results, code and primary
literature). Previous context: `research-20261001/TAKEOVER_SUMMARY.md`, your own
`codex/sota-review-20261002` branch (SOTA_REVIEW.md, protocols/, notes/).

## Nothing is running

No EGG cluster jobs; no local jobs; the analysis workflow was stopped after its five readers
finished (only the optional completeness critic was cut). EGG has been idle since 2 Oct.

## New facts from today

1. **Local compute is available and is the right place for EGG now.** The Unicorn queue is
   saturated by the evspv2g stochastic project (~3,000 `v2g*` tasks queued/running on
   16 Oct); EGG must yield to it. The user's Mac (Apple M3 Pro, 12 cores, 18 GB) has a FULL
   Gurobi academic license (`~/gurobi.lic`, expires 2027-02-11, Gurobi 12.0.1) plus
   gurobipy, torch 2.4.1, numpy 1.26.4, scipy 1.13.1, PySCIPOpt.
   - Isolated venv with python-mip 1.17.6 on top of system packages:
     `/Users/nadan/Documents/ChatGPT/egg/claude-research-20261001/.venv-claude`
     (git-excluded). Run drivers from `src/` with `PYTHONPATH=. OMP_NUM_THREADS=1
     ../.venv-claude/bin/python -m experiments.<driver>`.
   - Local data (outside git): `/Users/nadan/Documents/ChatGPT/egg/claude-local/`
     — v8 models (`v8/taskXX/inner_progress/{graph_attention,mean_message}_selected.npz`,
     preprocessing), training pool `20260930-route-pool128-v3`, E4 labels and E4 models,
     score files for bank/scale (`e3-prune-20261001/scores_v8_day.json`), public
     (`e5-public-20261001/scores_v8_day.json`) and multi8.
   - Keep local concurrency moderate (<= 6 single-thread Gurobi processes) — it is the
     user's laptop.
2. **Cross-machine variability is large.** Local rerun of E5 Hildenbrand-15 learned4 keep 30%
   T=180 s: 517.16 vs 490.72 on the cluster (+5.4%; Gurobi 12.0.1 local vs 12.0.3 cluster,
   different CPUs). Every comparison must be paired on ONE machine and use >= 3 solver
   seeds; do not mix local and cluster numbers.
3. **The Eberbach replay failure is path-dependent.** Local rerun of the E10 cell that failed
   on the cluster (Eberbach, learned4, keep 0, top-5 per trip, 600 s) completed and replayed:
   bill 1393.29, 838 movements kept, no failure.

## What the readers concluded (details and file:line citations in STATE_MAP json)

- **ML verdict:** the model works as a movement filter in front of Gurobi, not as a planner,
  and it has never been shown to beat a cheap non-learned ranking. Much of the headline
  gain over cold comes from shrinking the problem (random pruning alone beats cold where cold
  collapses to 25-32-bus plans); the ranking's measurable value is avoiding damage plus
  ~10-23% over random on 80-trip cases. Honest effect sizes are medians (-3.4%/-3.0% E3;
  -6.1%/-6.8% keep 15%), from correlated development cases.
- **Prior art (verified from the published PDF):** Gerbaux, Desaulniers & Cappart, Computers &
  Operations Research 173 (2025) 106848, doi:10.1016/j.cor.2024.106848 — GNN arc selection
  for electric bus scheduling with per-trip incoming/outgoing top-n (their Algorithm 2) and a
  greedy+GNN hybrid; 405 instances of 568-1474 trips, 71.6% time reduction at +2.2% cost.
  Do NOT claim learned arc pruning or per-trip top-m as new. Plausibly new: price-coupled
  pruning (time-varying prices + quadratic aggregate supply cost), tariff-induced
  distribution shift, and certified complete-fleet price support.
- **Replay root cause (primary, evidenced on one archived incumbent):** integrality-tolerance
  trickle flow through `z <= cap*x` linking rows (movement "off" with x ~ 1e-7 still
  carrying charge), caught by the 1e-8 kWh orphan/roundoff budget that was calibrated on a
  CBC artifact. Fixes ranked F1-F5: F1 round-and-re-solve fixed-topology charging completion
  (round x, re-solve charging with the fixed-route LP, replay); F2 matching bound/objective
  admission; F3 retain the best replay-valid incumbent across tangent rounds instead of
  aborting; F4 tighter IntFeasTol (diagnostic); F5 inward capacity margin in the completion LP.

## Recommended next steps (in order; all can run locally)

1. **Zero-solver offline diagnostics** (no Gurobi): per-trip recall@m (m=1..8) and recall at
   keep 5/15/30% of the v8 scores against the best known plans on the scaled/public cases;
   compare with CatBoost v5 and a non-learned slack/deadhead/depot-access ranking.
2. **Replay fix F1+F3** in `native_pathflow` / `claude_e3_prune.py`, with the
   NUMERICAL_RELIABILITY protocol's tests; rerun the archived failing cells.
3. **Ranking-source ablation** (your RECOVERABLE_PRUNING six-arm design): v8 vs CatBoost vs
   logistic vs a non-learned greedy ranking vs random, same keep rule, >= 3 Gurobi seeds,
   paired on the local machine, on >= 10 independent (non-prefix) base timetables per size.
   This is the decisive test of whether the GNN adds value.
4. **Recovery around pruning:** warm-start the full/widened MIP from the pruned plan for the
   remaining budget; staged widening.
5. **Ensemble/adaptive per-trip decoding** (average the 12 v8 models; per-trip cumulative
   probability mass instead of fixed m), then **training-signal work** (listwise per-trip loss,
   size-invariant competition features, public-like synthetic generator).

## Rules (unchanged)

EGG yields to cluster jobs named `v2g*` or commented `evspv2g-stochastic`; never touch other
projects' jobs; sealed DEV/TEST/A6/B3/GIRO stay closed; no PR merge or submission; write a
protocol before every launch and keep every failure.
