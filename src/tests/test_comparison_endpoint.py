"""Hand-built prospective policy examples; no runtime receipt/data/solver imports."""

from dataclasses import replace
from fractions import Fraction

import pytest

from egglab.comparison_endpoint import (
    AckState, Acquisition, ArtifactReference, BoundEvidence, BoundScope,
    CandidateEvidence, CandidateOrigin, CandidateState, Cause, CauseEvidence, CellIdentity,
    ControllerCertificate, Coverage, Deployment, DispatchState, EndpointKind,
    DeploymentLatenessEvidence, ExecutedMode, Integrity, LatenessStage, NormalizedEvidence, Processing, Qualification,
    QualificationEvidence, StartAcceptance, StartEvidence, StopScope,
    TerminalCause, TerminalEvidence, classify_endpoint,
)


def _evidence():
    refs = ("manifest",)
    return NormalizedEvidence(
        identity=CellIdentity(
            "assignment-1", "base-1", "tariff-1", "fresh", "cold", 7,
            "clock-1", "source-identity", "model-none", "environment-identity",
            "library-identity", "full-case-1", "selector-1",
        ),
        artifacts=(
            ArtifactReference("manifest", "immutable:manifest"),
            ArtifactReference("capture", "immutable:capture"),
            ArtifactReference("durable", "immutable:durable"),
        ),
        provenance_ids=refs,
        dispatch_state=DispatchState.DISPATCHED,
        integrity=Integrity.HEALTHY,
        qualification=QualificationEvidence((), (), refs),
        acquisition=Acquisition.NOT_ATTEMPTED,
        executed_mode=ExecutedMode.COLD_FULL,
        deployment=Deployment.SELECTED_WITNESS,
        start=StartEvidence(False, Processing.UNOBSERVED, StartAcceptance.NOT_SUBMITTED, None, refs),
        bound=BoundEvidence(BoundScope.NONE, True, refs),
        terminal=TerminalEvidence(
            True, AckState.COMPLETE, TerminalCause.ORDINARY_METHOD,
            100.0, 155.0, 156.0, 157.0, 160.0, 162.0,
            False, False, False, refs,
        ),
        candidates=(CandidateEvidence(
            "candidate-1", "witness-1", CandidateState.ADMITTED_VERIFIED,
            "capture", "durable", Fraction(123, 7), refs,
        ),),
        selected_candidate_id="candidate-1",
        causes=(),
    )


def _no_plan(e):
    return replace(e, candidates=(), selected_candidate_id=None, deployment=Deployment.EXPLICIT_NO_PLAN)


def test_cold_selected_plan_is_valid_at_exact_sixty_second_ack():
    result = classify_endpoint(_evidence())
    assert result.kind is EndpointKind.DEPLOYABLE_VALID
    assert result.exact_bill == Fraction(123, 7)
    assert result.selected_witness_id == "witness-1"
    assert result.primary_eligible and result.stop_scope is StopScope.NONE
    assert result.qualification is Qualification.NOT_REQUIRED


def test_acquisition_deadline_and_unexercised_cf1_coverage_do_not_disqualify_cold():
    e = _evidence()
    e = replace(
        e, acquisition=Acquisition.DEADLINE,
        qualification=QualificationEvidence(tuple(Coverage), (), ("manifest",)),
        causes=(CauseEvidence(Cause.ORDINARY_ACQUISITION_DEADLINE, ("manifest",)),),
    )
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.DEPLOYABLE_VALID
    assert result.qualification is Qualification.FAILED
    assert result.acquisition is Acquisition.DEADLINE
    assert result.start_acceptance is StartAcceptance.NOT_SUBMITTED


def test_qualification_pass_is_a_separate_conditional_attestation():
    e = _evidence()
    # Schema cannot independently prove this fixed-charging attestation. A false
    # caller assertion can pass; a real external verifier must establish it.
    fixed = QualificationEvidence((Coverage.FIXED_CHARGING,), (Coverage.FIXED_CHARGING,), ("manifest",))
    assert classify_endpoint(replace(e, qualification=fixed)).qualification is Qualification.PASSED
    for component in (Coverage.BINARY_FULL_START, Coverage.ATTRIBUTABLE_PROCESSING, Coverage.ACQUIRED_DURABLE_FALLBACK):
        coverage = QualificationEvidence((component,), (component,), ("manifest",))
        with pytest.raises(ValueError):
            replace(e, qualification=coverage)
    fully_covered = replace(
        e, acquisition=Acquisition.ADMITTED, executed_mode=ExecutedMode.WARM_FULL,
        candidates=(replace(e.candidates[0], origin=CandidateOrigin.ACQUISITION),),
        start=StartEvidence(True, Processing.OBSERVED, StartAcceptance.ACCEPTED, "candidate-1", ("manifest",)),
        qualification=QualificationEvidence(tuple(Coverage), tuple(Coverage), ("manifest",)),
    )
    assert classify_endpoint(fully_covered).qualification is Qualification.PASSED
    with pytest.raises(ValueError):
        replace(fully_covered, acquisition=Acquisition.NO_PROPOSAL)


