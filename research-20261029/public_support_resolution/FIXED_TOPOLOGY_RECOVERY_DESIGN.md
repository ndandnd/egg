# One-face exact fixed-topology charging recovery

29 October 2026. Source-only design and implementation candidate; not executed or qualified. The new module is `exact_fixed_topology.py`. It imports only Fraction and time; no backend or source model is imported implicitly.

## API and semantic inputs

`problem = build_problem(case_dict, selected_movement_ids, semantic_reconstruct)`

The callback is the cached `exact_dual._reconstruct`. It validates the complete original descriptor and supplies its exact elementary interval indices/capacities. The helper recovers the complete selected path cover and constructs a **charge-only** QP: one q for every selected visit/eligible positive-capacity interval, finite bounds 0<=q<=cap, all shared interval capacities, every original inventory prefix, and separate full-refill equality per bus. Prefix inventories are `B-consumption_so_far+eta*sum(previous_visit_charge)`. Nonnegative travel/service draw and monotone charging make pre/post-visit and per-leg/service checks sufficient; there is no guessed continuous SOC state and no omitted prefix.

Loads are exact linear sums of q by market period. Operating cost is fixed for the topology. The Hessian is implicit: H_ij=b_t for allocations sharing period t, zero otherwise. No dense full-graph SOC/y matrix is solved. This problem is an exact reformulation of charging on the fixed paths, not the global fleet problem.

A separately frozen native adapter can consume this problem and return

`proposal = {'values': [native q in variable order], 'dual_by_row': {row_name: native Pi}}`.

It must retain all rows and export every row multiplier. An integer MIQP incumbent alone generally supplies no such continuous-QP dual proposal; a new fixed-topology continuous solve is a distinct, prospectively budgeted call.

`result = recover(problem, proposal, physical_verify, limits=None)`

The physical callback is the separately cached original `independent_verify.verify`. The problem argument must be the freshly built, unchanged in-memory problem from the frozen source; it is not an arbitrary matrix admitted from an artifact. A future standalone certificate auditor should reconstruct the problem itself rather than trust serialized helper rows.

## One deterministic recovery, including degeneracy

There is exactly one absolute 1e-7 face-selection policy: q values within that distance of zero propose zero coordinates; equality rows and inequalities within that distance of tightness propose active rows. The tolerance has no role in final acceptance. It is never varied in response to failure.

After substituting proposed zeros, exact sparse elimination detects inconsistent equations and extracts an independent affine face basis. The equality-QP KKT system is formed only in the remaining q coordinates and this basis. Sparse rational elimination handles rank deficiency explicitly; free coordinates retain their specified native values as exact binary fractions. No uniqueness of the charging vector is assumed. The implicit Hessian is positive semidefinite, so a stationary solution minimizes the affine-face QP. That fact alone is insufficient: every original bound, inventory prefix, full-refill equality and shared capacity is then checked exactly.

For the final dual construction, **all** tight original rows are retained, including dependent inequalities; the primal row basis is not substituted for the sign-constrained dual opportunity set. Interior-coordinate stationarity is solved exactly, with free multiplier coordinates seeded by the supplied native Pi values. Multiplier signs and complementarity are checked, not projected after solving. Zero-coefficient rows may have multiplier zero because they contribute neither stationarity nor a nonzero tight RHS.

Every q, including those proposed zero, participates in the exact finite-box residual test. With gradient g at recovered loads and sign-valid row multipliers pi, compute `rho=g-A^T*pi`. Require each `rho_j*q_j=min(rho_j*l_j,rho_j*u_j)`. The independently checkable tangent bound

`LB=ops-sum_t b_t*load_t^2/2 + pi dot rhs + sum_j min(rho_j*l_j,rho_j*u_j)`

must equal the exact primal objective. This certifies the **whole** fixed-topology QP, rather than merely the selected face. Only then call the original physical replay once; require strict pass and matching exact objective.

## Boundedness, failures and scientific scope

Default limits are dimension250 for each exact system, two million monitored rational operations, 16,384 numerator/denominator bits and30 seconds for recovery. The full charge vector may be larger; the bound applies before constructing each reduced KKT/dual system. Resource enforcement for source admission, semantic problem construction and native solving belongs to the external frozen owner. This helper has checkpoints, not an interruptible process-level hard wall guarantee.

Wrong face, inconsistent exact equations, negative reconstructed q, wrong multiplier sign, failed residual equality, oversized/slow arithmetic or failed physical replay returns an explicit recovery failure with stage and reason. It does not prove topology infeasibility. Degenerate feasible dual families can defeat the deterministic seed choice even when a valid signed dual exists; the helper makes no complete recovery guarantee and performs no hidden sign-feasibility LP or alternate-face retry.

Success establishes an exact feasible schedule and the best quadratic charging cost **for those paths**. Its returned exact gradient is a legitimate candidate for a new global own-price response certificate. It does not establish global physical optimality, hull optimality or zero price-support gap. Those require the full-opportunity-set certification already described in `EXACT_SUPPORT_CLOSURE_PLAN.md`.
