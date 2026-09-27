"""Pure/fake-oracle regressions; deliberately no native optimizer execution."""
import copy
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from egglab import native_recharge as nr
from experiments import native_recharge_qualification as q


def plan(case, vehicles, charges):
    loads = [0.0]*(len(case.market_edges_min)-1)
    for c in charges:
        for k, (a, b) in enumerate(zip(case.market_edges_min, case.market_edges_min[1:])):
            loads[k] += c["grid_kwh"]*max(0, min(b, c["end_min"])-max(a, c["start_min"]))/(
                c["end_min"]-c["start_min"])
    modes = {m.id: m for m in case.movements}
    ops = case.vehicle_cost*len(vehicles)+case.deadhead_cost_per_min*sum(
        leg.arrive_min-leg.depart_min for v in vehicles for mid in v["movements"] for leg in modes[mid].legs)
    return {"schema": nr.SCHEMA, "case_identity": case.identity(), "vehicles": vehicles,
            "charges": charges, "load": loads, "ops_cost": ops}


def charge(v, owner, start, end, energy):
    return {"vehicle": v, "movement": owner, "connector": 0,
            "start_min": start, "end_min": end, "grid_kwh": energy}


def one_bus(case=None):
    case = case or q.cyclic_case()
    early = (30+case.reserve_kwh-case.battery_kwh)/case.efficiency
    late = 30/case.efficiency-early
    p = plan(case, [{"vehicle": 0, "trips": ["A", "B"],
                    "movements": ["out_A", "depot_AB", "in_B"]}],
             [charge(0, "depot_AB", 60, 60+60*early/case.resources[1].per_bus_kw, early),
              charge(0, "in_B", 180, 180+2*late, late)])
    return p


def two_bus(case=None):
    case = case or q.cyclic_case()
    return plan(case, [{"vehicle": i, "trips": [t], "movements": ["out_"+t, "in_"+t]}
                       for i, t in enumerate(("A", "B"))],
        [charge(0, "in_A", 60, 90, 5), charge(0, "in_A", 180, 200, 10),
         charge(1, "in_B", 200, 230, 15)])


def test_all_frozen_inputs_validate_without_a_solver():
    cells = q.controls()
    assert len(cells) == len({c["id"] for c in cells}) == 15
    assert sum(c["expected_status"] == "infeasible" for c in cells) == 3
    for cell in cells:
        nr.validate_case(cell["case"])
        assert cell["case"].identity() == nr.compile_case(cell["case"])["identity"]


@pytest.mark.parametrize("case", [q.cyclic_case(), q.cyclic_case(battery=21, reserve=1),
    q.cyclic_case(reserve=1, eta=19/20, early_kw=12)])
def test_one_bus_native_replay_energy_soc_and_full_replenishment(case):
    report = nr.replay_native(case, one_bus(case))
    assert report["grid_kwh"] == pytest.approx(30/case.efficiency)
    assert report["consumption_kwh"] == 30
    assert report["soc_trajectories"][0][-1]["soc_kwh"] == pytest.approx(case.battery_kwh)
    assert min(e["soc_kwh"] for e in report["soc_trajectories"][0]) >= case.reserve_kwh-1e-9


def test_complete_two_bus_family_can_charge_after_A_in_early_resource_window():
    case = q.cyclic_case()
    p = two_bus(case)
    assert nr.replay_native(case, p)["load"] == [0, 5, 0, 25]
    assert p["ops_cost"]+nr.true_cost([0, 4, 0, 0], [0, .2, 0, .2], p["load"]) == 99
    # Closing native terminal admission until hour 3 changes this feasible set.
    restricted = replace(case, terminal_open_min=180)
    p["case_identity"] = restricted.identity()
    with pytest.raises(ValueError, match="availability"):
        nr.replay_native(restricted, p)


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(case_identity="wrong"),
    lambda p: p["vehicles"][0]["trips"].append("A"),
    lambda p: p["vehicles"][0]["movements"].__setitem__(1, "direct_AB"),
    lambda p: p["charges"][0].update(movement="in_A"),
    lambda p: p["charges"][0].update(connector=1),
    lambda p: p["charges"][0].update(connector=False),
    lambda p: p["charges"][0].update(start_min=59),
    lambda p: p["charges"][0].update(grid_kwh=-1),
    lambda p: p["charges"][0].update(grid_kwh=float("nan")),
    lambda p: p["charges"][1].update(end_min=241),
    lambda p: p["charges"].pop(),
    lambda p: p["load"].__setitem__(1, 11),
    lambda p: p.update(ops_cost=0),
])
def test_corrupted_witnesses_fail_closed(mutation):
    case = q.cyclic_case()
    p = one_bus(case)
    mutation(p)
    with pytest.raises(ValueError):
        nr.replay_native(case, p)


