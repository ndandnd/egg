"""Route repair checks without native optimization."""
from types import SimpleNamespace

import pytest

from egglab import learned_proposals as lp
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import route_fixed_repair as repair
from experiments.native_recharge_qualification import cyclic_case


SELECTED = ("out_A", "depot_AB", "in_B")


def known_plan(case):
    plan = {"schema":nr.SCHEMA, "case_identity":case.identity(),
        "formulation":pf.FORMULATION, "native_matrix":pf.NATIVE_MATRIX,
        "extraction_policy":pf.EXTRACTION_POLICY,
        "vehicles":[{"vehicle":0, "trips":["A", "B"],
                     "movements":list(SELECTED)}],
        "charges":[{"vehicle":0, "movement":"depot_AB", "connector":0,
                    "start_min":60., "end_min":120., "grid_kwh":10.},
                   {"vehicle":0, "movement":"in_B", "connector":0,
                    "start_min":180., "end_min":220., "grid_kwh":20.}],
        "load":[0.,10.,0.,20.], "ops_cost":7.}
    assert nr.replay_native(case,plan)["replay_ok"]
    return plan


def prior_for(case):
    class FixedPrior(lp.EdgePrior):
        def logits(self, unused_case, unused_prices):
            return [10. if movement.id in SELECTED else -10.
                    for movement in unused_case.movements]

        def propose_topology(self, unused_case, unused_prices):
            return SELECTED
    size = len(lp.FEATURES)
    return FixedPrior((0.,)*size, (1.,)*size, (0.,)*size, (), ())


def test_decoder_makes_one_legal_path_cover():
    case = cyclic_case()
    logits = prior_for(case).logits(case,[1.]*4)
    cover = repair.decode_path_cover(case,logits,time_limit_seconds=1.)
    assert set(cover["selected_movements"]) == set(SELECTED)
    assert cover["vehicles"] == [{"vehicle":0,"trips":["A","B"],
                                  "movements":list(SELECTED)}]
    assert cover["wall_seconds"] >= 0


def test_native_charge_stage_fixes_all_binaries_and_replays(monkeypatch):
    case = cyclic_case()
    market = nh.Market("target",(1.,)*4,(0.,)*4)
    variables = [SimpleNamespace(var_type="B",lb=0,ub=1)
                 for _ in case.movements]
    built = {"x":variables}
    monkeypatch.setattr(pf,"build_feasible_model",lambda *args:built)
    monkeypatch.setattr(pf,"attach_objective",lambda *args:None)
    monkeypatch.setattr(pf,"_optimize_once",lambda *args:{
        "status":"OPTIMAL", "incumbent":37., "lower_bound":37.})
    monkeypatch.setattr(pf,"_extract",lambda *args,**kwargs:known_plan(case))
    plan, replay, stats = repair._solve_fixed_charge(case,market,SELECTED,
        nr.Budget(backend="CBC",phase_seconds=1.,wall_seconds=2.))
    assert stats["status"] == "OPTIMAL" and replay["replay_ok"]
    assert plan["formulation"] == pf.FORMULATION
    assert [(v.lb,v.ub) for v in variables] == [
        (int(m.id in SELECTED),int(m.id in SELECTED)) for m in case.movements]


def test_repair_returns_replayed_plan_or_typed_fallback(monkeypatch):
    case = cyclic_case()
    market = nh.Market("target",(1.,)*4,(0.,)*4)
    prior = prior_for(case)
    budget = nr.Budget(backend="CBC",phase_seconds=1.,wall_seconds=2.)
    plan = known_plan(case)
    monkeypatch.setattr(repair,"_solve_fixed_charge",lambda *args,**kwargs:
        (plan,nr.replay_native(case,plan),{"status":"OPTIMAL"}))
    result = repair.repair_target(case,market,prior,budget=budget,path_seconds=1.)
    assert result["repair_status"] == "replayed"
    assert result["plan"] == plan and result["true_cost"] == 37.
    assert result["timing_seconds"]["total"] >= 0
    def infeasible(*args,**kwargs):
        raise ValueError("no charging schedule")
    monkeypatch.setattr(repair,"_solve_fixed_charge",infeasible)
    failed = repair.repair_target(case,market,prior,budget=budget,path_seconds=1.)
    assert failed["repair_status"] == "fallback" and "plan" not in failed
    assert failed["failure"] == {"stage":"charging","type":"ValueError",
                                 "message":"no charging schedule"}


def test_invalid_cover_input_is_rejected():
    case = cyclic_case()
    with pytest.raises(ValueError,match="Invalid route logits"):
        repair.decode_path_cover(case,[float("nan")]*len(case.movements))


def test_no_cover_incumbent_preserves_highs_status_and_stage_time(monkeypatch):
    import scipy.optimize
    case = cyclic_case()
    market = nh.Market("target",(1.,)*4,(0.,)*4)
    monkeypatch.setattr(scipy.optimize,"milp",lambda *args,**kwargs:SimpleNamespace(
        x=None,status=1,message="time limit",mip_gap=None,mip_node_count=3))
    result = repair.repair_target(case,market,prior_for(case),
        budget=nr.Budget(backend="CBC",phase_seconds=1.,wall_seconds=2.))
    assert result["repair_status"] == "fallback" and "plan" not in result
    assert result["failure"]["stage"] == "cover"
    assert result["cover"]["status"] == 1
    assert result["cover"]["mip_node_count"] == 3
    assert result["cover"]["wall_seconds"] >= 0
    assert result["timing_seconds"]["cover"] >= 0


def test_no_charge_incumbent_preserves_native_stats_and_stage_time(monkeypatch):
    case = cyclic_case()
    market = nh.Market("target",(1.,)*4,(0.,)*4)
    variables = [SimpleNamespace(var_type="B",lb=0,ub=1)
                 for _ in case.movements]
    monkeypatch.setattr(pf,"build_feasible_model",lambda *args:{"x":variables})
    monkeypatch.setattr(pf,"attach_objective",lambda *args:None)
    stats = {"status":"INFEASIBLE", "incumbent":None, "lower_bound":None,
             "wall_s":0.01}
    monkeypatch.setattr(pf,"_optimize_once",lambda *args:stats)
    result = repair.repair_target(case,market,prior_for(case),
        budget=nr.Budget(backend="CBC",phase_seconds=1.,wall_seconds=2.))
    assert result["repair_status"] == "fallback" and "plan" not in result
    assert result["failure"]["stage"] == "charging"
    assert result["native_stats"] == stats
    assert result["timing_seconds"]["charging_and_replay"] >= 0
