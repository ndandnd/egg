# Bounded novelty review: common-loss efficient projection

Read `LOSSY_PROJECTION_CANDIDATE.md`. Targeted primary fulltext checks below, including one newly relevant source reached through Mukhi2025's cited chain. No code, numerical work, actual public input, source edit or new broad survey. This evaluates a candidate distinction; it does not certify originality or replace independent proof review.

## Judgment

The strongest plausible new statement is **assignment-dependent efficient aggregation with a fixed vehicle-cost layer**: in the stated common-window/common-efficiency model, every physical point is dominated by the attainable cardinality-matching envelope, which has at most two affine pieces per feasible cardinality. That is materially more precise than “we model charging losses” or “lossy V2G can be optimized convexly.” The latter ideas already have direct primary precedents.

No equivalent assignment-cardinality/gross-connector joint frontier theorem was identified in the inspected sections. However, the formula is built from elementary positive/negative-part elimination and classical matching minima. A skeptical reviewer can still regard it as a specialized corollary. Its significance depends on the exhaustive physical realization and domination proof, not on generic losses, V2G, matching, or finite polyhedral convexification being new.

## Closest primary comparisons and access scope

### Al Taha and Bitar2024: the most important additional comparator

Feras Al Taha and Eilyan Bitar, [When are Lossy Energy Storage Optimization Models Convex?](https://arxiv.org/html/2403.14010), arXiv2403.14010v2,19November2024; [PDF](https://arxiv.org/pdf/2403.14010). Inspected §II equations(1)–(6), PDF pp2–3; §III Theorems1–3/equations(7)–(10), PDF pp3–4; TableI/§III-A, p5.

They give an exact piecewise-affine grid-power/SOC coordinate transformation for a single lossy storage device. Its SOC feasible set is a convex polytope, and sufficient objective monotonicity conditions preserve convexity after substitution. TableI includes buy/sell energy-arbitrage conditions. Thus neither eliminating lossy charge/discharge variables nor conditional convex optimization through monotonicity can be claimed as new here.

Their inspected theorem has no endogenous service matching, cardinality-dependent bus fee or shared serial gross connector. Our candidate uses those additional structures to collapse all same-cardinality matchings to r_m and to characterize the efficient `(early grid load,terminal grid load,vehicle cost)` image. This is a conditional application distinction, not evidence that our model is more general: their temporal/leakage model is richer in other directions. The two formulations also assert different objects—exact transformed feasible profiles versus an efficient, domination-preserving fleet envelope.

### Mukhi, Loho and Abate2025: exact aggregation with an explicit losses limitation

[Exact Characterization of Aggregate Flexibility via Generalized Polymatroids](https://arxiv.org/html/2503.23458v2), v2,17June2025. Re-inspected §II-D–II-E, §III-B Remark4, and §III-C Theorem3/equation(15). These are HTML section/theorem locators; no unverified journal page numbers are asserted.

The exact generalized-polymatroid aggregation combines prescribed convex device populations. SectionII-E explicitly assumes perfect round-trip efficiency for bidirectional devices; charging-only efficiency can be absorbed by scaling. Remark4 explains why imperfect bidirectional efficiency breaks the relevant symmetry. This prevents treating their exact aggregation theorem as a direct proof of our lossy fleet result. Equally, it does not imply that losses have never been handled exactly—Al Taha–Bitar supplies an immediate counterexample to that broad claim. The candidate's useful difference remains the service-assignment/cost-labelled efficient envelope under highly restrictive shared-window physics.

### Mukhi and Abate2023: fixed-population charging polytope

[An Exact Characterisation of Flexibility in Populations of Electric Vehicles](https://arxiv.org/pdf/2306.16824). Re-inspected §III equations(9)–(14), Theorems1–2, PDF pp3–4. Its fixed-device aggregate charging set has a permutahedral/Minkowski characterization. It does not directly provide assignment-dependent cardinality fees or the candidate's common-loss two-window envelope. Do not market the finite-endpoint hull representation itself as a new aggregation principle.

### Zhou, An and Schmöcker2025: richer bus/V2G optimization

[Author full manuscript](https://www.researchgate.net/publication/392115348_Optimization_of_charging_and_discharging_schedules_for_battery_electric_buses_under_the_V2G_environment), DOI[10.1080/21680566.2025.2506689](https://doi.org/10.1080/21680566.2025.2506689). The immediately preceding focused review inspected §2, manuscript pp8–14, objective(1), constraints(2)–(23), and overnight/sensitivity discussion. No redundant retrieval was needed here. Fleet/assignment/partial charging/discharging and operational cost tradeoffs are already modeled. The extracted equations are imperfect, so this review does not certify every efficiency or connector detail. Those operational ingredients cannot distinguish the candidate; its proposed exact efficient-frontier theorem is the narrower claim.

## What should be claimed, and what should not

Suggested statement:

> Under common efficiencies, common charging windows, full replenishment, a fixed allowed successor graph and one gross-throughput connector, the coordinatewise efficient fleet load–vehicle-cost frontier is the Pareto pruning of finitely many attainable two-piece curves determined by classical cardinality-matching values. Coordinatewise monotone planning and nonnegative-price response values can therefore be reduced to this representation.

Retain “efficient,” “Pareto pruning,” and the objective/price restrictions. The full physical set includes dominated cycling and other terminal loads. The entire curve union need not be globally nondominated; zero-price ties can retain dominated responses. Negative marginal values, differing bus efficiencies, staggered availability or additional transition energy invalidate a silent extension. Convex hulls of the finite segment endpoints/kinks are standard once the reduction is established. No new universal scalar threshold-location support criterion has been proved.

The two-piece/common-efficiency result is a plausible structural advance over the lossless statement, but not automatically a strong-paper contribution. The best next presentation is a short exact theorem showing precisely why r_m remains sufficient despite bidirectional losses, followed by a physical allocation diagram and an explicit warning that only efficient/monotone values are preserved. A long account of familiar lossy accounting or repeated toy agreement would not answer the novelty objection.

## Search limits and recommended attribution

The narrow query also surfaced storage-complementarity work, including an AppliedEnergy2024 fulltext route that returned403; its inaccessible formulation was not used to draw an absence conclusion. No comprehensive fixed-charge scheduling/aggregation clearance was attempted. Add Al Taha–Bitar alongside Mukhi2025 when explaining the lossy coordinate change and monotonicity; distinguish the fleet/matching envelope from both. Existing pricing/matching attribution remains necessary. No first-ever or broad exact-lossy-aggregation claim is supported.
