# Approved qualification budget: independent source review

Source-only review,24 October2026. No imports, tests, assets, models, fixture generation or numerical dispatch. The runner now declares total ceiling1,800s, dispatch stop1,620s and shutdown reserve180s (`src/experiments/recovery_qualification.py:31`). This is a cumulative ceiling increase, not a fresh1,800s allowance. One thread,5GiB, task clocks and evidence requirements remain unchanged.

## Concrete blockers before a fresh check/freeze

1. **Two test fixtures encode the former dispatch threshold indirectly.** `test_run_budget_gate_creates_no_attempt` sets carried spend700s and expects dispatch refusal (`src/tests/test_recovery_qualification.py:275`). `test_monitor_child_cpu_query_deltas_reset_and_charge_once` does the same (`src/tests/test_recovery_supervision_repair.py:253`). Under1,620s, those fixtures permit launch; their failure-on-launch assertions therefore fail. No literal900/720 assertion was found in the five-module118-case suite, but these700s assumptions are equivalent stale expectations. The suite cannot remain byte-identical and test the changed live threshold successfully. Minimal test-only repair: derive synthetic near-stop spend from current `q.DISPATCH_STOP` and allocation, preserving every refusal/accounting assertion. Do not run against selectively restored old runtime limits merely to obtain a pass.

2. **The existing external freeze gate still hardcodes the old policy.** `research-20261023/run_recovery_freeze.py:65` rejects if `carried+32.5>720` or `carried+32.5+180>900`. Changing the runner's two constants does not update that independently enforced gate. A newly versioned, source-bound freeze supervisor must honor the approved policy, or this gate needs a narrowly authorized policy adaptation. Preserve previous helper/receipts unchanged. Its exact same-interpreter argv/path checks and fresh lock/fixture destination requirements should remain (`:67`,`:85`).

3. **The old check launcher is not reusable as a new attempt.** `run_admission_capture_checks_v2.py:16` fixes carried565.0277991267408s; its `main` uses an exclusive existing attempt namespace and specific prior-accounting input (`:140`,`:159`). A fresh prospective launcher/protocol must carry current complete spend and use a new namespace. Its import-safe helper tests do not themselves execute this stale `main`.

## Binding and ownership requirements

A new passing check can bind changed runner source: `checked_sources` compares current runner/test/coordinator hashes, rejects changed-during-check sources, requires successful exit, output hashes, owned-group absence and cumulative charge (`recovery_qualification.py:112`). Old passing checks cannot authorize the changed runner. The new launcher should snapshot the complete118-case inventory and its own supervisor sources, preserve all failed evidence and charge child/monitor/supervisor work once.

Freeze must receive accounting at least as large as the new check's cumulative result, with transitive immutable evidence hashes (`:154`,`:190`). Its new lock binds current source/check/accounting/reservation evidence; old locks fail current-source verification (`:244`). Native run additionally requires the matching successful external freeze receipt, confirmed ownership cleanup and conservative freeze charges (`:172`). Fresh attempts and output ownership must remain exclusive; incomplete/unknown ownership is not a resume opportunity.

Approval changes no30s endpoint,12/24s integer gates,27s admission cutoff or32.5s outer allocation. Parent must resolve the three concrete compatibility blockers before dispatch; no research or qualification success follows from the increased ceiling.

## Reviewed amendment — 24 October2026

The finalized new budget-check wrapper preserves every supervision helper body from immutable v2. Changes bind approved policy,587.8814716266195s prior spend plus the single20s package allowance, fresh namespace, inherited v2 proof hashes and current sources/argv. Both700s test fixtures now use `q.DISPATCH_STOP-20`; assertions remain intact. Six unchanged helper cases run against both wrappers, giving124 expected cases; the finalized protocol/command metadata agrees.

Correction to blocker2: the legacy freeze gate is conservative, **compatible if actual postcheck carry plus32.5 is<=720 and plus180 is<=900**—equivalently carry<=687.5s. Expected carry near610s fits; parent must confirm the measured value. No freeze-helper modification is required in that range. Historical evidence remains immutable; source review is not a passing check or launch decision.

## Independent terminal review — 24 October2026

The approved-budget attempt passed124 cases, with no errors/source changes. Independently verified160 source hashes,203 prior-evidence hashes,6 output hashes and exact argv binding. The receipt confirms three owned groups absent and leader reaped. Conservative allocation plus own CPU charges3.0352388751039507s; cumulative carry is610.9167105017234s including the existing single20s allowance, not another allowance. Legacy freeze admission computes643.4167105017234<=720 and823.4167105017234<=900 with reserve, so it is compatible now. See `RECOVERY_APPROVED_BUDGET_CHECK_RESULTS.md`; parent retains fresh freeze/receipt review responsibility. No runtime imports or test/native execution occurred in this independent review.
