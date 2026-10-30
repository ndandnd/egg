# CF1 late-return preparation diagnostics: bounded source repair

24 October 2026. Scope: ONLY constructive_proposal.py and
comparison_native_worker.py, plus this note. No native adapter, qualified core,
schedule, model, asset or old evidence is changed. The companion charging-helper
owner separately repairs cooperative inventory deadline checks and records
scalar preparation_timings; this provider preserves that additive field.

The first CF1 attempt entered charging around2.204 with a once-frozen8.204
endpoint, but returned around20.392. Previously the provider's post-return guard
raised before retaining the helper result, erasing its failure/stage diagnostics.
These observed times motivate localization, not a larger allowance or a retry.

Immediately after a helper returns, the provider now retains one compact audit
of its status, stages, inventory, scalar preparation_timings and other non-plan
metadata. It excludes plan, replay and events, so no raw incumbent capture or
physical plan is duplicated. Helper failures move to the provider's authoritative
failure list exactly once; they are not copied again inside the compact stage.
The stage adds entry, observed-return and unchanged deadline timestamps. A
clock-read exception is retained as a compact clock_error after the helper audit
has already been saved. A returned clock value passes the same finite,
nondecreasing/allowed/deadline guard without rereading away an invalid value.

Only then does the existing completed-return guard run. A late helper still
cannot supply any proposal/plan, even if it internally retained an earlier
witness. Its original completion deadline remains fixed across repairs, the
shared native allowance is neither reset nor charged again, and no new work
starts at the endpoint. Completed-return equality remains allowed; strictly
past the endpoint remains rejected. The provider's own late/clock failure is
appended once in addition to the preserved helper failures.

The native worker adds compact native_model60_build enter/return events with
monotonic at, phase, case identity and deadline; return adds start and elapsed.
The existing native_model60 event also records build start/finish/elapsed and
cutoff. The same typed pre-build guard is rechecked after entry-marker I/O before
calling the builder. The original fresh post-build clock cutoff check remains
in place after the return marker, so recording overhead cannot make a stale timely timestamp
open the build gate. Invalid/nonfinite/backward build-return time fails closed.
No capture persistence/reference, binary-start mapping, typed integer gate,
clock-sticky behavior or backend/library qualification rule is weakened.

This is source preparation for ONE directly affected symbolic/fake check. No
runtime import, test, native process, fixture/model access, cluster job or retry
was executed by this owner. Native v2 qualification requires a separate
prospective package; this diagnostic repair neither authorizes nor claims it.
