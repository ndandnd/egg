# Final significance referee: source-only assessment

Date: 29 October 2026. This is a fresh, skeptical assessment of the scientific narrative, not an independent certificate check or a novelty clearance.

## Verdict

**Suitable to circulate as an explicitly qualified independent-review copy; not established as submission-ready.** I see a coherent, potentially useful restricted optimization result. I do **not** presently see a sufficiently established ICML contribution. My likely ICML recommendation on the evidence in these sources would be reject for uncertain significance/novelty and weak venue fit, rather than for a demonstrated mathematical error. An optimization or energy reviewer could reasonably find the exact characterization interesting, but could also regard it as a specialized synthesis of standard tools whose practical reach remains unproved.

This judgment does not infer that the result is already known. The supplied literature discussion establishes substantial overlap with cost-aware aggregation, integrated assignment/charging, V2G and nonconvex pricing. It neither establishes nor excludes prior subsumption of the narrower replacement theorem. That question remains open.

## Scope and evidential status

I read `main.tex`, `related_work.tex`, `framework.tex`, `core_results.tex` and `INDEPENDENT_REVIEW_BRIEF.md`, then the complete projection proof in `full_lossy_projection.tex` and the setup approximation in `setup_time.tex` to assess the role of the ideal action assumptions. I did not survey new literature, inspect or execute certificate machinery, inspect raw data, compile, solve or run experiments. I did not independently verify the public-case bounds, the edge-task robustness construction, or all appendix consequences. Source references below refer to this draft, not independently established external facts.

The reviewed theorem and its proof support my provisional assessment that the central mechanism is coherent. This is weaker than a complete mathematical certification. Prior internal reviews and implementation checks are not premises of my novelty or significance judgment.

## Strongest precise contribution

The strongest claim is **exact replacement across service assignments at fixed fleet cardinality**, not the marginal-price support equivalence and not the five-vertex count by itself.

For the stated two-batch class, set

\[
r_m=\min_{|M|=m}\sum_{(i,j)\in M}(a_i+b_j-B)_+.
\]

At fixed cardinality, total service consumption, the sum of net-exchange lower endpoints, the sum of upper endpoints, and the vehicle fee are invariant across matchings. Assignment changes only the mandatory positive early requirement. A minimum-`r_m` matching therefore realizes the **entire** purchase/export polygon of every other matching of that size, at the same aggregate loads and fee. The interval allocation and finite neutral-cycle construction establish physical realization, rather than a formal relaxation that silently permits simultaneous charging/export. The union over cardinalities retains the assignment/vehicle-cost tradeoff. See `core_results.tex:39–87` and the proof of Theorem `thm:fulllossyprojection`.

That is a sharper statement than preserving a particular monotone optimum. It supports arbitrary objectives on the declared aggregate quantities, and supplies a compact exact description of both physical alternatives and their complete-plan hull. The result can replace a potentially large union over assignments by one matching statistic and one polygon per cardinality. This is a genuine mathematical consequence if the theorem is correct and distinct from prior work.

However, the small polygon size follows directly from five planar halfspaces; it is not an independent source of scientific depth. Matching, box aggregation, time sharing and convex-hull support remain classical, as the draft itself correctly states. The proof's main conceptual step is identifying the matching-invariant quantities and showing that only one assignment statistic survives the projection.

## Likely grounds for rejection

1. **The remaining novelty may be judged too narrow or routine.** Once the endpoint boxes and common-window assumptions are written down, the replacement follows from scalar interval allocation and the fact that the other aggregate bounds are fixed. The paper needs an external judgment about whether identifying and physically realizing that structure is a substantial new theorem, rather than treating its absence from the cited discussion as evidence of novelty. The Müller comparison is candid, but a fixed-population versus assignment-dependent distinction alone does not prove that existing aggregation machinery fails to imply the result after an appropriate formulation.

2. **The assumptions remove much of the operational scheduling difficulty.** Common windows, common capacity/efficiencies and full connector availability make serial aggregate-energy allocation possible. Zero transition resources and equal per-bus fees produce the matching invariants. Arbitrary finite, free direction changes permit the full cycling polygon. These assumptions are stated honestly; honesty does not by itself establish consequence. The setup result is conditional on a positive-slack anchor in every relevant nonempty layer, and the paper explicitly shows that an arbitrarily small setup can destroy a layer without that condition. Thus it does not yet establish general operational robustness of the exact reduction.

3. **The support-failure message is largely inherited from established nonconvex pricing theory.** The framework carefully distinguishes complete-fleet fixed-price response from tariff-reset strategic behavior, which is scientifically sound. But positive `D−CH` as an obstruction is classical. The exact physical characterization must carry the novelty burden. A larger inventory of support examples, ownership cases or certificates does not automatically increase that burden's satisfaction.

4. **The richer public case does not validate the central reduction's practical usefulness.** Its varied timetable lies outside the exact common-window theorem; its two charge-only consumption laws, synthetic economics and separately scoped certificates support a model-specific existence claim. They do not demonstrate that the new polygon reduction solves realistic instances, that the obstruction is prevalent, or that the monetary magnitude matters. Exact certification strengthens trust in the declared example; it does not establish operational importance or the novelty of the analytical theorem. The manuscript now makes these distinctions explicitly (`core_results.tex:132–155`).

