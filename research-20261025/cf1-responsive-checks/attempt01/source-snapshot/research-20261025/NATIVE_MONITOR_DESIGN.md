# Native supervision: separate control service from resource probes

25 October 2026. Static design only. No implementation, import, hash audit,
test, process launch or native retry. A new policy and namespace require parent
review; all v5e artifacts remain unchanged.

## Diagnosis and evidence

Source08 passed21 tests/61 subtests. V5e metadata passed with6.79046s elapsed,
10.266245s charged and closed PGID14802. Its reconciled postfreeze total was
2537.9429304233154s, before the subsequent failed owner and its closure charge.
That number must not replace the parent's next reconciled carry.
The parent has now reconciled the failed owner and closure to2541.8243213823207s,
leaving234.8991282486953s before package end2776.723449631016.

The actual owner receipt at
`research-20261024/cf1-entry-repaired-v5e/entry-owner-attempt01/owner-receipt.json`
records controller15112 returncode-15, entry_gate_issued=false, absent/reaped
owned group, elapsed1.421138959005475s and conservative charge1.8813909590054751s.
Its observations-complete flag remains false. The primary error is
`memory_pressure: Shared monitor sample deadline exhausted`, timeout0, after
the process snapshot consumed the shared0.24s sample budget. No numerical
Popen or output prefix was reached. Entry20s did not address this bottleneck.

The source has four coupled waits:

- `OwnerSupervisor.run` calls synchronous `_sample` before reading its socket;
  `q.monitor_sample` runs ps and then memory_pressure under one deadline.
- `_gate(prelaunch)` starts another full sample after receiving the controller's
  CPU timestamp. This consumes the client's0.3s response allowance and the
  conservative suffix, whose permit expiry is also capped by
  `request_sample_time + 2.5/(capacity+2)`. The0.1s permit lifetime begins at
  issue; it cannot compensate for an already old request.
- Controller `q.run` probes resources before reading the completion ACK. A slow
  probe can delay observation of a timely complete ACK beyond the60s endpoint.
- `EntryClient` sends runtime status only after a monitor's `communicate()`
  completes. Extending probe time alone conflicts with the owner's0.25s status
  age, its process-sample gap, and `q.resource_step`'s separate0.25s sample gap.

This is an operational observation/control failure, not CF1 infeasibility.

## Options

Increasing entry allocation alone has now failed. Giving each synchronous
command1s would still block socket/ACK service, break0.3s requests and0.25s
freshness, and require a larger funding tail. Returning cached data as if freshly
sampled would hide these failures and is unacceptable.

A faster in-process OS collector could retain0.25s resource freshness with a
smaller code change, but its available fields, lifetime accounting and actual
latency have not been established. Treat it as a later alternative, not an
assumed fix. A monitoring thread would also require changing the current
single-thread identity contract and synchronizing global bindings.

Choose single-thread control loops with an asynchronous probe state machine in
the existing external owner, with no additional Python monitor process or
thread. Keep `threading.active_count()==1` and the owning-thread identity checks
in both owner and controller. This removes duplicated owner/controller OS probes
and keeps the exact worker, nonce, roots, source closure and registered-spawn
rules. It requires a small, explicit new supervision policy, not a timeout edit.

## Chosen bounded implementation

The owner starts only the two fixed resource commands, concurrently, with
nonblocking stdout/stderr. Register each PID/process group before accepting any
result; cap output, kill/reap on failure and include all helper CPU/RSS and
cleanup in accounting. At most one probe pair is live. Each pair has a1s
deadline, clipped to the current phase deadline. Pair results carry sequence,
start/end timestamps, command identity and complete owned-process inventory.
Neither command's result is usable as a complete pair by itself.

The owner selector services control sockets, probe pipes, controller exit,
signals and deadline timers between bounded chunks of parsing. It must not call
blocking subprocess.run/communicate or start a fresh probe inside `_gate`.
Use a separate bounded resource/telemetry channel so unsolicited sample records
cannot violate the existing strictly request/response permit decoder. Bind this
channel and its records to the same root/nonce/task/controller identity.

The controller uses a narrow new supervision loop which polls ACK, owner
telemetry and child exit independently of resource completion. Send actual
self/waited-child rusage on a0.05s target cadence; retain the0.25s maximum
control/status age and fail closed on missed service. Continue actual monotone
sequence checks. A timer schedules the61s stop regardless of probe state;
cleanup remains clipped to the original62.5s outer deadline. A complete ACK is
timestamped when fully read, before optional probe parsing; its existing60s
admission test and transport witness remain unchanged. Never backdate an ACK or
credit time spent waiting for monitoring.

