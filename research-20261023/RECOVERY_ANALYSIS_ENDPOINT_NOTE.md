# Prospective comparison endpoint adjudication

24 October 2026. Bounded source/protocol review only: no runtime imports, tests,
fixtures, models, inference, solver, data or cluster access. This note specifies
the endpoint contract needed for the **unlaunched** learned-value comparison in
`RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md`. It changes no executable source,
qualification gate, historical failure label, budget or dispatch authorization.
The failed CF1 qualifications remain failed. This is not a launch manifest.

## Separate three questions

1. **Qualification coverage:** did the required fixed-charging/prefix → durable
   acquisition fallback → binary-only full start → attributable native processing
   path actually run? This is a gate on an interface claim, not a plan-quality
   endpoint. Cold success cannot qualify missing CF1 charging or warm-start paths.
2. **Evidence integrity:** can the assigned method's clock, identity, ownership,
   resource accounting, captures, witness admission and durable output be trusted?
   Broken or ambiguous evidence prevents a primary comparison.
3. **Method endpoint:** under a healthy evidence chain, what plan did the complete
   timed method actually deploy, or did it genuinely produce no timely plan?
   Acquisition can fail while cold full search supplies the deployed plan.

Keep acquisition outcome, executed full-search mode and qualification coverage
alongside the endpoint. Do not award an unexecuted warm path any benefit. Native
start **processing** is distinct from native start **acceptance**; a legitimately
rejected start does not itself invalidate an independently replay-valid fallback.
Unexpected setter/interface failures are different and trigger an engineering stop.

## Deterministic precedence before looking at either arm's bill

Apply to each assigned base/regime/seed/arm, preserving all causes and artifacts.
The labels below are proposed adjudication labels, not replacements for old files.

1. Preserve assignment first. No dispatch is `undispatched`, with its budget or
   administrative reason. Never replace an unfavorable assignment or drop the
   unmatched member of a block.
2. Any demonstrated integrity failure, ownership/monitor/clock/accounting fault,
   resource breach or unexpected native-interface failure is
   `infrastructure_unknown`; stop further dispatch. An ambiguous cause is also
   unknown. A method-looking timeout never overrides this evidence. If invalid
   admission or a false full-bound claim is established, retain the more specific
   `invalid_admitted` / `invalid_full_claim` diagnostic and stop; its primary
   outcome is unscorable, not an algorithmic failure/tie. Multiple causes remain
   visible even when one controls the outcome.
3. With the complete healthy chain, independently verify admitted witnesses and
   the final deployed selection. A timely durable replay-valid selected plan is
   `deployable_valid`, including a cold full-search plan after acquisition timeout,
   or an earlier retained fallback after later healthy search/candidate failure.
   Successful acquisition and warm-start acceptance are not necessary for this
   endpoint. A bound is not necessary either.
4. With healthy evidence but no such deployed plan, distinguish
   `algorithmic_no_plan` from `algorithmic_late`. The former is explicit no-plan
   under the frozen policy; the latter has known ordinary execution/admission/
   replay/billing/capture/finalization latency beyond its relevant cutoff. A
   late physical plan is diagnostic, never retroactively admitted. A bare
   `TimeoutError`, `censored=true`, nonzero exit or missing ACK is insufficient
   to establish either known algorithmic category.
5. An integrity check discovered after a provisional valid/no-plan/late label
   supersedes that provisional primary outcome. Never rewrite immutable receipts;
   append a versioned adjudication referencing their hashes and the superseded
   conclusion. No favorable bill can resolve an unknown cause.

“Stop” means stop the study's remaining dispatch and preserve/close owned work and
all spend; it does not convert already known healthy endpoints into failures.
Budget exhaustion stops the incomplete study with its full prefix and missing
suffix. An external administrative kill during an allocation is not evidence
that the algorithm would have failed; without a complete healthy terminal chain
that allocation is unknown. Correctly recorded method no-plan/late is an endpoint,
not a reason to replace the case or automatically stop the comparison.

## Evidence table

All rows require frozen assignment/source/environment binding and the final
integrity adjudication. Fields listed as “add” are prospective schema requirements.

