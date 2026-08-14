# Reading queue

Last updated: 2026-08-14

Statuses: `reviewed-full-text` (paper-level notes exist), `needs-pdf`
(request/acquire), `abstract-only` (found by external scan; full text needed
before citing details), `deprioritized`.

## Reviewed full text (17 supplied papers)

See `../HANDOFF_PRICE_MAKER_20260814.md` Section 4 for the canonical table
(DOIs, aliases) and `review_notes/` for the paper-level notes. Not repeated
here.

## Needs PDF — carried over from handoff Section 10 (user request list)

1. Liu, Yin (2025), *End-to-End Learning of User Equilibrium*, DOI
   `10.1287/trsc.2023.0489`.
2. You et al. (2026), *Two-Stage Learning to Branch in Branch-Price-and-Cut
   Algorithms*, DOI `10.1287/opre.2023.0615`.
3. De Vivero-Serrano, Bruninx, Delarue (2019), *Implications of bid
   structures on the offering strategies of merchant energy storage systems*,
   DOI `10.1016/j.apenergy.2019.113375`.

## Abstract-only — priority reads from the external scan (2026-08-14)

Ordered by how directly they gate a live decision (see
`RESEARCH_DIRECTIONS.md` Section 4).

1. *A Dantzig-Wolfe Single-Level Reformulation for Mixed-Integer Linear
   Bilevel Optimization* (2025, Optimization Online preprint). Gates
   Direction A's novelty scope. Open access.
2. Karasavvidis, Papadaskalopoulos, Strbac (2024), *Optimal Bidding of
   Flexible Demand in Electricity Markets With Block Orders*, IEEE TEMPR,
   DOI `10.1109/TEMPR.2024.3414988`. Gates Direction B.
3. Dragotto, Scatamacchia (2023), *The Zero Regrets Algorithm*, INFORMS J.
   Computing, DOI `10.1287/ijoc.2022.0282`. Core method for Direction E.
4. Carvalho, Dragotto, Lodi, Sankaranarayanan (2023), *Integer Programming
   Games: A Gentle Computational Overview*, INFORMS TutORials,
   arXiv:2306.02817 (open access). Orientation read for Direction E.
5. Carvalho, Dragotto, Lodi, Sankaranarayanan (2025), *The Cut-and-Play
   Algorithm*, Operations Research, DOI `10.1287/opre.2023.0327`.
6. Carvalho, Dragotto, Feijoo, Lodi, Sankaranarayanan (2024), *When Nash
   Meets Stackelberg*, Management Science 70(10), DOI
   `10.1287/mnsc.2022.03418` (arXiv:1910.06452 open access).
7. Kleinert, Labbé, Ljubić, Schmidt (2021), *A survey on mixed-integer
   programming techniques in bilevel optimization*, EURO J. Comput. Optim.,
   DOI `10.1016/j.ejco.2021.100007` (open access).
8. *Generating EUPHEMIA-compatible bids for flexible demand under imperfect
   information* (2026), arXiv:2606.24183 (open access). Direction B.
9. *Learning Generalized Linear Programming Value Functions* (NeurIPS 2024,
   open access proceedings). Direction D certified surrogates.
10. *Dissecting Performative Prediction: A Comprehensive Survey*, DOI
    `10.1145/3816429`. Direction D framing.
11. *Stochastic Optimization Schemes for Performative Prediction with
    Nonconvex Loss* (NeurIPS 2024, open access). Direction D framing.
12. Fischetti, Ljubić, Monaci, Sinnl (2017), *A new general-purpose algorithm
    for mixed-integer bilevel linear programs*, Operations Research 65(6).
13. Tahernejad, Ralphs, DeNegre (2020), MibS branch-and-cut, Math.
    Programming Computation (open access).
14. *A single-level reformulation of binary bilevel programs using decision
    diagrams* (2025), Mathematical Programming, DOI
    `10.1007/s10107-025-02294-1`.
15. Karasavvidis, Papadaskalopoulos, Strbac (2021), *Optimal Offering of a
    Power Producer in Electricity Markets With Profile and Linked Block
    Orders*, IEEE TPWRS, DOI `10.1109/TPWRS.2021.3129084`.
