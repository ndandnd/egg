# Exact lower certificates from approximate continuous duals

29 October 2026. Mathematical/source-only design based on `ENERGY_FLOW_FORMULATION.md`. No import, solver execution, numerical work, test, data read or hash. The `energy_flow.py` ledger API is not yet confirmed, so no executable checker is implemented in this step.

## 1. Certificate target and sign convention

Write a semantically validated rational linear relaxation as

    minimize k + c·x
    subject to A_i·x sense_i d_i,
               l_j ≤ x_j ≤ u_j.

Every variable must have finite rational l_j,u_j, with l_j≤u_j. Rows use the announced ledger convention `sum(coeff*x) sense rhs`. For minimization choose multipliers satisfying

    sense >= : y_i ≥ 0
    sense <= : y_i ≤ 0
    sense  = : y_i unrestricted.

This is the native Pi convention expected for minimization, but the checker must validate the signs itself rather than trusting a claimed backend convention. For every feasible x, sign validity gives y_i(A_i·x−d_i)≥0.

Put r=c−Aᵀy. Then the exact lower bound is

    LB = k + Σ_i y_i d_i
             + Σ_j min(r_j l_j, r_j u_j).

Equivalently, choose l_j when r_j≥0 and u_j when r_j<0. All terms are computed as exact Fractions.

**Proof.** For feasible x,

    k+c·x = k+y·d + r·x + y·(Ax−d)
           ≥ k+y·d + Σ_j min(r_j l_j,r_j u_j).

Thus LB is valid without stationarity, complementary slackness, primal optimality, accurate native reduced costs, an optimal native status, or agreement between rounded native rows and the exact rows. Finite-box compensation pays for every stationarity residual. Large residuals can make LB weak but cannot invalidate it. The proof also handles equality rows, duplicate rows and redundant inequalities.

Bounds here are not extra assumptions about a native incumbent. They must contain every physical plan's image in the intended energy-flow relaxation. A lower bound over that relaxation is a lower bound on D; because every convex combination of physical extended plans remains feasible, the same tangent certificate also bounds CH. Do not identify the relaxation optimum with CH.

## 2. Rationalizing a native multiplier proposal

Accept a native dual vector only as a source of proposed coefficients y. Reject NaN/infinity and malformed dimension/index data. Convert each finite float to its exact binary rational `Fraction(float_value)` or apply a deterministic, predeclared denominator-limited rationalization. Both are valid: y need not solve any dual optimization problem.

After rationalization project signs exactly: >= rows use max(0,y_i); <= rows use min(0,y_i); equality rows keep their rational value. Alternatively reject sign violations; projection is useful because small sign errors otherwise discard valid proposals. Record original proposal, rationalization rule and final rational y. Rounding accuracy is a strength question only.

The independent checker computes Aᵀy and r from its own exact reconstructed rows/objective. Native RC values are optional diagnostics, never substituted for r. No numerical stationarity tolerance is required for validity. The zero multiplier is always an admissible fallback and yields the simple objective box bound; failure to improve the existing bound must remain an unsuccessful outcome rather than trigger unregistered tuning.

## 3. Quadratic supply: exact tangent certificate

For operations o·x+o₀ and market loads e_t, the intended objective is

    J(x)=o₀+o·x+Σ_t(a_t e_t+b_t e_t²/2),  b_t≥0.

Choose any finite rational tangent point v_t. In the proposed diagnostic take each stored native root-load float as an exact binary Fraction; physical/root feasibility of v is unnecessary. Use the original binary-stored market coefficients converted individually to exact rationals, not a rounded native gradient or recomputed decimal surrogate.

Set tangent slope s_t=a_t+b_t v_t and tangent constant h=−Σ_t b_t v_t²/2. Then

    J(x) ≥ o₀+h+o·x+Σ_t s_t e_t,

because the difference is Σ_t b_t(e_t−v_t)²/2≥0. Apply the linear checker to k=o₀+h and c equal to operations plus these indexed load slopes. This yields an exact lower bound on the intended quadratic physical and complete-fleet-hull objectives. Singular/zero b_t is harmless.

A dual from a native QP is only a proposal for the tangent LP: native gradients/rows may differ slightly, but the residual-box formula absorbs that difference when evaluated against the intended exact model. No claim that its uncorrected native dual objective is exact is needed. For linear pricing, use the exact intended price-vector coefficients and no quadratic tangent constant.

## 4. Finite bounds for every energy-flow variable

Use independently proved conservative bounds; tightness is optional.

