# Prospective 60-second coordinator and CF1 integration source gate

24 October 2026. One bounded integration package after the CF1 source-unit gate.
No actual native solve, timetable generation, model/inference/training, comparison
cohort or cluster work is authorized here. Qualified30-second coordinator,
physical model, replay, lifting, starts and earlier source gates remain unchanged.
New modules expose an explicit60-second coordinator and constructive provider.
Their source checks do not constitute native qualification.

## Explicit clock and method allocation

`Schedule60` requires a finite supervisor anchor t0 and endpoint t0+60 exactly.
Freeze these absolute offsets before outcomes; do not modify old Schedule:

| Endpoint | Offset seconds |
| --- | ---: |
| CF1 construction end | 6 |
| CF1 charging stage end | 12 |
| Recovery prefix planned integer search end | 20 |
| Prefix original integer upper cap | 24 |
| Prefix planner target | 26 |
| Prefix physical/durable hard cutoff | 30 |
| Full planned integer search end | 44 |
| Full original integer upper cap | 48 |
| Full planner target | 50 |
| Full physical/bound hard cutoff | 54 |
| Output endpoint | 60 |

Planned admission headroom4 and finalization reserve6 are budgets, not runtime
guarantees. Planner targets may be missed only within still-open hard admission
gates; hard gates never renew the endpoint or permit a new native call beyond
its fixed cutoff. All imports/loading/scoring/construction/rebuilds, checks,
native calls, capture, replay, exact billing, durable writes and finalization
occur after the same supervisor anchor. Method timing begins before this API.
No free reference label, preprocessing, cached score or feasible-route oracle.
New work/dispatch entry closes at>=its hard endpoint. A completed operation or
return may equal its endpoint and is late only when>; this does not reopen a
new operation at equality. Internal helpers may apply stricter own checks.
Every coordinator clock observation (including native hooks and storage) must be
finite, nonboolean, nondecreasing and no earlier than the supervisor anchor;
invalid clocks latch a fault before further dispatch; recovery of the raw clock
does not reopen it. A fault during terminal storage forces a censored returned
diagnostic with certification/bounds withdrawn; already written files remain
unchanged and their pre-fault status is explicitly superseded. A custom provider's claimed
completion deadline may not exceed the declared charging stage endpoint.

Recovery performs at most one restricted prefix then one full solve. Cold skips
the prefix. CF1's provider REPLACES the restricted prefix; a missing constructive
witness may fall directly to cold full search if time/resource gates allow.
CF1 must not receive a second restricted prefix. Unused stage time returns to
full search under the original absolute full cutoff. The unrestricted MIP-round
cap is EIGHT TOTAL across prefix/full, never eight per stage. Reserve native
unfixed dispatch attempts before calling the backend, including failed calls;
pass only remaining rounds to the later planner. Reconcile record/result counts
without adding duplicate observations, fail closed on malformed accounting.
Fixed-route completion calls are governed by shared time quota, not MIP rounds.

Use one `CompletionAllowance(limit=6)` object across every executed phase. The
unchanged `native_limits` hook debits actual fixed-topology backend elapsed once;
no pipeline wall-time addition may double-charge it. All stages share that same
allowance, so CF1 charging and later full-model fixed completion do not each get6.
CF1 additionally freezes ONCE, before initial charging setup/build,
`completion_deadline=min(t0+12, first_completion_anchor+remaining_allowance)`.
The same value applies across feasibility/objectives, at most two LIFO repairs
and every rebuild. Construction ends at t0+6. Stage cutoff or now+6 renewal is
invalid. The whole provider charging window (including setup/replay/repair)
must fit its fixed deadline, although only native elapsed debits shared quota.

Freeze one conservative method rule: a constructor/helper returning past its
own hard endpoint supplies no provider proposal, including an earlier candidate
that remained only in memory. Record the overrun; never repair/renew or relabel
it timely. Cold full search may still use remaining global time. Native behavior
and useful timing remain untested; external supervision is still mandatory.

## Proposal, durable admission and certification

The provider calls the existing pure constructor once. Only qualified INITIAL
fixed-topology feasibility INFEASIBLE with no valid witness may trigger one LIFO
undo; at most two cumulative repairs. Objective infeasibility, timeout, unresolved
status, invalid replay or failed undo may not trigger repair. A valid helper plan
stops that loop. Common allowed/deadline gates apply before and after work and at
every native dispatch through the inherited serialized hook.

Provider plans are unadmitted raw plans, not durable fallbacks or start acceptance.
Coordinator independently lifts/replays/bills them against the full case, then
fsyncs a fallback before any warm full dispatch. Preserve the cheapest witness
using exact Fraction bills, including differences hidden by float totals.
Retain valid fallback through rejected starts, later failure or more expensive
full witnesses. Stop new dispatch on durable-storage failure or missed hard
admission gate. Keep actual start submission and native processing evidence
separate; a warm dispatch itself establishes neither.

Only independently re-admitted ORIGINAL unrestricted full-model MIP bounds may
be global. Restricted prefix/fixed-charging lower values remain labeled diagnostic
subproblem data. Contradiction with physical fallback clears global certification.
Shared final materialization records late result/receipt fsync as censored. Reused
DirectoryStorage receipt policy labels inherited storage mechanics; new result
and schedule policies must explicitly identify60 seconds, not imply30qualification.

## One source-bound solver-free check

After source/API/static review stability, freeze exact hashes and argv in
`comparison-pipeline-checks/command.json`. Parent alone may run one fresh
`attempt01` executing only `test_comparison_pipeline.py`, with handwritten
symbolic inputs, fake storage/planners/provider hooks and native-import guards.
Historical tests may be hashed dependencies but are not rerun. The new suite
may import pure fixture definitions from test_constructive_controls.py; freeze
that module as a dependency while selecting none of its historical test cases. Cover actual
shared-hook debit, conditional repairs, no renewed deadlines, durable-before-start,
late fsync/admission, exact-bill retention, full-bound scope and old30 preservation.
No native dispatch or comparison follows automatically.

Carry **1295.1392203401801 s** from
`constructive-controls-checks/accounting.json`, all earlier charges/failures intact,
ADMIN0. Approved1800 hard/1620 dispatch/180 shutdown, one single-thread worker,
5GiB persist. Reserve one40s check including supervision:30s work,32.5s outer
cleanup plus7.5 provision; planning cumulative1335.1392203401801. Actual complete
charges count. No automatic retry or budget reset. Reviewed supervision helper
bodies stay unchanged. The parent command after freeze is:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_comparison_pipeline_checks.py
```

Review receipts and preserve failures. Even a passing pure/fake gate leaves
actual60-second native behavior, credible control quality and comparisons
unqualified. Next is a separately frozen affected-path native preflight within
remaining qualification resources, not a blind old-matrix repeat. Update handoff
and meaningful GitHub backup; no routine Google Doc append for unit passes.