def test_processed_rejected_start_can_leave_a_valid_retained_fallback():
    e = _evidence()
    e = replace(e, acquisition=Acquisition.ADMITTED, executed_mode=ExecutedMode.WARM_FULL,
                start=StartEvidence(True, Processing.OBSERVED, StartAcceptance.REJECTED, "candidate-1", ("manifest",)))
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.DEPLOYABLE_VALID
    assert result.start_processing is Processing.OBSERVED
    assert result.start_acceptance is StartAcceptance.REJECTED
    interface_failure = replace(e, start=StartEvidence(False, Processing.UNOBSERVED,
                                StartAcceptance.INTERFACE_FAILED, "candidate-1", ("manifest",)))
    assert classify_endpoint(interface_failure).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN


def test_raw_rejection_is_diagnostic_and_cannot_be_selected_or_start_source():
    e = _evidence()
    rejected = CandidateEvidence("raw-2", None, CandidateState.RAW_REJECTED, "capture", None, None, ("manifest",))
    e = replace(e, candidates=(*e.candidates, rejected))
    assert classify_endpoint(e).kind is EndpointKind.DEPLOYABLE_VALID
    with pytest.raises(ValueError):
        replace(e, selected_candidate_id="raw-2")
    with pytest.raises(ValueError):
        replace(e, start=StartEvidence(True, Processing.UNOBSERVED, StartAcceptance.UNOBSERVED, "raw-2", ("manifest",)))
    rejected_only = replace(e, candidates=(rejected,), selected_candidate_id=None, deployment=Deployment.EXPLICIT_NO_PLAN)
    assert classify_endpoint(rejected_only).kind is EndpointKind.ALGORITHMIC_NO_PLAN


def test_invalid_admitted_candidate_stops_even_with_a_favorable_valid_selection():
    e = _evidence()
    invalid = CandidateEvidence("bad-2", "bad-witness-2", CandidateState.ADMITTED_INVALID, "capture", "durable", None, ("manifest",))
    result = classify_endpoint(replace(e, candidates=(*e.candidates, invalid)))
    assert result.kind is EndpointKind.INVALID_ADMITTED
    assert result.stop_scope is StopScope.STUDY_ENGINEERING
    assert not result.primary_eligible and result.exact_bill is None
    multiple_faults = replace(e, candidates=(*e.candidates, invalid),
                             bound=BoundEvidence(BoundScope.INVALID_FULL_CLAIM, False, ("manifest",)),
                             causes=(CauseEvidence(Cause.MONITOR_FAULT, ("manifest",)),))
    reasons = classify_endpoint(multiple_faults).reason_codes
    assert {"invalid_admitted_witness", "invalid_bound_claim", "monitor_fault"} <= set(reasons)


@pytest.mark.parametrize("bound", [
    BoundEvidence(BoundScope.INVALID_FULL_CLAIM, True, ("manifest",)),
    BoundEvidence(BoundScope.ORIGINAL_UNRESTRICTED_FULL, False, ("manifest",)),
])
def test_invalid_full_claim_stops_before_valid_bill(bound):
    result = classify_endpoint(replace(_evidence(), bound=bound))
    assert result.kind is EndpointKind.INVALID_FULL_CLAIM
    assert result.exact_bill is None and not result.primary_eligible
    assert result.stop_scope is StopScope.STUDY_ENGINEERING


@pytest.mark.parametrize("scope", [BoundScope.NONE, BoundScope.RESTRICTED_DIAGNOSTIC, BoundScope.ORIGINAL_UNRESTRICTED_FULL])
def test_bound_scope_is_independent_of_valid_plan(scope):
    result = classify_endpoint(replace(_evidence(), bound=BoundEvidence(scope, True, ("manifest",))))
    assert result.kind is EndpointKind.DEPLOYABLE_VALID
    assert result.bound_scope is scope
    if scope is not BoundScope.ORIGINAL_UNRESTRICTED_FULL:
        inconsistent = classify_endpoint(replace(_evidence(), bound=BoundEvidence(scope, False, ("manifest",))))
        assert inconsistent.kind is EndpointKind.INFRASTRUCTURE_UNKNOWN


