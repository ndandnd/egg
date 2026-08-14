# Synthesis: microgrid, benevolent dictator, and V2G scan

Date: 2026-08-14

Status: synthesis of four parallel deep-research reports preserved verbatim in
`agents/` (microgrid price formation; dictator/decomposition; V2G and mobile
energy; economic theory). All underlying evidence is abstract-level web-search
material; the same verification rules as `EXTERNAL_DEEP_DIVE_20260814.md`
apply. Read the four agent reports for per-paper detail, DOIs, and full idea
lists; this file records only the strategic conclusions.

## 0. The reframing this scan produces

The team's two existing artifacts are the two *endpoints* of the thesis:

- **EVSP-DR** (Swedish bus data, exact CG/expanded pricer) = the
  **price-taker** regime: exogenous prices, exact schedules.
- **Cho, Lodi, Scaglione (arXiv:2508.06752, submitted to Optimization and
  Engineering; code `ndandnd/evspv2g_dp`)** = the **benevolent dictator**
  regime: one optimization co-scheduling truck duties + charging + V2G +
  stationary storage + solar + fossil generation in a microgrid, by column
  generation (LP master with energy balance and generation cost; DP pricing;
  restricted master MIP).

Everything in between — how prices form, what they can and cannot coordinate,
what strategic behavior does, and what mechanisms repair — is the open thesis
territory. The microgrid is not a side case: it is the setting where the fleet
is the *dominant* load, price impact is first-order, the supply stack is a
step function (free solar / storage opportunity cost / diesel marginal cost /
scarcity), and everything that is marginal at national scale becomes extreme.

## 1. The unifying mathematical chain (verified unclaimed as a whole)

Each link exists in the literature; the chain does not. Details and citations
in `agents/AGENT2_DICTATOR_DECOMPOSITION_20260814.md`.

1. The dictator problem min over schedules S and generation g of
   [c_op(S) + C_gen(g)] subject to energy balance is a textbook Dantzig-Wolfe
   structure: master carries generation cost and balance rows; fleet duties
   are columns; **master duals are internal electricity prices**; the pricing
   subproblem is the EVSP at those prices (Dantzig-Wolfe 1960; the team's own
   manuscript implements exactly this).
2. The naive "chicken-and-egg" loop (post price -> solve EVSP -> recompute
   marginal-cost price) **is** the unstabilized version of this decomposition:
   an Uzawa/Kelley cutting-plane iteration on the dictator's Lagrangian dual.
   Its cycling is theorem-grade (Kelley instability: Briant et al. 2008;
   tatonnement cycles: Scarf 1960; EV-specific oscillation: Ma-Callaway-
   Hiskens 2013, Gan-Topcu-Low 2013).
3. **Damping is stabilization**: boxstep (Marsten-Hogan-Blankenship 1975),
   stabilized CG (du Merle et al. 1999), generalized bundle theory (Frangioni
   2002), auto-tuned smoothing (Pessoa et al. 2018) — principled damped price
   updates with finite convergence and LP certificates. The ad-hoc damping in
   the EV-charging literature is literally Wentges-style dual smoothing,
   unacknowledged.
4. At convergence, master duals are **convex-hull prices of the integrated
   fleet+generation economy** (Gribik-Hogan-Pope identity; Andrianesis et al.
   2021 compute CH prices by DW on the generation side), and the restricted-
   master-MIP-vs-LP gap is the **minimum internal uplift** — the exact amount
   by which any linear internal price fails to decentralize the integer fleet
   (Baumol-Fabian 1964; Scarf 1994; Gomory-Baumol 1960).
5. O'Neill et al. (2005) two-part prices (linear price + per-duty commitment
   payment) repair the support exactly — the internal-transfer-price fix.
   Whether such transfers stay incentive-compatible when the fleet privately
   knows its feasibility set is an open mechanism-design question.
6. **The strategic fleet is self-stabilizing** (conjecture, agent 2 idea 5 +
   agent 4 idea 2): with affine price impact, bill minimization adds a
   quadratic aggregate-load term formally identical to the damping penalties
   of Ma et al. and to a proximal term on the dictator's dual. Regime M = the
   taker at *marginal-outlay* prices = a stabilized decomposition of a
   perturbed dictator objective. This unifies the three regimes
   algorithmically and is a candidate headline theorem.

## 2. Novelty verdicts from this round (adds to prior scans)

**Confirmed open (nobody does it):**
- Exact set-partitioning EVSP as the demand-side oracle in ANY price-formation
  loop (microgrid or wholesale).
- Microgrid-internal price formation with a fleet-dominant, timetabled load
  (every depot/hub/islanded study takes prices or centrally dispatches).
- The centralization spectrum quantified on one physical system:
  dictator / posted internal prices / strategic fleet / auction.
- Four-point welfare ordering (uncontrolled / naive taker / strategic /
  planner) for *combinatorial* flexibility — including the possibly
  non-monotone result that the naive taker can be worse than the strategist.
- Monopsony theory for indivisible demand (lumpy withholding, no smooth
  markdown).
- Cycling/convergence theory tying the taker iteration's fixed points to the
  integrality gap of the set-partitioning LP.
- Performative stability with discontinuous (combinatorial) responders.
- Principal-agent where the private type is a scheduling feasibility set
  ("information rent = integrality gap" candidate theorem).
