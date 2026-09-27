# Journal positioning and evidence plan — 27 September 2026

Prepared by the literature/reviewer subagent. This is a focused primary-source
review, not a systematic review or proof of first-in-literature novelty. It uses
the September 21 research and implementation records, the PR52 coordination
certificate note, and the physical/reuse results copied into
`journal-research-work/doc`. No protected results were opened or scored.

## Recommendation

Target **Transportation Research Part C: Emerging Technologies**, with
**Public Transport: Planning and Operations** as the alternative. The proposed
paper should answer a transportation question: *when can electricity prices
coordinate an implementable electric-bus duty plan, and when does an apparently
small system-cost gap conceal an incentive or resource-feasibility problem?*

The TR-C publisher description emphasizes consequences for transportation
operation, resource use and performance, and explicitly emphasizes open datasets
and transferable benchmarking. This makes a reproducible fleet study a plausible
fit; it does not make a generic convex-hull theorem or solver wrapper sufficient.
The current official scope was read on September 27 through the
[Elsevier journal page](https://shop.elsevier.com/journals/transportation-research-part-c-emerging-technologies/0968-090X).
ScienceDirect's separate scope and author-guideline pages returned 403, so no
unverified page limits, template requirements or editorial timing are stated.

Public Transport's current scope explicitly covers computer-aided public
transport planning, vehicle scheduling, theoretical papers, applications and case
studies. It is a better fallback if the work ends as a careful, bounded scheduling
and economic-diagnostics study rather than a broad technology evaluation.
[Official Springer scope](https://link.springer.com/journal/12469/aims-and-scope).
This is a fit judgment, not an acceptance prediction or a journal-ranking claim.

EJOR is a stretch option only if a materially stronger general method emerges.
The [journal's EURO society description](https://www.euro-online.org/web/pages/518/european-journal-of-operational-research-ejor)
requires a major research finding or novel OR application; the indexed official
page was accessible, but a subsequent direct fetch timed out. Classical
convexification/duality specialized to buses is unlikely by itself to clear that
bar. Do not distort the research into an ML paper to seek a venue: the existing
reuse control shows no useful learned-column headroom.

## A defensible contribution statement

> We connect complete, physically implementable electric-bus duty schedules to
> price-support and lost-opportunity-cost diagnostics, preserving the distinction
> between a convexified load plan and a realizable fleet dispatch. A reproducible
> computational framework reports objective enclosures, replays physical
> feasibility, and makes boundary energy and shared-resource deviation rights
> explicit. Controlled examples separate system efficiency from individual
> incentives, and operational experiments test the size and relevance of those
> effects under declared assumptions.

The last sentence's operational clause is **prospective**. Replace it with actual
results before submission. Do not use “first,” “new equilibrium theorem,” “new
convex-hull pricing method,” “new fleet aggregation,” or “new use of column
generation” without substantially stronger novelty evidence. Direct antecedents
already cover all of these broad themes; see the [matrix](RELATED_WORK_MATRIX.md).

Suggested working title: **Price support and implementability in electric-bus
fleet coordination: complete-schedule certificates and charging constraints**.

## Five exact claims and their present limits

| Claim suitable for a draft now | Existing evidence | Missing evidence / wording boundary |
|---|---|---|
| **C1.** For the same nonempty compact physical schedule set in every model, convex differentiable supply cost, and attained minima, every physical schedule's own-gradient response regret satisfies `r(s) >= h(s)-z_CH >= z_D-z_CH`; zero planning gap is equivalent to existence of a physical best response at its own gradient price. | PR52's proof, attainment counterexample, arithmetic helper and independent review reported in the September 21 checkpoint. | Present as a specialization/interpretation of established nonconvex-market duality, not a new general theorem. Separate price taking from strategic market impact, and correspondence support from convergence of an iterative selection rule. An adapter's premise assertions do not authenticate physical facts. |
| **C2.** A fully replenished fleet can have a positive complete-schedule planning gap despite continuous charging: the new four-period cyclic construction has exact physical cost97, convexified cost7591/80 and gap169/80=2.1125. Both structures recharge exactly30 kWh. | Source/protocol frozen at7bf913a before execution. This review independently reconstructed all24 declared cases, with11 positive and13 zero gaps, and replayed every saved trajectory/mixture. [Analytical derivation](CYCLIC_CANDIDATE_CHECK.md), [artifact review](CYCLIC_INDEPENDENT_REVIEW.md). | This is an exact constructed reference model with native terminal windows, zero deadheads, unit efficiency and shared power rather than finite plug count. It is not a production-adapter or operational-prevalence result. The earlier0.8 depleted-terminal control remains useful as historical qualification but should not lead the journal's economic example. |
| **C3.** In the exact odd-N two-slot family, relative planner gap is `1/N²` under three stated normalizations, while absolute largest individual own-price regret can remain constant, decay as `1/N`, or decay as `1/N²`. | Exact rational laboratory and separate mathematical/economic reviews described in PR54 and the checkpoint. | These are deterministic examples, not sampled-population rates. Keep fleet fragmentation, ownership relabeling and supply-slope scaling distinct; report parity and common-price versus own-price regret. Operational prevalence remains unknown. |
| **C4.** Convexifying schedules before enforcing a within-fleet shared power limit can produce a misleading gap: the qualified caps4/4 example correctly has `D=CH=14`, whereas an aggregate-only cap leaves relaxed cost12.2. | Per-structure physical qualification and analytical control. | State exactly which hull is meant: convex hull of jointly feasible whole-fleet schedules versus intersection of separately convexified menus with a shared constraint. Neither is universally the “wrong” model; they correspond to different economic/resource rights. Shared power does not certify plug count or partially overlapping windows. |
| **C5.** On the four-state reuse control, retained physical columns reduced post-initialization pricing calls from3 to1 per transition at the same clean certificate; an additional analytic price proposal required2 and added no useful missing column. | Twelve certified cells, independent reconstruction, adversarial reuse tests; complete subprocess costs recorded. | This is one small control with two endpoint columns spanning the relevant minimum-energy face. It supports stronger reuse baselines, not a general speedup claim or rejection of learning. Harder fixed-physics trajectories, repetitions and matched full costs are necessary before a performance claim. |

For a journal manuscript, C1 supplies the interpretation; C2–C4 supply falsifiable
transport examples; C5 belongs in an implementation subsection or supplement
unless richer experiments establish a substantial new computational result.

## Reviewer questions to design against

These are my anticipated objections, not rules quoted from the journals.

1. **What is the actual decision-maker and feasible deviation?** A single fleet
   operator may own all buses and a depot, while multiple independent operators
   may share infrastructure. Define those models separately. A jointly feasible
   whole-fleet hull cannot automatically justify independent agents' access to
   an already occupied charger. If scarcity prices are introduced, account for
   charger rent separately from the energy supplier.
2. **Is the headline effect a boundary-energy artifact?** Lead with a cyclic
   instance, or price terminal stored energy explicitly. Report total service
   energy, starting/ending SOC, vehicle count and terminal-window rights beside
   every comparison. A native common terminal window is preferable to a
   zero-energy passenger-trip marker in the paper's model.
3. **Is the “convex hull” complete?** Explain the column object: a complete fleet
   plan differs from one vehicle duty in a set-partitioning master. An incomplete
   LP relaxation does not establish equilibrium nonexistence. Publish a tiny
   enumeration cross-check and identify which large-instance bound directions
   remain valid without full enumeration.
4. **How certain are the certificates?** Distinguish exact rational examples,
   numerical enclosures conditional on optimizer/replay tolerances, and formal
   interval/exact certificates. Report unresolved statuses as unresolved, not
   infeasible. A positive planning-gap lower bound requires physical LB minus
   convexified UB; zero-gap claims need stronger coverage. Show sensitivity to
   tighter tolerances and an independent solver on selected cases if feasible.
5. **Are prices economically calibrated?** Exogenous TOU prices, endogenous
   marginal supply costs, demand charges and charger scarcity prices are
   different objects. A public timetable supplies demand geometry; it does not
   identify the supply curvature `b`. Declare stylized curvature and give
   dimensional sensitivity until a defensible calibration exists.
6. **Does an incentive metric imply a funded mechanism?** Fleet LOC at a common
   convex-hull price can be zero while supplier LOC is positive. Own-gradient
   regret, minimum aggregate LOC, make-whole payments and cash financing are
   different. Do not claim budget balance, truthful reporting or voluntary
   participation from a planner-gap number.
7. **Are the comparisons fair?** If acceleration remains in the paper, use cold,
   retained pool and retained pool plus analytic shift under identical clean
   termination. Charge setup, replay, duplicate proposals, LP/pricing work and
   final verification; report failures separately. Never reuse old lower bounds
   across changed objective states.
8. **What transports beyond a constructed example?** Use fully disclosed
   synthetic parameter grids plus at least one provenance-qualified operational
   timetable. Preserve source units, directed/time-dependent deadheads and
   boundary energy. A simplified derivative must be labeled as such. Synthetic
   examples are useful for mechanism explanation, not prevalence estimates.

## Evidence and presentation package for a strong first draft

Prioritize these artifacts over a large learner campaign:

| Artifact | Scientific purpose | Required annotations |
|---|---|---|
| Two-panel duty timeline / SOC trajectory for a cyclic positive-gap example | Make the indivisibility and terminal-energy accounting inspectable. | Real services, native charge windows, each bus, shared and individual power, initial/final SOC, physically replayed traces. |
| Cost versus early charge with physical branches and the convexified lower boundary | Show exactly why the fractional optimizer is not a daily dispatch. | Label physical D, convexified CH, mixture weights; distinguish expected daily cost from cost at mean load. |
| Fleet/supplier LOC decomposition at own price and common CH price | Explain the price-conditioning issue without conflating transfers. | Same physical dispatch in both panels; prices in currency/kWh, LOC in currency. |
| Gap/regret versus fleet scale under three separate normalization panels | Show why a falling relative gap is insufficient. | Absolute values, relative values, parity, fixed/variable total service and supply slope; no unsupported fitted universal rate. |
| Resource-rights table and a shared-power witness | Prevent a misleading equilibrium interpretation. | Whole-fleet agent, residual-capacity deviations and scarcity-priced agents in separate rows. |
| Computational evidence table | Make numerical claims auditable. | Number of base instances and dependent transitions, certified/unresolved counts, LB/UB width, full runtime, model size, hardware/thread limits and source identities. |
| Operational translation table | Make the case-study simplifications reviewable. | Source field, source unit, model field, conversion, omission/extension and validation status. |

The first draft can be excellent while openly retaining a short “evidence still
needed” note. It should not fill missing results with projected numbers. Submission
readiness requires the central physical/operational claims to be resolved and all
figures reproducible from pinned artifacts.

## Material decisions to flag to the user

Routine experiments, negative results, failed hypotheses and tool repairs can
remain autonomous. Flag a consequential pivot if the effect disappears under
cyclic/reasonable parameters, if the operational dataset cannot be shared enough
for reproducibility, if the model must change from price-taking coordination to
strategic market power, or if a proposed transfer mechanism entails real funding
or institutional commitments. Journal choice can stay a working target until
the evidence warrants a submission decision. No submission or author commitment
has been made by this reviewer.