| Observation | Required evidence / key fields | Classification and primary use | Stop rule |
| --- | --- | --- | --- |
| Acquisition times out; cold full search delivers | `prefix_status` or `provider_status`, `provider_audit.stages`, timed acquisition events/cutoffs and complete failure cause; `mode=cold_full`, `full_dispatched`, valid round ledger; independently replayed `selected`, its exact target-tariff bill and durable artifact; final ACK by 60 s | `acquisition=deadline`, `deployable_valid`; use the actual cold result's bill. Retain failed acquisition and missing warm-path coverage | No comparison stop for a healthy policy deadline; qualification still fails if that path was required |
| Acquisition fallback survives later search failure | `durable_fallback_admitted`, matching `fallback_artifact` hash, stage/time, replay/bill, selected identity, later event cause, complete timely terminal chain | `deployable_valid` only if later cause is healthy algorithmic behavior; unexpected interface/integrity failure instead makes comparison unknown | Stop only for integrity/interface fault or invalid claim |
| Raw/completed candidate rejected before admission | Immutable capture reference and `candidate_rejected` stage/cause/time; add candidate ID and explicit `admitted=false`; prove it never became fallback/selected/start source | Ordinary `raw_admission`/`completion_admission` rejection is an acquisition/search diagnostic. Valid fallback still counts; no remaining witness under healthy evidence is no-plan. Fractional or infeasible raw proposals are not invalid admitted plans | No stop solely for a correctly rejected candidate; broken extraction/capture/interface is unknown and stops |
| Admitted fallback/selected witness fails independent replay or bill verification | Admission event/artifact and plan identity, full-case/target-market binding, exact independent replay and bill mismatch evidence | `invalid_admitted`; no primary win/tie or bill gain, even if another plan looks favorable | Stop study; preserve witness and causes |
| Full bound or infeasibility contradicts retained valid witness | `global_lower_bound`, `bound_provenance` scope/round/raw bound/guard, full-case identity/formulation/matrix and objective checks; retained exact replay; contradiction status | `invalid_full_claim`; clear usable certification, preserve contradictory raw evidence; no primary bill outcome. Restricted/fixed-route diagnostic bounds alone are not false full claims | Stop study |
| Healthy method explicitly returns no plan | Known complete shared round accounting, allowed-gate reasons, method/provider status, all rejected/late candidate records, intact monitor/capture/terminal chain; add explicit no-plan cause | `algorithmic_no_plan`; loses to a valid plan, ties another genuine algorithmic no-plan/late | No replacement or automatic comparison stop |
| Healthy ordinary work finishes late | Valid monotonic anchor and all stage/serialization/capture/ACK times; intact hashes and receipts; cause proves ordinary policy-compliant work, with no infrastructure flags | `algorithmic_late`, operationally censored; no late plan bill scored. Same primary treatment as genuine algorithmic no-plan | No automatic comparison stop; preserve overrun and charges |
| Missing/malformed ACK, clock read reversal, capture hash mismatch, unknown round accounting, monitor gap, ownership loss, unexpected interface failure | `clock_failure`, `materialization_failure`, `native_state.sink_failure`, `engineering_events`, supervisor `failure`/`monitor_failure`/`secondary_errors`, ownership probes, hashes and ACK diagnostics | `infrastructure_unknown`; missing primary contribution even opposite a valid result. Missing or corrupt evidence cannot be repaired by inferring a timeout from elapsed time | Engineering stop |
| Resource breach / accounting failure | Owned-tree RSS/CPU observations, limits, monitor coverage, charge ledger and stop reason | Stop condition; unscorable affected endpoint, not opponent win. Healthy undispatched suffix remains missing | Stop before spending further allocations; retain all charges |
| Required warm/charging path simply not exercised | `native_state.path_qualification` components and acquisition reason, attributable native log spans, inventory/capture evidence | `qualification=failed/unexercised`; alone does not establish infrastructure failure in a future comparison. Method may be deployable, no-plan or late after independent adjudication | Current preflight stops; future comparison must not use this coverage bit as its endpoint stop policy |
| Assignment never dispatched or interrupted by budget/admin stop | Frozen assignment list/order, launch ledger and causal stop record; add `dispatch_state` / `missing_reason` | `undispatched` or affected allocation unknown; retain in denominator and missing bounds | Stop at frozen budget/reserve; no selective completion/retry |

