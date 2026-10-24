# Approved-budget validation: checks pass, external freeze fails

The user approved **30 CPU minutes total**, preserving one local single-thread
worker, 5 GiB and all previous charges. The runtime changes only the two budget
constants. Two synthetic test spends now derive from the live dispatch limit;
the same assertions remain. Six helper tests exercise both old and new check
launchers, producing **124 passing solver-free tests**. The old launcher and
all failed attempts remain unchanged.

The passing check is at `admission-capture-checks-budget/attempt01`. Parent and
independent review verified 160 current source hashes, command/output/artifact
hashes, no drift/errors, leader reap and absence of all three owned groups.
Its cumulative charge is **610.9167105017234 seconds**, including the single
shared 20-second administration allowance. This establishes engineering behavior,
not 80-trip timing, learned prediction quality or economic improvement.

## Failed external freeze

Exactly one external source/fixture freeze was launched in
`recovery-phase1-v4/freeze-attempt01`. Its guarded worker and inner freeze returned
zero and produced a lock for the unchanged 50997/40 and 50999/80 engineering
cases. No solver task launched. The supervisor then reported an actual OS
`PermissionError` during its legacy `checked.cleanup` path. It recorded no
monitor failure or source drift; observed peak RSS was 199,147,520 bytes.

The legacy helper catches missing-process errors but lets permission errors
escape its signal/probe/escalation operations. Because it never returned,
`termination` retained initialized empty arrays. These are **not absence proof**.
The receipt lacks a traceback or syscall stage, so the exact failed operation
is unproved. This was not an automatic approval-review rejection.

Parent performed one separately recorded, read-only reconciliation of the sole
recorded PGID 37089. Signal-zero reported absent; a successful process snapshot
including the reconciler found no matching leader or group members. No signals
were sent. See `freeze-attempt01/cleanup-reconciliation.json`. This establishes
later absence and leaves the original freeze failed. It does not retroactively
provide timely cleanup or authorize its lock for a native run.

## Conservative accounting

The failed receipt's nominal cumulative charge is 612.3993446267449 seconds.
That includes its 1.1598571250215173-second allocation and 0.322777-second own
supervisor charge. Its child/worker CPU is already dominated by that allocation
and must not be added again. Because postreceipt watchdog CPU was not reaped,
the nominal receipt alone is an incomplete upper accounting bound.

The authoritative carry in `recovery-phase1-v4/accounting.json` is now
**718.8639492101057 seconds**, computed as:

```
610.9167105017234  complete pre-freeze carry
 32.5             full freeze allocation, replacing the nominal 1.159857...
  0.322777        recorded own supervisor CPU
 75.015458666     conservative possible single-watchdog CPU interval
  0.10900304238229991  measured read-only reconciliation charge
```

The possible-watchdog allowance runs from the observed guarded-worker exit to
the later absence reconciliation. Source inspection establishes exactly one
watch-parent, which spawns no children, after the guarded worker/inner freeze
have exited; thread limits remain one. This is an intentionally overlapping
upper reservation, **not measured CPU utilization**. The old nominal receipt
stays intact. No additional administration or 10-second audit charge is added;
source/closeout work uses the existing shared 20-second allowance. The approved
1800/1620/180 limits remain, with 901.1360507898943 seconds before dispatch stop.

## Next action

Stop-on-first-failure was honored: no native run, repeated freeze or test retry
followed. A new source-only supervisor revision is being prepared with the
already reviewed bounded cleanup helper, absolute cleanup deadline, persistent
known-group/reap/error evidence and approved budget constants. The old freeze
wrapper must remain immutable because historical hash chains bind it. The new
wrapper and fake regressions require independent review and one prospective
source-bound check before a deliberately versioned external freeze can occur.
Keep the original cases, task count and clocks. Approval of the total budget
persists; do not ask for it again or reset the ledger.
