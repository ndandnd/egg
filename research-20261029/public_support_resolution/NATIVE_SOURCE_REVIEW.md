# Native probe: independent source-only review

29 October 2026. Read `native_probe.py`, the needed `native_pathflow.build_feasible_model`/`recover_paths` source and relevant `native_recharge` API definitions. No module import, execution, test, compile, hash, data read or native solve was performed. This is a source review, not backend qualification.

## Scoped conclusion

**Translation and objective construction look coherent for native diagnostics, with the limitations below.** This does not qualify physical/exact bounds or approve unattended use as a hard-deadline/certificate harness. Parent protocol should explicitly address no-optimize outcomes, per-round evidence and certificate reconstruction.

### Translation and objective: scoped pass

- Source Python-MIP normalized linear expressions are copied as coefficients plus constant, compared with zero using the original sense. This agrees with the assembly in `native_pathflow`; variable indexes are used consistently for movement, SOC, load and charge mappings. The source model remains attached.
- Integer variables become continuous with original bounds in relaxation mode. No selected-column or bus-count restriction is introduced: the source's complete compact movement graph and maximum-vehicle inequality are retained. “All bus counts retained” means those allowed by the supplied case, not unlimited buses.
- Operations come from the source expression. MIQP uses `ops+sum(aL+bL²/2)`; OA uses valid tangents to that same convex separable cost. Defaults a=.2 and b=1/900 give the manuscript's L²/1800 convention. Linear pricing uses `ops+p·L`.
- A movement-only MIP start validates complete path-cover structure through `recover_paths`; it does not validate battery/charging feasibility or prove start acceptance. The explicit UNKNOWN acceptance label and UNDEFINED remaining start values are appropriate.

## Material caveats to resolve or freeze in protocol

### 1. No-optimize/deadline exhaustion is not a first-class result

`_optimize` returns False when the inclusive deadline has elapsed. MIQP and pricing ignore that Boolean and still call `_extract`; OA can likewise call final extraction after adding a new cut but skipping the next optimization. The code does not explicitly distinguish an unsolved model, the last optimized matrix and a matrix modified since its previous solve. Gurobi attribute availability/solution invalidation after pending modifications is not qualified by this source review.

**Required handling:** return an explicit no-optimize/deadline-exhausted outcome, and retain the last actually solved snapshot independently of later matrix changes. Never interpret a last raw status as a solved final model if that model was modified afterward. This also avoids an unhandled attribute-access failure replacing a useful completed round.

### 2. The inclusive time cap is advisory rather than a hard whole-call bound

The timer starts before backend imports/build, which is good, and each solve receives the remaining budget. However, imports/build, objective/cut attachment, callbacks, extraction and JSON writing cannot be interrupted by that native TimeLimit; extraction may be substantial. There is no final deadline enforcement, external owner timeout or disposal/resource guard here. `inclusive_elapsed_s` measures through extraction but is computed before finish-event logging and output writing, so it does not cover the full function call.

**Protocol implication:** use an external owner deadline/resource guard and account for finishing/output time separately. Do not claim `seconds` guarantees total wall time or exact aggregate containment.

### 3. OA round evidence lacks status and candidate provenance

Each round event saves upper/best-upper/best-bound but not that round's native status, solution count, runtime, bound, gap or snapshot. Only the final extraction has raw native fields. The retained best candidate is not labeled with its generating round. If later rounds time out or lack candidates, final raw fields need not describe the retained best candidate. Raw OA objective/gap concern the piecewise-linear relaxation, not the original quadratic objective.

**Required reporting:** retain compact per-round raw solver fields, the round of the best candidate and a clear last-solved snapshot. Use `best_evaluated_upper` and `best_native_lower` for the nonlinear diagnostic interval; never promote raw OA OPTIMAL or raw MIPGap to quadratic optimality. A negative numerical upper-minus-lower is not presently checked for contradiction before the stop condition.

### 4. Continuous exports are diagnostic ingredients, not certificates

For optimal continuous solves, Pi/Slack and RC/bounds/value/linear objective are exported. These are appropriate QP/LP ingredients. The result also includes the market coefficients. However, `source_linear_rows` contains only the original translated constraints: any OA cuts are absent. For a QP, the quadratic objective is not an explicit Hessian indexed against the exported variable names, and the semantic mapping is not self-contained in this output. It can be reconstructed using source order and market/load fields, but that is a separate verification obligation.

**Protocol implication:** if rational certificate reconstruction is intended, preserve the exact solved matrix/objective mapping, including load-variable indexes, every OA cut if applicable, objective constant and quadratic coefficients. Check stationarity, dual signs, complementarity, bounds and primal/dual objectives independently in the intended arithmetic. Continuous fractional selections thresholded at .5 are not physical movement candidates. The code's `physical_feasibility='unverified'` and `exact_certificate=False` correctly prevent that promotion.

## Additional scope observations

The probe intentionally bypasses native_pathflow's normal charge projection, physical decoding/replay, completion and bound-admission policies. It exports raw solver variables. Thus path recovery alone cannot turn a numerical candidate into an operational or ideal-model witness. This is acceptable only with the disclosed diagnostic label and separate later admission. Source construction also calls the existing backend identity path; its behavior and any build overhead remain part of a prospective execution, not something tested here.

No definite coefficient/sign mistranslation was found. The most consequential source issues are robust treatment of a skipped optimize and preservation of solved-round provenance; the largest interpretation risk is conflating native compact-relaxation or OA status with a complete-fleet hull/physical certificate.
