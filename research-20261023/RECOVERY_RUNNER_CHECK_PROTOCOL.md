# Operational recovery runner: bounded solver-free verification

23 October 2026, follow-up after coordinator commit002154a2. This is an implementation/check package. It does not launch a native solver, generate timetable fixtures, train a model, select a comparison cohort, or qualify a research result.

## Prospective scope and charge

Carry forward **88.20958837542922 charged CPU seconds**, verified from `coordinator-checks/accounting.json` and its immutable attempt/result receipts. All six earlier primitive attempts and both coordinator checks are terminal. A scoped local process check found no EGG numerical/check worker before this package. Implementation/review agents operate only on new runner/test/documentation files; historical native/lift/coordinator sources, locks, models and results remain unchanged.

Reserve **30CPU seconds** for this package's source inspection, static review, check preparation, hashing, documentation and accounting. This conservative administrative allowance is not measured CPU utilization. Authorize **one** named `runner-checks/attempt01` solver-free attempt with a30s wall limit, <=5GiB sampled process-tree memory and one native-library thread. Preserve its complete outputs/receipts whether passing or failing. Any repaired rerun requires a new prospective reason, attempt name and accounting; no automatic retry.

Initial carried charge including administration is118.20958837542922s. The original900s cumulative hard ceiling,720s dispatch stop and180s shutdown reserve remain in force. Before dispatch require room for a32.5s outer allocation. Charge max(elapsed allocation, sampled child CPU, observed reaped child CPU), plus check-supervisor CPU. Preserve original prior receipt hashes. Future native freeze and execution must carry this package's complete spend.

## Required check discipline

The source-hashed command is `.venv-local/bin/python -m pytest -q src/tests/test_recovery_qualification.py`. Native imports must be blocked/mocked, and timetable fixture generation must not run. Snapshot the checked source hashes before dispatch and check them afterward. Do not edit those files during the attempt. Log resource samples no more than0.25s apart, pressure at most1s apart, and fail closed if monitoring fails. Low system free-memory fraction below10% for5s or RSS breach stops the owned attempt. Bound monitor subprocesses themselves. Cleanup and CPU charge are distinct from a worker's result endpoint.

Checks should cover immutable attempts and source/task/receipt identity, prior spend carry-forward, terminal failure skip without retry, incomplete/corrupt attempt blockage, common-deadline completion validation, resource-stop handling, native-processing evidence classification, and ownership/watchdog integration. Pure fake-clock/unit checks cannot establish real native start processing or40/80 behavior. Any test that spawns a new session must own and clean it on every path; the outer check supervisor must track/terminate surviving owned descendants. Do not hide subprocess failures or count a censored endpoint as passing.

## Freeze remains separate

Only after passing checks and static review may a separate identity-only fixture reservation and phase1 source/task/environment lock be prepared. The eight native tasks and their log/ownership gates remain deferred until that lock and its evidence are complete. Generic implementation success is not evidence of prediction quality, tariff responsiveness, optimality, or publication readiness.
