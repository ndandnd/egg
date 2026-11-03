# Critical novelty review for the strengthened EGG paper

29 October 2026. The human withdrew the Hao–Michini comparison; that historical note is not a central positioning source. This bounded review uses five relevant primary fulltexts inspected in this continuing session, plus one important publisher-abstract lead whose fulltext remains inaccessible. It is not an absence-of-prior-art certificate. No numerical work or manuscript editing was performed.

## Assessment

The defensible candidate contribution is an exact, physically explicit investigation of support failure for complete bus schedules under full terminal replenishment, with conditions under which specified physical expansions preserve or erase it. General price support, convexification, LOC accounting, whole-schedule columns, price decomposition and bus/grid coupling are established. Submission readiness cannot be inferred from exact implementation agreement or a positive toy gap.

**Candidate claim:** “For a stated fully replenished electric-bus model with continuous charging, we characterize when assignment indivisibility prevents support at an ex-ante marginal supply tariff. We give explicit participant-scale calculations and physical/equipment expansion conditions distinguishing persistence from disappearance of the obstruction.”

This is a plausible narrow contribution description, not a verified novelty claim. The qualification on tariff institution and complete physical alternatives is essential.

## Five closest inspected fulltexts

### 1. Hümbs, Martin and Schewe: general support characterization

