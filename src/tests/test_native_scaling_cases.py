"""Pure frozen synthetic DEVELOPMENT inputs and replayed full-charge witnesses."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from egglab import native_recharge as nr
from experiments import native_scaling_cases as scaling

PINS = {
    "native_scale_dev_s1006_n08": "e46493aba0d055dac32abc52b921ff57726d52454d1aad1de8de98282d2adb8e",
    "native_scale_dev_s1006_n16": "6d3a176c62bd325db353f979d6d725f3931f7cc1cb7205965e5f37fb840e963a",
    "native_scale_dev_s1006_n24": "522e53c2b467dd252d6e725472a17994a6b7e08bbe4f9972047ecc4dc7508486",
    "native_scale_dev_s1012_n16": "ce5a430d2da4817a8002f57ea48fec79df5710344e5bb9c0796c3da5c9fce6aa",
    "native_scale_dev_s1009_n16": "b6c5fdde0f23917686c9913ed5f75e58f25f0d971a9b056ca930da98eb992260",
}
RECEIPT = PROJECT / "research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json"


def test_reserved_cells_and_reproducible_physical_identifies():
    cases = scaling.cases()
    assert set(cases) == set(PINS)
    assert {name: case.identity() for name, case in cases.items()} == PINS
    assert {name: case.identity() for name, case in scaling.cases().items()} == PINS
    with pytest.raises(ValueError, match="outside the five reserved"):
        scaling.make_case(1003, 16)  # reserved test seed
    with pytest.raises(ValueError, match="outside the five reserved"):
        scaling.make_case(1006, 12)
    with pytest.raises(ValueError, match="outside the five reserved"):
        scaling.make_case(1012, 24)
    assert [t.energy_kwh for t in cases["native_scale_dev_s1006_n08"].trips] == [
        t.energy_kwh for t in cases["native_scale_dev_s1006_n16"].trips[:8]]
    assert cases["native_scale_dev_s1012_n16"].trips != cases["native_scale_dev_s1009_n16"].trips


def test_actual_full_charge_replay_and_low_window_pressure():
    cases, plans = scaling.cases(), scaling.witnesses()
    receipt = json.loads(RECEIPT.read_text())
    assert {row["name"] for row in receipt["cases"]} == set(PINS)
    assert receipt["failed_cells"] == []
    assert receipt["generator_source_sha256"] == hashlib.sha256(
        (PROJECT / "src/experiments/native_scaling_cases.py").read_bytes()).hexdigest()
    for row in receipt["cases"]:
        case, plan = cases[row["name"]], plans[row["name"]]
        nr.validate_case(case)
        compiled = nr.compile_case(case)
        replay = nr.replay_native(case, plan)
        assert replay["replay_ok"] and all(
            trajectory[-1]["soc_kwh"] == pytest.approx(100)
            for trajectory in replay["soc_trajectories"])
        assert case.battery_kwh == 100 and case.reserve_kwh == 20
        assert case.efficiency == 0.9 and case.terminal_open_min == 1080
        assert case.recharge_deadline_min == 1800
        assert case.resources == (nr.Resource(0, 1800, 90, 90, 1),)
        assert case.vehicle_cost == 100 and case.deadhead_cost_per_min == 0
        assert len(case.trips) == row["services"]
        assert len(plan["vehicles"]) == row["duties"] == len(case.trips)//2
        assert max(t.end_min for t in case.trips) < 1080
        assert max(t.energy_kwh for t in case.trips) <= 28
        assert max(charge["end_min"] for charge in plan["charges"]) <= 1800
        assert replay["grid_kwh"] == pytest.approx(row["total_grid_replenishment_kwh"])
        assert replay["max_grid_kw"] <= 90 + nr.ENERGY_TOL
        assert min(p["soc_kwh"] for trajectory in replay["soc_trajectories"]
                   for p in trajectory) >= 20 - nr.ENERGY_TOL
        assert row["max_paired_duty_energy_kwh"] <= 60.5
        assert row["max_off_depot_wait_energy_kwh"] <= 0.5
        assert row["max_paired_pullout_pullin_energy_kwh"] <= 4
        assert row["compact_dimensions"] == scaling.compact_dimensions(case, compiled)
        service_lower = sum(t.energy_kwh for t in case.trips)/case.efficiency
        assert row["minimum_grid_replenishment_kwh_from_services_only"] == pytest.approx(service_lower)
        assert row["unavoidable_grid_energy_outside_any_four_hour_90kw_window_kwh"] == pytest.approx(
            max(0, service_lower-360))
        assert row["solver_invoked"] is False and row["model_allocated"] is False
    assert receipt["cases"][0]["unavoidable_grid_energy_outside_any_four_hour_90kw_window_kwh"] == 0
    assert all(row["unavoidable_grid_energy_outside_any_four_hour_90kw_window_kwh"] > 0
               for row in receipt["cases"][1:])


def test_price_only_variants_preserve_case_and_shift_window():
    cases, tariffs = scaling.cases(), scaling.tariffs()
    assert set(cases) == set(tariffs)
    for name, vectors in tariffs.items():
        assert set(vectors) == {"flat", "source_low", "target_low"}
        assert len(vectors["flat"]) == len(cases[name].market_edges_min)-1 == 30
        assert vectors["flat"] == (0.20,)*30
        assert [i for i, x in enumerate(vectors["source_low"]) if x == 0.10] == list(range(18, 22))
        assert [i for i, x in enumerate(vectors["target_low"]) if x == 0.10] == list(range(22, 26))
        assert all(x in (0.10, 0.30) for x in vectors["source_low"]+vectors["target_low"])
