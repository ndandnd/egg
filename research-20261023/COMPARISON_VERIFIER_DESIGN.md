# Independent verification before a timed comparison

24 October 2026. Source-only design; no implementation, real-output admission,
native qualification or launch authorization. This is the next boundary after
`comparison_endpoint.py` and `comparison_binding.py`, not another replacement
analysis framework. The existing analysis contract still controls outcomes,
clocks, fixed denominators and stop rules.
This integrated design takes precedence over the companion notes' sequencing
suggestions: byte-root loading and physical facts first, controller normalization
only after the missing timing semantics and observations are implemented.

## What is missing

The checked endpoint and binding modules establish conditional statements:
**if** the expected manifest is correct and the normalized evidence is independently
verified, the identities and endpoint scores are handled consistently. Their tags,
hash strings and `externally_verified_*` fields do not establish either premise.
Do not wrap a worker dictionary in these dataclasses to bridge the gap.

The smallest useful next implementation is a read-only **artifact and replay fact
checker**, followed by a separate controller-evidence adapter. The first slice
must not produce `NormalizedEvidence`, a deployable endpoint, a global bound or
permission to dispatch. Implementing a complete normalizer now would conceal
runtime facts that current receipts do not record.

## Authority and bytes

Use three explicit roles within the local research process:

1. The study coordinator freezes the complete expected assignments and byte identities
   before the first dispatch or new outcome. A reviewed, pinned Git object or a digest retained outside
   worker output supplies the expected root. Record the root in the controller's
   launch record. A manifest and a matching digest found together inside worker
   output are not an independent root. A Git hash identifies contents; it does
   not alone prove when they were frozen.
2. The controller launches the frozen worker, records the clock anchor, assigned
   cell, process ownership, ACK transport observations and resource/terminal
   observations. Workers must not supply the expected assignments or overwrite
   the controller journal.
3. The read-only verifier checks those expected roots and recomputes the physical
   facts from the admitted artifact bytes. It preserves unsupported claims as
   unsupported, rather than promoting a worker's status or stored replay flag.

This is a reproducibility boundary for trusted, reviewed local code and accidental
misbinding, corruption and incomplete evidence. It is not secure attestation
against a malicious researcher, operating system or controller. No signing service
or remote-attestation system is needed for this study. Preserve this limit when
describing verification as independent.
Under this stated trust model, a reviewed loader using a protected frozen library
and model snapshot can establish the required execution attribution. Inspection
of mapped machine-code pages is not a new prerequisite. Do not describe a path
hash alone as stronger proof than that trusted loading chain supplies.

For each authorized input, read a bounded immutable byte snapshot, check its
digest against the external root, and parse/use that same snapshot. Do not hash
one path read and later consume different bytes from that path. Reject ambiguous
JSON (duplicate keys or nonfinite constants), unsupported schemas, unlisted
artifacts and path escapes/symlinks. Record parsing and schema failures without
consulting paired bills. Compression, if supported later, needs a prospective
uncompressed-size limit and a declared digest domain. No general archive loader
is needed in the first slice.

The root binds the complete full-case physics, target tariff, scoring-input
condition, arm/model/selector, seed, source closure, interpreter/native library,
task and clock policy. Source or model hashes prove which bytes were registered;
they do not prove those bytes were executed or supplied to inference. Future
controller/worker instrumentation must separately bind observed loading and
scoring inputs to the frozen source and assignment. Retain the full expected
`CellIdentity` checks already implemented by `comparison_binding.py`.

## Required facts and current reuse