5. **ICML relevance is unestablished.** There is no learning problem, statistical result, learned decision rule, learning-enabled optimization result or demonstrated ML consequence in the reviewed narrative. Mathematical optimization can be relevant to ICML, but the sources supply no substantive connection here. A conventional solver or a learned proposal generator would not by itself change that assessment. This is a venue/significance concern, not a claim that the optimization result lacks all scientific value.

6. **The narrative has competing centers of gravity.** The title and opening motivate marginal-price support, the strongest new theorem describes a physical projection, and substantial space is devoted to public-certificate trust and boundary examples. The current text does connect them logically. Still, an independent reader may finish convinced that several carefully scoped statements hold without seeing one compelling new scientific lesson. The clearest center is: precisely when can all assignment alternatives be replaced by one matching per cardinality, and what does that replacement enable that prior formulations did not expose?

## Concrete coherence findings

**No demonstrated central inconsistency in the scoped read.** The proof accounts for gross connector use, full replenishment, SOC-feasible serial actions and lossless degeneracy. The support statement retains price/admissibility and qualification requirements. The public numerical gap is described as a lower bound on a separation, not an exact hull value. The two public energy laws are expressly distinguished. These are positive source findings, not proof that every appendix is correct.

Two small clarifications are warranted before handoff:

- `core_results.tex:5–12` says that A services are “in [0,1]” and B services “in [2,3]”, then declares a partial matching to use `2n−m` buses. State explicitly that same-batch chaining is excluded, or that services occupy their whole batch interval. If “in” were interpreted as arbitrary contained intervals that can be chained, that fleet count would not follow. I read the intended model as the stated matching class, so this is an ambiguity rather than a counterexample to that class.
- The brief still says PDF11 is pending and asks the parent to confirm final build correspondence. The parent supplied PDF11 as the reviewed artifact. Update the brief's build-status sentences to the parent's verified final status before circulation. This is a handoff inconsistency, not a scientific flaw.

The word “independently” in the public-result section should continue to be read with the explicit author-run qualification. The manuscript's final evidence paragraph already supplies that qualification. None of the local exports should be described as third-party replication.

## Minimum missing evidence that could change the judgment

For **novelty**, the minimum is a targeted, technically explicit comparison against the nearest aggregation and integrated-scheduling results: identify the exact hypotheses/conclusions that differ, and test whether the replacement theorem follows by a short specialization or extended formulation of those results. A concrete counterexample to a tempting fixed-population reduction could clarify the distinction; it would not alone establish novelty. Independent expert assessment of that comparison would be materially more valuable than another internal implementation check.

For **optimization/energy significance**, one convincing additional consequence could suffice: a nontrivial planning/pricing conclusion made transparent by the replacement theorem, or a useful extension/validated regime showing that realistic positive setup or window variation still admits a meaningful reduction. The existing compact representation is already such a candidate computational consequence, but its advantage and relevant use case are asserted rather than demonstrated against the nearest alternative formulations. The paper need not promise general scheduling; it needs to show why this exact restricted class matters.

For **practical robustness**, a quantitatively nonvacuous application of the stated slack-anchor bound to a relevant common-window setting would be evidence. The present conditional theorem and discontinuity example are analytically informative, but establish neither an operationally useful setup allowance nor prevalence of the required anchors. A positive gap in the separate synthetic public model does not fill this gap.

For **ICML**, changing my view would require a substantive learning question and result whose scientific content depends on the new structure. That would be a meaningful addition to the research, not a framing edit. It is not a prerequisite for a credible optimization/energy paper.

The appropriate next use of this draft is therefore independent mathematical and novelty review with the narrow replacement theorem identified as the contribution under evaluation. Its careful limitations make that review possible; they do not yet settle significance or submission readiness.

## Addendum: focused Müller comparison

I subsequently read only `MULLER_SUBSUMPTION_ANALYSIS.md`, as requested; I did not reread the primary paper or other draft sources for this addendum. Accordingly, I assess the note's logic, conditional on its source descriptions, rather than independently validating its quotations or coverage.

**The note does not overclaim novelty or non-subsumption.** It correctly separates representability of the scheduling problem, fixed-matching aggregation/disaggregation, and the stronger assertion that one matching's entire physical polygon contains every other matching's polygon at the same cardinality. Its concessions that Müller permits resource populations to be updated, that fixed-matching interval aggregation directly overlaps, and that ordinary extended formulations can encode endogenous duties prevent an artificial novelty claim based on a rigid reading of “fixed population.” The equal-summed-interval example appropriately illustrates information lost by a net-interval-only substitution; the note expressly avoids presenting it as a counterexample to Müller's full framework.

The safe conclusion remains the note's epistemic one: **direct subsumption has not been established by this comparison**. The fact that aggregation formulas do not *by themselves* prove the replacement identity does not establish that the identity is difficult, original, or not a short consequence of a different known theorem. Preserve that qualification wherever the comparison enters the paper. The note's last paragraph already does so.

This is a meaningful improvement on the targeted comparison requested above: it isolates the exact unresolved bridge instead of relying on the label “assignment-dependent.” It does not change my significance or ICML assessment. Expert scrutiny of the bridge and a compelling consequence/useful regime remain more consequential than further internal verification. The parent reports that the same-batch wording and brief's PDF pointer have been corrected; I have not rechecked those source edits, and final PDF correspondence remains the parent's responsibility.
