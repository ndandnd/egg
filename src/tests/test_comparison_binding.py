"""Handwritten symbolic metadata only; no receipts, data, models or solvers."""

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction

import pytest

from egglab import comparison_endpoint as policy
from egglab import comparison_scoring as scoring
from egglab.comparison_binding import (
    CellResult, ComparisonManifest, PairSpec, Role, RoleSpec, bind_comparison,
)


def _manifest(kind=scoring.CohortKind.MECHANISM):
    bases = (("small-one", 40), ("small-two", 40),
             ("large-one", 80), ("large-two", 80))
    if kind is scoring.CohortKind.PRIMARY:
        bases += (("small-three", 40), ("small-four", 40),
                  ("large-three", 80), ("large-four", 80))
    roster = scoring.AssignmentRoster(kind, tuple(
        scoring.PairAssignment(base, size, seed)
        for base, size in bases for seed in (17, 41, 73)
    ), Fraction(1, 100))
    a = RoleSpec("graph", "graph-learner", "fresh")
    c = RoleSpec("graph", "graph-learner", "stale")
    pairs = []
    for assignment in roster.assignments:
        cells = tuple(policy.CellIdentity(
            f"{assignment.base_id}-{assignment.seed}-{role.value}",
            assignment.base_id, "target-" + assignment.base_id,
            declaration.scoring_input_condition_id, declaration.arm_id,
            assignment.seed, f"clock-{assignment.base_id}-{assignment.seed}-{role.value}",
            "source-version", declaration.model_identity, "environment-version",
            "library-version", "full-" + assignment.base_id,
            f"selector-{assignment.base_id}-{role.value}",
        ) for role, declaration in ((Role.A, a), (Role.C, c)))
        pairs.append(PairSpec("fresh-versus-stale-graph", assignment, *cells))
    return ComparisonManifest("manifest-one", "immutable:manifest-one",
                              "fresh-versus-stale-graph", "sixty-second-clock-policy",
                              roster, a, c, tuple(pairs))


def _evidence(identity, bill=Fraction(10)):
    refs = ("external-proof",)
    return policy.NormalizedEvidence(
        identity=identity,
        artifacts=(policy.ArtifactReference("external-proof", "immutable:handwritten-example"),),
        provenance_ids=refs,
        dispatch_state=policy.DispatchState.DISPATCHED,
        integrity=policy.Integrity.HEALTHY,
        qualification=policy.QualificationEvidence((), (), refs),
        acquisition=policy.Acquisition.NOT_ATTEMPTED,
        executed_mode=policy.ExecutedMode.COLD_FULL,
        deployment=policy.Deployment.SELECTED_WITNESS,
        start=policy.StartEvidence(False, policy.Processing.UNOBSERVED,
                                   policy.StartAcceptance.NOT_SUBMITTED, None, refs),
        bound=policy.BoundEvidence(policy.BoundScope.NONE, True, refs),
        terminal=policy.TerminalEvidence(
            True, policy.AckState.COMPLETE, policy.TerminalCause.ORDINARY_METHOD,
            100, 155, 156, 157, 160, 162, False, False, False, refs,
        ),
        candidates=(policy.CandidateEvidence(
            "candidate", "witness", policy.CandidateState.ADMITTED_VERIFIED,
            "external-proof", "external-proof", bill, refs,
        ),),
        selected_candidate_id="candidate", causes=(),
    )


def _result(manifest, role, evidence=None, index=0):
    pair = manifest.pairs[index]
    cell = pair.expected_a if role is Role.A else pair.expected_c
    return CellResult(manifest.contrast_id, pair.assignment, role,
                      _evidence(cell) if evidence is None else evidence)


@pytest.mark.parametrize("kind,count", [(scoring.CohortKind.PRIMARY, 24),
                                         (scoring.CohortKind.MECHANISM, 12)])
def test_full_manifest_retains_fixed_denominator_with_no_evidence(kind, count):
    result = bind_comparison(_manifest(kind))
    assert len(result.pairs) == count
    summary = result.summary.overall
    assert summary.score.assigned_count == count
    assert summary.score.unknown_pairs == count
    assert summary.score.missing_mass == 1
    assert summary.score.bounds == scoring.ExactBounds(Fraction(-1), Fraction(1))
    assert summary.arm_a_validity.unknown == count
    assert summary.arm_c_validity.unknown == count


