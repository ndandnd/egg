# Prospective native qualification revision5

24 October2026 UTC. Metadata preparation only: no check, import, fixture, solver
or native task is executed here. Parent owns check receipt/accounting review,
external freeze, exact source/library/fixture/task lock, native dispatch and
analysis. Preserve all v1–v4 protocols, sources, failed freezes/runs, receipts,
reconciliations and charges. This is not automatic resume or retry.

## Budget and prerequisites

Approved qualification policy is **1800s cumulative ceiling,1620s dispatch stop,
180s shutdown reserve**. Start from reconciled718.8639492101057s and carry every
later charge. **ADMIN=0 for this package**: the single shared20s approved-revision
allowance is already included and must not be added again.

Before freeze, require the actual passing source-bound
**`freeze-v2-checks/attempt01`** receipt, covering the existing suite plus11 fake
freeze-wrapper cases (135 total). Reviewed source and fake cases are not an
executed check or proof of native cleanup. Parent writes v5
`input-accounting.json` only after that check, using its final cumulative charge
and authoritative prior evidence hashes. Incomplete accounting requires
reconciliation; do not replace unknown costs with zero.

Use **`run_recovery_freeze_v2.py`**, not the immutable legacy wrapper. Bind its
reviewed budget-check cleanup dependency and source/test/protocol hashes. It
uses the approved checked runtime budget constants, absolute cleanup deadline,
known PGIDs/reap/unknown states, primary/secondary errors and fail-closed final
CPU/output audits. Old failed freeze receipts remain failed.

Before each launch require the entire32.5s allocation and shutdown reserve under
actual cumulative spend. Eight task allocations total260s before monitor,
supervisor, replay/materialization and analysis charges. Record those costs once;
unused capacity authorizes no additional task, repair or automatic retry.

## Original fixed scope

Keep engineering cases **50997/40 and50999/80**, seed17, day tariff, frozen
nonlearned ranking and30% plus top-three coverage. The existing project-bounded
identity registry is `recovery-phase1-reservations-v2.json`; explicit v5
`design.json` avoids rejected50998 in the core default. No replacement case,
extra seed, trained model, protected data, cluster or comparison study.

Run only the original eight tasks: each size crossed with static restricted,
normal recovery, cold full8 and injected start-setter failure. One local worker,
one numerical thread/CPU and at most5GiB aggregate process-tree RSS.

Keep supervisor-anchored integer/physical prefix12/15s, full24/27s, final physical
endpoint30s and outer32.5s. Completion allowance3s is cumulative; finalization
reserve3s remains. Static/cold keep24/27s; supervisor stops by31s and cleanup
shares absolute32.5s. Sampling targets0.05s within the original0.25s completed-
sample policy. No stage resets its clock or receives extended search time.

Preserve independent full-case replay/exact bills, scoped bounds, durable
fallback through the injected fault, full capture once with checked compact
references, and honest cutoff/late-result diagnostics. Engineering evidence
policy is common across arms. Passing fake references proves no80-trip speedup.

## External freeze and native gate

All inner argv paths in v5 `freeze-command.json` are absolute and use the checked
interpreter. Confirm it matches wrapper `sys.executable`. Keep the phase0 GRB
library and hash unchanged:

- `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/gurobipy/_batch.cpython-312-darwin.so`
- SHA256 `54c2ca41a9a9c80b4dd27df09e6b8a73abbb18de90e95198ae676611910dca96`

Parent must review a passing external receipt and exact fresh lock before native
dispatch: matching lock hash, unchanged sources, no monitor/resource/accounting
or secondary audit failure, allocation≤32.5s, RSS≤5GiB and complete known-group
absence/reap confirmation. Missing or failed freeze blocks native work. Do not
overwrite v4's generated lock/fixtures or repair its immutable receipt.

If gates hold, execute this matrix once in the new v5 namespace. Stop further
dispatch on the first engineering/resource/receipt failure. Retain terminal
failures; incomplete/audit errors block automatic resume. No automatic retry.
Qualification passes only with all eight accounted timely endpoints, valid
replay/bills/mapping/bound scope, attributable native partial-start processing
and valid fallback retained through fault. Natural no-plan outcomes do not
replace missing required paths; late results remain censored. No ML, economic
superiority, generalization or publication-readiness claim follows.

## Exact parent commands — conditional, not executed

After the new source-bound check passes and parent writes bound input accounting:

```sh
.venv-local/bin/python research-20261023/run_recovery_freeze_v2.py \
  --attempt-dir research-20261023/recovery-phase1-v5/freeze-attempt01 \
  --command-json research-20261023/recovery-phase1-v5/freeze-command.json \
  --lock research-20261023/recovery-phase1-v5/lock.json \
  --checks research-20261023/freeze-v2-checks/attempt01 \
  --accounting research-20261023/recovery-phase1-v5/input-accounting.json \
  --protocol research-20261023/RECOVERY_PHASE1_V5_PROTOCOL.md

# Only after parent reviews the valid passing freeze receipt and exact lock:
PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification run \
  --lock research-20261023/recovery-phase1-v5/lock.json \
  --freeze-receipt research-20261023/recovery-phase1-v5/freeze-attempt01/supervisor.json \
  --output research-20261023/recovery-phase1-v5/runs

PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification analyze \
  --lock research-20261023/recovery-phase1-v5/lock.json \
  --output research-20261023/recovery-phase1-v5/runs \
  --report research-20261023/recovery-phase1-v5/gates.json
```

This package creates only design/argv/protocol metadata, not input accounting,
lock, fixtures, check/freeze attempts or native outputs.
