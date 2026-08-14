# Novelty matrix

Date: 2026-08-14

Rows: the papers closest to the thesis. Columns: the dimensions whose
*combination* defines our claim. Table A rows are full-text audited
(authoritative; see `review_notes/`); Table B rows are abstract-level
(verify before citing details; see `review_notes/EXTERNAL_DEEP_DIVE_20260814.md`
and `review_notes/agents/`).

Column key:

- **Duties**: timetabled, trip-covering vehicle duties (atomic EVSP)?
  Y / P (partial: some vehicle/route structure) / N (aggregate, flows, or
  sessions).
- **EndogP**: shared price formed endogenously (market clearing, supply
  stack, or dispatch duals moved by the agent's load)? Y / P (own-load cost
  nonlinearity or bargained contract only) / N (exogenous tariff).
- **Scale**: W = wholesale/transmission, D = distribution/DLMP,
  M = microgrid/local, - = none/abstract.
- **V2G**: bidirectional vehicle power (or storage as the flexible asset)?
- **Strat**: strategic (price-anticipating) actor modeled?
- **Mech**: settlement/mechanism design content (uplift, VCG, menus,
  baselines, transfers)?
- **Learn**: learning/surrogate component?
- **Exact**: certificates (LP bounds, exact B&P/CG, closed-form theory)?
  Y / P (MILP solver or relaxation without gap discipline) / N (heuristic).

## The target combination (no row below fills it)

> **This thesis:** Duties Y | EndogP Y | Scale W+M | V2G Y | Strat Y (and
> planner and mechanisms) | Mech Y | Learn optional | Exact Y (CG/B&P
> certificates, honest tiers).

## Table A — full-text audited (17 supplied papers)

| Paper | Duties | EndogP | Scale | V2G | Strat | Mech | Learn | Exact | One-line position |
|---|---|---|---|---|---|---|---|---|---|
| Deori et al. 2018 | N | Y (affine) | - | N | Y (many small) | N | N | Y (convex) | Continuous charging game; PoA -> 1; convexity does all the work |
| Zoltowska 2016 | N (divisible shift) | Y (auction) | W | N | N | Y (min-uplift) | N | Y (MILP) | Min-uplift for shiftable demand; no routes |
| Zou et al. 2016 | N | Y | W | Y (storage) | Y (EPEC) | N | N | N (local NLP) | Strategic storage equilibrium; KKT machinery fails for IPs |
| Fang et al. 2022 | N | Y (LP clearing) | W | Y (storage) | P | Y (VCG+bargain) | N | Y (convex) | Storage VCG; proofs need convexity |
| Wu et al. 2019 | N (frequencies) | Y (DLMP) | D | N | P (bilevel) | N | N | P (MPCC) | Bus ops + DLMP; service is elastic |
| Lu et al. 2021 | P (TSN, min departures) | Y | W | Y | Y (leader) | N | N | P (MILP/KKT) | Closest domain precedent; not trip-covering |
| Wang et al. 2024 | N (traffic UE) | Y (DLMP loop) | D | N | Y (aggregator) | P (retail prices) | N | N | The fixed-point loop exists; smooth flows only |
| Afentoulis & Vagropoulos 2025 | N (sessions) | N | W (balancing) | N | Y (gaming) | Y (baselines) | N | P (MILP) | Baseline manipulation, real data |
| Gonzalez Vaya & Andersson 2015 | N (virtual battery) | Y | W | N | Y | N | N | P (MILP/KKT) | Price-maker EV aggregator; aggregate only |
| Wu et al. 2016 | N (envelopes) | Y (LMP) | W | N (unidir. reg) | Y (Bayesian game) | N | P (regressions) | N | Multi-aggregator game; smooth responses |
| Toquica et al. 2020 | N (storage env.) | Y (ACOPF) | W | Y | Y (monopoly) | N | N | N (ant colony) | Monopoly V2G vs nodal prices |
| Xie & Xu 2025 | N | Y (learned SPQC) | W | Y (storage) | Y | N | Y (KDE curves) | N (local TR) | Learned price impact; observational, local |
| Ding et al. 2022 | N (logit flows) | Y (DNO) | D | Y | Y (Nash/Stack.) | P | N | N | Platform-DNO game; elastic service |
| Subramanian et al. 2022 | N (OD paths) | Y (SOCP ACOPF) | W | N | N (central) | N | N | P (conic MPEC, gaps) | Routing + endogenous LMP; no timetable |
| Chen et al. 2026 | N | P (optimizer labels) | D | N | N | N | Y (GNN) | N | Price-response surrogate; smooth aggregate |
| Wei et al. 2018 | N (Wardrop) | Y | D | N | N | N | N | Y (convex FP) | The static loop, formalized; nonatomic |
| Song et al. 2025 | N (dynamic UE) | Y | D | N | N | N | N | N (heuristic FP) | Dynamic loop + charger queues; nonatomic |

## Table B — abstract-level: closest external threats and anchors