16. *Convex Hull Pricing for Unit Commitment: Survey* (2024), Energies
    17(19):4851, DOI `10.3390/en17194851` (open access).
17. Fanzeres, Street, Pozo, column-and-constraint generation for Nash
    equilibria in pool-based electricity markets — **exact citation to
    verify** before any use.
18. *Optimal Charging Schedule Planning for Electric Buses Using Aggregated
    Day-Ahead Auction Bids* (2021), Energies 14(16):4727 (open access).
    Direction B prior art.
19. *Improving Directions in Mixed Integer Bilevel Linear Optimization*
    (2025), arXiv:2511.03566 (open access).
20. Oberdieck, Wittmann-Hohlbein, Pistikopoulos (2014), mp-MILP
    branch-and-bound, J. Global Optimization 59(2).

## Abstract-only — EVSP-side price-aware baselines (added 2026-08-14, see review_notes/EVSP_PRICE_FEEDBACK_NOVELTY_20260814.md)

- Wu, Lin, Liu, Jin (2021), *The multi-depot electric vehicle scheduling
  problem with power grid characteristics*, Transp. Res. Part B 155, DOI
  `10.1016/j.trb.2021.11.007`. Branch-and-price MDEVSP, TOU + peak-load
  objective. Open-access preprint exists (White Rose eprints).
- Zhang et al. (2024), *On the role of time-of-use electricity price in
  charge scheduling for electric bus fleets*, Computer-Aided Civil and
  Infrastructure Engineering, DOI `10.1111/mice.13134`. Branch-and-price,
  TOU + partial charging + limited chargers.

## Abstract-only — priority reads from the microgrid/dictator/V2G round (2026-08-14)

Gating the Chapter I-IV claims in `BRAINSTORM_20260814.md`; per-paper context
in `review_notes/agents/`.

1. Yao, Liu, Scaglione, Bekhor, Zhang (2025), *Integrated equilibrium model
   for electrified logistics and power systems*, arXiv:2505.04532.
   **Coordinate internally before drafting.**
2. Anunrojwong, Balseiro, Besbes, Xu, *Battery Operations in Electricity
   Markets: Strategic Behavior and Distortions*, SSRN 4877753. Gates B8.
3. Jiang, Nie, Skoulakis (2026), *The Welfare Gap of Strategic Storage*,
   arXiv:2602.19660. Gates B8.
4. Najafi, Fripp (2023), *Market-based coordination of price-responsive
   demand using Dantzig-Wolfe decomposition*, Energy & AI, DOI
   `10.1016/j.egyai.2023.100277`. Gates B1/B2 differentiation.
5. Andrianesis, Bertsimas, Caramanis, Hogan (2021), *Computation of Convex
   Hull Prices... Dantzig-Wolfe*, IEEE TPWRS, DOI
   `10.1109/tpwrs.2021.3122000` (already queued above; now gates B3).
6. Briant, Lemarechal, Meurdesoif, Michel, Perrot, Vanderbeck (2008),
   *Comparison of Bundle and Classical Column Generation*, Math. Programming.
7. du Merle, Villeneuve, Desrosiers, Hansen (1999), *Stabilized Column
   Generation*, Discrete Mathematics, DOI `10.1016/s0012-365x(98)00213-1`.
8. Frangioni (2002), *Generalized Bundle Methods*, SIAM J. Optimization, DOI
   `10.1137/s1052623498342186`; and Pessoa, Sadykov, Uchoa, Vanderbeck
   (2018), IJOC, DOI `10.1287/ijoc.2017.0784`.
9. Gribik, Hogan, Pope (2007), *Market-Clearing Electricity Prices and Energy
   Uplift* (working paper); O'Neill, Sotkiewicz, Hobbs, Rothkopf, Stewart
   (2005), EJOR, DOI `10.1016/j.ejor.2003.12.011`; Baumol, Fabian (1964),
   Management Science, DOI `10.1287/mnsc.11.1.1`; Scarf (1994), JEP, DOI
   `10.1257/jep.8.4.111`. The pricing-under-indivisibility spine.