def test_overlap_cannot_hide_behind_market_energy_totals():
    case = q.overlap_case(60)
    p = plan(case, [{"vehicle": i, "trips": [t], "movements": ["out_"+t, "in_"+t]}
                   for i, t in enumerate(("A", "B"))],
             [charge(0, "in_A", 30, 60, 5), charge(1, "in_B", 30, 60, 5)])
    assert p["load"] == [10]  # Equal to the misleading full-hour power budget.
    with pytest.raises(ValueError, match="connector"):
        nr.replay_native(case, p)


def test_serial_decoder_has_explicit_nonoverlapping_sessions():
    case = q.overlap_case(90)
    compiled = nr.compile_case(case)
    assert [(x["start"], x["end"]) for x in compiled["intervals"]] == [(0, 30), (30, 60), (60, 90)]
    sessions = nr.decode_serial(case, compiled, {(0, "in_A", 1): 5, (1, "in_B", 2): 5})
    p = plan(case, [{"vehicle": i, "trips": [t], "movements": ["out_"+t, "in_"+t]}
                   for i, t in enumerate(("A", "B"))], sessions)
    assert nr.replay_native(case, p)["max_grid_kw"] == 10
    assert sessions[0]["end_min"] == sessions[1]["start_min"] == 60
    with pytest.raises(ValueError, match="exceeds interval"):
        nr.decode_serial(case, compiled, {(0, "in_A", 1): 5, (1, "in_B", 1): 5})
    with pytest.raises(ValueError, match="unknown elementary"):
        nr.decode_serial(case, compiled, {(0, "in_A", 99): 1})


def test_exact_partial_window_grid_and_directed_multileg_replay():
    case = q.multileg_case()
    grid = nr.compile_case(case)
    assert [(i["start"], i["end"]) for i in grid["intervals"]] == [(0, 60), (60, 75), (75, 120)]
    p = plan(case, [{"vehicle": 0, "trips": ["A"], "movements": ["out_A", "in_A"]}],
             [charge(0, "in_A", 75, 103, 14)])
    report = nr.replay_native(case, p, [1, 1])
    assert report["pricing_objective"] == 36
    assert [e["soc_kwh"] for e in report["soc_trajectories"][0]][-1] == 20
    bad = replace(case.movements[0], legs=(replace(case.movements[0].legs[0], origin="X", destination="D"),
                                          case.movements[0].legs[1]))
    with pytest.raises(ValueError, match="directed chronological"):
        nr.validate_case(replace(case, movements=(bad, case.movements[1])))


def test_charge_completion_precedes_instantaneous_outbound_energy():
    case = q.cyclic_case(reserve=1, early_kw=11)
    modes = tuple(replace(m, legs=(m.legs[0], replace(m.legs[1], energy_kwh=5)))
                  if m.id == "depot_AB" else m for m in case.movements)
    case = replace(case, movements=modes, trips=(case.trips[0], replace(case.trips[1], energy_kwh=10)))
    p = plan(case, [{"vehicle": 0, "trips": ["A", "B"], "movements": ["out_A", "depot_AB", "in_B"]}],
             [charge(0, "depot_AB", 60, 120, 11), charge(0, "in_B", 180, 218, 19)])
    assert nr.replay_native(case, p)["consumption_kwh"] == 30


