"""Acceptance battery for B2-A2 certified column generation, anchored by the
tiny complete-enumeration gate (doc/MEASUREMENT_RESULTS.md Section 8)."""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import egglab.b2a2 as b2a2_mod
from egglab import checkpoint
from egglab.b2a2 import B2A2Error, PWL_TOL, certified_cg, column_from_solution
from egglab.enumerate_tiny import (
    PWL_TOL as ENUM_TOL,
    enumerate_structures,
    enumerated_ch,
    enumerated_dictator,
)
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator, solve_taker
from experiments.audit_runs import audit
from experiments.run_b2a2_pilot import BUDGET, EPSILON, build_cells

TOL_D = 1e-3  # dictator tolerance used in this battery
SLACK = PWL_TOL + ENUM_TOL + 1e-6  # combined upper-evaluation slack


@pytest.fixture(scope="module")
def tiny():
    inst = synthetic_instance(seed=1, n_trips=4, max_vehicles=2)
    market = make_affine_market(inst, shape="duck", b_scale=0.01)
    return inst, market


@pytest.fixture(scope="module")
def enum_truth(tiny):
    inst, market = tiny
    return enumerated_ch(inst, market), enumerated_dictator(inst, market)


@pytest.fixture(scope="module")
def dictator(tiny):
    inst, market = tiny
    return solve_dictator(inst, market, tol_abs=TOL_D)


@pytest.fixture(scope="module")
def cg_run(tiny, dictator, tmp_path_factory):
    inst, market = tiny
    out = str(tmp_path_factory.mktemp("cg"))
    state = certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                         tag="t", z_d_ub=dictator.obj_true, tol_d=TOL_D)
    return state, out


# --------------------------------------------------------------------------
# tiny complete-enumeration gate (requirement 8)
# --------------------------------------------------------------------------
def test_enumeration_is_complete(tiny):
    inst, _ = tiny
    structures = enumerate_structures(inst)
    assert len(structures) > 1
    # every structure covers all trips exactly once
    ids = sorted(t.id for t in inst.trips)
    for s in structures:
        assert sorted(t for seq in s["sequences"] for t in seq) == ids


def test_a2_terminates_at_enumerated_zch(cg_run, enum_truth):
    (state, _), (ch, _) = cg_run, enum_truth
    oc = state["outcome"]
    assert oc["type"] == "certified" and oc["certified"]
    assert oc["gap"] <= 1e-2
    # both UB_CH and z_ch_enum are exact evaluations of feasible points with
    # bounded model slack: they must agree within the combined slack + epsilon
    assert abs(oc["ub_ch"] - ch["z_ch"]) <= SLACK + 1e-2


def test_bounds_bracket_enumerated_zch_every_iteration(cg_run, enum_truth):
    (state, _), (ch, _) = cg_run, enum_truth
    z = ch["z_ch"]
    for lb in state["lb_history"]:
        assert lb <= z + SLACK, (lb, z)
    for ub in state["ub_history"]:
        assert ub >= z - SLACK, (ub, z)


def test_pricing_exhaustion_closes_gap(tiny, tmp_path):
    inst, market = tiny
    state = certified_cg(inst, market, epsilon=5e-4, budget=200,
                         out_dir=str(tmp_path), tag="x", pwl_tol=1e-5)
    oc = state["outcome"]
    assert oc["type"] == "certified"
    assert oc["gap"] <= 5e-4  # LB_CH = UB_CH within tolerance at exhaustion


def test_integer_master_reproduces_dictator(enum_truth, dictator):
    _, dd = enum_truth
    assert abs(dd["z_d"] - dictator.obj_true) <= TOL_D + ENUM_TOL + 1e-6


def test_uplift_interval_contains_enumerated(cg_run, enum_truth):
    (state, _), (ch, dd) = cg_run, enum_truth
    lo, hi = state["outcome"]["uplift_interval"]
    true_uplift = dd["z_d"] - ch["z_ch"]
    assert lo - SLACK <= true_uplift <= hi + SLACK, (lo, true_uplift, hi)
    assert hi >= lo


