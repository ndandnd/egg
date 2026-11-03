# Supervision repair check — 23 October 2026

The focused repair passes **54 solver-free tests**: the existing operational regression suite and13 new failure-path regressions. The single recorded attempt completed with stable sources, no monitoring failure and no surviving owned test groups. No native qualification was rerun, and the previous failed native gate remains failed.

The repair replaces separate80ms query timeouts with one bounded sample deadline, retains the exact timeout command/context, and treats permission-denied existence probes as unknown until absence is confirmed. Finalization now preserves primary and secondary errors, closes acknowledgment descriptors once, and reuses immutable receipts without duplicating task charges. Incomplete audit or post-receipt audit errors block automatic resume.

Sampling now targets0.05s to leave a slow query sufficient slack within the unchanged0.25s maximum completed-sample interval. The worker endpoint remains30s; supervisory stop begins by31s, and cleanup phases share the absolute32.5s outer deadline. Native solving gains no extra time. Monitor child CPU is separately measured around each sequential query and included once in budget checks and the supervisor ledger.

Most new cases use deterministic fake clocks/processes. The existing real parent-death/TERM-resistant-descendant helper also ran under the check supervisor. These checks do not establish that the repaired native timetable execution passes, nor do they establish a learning-quality or performance result.

| Evidence | Recorded value |
| --- | ---: |
| Pytest | 54 passed in2.04s |
| Charged allocation | 2.6541769579052925s |
| Check-supervisor CPU | 0.074112s |
| Observed reaped child CPU | 0.926179s |
| Peak sampled process-tree RSS | 92,848,128 bytes |
| Surviving owned groups | 0/3 |

**Current cumulative qualification charge is212.08502712584297CPU seconds.** It carries the historical169.35673816793766 ledger total, a newly explicit20s reconciliation allowance for old unmeasured native-monitor child CPU,20s current administration and the complete check allocation/supervisor charge. Those allowances are conservative accounting, not measured utilization. The old native receipts and their historical charge definition remain unchanged. `RECOVERY_SUPERVISION_REPAIR_PROTOCOL.md` recorded both allowances before dispatch.

The original900s hard ceiling and720s dispatch stop remain. The next freeze must use `supervision-repair-checks/accounting.json` and the passing `attempt01`, preserving native-v1 failure evidence and all prior spend. No second check, native retry or comparison screen is authorized by this result.

Next package: prospectively freeze a repaired native revision in a new namespace, using the same50997/40 and50999/80 identity-selected cases, current source/check hashes and exact original eight-task matrix. Review the freeze receipt before a deliberate native run. Do not replace cases according to outcomes or interpret unexercised paths as passing.
