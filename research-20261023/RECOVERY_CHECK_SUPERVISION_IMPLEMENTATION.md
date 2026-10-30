# Admission/capture check supervision revision 2

24 October 2026 UTC. New wrapper
`research-20261023/run_admission_capture_checks_v2.py` only; runtime, tests, old
wrapper and its failed attempt are unchanged by the implementation agent. No
check, native solve, fixture, cluster task or commit was executed here.

The sole destination is exclusive
`admission-capture-checks-v2/attempt01`. Carry 565.0277991267408 seconds from the
authoritative failed-check accounting and add the prospective 20-second
administrative allowance: **585.0277991267408 before the actual check**. Existing
900/720/180 hard/dispatch/shutdown limits remain. There is no automatic retry or
native launch after a pass.

## Shared supervision and owned cleanup

The wrapper imports the current runner's `monitor_deadline`, `monitor_sample`,
`stop_owned`, `group_probe` and diagnostic behavior. It reuses only the checked
ownership-registry and descendant-row functions from the old helper; it does not
call the old monitor or cleanup implementation. Registered detached test groups
are intentional, so the native policy rejecting unexpected groups is not used.

`sample_owned(proc, groups, registry, anchor, last_completed)` uses one absolute
sample deadline: minimum of tick+0.24, last completed sample+0.25 and anchor+30.
Process and memory queries share it. Sampling starts on a 0.05-second target;
slow queries are not excused. Initial pre-dispatch memory sampling is retained as
the first completed-sample boundary. Invalid memory, late samples, RSS above
5 GiB, sustained low memory and the 30-second check wall limit fail closed.

Every launch and completed sample durably records its owned PGIDs, including
explicit registrations and observed detached descendants. Before cleanup, the
wrapper also records the retained inventory, leader return state and primary
failure. `cleanup_receipt(proc, groups, deadline)` calls the shared cleanup once
with absolute anchor+32.5. It retains inventory, helper result, observed reap
state, probe diagnostics and every cleanup error even if that call raises.
Subsequent probes are observational; no automatic second cleanup/kill attempt is
made. Permission denied remains unknown; unknown/present groups or an unreaped
leader cannot satisfy the terminal gate. Missing confirmation requires separate
later reconciliation and does not become an empty successful termination.

`retain_error` preserves the first diagnostic as primary and appends later
cleanup/audit diagnostics separately. A query timeout therefore cannot be
replaced with a fictitious interruption or obscured by cleanup failure.

## Check binding and accounting

The exact pytest argv contains the four existing runner/supervision/cutoff/
admission modules plus `src/tests/test_check_supervision_v2.py`. It runs in
`.venv-local`, with all numerical thread settings at one and the explicit owned
PGID registry. Importing the wrapper performs no dispatch. Existing attempts are
never overwritten, including incomplete or failed ones.

The exclusive fsynced attempt binds all `src/egglab` and `src/experiments` Python
sources, the five test modules, wrapper/helper sources, new parent protocol,
implementation note, amendment plan and exact argv. Prior accounting evidence is
verified before adding hashes of the failed check receipt/output and separate
cleanup reconciliation. Before the terminal receipt, the wrapper checks source
hashes again and hashes stdout/stderr plus the flat attempt/resource/ownership
artifacts. Output-audit errors retain the primary failure, add secondary
diagnostics and explicit missing hashes, and allow a failed terminal record.
Preflight failure still produces an
explicit failed attempt/terminal record when storage remains writable.

`accounting` charges `max(allocation elapsed, sampled owned-tree CPU, observed
RUSAGE_CHILDREN CPU) + supervisor process CPU`. Total observed children includes
pytest and serial monitor children. The q monitor accumulator is reset and
retained as a diagnostic only; it is not added again. Failure and cleanup time
remain inside the allocation. Administrative allowance is conservative, not a
measurement of utilization. The outer allocation, ownership/reap confirmation,
source integrity, exit status and cumulative ceiling all participate in passing.
An unavailable final child-CPU observation is explicitly null with
`accounting_observations_complete=false`; retained charges are then only the
known lower bound. Such a failed receipt needs separate accounting reconciliation
before its spend can become an authoritative subsequent carry.

The test owner prepares deterministic fake-clock/monitor/cleanup/accounting
checks. No executions were performed by this agent. The parent must review and
freeze exact sources before the one deliberate check. A passing check supplies
no native latency, qualification or scientific result; another native package
needs a feasible prospective budget and explicit evidence limits.