def test_partial_pair_keeps_known_opponent_and_exact_bill():
    manifest = _manifest()
    evidence = _evidence(manifest.pairs[0].expected_c, Fraction(123, 7))
    result = bind_comparison(manifest, (_result(manifest, Role.C, evidence),))
    pair = result.pairs[0]
    assert pair.arm_a.evidence is None and pair.arm_a.assessment is None
    assert pair.arm_a.endpoint.kind is scoring.EndpointKind.UNKNOWN
    assert pair.arm_c.endpoint.bill == Fraction(123, 7)
    assert pair.arm_c.endpoint.currency_unit == Fraction(1, 100)
    assert pair.arm_c.evidence is evidence
    assert result.summary.overall.arm_c_validity.valid == 1
    assert result.summary.overall.arm_a_validity.valid == 0
    assert result.summary.overall.validity_difference.upper == Fraction(11, 12)
    assert result.summary.overall.score.unknown_pairs == 12


@pytest.mark.parametrize("field,value", [
    ("assignment_id", "other-assignment"), ("base_id", "other-base"),
    ("physical_tariff_variant_id", "wrong-tariff"),
    ("scoring_input_condition_id", "wrong-condition"), ("arm_id", "wrong-arm"),
    ("solver_seed", 41), ("clock_id", "wrong-clock-allocation"),
    ("source_identity", "wrong-source"), ("model_identity", "wrong-learner"),
    ("environment_identity", "wrong-environment"), ("library_identity", "wrong-library"),
    ("original_full_case_id", "wrong-full-case"), ("selector_id", "wrong-selector"),
])
def test_every_identity_component_is_checked_even_with_same_pair_key(field, value):
    manifest = _manifest()
    evidence = _evidence(replace(manifest.pairs[0].expected_a, **{field: value}))
    with pytest.raises(ValueError, match="full identity"):
        bind_comparison(manifest, (_result(manifest, Role.A, evidence),))


def test_swapped_role_and_mixed_contrast_reject_even_for_compatible_cells():
    manifest = _manifest()
    a = _result(manifest, Role.A)
    c = _result(manifest, Role.C)
    with pytest.raises(ValueError, match="full identity"):
        bind_comparison(manifest, (replace(a, evidence=c.evidence), replace(c, evidence=a.evidence)))
    with pytest.raises(ValueError, match="different contrast"):
        bind_comparison(manifest, (a, replace(c, contrast_id="graph-versus-catboost")))


def test_duplicate_unlisted_and_raw_results_reject():
    manifest = _manifest()
    a = _result(manifest, Role.A)
    with pytest.raises(ValueError, match="duplicate result"):
        bind_comparison(manifest, (a, a))
    outside = scoring.PairAssignment("outside", 40, 17)
    with pytest.raises(ValueError, match="outside"):
        bind_comparison(manifest, (replace(a, assignment=outside),))
    with pytest.raises(ValueError, match="CellResult"):
        bind_comparison(manifest, ({"bill": 1},))
    with pytest.raises(ValueError, match="NormalizedEvidence"):
        replace(a, evidence={"externally_verified": True})


@pytest.mark.parametrize("field,value", [
    ("base_id", "other-base"), ("solver_seed", 41),
    ("physical_tariff_variant_id", "other-target"),
    ("source_identity", "other-source"), ("environment_identity", "other-environment"),
    ("library_identity", "other-library"), ("original_full_case_id", "other-full-case"),
])
def test_pair_spec_rejects_incompatible_common_fields(field, value):
    pair = _manifest().pairs[0]
    with pytest.raises(ValueError):
        replace(pair, expected_c=replace(pair.expected_c, **{field: value}))


def test_declared_models_conditions_selectors_and_clock_allocations_can_differ():
    manifest = _manifest(scoring.CohortKind.PRIMARY)
    control = RoleSpec("catboost", "catboost-learner", "other-input-condition")
    pairs = tuple(replace(pair, expected_c=replace(
        pair.expected_c, arm_id=control.arm_id, model_identity=control.model_identity,
        scoring_input_condition_id=control.scoring_input_condition_id,
    )) for pair in manifest.pairs)
    manifest = replace(manifest, role_c=control, pairs=pairs)
    assert manifest.pairs[0].expected_a.clock_id != manifest.pairs[0].expected_c.clock_id
    result = bind_comparison(manifest, (_result(manifest, Role.A), _result(manifest, Role.C)))
    assert result.summary.overall.score.ties == 1
    assert result.summary.overall.score.unknown_pairs == 23
    assert result.pairs[0].arm_c.assessment.kind is policy.EndpointKind.DEPLOYABLE_VALID


@pytest.mark.parametrize("field,value", [("arm_id", "other-arm"),
                                         ("model_identity", "other-learner"),
                                         ("scoring_input_condition_id", "other-condition")])
