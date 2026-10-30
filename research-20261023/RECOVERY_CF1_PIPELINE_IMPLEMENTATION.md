# CF1 provider integration: source-only candidate

24 October 2026. New `src/egglab/constructive_proposal.py` implements
`propose(case,a,b,*,schedule,allowance,budget,clock,allowed,events,
constructor=None,completer=None,undoer=None)`. It changes no qualified core,
model, charging/construction helper, schedule or test source. The new comparison
coordinator owns independent lift/replay, physical/durable admission, storage,
full search and final output. This provider is not an admitted fallback or start.

Default delegates are `constructive_control.construct_routes`,
`constructive_charging.complete_topology` and `constructive_control.undo_merges`.
The optional injected delegates support bounded fake-only contract tests. No
runtime imports, process/test/native execution or model/data access were used
while writing this source.

Construction is called once under Schedule60's absolute construction endpoint
`t0+6`. Market/budget validation, gates, event recording and copying are inside
that deadline. A late return is rejected, even if the constructor returns a
proposal. No proposal ends CF1; the coordinator may later attempt cold full
search if its own gates permit. Construction is price-blind; charging uses a,b.

Immediately before the first fixed-topology setup/build, the provider computes
ONCE `completion_deadline=min(schedule.charging_stage_end,
first_completion_anchor+max(0,allowance.limit-allowance.spent))`.
Schedule60 supplies charging_stage_end=t0+12 and the shared allowance has limit6.
This exact deadline is reused for every call, undo and rebuild; neither a fresh
now+6 nor the stage endpoint alone replaces it. Setup, replay, exact billing,
recording, copying and repairs all fit within this fixed wall window. The
provider checks allowed()/finite nondecreasing clock and deadlines around steps.
New work/entry is closed at >= its endpoint; completed constructor/helper/undo
returns and final accounting checks allow equality and reject only >. Equality
does not authorize another repair or native call. It rejects an entire late
helper return even if that helper retained an earlier
in-memory witness. This explicit provider-stage rule is stricter than the
charging helper's internal best-witness retention rule.

One unchanged `recovery_coordinator.native_limits` context encloses all fixed
charging calls and repairs, with both integer_end and planner_end equal to the
fixed completion deadline. It receives the same allowance object as subsequent
full search. Its existing hook debits only actual fixed-native call elapsed time
exactly once; the provider adds no wall-time debit or second native charge.
Non-native setup/replay/repair is nevertheless constrained by the fixed deadline.
Context restoration is followed by a final gate/deadline check before return.

A returned physical candidate stops repairs. With no witness, repair is allowed
only when the completion status is infeasible, reverse_repair_allowed is exactly
true, failures are empty, and the first stage is feasibility with INFEASIBLE
status and no incumbent. Objective-stage INFEASIBLE, unresolved/no-incumbent, invalid replay,
exceptions and timeout do not permit undo. At most two one-merge LIFO undos and
three total completion calls occur. The unchanged undo helper validates the
hashed ledger/rebuild; provider checks active count decreases exactly one and
cumulative undone count increases one. Invalid/no-proposal repair stops. No
reference solution, label, feasibility oracle or retry window is introduced.

The JSON result includes raw plan/status, failures, stage ledgers, construction,
fixed completion deadline/anchor, repairs and any helper bill/replay. Events go
to the shared list, including complete helper capture events. `durable_fallback`
and `start_submitted` stay false and `global_lower_bound` stays null. A candidate
with earlier/later helper diagnostics remains subject to independent coordinator
admission; fixed-topology bounds never become unrestricted bounds.

This package establishes source/fake contract behavior only after its focused
gate. The composite sixty-second CF1 arm, native fixed-discrete inventory,
backend behavior, shared allowance in actual full search, durable fallback/start
and actual timing require future prospective native qualification. Prior V7
qualification is not qualification of these new source paths. No native launch,
comparison, quality, optimality, generalization or speedup claim follows here.
