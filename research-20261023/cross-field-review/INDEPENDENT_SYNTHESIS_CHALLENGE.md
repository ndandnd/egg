# Independent challenge to the cross-field synthesis

23 October 2026. Based on EV_OR_REVIEW.md, BIO_CONTROL_REVIEW.md and CHEM_QUANTUM_REVIEW.md. This is a skeptical integration judgment, not empirical validation. No new experiment or solver run was performed. Parent's additional screening, online-algorithm, CEGAR and warm-start checks are outside this note.

Subsequent source check: the Wu et al.2022 manuscript mentioned below has now been selectively inspected in GRID_EV_OVERLAP_NOTE.md. The original challenge is preserved; its request for a closer grid-formulation comparison remains relevant.

## Verdict

There is a defensible research program, but the present ingredients do not yet establish a new general algorithm. Learned restriction, restricted optimization, adaptive expansion, exact fallback and domain-specific feasibility checking are established. In particular, [Olson, Lusby and Røpke's 2026 primary conference abstract](https://orbit.dtu.dk/en/publications/graph-neural-network-enhanced-column-generation-for-electric-bus-/) explicitly restores edges when reduced-graph column generation stagnates, eventually using the full graph. Its preliminary status limits confidence in performance and proof details; it does not make the described recovery idea available for a novelty claim. [Montanaro et al. 2025](https://doi.org/10.1007/978-3-031-95976-9_7) also makes modern nonlearned GRASP/pruning an essential comparator.

The reports are strongest when they identify an unresolved decision: **which jointly feasible alternatives should receive limited search effort when shared charging and power make local edge usefulness misleading?** Calling this “biology plus chemistry plus control” would obscure the contribution. Each transfer should earn its place through a changed decision rule, measurable mechanism or proved statement.

## Transfers with incremental value

**Alternative-solution labels are the clearest addition.** Metabolic variability analysis supplies a precise objection to treating absence from one incumbent as a negative label. An EGG quality band, multiple witnesses and unresolved outcomes could change learning targets substantially. However, computing per-edge integral variability may cost more than the search it accelerates. The contribution must include label cost and show an improvement over cheap diverse-solution pools, positive-unlabeled treatment and ranking losses. A band defined by an incumbent is not automatically near-optimal.

**Coordinated repair has plausible value if complementarity is demonstrated.** Selected configuration interaction and ADAPT motivate current-state ranking and bundled restoration. These mostly rediscover adaptive pricing/neighborhood search at the architectural level. The added value would be a cheap, explicit coupling-aware score or repair generator that reliably detects improvements missed by one-at-a-time rules. Whole duties or paired vehicle/charging repairs are a better unit than arbitrary edges. Define the relevant neighborhood before claiming that a single-choice baseline cannot improve.

**Audits can add an honest statistical output.** Chemistry's separate construction/audit budgets are useful if the audited population and estimand are fixed: for example, the fraction of a specified repair neighborhood that contains improving moves. Known sampling probabilities can support uncertainty about that quantity. They cannot yield an optimality gap over all unenumerated plans. Test whether the diagnostic predicts costly failures before presenting it as a general method.

**Witness retention is sound engineering with a narrow guarantee.** Safety filtering and LMPC clarify how to retain a verified completion while evaluating new proposals. This protects an available incumbent under unchanged constraints and objective. It does not guarantee that a witness exists before the deadline, that later resource changes preserve it, or that the optimizer returns a better answer. Minimum-addition repair is a useful baseline; sparse repair alone can preserve an expensive fleet.

## Three strongest falsifiable questions

1. **Does the method learn energy scarcity after fleet improvements are removed?** Fix the fleet count and trips, vary tariffs and binding site-power/charger constraints, and compare full optimization, price-blind scores, ordinary greedy/GRASP pools and the proposed method at common total budgets. Measure charging cost, shifted demand and feasibility. Falsification: advantages vanish when fleet count is fixed, or price-blind selection performs equally well.

2. **Does coordinated selection outperform mature adaptive restriction?** Construct and independently verify instances with jointly valuable charging/movement changes; compare equal-size pools and identical restoration schedules using static ranks, randomized greedy/GRASP, reduced costs where valid, and explicit bundles. Falsification: equal-budget nonlearned or ordinary dual-based expansion closes the entire advantage, or bundles help only because they restore more choices.

3. **Do better labels/audits improve operational outcomes enough to repay their cost?** Compare single-incumbent labels, diverse witnesses and quality-band diagnostics on family/topology holdouts, accounting for labeling and audit computation. Evaluate catastrophic exclusions, returned objective and time to a valid full-model bound. Falsification: classification improves without downstream gains, or extra labeling/audit costs dominate savings.

## Overclaim and citation risks

- Restricted-model exactness, LP pricing termination and full integer optimality are different claims. Every bound needs its model universe and relaxation stated.
- “Price-aware,” “shared charging,” and “joint scheduling” already have close EV precedents. Supply coupling requires a formulation comparison, especially the independently unexamined Wu et al. 2022 power-grid paper.
- Rayleigh–Ritz, perturbation correction, operator completeness, flux consistency and recursive safety do not transfer their theorems to integral bus schedules. Preserve analogies as design hypotheses.
- Source depth varies markedly. Conference abstracts and abstract-only records support discovery and scope warnings, not implementation or reproduced numerical claims. Freeze arXiv versions; reconcile online and issue years. Verify recent 2026 chemistry publication metadata before final citation export.
- Engineering-day estimates are planning judgments, not literature evidence. FT50 fit is an aspiration until there is a strong general mechanism, credible operational setting and evidence beyond small synthetic instances.
