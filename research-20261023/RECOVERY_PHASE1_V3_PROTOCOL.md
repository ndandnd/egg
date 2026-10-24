# Prospective native qualification revision 3

23 October 2026. This package prepares four metadata files only. No fixture,
lock, attempt directory, check or native run is created here. The parent owns
review, the unchanged externally supervised freeze, terminal receipt review and
any subsequent deliberate native launch. This is a repaired revision, not an
automatic retry or resume of native-v1/v2.

## Preserved evidence and fixed scope

Native-v1 and native-v2 remain failed/incomplete with all original protocols,
sources, locks, fixtures, logs, receipts, gates and spend untouched. V1 stopped on
a resource-monitor timeout. V2 supervision was clean and its first static witness
was timely and replay-valid, but its intentional pre-build integer cutoff was
classified as an engineering failure. Seven tasks remained undispatched in each
revision. Do not analyze an old source lock using repaired sources or rewrite its
raw diagnostics.

The current revision passed **86 solver-free tests** in
`integer-cutoff-checks/attempt01`, including the existing 54 runner/supervision
cases and 32 typed-cutoff cases. The new lock must bind those exact checked
sources. Only a durable, exact, single-use pre-build cutoff is recognized as an
expected budget stop. Generic timeout, model-build overrun, malformed/mismatched
cutoff evidence, sink, replay, resource and monitor failures remain failures.
This engineering repair establishes no native qualification result and adds no
native search time.

Retain cases **50997/40 and 50999/80** from the existing
`recovery-phase1-reservations-v2.json`. Explicit `recovery-phase1-v3/design.json`
overrides the core default containing rejected 50998. No case is selected from a
bill, and reusing these engineering cases provides no independent generalization
evidence.

The matrix remains **eight tasks**: 40/80 trips crossed with static, normal
recovery, cold full and injected start-setter failure. Preserve seed **17**, target
**day** tariff, frozen nonlearned ranking, **30% plus top-three coverage**, one
worker, one numerical thread and at most **5 GiB** process-tree RSS. No additional
cases, seeds, solves, training, cluster work, protected-data access or comparison
study is authorized.

## Carried budget and unchanged clocks

Carry **298.7213646264001 charged seconds** from
`integer-cutoff-checks/accounting.json`, preserving all prior failed spend.
Prospectively add **20 seconds** for this package's preparation, review and
closeout administration. The input total is **318.7213646264001 seconds before
actual freeze or run**. This allowance is conservative accounting, not measured
utilization. Actual freeze, worker, monitor-child and supervisor charges are
additional; failures remain charged.

Retain the **900-second** cumulative ceiling, **720-second** dispatch stop and
**180-second** shutdown reserve. Each task must fit its complete **32.5-second**
outer allocation plus shutdown. Eight allocations reserve 260 seconds before
additional overhead. Unused capacity authorizes no extra task or retry.

The physical endpoint stays **30 seconds** from the supervisor's pre-interpreter
anchor. Recovery keeps prefix integer/physical cutoffs **12/15 seconds**, full
integer/physical cutoffs **24/27**, cumulative completion allowance **3 seconds**
and finalization reserve **3 seconds**. Static/cold controls keep 24/27 cutoffs.
No stage resets its clock. The unchanged repaired supervisor targets 0.05-second
sampling within the 0.25-second completed-sample limit, stops by 31 and shares
absolute cleanup deadline 32.5. These reserves add no solve time.

## External freeze and conditional native gate

Use unchanged `run_recovery_freeze.py` with exact v3 `freeze-command.json`,
`integer-cutoff-checks/attempt01`, v3 accounting and explicit design/registry. All
inner argv paths are absolute. The unchanged phase-0 GRB library is:

- `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/gurobipy/_batch.cpython-312-darwin.so`
- SHA256 `54c2ca41a9a9c80b4dd27df09e6b8a73abbb18de90e95198ae676611910dca96`

Input accounting retains the authoritative prior evidence hashes and adds the
prior accounting, this protocol, v3 design/argv and existing registry. The parent
must review a passing external terminal receipt and exact new source/environment/
library/fixture/market/movement/task lock before native dispatch. The receipt must
match the lock and original `recovery_fixture_freeze` contract: no source/monitor
failure, valid carried charge, elapsed allocation at most 32.5 seconds, RSS at most
5 GiB and every owned process group confirmed absent. Missing, failed or incomplete
freeze cannot authorize a task. No v1/v2 artifact is a writable output.

Only after those gates hold may the parent deliberately execute this repaired
eight-task qualification once in `recovery-phase1-v3/runs`. The first engineering,
resource or receipt failure stops further dispatch. Preserve completed failures;
incomplete/audit errors block automatic resume. Any new repair needs another
prospective decision carrying all spend. There are no automatic retries.

Independently replay and bill accepted witnesses, retain the durable fallback
through injected failure, separate restricted/fixed-route/full bounds, and require
actual native partial-start processing evidence. Expected cutoff does not excuse
late completion, missing witness/fault/processing coverage or a failed resource
gate. Parent receipt and machine-readable gate review is required for any
qualification claim. No economic, predictive-quality, novelty, certification or
learned-superiority conclusion follows from these engineering tasks.

## Parent commands, recorded only

```sh
.venv-local/bin/python research-20261023/run_recovery_freeze.py \
  --attempt-dir research-20261023/recovery-phase1-v3/freeze-attempt01 \
  --command-json research-20261023/recovery-phase1-v3/freeze-command.json \
  --lock research-20261023/recovery-phase1-v3/lock.json \
  --checks research-20261023/integer-cutoff-checks/attempt01 \
  --accounting research-20261023/recovery-phase1-v3/input-accounting.json \
  --protocol research-20261023/RECOVERY_PHASE1_V3_PROTOCOL.md

# Only after parent review of the passing freeze receipt and exact new lock:
PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification run \
  --lock research-20261023/recovery-phase1-v3/lock.json \
  --freeze-receipt research-20261023/recovery-phase1-v3/freeze-attempt01/supervisor.json \
  --output research-20261023/recovery-phase1-v3/runs

PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification analyze \
  --lock research-20261023/recovery-phase1-v3/lock.json \
  --output research-20261023/recovery-phase1-v3/runs \
  --report research-20261023/recovery-phase1-v3/gates.json
```

No command above is executed by this manifest-preparation package.
