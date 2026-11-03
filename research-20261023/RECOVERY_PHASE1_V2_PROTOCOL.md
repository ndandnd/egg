# Prospective native qualification revision 2

23 October 2026. This package prepares manifests only. No agent has generated a
fixture, executed a freeze/check/native task, or edited core/test sources here.
The parent owns source review, the externally supervised freeze, receipt review
and any subsequent deliberate native launch. This is an explicit repaired
revision, not automatic resume/retry of native-v1.

## Preserved evidence and scope

Native-v1 remains failed: its first 40-trip static task stopped on a monitor
timeout, seven tasks were undispatched, and its original cleanup permission
failure obscured the primary cause. Its fixtures, source/task lock, receipts,
logs, gates and spend stay untouched. Original sources remain available at
Git `269df001`. Do not analyze the old lock using changed sources or normalize
its immutable raw logs.

The current supervision revision passed **54 solver-free tests** in
`supervision-repair-checks/attempt01`. The new lock must bind those exact checked
sources. Shared monitor deadlines, timeout provenance, permission-denied unknown
state, idempotent finalization, primary/secondary error retention and separate
monitor-child CPU accounting are engineering repairs. They do not establish a
native qualification result or enlarge native search time.

Retain the same identity-selected cases **50997/40 and 50999/80**, with the existing
`recovery-phase1-reservations-v2.json`. The explicit v2 `design.json` overrides the
core default containing rejected 50998. These reused engineering cases are not
independent generalization tests; no case or regime is selected from a bill.

The matrix is unchanged: 40/80 trips crossed with static, normal recovery, cold
full and injected start-setter failure, **eight tasks**, seed **17**, target **day**
tariff, frozen nonlearned ranking, **30% plus top-three coverage**, one worker,
one numerical thread and at most 5 GiB process-tree RSS. No extra cases, seeds,
longer solves, training, cluster work, protected data or comparison screen.

## Budget and clocks

Carry **212.08502712584297 charged seconds** from
`supervision-repair-checks/accounting.json`, including the preserved historical
native failure and prior reconciliation. Prospectively add **20 seconds** for
this package's preparation/readback/analysis administration: the input total is
**232.08502712584297 seconds before actual freeze or run**. The allowance is
conservative accounting, not measured utilization. Freeze, worker, monitor-child
and supervisor charges are additional; all failures remain charged.

Keep the **900-second** cumulative ceiling, **720-second** dispatch stop and
**180-second** shutdown reserve. Each launch must fit its entire **32.5-second**
outer allocation plus shutdown. The eight allocations reserve at most 260 seconds
before additional measured overhead. Unused capacity authorizes no additional
task or retry. Budget exhaustion is incomplete qualification, never a pass.

The physical endpoint remains **30 seconds** from the supervisor's pre-interpreter
anchor. Recovery keeps prefix integer/physical cutoffs **12/15 seconds**, full
integer/physical cutoffs **24/27**, cumulative native completion reserve **3**, and
finalization reserve **3**. Standalone static/cold controls retain 24/27 cutoffs.
No stage resets its clock. The repaired native supervisor targets 0.05-second
sampling within the unchanged 0.25-second completed-sample limit, stops by 31 and
shares absolute cleanup deadline 32.5. These supervisory reserves add no solving
time. Source/assets remain frozen throughout execution.

## Source-bound freeze and launch gates

Use the unchanged reviewed `run_recovery_freeze.py` wrapper with the exact
`recovery-phase1-v2/freeze-command.json` argv, new lock/fixture/attempt destinations,
current input accounting and explicit design/registry. All argv paths are absolute.
The inherited phase-0 GRB library is unchanged:

- `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/gurobipy/_batch.cpython-312-darwin.so`
- SHA256 `54c2ca41a9a9c80b4dd27df09e6b8a73abbb18de90e95198ae676611910dca96`

`input-accounting.json` preserves the authoritative prior evidence hashes and adds
hashes of this protocol, the prior accounting, current check receipts, new design,
exact freeze command and existing registry. Freeze must lock current
source/environment/library/fixture/market/movement/task identities. No existing
v1 artifact is reused as a writable output.

Before any native launch, the parent must review the external terminal freeze
receipt and exact new lock. Passing requires the original receipt contract:
`phase=recovery_fixture_freeze`, matching lock hash, no source/monitor failure,
valid cumulative charge, elapsed allocation at most 32.5 seconds, RSS at most
5 GiB and every owned process group confirmed absent. Missing/failed/incomplete
freeze cannot authorize a native task. Any repair needs another prospective
decision and carried spend; no automatic retries.

If those gates hold, the parent may deliberately execute this repaired eight-task
qualification once in the new `recovery-phase1-v2/runs` namespace. The native
supervisor must stop subsequent dispatch on the first engineering/resource/
receipt failure. Completed failures are retained; incomplete/audit errors block
automatic resume. Independently replay/bill every accepted witness, retain the
durable fallback through the fault, distinguish restricted/fixed-route/full
bounds, and require actual native partial-start processing evidence. Natural
no-plan results do not replace missing fallback/fault/processing coverage.

The parent must inspect terminal receipts and machine-readable gates before
claiming qualification. No economic, predictive-quality, novelty, certification
or learned-superiority inference follows from these eight engineering tasks.

## Parent commands — preparation only

```sh
.venv-local/bin/python research-20261023/run_recovery_freeze.py \
  --attempt-dir research-20261023/recovery-phase1-v2/freeze-attempt01 \
  --command-json research-20261023/recovery-phase1-v2/freeze-command.json \
  --lock research-20261023/recovery-phase1-v2/lock.json \
  --checks research-20261023/supervision-repair-checks/attempt01 \
  --accounting research-20261023/recovery-phase1-v2/input-accounting.json \
  --protocol research-20261023/RECOVERY_PHASE1_V2_PROTOCOL.md

# Only after the parent approves that freeze receipt and new lock:
PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification run \
  --lock research-20261023/recovery-phase1-v2/lock.json \
  --freeze-receipt research-20261023/recovery-phase1-v2/freeze-attempt01/supervisor.json \
  --output research-20261023/recovery-phase1-v2/runs

PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification analyze \
  --lock research-20261023/recovery-phase1-v2/lock.json \
  --output research-20261023/recovery-phase1-v2/runs \
  --report research-20261023/recovery-phase1-v2/gates.json
```

These commands are recorded, not executed by this manifest-preparation package.