## Timing, durability and censorship

The current `Schedule60` is anchored at the supervisor's monotonic timestamp before
interpreter/model loading. Source constants are construction 6, CF1 charging stage
12, prefix search 20 / handoff target 26 / hard admission 30, full search 44 /
handoff target 50 / hard admission 54, and final deadline 60 seconds. MIP rounds
are capped at eight total; native fixed completion shares six seconds. A missed
handoff target is not itself a hard-cutoff violation. Admission entry must be
strictly before the hard cutoff; post-lift/copy/save checks accept equality but
reject times greater than the cutoff in the present source. Freeze these exact
boundary conventions and the timing implementation before future dispatch.

`DirectoryStorage.materialize` fsyncs result bytes, observes
`completion.finished_monotonic`, writes/fsyncs `completion.json`, then observes
another time. Thus the completion file's `censored` bit records result timing;
the returned completion receipt can additionally be censored by completion write
latency. `WorkerStorage.finalize` writes/fsyncs `worker-outcome.json`, then timestamps
and sends one atomic ACK binding result, completion and outcome hashes. The current
endpoint checker combines marker/outcome censorship with result and ACK times.
For a deployable endpoint require the identity/hash-bound post-fsync ACK timestamp
at or before anchor+60 **and** uncensored result/completion/outcome, not merely a
timely plan, an early completion marker or a zero process return code. Preserve
the result-fsync, completion-fsync and post-outcome ACK times separately in the
future schema so the terminal bottleneck is observable.

The 61-second supervisor stop and 62.5-second outer cleanup do not extend the
60-second physical/durable endpoint. Cleanup/ownership/accounting remains required.
Healthy write/capture latency is paid method time. Demonstrably broken writes,
capture contracts or ACK transport are engineering failure. A healthy **late but
complete** ACK can support algorithmic lateness; an absent/malformed ACK provides
no such proof and defaults to unknown. Never equate all censored rows with genuine
algorithmic failure, or all late captures with corrupt evidence.

## Current source behavior and gaps

- `comparison_coordinator.py:289–350` independently attempts acquisition and then
  selects `warm_full` iff it has a fallback, otherwise `cold_full`. A provider
  failure/no-plan returned before the hard acquisition cutoff can leave cold
  dispatch open. Crossing the hard cutoff or unknown round accounting closes it.
  Timeout alone therefore does not promise cold dispatch, but cold success is
  already a meaningful possible method outcome. Its first full candidate may
  supply the durable `fallback` at stage `full_candidate`.
- `comparison_native_worker.py:459–475` requires an acquisition-stage durable
  fallback, replay-valid fallback, full start proposal, binary submission and
  observed processing; CF1 also requires fixed inventory. Failure always appends
  `preflight_path/UnexercisedNativePath` to `engineering_events`. This is correct
  fail-closed **qualification** behavior. It does conflate an ordinary acquisition
  timeout/unexercised method path with infrastructure if reused as a future
  scientific endpoint classifier. The worker is expressly a two-task preflight
  (`task_matrix`: CF1/recovery), not a general six-arm comparison runner; its
  non-CF1 acquisition default would also demand `prefix_lift` for a cold arm.
- The exact administrative chain is `UnexercisedNativePath` →
  `engineering_events`/`result.failures` → `recovery_qualification.py:1203–1205`
  `worker_failure=true` → `:1323–1325` suffix halt (also `:1258–1260` on resume).
  The preflight adapter inherits that finish/run policy. Preflight analysis
  (`comparison_native_preflight.py:394–456`) also treats **any** failure as
  engineering and demands witnesses, processed starts and CF1 charging coverage.
  Do not weaken or retrospectively relabel this failed qualification. A distinct
  source-bound comparison policy/schema must separate coverage from integrity
  and scientific endpoint before launch.
- `record_event` (`comparison_native_worker.py:344–381`) already excludes ordinary
  `raw_admission` / `completion_admission` candidate rejection from engineering
  flags. Only the exact token/hash/case/phase-bound `IntegerGateClosed60` event is
  recognized as an expected native budget stop; every other native-search failure
  is flagged. That narrow qualification allowlist is not a complete prospective
  taxonomy for ordinary CF1 construction/charging/admission timeouts. Exception
  class/message and `bool(failures)` alone are not sufficient cause adjudication.
