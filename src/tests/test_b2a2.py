"""Acceptance battery for B2-A2 certified column generation, anchored by the
tiny complete-enumeration gate (doc/MEASUREMENT_RESULTS.md Section 8), plus
the adversarial batteries for MILP-bound accounting, transactional logging,
checkpoint identity, column identity, and audit strengthening."""
import copy
import json
import math
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import egglab.b2a2 as b2a2_mod
import egglab.evsp as evsp_mod
import egglab.records as records_mod
import egglab.regimes as regimes_mod
from egglab import checkpoint
from egglab.b2a2 import (
    B2A2Error,
    PWL_TOL,
    canonicalize_pricing_solution,
    certified_cg,
    column_from_solution,
    column_key,
    pricing_incumbent,
    solve_rmp,
)
from egglab.enumerate_tiny import (
    PWL_TOL as ENUM_TOL,
    enumerate_structures,
    enumerated_ch,
    enumerated_dictator,
)
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator, solve_taker
from egglab.solver import SolveStats
import experiments.run_b2a2_pilot as pilot_mod
from experiments.audit_runs import audit
from experiments.run_b2a2_pilot import BUDGET, EPSILON, build_cells, run_cell

TOL_D = 1e-3  # dictator tolerance used in this battery
SLACK = PWL_TOL + ENUM_TOL + 1e-6  # combined upper-evaluation slack

VOLATILE_KEYS = {
    "timestamp", "host", "slurm_job_id", "slurm_array_job_id",
    "slurm_array_task_id",
    "slurm_restart_count", "wall_s", "lp_wall_s", "master_wall_s",
    "pricing_wall_s",
}


def test_provenance_records_slurm_array_parent(monkeypatch):
    monkeypatch.setenv("SLURM_ARRAY_JOB_ID", "424242")
    monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "17")
    record = records_mod.provenance()
    assert record["slurm_array_job_id"] == "424242"
    assert record["slurm_array_task_id"] == "17"


def _strip_volatile(obj):
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in obj.items()
                if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip_volatile(x) for x in obj]
    return obj


def _read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _reprice_physical_solution(sol, prices):
    """Keep a mocked oracle column/objective coherent at new prices."""
    value = float(sol.ops_cost + np.dot(np.asarray(prices, dtype=float),
                                        np.asarray(sol.load, dtype=float)))
    sol.obj_true = value
    sol.obj_model = value
    sol.stats.obj = value
    return sol


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


@pytest.fixture(scope="module")
def ref_run(tiny, tmp_path_factory):
    """Uninterrupted reference run for the transactional-logging battery."""
    inst, market = tiny
    out = str(tmp_path_factory.mktemp("ref"))
    state = certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                         tag="p")
    return state, out


# --------------------------------------------------------------------------
# tiny complete-enumeration gate (requirement 8)
# --------------------------------------------------------------------------
def test_enumeration_is_complete(tiny):
    inst, _ = tiny
    structures = enumerate_structures(inst)
    assert len(structures) > 1
    ids = sorted(t.id for t in inst.trips)
    for s in structures:
        assert sorted(t for seq in s["sequences"] for t in seq) == ids


def test_a2_terminates_at_enumerated_zch(cg_run, enum_truth):
    (state, _), (ch, _) = cg_run, enum_truth
    oc = state["outcome"]
    assert oc["type"] == "certified" and oc["certified"]
    assert oc["gap"] <= 1e-2
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
    recs = _read_jsonl(os.path.join(out, "t.iterations.jsonl"))
    assert recs
    improving = 0
    for r in recs:
        # LB formula uses the CERTIFIED pricing bound, never the incumbent
        assert r["lb_ch"] == pytest.approx(
            r["z_rmp_model"] + min(0.0, r["min_reduced_cost_lb"]), abs=1e-9)
        # bound accounting: certified bound <= incumbent, gap logged
        assert r["min_reduced_cost_lb"] <= r["min_reduced_cost_ub"] + 1e-9
        assert r["pricing_gap_abs"] >= -1e-9
        if r["min_reduced_cost_ub"] < -1e-6:
            improving += 1
    assert improving >= 1  # pricing found improving columns (sign is right)
    last = recs[-1]
    assert last["oracle_prices_min"] >= 0.0
    assert last["oracle_prices_max"] > 0.0
    assert last["certificate_gap"] <= 1e-2


def test_ub_nonincreasing_and_lb_nondecreasing(cg_run):
    state, _ = cg_run
    ub, lb = state["ub_history"], state["lb_history"]
    assert len(ub) == len(lb)
    for a, b in zip(ub, ub[1:]):
        assert b <= a + PWL_TOL + 1e-6
    for a, b in zip(lb, lb[1:]):
        assert b >= a - 1e-9


