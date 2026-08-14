# Novelty matrix

Last updated: 2026-08-14 (closure pass: keys added, exactness rubric
tightened, Table C added so that every `core-threat` record in `papers.csv`
is scored).

Rows are identified by their `papers.csv` key. Table A rows are full-text
audited (authoritative; see `review_notes/`); Tables B and C are
abstract-level (verify before citing details; sources in
`review_notes/EXTERNAL_DEEP_DIVE_20260814.md` and `review_notes/agents/`).
Coverage: Table A holds all 17 audited records; Tables B and C together hold
all 60 non-audited `core-threat` records plus selected method anchors.
Validation: every key below must exist in `papers.csv` (and vice versa for
core-threats); check with `tools/bibliography.py validate` plus a grep.

## Column key

- **Duties**: timetabled, trip-covering vehicle duties (atomic EVSP)?
  Y / P (partial vehicle/route structure) / N (aggregate, flows, sessions).
- **EndogP**: shared price formed endogenously (market clearing, supply
  stack, or dispatch duals moved by load)? Y / P (own-load cost nonlinearity,
  bargained contract, or forecast-feedback only) / N (exogenous tariff).
- **Scale**: W wholesale/transmission; D distribution/DLMP; M microgrid or
  depot/local; - none/abstract.
- **V2G**: bidirectional vehicle power or storage as the flexible asset.
- **Strat**: strategic (price-anticipating) actor modeled.
- **Mech**: settlement/mechanism-design content (uplift, VCG, menus,
  baselines, transfers, bid formats).
- **Learn**: learning/surrogate/forecast component.
- **Exact** (tightened rubric):
  - **C-t** — theory with proofs (closed forms, existence, bounds);
  - **C-a** — algorithm with a proven optimality/convergence certificate for
    its stated model (exact B&P/CG with gap reporting, MILP solved to proven
    optimality, exact convex methods);
  - **P** — partial certificate (relaxation bounds, KKT/big-M reformulations
    with caveats, solver-level results, reported nonzero gaps, LR bounds);
  - **N** — heuristic / no certificate;
  - **E** — empirical, simulation, or demonstration study.

## The target combination (no row below fills it)

> **This thesis:** Duties Y | EndogP Y | Scale W+M | V2G Y | Strat Y (and
> planner and mechanisms) | Mech Y | Learn optional | Exact C-a (CG/B&P
> certificates, honest tiers).

## Table A — full-text audited (17 supplied papers)

| Key | Duties | EndogP | Scale | V2G | Strat | Mech | Learn | Exact | One-line position |
|---|---|---|---|---|---|---|---|---|---|
| deori2018 | N | Y (affine) | - | N | Y (many small) | N | N | C-t | Continuous charging game; PoA -> 1; convexity does all the work |
| zoltowska2016 | N (divisible shift) | Y (auction) | W | N | N | Y (min-uplift) | N | C-a | Min-uplift for shiftable demand; no routes |
| zou2016 | N | Y | W | Y (storage) | Y (EPEC) | N | N | N | Strategic storage equilibrium; local NLP, no certificate |
| fang2022 | N | Y (LP clearing) | W | Y (storage) | P | Y (VCG+bargain) | N | C-a | Storage VCG; proofs need convexity |
| wu2019 | N (frequencies) | Y (DLMP) | D | N | P (bilevel) | N | N | P | Bus ops + DLMP; service is elastic; MPCC |
| lu2021 | P (TSN, min departures) | Y | W | Y | Y (leader) | N | N | P | Closest domain precedent; MILP via KKT/big-M |
| wang2024 | N (traffic UE) | Y (DLMP loop) | D | N | Y (aggregator) | P (retail prices) | N | N | The fixed-point loop exists; smooth flows; no convergence proof |
| afentoulis2025 | N (sessions) | N | W (balancing) | N | Y (gaming) | Y (baselines) | N | C-a | Baseline manipulation, real data, rolling MILP |
| gonzalezvaya2015 | N (virtual battery) | Y | W | N | Y | N | N | P | Price-maker EV aggregator; MILP via KKT/big-M |
| wu2016 | N (envelopes) | Y (LMP) | W | N (unidir. reg) | Y (Bayesian game) | N | P (regressions) | N | Multi-aggregator game; smooth responses |
| toquica2020 | N (storage env.) | Y (ACOPF) | W | Y | Y (monopoly) | N | N | N | Monopoly V2G vs nodal prices; ant colony |
| xie2025 | N | Y (learned SPQC) | W | Y (storage) | Y | N | Y (KDE curves) | N | Learned price impact; observational, local trust region |
| ding2022 | N (logit flows) | Y (DNO) | D | Y | Y (Nash/Stack.) | P | N | N | Platform-DNO game; elastic service |
| subramanian2022 | N (OD paths) | Y (SOCP ACOPF) | W | N | N (central) | N | N | P | Routing + endogenous LMP; conic MPEC with 6-9% gaps |
| chen2026 | N | P (optimizer labels) | D | N | N | N | Y (GNN) | N | Price-response surrogate; smooth aggregate |
| wei2018 | N (Wardrop) | Y | D | N | N | N | N | C-t/P | Existence proved; alternation algorithm empirical |
| song2025 | N (dynamic UE) | Y | D | N | N | N | N | N | Dynamic loop + charger queues; heuristic fixed point |

