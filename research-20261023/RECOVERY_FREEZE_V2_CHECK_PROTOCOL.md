# One source-bound freeze-v2 regression check

24 October 2026. Prepare exactly one exclusive
`freeze-v2-checks/attempt01`. Parent owns execution, resource supervision, receipt
review and accounting. This preparation package performs no runtime import,
test, fixture generation, freeze, native solve or retry. All earlier wrappers,
attempts, failed outcomes and reconciliation artifacts remain immutable.

## Carried policy and scope

Carry **718.8639492101057 charged seconds** from
`recovery-phase1-v4/accounting.json`, including the failed freeze, conservative
watchdog allowance and separate confirmed-absence reconciliation. Add **zero**
administration: the prior single shared 20-second allowance is already included.
This is cumulative spend, not a fresh budget. Retain the approved **1800-second**
hard ceiling, **1620-second** dispatch stop and **180-second** shutdown reserve.

The new `run_freeze_v2_checks.py` is a policy-only copy of
`run_admission_capture_budget_check.py`. All sampling, ownership, cleanup,
diagnostic, output-audit and accounting helpers are unchanged. Differences are
the carried amount/admin, authoritative prior path, fresh namespace, six-module
test list, bound source inventory and descriptive receipt fields. The prior
accounting's complete evidence inventory already identifies freeze-attempt and
cleanup-reconciliation files; no stale `prior/attempt01` filenames are assumed.

Check the previous 124 cases plus the eleven fake freeze-v2 cases: **135 total**.
The exact child argv uses the checked interpreter and these six modules:

```sh
.venv-local/bin/python -m pytest -q \
  src/tests/test_recovery_qualification.py \
  src/tests/test_recovery_supervision_repair.py \
  src/tests/test_recovery_integer_cutoff.py \
  src/tests/test_recovery_admission_capture.py \
  src/tests/test_check_supervision_v2.py \
  src/tests/test_recovery_freeze_v2.py
```

No additional helper parametrization or tests are introduced for this launcher
copy. Native imports and real launches are forbidden in the new freeze tests;
the preexisting registered, bounded ownership test remains. No trained-asset
load, cohort inference, training, case generation or cluster work is included.

## Unchanged supervision and gates

Keep one numerical thread, **5 GiB** aggregate owned-tree RSS, **30-second** work
limit and absolute **32.5-second** cleanup allocation. Shared monitor deadlines,
0.05-second target scheduling and strict **0.25-second** completed-sample policy
remain. An overlong query fails closed. Preserve all known/registered descendant
groups, unknown permission-denied state, leader reap status, primary reason and
secondary cleanup/audit errors. Passing requires successful pytest exit, complete
accounting, unchanged sources/outputs and confirmed absence of all owned groups.
Missing proofs or an incomplete terminal audit cannot pass.

Charge max(allocation elapsed, sampled owned-tree CPU, total observed child CPU)
plus own supervisor CPU. Total children includes monitor commands; their separate
diagnostic is not added again. Every failure remains charged. An unavailable
child-CPU observation is explicit unknown/incomplete and needs reconciliation
before authoritative future carry. No additional administration is added at
check, freeze or native closeout.

Freeze exact current egglab/experiments sources, six test modules, launcher,
new freeze-v2 wrapper and dependency closure, implementation/review, this protocol,
approval record and command metadata before Popen. Verify inherited prior evidence
unchanged, retaining its hashes rather than replacing historical source evidence.
Recheck current source hashes and bind output/resource/ownership hashes in the
terminal receipt. Keep tested sources stable until receipt review.

## Parent command, recorded only

`freeze-v2-checks/command.json` records exact parent/child argv, environment,
stable source hashes and added evidence hashes. The command JSON cannot include
its own hash; the actual launcher attempt binds it too.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_freeze_v2_checks.py
```

Parent/static review precedes the **one** deliberate attempt. Stop on failure,
preserve receipts and do not retry automatically. Passing validates engineering
regressions only; any subsequent external freeze needs its own new namespace,
reviewed inputs and passing terminal receipt before native dispatch. This check
does not alter the failed v4 result or constitute native qualification.
