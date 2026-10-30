# Prospective endpoint policy primitive

24 October 2026. Source and hand-built test authoring only. Neither the module nor
the tests were imported or executed. No raw receipts, research data, model assets,
solver, cluster, native worker or historical qualification result was accessed by
this implementation. This implements a narrow part of
`RECOVERY_ANALYSIS_CONTRACT.md`, including the endpoint note's failure-only-path
refinement; it is neither a launch manifest nor a passed qualification.

`src/egglab/comparison_endpoint.py` exposes `classify_endpoint(NormalizedEvidence)`
and returns an immutable `EndpointAssessment`. Its version is
`comparison.endpoint.normalized.v1`; the exact input tag is
`externally_verified_normalized_evidence`. Nested immutable dataclasses require
exact enums, booleans and typed identities, unique artifact IDs/references, linked
provenance/capture/durable IDs, distinct candidate/witness IDs, exact `Fraction`
bills, and finite ordered terminal clocks. Unknown constructor fields are rejected
by dataclass constructors; malformed fields are rejected with `ValueError`.
Raw receipt dictionaries are deliberately rejected rather than normalized here.

This is a policy assessment **conditional on external verification**. Artifact
references and source/model/environment/library identities are opaque: this code
does not read or hash their bytes. It does not replay plans, verify an exact bill,
establish original-full-bound provenance, inspect ACK bytes, prove clock/ownership/
monitor/accounting health, or qualify mechanism coverage. An external source-bound
verifier must establish those facts before constructing an input. A caller who
falsely supplies healthy/verified fields can obtain a false valid result or false
qualification pass. The test deliberately illustrating unverifiable fixed-charging
attestation documents this limitation; it is not evidence of verified coverage.

Qualification is computed only from required versus externally verified coverage
components. Acquisition, executed mode, start submission/processing/acceptance,
deployment intent, bound scope, evidence integrity and dispatch remain separate.
Claimed binary-start coverage requires actual recorded submission; processing
coverage requires observed processing; acquired-fallback coverage requires admitted
acquisition and an independently verified durable candidate of acquisition origin.
These structural consistency checks do not prove the underlying recorded facts.
`NOT_STARTED` cannot coexist with candidates, acquisition/start activity, a
deployment claim, a healthy complete terminal chain or deployment-stage clocks.
A dispatched allocation that never began method execution can still retain
cleanup evidence and classify as unknown; undispatched assignments remain missing.
Failed charging/warm coverage alone does not prevent a valid cold fallback. A
processed but rejected start can retain a valid fallback. Raw candidate rejection
cannot be selected or used as a start source and does not become invalid admitted
evidence. Any invalid admitted candidate or invalid original-full-bound claim
stops primary use even alongside a favorable selected witness. Integrity, resource,
interface and accounting faults supersede a favorable bill; all supplied causes
and additional structural faults remain in reason codes.
An undispatched suffix retains an engineering stop when a positive engineering
fault caused the stop, including when a budget-stop cause also appears. Ambiguous
cause alone remains integrity unknown; it is not relabeled a demonstrated fault.
Both cases preserve undispatched primary missingness and all supplied causes.
Noncontradictory=false with no bound or only a restricted diagnostic yields unknown,
not an invalid global claim: no original-full claim was made on those axes.

Timely deployment requires an externally attested complete healthy terminal chain,
separate ordered result/completion/outcome/ACK/cleanup times, uncensored outputs
and a complete post-outcome ACK at or before anchor+60. Healthy complete late ACKs
support algorithmic lateness. Pre-60 deployment lateness additionally requires
provenance-linked positive deployment-stage cutoff-overrun clocks, an explicit
ordinary-lateness cause and output censorship. A lateness cause with a timely,
uncensored selected witness is contradictory/unknown rather than a fabricated
loss. Acquisition deadlines are not deployment-overrun evidence. Explicit no-plan
needs the same healthy complete chain. Censorship alone, missing/malformed ACK, administrative interruption and
ambiguous/incomplete evidence remain unknown. Cleanup timing never extends 60.
The future failure-only controller certificate is **unsupported**: its explicit
enum always produces unknown and no primary eligibility, even when paired with
other favorable attestations. No boolean can enable that path. No controller
certificate verifier or qualifying lifecycle is implemented.

Assessment fields contain semantic endpoint/qualification/axis labels, stop scope,
primary eligibility, reasons, evidence IDs and the exact selected bill/witness
only for a valid deployment. Inputs retain rejected, invalid and late diagnostics.
`DEPLOYABLE_VALID`, `ALGORITHMIC_NO_PLAN` and `ALGORITHMIC_LATE` are the only
primary-eligible kinds. Scoring uses its own symbolic endpoint kind; no implicit
adapter or runtime integration is provided here. Any future bridge must explicitly
map these kinds and keep every other endpoint unknown.

`src/tests/test_comparison_endpoint.py` has 17 compact hand-built test functions
covering these precedence, cutoff, unsupported-certificate and strict-schema
rules. These tests are authored examples awaiting separately authorized execution
and source-bound qualification; they establish no current qualification pass.
Existing native qualification gates and failed historical classifications remain
unchanged. No dispatch, retry, data access or budget expansion is authorized.