- `comparison_coordinator.py:351–375` and `recovery_coordinator.py:395–408` detect
  replay/bound contradictions, remove usable lower provenance and retain a
  contradiction status (subject to storage/clock precedence). `_full_lower`
  (`recovery_coordinator.py:214–246`) re-admits original unrestricted MIP bounds
  with full identity/formulation/matrix and replay/objective guard. Preserve
  these checks; a fixed-route completion bound or restricted-prefix diagnostic
  must never certify the full problem. A feasible bill without a bound is valid.
- Current dictionaries contain status/failures/events, not a versioned endpoint
  adjudication schema. Add explicit, independent `qualification`, `integrity`,
  `acquisition`, `executed_mode`, `deployment`, `dispatch_state`, `stop_scope`,
  `primary_eligible` and causal evidence-reference fields. Add candidate/witness
  IDs linking capture → rejection/admission → durable artifact → selected output
  → start source; do not infer admitted state from an error string. Record accepted,
  rejected, processed, unobserved and interface-failed starts separately.
- `completion_endpoint` (`comparison_native_preflight.py:239–270`) collapses many
  malformed/hash/clock/storage failures into `missing_or_malformed_completion`;
  retain granular validation diagnostics and all terminal timestamps prospectively.
  The existing `endpoint_wall_s` is result-fsync elapsed time, not ACK elapsed time.
  Do not report it alone as the complete 60-second deployment endpoint. Independent
  source-bound adjudication must reference immutable supervisor/worker/capture
  receipts and preserve provisional versus final classifications.

## Pair scoring and retained missingness

### Integration refinement: a separately qualified failure-only certificate

The earlier table's missing-ACK-to-unknown default is correct for CURRENT receipts,
but is not a universal requirement that every known algorithmic failure have a
worker ACK. An independent integration reviewer identified this overstatement.
The addendum's complete healthy receipt chain may prospectively be completed by
a distinct source-bound controller certificate of ordinary method deadline with
no timely deployment. Root adopted the narrower rule in RECOVERY_ANALYSIS_CONTRACT.md.

That future failure-only path needs frozen task/source/clock/ownership binding,
the full uninterrupted assigned method window, positive evidence that its preset
ordinary deadline caused the stop, affirmative stage health, no earlier/concurrent
integrity/interface/accounting/resource fault, definitive ACK-channel drain and
closure after all owned writers terminate, and proven cleanup/full charges.
Preserve all bytes/times/partial or malformed messages; silence or a stop-reason
string cannot supply missing causal health evidence. Administrative cancellation
before the complete allocation is unknown. Partial/malformed ACK, transport/read
fault or ambiguous stage cause remains unknown.

This certificate may support algorithmic_deadline_no_deployment only, never a
valid plan/bill/bound, successful finalization or qualification coverage. Existing
cleanup has no qualified drain-to-EOF/no-writer certificate, so current missing
ACKs remain unknown and historical gates remain failed. This note does not
implement or qualify the new controller path, authorize execution or reclassify
any current receipt.

For graph versus CA1 (primary), and graph versus CatBoost/CF1 (direct secondaries),
use a contribution of +1/0/−1 only after both endpoints are adjudicated. A valid
plan beats a genuine algorithmic no-plan/late; two genuine algorithmic failures
tie. With both valid, lower target-tariff bill wins outside
`0.005 * max(abs(B_graph), abs(B_control), 1 currency unit)`; otherwise tie.
Infrastructure-unknown, invalid admitted/full claims and undispatched endpoints
are missing comparisons, including when the other arm is valid. Never award the
other arm a win or call two unknown/invalid rows a both-failed tie.

Keep every assigned seed contribution; bound each missing contribution in [−1,1],
average the three seeds within each base, weight bases equally and sizes equally,
and report the resulting incomplete-study interval plus all cause counts. Report
acquisition reliability, deployment reliability, qualification coverage, censorship
and infrastructure incidents separately. Both-valid bill gains require their own
denominator. No historical qualification relabeling, outcome-driven replacement,
retry, favorable suffix selection or free preprocessing follows from this note.
