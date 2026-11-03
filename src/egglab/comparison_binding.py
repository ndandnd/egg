"""Pure identity binding for one predeclared oriented comparison contrast.

The manifest is an immutable external declaration, not a discovered cohort.
Evidence must already be normalized and EXTERNALLY VERIFIED. This adapter checks
identity equality and calls the conditional endpoint policy; it verifies no raw
receipts, hashes, replay, ACK bytes, real clocks, runtime, or manifest truth.
False external declarations/attestations can still produce false conclusions.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable

from . import comparison_endpoint as policy
from . import comparison_scoring as scoring


def _text(value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("expected nonempty, unpadded manifest identity")


class Role(str, Enum):
    A = "a"
    C = "c"


@dataclass(frozen=True)
class RoleSpec:
    """Opaque fixed arm/learner/scoring-condition policy declaration for one role.

    Distinct condition policy IDs do not require different numerical inputs;
    zero-exposure/identical-value pairs remain part of the declared cohort.
    """

    arm_id: str
    model_identity: str
    scoring_input_condition_id: str

    def __post_init__(self) -> None:
        for value in (self.arm_id, self.model_identity, self.scoring_input_condition_id):
            _text(value)


@dataclass(frozen=True)
class PairSpec:
    """An oriented pair whose complete expected cells are predeclared.

    Model, scoring input, selector, arm and clock allocation may differ. Opaque
    clock_id values identify allocations, not the common clock policy declared
    by ComparisonManifest. No semantic meaning is inferred from ID spellings.
    """

    contrast_id: str
    assignment: scoring.PairAssignment
    expected_a: policy.CellIdentity
    expected_c: policy.CellIdentity

    def __post_init__(self) -> None:
        _text(self.contrast_id)
        if type(self.assignment) is not scoring.PairAssignment:
            raise ValueError("expected exact PairAssignment")
        if any(type(cell) is not policy.CellIdentity for cell in (self.expected_a, self.expected_c)):
            raise ValueError("expected exact CellIdentity records")
        for cell in (self.expected_a, self.expected_c):
            if (cell.base_id, cell.solver_seed) != (self.assignment.base_id, self.assignment.seed):
                raise ValueError("expected cell differs from assigned base/seed")
        if self.expected_a == self.expected_c:
            raise ValueError("oriented roles require distinct expected cells")
        common = (
            "base_id", "solver_seed", "original_full_case_id",
            "physical_tariff_variant_id", "environment_identity",
            "library_identity", "source_identity",
        )
        if any(getattr(self.expected_a, name) != getattr(self.expected_c, name) for name in common):
            raise ValueError("paired cells differ in a required common identity")


@dataclass(frozen=True)
class ComparisonManifest:
    """Complete primary 24-pair or one-learner mechanism 12-pair declaration.

    AssignmentRoster enforces the fixed sizes, bases and seeds. The external
    manifest author declares which learner/arms a contrast means; this module
    cannot infer learner semantics from model or contrast identity strings.
    A mechanism contrast requires the same frozen model and arm for both roles,
    with distinct scoring-condition policy IDs; primary roles may differ.
    A separate call/manifest is required for every contrast, even when a real
    endpoint legitimately participates in more than one contrast.
    """

    manifest_id: str
    immutable_reference: str
    contrast_id: str
    clock_policy_id: str
    roster: scoring.AssignmentRoster
    role_a: RoleSpec
    role_c: RoleSpec
    pairs: tuple[PairSpec, ...]

    def __post_init__(self) -> None:
        for value in (self.manifest_id, self.immutable_reference, self.contrast_id, self.clock_policy_id):
            _text(value)
        if type(self.roster) is not scoring.AssignmentRoster:
            raise ValueError("expected exact AssignmentRoster")
        if any(type(assignment) is not scoring.PairAssignment for assignment in self.roster.assignments):
            raise ValueError("roster must contain exact PairAssignment records")
        if any(type(role) is not RoleSpec for role in (self.role_a, self.role_c)):
            raise ValueError("expected exact RoleSpec declarations")
        if self.roster.kind is scoring.CohortKind.MECHANISM:
            if (self.role_a.arm_id, self.role_a.model_identity) != (self.role_c.arm_id, self.role_c.model_identity):
                raise ValueError("mechanism contrast must retain one frozen learner and arm")
            if self.role_a.scoring_input_condition_id == self.role_c.scoring_input_condition_id:
                raise ValueError("mechanism contrast requires distinct declared scoring-condition policies")
        if type(self.pairs) is not tuple or any(type(pair) is not PairSpec for pair in self.pairs):
            raise ValueError("expected immutable tuple of exact PairSpec records")
        if any(pair.contrast_id != self.contrast_id for pair in self.pairs):
            raise ValueError("manifest must contain exactly one contrast")
        assignments = tuple(pair.assignment for pair in self.pairs)
        if len(set(assignments)) != len(assignments):
            raise ValueError("duplicate manifest pair assignment")
        if set(assignments) != set(self.roster.assignments):
            raise ValueError("manifest must declare every fixed roster assignment exactly once")
        cells = tuple(cell for pair in self.pairs for cell in (pair.expected_a, pair.expected_c))
        if len(set(cells)) != len(cells):
            raise ValueError("duplicate expected cell")
        if len({cell.assignment_id for cell in cells}) != len(cells):
            raise ValueError("assignment_id must uniquely identify each expected cell")
        for pair in self.pairs:
            for cell, role in ((pair.expected_a, self.role_a), (pair.expected_c, self.role_c)):
                if (cell.arm_id, cell.model_identity, cell.scoring_input_condition_id) != (
                    role.arm_id, role.model_identity, role.scoring_input_condition_id
                ):
                    raise ValueError("expected cell differs from fixed manifest role declaration")


@dataclass(frozen=True)
class CellResult:
    """Verifier-supplied evidence explicitly labelled with contrast and role."""

    contrast_id: str
    assignment: scoring.PairAssignment
    role: Role
    evidence: policy.NormalizedEvidence

    def __post_init__(self) -> None:
        _text(self.contrast_id)
        if type(self.assignment) is not scoring.PairAssignment or type(self.role) is not Role:
            raise ValueError("expected exact PairAssignment and Role")
        if type(self.evidence) is not policy.NormalizedEvidence:
            raise ValueError("expected NormalizedEvidence, never raw receipt dictionaries")


@dataclass(frozen=True)
class BoundCell:
    """Retain full binding and policy provenance, including faults and stops.

    Missing evidence has assessment=None and an UNKNOWN scoring endpoint.
    Explicit undispatched evidence retains its assessment and separate count.
    """

    role: Role
    expected_identity: policy.CellIdentity
    evidence: policy.NormalizedEvidence | None
    assessment: policy.EndpointAssessment | None
    endpoint: scoring.Endpoint


@dataclass(frozen=True)
class BoundPair:
    spec: PairSpec
    arm_a: BoundCell
    arm_c: BoundCell
    observation: scoring.PairObservation


@dataclass(frozen=True)
class BoundComparison:
    manifest: ComparisonManifest
    pairs: tuple[BoundPair, ...]
    summary: scoring.CohortSummary

    @property
    def stop_scopes(self) -> tuple[policy.StopScope, ...]:
        """All non-NONE scopes, in cell order; cell assessments retain reasons."""
        return tuple(cell.assessment.stop_scope for pair in self.pairs
                     for cell in (pair.arm_a, pair.arm_c)
                     if cell.assessment is not None and cell.assessment.stop_scope is not policy.StopScope.NONE)


def _bind_cell(role: Role, expected: policy.CellIdentity,
               evidence: policy.NormalizedEvidence | None,
               currency_unit: Fraction) -> BoundCell:
    if evidence is None:
        return BoundCell(role, expected, None, None,
                         scoring.Endpoint(scoring.EndpointKind.UNKNOWN, currency_unit=currency_unit))
    assessment = policy.classify_endpoint(evidence)
    if assessment.kind is policy.EndpointKind.DEPLOYABLE_VALID:
        endpoint = scoring.Endpoint(scoring.EndpointKind.VALID, assessment.exact_bill, currency_unit)
    elif assessment.kind in (policy.EndpointKind.ALGORITHMIC_NO_PLAN, policy.EndpointKind.ALGORITHMIC_LATE):
        endpoint = scoring.Endpoint(scoring.EndpointKind.ALGORITHMIC_FAILURE, currency_unit=currency_unit)
    else:
        kind = (scoring.EndpointKind.UNDISPATCHED if assessment.kind is policy.EndpointKind.UNDISPATCHED
                else scoring.EndpointKind.UNKNOWN)
        endpoint = scoring.Endpoint(kind, currency_unit=currency_unit)
    return BoundCell(role, expected, evidence, assessment, endpoint)


def bind_comparison(manifest: ComparisonManifest,
                    results: Iterable[CellResult] = ()) -> BoundComparison:
    """Validate every oriented full identity, classify, then score fixed pairs.

    Duplicate, unlisted, wrong-contrast or identity-mismatched results reject the
    entire call. No endpoint is selected by bill or arrival order. Every manifest
    pair remains, and each missing cell becomes UNKNOWN independently, preserving
    a known opponent and the original denominator. All supplied evidence and
    classifier diagnostics remain in the returned immutable binding records.
    """
    if type(manifest) is not ComparisonManifest:
        raise ValueError("expected exact ComparisonManifest")
    specs = {pair.assignment: pair for pair in manifest.pairs}
    observed: dict[tuple[scoring.PairAssignment, Role], policy.NormalizedEvidence] = {}
    for item in results:
        if type(item) is not CellResult:
            raise ValueError("expected CellResult records, never raw receipt dictionaries")
        if item.contrast_id != manifest.contrast_id:
            raise ValueError("result belongs to a different contrast")
        if item.assignment not in specs:
            raise ValueError("result is outside the fixed manifest roster")
        slot = (item.assignment, item.role)
        if slot in observed:
            raise ValueError("duplicate result for an oriented cell")
        spec = specs[item.assignment]
        expected = spec.expected_a if item.role is Role.A else spec.expected_c
        if item.evidence.identity != expected:
            raise ValueError("result full identity differs from its oriented expected cell")
        observed[slot] = item.evidence
    bound = []
    for assignment in manifest.roster.assignments:
        spec = specs[assignment]
        a = _bind_cell(Role.A, spec.expected_a, observed.get((assignment, Role.A)), manifest.roster.currency_unit)
        c = _bind_cell(Role.C, spec.expected_c, observed.get((assignment, Role.C)), manifest.roster.currency_unit)
        observation = scoring.PairObservation(assignment, a.endpoint, c.endpoint)
        bound.append(BoundPair(spec, a, c, observation))
    pairs = tuple(bound)
    summary = scoring.summarize_comparison(manifest.roster, (pair.observation for pair in pairs))
    return BoundComparison(manifest, pairs, summary)
