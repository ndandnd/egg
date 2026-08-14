# Research directions (live document)

Last updated: 2026-08-14

This is the live hypotheses-and-decisions file requested by
`../HANDOFF_PRICE_MAKER_20260814.md` Section 9. Evidence base: the 17-paper
full-text audit (`review_notes/BIDDING_GAMES_20260814.md`,
`review_notes/MARKET_MECHANISMS_AND_BUS_DR_20260814.md`,
`review_notes/ROUTE_AND_RESPONSE_LEARNING_20260814.md`) plus the
abstract-level external scan
(`review_notes/EXTERNAL_DEEP_DIVE_20260814.md`). Claims sourced only from the
external scan are marked "(scan)" and carry its verification debts.

## 1. Umbrella thesis (unchanged, reaffirmed)

> **Exact markets and incentives for nonconvex mobile flexibility.**
> How should a power market clear and compensate mandatory, indivisible
> electric-fleet schedules so that operations remain exact, selected fleets
> have no profitable feasible rescheduling deviation, and prices/payments are
> economically defensible under endogenous prices and market power?

The external scan did not find prior work occupying this question; it found
substantial *methodological* literatures that make each chapter buildable
(and that must be cited rather than reinvented). The mathematical object
remains the set of complete, feasible, trip-covering fleet schedules; the
common computational asset remains the EVSP branch/column-generation oracle
used as: best-response solver, deviation/separation oracle, counterfactual
solver, bid-menu generator, and certificate producer.

**The single most reusable formal observation:** Zoltowska-style no-deviation
uplift constraints, Zero-Regrets-style equilibrium inequalities (scan), VCG
counterfactual solves, and convex-hull-pricing lost-opportunity-cost terms
are all *the same computational pattern* — separation over the fleet's
schedule set by a best-response oracle. One oracle, four economic products.
That unification is a credible thesis-level methodological identity.

**Claim discipline (added 2026-08-14, see
`review_notes/EVSP_PRICE_FEEDBACK_NOVELTY_20260814.md`):** within EVSP,
own-load-dependent *costs* already exist (demand charges, peak-load
objectives, e.g., Wu et al. 2021 TRB branch-and-price MDEVSP). What is
unoccupied is *market-mediated* price formation — a shared price moved by the
fleet's load. Never phrase the novelty as "first EVSP where cost depends on
own load"; phrase it as "first EVSP embedded in shared price formation," with
the strategic/equilibrium/welfare structure that entails. A demand charge is
a private nonlinearity; a market price is a shared externality.

## 2. Directions, updated

### Direction A — Certified atomic price-maker fleet market

- Statement: embed exact trip-covering schedules in market clearing with
  endogenous prices; surrogates propose, the exact oracle verifies and bounds.
- Strongest prior art: Lu et al. (2021) (closest domain precedent, stylized
  service); Gonzalez Vaya and Andersson (2015) (aggregate bilevel MILP);
  Xie and Xu (2025) (learned price impact, trust region). Methodologically
  (scan): mixed-integer bilevel branch-and-cut (MibS lineage), decision-diagram
  and Dantzig-Wolfe single-level reformulations (2025).
- Defensible gap: bilevel market clearing where the follower is an EVSP whose
  variables are *generated*, not enumerated; honest exactness tiers on the
  follower response; scaling beyond compact-formulation MIBLP benchmarks.
- Risk: the 2025 DW-bilevel preprint may already delay follower-vertex
  generation. **Priority read before any claim is drafted.**
- Status: leading candidate for the methods core, jointly with E.

### Direction B — Fleet duties as a bid language (EUPHEMIA exclusive groups)

- Statement: offer complete feasible duty schedules as mutually exclusive
  block bids; study menu generation, welfare loss vs menu size, payments,
  and strategic menu choice.
- Strongest prior art (scan): EUPHEMIA exclusive groups are a live product;
  Karasavvidis, Papadaskalopoulos, Strbac (2024, IEEE TEMPR) do optimal
  exclusive-group bidding for stylized price-taking flexible demand; a 2026
  preprint (arXiv:2606.24183) compares hourly vs exclusive-group bids under
  imperfect information; Hubner and Hug (2026) study package-bid welfare
  losses; an Energies 2021 paper bids aggregate e-bus energy envelopes into
  the day-ahead auction.
- Defensible gap: menu *generation* from an exact trip-covering model
  (column generation as bid-menu generator, with a certified menu-optimality
  gap); mandatory-service fallback/exposure when all blocks are rejected;
  strategic (price-making) menu design; welfare comparison of bid languages
  for atomic fleet flexibility.
- Why elevated: institutional realism (the market our Swedish data trades in
  supports these bids today), low model risk, direct reuse of the column
  machinery, and a naturally bounded first paper (price-taking menu design)
  inside a thesis-scale arc (strategic menus, mechanism comparison).
- Status: promoted by this scan to co-leading candidate; best candidate for
  the *first* self-contained paper after Phase 0/1.

### Direction C — Counterfactual-free flexibility products

- Statement: sell feasible capacity limits / envelopes / schedule rights
  derived from the exact fleet model instead of baseline payments.
- Strongest prior art: Afentoulis and Vagropoulos (2025) (baseline gaming
  with real EV data); Ziras et al. (2021) (capacity limitations over
  baselines); (scan) 2023-2025 capacity-limitation-service and capacity
  subscription literature.