def test_manifest_cannot_silently_mix_role_meanings_between_bases(field, value):
    manifest = _manifest()
    pair = manifest.pairs[0]
    changed = replace(pair, expected_a=replace(pair.expected_a, **{field: value}))
    with pytest.raises(ValueError, match="role declaration"):
        replace(manifest, pairs=(changed, *manifest.pairs[1:]))


def test_manifest_requires_complete_unique_cells_and_single_contrast():
    manifest = _manifest()
    pair = manifest.pairs[0]
    for pairs in (manifest.pairs[:-1], (pair, *manifest.pairs[:-1])):
        with pytest.raises(ValueError):
            replace(manifest, pairs=pairs)
    with pytest.raises(ValueError, match="one contrast"):
        replace(manifest, pairs=(replace(pair, contrast_id="other"), *manifest.pairs[1:]))
    changed = replace(pair, expected_c=replace(pair.expected_c, assignment_id=pair.expected_a.assignment_id))
    with pytest.raises(ValueError, match="assignment_id"):
        replace(manifest, pairs=(changed, *manifest.pairs[1:]))
    with pytest.raises(ValueError, match="immutable tuple"):
        replace(manifest, pairs=list(manifest.pairs))
    with pytest.raises(FrozenInstanceError):
        manifest.contrast_id = "changed"


def test_manifest_rejects_roster_assignment_subclass_even_with_compatible_equality():
    class CompatibleAssignment(scoring.PairAssignment):
        def __eq__(self, other):
            return isinstance(other, scoring.PairAssignment) and (
                self.base_id, self.size, self.seed
            ) == (other.base_id, other.size, other.seed)

        __hash__ = scoring.PairAssignment.__hash__

    manifest = _manifest()
    original = manifest.roster.assignments[0]
    subclass = CompatibleAssignment(original.base_id, original.size, original.seed)
    assert subclass == original and hash(subclass) == hash(original)
    roster = replace(manifest.roster, assignments=(subclass, *manifest.roster.assignments[1:]))
    with pytest.raises(ValueError, match="roster must contain exact PairAssignment"):
        replace(manifest, roster=roster)


@pytest.mark.parametrize("field,value", [("arm_id", "catboost"),
                                         ("model_identity", "catboost-learner"),
                                         ("scoring_input_condition_id", "fresh")])
def test_mechanism_requires_one_frozen_learner_and_distinct_condition_policies(field, value):
    manifest = _manifest()
    changed_role = replace(manifest.role_c, **{field: value})
    pairs = tuple(replace(pair, expected_c=replace(pair.expected_c, **{field: value}))
                  for pair in manifest.pairs)
    with pytest.raises(ValueError, match="mechanism contrast"):
        replace(manifest, role_c=changed_role, pairs=pairs)


@pytest.mark.parametrize("late", [False, True])
def test_only_classifier_healthy_no_plan_or_late_becomes_failure(late):
    manifest = _manifest()
    e = _evidence(manifest.pairs[0].expected_a)
    if late:
        e = replace(e, terminal=replace(e.terminal, post_outcome_ack_monotonic=161))
    else:
        e = replace(e, candidates=(), selected_candidate_id=None, deployment=policy.Deployment.EXPLICIT_NO_PLAN)
    result = bind_comparison(manifest, (_result(manifest, Role.A, e), _result(manifest, Role.C)))
    assert result.pairs[0].arm_a.endpoint.kind is scoring.EndpointKind.ALGORITHMIC_FAILURE
    assert result.pairs[0].arm_a.endpoint.bill is None
    assert result.summary.overall.score.losses == 1
    assert result.summary.overall.score.missing_mass == Fraction(11, 12)


def test_faults_cannot_be_dropped_to_rescue_favorable_bill_and_all_diagnostics_remain():
    manifest = _manifest()
    e = _evidence(manifest.pairs[0].expected_a, Fraction(1))
    e = replace(e, bound=policy.BoundEvidence(policy.BoundScope.INVALID_FULL_CLAIM, False, e.provenance_ids),
                causes=(policy.CauseEvidence(policy.Cause.MONITOR_FAULT, e.provenance_ids),
                        policy.CauseEvidence(policy.Cause.ACCOUNTING_FAULT, e.provenance_ids)))
    result = bind_comparison(manifest, (_result(manifest, Role.A, e), _result(manifest, Role.C)))
    cell = result.pairs[0].arm_a
    assert cell.endpoint.kind is scoring.EndpointKind.UNKNOWN and cell.endpoint.bill is None
    assert cell.evidence is e
    assert {"invalid_bound_claim", "monitor_fault", "accounting_fault"} <= set(cell.assessment.reason_codes)
    assert cell.assessment.causal_evidence_ids == e.provenance_ids
    assert result.stop_scopes == (policy.StopScope.STUDY_ENGINEERING,)
    assert result.summary.overall.arm_c_validity.valid == 1
    assert result.summary.overall.score.unknown_pairs == 12


