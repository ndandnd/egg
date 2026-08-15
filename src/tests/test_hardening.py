"""Acceptance tests for the Phase 1/2 correctness hardening (reviewer spec)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from egglab.boundary import classify_pair, sweep_slot
from egglab.evsp import Solution, solve_fixed_sequences, validate_solution
from egglab.instance import synthetic_instance
from egglab.loops import detect_outcome, taker_fixed_point
from egglab.market import make_affine_market
from egglab.records import make_record
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


# --- detection correctness (pure-function) --------------------------------
def test_repeated_loads_with_moving_prices_not_fixed_point():
    # prices still moving (residual > tol) although the response repeated
    hist = [[1.0, 2.0]]
    p_curr = [1.5, 2.5]
    p_next = [1.75, 2.75]  # residual 0.25 > tol
    assert detect_outcome(hist, p_curr, p_next, tol_price=1e-4) is None


def test_aba_responses_with_different_prices_not_cycle():
    # state trajectory p0, p1, p2 all distinct: no state recurrence, even if
    # the fleet's response alternated A-B-A along the way
    hist = [[1.0, 2.0], [3.0, 1.0]]
    p_curr = [2.0, 1.5]  # differs from both history states
    p_next = [2.5, 1.2]
    assert detect_outcome(hist, p_curr, p_next, tol_price=1e-4) is None


def test_true_fixed_point_detected():
    out = detect_outcome([[0.5, 0.5]], [1.0, 1.0], [1.0 + 1e-6, 1.0], tol_price=1e-4)
    assert out and out["type"] == "fixed_point"


def test_true_cycle_detected():
    # p_curr recurs state j=0 (two steps back) -> 2-cycle
    hist = [[1.0, 2.0], [2.0, 1.0]]
    out = detect_outcome(hist, [1.0, 2.0], [2.0, 1.0], tol_price=1e-4)
    assert out and out["type"] == "cycle" and out["length"] == 2


def test_immediate_predecessor_not_cycle():
    # p_curr equals only the immediate predecessor state: that is
    # convergence (handled by the fixed-point test), never a cycle
    hist = [[5.0], [1.0]]
    out = detect_outcome(hist, [1.0], [3.0], tol_price=1e-4)
    assert out is None


# --- hash normalization -----------------------------------------------------
def test_negative_zero_hashes_equal():
    a = Solution(sequences=[["t0"]], arc_kinds=[[]], charges=[], load=[0.0, 1.23])
    b = Solution(sequences=[["t0"]], arc_kinds=[[]], charges=[], load=[-0.0, 1.23])
    assert a.load_hash() == b.load_hash()


# --- adaptive convex approximation ------------------------------------------
def test_adaptive_gap_certified(inst, market):
    tol = 1e-2
    for solver in (solve_strategic, solve_dictator):
        sol = solver(inst, market, n_seg=4, tol_abs=tol)  # coarse start on purpose
        ex = sol.stats.extra
        assert ex["adaptive_converged"], ex
        assert ex["adaptive_gap_abs"] <= tol + 1e-9
        assert ex["adaptive_ub"] >= ex["adaptive_lb"] - 1e-9
        assert sol.obj_true == pytest.approx(ex["adaptive_ub"])


def test_dictator_dominates_in_true_system_cost(inst, market):
    tol = 1e-2
    posted = market.price(np.zeros(market.n_slots))
    sols = {
        "uncontrolled": solve_uncontrolled(inst, market),
        "taker": solve_taker(inst, posted),
        "strategic": solve_strategic(inst, market, tol_abs=tol),
        "dictator": solve_dictator(inst, market, tol_abs=tol),
    }
    ev = {k: evaluate(inst, s, market) for k, s in sols.items()}
    for name in ("uncontrolled", "taker", "strategic"):
        assert (
            ev["dictator"]["total_system"] <= ev[name]["total_system"] + tol + 1e-6
        ), (name, ev[name]["total_system"], ev["dictator"]["total_system"])


# --- replay validation in records -------------------------------------------
def test_records_carry_replay_status(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, posted)
    rec = make_record("test", inst, sol, market=market, prices=posted, regime="taker")
    assert rec["replay_ok"] is True
    assert rec["replay_violations"] == []
    assert rec["obj_true"] == pytest.approx(rec["obj_model"])


# --- fixed-sequence oracle and margin machinery ------------------------------
def test_fixed_sequence_rerealization(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, posted)
    re = solve_fixed_sequences(inst, sol.sequences, ("linear", posted))
    assert re is not None
    assert re.obj_model <= sol.obj_model + 1e-6  # same partition: can't be worse
    assert validate_solution(inst, re) == []


def test_classify_pair_kinds():
    a = dict(schedule_hash="A", load_hash="x", load=[10.0, 0.0], fleet=2,
             delta=0.0, load_slot=10.0, obj=100.0)
    b_tie = dict(a, schedule_hash="B")  # same load: degenerate tie
    sw = classify_pair(a, b_tie)
    assert sw["kind"] == "degenerate_tie"
    b_chg = dict(a, load_hash="y", load=[0.0, 10.0], load_slot=0.0)
    assert classify_pair(a, b_chg)["kind"] == "charging_only"
    b_duty = dict(b_chg, schedule_hash="B")
    assert classify_pair(a, b_duty)["kind"] == "duty_change"
    b_fleet = dict(b_duty, fleet=3)
    assert classify_pair(a, b_fleet)["kind"] == "fleet_change"


def test_sweep_with_margin_tests(inst, market, tmp_path):
    base = market.price(np.zeros(market.n_slots))
    state = sweep_slot(
        inst, base, slot=10, deltas=[-0.6, 0.0, 0.6],
        out_dir=str(tmp_path), tag="s", run_margin_tests=True,
    )
    assert state["done"]
    assert "counts_by_kind" in state and "n_economic_switches" in state
    for s in state["switches"]:
        assert s["kind"] in ("degenerate_tie", "charging_only", "duty_change", "fleet_change")


# --- loop end-to-end with state detection ------------------------------------
def test_loop_price_state_outcome(inst, market, tmp_path):
    state = taker_fixed_point(
        inst, market, alpha=0.5, max_iters=25, out_dir=str(tmp_path), tag="l"
    )
    assert state["done"]
    assert state["outcome"]["type"] in ("fixed_point", "cycle", "max_iters")
    # price history is fully stored
    assert len(state["price_history"]) == state["iter"]
