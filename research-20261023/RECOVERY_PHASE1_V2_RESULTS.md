# Native recovery qualification revision 2: results

23 October 2026. Revision 2 deliberately reran the unchanged qualification design after the source-bound supervision repair. The external freeze passed; the task/source/fixture lock is SHA256 `3e11826f16a58a240f940cee975aee496a2dfee822c325b9dacd6bbe85e8d816`. Native sources were preserved at Git `89da9819` and remained unchanged throughout execution. The two engineering cases, seed, tariff, eight tasks and shared clocks were unchanged from native-v1. This package changed no solver, model or test source.

## Observed result and limitation

The first static 40-trip task completed in 24.48 seconds and retained a plan that passed independent physical replay: four vehicles and a true bill of 658.68. This is an engineering witness, not a learned-model gain, tariff-response finding or full-problem certificate. No global bound was promoted from the restricted solve.

Supervision completed cleanly: no monitor failure, secondary error or cleanup diagnostic; its owned process group was confirmed absent. The maximum recorded complete-sample gap was 0.1828 seconds, below the 0.25-second policy. Peak sampled tree RSS was 223,313,920 bytes; minimum recorded free memory was 23%. The completion acknowledgement was timely and uncensored at 24.480918957851827 seconds. The earlier supervision failure did not recur on this task.

**Qualification nevertheless failed and stopped after one of eight tasks.** The next outer-approximation round reached a deliberate integer-stage pre-build guard at approximately 24.30143 seconds. The guard correctly refused to begin a new model after its 24-second cutoff, while the enclosing physical planner still had about 2.70 seconds before its 27-second cutoff. That refusal raised a generic `TimeoutError`, which the event classifier recorded as an engineering failure. The underlying builder was not called by that refused attempt.

The failed gate remains unchanged. Seven tasks were not dispatched; normal recovery, native partial-start processing, cold control and injected-fault retention were not exercised. One replay-valid static witness and clean supervision do not establish native qualification, recovery effectiveness or comparative performance. See `RECOVERY_PHASE1_V2_REVIEW.md` for the independent diagnosis. No automatic retry occurred.

## Complete accounting

| Component | Charged seconds |
| --- | ---: |
| Effective cumulative charge at native entry, including freeze | 233.41802150122086 |
| First task allocation | 25.05819333344698 |
| Run supervision, including monitor children | 16.754902 |
| Final analysis supervision | 0.262521 |
| **Authoritative cumulative charge** | **275.4936378346678** |

Run supervision includes 15.116176 seconds of measured monitor-child CPU. This overhead is retained in the cost record; it must not disappear from later end-to-end comparisons or be counted twice. Historical failures, conservative charges and allowances remain included. These charges are not all measured solver utilization. The gate report predates the final analysis ledger append; use `compact-summary.json` and `accounting.json` for the authoritative total. The original 900-second cumulative ceiling, 720-second dispatch stop and 180-second shutdown reserve remain unchanged.

## Next bounded action

Implement and test a narrow, typed, evidence-backed representation of the deliberate pre-build cutoff, following `RECOVERY_INTEGER_CUTOFF_REPAIR_PLAN.md`. Ordinary timeouts and build overruns must remain failures. Passing solver-free tests would permit preparation of a new prospective source/output freeze, not automatic native dispatch. Preserve v1 and v2 unchanged. No comparison screen, training, cluster use or protected-data access occurred. No EGG numerical worker remains active.
