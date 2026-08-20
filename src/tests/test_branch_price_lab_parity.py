"""Mandatory drift guard for the duplicated direct-Gurobi fleet MILP.

Every burned seed below 16 and every positive size n<=4 is checked.  These
are tiny unit fixtures, not an experiment population or campaign.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.b2a2 import B2A2Error, canonicalize_pricing_solution
from egglab.branch_price_lab import (
    _solve_full_fleet_oracle,
    gurobi_runtime_available,
    solve_tree,
)
from egglab.enumerate_tiny import (
    PWL_TOL as ENUM_PWL_TOL,
    enumerated_ch,
    enumerated_dictator,
)
from egglab.evsp import validate_solution
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator, solve_taker


pytestmark = pytest.mark.skipif(
    not gurobi_runtime_available(),
    reason="optional licensed Gurobi runtime is unavailable",
)

EPSILON = 1e-2
PWL_TOL = 1e-4
FIXTURES = [
    pytest.param(seed, n_trips, id=f"s{seed}-n{n_trips}")
    for seed in range(16)
    for n_trips in range(1, 5)
]


def _instance(seed, n_trips):
    return synthetic_instance(
        seed=seed,
        n_trips=n_trips,
        max_vehicles=max(1, (n_trips + 1) // 2),
    )


def _price_vectors(inst):
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    return {
        "zero": np.zeros(inst.n_slots),
        "posted-duck": market.price(np.zeros(inst.n_slots)),
        "alternating-ramp": np.asarray(
            [0.2 + 0.07 * t + 0.4 * (t % 2) for t in range(inst.n_slots)]
        ),
    }


def _canonical_taker(inst, prices):
    try:
        solution = solve_taker(inst, prices, max_mip_gap=1e-9)
    except RuntimeError as exc:
        assert "INFEASIBLE" in str(exc)
        return None
    canonicalize_pricing_solution(inst, solution, prices)
    assert validate_solution(inst, solution) == []
    return solution


@pytest.mark.parametrize("seed,n_trips", FIXTURES)
def test_linear_taker_formulation_parity(seed, n_trips):
    inst = _instance(seed, n_trips)
    for label, prices in _price_vectors(inst).items():
        canonical = _canonical_taker(inst, prices)
        direct = _solve_full_fleet_oracle(
            inst,
            prices,
            [],
            call_id=f"parity-s{seed}-n{n_trips}-{label}",
            mip_gap=1e-9,
        )
        direct_feasible = direct["solver"]["status"] == "OPTIMAL"
        assert direct_feasible == (canonical is not None)
        if canonical is None:
            assert direct["solver"]["status"] == "INFEASIBLE"
            assert direct["infeasibility_certified"]
            continue
        assert direct["replay_ok"]
        allowance = (
            direct["tolerance_evidence"]["pricing_bound_allowance"] + 1e-6
        )
        assert direct["physical_objective"] == pytest.approx(
            canonical.obj_true, abs=allowance
        )


def _try_enumeration(inst, market):
    try:
        return enumerated_ch(inst, market), enumerated_dictator(inst, market)
    except B2A2Error as exc:
        assert (
            "infeasible" in str(exc)
            or "no feasible structure" in str(exc)
        )
        return None


def _try_compact_dictator(inst, market):
    try:
        return solve_dictator(
            inst, market, tol_abs=EPSILON, max_mip_gap=1e-9
        )
    except RuntimeError as exc:
        assert "INFEASIBLE" in str(exc)
        return None


@pytest.mark.parametrize("seed,n_trips", FIXTURES)
def test_convex_master_dictator_enumeration_parity(
    seed, n_trips, tmp_path
):
    inst = _instance(seed, n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    enumeration = _try_enumeration(inst, market)
    compact = _try_compact_dictator(inst, market)
    tree = solve_tree(
        inst,
        market,
        str(tmp_path),
        epsilon=EPSILON,
        pwl_tol=PWL_TOL,
    )
    tree_feasible = tree["outcome"]["status"] == "optimal"

    assert tree_feasible == (enumeration is not None)
    assert tree_feasible == (compact is not None)
    if not tree_feasible:
        assert tree["nodes"]["n0000"]["lp_outcome"]["status"] == "infeasible"
        return

    enum_ch, enum_d = enumeration
    root = tree["nodes"]["n0000"]["lp_outcome"]
    assert root["lower_bound"] - ENUM_PWL_TOL <= enum_ch["z_ch"]
    assert enum_ch["z_ch"] <= root["upper_bound"] + ENUM_PWL_TOL

    compact_lower = compact.stats.extra["adaptive_lb"]
    assert compact_lower - ENUM_PWL_TOL <= enum_d["z_d"]
    assert enum_d["z_d"] <= compact.obj_true + ENUM_PWL_TOL
    assert tree["outcome"]["global_bound"] - ENUM_PWL_TOL <= enum_d["z_d"]
    assert enum_d["z_d"] <= (
        tree["outcome"]["incumbent_upper_bound"] + ENUM_PWL_TOL
    )


def test_seed11_n4_every_formulation_agrees_on_infeasibility(tmp_path):
    inst = _instance(seed=11, n_trips=4)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)

    for prices in _price_vectors(inst).values():
        assert _canonical_taker(inst, prices) is None
        direct = _solve_full_fleet_oracle(
            inst,
            prices,
            [],
            call_id="seed11-n4-infeasible",
            mip_gap=1e-9,
        )
        assert direct["solver"]["status"] == "INFEASIBLE"
        assert direct["infeasibility_certified"]

    assert _try_enumeration(inst, market) is None
    assert _try_compact_dictator(inst, market) is None
    tree = solve_tree(inst, market, str(tmp_path))
    assert tree["outcome"]["status"] == "infeasible"