# --------------------------------------------------------------------------
# rigorous MILP-bound accounting (correction 1)
# --------------------------------------------------------------------------
def test_adaptive_bound_regression_old_calc_would_false_certify(monkeypatch):
    """obj != bound: the pre-fix calculation (lb = incumbent obj_model) would
    certify within tol; the corrected calculation (lb = certified dual bound)
    must not."""
    tol = 1e-2
    fake_sol = types.SimpleNamespace(
        ops_cost=0.0, load=[0.0], obj_model=10.0, obj_true=None,
        oracle_tier="",
        stats=SolveStats(backend="FAKE", status="OPTIMAL", obj=10.0,
                         bound=9.5))

    monkeypatch.setattr(regimes_mod, "solve_evsp",
                        lambda *_a, **_k: copy.deepcopy(fake_sol))
    sol = regimes_mod._solve_convex_adaptive(
        None, seg0=[[(0.0, 0.0)]], tangents_at=lambda L: [(0.0, 0.0)],
        true_energy_cost=lambda L: 10.005, label="test",
        tol_abs=tol, max_rounds=3)
    ex = sol.stats.extra
    # the OLD formula would have certified: ub - incumbent <= tol
    assert ex["adaptive_ub"] - ex["adaptive_model_obj"] <= tol
    # the corrected formula does not: ub - certified bound > tol
    assert ex["adaptive_lb"] == pytest.approx(9.5)
    assert ex["adaptive_gap_abs"] > tol
    assert ex["adaptive_converged"] is False


def test_adaptive_requires_finite_bound(monkeypatch):
    fake_sol = types.SimpleNamespace(
        ops_cost=0.0, load=[0.0], obj_model=10.0, obj_true=None,
        oracle_tier="",
        stats=SolveStats(backend="FAKE", status="OPTIMAL", obj=10.0,
                         bound=None))
    monkeypatch.setattr(regimes_mod, "solve_evsp",
                        lambda *_a, **_k: copy.deepcopy(fake_sol))
    with pytest.raises(RuntimeError, match="finite certified bound"):
        regimes_mod._solve_convex_adaptive(
            None, seg0=[[(0.0, 0.0)]], tangents_at=lambda L: [(0.0, 0.0)],
            true_energy_cost=lambda L: 10.0, label="test")


def test_pricing_bound_regression_no_false_exhaustion(tiny, tmp_path,
                                                      monkeypatch):
    """Pricing incumbent shows no improvement (rc_ub >> 0) while the
    certified bound stays hugely negative (rc_lb << 0). The pre-fix
    calculation LB = z_model + min(0, rc_ub) would have declared LB ~= z_model
    and false-certified; the corrected run keeps LB low, escalates the
    pricing gap, and fails loudly rather than certifying."""
    inst, market = tiny
    out = str(tmp_path)
    real_solve = b2a2_mod.solve_taker
    first = {}

    def fake_solve(_inst, prices, **kw):
        if "sol" not in first:
            first["sol"] = real_solve(_inst, prices, **kw)
            return first["sol"]
        sol = copy.deepcopy(first["sol"])
        _reprice_physical_solution(sol, prices)  # duplicate: no improvement
        sol.stats.bound = -1e12       # certified bound: cannot rule one out
        return sol

    monkeypatch.setattr(b2a2_mod, "solve_taker", fake_solve)
    with pytest.raises(B2A2Error, match="cannot certify exhaustion"):
        certified_cg(inst, market, epsilon=1e-2, budget=30,
                     out_dir=out, tag="g")
    ck = checkpoint.load(os.path.join(out, "g.cg.ckpt.json"))
    assert not ck["done"]
    assert ck["iteration_events"]
    for it in ck["iteration_events"]:
        # proof the OLD calculation would have false-certified here:
        assert it["min_reduced_cost_ub"] >= -b2a2_mod.RC_TOL
        assert it["ub_ch"] - it["z_rmp_model"] <= 1e-2
        # while the CORRECTED lower bound keeps the gap enormous:
        assert it["certificate_gap"] > 1e-2
        assert it["lb_ch"] < it["z_rmp_model"] - 1e6
    # escalation actually tightened the pricing gap setting
    assert ck["pricing_max_mip_gap"] < 1e-6


def test_pricing_requires_finite_bound(tiny, tmp_path, monkeypatch):
    inst, market = tiny
    real_solve = b2a2_mod.solve_taker

    def degraded(_inst, prices, **kw):
        sol = real_solve(_inst, prices, **kw)
        sol.stats.bound = None
        return sol

    monkeypatch.setattr(b2a2_mod, "solve_taker", degraded)
    with pytest.raises(B2A2Error, match="bound"):
        certified_cg(inst, market, epsilon=1e-2, budget=5,
                     out_dir=str(tmp_path), tag="f")


