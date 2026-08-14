# Master brainstorm: price formation for indivisible mobile flexibility

Date: 2026-08-14

Status: living idea catalog. Consolidates the handoff Section 6.2 brainstorm,
the external deep-dive scan, and the four-agent microgrid/dictator/V2G/theory
scan (full reports in `review_notes/agents/`). Every idea carries a stable ID
for future reference, its closest prior art, and a kill test. Evidence tiers:
the 17 supplied papers are full-text audited; everything else is
abstract-level pending verification (`review_notes/` for details).

## 1. The scenario map (three axes)

Every idea below lives at a point (or path) in this cube:

- **Axis 1 — Who controls what (the regime spectrum):**
  U = uncontrolled charging; T = price-taking fleet (EVSP at posted prices —
  EVSP-DR today); M = strategic price-maker fleet (minimizes own bill
  anticipating price impact); D = benevolent dictator (one agent plans both
  generation and fleet — the Cho-Lodi-Scaglione manuscript today); MECH =
  decentralized but designed (internal tariffs, two-part transfers, menus,
  auctions).
- **Axis 2 — Grid scale:** national day-ahead market (fleet small but
  non-negligible; Nord Pool/SE3 data) <-> distribution feeder (DLMP) <->
  microgrid (fleet is 50-90% of load; step supply stack: solar ~0, storage
  opportunity cost, diesel marginal cost, scarcity; islanding possible).
- **Axis 3 — Technology:** charging only <-> V2G <-> V2G + on-site solar +
  stationary storage <-> mobile energy (spatial transport, resilience).

The thesis's identity: the fleet's flexibility is **indivisible** (trip-
covering duties, integer vehicles), so its value function
V(p) = min_S [c(S) + p·e(S)] is concave piecewise-linear, its load response
is a jumping supergradient, and *every* classical price-coordination result
(existence, convergence, welfare bounds, marginal pricing, smooth monopsony)
breaks in a characterizable way. One oracle (the CG/branch-and-price EVSP)
serves as: best-response solver, deviation/separation oracle, counterfactual
solver, bid/menu generator, and certificate producer.

## 2. The unified narrative (the "spine")

> **Price formation for indivisible mobile flexibility: from benevolent
> dictator to market.**

The chain (each link literature-verified as separately known, jointly
unclaimed — see `review_notes/MICROGRID_DICTATOR_V2G_SYNTHESIS_20260814.md`):

1. The dictator problem is a Dantzig-Wolfe structure; master duals are
   internal prices; the EVSP is the pricing subproblem.
2. The naive chicken-and-egg loop = unstabilized decomposition (Uzawa/Kelley);
   its cycling is the discrete Scarf/cobweb phenomenon.
3. Damping = stabilized column generation, with certificates.
4. Converged duals = convex-hull prices of the integrated economy; the
   MIP-LP gap = minimum internal uplift = the price of indivisibility.
