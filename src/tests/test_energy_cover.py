"""Necessary energy cover checks; no native optimization is run."""
from dataclasses import replace
import json
import math
from pathlib import Path

import pytest

from egglab import learned_proposals as lp
from egglab import native_recharge as nr
from egglab import route_fixed_repair as repair
from experiments.native_recharge_qualification import cyclic_case


ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1"


def test_energy_relaxation_requires_depot_opportunity():
    with_charge = cyclic_case()
    cover = repair.decode_path_cover(with_charge, cover_policy="cost_only",
                                     energy_relaxation=True, time_limit_seconds=2)
    assert cover["pullout_count"] == 1
    assert "depot_AB" in cover["selected_movements"]
    assert cover["energy_relaxation"] is True
    assert cover["relaxation_minimum_bus_count_reported"] is True
    assert cover["native_minimum_bus_count_reported"] is False
    assert set(cover["soc_after_trip_witness_kwh"]) == {"A", "B"}

    no_charge = cyclic_case(early_kw=0)
    cover = repair.decode_path_cover(no_charge, cover_policy="cost_only",
                                     energy_relaxation=True, time_limit_seconds=2)
    assert cover["pullout_count"] == 2
    assert "depot_AB" not in cover["selected_movements"]
    assert "direct_AB" not in cover["selected_movements"]


def test_energy_relaxation_respects_depot_and_terminal_arrival_reserve():
    case = cyclic_case()
    modes = tuple(replace(mode, legs=(replace(mode.legs[0], energy_kwh=6.0),
                                        mode.legs[1])) if mode.id == "depot_AB" else mode
                  for mode in case.movements)
    inbound_too_long = replace(case, name="inbound-too-long", movements=modes)
    cover = repair.decode_path_cover(inbound_too_long, cover_policy="cost_only",
                                     energy_relaxation=True, time_limit_seconds=2)
    assert cover["pullout_count"] == 2

    modes = tuple(replace(mode, legs=(replace(mode.legs[0], energy_kwh=6.0),))
                  if mode.id == "in_B" else mode for mode in case.movements)
    terminal_too_far = replace(case, name="terminal-too-far", movements=modes)
    with pytest.raises(repair.RepairStageFailure, match="no integral incumbent"):
        repair.decode_path_cover(terminal_too_far, cover_policy="cost_only",
                                 energy_relaxation=True, time_limit_seconds=2)


def test_replayed_source_zero_plans_have_physical_soc_witness():
    frozen = json.loads((STAGE2 / "frozen.json").read_text())
    checked = 0
    for case_name in ("learning_s2016_n20", "learning_s2017_n28"):
        case = lp.case_from_dict(frozen["design"]["groups"][case_name]["case"])
        compiled = nr.compile_case(case)
        rows = repair._energy_relaxation_rows(case, compiled)
        artifact = STAGE2 / case_name / "state0/source0/raw_result.json"
        columns = json.loads(artifact.read_text())["result"]["columns"]
        for column in columns:
            plan = column["plan"]
            assert nr.replay_native(case, plan)["replay_ok"]
            selected = {mid for vehicle in plan["vehicles"]
                        for mid in vehicle["movements"]}
            after = {}
            for vehicle, trajectory in zip(plan["vehicles"],
                                           plan["replay"]["soc_trajectories"]):
                services = [event["soc_kwh"] for event in trajectory
                            if event["kind"] == "service"]
                assert len(services) == len(vehicle["trips"])
                after.update(zip(vehicle["trips"], services))
            assert set(after) == {trip.id for trip in case.trips}
            witness = ([float(mode.id in selected) for mode in case.movements] +
                       [after[trip.id] for trip in case.trips])
            for coefficients, lower, upper in rows:
                value = sum(coefficient*witness[index]
                            for index, coefficient in coefficients.items())
                assert math.isinf(lower) or value >= lower - 1e-6
                assert math.isinf(upper) or value <= upper + 1e-6
            for trip in case.trips:
                assert case.reserve_kwh - 1e-6 <= after[trip.id]
                assert after[trip.id] <= case.battery_kwh-trip.energy_kwh+1e-6
            checked += 1
    assert checked >= 2


def test_nonfinite_soc_witness_is_rejected_before_receipting(monkeypatch):
    from types import SimpleNamespace
    import scipy.optimize
    case = cyclic_case()
    selected = {"out_A", "depot_AB", "in_B"}
    vector = [float(mode.id in selected) for mode in case.movements]+[float("nan")]*len(case.trips)
    monkeypatch.setattr(scipy.optimize, "milp", lambda **kwargs: SimpleNamespace(
        x=vector, fun=1., status=0, message="malformed native return", mip_gap=0., mip_node_count=1))
    with pytest.raises(repair.RepairStageFailure, match="no integral incumbent"):
        repair.decode_path_cover(case, cover_policy="cost_only", energy_relaxation=True)