# --------------------------------------------------------------------------
# safety failures
# --------------------------------------------------------------------------
def test_inconsistent_pricing_objective_fails_safely(tiny):
    inst, market = tiny
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    sol.obj_true = -1e6
    with pytest.raises(B2A2Error, match="pricing objective/column mismatch"):
        pricing_incumbent(col, sol, prices)


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
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    assert col["replay_ok"] and col["column_key"]
    bad = copy.deepcopy(sol)
    bad.charges[0]["kwh"] = 0.0
    with pytest.raises(B2A2Error, match="replay-invalid"):
        column_from_solution(inst, bad)


def test_physical_load_reconstruction_repairs_holdout_residual(tiny):
    """Regression for Unicorn A6 holdout job 218143, seed 26/n8/b.05."""
    inst, _market = tiny
    raw = [0.0] * inst.n_slots
    raw[7] = -7.356248409800537e-06
    raw[8] = 45.40000735693806
    charges = [{"slot": 8, "kwh": 45.4}]
    stats = SolveStats(status="OPTIMAL")

    load = evsp_mod._physical_load_from_charges(inst, charges, raw, stats)

    assert load[7] == 0.0
    assert load[8] == 45.4
    assert min(load) >= 0.0
    evidence = stats.extra["load_reconstruction"]
    assert evidence["policy_version"] == 1
    assert evidence["raw_min_kwh"] == raw[7]
    assert evidence["max_abs_residual_kwh"] == pytest.approx(
        7.356938063196372e-06)


@pytest.mark.parametrize("bad", [-2e-4, float("nan"), float("inf")])
def test_physical_load_reconstruction_rejects_material_or_nonfinite(
        tiny, bad):
    inst, _market = tiny
    raw = [0.0] * inst.n_slots
    raw[0] = bad
    match = "nonfinite" if not math.isfinite(bad) else "disagrees"
    with pytest.raises(RuntimeError, match=match):
        evsp_mod._physical_load_from_charges(inst, [], raw, SolveStats())


def test_generic_taker_representation_is_not_changed_by_cg_policy(tiny):
    """The incident repair must not alter legacy Phase-1 resume semantics."""
    inst, market = tiny
    sol = solve_taker(inst, market.price(np.zeros(market.n_slots)))
    assert "load_reconstruction" not in sol.stats.extra
    assert sol.obj_true == sol.obj_model


def test_cg_pricing_load_matches_charge_events_and_physical_objective(tiny):
    inst, market = tiny
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    per_slot = [0.0] * inst.n_slots
    for charge in sol.charges:
        per_slot[charge["slot"]] += charge["kwh"]

    assert sol.load == per_slot
    assert min(sol.load) >= 0.0
    assert sol.obj_true == pytest.approx(
        sol.ops_cost + float(np.dot(prices, sol.load)))
    assert sol.stats.extra["load_reconstruction"]["policy_version"] == 1
    assert "pricing_objective_reconstruction" in sol.stats.extra


def test_pricing_incumbent_uses_physical_column_not_model_incumbent(tiny):
    inst, market = tiny
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    sol.obj_model = float(sol.obj_true) - 1.0

    got = pricing_incumbent(col, sol, prices)

    assert got == pytest.approx(sol.obj_true)
    assert got != pytest.approx(sol.obj_model)


@pytest.mark.parametrize("bad,match", [
    (-7.356248409800537e-06, "negative"),
    (float("nan"), "nonfinite"),
])
def test_rmp_rejects_nonphysical_checkpoint_column_before_backend(
        tiny, bad, match, monkeypatch):
    inst, market = tiny
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    col["load"][0] = bad
    monkeypatch.setattr(
        b2a2_mod, "new_model",
        lambda *_a, **_k: pytest.fail("backend must not be constructed"),
    )
    with pytest.raises(B2A2Error, match=match):
        solve_rmp(inst, market, [col], [])


def test_seed26_one_column_rmp_is_feasible_after_reconstruction():
    inst = synthetic_instance(seed=26, n_trips=8)
    market = make_affine_market(inst, shape="duck", b_scale=0.05)
    prices = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, prices)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)

    assert min(col["load"]) >= 0.0
    rmp = solve_rmp(inst, market, [col], [])
    assert rmp["lambdas"] == pytest.approx([1.0])
    assert min(rmp["L"]) >= -1e-12