def test_explicit_undispatched_stays_distinct_from_absent_unknown_and_retains_stop():
    manifest = _manifest()
    e = _evidence(manifest.pairs[0].expected_a)
    e = replace(e, dispatch_state=policy.DispatchState.UNDISPATCHED,
                executed_mode=policy.ExecutedMode.NOT_STARTED, deployment=policy.Deployment.UNKNOWN,
                candidates=(), selected_candidate_id=None,
                terminal=policy.TerminalEvidence(False, policy.AckState.MISSING,
                    policy.TerminalCause.ADMINISTRATIVE, 100, None, None, None, None, None,
                    False, False, False, e.provenance_ids),
                causes=(policy.CauseEvidence(policy.Cause.BUDGET_STOP, e.provenance_ids),))
    result = bind_comparison(manifest, (_result(manifest, Role.A, e),))
    assert result.pairs[0].arm_a.endpoint.kind is scoring.EndpointKind.UNDISPATCHED
    assert result.summary.overall.arm_a_validity.undispatched == 1
    assert result.summary.overall.arm_a_validity.unknown == 11
    assert result.summary.overall.arm_c_validity.unknown == 12
    assert result.stop_scopes == (policy.StopScope.STUDY_BUDGET,)


def test_qualification_failure_does_not_override_valid_policy_result():
    manifest = _manifest()
    e = _evidence(manifest.pairs[0].expected_a)
    e = replace(e, qualification=policy.QualificationEvidence(tuple(policy.Coverage), (), e.provenance_ids))
    result = bind_comparison(manifest, (_result(manifest, Role.A, e),))
    cell = result.pairs[0].arm_a
    assert cell.endpoint.kind is scoring.EndpointKind.VALID
    assert cell.assessment.qualification is policy.Qualification.FAILED


@pytest.mark.parametrize("condition", ["missing_ack", "invalid_admitted", "unsupported_certificate"])
def test_other_classifier_outcomes_are_unknown_not_failure_or_valid(condition):
    manifest = _manifest()
    e = _evidence(manifest.pairs[0].expected_a)
    if condition == "missing_ack":
        e = replace(e, terminal=replace(e.terminal, ack=policy.AckState.MISSING,
                                       post_outcome_ack_monotonic=None))
    elif condition == "invalid_admitted":
        e = replace(e, candidates=(*e.candidates, policy.CandidateEvidence(
            "bad-candidate", "bad-witness", policy.CandidateState.ADMITTED_INVALID,
            "external-proof", None, None, e.provenance_ids,
        )))
    else:
        e = replace(e, controller_certificate=policy.ControllerCertificate.UNSUPPORTED_FAILURE_ONLY)
    result = bind_comparison(manifest, (_result(manifest, Role.A, e), _result(manifest, Role.C)))
    assert result.pairs[0].arm_a.endpoint.kind is scoring.EndpointKind.UNKNOWN
    assert result.pairs[0].arm_a.endpoint.bill is None
    assert result.pairs[0].arm_a.assessment.stop_scope is policy.StopScope.STUDY_ENGINEERING
    assert result.summary.overall.arm_c_validity.valid == 1
    assert result.summary.overall.arm_a_validity.algorithmic_failures == 0


def test_same_endpoint_can_be_reused_only_in_explicit_separate_contrast_calls():
    first = _manifest(scoring.CohortKind.PRIMARY)
    control = RoleSpec("ca1", "model-none", "price-a-and-b")
    second = replace(first, manifest_id="manifest-two", immutable_reference="immutable:manifest-two",
                     contrast_id="graph-versus-control", role_c=control,
                     pairs=tuple(replace(pair, contrast_id="graph-versus-control", expected_c=replace(
                         pair.expected_c, arm_id=control.arm_id, model_identity=control.model_identity,
                         scoring_input_condition_id=control.scoring_input_condition_id,
                     )) for pair in first.pairs))
    e = _evidence(first.pairs[0].expected_a)
    a = bind_comparison(first, (_result(first, Role.A, e),))
    b = bind_comparison(second, (_result(second, Role.A, e),))
    assert a.pairs[0].arm_a.evidence is b.pairs[0].arm_a.evidence
    assert a.manifest.contrast_id != b.manifest.contrast_id