| Paper | Duties | EndogP | Scale | V2G | Strat | Mech | Learn | Exact | One-line position |
|---|---|---|---|---|---|---|---|---|---|
| Yao, Liu, Scaglione, Bekhor, Zhang 2025 (arXiv:2505.04532) | N (MDP fleet) | Y (LMP FP, existence) | W | ? | N (equilibrium) | N | P | P | The loop formalized for logistics; coordinate internally |
| Cho, Lodi, Scaglione 2025 (arXiv:2508.06752) | Y | P (internal dispatch cost) | M | Y | N (dictator) | N | N | Y (CG, gaps) | Our dictator endpoint; no price-formation reading yet |
| Yetkin et al. 2024 (Opt&Eng) | N (mobile storage) | P (planner internal) | W (DC-OPF) | Y | N | N | N | P (MILP) | Dictator-with-fleet competitor; no set-partitioning/UC |
| Najafi & Fripp 2023 (Energy&AI) | N (convex devices) | Y (DW duals) | W | N | N | N | N | Y (convex DW) | DW = price coordination; stops at convexity |
| Andrianesis et al. 2021 (TPWRS) | N | Y (CH prices) | W | N | N | Y (uplift) | N | Y (DW exact) | DW computes CH prices; generation side only |
| Anjos, Lodi, Tanneau 2018 (TPWRS) | N (DER MILPs) | Y (DW duals) | D | P | N | N | N | Y (convexified) | DW coordination of MILP DERs; foundation |
| Cornelusse et al. 2019 (Applied Energy) | N (no vehicles) | Y (internal market) | M | P | N | Y (redistribution) | N | P (bilevel) | Dictator<->market spectrum, no fleet |
| Anunrojwong et al. (SSRN 4877753) | N (convex battery) | Y (closed form) | W | Y (storage) | Y | N | N | Y (theory) | 3-regime PoA in [9/8,4/3]; convexity essential |
| Jiang, Nie, Skoulakis 2026 (arXiv:2602.19660) | N | Y | W | Y (storage) | Y | N | N | Y (theory) | PoA unbounded for convex price fns (= step stacks) |
| Kazempour, Conejo, Ruiz 2015 (TPWRS) | N (bid curves) | Y | W | N | Y (monopsony) | N | N | P (MPEC) | Canonical strategic large consumer; smooth |
| Ma, Callaway, Hiskens 2013 (TCST) | N (convex profiles) | Y (broadcast) | - | N | N | N | N | Y (contraction) | Oscillation + damping proof; mean field |
| Gan, Topcu, Low 2013 (TPWRS) | N | Y (signal) | - | N | N | N | N | Y (convex) | Damped protocol converges; convex sets |
| Roozbehani, Dahleh, Mitter 2012 (TPWRS) | N | Y (feedback) | W | N | N | N | N | Y (control) | Elasticity-ratio instability criterion |
| Bailey et al. 2025 (AER:Insights) | N (households) | Y (empirical) | D | N | N | P (tariff design) | N | - (field exp.) | TOU shadow peaks: self-defeating takers, empirically |
| Wu, Lin, Liu, Jin 2021/22 (TRB) | Y | P (peak objective) | - | N | N | N | N | Y (B&P) | Exact MDEVSP + grid proxy; no price formation |
| Zhang, Wang, Qu 2021 (TRE) | Y | N | - | N | N | N | N | Y (B&P) | Degradation in exact pricing; G2V only |
| Klein & Schiffer 2023 (Transp. Sci.) | P (fixed trips, flex ops) | N | - | N | N | N | N | Y (B&P) | Best labeling machinery; no V2G, no market |
| Karasavvidis et al. 2024 (TEMPR) | N (stylized FD) | N (price taker) | W (EUPHEMIA) | N | N | Y (bid formats) | N | P (MILP) | Exclusive-group bidding; no fleet, no CG menus |
| Energies 14(16):4727 2021 (bus auction bids) | P (aggregation stage) | N | W | N | N | P (bid format) | N | P (MILP) | Bus fleet -> aggregate DA bids; price-taking |
| Dolatabadi et al. 2025 (arXiv:2510.14131) | N (no timetable) | N | M (outage) | Y (V2B) | N | N | N | Y (B&P) | B&P energy logistics; most method-similar group |
| Manzolli et al. 2024 (Energy) | N (fixed trips) | P (bilevel prices) | - | Y | Y (aggregator) | P | N | P | Aggregator sets prices over PTO; trips fixed |
| Terada et al. 2025 (SEGAN) | N (charge slots) | P (Nash-bargained) | M | Y | P | P | N | P (MILP) | Microgrid sizing + V2G; bargained not market price |
| Luke et al. 2025 (Applied Energy) | P (route assignment) | N (emissions signal) | - | N (BESS) | N | N | P (forecasts) | P | 24/7 CFE fleet benchmark |
| Fei et al. 2023 (TRC) | P (timetable+fleet design) | N (contracts) | W | Y | N | P (contract types) | N | N | Transit V2G market economics |
| Zhou, An, Schmocker 2025 (Transportmetrica B) | P (cross-line) | N | - | Y | N | N | N | N (ALNS) | Best metaheuristic V2G-EVSP competitor |
| Crozier et al. 2023 (arXiv:2311.11464) | N (delivery, time windows) | N (price taker) | W (nodal) | Y | N | N | N | N | Spatial arbitrage by moving trucks |
| Sun et al. 2025 (Energy, seaport) | P (berth allocation) | Y (Stackelberg) | M | P | Y | N | N | P | Nearest cross-domain analogue (maritime) |
| Kuehnbach et al. 2021 (ESR) | N (population) | Y (avalanche) | W | N | N | N | N | - (simulation) | Names the avalanche effect at scale |

## How to read this

Every row has at least one N/P in {Duties, EndogP, Exact}; most have several.
The audited Table A establishes that the *combination* is unoccupied at
full-text confidence for the 17 closest supplied works; Table B extends that
to the scanned frontier at abstract confidence. The three columns that carry
our identity are Duties x EndogP x Exact — no found paper has all three at Y,
with or without the V2G/mechanism/learning extensions.

Maintenance rule: when a new paper is read, add a row *before* deciding what
it kills; if any new row reaches Y-Y-Y on Duties x EndogP x Exact, escalate
immediately (it is either a collision or a sibling to cite).
