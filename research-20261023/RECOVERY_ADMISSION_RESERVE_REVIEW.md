# Prospective admission-reserve contract and resource review

24 October 2026. Narrow static review of the current continuation, v5 diagnosis, coordinator/qualification boundary and relevant native deadline handling. No tests, runtime imports, solver/native jobs, fixture reads, signals or source edits. V5 remains failed at 5/8; this note grants no passing qualification or automatic retry.

## Proposed allocation

The parent's provisional policy is **planned integer stops 10/22 s, planner handoffs 13/25 s**, reserving 2 s before unchanged prefix/full admission endpoints 15/27 s. Original integer caps 12/24 s remain upper bounds; physical output 30 s, outer allocation 32.5 s, cumulative native completion 3 s and finalization reserve 3 s remain unchanged. This applies equally to recovery, static/cold controls and the injected-fault arm. Two seconds is a prospective engineering allocation, not a measured upper bound on replay, capture, storage or model work.

The earlier planner deadline must propagate through wall budget, planner argument and native fixed-topology completion clamp. Outer independent lift, exact bill, durable save and full-bound admission retain their original physical cutoff and post-operation rejection. A reserve guard does not preempt nonpreemptive capture or replay; overruns still fail closed. Preserve an already timely durable fallback on later failure and retain late candidates only as diagnostics. Do not convert generic timeouts into expected stops.

Typed pre-build cutoff evidence must bind the effective 10/22 policy, task/case/phase/anchor and exact observed cutoff; reject stale evidence for the former planned cutoffs. Pre-build, post-build and start-attachment checks must agree. Declare effective handoffs and original caps distinctly in frozen lock validation and result schedules. Frozen native model/replay core need not change.

## Required focused source checks

- Confirm absolute 10/22 and 13/25 propagation without clock resets, completion-allowance renewal or reserve leakage; cover all arms and both recovery stages.
- Exercise timely admission, insufficient remaining reserve, post-lift/save overrun, full-bound timeout and preservation of the prior valid fallback. A fake passing path does not establish actual 80-trip latency.
- Exercise exact typed-token matching under the revised cutoff and rejection of stale/malformed/generic timeout evidence.
- Make 80-trip-first order deterministic in `task_matrix` and lock validation. Current ascending-size sorting ignores design order; merely reversing design metadata is insufficient. Preserve exactly the same eight task identities and within-size arm order.
- Bind changed source/tests to one fresh solver-free check and a fresh freeze/lock/namespace; historical v5 sources, receipts and failure remain immutable.

## Complete planning envelope

Authoritative carry is **912.8922626277902 s**, ADMIN=0. Approved limits remain 1800 hard /1620 dispatch /180 shutdown reserve, one worker/thread and 5 GiB.

| Future component | Planned maximum charge (s) |
| --- | ---: |
| One source-bound check, including its supervision | 40 |
| One external freeze, including its supervision | 40 |
| Eight worker allocations at 32.5 s | 260 |
| Run supervisor and monitor children, counted once | 300 |
| Final analysis | 20 |
| Package contingency | 40 |
| **Total** | **700** |

This totals **1612.8922626277902 s**, leaving **7.1077373722098 s** below dispatch stop and **187.1077373722098 s** below hard ceiling. The 40 s check/freeze provisions each include the 32.5 s external allocation plus 7.5 s supervision provision; they are not longer worker limits. The 300 s run-supervision provision replaces the infeasible old 520 s allowance. V5 monitor costs are calibration only, not a forecast guarantee. Do not add its already charged monitor CPU again.

After check/freeze, reconcile actual complete charges and recompute whether the remaining eight allocations plus declared supervision/analysis provision still fit. Existing per-dispatch runtime budget gates remain authoritative; the envelope cannot guarantee completion if monitoring or admission overruns. First engineering/resource/receipt failure stops dispatch; missing/undispatched outcomes remain visible, with no automatic retry, extra case or shutdown-reserve borrowing.

## Stable runtime/test readback and check gate

Reviewed the stable coordinator/qualification diff and new reserve test module plus the three existing test adaptations. Original Schedule fields remain 12/15/24/27; separate effective 10/22 and handoff 13/25 fields propagate through planner/native budgets and frozen split/result metadata. Typed evidence requires the effective cutoff and independently checked original upper cutoff. Planner returns without a candidate are also subject to handoff rejection. Task generation now explicitly sorts 80 first while preserving task identity construction and within-size arms.

The final durability correction publishes the first fallback/selected witness only after successful save and its timely post-save observation. A late persisted artifact is a rejected diagnostic, not an admitted fallback; save exceptions leave no published fallback. A previously admitted fallback survives later candidate failures. Independent replay and physical post-operation guards remain.

The planned 191-case suite adds actual fake-clock coordinator/control/native-hook coverage to the previous suite, covering effective budget propagation, unchanged hard caps, cumulative completion, exact handoff boundaries, late no-plan/bound-only return, prefix stop, prior fallback retention, late/failed first save and deterministic 80-first task identities. Existing typed-cutoff tests preserve generic/post-build failure classification and reject stale effective/original upper-cutoff evidence. No tests were executed by this reviewer.

**Source/test contract gate: clear for one fresh source-bound solver-free check**, subject to final parent review and freezing of its exact wrapper/protocol/inventory. No concrete runtime/test blocker was found in this narrow readback. The 700 s envelope remains prospective; this is not a passing check, external-freeze gate or native-launch gate. Reconcile actual complete charges before any subsequent phase.