5. Two-part (O'Neill) transfers repair support; incentive compatibility under
   private duty information is open.
6. The strategic fleet = the taker at marginal-outlay prices = a proximal
   step on the dictator's dual: **strategic behavior is self-stabilizing**.

This spine connects the two existing artifacts (EVSP-DR = T endpoint;
evspv2g_dp = D endpoint) and makes the microgrid the setting where every
effect is first-order rather than marginal.

## 3. Idea catalog

Grouped by candidate thesis chapter. Priority tags: [CORE] load-bearing for
the recommended arc; [STRONG] high-value optional; [OPP] opportunistic /
collaboration-dependent; [LATER] real but sequenced after the core.

### Chapter I — Computation: decomposition as price formation

- **B1 [CORE] "Tatonnement = Kelley" theorem + minimal cycling instance.**
  Formalize: naive price iteration = unit-step Uzawa / Kelley cutting-plane
  on the dictator's Lagrangian dual. Construct a minimal two-duty, two-period
  instance that 2-cycles (fleet flip-flops between charging windows — a
  discrete Scarf economy). Prove stabilized CG (du Merle box/penalty; bundle
  per Frangioni 2002) restores finite convergence with monotone LP
  certificates. Prior art: all pieces published separately (Briant 2008;
  Scarf 1960; Ma-Callaway-Hiskens 2013; du Merle 1999); the identity is not.
  Kill test: a paper is found stating this equivalence for demand-side
  scheduling (none found by agent 2 after targeted probes).
- **B2 [CORE] Stabilized price negotiation on the evspv2g_dp master.** Wrap
  the existing DP pricer in a stabilized master (5-piece du Merle penalty;
  Pessoa-style auto-tuned smoothing; stability center at historical/TOU
  prices). Report iterations-to-certificate vs unstabilized, and dual-path
  smoothness — "the price path a coordinator would broadcast" — a metric no
  OR paper reports. Nobody has stabilized a two-sided master (generation rows
  + fleet convexity rows) — agent 2, novelty check (b).
- **B3 [CORE] Internal uplift atlas.** At CG termination, duals = convex-hull
  prices of the integrated economy; define internal uplift = restricted-
  master-MIP minus master-LP value; map it vs fleet size, charger scarcity,
  V2G on/off, battery size, solar share. Practitioner punchline: "how big a
  make-whole budget does a depot need before prices alone can run it?"
  Prior art: Gribik-Hogan-Pope identity, Andrianesis 2021 (generation side);
  internal/organizational version unclaimed.
- **B4 [STRONG] Shapley-Folkman asymptotics.** Prove per-vehicle duality gap
  of the dictator problem is O(1/N) in fleet size — price coordination
  becomes asymptotically exact for large fleets, which is precisely why the
  microgrid/small-fleet case genuinely needs integration. (Verify the
  Aubin-Ekeland base reference.)
- **B5 [STRONG] Prices vs quantities inside the dictator.** Benders/
  Kornai-Liptak quantity-directed coordination (energy budgets to the fleet)
  vs DW price-directed; compare convergence, certificates, degeneracy
  robustness. Practical reading: the right day-ahead *contract format*
  between a transit authority and a utility. Prior art: Burton-Damon-
  Loughridge 1974 (LP world only).
- **B6 [OPP] Truncated-negotiation bounds.** Real coordination gets k rounds
  (day-ahead: k=1). Bound suboptimality after k serious steps of stabilized
  CG — the communication complexity of the implied market. 
- **B7 [OPP] Degeneracy surgery for two-sided masters.** Identical trucks x
  identical gensets = doubly degenerate duals ("chattering" both sides);
  characterize the dual optimal face; test minimum-norm/interior dual
  selections as "canonical internal prices."

### Chapter II — Economics: the welfare ladder and its pathologies

- **B8 [CORE] Four-regime welfare theorem (W_U, W_T, W_M, W_D).** With
  combinatorial S and step/convex supply g: (i) W_D <= W_M always; (ii) test
  whether the 4/3 linear-price PoA bound (Anunrojwong et al.; Jiang et al.
  tightness) survives combinatorial strategy sets; (iii) **construct
  instances with W_T > W_M and even W_T > W_U** — the naive price-taker
  strictly worse than doing nothing (the atomic-agent formalization of the
  avalanche effect; headline: *price signals can be worse than no signals
  for a single large discrete agent*); (iv) bound W_T − W_D by supply-step
  sizes at the herding hour. Kill test: Anunrojwong/Jiang machinery is shown
  to cover finite strategy sets already (verify full texts first).
- **B9 [CORE] Discrete monopsony lemma.** Show regime M = regime T evaluated
  at marginal-outlay prices p~_t = g_t + L_t g_t'; hence M is computable with
  the *same* EVSP oracle at modified prices (algorithmic payoff), and the
  monopsony distortion is a difference of two supergradient selections —
  zero until a threshold fleet size, then a lumpy withholding jump. A
  qualitatively new monopsony phenomenon (classical markdown formulas assume
  smooth demand). Prior art: Kazempour-Conejo-Ruiz MPEC (continuous);
  Baldick monopsony notes; nothing discrete.
- **B10 [CORE] Cobweb/cycling theorem tied to the integrality gap.** The
  taker iteration has a fixed point iff the CG master has an integral optimum
  at the equilibrium price; otherwise 2-cycles exist and damped price
  iteration converges to a *mixed/split schedule* equilibrium. Ties market
  convergence to the thesis's own algorithmic object. (With B1, possibly one
  paper.)