@pytest.mark.parametrize("cause", [Cause.MONITOR_FAULT, Cause.RESOURCE_BREACH, Cause.INTERFACE_FAULT, Cause.AMBIGUOUS_CAUSE])
def test_earlier_integrity_fault_overrides_valid_bill_and_acquisition_deadline(cause):
    e = replace(_evidence(), acquisition=Acquisition.DEADLINE,
                causes=(CauseEvidence(cause, ("manifest",)),))
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    assert result.exact_bill is None and not result.primary_eligible
    assert cause.value in result.reason_codes
    assert result.stop_scope is StopScope.STUDY_ENGINEERING
    assert result.integrity is (Integrity.UNKNOWN if cause is Cause.AMBIGUOUS_CAUSE else Integrity.FAULT)
    if cause is Cause.AMBIGUOUS_CAUSE:
        positive = replace(e, causes=(*e.causes, CauseEvidence(Cause.MONITOR_FAULT, ("manifest",))))
        assert classify_endpoint(positive).integrity is Integrity.FAULT


def test_healthy_no_plan_and_late_ack_are_eligible_algorithmic_failures():
    e = _evidence()
    no_plan = classify_endpoint(_no_plan(e))
    assert no_plan.kind is EndpointKind.ALGORITHMIC_NO_PLAN
    assert no_plan.primary_eligible and no_plan.exact_bill is None
    late = classify_endpoint(replace(e, terminal=replace(e.terminal, post_outcome_ack_monotonic=160.01)))
    assert late.kind is EndpointKind.ALGORITHMIC_LATE
    assert late.primary_eligible and late.exact_bill is None
    assert late.stop_scope is StopScope.NONE


@pytest.mark.parametrize("ack", [AckState.MISSING, AckState.MALFORMED])
def test_missing_or_malformed_ack_remains_unknown_even_after_elapsed_deadline(ack):
    e = _no_plan(_evidence())
    e = replace(e, terminal=replace(e.terminal, ack=ack, post_outcome_ack_monotonic=None,
                                   owned_cleanup_monotonic=170.0))
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    assert not result.primary_eligible


def test_future_failure_only_controller_certificate_is_explicitly_unsupported():
    e = _no_plan(_evidence())
    e = replace(e, controller_certificate=ControllerCertificate.UNSUPPORTED_FAILURE_ONLY)
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    assert "failure_only_controller_certificate_unsupported" in result.reason_codes
    with pytest.raises(ValueError):
        replace(e, controller_certificate=True)


def test_censorship_or_administrative_interruption_alone_cannot_prove_algorithmic_failure():
    e = _no_plan(_evidence())
    for terminal in (
        replace(e.terminal, result_censored=True),
        replace(e.terminal, cause=TerminalCause.ADMINISTRATIVE),
        replace(e.terminal, externally_verified_complete_healthy_chain=False),
        replace(e.terminal, completion_fsync_monotonic=None),
        replace(e.terminal, cause=TerminalCause.KNOWN_ORDINARY_LATENESS),
        replace(e.terminal, result_censored=True, cause=TerminalCause.KNOWN_ORDINARY_LATENESS),
    ):
        assert classify_endpoint(replace(e, terminal=terminal)).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    lateness = DeploymentLatenessEvidence(LatenessStage.ADMISSION, 154.0, 154.01, ("manifest",))
    known_late = replace(e.terminal, result_censored=True, cause=TerminalCause.KNOWN_ORDINARY_LATENESS,
                         deployment_lateness=lateness)
    assert classify_endpoint(replace(e, terminal=known_late)).kind is EndpointKind.ALGORITHMIC_LATE
    selected = _evidence()
    assert classify_endpoint(replace(selected, terminal=replace(selected.terminal,
                             cause=TerminalCause.KNOWN_ORDINARY_LATENESS))).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    assert classify_endpoint(replace(e, deployment=Deployment.UNKNOWN)).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    interrupted = replace(e, causes=(CauseEvidence(Cause.ADMINISTRATIVE_STOP, ("manifest",)),))
    assert classify_endpoint(interrupted).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN


