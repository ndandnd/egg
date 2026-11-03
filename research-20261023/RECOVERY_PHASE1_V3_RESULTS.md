# Native recovery qualification revision 3: results

23 October 2026. The repaired revision passed its external source-bound freeze and deliberately attempted the unchanged engineering matrix. Qualification **failed/incomplete at five of eight tasks**. Four 40-trip tasks completed cleanly; the first 80-trip task missed the physical endpoint and stopped subsequent dispatch. The three remaining 80-trip tasks were not launched. No retry followed. Sources/models were unchanged throughout execution; current runtime source is preserved at Git `f3f93e6c` and lock SHA256 `0c874e7a6474eb04b1dd51d297b347249c1ff0c79d24d338deda01803bc6a436`.

## Observed engineering behavior

| Trips | Task | Endpoint seconds | Observation |
| --- | --- | ---: | --- |
| 40 | Static restricted | 24.766 | Replay-valid retained witness; expected cutoff |
| 40 | Full recovery | 26.568 | One native binary start processed and accepted; fallback retained |
| 40 | Cold full | 25.543 | Replay-valid witness and full-model bound provenance |
| 40 | Injected setter failure | 13.495 | Fault exercised after durable fallback; same fallback retained |
| 80 | Static restricted | 30.384 | Late/censored, no admitted task result; dispatch stopped |

All five terminal supervisor receipts were clean, with owned groups confirmed absent. Independent analysis found zero invalid admitted witnesses, mapping violations or bound-scope violations; it found one censored endpoint. Expected pre-build cutoffs remained explicit diagnostics rather than engineering failures. The accepted recovery start is supported by attributed native log spans, not setter success alone. Extra unattributed messages do not create additional submissions or acceptances.

The three 40-trip static/recovery/fault witnesses had the same exact bill, approximately 658.68, and were preserved under the injected fault. The cold witness was approximately 658.71. These are single-seed engineering observations using a nonlearned ranking, not a matched economic comparison, ML prediction result, tariff-response finding, optimality proof or superiority claim. Full-model lower bounds remain distinct from restricted/fixed-route bounds. Four clean tasks do not convert the incomplete eight-task qualification into a pass.

## Why the 80-trip task failed

The native integer call returned at about 24.062 seconds. Candidate processing ended at about 27.996 seconds, already beyond the 27-second physical cutoff. An intervening interval of approximately 2.73 seconds includes full incumbent capture and synchronous evidence work; candidate processing itself took approximately 1.21 seconds. Exact capture, serialization and replay costs are not separately instrumented. The outer control then attempted additional independent lift/replay before checking its cutoff, discarded the late candidate, and finalized at 30.384 seconds.

The trace supports a physically valid late candidate, not an admissible timely result or evidence of physical infeasibility. Capture/evidence payloads and repeated serialization are material overhead, but the current timestamps cannot identify a single dominant cause. See `RECOVERY_PHASE1_V3_TIMING_DIAGNOSIS.md`; do not attribute the miss solely to the outer lift or rescue the censored outcome retrospectively.

## Complete accounting and resource evidence

| Component | Charged seconds |
| --- | ---: |
| Effective native-entry carry including freeze | 320.3288348765555 |
| Five task allocations | 123.77242229226977 |
| Run supervision including monitor children | 96.94560999999948 |
| Final analysis supervision | 1.9726150000000002 |
| **Authoritative cumulative qualification charge** | **543.0194821688248** |

Run supervision includes 83.90231099999947 seconds of measured monitor-child CPU, retained once. Historical failures and conservative administration/elapsed charges remain included; these charges are not all native solver utilization. The analysis gate predates the final ledger append; use `compact-summary.json` and `accounting.json` for the complete total.

There were 2,107 saved resource samples; maximum recorded sample gap was 0.1351 seconds, peak sampled tree RSS was 518,848,512 bytes, and minimum recorded free memory was 23%. The original one-worker/one-thread/5 GiB limits and 900-second hard ceiling/720-second dispatch stop/180-second shutdown reserve were preserved. No EGG numerical process remains. No cluster, protected data or training was used.

## Next bounded package

Repair unnecessary post-cutoff admission work and add explicit stage timing. Replace repeated complete capture payloads in accumulated events with checked references after one durable complete capture, without losing raw evidence or weakening independent replay. Any additional admission reserve must shorten search within the existing deadline. First perform source-bound solver-free checks, preserving v3 unchanged.

The current dispatch-stop headroom is only **176.980518 charged seconds before further administration/check/freeze costs**. It cannot cover an unconditional eight-task repeat even before monitor overhead. Do not launch such a repeat, reuse the failed namespace, lengthen time or silently reset the budget. After the repair/check, prospectively define a sufficient scoped qualification with explicit evidence reuse limits and feasible resource accounting, or resolve a changed budget before dispatch. No broader comparison can launch before its applicable engineering gates pass. This package makes no model-quality or publication-readiness claim.
