# External deep-dive literature scan

Date: 2026-08-14

Status: web-search evidence only. Unlike the three full-text review notes in
this directory, every claim below is based on abstracts, publisher pages, and
search summaries, not on an end-to-end read of the paper. Treat each entry as
"verified to exist and to claim X in its abstract," and re-verify any detail
that will support a manuscript claim. Papers that must be acquired in full are
flagged in `../READING_QUEUE.md`.

Purpose: the 17-paper full-text audit (see `../../HANDOFF_PRICE_MAKER_20260814.md`
Sections 3-4) established what the *domain* literature already covers. This scan
asks a different question: which *methodological* literatures already exist for
the pieces we thought we might have to invent, and do they threaten or enable
the candidate thesis directions A-E?

## Executive summary of what this scan changes

1. **The multi-fleet atomic equilibrium problem has an existing name and
   toolbox: Integer Programming Games (IPGs).** A mature algorithmic
   literature (2018-2025) computes, enumerates, and optimizes over Nash
   equilibria when players' strategy sets are integer programs. Its central
   device — an "equilibrium separation oracle" that finds a profitable
   deviation or certifies none exists — is *exactly* the role we planned for
   the EVSP best-response oracle. This is a large enabler for Directions A and
   E and simultaneously kills any claim that cutting-plane equilibrium
   computation over integer strategies is itself new.

2. **Mixed-integer bilevel programming (MIBLP) is now a solver technology,
   not an open problem.** Branch-and-cut with intersection cuts (Fischetti et
   al.), the open-source solver MibS, improving-direction unification (2025),
   decision-diagram reformulations (2025), and a Dantzig-Wolfe single-level
   reformulation (2025) mean a market/tariff leader over an *integer* EVSP
   follower is in principle computable without KKT. The DW-reformulation
   paper is the closest methodological neighbor to "duty columns inside a
   bilevel market problem" and must be read in full.

3. **Direction B has a live institutional anchor: EUPHEMIA exclusive groups.**
   The European day-ahead market already clears sets of mutually exclusive
   block orders (at most one accepted). Optimal exclusive-group bidding for
   *stylized* flexible demand exists (Karasavvidis et al. 2024; a 2026
   follow-up compares hourly vs exclusive-group bids under price uncertainty).
   Nobody generates the exclusive-group menu from an exact trip-covering
   fleet model, and nobody addresses menu design (which K schedules to bid)
   with column generation. Given the project's Swedish (Nord Pool) data, this
   is the most concrete, directly implementable direction found by this scan.

4. **Direction D gains two rigorous theory frames.** (i) Performative
   prediction has grown into a field with a 2025/26 survey, nonconvex-loss
   convergence results, and decision-dependent distribution dynamics — but
   essentially all of it assumes smooth losses and continuous decision maps;
   an atomic EVSP response violates those assumptions in a way that is
   precisely characterizable. (ii) The algorithms-with-predictions /
   learning-augmented-algorithms literature formalizes
   consistency-robustness-graceful-degradation — the exact contract of our
   "surrogate proposes, exact pricer verifies" architecture; a 2024 Dagstuhl
   report explicitly lists bridging these guarantees with ML-augmented
   combinatorial solvers as open.

5. **The domain gap survives.** A targeted scan for a price-making,
   timetabled, exact-scheduling transit fleet in wholesale markets found
   practice-oriented aggregation work, price-taking envelope bidding, and one
   2026 "agentic aggregator" preprint, but nothing that closes the gap left
   by Lu et al. (2021). The atomic-EVSP-inside-the-market claim remains open.

---

## A. Integer programming games: equilibria with combinatorial strategy sets

Relevant to: Direction A (strategic fleet), Direction E (competition),
Section 6.2 brainstorm items "multiple fleets" and "exact no-deviation
pricing".

### Key works identified

- Carvalho, Dragotto, Lodi, Sankaranarayanan (2023), *Integer Programming
  Games: A Gentle Computational Overview*, INFORMS TutORials.
  arXiv:2306.02817. Tutorial covering complexity (deciding existence of a
  pure Nash equilibrium in an IPG is Sigma-p-2-complete) and the main
  algorithms: Sample Generation Method, exhaustive SGM, Cut-and-Play,
  Branching Method, Branch-and-Prune, Zero Regrets.