Consume each resource record once. Do not refresh its timestamp on cache reads
or reset `item.last_sample` merely because the control loop ran. Leave historical
q unchanged: the new scoped adapter must explicitly separate control freshness
from resource-record validation; otherwise its current0.25s resource_step gap
will still stop the run.

Resource policy is explicit: probe duration<=1s, completed-pair gap<=1.25s, and
record age measured conservatively from the earliest probe START, not delivery.
These imply a maximum usable resource age2.25s immediately before the next
pair completes. Enforce that age directly as well as the completed gap. This
changes resource detection latency and must be recorded in the new policy;
it does not change0.25s control freshness or any scientific endpoint. Reject
late/partial/reordered samples, unknown descendants and bad memory observations;
RSS and memory-pressure observations remain sampled, not continuous guarantees.

Before entry admission require a complete owned-process sample, no unexpected
descendants, no controller helpers left live, fresh controller rusage, and enough
entry budget for the sample's uncertainty plus suffix2.5s. Wait for a probe
asynchronously if necessary, then request NEW controller rusage; do not reuse the
timestamp from before the wait. Issue the existing one-use permit only after
this check. Preserve its0.1s maximum lifetime, capacity-scaled suffix expiry,
entry deadline, durable readback, exact final Popen interception and funding
recheck. Slow final filesystem/readback may still fail closed.

## Funding and ownership obligations

Let C be the independently recorded CPU capacity. A conservative uncertainty
rate K=C+3 permits separately charged owner and two probe channels; use this
loose bound until a tighter registered-thread bound is justified. Every live
check adds at least `K * max(resource_start_age, controller_status_age)` to the
existing conservative observed charge, without subtracting elapsed/precharge
overlaps. Also reserve `K * control_deadline` until the next0.25s service deadline
and a separate conservative cleanup tail `K * 1.5s`, together with the remaining
native allocation and final analysis reserve. Avoid charging the same measured
counter twice as an exact observation; conservative overlap is labelled and
never refunded. Terminal waited CPU cannot repair missing live observations.

The full2.25s resource allowance is not automatically affordable. Entry20s or
the remaining package may impose a smaller usable age on this host. Compute
the admissible age from current remaining funds; stop before its expiry rather
than assume the next sample will be fast. Keep owner CPU limit15s inside
supervision45s, package350/end2776.723449631016 and global3000/2820/180 until
review explicitly changes them. A collector that cannot fit these provisions
does not qualify. No new parent-budget question is implied by this design.

Register every allowed worker/probe spawn and retain observed groups through
cleanup. Longer sampling delays discovery of unexpected descendants; trusted
frozen code and exact spawn registration remain essential. This is not kernel
containment against hostile native fork/escape behavior, either before or after
this change.

## Meaningful qualification, before numerical work

Parent's prospective provisions are30s source (including its closure),15s
non-numerical primitive/integration (including its closure),25s metadata,20s
entry,62.5s native,45s supervision and30s finalization:227.5s total. From the
reconciled carry this nominally ends2769.3243213823207, leaving7.3991282486953s
before the unchanged package ceiling. This arithmetic is a proposal, not a
manifest or launch clearance. Capacity tails, actual helper CPU, helper RSS and
control-service feasibility must be funded and qualified; do not assume they
fit that nominal margin or silently enlarge the native endpoints. Retain one
numerical worker, one native thread and aggregate5GiB sampled RSS limit.
The parent must freeze exact commands/bytes and verify actual carry plus all
remaining reservations and uncertainty bounds before executing a phase.

1. Fake-clock/pipe cases delay ps, memory or both across0.24s,0.3s and1s while
   delivering partial ACKs/control messages. Assert timely control service,
   complete-ACK observation on both sides of60s,61s stop and62.5s cleanup;
   delayed parsing never makes a late ACK timely.
2. Check resource START-age boundaries, slow first samples, unchanged cached
   sequence, missing/reordered status, exhausted CPU tails, multiple capacities,
   root changes, helper failure and one-use/expired permits at final Popen.
   Retain primary and cleanup failures; no success from partial samples.
3. One metered non-numerical owned stub validates real socket/probe responsiveness,
   helper ownership/reaping and CPU/RSS accounting under injected probe latency.
   Measure rather than assume owner CPU15s/control0.25s viability. No solver,
   fixture inference, native worker or source/hash audit loop is needed.

These tests can qualify transport/accounting behavior under their conditions.
They cannot establish hard real-time scheduling, instantaneous memory bounds,
hostile-code containment, actual CF1 mechanics or successful runtime timing.
Keep all v5e failures and incomplete-observation flags. Review and a fresh bound
policy/source gate/metadata freeze are required before any native attempt.
