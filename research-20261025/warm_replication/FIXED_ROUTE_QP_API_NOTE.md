# Direct fixed-route convex QP: static API finding

25 October 2026. Replication dispatch remains on hold. Source/package-file
inspection only; no imports, license checks, tests, hashes, solves or QP
implementation. Existing replication sources and completed studies are unchanged.

**A direct convex charging QP is expressible locally, but the existing hull QP
helper is not that control.** `native_hull.solve_qp_rmp` delegates to
`restricted_qp_proposal.propose`: SciPy SLSQP over weights of already complete
schedule columns, followed by exact simplex/mixture checks. It does not optimize
the original SOC/charging matrix. `native_pathflow_hull` wraps the same coordinator
with compact pricing; it adds no direct physical QP routine.

`gurobipy` **12.0.1** files are present under
`/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/`.
The local `.venv-local/pyvenv.cfg` enables system site packages. Its installed
`gurobipy/__init__.pyi` exposes Model, addVar/addLConstr, LinExpr, QuadExpr,
setObjective, optimize, getRow/getCoeff and getVars. This supports a prospective
adapter without installing a package; runtime import/license usability has not
been checked. The local Python-MIP 1.17.6 Gurobi bridge exposes a linear
`set_objective` and has no declared quadratic-objective/GRBaddqpterms interface.
Adding private CFFI declarations or wrapping its native pointer would introduce
an additional unsupported bridge path and is unnecessary given gurobipy.

The smallest supported design is:

1. Build the unchanged `native_pathflow.build_feasible_model` once. Fix every
   original routing x to the shared prior's zero/one selection. Audit that all
   other variables are continuous. Clone **the actual built matrix**, not a
   hand-coded replacement: one index map, all variable bounds and every original
   row's sense, coefficients and constant. Preserve original binary64 values
   directly; avoid an unverified LP/MPS text round trip. Represent the fixed x
   as continuous variables with identical equal lower/upper bounds, leaving the
   feasible physical set unchanged. Read back and compare stored coefficients,
   bounds and row counts before optimization.
2. Copy `built['ops']` and add `sum(a[t]*h[t] + .5*b[t]*h[t]*h[t])` using the
   mapped `built['loads']`. With b nonnegative and all remaining constraints
   linear, this is a convex QP on the original fixed topology. Use one thread
   and a prospectively bounded solve; preserve native status, timing and residuals.
3. Map the QP solution back by original variable index through a small value
   view for unchanged `pf._extract`, which currently reads MIP variable `.x`.
   This view still needs implementation/review: gurobipy variables are not a
   drop-in MIP model. Keep the existing projection/serial-decoding tolerances and
   independent full-case replay; recompute the admitted objective exactly with
   Fraction operating cost plus `native_hull.supply`. Reject extraction failure
   rather than relax tolerances or infer physical infeasibility.

Native OPTIMAL would qualify this numerical **fixed-topology** optimization,
not an exact rational proof, unrestricted fleet/route certificate or learned
price mechanism. Matrix copying, model construction and extraction must be paid.
This stronger control could distinguish insufficient four-tangent charging
optimization from value of alternative routes; the present static check supplies
no measured bound on that confound. Parent triage must select a fresh prospective
protocol and budget before any implementation or numerical dispatch.
