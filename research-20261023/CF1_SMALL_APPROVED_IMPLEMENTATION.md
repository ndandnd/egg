# Approved CF1 singleton implementation (v4)

`cf1-small-approved-v4` delegates the reviewed v3/v2 ownership machinery for one
existing synthetic50997/40 CF1, seed17, day, no-fault mechanism check. The task
uses protocol revision4. The inherited frozen modules and old v3 dispatch block
are unchanged. No model data or fixture is generated.

The serialized context temporarily installs total1920s, dispatch1740s and
shutdown180s, package start1509.9511370494984s, limit165s and
cap1674.9511370494984s. It retains30s for20s analysis plus10s closure, and45s for
supervision. Every binding is restored on exit/failure. The original physical
and worker-ACK endpoint60s, stop61s, outer62.5s and charging windows remain.

The worker's existing timestamp precedes `os.write`; it does not independently
prove when transport completed. A v4-only controller wrapper calls the original
nonblocking `receive_ack` and, only after a new complete ACK was actually read,
captures controller monotonic time and exclusively writes a fresh flat
`controller-ack-observation-v4.json`. It records task/lock/anchor identity and the
exact raw wire digest. Repeated reads without new bytes do not rewrite it;
identity, read and durable-write failures propagate without resetting errors.
The write occurs before the existing finish artifact inventory.

The existing exclusive report-writer seam crosschecks that saved observation
against the task attempt, terminal ACK, lock and terminal artifact digest. A
complete ACK observed by anchor+60 is sufficient transport evidence. Missing,
invalid or later observation fails qualification with timing unestablished;
later observation makes no claim that the worker sent late. Historical receipts
and the original completion endpoint are untouched.

The affected solver-free test uses AST-loaded source and inert dependencies. It
targets restoration, singleton policy, scoped limits, source gates, actual-read
observation, identity/error retention and conservative analysis. The gate adds
the new module/test and constructive-controls dependency to inherited required
source/test hashes. Broad historical tests are hashed, not rerun.
The source gate accepts only `cf1-small-approved-checks/attempt01`, revision4,
the exact approved pytest command and sole affected executed test, with a v4
result policy and matching command digest. Matching source hashes alone cannot
substitute for this new affected check.

This source-only handoff has not imported, executed, tested, frozen or dispatched
the implementation. Parent source review and the approved affected check precede
any native work. Approval is recorded separately in
`cf1-small-approved-v4/approval.json`.
