# Deep-research sweep 2026-08-20 (abstract-level; verify before citing)

Four parallel web sweeps (~80 searches) against the 2026-08-14 baseline.
Full narrative: Claude artifact "Price-Maker Frontier" (session of 2026-08-20).
Everything below is abstract-level confidence unless noted; nothing is
scored evidence.

## Verdicts

1. Novelty claim STANDS as of 2026-08-20: no work jointly fills
   Duties=Y / EndogP=Y / Exact=C-a. Confirmed from three angles (exact-EVSP
   line, pricing/CHP line, direct threat hunt).
2. CHP/uplift for an indivisible DEMAND-side asset: open niche. 2025-26
   frontier is supply-side (SDP pricing arXiv:2602.15722; European PRO/PAO
   strong-duality arXiv:2603.25490 handles demand blocks only via a
   sufficient condition).
3. Scope correction for our prose: state the B2 result as "dense iterative
   stabilization loses end-to-end at small n". Learned pairwise DOIs with
   exact recovery (You et al. arXiv:2607.13373: -55/-83% root-CG time at
   zero bound loss) contradict any broader claim. Wang & Khir
   arXiv:2604.23889 (learned stabilization control, convergence guarantees)
   is direct prior art for the A6 adaptive/event-triggered idea — cite it.
4. arXiv:2508.06752 (our dictator): 0 citations on OpenAlex (Semantic
   Scholar unverified, 429s). yao2025 (arXiv:2505.04532) now listed for
   IEEE CDC 2025, substance unchanged, still v1. NOTE: Scaglione is OUR
   COAUTHOR — yao2025 is a coordination bridge, not an adversarial threat;
   position the two papers jointly with her, and cite it as the nearest
   neighbor on the endogenous fixed point (smooth responses, no atomic
   duties, no certificates).

## New papers.csv candidates (key facts)

Threat-adjacent:
- TR-C May 2026 S0968090X26001968 — bilevel dynamic pricing + V2G
  ride-hailing fleet; sharpest new adjacent (EndogP~Y, Duties=N, Exact=?).
- Gu & Qin arXiv:2510.26036 — competitive equilibrium, spatially flexible
  loads (EV/datacenter); theory only.
- Brenner/Roald/Amin arXiv:2510.20805 — strategic data-center load over ED;
  dominant-load price-maker analog, convex lower level.
- Caustur et al. arXiv:2509.05940 — e-bus, 232 timetabled trips, peak
  demand charge; Duties=Y, EndogP=N, gaps not proven-optimal (newest
  Wu-2021 descendant).
- Löbel/Borndörfer/Weider arXiv:2407.14446 — own-load feedback into
  charging RATES/grid capacity (feasibility, not prices); certified PWL
  under/over-approx of charge curves.
- Sun et al. maritime Stackelberg now published: Energy 322 (2025),
  S0360544225012824.
- Manzolli et al. "When Agents Meet" pinned: arXiv:2606.26400.

Method anchors (exact EVSP):
- Haslinger/Gaar/Parragh arXiv:2504.13063 — exact MDEVSP partial charging,
  ~80 trips frontier.
- Wu/Li/Lin C&IE 206 (2025) — B&P pulse pricing, 101 trips claimed.
- Zhou et al. TRE 196:103994 (2025) — B&P + TOU.
- Jacquillat & Lo arXiv:2407.02640 — subpath columns for EVRP w/ nonlinear
  charging.
- van Rossum arXiv:2606.10081 — 75 crew B&P benchmarks: primal heuristics
  dominate; dual bound is the bottleneck; branching second-order.
- Gerbaux/Cappart/Desaulniers C&OR 173:106848 — ML-CG heuristic on
  multi-depot ELECTRIC bus scheduling, 3.5x @ 2.2% loss. READ FIRST for ML.

Method anchors (pricing/market):
- Gutierrez & Silvente arXiv:2601.20226 — EPEX aggregated DA curve models
  (parametric + DDPM), validated on price-maker storage; justifies affine
  b_t as elastic-region linearization.
- Dumitrescu/Silvente/Tankov arXiv:2410.12495 — storage price impact,
  FBSDE equilibrium, French data.
