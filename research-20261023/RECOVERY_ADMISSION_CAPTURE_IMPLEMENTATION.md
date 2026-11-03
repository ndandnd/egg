# Admission timing and single durable incumbent capture

23 October 2026. Source-only repair following
`RECOVERY_PHASE1_V3_TIMING_DIAGNOSIS.md`. Runtime changes are confined to
`src/experiments/recovery_qualification.py`. No solver-free check, native solve,
fixture generation, retry, cluster work or commit was performed by the
implementation agent. Native-v1/v2/v3 artifacts and their charged spend remain
immutable. The authoritative continuation carries 543.0194821688248 seconds;
the parent owns prospective preparation/check accounting and any later design.

## Admission guard and clocks

Standalone `control` records anchored `control_planner_return`,
`control_lift_enter`, `control_lift_exit` and `control_materialization_start`
events. Each includes task id, supervisor anchor, observed monotonic time,
elapsed time and applicable cutoff. Lift exit is recorded even if lift raises.

Immediately before outer lift, a time at or after the original physical
anchor+27 cutoff now prevents the lift from starting. It records a control
failure and admits no late plan. The existing post-lift guard remains: a lift
finishing strictly after 27 is rejected before fallback admission. Exact 27 at
post-lift retains the previous boundary semantics. Independent source/full
replay, exact billing and the original 12/15/24/27/30 clocks are unchanged.
Integer search is not shortened in this package.

Worker materialization records a common anchored `materialization_start` event
before reference validation, evidence/plan writes and result serialization. The
existing result/completion marker still records its own immutable endpoint.
After that marker is fsynced, a separate flat `materialization-reference.json`
binds the start time, task/lock, result hash, exact completion marker hash and
recorded endpoint. No earlier result or marker is rewritten to add later timing.
The worker's acknowledgment time is sampled after this additional audit file is
fsynced, so a late required audit write cannot produce a timely acknowledgment.

## Complete capture and checked compact reference

The runner sink handles each `native_incumbent` through
`persist_incumbent_capture(folder, task, policy, event)`. It applies the existing
diagnostic conversion and serializes the complete event once into an exclusive
flat file `incumbent-{phase}-round{round}.json`. The same bytes determine its hash
and length. The file and directory are fsynced before a reference is issued.
Existing files are never overwritten or silently reused. Flat files are covered
by the supervisor's existing task-folder hash inventory.

The complete envelope and compact reference bind lock hash, attempt hash, full
task hash/id, frozen case identity, phase, round and supervisor anchor. Phase is
resolved by the existing exact frozen full/restricted identity policy. The
reference additionally binds its confined filename, zero byte offset, full byte
length, SHA256 and schema. Prefix/full round zero therefore cannot collide.

`verify_capture_reference` checks identity/range, rejects symlink substitution,
checks exact bytes/hash and verifies the complete envelope metadata. It runs
after initial persistence and again at the final audit boundary. It does not
reserialize the full capture or reread it on each forwarding operation. These
checks and their I/O remain inside charged task time; no performance gain is
assumed from the source repair alone.

`record_planner_event` is the production planner callback. Both the native event
stream and the coordinator/control callback receive `native_incumbent_reference`
instead of the full payload. The result and accumulated events therefore retain
compact references, while the original complete capture remains durably
available. Other planner diagnostics retain their existing representation.

At materialization, `audit_capture_references` rejects raw/unregistered capture
events and verifies the registered references. The frozen recovery coordinator
adds a prefix/full `stage` to callback rows; canonical comparison removes only
that wrapper field and requires it to agree with the reference phase.

## Failure behavior and verification status

Capture serialization, persistence, reference, downstream event-sink and callback
errors set the existing sink-failure gate before propagating. This is necessary
because the frozen planner catches callback exceptions as instrumentation
failures. Further native dispatch closes; evidence is not silently omitted.
Final audit corruption adds explicit `capture_reference`/`native_sink` failures.
Previously valid physical fallbacks remain retained and the task cannot pass the
engineering gate. A failed completion audit supplies no acknowledgment.

The separate test owner prepares solver-free coverage for late planner return,
pre/post-lift boundaries, timing events, full capture/reference round trips,
metadata/bytes corruption, callback/sink failures, coordinator stage enrichment
and immutable completion timing. The implementation agent executes no tests.
Parent source-hashed check/review is required before any new native design; a
full eight-task repeat does not fit the remaining original dispatch budget.
