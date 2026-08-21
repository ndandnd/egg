# 05 — The bounded integrity claim

## Why this document exists

Five independent review rounds on the B3 closeout each found a real
false-acceptance path. The evidence-consumption and provenance defects that
required **no attacker** are closed. Every path still open requires a **local
same-UID caller**: a process running as the same OS user, able to write the
repository, the run tree, the analysis outputs and the process environment.

Portable user-space Python cannot defend against that. Such a process can
rewrite files, repository metadata, executable dispatch, configuration and
environment during verification -- and, more simply, could edit the published
artifact directly. Continuing to harden against it does not terminate, and each
round costs hours while the flagship decision stays unfrozen.

The reviewer who found most of these paths agreed the boundary is legitimate,
with one condition: it is honest **only** as an explicitly disclosed scope, and
only once the non-same-UID defects are actually closed.

## The wording to put in the specification

Supplied verbatim by the external reviewer. Use it in
`doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`, in the analyzer module docstring, and as a
field in `SELECTION.json`:

> **Integrity-certificate scope.** The pipeline binds the enumerated input
> files, serialized solver evidence, and reviewed repository commits, and is
> designed to detect accidental corruption and post-hoc modification by a party
> without write access to the repository, run tree, analysis outputs, or process
> environment. It is not a cryptographic attestation and does not defend against
> a malicious or concurrent process operating as the same OS user, which can
> modify repository metadata, files, executable dispatch, configuration, or
> environment during verification. The certificate is therefore conditional on a
> clean, quiescent, cooperatively administered local namespace. It replays
> serialized evidence but does not independently re-solve the underlying
> optimization problems.

Avoid "tamper-proof", "secure against local modification", or similar.

## What the certificate does attest

- The scored bytes are the bytes named in `raw_binding`: every consumed file is
  digest-checked in the same read that parses it, against a frozen inventory.
- The population is the frozen one: 60 cells, exact identities, screen SHA
  `27c04d82...`, run manifest, solver identity, budget ceiling.
- The raw tree matches an **outcome-blind** pre-analysis anchor
  (`efc5ca31...`, 363 files) captured before anyone knew the result.
- The decision follows the preregistered rule exactly -- verified by executable
  equivalence against an independent re-derivation, with the thresholds,
  ordering and comparison operators unchanged from the pre-repair baseline.
- Provenance commits resolve through a hardened, repository-pinned,
  allowlisted-environment, replacement-free git runner.
- Certificates are **replayed from chronological solver evidence, not
  re-solved**. This is the load-bearing limitation and must be stated wherever
  the certificate is claimed.

## The one empirical answer to the replay limitation

A replication of the same 60 cells, compared under the contract frozen in PR
#48 *before* any replica existed. 60/60 agreement makes the
replay-versus-re-solve gap empirically implausible; any disagreement is an
incident. That is stronger than any further code hardening can be, because it
tests the pipeline rather than the reader of the pipeline.

## Residual, disclosed

- A local same-UID caller can defeat worker identity, provenance resolution and
  file authentication. Disclosed in code docstrings and here.
- A linked-worktree gitfile swap after the provenance precheck (same-UID only).
- Programmer errors inside the audit are caught broadly and surface as
  `INVALID/HALT` rather than propagating. This fails closed, which is right for
  scientific safety, but it can mislabel a code defect as invalid evidence.
- `analyze_b2_pilot.py`, `analyze_a6_holdout.py`, `package_a6_holdout.py` and
  `local_a6_preflight.py` still shell a bare `git`. Out of scope for the B3
  closeout; a repo-wide follow-up. **Note before running the A6 recovery.**