- Hyder et al. Energies 2024 CHP survey; ADMM CHP C&OR 2024
  (S0305054824002958).
- Data for b_t calibration: Nord Pool Aggregated Bidding Curves (per zone,
  since 2021-10); EPEX AggregatedCurves; OMIE daily aggregate curves (free,
  longest history). MISO publishes none; US route = ERCOT 60-day disclosure.

Motivation (empirical self-defeating charging):
- Yu et al. Nature Communications 16:8451 (2025) — 760k+ China UFC
  sessions; +31.6% peak-to-valley from 2k stations; storage worsens
  price-transition surges.
- SEGAN 2025 S2352467725003595 — ~28k Norwegian sessions; fleet peak
  +31->54% with rising price sensitivity.

ML-for-CO anchors:
- Kraul/Seizinger/Brunner IJOC 35(3):692 (2023) — dual-value prediction for
  stabilized CG. Sugishita et al. arXiv:2110.06872 — ML dual warm starts
  for DW on UC. Shen et al. ICML 2024 arXiv:2405.11198 — adaptive
  stabilization from predicted duals.
- Bertsimas & Stellato IJOC 2022 (strategy prediction, parametric MIO);
  Xavier/Qiu/Ahmed IJOC 2021 (SCUC reopt, 4.3x WITH guarantees) — the
  template for our price-loop reoptimization.
- Morabit/Desaulniers/Lodi TS 2021 (column selection, best paper);
  IJOO 2023 (arc selection); RLCG arXiv:2206.02568; MLPH arXiv:2112.04906.
- Václavík EJOR 2018 — pricing-value regression (degeneracy-immune labels).
- SymILO arXiv:2409.19678 — names multiple-optima label ambiguity;
  FrontierCO arXiv:2505.16952 — synthetic-to-real transfer is the weak
  point; ML4CO norms PMLR 176 (~10k train / 4k val instances).
- Consensus architecture: ML proposes, exact oracle certifies. End-to-end
  learned pricing ~9% gaps (arXiv:2504.02383) — not certificate-viable.
- Reoptimization benchmark protocol: arXiv:2311.14834.

## Ranked ML targets for us (detail in artifact)

