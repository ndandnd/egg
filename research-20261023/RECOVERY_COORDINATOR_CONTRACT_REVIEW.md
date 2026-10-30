# Shared-clock coordinator contract review — 23 October 2026

Read-only interface review against `RECOVERY_QUALIFICATION_PROTOCOL.md`,
`src/egglab/native_pathflow.py` (`solve_planner` and candidate/start helpers),
`src/egglab/recovery_lift.py`, and `src/tests/test_recovery_interface.py`.
This note records implementation recommendations, not execution evidence or
additional qualification gates. No tests, native calls, training, cluster work,
or protected-data access were performed for this review.

## Clock contract

Use the supervisor's pre-interpreter monotonic anchor `t0` throughout. The hard
endpoint is `D = t0 + 30`; import/loading/model construction/lift/start/write time
all consume it. Prefix integer search stops by `t0 + 12`, leaving the specified
three seconds for extraction/completion/lift before `t0 + 15`. Full recovery
dispatch requires a durably saved independently replayed full witness and
`now < D - 6`. Preserve the specified cumulative three-second completion reserve
and three-second finalization reserve. Do not allocate either reserve afresh
per round or completion phase. Unused prefix time does not reset any clock.

Current `solve_planner` clamps an external deadline against its local wall budget,
checks after model/objective/start setup, and passes the same deadline into both
integer optimization and `_complete_topology`. This avoids a later deadline reset
but does not itself distinguish integer cutoff from completion allowance. The
integration must represent those cutoffs separately; passing the prefix integer
cutoff as the only planner deadline also prevents reserved completion from using
the remaining prefix allowance. Fixed-topology feasibility and objective calls
must share the remaining cumulative completion allocation. Recheck after replay,
durability, setup and each completion phase. With no native allowance, finalize
the retained fallback without constructing or calling a solver.

## Physical admission and durability

`lift_plan(source_case, full_case, source_plan, a=..., b=...)` already replays
source and full witnesses, compares movement/trip physics, reconstructs full
loads, recomputes the target-market bill (including exact representation), and
returns an all-full-movement binary specification keyed by IDs. Use this result
as physical evidence; never copy the prefix cached objective or source variable
indices. Keep its plan, exact bill and provenance separately from the optional
native start and later solver results.

The current planner accepts `start_plan`/`start_case` and performs lift internally;
it has no independently supplied fallback argument. A coordinator can retain the
admitted fallback outside that call or add the separate interface required by the
protocol. Either way, start submission, setter failure, unknown/rejected native
processing, model failure, timeout, no incumbent and subsequent replay rejection
must not erase the retained physical witness. Invalid lift produces no fallback.

Do the durable witness write explicitly before full dispatch. `solve_planner`
deliberately swallows diagnostic `record` exceptions and reports them in
`instrumentation_failures`; a `recovery_fallback_admitted` callback alone cannot
prove successful persistence. A failed required artifact write must prevent full
dispatch, while leaving any previously admitted in-memory witness available for
finalization. After successful full search, independently admit any selected
replacement and compare physical bills against the retained fallback.

## Bound and failure contract

Coordinator global lower-bound state starts empty. Prefix restricted-model
bounds and fixed-topology completion bounds remain scoped evidence only. A full
unrestricted result can contribute a lower bound only through the existing
admission guard and objective reconstruction; preserve its native provenance.
`_candidate_impl` deliberately combines the original unrestricted MIP bound with
the completed incumbent rather than importing the fixed-topology LP lower bound.
Do not replace that original bound with completion statistics.

Keep the selected witness's own independently replayed bill as upper bound.
`test_full_bound_separate_from_physical_fallback_objective` expressly exercises
this separation. If later evidence reverses the enclosure, invalidate the global
lower and expose the contradiction; do not alter the fallback bill to certify a
gap. An unrestricted infeasibility claim with an admitted witness is likewise a
visible model/replay contradiction, never certified infeasibility.

Planner setup and candidate exceptions currently retain an admitted fallback;
diagnostic sink failures do too. The coordinator must extend this property across
its own lift, persistence, result selection and serialization boundaries. A valid
fallback does not turn a failed or late completion receipt into a passing endpoint:
materialization time is measured from the parent anchor, independently of cleanup,
and late/missing/malformed completion remains censored under the protocol.

