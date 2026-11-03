# Direct convex charging QP on the eight existing prior topologies

Prospective diagnostic,25 October2026. The completed warm experiment remains
unchanged. Its fixed_route arm was a four-round supporting-tangent method, not
a converged convex optimum. Two compact saved records showed unused time and a
finite-envelope gap. This new control tests a stronger conventional optimizer
before the prepared eight-group replication. No model training or inference.

## Fixed cohort, common input and question

Use ALL eight already acquired prior plans from warm_replanning/attempt01:
base IDs50600–50603, sizes40/80, ascending base then size, native seed17.
Read the original complete campaign receipt to resolve the exact acquisition
folders and bind their saved best-plan, best-replay and receipt once. Do not use
any GNN endpoint or choose a topology using its QP result. Reconstruct the same
original physical case and verify identity against its saved prior. Reprice and
independently replay that prior under the same late market before solving.

Every original routing binary is fixed to the common prior's0/1 topology.
Fleet count is therefore fixed too. All SOC/energy/shared-charging/terminal/load
constraints remain the stored original physical matrix. The new problem is a
continuous convex QP conditional on that route topology, not the unrestricted
EVSP. Original data/old outcomes, capped-control results and frozen gate stay
immutable; new results are an additional diagnostic, never a replacement.

## Original-matrix clone and objective

Build the original Python-MIP path-flow model with its unchanged physical rows.
Fix every routing variable exactly. Reuse the original linear objective
operating cost+a'L. Clone its stored variable bounds, linear row coefficients,
senses and right-hand sides into a public gurobipy model with original-index
mapping. Fixed binaries may be continuous because their bounds are equal0/1;
all other original variables must already be continuous. Do not project out
variables, relax rows, serialize through LP/MPS, patch private CFFI functions,
or silently round coefficients. Treat infinity sentinels semantically as
unbounded; finite stored coefficients/bounds/RHS must agree on readback. Exact
zero coefficients can be dropped without changing a row. Record counts/mapping
checks; do not create a second massive row-inventory or hash audit.

Add the original convex quadratic objective .5*sum(b_t*L_t^2), not the atomic
payment sum(b_t*L_t^2). Use public QuadExpr coefficient-variable pairs and check
the sparse quadratic terms/linear part on readback; never allocate an N-by-N
dense matrix. One optimize call only. Set/read Threads1 and Seed17, native
TimeLimit to the remaining absolute native cutoff. Record actual solver/library
parameters:FeasibilityTol1e-9,OptimalityTol1e-9,BarConvTol1e-10. These tighten
numerical solution accuracy for the strong control; they change no stored row,
objective or independent replay tolerance. All accuracy cost remains paid.
Record actual solver/library
versions, status, solution count, objective and numerical quality attributes;
unsupported dual-bound attributes remain null. A numerical OPTIMAL status is a
conditional solver report, not an independent exact physical certificate.

Public API references (local installed gurobipy12.0.1 stubs were inspected too):
https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html
https://docs.gurobi.com/projects/optimizer/en/current/reference/python/quadexpr.html
Model.getRow/getQ expose the stored linear/quadratic expressions; setObjective
accepts a quadratic expression. QuadExpr coefficients multiply their specified
variable pair, hence the .5 factor is explicit. No long external quotation.

## Extraction, replay and retention

The supported gurobipy model differs from the legacy Python-MIP object. Use a
narrow original-index solution-value facade only for the attributes consumed
by unchanged native_pathflow._extract. Preserve the original compiled identity,
physical metadata and variable mapping; do not write a new route decoder or
weaken projection/replay tolerances. The facade supplies the snapshot of native
QP values, not values from the unsolved original model. If that contract fails,
record a fatal copy/identity error and stop further dispatch.

Independently replay the extracted plan on the original full case; require the
exact same selected movements/topology, same vehicle count and consistent raw
QP objective versus operating plus linear/quadratic costs under existing guards.
Compute the exact Fraction system cost from replayed data. Retain the best valid
prior if native solve, extraction, replay or numerical objective checks fail.
If a nonoptimal native status has an available finite incumbent, attempt the
same extraction/replay/objective checks and retain a valid improvement as
PROVISIONAL. `qp_candidate_admitted` is distinct from `qp_success`, which requires
native OPTIMAL plus valid timely admission. Do not discard a valid incumbent
merely because a time/iteration/work limit was reached. A native return after
the52s solver dispatch/time-limit boundary can use the reserved final admission
window through60s; report its actual overrun and charge all work, no extra call.
Apply the unchanged OBJECTIVE_TOL to replayed versus raw integrated objective.
No feasibility repair solve, extra LP, additional seed or automatic retry.
A timeout/failure with fallback availability is not a successful QP endpoint.

The eight cases are exposed diagnosis, not generalization or a timing advantage
against the old backend. Report raw numerical quality/conditional status and
true replayed bill. Comparing against the old four-round fixed_route bill
quantifies that control's finite-approximation weakness. Comparing the stronger
witness with old GNN bills can challenge a route-adaptation interpretation, but
old/new solver/library/procedure differences prohibit a clean speedup claim.

## Clocks, resources and preservation

Fresh local worker per case. Parent monotonic anchor precedes process creation;
case construction, fallback read/replay, gurobipy import, original model build,
clone/readback, objective, solve, extraction/replay and durable output all count
inside60seconds. Native cutoff52; parent observes worker exit and complete output
read by60. One native QP call/thread, observed peakRSS<=5GiB, CPUhard90 perworker,
simple parent timeout plus3seconds cleanup. No new supervisor/transport framework.

New package TOTAL1800CPU/2700wall seconds, dispatchstop1620CPU/reserve180,
including preflight, all eight cells, failures, startup and compact finalization.
No approval is pending under the human's practical routine resource authority.
Hash consumed source/input/prior files once in one metered preflight; no learned
assets, old native captures or duplicate audit. Preserve every assigned cell,
late result, copied-matrix failure and all resource costs. No auto-resume/retry.
Freeze exact sources/command after parent and one focused static review, before
execution in fresh fixed_route_qp/attempt01. Current source/API note is not a run.

Prior closed reset numerical-process CPU7004.35s/elapsed-sum7177.22s is retained;
separate conditional historical guard2546.091499549272s remains, actual historical
review CPU UNKNOWN. No reset, whole-session exact CPU or restored compliance claim.
No cluster, sealed DEV/TEST/A6/B3/confirmation/GIRO, model fitting, manuscript,
merge, submission, private-data publication or reset credits.