@pytest.mark.parametrize("alter", [
    lambda c: replace(c, movements=tuple(m for m in c.movements if m.kind != "pullin")),
    lambda c: replace(c, resources=(nr.Resource(0, 240, 30, 30, 2),)),
    lambda c: replace(c, resources=(nr.Resource(1, 240, 30, 30),)),
    lambda c: replace(c, efficiency=0),
    lambda c: replace(c, efficiency=1.1),
    lambda c: replace(c, reserve_kwh=20),
    lambda c: replace(c, movements=(replace(c.movements[0], legs=(replace(c.movements[0].legs[0], energy_kwh=None),)),)+c.movements[1:]),
])
def test_invalid_graph_and_unsupported_physics_fail_closed(alter):
    with pytest.raises(ValueError):
        nr.validate_case(alter(q.cyclic_case()))


@pytest.mark.parametrize("budget", [nr.Budget(threads=2), nr.Budget(phase_seconds=0),
    nr.Budget(wall_seconds=float("inf")), nr.Budget(max_rounds=0), nr.Budget(epsilon=float("nan")),
    nr.Budget(backend="AUTO"), nr.Budget(epsilon=1e-7)])
def test_budget_validation_precedes_any_native_model(budget, monkeypatch):
    monkeypatch.setattr(nr, "build_feasible_model", lambda *a: pytest.fail("native model was initialized"))
    with pytest.raises(ValueError):
        nr.solve_pricing(q.cyclic_case(), [1]*4, budget)


@pytest.mark.parametrize("stats", [
    {"status": "NO_SOLUTION_FOUND", "lower_bound": 0},
    {"status": "FEASIBLE", "lower_bound": None},
    {"status": "FEASIBLE", "lower_bound": float("nan")},
    {"status": "OPTIMAL", "lower_bound": 40},
])
def test_bad_native_status_or_bound_not_admitted(stats):
    with pytest.raises(ValueError):
        nr.admit_bound(stats, 37)


def fake_oracle(monkeypatch, bounds):
    built, attached = [], []
    def builder(case, backend):
        state = {"physical_identity": case.identity()}
        built.append(state)
        return state
    def attach(state, kind, payload):
        attached.append((kind, copy.deepcopy(payload), state["physical_identity"]))
    stats = iter(bounds)
    monkeypatch.setattr(nr, "build_feasible_model", builder)
    monkeypatch.setattr(nr, "attach_objective", attach)
    monkeypatch.setattr(nr, "_optimize_once", lambda *args: next(stats))
    monkeypatch.setattr(nr, "_extract", lambda case, state: one_bus(case))
    return built, attached


def test_feasible_status_can_bound_without_being_renamed_optimal(monkeypatch):
    fake_oracle(monkeypatch, [{"status": "FEASIBLE", "incumbent": 37, "lower_bound": 36}])
    events = []
    result = nr.solve_pricing(q.cyclic_case(), [1]*4, record=events.append)
    assert result["status"] == "bounded"
    assert result["stats"]["status"] == "FEASIBLE"
    assert result["lower"] == pytest.approx(36-nr.BOUND_GUARD)
    assert [e["event"] for e in events] == ["native_start", "native_status"]


def test_narrow_feasible_bound_certifies_but_preserves_status(monkeypatch):
    fake_oracle(monkeypatch, [{"status": "FEASIBLE", "incumbent": 37, "lower_bound": 37}])
    result = nr.solve_pricing(q.cyclic_case(), [1]*4)
    assert result["status"] == "certified"
    assert result["stats"]["status"] == "FEASIBLE"


def test_planner_uses_global_bound_and_logs_immutable_tangents(monkeypatch):
    built, attached = fake_oracle(monkeypatch, [
        {"status": "FEASIBLE", "incumbent": 97, "lower_bound": 7},
        {"status": "OPTIMAL", "incumbent": 97, "lower_bound": 97}])
    events = []
    result = nr.solve_planner(q.cyclic_case(), [0, 4, 0, 0], [0, .2, 0, .2], record=events.append)
    assert result["status"] == "certified" and len(result["rounds"]) == 2
    assert result["rounds"][0]["lower"] == pytest.approx(7-nr.BOUND_GUARD)
    assert all(len(rows) == 1 for rows in result["rounds"][0]["tangents"])
    assert all(len(rows) == 2 for rows in result["rounds"][1]["tangents"])
    assert built[0] is not built[1]
    assert {row[2] for row in attached} == {q.cyclic_case().identity()}
    assert events[0]["tangents"] == result["rounds"][0]["tangents"]