- Carvalho, Lodi, Pedroso (2022), *Computing equilibria for integer
  programming games*, EJOR 303(3), DOI `10.1016/j.ejor.2022.03.048`. The
  SGM: iterate between a sampled finite game and best-response computation;
  computes mixed equilibria for separable payoffs.
- Dragotto, Scatamacchia (2023), *The Zero Regrets Algorithm: Optimizing over
  Pure Nash Equilibria via Integer Programming*, INFORMS J. Computing, DOI
  `10.1287/ijoc.2022.0282`. Cutting-plane framework built on "equilibrium
  inequalities" separated by an *equilibrium separation oracle* (a
  best-response computation). Computes, enumerates, and selects pure Nash
  equilibria, including welfare-optimal ones.
- Carvalho, Dragotto, Lodi, Sankaranarayanan (2025), *The Cut-and-Play
  Algorithm: Computing Nash Equilibria via Outer Approximations*, Operations
  Research, DOI `10.1287/opre.2023.0327`. Computes equilibria by refining
  outer convex approximations of each player's strategy set — conceptually a
  cutting-plane/branching analogue of playing over cl conv(X_i).
- Carvalho, Dragotto, Feijoo, Lodi, Sankaranarayanan (2024), *When Nash Meets
  Stackelberg*, Management Science 70(10), DOI `10.1287/mnsc.2022.03418`.
  NASPs: simultaneous Nash games among players who each solve a Stackelberg
  program (linear leader, convex-quadratic followers). Existence is
  Sigma-p-2-hard to decide; exact algorithms provided; applied to
  international energy markets.
- Carvalho, Dragotto, Lodi, Sankaranarayanan, *Integer Programming Games*
  (survey volume), DOI `10.1561/2400000040`. Comprehensive survey including
  bilevel variants.
- Fanzeres, Street, Pozo (c. 2020-2021), column-and-constraint generation for
  Nash equilibria in pool-based electricity markets (exact venue/DOI to
  verify). Reports roughly 20-30x speedups over an EPEC formulation on the
  supply side with continuous quantities.

### Novelty threats

- "We introduce a cutting-plane/oracle method for equilibria over integer
  strategy sets" is dead: Zero Regrets *is* that method, generically.
- "Column-and-constraint generation for electricity-market equilibria" exists
  on the generation side (Fanzeres et al.), in continuous strategies.
- NASP kills "first simultaneous game among Stackelberg leaders with exact
  algorithms," for the convex-follower case.

### What remains open (and is now better defined)

- No published IPG application has players whose strategy sets are
  *exponential-size vehicle-scheduling feasibility sets accessed only through
  column generation*. All benchmarked IPGs use compact formulations (knapsack,
  network formation, facility location, cybersecurity). An "EVSP-IPG" in
  which the equilibrium separation oracle is a branch-and-price EVSP solver —
  with all of our exactness-tier caveats — appears genuinely new, and it
  slots our existing machinery into a rigorous, citable framework.
- The interesting equilibrium coupling for us is through *prices*
  (payoff interaction via aggregate load), which gives the game a structured,
  low-dimensional interaction — plausibly exploitable and unstudied at this
  intersection.
- NASPs assume convex followers. Fleets bidding into a market whose clearing
  is itself an optimization, each fleet solving an integer program, is beyond
  current NASP results. Even negative/complexity results with a working
  restricted algorithm would be a contribution.
- Equilibrium inequalities give a clean formal home for the handoff's
  "certified equilibrium gap": ZR-style bounds on how far a candidate profile
  is from equilibrium, computed with capped oracles and honestly labeled.

---

## B. Mixed-integer bilevel optimization: the leader-over-integer-EVSP backbone

Relevant to: Direction A, tariff/mechanism design chapters, and the critique
(inherited from the 17-paper audit) that KKT reformulations fail for integer
followers.

### Key works identified

- Kleinert, Labbé, Ljubić, Schmidt (2021), *A survey on mixed-integer
  programming techniques in bilevel optimization*, EURO J. Comput. Optim.,
  DOI `10.1016/j.ejco.2021.100007`. The standard survey.
- Fischetti, Ljubić, Monaci, Sinnl (2017), *A new general-purpose algorithm
  for mixed-integer bilevel linear programs*, Operations Research 65(6).
  Branch-and-cut with intersection cuts; basis of state-of-the-art solvers.
- Tahernejad, Ralphs, DeNegre (2020), *A branch-and-cut algorithm for mixed
  integer bilevel linear optimization problems and its implementation*
  (solver: MibS), Math. Programming Computation.