- **B11 [STRONG] Performative scheduling.** Import Perdomo et al.: the
  price-forecast map is piecewise-constant, so pure self-confirming forecasts
  can fail to exist (Grunberg-Modigliani continuity fails); distributional
  stable forecasts exist by Kakutani over the schedule simplex; convergence
  of repeated retraining iff B10's damping holds. Define the fleet's
  **performative power** P = max over schedule pairs of induced price
  movement — a measurable "big enough to matter" statistic; show the T/M gap
  is O(P · fleet energy). First performative-prediction analysis with a
  combinatorial responder; ML-venue-compatible.
- **B12 [STRONG] Major-minor game: atomic fleet + convex fringe.** One
  integer-program major player, mean-field fringe of small chargers. Does the
  fringe smooth the residual price curve enough to restore convergence
  ("fringe as stabilizer")? Comparative statics in the fleet/fringe ratio
  interpolate the national-market and microgrid poles. First major-minor
  model whose major player is an IP.
- **B13 [OPP] Emissions-dictator vs cost-dictator.** Both solve min over the
  same S with different hourly signals; characterize schedule overlap via
  rank correlation of the price and emissions stacks; bound the emissions
  excess of the cost-dictator. Performative twist: a large fleet invalidates
  marginal-emissions signals exactly as it invalidates prices (Nature Comms
  cascading-MEF); the "cascading MEF fixed point" = the emissions-dictator
  optimum. Connects to 24/7-CFE debate (Xu et al. Joule 2024; Luke et al.).
- **B14 [OPP] Market-power monitoring with a timetable alibi.** Extend
  storage-withholding detection (arXiv:2405.01442) to a duty-constrained
  fleet: can monitors distinguish strategic under-discharge from
  timetable-forced behavior? Policy: should municipally-owned fleets in thin
  local markets be mitigated?

### Chapter III — Mechanism and market design for one indivisible bidder

- **B15 [CORE] The decentralization ladder on one instance family.** On
  evspv2g_dp instances: (R1) dictator MILP; (R2) posted internal marginal
  prices, price-taking fleet; (R3) strategic fleet (bilevel); (R4)
  auction/transactive clearing with duty-flexibility bids. Report the "price
  of decentralization" at each rung. Prior art: Cornélusse 2019 does
  R1-vs-R2 without vehicles; battery-PoA papers do R1-vs-R3 without duties.
- **B16 [CORE] Internal settlement layer: CH prices vs O'Neill two-part
  transfers.** Two internal transfer-price systems for the same physical
  dictator solution (uniform minimum-uplift vs multi-part exactly-supporting);
  which better guides incremental decisions (adding a truck, shifting a
  trip)? An organizational-economics experiment nobody has run on a real
  scheduling model. Extends B3.
- **B17 [CORE] Screening a fleet whose type is a feasibility set.**
  Principal-agent: SO knows g, fleet privately knows (S, c). Type space =
  support functions of discrete sets (V(p) itself). Targets: revelation
  principle reduces mechanisms to menus of (load profile, payment) pairs
  (Chao-Wilson generalized from reliabilities to profiles); **"information
  rent >= integrality gap"** candidate theorem; does efficiency require
  commanding wasteful duties (Gerding-style "burning")? Prior art: priority
  service, DR menus, online EV mechanisms with interval types — never a
  combinatorial feasibility-set type.
- **B18 [STRONG] Duties as bids, two institutional instantiations.**
  (a) Wholesale: EUPHEMIA exclusive-group menus generated by column
  generation (menu design under bid-count budgets; exposure/fallback for
  mandatory service; welfare loss vs K) — anchored to Karasavvidis 2024 and
  the live Nord Pool product; (b) Microgrid: CG columns as package bids in an
  internal combinatorial auction — the LP master *is* the winner-determination
  relaxation; design payments (pay-as-clear duals + uplift, or VCG-on-columns)
  and analyze misreporting. Prior art: EG bidding for stylized flexible
  demand (2024/2026); LEM auctions assume many small simple bidders.
