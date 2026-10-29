# Native probe response to the independent source review

Source-only repair of native_probe.py, addressing items1 and3 and the export
mapping in item4 of NATIVE_SOURCE_REVIEW.md. The underlying egglab source and
all frozen historical inputs/results were left unchanged. No module import,
compile, numerical test, hash, native solve, or commit was performed. These
changes require integrated source review and prospective bounded execution;
this document makes no backend qualification or physical/exact claim.

## Explicit unsolved states and solved snapshots

MIQP and pricing now honor _optimize's Boolean. If the inclusive deadline
prevents optimization, they return NO_OPTIMIZE_DEADLINE_EXHAUSTED, raw status
and objective/bound/gap None, solution_count0, optimization_called=False, and
no candidate or invented native status. They never extract an unsolved model.

OA checks the deadline before attaching another round and handles expiry
between cut attachment and optimize. It preserves the last completed solved
snapshot separately, records its solved_matrix_revision, and reports the
current matrix revision and whether it has changed since that solve. Final
results are copied from the last solved snapshot; no final extraction is made
against a later mutated live model. Explicit outcomes distinguish exhaustion
without a solve, exhaustion after a solved round, and exhaustion after matrix
mutation. Optimize-call counts and final-skipped/deadline flags are recorded.
The finish event accepts raw_status=None and includes the diagnostic outcome.

## OA provenance and contradictory intervals

Each compact round now records raw native status, solution count, runtime,
objective, bound, raw MIP gap, node count, solved matrix revision, candidate
load and operating cost, evaluated nonlinear upper, retained upper/lower,
evaluated interval gap and candidate/bound generating rounds. Raw gap semantics
are explicitly those of the piecewise-linear OA model. The best candidate
and its generating round are separate from the last solved model snapshot.

A negative best-evaluated-upper minus best-native-lower sets a numerical
contradiction flag and stops with NEGATIVE_NUMERICAL_INTERVAL. It cannot enter
the nonnegative tolerance-closure branch. native_interval_closed is false in
that state. This is a contradiction requiring review, not nonlinear success.
Neither native OA OPTIMAL nor raw MIPGap is promoted to quadratic, physical,
complete-hull or ideal rational-model optimality.

## Self-contained diagnostic exports

Every solved snapshot exports original normalized linear rows and all OA cut
rows actually present at that solve, including their names, coefficient
indices, senses, constants and generation/tangent metadata. The objective
export includes the constant, indexed full linear coefficients, indexed
quadratic diagonal and explicit one-half Hessian convention. Source operating
coefficients/constant and hourly load-variable indices are retained separately.
All optimized variables have index, native name, source name where applicable,
type and lower/upper bounds; the native infinity convention is recorded.
Continuous optimal dual and reduced-cost exports retain their diagnostic role.

Snapshot row lists and objective mappings are detached from later list
append/replacement operations; historical source rows are never mutated.
The mapped data are binary-float native ingredients, not rational certificates.
Independent stationarity, primal feasibility, signs, bounds, complementarity
and objective verification remain required before any stronger admission.
Fractional continuous selections and recovered integer path covers remain
physically unverified.

## Timing and remaining interpretation limits

Review item2 remains an explicit owner/protocol obligation: solver TimeLimit
is not an interrupt for backend imports, matrix construction, extraction or
serialization. The outer owner must impose its deadline, kill/reap ownership,
resource accounting and exclusive paid output. inclusive_elapsed_s is measured
before final event/output work and must not replace the owner's complete-call
meter. No hard whole-call or instantaneous aggregate containment claim is added.
