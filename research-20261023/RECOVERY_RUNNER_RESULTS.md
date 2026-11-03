# Operational runner checks — 23 October 2026

Implemented the phase 1 recovery qualification runner in `src/experiments/recovery_qualification.py`. The focused solver-free suite passes **41 tests**. This qualifies the checked engineering behavior only: no 40/80 fixture was generated, no native solver or trained model was invoked, and no economic comparison or new learning result was produced.

The runner connects source/task/environment locks, fixed 30s supervisor clocks, a post-fsync pipe acknowledgment, owned-process cleanup, resource monitoring, terminal receipts and resume validation, actual binary-start inventories/log attribution, independent physical replay and machine-readable qualification gates. Restricted and fixed-route bounds remain separate from unrestricted bounds. Previous native/coordinator sources were not edited. See `RECOVERY_RUNNER_IMPLEMENTATION.md` for the required later freeze receipt and entry points.

## Internal review and explicit second check

Static review resolved escaped-process cleanup, delayed observation versus completion timing, evidence-sink failure propagation, concurrent analysis/ledger mutation, ordinary native failure reporting and check-receipt schema mismatches. Native log offsets explicitly flush C stdio; unmatched messages cannot establish acceptance. These are internal implementation reviews, not scientific peer review.

Attempt01 passed 39 tests. Subsequent source review found one omitted condition: ordinary native failure stopped later tasks but did not immediately close further native dispatch within the same recovery task. Before editing, the original runner, tests and check supervisor were archived with verified hashes. `RECOVERY_RUNNER_REPAIR02.md` prospectively recorded the minimal fix, two targeted tests, a 5s administrative allowance and one new attempt. Attempt02 passed 41 tests. Both histories are retained; neither used a native backend. There was no automatic retry.

| Check | Pytest outcome | Charged allocation (s) | Supervisor CPU (s) | Peak sampled RSS (bytes) |
| --- | --- | ---: | ---: | ---: |
| attempt01 | 39 passed in 1.97s | 2.789626583 | 0.059588 | 75,923,456 |
| attempt02 | 41 passed in 1.95s | 2.287451916 | 0.057350 | 93,290,496 |

Each check includes the existing bounded real parent-death/TERM-resistant-descendant helper. New test process groups were durably registered before fault injection. All six owned groups across both attempts were absent at cleanup; both receipts report no source changes and no monitor failure. Other cases primarily use fake clocks, models and receipts; actual 40/80 native behavior remains untested.

## Shared budget and next work

**Cumulative qualification charge: 128.4036048752605CPU seconds.** This carries the previous 88.20958837542922s, 30s package administration, 5s explicit repair allowance and both check allocations/supervisor charges. Allowances and conservative elapsed charges are not measured CPU utilization. All phases share 900s total, with dispatch stopping at 720s. Remaining allowance is 771.5963951247395s overall and 591.5963951247395s before dispatch stop. `runner-checks/accounting.json` is the next freeze's machine-readable input.

The next bounded package must prepare an identity-only exclusion/reservation registry, verify two fresh TRAIN-derived 40/80 qualification identities, and execute fixture/source freezing through a resource-supervised wrapper. Native `run` refuses to proceed without that freeze's bound accounting/resource receipt. Then execute only the separately frozen eight-task qualification matrix under the remaining shared allowance and review all gates. Candidate IDs in source are proposals, not verified reservations. Preserve failed freezes/runs and all spend; no automatic retry or outcome-based case replacement.

No comparative screen is authorized by these checks. Before a later matched comparison, specify the constructive/charging-aware classical control and freeze its cohort, methods and budgets. Learning-quality claims are unchanged. No numerical worker is active at package closeout; no routine Google Doc update is needed.
