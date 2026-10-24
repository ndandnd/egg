# Explicit60-second comparison composition

24 October2026. New `src/egglab/comparison_coordinator.py` and this note only.
The qualified30-second coordinator/runner, native model, replay and assets remain
unchanged. No runtime import, test, numerical call, process, fixture generation
or comparison was executed by this implementation agent. The separate provider
owner supplies `constructive_proposal.propose`. This composite and its actual
native behavior remain **unqualified**.

## Schedule and interfaces

`Schedule60(parent_monotonic, deadline)` requires exactly60 seconds between the
supervisor anchor and deadline. It is a new class, not a silent scaling of the
qualified30-second Schedule. Absolute offsets are:

| Stage | Original integer upper | Planned search | Planner target | Hard admission |
| --- | ---: | ---: | ---: | ---: |
| Restricted recovery prefix | 24 | 20 | 26 | 30 |
| Full unrestricted search | 48 | 44 | 50 | 54 |

Finalization reserve is6 seconds; planned admission headroom is4 seconds. CF1
construction ends at6 and charging stage at12. Native fixed-topology time is
limited to6 seconds cumulatively, not6 per stage. Every operation remains charged
to the original anchor, including loading/scoring before this function is called.

`coordinate60(source_case, full_case, a, b, *, arm='recovery',
parent_monotonic, deadline, storage, budget=None, planner=None,
proposal_provider=None, clock=time.monotonic, allowed=...)` supports:

- `recovery`: one restricted prefix invocation, then at most one full invocation.
- `cold`: skip both restricted search and CF1; attempt full search with remaining
  absolute time.
- `cf1`: CF1 replaces the restricted prefix. Call the provider once, then attempt
  full search. There is no second restricted attempt after no proposal.

The provider receives `(full_case,a,b)` and keyword-only `schedule`, `allowance`,
`budget`, `clock`, `allowed`, `events`. The exact same
`rc.CompletionAllowance(limit=6)` object is passed to it and later planner hooks.
The provider owns its native_limits scope; the coordinator never nests another
scope around it. Only fixed native-call elapsed time debits that allowance;
provider setup/replay/repair wall time is separately bounded, not double-debited.
Constructor/helper/undo injection remains the provider's interface.

One checked clock is passed uniformly to planners, provider, native hooks and
storage. It rejects bool/nonfinite/non-numeric readings, readings before the
supervisor anchor and backward movement. Invalid initial time raises before any
work. A later fault is sticky: even raw-clock recovery cannot reopen checked
reads, admission or native dispatch. Prior durable fallback artifacts remain;
bounds/certification are cleared, result status is `clock_failed`, and inability
to obtain a trustworthy final endpoint follows the censored materialization-
failure path. A clock fault never becomes a fresh allowance.
Finalization checks the clock again even if custom storage returns success after
swallowing a clock exception. A first fault during materialization also replaces
the returned diagnostic status with `clock_failed`, clears global bounds and
provenance, includes the sticky cause and forces censorship. The diagnostic labels
which status it supersedes; already written result/completion files remain
untouched and may retain their earlier status. This is no history rewrite.

## Admission and retention

The coordinator reuses qualified `native_limits`, `lift_plan`, `_full_lower`,
`admission_window` and the DirectoryStorage protocol. Planner calls retain the
exact `solve_planner` signature and `completion=True`. Provider plans are raw
proposals, not admitted fallbacks. Their supplied completion deadline must be
finite, no later than the absolute charging-stage endpoint12, and respected by
the actual completed provider return. A late provider return cannot rescue its
in-memory plan.

Targets26/50 remain diagnostic for nonpreemptive planner returns; new admission
must start strictly before30/54. Completed returns and work finishing exactly
at an endpoint are permitted, but actual lift, copy and required save overruns
fail. First witness publication occurs only after successful timely durable
saving. Warm full dispatch cannot precede that save. Best admitted witness
selection compares `Fraction(true_bill_exact)`, including differences hidden by
equal rounded float totals. A later replay rejection, start/search exception or
deadline miss cannot erase an earlier valid fallback.

Known prefix/provider failures can fall back to cold full search while time and
the external gate remain. Storage failure, actual acquisition hard-cutoff breach
or unknown round accounting blocks further dispatch. Loading past an unused
prefix window alone does not renew it or prohibit otherwise available cold full
time. Only independently re-admitted unrestricted full MIP bounds are promoted;
restricted and CF1 fixed-topology bounds remain diagnostic. Contradictions clear
global bounds without discarding physical witnesses.

## Eight-round dispatch guard

Default budget permits eight MIP rounds total; larger requested caps are rejected.
Full receives the remaining cap after acquisition, not another eight rounds.
The event list passed to `native_limits` guards its `native_dispatch` append,
which occurs before the original optimizer call. It reserves unfixed calls and
raises before an extra backend optimization, even if a fake/misbehaving planner
ignores its remaining budget. An unfixed call from CF1 is rejected.

Per-stage usage conservatively reconciles the maximum of native-start count,
actual unfixed dispatch count, valid result-round length and observed failed/start
round indices. These are overlapping observations, never summed. Failed calls
remain counted even if no planner result is returned. Missing/malformed result
rounds, duplicate/gapped indices, exceptions with incomplete accounting or cap
violations stop further dispatch; unknown is never interpreted as a free zero.
Fixed charging calls consume the shared time allowance, not this MIP-round quota.
This guard bounds optimizer dispatch; it is not a qualified60-second pre-build
or native-start instrumentation system.

## Evidence and remaining qualification

Results/schedules explicitly identify `comparison60-anytime-coordinator-v1` and
`native_qualification_established=false`. Inherited storage receipt policy labels
the unchanged storage protocol, while its actual anchor/deadline/elapsed fields
still describe60 seconds. Result and completion fsync costs determine censorship
under the original endpoint; no fresh materialization clock is introduced.

`start_proposal` records whether the coordinator proposed its durable plan to
full search. Native processing is explicitly `unknown`, requiring external
attributable log evidence. Binary attachment, callback status or dispatch alone
cannot establish native acceptance or processing.

The compact provider audit preserves construction/repair ledgers and charging
inventories, statuses, scoped stats, failures and deadlines. Duplicate raw plans,
replay and capture events are excluded there: admitted plans remain selected/
fallback artifacts, complete captures remain in the root event stream. Every
root event receives an ordered unique `event_sequence`, distinguishing captures
across provider attempts and full search even when helper round numbers restart0.
A future durable capture sink must bind phase/attempt or this sequence and must
not overwrite captures by bare round number. No capture-persistence refactor is
claimed in this source package.

Focused fake checks and independent review are pending parent execution. Existing
30-second native instrumentation/locks cannot silently qualify this60-second
composition, full evidence pipeline or proposed study. Parent owns any new
source-bound gate and later native decision. Current carry is1295.1392203401801s,
ADMIN0, under1800/1620/180 and one thread/5GiB; no comparison campaign or new
resource commitment is created here.
