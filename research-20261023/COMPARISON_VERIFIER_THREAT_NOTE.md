# Smallest credible local comparison verifier boundary

24 October 2026. Source-only design review of `comparison_endpoint.py`,
`comparison_binding.py`, and `RECOVERY_ANALYSIS_CONTRACT.md`, with targeted source
inspection of the current ACK writer/reader. No runtime,
fixtures, models, saved outcomes or sealed data were read; no execution or
qualification was performed. This note proposes one implementation slice, not
launch authority or another qualification protocol.

## Trust that must exist outside the submitted bundle

The endpoint policy checks conditional claims. The binding adapter checks that
those claims equal a supplied expected manifest. Neither authenticates the
manifest, immutable-reference strings, artifact bytes, clocks, ACK or replay.
An internally consistent fabricated manifest and evidence can therefore pass.
Adding another worker-written hash or `verified=true` field does not close this.

For local research, use an explicitly trusted study custodian, controller and
verifier. The custodian freezes the complete expected manifest **before any new
outcome**, deriving its meaning from the authorized study contract rather than
from result directories. A reviewer other than the result producer checks its
role orientation, complete assignment roster, contrast, clock policy and currency
unit. Store its exact bytes and ordinary SHA-256 digest in a custodian-controlled
location; give the verifier that digest through a trusted local invocation or
configuration, outside the candidate evidence bundle. No signing service is
needed. A digest copied from the bundle being checked is not a trust anchor.

The freeze includes every expected cell and exact byte roots for source plus
transitive runtime dependencies, model/checkpoint, complete original case and
physical target tariff, scoring-input policy and supplied input artifacts,
selector/backbone/K/tie rule, environment/library identity, seed, and clock
allocation. Record absent-model arms explicitly. Version names and paths are
labels, not byte identities. Mechanism roles retain the same learner and physical
target while their declared scoring-input policies may differ; equal numerical
inputs or masks remain legitimate assigned observations.

The trusted launcher runs from a frozen read-only snapshot, resolves executable,
imports, model and case paths there, and records those resolved roots. Workers
cannot replace that snapshot or write the custodian's manifest, controller journal
or verifier output. Avoid hash-then-reopen of mutable paths: retain the verified
objects/snapshot through execution and replay. A post-run hash alone cannot rule
out replacement followed by restoration. A read-only flag under the same hostile
user account is not isolation; a malicious same-user process or administrator is
outside this inexpensive boundary unless separate account/OS write permissions
actually protect the trusted material.

## One producer of normalized evidence

The eventual independent verifier entry point accepts the trusted manifest root
and a controller-owned run directory, checks their relationship, then constructs
`NormalizedEvidence` and calls the existing binding adapter. Do not accept
serialized normalized objects or promote worker assertions to verifier facts.
Keep rejected bytes and reason codes in the same verification report. Decide
integrity/cause before exposing bills to pairwise scoring.

The controller owns a contemporaneous journal: manifest/cell identity, fresh run
identity, launched process and owned descendants, resolved byte roots, monotonic
clock domain and anchor, stage/transport observations, resource/accounting events,
captured artifact bytes/digests, received ACK bytes/time, and termination/cleanup.
It either durably writes captured artifacts itself or relies explicitly on the
reviewed pinned writer for fsync claims; receiving an ACK is not an independent
observation of a worker's fsync syscall. Preserve raw partial messages and channel
errors. The verifier checks all artifact references against these retained bytes,
not filenames in a receipt.

There is a concrete current timing gap: `WorkerStorage.finalize` in
`src/experiments/comparison_native_worker.py` samples `completion_monotonic`
**before** serializing and writing the ACK; `receive_ack` in
`src/experiments/recovery_qualification.py` retains bytes without a receive
timestamp. A scheduling pause can cross 60 seconds after that sample. It proves
neither ACK write completion nor receipt by 60. Separate result, completion and
outcome post-fsync event times also cannot be invented from this one sample.
Do not normalize current records into the policy's complete terminal chain.
Freeze explicit future ACK clock semantics before implementing that chain.
Controller acceptance of a complete, identity-checked ACK by 60 is a sufficient
conservative timely observation, but choosing receipt/acceptance as the endpoint
requires a separately frozen policy clarification/change. Late receipt alone
does not prove late sending under the old semantics; scheduling/transport
uncertainty must not manufacture an algorithmically late competitor.

This proves what an honest pinned runner launched and observed. Command lines,
PID ownership, a model path or a returned score do not alone prove model loading,
inference, start acceptance, solver processing or a causal effect on the plan.
Execution attribution additionally requires the reviewed entry point's actual
load/use chain tied to the frozen model/input roots and captured feature,
transformed-input, score/rank and mask artifacts where claimed. A nonce prevents
accidental cross-run joins; it does not prove computation. An arbitrary malicious
worker can relabel old bytes with a new nonce. Such workers require stronger
isolation/attestation or trusted re-execution, beyond this proposal.

## False acceptance attacks and the evidence that rejects them

