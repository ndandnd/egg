# Condensed core/main review

Mathematical content PASS, with three small hypothesis clarifications recommended for the core to stand alone. Reviewed `core_results.tex` and changed `framework.tex` against the already reviewed complete-projection theorem and critical evidence scope. No raw artifacts, source audit, execution, imports, tests, hashes, computation or shared-TeX edits occurred.

## Clarifications for the parent

1. Explicitly state that services are indivisible NONCHARGING intervals with nonnegative draw throughout. Positive total “battery demands” and the specified charging windows suggest this, but the endpoint-SOC proof relies on it; intra-service regeneration or additional access would be a different model.
2. Explicitly call terminal access CHARGE-ONLY. “Terminal charging” and the formula for terminal purchases imply it, but allowing terminal exports/cycles would enlarge the complete projection. Early bidirectionality must not be read as applying to terminal actions too.
3. State that planning/support conclusions assume at least one W_m is nonempty. The set-equality theorem correctly permits empty polygons and even an infeasible union; the framework's nonempty compact-image assumption supplies the planning hypothesis, but repeating it here avoids confusion in the standalone summary.

These are premise clarifications, not corrections to the polygon formula or proof. They were sent to the parent before this note; no shared source was edited.

## Verified core statements

The five halfspaces, fleet/cardinality counts, arbitrary allowed graph with standalones, efficiencies, full replenishment, zero auxiliary/reserve, shared gross power and exact cost image agree with the complete theorem. R_m is the minimum summed positive early battery requirement. The proof sketch retains the indispensable nonempty-bus/B>0 finite-cycle construction, boundary inventories, common full-window availability, zero switching/session/cycling restrictions and zero-power cases. Minimum-R matching contains all other same-cardinality polygons at the SAME C,X and fee, hence establishes full equality rather than monotone dominance. At-most-five-vertex and exact convex-hull statements include lower-dimensional/lossless images. The finite-cycle assumptions are prominent, and signed objective domains/background translation are explicitly required.

The summary correctly separates full polygons from the monotonicity-dependent efficient set, exact vertex convexification from the failed fractional-cardinality shortcut, common transition totals from arbitrary edge-dependent consumption, and affine wear/directional-power extensions from the base theorem. Relative robustness remains conditional on fixed topology/timing/access/physics; no universal radius or operational claim appears.

The changed framework correctly defines complete-plan mixtures, one complete-fleet participant and fixed posted prices. It permits signed net loads while charge-only variants restrict their physical loads. The unrestricted quadratic gradient convention at zero removes an economic ambiguity: orthant normal vectors are not additional generation-price choices. The subgradient/support statement, qualified hull-dual attainment and restricted admissible-price caveat remain consistent; positive gap excludes every admissible own-load support, while equality's converse requires the stated price qualification. Nonsmooth prices retain their existential quantifier.

The public summary distinguishes original binary consumption on a declared graph from the newly certified exact-additive paired-arc/wait model. It says both certificates have coincident conservative decimals but no automatic feasibility/certificate transfer; exact physical/hull optima remain unknown. Physical lower versus feasible mixture upper is clear. The larger-walk conclusion retains triangle/common-access premises and is not empirical road completeness. Synthetic economics, charge-only scope, no public V2G and no calibrated-prevalence/savings claim are preserved, with full model/certificate references. No evidence or reproducibility scope conflict was found.
