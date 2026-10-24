# Conditional identity binding adapter

`src/egglab/comparison_binding.py` bridges the existing normalized endpoint policy
to the exact fixed-roster scorer. This is pure source work: no receipts, assets,
cohort generation, solver, native execution, imports, or tests were executed by
the implementation agent. An independent source review and separately authorized
frozen source gate remain the parent's responsibility.

The API is `ComparisonManifest` → `bind_comparison(manifest, CellResult iterable)`
→ `BoundComparison`. A frozen manifest declares its immutable reference, one
contrast, common clock-policy label, complete `AssignmentRoster`, fixed A/C
`RoleSpec` declarations, and every oriented `PairSpec` with exact expected
`CellIdentity` values. The roster requires exactly 24 primary pairs or 12
mechanism pairs for one learner. Nothing generates the prospective 192 decisions.

Pair compatibility requires the same base, solver seed, physical target tariff,
original full case, source, environment and library. Model/scoring/arm declarations
can differ between A/C; selectors and clock allocation IDs can differ per cell.
Clock-policy identity is a manifest declaration; clock instances are checked
against each expected cell, never equated between runs. Role arm/model/condition
IDs are fixed across the roster; these opaque declarations prevent accidental
cross-base learner or condition mixing without interpreting identity spellings.
Cell assignment IDs are globally unique within one manifest.
Roster entries require exact `PairAssignment` types, including when a subclass
supplies compatible equality/hash behavior accepted by the inherited scorer.
Mechanism contrasts retain one frozen learner and arm and require distinct
declared scoring-condition policy IDs. These IDs need not imply different
numerical price vectors: zero-exposure and identical-value pairs remain assigned.

Each result must declare the same contrast, assigned pair and role and carry an
exact `NormalizedEvidence` record. Full identity equality checks every field,
including assignment, tariff, learner/model, condition, clock and selector.
Wrong-role, wrong-contrast, duplicate and unlisted results reject the entire call.
A legitimately shared graph endpoint can participate in separate contrast calls;
results from different contrasts cannot be mixed in one call.

The adapter calls `classify_endpoint` itself. Only `DEPLOYABLE_VALID` becomes an
exact valid-bill endpoint; healthy algorithmic no-plan/late becomes algorithmic
failure; explicit undispatched retains that label; every other outcome is unknown.
It never reads a favorable raw bill to bypass classifier faults. Every assigned
pair remains in the denominator, and missing cells become unknown separately so
a known opposing endpoint survives. The returned manifest, pair specs, complete
evidence and assessments preserve provenance, reasons, bound scopes and stop
scopes; `stop_scopes` exposes all non-NONE occurrences without choosing precedence.
The summary confers no dispatch or scientific authority.

Both trust boundaries remain conditional. An external authority must honestly
predeclare the expected manifest and independently verify the normalized evidence.
This module does not authenticate either assertion, verify hashes/replays/ACK
bytes/real clocks/runtime, qualify a controller, or convert worker dictionaries
into trusted attestations. A dishonest expected manifest or false normalized
attestation can still produce a false result. Opaque clock/learner/policy labels
do not independently establish the physical or scientific claims they name.

`src/tests/test_comparison_binding.py` contains self-contained handwritten metadata
examples only: every identity mutation, role/learner/condition mixing, incompatible
pairs, fixed missing denominators, separate unknown/undispatched counts, retained
opponents and diagnostics, exact bills, healthy failures, strict result types,
and explicit endpoint reuse across separate contrast manifests. No earlier test
module or real asset is imported by that test file.