def test_failed_extraction_still_records_native_status(monkeypatch):
    fake_oracle(monkeypatch, [{"status": "OPTIMAL", "incumbent": 37, "lower_bound": 37}])
    monkeypatch.setattr(nr, "_extract", lambda *args: (_ for _ in ()).throw(ValueError("corrupt")))
    events = []
    with pytest.raises(ValueError, match="corrupt"):
        nr.solve_pricing(q.cyclic_case(), [1]*4, record=events.append)
    assert events[-1]["event"] == "native_status"


def test_receipt_writer_never_overwrites_and_worker_preserves_exception(tmp_path, monkeypatch):
    q._json(tmp_path/"exclusive.json", {"first": True})
    with pytest.raises(FileExistsError):
        q._json(tmp_path/"exclusive.json", {"first": False})
    monkeypatch.setattr(q, "source_hashes", lambda: {"test": "fixed"})
    monkeypatch.setattr(nr, "solve_pricing", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("deliberate fake oracle failure")))
    assert q.worker("single_linear", tmp_path, nr.Budget(), {"test": "fixed"}) == 2
    assert "deliberate fake oracle failure" in (tmp_path/"exception.json").read_text()
    assert not (tmp_path/"result.json").exists()


def test_tiny_positive_session_cannot_evade_resource_sweep():
    case = q.cyclic_case()
    p = one_bus(case)
    p["charges"][0]["end_min"] = 60+5e-8
    with pytest.raises(ValueError, match="power exceeded"):
        nr.replay_native(case, p)


def test_adjacent_float_session_cannot_disappear_at_rounded_midpoint():
    case = q.cyclic_case()
    p = one_bus(case)
    p["charges"][0]["end_min"] = math.nextafter(60.0, math.inf)
    assert (p["charges"][0]["start_min"]+p["charges"][0]["end_min"])/2 == 60
    with pytest.raises(ValueError, match="power exceeded"):
        nr.replay_native(case, p)


@pytest.mark.parametrize("incumbent,lower", [(-1e6, 37), (38, 37), (None, 37), (37, 38)])
def test_pricing_checks_native_incumbent_against_replayed_objective(monkeypatch, incumbent, lower):
    fake_oracle(monkeypatch, [{"status": "FEASIBLE", "incumbent": incumbent, "lower_bound": lower}])
    if incumbent is None:
        assert nr.solve_pricing(q.cyclic_case(), [1]*4)["status"] == "unresolved"
    else:
        with pytest.raises(ValueError):
            nr.solve_pricing(q.cyclic_case(), [1]*4)


def test_planner_allows_epigraph_slack_but_checks_saved_envelope(monkeypatch):
    fake_oracle(monkeypatch, [
        {"status": "FEASIBLE", "incumbent": 97, "lower_bound": 47},
        {"status": "FEASIBLE", "incumbent": 100, "lower_bound": 97}])
    result = nr.solve_planner(q.cyclic_case(), [0, 4, 0, 0], [0, .2, 0, .2])
    assert result["status"] == "certified"
    assert [r["replayed_tangent_objective"] for r in result["rounds"]] == [47, 97]
    assert [r["native_epigraph_slack"] for r in result["rounds"]] == [50, 3]


@pytest.mark.parametrize("incumbent,lower", [(40, 40), (97, 50)])
def test_planner_rejects_impossible_incumbent_or_bound_below_true_cost(monkeypatch, incumbent, lower):
    # First solved PWL envelope at this load is 47, while true cost is 97.
    fake_oracle(monkeypatch, [{"status": "FEASIBLE", "incumbent": incumbent, "lower_bound": lower}])
    with pytest.raises(ValueError):
        nr.solve_planner(q.cyclic_case(), [0, 4, 0, 0], [0, .2, 0, .2])


