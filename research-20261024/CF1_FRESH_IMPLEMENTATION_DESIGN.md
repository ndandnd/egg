# Prospective CF1 entry repair: implementation design only

Date: 2026-10-24. Status: source-inspected proposal; no implementation,
qualification, timing proof, metadata freeze, entry preparation, or native
dispatch has been performed by this packet. The parent protocol will specify
the final authorization and receipt identities. Historical v3 remains disabled;
historical v4 failed before launch and its stopped state and artifacts are
immutable. This proposal does not reopen either attempt.

## Prospective identity and budget

- New module: `src/experiments/cf1_entry_repaired.py`.
- New test: `src/tests/test_cf1_entry_repaired.py`.
- New policy: `cf1-entry-repaired-v5` (subject to the parent protocol).
- New namespace: `research-20261024/cf1-entry-repaired-v5`.
- Exact future source-check namespace:
  `research-20261024/cf1-entry-repaired-checks/attempt01`.
- Current reconciled carry: `1527.8351450899538` seconds.
- Additional package cap: `175.0` seconds; absolute package end:
  `1702.8351450899538` seconds.
- Global hard ceiling / dispatch stop / shutdown reserve: `1920 / 1740 / 180`
  seconds. These are cumulative limits, not another package allocation.
- Prospective phase ceilings: source check 20; metadata freeze 10; whole entry
  7.5; worker outer allocation 62.5; supervision 45; analysis 20; final closure
  10 seconds. Their allocations sum to 175 seconds. Future observed charges
  and complete reconciliation remain required; allocating a phase is not proof
  that the phase met its cap.

Keep the adapter's final reserve at 30 seconds, explicitly representing the
20-second analysis allocation plus 10-second closure allocation. Reducing its
reserve to 20 would omit closure from the existing next-worker package guard.
The inherited 60-second endpoint, 61-second stop, and 62.5-second outer worker
allocation are unchanged.

The task remains exactly one inspected CF1 engineering50997/40 case, seed17,
seconds60, faultNone, with `protocol_revision: 5`. Derive its fresh ID from that
entire task using the existing stable hash. Do not reuse a v4 task ID, output,
lock, source receipt, or output-prefix initialization. No fixture generation or
claim about engineering80, comparative quality, optimality, or generalization.

## Scoped reuse of unchanged v4 ACK and analysis code

The v4 observer and transport analyzer resolve `POLICY`, `task_matrix`, and
`ACK_OBSERVATION` from the v4 module's globals when invoked. Rebinding only the
adapter or native worker is insufficient. Copying or weakening those functions
is unnecessary.

Use a private v5 configuration context with the following ownership order:

1. Acquire a new nonblocking v5 lock, then acquire the original v4
   `_CONFIG_LOCK` nonblocking. Failure changes no configuration.
2. While holding the original v4 lock, save the exact original values and bind
   v4 `POLICY`, `PACKAGE_START`, `PACKAGE_LIMIT`, `PACKAGE_CAP`, `task_matrix`,
   `checked_sources`, and `ACK_OBSERVATION` to prospective values. Use a fresh
   filename, `controller-ack-observation-v5.json`. Retain the existing final
   reserve30 and supervision45 unless the parent protocol requires explicitly
   assigning those same values.
3. Save v4 `_CONFIG_LOCK` and replace its visible binding with an owner-thread
   delegate following the existing v2 `_DelegateLock` contract. The original
   lock remains held throughout. Cross-thread acquisition and active nested
   use fail. The original v4 `revision4()` can then run its existing serialized
   v3/v2/adapter ownership chain without reacquiring the original v4 lock.
4. Enter the original, unchanged v4 `revision4()` where adapter/native-worker
   bindings are required. It installs the exact existing observer, whose v4
   globals now identify v5. It also retains the original ACK bytes, complete
   read timing, exclusive observation publication, original read failures,
   saved inventory checks, and independent transport analysis.
5. Restore every saved module binding in `finally`, then release the original
   v4 lock and the new v5 lock. Save before each possible mutation; exceptions
   in acquisition, partial setup, preparation, execution, or analysis must not
   leak any binding. Never persistently change v3/v4 clearance flags.

Worker argv is an important exception: v4 `revision4()` hardcodes its own
worker module. Inside that original context, override only
`adapter.WORKER_ARGV_PREFIX` to
`('-m', 'experiments.cf1_entry_repaired', 'worker')` before calling
`adapter.run`. The original v4 context already restores this adapter field on
exit. The fresh worker command installs the same prospective context before
delegating to the unchanged native worker. Every command that can launch a
worker must have the prospective worker prefix, never the v4 prefix.

For analysis, call the original v4 `analyze(args)` while the private outer v5
configuration is installed and no original v4 context is already active.
Its own original `revision4()` then supplies the context, report interception,
and exact `_transport_evidence` checks. This avoids modifying the analyzer or
its context function. Native freeze/run/worker entrypoints remain denied until
the parent separately authorizes their relevant future phase.

## Entry preparation and the unresolved accounting boundary

The minimal preparation ordering is, within the private serialized v5 scope:

```text
enter original v4 revision4()
install prospective worker argv
enter adapter.bound60() without run state
    prepare_new_output(independent lock/receipt/accounting hashes,
                       independently reconciled postfreeze total,
                       expected prospective policy)
leave temporary bound60()
establish and durably charge the whole-entry accounting boundary
call adapter.run(args), which enters its own stateful bound60()
leave original v4 revision4()
```