- *Improving Directions in Mixed Integer Bilevel Linear Optimization* (2025),
  arXiv:2511.03566. Unifies bilevel-feasibility checking and cut generation
  through a single "improving feasible direction" subproblem; implemented in
  MibS.
- *A single-level reformulation of binary bilevel programs using decision
  diagrams* (2025), Mathematical Programming, DOI
  `10.1007/s10107-025-02294-1`. Encodes the follower's solution set in a
  decision diagram; strong on followers with combinatorial structure.
- *A Dantzig-Wolfe Single-Level Reformulation for Mixed-Integer Linear
  Bilevel Optimization: Exact and Heuristic Approaches* (2025, Optimization
  Online). Single-level reformulation via DW; explicitly motivated by the
  failure of KKT/duality reformulations for MILP followers. **Closest
  methodological neighbor to "duty columns inside a bilevel market."**
- Already in the handoff: Dumouchelle et al. (2024), *Neur2BiLO: Neural
  Bilevel Optimization* — learned value-function surrogates for bilevel.

### Novelty threats

- "KKT fails for integer followers, so we propose a new exact bilevel
  method" is not, by itself, a contribution: MibS-class branch-and-cut,
  decision diagrams, and DW reformulations already exist, and the value
  function of a MILP follower is a studied (nonconvex, discontinuous) object
  (Hassanzadeh and Ralphs 2014 lineage).
- A generic "Dantzig-Wolfe for bilevel" claim is now taken (2025 preprint).

### What remains open

- Existing MIBLP solvers assume a *compact* follower formulation. An EVSP
  follower whose variables (duties) are generated on the fly is outside every
  benchmark; combining bilevel branch-and-cut with column generation on the
  follower is unexplored at scale and matches our infrastructure exactly.
- The DW-bilevel preprint must be read carefully: if its master enumerates
  follower vertices, our contribution is the *delayed generation* of those
  vertices with a certified pricing oracle plus the market interpretation of
  the columns (duties as bids). If it already delays generation, our
  contribution narrows to the market application and the response-exactness
  hierarchy — still substantial but different. Priority read.
- Nobody appears to combine (i) bilevel market clearing, (ii) integer
  follower via column generation, and (iii) an honest exactness hierarchy
  (finite-pool vs discretized-certificate vs heuristic tiers). That
  three-way combination is where our EVSP-DR inheritance is differentiated.

---

## C. Nonconvex pricing, bid languages, and the EUPHEMIA anchor

Relevant to: Direction B (duties as bids), Direction C (products), Chapter
"prices and payments"; sharpens Zoltowska/Fang implications from the audit.

### Convex hull pricing state of the art

- *Convex Hull Pricing for Unit Commitment: Survey, Insights, and
  Discussions* (2024), Energies 17(19):4851, DOI `10.3390/en17194851`.
  Systematic survey; notes CHP extensions to demand response and AC-OPF; ~27
  papers total, so the field is small and mostly supply-side.
- Andrianesis, Bertsimas, Caramanis, Hogan (2022), *Computation of Convex
  Hull Prices in Electricity Markets with Non-Convexities using Dantzig-Wolfe
  Decomposition*, IEEE TPWRS, DOI `10.1109/TPWRS.2021.3122000` (already in
  handoff Section 5): CHP computed by DW/column generation where each
  resource contributes columns.
- Modified CHP with price-sensitive load exists (DOI
  `10.1016/j.ijepes.2018.02.023`), demand-side but divisible.

Implication: computing *atomic fleet* convex-hull prices by pricing duty
columns (handoff 6.2 "atomic convex-hull prices") composes two known pieces
(Andrianesis DW-CHP; our duty pricer) in an unoccupied application: the
convexified resource is a trip-covering fleet, whose lost-opportunity-cost
must be evaluated against feasible schedules, not power envelopes. The
separation oracle for demand-side LOC is our EVSP — same oracle as everywhere
else. Coherent, not yet taken.

### Bid languages: EUPHEMIA block orders and exclusive groups

- EUPHEMIA public description (NEMO Committee / Nord Pool): the European
  day-ahead clearing algorithm supports profiled block orders, linked blocks,
  *exclusive groups* (sets of blocks whose accepted ratios sum to at most 1 —
  with fill-or-kill blocks, at most one member accepted), flexible orders,
  and scalable complex orders. Exclusive groups are a production-grade XOR
  bid language, live in the market our Swedish data belongs to.
