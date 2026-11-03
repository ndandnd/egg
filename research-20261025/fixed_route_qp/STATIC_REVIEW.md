# Focused static review of the direct fixed-route QP

25 October 2026. One source pass plus narrow requested-delta review. **STATIC
REVIEW PASS: no unresolved blocker found in the reviewed scope. This is not
numerical qualification or execution authorization.** No source imports, compilation, tests, hashes, OS/resource
probes, case generation, inference, solver execution or commits were performed.

Reviewed `qp_control.py`, `run.py`, `PROTOCOL.md`, `RESOURCE_DECISION.md`, and the
specific unchanged `native_pathflow` builder/extractor and objective attachment
they call. Public API documentation and the installed gurobipy12.0.1
`__init__.pyi` declarations were checked as text; no package was imported.
No old outcome/capture was opened to choose a topology or tune this control.

## Concrete corrections and disposition

1. **Exact-zero sparse terms — corrected and delta inspected.** Source and public
   Gurobi readback may differ in whether explicit zero coefficients are retained.
   `_linear_terms` and `_gp_linear_terms` now omit only exact zero (including
   negative zero), while retaining exact comparison of every nonzero coefficient.
   This changes neither a constraint nor a tolerance.
2. **Caller fixed-topology/replay mismatch — corrected and delta inspected.** The
   independent candidate replay/fleet/route predicate now sets `identity_failure`
   and raises `ConfigurationFailure`, so a violated fixed-topology contract stops
   later dispatch. A valid improved returned witness is retained independently
   of `qp_success`; provisional helper outcomes remain representable.
3. **Physical objective consistency — corrected and delta inspected.** In addition
   to copied raw expression versus `ObjVal`, the helper now checks the exact
   Fraction difference between replayed physical bill and raw expression against
   unchanged `native_recharge.OBJECTIVE_TOL`. The rejected delta is retained in
   statistics; an inconsistent candidate does not replace the fallback. Physics
   and extraction tolerances are unchanged.
4. **Parent-requested provisional retention — corrected and delta inspected.**
   After the one native call, the helper uses the 60-second admission guard and
   records actual overrun of the 52-second native target. A finite solution from
   TIME_LIMIT, SUBOPTIMAL, ITERATION_LIMIT, INTERRUPTED or WORK_LIMIT can receive
   the same extraction/replay/objective checks while admission time remains.
   Valid improvements can be retained provisionally; `qp_success` requires
   numerical OPTIMAL, and `qp_candidate_admitted`/provisional status are separate.
   The caller retains valid better returned plans independently of `qp_success`.
   No extra native call or tolerance change was introduced.

The authors received the concrete items directly; the final changed hunks were
reviewed without repeating the full audit. Parent accepts **strict
fail-closed infinity readback** for this backend rather than adding a normalization
framework. This is a limitation, not a remaining correctness blocker: different
representations of an unbounded bound may reject the clone before optimization.
Gurobi 12 treats sufficiently large signed bounds as infinity; that is not a
reason to weaken genuinely finite physical bounds or ignore a mismatch.
[Gurobi 12 variable-bound reference](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/attributes/variable.html).

## Contracts checked in the source pass

- The original path-flow builder supplies all stored physical rows. Every routing
  binary is fixed to the prior's exact 0/1 topology before copying, and every
  other original variable must be continuous. Replacing fixed binaries by
  continuous singleton bounds preserves this conditional feasible set. Dense
  original/copy variable and row indexes, all finite bounds, every nonzero row
  coefficient, row constant/sense, dimensions and objective readback are guarded.
- The public model objective is the original operating-plus-linear expression
  plus diagonal `.5*b_t*L_t^2`, with nonnegative curvature and no dense quadratic
  matrix. Sparse quadratic coefficients are checked after storage. The documented
  `QuadExpr(LinExpr)`, coefficient/variable-pair `addTerms`, and linear/quadratic
  query methods match this construction. [Gurobi 12 manual, Python QuadExpr
  reference](https://docs.gurobi.com/_/downloads/optimizer/en/12.0/pdf/).
  The installed12.0.1 stub also declares `addLConstr(lhs,sense,rhs)`,
  `getAttr(name,Sequence[Var])`, `QuadExpr(LinExpr)`, scalar quadratic `addTerms`,
  expression queries and Var/Constr `.index` properties. Text locations:
  `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/gurobipy/__init__.pyi`
  and adjacent `gurobipy-12.0.1.dist-info/METADATA` (Name/Version fields only).
- The `.x`-only snapshot facade supplies exactly the three value collections
  consumed by the unchanged extractor: routing, charge and loads. Original
  compiled/physical metadata remain in the view. The extractor's existing whole
  incumbent projection, serial decoding, correction budget and physical replay
  are retained. No alternative route decoder or extra repair solve is introduced.
- There is one explicit `qp.optimize()` call, with remaining absolute native
  time, one thread, seed17 and recorded numerical settings/quality attributes.
  Unsupported quality/bound attributes remain null. Raw numerical `OPTIMAL` and
  any bound concern only this copied fixed-topology QP; they are not an exact
  physical or unrestricted-fleet certificate.
- The caller uses all eight predetermined acquired priors, checks saved/fresh
  identities and exact repricing, retains a valid fallback before QP work, and
  distinguishes a valid fallback packet from successful QP completion. It starts
  clocks before worker creation and observes exit plus complete receipt read
  within 60 seconds, with native cutoff52. Unknown interrupted helper call counts
  are not fabricated as zero; waited-child CPU and unresolved reserves are kept.
- The selected 1800 CPU/2700 wall package, dispatch1620/reserve180, worker90 CPU,
  observed5GiB and finalization provision are explicit. Closed 7004.35 CPU /
  7177.22 elapsed-sum measurements and the separate historical guard with unknown
  actual review CPU are retained. The prepared 384-cell replication stays held.

## Limits

This is a source/API compatibility review, not evidence that the installed solver
will accept the clone, converge within the clock, satisfy numerical guards, or
produce an improved independently admitted physical witness. A failure is useful
diagnostic evidence and does not authorize a retry or weaker physics. Comparisons
with the old finite-tangent control can diagnose its numerical weakness; changed
backend/procedure and exposed cases do not establish a timing or generalization
advantage. All requested source deltas above are closed by text inspection.
Actual solver compatibility, numerical quality, timing, physical admission and
resource closure remain observations for the single prospectively frozen run.