def test_reduced_cost_sign_and_lb_formula(cg_run):
    state, out = cg_run
    recs = [json.loads(l) for l in open(os.path.join(out, "t.iterations.jsonl"))]
    assert recs
    improving = 0
    for r in recs:
        # LB formula: lb_ch == z_rmp_model + min(0, min_reduced_cost)
        assert r["lb_ch"] == pytest.approx(
            r["z_rmp_model"] + min(0.0, r["min_reduced_cost"]), abs=1e-9)
        if r["min_reduced_cost"] < -1e-6:
            improving += 1
    assert improving >= 1  # pricing found improving columns (sign is right)
    # oracle prices p = -pi are economically sensible at the end:
    # nonnegative everywhere (zero only on unused slots, where the PWL
    # marginal cost prices at 0) and strictly positive at the maximum
    last = recs[-1]
    assert last["oracle_prices_min"] >= 0.0
    assert last["oracle_prices_max"] > 0.0
    assert last["certificate_gap"] <= 1e-2


def test_ub_nonincreasing_and_lb_nondecreasing(cg_run):
    state, _ = cg_run
    ub, lb = state["ub_history"], state["lb_history"]
    for a, b in zip(ub, ub[1:]):
        assert b <= a + PWL_TOL + 1e-6
    for a, b in zip(lb, lb[1:]):
        assert b >= a - 1e-9


# --------------------------------------------------------------------------
# safety failures (requirement 8, tail)
# --------------------------------------------------------------------------
def test_duplicate_negative_rc_fails_safely(tiny, tmp_path, monkeypatch):
    inst, market = tiny
    real = solve_taker(inst, market.price(np.zeros(market.n_slots)))

    def fake_solve(_inst, _prices, **kw):
        sol = copy.deepcopy(real)
        sol.obj_model = -1e6  # forces a hugely negative reduced cost
        return sol

    monkeypatch.setattr(b2a2_mod, "solve_taker", fake_solve)
    with pytest.raises(B2A2Error, match="duplicate column"):
        certified_cg(inst, market, epsilon=1e-9, budget=30,
                     out_dir=str(tmp_path), tag="d")


def test_replay_invalid_fails_loudly(tiny, tmp_path, monkeypatch):
    inst, market = tiny
    monkeypatch.setattr(b2a2_mod, "validate_solution",
                        lambda *_a, **_k: ["deliberate violation"])
    with pytest.raises(B2A2Error, match="replay-invalid"):
        certified_cg(inst, market, epsilon=1e-2, budget=5,
                     out_dir=str(tmp_path), tag="r")


def test_non_optimal_fails_loudly(tiny, tmp_path, monkeypatch):
    inst, market = tiny
    real_solve = b2a2_mod.solve_taker

    def degraded(_inst, prices, **kw):
        sol = real_solve(_inst, prices, **kw)
        sol.stats.status = "TIME_LIMIT"
        return sol

    monkeypatch.setattr(b2a2_mod, "solve_taker", degraded)
    with pytest.raises(B2A2Error, match="OPTIMAL"):
        certified_cg(inst, market, epsilon=1e-2, budget=5,
                     out_dir=str(tmp_path), tag="n")


