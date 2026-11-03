# Heterogeneous two-batch theorem: focused novelty review

29 October 2026. Read current `heterogeneous.tex` and the already reviewed proof candidate. Four focused new primary fulltexts were inspected below; no numerical work, imports, hashes, commits or new agents. No renewed search of the classic pricing papers or Wu2019 routes. This is a bounded comparison, not an absence/first-ever clearance.

## Assessment

The extension gives a meaningful **narrow physical classification**, rather than just another identical-copy example: assignment decisions alter intermediate recharge obligations, all crossmatchings are admitted, and a cost-labelled projected frontier yields an exact support criterion. However, its mathematical ingredients are elementary once that frontier is established. It is not a new exact EV aggregation principle, new matching algorithm, or general marginal-pricing theorem. A skeptical reviewer can still regard it as an application corollary of standard interval aggregation, assignment integrality/value convexity and convex support.

Crucially, **the energy-only aggregate feasible set is already [0,U]**: the zero-matching branch spans it. The structural result concerns the joint `(E,S−E,operating cost)` projection and its cardinality-dependent lower frontier. Describing it simply as a new nonconvex “aggregate-load projection” would obscure the actual contribution and invite unfavorable comparison with much richer exact flexibility results.

## Inspected primary sources

### 1. Mukhi and Abate (2023): exact fixed-population EV aggregation