# --------------------------------------------------------------------------
# transactional, idempotent preemption handling (correction 2)
# --------------------------------------------------------------------------
def _run_interrupted_then_resume(tiny, out, monkeypatch, fault):
    """Install `fault` (which raises KeyboardInterrupt at its trigger point),
    run until interrupted, remove the fault, resume to completion."""
    inst, market = tiny
    fault(monkeypatch)
    with pytest.raises(KeyboardInterrupt):
        certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out, tag="p")
    monkeypatch.undo()
    return certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                        tag="p")


def _assert_exactly_once_and_identical(out, ref_out, state, ref_state):
    oracle = _read_jsonl(os.path.join(out, "p.oracle.jsonl"))
    iters = _read_jsonl(os.path.join(out, "p.iterations.jsonl"))
    ref_oracle = _read_jsonl(os.path.join(ref_out, "p.oracle.jsonl"))
    ref_iters = _read_jsonl(os.path.join(ref_out, "p.iterations.jsonl"))
    ids = [r["extra"]["call_id"] for r in oracle]
    # no missing or duplicate call IDs, exactly the reference sequence
    assert len(ids) == len(set(ids))
    assert ids == [r["extra"]["call_id"] for r in ref_oracle]
    assert [r["iteration_id"] for r in iters] == \
        [r["iteration_id"] for r in ref_iters]
    # identical final records to the uninterrupted run (volatile stripped)
    assert _strip_volatile(oracle) == _strip_volatile(ref_oracle)
    assert _strip_volatile(iters) == _strip_volatile(ref_iters)
    assert state["outcome"]["ub_ch"] == pytest.approx(
        ref_state["outcome"]["ub_ch"], abs=1e-9)
    assert state["oracle_calls"] == ref_state["oracle_calls"]


def test_interrupt_after_solve_before_checkpoint(tiny, ref_run, tmp_path,
                                                 monkeypatch):
    ref_state, ref_out = ref_run
    out = str(tmp_path)

    def fault(mp):
        real_save = b2a2_mod.checkpoint.save
        n = {"v": 0}

        def dying_save(path, obj):
            n["v"] += 1
            if n["v"] == 3:  # commit of the 2nd pricing iteration
                raise KeyboardInterrupt("killed before checkpoint")
            return real_save(path, obj)

        mp.setattr(b2a2_mod.checkpoint, "save", dying_save)

    state = _run_interrupted_then_resume(tiny, out, monkeypatch, fault)
    _assert_exactly_once_and_identical(out, ref_out, state, ref_state)


def test_interrupt_after_checkpoint_before_materialization(tiny, ref_run,
                                                           tmp_path,
                                                           monkeypatch):
    ref_state, ref_out = ref_run
    out = str(tmp_path)

    def fault(mp):
        real_mat = b2a2_mod._materialize_logs
        n = {"v": 0}

        def dying_mat(state, oc_path, it_path):
            n["v"] += 1
            if n["v"] == 3:
                raise KeyboardInterrupt("killed before materialization")
            return real_mat(state, oc_path, it_path)

        mp.setattr(b2a2_mod, "_materialize_logs", dying_mat)

    state = _run_interrupted_then_resume(tiny, out, monkeypatch, fault)
    _assert_exactly_once_and_identical(out, ref_out, state, ref_state)


def test_interrupt_during_materialization(tiny, ref_run, tmp_path,
                                          monkeypatch):
    ref_state, ref_out = ref_run
    out = str(tmp_path)

    def fault(mp):
        real_write = b2a2_mod._atomic_write_lines
        n = {"v": 0}

        def dying_write(path, records):
            n["v"] += 1
            if n["v"] == 6:  # oracle log of it-2 written, iteration log not
                raise KeyboardInterrupt("killed mid-materialization")
            return real_write(path, records)

        mp.setattr(b2a2_mod, "_atomic_write_lines", dying_write)

    state = _run_interrupted_then_resume(tiny, out, monkeypatch, fault)
    _assert_exactly_once_and_identical(out, ref_out, state, ref_state)


def test_interrupt_after_materialization(tiny, ref_run, tmp_path, monkeypatch):
    ref_state, ref_out = ref_run
    out = str(tmp_path)

    def fault(mp):
        real_mat = b2a2_mod._materialize_logs
        n = {"v": 0}

        def dying_mat(state, oc_path, it_path):
            real_mat(state, oc_path, it_path)
            n["v"] += 1
            if n["v"] == 3:
                raise KeyboardInterrupt("killed after materialization")

        mp.setattr(b2a2_mod, "_materialize_logs", dying_mat)

    state = _run_interrupted_then_resume(tiny, out, monkeypatch, fault)
    _assert_exactly_once_and_identical(out, ref_out, state, ref_state)


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
        certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                     tag="q", z_d_ub=dictator.obj_true, tol_d=TOL_D)
    ck = checkpoint.load(os.path.join(out, "q.cg.ckpt.json"))
    assert ck is not None and not ck["done"]
    cols_before = len(ck["columns"])
    assert ck["oracle_calls"] == 3  # completed calls only

    monkeypatch.setattr(b2a2_mod, "solve_taker", real_solve)
    state = certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                         tag="q", z_d_ub=dictator.obj_true, tol_d=TOL_D)
    assert state["outcome"]["type"] == "certified"
    assert len(state["columns"]) >= cols_before  # nothing lost
    ub = state["ub_history"]
    for a, b in zip(ub, ub[1:]):
        assert b <= a + PWL_TOL + 1e-6  # bounds sane across the resume


