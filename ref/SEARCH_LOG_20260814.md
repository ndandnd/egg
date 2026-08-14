# Search log and breadth-phase closure

Date: 2026-08-14

This log makes the breadth review auditable: what was searched, when, with
which tools, under which inclusion rules, and why searching stopped.

## Tooling and scope

- Tool: web search (search-engine snippets + publisher/arXiv pages) via
  Cursor cloud agents, all on 2026-08-14 (UTC).
- Languages: English only. Chinese-language transit journals are known to be
  undersampled (flagged as an open coverage gap).
- No systematic forward/backward citation chasing was performed (open gap;
  recommended around the ~10 closest threats once the flagship is chosen).
- Evidence rule: everything found by search is `abstract-level` until a
  full-text audit; identifiers recorded verbatim, never inferred.

## Round 1 — external methodological scan (main agent, 15 queries)

Written up in `review_notes/EXTERNAL_DEEP_DIVE_20260814.md`. Queries:

1. integer programming games Nash equilibria computation Carvalho Lodi
   Dragotto survey cutting plane 2023 2024 2025
2. bilevel optimization mixed-integer lower level follower value function
   branch-and-cut survey Kleinert Labbe Ljubic Schmidt recent advances 2024
   2025
3. "When Nash Meets Stackelberg" Carvalho Dragotto Feijoo Lodi
   Sankaranarayanan NASP energy market application
4. convex hull pricing demand response flexible load nonconvex electricity
   market pricing 2024 2025 2026 uplift
5. electric bus fleet scheduling day-ahead electricity market bidding vehicle
   scheduling problem endogenous prices 2024 2025 2026
6. EUPHEMIA exclusive block orders demand-side flexibility bidding Nord Pool
   complex orders literature
7. performative prediction decision-dependent distributions state of the art
   2024 2025 survey stochastic optimization
8. Karasavvidis exclusive group bids flexible demand day-ahead market optimal
   offering block orders
9. multiparametric mixed-integer programming value function objective
   coefficients parametric MILP regions learning 2024 2025
10. machine learning column generation branch-and-price acceleration 2025
    2026 vehicle scheduling crew pricing subproblem
11. "electric bus" OR "transit fleet" market power price-maker V2G strategic
    bidding wholesale market 2025 2026 paper
12. algorithms with predictions learning-augmented optimization warm start
    guarantees consistency robustness combinatorial optimization survey 2024
    2025
13. column generation computing Nash equilibrium game Dantzig-Wolfe
    "equilibrium" branch-and-price strategy generation electricity market
14. capacity subscription flexibility product baseline-free demand response
    market design 2024 2025 local flexibility market
15. parametric column generation reuse columns across scenarios tariffs
    objective coefficients warm start "column pool" electric vehicle
    scheduling

## Round 2 — EVSP-specific novelty verification (main agent, 4 queries)

Written up in `review_notes/EVSP_PRICE_FEEDBACK_NOVELTY_20260814.md`.
Queries:

16. "electric vehicle scheduling problem" OR "electric bus scheduling"
    endogenous electricity price price feedback load-dependent price
    price-maker
17. electric bus depot charging scheduling demand charge peak power price
    time-of-use MILP column generation 2023 2024 2025
18. electric bus scheduling review Perumal Lusby Larsen OR Zhou 2024 charging
    "electricity price" gap endogenous grid interaction future research
19. bilevel electric bus scheduling charging "locational marginal price" OR
    "market clearing" trips timetable duty grid operator coupled 2023 2024
    2025 2026

## Round 3 — microgrid / dictator / V2G round (4 parallel research agents)

Full reports in `review_notes/agents/`. Each agent ran many searches; their
complete query lists were not preserved (logged limitation). Their briefs
(topic scopes) and the probe queries they explicitly recorded:

- Agent 1 (microgrid price formation): transactive/local energy markets,
  depot/hub microgrids, DLMP at small scale, islanded systems with EV
  fleets, strategic behavior in thin local markets; explicit novelty probes
  on "transactive market + timetabled vehicle scheduling", "EV fleet
  strategic bidding in local energy market", "microgrid marginal price
  feedback to fleet schedule iteration".
- Agent 2 (dictator/decomposition): price-based decomposition classics and
  stabilization, LR for unit commitment, DW coordination of flexible demand,
  integrated transport-energy planning, pricing under indivisibilities;
  recorded probes: "price iteration as Dantzig-Wolfe EV", "tatonnement
  Dantzig-Wolfe equivalence EV", "chicken-and-egg electricity price fleet
  schedule iteration", "iterative price update oscillation EV decomposition".
- Agent 3 (V2G/mobile energy): V2G e-bus scheduling methods 2023-2026,
  degradation modeling, solar/uncertainty two-stage designs, mobile energy
  storage and resilience, ancillary services by scheduled fleets; explicit
  novelty probes on endogenous prices in V2G-EVSP, certified CG for
  V2G-EVSP, locational duals in duty pricing, timetabled service + spatial
  energy transport.
- Agent 4 (economic theory): welfare comparisons for large flexible agents,
  monopsony, potential games/cycling, major-minor games, screening with
  private combinatorial types, emissions-vs-cost objectives, performative
  prediction in energy.

## Round 4 — canonicalization (no new searches)

Extraction of all named works from the round 1-3 notes into `papers.csv`
(two extraction agents + merge/validation tooling in `tools/`).

## Inclusion and classification rules

- Included: any work named with a title or a verifiable identifier in the
  notes. Excluded: passing mentions with neither.
- Tiers: `audited-full-text` (17 supplied papers, pre-existing audit),
  `abstract-level`, `institutional/grey`.
- Relevance: `core-threat` / `method-anchor` / `domain-context` /
  `deprioritized`; every core-threat is scored in `NOVELTY_MATRIX.md`.

## Saturation evidence and stopping rule

- Later queries increasingly re-hit works already catalogued (e.g., the
  team's own arXiv:2508.06752 began surfacing in agent searches; Wu et al.
  2019, Lu et al. 2021, Gonzalez Vaya 2015, Ma/Gan damping papers, and the
  DLMP loop literature were each rediscovered independently by 2+ agents).
- The four Round-3 agents, scoped to disjoint fronts, converged on the same
  short list of external threats (Yao 2025; Najafi-Fripp 2023; Andrianesis
  2021/22; Dolatabadi 2025; Manzolli 2024; Cornelusse 2019; Yetkin 2024;
  Anunrojwong/Jiang).
- Stopping rule applied: stop broad scanning when (a) new queries mostly
  return already-catalogued works, and (b) independent scans converge on the
  same threat set. Both held on 2026-08-14.

## Closure statement

> **Breadth phase closed 2026-08-14.** Milestone: *Initial literature review
> v1 — breadth complete; verification and flagship-specific review pending.*
> Remaining lit-review work is (1) full-text verification per
> `READING_QUEUE.md`, (2) a flagship-specific related-work sweep once the
> first paper is selected, (3) forward-citation chasing around the closest
> threats, (4) maintenance (alerts; matrix rule in `NOVELTY_MATRIX.md`).
