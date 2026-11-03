# Prospective anytime admission policy

24 October 2026. Source-only implementation in `recovery_coordinator.py` and
`recovery_qualification.py`, following `RECOVERY_HANDOFF_POLICY_REVIEW.md` and
parent approval. No runtime import, test, solver, fixture generation or native
retry was performed. V6 remains failed under its frozen strict handoff policy;
none of its candidate evidence is backdated or reclassified.

## Clock semantics and evidence

All stages retain the supervisor's original absolute anchor. Planned integer
search stops remain10/22 seconds, within original12/24 upper caps. The native
planner and completion deadlines remain13/25; native calls are not renewed after
those targets. Fixed-topology native completion remains three seconds cumulative
across stages. Full incumbent capture and reference verification are unchanged.

The13/25 planner handoffs are now **budget targets**. Missing a target alone
produces diagnostic evidence and does not raise an engineering failure. Every
planner return, including no-plan/bound-only returns, records its target overrun
and remaining hard-admission time. Independent admission may start only strictly
before15/27. A return or entry at or after that hard endpoint raises a timing
failure; no lift begins. Nonpreemptive lift/replay, witness copying and required
durable saving must actually finish at or before15/27. Their existing post-work
checks remain, as do late-bound rejection and output censorship after30. Outer
cleanup remains32.5. No arm receives additional time.

A prefix target overrun can consume planned headroom up to15 and shorten the
remaining full-search window before22. A real prefix hard-cutoff miss still
blocks full dispatch. A first fallback/selected witness is published only after
its successful timely durable save. A late saved file remains rejected diagnostic
evidence. Any previously admitted valid fallback and exact bill survive later
planner, replay, copy or save failure. The optional injected initial full fallback
now also uses the full27-second admission cutoff, rather than30.

`admission_window(at, target, cutoff)` supplies `planner_target`,
`target_overrun_s`, `admission_cutoff`, signed `admission_remaining_s` and
`admission_open` on return and lift entry/exit events, with finite-clock checks.
`admission_open` describes whether new admission could start at that instant;
an exit exactly at the cutoff is valid even though this launch flag is false.
Existing event names and anchored timestamps remain available across controls
and recovery. Generic exceptions, invalid replay, backend failures, capture/sink
errors and malformed typed gate evidence retain their failure classifications.
There is no general `TimeoutError` suppression.

Fresh lock split and result schedule metadata contain
`handoff_policy: anytime-hard-admission-v1` and
`planned_admission_headroom_s: 2`. This explicitly replaces the serialized
`admission_reserve_s` label: the gap is planned headroom, not a guaranteed reserve.
The old readonly Schedule property remains a documented compatibility alias.
Exact split verification rejects an old strict-policy lock against these sources.

## Per-size qualification

The analyzer now reports `coverage_by_size` for40 and80 independently. Each size
requires a clean, uncensored normal-recovery row with a valid fallback and
observed native partial-start processing, plus a clean, uncensored start-fault
row with a valid fallback and the actual fault-exercised flag. Analyzer rows now
include that flag. `size_path_coverage(rows)` implements these requirements; missing
paths append size-specific unresolved reasons. Aggregate counts remain diagnostic
and cannot fill a missing size's path. Witness validity and exact bills continue
to be independently checked before a row can qualify as clean.

## Verification and resource status

Runtime sources are held stable for independent static review and the test
owner's focused/regression adaptations. Parent must freeze final sources and
conduct one explicit source-bound solver-free check before any fresh native lock.
Fakes establish boundary behavior and provenance, not real-time completion.
Authoritative carry is1005.1053913375928s, ADMIN0, under the existing1800/1620/180
ceiling/dispatch/reserve and one-thread5GiB limits. Parent owns all later
execution and accounting; this implementation creates no new native attempt.
