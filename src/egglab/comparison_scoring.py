"""Exact descriptive scores for an explicit, fixed comparison assignment roster.

Inputs are already-adjudicated symbolic endpoints. This module neither reads
receipts nor establishes replay validity, health, timeliness, or currency policy.
Records do not carry arm, learner, tariff, or scoring-input identities: the caller
and external verifier must establish identity-only joins for one oriented contrast.
Arithmetic cannot detect a cross-learner/cross-tariff misjoin with the same key.
Unknown-score bounds are marginal missing-outcome bounds, not confidence
intervals or a jointly attainable ranking across contrasts. No inference or
runtime/solver dependencies are provided.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable


RationalInput = Fraction | int | str
SIZES = (40, 80)
SEEDS = (17, 41, 73)


def exact_rational(value: RationalInput) -> Fraction:
    """Accept exact integers/Fractions or canonical reduced rational strings.

    Strings must equal Fraction's canonical spelling (e.g. ``-3/2`` or ``2``).
    Floats, booleans, decimal strings, whitespace, and nonfinite values fail.
    """
    if isinstance(value, bool):
        raise TypeError("booleans are not rational inputs")
    if isinstance(value, (Fraction, int)):
        return Fraction(value)
    if isinstance(value, str):
        try:
            parsed = Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError("expected a canonical rational string") from exc
        if str(parsed) != value:
            raise ValueError("expected a canonical rational string")
        return parsed
    raise TypeError("use Fraction, int, or a canonical rational string")


def _positive_unit(value: RationalInput) -> Fraction:
    unit = exact_rational(value)
    if unit <= 0:
        raise ValueError("currency_unit must be positive")
    return unit


class EndpointKind(str, Enum):
    VALID = "valid"
    ALGORITHMIC_FAILURE = "algorithmic_failure"
    UNKNOWN = "unknown"
    UNDISPATCHED = "undispatched"


@dataclass(frozen=True)
class Endpoint:
    """An externally adjudicated endpoint; only VALID carries a bill.

    ALGORITHMIC_FAILURE asserts a complete healthy failure adjudication supplied
    by the caller. UNKNOWN includes invalid/ambiguous source evidence. Creating
    VALID here does not certify the source evidence or independently replay it.
    """

    kind: EndpointKind
    bill: RationalInput | None = None
    currency_unit: RationalInput = 1

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EndpointKind):
            raise TypeError("kind must be an EndpointKind, not a raw status")
        object.__setattr__(self, "currency_unit", _positive_unit(self.currency_unit))
        if self.kind is EndpointKind.VALID:
            if self.bill is None:
                raise ValueError("a valid endpoint requires an exact bill")
            object.__setattr__(self, "bill", exact_rational(self.bill))
        elif self.bill is not None:
            raise ValueError("only a valid endpoint may carry a bill")


@dataclass(frozen=True)
class ExactBounds:
    lower: Fraction
    upper: Fraction


@dataclass(frozen=True)
class PairScore:
    """Known score or conservative [-1, 1]; bill diagnostics only if both valid."""

    value: int | None
    bounds: ExactBounds
    tie_band: Fraction | None = None
    bill_difference: Fraction | None = None  # bill_C - bill_A


def _check_endpoints(arm_a: Endpoint, arm_c: Endpoint) -> None:
    if not isinstance(arm_a, Endpoint) or not isinstance(arm_c, Endpoint):
        raise TypeError("pair inputs must be Endpoint records")
    if arm_a.currency_unit != arm_c.currency_unit:
        raise ValueError("pair currency units must match")


def score_pair(arm_a: Endpoint, arm_c: Endpoint) -> PairScore:
    """Positive favors A; exact 1/200 band includes equality in the tie."""
    _check_endpoints(arm_a, arm_c)
    unknown = (EndpointKind.UNKNOWN, EndpointKind.UNDISPATCHED)
    if arm_a.kind in unknown or arm_c.kind in unknown:
        return PairScore(None, ExactBounds(Fraction(-1), Fraction(1)))
    if arm_a.kind is EndpointKind.VALID and arm_c.kind is EndpointKind.VALID:
        band = max(abs(arm_a.bill), abs(arm_c.bill), arm_a.currency_unit) / 200
        difference = arm_c.bill - arm_a.bill
        value = 1 if difference > band else -1 if difference < -band else 0
        return PairScore(value, ExactBounds(Fraction(value), Fraction(value)),
                         band, difference)
    value = int(arm_a.kind is EndpointKind.VALID) - int(arm_c.kind is EndpointKind.VALID)
    return PairScore(value, ExactBounds(Fraction(value), Fraction(value)))


def validity_bounds(endpoint: Endpoint) -> ExactBounds:
    if not isinstance(endpoint, Endpoint):
        raise TypeError("validity input must be an Endpoint record")
    if endpoint.kind is EndpointKind.VALID:
        return ExactBounds(Fraction(1), Fraction(1))
    if endpoint.kind is EndpointKind.ALGORITHMIC_FAILURE:
        return ExactBounds(Fraction(0), Fraction(0))
    return ExactBounds(Fraction(0), Fraction(1))


def validity_difference_bounds(arm_a: Endpoint, arm_c: Endpoint) -> ExactBounds:
    """Retain known opponent validity even when practical score is unknown."""
    _check_endpoints(arm_a, arm_c)
    a, c = validity_bounds(arm_a), validity_bounds(arm_c)
    return ExactBounds(a.lower - c.upper, a.upper - c.lower)


class CohortKind(str, Enum):
    PRIMARY = "primary"
    MECHANISM = "mechanism"


@dataclass(frozen=True)
class PairAssignment:
    """One preassigned paired seed; base identifiers are supplied by the caller."""

    base_id: str
    size: int
    seed: int

    def __post_init__(self) -> None:
        if not isinstance(self.base_id, str) or not self.base_id or self.base_id.strip() != self.base_id:
            raise ValueError("base_id must be a nonempty unpadded string")
        if type(self.size) is not int or self.size not in SIZES:
            raise ValueError("size must be 40 or 80")
        if type(self.seed) is not int or self.seed not in SEEDS:
            raise ValueError("seed must be one of 17, 41, 73")


@dataclass(frozen=True)
class AssignmentRoster:
    """The full roster, including missing/undispatched assignments.

    PRIMARY requires eight bases (four per size); MECHANISM requires four
    (two per size), for one learner only. Both require all three fixed seeds.
    Currency unit is a fixed exact manifest input, shared by all endpoints.
    """

    kind: CohortKind
    assignments: tuple[PairAssignment, ...]
    currency_unit: RationalInput = 1

    def __post_init__(self) -> None:
        if not isinstance(self.kind, CohortKind):
            raise TypeError("kind must be a CohortKind")
        object.__setattr__(self, "currency_unit", _positive_unit(self.currency_unit))
        assignments = tuple(self.assignments)
        object.__setattr__(self, "assignments", assignments)
        if any(not isinstance(item, PairAssignment) for item in assignments):
            raise TypeError("roster entries must be PairAssignment records")
        if len(set(assignments)) != len(assignments):
            raise ValueError("duplicate assignment pair key")
        base_sizes: dict[str, int] = {}
        base_seeds: dict[str, set[int]] = {}
        for item in assignments:
            if item.base_id in base_sizes and base_sizes[item.base_id] != item.size:
                raise ValueError("a base identifier cannot occur in different sizes")
            base_sizes[item.base_id] = item.size
            base_seeds.setdefault(item.base_id, set()).add(item.seed)
        bases_per_size = 4 if self.kind is CohortKind.PRIMARY else 2
        if any(sum(size == h for size in base_sizes.values()) != bases_per_size for h in SIZES):
            raise ValueError("wrong fixed number of bases per size")
        if any(seeds != set(SEEDS) for seeds in base_seeds.values()):
            raise ValueError("every base must retain the three assigned seeds")

    @property
    def pair_weight(self) -> Fraction:
        return Fraction(1, len(self.assignments))

    @property
    def base_weight(self) -> Fraction:
        return 3 * self.pair_weight

    @property
    def size_weight(self) -> Fraction:
        return Fraction(1, 2)


@dataclass(frozen=True)
class PairObservation:
    assignment: PairAssignment
    arm_a: Endpoint
    arm_c: Endpoint

    def __post_init__(self) -> None:
        if not isinstance(self.assignment, PairAssignment):
            raise TypeError("observation requires a PairAssignment")
        _check_endpoints(self.arm_a, self.arm_c)


@dataclass(frozen=True)
class ScoreSummary:
    assigned_count: int
    known_score_sum: int
    wins: int
    ties: int
    losses: int
    unknown_pairs: int
    known_component: Fraction
    missing_mass: Fraction
    bounds: ExactBounds


@dataclass(frozen=True)
class ValiditySummary:
    assigned_count: int
    valid: int
    algorithmic_failures: int
    unknown: int
    undispatched: int
    bounds: ExactBounds


@dataclass(frozen=True)
class GroupSummary:
    score: ScoreSummary
    arm_a_validity: ValiditySummary
    arm_c_validity: ValiditySummary
    validity_difference: ExactBounds


@dataclass(frozen=True)
class BaseSummary:
    base_id: str
    size: int
    summary: GroupSummary


@dataclass(frozen=True)
class SizeSummary:
    size: int
    summary: GroupSummary


@dataclass(frozen=True)
class CohortSummary:
    """Fixed assigned-cohort summaries; not sampling confidence intervals."""

    per_base: tuple[BaseSummary, ...]
    per_size: tuple[SizeSummary, ...]
    overall: GroupSummary


def _validity_summary(endpoints: tuple[Endpoint, ...]) -> ValiditySummary:
    n = len(endpoints)
    counts = {kind: sum(item.kind is kind for item in endpoints) for kind in EndpointKind}
    valid = counts[EndpointKind.VALID]
    unknown = counts[EndpointKind.UNKNOWN]
    undispatched = counts[EndpointKind.UNDISPATCHED]
    return ValiditySummary(n, valid, counts[EndpointKind.ALGORITHMIC_FAILURE], unknown,
                           undispatched, ExactBounds(Fraction(valid, n),
                                                    Fraction(valid + unknown + undispatched, n)))


def _group_summary(observations: tuple[PairObservation, ...]) -> GroupSummary:
    n = len(observations)
    scores = tuple(score_pair(item.arm_a, item.arm_c).value for item in observations)
    wins, ties, losses = (scores.count(value) for value in (1, 0, -1))
    unknown = scores.count(None)
    total = wins - losses
    score = ScoreSummary(n, total, wins, ties, losses, unknown,
                         Fraction(total, n), Fraction(unknown, n),
                         ExactBounds(Fraction(total - unknown, n), Fraction(total + unknown, n)))
    differences = tuple(validity_difference_bounds(item.arm_a, item.arm_c) for item in observations)
    return GroupSummary(score, _validity_summary(tuple(item.arm_a for item in observations)),
                        _validity_summary(tuple(item.arm_c for item in observations)),
                        ExactBounds(sum((item.lower for item in differences), Fraction()) / n,
                                    sum((item.upper for item in differences), Fraction()) / n))


def summarize_comparison(roster: AssignmentRoster,
                         observations: Iterable[PairObservation] = ()) -> CohortSummary:
    """Score one oriented contrast using the complete fixed assignment roster.

    Omitted observations become UNKNOWN for both arms, preserving denominator.
    Explicit UNDISPATCHED endpoints retain that separate validity count. Duplicate
    or unlisted observations, mixed units, and malformed rosters are rejected.
    The caller/external verifier must establish arm, learner, tariff, scoring-input,
    and oriented-contrast alignment through identity-only joins before this call;
    these records lack those identities and cannot detect same-key misjoins.
    Balanced roster validation makes uniform seed weights exactly equivalent to
    averaging three seeds per base, equal bases per size, then sizes equally.
    """
    if not isinstance(roster, AssignmentRoster):
        raise TypeError("roster must be an AssignmentRoster")
    assigned = set(roster.assignments)
    observed: dict[PairAssignment, PairObservation] = {}
    for item in observations:
        if not isinstance(item, PairObservation):
            raise TypeError("observations must be PairObservation records")
        if item.assignment not in assigned:
            raise ValueError("observation is outside the fixed roster")
        if item.assignment in observed:
            raise ValueError("duplicate observation pair key")
        if item.arm_a.currency_unit != roster.currency_unit:
            raise ValueError("observation currency unit differs from the roster")
        observed[item.assignment] = item
    missing = Endpoint(EndpointKind.UNKNOWN, currency_unit=roster.currency_unit)
    complete = tuple(observed.get(key, PairObservation(key, missing, missing))
                     for key in roster.assignments)
    bases = sorted({(item.assignment.size, item.assignment.base_id) for item in complete})
    per_base = tuple(BaseSummary(base, size, _group_summary(tuple(
        item for item in complete if item.assignment.base_id == base))) for size, base in bases)
    per_size = tuple(SizeSummary(size, _group_summary(tuple(
        item for item in complete if item.assignment.size == size))) for size in SIZES)
    return CohortSummary(per_base, per_size, _group_summary(complete))
