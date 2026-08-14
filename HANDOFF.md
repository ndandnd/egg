# Zero-context handoff

Audience: an LLM (or human) with no prior context joining this project.
Last updated: 2026-08-14. For repository layout see `README.md`.

## 1. What this project is

PhD-thesis research on the **price-maker electric vehicle scheduling problem
(EVSP)**. The EVSP assigns electric vehicles to timetabled, mandatory trips
(set-partitioning over "duties" = feasible vehicle workdays, solved by column
generation; the pricing subproblem is a resource-constrained shortest path
with battery state of charge and charging decisions). Classical EVSP treats
electricity prices as exogenous. This project studies what happens when the
fleet's charging/discharging load is large enough to move the price itself:

> price -> optimal schedule -> aggregate load -> price ("chicken-and-egg").

Key mathematical object: the fleet's value function
V(p) = min over schedules S of [c(S) + p·e(S)] is concave piecewise-linear in
the price vector; the load response is its supergradient and *jumps* at
kinks. Every classical price-coordination result (existence, convergence,
marginal pricing, smooth monopsony, welfare bounds) breaks at those kinks in
a characterizable way. Three economic regimes are kept strictly separate:
price-taker (optimize at posted prices), strategic price-maker (minimize own
bill anticipating price impact), benevolent dictator (one planner controls
generation and fleet; minimizes true cost).

## 2. The team's existing assets (separate repositories)

- **EVSP-DR** (`/Users/nathan.cho/Documents/demandResponse/EVSP-DR`, branch
  `peel-and-price`): exact price-taking EVSP machinery on Swedish (Partille)
  bus data — CG with an SOC-by-time expanded exact pricer (certificates on a
  discretized route space), route re-realization under new tariffs,
  restricted-master MIP. Runs on the Unicorn cluster.
- **evspv2g_dp** (github.com/ndandnd/evspv2g_dp): code for Cho, Lodi,
  Scaglione, *Electric Vehicle Scheduling and Vehicle-to-Grid Integration in
  Microgrids* (arXiv:2508.06752, submitted to Optimization and Engineering):
  the benevolent-dictator problem in a microgrid — trucks + charging + V2G +
  stationary storage + solar + fossil generation co-optimized by column
  generation.

These are the two *endpoints* of the thesis spectrum (price-taker and
dictator). This repository (`egg`) develops everything in between. Rule: call
those solvers as oracles; do not copy their code here.

## 3. What the literature review established (status: breadth complete)

A four-round review was completed on 2026-08-14 (log:
`ref/SEARCH_LOG_20260814.md`):

1. **17 supplied papers fully audited** (paper-level notes in
   `ref/review_notes/`, PDFs in `ref/papers/`). Conclusion: generic
   price-load feedback is NOT novel — traffic-equilibrium loops, aggregate
   EV-battery bilevel bidding, strategic storage (MPEC/EPEC), minimum-uplift
   pricing for shiftable demand, and learned price impact are all published.
   The closest domain precedent is Lu et al. 2021 (price-making intercity
   transport company), which relaxes exactly the trip-covering structure
   that defines EVSP.
2. **EVSP-specific verification**: within EVSP proper, prices are always
   exogenous ToU tariffs; own-load *cost* nonlinearity exists (demand
   charges, peak objectives) but *market-mediated shared* price formation
   does not. Claim discipline: say "first EVSP embedded in shared price
   formation", never "first EVSP where cost depends on own load".
3. **Methodological scans**: the toolboxes for every missing piece exist and
   must be cited, not reinvented — integer programming games (equilibria
   over integer strategy sets via an "equilibrium separation oracle" — the
   role our EVSP solver plays), mixed-integer bilevel solvers, stabilized
   column generation, convex-hull/uplift pricing, EUPHEMIA exclusive-group
   block orders (a live European bid format matching "menu of complete
   schedules"), performative prediction, algorithms-with-predictions.
4. **The unifying frame (verified unclaimed as a whole)**: the naive
   chicken-and-egg iteration IS unstabilized Dantzig-Wolfe/Lagrangian
   decomposition of the dictator problem; ad-hoc "damping" in the EV
   literature IS stabilized column generation; converged master duals are
   convex-hull prices of the integrated economy; the MIP-LP gap is the
   minimum "internal uplift" (the price of indivisibility); the strategic
   fleet is formally a proximal/stabilized step ("strategic behavior is
   self-stabilizing"). Each link is published separately; the chain is not.

Catalog: 322 unique works in `ref/papers.csv` (17 audited / 270
abstract-level / 35 grey). All 77 identified "core-threat" works are scored
in `ref/NOVELTY_MATRIX.md`; none reaches Y-Y-C-a on
Duties x EndogenousPrice x Exactness — that triple is the thesis's identity.

## 4. Idea inventory and recommended arc

`ref/BRAINSTORM_20260814.md` holds 34 documented ideas (B1-B34) with prior
art and kill tests, organized into a recommended four-chapter arc:

- **I. Computation**: "damping is stabilization" theorem + stabilized
  two-sided master + internal-uplift atlas (B1-B3, B22).
- **II. Economics**: four-regime welfare ladder (can the naive price-taker be
  *worse than uncontrolled*?), discrete monopsony lemma (strategist = taker
  at marginal-outlay prices), cycling tied to the integrality gap (B8-B11).
- **III. Mechanisms**: decentralization ladder, convex-hull vs O'Neill
  two-part internal settlements, screening when the private type is a
  feasibility set ("information rent = integrality gap"), duties as
  exclusive-group bids (B15-B21).
- **IV. Technology**: locational duals in duty pricing, energy-deadheading
  ("bus network as virtual transmission"), V2G-degradation-aware labeling,
  reserve deliverability by timetable (B22-B30).
- Cross-cutting/later: switch-boundary learning (B31), multi-fleet integer
  programming game (B32), open benchmark instances (B33).

**Flagship first paper: recommended = Chapter I package (B1+B2+B3), NOT yet
ratified by the user** (`ref/RESEARCH_DIRECTIONS.md` Section 4).

## 5. Live warnings

- **Coordinate with Anna Scaglione** before drafting: she co-authored
  arXiv:2505.04532 (logistics fleet <-> LMP fixed-point equilibrium), the
  closest external work.
- **Timing pressure on Chapter I**: the dictator formulation is public
  (arXiv:2508.06752); Najafi-Fripp 2023 and Andrianesis et al. 2021 own the
  nearest framings; the Dolatabadi/Zeng group (arXiv:2510.14131) has the most
  similar machinery (branch-and-price energy logistics).
- **Evidence tiers are load-bearing**: 305 of 322 catalogued works are
  unverified abstracts. `ref/READING_QUEUE.md` ranks the ~50 gating reads.
- **Honest-labeling regime** (inherited from EVSP-DR): distinguish exact
  certificates / finite-pool optima / heuristics; several older claims were
  explicitly withdrawn — see `ref/context/` before repeating any result.

## 6. What happens next

1. User ratifies (or overrides) the flagship choice.
2. Acquire and audit the top of `ref/READING_QUEUE.md`; re-score matrix rows
   as audits land; run the flagship-specific related-work sweep.
3. Implementation Phase 0/1 per the historical handoff Section 8
   (`ref/context/HANDOFF_PRICE_MAKER_20260814.md`): freeze the
   oracle/logging contract; synthetic monotone price-response experiments
   (p_t = a_t + b_t L_t) on small Partille instances, comparing
   taker-iteration / damped iteration / strategic / dictator. Code goes in
   `src/`, outputs in `result/`, write-ups in `doc/`.
