# Recovery shared-clock coordinator — implementation result

23 October 2026. This is a solver-free engineering package, not a new fleet experiment or a completed native qualification.

`src/egglab/recovery_coordinator.py` now connects the existing native planner to a supervisor-owned absolute clock. It separates integer-search cutoffs from physical completion/replay cutoffs, shares a conservative three-second native completion allowance across stages, persists a replay-valid full-case fallback before warm recovery, and re-admits bounds only from original unrestricted MIP rounds. Scoped native hooks are restored after exceptions. The original native/lift sources and historical results were not modified.

The independent static review found two timing defects before execution: a late prefix save could still dispatch the full problem, and expensive bound replay could cross its cutoff unnoticed. Both were corrected and covered by focused fake-clock tests. Diagnostic nonfinite values now receive explicit tags without relaxing strict finite physical-result serialization. The check supervisor bounds its monitor calls, records owned-process-group termination and counts child/supervisor CPU separately. See `RECOVERY_COORDINATOR_CONTRACT_REVIEW.md`.

## Executed checks and preserved failure

The exact source-hashed command was `.venv-local/bin/python -m pytest -q src/tests/test_recovery_coordinator.py`, with one-thread environment settings and resource supervision. Existing interface tests were not rerun in this package; the new tests exercise the real planner API with fake native methods and prohibit backend imports.

| Attempt | Outcome | Allocation charge (s) | Supervisor CPU (s) | Sampled peak RSS |
| --- | --- | ---: | ---: | ---: |
| attempt01 | 22 passed, 12 failed | 0.773469208 | 0.018853 | 43,057,152 bytes |
| attempt02 | 34 passed | 0.524429168 | 0.012702 | 44,367,872 bytes |

The first attempt exposed an exact test-expectation error: the fixture used binary float `.2`, but seven assertion sites expected the decimal rational `1/5`. All twelve failed cases had that same first failing assertion. The repair uses the independently hand-derived expression `Fraction(7) + 2*15 + Fraction(.2)*225/2`, preserving exact equality rather than widening tolerances. Production arithmetic was unchanged. The explicit repair decision preceded attempt02; there was no automatic retry. The original eight source files are preserved in `coordinator-checks/attempt01/source-snapshot/`, with original logs, hashes and result receipt. `RECOVERY_COORDINATOR_REPAIR02.md` records the diagnosis and prospective repair.

Both attempts have terminal receipts, unchanged sources during execution and confirmed absence of their owned process groups after cleanup. No native solver, model training, timetable generation, cluster job or protected data was used. Native-start acceptance, actual 40/80 timetable behavior and full operational-supervisor qualification remain untested by this package.

## Cumulative budget

Carry forward **88.20958837542922 charged CPU seconds**:

- Phase-0/prior charge:66.880135 seconds.
- This package's conservative administrative/review allowance:20 seconds.
- Both check allocations and supervisor CPU:1.329453375429213 seconds.

The900-second cumulative ceiling and720-second dispatch stop remain unchanged. The remaining hard allowance is811.7904116245708 seconds, with631.7904116245708 seconds before the dispatch stop. Allowances and conservative wall charges are not measured utilization. Future freeze/fixture/run/analysis costs must be added; never start a new budget at zero. The future lock must hash both attempt/result receipts, the phase-0 evidence and this check protocol.

## Next executable package

Build the phase-1 native runner around this coordinator and the existing ownership/receipt mechanisms. Add immutable attempt IDs, source/environment/fixture locking, append-only native/ledger events, parent/descendant shutdown, resume validation, common endpoint verification and machine-readable gates. Freeze the two identity-only 40/80 qualification cases and eight-task matrix only after those runner checks pass. No comparison screen is authorized by these unit-test results. The modern constructive comparator remains necessary before any learned-superiority claim.

There is no active numerical worker at closeout. No Google Doc update is needed for this routine implementation step; the last consolidated scientific milestone remains the cross-field review.
