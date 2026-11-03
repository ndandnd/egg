# Proposed repair: distinguish an intentional integer cutoff

23 October 2026. Proposal following native-v2's failed one-of-eight qualification. This note executes no source change, check or native retry. Carry 275.4936378346678 charged seconds; preserve all v1/v2 evidence. The shared 900-second ceiling, 720-second dispatch stop, one single-thread worker and 5 GiB limit continue to apply.

The next bounded package should change only the expected-cutoff representation and its focused tests. The physical model, replay, retained witness, pricing, fixtures and learning assets need no change for this diagnosis.

1. Use a dedicated guard-owned exception such as `IntegerGateClosed(TimeoutError)` for deliberate refusal before invoking the underlying model builder. Do not classify by an error-message substring.
2. Record durable task/case/phase identity, supervisor clock anchor, absolute integer cutoff, observed finite monotonic time, guard point `before_model_build` and `native_dispatched=false`. Issue a single-use pending token when this guard closes.
3. Treat the event as an expected budget stop only when the exact typed event matches that token, correct task/case/phase and pre-build stage, the cutoff equals the applicable original 12- or 24-second anchored policy, and observed time is at or after that cutoff. Keep the diagnostic visible. Unmatched/reused tokens or malformed evidence remain engineering failures.
4. Keep generic `TimeoutError`, native/build timeout, build overrun, post-dispatch refusal, replay, storage, sink, resource and monitor failures fatal. An expected cutoff does not grant extra time, excuse a censored endpoint or convert missing coverage to a pass.
5. Add solver-free tests for the exact boundary, pre-cutoff rejection, wrong phase/case/task/anchor/cutoff, nonfinite times, reused/missing token, generic timeout and genuine overrun. Retain primary/secondary-failure and finalization tests.

Before running checks, freeze exact changed source/test hashes, argv, attempt namespace and a prospective allowance within the remaining cumulative budget. Preserve failures without automatic retries. After review of the single check receipt, any deliberate native revision 3 needs its own protocol, source/environment/task lock, externally supervised freeze and output namespace. Retain cases 50997/40 and 50999/80, seed 17, day tariff, the original eight-task matrix and original clocks. Do not replace an outcome, lengthen a solve or begin the comparison screen from this proposal alone.