def test_undispatched_assignment_is_preserved_without_primary_outcome():
    e = _no_plan(_evidence())
    terminal = replace(e.terminal, externally_verified_complete_healthy_chain=False,
                       ack=AckState.MISSING, cause=TerminalCause.ADMINISTRATIVE,
                       result_fsync_monotonic=None, completion_fsync_monotonic=None,
                       outcome_fsync_monotonic=None, post_outcome_ack_monotonic=None,
                       owned_cleanup_monotonic=None)
    e = replace(e, dispatch_state=DispatchState.UNDISPATCHED, executed_mode=ExecutedMode.NOT_STARTED,
                deployment=Deployment.UNKNOWN, terminal=terminal,
                causes=(CauseEvidence(Cause.BUDGET_STOP, ("manifest",)),))
    result = classify_endpoint(e)
    assert result.kind is EndpointKind.UNDISPATCHED
    assert result.stop_scope is StopScope.STUDY_BUDGET
    assert result.assignment_id == "assignment-1" and not result.primary_eligible
    for stopped in (
        replace(e, causes=(*e.causes, CauseEvidence(Cause.MONITOR_FAULT, ("manifest",)))),
        replace(e, integrity=Integrity.FAULT),
    ):
        engineering = classify_endpoint(stopped)
        assert engineering.kind is EndpointKind.UNDISPATCHED
        assert engineering.stop_scope is StopScope.STUDY_ENGINEERING
        assert engineering.integrity is Integrity.FAULT and not engineering.primary_eligible
    ambiguous = classify_endpoint(replace(e, causes=(CauseEvidence(Cause.AMBIGUOUS_CAUSE, ("manifest",)),)))
    assert ambiguous.kind is EndpointKind.UNDISPATCHED
    assert ambiguous.stop_scope is StopScope.STUDY_ENGINEERING
    assert ambiguous.integrity is Integrity.UNKNOWN and not ambiguous.primary_eligible


@pytest.mark.parametrize("changes", [
    {"schema_version": "comparison.endpoint.normalized.v2"}, {"tag": "raw_worker_receipt"},
    {"integrity": "healthy"}, {"acquisition": "anything"}, {"artifacts": []},
    {"provenance_ids": ()}, {"provenance_ids": ("missing",)},
])
def test_strict_schema_rejects_unknown_versions_tags_enums_and_references(changes):
    with pytest.raises(ValueError):
        replace(_evidence(), **changes)


def test_strict_identity_artifact_and_candidate_validation():
    e = _evidence()
    with pytest.raises(ValueError):
        replace(e, executed_mode=ExecutedMode.NOT_STARTED)
    with pytest.raises(ValueError):
        replace(_no_plan(e), executed_mode=ExecutedMode.NOT_STARTED)
    unstarted_terminal = replace(e.terminal, externally_verified_complete_healthy_chain=False,
                                ack=AckState.MISSING, cause=TerminalCause.AMBIGUOUS,
                                result_fsync_monotonic=None, completion_fsync_monotonic=None,
                                outcome_fsync_monotonic=None, post_outcome_ack_monotonic=None)
    unstarted = replace(_no_plan(e), executed_mode=ExecutedMode.NOT_STARTED,
                        deployment=Deployment.UNKNOWN, terminal=unstarted_terminal)
    assert classify_endpoint(unstarted).kind is EndpointKind.INFRASTRUCTURE_UNKNOWN
    for artifacts in (e.artifacts + (e.artifacts[0],),
                      e.artifacts + (ArtifactReference("alias", "immutable:manifest"),)):
        with pytest.raises(ValueError):
            replace(e, artifacts=artifacts)
    with pytest.raises(ValueError):
        replace(e.identity, solver_seed=True)
    with pytest.raises(ValueError):
        ArtifactReference("manifest", "immutable:manifest", tag="verified_hash")
    with pytest.raises(ValueError):
        replace(e.candidates[0], exact_bill=1.5)
    with pytest.raises(ValueError):
        replace(e, candidates=(replace(e.candidates[0], capture_artifact_id="missing"),))
    with pytest.raises(ValueError):
        classify_endpoint({"failures": [], "selected": "looks-valid"})


@pytest.mark.parametrize("changes", [
    {"anchor_monotonic": True}, {"result_fsync_monotonic": float("nan")},
    {"post_outcome_ack_monotonic": float("inf")}, {"completion_fsync_monotonic": 154.0},
    {"owned_cleanup_monotonic": 159.0}, {"result_censored": 0},
    {"externally_verified_complete_healthy_chain": 1},
])
def test_reversed_nonfinite_or_malformed_terminal_evidence_is_rejected(changes):
    with pytest.raises(ValueError):
        replace(_evidence().terminal, **changes)
