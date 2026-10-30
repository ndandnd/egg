# Distinct exact primal admission and dual-feasibility method

29 October 2026. Source-only decision and new helper; no numerical run, native call, gzip read, imports, tests, hashes or old-source edits. Only the completed phase's compact results and frozen helper source were inspected.

The preceding phase closed administratively and preserved a real mathematical failure: its rational point passed all original charge-only primal checks, but a seeded member of a degenerate dual affine family had the wrong sign. Its public native objective was441.53291205116824; no exact physical or optimality admission follows from that number. The old failed attempt remains failed and unchanged.

## Why a new method is justified

The failed routine did not solve dual sign feasibility. It assigned unconstrained free multiplier coordinates from a numerical proposal, then correctly rejected the resulting sign. A signed feasible member of that affine family may nevertheless exist. The new method solves this different mathematical problem explicitly; it neither weakens that guard nor tries alternative tolerances/faces. No optimizer is rerun.

First recover the same one-face rational primal from the newly saved QP's charge values and freshly reconstructed original problem. Check every prefix, full-refill equation and finite box; then independently replay the exact candidate immediately. This produces a first-class physical upper witness even if no optimality certificate follows. The original routine withheld that admission until after dual certification. Do not trust serialized old problem rows: rebuild from the source-bound descriptor/topology and frozen builder, and compare variable-order metadata before consuming the saved values.

## Deterministic signed-dual feasibility

For the admitted point x, retain every tight original row. A >= row has a nonnegative multiplier; a <= row uses its negated normal and a nonnegative multiplier; an equality gets positive and negative columns. On each charge coordinate enforce:

* interior: `A_normal*lambda = gradient`;
* at lower bound: `A_normal*lambda <= gradient`;
* at upper bound: `A_normal*lambda >= gradient`;
* fixed lower=upper: no residual restriction.

Convert inequalities with nonnegative slacks into `M z=d, z>=0`. Coalesce only identical coordinate conditions, never remove sign-relevant active normals. Full original-coordinate residual checks remain mandatory afterwards.

The new `phase_one` uses an artificial identity basis, exact fractions, Bland's smallest entering index and smallest basic-index ratio tie break. Dependent rows and zero artificial basics are allowed. Phase-I objective zero supplies an exactly checked feasible z without phase II. A positive optimum supplies an unrestricted-sign Farkas vector y with `y M<=0` and `y d>0`; these inequalities are checked independently of the pivot history. A limit or invariant failure is UNRESOLVED, never infeasibility.

Recovered original multipliers must pass signs, row complementarity and the finite-box residual minimum on **every** charge, including proposed zeros. The exact tangent lower must equal the exact primal cost. The `check_certificate` API independently repeats that algebra without trusting phase-I status or histories. Wrong-sign, ignored-zero-coordinate and altered-value certificates therefore have meaningful rejection controls. `verify_phase_one` separately audits feasible/Farkas vectors, including negative RHS normalization and arbitrary Farkas signs.

## API, budget and claims

`recover_primal(problem,proposal,affine,physical_verify,limits)` returns ADMITTED_PRIMAL or PRIMAL_UNRESOLVED. The affine callback module is the frozen old exact helper; no old signed-dual solve is called. `certify_dual(problem,values,limits)` returns CERTIFIED_FIXED_TOPOLOGY_OPTIMUM, DUAL_INFEASIBLE_FOR_THIS_PRIMAL or DUAL_UNRESOLVED. An admitted physical upper is retained independently of all three outcomes.

Default dual limits are250 equations,1000 total columns including artificials,2000 pivots,5million monitored checkpoints,16384-bit fractions and30 seconds; a prospective control may explicitly freeze60 seconds. These are bounded exact-algorithm checkpoints, with the external owner enforcing the complete package allowance. Worst-case simplex work remains exponential. No successful recovery is promised from the saved proposal.

This is a new certificate algorithm and first physical admission of a newly reconstructed point, not an automatic native retry or retrospective repair of the failed phase. Fixed-topology optimality still says nothing by itself about global fleet optimality, the unrestricted hull, or own-price support. Subsequent complete-graph pricing would need its own separate authorization and freeze; it is not included here.
