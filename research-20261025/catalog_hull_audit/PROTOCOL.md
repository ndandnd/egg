# Observed-catalog convex-hull diagnostic

Static prospective protocol, 25 October 2026. Parent review and an explicit metered command precede execution. No result or passed flag is asserted here.

## Inputs and finite scope

Read only `research-20261025/price_signal_audit/results.json` and this script/protocol. Require the price audit's successful admission of all 342 replay-valid development endpoints in the original twenty timetable groups (ten 40-trip, ten 80-trip groups). Do not read raw task results, solver/model assets, new timetables, sealed sources or GIRO sources. Hash those three consumed files once, inside this process. Preserve the upstream audit hashes as inherited provenance, without rereading their files.

Within each case, pool all admitted arms and seeds, choose the **minimum observed fleet count**, and deduplicate exact `(ops_cost, load[30])` pairs. Retain all original directory/arm/seed aliases. Numeric rows reconstruct the original binary64 values with `Fraction.from_float`; tariffs and the original scalar curvature reconstruct the upstream rational strings. These are hindsight, fixed-plan banks with fixed charges; the chosen fleet need not be globally minimal, and deduplication does not recover unseen schedules.

Use the upstream `day` and `late` linear tariffs (stored binary64 0.1/0.3 represented exactly), and curvature multipliers **0, 1, 5** times its stored original binary64 `1/900`. Only curvature changes. Loads, energy, routes, infrastructure and fleet costs remain the observed values. This produces **20 × 2 × 3 = 120 catalog cells**. The upstream audit already contains same-bank system-cost versus uniform-price-payment comparisons for original curvature, for both tariffs and both fleet scopes; reference them, and do not count them as a new result.

## Frozen optimization and exact checks

For bank rows `(c_j,L_j)`, minimize

`F(lambda) = c @ lambda + a @ (lambda @ L) + (b/2) ||lambda @ L||^2`

over the simplex. At `b=0`, select the exact minimum vertex analytically. At positive curvature, make **one SciPy SLSQP call** from the uniform simplex point, with analytic objective gradient `c + L @ (a + b*(lambda @ L))`, equality `sum(lambda)=1`, bounds `[0,1]`, `maxiter=300`, and `ftol=1e-12`. No retry, restart, alternate solver, adaptive tolerance or parameter search. Preserve its actual status/message/iterations and any exception. A non-success status remains a recorded failure even if its candidate admits a tight exact bound.

Clip returned finite weights at zero, normalize in binary64, convert every normalized weight with `Fraction.from_float`, then **renormalize exactly**. This gives a truly feasible rational mixture, independent of SLSQP's feasibility tolerance. Preserve the raw weight extrema and clipping count. Let exact `Lbar=sum(lambda_j L_j)`, `cbar=sum(lambda_j c_j)`, and `U=cbar+S(Lbar)`, where `S(L)=a·L+(b/2)||L||²`. At positive curvature set

`p=a+b*Lbar; eta=min_j(c_j+p·L_j); LB=eta-sum_t((p_t-a_t)^2)/(2b)`.

At zero curvature use the exact linear minimum, so `LB=U=best_pure`. Every feasible mixture gives a catalog upper bound; the displayed tangent/conjugate expression gives a catalog lower bound. Verify with exact rational arithmetic for **every bank row**:

`pure_cost_j-LB = (c_j+p·L_j-eta) + (b/2)||L_j-Lbar||²`.

Also verify exact Jensen identity

`sum_j lambda_j*pure_cost_j-U = (b/2)sum_j lambda_j||L_j-Lbar||²`.

Report `[best_pure-U, best_pure-LB]` and its division by positive `best_pure` as the **catalog pure-minus-hull optimum gap interval**. A negative lower endpoint is permitted when the candidate is poor; do not relabel it as an observed improvement. Report support, aliases, rational mixture/load/price, LOC values and variance. Mark `numerical_catalog_qualification` exactly when `U-LB <= 1e-6*(1+abs(U))`; this exact inequality qualifies only this finite-catalog numerical optimization. Retain the optimizer status independently.

Describe the bank's load variation by SVD of binary64 rows `L_j-L_0`: numerical rank at `max(shape)*eps*sigma_max`, dimensions reaching 95% squared-singular-value energy, and entropy effective rank using squared-singular-value shares. These are descriptors, not physical latent dimensions or proof of structural low rank. A singleton/identical-load bank reports zero rank.

## Limits and failure preservation

Body CPU limit **60 seconds**, body wall limit **90 seconds**. Allow up to ten seconds startup and five seconds final publication, within a **75 CPU / 105 wall second total-process cap**. Install CPU soft/hard limits 70/75 and a wall alarm at 105 before numerical imports; callbacks, objective/gradient calls, SVD boundaries and exact loops check body deadlines. Set BLAS/OpenMP thread environment variables before NumPy/SciPy imports and require `threadpoolctl` to enforce and inspect one native computation thread per loaded pool; require one Python thread. No child processes or subprocess calls. Dependencies are NumPy, SciPy and threadpoolctl; missing dependencies produce failure, not installation or fallback.

Output is exclusively created (`--output`, no overwrite). Include consumed-file hashes, inherited input hashes, admitted and deduplicated denominators, all completed/failed cell records, unprocessed cells, actual self/child resource receipts, body/startup timing, and scope flags. The receipt's self timing ends before encoding/write/exit; the parent's process meter must charge publication and exit. A hard OS kill can prevent a complete local receipt; retain that as an external failure, never infer success. No automatic rerun.

Prospective command from the worktree root, subject to parent review:

```
python research-20261025/catalog_hull_audit/analyze.py --output research-20261025/catalog_hull_audit/results.json
```

The convex identities are classical. Fractional mixtures are mathematical catalog relaxations, not implementable fractional fleets. Results cannot establish full-problem bounds, a full-price certificate, equilibrium, tariff causality, learned-policy value, ML generalization or a novel theorem. Fleet selection and pooled historical plans can hide alternatives. No execution of the scheduling owner, solver, model or replay is performed.
