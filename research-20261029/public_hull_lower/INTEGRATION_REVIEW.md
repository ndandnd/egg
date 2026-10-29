# Source-only hull-lower integration review

Reviewed the new producer.py, worker.py, run.py, PROTOCOL.md and DRAFT LAUNCH.json, with narrow checker/semantic API reads to establish integration contracts. Admission's internal algebra was not re-reviewed. No actual artifacts, packets, computations, imports, tests, hashes, compilation, native calls or commits were consumed or performed.

**Outcome: source integration PASS, subject to parent source/control freeze and ordinary prospective qualification. No clear source bug requiring an edit was found.** DRAFT is not launch authority, and this review supplies no execution authority or runtime qualification.

## Objective and complete domain

Producer prepares a linear checker context with explicit fixed prices and fleet_count=None. Native objective is intrinsic movement/vehicle operations plus those prices times market loads. It uses the existing continuous energy-flow model, retains original movements, the source-derived minimum-fleet cut and original fleet maximum, and adds no exact-two equation or nonlinear higher-fleet floor. Final independent audit reconstructs the same full-domain linear semantics without exclusions. Its certified quantity is V(p); only the separate k+L_V operation supplies a CH lower.

Native row and variable names are drawn from the frozen energy-flow builder; multipliers are checked against independently reconstructed semantic rows, including source-defined branch equality names. The narrow row-family comparison shows matching selection/shared resource, headroom/reserve, start/end inventory, leg/service consumption, fleet coverage and market-load families. The native model represents rational coefficients in floating point, while exact verification uses original rational semantics. This seam is safe for validity: arbitrary native multipliers remain mere proposals, and exact residual/finite-box compensation decides their bound. It may affect strength. No native objective or status is accepted as an exact lower.

## Coverage and failure behavior

The initial zero-multiplier finite-box proof is explicit and source-defined, not fabricated from missing native Pi. Each branch retains both original-binary children. A parent's certificate remains valid in each child because all its branch equalities remain available and new equalities need no nonzero multiplier. Canonical proofs retain all nonzero corrected multipliers, including inherited branch rows. Proof references are expanded only in memory for independent checking.

Exact accepted bounds alone prune at the frozen linear target. Native infeasibility needs an exact positive box/Farkas contradiction; failure retains the inherited bound and explicit open-search state. Budget/node/call limits likewise retain a complete bound fringe, which can yield a valid lower even when it misses epsilon. A complete all-infeasible tree is explicitly rejected as contradicting admitted components. Final semantic audit checks full branch coverage and finite rational lower before admission.close_bound transforms it; a rejected/unresolved audit yields no new global lower. Search completeness, complete bound coverage, epsilon success and exact optimality are kept distinct.

## Admission, clocks and closure

Worker admits own sources, frozen semantic/checker sources and exactly the three pinned case/authority/MIXTURE inputs by cached bytes and immutable path identity. It does not follow metadata paths, reread old physical witnesses, reoptimize mixture weights, audit the old tree, or consume an old root packet. The MIXTURE payload is decoded once transiently for the new metadata transform. Original binary coefficients are source-defined consistently with the frozen market convention; NativeCase identity must match the fixed descriptor token.

All four states remain assigned. Q0 is expressly pure literal algebra/checker qualification with backend_calls=0; neither code nor protocol presents it as a native backend or runtime qualification. The previously corrected rejection wrapper accepts returned REJECTED and admission exceptions, while UNRESOLVED does not count as a successful negative control.

Producer charges model construction within its complete search clock, requires a fully funded next LP/check plus closure reserve, enforces concurrent call/node/time ceilings, and disposes its model inside the producer's final clock. Worker subtracts prior inclusive usage before funding search and reserves the complete final audit/publication allowance. Final context/materialization/check get a bounded window. Resource insufficiency fails closed rather than silently reducing the audit. Stage clocks include compressed publication. The owner includes child wait/reaping, compact result validation, complete assigned ledger, receipts and shutdown under its outer clock; external metering remains authoritative. Resource observations sampled before final writes are not a claim to measure subsequent publication for free—the external complete meter captures it.

The owner handles disappeared process groups, attempts bounded reaping, rejects malformed/incomplete masters and reports unknown rather than inferred progress if the master is unavailable. Observed RSS is a monitored acceptance gate, not a hard allocation limit; hard CPU/outer wall supervision and the declared single native thread remain explicit. No automatic changed-price or native retry exists.

## Freeze recommendations

Parent must fill FROZEN source/control/command/console/external meter fields, preserve the fixed epsilon and exact input paths, and review any later edit before dispatch. The fixed-price goal can intrinsically fail even with an exact oracle; a valid lower with width above epsilon is an informative bounded outcome, not permission for a new price or mixture. This source-only review does not promise that the proposed resource allowance will achieve the goal.

## Subsequent narrow display delta

Reviewed the added worker.outward helper and the three closure display fields. Integer division gives exact floor at six decimals; the negated floor of the negated numerator gives exact ceiling, including for negative rationals. The formatter retains sign and six fractional digits. hull_lower is floored, hull_upper and width are ceiled. All underlying bounds, width and epsilon comparisons remain exact and unchanged. This delta is correct and adds no computational authority; no execution was performed.