- V2G-cycle degradation inside exact duty pricing; locational (node-indexed)
  duals inside duty pricing; timetabled service + spatial energy transport
  ("energy deadheading"); reserve deliverability certified against the
  timetable; duty-level recourse under PV uncertainty.

**Serious threats found (cite and differentiate; verify full texts):**
1. **Yao, Liu, Scaglione, Bekhor, Zhang 2025 (arXiv:2505.04532)** — logistics
   fleet <-> LMP fixed-point equilibrium with existence proof. Shares an
   author with the team's manuscript: coordinate positioning internally
   before drafting anything.
2. **Anunrojwong, Balseiro, Besbes, Xu (SSRN 4877753)** + **Jiang, Nie,
   Skoulakis (arXiv:2602.19660)** — three-regime welfare comparison and tight
   PoA bounds [9/8, 4/3] for a *convex* battery; unbounded PoA for convex
   price functions. The welfare-ladder chapter must position against these.
3. **Najafi & Fripp 2023 (DOI 10.1016/j.egyai.2023.100277)** — DW master
   computes price signals for convex flexible devices. Owns the generic
   "DW = price coordination" claim; stops exactly where the thesis starts.
4. **Dolatabadi, Dong, Bhuiyan, Zeng, O'Neill, Severson (arXiv:2510.14131)** —
   exact branch-and-price for electric school buses ferrying energy in
   disaster recovery. Most method-similar external group; watch closely.
5. **Wu, Guo, Polak, Strbac 2019** (already audited in full) — bus operations
   coupled to DLMP clearing; tactical, not exact EVSP.
6. **Manzolli et al. 2024 (Energy, 10.1016/j.energy.2024.132497)** — bilevel
   aggregator <-> bus-fleet price setting with fixed trips; the Coimbra line
   iterates fast.
7. **Yetkin, Augustino, Lamadrid, Snyder 2024 (Opt. & Eng.,
   10.1007/s11081-023-09878-w)** — social-planner grid + transit co-optimization
   (mobile storage, no set-partitioning, no UC, no decomposition theory).
   Note: same journal the team's manuscript is submitted to.
8. **Cornélusse et al. 2019 (10.1016/j.apenergy.2019.03.109)** — community
   microgrid with internal marginal-price market + benevolent redistribution
   (bilevel), the no-vehicles precedent for the dictator<->market spectrum.

**Timing pressure:** the team's own arXiv:2508.06752 makes the dictator
formulation public. The decomposition-as-price-formation framing paper should
be claimed quickly (agent 2, threat 8).

## 3. What the microgrid setting changes, precisely

- **Price impact is structural, not marginal**: at 50-90% of load, prices are
  mostly self-generated; the "market" degenerates and the right comparison is
  dictator vs internal-transfer mechanisms (agent 4, gap 8).
- **Step supply stacks break the nice theory**: Jiang et al. show PoA bounds
  blow up for non-linear price functions; merit-order stacks are the
  non-linear case. Zero-marginal-cost solar makes marginal prices degenerate
  (10.1109/tsg.2021.3122879: marginal pricing provably fails to coordinate
  storage in 100%-renewable microgrids).
- **Cycling is generic**: an atomic fleet has locally infinite price
  elasticity at kinks of V(p); by the Roozbehani-Dahleh-Mitter instability
  criterion (consumer elasticity > producer elasticity) the naive loop sits
  in the unstable regime *by construction*.
- **Empirics support the premise**: TOU "shadow peaks" from synchronized EV
  response (Bailey et al., AER: Insights, 10.1257/aeri.20240476); avalanche
  effects (10.1016/j.esr.2020.100608); the 400 MW electrolyzer moving Nord
  Pool prices by ~35 EUR/MWh.

## 4. V2G + solar: what it adds beyond the manuscript

From `agents/AGENT3_V2G_MOBILE_ENERGY_20260814.md`:

- The manuscript's method claim (CG-based EVSP + V2G + microgrid dispatch)
  appears safe as of 2026-08; every competing V2G-e-bus scheduler is
  MILP+metaheuristic or fixes trips.
- Degradation is the make-or-break economics term (V2G profitable below
  ~100 EUR/kWh replacement cost; reserves beat arbitrage because they cycle
  less). Degradation-aware labeling exists for charging only (Zhang 2021;
  Klein-Schiffer 2023) — V2G-cycle wear inside pricing is open.
- Mobile-energy economics is quantified and self-eroding (HBS/PJM: each
  storage entrant cannibalizes spreads; He et al. Joule 2021): only a
  price-maker model prices V2G at fleet scale correctly — a strong motivation
  for the whole thesis.
- "Energy deadheading" (insert a non-service leg to move stored energy to a
  higher-value node) is confirmed open for timetabled fleets; Crozier
  (arXiv:2311.11464, freight) and Dolatabadi (school buses) are the near
  misses. Frame: *the bus network as a virtual transmission line*.

## 5. Follow-ups

1. Coordinate with Scaglione on arXiv:2505.04532 positioning before any
   drafting.
2. Full-text reads gating claims: Najafi-Fripp 2023; Andrianesis et al. 2021;
   Anunrojwong et al.; Jiang et al. arXiv:2602.19660; Cornélusse et al. 2019;
   Yetkin et al. 2024; Dolatabadi arXiv:2510.14131; Manzolli 2024;
   Briant et al. 2008; du Merle et al. 1999. (Added to `../READING_QUEUE.md`.)
3. The brainstorm catalog and recommended thesis arc are maintained in
   `../BRAINSTORM_20260814.md`.
