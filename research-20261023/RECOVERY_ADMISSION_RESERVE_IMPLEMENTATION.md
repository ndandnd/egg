# Earlier planner handoff and independent admission reserve

24 October 2026. Source-only implementation after native-v5's correctly rejected
late 80-trip lift. No solver, test, runtime import, fixture generation or native
retry was performed by the implementation agent. V1–v5 evidence is unchanged.
The authoritative carry remains 912.8922626277902s; parent owns later checks and
execution under 1800s total /1620s dispatch /180s reserve, ADMIN0.

## Declared allocation

All endpoints below are seconds after the same supervisor monotonic anchor.
Static and cold controls use the full-stage allocation; recovery and fault arms
use the prefix and full allocations without resetting any clock or allowance.

| Stage | Planned integer search | Original integer upper cap | Planner handoff | Independent admission cutoff |
| --- | ---: | ---: | ---: | ---: |
| Prefix | 10 | 12 | 13 | 15 |
| Full / static / cold | 22 | 24 | 25 | 27 |

This reserves two seconds for independent full-case lift/replay, witness copies,
durable fallback persistence and unrestricted bound admission. The three seconds
between planned search and planner handoff also contain candidate processing,
full incumbent capture and any fixed-topology completion. Native completion is
still capped at **three seconds cumulative across stages**, not three new
seconds per stage. Final materialization remains bounded by30 and supervisory
cleanup by32.5. These allocations are conservative engineering choices, not a
measured worst-case latency guarantee; nonpreemptive work may still overrun and
must be reported as failure.

## Source changes

`src/egglab/recovery_coordinator.py` retains the original Schedule hard endpoints
and adds distinct `prefix_search_end`, `full_search_end`,
`prefix_handoff_end`, `full_handoff_end`, `admission_reserve_s` and `as_dict()`.
Planner budgets, external deadlines and native clamps use10/22 and13/25.
Every planner return, including no-plan returns, is clock-checked against its
handoff; a late prefix return stops full dispatch. Admission entry is checked
again before the lift. Exact13/25 handoffs are permitted; returns or entries
after them fail. Anchored planner-return and lift-entry/exit events expose the
handoff separately from the unchanged15/27 admission endpoint. Post-lift,
copy and durable-save cutoff checks remain in force. Late or rejected new work
does not replace a previously admitted selected witness or erase its exact bill.
A first witness is published as fallback/selected only after its durable save
returns within the admission cutoff. A late saved artifact remains diagnostic
evidence in an explicit rejection event, with failure recorded and no newly
admitted fallback. A failed save likewise cannot admit the first witness.

`src/experiments/recovery_qualification.py` applies the same full allocation to
static/cold controls, with uniform post-return and pre-lift checks, post-copy/save
checks and result schedule metadata. `qualification_split()` records both
original upper caps and new planned search/handoff/reserve fields; freeze and
lock verification require that exact policy. Fresh task locks deterministically
put80 trips before40, preserving arm order and task identities.

The typed pre-build guard, post-build check and start-attachment gate use the
effective10/22 search cutoff. Durable `IntegerGateClosed` evidence now records
both `integer_cutoff` (10/22) and `integer_upper_cutoff` (12/24), anchored to the
same supervisor time. The one-use classifier validates both; stale12/24 planned
cutoffs, generic timeouts, build overruns, sink failures and mismatched tokens
remain failures. Full capture, native model/planner implementation, independent
lift/replay, exact billing and lower-bound provenance are unchanged.

## Verification status

Independent static runtime review found no contract blocker. Parent must freeze
the final sources plus focused and existing solver-free tests for one explicit
check before any fresh lock/native qualification. Passing fakes can establish
deadline propagation, rejection and fallback retention; they cannot establish
real80-trip completion within the reserve. No earlier failed lock is eligible
for dispatch against these changed sources.
