# CF1 v5 owning-entry source design

24 October 2026. Source implementation and inspection only. No import, test,
subprocess, freeze, fixture/model read, controller, native worker, numerical work,
cluster operation or commit was performed by this implementation subtask.
`src/experiments/cf1_entry_owner.py` is prospective code, not a qualified runtime
receipt or launch clearance. The sole combined fake test belongs to the separate
v5 review/test subtask.

## Ownership and independent roots

`OwnerSupervisor(directory=BASE/entry-owner-attempt01, roots=..., task=...,
output=BASE/runs).run(controller_base_command)` is the independent owning parent.
It accepts only the v5 `run` controller command, never a worker command, and does
not retry. `BASE` is the fresh v5 namespace; historical namespaces remain unused.

Before creating the controller, the parent establishes its monotonic anchor,
process-CPU and waited-child-CPU baselines, OS CPU count, fresh random nonce,
independently retained lock/freeze/account hashes and cumulative total, exact full
task, output and reviewed base command. It durably publishes exclusive
`BASE/entry-owner.json`. A socketpair descriptor is the live handoff transport.
The parent appends the freshly generated owner FD/root/hash/nonce CLI options to
the reviewed base command. `entry-owner-attempt01/controller.json` binds its exact
resulting argv and child PID to the already published root. Generated transport
options are distinct from the independently frozen base command; putting the
root hash inside its own hashed argv would create a circular binding.

An initial socket `ready` follows durable child identity publication. The child
cannot race ahead of that publication. `EntryClient` checks the root bytes,
retained digest, nonce, parent PID, controller PID, output, full task, roots,
policy, allocation constants and CPU count. It repeats these checks through the
final worker gate. Changing any binding, an absent owner, a broken/late channel
or an existing partial namespace blocks the launch.

## Preparation, exact precharge and actual resume

The wrapper enters `owner.entry_scope()` around preparation and execution. It
prepares under a temporary `adapter.bound60()` and leaves that context before
`adapter.run()` enters its own stateful bound. Under the installed real q policy,
`precharge(output, policy=..., task=..., lock_sha256=...,
postfreeze_total_s=..., budget_lock=...)` does all of the following:

1. Verifies the independently retained identity and postfreeze total, with no
   prior launch or owner precharge in the real hash-chained ledger.
2. Calls the real `q.resume_state` and requires exactly that postfreeze total and
   no completed task.
3. Appends one durable `supervisor_cpu` event with phase
   `whole_entry_precharge`, charge exactly 7.5 seconds, `nonrefundable: true`,
   owner-root path/hash, nonce, controller PID, full task, output, lock and policy.
4. Reads back the entire ledger and calls the real resume consumer again,
   requiring exactly the former total plus 7.5. Any partial append remains;
   another invocation cannot charge or launch again.

The actual adapter/q dispatch guards therefore consume the precharge. The
wrapper's funding callback independently validates the semantic event and the
unchanged prepared prefix, and rechecks cumulative/package funding. After the
original q launch appends its launch event, funding validation permits precisely
that one expected tail; calling the ordinary resume consumer at that intermediate
point would correctly fail because no terminal worker receipt exists yet.

## Live observation and the final Popen boundary

The parent continually uses the reviewed q complete process/memory samples with
the 0.25-second observation-gap condition, including the first interval from its
own anchor. It retains every observed owned PID/process group. Before native
handoff, unexpected descendants, parent/session mismatch, unknown observations,
RSS or memory-pressure failure block execution and trigger owned cleanup.

Within the child entry scope, Popen accepts only the exact existing q process and
memory monitor commands. Each pre-native monitor is registered over the live
channel before creation. It cannot detach its session or use a shell/preexec
hook. The client retains its real Popen object and must observe/reap every such
helper before the final gate. The parent verifies the complete registered helper
inventory and independently samples an entry tree with no remaining descendants.
The child reports actual process-lifetime `RUSAGE_SELF` and
`RUSAGE_CHILDREN`, retaining short-lived waited helper CPU from interpreter
startup onward. These are trusted frozen-source instrumentation, not fabricated
owner timestamps or independently observed ACK timing.

`launch_guard(..., delegate=original_adapter_launch, funding_check=...)` requests
one parent permit before delegating to the unchanged original q launch body. Its
scoped Popen interception runs after the adapter has translated the legacy argv
to exactly `experiments.cf1_entry_repaired worker`. It accepts that one exact
task/output/lock/controller/ACK command, checks that the original native anchor
already exists, revalidates funding and durable permit bytes, and checks the
permit expiry immediately before the true Popen call. Another Popen or changed
argv fails. All temporary Popen bindings and locks restore on every exit.