## Table B — abstract-level: closest external threats and anchors

| Key | Duties | EndogP | Scale | V2G | Strat | Mech | Learn | Exact | One-line position |
|---|---|---|---|---|---|---|---|---|---|
| yao2025 | N (MDP fleet) | Y (LMP FP) | W | ? | N | N | P | C-t/P | Loop formalized for logistics; coordinate internally |
| cho2025 | Y | P (internal dispatch cost) | M | Y | N (dictator) | N | N | C-a | Our dictator endpoint; no price-formation reading yet |
| yetkin2024 | N (mobile storage) | P (planner internal) | W | Y | N | N | N | P | Dictator-with-fleet competitor; no set-partitioning/UC |
| najafi2023 | N (convex devices) | Y (DW duals) | W | N | N | N | N | C-a | DW = price coordination; stops at convexity |
| andrianesis2022 | N | Y (CH prices) | W | N | N | Y (uplift) | N | C-a | DW computes CH prices; generation side only |
| anjos2018 | N (DER MILPs) | Y (DW duals) | D | P | N | N | N | C-a | DW coordination of MILP DERs; foundation |
| cornelusse2019 | N (no vehicles) | Y (internal market) | M | P | N | Y (redistribution) | N | P | Dictator<->market spectrum, no fleet |
| anunrojwong | N (convex battery) | Y | W | Y (storage) | Y | N | N | C-t | 3-regime PoA in [9/8,4/3]; convexity essential |
| jiang2026 | N | Y | W | Y (storage) | Y | N | N | C-t | PoA unbounded for convex price fns (= step stacks) |
| kazempour2015 | N (bid curves) | Y | W | N | Y (monopsony) | N | N | P | Canonical strategic large consumer; smooth |
| ma2013 | N (convex profiles) | Y (broadcast) | - | N | N | N | N | C-t | Oscillation + damping proof; mean field |
| gan2013 | N | Y (signal) | - | N | N | N | N | C-t | Damped protocol converges; convex sets |
| roozbehani2012 | N | Y (feedback) | W | N | N | N | N | C-t | Elasticity-ratio instability criterion |
| bailey2025 | N (households) | Y (empirical) | D | N | N | P (tariffs) | N | E | TOU shadow peaks: self-defeating takers |
| wu2021 | Y | P (peak objective) | - | N | N | N | N | C-a | Exact B&P MDEVSP + grid proxy; no price formation |
| zhang2021 | Y | N | - | N | N | N | N | C-a | Degradation in exact pricing; G2V only |
| klein2023 | P (fixed trips, flex ops) | N | - | N | N | N | N | C-a | Best labeling machinery; no V2G, no market |
| karasavvidis2024 | N (stylized FD) | N (price taker) | W (EUPHEMIA) | N | N | Y (bid formats) | N | P | Exclusive-group bidding; no fleet, no CG menus |
| optimalchargingschedule2021 | P (aggregation stage) | N | W | N | N | P (bid format) | N | P | Bus fleet -> aggregate DA bids; price-taking |
| dolatabadi2025 | N (no timetable) | N | M (outage) | Y (V2B) | N | N | N | C-a | B&P energy logistics; most method-similar group |
| manzolli2024 | N (fixed trips) | P (bilevel prices) | - | Y | Y (aggregator) | P | N | P | Aggregator sets prices over PTO; trips fixed |
| terada2025 | N (charge slots) | P (Nash-bargained) | M | Y | P | P | N | P | Microgrid sizing + V2G; bargained not market price |
| luke2025 | P (route assignment) | N (emissions signal) | - | N (BESS) | N | N | P (forecasts) | P | 24/7 CFE fleet benchmark |
| fei2023 | P (timetable+fleet design) | N (contracts) | W | Y | N | P (contract types) | N | N | Transit V2G market economics |
| zhou2025 | P (cross-line) | N | - | Y | N | N | N | N | Best metaheuristic V2G-EVSP competitor |
| crozier | N (delivery windows) | N (price taker) | W (nodal) | Y | N | N | N | P | Spatial arbitrage by moving trucks |
| sun2025 | P (berth allocation) | Y (Stackelberg) | M | P | Y | N | N | P | Nearest cross-domain analogue (maritime) |
| kuehnbach2021 | N (population) | Y (avalanche) | W | N | N | N | N | E | Names the avalanche effect at scale |

