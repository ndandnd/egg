# EGG handoff from Claude to GPT — 2 October 2026, ~04:45 UTC

## Suggested opening request (paste into GPT)

> Read `doc/GPT_HANDOFF_20261002.md` on branch `claude/research-20261001` of
> https://github.com/ndandnd/egg (or the bundle `output/gpt-handoff-20261002.zip`).
> Claude is still running the cluster side until ~17:45 UTC 2 October. Please do two
> things that need no cluster compute: (1) post the six pending research-log updates in
> `research-20261001/GOOGLE_DOC_PENDING.md` to the existing Google Doc, verbatim and in
> order, if you have Docs write access; (2) run the deep research brief in Section 5 and
> write the report to `research-20261002/sota-review/SOTA_REVIEW.md` on a new branch
> `codex/sota-review-20261002`. Do not submit cluster jobs, modify
> `claude/research-20261001`, or open sealed DEV/TEST/A6/B3/GIRO data.

## 1. Where things stand

Claude took over on 1 October (~05:15 UTC) after Codex paused. All work is on branch
`claude/research-20261001` (forked from Codex pause commit `2d66b55`; the Codex branch is
untouched). Live state and job ledger: `research-20261001/STATE.md`. Independent
assessment: `doc/CLAUDE_ASSESSMENT_20261001.md`. Every experiment has a `PROTOCOL.md`
(written before launch) and a results file in `research-20261001/<experiment>/`.

The central finding of the takeover: **learned pruning works.** Take the graph-attention
movement scorer, keep only the highest-scored connections (plus a per-trip safety
floor), and let the MIP optimize routes and charging on the reduced model. At equal wall
time this beats unpruned solving decisively once instances exceed ~40 trips, and it
transfers to real public timetables the model never saw.

## 2. Results (all exploratory development evidence; one run per cell unless noted)

| Exp | Question | Result |
|---|---|---|
| v8 | Longer graph training (Codex job, collected) | Anchors reproduce v6 exactly; held-out log loss 0.0719 -> 0.0543, AP 0.843 -> 0.899; beats all tree models |
| E0 | v7 hull controls with the `pool_tol` typo fixed | 14/16 hulls certify; **4/16 timetables have a certified positive physical-minus-hull gap** (no supporting price), all <= 0.1% of the bill |
| E1 | Does route topology respond to the tariff? | Bus count never changes (16/16); topology changes in 14/16; midday-cheap tariff doubles midday charging. Explains v7's learned-route loss |
| E2 | Cold MIP time-to-quality vs size | Trivial at 20-28 trips; 2-79% gaps after 600 s at 60-80 trips (one 80-trip best plan uses 30 buses) |
| E3 | Learned pruning vs cold / LP-score / random pruning (keep 30%) | Bank (20-28 trips): beats random 15/16, LP 8/7/1, small wins vs cold. 40-80 trips: beats cold 10/2 (60 s), 9/1/2 (300 s); beats LP and random 12/12 |
| E4 | Tariff-diverse labels (7 tariffs per timetable, midday tariff held out) | Held-out-tariff AP better 4/4 folds; physical gap to cold halves (18.2 -> 8.6); first learned arm to beat v7 source reuse on average |
| E5 | Pruning on public Hildenbrand (37 svc) and Eberbach (105 svc, 10,359 movements) | Pruning + four-round solver split is best in 6/6 public cells; on Eberbach 600 s pruned beats 1800 s unpruned |
| E6 | Keep fraction 15/30/50% | 15% best on synthetic 40-80 trips: 12/12 vs cold at 60 and 300 s |
| E7 | Prune with tariff-aware (E4) scores | Helps large synthetic cases at 60 s; worse on all 6 public cells |
| E8 | Keep 5/10% | Synthetic: smaller keep at larger size (5% best at 80 trips). Public: 30% best; 5% loses 17-19% |
| E9 | Learned plans as seeds for hull certification at 40-80 trips | Seeded hull enclosures tighter on 10/10 cases (width ratio 0.08-0.63); 1 newly certified; gaps still include 0 |
| E10 | Per-trip top-m rule instead of a global fraction | m=5/8 beat cold 27-28/30 without regime tuning; but 4/6 long Eberbach runs fail exact replay |
| E11 | Gurobi seed robustness (seeds 1-3; 72/96 done, paused) | Learned beats cold 17-18/18 seed-paired; 60-trip learned arms vary up to ~9% by seed |