# --------------------------------------------------------------------------
# checkpoint identity (correction 3)
# --------------------------------------------------------------------------
def test_identity_rejects_changed_market(tiny, cg_run, dictator):
    inst, _ = tiny
    _, out = cg_run
    other_market = make_affine_market(inst, shape="duck", b_scale=0.02)
    with pytest.raises(B2A2Error, match="identity mismatch.*market_hash"):
        certified_cg(inst, other_market, epsilon=1e-2, budget=60,
                     out_dir=out, tag="t", z_d_ub=dictator.obj_true,
                     tol_d=TOL_D)


def test_identity_rejects_changed_epsilon(tiny, cg_run, dictator):
    inst, market = tiny
    _, out = cg_run
    with pytest.raises(B2A2Error, match="identity mismatch.*epsilon"):
        certified_cg(inst, market, epsilon=5e-3, budget=60,
                     out_dir=out, tag="t", z_d_ub=dictator.obj_true,
                     tol_d=TOL_D)


def test_identity_rejects_changed_budget(tiny, cg_run, dictator):
    inst, market = tiny
    _, out = cg_run
    with pytest.raises(B2A2Error, match="identity mismatch.*budget"):
        certified_cg(inst, market, epsilon=1e-2, budget=61,
                     out_dir=out, tag="t", z_d_ub=dictator.obj_true,
                     tol_d=TOL_D)


def test_identity_rejects_stale_dictator(tiny, cg_run, dictator):
    inst, market = tiny
    _, out = cg_run
    with pytest.raises(B2A2Error, match="identity mismatch.*z_d_ub"):
        certified_cg(inst, market, epsilon=1e-2, budget=60,
                     out_dir=out, tag="t",
                     z_d_ub=dictator.obj_true + 1.0, tol_d=TOL_D)


def test_identity_accepts_exact_match(tiny, cg_run, dictator):
    inst, market = tiny
    state0, out = cg_run
    state = certified_cg(inst, market, epsilon=1e-2, budget=60, out_dir=out,
                         tag="t", z_d_ub=dictator.obj_true, tol_d=TOL_D)
    assert state["done"] and state["outcome"] == state0["outcome"]


def test_pilot_rejects_stale_dictator_checkpoint(tmp_path):
    cell = build_cells()[0]
    tag = f"s{cell[0]}_n{cell[1]}_b{cell[2]:g}"
    cell_dir = os.path.join(str(tmp_path), tag)
    checkpoint.save(os.path.join(cell_dir, "dictator.ckpt.json"),
                    {"identity": {"instance_hash": "stale",
                                  "market_hash": "stale", "tol_d": 1.0},
                     "z_d_ub": 0.0, "tol_d": 1.0})
    args = types.SimpleNamespace(out=str(tmp_path), mip_gap=1e-6)
    with pytest.raises(RuntimeError, match="stale dictator checkpoint"):
        run_cell(cell, args)


# --------------------------------------------------------------------------
# column identity (correction 4)
# --------------------------------------------------------------------------
def test_column_identity_includes_cost_and_full_precision():
    base = {"load": [1.0, 2.5, 0.0], "ops_cost": 100.0}
    same = {"load": [1.0, 2.5, 0.0], "ops_cost": 100.0}
    cheaper = {"load": [1.0, 2.5, 0.0], "ops_cost": 99.999999999}
    tiny_load_diff = {"load": [1.0, 2.5 + 1e-13, 0.0], "ops_cost": 100.0}
    k = column_key(base)
    assert len(k) == 64  # full SHA-256, not a prefix
    assert k == column_key(same)
    # identical loads with different operating costs must never collide
    assert k != column_key(cheaper)
    # full precision: no six-decimal rounding collisions
    assert k != column_key(tiny_load_diff)
    # -0.0 normalizes to 0.0
    assert k == column_key({"load": [1.0, 2.5, -0.0], "ops_cost": 100.0})


# --------------------------------------------------------------------------
# pilot driver and audit gate (requirements 9-11 + corrections 5-6)
# --------------------------------------------------------------------------
def test_pilot_list_is_exactly_the_spec():
    cells = build_cells()
    assert len(cells) == 12
    assert cells == [(s, n, b) for s in (0, 11, 15) for n in (8, 12)
                     for b in (0.01, 0.05)]
    assert EPSILON == 1e-2 and BUDGET == 240


