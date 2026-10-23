# Focused supervision repair review

23 October 2026. Independent static review against
`RECOVERY_PHASE1_REPAIR_PLAN.md`. This note owns no implementation/test sources
and performs no execution or native retry.

Carry169.35673816793766s from the failed v1 qualification and prior work. The
parent prospectively reserves20s administration and one30s solver-free check;
all actual check/supervisor charges and failed work must remain accounted.

Review scope is the original at-most0.25s monitor policy, actual timeout command
and allocated-time provenance, EPERM-as-unknown bounded owned-group cleanup,
idempotent terminalization preserving primary and secondary failures, and
complete conservative spend/resume semantics. No unrelated infrastructure or
native qualification gate is added. Source/test readback is pending.

## Focused static findings and repairs

The outer check supervisor initially lacked explicit sample-gap failure and
permission-denied existence handling. It now enforces the0.25s gap, supervisor-PID
snapshot completeness and finite0..100 pressure; a scoped restored probe wrapper
records EPERM as unknown/present during bounded cleanup. No remaining blocker was
found in that check-supervisor readback.

The core shared-deadline command wrapper retains command/context/allocated timeout
and does not give the pressure query a fresh budget. Group probing is tri-state;
bounded cleanup preserves permission diagnostics and never calls unknown absent.
The parent found that the old0.20s nominal scheduling target would leave only
about0.05s under the completed-sample deadline. The repaired nominal interval is
0.05s while the original0.25s maximum remains enforced; its monitoring overhead
must remain visible and charged.

Finish now caches owned-group cleanup and acknowledgment close, reuses immutable
receipts and deduplicates the terminal ledger event. This avoids repeated task
charge when receipt writing succeeds but ledger writing fails; later audit CPU
belongs to supervisor accounting. Review identified that post-receipt
`terminal_audit_error` entries initially did not block resume/analyze. They now
explicitly block pending reconciliation, preserving immutable success receipts
without allowing a recorded engineering failure to pass or continue.

## Accounting clarification

Review identified that historical supervisor `process_time` excluded monitor
subprocess CPU. Parent prospectively adds20s conservative historical monitor
reconciliation and20s current administration, making the pre-check carry
209.35673816793766s. Historical receipts remain unchanged; the reconciliation is
an allowance, not measured utilization.

The repaired `monitor_command` brackets each sequential monitor subprocess with
`RUSAGE_CHILDREN` and accrues its delta in `finally`. Run resets this accumulator,
includes it in dispatch/hard-budget checks, and records supervisor process CPU
and monitor-child CPU separately with their sum as the ledger charge. Worker
reaping occurs outside that bracket, avoiding whole-run child-CPU double count.
Resume sums the recorded charge once. Static inspection found no accounting API
drift or worker double-count defect in that wiring.

Final focused regression/source stable readback remains pending. No check or
native execution was performed by this reviewer.

The parent also identified an outer-allocation mismatch: permitting worker
supervision through32s followed by up to1.5s cleanup exceeded32.5s admission.
Static readback confirms the minimal correction: supervisory stop/sample cutoff
is now anchor+31s, physical endpoint remains30s, and `finish` supplies the absolute
anchor+32.5s cleanup deadline. TERM/reap/absence phases clamp to its remainder;
unknown at exhaustion remains failure. Partial terminal audit records its
primary/secondary causes and provisional worker charge, preserves supervisor
accounting and blocks resume pending reconciliation.

## Final stable readback: solver-free check ready

Reviewed the final runtime,13 focused regression cases, authorized existing-test
deadline-argument adapter, parent check supervisor and prospective protocol.
No remaining blocker was found to the single source-hashed solver-free check
under the209.35673816793766s pre-check carry. No reviewer execution occurred;
source/test files were not edited by this reviewer.

The focused additions cover shared query deadlines/timeout provenance,
scheduling slack under the unchanged0.25s policy, EPERM unknown/transient
absence/persistent uncertainty, one cleanup and acknowledgment close, unchanged
receipt/task charge across audit retry, post-receipt ledger failure blocking
resume, per-query monitor-child CPU with accumulator reset/ledger sum, and
absolute32.5s cleanup exhaustion. The existing operational suite is included
because these changes affect its monitor/run/finish/receipt interfaces; unrelated
physical/coordinator suites are not repeated.

The parent check supervisor retains source/prior-evidence/output hashes, one
exclusive attempt, bounded healthy monitoring, registered-group cleanup and
conservative allocation/child/supervisor charge. Static readiness is not a test
pass or native retry authorization. Any future native revision still needs its
explicit new source/check/fixture/accounting lock and output namespace while
preserving the failed v1 evidence and cases.
