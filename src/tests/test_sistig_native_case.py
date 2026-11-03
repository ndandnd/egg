"""Public-source adapter and NativeCase preflight; never calls an optimizer."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys

import pytest

SRC = Path(__file__).resolve().parents[1]
PROJECT = SRC.parent
sys.path.insert(0, str(SRC))

from egglab import native_recharge as nr
from experiments import sistig_native_case as adapter


DATA_PATH = PROJECT / "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"


@pytest.fixture(scope="module")
def document():
    assert DATA_PATH.is_file(), "regenerate the public-derived Hildenbrand case first"
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def source_indexes(document):
    source = document["source_data"]
    trips_by_id = {f"H{int(t['trip_id']):04d}": t for t in source["service_trips"]}
    arc_by_od = {(int(a["origin_stop_id"]), int(a["destination_stop_id"])): a
                 for a in source["deadhead_arcs_directed_row_major"]}
    assert len(trips_by_id) == 37
    assert len(arc_by_od) == 25
    return trips_by_id, arc_by_od


def assert_minute_exact(seconds, minutes):
    assert isinstance(minutes, (int, float)) and not isinstance(minutes, bool)
    assert float(minutes) * 60 == seconds
    assert seconds % 30 == 0


def test_public_provenance_and_data_scope(document):
    ds = document["dataset"]
    assert ds["doi"] == "10.6084/m9.figshare.26088190.v1"
    assert ds["license"] == "CC BY 4.0"
    assert document["source_archive_provenance"]["archive_sha256"] == adapter.ZIP_SHA256
    assert document["source_archive_provenance"]["archive_md5"] == adapter.ZIP_MD5
    assert document["source_archive_provenance"]["archive_bytes"] == adapter.ZIP_BYTES
    assert document["source_archive_provenance"]["archive_verified_intake_sha256"] == adapter.ZIP_SHA256
    assert document["source_archive_provenance"]["archive_figshare_supplied_md5"] == adapter.ZIP_MD5
    assert "publisher_expected_sha256" not in json.dumps(document["source_archive_provenance"])
    members = document["source_archive_provenance"]["member_provenance"]
    assert {Path(x["member_path"]).name for x in members} == set(adapter.EXPECTED_MEMBERS)
    assert all(len(x["sha256"]) == 64 and x["uncompressed_bytes"] > 0 for x in members)
    assert "archive_path_local_only" not in document["source_archive_provenance"]
    assert not (DATA_PATH.parent / "sistig-26088190-v1.zip").exists()
    assert document["modeling_assumptions"]["publisher_derived_schedule_or_charging_used"] is False
    assert document["modeling_assumptions"]["scientific_campaign_frozen"] is False


def test_all_37_source_services_and_full_directed_matrix_are_retained(document):
    source = document["source_data"]
    trips = source["service_trips"]
    arcs = source["deadhead_arcs_directed_row_major"]
    assert len(trips) == 37
    assert len({t["trip_id"] for t in trips}) == 37
    assert len(arcs) == 25
    assert len({(a["origin_stop_id"], a["destination_stop_id"]) for a in arcs}) == 25
    assert source["source_day_type_ids"] == [1]
    assert source["calendar_date_present"] is False
    assert all(t["source_energy_kwh"] is None for t in trips)
    assert all(a["source_energy_kwh"] is None for a in arcs)
    assert all(math.isfinite(a["distance_m_source"]) and math.isfinite(a["time_sec_source"])
               for a in arcs)
    assert len(source["stops"]) == 5
    assert sum(bool(s["b_depot"]) for s in source["stops"]) == 2
    depot_ids = {int(s["id"]) for s in source["stops"] if s["b_depot"]}
    service_endpoint_ids = {int(t[k]) for t in trips for k in ("dep_stop_id", "arr_stop_id")}
    assert depot_ids.isdisjoint(service_endpoint_ids)
    # The source matrix must remain directed; no adapter-level symmetrization.
    arc_by_od = {(int(a["origin_stop_id"]), int(a["destination_stop_id"])): a for a in arcs}
    assert any(arc_by_od[a, b]["distance_m_source"] != arc_by_od[b, a]["distance_m_source"]
               for a in source["deadhead_stop_order_source"]
               for b in source["deadhead_stop_order_source"] if a != b)


def test_source_time_precision_and_modelled_energy_are_separate(document):
    source = document["source_data"]
    raw = source["service_trips"]
    assert any(int(t["dep_time_sec"]) >= 86400 or int(t["arr_time_sec"]) >= 86400 for t in raw)
    for row in raw:
        assert adapter.parse_day_time(row["dep_time"]) == row["dep_time_sec"]
        assert adapter.parse_day_time(row["arr_time"]) == row["arr_time_sec"]
        assert adapter.parse_duration(row["duration"]) == row["arr_time_sec"] - row["dep_time_sec"]
        assert row["dep_time_sec"] % 60 == row["arr_time_sec"] % 60 == 0
    assumption = document["modeling_assumptions"]["vehicle_concept"]
    assert assumption["paper_vehicle_id"] == "4103"
    assert assumption["paper_vehicle_name"] == "EB-3"
    assert assumption["usable_battery_kwh"] == 400
    assert assumption["service_traction_kwh_per_km"] == pytest.approx(1.20)
    assert assumption["deadhead_traction_kwh_per_km"] == pytest.approx(0.96)
    assert assumption["auxiliary_kwh_per_hour"] == pytest.approx(16)
    for variant in document["native_cases"]:
        model_trips = {x["native"]["id"]: x for x in variant["trips"]}
        for service_id, raw_row in source_indexes(document)[0].items():
            model = model_trips[service_id]
            assert model["source_energy_kwh"] is None
            assert_minute_exact(raw_row["dep_time_sec"], model["native"]["start_min"])
            assert_minute_exact(raw_row["arr_time_sec"], model["native"]["end_min"])
            energy = model["model_energy"]
            expected_traction = 1.20 * float(raw_row["distance"])
            expected_aux = 16.0 * (raw_row["arr_time_sec"]-raw_row["dep_time_sec"]) / 3600
            assert energy["modeled_energy_kwh"] == pytest.approx(expected_traction + expected_aux)
            assert energy["energy_components"]["traction_kwh"] == pytest.approx(expected_traction)
            assert energy["energy_components"]["auxiliary_kwh"] == pytest.approx(expected_aux)


@pytest.mark.parametrize("depot_id", [15, 16])
def test_native_schema_preflight_and_fixed_directed_movement_policies(document, depot_id):
    variant = next(x for x in document["native_cases"] if x["selected_depot_id"] == depot_id)
    case = adapter.native_case_from_payload(variant)
    assert case.max_vehicles == 37
    assert case.battery_kwh == 400
    assert case.reserve_kwh == 0
    assert case.efficiency == 1
    assert case.terminal_open_min == 0
    assert case.recharge_deadline_min == 1800
    assert case.resources == (nr.Resource(0, 1800, 360.0, 360.0, 1),)
    assert case.market_edges_min == tuple(range(0, 1801, 60))
    nr.validate_case(case)
    compiled = nr.compile_case(case)
    assert compiled["identity"] == case.identity() == variant["case_identity"]
    assert compiled["physical_schema"] == nr.SCHEMA
    assert compiled["intervals"]

    source_trips, arc_by_od = source_indexes(document)
    native_trip_by_id = {x.id: x for x in case.trips}
    modes = {m.id: m for m in case.movements}
    mode_prov = {x["movement_id"]: x for x in variant["movement_provenance"]}
    assert set(modes) == set(mode_prov)
    assert len(native_trip_by_id) == 37
    assert variant["movement_mode_counts"]["pullout"] == 37
    assert variant["movement_mode_counts"]["pullin"] == 37
    assert variant["movement_mode_counts"]["direct"] > 0
    assert variant["movement_mode_counts"]["depot"] > 0
    assert variant["direct_off_depot_wait_mode_count"] == 648
    assert variant["direct_wait_at_flagged_depot_count"] == 0
    assert variant["direct_wait_at_flagged_depot_count"] == 0

    for mode_id, mode in modes.items():
        provenance = mode_prov[mode_id]
        assert len(mode.legs) == len(provenance["legs"])
        for native_leg, source_leg in zip(mode.legs, provenance["legs"]):
            assert_minute_exact(source_leg["depart_sec"], native_leg.depart_min)
            assert_minute_exact(source_leg["arrive_sec"], native_leg.arrive_min)
            assert native_leg.energy_kwh == pytest.approx(source_leg["modeled_energy_kwh"])
            assert source_leg["source_energy_kwh"] is None
            if source_leg["leg_role"] == "off_depot_stationary_wait":
                assert source_leg["origin_stop_id"] == source_leg["destination_stop_id"]
                assert source_leg["source_member"] is None
            else:
                arc = arc_by_od[(source_leg["origin_stop_id"], source_leg["destination_stop_id"])]
                assert source_leg["source_distance_m"] == arc["distance_m_source"]
                assert source_leg["source_travel_time_sec"] == arc["time_sec_source"]
                assert source_leg["source_height_difference_m"] == arc["height_difference_m_source"]

        if mode.kind == "direct":
            before = source_trips[mode.before]
            after = source_trips[mode.after]
            first = provenance["legs"][0]
            arc = arc_by_od[(int(before["arr_stop_id"]), int(after["dep_stop_id"]))]
            assert first["leg_role"] == "deadhead_direct"
            assert first["depart_sec"] == before["arr_time_sec"]
            assert first["arrive_sec"] == before["arr_time_sec"] + arc["time_sec_source"]
            assert provenance["legs"][-1]["arrive_sec"] == after["dep_time_sec"]
            if len(provenance["legs"]) == 2:
                assert provenance["legs"][1]["leg_role"] == "off_depot_stationary_wait"
        elif mode.kind == "depot":
            assert provenance["depot_id"] == depot_id
            assert provenance["depot_split_after_leg"] == 1
            assert provenance["depot_dwell_start_sec"] <= provenance["depot_dwell_end_sec"]
            assert provenance["legs"][0]["depart_sec"] == source_trips[mode.before]["arr_time_sec"]
            assert provenance["legs"][1]["arrive_sec"] == source_trips[mode.after]["dep_time_sec"]
        elif mode.kind == "pullout":
            assert mode.after is not None and mode.before is None
            assert provenance["legs"][0]["arrive_sec"] == source_trips[mode.after]["dep_time_sec"]
        elif mode.kind == "pullin":
            assert mode.before is not None and mode.after is None
            assert provenance["legs"][0]["depart_sec"] == source_trips[mode.before]["arr_time_sec"]
            assert provenance["terminal_charge_window_sec"][1] == 108000
        else:
            pytest.fail(f"unexpected movement kind: {mode.kind}")

    # Every time-feasible fixed immediate-direct policy pair appears once.
    direct_pairs = {(m.before, m.after) for m in modes.values() if m.kind == "direct"}
    expected_pairs = set()
    ordered = sorted(source_trips.items(), key=lambda kv: (kv[1]["dep_time_sec"], kv[1]["arr_time_sec"]))
    for bid, b in ordered:
        for aid, a in ordered:
            if bid == aid:
                continue
            arc = arc_by_od[(int(b["arr_stop_id"]), int(a["dep_stop_id"]))]
            if b["arr_time_sec"] + arc["time_sec_source"] <= a["dep_time_sec"]:
                expected_pairs.add((bid, aid))
    assert direct_pairs == expected_pairs


def test_models_are_explicit_single_depot_restrictions_not_source_two_depot_result(document):
    assert {v["selected_depot_id"] for v in document["native_cases"]} == {15, 16}
    assert all(v["variant_policy"] == "single source-flagged depot only; not the source two-depot fleet model"
               for v in document["native_cases"])
    assert all(v["scientific_campaign_frozen"] is False for v in document["native_cases"])
    assert all(v["publisher_schedule_or_charging_output_used"] is False for v in document["native_cases"])
    assert all(v["charging_model"]["connectors"] == 1 for v in document["native_cases"])
    assert all(v["charging_model"]["per_bus_kw"] == 360
               and v["charging_model"]["shared_grid_kw"] == 360 for v in document["native_cases"])


@pytest.mark.parametrize("depot_id", [15, 16])
def test_constructive_one_trip_per_bus_witness_and_candidate_interval_count(document, depot_id):
    variant = next(x for x in document["native_cases"] if x["selected_depot_id"] == depot_id)
    summary = variant["preflight_witness_and_dimensions"]
    assert summary["classification"] == "constructed one-trip-per-bus feasible witness; not optimized"
    assert summary["replay_ok"] is True
    assert summary["solver_invoked"] is False
    assert summary["used_vehicle_count"] == 37
    assert summary["latest_pullin_arrival_min"] < 1800
    assert summary["last_terminal_charge_end_min"] <= 1800
    assert summary["maximum_shared_grid_kw"] <= 360 + 1e-8
    assert summary["total_terminal_charge_kwh"] == pytest.approx(
        summary["one_trip_per_bus_total_battery_energy_kwh"])
    assert summary["candidate_charge_variables_at_max_vehicles"] == (
        summary["eligible_mode_interval_pairs_per_vehicle"] * 37)
    assert summary["compiled_resource_interval_count"] > 0
    assert variant["movement_mode_counts"]["direct"] > 0
    assert variant["movement_mode_counts"]["depot"] > 0
    assert document["readiness_summary"]["last_service_arrival"]["timestamp_min"] < 1800
