# Critical review 07: novelty and positioning after the full polygon

Source-only review of current `main.tex`, `related_work.tex` and `full_lossy_projection.tex`, against the already inspected primary-source comparisons in `FULL_LOSSY_PRIOR_ART_CHECK.md` and `TARGETED_FRONTIER_NOVELTY_REVIEW06.md`. No fresh literature search, numerical work, evidence replay or TeX edit.

## Overall judgment

**The paper now states a precise structural contribution, with substantially better boundaries. Originality and sufficient significance remain open; submission readiness is not established.** The new full projection is a clearer primary result than another operational V2G example: it identifies exactly what is preserved, for which physical action model, and why objective monotonicity is no longer needed. It does not create an ML contribution.

## Concrete claim that survives this review

The strongest defensible claim is: for the declared two-batch/common-window model, a minimum early-requirement matching at each cardinality suffices for the **entire attainable joint period-load and intrinsic-cost image**, represented by five-halfspace polygons and constructively realized with serial inventory-feasible actions. The full-set equality makes negative-price response values meaningful without the earlier Pareto-pruning restriction. It is stronger than reporting an optimal schedule for one chosen tariff, and different from projecting a fixed population whose charging availability is prescribed.

The mathematical burden is assignment replacement and physical sufficiency—not the elementary observation that five halfspaces in two dimensions have at most five vertices. The current proof makes the important steps visible: per-bus endpoint boxes, baseline exchanges, finite neutral cycles, gross connector occupation, full terminal refill, and containment across all matchings at one cardinality. The negative-price example explains why the extra physical points matter and correctly states D=CH for its linear objective.

## What the power/wear corollary contributes

Unequal common directional powers replace an energy budget by serial occupation `C/K_c+X/K_d<=1`. Common affine throughput wear belongs in the cost image; lossless neutral cycles can leave net loads unchanged while altering wear. These are useful model-completeness consequences and prevent the apparent projection from forgetting economically relevant variables. The conservative finite action bound gives a concrete finite realization, rather than relying on an unbounded switching limit.

These are natural extensions of the construction, **not independent generic breakthroughs** in battery convexification, degradation modelling or scheduling complexity. They do not cover heterogeneous acceptance, nonlinear depth/rate-dependent wear, session costs, positive switching time or arbitrary low action caps. The text states those limits and distinguishes this source-reviewed corollary from the eight symmetric/no-wear implementation cases. The abstract does not advertise power/wear as numerically qualified, which is appropriate.

## Prior-art positioning

The current related work correctly credits operational service assignment, vehicle fees and charger capacities to scheduling models; the inspected Borndörfer formulation is material positive overlap, not merely a generic citation. Fixed-population Minkowski/generalized-polymatroid aggregation remains prior art. Al Taha–Bitar's signed-per-step SOC bijection must not be relabelled as the same coarse-window cycling model; the manuscript now explains that difference without presenting unconstrained simultaneous charging/export as physical exactness.

Matching, conversion bookkeeping, time sharing, box sums, planar vertex counts, affine imaging, disjunctive convexification and support duality are expressly classical. No first EVSP/grid, first transport–V2G, first spare-bus, first convex storage, or first negative-price assertion appears in the reviewed lead. The Wu2019 access footnote appropriately preserves unresolved formulation overlap rather than inferring absence. These choices are sound. The previous bounded checks still do not exclude an equivalent exact special-case projection elsewhere.

## Strongest reasons to reject or request major revision

1. **Depth:** an expert may regard the result as an elementary synthesis once the exceptionally synchronized service/access model is imposed. Exact physical coverage is necessary but does not by itself establish a deep theorem. The useful question for an outside reviewer is whether the matching statistic's full-set sufficiency provides a reusable insight beyond that ideal class.
2. **Operational significance:** cycling without switching/degradation penalties is deliberately permissive. Affine wear improves completeness, but is not empirical validation of such cycling or calibrated battery economics. One public charge-only timetable proves existence in another declared model; it does not validate the closed form on operational fleets or establish the size/prevalence of losses.
3. **Scope and presentation:** the main hierarchy is now appropriate, but a reader faces many extensions, boundaries and certificate histories. Keep the full projection primary, the efficient/support statements as consequences, the edge-dependent construction as a precise failure boundary, and the public certificate as separate existence evidence. Do not let the count of examples substitute for one clear scientific message.
4. **Independent validation:** exact controls and internal independent implementations improve trust, but are not external replication or exhaustive literature validation. The local-only bundle and separately scoped binary/exact-additive models must remain explicit.

## ICML positioning

**The central ML gap remains decisive for an ICML-oriented submission claim.** The reviewed draft has no substantive learning problem, learning algorithm, statistical/generalization theorem, or demonstrated learning result. Classical matching, convex optimization, exact certificates and a physical projection are not converted into ML by using “prediction”, proposing future surrogates, or pointing to old failed capacity experiments. This is a scientific-content assessment, not a claim about conference rules or a guarantee of rejection.

The honest next positioning is as an operations/energy-market structural theory paper whose significance needs domain-expert assessment. Adding a rushed ML label or an unrelated predictive benchmark would weaken the coherence. The current contribution can be stated precisely without that label; its originality, depth and practical reach still require critical evaluation. No submission-ready conclusion follows from this review.