- Karasavvidis, Papadaskalopoulos, Strbac (2024), *Optimal Bidding of
  Flexible Demand in Electricity Markets With Block Orders*, IEEE Trans.
  Energy Markets, Policy and Regulation, DOI `10.1109/TEMPR.2024.3414988`.
  First (per its own abstract) optimal-bidding model for a price-taking
  stand-alone flexible-demand participant using exclusive groups; compares
  hourly orders, independent blocks, and EGs; finds EGs particularly valuable
  for flexible demand. Related: same group on profile/linked blocks (TPWRS
  2021, DOI `10.1109/TPWRS.2021.3129084`) and loop blocks for storage (TPWRS
  39(1), 2023/24).
- *Generating EUPHEMIA-compatible bids for flexible demand under imperfect
  information* (2026), arXiv:2606.24183. Hourly bids vs exclusive-group bids
  (mutually exclusive operational schedules at opportunity cost) for an
  electrolyzer and a real steel plant; which format wins depends on
  flexibility structure and price volatility.
- Hubner, Hug (2026), *Package Bids in Combinatorial Electricity Auctions*
  (already in handoff Section 5), DOI `10.1287/opre.2024.0777`.

### Novelty threats

- "Propose XOR/package bids for flexible demand in day-ahead markets" is
  dead several times over: the product exists (EUPHEMIA), and optimal EG
  bidding for flexible demand is published (2024) with a 2026 follow-up.
- "Bus aggregator bids min/max hourly energy envelopes into the day-ahead
  auction" exists (Zoltowska-adjacent: *Optimal Charging Schedule Planning
  for Electric Buses Using Aggregated Day-Ahead Auction Bids*, Energies
  14(16):4727, 2021) — price-taking, aggregate-envelope, no duty structure.

### What remains open (Direction B, sharpened)

- **Menu generation is the unclaimed core.** For a trip-covering fleet, each
  exclusive-group member is a *complete feasible duty schedule with its load
  profile and opportunity cost* — i.e., a column (or bundle of columns) from
  our solver. Open questions no one addresses:
  1. Which K schedules should the fleet bid (menu design under a bid-count
     budget)? Welfare/profit loss vs K; column generation as the menu
     generator; certified menu optimality gaps via pricing.
  2. Price-making with blocks: EG bidding as a *strategic* instrument (all
     prior EG work is price-taking).
  3. Truthfulness and exposure: blocks clear at market price with
     fill-or-kill acceptance — paradoxical rejection and exposure risk for a
     mandatory-service fleet (it must run *some* schedule even if all its
     blocks are rejected: the fallback bid is itself a design question).
  4. Comparison against Zoltowska-style centralized shifting bids and against
     US-style multi-part self-scheduling: which bid language loses least
     welfare for atomic fleet flexibility?
- This direction has unusually low model risk (the market rules are public
  and fixed), direct use of the Nordic data, and a natural experiment ladder
  (price-taking EG menu first, strategic later).

### Baseline-free products update (Direction C)

- Capacity limitation services are maturing as the alternative to baselines:
  Ziras et al. (2021) (already in handoff), a 2023 DTU thesis standardizing
  CLS market clearing, a 2025 LFM design taxonomy (Energy, DOI
  `10.1016/j.energy.2025.136051`), and 2025 work on capacity subscription as
  a decentralized adequacy mechanism (Applied Energy 391).
- Open for us: *deliverability*. A capacity cap sold by a transit fleet is
  only real if a trip-covering schedule exists under the cap. Computing the
  feasible set of sellable caps/envelopes — and pricing them — requires
  exactly our oracle. No CLS paper models mandatory service feasibility.

---

## D. Learning-theory frames for the price-schedule feedback loop

Relevant to: Direction D (active learning at switch boundaries), Chapter
"learning with correction", and the honest-labeling policy.

### Performative prediction has become a field

- *Dissecting Performative Prediction: A Comprehensive Survey* (2025/26), DOI
  `10.1145/3816429`. Organizes solution concepts (performative stability vs
  performative optimality), distribution-map information regimes, and
  algorithm families.
- *Stochastic Optimization Schemes for Performative Prediction with Nonconvex
  Loss* (NeurIPS 2024): first nonconvex-loss analysis; introduces stationary
  performative stability; greedy vs lazy deployment bias bounds.