| Attack | Required rejecting proof/check |
| --- | --- |
| Edit expected arms/model IDs or omit inconvenient assignments, then make all result identities agree. | Manifest bytes must equal the independently retained pre-outcome root, whose reviewed roster and oriented role declarations are authoritative. Do not discover expected cells from supplied results. A changed root rejects the invocation. |
| Rewrite receipts and their self-hashes; swap source/model/fixture bytes between preflight and launch, then restore them. | Recompute artifact digests against externally frozen roots and verify execution/replay used the same protected snapshot or retained objects throughout. A matching self-hash or final path hash is insufficient; absent continuous custody means unknown. |
| Label an old saved plan as fresh graph inference, or bill it with an easier tariff while naming the assigned target. | Join fresh controller dispatch and capture to the exact assigned source/model/input roots and trusted load/use chain; independently replay selected captured bytes against the frozen full physical target and recompute its exact rational bill. Replay alone proves feasibility/cost of those bytes, not fresh model execution. Missing execution attribution means unknown for that assigned method. |
| Subtract a worker's wall clock or another process/reboot's monotonic value from the controller anchor to appear under 60 seconds. | Check an explicit controller clock domain/epoch and ordered controller observations for anchor, durable result/completion/outcome, post-outcome ACK and cleanup. Compare ACK with that domain's anchor+60. Unproved clock conversion/domain continuity means unknown. Cleanup limits do not extend the endpoint. |
| Forge an ACK JSON, reuse another cell's ACK, or write one before final artifact fsync or after a prewrite timestamp. | Match exact ACK bytes on the owned channel to this run/cell and retained result/completion/outcome digests; establish post-fsync order through controller-owned writes or the trusted pinned writer, plus actual terminal timing under a prospectively frozen clock meaning. A prewrite timestamp cannot prove write completion. Missing phase timing, missing/malformed/partial ACK or channel ambiguity remains unknown. |
| Admit a truncated/infeasible capture, trust a worker bill, or call a fixed-route/restricted lower bound global. | Verify the capture-to-durable-to-selection identity chain; full independent physical replay and exact billing must pass. Global scope additionally needs verified correspondence to the original unrestricted full model and a supported bound justification, not a solver banner. Unsupported full claims/contradictions or invalid admitted witnesses stop with primary unknown; honest absent/restricted bounds can coexist with valid plans. |
| Turn a killed, resource-limited, unowned or partly observed competitor into ordinary no-plan/late, creating a win. | A healthy complete chain must affirm ordinary cause, stage health, ownership and complete charges, with no resource/interface/monitor/capture fault. A late complete healthy ACK can prove lateness; silence or a timeout label cannot. Any such fault/ambiguity dominates an attractive bill and maps to unknown plus the prescribed stop. |
| Drop a missing counterpart, substitute a better seed/retry, swap roles, or renormalize to completed pairs. | Bind every supplied result exactly once to its frozen oriented full identity; reject duplicate, foreign or mismatched records. Iterate the complete manifest, retaining each missing/undispatched cell and known opponent. Its practical pair contribution stays [-1,+1] in the original denominator, never an observed win or zero. |

## Prioritized next slice and limits

Implement a **verification-facts-only** frozen-root reader and journal/artifact
checker first: expected-versus-observed identities, custody/provenance, existing
clock observations and their precise meanings, missing fsync/ACK events, and
unsupported claims. Its output must state which facts are established or missing;
it must not yet emit real normalized endpoints or historical win/loss summaries.
Then freeze the missing prospective clock/writer semantics and implement the
controller observations and independent physical replay needed for normalization.
The eventual successful path requires genuine dispatch, protected execution roots,
a complete healthy terminal chain, hash-bound timely ACK, independently replayed
selected witness and exact bill. Unsupported operational assertions remain
unknown. Treat malformed/foreign evidence as a rejection retaining diagnostics;
do not silently repair it. Keep qualification
coverage, submitted/processed/accepted start, and deployed fallback validity
separate. A rejected raw candidate need not spoil a separately verified fallback;
an invalid admitted candidate is an integrity stop.

Initially accept no worker-claimed global bound without an implemented verifier
for its scope/justification. Leave absent bounds absent, and do not silently erase
a false full claim. Do not add the future failure-only controller certificate in
this slice: current policy intentionally marks it unsupported. Until separately
implemented and qualified, missing ACK is unknown even when cleanup succeeded.
A later certificate would require the full uninterrupted method window, positive
ordinary-deadline causation, affirmative stage health, no preceding/concurrent
fault, drain/closure after all owned writers terminate, and complete owned cleanup
and charges; it would establish failure only, never a plan, bill, bound or warm
qualification.

One frozen declaration, one protected journal and one verification report suffice.
The remaining trust is substantial and explicit: an honest custodian, reviewed
runner/controller/verifier, correct replay and model builders, truthful OS clock
and accounting, and effective local write isolation. Offline review cannot
reconstruct unrecorded timing or prove a malicious worker executed a model.
Agreement between two components sharing a bug is not independent physical
validation. This boundary makes ordinary fabrication and accidental relabeling
rejectable; it does not provide hostile-host security, prove model causality or
repair historical evidence.