| Fact | Reuse and limit | Evidence still needed |
| --- | --- | --- |
| Expected manifest and artifacts | Current preflight `verify_lock`/`verify_artifacts` check inventories and file consistency. They cannot choose their own trusted root. | Caller-pinned root, expected assignments and stable consumed bytes. |
| Selected physical witness and bill | `native_recharge.replay_native` independently sweeps physical events; `recovery_lift.lift_plan` replays the submitted plan before lifting, then replays the full-case witness. | Recompute from the selected plan and full-case/target bytes; bind the selected candidate to the deployed artifact and admission chain. No route repair or new charging solve during audit. |
| Exact bill arithmetic | `native_hull.supply` rationalizes stored finite numbers; the existing lift constructs a rational bill. | Preserve those exact reconstructed values and tariff identity. Physical replay remains floating-point and tolerance-conditional, not an exact mathematical feasibility certificate. |
| Actual method execution | Frozen source inventories, capture envelopes and submitted-start log attribution are useful checks. | Trace the actual loading/scoring/selection/start events under the frozen source; a saved model name or matching hash is insufficient. A valid bill alone says nothing about which model produced it. |
| Terminal deployment and timing | Current preflight binds result/completion/outcome hashes to an ACK and checks worker timestamps. | Controller-bound transport and phase evidence under an explicit endpoint definition; see the timing gap below. |
| Ownership and resources | Qualification controller already records owned groups, cleanup, monitor failures and conservative charges. | Preserve independent controller observations, termination/reaping and all spend. Do not turn worker resource flags or sampled peaks into stronger hard-limit proofs. |
| Full bound | Existing native provenance and inventories help audit scope. A physically valid plan establishes an upper bound only. | Independently establish original unrestricted model/scope and admissible native bound evidence. Restricted/fixed-route bounds never become global through relabeling. Unsupported claims remain unsupported. |

Detailed helper locations and limitations are in `COMPARISON_VERIFIER_REUSE_NOTE.md`;
failure examples are in `COMPARISON_VERIFIER_THREAT_NOTE.md`. Importing the old
preflight analyzer wholesale would also import qualification-specific requirements
and native-runtime/global-patching dependencies. Reuse the pure checks directly
or extract them once, rather than copying its result flags.

## Timing gap to resolve before controller normalization

`comparison_native_worker.WorkerStorage.finalize` samples
`completion_monotonic` **before** writing the ACK to the pipe. A scheduling delay
between that sample and `os.write` can cross the 60-second endpoint. The current
controller's `receive_ack` stores the payload without a controller receive time.
Matching that payload and its artifact hashes therefore does not by itself prove
that the ACK write completed by the cutoff. Existing receipts also lack separate
persisted post-fsync phase observations for all the terminal fields requested by
`TerminalEvidence`.

Freeze an explicit transport-time rule before a new comparison controller is
implemented. A controller-stamped complete ACK received and accepted by 60 seconds
can give a conservative sufficient observation; choosing receiver acceptance as
the endpoint would be a prospective policy change, including its polling cost.
A late receive alone does not prove a late send under the old rule. Do not fill
missing phase times with the ACK timestamp or reinterpret historical receipts.
The 61/62.5-second supervision/cleanup allowances never extend deployment time.

Keep the unsupported ACK-less failure certificate out of the first implementation.
Silence, a deadline label or a cleaned-up process group does not prove ordinary
algorithmic failure. Missing transport/clock/health evidence stays unknown.

## First implementation slice and acceptance

Expose only fact reports: a fact is `verified`, `contradicted` or `unestablished`,
with the expected root, consumed-byte digests, assignment, checker version and
specific evidence/reason references. No whole-cell success flag. Missing timing
must remain unestablished even when the selected physical plan replays.

The first source change should implement externally pinned root/artifact loading
and physical-witness/bill recomputation, without a native solver, model inference
or controller launch. Use small handcrafted source-test artifacts only under one
prospective affected-source check package. Check at least wrong root, edited bytes,
ambiguous JSON, wrong case/tariff, changed selected artifact, a physically invalid
plan with a forged replay flag, an incorrect bill, and a replay-valid witness with
absent terminal evidence. The last case verifies only the physical fact; it cannot
enter a deployable comparison or establish that a trained model ran.

After reviewing that bounded slice, design the genuinely separate comparison
controller/normalizer against the identified missing runtime observations. Existing
qualification gates stay unchanged. No repeated native qualification or broad
historical matrix is justified by this design alone.

Independent post-run audit may confirm only what the timely deployed immutable
artifact already contained; it cannot repair or improve that output after the
clock. Online admission/replay/finalization remain inside the common method clock;
post-run audit compute is recorded separately in the campaign accounting. A failed
audit preserves the assigned cell, diagnostics and fixed-denominator missing mass.

No asset, solver, model or real-output conversion was run for this design. The
native ceiling remains 1800 seconds with dispatch stop 1620 and shutdown reserve
180; the previously requested increase to 1920 has no reply. The authoritative
spent carry remains `comparison-binding-checks/accounting.json`:
1509.9511370494984 seconds. There is no new launch manifest or test receipt here.
