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