- *Decision-Dependent Stochastic Optimization: The Role of Distribution
  Dynamics* (2025), arXiv:2503.07324: stateful/dynamic distribution maps.
- Existing extensions cover multi-agent/competing performative predictors
  (Narang et al., Piliouras and Yu) — relevant precedent for multiple
  strategic fleets learning simultaneously.

Threats: "the price-load loop is performative prediction" is an observation,
not a contribution; smooth-case algorithms and stability notions are taken.

Open: the entire literature assumes (strongly) convex losses, Lipschitz
distribution maps, and continuous decisions. An atomic fleet's
price-to-schedule map is piecewise constant with jumps — the composition
"price model -> EVSP argmin -> induced load -> price distribution" violates
the core smoothness assumptions *in a structured, analyzable way* (finitely
many schedule regions; see Section D.3 below). Questions with theory value:
does a performatively stable schedule exist (vs only mixed/randomized
stability)? Do repeated-retraining dynamics cycle exactly when the
fixed-point damping fails in our Phase-1 experiments? Can region structure
restore convergence guarantees that smoothness normally provides?

### Algorithms with predictions / learning-augmented algorithms

- Framework: consistency (near-optimal when predictions are good),
  robustness (never worse than the prediction-free baseline), graceful
  degradation in prediction error. Mature for online problems; growing for
  offline warm-starting of exact solvers; a systematic offline framework
  appears in *Approximation Algorithms for Combinatorial Optimization with
  Predictions* (arXiv:2411.16600).
- Dagstuhl Report 14(10) (*Machine Learning Augmented Algorithms for
  Combinatorial Optimization*, 2024) explicitly poses as open: proving
  consistency-robustness guarantees for ML-augmented branch-and-bound /
  column generation and bridging them with generalization bounds.

Open for us: state and prove the two-fidelity architecture's contract in
this language — e.g., ML-proposed columns/duty menus make the pipeline
1-consistent (exact optimum retained when predictions are perfect, because
exact pricing remains the fallback) and rho-robust (bounded extra cost/time
when predictions are garbage), with degradation controlled by a measurable
prediction error. This converts our engineering discipline (exactness tiers,
fallback pricing) into theorems the ML-for-OR community has asked for.

### Parametric structure of the response map

- Multiparametric MILP theory (Oberdieck, Wittmann-Hohlbein, Pistikopoulos
  2014, J. Global Optim. 59(2); Dua and Pistikopoulos lineage) partitions the
  parameter space (here: the tariff/price vector) into critical regions with
  affine value behavior per region — the *formal* object behind the handoff's
  Phase-2 "switch boundary" mapping. Exhaustive region enumeration will not
  scale to 24-dimensional price space, which is precisely why *learning* the
  region structure (Direction D) is the right move; mp-MILP supplies the
  vocabulary (regions, envelopes) and small-instance ground truth.
- *Learning Generalized Linear Programming Value Functions* (NeurIPS 2024):
  learns LP value functions over objective and constraint-bound parameters
  with a structure-matched architecture that guarantees a true
  *under-approximation* in the constraint bounds and is LP-embeddable.
  One-sided approximations are exactly what certification needs; an analogous
  learned lower bound on the fleet's cost-vs-tariff value function would give
  cheap certified bounds between exact solves.
- *Decision-Focused Surrogate Modeling for MILP* (2025 preprint): learns
  parametric cutting planes so an LP surrogate reproduces MILP optima —
  another certified-surrogate template.

Threats: "learn a value-function surrogate for a MILP" is taken in generic
form. Open: price-parametric value functions and region maps for
set-partitioning/EVSP structure, active sampling at region boundaries, and
coupling the learned map back into a market equilibrium with exact correction.

### ML-accelerated column generation (update to handoff Section 5)

Beyond Gerbaux/Morabit/Xia/You already catalogued: AGGNNI-CG (GNN-guided
pricing for joint paratransit trip planning and crew scheduling,
arXiv:2401.03692), RL hyper-heuristic pruning of pricing networks including
bus driver scheduling (Computers & Industrial Engineering, 2025), ML ranking
of multiple pricing problems in branch-and-price (EJOR 320(2), 2025), and
end-to-end RL pricing (POMO-CG, arXiv:2504.02383). The acceleration space is
crowded; our differentiation must stay "learning across *price/tariff*
parameters with certificates," not generic CG speedups.

---

## E. Domain scan: electric bus fleets in electricity markets (2024-2026)

