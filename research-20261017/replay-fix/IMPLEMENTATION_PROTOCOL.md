# F1/F3 implementation check protocol — 17 October 2026

Scope: native_pathflow and focused unit tests only, no commits or experiments.
Historical extraction remains default. Opt-in fixed-topology completion qualifies every
movement binary against the model's existing integer tolerance, checks route coverage,
fixes every binary, solves original constraints for feasibility, then restores the attached
linear/tangent objective and solves within the original common deadline. No constraint,
replay tolerance, solver tolerance, or charging margin changes. Original MIP lower bounds
remain separate from fixed-topology objectives; repaired objectives cannot certify global
optimality by themselves. Every rejected candidate and completion stage is recorded.
All planner policies retain the lowest independently replayed true-bill candidate across
later candidate failures; without one return extraction_failed.

Checks: mocked deterministic retention, first failure, no-time, integer qualification,
bound separation; tiny existing fixture fixed-topology feasible/infeasible checks if feasible.
At most one solver thread and 120 seconds cumulative solver allowance. No cluster,
sealed DEV/TEST/A6/B3/confirmation/GIRO access, no new dependencies. Larger studies
require parent coordination and a separately frozen manifest. Tests are implementation
evidence, not historical recovery or numerical reliability qualification.

## Implementation check results

- 21 deterministic tests passed: eight new completion/retention tests plus existing
  MIP-start tests. No solver used by these tests.
- Tiny cyclic fixture, GRB, completion=True, one thread, 5s common cap,
  2s phase caps: certified [36.999999, 37.000001], unchanged replay passed.
  Installed Gurobi academic runtime reported license expiry 2027-02-11.
- Earlier tiny CBC attempt (two policies each capped 5s, sequential in one process)
  exited 137 after 2.25s with no stdout. This is a preserved backend execution
  failure, not evidence of infeasibility or recovery. No further CBC attempts.
- Conservative solver allowance charged: <=15 seconds (two CBC calls configured
  at 5s each, GRB at 5s); actual process wall time 3.08s. No larger experiments.

Caller compatibility follow-up: explicit absent-plan extraction_failed passes compact
provenance validation and maps to PricingUnresolved in native_hull. Existing prior lower
certificate/mixture remain available; the failed request supplies no new global bound.
Pure first/late failure integration cases cover both unresolved and extraction_failed.
Combined focused suite: 50 passed; zero additional solver calls. Completion remains
opt-in at pathflow API only; historical hull wrapper does not activate completion.

Search failure retention follow-up: planner model construction, objective attachment,
and optimization exceptions emit native_search_failed with stage, type, message and
wall timings, plus a round search_failure record. Prior accepted best returns bounded;
without one return search_failed. Errors remain visible rather than disappearing into a
fallback. Four mocked first/later TimeoutError/RuntimeError cases added; combined suite
54 passed. No new solver calls.

Deadline guidance: always-on completion has no free postprocessing allowance. If raw
optimization consumes the common deadline, completion explicitly times out. A future
runner must prospectively reserve completion/replay time inside its total cap (e.g.
search phase cap lower than wall cap), or predeclare qualified direct extraction as a
fallback policy. This implementation introduces neither a hidden reserve nor extra time.

## Prospective policy correction before qualification

The completion policy first extracts and independently admits the raw same-round witness
BEFORE mutating the model. Raw admission uses the existing raw-load objective consistency,
original global bound, physical replay and bill checks; it gains no relaxed tolerances.
The fixed qualified-topology feasibility/objective phases then run within the same deadline.
Each completed witness passes the same independent accounting/admission checks against
its own incumbent objective and the ORIGINAL MIP lower bound. Among admitted raw and
completed witnesses, select lowest replayed linear pricing cost for pricing, or lowest
recomputed true physical supply bill for planner (never choose by tangent objective).
Completion timeout/error, including objective-phase failure after feasible charging,
retains an admitted raw witness. Both failures produce explicit extraction_failed; all
stage failures stay in candidate_failures and candidate_rejected events. This policy is
prospective; no screen or historical recovery has run under it.

Pricing result stats now describe the selected witness's admission incumbent with the
original global lower bound. raw_mip_stats separately preserves the original objective,
status and bound; completion_stats separately holds restricted LP diagnostics. Therefore
an ordinary downstream admit_bound(result['stats'], physical_objective) is consistent;
the fixed-topology LP lower bound never becomes global evidence.

New mock checks cover same-round raw survival after timeout/runtime error, worse completed
true quadratic bill despite identical tangent objectives, and downstream pricing admission
when the completion objective changes. Combined focused suite: 58 passed; no solver calls.