- Defensible gap: *deliverability* — no CLS work verifies that a mandatory
  trip-covering schedule exists under a sold cap; computing/pricing the
  feasible cap set is an EVSP-oracle problem.
- Status: alive; natural later chapter once the oracle contract is frozen;
  pairs well with B (a capacity product is a coarser bid language).

### Direction D — Active learning at schedule-switch boundaries

- Statement: the price-to-schedule map is piecewise constant with jumps;
  learn where it switches, not average response; exact solver labels and
  certifies.
- Strongest prior art: Chen et al. (2026) (GNN price-response surrogate,
  smooth aggregate); Luan et al. (2026) and Liu et al. (2024) (congestion
  pricing surrogates/BO); (scan) multiparametric MILP theory (critical
  regions), GVF learning with one-sided guarantees (NeurIPS 2024),
  decision-focused MILP surrogates (2025), and a crowded ML-for-CG
  acceleration field.
- Defensible gap: region/boundary learning for set-partitioning EVSP value
  functions over tariff space; one-sided (certified) learned bounds; active
  sampling driven by boundary uncertainty; all with exact fallback.
- New theory frames (scan): performative prediction (the loop is literally
  decision-dependent distribution shift, but all existing theory assumes
  smoothness the atomic response violates) and algorithms-with-predictions
  (consistency/robustness statements for the two-fidelity oracle, an open
  problem explicitly posed by the 2024 Dagstuhl report).
- Status: alive as the learning chapter; its scope should be decided by
  Phase-2 evidence (how often duty switches actually matter economically).

### Direction E — Competition and mitigation (now: the EVSP-IPG)

- Statement: multiple strategic fleets (or fleet vs generator) interacting
  through prices, each with a combinatorial strategy set.
- Strongest prior art: Wu et al. (2016) (Bayesian aggregate-envelope game);
  Zou et al. (2016) (continuous EPEC); (scan) the Integer Programming Games
  literature — Sample Generation Method, Zero Regrets, Cut-and-Play, NASPs —
  plus a column-and-constraint-generation Nash computation for pool markets
  on the supply side (Fanzeres/Street/Pozo, citation to verify).
- Defensible gap: no IPG application accesses strategy sets through column
  generation; price-mediated payoff coupling gives exploitable structure;
  certified equilibrium gaps under capped oracles extend ZR-style bounds to
  the honest-labeling regime we already enforce.
- Status: strongly upgraded — E is no longer "vague future multi-agent
  work" but a concrete formal program with named prior algorithms to extend
  and benchmark against. Candidate methods core jointly with A.

## 3. Recommended chapter architecture (updated)

1. **Atomic response and equilibrium** (A+E): characterize the discontinuous
   price-to-duty response (mp-MILP regions vocabulary); single-fleet
   strategic response via MIBLP-with-column-generation; multi-fleet EVSP-IPG
   with equilibrium separation by branch-and-price; certified equilibrium
   gaps.
2. **Learning with correction** (D): switch-boundary/region learning,
   one-sided value-function bounds, active sampling; performative-prediction
   and algorithms-with-predictions framing with provable
   consistency/robustness of the two-fidelity pipeline.
3. **Bid language and clearing** (B): exclusive-group menu generation by
   column generation; welfare loss vs menu size; exposure/fallback design for
   mandatory service; comparison of bid languages (EG vs shifting bids vs
   multi-part).
4. **Prices and payments** (C + audit Layer 4): EVSP-separated minimum-uplift
   and convex-hull prices via duty columns; service-preserving VCG
   counterfactuals; deliverable capacity products as baseline-free
   settlement.

The four chapters share one oracle and one logging/exactness contract
(handoff Section 8.1), which is what makes this a thesis rather than four
papers.

## 4. Decision points now open

1. **Flagship first paper.** Candidates: (i) Direction B price-taking
   exclusive-group menu design on Partille data (bounded, institutional,
   novel); (ii) Phase-1 price-feedback study (Claude's original Track-A
   fallback: oscillation/damping with real duties — publishable but closer to
   known territory, per the audit's warnings about Wei/Wang/Song). This
   choice does not block Phase 0/1, which serve both.
2. **Read-first list** before committing claims: DW-bilevel preprint (2025),
   Karasavvidis 2024, Zero Regrets, Cut-and-Play, IPG tutorial — see
   `READING_QUEUE.md`.
3. **Unchanged decision gates** from handoff Section 8.7 remain in force,
   especially: if Phase-2 shows duty switches are rare and charging-only
   response explains nearly everything, lean toward B/C (market design) and
   away from heavy route-learning claims.

## 5. Falsification tests added by the external scan

- If the DW-bilevel reformulation already handles delayed follower-column
  generation at scale, Direction A's methods novelty narrows to the market
  application and exactness hierarchy; re-scope accordingly.
- If EUPHEMIA bid-count/format limits (current NEMO rules) cap exclusive
  groups at a size that makes menu design trivial, Direction B's menu-design
  question weakens; check the current public description early.
- If ZR/Cut-and-Play-style oracles are practically unusable with
  branch-and-price best responses (oracle too slow even capped), Direction E
  falls back to sequential best-response with certified unilateral-deviation
  gaps only.