[An Exact Characterisation of Flexibility in Populations of Electric Vehicles](https://arxiv.org/pdf/2306.16824), Karan Mukhi and Alessandro Abate, arXiv2306.16824 (2023). Inspected §II equations1–5, PDF p.2; §III Theorem1/equations8–10, p.3; Theorem2/equation13, p.4.

Their individual EV has fixed arrival/departure, power bound and a prescribed total charge, explicitly full at departure. Fixed-device flexibility is a polytope; exact aggregation is a Minkowski sum represented using permutahedra. EGG must not claim full recharge, heterogeneous availability or exact aggregation is itself new. The inspected theorem aggregates given EV profiles; it does not optimize the number of buses assigned to paired mandatory services or attach a fee-dependent operating-cost layer. Thus it does not directly supply EGG's matching-cardinality frontier, although interval aggregation at fixed matching is substantially simpler than its multi-period result.

### 2. Mukhi, Loho and Abate (2025 author version): generalized polymatroids

[Exact Characterization of Aggregate Flexibility via Generalized Polymatroids](https://arxiv.org/html/2503.23458v2), Karan Mukhi, Georg Loho and Alessandro Abate, arXiv2503.23458v2,17 June2025. Inspected §II-A equations1–4/Definition1, §III-B Theorem2/equation14, §III-C Theorem3/equation15 and §III-D EV specialization/equation16. HTML theorem identifiers are verified; no journal-page numbers are asserted.

Their given individual power/cumulative-energy constraints define compact convex sets; Theorem2 identifies generalized polymatroid structure, and Theorem3 exactly aggregates by summing set functions. The paper explicitly focuses on convex individual consumption sets. EGG's useful difference is endogenous assignment/cardinality with fixed operating fees, not a better general load-flexibility representation. For each fixed matching, EGG's interval can be understood within established convex flexibility logic. The union of cost-labelled assignment layers is the part requiring its physical assignment argument. No direct matching/support theorem overlap was found in these inspected sections; this is not a claim about every result in the broader literature.

### 3. Borndörfer et al. (2024): assignments, resource coupling and flow/path integration

[Solving the Electric Bus Scheduling Problem by an Integrated Flow and Set Partitioning Approach](https://drops.dagstuhl.de/storage/01oasics/oasics-vol123-atmos2024/OASIcs.ATMOS.2024.11/OASIcs.ATMOS.2024.11.pdf), Ralf Borndörfer, Andreas Löbel, Fabian Löbel and Steffen Weider, ATMOS2024, article11. Inspected §2–2.1, printed pp.11:3–11:5, flow constraints1–6 and battery extension7–15; path formulation16–21 at11:6; decomposition27–31 at11:11.

This directly establishes that service assignment, battery feasibility, charging slots, vehicle mix and integer flow/path formulations are mature electric-bus modeling territory. EGG cannot treat exhaustive trip assignment or joint charging feasibility as a standalone methodological advance. The inspected framework tackles richer real scheduling through optimization rather than deriving EGG's two-batch scalar frontier. No matching-threshold support criterion appears in the inspected formulations. EGG's restricted simultaneity/zero-travel/scaled-capacity assumptions buy analytical tractability; they do not supersede this operational model or establish scalability beyond it.

### 4. de Vos, van Lieshout and Dollevoet (2022 author version): partial charging and fixed vehicle costs

[Electric Vehicle Scheduling with Capacitated Charging Stations and Partial Charging](https://arxiv.org/pdf/2207.13734), Marelot H. de Vos, Rolf N. van Lieshout and Twan Dollevoet, arXiv2207.13734v2, manuscript dated1 August2022. Inspected §2, printed p.4; §4.1, pp.8–9; §4.2.1/4.2.3 on pricing/valid lower bounds, pp.10–16. Version title differs from later journal wording; references should identify the inspected version.

Its model already includes heterogeneous vehicle types, partial charging, station capacity and fixed investment plus operational cost. Paths encode service choices and recharge actions. Conservative discretization omits some physical duties, while an optimistic dual network supplies valid underlying lower bounds. This is operationally adjacent rather than an exact scalar projection/support theorem. EGG's complete continuous two-batch classification avoids a discretized plan bank but covers a vastly narrower class. Fixed vehicle fees and charging-dependent assignment themselves are not new. Do not claim superior computational efficiency from having closed formulas under those restrictions.

## Exact overlap versus standard corollary

The fixed-matching physical interval follows by summing independent early-charge intervals and serially realizing terminal demand. That is elementary aggregation, not a new polyhedral family. The nontrivial application work is proving that these independent intervals and terminal groups really exhaust the declared fleet under all matchings and do not omit shared-resource constraints.

The r_m discrete convexity is standard bipartite min-cost-flow value-function reasoning. The interpolated lower cost boundary then follows from the affine vehicle fee and convex threshold sequence. Once that boundary is known, “gap0 exactly at physically attained hull minimizers” is an instance of the existing support/convexification framework. The theorem's contribution must be evaluated as the complete composition of those facts for this physical class, not as each fact separately being new.

No directly identical complete cost-labelled matching projection/support classification was verified in the four inspected sources. That supports a tentative precise distinction, not a declaration of originality. A broader search of fixed-charge assignment energy models could still reveal the same reduction.

## Additional classical structure: own algebraic observation

There is more structure than the current generic matching presentation reveals. Sort A and B energies increasingly. Since `[a+b−20]_+` is nondecreasing in each argument, an optimal size-m matching can select the m smallest A and m smallest B energies: replacing a selected larger energy by an unused smaller one never increases any edge requirement.

For a≤a' and b≤b', convexity of the positive-part function gives

    [a+b−20]_+ + [a'+b'−20]_+
       ≥ [a+b'−20]_+ + [a'+b−20]_+.

This inverse-Monge exchange inequality implies that opposite ordering of the selected energies minimizes the sum. Hence a candidate simplification is

    r_m = Σ_(i=1)^m [a_(i)+b_(m+1−i)−20]_+,

where a_(i),b_(i) are increasing order statistics. This is a direct proof observation, not a numerical result or a claim of a novel matching theorem. It should receive separate mathematical review before manuscript insertion. I also consulted a Burkard–Çela assignment exposition for the standard inverse-Monge convention, but do not use that secondary exposition as one of the four primary novelty comparisons.

This does not invalidate EGG's matching formulation; it makes the strongest novelty objection sharper. Complete crossmatching choices matter physically, yet their optimization is highly ordered under the exact positive-part energy formula and all-crosslinks assumption. Do not suggest generic hard matching structure is what makes this theorem significant. A useful improvement would expose the ordered structure transparently and explain why fixed-charge cost layers still create the support obstruction.

### Follow-up proof check of the sorted-threshold corollary

The displayed corollary is valid for complete crossassignment. For fixed m, replace any selected A energy outside the m smallest by an unused smaller energy while retaining its partner; coordinatewise monotonicity cannot increase cost. Repeat on B. Hence some optimal matching uses precisely the m smallest members of each list (ties arbitrary).

Write h(t)=[t−20]_+. For a≤a' and b≤b', put d=a'−a≥0. Convexity makes h(t+d)−h(t) nondecreasing in t; apply it at t=a+b and a+b'. Rearrangement yields h(a+b)+h(a'+b')≥h(a+b')+h(a'+b). Whenever two partners are ordered in the same increasing direction, swapping them does not increase cost. Repeated exchanges produce opposite ordering. This proves the threshold formula, including ties and zero-cost edges; it is not restricted to all-positive costs.

The literature convention is described in Burkard and Çela's author exposition, [Linear Assignment Problems and Extensions](https://www.andrew.cmu.edu/course/42-731/handouts/Burkard_LAP_review.pdf), printed p.9, equations8–10: inverse-Monge matrices admit an opposite-order optimal assignment. This is an attribution aid for classical assignment structure, not evidence that EGG's physical frontier was previously proved. The direct argument above avoids relying on that secondary exposition for the new application claim. The four primary EV/bus sources remain the bounded application comparison.

The parent's proposed single shared early/terminal power generalization has not been proved or qualified in this review. Its suggested interval must be checked against release windows, per-bus acceptance and terminal serialization; no manuscript edit or extension validity is inferred here.

## Defensible claim and significance bar

Suggested claim:

> “For heterogeneous services in two simultaneous batches with complete zero-travel crossassignment and the stated charging resources, we derive the exact load–vehicle-cost projection, its lower convex boundary and a necessary-and-sufficient own-marginal-price support criterion. The physical realization and assignment-dependent recharge thresholds specialize established aggregation, matching and nonconvex-pricing ideas.”

This is stronger and more accurate than “we exactly aggregate heterogeneous EV flexibility.” It is also narrower. The paper should make visible which resource assumptions allow n independent early decisions and n serial terminal groups; shared bottlenecks or missing/time-dependent crosslinks change the projection.

The strongest rejection remains that the class is deliberately structured enough for elementary projection and scalar convex minimization, and the known support theory then does most of the economic work. The new heterogeneous theorem helps by admitting assignment choices that genuinely alter recharge needs, but it does not alone establish practical consequence, general-EVSP tractability, new market design or operational prevalence. Public-case certificates remain complementary scale evidence, not empirical validation of this exact two-batch class. No absence/first-ever language is warranted.
