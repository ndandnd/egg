# Supervision repaired; 80-trip admission still needs a time reserve

**Qualification remains incomplete: five of eight tasks ran, then dispatch
stopped at the first failure.** This package used the original two synthetic
engineering timetables, seed 17, nonlearned ranking and fixed stage clocks.
It trained no model and ran no learned-method comparison.

The repaired supervision interface passed 135 solver-free checks and a fresh
externally supervised fixture freeze. Parent and independent review confirmed
current source/command/output hashes, complete ownership cleanup and accounting.
The generated cases, movement identities, market and task matrix were identical
to v4. The old failed v4 freeze remains failed. Its cleanup error did not recur;
the native fault task even retained a transient permission-denied probe followed
by confirmed absence. This is interface evidence, not a runtime guarantee on
other machines or larger cases.

| Engineering timetable / arm | Endpoint (s) | Outcome |
| --- | ---: | --- |
| 40 trips / static | 24.39 | Replay-valid witness retained |
| 40 trips / recovery | 24.95 | Valid fallback; one native partial start processed and accepted |
| 40 trips / cold | 24.84 | Replay-valid witness |
| 40 trips / injected start failure | 12.79 | Same valid fallback survived the fault |
| 80 trips / static | 27.35 | Full-case admission exceeded its 27-second cutoff; no witness admitted |
| 80 trips / remaining three arms | — | Undispatched |

The four successful checks are four paths on **one** timetable, not four
independent timetables or seeds. Independent replay found zero invalid admitted
witnesses; mapping and full/restricted bound audits found zero violations.
Recovery retained its original fallback here; accepted-start evidence alone
does not establish a better solution or useful learning. Eight-task coverage
and 80-trip recovery/fault behavior remain unproved.

## Measured bottleneck

The 80-trip planner returned at 26.8404 seconds. Full-case lift/replay began at
26.8404, with only **0.1596 seconds** before the admission cutoff, and took
**0.2942 seconds**. It returned normally at 27.1346; the post-lift deadline check
then rejected it. The eventual result was uncensored at 27.35 seconds, within
the 30-second output window. This does not make the failed 27-second admission
timely. No late witness was retroactively admitted, and no previously admitted
fallback was lost in this task.

There was no native engineering event, capture-sink failure or replay exception.
The expected pre-build integer cutoff was correctly recognized. The fake tests
had already verified the rejection branch; they did not establish real 80-trip
replay latency. See `RECOVERY_PHASE1_V5_DIAGNOSIS.md` for the anchored timeline.
Its 0.1346-second shortfall is one observation, not a universal reserve estimate.
One complete native capture was 21.28 MB; the available timestamps do not isolate
its persistence cost from other work between native return and candidate entry.

## Accounting and retained evidence

The authoritative terminal-ledger carry is approximately **912.89 charged
seconds**, in `recovery-phase1-v5/accounting.json`, under the approved total
1800/1620/180 policy. It includes every earlier failure, the conservative earlier
watchdog allowance, this check/freeze, all five task allocations, supervisor and
monitor CPU, and the final analysis tail. No new administration was added.
Use the final ledger rather than the slightly earlier gates-report total;
monitor CPU is already included and must not be added again. All owned groups
are confirmed absent and the owner marker is removed. No retry followed.

Plans, complete capture JSON, exact bills, gates, ledger and receipts are retained.
Raw native/license diagnostics stay local with hashes in
`raw-diagnostics-index.json`. The original Google Doc received one consolidated
verified update; exact append and unchanged prior structure were read back
(`google-doc-update.json`). Earlier entries and visuals remain intact.

## Next bounded package

Implement an explicit earlier planner handoff and admission-launch reserve,
consistently across matched controls, inside the existing admission/output
deadlines. Shorten planned search if needed; keep independent full replay and
the post-lift cutoff check. Do not suppress generic timeouts or relabel v5.
Focused fake tests must establish that sub-budgets share the original anchor
and preserve an earlier timely fallback. A deliberate new real qualification
should prioritize the 80-trip bottleneck in its prospectively frozen order,
with unchanged case identities and no automatic retries. Its complete resource
plan must fit the remaining approved ledger. Do not rerun the successful 40-trip
prefix merely to rediscover this same timing failure.

This is an engineering allocation change, not a reason to expand training or
claim an ML contribution. After applicable native gates pass, resume the exact-
cardinality selector and credible classical controls required by the learned-
value study. The existing model's substantive advantage remains an open question.
