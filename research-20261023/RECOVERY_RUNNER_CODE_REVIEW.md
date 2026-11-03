# Operational recovery runner: bounded code review

23 October 2026. Independent static review for the next operational runner
package. This review owns this note only and performs no tests, native calls,
backend dispatch, fixture generation, cluster work or protected-data access.
The native gate remains deferred until runner checks and fixture locking.

## Acceptance contract

Derived from `RECOVERY_QUALIFICATION_PROTOCOL.md` and
`RECOVERY_COORDINATOR_RESULTS.md`; these are existing requirements, not new
scientific gates.

1. Preserve the supervisor's monotonic anchor established before interpreter
   launch. Coordinator search/completion/finalization cutoffs share it. Verify
   the fsynced result and hashed completion endpoint independently of cleanup;
   late, absent or malformed completion is censored.
2. Fail closed on parent/monitor/resource failure. Bound monitor calls, sample
   process-tree CPU/RSS at most0.25s apart and system pressure at most1s apart;
   enforce one worker/thread and5GiB RSS. Stop dispatch on resource failure or
   sustained low memory and terminate only owned process-group descendants.
3. Freeze source/model/case-generation, tariff/movement-order/split/reserve/fault,
   task identity, environment and native versions in a new namespace. Do not
   mutate historical frozen workers or qualification results.
4. Make attempt identity immutable and native/ledger evidence append-only. Carry
   forward88.20958837542922 charged CPU seconds plus all new setup, tests,
   failures, monitoring and repairs. Respect720s dispatch stop,900s cumulative
   ceiling, full32.5s launch allocation and shutdown reservation. Count supervisor
   CPU; missing final CPU evidence is conservatively charged rather than zero.
5. Resume skips completed success and failure attempts. Missing/corrupt/incomplete
   attempts block resume pending audited reconciliation; no automatic retry or
   in-place repair. Validate prior evidence hashes and terminal receipts.
6. Keep explicit freeze/self-test/run/analyze entry points. Solver-free checks
   must not import/call native backends. Native dispatch requires those checks
   and the later frozen identity-only two-case/eight-task matrix; this code
   package does not itself authorize native qualification.
7. Machine-readable gates distinguish physical witness validity, start submission
   from native processing acceptance, retained witness bill from later solver
   objective, and restricted/fixed-route bounds from full unrestricted evidence.
   Expose incomplete required paths and engineering censorship without changing
   the economic selection rules or declaring a performance result.

## Review state

The implementation files were not yet present when this checklist was written.
Substantive code findings and final static verdict will be appended after the
implementation is available. No execution evidence is claimed here.

## Check-supervisor static review

Reviewed `RECOVERY_RUNNER_CHECK_PROTOCOL.md` and
`run_recovery_runner_checks.py` before execution. Source locking includes the new
operational module transitively through the existing experiment/egglab source
inventory. Prior88.20958837542922s plus30s administration is carried forward.
The maximum elapsed/sampled/reaped-child CPU charge plus supervisor CPU is
conservative. Monitor subprocesses are bounded, and cleanup records surviving
owned PGIDs. No substantive accounting or source-lock defect was identified.

One ownership limitation requires attention in the forthcoming fixtures:
descendant PGIDs are retained only after ancestry is observed during sampling.
A newly detached session whose parent exits before observation cannot be
rediscovered from ancestry. Parent-death tests must synchronously establish owned
PGID evidence before injecting parent death and clean sessions on every path;
polling alone cannot establish that ownership claim. This was sent to parent and
implementer for the implementation/fixture review. No check was executed.

The parent subsequently added `EGG_CHECK_PGID_REGISTRY`; ownership fixtures must
fsync each newly created PGID before parent-death injection. Static readback
confirms registration is read before sampling and final cleanup, while malformed
registration records failure without skipping root/known-group cleanup. Missing
source paths now become source changes while retaining a terminal receipt.
This resolves the polling-only ownership limitation under the stated fixture
registration contract. No new check-supervisor blocker was found.

## Initial operational-module findings

Read the initial `src/experiments/recovery_qualification.py` while the implementer
was still preparing focused tests. Findings were sent directly to parent and
implementer; no source edit or execution was performed.

- `resource_step` detected an observed escaped descendant process group, but
  cleanup killed only the original root PGID. Retain and terminate every observed
  owned group when reporting that resource/ownership failure.
- `completion_endpoint` censored a timely result/marker first observed just after
  the deadline because of polling latency. The endpoint design must distinguish
  late serialization from delayed observation and keep result materialization
  independent of cleanup. This is conservative false censorship, not false pass.
