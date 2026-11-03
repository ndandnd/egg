# Explicit pre-build integer cutoff

23 October 2026. Source-only implementation of
`RECOVERY_INTEGER_CUTOFF_REPAIR_PLAN.md`. This package executes no solver-free
check, fixture generation, freeze or native retry. The parent owns the prospective
check receipt and any later revision decision. Preserved native-v1/v2 outcomes and
their charged spend remain unchanged; the repair plan carries 275.4936378346678
seconds before separately authorized preparation/check charges.

## Changed interface

Only `src/experiments/recovery_qualification.py` changes runtime behavior.
`IntegerGateClosed(TimeoutError)` represents a deliberate refusal **before** the
underlying model builder is called. Its serialized exception message is exactly
`integer_gate_closed:<32-hex-token>`. The frozen planner still catches and records
the exception using its existing `error_type`/`error` interface; no native,
coordinator, replay, model or physical clock source changes.

`integer_gate_spec(task, policy, case_identity)` resolves an exact frozen identity:
restricted prefix for recovery/start-fault gets anchor+12; their full stage gets
anchor+24; static restricted and cold full get anchor+24. An arbitrary non-full
case is rejected. The independent instrumentation policy binds the complete task
hash/id, supervisor anchor, full identity and restricted identity. Existing
unanchored test instrumentation retains its prior behavior.

When that pre-build guard closes, it synchronously appends and fsyncs an
`integer_gate_closed` record through the existing native evidence sink containing:

- token, complete task hash and task id;
- case identity and phase (`prefix`, `full`, `static` or `cold`);
- supervisor anchor, absolute integer cutoff, actual observed monotonic time and
  elapsed time from the anchor;
- `guard_point=before_model_build` and `native_dispatched=false`.

Only a successful durable append creates `state.integer_gate_pending`. Evidence
sink failure sets the existing sink-failure gate and issues no expected token.
The original model builder is never called on this closed-gate path.

`expected_integer_gate(task, state, event)` consumes that pending token once.
`native_event_is_failure` exempts a native search failure only when the event has
the exact `IntegerGateClosed` type, model-build stage and token message, and all
pending metadata match the independent policy. Times must be finite; the cutoff
must equal the original anchored 12/24-second rule; observed time must be at or
after cutoff; elapsed time must exactly equal observed minus anchor. Missing,
reused, wrong or malformed tokens/evidence fail closed. Matching evidence is also
retained in `native_state.expected_budget_stops`; the durable guard record and
original planner failure diagnostic remain visible.

## Limits and verification status

Generic `TimeoutError`, post-build allowance exhaustion, start-setter timing,
native optimization, replay, storage, sink, resource and monitor failures keep
their existing engineering-failure treatment. A recognized budget stop grants no
new dispatch time, admits no witness, changes no bound and cannot excuse late
completion or absent qualification coverage. The preexisting expected injected
start-setter fault remains a separate path.

The focused test owner prepares boundary, metadata/token mutation, nonfinite,
generic-timeout, post-build-overrun and sink-failure cases, including the actual
guard → frozen `solve_planner` catch → event classifier path with a fake builder.
No tests have been executed by the implementation agent. Passing source-hashed
solver-free checks and review must precede any separately frozen native revision.
