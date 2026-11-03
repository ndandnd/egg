# Claim hierarchy and adversarial significance review

29 October 2026. Bounded substantive review of current main, heterogeneous theorem/proofs, related work and framework, informed by the existing focused novelty and significance notes. No new literature lookup was necessary. No numerical work, imports, hashes, source audit, execution or TeX edits. This is not originality certification.

## Strongest defensible new statement

The main candidate contribution is now the **complete joint load–vehicle-cost classification for heterogeneous two-batch services with one fixed shared connector per charging window**, followed by the necessary-and-sufficient physical-attainment criterion for its hull optimum. It is stronger than the original scaled-resource example: K and H remain fixed with population, terminal throughput can impose a positive lower load, high matching cardinalities can become infeasible, and the first hull edge is genuinely clipped. Every complete crossassignment is included rather than selected from a plan bank.

A precise claim is:

> For the specified two-batch, complete-crossmatching model with full replenishment, we derive the exact cost-labelled physical projection under fixed early and terminal shared charging resources, its clipped lower convex frontier, and the physical-attainment conditions for a strictly convex supply optimum. Under the stated price-attainment qualifications these conditions characterize marginal-price support.

The core contribution is this composition with its physical realization, not a new support theorem, a new matching algorithm or a new general EV aggregation principle. The load-only set is the interval [L,U]. The interesting discrete object is the cheapest bus count attainable at a load, and the resulting joint frontier.

## What is classical and what remains application-specific

1. **Fixed-matching charging interval:** raw SOC gives independent early boxes; common availability permits serializing their total at K and terminal replacement at H. This is elementary convex aggregation, substantially simpler than the prescribed-population multiperiod aggregation results reviewed in Mukhi–Abate2023 and Mukhi–Loho–Abate2025.
2. **Selecting and pairing services:** monotonicity selects the m smallest energies in each batch and the positive-part exchange inequality yields opposite ordering. The sorted corollary is transparent and correct, including ties and zero edges. It sharpens the objection that no difficult combinatorial optimization remains under these assumptions.
3. **Cardinality convexity:** integral bipartite flow and convex LP value functions give convex matching thresholds. Affine bus fees then turn these thresholds into the lower hull. Neither ingredient is novel in isolation.
4. **Support:** physical attainment of a hull minimizer, and dual prices supporting an attained physical optimum, are classical nonconvex-pricing facts. The new content is where the exhaustive physical fleet model attains that frontier. Related work correctly distinguishes this from operational bus formulations with richer routing/capacity physics, including Borndörfer2024.

No directly identical joint classification was verified in the already inspected primary sources. That supports a bounded candidate distinction, not an absence claim against the wider fixed-charge scheduling/aggregation literature.

## Proof and claim gaps

No new fatal mathematical gap was found in the displayed shared-resource projection or support proof. In particular:

- Every paired early lower bound is at most its A demand because b_j<=B. This makes the raw intervals nonempty before aggregate clipping, and the zero matching proves feasibility iff L<=U.
- Common full-hour availability and acceptance of connector power are what make total-energy inequalities sufficient. These assumptions exclude arrival-dependent charging queues, heterogeneous acceptance limits, switching overhead and intermediate departures. They must remain next to the theorem; the word “shared” alone does not generalize to those settings.
- Clipping the first threshold increment shortens it and preserves the nondecreasing increment order. Removing cardinalities above U is valid because their entire physical intervals are empty. L, all retained physical thresholds on collinear faces, and the final physical horizontal interval are retained in the support statement.
- Strict convexity establishes unique hull load and the value-gap criterion. It does not by itself provide an admissible supply price. The current corollary correctly adds the framework's independent subgradient/dual-attainment qualification. Keep that distinction in abstract/conclusion wording rather than silently strengthening to all strictly convex continuous supply functions.
- Fee zero is a separate boundary case, not an application of the positive-fee open-edge rule. The current text handles it explicitly.

There are editorial consistency defects visible in the current snapshot: main still says the two-batch theorem uses scaled charging resources, while the lead theorem has fixed K/H; numerical qualification statements must also be synchronized only after actual closure. Parent is already correcting the first defect. These do not undermine the proof but can make the paper look internally inconsistent.

## Strongest rejection arguments

**Elementary consequence under tailored assumptions.** A reviewer may accept the theorem and still see a scalar fixed-charge scheduling exercise obtained by composing interval addition, ordered matching and a standard hull argument. Fixed shared resources improve the scope, but simultaneous batches and complete zero-travel crosslinks remove most EVSP difficulty. State the resulting exact mechanism as the contribution; do not imply general scheduling tractability.

**Unestablished practical significance.** Synthetic supply and vehicle fees show possibility and exact regimes, not calibrated relevance. Full replenishment is sound energy accounting, but full charging, endogenous assignment and grid objectives already coexist in prior bus work. A public incumbent's failure of own-price support does not establish failure for the public physical optimum. Current bounds and failed recovery diagnostics cannot supply that missing claim.

**Too many peripheral theorems obscure the strongest one.** The movement-only result preserves a dominated opportunity enlargement; equipment expansion is more informative because it changes the useful frontier. Replication clarifies ownership/scaling but brings different reserved rights and a different supply scaling. Equal abstract weight makes the paper look like a collection of examples rather than a structural classification.

**Institutional relevance remains a modeling choice.** Own-load marginal-price support is a coherent decentralization test. It is not a strategic bus operator's equilibrium, a price iteration convergence theorem, or evidence that a deployed tariff fails. A brief concrete explanation of the diagnostic's role is preferable to broad market-design language.

**No present learning contribution.** The strongest theorem and current evidence are operations-research/energy-market theory. Internal rational verification and native recovery diagnostics do not constitute learning results. An ICML-oriented submission would face a fundamental fit objection without a substantive learning question, method and independently evaluated benefit. Adding an ML label or a small predictor benchmark would not repair that gap. A scheduling/optimization/energy-economics audience is the natural intellectual audience, although significance and operational relevance remain hurdles there too.

## Actionable hierarchy

Lead with the fixed-resource heterogeneous classification and one readable diagram of its clipped cost frontier. Use the two-service region and equipment fee counterexample to explain the mechanism and its boundary. Present movement dominance as a scope lemma and ownership replication as a secondary consequence. Keep public evidence as an explicitly unresolved scale diagnostic, with exact incumbent/hull/global claims separated.

Prefer a title such as **“Assignment-Dependent Charging and Marginal-Price Support in Electric-Bus Fleets.”** The current title is accurate but does not advertise the structural contribution. A concise abstract should state: (i) the complete fixed-resource physical class, (ii) its exact cost-labelled frontier and conditional support criterion, (iii) the capacity/fee/equipment consequence, and (iv) the unresolved public optimum. Classical attribution can be one direct sentence rather than repeated self-assessment.

The most useful additional evidence would be a genuinely admitted global public support/non-support certificate or a clearly bounded analytical extension that breaks a restrictive assumption. Neither is required to state this theorem correctly, and neither should be promised. Further toy-case agreement chiefly qualifies implementations; it does not independently resolve the novelty or significance objections above.
