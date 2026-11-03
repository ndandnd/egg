# Native-v5: outer admission exceeded its physical cutoff

24 October 2026. Bounded read-only diagnosis of failed task
`de8d8da71bc8d2dd1d5d` using only its supervisor/result/completion/native-event
receipts and relevant runner/coordinator source. No capture payload, model or
sealed data was read; no solver, test, retry or runtime change occurred. V5 remains
stopped at 5/8: four timely 40-trip tasks, then this failed 80-trip static task.
Parent reports no invalid witness, mapping or bound-scope violation. The three
undispatched tasks remain undispatched.

## Exact failure and anchored timeline

The terminal control failure is **`TimeoutError`**, stage **`control`**, message
**`Control physical admission exceeded shared planner cutoff`**. It comes from
the explicit post-lift check in `control`, not a replay exception, capture-reference
failure, native backend exception or OS cleanup failure. Native engineering
events are empty and the evidence sink reports no failure.

Supervisor anchor is `6005866.875673916`. Times below are elapsed seconds.

| Event | Elapsed |
| --- | ---: |
| Integer native dispatch | 1.427784584 |
| Integer native return, reconstructed | 24.029104417 |
| Candidate-processing entry, inferred | 25.396603417 |
| Fixed-topology feasibility dispatch | 26.061034542 |
| Fixed-topology objective dispatch | 26.077901917 |
| Candidate processing complete | 26.814330709 |
| Expected next-round integer guard | 26.827559959 |
| Planner returned to control | 26.840382500 |
| Outer lift entered | 26.840388374 |
| Outer lift returned | 27.134560958 |
| Worker materialization started | 27.136367209 |
| Result fsync endpoint | 27.349969209 |
| Post-completion acknowledgment | 27.350382792 |

The capture reference binds one complete 21,279,163-byte static-round-zero file.
It is forwarded twice as compact references, not duplicated full payloads. The
approximately 1.367499 seconds between integer return and candidate entry include
capture and evidence work; no separate timestamp isolates persistence or replay
verification, so none is assigned an exact duration here.

Candidate processing took 1.417727293 seconds. Both fixed-topology native calls
occurred inside the physical cutoff; cumulative native completion time is
0.079266917 seconds. The subsequent round-one `IntegerGateClosed`, stage
`model_build`, exactly matches the durable guard token and is correctly recorded
as an expected pre-build budget stop, with no new native dispatch.

## What failed, and what did not

The pre-lift check was open: 26.840388374 is before the anchor+27 admission
cutoff. Only **0.159611626 seconds** remained. The independent source-to-full
lift took **0.294172584 seconds**, returning **0.134560958 seconds late**.
Its normal return indicates that validation/replay/billing completed; then the
post-lift clock check cleared `selected` and raised the recorded timeout before
durable fallback admission.

The planner already held a replay-valid restricted-case candidate. That is not
the same artifact as an independently admitted full-case fallback under the
frozen deadline contract. No full-case fallback had been admitted earlier in
this task, so the earlier-fallback retention guarantee was not violated. The
late full lift cannot be retroactively counted as timely simply because final
materialization finished before 30. Saved `selected` and `fallback` are absent,
status is `no_plan`, and the global lower bound is absent.

This is a legitimate enforced **27-second admission cutoff**, exposing
insufficient reserved time for nonpreemptive outer replay/lift. It is not the
earlier integer-cutoff misclassification bug, nor an invalid physical witness.
The post-lift guard behaved as specified. The terminal result is **uncensored**
at 27.349969209 seconds; `worker_failure=true` follows the explicit control
failure list. The frozen stop-on-first-engineering-failure rule was honored.

## Why the fake checks did not establish success here

The 135 solver-free checks validate branches, evidence and accounting using
fake clocks, symbolic cases and small captures. The control tests already
exercise post-lift overrun and require rejection/no fallback. They do not bound
real 80-trip validation cost or guarantee that a planner returning just before
27 leaves enough time for independent full admission. Passing them therefore
predicts correct rejection here, not a successful 80-trip timed endpoint.

## Narrow prospective recommendation

Reserve explicit admission headroom before the unchanged 27-second cutoff:
declare an earlier absolute planner/completion cutoff and an admission-launch
guard, clamping integer search earlier within its existing cap if necessary.
Keep independent source/full replay, exact billing, the post-lift check and
30-second endpoint. Apply the declared allocation consistently across matched
arms; do not grant this case extra time. This trace shows a 0.134561-second
shortfall, not a validated universal reserve.

Retain late candidates as diagnostics only and preserve any already timely
admitted fallback. Do not fix this by suppressing generic timeouts, bypassing
full replay or relabeling v5 as a pass. Any future typed expected-budget outcome
must carry exact cutoff evidence and still report missing timed qualification
coverage. A prospective source-bound revision and actual bounded qualification
would be needed; no implementation or new dispatch is authorized by this note.
