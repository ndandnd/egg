"""End-to-end smoke test on a tiny synthetic instance (CBC-solvable in
seconds). Run from src/: python -m pytest tests/ -q"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from egglab.boundary import sweep_slot
from egglab.evsp import validate_solution
from egglab.instance import synthetic_instance
from egglab.loops import taker_fixed_point
from egglab.market import make_affine_market
from egglab.regimes import (
    evaluate,
    solve_dictator,
    solve_strategic,
    solve_taker,
    solve_uncontrolled,
)


@pytest.fixture(scope="module")
def inst():
    return synthetic_instance(seed=0, n_trips=6, max_vehicles=3)


@pytest.fixture(scope="module")
def market(inst):
    return make_affine_market(inst, shape="duck", b_scale=0.01)


def test_taker_solves_and_validates(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, posted)
    assert sol.stats.status in ("OPTIMAL",)
    assert sol.fleet >= 1
    covered = sorted(t for seq in sol.sequences for t in seq)
    assert covered == sorted(t.id for t in inst.trips)
    errs = validate_solution(inst, sol)
    assert errs == [], errs
    # charging must be material for the price-response questions to bite
    assert sol.energy_charged_kwh > 1.0, "instance requires no charging"
    # statistics contract
    assert sol.stats.lp_obj is not None
    assert sol.stats.obj is not None
    assert sol.stats.n_int > 0


def test_regime_ladder(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    sols = {
        "uncontrolled": solve_uncontrolled(inst, market),
        "taker": solve_taker(inst, posted),
        "strategic": solve_strategic(inst, market, n_seg=12),
        "dictator": solve_dictator(inst, market, n_seg=12),
    }
    for name, sol in sols.items():
        errs = validate_solution(inst, sol)
        assert errs == [], (name, errs)
    ev = {k: evaluate(inst, s, market) for k, s in sols.items()}
    # with adaptive certification the dominance tolerances are the certified
    # gaps (default 1e-2), not PWL guesswork
    tol = 2e-2
    for name in ("uncontrolled", "taker", "strategic"):
        assert ev["dictator"]["total_system"] <= ev[name]["total_system"] + tol, (
            name,
            ev[name]["total_system"],
            ev["dictator"]["total_system"],
        )
    for name in ("uncontrolled", "taker", "dictator"):
        assert ev["strategic"]["total_private"] <= ev[name]["total_private"] + tol, (
            name,
            ev[name]["total_private"],
            ev["strategic"]["total_private"],
        )


def test_loop_and_checkpoint(inst, market, tmp_path):
    out = str(tmp_path / "loop")
    state = taker_fixed_point(
        inst, market, alpha=1.0, max_iters=3, out_dir=out, tag="t"
    )
    assert state["iter"] >= 1
    assert os.path.exists(os.path.join(out, "t.jsonl"))
    # resuming a finished run is a no-op
    state2 = taker_fixed_point(
        inst, market, alpha=1.0, max_iters=3, out_dir=out, tag="t"
    )
    assert state2["done"] == state["done"]


def test_boundary_sweep(inst, market, tmp_path):
    out = str(tmp_path / "sweep")
    base = market.price(np.zeros(market.n_slots))
    state = sweep_slot(inst, base, slot=10, deltas=[-0.5, 0.0, 0.5], out_dir=out, tag="s")
    assert state["done"] and len(state["points"]) == 3
    assert "n_switches" in state