def test_truncated_worker_trace_preserves_prefix_and_continues_all_controls(tmp_path, monkeypatch):
    cells = q.controls()
    calls = []
    monkeypatch.setattr(q, "source_hashes", lambda: {"test": "fixed"})
    monkeypatch.setattr(q, "environment", lambda: {"unit_test": "fake runtime"})
    def fake_run(cmd, **kwargs):
        cell_id = cmd[cmd.index("--worker")+1]
        folder = Path(cmd[cmd.index("--output")+1])
        calls.append(cell_id)
        start = {"event": "native_start", "round": 0}
        if len(calls) == 1:
            (folder/"events.jsonl").write_text(json.dumps(start)+'\n{"event": "native_status",')
            (folder/"result.json").write_text('{"result":')
            raise q.subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        status = {"event": "native_status", "round": 0, "stats": {"wall_s": .01}}
        (folder/"events.jsonl").write_text(json.dumps(start)+'\n'+json.dumps(status)+'\n')
        expected = next(c["expected_status"] for c in cells if c["id"] == cell_id)
        q._json(folder/"result.json", {"assessment": {"pass": True}, "result": {"status": expected}})
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(q.subprocess, "run", fake_run)
    out = tmp_path/"fake_attempt"
    assert q.qualify(out, "pure-fake-oracle-test") == 1
    summary = json.loads((out/"summary.json").read_text())
    assert calls == [c["id"] for c in cells]
    first = summary["cells"][0]
    assert first["hard_timeout"] and not first["pass"]
    assert first["native_calls_started"] == 1 and first["native_calls_returned"] == 0
    assert not first["native_accounting_complete"]
    assert {e["file"] for e in first["evidence_issues"]} == {"events.jsonl", "result.json"}
    assert all(row["pass"] for row in summary["cells"][1:])
    assert (out/cells[0]["id"]/"result.json").read_text() == '{"result":'


def test_requested_backend_and_loaded_implementation_must_agree(monkeypatch):
    fake_solver = type("FakeCBC", (), {"__module__": "mip.cbc"})()
    monkeypatch.setitem(sys.modules, "mip.cbc", SimpleNamespace(libfile=None))
    model = SimpleNamespace(solver_name="CBC", solver=fake_solver)
    assert nr._backend_identity(model, "CBC")["model_solver_name"] == "CBC"
    with pytest.raises(ValueError, match="mismatch/fallback"):
        nr._backend_identity(model, "GRB")
    model.solver_name = "GRB"  # Merely relabeling the same implementation is rejected.
    with pytest.raises(ValueError, match="mismatch/fallback"):
        nr._backend_identity(model, "GRB")


def test_phase_settings_apply_before_single_native_call(monkeypatch):
    class FakeModel:
        num_solutions, objective_bound = 0, float("inf")
        num_cols, num_int, num_rows = 8, 3, 12
        calls = 0
        def optimize(self, max_seconds):
            assert self.threads == 1 and self.max_mip_gap == 1e-9
            assert max_seconds == self.max_seconds == 3
            self.calls += 1
            return SimpleNamespace(name="INFEASIBLE")
    model = FakeModel()
    monkeypatch.setattr(nr.time, "monotonic", lambda: 100)
    built = {"model": model, "backend": "CBC", "backend_runtime": {"requested": "CBC"},
             "constraint_count_before_objective": 10}
    stats = nr._optimize_once(built, nr.Budget(phase_seconds=10), deadline=103)
    assert model.calls == 1
    assert stats["status"] == "INFEASIBLE" and stats["lower_bound"] is None
    assert stats["raw_lower_bound_repr"] == "inf"
    assert stats["n_constraints"] == 12 and stats["physical_constraints"] == 10
    with pytest.raises(TimeoutError):
        nr._optimize_once(built, nr.Budget(), deadline=99)
    assert model.calls == 1
