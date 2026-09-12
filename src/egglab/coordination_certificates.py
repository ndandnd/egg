"""Conditional price-coordination conclusions from certified cost intervals.

Pure standard-library arithmetic: no solver, file access, population adapter,
physical replay, or proof of caller-supplied premises. See
``doc/COORDINATION_CERTIFICATES.md``. This is complementary to PR #40's
price-conditioned participant settlement; it does not compute that settlement.

All loads are slot energy in kWh, all prices monetary_unit/kWh, and all costs
monetary_unit. Inputs may be exact strings, integers, Decimal or Fraction;
binary floats and booleans are rejected. Fraction operations are exact, so
there is no arithmetic rounding allowance. Uncertainty in the source evidence
must already be enclosed or supplied through ``absolute_error``.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction


Exact = str | int | Decimal | Fraction


def _exact(value: Exact, label: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal, Fraction)):
        raise ValueError(f"{label} must be an exact finite number, not a float or boolean")
    try:
        return Fraction(value)
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError(f"{label} must be an exact finite number") from exc


def _nonnegative(value: Exact, label: str) -> Fraction:
    result = _exact(value, label)
    if result < 0:
        raise ValueError(f"{label} must be nonnegative")
    return result


@dataclass(frozen=True)
class CostBounds:
    """An objective enclosure after widening both ends by absolute_error.

    The caller certifies the widened enclosure for the true objective. The
    allowance is in the same currency and may cover certified serialization,
    reconstruction or approximation errors; the helper cannot estimate them.
    """

    lower: Exact
    upper: Exact
    monetary_unit: str
    absolute_error: Exact = "0"

    def __post_init__(self) -> None:
        lo = _exact(self.lower, "lower")
        hi = _exact(self.upper, "upper")
        error = _nonnegative(self.absolute_error, "absolute_error")
        if lo > hi:
            raise ValueError("reversed objective bounds")
        if not isinstance(self.monetary_unit, str) or not self.monetary_unit.strip():
            raise ValueError("monetary_unit must be a nonempty label")
        object.__setattr__(self, "lower", lo)
        object.__setattr__(self, "upper", hi)
        object.__setattr__(self, "absolute_error", error)

    @property
    def enclosure(self) -> tuple[Fraction, Fraction]:
        return self.lower - self.absolute_error, self.upper + self.absolute_error


@dataclass(frozen=True)
class Premises:
    """Caller assertions, not authenticated evidence or verified model facts.

    The first three assertions are required for the gap/regret theorem.
    Physical attainment is required only for the zero-gap converse. The last
    two assertions are required only when price_error_per_kwh is positive.
    """

    common_complete_schedule_model: bool
    convex_differentiable_system_cost: bool
    certified_bounds_include_all_errors: bool
    physical_minimum_attained: bool = False
    price_error_at_same_physical_load: bool = False
    global_load_diameter_bound: bool = False

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if type(value) is not bool:
                raise ValueError(f"premise {name} must be a boolean")


@dataclass(frozen=True)
class CoordinationCertificate:
    """Conclusions conditional on all declared premises and input bounds.

    ``gap`` intersects ``raw_gap`` with the theorem's nonnegative half-line.
    ``regret_lower`` applies to EVERY physical schedule at its OWN gradient
    price. It is not the regret at a shared convex-hull settlement price.
    False exclusion/existence fields mean no corresponding conclusion.
    """

    raw_gap: tuple[Fraction, Fraction]
    gap: tuple[Fraction, Fraction]
    regret_lower: Fraction
    approximate_regret_ceiling: Fraction
    excludes_exact_equilibrium: bool
    excludes_approximate_equilibrium: bool
    establishes_exact_equilibrium: bool
    monetary_unit: str
    epsilon_cost: Fraction
    price_error_per_kwh: Fraction
    load_diameter_kwh: Fraction
    premises: Premises


def coordination_certificate(
    dictator: CostBounds,
    convexified: CostBounds,
    *,
    premises: Premises,
    epsilon_cost: Exact = "0",
    price_error_per_kwh: Exact = "0",
    load_diameter_kwh: Exact = "0",
) -> CoordinationCertificate:
    """Derive an interval for Δ and exclusions at ε + η D_1.

    The objectives refer to the SAME complete physical feasible schedule set,
    costs and loads: z_D=inf_s(c_s+F(L_s)); z_CH=inf_conv(c+F(L)).
    A feasible restricted mixture suffices for the convexified upper bound,
    but a restricted-master optimum is not generally a lower bound.

    Epsilon bounds private-objective regret at the posted price. Eta bounds
    infinity-norm price error relative to ∇F at that SAME realized load, and
    D_1 bounds the one-norm load diameter over the ENTIRE feasible set.
    Exclusion uses a strict comparison, with no tolerance-based equality.
    """
    if not isinstance(dictator, CostBounds) or not isinstance(convexified, CostBounds):
        raise ValueError("both objectives must be CostBounds")
    if not isinstance(premises, Premises):
        raise ValueError("premises must be supplied explicitly")
    required = (
        "common_complete_schedule_model",
        "convex_differentiable_system_cost",
        "certified_bounds_include_all_errors",
    )
    missing = [name for name in required if not getattr(premises, name)]
    if missing:
        raise ValueError("unestablished theorem premises: " + ", ".join(missing))
    if dictator.monetary_unit != convexified.monetary_unit:
        raise ValueError("objective monetary units differ; convert bounds explicitly")
    epsilon = _nonnegative(epsilon_cost, "epsilon_cost")
    eta = _nonnegative(price_error_per_kwh, "price_error_per_kwh")
    diameter = _nonnegative(load_diameter_kwh, "load_diameter_kwh")
    if eta > 0 and not (
        premises.price_error_at_same_physical_load
        and premises.global_load_diameter_bound
    ):
        raise ValueError("approximate price requires same-load error and global diameter premises")
    ld, ud = dictator.enclosure
    lc, uc = convexified.enclosure
    raw = (ld - uc, ud - lc)
    if raw[1] < 0:
        raise ValueError("negative upper gap contradicts the declared relaxation premises")
    gap = (max(Fraction(0), raw[0]), raw[1])
    ceiling = epsilon + eta * diameter
    return CoordinationCertificate(
        raw_gap=raw,
        gap=gap,
        regret_lower=gap[0],
        approximate_regret_ceiling=ceiling,
        excludes_exact_equilibrium=gap[0] > 0,
        excludes_approximate_equilibrium=gap[0] > ceiling,
        establishes_exact_equilibrium=(gap[1] == 0 and premises.physical_minimum_attained),
        monetary_unit=dictator.monetary_unit,
        epsilon_cost=epsilon,
        price_error_per_kwh=eta,
        load_diameter_kwh=diameter,
        premises=premises,
    )