Relevant to: overall novelty of the umbrella thesis.

- *When Agents Meet Electric Bus Fleet Operations* (2026), arXiv:2606.26400:
  an LLM-agent "aggregator" layer over an e-bus scheduling optimizer with
  V2G, tariff adaptation, and re-optimization triggers; studies
  aggregator-vs-operator value split. Not exact market design, no endogenous
  prices; signals the domain is active and that the aggregator/operator
  *split of flexibility value* resonates — our mechanism-design chapters
  answer questions this line raises informally.
- *Optimal Charging Schedule Planning for Electric Buses Using Aggregated
  Day-Ahead Auction Bids* (Energies 14(16):4727, 2021): three-stage
  aggregate-envelope bidding for a real campus bus system; price-taking; no
  duty-level bids; disaggregation stage acknowledges the aggregate-to-vehicle
  gap that our atomic approach eliminates by construction.
- DTU MSc thesis (2024/25): e-bus aggregated FCR-D/aFRR bidding in DK2 with
  MILP scheduling — reserve markets, price-taking.
- *Grid-Aware Charging and Operational Optimization for Mixed-Fleet Public
  Transit* (2026), arXiv:2601.08753: MILP joint charging + trip assignment
  under dynamic prices (Chattanooga); operations only, exogenous prices.
- Regulatory tailwind (FERC Order 2222 implementations, EU bidirectional
  tariff mandates) makes fleet-scale market participation institutionally
  real — useful for motivation sections.

Conclusion: no new academic work closes the Lu et al. (2021) gap. The
umbrella thesis question (clear and compensate mandatory, indivisible fleet
schedules under endogenous prices, exactly) remains open.

---

## F. Consolidated implications for the candidate directions

| Direction (handoff Section 6) | Scan verdict | Sharpened by |
|---|---|---|
| A. Certified atomic price-maker fleet market | Strengthened: MIBLP + IPG toolboxes exist to build on; read DW-bilevel preprint first | Sections A, B |
| B. Fleet duties as a bid language | Strongest single upgrade: EUPHEMIA exclusive groups are a live product; menu *generation* via CG is unclaimed | Section C |
| C. Counterfactual-free flexibility products | Alive; deliverability of capacity caps under mandatory service is the unclaimed piece | Section C |
| D. Active learning at switch boundaries | Two citable theory frames (performative prediction; algorithms with predictions); mp-MILP gives the vocabulary | Section D |
| E. Competition and mitigation | Renamed: this is an EVSP-IPG; equilibrium separation = our oracle; no IPG application uses CG-accessed strategy sets | Section A |

New brainstorm entries this scan adds (extending handoff Section 6.2):

- **EVSP-IPG.** Formulate the multi-fleet game as an integer programming game
  whose equilibrium separation oracle is branch-and-price EVSP; report
  ZR-style certified equilibrium gaps under capped oracles.
- **Exclusive-group menu design.** Column generation as a bid-menu generator
  for EUPHEMIA exclusive groups; welfare/profit loss vs menu size; strategic
  vs price-taking menus; fallback-schedule exposure for mandatory service.
- **One-sided learned value functions.** Learn certified lower bounds on the
  fleet's tariff-to-cost value function (GVF-style) to prune price search
  with guarantees between exact solves.
- **Performative scheduling theory.** Existence/convergence of performatively
  stable schedules when the decision map is an argmin over a finite duty
  space; connect Phase-1 cycling experiments to stateful performative
  prediction.
- **Consistency-robustness certificates.** State the two-fidelity oracle as a
  learning-augmented algorithm and prove its consistency/robustness contract.
- **Deliverable capacity products.** Compute and price the feasible set of
  capacity limitations a trip-covering fleet can sell (CLS literature +
  EVSP feasibility oracle).

## G. Verification debts created by this scan

Every entry above is abstract-level. Before any of it enters a manuscript or
a final thesis pitch:

1. Read in full: the DW-bilevel single-level reformulation preprint (2025);
   Karasavvidis et al. (2024) TEMPR; the ZR and Cut-and-Play papers; the IPG
   tutorial; the performative-prediction survey; the GVF NeurIPS 2024 paper.
2. Verify the exact citation of the Fanzeres/Street/Pozo CCG-for-Nash paper.
3. Confirm EUPHEMIA exclusive-group rules from the current NEMO Committee
   public description (the 2013 description found here may be outdated in
   details such as bid-count limits, which matter for menu-size questions).
