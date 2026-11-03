"""Charging-window cover checks without native solver runs."""
import json
import math
from pathlib import Path

import pytest

from egglab import learned_proposals as lp
from egglab import native_recharge as nr
from egglab import route_fixed_repair as repair
from experiments.native_recharge_qualification import cyclic_case, single_case


ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1"


def three_trip_case(second_kw):
    trips = tuple(nr.Trip(label, start, start+30, "D", "D", 9.0)
                  for label, start in (("A", 0), ("B", 60), ("C", 120)))
    movements = []
    for trip in trips:
        movements.extend((
            nr.Movement("out_"+trip.id, "pullout", None, trip.id,
                        (nr.Leg("D", "D", trip.start_min, trip.start_min, 0.0),)),
            nr.Movement("in_"+trip.id, "pullin", trip.id, None,
                        (nr.Leg("D", "D", trip.end_min, trip.end_min, 0.0),))))
    for before, after, left, right in (("A", "B", 30, 60),
                                       ("B", "C", 90, 120)):
        movements.append(nr.Movement("depot_"+before+after, "depot", before, after,
            (nr.Leg("D", "D", left, left, 0.0),
             nr.Leg("D", "D", right, right, 0.0)), 1))
    resources = tuple(nr.Resource(a, b, kw, kw, int(kw > 0))
                      for a,b,kw in ((0,30,0),(30,60,8),(60,90,0),
                                     (90,120,second_kw),(120,150,0),
                                     (150,210,30)))
    return nr.NativeCase("two-depot-windows", trips, tuple(movements), resources,
        (0,30,60,90,120,150,210), "D", 3, 20, 0, 150, 210, 7)


def test_charging_cap_flag_and_short_window():
    with pytest.raises(ValueError, match="requires energy_relaxation"):
        repair.decode_path_cover(cyclic_case(), cover_policy="cost_only",
                                 charging_caps=True)
    enough = repair.decode_path_cover(cyclic_case(early_kw=10),
        cover_policy="cost_only", energy_relaxation=True, charging_caps=True,
        time_limit_seconds=2)
    assert enough["pullout_count"] == 1
    assert enough["charging_caps"] is True
    assert enough["relaxation_minimum_bus_count_reported"] is True
    assert enough["native_minimum_bus_count_reported"] is False
    short = repair.decode_path_cover(cyclic_case(early_kw=9),
        cover_policy="cost_only", energy_relaxation=True, charging_caps=True,
        time_limit_seconds=2)
    assert short["pullout_count"] == 2
    assert "depot_AB" not in short["selected_movements"]


def test_cumulative_two_visit_caps_and_terminal_refill():
    enough = repair.decode_path_cover(three_trip_case(8),
        cover_policy="cost_only", energy_relaxation=True, charging_caps=True,
        time_limit_seconds=2)
    assert enough["pullout_count"] == 1
    assert {"depot_AB", "depot_BC"}.issubset(enough["selected_movements"])
    short = repair.decode_path_cover(three_trip_case(4),
        cover_policy="cost_only", energy_relaxation=True, charging_caps=True,
        time_limit_seconds=2)
    assert short["pullout_count"] == 2
    # One service can reach the terminal with reserve, but the short terminal
    # charge cannot restore its full battery by the deadline.
    terminal_short = single_case("terminal-cap", power=10)
    old = repair.decode_path_cover(terminal_short, cover_policy="cost_only",
        energy_relaxation=True, time_limit_seconds=2)
    assert old["pullout_count"] == 1
    with pytest.raises(repair.RepairStageFailure, match="no integral incumbent"):
        repair.decode_path_cover(terminal_short, cover_policy="cost_only",
            energy_relaxation=True, charging_caps=True, time_limit_seconds=2)


def test_archived_replayed_sources_admit_physical_soc_witness():
    frozen = json.loads((STAGE2 / "frozen.json").read_text())
    count = 0
    for name in ("learning_s2016_n20", "learning_s2017_n28"):
        case = lp.case_from_dict(frozen["design"]["groups"][name]["case"])
        rows = repair._energy_relaxation_rows(case, nr.compile_case(case),
                                               charging_caps=True)
        source = STAGE2 / name / "state0/source0/raw_result.json"
        for column in json.loads(source.read_text())["result"]["columns"]:
            plan = column["plan"]
            assert nr.replay_native(case, plan)["replay_ok"]
            selected = {mid for vehicle in plan["vehicles"]
                        for mid in vehicle["movements"]}
            soc = {}
            for vehicle, trajectory in zip(plan["vehicles"],
                                           plan["replay"]["soc_trajectories"]):
                services = [event["soc_kwh"] for event in trajectory
                            if event["kind"] == "service"]
                assert len(services) == len(vehicle["trips"])
                soc.update(zip(vehicle["trips"], services))
            assert set(soc) == {trip.id for trip in case.trips}
            witness = ([float(mode.id in selected) for mode in case.movements] +
                       [soc[trip.id] for trip in case.trips])
            for coefficients, lower, upper in rows:
                lhs = sum(coefficient*witness[index]
                          for index, coefficient in coefficients.items())
                assert math.isinf(lower) or lhs >= lower-1e-6
                assert math.isinf(upper) or lhs <= upper+1e-6
            count += 1
    assert count >= 2
