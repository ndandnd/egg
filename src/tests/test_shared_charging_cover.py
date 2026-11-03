"""Shared interval charging rows on small cases and archived physical plans."""
import json
import math
from pathlib import Path

import pytest

from egglab import learned_proposals as lp
from egglab import native_recharge as nr
from egglab import route_fixed_repair as repair


ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1"


def overlapping_depot_case(visit_kw):
    trips = tuple(nr.Trip(label, start, start+60, "D", "D", 15.0)
                  for label,start in (("A1",0),("A2",0),("B1",120),("B2",120)))
    modes = []
    for trip in trips:
        modes.extend((
            nr.Movement("out_"+trip.id, "pullout", None, trip.id,
                        (nr.Leg("D","D",trip.start_min,trip.start_min,0.0),)),
            nr.Movement("in_"+trip.id, "pullin", trip.id, None,
                        (nr.Leg("D","D",trip.end_min,trip.end_min,0.0),))))
    for suffix in ("1","2"):
        modes.append(nr.Movement("depot_"+suffix, "depot", "A"+suffix, "B"+suffix,
            (nr.Leg("D","D",60,60,0.0), nr.Leg("D","D",120,120,0.0)),1))
    resources = (nr.Resource(0,60,0,0,0),
                 nr.Resource(60,120,visit_kw,visit_kw,1),
                 nr.Resource(120,180,0,0,0),
                 nr.Resource(180,360,60,60,1))
    return nr.NativeCase("overlapping-depots",trips,tuple(modes),resources,
        (0,60,120,180,360),"D",4,20,0,180,360,7)


def test_shared_flag_and_depot_interval_competition():
    case = overlapping_depot_case(15)
    with pytest.raises(ValueError, match="requires energy_relaxation"):
        repair.decode_path_cover(case, cover_policy="cost_only", shared_charging=True)
    with pytest.raises(ValueError, match="requires energy_relaxation"):
        repair.decode_path_cover(case, cover_policy="cost_only",
                                 energy_relaxation=True, shared_charging=True)
    individual = repair.decode_path_cover(case, cover_policy="cost_only",
        energy_relaxation=True, charging_caps=True, time_limit_seconds=2)
    assert individual["pullout_count"] == 2
    shared = repair.decode_path_cover(case, cover_policy="cost_only",
        energy_relaxation=True, charging_caps=True, shared_charging=True,
        time_limit_seconds=2)
    assert shared["pullout_count"] == 3
    assert shared["shared_charging"] is True
    assert shared["shared_charge_variable_count"] > 0
    assert shared["shared_charge_witness"]
    assert all(row["grid_kwh"] > 0 and row["start_min"] < row["end_min"]
               for row in shared["shared_charge_witness"])
    assert shared["native_minimum_bus_count_reported"] is False
    assert shared["relaxation_minimum_bus_count_reported"] is True
    enough = repair.decode_path_cover(overlapping_depot_case(20),
        cover_policy="cost_only", energy_relaxation=True, charging_caps=True,
        shared_charging=True, time_limit_seconds=2)
    assert enough["pullout_count"] == 2


def test_archived_replayed_source_plans_satisfy_shared_rows():
    frozen = json.loads((STAGE2 / "frozen.json").read_text())
    count = 0
    for name in ("learning_s2016_n20", "learning_s2017_n28"):
        case = lp.case_from_dict(frozen["design"]["groups"][name]["case"])
        compiled = nr.compile_case(case)
        caps, rows, keys = repair._shared_charging_rows(case, compiled)
        source = STAGE2 / name / "state0/source0/raw_result.json"
        for column in json.loads(source.read_text())["result"]["columns"]:
            plan = column["plan"]
            assert nr.replay_native(case, plan)["replay_ok"]
            selected = {mid for vehicle in plan["vehicles"]
                        for mid in vehicle["movements"]}
            after = {}
            for vehicle, trajectory in zip(plan["vehicles"],
                                           plan["replay"]["soc_trajectories"]):
                values = [event["soc_kwh"] for event in trajectory
                          if event["kind"] == "service"]
                assert len(values) == len(vehicle["trips"])
                after.update(zip(vehicle["trips"], values))
            charge = {}
            for segment in plan["charges"]:
                matches = [k for k, interval in enumerate(compiled["intervals"])
                           if interval["start"] <= segment["start_min"]
                           and segment["end_min"] <= interval["end"]
                           and segment["movement"] in interval["visits"]]
                assert len(matches) == 1
                key = (segment["movement"], matches[0])
                charge[key] = charge.get(key, 0.0)+segment["grid_kwh"]
            assert set(charge).issubset(set(keys))
            witness = ([float(mode.id in selected) for mode in case.movements] +
                       [after[trip.id] for trip in case.trips] +
                       [charge.get(key,0.0) for key in keys])
            for value, cap in zip(witness[-len(caps):], caps):
                assert -1e-6 <= value <= cap+1e-6
            for coefficients, lower, upper in rows:
                lhs = sum(coefficient*witness[index]
                          for index, coefficient in coefficients.items())
                assert math.isinf(lower) or lhs >= lower-1e-6
                assert math.isinf(upper) or lhs <= upper+1e-6
            count += 1
    assert count >= 2