The temporary `bound60()` installs the exact q policy, lock consumer, freeze
consumer, and limits required by `prepare_new_output`; it must exit before the
stateful `adapter.run` context. Preparation must complete before `q.run` can
execute. Its canonical prefix readback must pass. Existing or partial output
blocks reuse; no cleanup/retry or fallback to q.run's legacy prefix creation.
Expected roots and total come independently from the owning supervisor, never
from the records' own claimed hashes. Today's carry is not automatically the
future postfreeze total.

**Unresolved implementation requirement:** neither this ordering nor
`adapter.run` alone accounts for whole-entry cost. `adapter.run` starts its
`cpu0` after import and preparation. Its later charge cannot cover work that
occurred before that anchor. Starting a timestamp or process CPU sample inside
the new module would also miss interpreter startup/import cost and would not
prove a whole-entry bound. Preparation is not complete until this gap is
designed, implemented, and qualified using fake execution.

The preferred bounded design is an owning supervisor plus a conservative
7.5-second entry precharge, with these obligations:

- The independent owner starts its monotonic and process-ownership observation
  before creating the fresh controller process. It observes that exact process
  identity and cumulative user+system CPU through the agreed handoff to
  `adapter.run`, covering interpreter startup, imports, rooted-metadata reads,
  preparation, and prefix publication. Any entry child processes require owned
  aggregate accounting; absent that support they must be prohibited. Owner CPU
  and control-transport work require their own accounted phase allocation.
- Before `adapter.run` begins, append a distinct, durable conservative charge
  of the full 7.5-second entry allocation to the new ledger. Bind its fresh
  policy, output, lock, external owner evidence, exact interval/phase meaning,
  and non-refund treatment. An existing finite `supervisor_cpu` ledger event
  can carry such a charge numerically, but the new wrapper must independently
  validate its semantics and uniqueness: the generic resume consumer does not.
  Do not disguise a reserve as an observed completed metadata-freeze charge.
- Read the ledger through the real resume consumer after this append; require
  the reconciled postfreeze total plus exactly that entry precharge. When
  `adapter.run` resumes the ledger, both its package state and q's cumulative
  dispatch guard must include the precharge before their launch decisions.
  Keep post-`adapter.run` CPU accounting; conservative overlap cannot become a
  subtraction or credit. The actual runtime package guard may reject a launch
  even if nominal phase ceilings sum to the available package.
- Immediately before actual worker creation, an owning-supervisor gate must
  verify that the entire entry interval was within the charged 7.5-second
  allocation and that its external observations and current cumulative/package
  guards remain complete. A scoped wrapper around `adapter.launch` can enforce
  that gate before delegating to the unchanged original launch. The owner must
  observe the handoff boundary and any CPU used while waiting for its response;
  stale snapshots cannot establish coverage through a later boundary. Failure,
  lateness, missing ownership, excess cost, or unresolved observations stops
  before worker creation and still charges/reconciles spent work.

An externally measured, durably charged whole-entry amount instead of the
conservative precharge is also possible, but needs the same complete interval,
ownership, boundary handoff, and predispatch checks. Do not choose it merely
because a controller-local process_time sample is easy. No such supervision,
precharge, boundary protocol, or timing proof exists as a result of this packet.

## Fresh source gate and future fake-execution checks

The new checked_sources gate must accept only the exact prospective check
directory above and a fresh revision5 attempt/result identity. Require the
exact future command for `src/tests/test_cf1_entry_repaired.py`, its stable
command hash, and `executed_tests == ['test_cf1_entry_repaired.py']`. The parent
protocol must specify any externally supervised command wrapper and its exact
receipt schema before execution.

Reuse the inherited v3 checked-source chain for the existing qualified
dependency checks; do not call v4's historical exact-attempt gate. Preserve the
base receipt's passing return code, termination/reaping, complete accounting,
artifact/stdout/stderr, cumulative charge, and current source-hash requirements.
Additionally bind v4 module/test and constructive-controls test, the new v5
module/test, launch_entry_preparation.py, launch_prefix_initializer.py,
egglab/launch_accounting.py, and each helper's tests. Require every current entry
of `q.campaign.sources()` in attempt source_hashes, plus the qualified test
dependencies. That function hashes all experiment and egglab Python sources.
Qualified historical tests are hashed dependencies; this is not permission to
execute the old test matrix. Result artifacts are not transferable launch
clearance.

Only the future new test file should execute. Use AST/inert bindings and fake
execution to check fresh identity, original observer/analyzer delegation,
worker argv, cross-thread/nested rejection, exact restoration after every
injected failure, independently rooted preparation before fake q.run, and
refusal after partial publication. Also cover the new entry-accounting gate:
import/preparation cost precedes dispatch charges, real resume consumes the
precharge exactly once, incomplete/late/over-cap owner evidence stops before
fake worker creation, and historical namespace/receipt/task IDs are rejected.
No numerical import, fixture/data generation, native call, old matrix, cluster
work, or additional test command is authorized by this design.

## Next implementation decisions

The parent must finalize the fresh protocol and choose a complete externally
owned whole-entry accounting/handoff scheme. Then implement the single fresh
module and single fake-execution test file, with explicit entrypoint clearance
guards and a source gate matching that protocol. Only a separately authorized,
bounded future source check can produce fresh evidence; only a later explicit
phase authorization can permit freeze/preparation/native work. Preserve all
existing stopped states and artifacts throughout. This design packet itself is
the sole output of the current bounded wake.
