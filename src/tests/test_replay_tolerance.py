"""Regression tests for the Unicorn replay-validation incident (2026-08-15).

Jobs 51417 (phase 1) and 51831 (boundary) failed replay with messages like
`terminal SOC 6.00 < 6.0`: extracted charges/loads were rounded to 6 decimals
before the independent replay, while replay used a 1e-6 kWh tolerance;
rounding and solver feasibility residuals accumulated along vehicle chains.
Fix: full-precision extraction everywhere + one documented audit tolerance
REPLAY_TOL_KWH = 1e-4 kWh (0.1 Wh) + diagnostic error messages.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from egglab.evsp import REPLAY_TOL_KWH, validate_solution
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_taker, solve_uncontrolled


@pytest.fixture(scope="module")
def inst():
    return synthetic_instance(seed=0, n_trips=6, max_vehicles=3)


@pytest.fixture(scope="module")
def market(inst):
    return make_affine_market(inst, shape="duck", b_scale=0.01)


@pytest.fixture(scope="module")
def sol(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    s = solve_taker(inst, posted)
    assert s.charges, "test instance must require charging"
    return s


def _shortfall(sol, delta):
    """Reduce the LAST charge event (by slot) of a charging vehicle by delta.
    At optimality some downstream SOC constraint is solver-tight, so the
    shortfall propagates to a bound with ~zero slack."""
    s = copy.deepcopy(sol)
    veh = s.charges[0]["vehicle"]
    ev = [c for c in s.charges if c["vehicle"] == veh]
    c = max(ev, key=lambda c: c["slot"])
    c["kwh"] -= delta
    return s


def test_replay_tolerance_constant():
    assert REPLAY_TOL_KWH == pytest.approx(1e-4)


def test_tiny_shortfall_accepted(inst, sol):
    # 5e-5 kWh < 1e-4 kWh tolerance: must be accepted
    errs = validate_solution(inst, _shortfall(sol, 5e-5))
    assert errs == [], errs


def test_material_shortfall_rejected_with_diagnostics(inst, sol):
    # 1e-3 kWh > tolerance: must be rejected, with full diagnostics
    errs = validate_solution(inst, _shortfall(sol, 1e-3))
    assert errs, "1e-3 kWh shortfall must be rejected"
    text = " | ".join(errs)
    assert "actual=" in text
    assert "required>=" in text or "required<=" in text
    assert "shortfall=" in text or "excess=" in text
    assert "tol=1.0e-04" in text


def test_old_rounding_now_within_tolerance(inst, sol):
    # the incident scenario: 6-decimal rounding of every charge must not
    # trip the audit under the documented tolerance
    s = copy.deepcopy(sol)
    for c in s.charges:
        c["kwh"] = round(c["kwh"], 6)
    assert validate_solution(inst, s) == []


def test_genuine_violation_still_caught(inst, sol):
    # tolerance must not mask real infeasibility: remove a whole charge event
    s = copy.deepcopy(sol)
    kwh = s.charges[0]["kwh"]
    if kwh > 2 * REPLAY_TOL_KWH:
        s.charges[0]["kwh"] = 0.0
        assert validate_solution(inst, s), "removing a charge must be caught"


def test_solutions_replay_clean_at_full_precision(inst, market, sol):
    assert validate_solution(inst, sol) == []
    unc = solve_uncontrolled(inst, market)
    assert validate_solution(inst, unc) == []
    posted = market.price(np.zeros(market.n_slots))
    rec = make_record("test", inst, sol, market=market, prices=posted, regime="taker")
    assert rec["replay_ok"] is True
