# Responsive v6 core: static integration handoff

Core source is `src/experiments/cf1_responsive_supervision.py` and
`src/experiments/cf1_responsive_owner.py`; the separate collector is
`src/egglab/async_resource_probe.py`. Legacy production files and v5e evidence
were not edited. No import, compile, hash audit, test, probe or process was run
by the implementation agents. Parent review and exact phase manifests remain
required; this note clears no execution.

Policy/task revision are `cf1-responsive-supervision-v6`/6. Native namespace is
`research-20261025/cf1-responsive-v6`; checks are
`research-20261025/cf1-responsive-checks/attempt01`. Retain carry2541.8243213823207,
global3600/3420/180 and package600 from2426.723449631016/end3026.723449631016.
Entry65/startup-observed20, controllerCPU31.5, ownerCPU15, supervision120 and
analysis/final45 are explicit. Default metadata10/scoped17.5 is reused and restored.

## One source gate

The exact test command expected by the consumer is:

```
<ROOT>/.venv-local/bin/python -m pytest -q src/tests/test_responsive_supervision_v6.py
```

Execute only that file inside the parent's metered30s source provision.
Attempt/result must identify attempt01, revision6, the policy above, exact
command/digest and executed_tests=`["test_responsive_supervision_v6.py"]`.
Required production closure is the complete current `q.campaign.sources()`;
this includes all three new modules and the unchanged physical worker/replay.
Required hashed test dependencies, not additional test executions, are:

- `test_constructive_controls.py`
- `test_comparison_native_adapter.py`
- `test_cf1_preparation_preflight.py`
- `test_cf1_small_mechanism_preflight.py`
- `test_cf1_small_mechanism_approved.py`
- `test_launch_accounting.py`
- `test_launch_prefix_initializer.py`
- `test_launch_entry_preparation.py`
- `test_cf1_entry_repaired.py`
- `test_responsive_supervision_v6.py`

## Explicit entry API, after separate qualification

Module CLI is `python -m experiments.cf1_responsive_supervision` with subcommands
freeze/run/worker/analyze. Freeze requires `--design --lock --checks --accounting`.
Analyze retains `--lock --output --report`. Worker retains the exact internal
`--lock --output --parent-pid --ack-fd` interface and physical60/61/62.5 clocks.

The frozen run base command requires `--lock --output --freeze-receipt
--accounting --expected-lock-sha256 --expected-freeze-receipt-sha256
--expected-accounting-sha256 --expected-cumulative-charge-s`. Expected values
must come from independently retained actual frozen metadata. The eight owner
roots are lock_path/freeze_receipt_path/accounting_path, their three expected
SHA256 fields, expected_cumulative_charge_s and expected_policy.

Inside the restored `revision6()` context, construct
`OwnerSupervisor(directory=BASE/'entry-owner-attempt01', roots=roots,
task=task_matrix()[0], output=BASE/'runs', policy=POLICY).run(base_command)`.
The owner supplies both `--owner-fd` and NEW `--owner-telemetry-fd`, plus its root,
root hash and nonce. Do not freeze these generated transport options into the
base command or pass them yourself. The privileged request/response socket and
resource/status socket are distinct.

## Specific integration and proof limits

The actual Popen/one-use/expiry guard is inherited under restored v6 bindings.
Actual worker PID publication occurs before q.launch restores its signal mask;
post-Popen publication failure returns the known process for truthful cleanup,
not the legacy unspawned-child failure branch. The unchanged physical worker's
single watch-parent helper is accepted only through its exact four-field
owned-processes.json contract/PID and same worker PGID. Unknown children,
including a lone child escaping that PGID, are rejected. Reparented registered
watchdog rows remain owned and counted. Their parent must be the worker or PID1;
PID1 is allowed even while a zombie worker row remains. Arbitrary parents remain
invalid in both owner and controller consumers.

Control/ACK service precedes bounded probe work; host-table ownership validation
yields every32 rows. Resource age is from true probe START, with1s pair duration,
1.25s completed gap,2.25s age and.25s minimum start interval. The collector derives
CPU precision and rejects coarser than.01s; a labelled K*.02 quantization guard
fits entry65/supervision120. Final owner charges retain the conservative
uncertainty highwater rather than discarding live tails at closure.

Terminal cleanup is explicit before legacy finish/audit. The owner continues
resource/funding and61/62.5 worker timers but does not claim.25s controller
service while that finalization blocks. Complete observations require real
helper reaps, group absence, finite counters and CPU limits; independent
scientific analysis is still mandatory. OS spawn, filesystem and scheduler
stalls can fail these conditions. No hard real-time, instantaneous RSS, actual
probeCPU15 viability or CF1 success is established by static/compositional tests.
The real20s no-native primitive remains separate after a passing source gate.
