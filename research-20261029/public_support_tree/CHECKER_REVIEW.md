# Independent exact tree checker review

Scoped mathematical/source PASS for the admitted original public-model context and an independently implemented source-bound exclusion callback. Read `checker.py` and, at the parent's request, only the frozen semantic descriptor-validation fields needed to harden the service floor; no broad source/native audit, actual data, imports, hashes, execution, tests or commits. Two new-checker hardening changes below were authorized and reported to the parent. Runtime qualification and controller integration remain separate.

## Exact node certificate

`prepare` reconstructs the semantic finite boxes and original rows through the admitted callback instead of trusting a serialized matrix. Only original movement selection variables with [0,1] bounds can branch. A two-bus equation is explicitly conditional. The context must be newly prepared and remain trusted/unmodified; accepting an artifact-supplied context would invalidate this boundary.

For minimization, residual `c-A^T*pi` with >= nonnegative multipliers, <= nonpositive multipliers and unrestricted equality multipliers has lower bound `constant+pi*rhs+sum min(residual*lower,residual*upper)`. The code implements these signs correctly. Projecting a proposed multiplier onto its valid sign is safe because the residual compensation is recomputed exactly; stationarity need not hold. Unknown or unavailable branch rows are rejected. Missing sparse entries mean explicit zero, while a missing multiplier dictionary is rejected.

The quadratic slope is the exact original binary `a+b*tangent` with constant `-sum b*tangent^2/2`; it is a global convex tangent for any rational proposed load. No feasibility or native optimality of the tangent is required. Linear mode uses the exact supplied vector. For an infeasibility leaf, objective/constant are zero: a strictly positive row-plus-box lower for the zero function proves the node empty. This is an exact finite-box Farkas contradiction, not a native status.

## Coverage and scope

Every branch fixes a previously unfixed original movement to both zero and one. Distinct children, no shared/cyclic/missing nodes, no unreachable nodes and exact inherited decisions make the declared leaves exhaustive over all integral movement selections in the prepared domain. Continuous charging remains in the checked node relaxation; it need not be branched. A leaf can stop without fixing every movement because its relaxation lower applies to all remaining integer completions.

Explicit open leaves prevent complete coverage. The minimum of all bound leaves is a valid complete-domain lower; an all-infeasible tree correctly gives +infinity. Node/depth/checkpoint failure is unresolved and removes the global lower. Complete quadratic trees certify **physical D**, not the unrestricted complete-plan hull CH: branching selects disjunctive physical alternatives and prevents arbitrary mixtures across those branches. Linear trees certify V(p) for their exact frozen price vector. The fields correctly disclaim a CH conclusion and do not authenticate a separately supplied target.

## Exact-two plus typed higher-fleet floor

A two-bus tree becomes global only with a proven minimum fleet at least two and a valid floor covering every count >=3. The combination is the minimum of its two-bus lower and that floor. The source-bound callback must authenticate already cached fixed paths/revisions and same-case authority; returning True based merely on metadata equality is insufficient.

The checker independently reconstructs the correct objective-specific floor. Quadratic mode uses `3*fee+binary_a*service/eta`; linear mode requires the **new exact price vector**, nonnegative prices, and uses `3*fee+min(price)*service/eta`. It rejects a nonlinear floor presented for a linear response. A transferred lower may be weakened but cannot exceed the reconstructed elementary floor. This avoids silently reusing the old nonlinear numerical exclusion at new prices.

Important domain obligation: these service floors require nonnegative bus fee, positive efficiency, and nonnegative omitted movement/waiting costs and energy, together with full replacement-energy accounting. In particular, 3*fee is not a floor for all >=3 fleets if fee is negative. The authorized hardening now checks the exact admitted descriptor schema and graph scope, fee>=0, 0<eta<=1, nonnegative travel cost, each service/leg energy, leg duration and every reconstructed operating-cost coefficient. The known strict descriptor schema has no separate hidden waiting/auxiliary cost fields; any such energy belongs in its movement legs. Unknown/missing schemas or parameters reject exclusion. Full initial/final inventory remains part of the pinned original semantic reconstruction, not something a data-supplied proof record can assert. The current review does not certify arbitrary contexts or arbitrary exclusion callbacks.

## Reporting caution and qualification requirements

A second authorized hardening clears all success-derived global-bound/comparison/exclusion fields whenever the final result is not COMPLETE with complete true. This prevents a late checkpoint or exception from leaving apparent success residue such as positive target excess. Every consumer must still gate **status COMPLETE and complete true plus an actual global bound** before using any comparison. This does not change the node mathematics.

Prospective qualification should reject omitted/shared/unreachable children, repeated branch decisions, wrong inherited branch rows, altered bound/contradiction claims, open coverage and cross-objective/cross-price exclusions; separately exercise resource-unresolved paths. It must authenticate the supplied target and exclusion source outside this checker. No such tests were run in this review.