[Exploiting complete linear descriptions for decentralized power market problems with integralities](https://link.springer.com/article/10.1007/s00186-022-00775-z), Mathematical Methods of Operations Research95,451–474 (2022), DOI10.1007/s00186-022-00775-z.

Inspected §2, complete-description definition, Theorem1 and its discussion. Linear-price equilibrium is characterized through an integral optimum of the central LP relaxation when participant descriptions are complete. The authors also identify Harks's related earlier theorem. EGG's common-fleet support equivalence is a convex-supply specialization of this general line, not a new discovery that integer decisions can obstruct prices. EGG's use of the full fleet set is modeling discipline rather than a new economic principle.

### 2. Hua and Baldick: convex hull, duality and LOC

[A Convex Primal Formulation for Convex Hull Pricing](https://users.ece.utexas.edu/~baldick/papers/convex_hull_2017.pdf), IEEE Transactions on Power Systems32(5),3814–3823 (2017), DOI10.1109/TPWRS.2016.2637718.

Inspected §§II–III, Theorem1 at journal p.3816, and ramp extension §IV-C at p.3820. Convexified participant costs/sets represent the Lagrangian dual; the balance-only duality gap is total LOC. EGG's Fenchel identities and hull pricing inherit this framework. Moving indivisibility to bus assignments with convex generation gives a specific application, while ramps themselves are already treated. A set of admissible subgradient prices is mathematically standard; the bus example and correct reporting may be valuable without constituting new price theory.

### 3. Andrianesis et al.: whole feasible schedules as columns

[Computation of Convex Hull Prices in Electricity Markets with Non-Convexities Using Dantzig–Wolfe Decomposition, author v2](https://arxiv.org/html/2012.13331v2), IEEE Transactions on Power Systems37(4),2578–2589 (2022), DOI10.1109/TPWRS.2021.3122000.

Inspected §§II–III, especially equations7–13 and schedule/column interpretation. A column represents an entire participant schedule; pricing is self-scheduling at announced prices. The formulation permits continuous feasible dispatch schedules and develops the hull through extreme points. EGG's whole-fleet columns apply this machinery to a harder participant oracle containing service coverage and shared charging. Its CG/subgradient comparison is not algorithmic novelty. An unresolved full-fleet oracle is an obstacle, not a demonstrated computational advance.

### 4. Zoltowska and Lin: bus bids and discrete charging

[Optimal Charging Schedule Planning for Electric Buses Using Aggregated Day-Ahead Auction Bids](https://mdpi-res.com/d_attachment/energies/energies-14-04727/article_deploy/energies-14-04727.pdf?version=1628071003), Energies14(16),4727 (2021), DOI10.3390/en14164727.

Inspected §§2.1–2.3 and case discussion: aggregation/disaggregation MILPs preserve detailed bus/charger constraints around a linear hourly auction. Bus trip energy and availability are inputs. Equation2 subtracts usable initial inventory; the case permits ending at minimum SOC. EGG's endogenous service assignment, operating cost and compulsory terminal refill distinguish its question. Do not claim that this predecessor lacks integer charging decisions, market participation or physical detail. Its terminal convention motivates EGG's boundary choice, not a universal criticism of its model.

### 5. Wu et al.: endogenous vehicle-to-trip assignment and grid objectives

[The multi-depot electric vehicle scheduling problem with power grid characteristics, accepted manuscript](https://eprints.whiterose.ac.uk/id/eprint/180812/1/Wu%20et%20al%20-%20TRB2021%20-%20EV%20scheduling%20-%20WWR.pdf), Transportation Research Part B155,322–347 (2022), DOI10.1016/j.trb.2021.11.007.

Inspected §3.1 assumptions, §3.3 costs and §3.4 formulation, particularly objectives3–4 and constraints5–17, manuscript pp.7–12. It chooses vehicle-to-trip assignments and charging under time-of-use tariffs and a peak-load objective, with branch-and-price. AssumptionA1 includes full overnight charging and full recharge when plugged in. Thus “full charging plus endogenous assignments plus grid-aware scheduling” is already established. EGG instead asks support at load-dependent marginal supply prices and compares complete physical/hull costs. Do not conflate assumed overnight charging with EGG's explicit horizon-end replacement-energy accounting without checking their cost treatment.

## Important closer endogenous-price lead: access limitation

Z. Wu, F. Guo, J. Polak and G. Strbac, [Evaluating grid-interactive electric bus operation and demand response with load management tariff](https://doi.org/10.1016/j.apenergy.2019.113798), Applied Energy255,113798 (2019).

The inspected publisher abstract explicitly describes bus service planning and electricity market clearing in a bilevel framework using distribution locational marginal prices. Publisher section previews identify bus planning §2.2, clearing §2.3, DLMP §2.4 and MPCC §2.5. Fulltext retrieval was blocked; no theorem, integrality, refill or convex-hull absence claim is justified. **This source is sufficient to reject broad first-ever bus-operation/endogenous-electricity-price coupling language, but insufficient to settle the narrow support-counterexample comparison.** Verify its full formulation before final submission positioning. Bibliography below preserves initials because expanded author names were inconsistent across secondary records.

## What survives the overlap

| Current EGG result | Critical novelty assessment |
|---|---|
| Support iff physical/hull values agree, under qualification | Attributed established machinery; no general theorem novelty. |
| Full-refill continuous-charging obstruction and robustness example | Plausible application-specific constructive content; full refill removes a modeling shortcut, but needs an explanation of why this exact obstruction matters. |
| Capacity/fee phase region | Exact within-project characterization; algebraic breadth within the toy is not operational breadth. |
| Whole-owner absolute regret versus reserved-pair regret under replication | Useful exact participant-scale distinction. No broad coalition/replication novelty clearance from these five sources. The prior Hreinsson abstract-only check cannot establish that its full paper lacks a related result. |
| Enlargement cannot rescue an old plan; dual/Fenchel margin certificate | Elementary/general consequences; present as tools, not flagship novelty. |
| Movement-only dominance and changed-equipment threshold/fee8 counterexample | Strongest recent physical content. Explain that the movement class adds dominated alternatives under fixed resources; acknowledge the apparent restrictiveness. The equipment example shows real set changes can erase the mechanism, rather than claiming arbitrary omitted duties are harmless. |
| Public37-service support resolution | Potentially valuable independent scale evidence, but only the eventual certified result can be claimed. Two depot variants of one timetable do not measure prevalence. Synthetic economics do not calibrate actual losses. |

## Submission-readiness bar

The strongest objection remains **significance**: mature pricing theory plus small physical constructions and dominated-expansion stability may be mathematically correct yet too modest. A larger exact certificate would address scale and oracle credibility, but one synthetic public scenario alone would not establish institutional relevance. The paper needs a concrete reason the tested posted-price institution is worth diagnosing, a structural insight that survives meaningful fleet alternatives, and evidence that the issue can be consequential rather than merely possible.

Before describing the strengthened paper as submission-ready, require:

- Precise attribution: all general hull/support/dual/CG claims separated from the actual physical theorem.
- A defensible tariff and participant definition; keep strategic billing, fixed-price deviation and planner cost distinct.
- New physical statements with nontrivial scope, or certified timetable evidence whose assumptions and unresolved bounds are visible.
- Direct inspection of the Wu2019 formulation to close the closest endogenous-price source gap.
- An honest endpoint if public support remains unresolved: possibility is proved; prevalence and meaningful magnitude are not.

No ML survey or new learned-method claim is needed for this paper. No “first,” universal absence, broad V2G novelty or operational savings claim follows from this bounded review.

## Citation-ready bibliography

Existing manuscript keys: `huembs2022complete`, `huaBaldick2017`, `andrianesis2022hull`, `zoltowskaLin2021`, `wu2022grid`. Their verified metadata and DOI links are above; reuse rather than duplicate them.

Proposed additional entry (fulltext inspection still pending):

```bibtex
@article{wu2019gridinteractive,
  author = {Wu, Z. and Guo, F. and Polak, J. and Strbac, G.},
  title = {Evaluating Grid-Interactive Electric Bus Operation and Demand Response with Load Management Tariff},
  journal = {Applied Energy},
  year = {2019},
  volume = {255},
  pages = {113798},
  doi = {10.1016/j.apenergy.2019.113798},
  url = {https://doi.org/10.1016/j.apenergy.2019.113798}
}
```
