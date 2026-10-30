# Intentional integer-cutoff repair: prospective check

23 October 2026. This package implements and solver-free tests the narrow repair proposed in `RECOVERY_INTEGER_CUTOFF_REPAIR_PLAN.md`. It authorizes no native rerun, new fixture, training or comparison. Native-v1/v2 failures, their locks and spent time remain immutable. The qualification is still incomplete.

Carry **275.4936378346678 charged seconds** from `recovery-phase1-v2/accounting.json`. Reserve **20 seconds** for implementation preparation, source review, hashing, documentation and closeout. Pre-check charge is **295.4936378346678 seconds**. Authorize exactly one exclusive `integer-cutoff-checks/attempt01`, no automatic retry, using one single-thread worker and 5 GiB process-tree RSS, 30 seconds wall with up to 2.5 seconds cleanup. Keep the shared 900-second ceiling, 720-second dispatch stop and 180-second shutdown reserve. Charge maximum observed allocation/children CPU plus supervisor CPU; the child measurement includes both pytest and monitor commands. Preserve every failure, source drift and interrupted attempt. All administration allowances are conservative accounting, not measured utilization.

The source change is confined to `src/experiments/recovery_qualification.py`. A dedicated guard-owned exception and one-use evidence distinguish deliberate refusal before starting a model after its integer cutoff from native/search failures. Exact task, case, phase, clock anchor, cutoff and observed time must match; generic timeout, actual build overrun, wrong or missing evidence, token reuse, post-dispatch and sink/resource/receipt failures remain fatal. The refusal remains a recorded diagnostic, grants no extra time, and cannot turn absent native-start/fault coverage into a pass.

The exact check argv is:

```sh
.venv-local/bin/python -m pytest -q src/tests/test_recovery_qualification.py src/tests/test_recovery_supervision_repair.py src/tests/test_recovery_integer_cutoff.py
```

Native imports are prohibited. Existing operational and supervision checks are retained because the cutoff classifier interacts with dispatch, result materialization and terminal failure. New tests use fake clocks/builders and cover expected boundary handling and malformed/mismatched evidence; no solver, fixture generation or protected data is needed. The existing registered process-group test remains bounded. No unrelated physical/model suite or training experiment is repeated.

`run_integer_cutoff_checks.py` reuses the previous bounded check supervision and records exact source hashes, argv, carried accounting, prior result/gate/lock evidence, resource samples, stdout/stderr digests and terminal process ownership. Before executing it, review the frozen source/test diff and wrapper. Keep all bound sources unchanged during the check. Stop and retain evidence on any failure. Passing establishes this engineering distinction only; another deliberate native revision requires a separately recorded protocol, source/task/environment lock, external freeze and new output namespace. Reuse the original engineering cases/seeds/clocks, and do not automatically run native-v3 from this check.