- The worker's direct planner-event `native_append` sink did not set the shared
  sink-failure state. The core deliberately swallows record exceptions, so native
  calls could continue after evidence loss. Mark sink failure explicitly so the
  next dispatch gate closes and terminal evidence records it.
- `analyze` appended to the hash-chained ledger without owner serialization,
  allowing a concurrent run/analyze race. Serialize ledger mutation through the
  same owner mechanism. Include an explicit cumulative900s ceiling gate in the
  report.
- Core native build/start/optimize exceptions may become
  `native_search_failed` events with a retained feasible fallback and no top-level
  coordinator failure. The initial `finish` could treat that outcome as clean and
  continue dispatch. Propagate actual search failures into the engineering gate,
  except the prospectively expected setter-fault exercise. Do not blanket reject
  candidate alternatives or natural no-incumbent/no-plan outcomes.

Freeze is expressly described as externally budgeted; before its future use the
parent must supply bounded resource supervision and retained failed-freeze
accounting. This package does not authorize an unsupervised fixture freeze or
native launch. These initial findings are not a verdict on subsequent repairs.

## Repaired-source/check readiness verdict

Bounded static readback of the repaired runner and
`src/tests/test_recovery_qualification.py` found no remaining correctness blocker
to freezing the one prospectively authorized solver-free check, once the
implementer declares the sources stable. This is permission to prepare that
check under the existing protocol, not evidence of passing or native-launch
authorization. The reviewer performed no execution.

Observed repairs address the findings above: all observed owned PGIDs are
terminated and verified; post-fsync completion identity/hash/timestamp is sent
over a bounded pipe and retained in the receipt; direct planner sink failure
closes dispatch; unexpected native search failures become engineering evidence
while the expected setter fault remains distinct; analyze owns ledger mutation
and gates the cumulative ceiling. A genuine external bounded freeze receipt is
now required before native `run`, with its complete charge carried forward.

One additional cross-file mismatch found during readback was repaired:
`checked_sources` now accepts the actual check supervisor's owned/surviving-PGID
receipt schema, instead of requiring an absent `group_absent` key. The current
check is tied to source hashes, output hashes, ownership outcome and cumulative
charge; future fixture freezing cannot omit that check spend.

Native-log offsets now flush Python and process C stdio before and after native
calls. This improves attributable evidence but cannot by static review establish
actual backend processing; unmatched or ambiguous evidence remains unknown.
Independent analysis replays saved full-case witnesses and checks native binary
inventory/bounds metadata. Actual backend processing and40/80 behavior remain
deferred.

The focused tests block native imports during collection and each test, use fake
models/clocks/receipts, and exercise ownership with the existing real-process
helper only. The ownership fixture fsync-registers each new PGID before
parent-death action and kills/reaps captured processes in `finally`. Static
inspection does not replace the supervised test outcome or terminal receipts.

## First check and prospective minimal repair

The parent reports attempt01 passed39 tests, cumulative charge
121.05880295888622s, with every owned PGID absent. This reviewer performed no
execution. That check does not establish native behavior or authorize fixture
generation/native dispatch.

After that check the implementer identified a remaining same-task dispatch gap:
ordinary native search failures entered `native_state.engineering_events` and
the terminal receipt stopped later tasks, but worker `allowed()` did not consult
that list. A prefix failure could therefore permit full continuation within the
same task. The earlier static readiness verdict did not catch that distinction.

The minimal repair is to close `allowed()` when unexpected engineering events
exist, covering all later planner/native dispatch within the task. The
prospectively injected start-setter exception remains excluded from that list;
natural no-incumbent/no-plan outcomes and rejected raw/completed alternatives
retain their existing treatment. Parent has stated that the original source and
receipt will be preserved before a prospectively named repair02; no retry is
authorized by this review note alone. Minimal source/test readback is pending.

Repair02 static readback is complete. `native_event_is_failure` preserves the
existing event classification; `dispatch_allowed` adds the missing empty
`engineering_events` prerequisite. The actual worker event sink and every
subsequent planner/native gate use those helpers. Two focused cases drive the
same emitted-event → classification → saved state → gate path: ordinary setter
failure closes dispatch, while the expected prospectively injected setter fault
does not. Existing parent/sink/STOP checks still close dispatch independently.

The explicit attempt02 supervisor carries the first check's cumulative receipt
plus5s repair administration, verifies prior output/source-archive hashes, locks
the repair protocol, and preserves exclusive attempt identity. No remaining
blocker was found for the explicitly authorized second solver-free check after
sources are stable. No execution was performed by this reviewer. The result of
that check, all prior charges and the original first-check evidence must remain
part of future freeze accounting. Native fixture and processing claims remain
deferred.
