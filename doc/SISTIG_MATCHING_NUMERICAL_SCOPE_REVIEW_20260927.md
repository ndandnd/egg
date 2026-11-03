# Independent review of matching-bound numerical scope

27 September 2026. **PASS for the stated relationship between the exact matching relaxation and the intended physical model.** This is a narrow semantic/code review, not the full assignment-algorithm/reduction preflight assigned to another reviewer. No public-case matching calculation, optimizer execution or scientific source edit was performed.

The candidate constructs each movement cost from the exact rational sum of individually stored leg energies and exact leg-duration differences. Service energy is likewise summed as exact stored numbers. The scalar price and efficiency are interpreted as exact rational values of the saved inputs, including binary float 0.2 rather than silently replacing it with 1/5. Under ideal full initial and terminal SOC, total charging energy is exactly total selected consumption divided by efficiency. Consequently the additive path-cover cost is the objective of a relaxation of that ideal physical problem.

The relaxation retains every service and the declared directed movement alternatives, permits independent cheapest valid endpoint/parallel-mode choices, and explicitly drops battery/reserve, charge availability, shared resource and maximum-fleet constraints. Those choices can create physically impossible paths; that does not invalidate the lower bound. Positive-duration service timing and validated chronological movements give a DAG, preventing a fully matched cycle without depot endpoints. The output correctly calls its selected path count a relaxation count rather than a feasible bus requirement.

The candidate's arithmetic differs deliberately from the native formulation. Native movement SOC rows use rounded per-mode leg sums; pullout/terminal and big-M expression constants incur additional rounding. Native objective assembly, solver feasibility/integrality tolerances, session normalization and physical replay also have their own numerical policy. Therefore an exact assignment primal/dual certificate establishes an exact lower bound for the stated ideal model, not automatically for the exact binary native matrix or every tolerance-admitted native incumbent.

The prospective protocol states this distinction correctly. It keeps ideal lower bounds separate from saved numerical native endpoints, and forbids treating close agreement with a tolerance-conditional physical witness as an exact ideal optimum. A future combined enclosure would need an exact physical feasibility/objective witness or an independently justified propagated bound between the models. The proposed aggregate-energy band alone does not establish all such objective, constraint and solver-tolerance relationships. No automatic replacement of a native lower endpoint is justified by this review.

The source returns the case identity, exact flat price, explicit interpretation, exact baseline/service constant, selected movement IDs and exact assignment certificate. The full-algorithm reviewer should independently verify the assignment certificate and baseline reconstruction; this note does not substitute for that review or the later public-result audit.

One wording refinement was sent to the principal researcher: “pinned EGG-modeled energy inputs” is clearer than “published modeled energy inputs,” because the adapter derives energies from source distances/times and assumptions rather than publisher-observed service energy. This wording does not affect the reduction.

## Inspected candidate hashes

- `src/egglab/flat_energy_relaxation.py`: `5f3e9e2047abc1b4af586b062966334ae737fae2cb0d5cbea98a87a6026b71cb`
- `doc/SISTIG_MATCHING_PROTOCOL_20260927.md`: `4783e18ba1af6594845e3b95adad1569106453719a3c20fd20838880d66635f6`
- `src/egglab/native_recharge.py`: `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`