def test_every_master_solve_is_evidenced(cg_run):
    state, out = cg_run
    iters = _read_jsonl(os.path.join(out, "t.iterations.jsonl"))
    oracle_ids = {r["extra"]["call_id"]
                  for r in _read_jsonl(os.path.join(out, "t.oracle.jsonl"))}
    seen_solve_ids = set()
    for it in iters:
        assert it["master_solves"], "iteration without master-solve evidence"
        for ms in it["master_solves"]:
            assert ms["status"] == "OPTIMAL"
            assert ms["solve_id"] not in seen_solve_ids  # stable and unique
            seen_solve_ids.add(ms["solve_id"])
            assert math.isfinite(ms["obj"]) and ms["n_vars"] > 0
            assert ms["n_int"] == 0  # the clean RMP is an LP; zero matters
        # pricing referenced by id, not duplicated as another solve entry
        assert it["pricing_solve_id"] in oracle_ids
    # oracle-call count agrees with unique committed records
    assert state["oracle_calls"] == len(oracle_ids)


def test_audit_cg_gate(cg_run, tmp_path):
    state, out = cg_run
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
    bad["ub_history"] = [1.0, 5.0] + bad["ub_history"][2:]
    checkpoint.save(os.path.join(root, "cell_b", "a2.cg.ckpt.json"), bad)
    _, ok3, problems3 = audit(root, expect_cg=2)
    assert not ok3 and any("UB increased" in p for p in problems3)


def test_audit_cg_detects_incoherent_outcome_and_events(cg_run, tmp_path):
    _, out = cg_run
    ck = checkpoint.load(os.path.join(out, "t.cg.ckpt.json"))
    root = str(tmp_path / "root")

    # outcome gap must equal final UB minus LB_best
    bad = json.loads(json.dumps(ck))
    bad["outcome"]["gap"] = bad["outcome"]["gap"] + 1e-3
    checkpoint.save(os.path.join(root, "c1", "a2.cg.ckpt.json"), bad)
    _, ok, problems = audit(root, expect_cg=1)
    assert not ok and any("outcome gap" in p for p in problems)

    # oracle-call count must agree with committed events
    bad2 = json.loads(json.dumps(ck))
    bad2["oracle_events"] = bad2["oracle_events"][:-1]
    checkpoint.save(os.path.join(root, "c1", "a2.cg.ckpt.json"), bad2)
    _, ok2, problems2 = audit(root, expect_cg=1)
    assert not ok2 and any("committed oracle events" in p for p in problems2)

    # a non-OPTIMAL committed oracle record fails
    bad3 = json.loads(json.dumps(ck))
    bad3["oracle_events"][0]["solver"]["status"] = "TIME_LIMIT"
    checkpoint.save(os.path.join(root, "c1", "a2.cg.ckpt.json"), bad3)
    _, ok3, problems3 = audit(root, expect_cg=1)
    assert not ok3 and any("!= OPTIMAL" in p for p in problems3)

    # mismatched history lengths fail
    bad4 = json.loads(json.dumps(ck))
    bad4["lb_history"] = bad4["lb_history"][:-1]
    checkpoint.save(os.path.join(root, "c1", "a2.cg.ckpt.json"), bad4)
    _, ok4, problems4 = audit(root, expect_cg=1)
    assert not ok4 and any("length mismatch" in p for p in problems4)

    # certified outcome with gap > epsilon fails
    bad5 = json.loads(json.dumps(ck))
    bad5["outcome"]["gap"] = 0.5
    bad5["outcome"]["lb_best"] = bad5["outcome"]["ub_ch"] - 0.5
    bad5["lb_best"] = bad5["outcome"]["lb_best"]
    bad5["lb_history"][-1] = bad5["outcome"]["lb_best"]
    checkpoint.save(os.path.join(root, "c1", "a2.cg.ckpt.json"), bad5)
    _, ok5, problems5 = audit(root, expect_cg=1)
    assert not ok5 and any("certified but gap" in p for p in problems5)


def test_audit_solve_ids_are_cell_local(cg_run, tmp_path):
    """Two different cell directories with IDENTICAL local solve ids must
    pass: every pilot cell runs the same driver/tag, so cross-cell id
    repetition is the normal case, not a violation."""
    _, out = cg_run
    root = str(tmp_path / "root")
    for cell in ("cell_a", "cell_b"):
        d = os.path.join(root, cell)
        os.makedirs(d, exist_ok=True)
        for fn in ("t.cg.ckpt.json", "t.iterations.jsonl", "t.oracle.jsonl"):
            with open(os.path.join(out, fn)) as src, \
                    open(os.path.join(d, fn), "w") as dst:
                dst.write(src.read())
    lines, ok, problems = audit(root, expect_cg=2)
    assert ok, problems
    assert not any("duplicate master solve_id" in p for p in problems)


