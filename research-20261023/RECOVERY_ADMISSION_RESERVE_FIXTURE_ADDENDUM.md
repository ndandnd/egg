# Prospective correction of the serialization-test fixture

24 October2026. This addendum supersedes only the passing-check dependency,
freeze command and remaining-budget carry in `RECOVERY_PHASE1_V6_PROTOCOL.md`.
The native v6 freeze/lock/run have **not** been attempted. The eight engineering
tasks, fixtures, native source, clock allocation and pass criteria are unchanged.
The failed191-case check and its exact source are preserved in commit37d7262a,
`admission-reserve-checks/attempt01` and its results/accounting notes.

## Diagnosed correction and deliberate new check

The old serialization fixture begins at23s, beyond the newly declared22s search
stop. The planner correctly never runs, so the expected injected RuntimeError
cannot exist. Change only its fake start23→21 and serialization8→10; keep all
three assertions unchanged. The injected error then occurs before22 and output
still ends late at31. No production source, guard or expected failure is relaxed.

Require one explicit new source-bound191-case check in
`admission-reserve-fixture-checks/attempt01`, using
`run_admission_reserve_fixture_checks.py`. The eight test modules and supervision
helpers remain those of the preceding check. Parent reviews exact hashes,
complete accounting, source stability and confirmed owned-group absence/reap.
No native/freeze launch or automatic retry follows from this addendum alone.
This replaces the unfulfilled requirement for a passing original
`admission-reserve-checks/attempt01`; that original receipt remains failed.

Carry **915.958148670185s** from `admission-reserve-checks/accounting.json`,
including its3.0658860423948764s failed-check charge. ADMIN0, hard1800,
dispatch1620, shutdown180, one single-thread numerical worker and5GiB remain.
Rebased pending envelope remains700s: check40, freeze40 (each32.5 external
plus7.5 supervisor provision), workers260, run supervision300, analysis20,
contingency40. Prospective end1615.958148670185s leaves4.041851329815s below
dispatch. This is not a guaranteed cost or permission to borrow shutdown reserve.
Reconcile actual complete check/freeze costs and all remaining allocations
before native dispatch. Preserve all prior failed spend and conservative charges.

## Corrected conditional commands

Exact new argv/environment and source metadata are in
`admission-reserve-fixture-checks/command.json`. After parent static review:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_admission_reserve_fixture_checks.py
```

Only after the actual passing check, parent writes v6 input accounting from its
complete final carry and inherited proof inventory. Exact inner freeze argv is
`recovery-phase1-v6/freeze-command-corrected.json`. Parent then uses:

```sh
.venv-local/bin/python research-20261023/run_recovery_freeze_v2.py \
  --attempt-dir research-20261023/recovery-phase1-v6/freeze-attempt01 \
  --command-json research-20261023/recovery-phase1-v6/freeze-command-corrected.json \
  --lock research-20261023/recovery-phase1-v6/lock.json \
  --checks research-20261023/admission-reserve-fixture-checks/attempt01 \
  --accounting research-20261023/recovery-phase1-v6/input-accounting.json \
  --protocol research-20261023/RECOVERY_ADMISSION_RESERVE_FIXTURE_ADDENDUM.md
```

Retain the v6 native run/analyze commands and all original freeze/library/fixture
and pass/fail gates. The passing check alone proves no actual80-trip timing,
native qualification, learned value, generalization or scientific novelty.