| Variable family | Safe finite box under the formulation assumptions |
|---|---|
| Movement selection y_m | [0,1]. Integer restriction is relaxed. |
| Movement/leg-boundary inventories U,W,C,D or individual s | [0,B]. Perspective constraints additionally link them to y. |
| Service aggregate before/after inventories | [r,B] where they exist explicitly; [0,B] is a conservative alternative. |
| Elementary allocation q_mk | [0,cap_k], with exact cap_k from resource power and interval duration. |
| Total visit charge q_m | [0,Σ_{eligible k}cap_k]. Under the stated visit conservation, [(B−r)/eta] is also a valid upper bound, so the minimum may be used if proved by the reconstructed rows. |
| Market load e_t | [0,Σ_{k in period t}cap_k], counting each shared interval once, not once per movement. |

Noncharging arcs need no q variables. If an implementation adds auxiliary operations variables, bound them from vehicle-count/movement selections and exact nonnegative fees. Avoid epigraph theta variables in the independent tangent certificate: substitute the explicit linear tangent objective instead. A native unbounded-above sentinel is not a finite rational upper bound. Never turn `1e100` infinity into a claimed physical bound simply because it is a finite float; derive the intended box independently.

The safe load bound follows from shared interval rows, not the number of visits. The exact cap is min(P_bus,P_grid)×(end−start)/60 for one available connector, and zero otherwise. Compute it from individual exact stored inputs; inward-rounded native cap RHS is not the intended physical capacity. All candidate upper witnesses remain subject to original exact capacities separately.

## 5. Do not certify an untrusted exported model

A perfect dual bound for a malicious, restricted or misassembled ledger says nothing about the intended fleet. The checker must independently reconstruct the relaxation from the admitted case descriptor and the written formulation, rather than accept exported row coefficients as truth.

Recommended separation:

1. Independently validate unique IDs, case horizon, mandatory services, DAG chronology, movement endpoints/legs/depot split and the scoped single-connector resource assumptions. Reject unknown model restrictions or undeclared selection-variable fixing.
2. Reconstruct elementary intervals from all declared window, market and resource boundaries. Derive window eligibility, exact per-leg energy coefficients and exact capacities without native compiler helpers.
3. Build deterministic semantic variable keys and exact finite bounds. Reconstruct coverage, pullout/pull-in count, per-leg conservation, initial/terminal fullness, service balances, depot-gap charging, perspective inventory bounds, allocation-selection links, shared capacities and load aggregation. Include the full admitted graph and all allowed bus counts.
4. Map multiplier proposals by unique semantic row keys. Do not trust positional agreement or row names alone. Compare the exported ledger with independently reconstructed canonical rows (exact coefficient aggregation, orientation and RHS), or explicitly record that proposals were remapped to independently generated rows. Missing proposal entries can safely receive y=0; missing intended constraints can produce a weaker valid relaxation, but extra restrictions must never enter unnoticed.
5. Reconstruct operations and a/b objectives independently. Validate the tangent-load variable mapping. Evaluate LB only on this intended exact model; store r and its endpoint compensation by semantic variable key.

An alternative is to validate against a separately source-proved exact builder, but that requires an explicit reviewed source-to-model argument. Merely reading the same builder or trusting its `exact=True` metadata is not independent semantic verification. An exact match of two copies of an incorrect ledger is not a physical certificate.

Row scaling/orientation changes must transform y consistently; the simplest first API requires canonical orientation and exact equality of reconstructed rows. Native rows need not numerically equal intended rows for LB validity once multipliers are remapped: the checker recomputes everything on the intended rows.

## 6. Proposed checker API and receipt, pending confirmation

Prefer `check(case_descriptor, proposal, market, tangent_load)` where the checker independently constructs its model. The proposal contains semantic row keys plus raw finite dual numbers; an exported ledger may be supplied only as comparison evidence. No files, paths or executable expressions are followed from model data.

Return exact rational LB, tangent constant/slopes, rationalized/sign-projected multipliers, per-variable residuals, chosen bound endpoints and correction terms, semantic-validation status, original/proposed model comparison, and explicit target `physical_and_complete_fleet_hull_lower_bound`. A compact receipt should expose total y·d and total box compensation so any apparent large correction is visible.

Before an actual public attempt, prospective literal cases should exercise <=/>=/equality signs, nonzero stationarity residuals selecting both finite endpoints, row/RHS/objective corruption and quadratic tangent constants. These checks must be inside the separately authorized frozen paid execution, not run as part of this source-only design. No benchmark or pass is claimed here.
