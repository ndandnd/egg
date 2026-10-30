# Focused recovery supervision repair

23 October 2026. Implementation only until the parent's separately budgeted check
is receipted. No test, native retry, fixture generation or numerical run was
executed by the implementation agent. The failed v1 task, lock and original source
at Git `269df001` remain evidence; this revision requires a new future source lock
and output namespace. Physical/native formulations, lift, coordinator and model
assets are unchanged.

## Bounded monitor sampling and accounting

`recovery_qualification.py` replaces separate 80 ms command limits with one shared
absolute sample deadline. Process and pressure commands consume the actual
remaining allowance; the complete sample must fit both a 0.24-second cap and the
original maximum 0.25-second gap since the preceding completed sample. The outer
supervisory stop at anchor+31 also clamps that deadline. Failed or incomplete samples still stop
dispatch; missing data are never interpreted as healthy.

The target sampling interval is prospectively changed from 0.20 to **0.05 seconds**
to start queries early enough to preserve deadline slack. For example, a prior
sample completing 0.01 seconds after its start leaves about 0.21 seconds for the
next shared sample, rather than the approximately 0.06 seconds a 0.20-second
schedule would leave. Pressure remains sampled at most one second apart. This
increases potential monitoring overhead and does not relax the resource policy.

`MonitorError` retains the actual command, allocated timeout, shared deadline,
context, original exception type and message. The STOP marker, in-memory primary
reason and terminal receipt retain this diagnostic, including `TimeoutExpired`
command provenance.

Monitor subprocess CPU is now measured around each sequential monitor command
with `RUSAGE_CHILDREN` before/after, including failing commands. The single-thread
supervisor does not reap native workers inside those calls. This avoids adding a
whole-run child-CPU delta that could double-count workers. The accumulator resets
per run, enters dispatch/hard-budget checks, and is reported separately from the
supervisor's own `process_time` in the final ledger charge. Fake commands yield no
child-CPU increment.

Preserve **169.35673816793766 seconds** of prior receipts unchanged. The parent
prospectively adds **20 seconds** as explicit retrospective reconciliation for v1's
unmeasured serial monitor CPU, and **20 seconds** for this repair package's
administration. Thus the pre-check total is **209.35673816793766 seconds**. These
are conservative allowances, not measured utilization or retroactive changes to
old receipts. The new check and its supervisor CPU must be added; the 900-second
ceiling, 720-second dispatch stop and shutdown reserve remain unchanged.

## Ownership and terminal audit

A permission-denied process-group existence probe is **unknown**, not absent.
Bounded TERM/KILL/reap/absence polling retains probe diagnostics and confirms
actual eventual absence or produces unresolved cleanup errors. Persistent unknown
state cannot pass cleanup, release ownership or enable further dispatch. Observed
owned groups and the existing parent-death watchdog remain in use.

The physical endpoint remains anchor+30. Supervisory stopping moves to anchor+31
to reserve 1.5 seconds within the existing 32.5-second outer allocation. Cleanup
receives the absolute anchor+32.5 deadline; TERM, reap and final absence waits each
use the smaller of their 0.5-second cap and the actual remainder. An unknown state
at that deadline is a failure, never an extra allowance or an absence claim.

`finish` caches its cleanup outcome and acknowledgment-close state before fallible
artifact work. Reentry does not kill a retired group again, close a reused file
descriptor, overwrite immutable artifacts or double-append a finish charge. An
already fsynced receipt is reused, and ledger append recovery checks the existing
matching finish record. The original STOP/monitor reason remains primary;
secondary cleanup and audit errors remain separate. A real interruption is not
invented to replace a preexisting monitor failure.

Errors after receipt fsync are retained as hash-chained `terminal_audit_error`
events instead of mutating the receipt. Such events block resume and analysis
pending explicit reconciliation, so an immutable successful receipt cannot hide
an engineering audit failure. If audit remains incomplete, finally records its
primary/secondary diagnostics and a provisional conservative worker charge,
records supervisor plus monitor-child CPU, and retains ownership. Provisional
charges require reconciliation, not blind addition to a later terminal charge.
Storage failure that prevents the ledger itself being written remains an
incomplete attempt; it cannot resume automatically.

## Prospective focused evidence

Parent execution subsequently passed all54 tests in2.04s on the single authorized attempt. Sources remained unchanged, all three owned groups were absent, and the cumulative charge is212.08502712584297s. See `RECOVERY_SUPERVISION_REPAIR_RESULTS.md` for exact accounting and scope. No native retry occurred.

The separate test agent owns `test_recovery_supervision_repair.py`. Regressions
cover shared deadlines and scheduling slack, timeout attribution, transient and
persistent permission-denied probes, cached cleanup/ack closure, artifact/ledger
retry, primary-cause retention through `run`/`finally`, and monitor-child CPU
accounting. The old operational suite has only the authorized mock-signature
adapter for explicit deadline arguments; assertions are preserved. The parent
will execute one bounded source-hashed solver-free check after review. Native
qualification remains failed/deferred until a separate repaired revision is
prospectively frozen and deliberately launched.