def test_audit_duplicate_solve_id_within_cell_fails(cg_run, tmp_path):
    _, out = cg_run
    root = str(tmp_path / "root")
    d = os.path.join(root, "cell_a")
    os.makedirs(d, exist_ok=True)
    for fn in ("t.cg.ckpt.json", "t.iterations.jsonl", "t.oracle.jsonl"):
        with open(os.path.join(out, fn)) as src, \
                open(os.path.join(d, fn), "w") as dst:
            dst.write(src.read())
    # duplicate one master solve entry twice WITHIN the cell's iteration log
    it_path = os.path.join(d, "t.iterations.jsonl")
    recs = _read_jsonl(it_path)
    recs[-1]["master_solves"] += [dict(recs[-1]["master_solves"][0])] * 2
    with open(it_path, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    _, ok, problems = audit(root, expect_cg=1)
    assert not ok
    dup_problems = [p for p in problems if "duplicate master solve_id" in p]
    # aggregated per cell: one line naming the cell scope, not a huge list
    assert len(dup_problems) == 1
    assert "cell_a" in dup_problems[0]
    assert "2 duplicate" in dup_problems[0]
    assert "cell-local" in dup_problems[0]


def test_audit_checks_cg_iteration_master_solves(tmp_path):
    root = str(tmp_path)
    rec = {"record_kind": "cg-iteration", "iteration_id": "x-it1",
           "master_solves": [{"solve_id": "x-it1-rmp-r0",
                              "status": "TIME_LIMIT"}]}
    with open(os.path.join(root, "it.jsonl"), "w") as f:
        f.write(json.dumps(rec) + "\n")
    _, ok, problems = audit(root)
    assert not ok and any("cg master solve" in p for p in problems)


def test_solver_records_thread_setting(tiny, monkeypatch):
    inst, market = tiny
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "4")
    sol = solve_taker(inst, market.price(np.zeros(market.n_slots)))
    assert sol.stats.extra.get("threads") == 4


# --------------------------------------------------------------------------
# transactional dictator stage (final amendment, item 1)
# --------------------------------------------------------------------------
def _tiny_pilot_args(tmp_path, monkeypatch, tiny):
    inst, _ = tiny
    monkeypatch.setattr(pilot_mod, "synthetic_instance",
                        lambda **_kw: inst)
    return types.SimpleNamespace(out=str(tmp_path), mip_gap=1e-6)


def test_dictator_interrupt_after_checkpoint_before_materialization(
        tiny, tmp_path, monkeypatch):
    args = _tiny_pilot_args(tmp_path, monkeypatch, tiny)
    cell = build_cells()[0]
    tag = f"s{cell[0]}_n{cell[1]}_b{cell[2]:g}"
    jsonl = os.path.join(str(tmp_path), tag, "dictator.jsonl")

    def dying_mat(d_state, path):
        raise KeyboardInterrupt("killed before dictator materialization")

    real_mat = pilot_mod._materialize_dictator
    pilot_mod._materialize_dictator = dying_mat
    try:
        with pytest.raises(KeyboardInterrupt):
            run_cell(cell, args)
    finally:
        pilot_mod._materialize_dictator = real_mat
    # checkpoint committed, log missing — resume repairs and completes
    assert checkpoint.load(jsonl.replace(".jsonl", ".ckpt.json"))["record"]
    assert not os.path.exists(jsonl)
    run_cell(cell, args)
    assert len(_read_jsonl(jsonl)) == 1
    run_cell(cell, args)  # idempotent: rerun never duplicates
    assert len(_read_jsonl(jsonl)) == 1


def test_dictator_interrupt_during_materialization(tiny, tmp_path,
                                                   monkeypatch):
    args = _tiny_pilot_args(tmp_path, monkeypatch, tiny)
    cell = build_cells()[0]
    tag = f"s{cell[0]}_n{cell[1]}_b{cell[2]:g}"
    jsonl = os.path.join(str(tmp_path), tag, "dictator.jsonl")

    def dying_write(path, records):
        raise KeyboardInterrupt("killed mid-materialization")

    real_write = pilot_mod._atomic_write_lines
    pilot_mod._atomic_write_lines = dying_write
    try:
        with pytest.raises(KeyboardInterrupt):
            run_cell(cell, args)
    finally:
        pilot_mod._atomic_write_lines = real_write
    run_cell(cell, args)
    assert len(_read_jsonl(jsonl)) == 1
    # the materialized record equals the committed one
    ck = checkpoint.load(jsonl.replace(".jsonl", ".ckpt.json"))
    assert _read_jsonl(jsonl)[0] == ck["record"]