1. Dual-trajectory warm starts across the price loop (canonicalized
   barrier/analytic-center dual labels; kill baseline = reuse previous
   iterate's duals — preregister it).
2. Learned pricing-network reduction, Gerbaux-style, labels = arc frequency
   in accepted margin-filtered columns; full exact pricing as fallback.
3. Parametric strategy/support prediction (Bertsimas-Stellato / Xavier).
4. Pricing-value regression (skip provably useless calls).
5. Column selection (only if master dominates). 6. Input-convex value
   surrogate (GVF NeurIPS 2024; high risk/high novelty).

Degeneracy defenses (consensus): learn values not argmins; canonicalize
labels; aggregate over optima (marginals/frequencies); margin filtering.
Our 2,559-vs-92 measurement is itself a publishable methodological unit.

## Venue bar

IJOC best fit for ML-warm-started certified negotiation (report
with-guarantees and without-guarantees speedups separately, Xavier
convention); TS if the application carries; EJOR fallback; TPWRS/Energy
Economics for the calibrated price-formation half. Universal bar: speedup
at UNCHANGED certificate quality.

## Addendum (same day, evening): implementation-grade extractions

### ML dual warm-start / stabilization — design contract (from full-paper reads)

- Sugishita/Grothey/McKinnon arXiv:2110.06872: OUR SETTING EXACTLY (fixed
  structure + shifting parameter vector; their demand = our prices). Feed
  only the changing price vector; MLP 4x1000 tanh (or k-NN k=4 over past
  solves — near-free baseline the model must beat). ~1.7-2.1x to certified
  0.25% gap. Code: github.com/nsugishita/ml_to_warmstart_cg.
- Kraul/Seizinger/Brunner IJOC 2023 (OA: opus.bibliothek.uni-augsburg.de
  /opus4/files/104599/104599.pdf): predicted duals as FROZEN du Merle box
  centers; epsilon halved whenever pricing finds no negative-RC column,
  driven to 0 -> exact LP optimum guaranteed. ~2x. Per-item SPARSE
  featurization (5 inputs -> 1 dual, net 2x7!) generalizes across sizes;
  whole-instance FULL breaks outside trained dims. 100k training
  instances. Data: github.com/SebastianKraul/Machine-learning-supported-
  prediction-of-dual-variables-for-the-cutting-stock-problem.
- Shen et al. ICML 2024 arXiv:2405.11198: adaptive rule eps = c*/(c*-1)
  if min reduced cost c*<0 else 0 — provably reaches 0 in finitely many
  iterations (their Lemma 3.5). Label = AVERAGE of duals across multiple
  optima (degeneracy fix). FFNN beats GCN out-of-distribution. Warning:
  stabilized duals densify -> pricing slows; -44% iterations became -9.6%
  time with exact pricing. Code: github.com/yunzhuangshen/
  ML-based-Adaptive-Stabilization.
- You et al. arXiv:2607.13373 (learned pairwise DOIs): label protocol =
  sample K=20 duals from the OPTIMAL FACE, pair (i,j) labeled if p_i<=p_j
  in >=80% of samples; XGBoost on pair features; DOIs enter as zero-cost
  columns; xi-activity check + iterative release restores exact bound
  (0% loss at -55/-83% time). Label cost ~2m auxiliary LPs/instance.
- Gerbaux thesis (open: publications.polymtl.ca/53409/1/
  2023_JulietteGerbaux.pdf) + C&OR 173:106848: arc pruning = keep
  predicted-score rank<=2 arcs UNION greedy-solution arcs (union is what
  protects quality); heuristic only (no exact fallback in paper); GNN
  does NOT transfer across road networks (+1055% cost with wrong-network
  model). 500 instances/type; labels 465-19,300 s/instance.
- Wang & Khir arXiv:2604.23889 (RL stabilization control): gains vanish
  and can reverse on degenerate instances; per-iteration inference
  overhead. Cite as A6 prior art; not the first thing to build.

Brief must specify: (i) label protocol — solver, stopping gap, dual
canonicalization (barrier/analytic-center or averaged-across-optima,
price-normalized), Slurm budget/instance; (ii) integration contract —
du Merle 3-piece with centers=prediction frozen, epsilon schedule that
provably hits 0, certification path unchanged; (iii) distribution
definition — price-perturbation range of the loop, instance-level splits,
out-of-range detection. Report iterations AND wall-clock separately.

### Market-curve data access (verified, incl. one real download)

- RECOMMENDED: OMIE (MIBEL). Free, no registration. Daily files
  omie.es/en/file-download?parents[0]=curva_pbc&filename=
  curva_pbc_YYYYMMDD.1 (~4MB/day, 2023->now); yearly ZIPs
  curva_pbc_YYYY.zip verified for 2018-2022. Format: semicolon/Latin-1,
  decimal comma, 2 header lines; Tipo Oferta C=demand V=supply;
  O=offered/C=matched. Validation: reconstructed S/D intersection must
  reproduce OMIE marginalpdbc price. Terms: cite the source; fitted
  slopes publishable. Watch: 15-min MTU (96 periods) after SDAC
  switch in late 2025; DST 23/25-period days.
- Nord Pool Aggregated Bidding Curves: PAID (~EUR 430-1650/yr/cluster,
  API); academic terms negotiable, not self-serve. History since 2021-10.
- EPEX aggregated curves: PAID (EUR 200/area/yr current + 160 historical,
  SFTP, internal-use license; university use = contact them). No open
  mirror; arXiv:2601.20226 has no replication package.
- ENTSO-E: does NOT publish DA bid curves (prices A44, load A65 only —
  use as complements via entsoe-py).
- US fallback: ERCOT NP3-966-ER 60-day DAM disclosure (free CSVs,
  per-resource bid/offer curves, ~4-yr rolling retention; reconstruct
  aggregates yourself). PJM/CAISO/MISO: masked per-resource only.
- Slope recipe (per hour): parse curves -> cumulative step functions ->
  residual supply around clearing volume -> regress price on volume in a
  +/-250-1000 MW window sized to fleet load; store slope, window, step
  count, R^2.
