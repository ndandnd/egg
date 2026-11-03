# Targeted frontier novelty review 06

## Outcome and access scope

**No equivalent matching-cardinality/common-loss frontier reduction was located in the relevant formulation sections inspected below. This is a bounded comparison, not an absence or originality certificate.** The strongest verified overlap is broader endogenous scheduling, vehicle cost and shared charging—not merely fixed-population aggregation.

I read the current related-work entry, the earlier precise contribution comparison and the renewed Wu access limitation. Wu was not searched again. I selected one already identified, fully accessible primary source: Ralf Borndörfer, Andreas Löbel, Fabian Löbel and Steffen Weider, *Solving the Electric Bus Scheduling Problem by an Integrated Flow and Set Partitioning Approach*, ATMOS 2024, 11:1–11:16, [official record](https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.ATMOS.2024.11), [official open PDF](https://drops.dagstuhl.de/storage/01oasics/oasics-vol123-atmos2024/OASIcs.ATMOS.2024.11/OASIcs.ATMOS.2024.11.pdf). Relevant full mathematical text was inspected, not just its abstract: Sections 2–2.2, Section 4 and Section 5's formulation/dual discussion. No new source or citation chain was pursued.

## Verified positive overlap and exact anchors

Section 2, pp.11:2–11:4, jointly selects trip chains, vehicle/depot types and fleet composition; fleet size and operating expense enter the optimization. Equations (1)–(6) include integer assignments, exact trip coverage and vehicle-mix bounds. Section 2.1, pp.11:4–11:5, equations (7)–(15), adds SOC flow and capacity-limited charger-slot timelines with state-dependent replenishment; equation (10) imposes full pullout inventory. Section 4, pp.11:8–11:10, explains fractional recharge sharing, then couples selected vehicle blocks to the flow model in equations (21)–(26). Its between-block full-restoration restriction is explicit, with opportunity charging discussed separately. Section 5, p.11:11, equations (27)–(31), develops a Lagrangian decomposition of the relaxed formulation.

These are substantive predecessors to assignment-created charging opportunities, paid vehicle use, shared charging and physical-versus-fractional distinctions. They invalidate a contribution framed as introducing those ingredients. The inspected formulation is a general optimization representation; it is not the particular frontier theorem considered here.

## The exact comparison the present paper must earn

Our candidate contribution is a representation of a restricted physical image **before fixing one supply objective**. For two simultaneous batches and fixed single-connector resources, the lossless theorem retains vehicle-cost layers while pairings change. In the common-loss extension, the claim is only an efficient early-load/terminal-load/vehicle-cost image: a minimum-cost matching statistic `r_m` at each cardinality suffices, followed by at most two affine pieces per cardinality and Pareto pruning. It is not the entire lossy feasible image.

For an exact anticipation of that result, the crucial prior step would be a proof that every same-cardinality assignment can be replaced by an `r_m` minimizer without increasing either grid-load coordinate or vehicle fee, while respecting gross bidirectional connector use and full replenishment. A generic route/charging MIP can contain such a special case without stating that replacement theorem. Conversely, expressibility within a richer formulation does not make the claimed closed form automatically original or significant.

No such replacement/finite-frontier assertion was identified in the inspected sections. Do not turn that bounded observation into a claim about every result in this paper, its references, or the scheduling literature. In particular, generic nonlinear charging is not automatically a treatment of common bidirectional conversion losses and symmetric export settlement; neither should our simpler loss model be presented as operationally richer.

## Reader value and strongest rejection

If correct, the proposed reduction lets a reader compute cardinality-dependent feasible load/cost layers and optimize several monotone supply objectives without repeatedly enumerating complete assignments. It also identifies precisely why a lossless load interval can still have a nonconvex cost-labelled image. The support criterion and hull machinery remain classical applications; their familiarity is not evidence against the physical reduction, but limits the novelty claim.

The strongest rejection remains that the reduction may be an elementary consequence of box aggregation, positive-part accounting and classical matching once the common windows, common efficiencies and constant total service energy are imposed. The paper must make the exhaustive physical replacement/attainment argument and the resulting decisions clear. More numerical examples cannot resolve that judgment. Assignment-dependent transition energy, differing windows/efficiencies, or richer operational costs cannot inherit the one-statistic result automatically.

## Recommended wording and residual uncertainty

Keep the current attribution to integrated flow/set-partitioning models, optionally pointing to Section 2.1 and equations (21)–(26). Describe the present advance as an **exact restricted cost-labelled projection and common-loss efficient reduction**, not first assignment-aware aggregation, first shared charging, first fractional-versus-physical distinction, or new pricing duality. Do not add a stronger absence claim.

This one-source full-formulation check strengthens the positive-overlap account and narrows a plausible distinction. It does not settle whether an equivalent special-case theorem exists elsewhere. Wu2019's exact institution remains an explicitly unresolved separate comparison; failed access contributes no evidence for the frontier's novelty. External subject-matter assessment remains necessary for significance and originality.