- **B19 [STRONG] Deliverable capacity products.** Compute and price the
  feasible set of capacity caps/envelopes a trip-covering fleet can sell
  (caps verifiable by meter — no baseline). The cap's shadow price sits on an
  IP, not an LP — characterizing it is the open part. Fits the capacity-
  limitation-service literature (Ziras 2021; DTU 2023) which never checks
  mandatory-service deliverability.
- **B20 [STRONG] Reverse-Stackelberg tariff design against an EVSP follower.**
  The operator designs a (time-varying, affine-in-power) internal tariff such
  that the fleet's own EVSP reproduces the welfare-optimal schedule. Exact
  steering is generally impossible under integrality — characterize the
  achievable set and optimal affine approximation. Prior art: EJOR 2025
  reverse-Stackelberg LEM (convex prosumers).
- **B21 [OPP] Market-impact fee.** Charge the fleet the marginal-outlay wedge
  L_t g_t' and prove it implements D in dominant strategies when g is known;
  quantify mis-implementation under private duty costs. Policy-facing
  companion to B9/B17.

### Chapter IV — Technology: V2G, solar, location, resilience

- **B22 [CORE] Price-maker EVSP-V2G via convex supply stack in the master.**
  Replace linear energy cost with a convex PWL supply curve (microgrid stack
  or residual-demand curve); master stays LP; time-indexed balance duals
  become endogenous prices fed to DP pricing; CG converges to a fleet-level
  equilibrium with a certificate ("CG = tatonnement over duty space").
  Compare vs bilevel/MPEC baselines (Manzolli-style) on cost and scale. This
  is the concrete algorithmic realization of B1/B2 with V2G included.
- **B23 [STRONG] Locational duals in duty pricing.** Multi-node microgrid /
  linearized DistFlow in the master; chargers at nodes; labeling sees node-
  and time-indexed reduced costs, so duties decide *where* to charge or
  discharge under congestion. First exact "locational V2G-EVSP" (agent 3
  novelty check (c): no incumbent). Swedish data + synthetic feeder.
- **B24 [STRONG] Energy-deadheading duties ("the bus network as a virtual
  transmission line").** Add energy-ferry arcs (deadhead purely to discharge
  at a higher-value node); derive the basis-entry condition
  (spread >= wear + deadhead + driver cost), echoing mobile-storage marginal-
  value theory (arXiv:2303.09704) under service-coverage constraints.
  Confirmed open (nearest misses: Crozier freight arbitrage; Dolatabadi
  school-bus energy logistics).
- **B25 [STRONG] Degradation-consistent V2G labeling.** Dominance rules for
  labels carrying (SOC, accumulated wear) under a DOD-nonlinear wear-density
  valid for charge and discharge; prove correctness for monotone densities;
  validate ex post with rainflow. Generalizes Zhang 2021 / Klein-Schiffer
  2023 to bidirectional power.
- **B26 [OPP] Two-stage stochastic CG with duty-level recourse.** Second-stage
  columns re-cover trips under PV/price scenarios (current literature's
  recourse is only "buy grid power" or "send a diesel bus"); value of duty
  recourse is largest when V2G commitments are aggressive.
- **B27 [OPP] P90-certified reserve-by-timetable.** Joint chance constraint:
  committed reserve deliverable in >=90% of scenarios given realized
  timetable/SOC — the *schedule* is the decision, not just the bid. Nordic
  P90 rule (arXiv:2404.12807) is the regulatory container.
- **B28 [OPP] V2G self-cannibalization curve.** With B22, sweep fleet size
  and quantify per-bus V2G revenue decay as the fleet's own discharge
  depresses peaks (endogenizes the HBS/PJM spread-cannibalization finding).
  A policy artifact no price-taking model can produce.
- **B29 [OPP] Resilience option value.** Duties remain feasible while
  reserving mobile energy for islanding events in a rare-event scenario tree;
  prices the fleet-as-backup option without dedicated MESS capex. Military
  and school-district cases.
- **B30 [LATER] Islanded-microgrid regime map.** Map optimal duty structure
  across internal price regimes (solar-surplus ~0 / storage opportunity /
  diesel / scarcity) as fleet dominance grows 10%->80%; quantify the error of
  the exogenous-tariff assumption used by the entire depot-EMS literature.
  The cleanest empirical "so what" experiment.