10. Ma, Callaway, Hiskens (2013), IEEE TCST, DOI `10.1109/tcst.2011.2174059`;
    Gan, Topcu, Low (2013), IEEE TPWRS, DOI `10.1109/TPWRS.2012.2210288`;
    Roozbehani, Dahleh, Mitter (2012), IEEE TPWRS, DOI
    `10.1109/tpwrs.2012.2195037`. The oscillation/damping canon.
11. Cornélusse, Savelli, Paoletti, Giannitrapani, Vicino (2019), *A community
    microgrid architecture with an internal local market*, Applied Energy,
    DOI `10.1016/j.apenergy.2019.03.109`. The no-vehicles dictator<->market
    precedent.
12. Yetkin, Augustino, Lamadrid, Snyder (2024), *Co-optimizing the smart grid
    and electric public transit bus system*, Optimization and Engineering,
    DOI `10.1007/s11081-023-09878-w`. Main published dictator-with-fleet
    competitor; same journal as the team's submission.
13. Dolatabadi, Dong, Bhuiyan, Zeng, O'Neill, Severson (2025), *Leveraging
    Electric School Buses for Disaster Recovery... Branch-and-Price*,
    arXiv:2510.14131. Most method-similar external group.
14. Manzolli et al. (2024), *Aggregator-supported strategy for electric bus
    fleet charging*, Energy, DOI `10.1016/j.energy.2024.132497`.
15. Wu, Guo, Polak, Strbac (2019) — already audited full-text; re-read
    against the microgrid framing.
16. Bailey, Brown, Myers, Shaffer, Wolak (2025), *Unintended Consequences of
    Time-of-Use Pricing*, AER: Insights, DOI `10.1257/aeri.20240476`; and
    Kuehnbach, Stute, Klingler (2021), avalanche effects, DOI
    `10.1016/j.esr.2020.100608`. Empirical self-defeating-taker anchors.
17. Klein, Schiffer (2023), *EV Charge Scheduling with Flexible Service
    Operations*, Transportation Science, DOI `10.1287/trsc.2022.0272`; and
    Zhang, Wang, Qu (2021), TRE, DOI `10.1016/j.tre.2021.102445`.
    Degradation-aware labeling baselines for B25.
18. Hardt, Jagadeesan, Mendler-Duenner (2022), *Performative Power*, NeurIPS.
    Gates B11.
19. Sioshansi (2010), Energy Journal, DOI
    `10.5547/issn0195-6574-ej-vol31-no2-7`; Kazempour, Conejo, Ruiz (2015),
    IEEE TPWRS, DOI `10.1109/tpwrs.2014.2332540`. Storage-welfare and
    monopsony baselines for B8/B9.
20. He, Michalek, Kar, Chen, Zhang, Whitacre (2021), *Utility-Scale Portable
    Energy Storage Systems*, Joule, DOI `10.1016/j.joule.2020.12.005`; and
    Crozier et al., arXiv:2311.11464. Mobile-energy economics for B24.

## Abstract-only — context, lower priority

- *When Agents Meet Electric Bus Fleet Operations* (2026), arXiv:2606.26400.
- *Approximation Algorithms for Combinatorial Optimization with Predictions*
  (arXiv:2411.16600) and Dagstuhl Report 14(10) on ML-augmented CO.
- *Decision-Dependent Stochastic Optimization: The Role of Distribution
  Dynamics* (arXiv:2503.07324).
- *Decision-Focused Surrogate Modeling for Mixed-Integer Linear Optimization*
  (2025 preprint).
- ML-for-CG updates: AGGNNI-CG (arXiv:2401.03692); RL hyper-heuristic CG
  (Computers & Industrial Engineering, 2025); pricing-problem ranking (EJOR
  320(2), 2025); POMO-CG (arXiv:2504.02383).
- Capacity-limitation / local-flexibility-market set: LFM design taxonomy
  (Energy, 2025, DOI `10.1016/j.energy.2025.136051`); capacity subscription
  agent-based study (Applied Energy 391, 2025); DTU CLS thesis (2023).
- Current NEMO Committee EUPHEMIA public description (institutional document;
  verify current exclusive-group rules and bid limits).

## Deprioritized (unchanged from handoff)

- Additional heuristic DP/peel/greedy campaign literature.
- Generic MARL bidding surveys beyond what the audit already covers.
