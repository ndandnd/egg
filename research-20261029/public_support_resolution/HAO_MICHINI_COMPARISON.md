# Hao–Michini comparison: identified sources and unresolved identity

29 October 2026. Bounded primary-source review; no numerical experiments, solver runs or old computational replay. This is not an exhaustive novelty clearance.

## Identity finding

**The exact intended “Hao–Michini” paper is ambiguous.** I could verify Bainian Hao and Carla Michini's congestion/cost-sharing papers, but did not identify a joint paper whose stated subject is linear-price support of nonconvex electric-bus fleets. Do not cite a guessed pricing title. The [primary university profile](https://engineering.wisc.edu/directory/profile/carla-michini/) and [Optimization Online author listing](https://optimization-online.org/author/michini/) identify their relevant work. A precise title/DOI from the human would resolve the remaining identity uncertainty.

Three plausible comparisons were inspected below. The strongest thematic match is the integer-splittable bin-packing paper: system-optimal allocations need not be stable, even under symmetric capacitated resources. Its institution is nevertheless different from EGG's posted marginal tariff.

## 1. Integer-splittable Bin Packing Games

**Verified authors/title:** Bainian Hao and Carla Michini, [Integer-splittable Bin Packing Games, author fulltext](https://optimization-online.org/wp-content/uploads/2025/05/WINE2025-18page-full.pdf). Use this specific version's internal numbering: PDF page index0 is an unnumbered title page; printed page numbers below are those on the paper.

Inspected §2, printed pp.3–5; Theorem1 and Lemma1, p.5; Theorem2, p.6; its full appendix proof, pp.20–21. Each player divides an integer-sized item across capacitated bins and pays proportional shares using load-dependent unit costs. Deviations change loads and their resulting charges. Theorem1 establishes NP-hardness of nonuniform social optimization even with one item, hence best response. Lemma1 characterizes the occupied-bin count of uniform equilibria; with identical bin costs, equilibria are socially optimal, but the converse can fail. Theorem2 supplies a regular instance with no pure Nash equilibrium (five items of size5, four bins of capacity/cost8).

**Comparison:** this already undermines broad claims that “integer allocation plus charging-like capacities can make optimum unstable” is new. It does not establish EGG's own-price/hull equivalence: proportional cost sharing, endogenous deviation charges and integer splitting differ from fixed linear bills, convex supply and continuous charging. EGG's battery chronology/full refill and exact capacity/equipment boundaries are physical distinctions. Its replication is additive posted-price regret, not this paper's multiplicative equilibrium approximation.

## 2. The Price of Anarchy in Series-Parallel Network Congestion Games

**Verified authors/title:** Bainian Hao and Carla Michini, [author manuscript dated30 September2021](https://optimization-online.org/wp-content/uploads/2020/11/8108.pdf). The inspected manuscript precedes the later journal publication; do not transfer theorem numbers to another version without checking.

Inspected introduction, model and proof setup. Theorem1, printed p.2, bounds price of anarchy by2 for symmetric series-parallel network congestion games with affine delays. Theorem3 and Corollary4, printed p.7, provide the deviation comparison used in the bound; the proof starts there and continues in §4. These are atomic path-choice games: a deviator encounters the load after adding itself to newly used edges. Social cost is the sum of experienced delays.

**Comparison:** EGG does not presently prove a price-of-anarchy bound or a congestion-network structure theorem. Its planner cost is c+F, and the posted-price response freezes the price rather than updating edge costs after a deviation. Therefore one cannot directly import their PoA bound, interpret EGG's regret as PoA, or claim to contradict equilibrium existence in their class. EGG's whole-owner/reserved-owner distinction is relevant to atomic versus small-player modeling, but the exact replicated family is a different question. This source is background motivation, not the closest support-theorem precedent.

## 3. Computing Equilibria in Integer Programming Games with Shared Constraints

**Verified authors/title:** Bainian Hao, Hyunwoo Lee, Robert Hildebrand and Carla Michini, [arXiv2610.04279v1 HTML fulltext](https://arxiv.org/html/2610.04279v1). This has four authors, not merely a Hao–Michini byline. PDF retrieval failed; the section/theorem identifiers below are verified in HTML, and no PDF pages are claimed.

Inspected §2 Definitions1–3, conditional equilibrium inequality(4), §2.2 Algorithm1/Proposition2 and §3 Theorem1/Corollary1. The model has finite jointly constrained integer profiles and opponent-dependent feasible deviations. Proposition2 certifies the generalized zero-regret procedure only with optimal best responses and valid initial inequalities; incomplete search cannot establish nonexistence. Theorem1 requires concave player costs and integral conditional-polytope vertices to obtain constancy on the minimal face; strict concavity gives vertex equilibrium strategies.

**Comparison:** EGG's reserved connectors are an explicit way to avoid silently treating shared-resource deviations as independent. This paper is a direct warning against that shortcut. It is not a linear marginal-price support theorem, and its finite-integer model does not directly cover EGG's mixed discrete/continuous fleet oracle. EGG should not claim a general equilibrium algorithm from its current hull column generation. The two models require different certificates and costs.

## Comparison with EGG's actual claims

Relevant local statements: `paper/latex/model_theory.tex`, complete-fleet support proposition and LOC identities; `paper/latex/exact_results.tex`, nominal/robustness/replication constructions; `research-20261029/support_extension/PROOF.md`, general expansion certificates, movement-only dominance and equipment-expansion region. These were already read in the continuing session; no old numerical artifacts were reopened.

| EGG statement | Relationship and defensible scope |
|---|---|
| Positive physical/hull gap prevents own-price support; zero gap permits it under qualification | Established convexification/duality specialization. None of the identified Hao–Michini texts makes this precise theorem their central result, but absence of direct overlap is not novelty: the manuscript already cites closer pricing precedents. |
| Full replenishment with continuous charging can leave support failure | Physically explicit application construction. Compare with cost-sharing nonexistence without suggesting theirs lacks integer structure or capacities. |
| Gap vanishes while absolute whole-owner regret persists along a subsequence; separately reserved individual gains vanish | Exact participant-scale calculation. Do not equate it with strategic Nash cost or claim a universal large-market counterexample. A full wider replication/coalition literature check remains outside this bounded review. |
| Adding alternatives cannot reduce an old plan's regret at its unchanged price | Elementary minimum-over-a-larger-set monotonicity. Useful clarification, weak standalone novelty. New supported plans may still erase global failure. |
| Old hull-dual bill certificate and strict positive-margin gap bound | Standard dual/Fenchel consequences specialized to set expansion. Do not sell as a new general pricing theorem. |
| Same-hardware nonnegative movement class preserves D/CH; changed-battery exact threshold and fee8 counterexample | Strongest specific new content here: physical dominance plus a completely characterized changed-equipment example. Its restrictions are essential; it is not an unrestricted omitted-duty theorem. |

## Strongest novelty objection and response

**Objection:** the paper packages familiar instability of discrete allocations and standard support/duality facts in a small bus example. The movement stability class may be read as dominance of deliberately nonbeneficial alternatives; the battery/fee boundaries are algebra on a two-service model. Neither source checking nor exact implementation agreement establishes significance. Resolving a synthetic public-timetable scenario would improve external evidence but would still not establish actual market prevalence or calibrated payments.

**Defensible response:** claim only the bus-specific physical mechanism and exact conditions, making full terminal replacement, admissible resource rights and the complete feasible alternatives explicit. Treat the broad theorem as attributed machinery. The sharpened question is whether physically meaningful alternative duties/equipment eliminate support failure and whether informative complete-fleet certificates establish it beyond the constructed example. If the public gap remains unresolved, say so. Do not frame distinction from these Hao–Michini games as a new general equilibrium or pricing theory.

**Suggested manuscript wording:** “Related discrete resource-sharing games demonstrate that optimality and equilibrium need not coincide. Our question instead fixes an ex-ante linear marginal tariff and compares complete, fully replenished bus plans under convex supply. We provide explicit physical constructions and conditions for preservation or disappearance of support failure; the underlying support/convexification logic is established theory.”

This wording remains conditional on identifying which Hao–Michini paper the human intended. The review does not justify an assertion that their entire body of work lacks any related result.