def test_dictator_rejects_stale_solver_settings(tiny, tmp_path, monkeypatch):
    args = _tiny_pilot_args(tmp_path, monkeypatch, tiny)
    cell = build_cells()[0]
    run_cell(cell, args)  # complete run with mip_gap=1e-6
    args_changed = types.SimpleNamespace(out=str(tmp_path), mip_gap=1e-8)
    with pytest.raises(RuntimeError, match="stale dictator checkpoint"):
        run_cell(cell, args_changed)


# --------------------------------------------------------------------------
# adaptive subsolve evidence (final amendment, item 2)
# --------------------------------------------------------------------------
def test_adaptive_non_optimal_round_fails_immediately(monkeypatch):
    fake_sol = types.SimpleNamespace(
        ops_cost=0.0, load=[0.0], obj_model=10.0, obj_true=None,
        oracle_tier="",
        stats=SolveStats(backend="FAKE", status="TIME_LIMIT", obj=10.0,
                         bound=9.5))
    monkeypatch.setattr(regimes_mod, "solve_evsp",
                        lambda *_a, **_k: copy.deepcopy(fake_sol))
    with pytest.raises(RuntimeError, match="!= OPTIMAL; failing immediately"):
        regimes_mod._solve_convex_adaptive(
            None, seg0=[[(0.0, 0.0)]], tangents_at=lambda L: [(0.0, 0.0)],
            true_energy_cost=lambda L: 10.0, label="test")


def test_adaptive_solve_stats_are_structured(dictator):
    stats = dictator.stats.extra["adaptive_solve_stats"]
    assert len(stats) == dictator.stats.extra["adaptive_rounds"]
    for s in stats:
        assert s["status"] == "OPTIMAL"
        assert math.isfinite(s["bound"]) and math.isfinite(s["incumbent"])
        assert s["gap"] == pytest.approx(s["incumbent"] - s["bound"], abs=1e-12)
        assert s["n_vars"] > 0 and s["n_int"] > 0 and s["n_constrs"] > 0
        assert "wall_s" in s and "backend" in s and "threads" in s


def test_audit_checks_nested_adaptive_subsolves(tmp_path):
    root = str(tmp_path)
    rec = {"experiment": "t", "replay_ok": True,
           "solver": {"backend": "GRB", "status": "OPTIMAL", "wall_s": 1.0,
                      "extra": {"adaptive_solve_stats": [
                          {"round": 1, "status": "OPTIMAL"},
                          {"round": 2, "status": "TIME_LIMIT"}]}}}
    with open(os.path.join(root, "r.jsonl"), "w") as f:
        f.write(json.dumps(rec) + "\n")
    _, ok, problems = audit(root)
    assert not ok and any("adaptive subsolve round 2" in p for p in problems)


# --------------------------------------------------------------------------
# terminal budget RMP evidence (final amendment, item 3)
# --------------------------------------------------------------------------
def test_budget_exhaustion_records_terminal_master(tiny, tmp_path):
    inst, market = tiny
    out = str(tmp_path / "cell")
    state = certified_cg(inst, market, epsilon=1e-2, budget=3,
                         out_dir=out, tag="b")
    oc = state["outcome"]
    assert oc["type"] == "budget_exhausted" and oc["certified"] is False

    iters = _read_jsonl(os.path.join(out, "b.iterations.jsonl"))
    # the terminal clean RMP is evidenced by a master-only event
    term = iters[-1]
    assert term["terminal"] is True and term["pricing_solve_id"] is None
    assert term["master_solves"]
    # every actual master solve has one globally unique id, with n_int
    seen = set()
    for it in iters:
        for ms in it["master_solves"]:
            assert ms["solve_id"] not in seen
            seen.add(ms["solve_id"])
            assert ms["status"] == "OPTIMAL" and ms["n_int"] == 0
            assert math.isfinite(ms["obj"])
    # histories and outcome coherent
    assert len(state["ub_history"]) == len(state["lb_history"])
    assert oc["gap"] == pytest.approx(oc["ub_ch"] - oc["lb_best"], abs=1e-12)
    assert state["ub_history"][-1] == oc["ub_ch"]

    # strengthened audit: complete/sane but NOT certified
    lines, ok, problems = audit(out, expect_cg=1)
    assert ok, problems
    text = "\n".join(lines)
    assert "complete and sane: 1" in text
    assert "CERTIFIED (gap <= epsilon): 0" in text
    assert "budget-exhausted" in text
    assert "CG certification outcomes reported separately above" in text