## Conservative body and suffix

The complete 7.5-second entry allocation includes a **2.5-second conservative
suffix**, selected by the parent within the unchanged allocation. This supersedes
the initial suggested 0.5-second suffix: it does not add budget or extend any
native endpoint. The body is

```
max(owner elapsed, sampled tree CPU,
    reported controller CPU + reported reaped helper CPU)
    + actual owner CPU + actual owner monitor child CPU
```

The parent requires body plus 2.5 <= 7.5. Thus at most 5 seconds remain for the
observed body. A permit expires no later than all of:

```
parent issue time + 0.1 seconds
controller resource sample time + 2.5 / (os.cpu_count() + 2)
owner anchor + 7.5 seconds
```

The physical capacity bound applies only to the unobserved transport/publication
and handoff suffix. Its extra two slots conservatively allow the separately
counted owner and monitor channels. Expiry starts at the earlier controller CPU
sample, so the parent's final OS sample and permit publication consume the same
suffix. A slow sample, filesystem, transport or final funding readback can make
the permit unusable; it then fails closed. There is no assumption of a four-core
machine, no all-core multiplier on the entire entry body, and no credit for
overlap after the original native clock has started.

After the permit is consumed, the entry scope continues to allow only the fixed
q monitoring commands without reusing the expired entry handshake. Existing
native monitoring keeps its original 60/61/62.5 clocks and full accounting.

## Live whole-package funding after handoff

After each real registered runtime monitor's `communicate()` has completed and
the process is reaped, the child sends one small one-way status containing actual
process-lifetime self/waited-child CPU, sample time, sequence, and the unchanged
nonce/root/full-task/controller binding. No numerical callback is changed. The
parent validates monotonic resources, identity and message order, independently
samples the live owned tree, and rejects absent/stale status beyond 0.25 seconds.
The parent input decoder accepts multiple framed status records while client
request/response handshakes reject trailing or pipelined replies.

The parent requires actual own CPU plus its monitor CPU <=15 seconds, explicitly
inside the existing 45-second combined supervision provision. This is no new
allocation; q retains its original 45-second prospective reservation, while all
actual internal and external spending is aggregated by the live whole-package
guard. That guard conservatively computes

```
postfreeze total + 7.5 entry precharge
    + max(owner elapsed, observed tree CPU,
          reported controller self + reaped children + sampled active other CPU)
    + actual owner CPU + actual owner monitor CPU
    + (physical CPU count + 2) * report age
```

It includes the remaining original 62.5-second native allocation, then requires
30 seconds for analysis/final closure plus 1.5 seconds for immediate owned cleanup
inside the unchanged package cap. It also enforces the 1740 dispatch stop and
1920 hard ceiling with the full 180-second shutdown reserve. Recorded work is
never subtracted for overlaps. A report that is stale, incomplete, out of order,
over provision or insufficiently funded stops the owned tree before further work.

This intentionally has no background heartbeat thread. If entry, active native
supervision or finalization stops producing the registered runtime monitor
statuses for more than 0.25 seconds, the parent fails closed. Whether the frozen
small-case implementation can maintain that interval is an operational question
for future separately authorized evidence, not a timing claim from source review.

## Cleanup, accounting and limits of this source packet

The owner continues supervising even if imports, preparation, transport or the
entrypoint block. Stop signals are recorded without interrupting the Popen/PID
publication boundary. It subsequently terminates all observed groups and reaps
the controller through `q.stop_owned`. Primary failures and cleanup/accounting
secondary errors survive in an exclusive owner receipt. Missing observations
produce unresolved accounting, never an invented zero charge or a success
certificate. A controller failure or missing entry handoff fails the owner.

The owner receipt retains actual waited descendant CPU, its complete observed
elapsed interval, sampled peak CPU, parent CPU and parent monitor CPU. A positive
external final tail and reconciliation with existing q ledger charges are still
required; the receipt explicitly says `reconciliation_required: true`. Overlap
between a conservative precharge and later actual charges cannot be refunded.

Coverage assumes the independently frozen, reviewed import closure and registered
spawn channels, with numerical imports and detached entry children excluded.
Python Popen interception and sampled ps ownership are not kernel containment
against hostile native forks or arbitrary modified interpreter startup code.
No such hostile path is identified in the inspected trusted q/campaign entry
imports. This source packet does not establish actual runtime timing, native
qualification, successful physical CF1 behavior, or permission for another phase.
