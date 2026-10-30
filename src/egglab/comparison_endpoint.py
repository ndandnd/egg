"""Prospective policy over normalized, EXTERNALLY VERIFIED endpoint evidence.

This module does not read receipts, replay plans, hash artifacts, verify ACKs, or
qualify any controller. A caller's false attestation can produce a false result.
Only an independent, source-bound verifier may construct evidence for real use.
No current worker dictionaries or historical qualification results are inputs.
"""

from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
import math
from typing import Optional, Tuple


SCHEMA_VERSION = "comparison.endpoint.normalized.v1"
EVIDENCE_TAG = "externally_verified_normalized_evidence"
REFERENCE_TAG = "externally_verified_artifact_reference"
DEPLOYMENT_WINDOW_S = 60


class DispatchState(str, Enum):
    DISPATCHED = "dispatched"
    UNDISPATCHED = "undispatched"


class Integrity(str, Enum):
    HEALTHY = "healthy"
    FAULT = "fault"
    UNKNOWN = "unknown"


class Acquisition(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    ADMITTED = "admitted"
    NO_PROPOSAL = "no_proposal"
    DEADLINE = "deadline"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class ExecutedMode(str, Enum):
    NOT_STARTED = "not_started"
    ACQUISITION_ONLY = "acquisition_only"
    COLD_FULL = "cold_full"
    WARM_FULL = "warm_full"


class Deployment(str, Enum):
    SELECTED_WITNESS = "selected_witness"
    EXPLICIT_NO_PLAN = "explicit_no_plan"
    UNKNOWN = "unknown"


class Coverage(str, Enum):
    FIXED_CHARGING = "fixed_charging"
    ACQUIRED_DURABLE_FALLBACK = "acquired_durable_fallback"
    BINARY_FULL_START = "binary_full_start"
    ATTRIBUTABLE_PROCESSING = "attributable_processing"


class Qualification(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


class Processing(str, Enum):
    OBSERVED = "observed"
    UNOBSERVED = "unobserved"


class StartAcceptance(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNOBSERVED = "unobserved"
    INTERFACE_FAILED = "interface_failed"


class CandidateState(str, Enum):
    RAW_REJECTED = "raw_rejected"
    ADMITTED_VERIFIED = "admitted_verified"
    ADMITTED_INVALID = "admitted_invalid"


class CandidateOrigin(str, Enum):
    ACQUISITION = "acquisition"
    FULL_SEARCH = "full_search"


class LatenessStage(str, Enum):
    ADMISSION = "admission"
    REPLAY_BILLING = "replay_billing"
    CAPTURE = "capture"
    FINALIZATION = "finalization"


class BoundScope(str, Enum):
    NONE = "none"
    RESTRICTED_DIAGNOSTIC = "restricted_diagnostic"
    ORIGINAL_UNRESTRICTED_FULL = "original_unrestricted_full"
    INVALID_FULL_CLAIM = "invalid_full_claim"


class AckState(str, Enum):
    COMPLETE = "complete"
    MISSING = "missing"
    MALFORMED = "malformed"


class TerminalCause(str, Enum):
    ORDINARY_METHOD = "ordinary_method"
    KNOWN_ORDINARY_LATENESS = "known_ordinary_lateness"
    ADMINISTRATIVE = "administrative"
    AMBIGUOUS = "ambiguous"


class ControllerCertificate(str, Enum):
    ABSENT = "absent"
    UNSUPPORTED_FAILURE_ONLY = "unsupported_failure_only"


class Cause(str, Enum):
    INTEGRITY_FAULT = "integrity_fault"
    CLOCK_FAULT = "clock_fault"
    OWNERSHIP_FAULT = "ownership_fault"
    MONITOR_FAULT = "monitor_fault"
    ACCOUNTING_FAULT = "accounting_fault"
    RESOURCE_BREACH = "resource_breach"
    INTERFACE_FAULT = "interface_fault"
    CAPTURE_FAULT = "capture_fault"
    AMBIGUOUS_CAUSE = "ambiguous_cause"
    BUDGET_STOP = "budget_stop"
    ADMINISTRATIVE_STOP = "administrative_stop"
    RAW_CANDIDATE_REJECTED = "raw_candidate_rejected"
    ORDINARY_ACQUISITION_DEADLINE = "ordinary_acquisition_deadline"


class EndpointKind(str, Enum):
    DEPLOYABLE_VALID = "deployable_valid"
    ALGORITHMIC_NO_PLAN = "algorithmic_no_plan"
    ALGORITHMIC_LATE = "algorithmic_late"
    INFRASTRUCTURE_UNKNOWN = "infrastructure_unknown"
    INVALID_ADMITTED = "invalid_admitted"
    INVALID_FULL_CLAIM = "invalid_full_claim"
    UNDISPATCHED = "undispatched"


class StopScope(str, Enum):
    NONE = "none"
    STUDY_ENGINEERING = "study_engineering"
    STUDY_BUDGET = "study_budget"
    STUDY_ADMINISTRATIVE = "study_administrative"


def _enum(value, cls):
    if type(value) is not cls:
        raise ValueError("expected exact " + cls.__name__ + " enum")


def _text(value):
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("expected nonempty, unpadded identity/reference")


def _boolean(value):
    if type(value) is not bool:
        raise ValueError("expected bool")


def _tuple(value, cls):
    if type(value) is not tuple or any(type(item) is not cls for item in value):
        raise ValueError("expected tuple of exact " + cls.__name__)


def _ids(value):
    _tuple(value, str)
    for item in value:
        _text(item)
    if not value or len(set(value)) != len(value):
        raise ValueError("provenance IDs must be nonempty and unique")


@dataclass(frozen=True)
class ArtifactReference:
    """Opaque verifier-supplied identity; no hash or byte verification occurs here."""

    artifact_id: str
    immutable_reference: str
    tag: str = REFERENCE_TAG

    def __post_init__(self):
        _text(self.artifact_id)
        _text(self.immutable_reference)
        if type(self.tag) is not str or self.tag != REFERENCE_TAG:
            raise ValueError("unsupported artifact reference tag")


@dataclass(frozen=True)
class CellIdentity:
    assignment_id: str
    base_id: str
    physical_tariff_variant_id: str
    scoring_input_condition_id: str
    arm_id: str
    solver_seed: int
    clock_id: str
    source_identity: str
    model_identity: str
    environment_identity: str
    library_identity: str
    original_full_case_id: str
    selector_id: str

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name == "solver_seed":
                if type(value) is not int or value < 0:
                    raise ValueError("solver_seed must be a nonnegative int")
            else:
                _text(value)


@dataclass(frozen=True)
class QualificationEvidence:
    required: Tuple[Coverage, ...]
    externally_verified_covered: Tuple[Coverage, ...]
    provenance_ids: Tuple[str, ...]

    def __post_init__(self):
        for value in (self.required, self.externally_verified_covered):
            _tuple(value, Coverage)
            if len(set(value)) != len(value):
                raise ValueError("duplicate qualification component")
        _ids(self.provenance_ids)


@dataclass(frozen=True)
class StartEvidence:
    submitted: bool
    processing: Processing
    acceptance: StartAcceptance
    source_candidate_id: Optional[str]
    provenance_ids: Tuple[str, ...]

    def __post_init__(self):
        _boolean(self.submitted)
        _enum(self.processing, Processing)
        _enum(self.acceptance, StartAcceptance)
        _ids(self.provenance_ids)
        if self.source_candidate_id is not None:
            _text(self.source_candidate_id)
        if not self.submitted and (
            self.processing is not Processing.UNOBSERVED
            or self.acceptance not in (StartAcceptance.NOT_SUBMITTED, StartAcceptance.INTERFACE_FAILED)
        ):
            raise ValueError("unsubmitted start has processing/acceptance")
        if self.submitted and (
            self.source_candidate_id is None
            or self.acceptance is StartAcceptance.NOT_SUBMITTED
        ):
            raise ValueError("submitted start needs source and acceptance status")


@dataclass(frozen=True)
class CandidateEvidence:
    candidate_id: str
    witness_id: Optional[str]
    state: CandidateState
    capture_artifact_id: str
    durable_artifact_id: Optional[str]
    exact_bill: Optional[Fraction]
    provenance_ids: Tuple[str, ...]
    origin: CandidateOrigin = CandidateOrigin.FULL_SEARCH

    def __post_init__(self):
        _text(self.candidate_id)
        _text(self.capture_artifact_id)
        _enum(self.state, CandidateState)
        _enum(self.origin, CandidateOrigin)
        _ids(self.provenance_ids)
        for value in (self.witness_id, self.durable_artifact_id):
            if value is not None:
                _text(value)
        if self.exact_bill is not None and type(self.exact_bill) is not Fraction:
            raise ValueError("bill must be an exact Fraction")
        if self.state is CandidateState.RAW_REJECTED:
            if any(x is not None for x in (self.witness_id, self.durable_artifact_id, self.exact_bill)):
                raise ValueError("raw rejection cannot claim admitted witness/bill/artifact")
        elif self.witness_id is None:
            raise ValueError("admitted candidate needs witness identity")
        if self.state is CandidateState.ADMITTED_VERIFIED and (
            self.durable_artifact_id is None or self.exact_bill is None
        ):
            raise ValueError("verified admission needs durable artifact and exact bill")


@dataclass(frozen=True)
class BoundEvidence:
    scope: BoundScope
    externally_verified_noncontradictory: bool
    provenance_ids: Tuple[str, ...]

    def __post_init__(self):
        _enum(self.scope, BoundScope)
        _boolean(self.externally_verified_noncontradictory)
        _ids(self.provenance_ids)


@dataclass(frozen=True)
class CauseEvidence:
    code: Cause
    provenance_ids: Tuple[str, ...]

    def __post_init__(self):
        _enum(self.code, Cause)
        _ids(self.provenance_ids)


@dataclass(frozen=True)
class DeploymentLatenessEvidence:
    """External proof of a deployment-stage overrun, never an acquisition delay."""

    stage: LatenessStage
    cutoff_monotonic: float
    observed_monotonic: float
    provenance_ids: Tuple[str, ...]

    def __post_init__(self):
        _enum(self.stage, LatenessStage)
        _ids(self.provenance_ids)
        for value in (self.cutoff_monotonic, self.observed_monotonic):
            if type(value) not in (int, float):
                raise ValueError("lateness clocks must be finite numeric, excluding bool")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError("lateness clocks must be finite")
        if self.observed_monotonic <= self.cutoff_monotonic:
            raise ValueError("lateness requires a positive cutoff overrun")


@dataclass(frozen=True)
class TerminalEvidence:
    """All booleans and times are verifier attestations, never local verification."""

    externally_verified_complete_healthy_chain: bool
    ack: AckState
    cause: TerminalCause
    anchor_monotonic: float
    result_fsync_monotonic: Optional[float]
    completion_fsync_monotonic: Optional[float]
    outcome_fsync_monotonic: Optional[float]
    post_outcome_ack_monotonic: Optional[float]
    owned_cleanup_monotonic: Optional[float]
    result_censored: bool
    completion_censored: bool
    outcome_censored: bool
    provenance_ids: Tuple[str, ...]
    deployment_lateness: Optional[DeploymentLatenessEvidence] = None

    def __post_init__(self):
        _boolean(self.externally_verified_complete_healthy_chain)
        _enum(self.ack, AckState)
        _enum(self.cause, TerminalCause)
        _ids(self.provenance_ids)
        for value in (self.result_censored, self.completion_censored, self.outcome_censored):
            _boolean(value)
        clocks = (
            self.anchor_monotonic, self.result_fsync_monotonic,
            self.completion_fsync_monotonic, self.outcome_fsync_monotonic,
            self.post_outcome_ack_monotonic, self.owned_cleanup_monotonic,
        )
        if self.anchor_monotonic is None:
            raise ValueError("anchor clock is required")
        previous = None
        for value in clocks:
            if value is None:
                continue
            if type(value) not in (int, float):
                raise ValueError("clock must be finite numeric, excluding bool")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError("clock must be finite numeric, excluding bool")
            if previous is not None and value < previous:
                raise ValueError("reversed terminal clock")
            previous = value
        if self.ack is AckState.COMPLETE and self.post_outcome_ack_monotonic is None:
            raise ValueError("complete ACK needs a timestamp")
        if self.ack is not AckState.COMPLETE and self.post_outcome_ack_monotonic is not None:
            raise ValueError("missing/malformed ACK cannot attest a complete ACK time")
        late = self.deployment_lateness
        if late is not None:
            if type(late) is not DeploymentLatenessEvidence:
                raise ValueError("expected exact DeploymentLatenessEvidence")
            if not self.anchor_monotonic <= late.cutoff_monotonic <= self.anchor_monotonic + DEPLOYMENT_WINDOW_S:
                raise ValueError("deployment lateness cutoff must be in assigned window")
            if self.owned_cleanup_monotonic is not None and late.observed_monotonic > self.owned_cleanup_monotonic:
                raise ValueError("deployment lateness cannot occur after owned cleanup")
            if self.post_outcome_ack_monotonic is not None and late.observed_monotonic > self.post_outcome_ack_monotonic:
                raise ValueError("deployment-stage overrun cannot occur after final ACK")


@dataclass(frozen=True)
class NormalizedEvidence:
    identity: CellIdentity
    artifacts: Tuple[ArtifactReference, ...]
    provenance_ids: Tuple[str, ...]
    dispatch_state: DispatchState
    integrity: Integrity
    qualification: QualificationEvidence
    acquisition: Acquisition
    executed_mode: ExecutedMode
    deployment: Deployment
    start: StartEvidence
    bound: BoundEvidence
    terminal: TerminalEvidence
    candidates: Tuple[CandidateEvidence, ...]
    selected_candidate_id: Optional[str]
    causes: Tuple[CauseEvidence, ...]
    controller_certificate: ControllerCertificate = ControllerCertificate.ABSENT
    schema_version: str = SCHEMA_VERSION
    tag: str = EVIDENCE_TAG

    def __post_init__(self):
        if type(self.schema_version) is not str or self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported normalized evidence schema version")
        if type(self.tag) is not str or self.tag != EVIDENCE_TAG:
            raise ValueError("unsupported normalized evidence tag")
        for name, cls in (
            ("identity", CellIdentity), ("qualification", QualificationEvidence),
            ("start", StartEvidence), ("bound", BoundEvidence), ("terminal", TerminalEvidence),
        ):
            if type(getattr(self, name)) is not cls:
                raise ValueError("expected exact " + cls.__name__)
        for name, cls in (
            ("dispatch_state", DispatchState), ("integrity", Integrity),
            ("acquisition", Acquisition), ("executed_mode", ExecutedMode),
            ("deployment", Deployment), ("controller_certificate", ControllerCertificate),
        ):
            _enum(getattr(self, name), cls)
        _tuple(self.artifacts, ArtifactReference)
        _tuple(self.candidates, CandidateEvidence)
        _tuple(self.causes, CauseEvidence)
        _ids(self.provenance_ids)
        artifact_ids = {x.artifact_id for x in self.artifacts}
        if len(artifact_ids) != len(self.artifacts) or len({x.immutable_reference for x in self.artifacts}) != len(self.artifacts):
            raise ValueError("artifact IDs and immutable references must each be unique")
        linked = [self, self.qualification, self.start, self.bound, self.terminal, *self.candidates, *self.causes]
        if self.terminal.deployment_lateness is not None:
            linked.append(self.terminal.deployment_lateness)
        if any(not set(item.provenance_ids) <= artifact_ids for item in linked):
            raise ValueError("dangling provenance artifact ID")
        by_id = {x.candidate_id: x for x in self.candidates}
        witnesses = [x.witness_id for x in self.candidates if x.witness_id is not None]
        if len(by_id) != len(self.candidates) or len(set(witnesses)) != len(witnesses):
            raise ValueError("candidate and witness identities must be unique")
        for candidate in self.candidates:
            refs = {candidate.capture_artifact_id}
            if candidate.durable_artifact_id is not None:
                refs.add(candidate.durable_artifact_id)
            if not refs <= artifact_ids:
                raise ValueError("dangling capture/durable artifact ID")
        for candidate_id in (self.selected_candidate_id, self.start.source_candidate_id):
            if candidate_id is not None:
                _text(candidate_id)
                if candidate_id not in by_id or by_id[candidate_id].state is CandidateState.RAW_REJECTED:
                    raise ValueError("selection/start source must reference admitted candidate")
        covered = set(self.qualification.externally_verified_covered)
        if Coverage.BINARY_FULL_START in covered and not self.start.submitted:
            raise ValueError("binary-start coverage contradicts absent submission")
        if Coverage.ATTRIBUTABLE_PROCESSING in covered and self.start.processing is not Processing.OBSERVED:
            raise ValueError("processing coverage contradicts unobserved processing")
        if Coverage.ACQUIRED_DURABLE_FALLBACK in covered and (
            self.acquisition is not Acquisition.ADMITTED or not any(
                c.origin is CandidateOrigin.ACQUISITION and c.state is CandidateState.ADMITTED_VERIFIED
                for c in self.candidates
            )
        ):
            raise ValueError("acquired-fallback coverage needs verified acquisition admission")
        if (self.deployment is Deployment.SELECTED_WITNESS) != (self.selected_candidate_id is not None):
            raise ValueError("selected deployment and candidate identity must agree")
        if self.deployment is Deployment.EXPLICIT_NO_PLAN and any(
            c.state is CandidateState.ADMITTED_VERIFIED for c in self.candidates
        ):
            raise ValueError("explicit no-plan conflicts with verified retained witness")
        if self.executed_mode is ExecutedMode.NOT_STARTED and (
            self.candidates or self.start.submitted or self.start.source_candidate_id is not None
            or self.start.processing is not Processing.UNOBSERVED
            or self.start.acceptance is not StartAcceptance.NOT_SUBMITTED
            or self.acquisition is not Acquisition.NOT_ATTEMPTED
            or self.deployment is not Deployment.UNKNOWN
            or self.terminal.externally_verified_complete_healthy_chain
            or self.terminal.deployment_lateness is not None
            or any(x is not None for x in (
                self.terminal.result_fsync_monotonic, self.terminal.completion_fsync_monotonic,
                self.terminal.outcome_fsync_monotonic, self.terminal.post_outcome_ack_monotonic,
            ))
        ):
            raise ValueError("not-started mode cannot claim method execution evidence")
        if self.dispatch_state is DispatchState.UNDISPATCHED and (
            self.executed_mode is not ExecutedMode.NOT_STARTED or self.candidates or self.start.submitted
            or self.acquisition is not Acquisition.NOT_ATTEMPTED
            or self.deployment is not Deployment.UNKNOWN
            or self.terminal.externally_verified_complete_healthy_chain
            or any(x is not None for x in (
                self.terminal.result_fsync_monotonic, self.terminal.completion_fsync_monotonic,
                self.terminal.outcome_fsync_monotonic, self.terminal.post_outcome_ack_monotonic,
                self.terminal.owned_cleanup_monotonic,
            ))
        ):
            raise ValueError("undispatched assignment cannot claim executed method evidence")


@dataclass(frozen=True)
class EndpointAssessment:
    """Semantic policy result only; contains no verification or launch authority."""

    assignment_id: str
    kind: EndpointKind
    qualification: Qualification
    integrity: Integrity
    acquisition: Acquisition
    executed_mode: ExecutedMode
    deployment: Deployment
    dispatch_state: DispatchState
    start_processing: Processing
    start_acceptance: StartAcceptance
    bound_scope: BoundScope
    primary_eligible: bool
    stop_scope: StopScope
    selected_witness_id: Optional[str]
    exact_bill: Optional[Fraction]
    reason_codes: Tuple[str, ...]
    causal_evidence_ids: Tuple[str, ...]
    schema_version: str = SCHEMA_VERSION


_FAULT_CAUSES = frozenset((
    Cause.INTEGRITY_FAULT, Cause.CLOCK_FAULT, Cause.OWNERSHIP_FAULT,
    Cause.MONITOR_FAULT, Cause.ACCOUNTING_FAULT, Cause.RESOURCE_BREACH,
    Cause.INTERFACE_FAULT, Cause.CAPTURE_FAULT,
))


def classify_endpoint(evidence: NormalizedEvidence) -> EndpointAssessment:
    """Assess strict normalized attestations; never accept a raw receipt mapping.

    Malformed schema raises ValueError. Unknown/missing operational evidence is
    a semantic unknown with a study stop. Qualification failure alone does not
    affect deployment eligibility. No failure-only controller path is supported.
    """
    if type(evidence) is not NormalizedEvidence:
        raise ValueError("expected NormalizedEvidence, not raw runtime receipts")
    e = evidence
    qualification = (
        Qualification.NOT_REQUIRED if not e.qualification.required else
        Qualification.PASSED if set(e.qualification.required) <= set(e.qualification.externally_verified_covered)
        else Qualification.FAILED
    )
    reasons = [cause.code.value for cause in e.causes]
    if any(c.state is CandidateState.ADMITTED_INVALID for c in e.candidates):
        reasons.append("invalid_admitted_witness")
    if e.bound.scope is BoundScope.INVALID_FULL_CLAIM or (e.bound.scope is BoundScope.ORIGINAL_UNRESTRICTED_FULL and not e.bound.externally_verified_noncontradictory):
        reasons.append("invalid_bound_claim")
    if not e.bound.externally_verified_noncontradictory:
        reasons.append("bound_evidence_contradictory")
    if e.start.acceptance is StartAcceptance.INTERFACE_FAILED:
        reasons.append("start_interface_failed")
    if e.terminal.ack is not AckState.COMPLETE:
        reasons.append("ack_" + e.terminal.ack.value)
    if e.controller_certificate is not ControllerCertificate.ABSENT:
        reasons.append("failure_only_controller_certificate_unsupported")
    refs = set(e.provenance_ids)
    for item in (e.qualification, e.start, e.bound, e.terminal, *e.candidates, *e.causes):
        refs.update(item.provenance_ids)
    for candidate in e.candidates:
        refs.add(candidate.capture_artifact_id)
        if candidate.durable_artifact_id is not None:
            refs.add(candidate.durable_artifact_id)
    if e.terminal.deployment_lateness is not None:
        refs.update(e.terminal.deployment_lateness.provenance_ids)
    selected = next((c for c in e.candidates if c.candidate_id == e.selected_candidate_id), None)
    positive_fault = (
        e.integrity is Integrity.FAULT
        or any(c.code in _FAULT_CAUSES for c in e.causes)
        or e.start.acceptance is StartAcceptance.INTERFACE_FAILED
    )
    ambiguous_cause = any(c.code is Cause.AMBIGUOUS_CAUSE for c in e.causes)

    def result(kind, reason, stop=StopScope.NONE, integrity=None):
        valid = kind is EndpointKind.DEPLOYABLE_VALID
        return EndpointAssessment(
            assignment_id=e.identity.assignment_id, kind=kind,
            qualification=qualification, integrity=integrity or e.integrity,
            acquisition=e.acquisition, executed_mode=e.executed_mode,
            deployment=e.deployment, dispatch_state=e.dispatch_state,
            start_processing=e.start.processing, start_acceptance=e.start.acceptance,
            bound_scope=e.bound.scope,
            primary_eligible=kind in (EndpointKind.DEPLOYABLE_VALID, EndpointKind.ALGORITHMIC_NO_PLAN, EndpointKind.ALGORITHMIC_LATE),
            stop_scope=stop,
            selected_witness_id=selected.witness_id if valid else None,
            exact_bill=selected.exact_bill if valid else None,
            reason_codes=tuple(dict.fromkeys((*reasons, reason))),
            causal_evidence_ids=tuple(sorted(refs)),
        )

    if e.dispatch_state is DispatchState.UNDISPATCHED:
        if positive_fault or ambiguous_cause:
            return result(EndpointKind.UNDISPATCHED, "assignment_undispatched", StopScope.STUDY_ENGINEERING,
                          Integrity.FAULT if positive_fault else Integrity.UNKNOWN)
        stop = StopScope.STUDY_BUDGET if any(c.code is Cause.BUDGET_STOP for c in e.causes) else StopScope.STUDY_ADMINISTRATIVE
        return result(EndpointKind.UNDISPATCHED, "assignment_undispatched", stop)
    # Preserve all supplied causes; a favorable selected bill cannot override any.
    if any(c.state is CandidateState.ADMITTED_INVALID for c in e.candidates):
        return result(EndpointKind.INVALID_ADMITTED, "invalid_admitted_witness", StopScope.STUDY_ENGINEERING, Integrity.FAULT)
    if e.bound.scope is BoundScope.INVALID_FULL_CLAIM or (e.bound.scope is BoundScope.ORIGINAL_UNRESTRICTED_FULL and not e.bound.externally_verified_noncontradictory):
        return result(EndpointKind.INVALID_FULL_CLAIM, "invalid_bound_claim", StopScope.STUDY_ENGINEERING, Integrity.FAULT)
    if not e.bound.externally_verified_noncontradictory:
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "bound_evidence_contradictory", StopScope.STUDY_ENGINEERING, Integrity.FAULT)
    if e.integrity is not Integrity.HEALTHY or positive_fault or ambiguous_cause:
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "integrity_not_established", StopScope.STUDY_ENGINEERING,
                      Integrity.FAULT if positive_fault else Integrity.UNKNOWN)
    if any(c.code in (Cause.BUDGET_STOP, Cause.ADMINISTRATIVE_STOP) for c in e.causes):
        stop = StopScope.STUDY_BUDGET if any(c.code is Cause.BUDGET_STOP for c in e.causes) else StopScope.STUDY_ADMINISTRATIVE
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "assigned_method_interrupted", stop, Integrity.UNKNOWN)
    if e.controller_certificate is not ControllerCertificate.ABSENT:
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "failure_only_controller_certificate_unsupported", StopScope.STUDY_ENGINEERING, Integrity.UNKNOWN)
    t = e.terminal
    complete_times = all(x is not None for x in (
        t.result_fsync_monotonic, t.completion_fsync_monotonic,
        t.outcome_fsync_monotonic, t.post_outcome_ack_monotonic, t.owned_cleanup_monotonic,
    ))
    if not t.externally_verified_complete_healthy_chain or t.ack is not AckState.COMPLETE or not complete_times or t.cause not in (TerminalCause.ORDINARY_METHOD, TerminalCause.KNOWN_ORDINARY_LATENESS):
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "complete_healthy_terminal_chain_missing", StopScope.STUDY_ENGINEERING, Integrity.UNKNOWN)
    if t.post_outcome_ack_monotonic > t.anchor_monotonic + DEPLOYMENT_WINDOW_S:
        return result(EndpointKind.ALGORITHMIC_LATE, "known_ordinary_method_lateness")
    if t.cause is TerminalCause.KNOWN_ORDINARY_LATENESS or t.deployment_lateness is not None:
        if t.cause is TerminalCause.KNOWN_ORDINARY_LATENESS and t.deployment_lateness is not None and (t.result_censored or t.completion_censored or t.outcome_censored):
            return result(EndpointKind.ALGORITHMIC_LATE, "known_ordinary_deployment_cutoff_overrun")
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "deployment_lateness_not_consistently_established", StopScope.STUDY_ENGINEERING, Integrity.UNKNOWN)
    if t.result_censored or t.completion_censored or t.outcome_censored:
        return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "censored_without_known_lateness", StopScope.STUDY_ENGINEERING, Integrity.UNKNOWN)
    if selected is not None and selected.state is CandidateState.ADMITTED_VERIFIED:
        return result(EndpointKind.DEPLOYABLE_VALID, "timely_verified_selected_witness")
    if e.deployment is Deployment.EXPLICIT_NO_PLAN:
        return result(EndpointKind.ALGORITHMIC_NO_PLAN, "healthy_explicit_no_plan")
    return result(EndpointKind.INFRASTRUCTURE_UNKNOWN, "deployment_not_established", StopScope.STUDY_ENGINEERING, Integrity.UNKNOWN)