def test_checkpoint_resume_preserves_columns_and_bounds(tiny, dictator, tmp_path,
                                                        monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_solve = b2a2_mod.solve_taker
    calls = {"n": 0}

    def preempting(_inst, prices, **kw):
        calls["n"] += 1
        if calls["n"] == 4:  # simulate preemption during the 4th oracle solve
            raise KeyboardInterrupt("simulated preemption")
        return real_solve(_inst, prices, **kw)

    monkeypatch.setattr(b2a2_mod, "solve_taker", preempting)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out, tag="p")
    ck = checkpoint.load(os.path.join(out, "p.cg.ckpt.json"))
    assert ck is not None and not ck["done"]
    cols_before = len(ck["columns"])
    assert ck["oracle_calls"] == 3  # completed calls only

    monkeypatch.setattr(b2a2_mod, "solve_taker", real_solve)
    state = certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                         tag="p", z_d_ub=dictator.obj_true, tol_d=TOL_D)
    assert state["outcome"]["type"] == "certified"
    assert len(state["columns"]) >= cols_before  # nothing lost
    ub = state["ub_history"]
    for a, b in zip(ub, ub[1:]):
        assert b <= a + PWL_TOL + 1e-6  # bounds sane across the resume


def test_bound_corruption_detected(tiny, tmp_path, monkeypatch):
    inst, market = tiny
    out = str(tmp_path)
    real_solve = b2a2_mod.solve_taker
    calls = {"n": 0}

    def preempting(_inst, prices, **kw):
        calls["n"] += 1
        if calls["n"] == 3:
            raise KeyboardInterrupt("simulated preemption")
        return real_solve(_inst, prices, **kw)

    monkeypatch.setattr(b2a2_mod, "solve_taker", preempting)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out, tag="c")
    monkeypatch.setattr(b2a2_mod, "solve_taker", real_solve)
    ckp = os.path.join(out, "c.cg.ckpt.json")
    ck = checkpoint.load(ckp)
    ck["lb_best"] = (min(ck["ub_history"]) if ck["ub_history"] else 0.0) + 100.0
    checkpoint.save(ckp, ck)
    with pytest.raises(B2A2Error, match="corrupt checkpoint"):
        certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out, tag="c")


def test_column_requires_valid_optimal_solution(tiny):
    inst, market = tiny
    sol = solve_taker(inst, market.price(np.zeros(market.n_slots)))
    col = column_from_solution(inst, sol)
    assert col["replay_ok"] and col["column_key"]
    bad = copy.deepcopy(sol)
    bad.charges[0]["kwh"] = 0.0
    with pytest.raises(B2A2Error, match="replay-invalid"):
        column_from_solution(inst, bad)


# --------------------------------------------------------------------------
# pilot driver and audit gate (requirements 9-11)
# --------------------------------------------------------------------------
def test_pilot_list_is_exactly_the_spec():
    cells = build_cells()
    assert len(cells) == 12
    assert cells == [(s, n, b) for s in (0, 11, 15) for n in (8, 12)
                     for b in (0.01, 0.05)]
    assert EPSILON == 1e-2 and BUDGET == 240


def test_audit_cg_gate(cg_run, tmp_path):
    state, out = cg_run
    # a passing root: the finished cg checkpoint + minimal records file
    root = str(tmp_path / "root")
    os.makedirs(root, exist_ok=True)
    ck = checkpoint.load(os.path.join(out, "t.cg.ckpt.json"))
    checkpoint.save(os.path.join(root, "cell_a", "a2.cg.ckpt.json"), ck)
    with open(os.path.join(root, "r.jsonl"), "w") as f:
        f.write(json.dumps({"experiment": "t", "replay_ok": True,
                            "solver": {"backend": "GRB", "status": "OPTIMAL",
                                       "wall_s": 1.0}}) + "\n")
    _, ok, problems = audit(root, expect_cg=1)
    assert ok, problems
    # absent checkpoint fails the gate
    _, ok2, problems2 = audit(root, expect_cg=2)
    assert not ok2 and any("cg: 1/2 complete" in p for p in problems2)
    # corrupted bound history fails sanity
    bad = json.loads(json.dumps(ck))
    bad["ub_history"] = [1.0, 5.0]  # UB increased
    checkpoint.save(os.path.join(root, "cell_b", "a2.cg.ckpt.json"), bad)
    _, ok3, problems3 = audit(root, expect_cg=2)
    assert not ok3 and any("UB increased" in p for p in problems3)
