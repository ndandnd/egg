# Exact-law retained-proof adapter: source handoff

Source only; no evidence has been decoded, assembled or checked in this task.
The parent must review and separately freeze sources, inputs and command.

`bundle.build(repo_root,out_dir,source_revision,source_buffers=None)` requires a
full lowercase40hex revision and a fresh output directory. Optional cached
buffers have the sole key `verify.py`. Its return is
`BUILT_LOCAL_REVIEW_ONLY`, `manifest_sha256`, `manifest`, `native_calls=0`,
`verification_performed=False`, and unresolved redistribution status.

All ten fixed source/input bindings are in `bundle.PINS`; there is no separate
SOURCE_PINS constant. The fourth source is frozen target `checker.py`, used
only for assembly's `graft_proposals`. Exported mathematical closure is exactly
three stdlib modules: target semantics6665c2b9, physical3278d50f, tree6a171357.
The six evidence inputs are the TARGET and two NEW top-level candidate packets
at d27f9f13, original303-node tree at ef0e0820, refinement at d8e22ffd, and
fixed COMPARISON at fdb85682. Full revisions and paths are source constants.
The assembler also pins this new `verify.py` to its supplied source revision.

The ten exported members are three checkers, `evidence/case.json`,
`physical.json`, `response.json`, `tree.json.gz`, `claims.json`, `verify.py`, and
`README.md`. Candidate projections retain every selected movement and every
exact allocation, including zeros; diagnostic integer-key dictionaries and
optional native SOC/load claims are deliberately omitted. Original nonenergy
JSON integers/floats retain their types; energy/proof fractions remain strings.
The tree is grafted once into375 nodes. Historical scalar bounds are used only
by the frozen helper to choose a proposed certificate, then completely stripped.

`verify.verify_bundle(directory,expected_manifest_sha256,limits=None)` returns
PASS or FAIL_OR_UNRESOLVED. It freshly reconstructs the target rows/minimum
fleet, strictly replays both complete target witnesses, recomputes their fixed
mixture, and checks the complete375-node target tree plus fresh typed3+ floor.
It never trusts a serialized ledger, native status or historical lower bound.
Only the declared exact-additive descriptor is qualified; source transformation,
canonical access premises and empirical road realization are not re-audited.

`DEFAULT_LIMITS`:500wall seconds,450checker seconds,2GiB observed RSS,
375nodes/depth,512MiB compressed/per-decompressed-member,1GiB total bytes.
The immutable tree checker separately caps100million rational operations and
32768-bit fractions. Outer owner/child limits remain authoritative.

`literal_qualification()` defines three adapter anchors and12 named negative
controls, returns status PASS/native_calls0, and performs no physical replay or
tree algebra qualification. It is intended to be called once in future paidQ0.

Standalone command, run exactly once in the prospective owner:

`python -I -S -B verify.py --manifest-sha256 TRUSTED_DIGEST --output verification.json`

The trusted manifest digest must come from the separately admitted builder
receipt. It binds the complete source/evidence closure; an untrusted manifest's
self-computed digest is insufficient. Exported verification requires no Git,
native solver or third-party package. Assembly uses fixed Git byte comparisons.
No external reproduction or public redistribution/license permission is claimed.
