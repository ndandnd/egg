# Source-only freeze supervision revision 2

New `run_recovery_freeze_v2.py` preserves the historical
`run_recovery_freeze.py` byte-for-byte on disk. The failed native-v4 freeze,
known PGID 37089 and parent's separate successful absence reconciliation remain
immutable. This package creates source/tests/documentation only: no check,
fixture, lock, attempt, signal, solver or retry was executed.

The new copy changes the entry allocation guard to the checked runner's
`OUTER_ALLOCATION`, `DISPATCH_STOP`, `SHUTDOWN_RESERVE` and `CEILING` constants.
It therefore follows the approved cumulative 1800/1620/180 policy without
resetting carried spend. Current failed-freeze spend and reconciliation must
remain in the parent's authoritative next accounting. No new allowance is
created here.

Legacy `checked.cleanup` is replaced with the already reviewed
`run_admission_capture_budget_check.cleanup_receipt`, receiving absolute
anchor+32.5. The adapter retains every known PGID, leader return/reap state,
group state, cleanup deadline and diagnostic. An unexpected helper exception
keeps a conservative unknown-state inventory, never an empty successful result.
The first actual cleanup diagnostic becomes primary only if there was no earlier
failure; otherwise it is secondary. Worker-receipt and lock-validation failures
also preserve the earlier cause. Passing additionally requires no primary or
secondary error, confirmed absence for every recorded group and a reaped leader.

The new wrapper reuses the reviewed guarded output-audit helper so an output
hash failure can retain a failed terminal receipt rather than erase cleanup
evidence. A failed final child-CPU read likewise retains the primary/secondary
errors and ownership receipt, records child CPU as null and accounting as
incomplete/unresolved, and prevents passing. Only the available elapsed,
sampled and worker charge observations remain as a lower bound; parent accounting
reconciliation is required before authoritative subsequent carry.
Final allocation time is remeasured after these audits and remains
subject to 32.5 seconds. The existing command/source/path/identity, native-library,
memory/RSS/monitor, worker 30-second deadline, exit-observation and lock gates
remain. Monitor cadence and query behavior are unchanged. The guarded-worker
and watch-parent function body is unchanged; this repair makes no claim that
every possible monitor query will finish on time.

New dependency hashes include the reviewed cleanup wrapper, checked ownership
helper, immutable old freeze wrapper and this note. A future successful source-
bound check must include the new wrapper and its dependency closure before an
external freeze can use it.

`src/tests/test_recovery_freeze_v2.py` adds eleven fake-only cases: permission-denied
cleanup with primary monitor retention, unexpected helper exception, unknown
versus absent/reaped combinations, checked-runner budget boundaries and a complete
fake-supervisor terminal receipt, including final child-CPU failure. Native imports and real process launches are
forbidden. No existing test file, runtime/model/lift source or old wrapper changes.
These tests are **unexecuted**. The next step is a newly prospectively recorded,
exclusive source-bound solver-free check including these eleven cases and the prior
124 cases (135 total), followed by receipt review. No check or subsequent deliberate native
version is launched automatically by this note; numerical dispatch stops on the
current freeze failure.