### Cross-cutting — learning and competition (kept alive, sequenced later)

- **B31 [LATER] Switch-boundary/region learning with certificates.** As in
  the prior scan (mp-MILP vocabulary; GVF one-sided bounds; algorithms-with-
  predictions consistency/robustness for the two-fidelity oracle). Scope
  decided by Phase-2 evidence on how often duty switches matter.
- **B32 [LATER] EVSP-IPG (multi-fleet competition).** Two depots on one
  microgrid/feeder, each with an exact oracle, interacting through prices;
  Zero-Regrets-style equilibrium separation with branch-and-price best
  responses; certified equilibrium gaps under capped oracles. Also the
  "timetable rigidity softens or intensifies competition?" hypothesis.
- **B33 [LATER] Benchmark suite.** Public EVSP-V2G-microgrid instances
  (Swedish-data derivative + solar traces + supply stacks) with LP bounds and
  gaps — the "Solomon instances" of the field; sets the evaluation standard
  competitors (mostly metaheuristics without bounds) must meet.
- **B34 [OPP] Seaport/drayage transfer case.** Port microgrids already couple
  berth scheduling with energy management via Stackelberg (Sun et al. 2025);
  a domain-transfer chapter strengthens generality and taps a distinct
  reviewer pool.

## 4. Recommended thesis arc (my ordering)

Working title: **"Price formation for indivisible mobile flexibility: from
benevolent dictator to market."**

1. **Chapter I (methods core): B1 + B2 + B3 (+B22).** Fastest to results —
   it extends evspv2g_dp directly, the machinery exists, and there is timing
   pressure (the manuscript is public; Najafi-Fripp and Andrianesis own the
   nearest framings). Deliverable: "Damping is stabilization: the
   chicken-and-egg iteration as unstabilized Dantzig-Wolfe," with the
   internal-uplift atlas as the empirical half.
2. **Chapter II (economics): B8 + B9 + B10 (+B11).** The four-regime welfare
   ladder with the self-defeating-taker construction and the discrete
   monopsony lemma. Positions directly against Anunrojwong/Jiang (convex
   batteries) — verify those two full texts before finalizing claims.
3. **Chapter III (design): B15 + B16 + B17 (+B18/B19).** The decentralization
   ladder, internal settlements, and the feasibility-set screening theory.
   B18a (EUPHEMIA menus) doubles as a standalone, institutionally grounded
   paper on the Nordic data.
4. **Chapter IV (technology): B23 + B24 + B25 (+B27/B28).** Locational and
   V2G extensions where the microgrid makes everything first-order; energy
   deadheading is the most original single idea in the catalog.
5. **Cross-cutting (sequenced by evidence): B31-B33.**

Earlier direction letters map as: A -> I+III, B -> III (B18), C -> III (B19),
D -> cross-cutting (B31), E -> cross-cutting (B32). Nothing is dropped; the
microgrid/dictator frame re-centers them.

**First-paper recommendation (decision pending user approval; see
`RESEARCH_DIRECTIONS.md` Section 4):** Chapter I's B1+B2+B3 package, on
evspv2g_dp instances. Rationale: unique claim with verified white space,
direct reuse of existing code, natural co-author alignment (Lodi: CG/IPG;
Scaglione: microgrids), and it establishes the spine every later chapter
cites. B18a (exclusive-group menus, Nordic data) is the strongest independent
second paper and can proceed in parallel with EVSP-DR machinery.

### Future-frontier additions (added 2026-08-14 evening, supplied by the user
from external LLM brainstorming; abstract-level, kill tests as given)

