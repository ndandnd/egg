# Native-v6: full processing missed the planner handoff

24 October 2026. Bounded read-only diagnosis from the two terminal task
supervisor/result/completion receipts, targeted native events, gates and relevant
runner/coordinator/native interfaces. No captured variable payload, trained asset
or sealed data was inspected. No source change, test, solver or retry occurred.
Parent owns accounting. V6 remains **failed, stopped at2/8**, with six tasks
undispatched and the fault path unexercised.

## Outcome and exact failure

The80-trip static control passed: planner returned24.930877000s, independent
lift ran24.930894042–25.223653668s, and result fsync completed25.451054876s.
Its full-case fallback is valid; output was uncensored. The new reserve therefore
resolved the earlier static failure on this execution, without establishing a
general latency bound.

The subsequent80-trip recovery task `85710efee4db820ff4bc` retained a valid,
timely durable prefix fallback and submitted a full-model partial binary start.
The native evidence classifies that start as **processed and accepted**. Its sole
terminal failure is **`TimeoutError`**, stage **`full`**, message
**`Planner return exceeded admission handoff`**. Native engineering events are
empty; the evidence sink reports no failure. Resource supervision and cleanup
are clean. A feasible retained fallback and uncensored output do not make the
frozen full-stage handoff pass.

## Anchored recovery timeline

Anchor: `6010209.246793583`. Times below are elapsed seconds. Integer-return
times reconstructed from dispatch plus recorded native duration are approximate;
the hook samples its duration immediately after the dispatch event.

| Event | Elapsed seconds |
| --- | ---: |
| Prefix integer search dispatch / planned cutoff | 1.460707708 /10 |
| Prefix planner return; handoff13 | 12.762953333 |
| Independent prefix lift entry / exit | 12.762959208 /13.051808542 |
| Prefix fallback durable admission; cutoff15 | 13.076793750 |
| Full planner dispatch | 13.077449625 |
| Full integer native dispatch / planned cutoff | 15.756774792 /22 |
| Full integer native return, reconstructed | approximately22.025570626 |
| Full candidate processing entry, inferred | 24.410437417 |
| Full candidate processing exit, inferred | 25.900056792 |
| Full planner return; handoff25 | 26.015096875 |
| Materialization entry | 26.049409667 |
| Result fsync endpoint; output cutoff30 | 26.635278917 |

The prefix typed pre-build stop was correctly matched to its effective10-second
cutoff and original12-second upper cap. Full search received a22-second absolute
deadline and overshot it by approximately0.025571s in its native return. This
small native stop latency does not explain the later1.015097s planner-handoff
overrun. Original integer upper caps12/24, admission cutoffs15/27, output30 and
cleanup32.5 remain distinct from the planned search/handoff allocations.

## Where the full-stage time went

The full incumbent reference binds **39,779,425 bytes**, versus21,279,163 bytes
for this task's prefix capture and the static capture. Complete captures remain
durable; compact references are forwarded. The approximately2.384867s between
integer return and candidate-processing entry includes full snapshot construction,
serialization, write/fsync, immediate byte/hash/envelope verification and adjacent
instrumentation. There are no separate timestamps for these components, so this
is not an isolated measurement of disk persistence or capture cost.

Candidate processing then took **1.489619375s**, finishing0.900056792s after the
25-second planner deadline. `_candidate_impl` first extracts and replay-scores
the raw candidate, then attempts fixed-topology completion. Completion refused
immediately with `TimeoutError: No time for fixed-topology completion`; its native
stage list is empty. The cumulative0.083832084s native completion charge belongs
to the prefix; full-stage completion did not spend additional native time.
The completion-alternative rejection is an explicitly allowed alternative path,
not a hidden native engineering failure.

The raw full-case candidate was internally replay-admitted and its objective
reconstructed; the diagnostic true bill is3628.9138160493826, below the retained
prefix bill3642.5298555555555. Approximately0.115040s more elapsed before planner
return. The total observed native-return-to-planner-return tail is approximately
3.989526s, exceeding the allocated three-second22→25 tail. These observations do
not prove a safe universal replacement constant.

## Captured candidate versus admitted fallback

The full candidate was not erased: its complete native capture and replayed
iteration diagnostics are preserved. It was **not independently admitted by the
coordinator**. `solve()` checks the return before returning its result to the
caller; at26.015096875 it raises under the frozen strict25-second handoff.
Consequently `full_result` remains unset, no `full_candidate` lift occurs, no
new full lower bound is imported, and no full candidate replaces the selected
fallback. The only outer admission stage is `prefix_lift`.

The saved selected witness equals the previously admitted prefix fallback,
including its exact bill. At full return,0.984903125s remained before the hard27
admission cutoff, but V6 did not authorize spending that interval after a missed
handoff. Whether a hypothetical new lift would have completed is unobserved.
The30-second endpoint was met; this cannot retroactively satisfy25 or establish
a timely new full-case admission. Gates correctly remain false.

## Prospective policy alternatives, not a V6 reclassification

One option retains strict13/25 handoffs and gives full capture, extraction,
independent raw admission, completion setup and postprocessing an explicit
conservative internal budget, shortening native search accordingly. The observed
39.8MB full capture and approximately3.99s processing tail show why an isolated
0.1-second adjustment is not principled. Deadline-aware capture/completion would
need declared safe checkpoints and lossless evidence retention; optional repair
must not erase a previously replay-valid candidate or durable fallback.

A different anytime interface could prospectively treat13/25 as planner budget
targets, record overruns, and attempt independent admission only while time
remains before15/27. Actual replay, copying and durable admission would still
have to finish by the hard cutoff, with artifacts by30; late candidates would
remain rejected and prior valid fallbacks retained. This can use residual time
but offers no guaranteed admission reserve. It changes the handoff contract and
its engineering-failure classification, rather than fixing a misclassified
exception in V6.

Either policy requires one declared allocation applied consistently across arms,
a new source-bound protocol/check and prospective adjudication. V6 stays failed;
there is no automatic retry or claim that aggregate start acceptance covers both
sizes or the unexecuted fault path.