## Existing fixture coverage and integration focus

The inspected solver-free tests already cover binary inventory and untouched
bounds; build/start/optimize/no-incumbent/replay/infeasibility fallback retention;
expired/setup-exhausted clocks; invalid fallback; bound/objective separation;
diagnostic/capture failures; and invalidation of contradictory prior bounds.
Coordinator fixtures should connect these existing behaviors to the protocol's
shared parent clock, explicit durable-save prerequisite, reserve consumption and
terminal materialization/censoring. Native processing acceptance remains separate
from submission, exactly as required by the recorded protocol.

## Static implementation review

Reviewed the initial `src/egglab/recovery_coordinator.py`,
`src/tests/test_recovery_coordinator.py`, and
`research-20261023/run_coordinator_checks.py` against
`RECOVERY_COORDINATOR_CHECK_PROTOCOL.md`; no execution. The scoped/restored
optimizer hook preserves frozen core sources, clamps integer calls to anchor+12
and D−6, clamps physical planner calls to anchor+15 and D−3, and shares native
fixed-topology completion elapsed time across both stages. The lock and `finally`
restoration protect the declared serialized-worker use. The conservative
three-second cumulative native-completion interpretation matches the new check
protocol; it is not a fresh allowance per stage or native phase.

The original unrestricted MIP lower bound combined with an admitted completed
incumbent in `_full_lower` matches the frozen core's `_candidate_impl` semantics.
The completion LP lower is excluded. Explicit durable fallback storage precedes
warm dispatch, and plans are copied before a solver can mutate them.

Review findings sent to the parent and implementer before the first check:

- A prefix save finishing after15 but before24 raises a recorded timing failure
  yet still permits warm full dispatch. The physical prefix contract is missed.
  Stop subsequent dispatch on that stage timing failure; retaining the physical
  fallback for finalization remains appropriate. If continuation is intentionally
  retained, a future qualification analyzer must treat the recorded prefix timing
  failure as failure even when final completion is timely and the selected plan
  is feasible.
- `_full_lower` initially checks time only before each replay/admission round.
  Check again after independent replay/objective admission so a slow round cannot
  silently add a lower bound after the physical cutoff.
- Strict JSON serialization covers unfiltered native diagnostic events. Normal
  captured variable infinities already use null plus a repr, and initial global
  lower is converted to null. A core bound-contradiction row is not emitted into
  the current coordinator event stream. Arithmetic or injected diagnostic
  nonfinites can nevertheless reject the whole artifact. Encode them deliberately
  at the artifact boundary, keeping admission arithmetic unchanged.
- The bounded-check receipt should explicitly record owned process-group cleanup
  outcome, as required by its check protocol. Existing monitor helper subprocess
  calls have no timeout; this is a limitation of a claimed hard outer wall bound
  if one of those helpers hangs. This note does not qualify operating-system
  supervision, which the check protocol explicitly defers.

These are initial-code findings, not a verdict on later repairs or test results.

## Repaired-source static verdict

Re-read the coordinator, focused fixtures and bounded-check runner after the
parent's first source-hashed check and the scoped repairs. No execution was
performed by this reviewer. No remaining correctness blocker was identified for
the explicitly authorized second solver-free check.

The revised coordinator stops dispatch after a prefix physical/save overrun while
retaining its admitted fallback; a prefix gate never entered after late loading
still permits the required cold continuation. Full lower-bound replay now checks
its physical cutoff after objective admission and before importing a bound.
Native diagnostic nonfinites receive explicit tagged representations; physical
witness JSON remains strict. Focused fixtures cover all three repairs.

The revised check runner bounds monitoring subprocesses within each sample,
records owned-group absence after cleanup, and charges the maximum of elapsed
allocation, sampled process-tree CPU and observed child CPU, plus supervisor CPU.
The parent reports preserving the failed first-attempt source snapshot and receipt;
this static verdict does not replace receipt inspection or the second check.

Fixture exact bills now use the independently written expression
`Fraction(7) + 2*15 + Fraction(.2)*225/2`. This correctly preserves the exact
binary-floating-point tariff supplied by the fixture, rather than treating that
input as rational one-fifth. The runtime lift/bill implementation is unchanged.
Native and operating-system qualification remain deferred as declared.
