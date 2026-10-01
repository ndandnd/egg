"""Focused, source-derived Eberbach intake checks; no optimizer is called."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from egglab import native_recharge as nr
from experiments import sistig_native_case as adapter

DATA = PROJECT / "data/public/sistig_26088190_v1/eberbach_native_case.json"


@pytest.fixture(scope="module")
def document():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_pinned_source_inputs_and_exact_service_semantics(document):
    source = document["source_data"]
    trips, stops = source["service_trips"], source["stops"]
    routes, itineraries = source["routes"], source["itineraries"]
    arcs = source["deadhead_arcs_directed_row_major"]
    assert source["operator_directory"] == "003__Stadtwerke Eberbach"
    assert source["operator_name"] == "Stadtwerke Eberbach"
    assert len(trips) == len({t["trip_id"] for t in trips}) == 105
    assert len(stops) == len({s["id"] for s in stops}) == 14
    assert len(arcs) == len({(a["origin_stop_id"], a["destination_stop_id"]) for a in arcs}) == 196
    assert [s["id"] for s in stops if s["b_depot"]] == [36]
    assert len(routes) == 9 and len(itineraries) == 49
    assert source["calendar_date_present"] is False
    assert source["source_day_type_ids"] == [1]
    members = document["source_archive_provenance"]["member_provenance"]
    assert {Path(x["member_path"]).name for x in members} == set(adapter.EXPECTED_MEMBERS)
    assert all(x["member_path"].startswith(adapter.OPERATOR_CONFIGS["eberbach"]["member_prefix"])
               for x in members)
    assert document["source_archive_provenance"]["archive_sha256"] == adapter.ZIP_SHA256
    stop_ids = {s["id"] for s in stops}
    itinerary_by_id = {i["id"]: i for i in itineraries}
    route_by_id = {r["bus_route_id"]: r for r in routes}
    for t in trips:
        assert t["trip_type"] == 1 and t["bool_service"] is True
        assert adapter.parse_day_time(t["dep_time"]) == t["dep_time_sec"]
        assert adapter.parse_day_time(t["arr_time"]) == t["arr_time_sec"]
        assert adapter.parse_duration(t["duration"]) == t["arr_time_sec"]-t["dep_time_sec"]
        assert t["dep_time_sec"] % 30 == t["arr_time_sec"] % 30 == 0
        assert {t["dep_stop_id"], t["arr_stop_id"]} <= stop_ids
        assert t["bus_route_id"] in route_by_id
        itinerary = itinerary_by_id[t["itinerary_id"]]
        assert (itinerary["bus_route_id"], itinerary["dep_stop_id"], itinerary["arr_stop_id"]) == (
            t["bus_route_id"], t["dep_stop_id"], t["arr_stop_id"])
        assert t["source_energy_kwh"] is None
    assert {r["bus_route_id"]: r["num_trips"] for r in routes} == {
        rid: sum(t["bus_route_id"] == rid for t in trips) for rid in route_by_id}
    arc_by_od = {(a["origin_stop_id"], a["destination_stop_id"]): a for a in arcs}
    assert set(arc_by_od) == {(a, b) for a in stop_ids for b in stop_ids}
    assert all(a["source_energy_kwh"] is None and a["time_sec_source"] % 30 == 0 for a in arcs)
    assert any(arc_by_od[a, b]["distance_m_source"] != arc_by_od[b, a]["distance_m_source"]
               for a in stop_ids for b in stop_ids if a != b)


def test_single_depot_case_and_pure_preflight(document):
    assert len(document["native_cases"]) == 1
    variant = document["native_cases"][0]
    case = adapter.native_case_from_payload(variant)
    assert case.name == "sistig_eberbach_single_depot_36_eb3"
    assert case.identity() == variant["case_identity"]
    assert case.depot == "P36" and case.max_vehicles == 105
    assert case.battery_kwh == 400 and case.recharge_deadline_min == 1800
    assert case.resources == (nr.Resource(0, 1800, 360, 360, 1),)
    assert case.vehicle_cost == 100 and case.deadhead_cost_per_min == 0
    assert len(case.trips) == 105
    assert {t.id for t in case.trips} == {f"E{int(t['trip_id']):04d}"
                                             for t in document["source_data"]["service_trips"]}
    assert max(t.energy_kwh for t in case.trips) < case.battery_kwh
    assert variant["movement_mode_counts"] == {
        "direct": 5189, "depot": 4960, "pullout": 105, "pullin": 105}
    assert variant["direct_wait_at_flagged_depot_count"] == 0
    assert variant["publisher_schedule_or_charging_output_used"] is False
    assert document["modeling_assumptions"]["source_energy_observed"] is False
    nr.validate_case(case)
    compiled = nr.compile_case(case)
    assert len(compiled["intervals"]) == 186
    assert adapter.estimate_compact_model_dimensions(case, compiled) == variant["compact_preflight_dimensions"]
    assert variant["compact_preflight_dimensions"]["charge_interval_continuous_variables"] == 281038
    assert variant["compact_preflight_dimensions"]["model_allocated"] is False
    witness = variant["preflight_witness_and_dimensions"]
    assert witness["replay_ok"] is True and witness["used_vehicle_count"] == 105
    assert witness["last_terminal_charge_end_min"] <= case.recharge_deadline_min
    assert witness["solver_invoked"] is False


def test_operator_output_paths_are_distinct():
    assert adapter.DEFAULT_OUTPUT.name == "hildenbrand_native_cases.json"
    assert adapter.EBERBACH_OUTPUT.name == "eberbach_native_case.json"
    assert adapter.DEFAULT_OUTPUT != adapter.EBERBACH_OUTPUT