- **B35 [LATER] Incentives under bounded computation ("the price of a time
  limit").** Make the exactness-tier hierarchy an economic primitive: the
  operator's counterfactual and no-deviation solves are branch-and-price runs
  with budgets, so every payment (VCG, uplift, convex-hull) is computed from
  an anytime bound, not a true optimum. Which settlement rules retain
  (approximate) incentive compatibility when computed from certified LP
  bounds? Can a bidder exploit the operator's time limit by submitting
  hard-to-price instances? Do monotone certificates restore truthfulness
  where Nisan-Ronen-style approximate VCG loses it? Kill test: the
  approximate-mechanism-design literature already covers settlement from
  certified bounds in combinatorial exchanges.
- **B36 [LATER] Endogenous timing: the chicken-and-egg as a commitment
  game.** In a Hamilton-Slutsky endogenous-timing game, does the indivisible
  fleet prefer to commit quantities before price formation (inelastic bids)
  or respond after (price-responsive bids)? Bid-format choice = timing
  choice; gives B18 a strategic foundation. Plausibly kinks make commitment
  strictly valuable where smooth players are indifferent. Kill test:
  endogenous-timing results already cover finite/discrete strategy sets
  transferably.
- **B37 [STRONG-LATER] "How wrong is the virtual battery?" — certified
  aggregation error.** Compute certified inner and outer approximations of
  the true trip-covering load-flexibility set (projection of the duty
  polytope onto load space) via column generation; prove hardness of exact
  aggregation; bound the error vs fleet size (Shapley-Folkman/B4 gives the
  O(1/N) upper end; the interesting result is the small-fleet/microgrid
  lower end). The quantitative indictment justifying the thesis; strengthens
  B19 (the inner approximation is the sellable capacity product). Kill test:
  the TCL/EV flexibility-aggregation (zonotope/virtual-battery) literature
  already has tight bounds for set-partitioning-constrained loads.
- **B38 [LATER] Forward contracting / two-settlement for a discrete
  monopsonist.** Allaz-Vila says forwards erode market power for smooth
  players; with a piecewise-constant marginal-outlay response, small forward
  positions can flip whole duties, so the classical result may fail or
  reverse. Pairs with B9; same oracle at contract-adjusted prices. Kill
  test: storage two-settlement papers already handle nonconvex responders.
- **B39 [LATER] The slow loop: timetable design as the outer
  chicken-and-egg.** Service design shapes the flexibility set being priced
  (slack minutes, interlining freedom, depot placement are purchases of
  flexibility): flexibility-aware timetabling under endogenous prices, the
  investment-timescale feedback loop. Highest model risk; check the joint
  timetabling-and-charging literature first.

External reviewer's ranking of these: B35 and B37 are load-bearing for the
thesis identity (one makes the exactness regime a contribution, the other
makes "atomic matters" a theorem rather than a premise); B36 cheapest to
check; B38/B39 optional breadth.

## 5. Decision gates and falsification tests (additions to handoff 8.7)

- If the 2025 DW-bilevel preprint or any found paper already delays
  follower-column generation inside price formation, narrow Chapter I to the
  economic reading (uplift atlas, price-path quality) — the framing survives,
  the algorithmic claim shrinks.
- If Anunrojwong/Jiang's PoA machinery extends trivially to finite strategy
  sets, Chapter II pivots to the T-regime (their comparison omits the naive
  taker) and the cycling/integrality-gap link (B10), which they cannot state.
- If Phase-2 experiments show duty switches are rare and charging-only
  response explains nearly everything, B31 shrinks and Chapters I/III carry
  the thesis (they do not depend on switch frequency).
- If stabilized CG does not materially beat damped heuristics empirically,
  the *certificate* story (bounds at every iterate) remains the differentiator
  — report honestly.
- B24 (energy deadheading) dies if deadhead + wear costs dominate all
  realistic locational spreads at microgrid scale; check magnitudes early
  with a back-of-envelope screen before building anything.

## 6. Coordination and timing notes

1. **Internal:** Scaglione co-authored arXiv:2505.04532 (logistics<->LMP
   fixed-point equilibrium). The thesis must position relative to that line —
   coordinate before drafting; ideally it becomes a cited sibling, not a
   collision.
2. **Speed:** arXiv:2508.06752 makes the dictator formulation public;
   Najafi-Fripp (DW price coordination), Andrianesis (DW = CH prices), and
   the Dolatabadi/Zeng B&P energy-logistics group are all one step away from
   the framing. Chapter I should be claimed quickly.
3. **Full-text verification debts** are tracked in `READING_QUEUE.md`; no
   claim in this file is manuscript-grade until its anchors are read.
