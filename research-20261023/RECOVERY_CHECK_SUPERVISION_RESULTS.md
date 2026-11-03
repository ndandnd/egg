# Revised check supervision and admission/capture validation

24 October 2026 UTC. The one deliberately recorded check-supervision revision passed **118 solver-free tests**: the previous86 runner/supervision/cutoff cases,26 admission/capture cases and6 focused check-supervisor regressions. Exact source/output/artifact hashes matched, no primary or secondary failure occurred, the leader was reaped, and all three owned process groups were confirmed absent. No native solve, timetable generation, training, cluster or protected-data access occurred.

The current admission/capture implementation is now supported by the solver-free check: pre-lift deadline guard, unchanged post-lift guard, anchored timing, complete exclusive durable captures and compact identity/hash-bound references through actual worker/coordinator/materialization paths. Malformed/corrupt references fail closed and preserve an existing physical fallback. These tests validate interface behavior; net80-trip latency and ML/economic performance remain unproved.

The new check supervisor reuses the reviewed shared sample deadlines/early scheduling and bounded cleanup, with registered detached test-group ownership. Known PGIDs, reap status, primary and secondary errors survive cleanup/audit failures. Output hashes can be explicitly missing without erasing the terminal diagnosis. Unknown child-CPU observations cannot pass. Tests cover these failure paths without native imports. The old failed wrapper/check remains failed and immutable, with its separate cleanup reconciliation preserved; it was not resumed or overwritten.

## Accounting

| Component | Charged seconds |
| --- | ---: |
| Complete prior cumulative charge | 565.0277991267408 |
| Prospective package administration/closeout allowance | 20.0 |
| Check allocation | 2.423311499878764 |
| Supervisor CPU | 0.43036099999999994 |
| **Cumulative qualification charge** | **587.8814716266195** |

Pytest reported118passed in2.07seconds. Observed child CPU was2.053517seconds, including1.5361199999999995seconds of measured monitor-child CPU; it is included once, never added again. Conservative elapsed allocation was charged instead. Peak sampled process-tree RSS was97,583,104bytes. The20-second allowance covers preparation, review, hashing, documentation and closeout; these are not measured native solver costs.

## Native gate and resource decision

No new native task was attempted. Native-v3 remains failed/incomplete5/8: four40-trip tasks clean;80-trip admission late/censored; three80-trip tasks undispatched. Existing900-second hard ceiling,720-second dispatch stop and180-second shutdown reserve are unchanged. Remaining dispatch-stop headroom is132.1185283733805seconds, which cannot fit eight32.5-second allocations before overhead.

A concrete proposal in `RECOVERY_BUDGET_EXTENSION_PROPOSAL.md` recommends a total0.5CPUh ceiling (15additionalCPUminutes), one local thread/5GiB, preserving original cases/clocks and all failed spend. Its patch has been checked for applicability but **not applied**. A new budget requires the user's decision because the current heartbeat explicitly imposes the0.25CPUh hard cap. Until then, retain the current limits, perform no automatic native repeat and continue useful offline design/analysis. No comparison screen or publication-readiness claim follows from this check.