## Table C — remaining core-threat records (abstract-level, terse)

| Key | Duties | EndogP | Scale | V2G | Strat | Mech | Learn | Exact | One-line position |
|---|---|---|---|---|---|---|---|---|---|
| aggregator-contract-design2023 | N | N | - | N | P (screening) | Y (menus) | N | C-t | DR contract menus; scalar types |
| bragin2023 | N | P (multipliers) | W | N | N | N | N | C-t | LR survey; owns price-coordination rhetoric |
| bus-depot-microgrid-codesign2024 | N | N (tariffs) | M | P (ESS) | N | N | N | P | Depot-microgrid co-design/TCO |
| carvalho2024 | N (generic) | Y (follower markets) | - | N | Y | N | N | C-a | NASPs: Nash among Stackelberg leaders, exact algorithms |
| chao1987 | N | N | W | N | P | Y (priority menus) | N | C-t | Founding menu-of-contracts literature |
| cross-line-depot-config2026 | Y (cross-line) | N (ToU) | M (depot) | P | N | N | N | P (Benders) | Joint bus scheduling + depot sizing |
| dantzigwolfebilevel2025 | N (generic) | N | - | N | Y (bilevel) | N | N | C-a | DW single-level MIBLP; gates Chapter I scope |
| decision-focused-learning2024 | N | P (forecast feedback) | W | N | N | N | Y | P | Operator-side biased forecasts for price-responsive demand |
| dlmp-congestion-ev2025 | N (aggregate EVA) | Y (DLMP/ADMM) | D | N | N | N | N | P | Iterative DSO-EVA price loop |
| dlmp-ev-aggregator-bilevel2020 | N (envelope) | Y (DLMP) | D | N | Y | N | N | P | Price-anticipating EV aggregator vs DSO |
| dr-vcg2017 | N | N | - | N | Y | Y (VCG bundles) | N | C-t | Truthful DR contract bundles |
| dragotto2023 | N (generic IPG) | N | - | N | Y | N | N | C-a | Zero Regrets: equilibrium separation oracle |
| eb-operator-bidding2022 | P (trip-chain region) | N (price taker) | W | N | N | N | N | P (Benders) | Timetable-aware bidding; exogenous auction |
| ebus-control-arxiv2309 | P | N | - | N | N | N | N | P (LR) | E-bus charging + real-time control via LR |
| ebus-lr-applied-energy | N (per-bus charging) | N (ToU) | - | N | N | N | N | P (LR+DP) | Price-mediated decomposition inside transit charging |
| ev-microgrid-double-auction | N | Y (auction) | M | ? | P | Y | N | ? | EV microgrid double-auction comparison; verify |
| fanzeres2020 | N (gen side) | Y | W | N | Y | N | N | P (verify) | CCG for Nash in pool markets; citation to verify |
| generatingeuphemiabids2026 | N (electrolyzer/steel) | N (price taker) | W (EUPHEMIA) | N | N | Y (bid formats) | N | P | Hourly vs exclusive-group bids under uncertainty |
| gerding2011 / robu2013 | N (interval types) | N | - | N | Y | Y (online DSIC) | N | C-t | Private availability windows; "burning" inefficiency |
| graph-benders-etrucks2026 | N (freight routing) | N | - | Y | N | N | N | P (near-opt) | Exact-framework routing+V2G competitor |
| hammerstrom2008 | N | Y (double auction) | D/M | N | N | Y | N | E | Olympic Peninsula transactive demo |
| hardt2022 | N | Y (performative power) | - | N | Y | N | Y | C-t | Measures causal power to move the distribution |
| integer-bilevel-jota | N (generic) | N | - | N | Y | N | N | C-a | Integer-bilevel algorithmics toolbox |
| integrated-smart-charging-framework2025 | N (fixed trips) | N (dynamic tariffs) | M (depot) | Y | N | N | N | P (MILP) | Brussels everything-in-one-depot benchmark |
| joint-eb-charger-scheduling | P | N | - | N | N | N | N | P (LR bounds) | LR fleet+charger decomposition; tariff exogenous |
| kizil2025 | N (fixed trips) | P (grid constraints) | D | Y | N | N | N | P (MISOCP) | Bus V2G vs voltage/congestion; PV surplus |
| li2014 | N (aggregate) | Y (DLMP) | D | N | N | N | N | C-a (convex) | Canonical "prices decentralize the optimum" for EVs |
| luan2026 | N (nonatomic UE) | Y (congestion pricing) | - | N | N | N | Y | P | Learned price-to-route response, surrogate loop |
| ma2016 | N (profiles) | Y (smoothed) | - | N | N | N | N | C-t | Damped tatonnement = dual smoothing, unacknowledged |
| milp-v2g-degradation2025 | N (fixed fleet) | N (DA prices) | W | Y | N | N | N | P (MILP) | V2G-vs-smart-charging gap narrow at current costs |
| parametric-bilevel-bidding2013 | N | Y | W | N | Y | N | N | C-a | Bilevel bidding with integer lower level, exact |
| perdomo2020 | N | P (distribution map) | - | N | N | N | Y | C-t | Performative prediction founding paper |
| priority-service-bilevel2020 | N | P | W (UC) | N | P | Y (menus+UC) | N | P | Menu design with nonconvex generation |
| storage-withholding2024 | N (storage) | Y | W | Y (storage) | Y | P (monitoring) | N | C-t/P | Withholding detection framework |
| vaya2015a | N (virtual battery) | Y | W | P (regulation) | Y | N | N | P | Aggregator DA+regulation bidding, price impact |
| whenagentsmeet2026 | P (opt. model inside) | P (aggregator prices) | M (depot) | Y | P | P (value split) | Y (LLM agents) | N | Agentic aggregator over e-bus optimizer |

## How to read this

Every row has at least one N/P in {Duties, EndogP, Exact}; most have several.
Table A establishes at full-text confidence that the *combination* is
unoccupied among the 17 closest supplied works; Tables B and C extend that to
every scanned core-threat at abstract confidence. The three columns that
carry our identity are Duties x EndogP x Exact — no scored work reaches
Y / Y / C-a jointly, with or without the V2G/mechanism/learning extensions.

Maintenance rules:
1. When a new paper is read, add or update its row *before* deciding what it
   kills. Any row reaching Y-Y-C-a on Duties x EndogP x Exact escalates
   immediately (collision or sibling to cite).
2. Every `core-threat` record in `papers.csv` must have a row here; when
   tagging a new record core-threat, score it in the same commit.
3. Abstract-level scores (Tables B, C) are re-scored upon full-text audit and
   the row moves to Table A style confidence in the notes.