Recurring infrastructure issue: native solutions sometimes fail exact replay or the
charge-projection roundoff check ("Whole-incumbent charge projection exceeds roundoff
budget", "Used bus did not finish fully replenished", "Replayed SOC violates reserve").
Seen in E2, E4 labels (17/896), E0 (10069), E3 (10068), E10 (Eberbach). Worth a focused
numerical-tolerance study.

Harness lessons: (a) a planner timeout bug discarded earlier-round plans (fixed in
`claude_e3_prune.py`, affected cells rerun once as `-hfix`); (b) the round policy
(single budget vs four tangent rounds) matters as much as pruning on public cases, so
every comparison is paired within the same policy (cold vs learned, cold4 vs learned4).

## 3. Code and data

- Drivers: `src/experiments/claude_*.py` (e0 support, e2 profile, e3 prune [all pruning
  arms incl. per-trip `--min-options`, `--grb-seed`], e4 labels/train/eval, e9 hull,
  decode, score_v8). Case loader for bank/scaled/public: `src/egglab/claude_cases.py`;
  scaled generator `src/egglab/claude_scale_cases.py`.
- Cluster: unicorn2, `~/egg-claude-20261001/{current, runs/, data/public}`; generic array
  runner `src/cluster/claude_array.sbatch`.
- Public payloads: `data/public/sistig_26088190_v1/` (Hildenbrand, Eberbach).

## 4. Operating rules (unchanged unless the user says otherwise)

- **Cluster priority:** EGG yields to the evspv2g stochastic project (jobs named `v2g*` or
  `--comment=evspv2g-stochastic`). `~/egg-claude-20261001/yield_check.sh` enforces this;
  Claude runs it every 5 minutes. As of 04:20 UTC ~109 v2g jobs are queued, so EGG work
  is paused (E11 at 72/96). Never cancel or alter other projects' jobs; exclude
  `scaglione-compute-01`; at most 6-8 concurrent EGG Gurobi processes.
- Sealed: DEV/TEST physical groups, A6/B3/confirmation, private GIRO data.
- No PR merge, no paper submission, no reset-credit redemption.
- **Coordination:** until Claude's wrap-up (~17:45 UTC 2 Oct) Claude owns the cluster and
  branch `claude/research-20261001`. GPT should work on its own branch and not submit
  jobs. After the wrap-up, `research-20261001/TAKEOVER_SUMMARY.md` will list what is
  running and the recommended next steps.

## 5. Deep research brief for GPT (no compute needed)

Goal: identify state-of-the-art techniques that could improve our pipeline, ranked by
expected impact on *time-to-quality of complete-fleet electric-bus schedules* and on
*complete-fleet convex-hull (price-support) certification*. For every technique: the
primary source (verify titles/venues/DOIs; do not guess), what problem it solves, how it
maps onto our components, evidence quality in its paper, estimated implementation
effort, and a concrete experiment we could run with a stop/go criterion.

Our pipeline today: graph-attention edge scorer (2 layers, ~18k params, 17 edge
features incl. window prices) trained by imitation of feasible incumbents -> prune the
MIP's movement set (global top-k% or per-trip top-m) -> Gurobi solves a compact
path-flow MILP with time-indexed continuous charging and a tangent outer approximation
of a quadratic supply cost (four rounds) -> exact event replay. Hull certification uses
Dantzig-Wolfe over complete-fleet columns with a numerical QP restricted master and
Fenchel lower bounds from global pricing MIPs.

Questions:
1. **ML-guided MILP primal heuristics** beyond plain pruning: predict-and-search /
   trust-region fixing, Neural Diving and its successors, contrastive or uncertainty-
   aware variants, learned large-neighbourhood search, GNN warm starts. Which give the
   best time-to-quality on scheduling/routing MILPs of our size (300-10,000 binaries,
   ~300k continuous variables)? Which handle distribution shift (our synthetic ->
   public transfer, E7/E8) better than a fixed keep threshold?
2. **Training signal:** imitation of single incumbents vs solution pools, cost-aware or
   contrastive labels, learning from LP/dual information, self-improvement (iterating
   prune -> solve -> relabel). What fixes the "better ranking does not mean cheaper
   fleets" gap we saw before E3?
3. **Calibrated or adaptive pruning:** confidence-based or conformal keep sets,
   per-node top-m, safe-pruning with recovery (reinsert movements when reduced costs
   or a repair step indicate need).
4. **Electric vehicle / bus scheduling specifically:** recent exact and learning-based
   E-VSP methods with charging (branch-and-price with charging-aware pricing, labeling
   algorithms, ML-accelerated column generation). Which would make our pricing oracle
   (the hull/regret bottleneck, E9) materially stronger?
5. **Convex-hull pricing computation at scale:** stabilized column generation, bundle /
   proximal methods, primal-dual heuristics, warm starts from learned columns
   (Andrianesis et al. 2022 and successors). What would close our 40-80-trip hull gaps?
6. **Numerical robustness:** best practice for MIP solutions that fail exact replay
   (tolerance tightening, scaling, rounding-and-repair, exact re-verification).

Deliverable: `SOTA_REVIEW.md` with a ranked shortlist (top 5) of experiments, each with
source, mapping, effort (hours), required compute (CPU-hours), and stop/go; plus a short
"do not pursue" list with reasons. Distinguish verified primary sources from abstract-only
or secondary claims, as the project's literature rules require.

Starting points that must be verified, not assumed: Nair et al. (2020) "Solving Mixed
Integer Programs Using Neural Networks" (Neural Diving); Han et al. (ICLR 2023) "A
GNN-Guided Predict-and-Search Framework for Mixed-Integer Linear Programming"; Huang et
al. (ICML 2024) contrastive predict-and-search; Gasse et al. (NeurIPS 2019) GCNN
branching; Morabit, Desaulniers & Lodi (2021) ML column selection; Andrianesis et al.
(2022) convex-hull pricing via Dantzig-Wolfe; Parmentier, Martinelli & Vidal (2023)
column generation for electric fleets.
