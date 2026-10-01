#!/usr/bin/env python3
"""Independent post-run audit of the frozen v2 one-cell Sistig nonlinear pilot.

This module only reads a sealed result and Git blobs. It imports copied
standard-library audit helpers from this review directory, never project
modules or solver packages. In particular, it does not enumerate the 37-trip
schedule space: native lower bounds remain explicitly solver-conditioned.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

import independent_compact_core as compact
import independent_energy_band as energy_band
import independent_fixture_core as base
import independent_hull_v3_core as hull_audit
import independent_projection_audit as projection

need, near = base.need, base.near
HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "e23a653dcd77b6ce02eb0af5e544fea7edab9eca"
PROTOCOL = "sistig-nonlinear-one-cell-20260927-v2"
ATTEMPT_REL = Path("result/sistig_nonlinear/20260927-attempt2")
PUBLIC_ATTEMPT_REL = Path("result/sistig_nonlinear/20260927-attempt2-publication")
PUBLIC_MANIFEST_SHA256 = "facff4a3b2d6c38d0ce01e5cdaf0789b080ec30da5e9f621a026145763410137"
PAYLOAD_REL = Path("data/public/sistig_26088190_v1/hildenbrand_native_cases.json")
PAYLOAD_SHA = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
CASE_ID = "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7"
ORACLE = "egg-native-pathflow-v3-energy-band-orphan-projection"
POLICY = "native-pathflow-orphan-projection-v1"
FORMULATION = ORACLE
NATIVE_MATRIX = "egg-native-pathflow-v2-energy-band"
SHARED_POLICY = "native-roundoff-qualification-v2"
RESOLUTION = Q(5)
NEGATIVE_GUARD = Q(1, 10_000)
BOUND_GUARD = Q(1e-6)
ROUTINE_CAPS = {"planner": 240, "hull": 1440, "own_price": 240}
NATIVE_WALL_CAPS = {"planner": 225, "hull": 1380, "own_price": 225}
CHILD_CAPS = {"planner": 255, "hull": 1455, "own_price": 255}
TOTAL_CAP = 2040
STAGES = ("planner", "hull", "own_price")
HULL_BUDGET = {
    "backend": "GRB", "threads": 1, "phase_seconds": 180.0,
    "wall_seconds": 1380.0, "pricing_calls": 6, "master_calls": 8,
    "pool_cap": 48, "epsilon": 1e-4, "pool_tolerance": 1e-6,
    "polish_steps": 256, "rational_bits": 8192, "polish_seconds": 5.0,
}
PHYSICAL_BUDGETS = {
    stage: {"backend": "GRB", "threads": 1, "phase_seconds": 180.0,
            "wall_seconds": 225.0, "max_rounds": 48 if stage == "planner" else 1,
            "epsilon": 1e-4}
    for stage in ("planner", "own_price")
}
TARGET_AUDIT_OUTCOME = "PASS: independent v2 physical/hull/own-price result audit"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_json(value) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def read_json(path: Path):
    return json.loads(path.read_bytes())


def finite(value):
    return type(value) in (int, float) and math.isfinite(float(value))


def reconstruct_case(variant):
    """Independently project the source-audited public payload into native data."""
    charging, cost = variant["charging_model"], variant["cost_policy"]
    return {
        "name": variant["case_name"],
        "trips": [t["native"] for t in variant["trips"]],
        "movements": [{k: m[k] for k in
                       ("id", "kind", "before", "after", "legs", "depot_split")}
                      for m in variant["movement_modes"]],
        "resources": [variant["resource_policy"]],
        "market_edges_min": variant["market_edges_min"],
        "depot": variant["selected_depot_native_place"],
        "max_vehicles": int(variant["vehicle_cap"]),
        "battery_kwh": charging["usable_battery_kwh"],
        "reserve_kwh": charging["reserve_kwh"],
        "terminal_open_min": 0,
        "recharge_deadline_min": 1800,
        "vehicle_cost": cost["vehicle_cost"],
        "deadhead_cost_per_min": cost["deadhead_cost_per_min"],
        "efficiency": charging["efficiency"],
        "graph_scope": "declared-movement-modes-only",
    }


def frozen_inputs(repo: Path, frozen: dict):
    need(frozen.get("protocol") == PROTOCOL, "pilot protocol identity")
    need(frozen.get("source_commit") == SOURCE_COMMIT,
         "published immutable pilot source commit")
    need(frozen.get("backend") == "GRB" and frozen.get("stages") == list(STAGES),
         "GRB and exact three-stage order")
    need(frozen.get("routine_caps") == ROUTINE_CAPS
         and frozen.get("native_wall_caps") == NATIVE_WALL_CAPS
         and frozen.get("child_caps") == CHILD_CAPS
         and frozen.get("total_cap") == TOTAL_CAP,
         "complete-routine/native-wall/child/whole-attempt caps")
    need(frozen.get("budgets") == {**PHYSICAL_BUDGETS, "hull": HULL_BUDGET},
         "full frozen model budgets")
    need(frozen.get("resolution") == "5" and frozen.get("negative_guard") == "1/10000",
         "predeclared five-unit and negative-consistency thresholds")
    hashes = frozen.get("source_hashes")
    need(isinstance(hashes, dict) and hashes, "nonempty frozen source map")
    for rel, expected in hashes.items():
        need(type(rel) is str and not Path(rel).is_absolute() and ".." not in Path(rel).parts,
             "safe frozen source path")
        blob = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{rel}"], cwd=repo)
        need(digest_bytes(blob) == expected, "frozen Git-blob source hash " + rel)
    payload_raw = (repo / PAYLOAD_REL).read_bytes()
    need(digest_bytes(payload_raw) == PAYLOAD_SHA, "pinned public source payload SHA-256")
    payload = json.loads(payload_raw)
    variants = payload.get("native_cases", [])
    need(len(variants) == 2 and [v["selected_depot_id"] for v in variants] == [15, 16],
         "complete two-depot public payload retained")
    case = reconstruct_case(variants[0])
    need(case == frozen.get("case"), "full depot-15 case matches source payload")
    case_id = digest_json({"schema": "egg-native-recharge-v1", "case": case})
    need(case_id == CASE_ID == frozen.get("case_identity"), "depot-15 case identity")
    need(len(case["trips"]) == 37 and case["battery_kwh"] == 400
         and case["reserve_kwh"] == 0 and case["efficiency"] == 1
         and case["max_vehicles"] == 37 and case["recharge_deadline_min"] == 1800,
         "full 37-service declared case physics")
    need(len(case["market_edges_min"]) == 31
         and case["market_edges_min"] == list(range(0, 1801, 60)),
         "30 hourly intervals through 30:00")
    market = frozen.get("market")
    need(isinstance(market, dict) and len(market.get("a", [])) == 30
         and len(market.get("b", [])) == 30
         and market.get("a") == [.2] * 30
         and market.get("b") == [1/900] * 30,
         "stored binary-float 30-period nonlinear market")
    market_id = digest_json(market)
    need(market_id == frozen.get("market_identity"), "frozen market identity")
    return case, market, case_id, market_id, payload


def verify_manifest(attempt: Path, expected_sha: str, *, public_copy=False):
    path = attempt / "MANIFEST.json"
    raw = path.read_bytes()
    need(digest_bytes(raw) == expected_sha, "caller-pinned sealed supervisor manifest")
    manifest = json.loads(raw)
    need(manifest.get("protocol") == PROTOCOL and isinstance(manifest.get("files"), dict),
         "sealed manifest protocol/map")
    expected = set(manifest["files"])
    omitted_names = set()
    # The batch script appends this one receipt only after supervise has sealed
    # its write-once manifest, by protocol design.
    actual = {str(p.relative_to(attempt)) for p in attempt.rglob("*") if p.is_file()}
    if public_copy:
        public_path = attempt / "PUBLIC_MANIFEST.json"
        public_raw = public_path.read_bytes()
        need(digest_bytes(public_raw) == PUBLIC_MANIFEST_SHA256,
             "caller-pinned public-copy omission manifest")
        public = json.loads(public_raw)
        omitted = {
            "hull/stdout.txt": {"bytes": 912, "sha256": "1dd8d47d16df8a1fbc95ab4047011275919353ea8ab0facbe2832d04081c4df0"},
            "own_price/stdout.txt": {"bytes": 152, "sha256": "4d6f5fb03c58ea40fc56b696dedb61dc744dbe9c824576c069c2fb20b8cc6932"},
            "planner/stdout.txt": {"bytes": 304, "sha256": "7649d8d3aba1e06cd13967c3a0b97820db44aef69834e1437660834596c1c87f"},
        }
        omitted_names = set(omitted)
        need(public.get("original_manifest_sha256") == expected_sha
             and public.get("raw_attempt") == str(ATTEMPT_REL)
             and public.get("source_commit") == SOURCE_COMMIT,
             "public-copy manifest is tied to the exact raw attempt and frozen source")
        records = public.get("omitted_files")
        need(type(records) is dict and set(records) == set(omitted),
             "public copy omits exactly the three declared licensing-only stdout files")
        for rel, pin in omitted.items():
            record = records[rel]
            need(type(record) is dict and record.get("bytes") == pin["bytes"]
                 and record.get("sha256") == pin["sha256"],
                 "public omission pin " + rel)
            need(manifest["files"].get(rel) == pin,
                 "public omission pin matches original sealed raw manifest " + rel)
        unchanged = public.get("unchanged_published_files")
        need(type(unchanged) is dict and set(unchanged) == expected - set(omitted),
             "public copy retains every non-omitted sealed file and no undeclared file")
        need(unchanged == {rel: manifest["files"][rel] for rel in sorted(expected-set(omitted))},
             "every retained public file matches original raw manifest record")
        wrapper_path = attempt / "slurm_wrapper_receipt.json"
        wrapper_data = wrapper_path.read_bytes()
        wrapper_record = {"bytes": len(wrapper_data), "sha256": digest_bytes(wrapper_data)}
        need(public.get("postseal_receipts") == {"slurm_wrapper_receipt.json": wrapper_record},
             "public post-seal wrapper receipt matches its pinned hash and size")
        public_expected = (expected-set(omitted)) | {
            "MANIFEST.json", "slurm_wrapper_receipt.json", "PUBLIC_MANIFEST.json", "README.md"}
        need("MANIFEST.json" not in expected and actual == public_expected,
             "public copy has exactly unchanged sealed files, required receipts, and two package metadata files")
    else:
        need("MANIFEST.json" not in expected and actual == expected | {"MANIFEST.json", "slurm_wrapper_receipt.json"},
             "raw attempt is exactly the sealed manifest plus manifest and declared later Slurm receipt")
    total = 0
    for rel, record in manifest["files"].items():
        if public_copy and rel in omitted_names:
            # The pinned public manifest binds the omitted file's original
            # byte count and hash to the private sealed manifest. The omitted
            # license-only bytes are deliberately absent from the public copy.
            continue
        p = attempt / rel
        need(not Path(rel).is_absolute() and ".." not in Path(rel).parts,
             "safe relative manifest path")
        data = p.read_bytes()
        need(record == {"bytes": len(data), "sha256": digest_bytes(data)},
             "manifest size/hash " + rel)
        total += len(data)
    return manifest, total


def parse_events(folder: Path):
    path = folder / "events.jsonl"
    need(path.is_file(), "stage event ledger present: " + folder.name)
    events, issues = [], []
    for line_no, raw in enumerate(path.read_bytes().splitlines(), 1):
        try:
            event = json.loads(raw)
            need(type(event) is dict and type(event.get("event")) is str,
                 "event object/label line " + str(line_no))
            events.append(event)
        except (ValueError, TypeError, UnicodeError, AssertionError) as exc:
            issues.append({"line": line_no, "message": str(exc),
                           "valid_prefix_events": len(events)})
            break
    need(not issues, "complete parseable event ledger")
    return events


def grb_runtime(stats: dict, cap: float, all_runtimes: list, *, master=False):
    need(stats.get("backend") == "GRB" and stats.get("threads") == 1,
         "explicit GRB one-thread native telemetry")
    need(finite(stats.get("seconds_cap")) and 0 < stats["seconds_cap"] <= cap
         and finite(stats.get("wall_s")) and 0 <= stats["wall_s"],
         "native phase cap and observed time")
    need(stats.get("status") in ("OPTIMAL", "FEASIBLE"),
         "native status preserved with usable incumbent")
    rt = stats.get("backend_runtime", {})
    actual = str(rt.get("model_solver_name", "")).upper()
    need(rt.get("requested") == "GRB" and actual in ("GRB", "GUROBI")
         and rt.get("solver_module") == "mip.gurobi"
         and "gurobi" in str(rt.get("solver_class", "")).lower(),
         "runtime is native GRB with no CBC fallback")
    need(type(rt.get("native_library_sha256")) is str
         and re.fullmatch(r"[0-9a-f]{64}", rt["native_library_sha256"])
         and type(rt.get("native_library_path")) is str and rt["native_library_path"],
         "recorded GRB library fingerprint/path")
    need(finite(stats.get("incumbent")) and finite(stats.get("lower_bound"))
         and stats["lower_bound"] <= stats["incumbent"] + 1e-6,
         "finite solver-conditioned global MIP bound under incumbent")
    if master:
        need(stats.get("n_int") == 0, "continuous RMP master")
    all_runtimes.append(rt)
    return rt


def expected_ledger(cell, start, stats, snapshot, events, plan, prices, runtimes, *, stage):
    """Replay one raw physical round without solving or enumerating schedules."""
    need(all(e.get("round") == start.get("round") for e in events),
         "physical call round identity")
    grb_runtime(stats, 180, runtimes)
    raw = compact.raw_primal(cell, start, stats, snapshot)
    raw["case"] = cell["case"]
    need(snapshot.get("native_matrix") == NATIVE_MATRIX
         and snapshot.get("formulation") == FORMULATION
         and snapshot.get("extraction_policy") == POLICY
         and snapshot.get("shared_negative_normalizer_policy") == SHARED_POLICY,
         "raw compact V3 matrix/formulation/policy")
    norm = next(e for e in events if e["event"] == "charge_normalization")
    projections = [e for e in events if e["event"] == "charge_projection"]
    need(len(projections) == 4, "four ordered projection ledger records")
    before, predecode, prereplay, final = projections
    H = [projection.qfloat(v) for v in plan["load"]]
    T = [projection.qfloat(v) for v in plan["replay"]["load"]]
    exp = projection.projection_records(raw, snapshot, cell, norm)
    exp["grid"] = raw["grid"]
    exp["cell"] = cell
    projection.verify_projection_stage(before, exp, "before_budget")
    plan_l1 = projection.verify_projection_stage(predecode, exp, "before_decoding", H)
    decoded = next(e for e in events if e["event"] == "serial_decoding")
    I, J = projection.verify_decoder(raw, exp, decoded, plan)
    projection.verify_projection_stage(prereplay, exp, "before_replay", H, I=I, J=J)
    projection.verify_projection_stage(final, exp, "final", H, I=I, J=J, T=T)
    witness = base.physical(cell, plan)
    objective_event = next(e for e in events if e["event"] == "objective_reconstruction")
    objective = projection.objective_check(cell, raw, start, stats, plan, objective_event)
    if stage == "planner":
        objective["pwl_objective"] = Q(objective_event["pwl_objective"])
    need(plan.get("formulation") == FORMULATION and plan.get("native_matrix") == NATIVE_MATRIX
         and plan.get("extraction_policy") == POLICY,
         "physical plan V3 identity")
    need(plan.get("vehicles") == raw["paths"], "selected graph maps to replayed vehicle paths")
    need(plan["roundoff"]["projection"] ==
         {k: v for k, v in final.items() if k not in ("event", "round", "stage")},
         "plan/final projection ledger equality")
    need(plan["roundoff"]["negative_correction"] ==
         {k: v for k, v in norm.items() if k not in ("event", "round")},
         "plan negative-normalization ledger")
    need(plan["roundoff"]["serial_decoding"] ==
         {k: v for k, v in decoded.items() if k not in ("event", "round", "charges")},
         "plan serial-decoding ledger")
    need(len(plan["roundoff"]["native_load_delta_kwh"]) == len(T),
         "native/replay load correction dimension")
    for index, (hload, native_load, replay_load) in enumerate(zip(H, exp["L"], T)):
        near(plan["roundoff"]["native_load_delta_kwh"][index],
             float(replay_load-native_load), "native/replay load correction", 1e-12)
    if stage == "own_price":
        qprices = list(map(Q, prices))
        objective_value = Q(witness["ops"]) + sum(
            (p*Q(x) for p, x in zip(qprices, witness["load"])), Q(0))
        answer = objective_event
        result = cell["stage_result"]
        lo = float(stats["lower_bound"]) - 1e-6
        hi = float(objective_value) + 1e-6
        need(result["objective"] == "complete-fleet-linear" and result["prices"] == prices,
             "linear own-price objective/price vector")
        near(result["lower"], lo, "own-price guarded global lower", 1e-12)
        near(result["upper"], hi, "own-price replayed upper", 1e-12)
        near(result["gap"], hi-lo, "own-price interval width", 1e-12)
        near(answer["linear_objective"], float(objective_value),
             "own-price replay objective event", 1e-6)
        return {"witness": witness, "objective": objective_value,
                "raw": raw, "projection": exp, "plan_correction_l1": plan_l1,
                "interval_excess": I, "session_excess": J,
                "interval": [Q(result["lower"]), Q(result["upper"])],
                "native_stats": stats}
    return {"witness": witness, "objective": objective,
            "raw": raw, "projection": exp, "plan_correction_l1": plan_l1,
            "interval_excess": I, "session_excess": J,
            "native_stats": stats}


def audit_physical_stage(stage: str, cell_base: dict, market: dict, case_id: str,
                         raw_stage: dict, runtimes: list, *, require_accepted=True):
    need(stage in ("planner", "own_price"), "physical stage identity")
    instruction = raw_stage["input"]
    package = raw_stage.get("result_package")
    result_wrapper = raw_stage.get("raw_result")
    events = raw_stage["events"]
    receipt = raw_stage["receipt"]
    need(instruction.get("stage") == stage, "stage instruction identity")
    expected_types = ["native_start", "native_status", "native_incumbent",
                      "charge_normalization", "charge_projection", "charge_projection",
                      "serial_decoding", "charge_projection", "charge_projection",
                      "objective_reconstruction"]
    by_round = {}
    for event in events:
        need(type(event.get("round")) is int and event["round"] >= 0,
             "physical event round index")
        by_round.setdefault(event["round"], []).append(event)
    need(list(by_round) == list(range(len(by_round))) and len(by_round) > 0,
         "sequential nonempty physical rounds")
    result = package["result"] if package else (result_wrapper.get("result") if result_wrapper else None)
    need(result is not None and result_wrapper is not None
         and result_wrapper.get("result") == result,
         "worker raw result preserved and matches assessed result")
    need(result_wrapper.get("stage") == stage
         and result_wrapper.get("frozen_sha256") == raw_stage["frozen_sha256"],
         "worker raw result stage/frozen identity")
    need(result.get("case_identity") == case_id and result.get("formulation") == FORMULATION
         and result.get("native_matrix") == NATIVE_MATRIX
         and result.get("extraction_policy") == POLICY,
         "physical result identity/formulation/policy")
    if stage == "own_price":
        need(len(by_round) == 1, "own-price stage has one fresh native call")
        prices = instruction.get("prices")
        need(type(prices) is list and len(prices) == 30 and all(finite(x) for x in prices),
             "own-price fixed 30-period vector")
        need(result.get("prices") == prices, "own-price instruction/result equality")
    else:
        prices = None
        need(result.get("a") == market["a"] and result.get("b") == market["b"],
             "planner curvature/linear coefficients frozen")
    cell = {"id": stage, "case": cell_base["case"], "case_identity": case_id,
            "objective": "planner" if stage == "planner" else "pricing",
            "a": market["a"], "b": market["b"]}
    cell["stage_result"] = result
    if prices is not None:
        cell["prices"] = prices
    round_records = []
    best_ups = []
    lower_ends = []
    expected_tangents = [[(float(a), 0.0)] for a in market["a"]]
    for index, events_one in by_round.items():
        expected = expected_types + (["replayed_iteration"] if stage == "planner" else [])
        need([e["event"] for e in events_one] == expected,
             f"complete ordered raw/matrix/projection/replay trace for {stage} round {index}")
        start, status, snapshot = events_one[:3]
        need(start.get("round") == status.get("round") == snapshot.get("round") == index,
             "round attribution")
        if stage == "planner":
            need(start["tangents"] == [[list(line) for line in row]
                                       for row in expected_tangents],
                 "exact stored tangent initialization and evolution")
        stats = status["stats"]
        plan = events_one[-1]["plan"] if stage == "planner" else result["plan"]
        ledger = expected_ledger(cell, start, stats, snapshot, events_one, plan, prices,
                                 runtimes, stage=stage)
        if stage == "planner":
            replay = events_one[-1]
            need(replay["stats"] == stats and replay["tangents"] == start["tangents"],
                 "immutable planner round snapshot")
            need(replay["plan"] == plan, "planner replay witness attribution")
            true_value = Q(ledger["objective"]["physical_objective"])
            lower_float = float(stats["lower_bound"]) - 1e-6
            upper_float = float(true_value) + 1e-6
            near(replay["lower"], lower_float, "planner guarded global lower", 1e-12)
            near(replay["upper"], upper_float, "planner replayed nonlinear upper", 1e-12)
            near(replay["replayed_tangent_objective"],
                 float(ledger["objective"]["pwl_objective"]), "planner replay tangent envelope", 1e-6)
            need(stats["lower_bound"] <= stats["incumbent"] + 1e-6,
                 "planner MIP lower bound does not exceed incumbent")
            lower_ends.append(Q(replay["lower"]))
            best_ups.append((Q(replay["upper"]), plan))
            round_records.append({"round": index, "status": stats["status"],
                                  "lower": Q(replay["lower"]), "upper": Q(replay["upper"]),
                                  "physical_witness": ledger["witness"],
                                  "raw_variables": ledger["raw"]["variables"],
                                  "max_primal_residual": ledger["raw"]["max_constraint_residual"],
                                  "solver_incumbent": stats["incumbent"],
                                  "solver_lower_bound": stats["lower_bound"],
                                  "phase_cap_seconds": stats["seconds_cap"],
                                  "phase_wall_seconds": stats["wall_s"],
                                  "phase_cap_excess_seconds": max(0.0, stats["wall_s"]-stats["seconds_cap"]),
                                  "roundoff_projection": {
                                      k: plan["roundoff"]["projection"][k]
                                      for k in ("negative_l1_exact", "orphan_positive_l1_exact",
                                                "raw_load_row_residual_l1_exact",
                                                "plan_sum_residual_l1_exact",
                                                "interval_capacity_excess_exact",
                                                "session_capacity_excess_exact",
                                                "replay_load_residual_l1_exact",
                                                "whole_incumbent_total_exact", "budget_exact", "accepted")}})
            for t, load in enumerate(plan["replay"]["load"]):
                expected_tangents[t].append([
                    float(market["a"][t] + market["b"][t] * load),
                    float(-0.5 * market["b"][t] * load * load)])
        else:
            stats = events_one[1]["stats"]
            lower_ends.append(Q(result["lower"]))
            best_ups.append((Q(result["upper"]), plan))
            round_records.append({"round": index, "status": stats["status"],
                                  "lower": Q(result["lower"]), "upper": Q(result["upper"]),
                                  "physical_witness": ledger["witness"],
                                  "raw_variables": ledger["raw"]["variables"],
                                  "max_primal_residual": ledger["raw"]["max_constraint_residual"]})
    if stage == "planner":
        need(len(result.get("rounds", [])) == len(round_records),
             "all planner rounds archived in result")
        need(result["rounds"] == [
            {k: v for k, v in by_round[i][-1].items() if k not in ("event", "round")}
            for i in range(len(by_round))], "planner event/result round equality")
        final_lower, final_upper = max(lower_ends), min(u for u, _ in best_ups)
        best_plan = next(p for u, p in best_ups if u == final_upper)
        need(Q(result["lower"]) == final_lower and Q(result["upper"]) == final_upper
             and Q(result["gap"]) == final_upper-final_lower,
             "planner final bound propagation from all round receipts")
        need(result["plan"] == best_plan, "planner retains best replayed physical witness")
        need(result["status"] == ("certified" if final_upper-final_lower <= Q(1e-4) else "bounded"),
             "planner certified/bounded label follows frozen epsilon")
    else:
        need(len(result.get("stats", {})) > 0, "own-price result includes its one native status")
        need(result["stats"] == by_round[0][1]["stats"], "own-price raw status/result equality")
        need(Q(result["gap"]) == Q(result["upper"])-Q(result["lower"]),
             "own-price final interval arithmetic")
        need(result["status"] == ("certified" if result["gap"] <= 1e-4 else "bounded"),
             "own-price certified/bounded label")
    if require_accepted:
        need(receipt.get("pass") is True and receipt.get("returncode") == 0
             and receipt.get("hard_timeout") is False and receipt.get("evidence_issues") == [],
             "physical stage accepted receipt")
    else:
        need(receipt.get("pass") is False and receipt.get("returncode") != 0
             and receipt.get("evidence_issues") == [],
             "failed stage remains explicitly unadmitted")
    native_statuses = [e["stats"] for e in events if e["event"] == "native_status"]
    native_starts = sum(e["event"] == "native_start" for e in events)
    native_solver_wall = math.fsum(float(e["stats"]["wall_s"]) for e in events
                                   if e["event"] == "native_status")
    need(native_starts == len(native_statuses) == receipt["accounting"]["native_starts"]
         == receipt["accounting"]["native_returns"]
         and receipt["accounting"]["native_accounting_complete"] is True
         and len(native_statuses) == (len(by_round) if stage == "planner" else 1),
         "stage native starts/returns and controller call receipt")
    need(len(by_round) <= PHYSICAL_BUDGETS[stage]["max_rounds"],
         "physical call count stays within frozen native round cap")
    need(native_solver_wall <= NATIVE_WALL_CAPS[stage] + 1e-6,
         "sum of observed physical native solve wall time stays within frozen native wall budget")
    if package is not None:
        need(package["stage"] == stage
             and package["frozen_sha256"] == raw_stage["frozen_sha256"],
             "physical package/frozen identity")
        need(0 <= package["elapsed_seconds"] <= ROUTINE_CAPS[stage]
             and package["elapsed_seconds"] <= receipt["elapsed_seconds"],
             "physical scientific routine elapsed cap")
    else:
        exception = raw_stage.get("exception") or {}
        need(not require_accepted and exception.get("type") == "TimeoutError"
             and exception.get("message") == "Scientific routine/admission cap exceeded"
             and exception.get("elapsed_seconds", 0) > ROUTINE_CAPS[stage],
             "missing package has explicit routine-cap failure evidence")
    need(receipt["elapsed_seconds"] <= CHILD_CAPS[stage], "physical child cap")
    return {"stage": stage, "status": result["status"], "bounds": [Q(result["lower"]), Q(result["upper"])],
            "plan": result["plan"], "rounds": round_records, "prices": prices,
            "native_solver_wall_seconds": native_solver_wall,
            "native_wall_cap_seconds": NATIVE_WALL_CAPS[stage],
            "assessment": package["assessment"] if package else None,
            "routine_cap_exceeded": package is None,
            "exception": raw_stage.get("exception"), "receipt": receipt}


def own_price_vector(market: dict, planner: dict):
    load = planner["assessment"]["replay"]["load"]
    need(len(load) == 30, "planner replay load dimension")
    prices = [float(a + b * e) for a, b, e in zip(market["a"], market["b"], load)]
    return prices


def audit_hull_accounting(events):
    """Independent structural native/polish call ledger."""
    pricing_starts = pricing_returns = master_starts = master_returns = 0
    seed_requests = pricing_requests = checks = steps = phases_start = phases_end = 0
    phase_steps = phase_checks = 0
    active = None
    last = None
    native_wall, polish_wall = [], []
    for event in events:
        kind = event.get("event")
        if kind == "pricing_request":
            pricing_requests += 1
            seed_requests += int(event.get("seed") is True)
        if kind == "pricing_native":
            detail = event.get("detail", {})
            if detail.get("event") == "native_start": pricing_starts += 1
            if detail.get("event") == "native_status":
                pricing_returns += 1
                native_wall.append(detail["stats"]["wall_s"])
        if kind == "master_start": master_starts += 1
        if kind == "master_status":
            master_returns += 1
            native_wall.append(event["stats"]["wall_s"])
        if kind == "pool_polish_start":
            need(active is None and event.get("cumulative_steps") == steps,
                 "polish start sequential ledger")
            active = event["master_call"]; phases_start += 1
            phase_steps = phase_checks = 0; last = "start"
        elif kind == "pool_polish_check":
            need(active == event.get("master_call") and last in ("start", "step"),
                 "polish check order")
            checks += 1; phase_checks += 1; last = "check"
        elif kind == "pool_polish_step":
            need(active == event.get("master_call") and last == "check"
                 and event.get("step") == steps + 1, "polish transfer order")
            steps += 1; phase_steps += 1; last = "step"
        elif kind == "pool_polish_finish":
            need(active == event.get("master_call")
                 and event.get("steps_completed") == phase_steps
                 and event.get("checks_completed") == phase_checks,
                 "polish finish counters")
            phases_end += 1; polish_wall.append(event["elapsed_s"])
            active = None; last = None
    need(active is None and pricing_starts == pricing_returns
         and master_starts == master_returns and phases_start == phases_end,
         "balanced hull start/status/polish call ledger")
    return {"pricing_requests": pricing_requests, "seed_requests": seed_requests,
            "pricing_starts": pricing_starts, "master_starts": master_starts,
            "native_starts": pricing_starts+master_starts,
            "native_returns": pricing_returns+master_returns,
            "native_wall_s": math.fsum(native_wall),
            "native_accounting_complete": True,
            "polish_starts": phases_start, "polish_returns": phases_end,
            "polish_steps": steps, "polish_checks": checks,
            "polish_wall_s": math.fsum(polish_wall),
            "polish_accounting_complete": True}


def hull_context(case, case_id, market, market_id, frozen, state_identity):
    return {"id": "hull", "case": case, "case_identity": case_id,
            "physical_identity": case_id, "market_identity": market_id,
            "market": market, "pricing_oracle": ORACLE, "extraction_policy": POLICY,
            "state_identity": state_identity, "arm": "cold", "state_index": 0,
            "predecessor": None}


def state_identity(case_id, market_id, budget):
    value = {"schema": "egg-native-hull-v2", "case": case_id, "market": market_id,
             "arm": "cold", "state_index": 0, "budget": budget,
             "extraction_policy": POLICY, "pricing_oracle": ORACLE}
    return digest_json(value)


def normalize_hull_blob(stage: dict, cell: dict, budget: dict):
    raw_receipt = stage["receipt"]
    account = stage["accounting_recomputed"]
    need(raw_receipt.get("accounting") == account,
         "controller hull accounting receipt equals independent event ledger")
    receipt = {**raw_receipt, **account, "cell": cell["id"],
               "timeout": raw_receipt["hard_timeout"],
               "elapsed_s": raw_receipt["elapsed_seconds"]}
    package = copy.deepcopy(stage["result_package"])
    package["elapsed_s"] = package["elapsed_seconds"]
    return {"events": stage["events"], "receipt": receipt, "result": package}


def audit_hull_stage(case, case_id, market, market_id, frozen, stage, runtimes,
                     *, diagnostic_budget_overrun=False):
    events = stage["events"]
    result_package = stage.get("result_package")
    raw_result = stage.get("raw_result")
    need(result_package is not None and raw_result is not None
         and result_package["result"] == raw_result["result"],
         "hull assessed/raw result equality")
    budget = frozen["budgets"]["hull"]
    expected_state = state_identity(case_id, market_id, budget)
    cell = hull_context(case, case_id, market, market_id, frozen, expected_state)
    need(events and events[0].get("event") == "state_start"
         and events[0].get("state_identity") == expected_state,
         "cold full-fleet hull state identity")
    need(events[0].get("market_identity") == market_id
         and events[0].get("pricing_oracle") == ORACLE
         and events[0].get("imported_column_keys") == [],
         "hull one-cell fresh cold source identity; extraction policy is bound inside independently recomputed state identity")
    accounting = audit_hull_accounting(events)
    stage["accounting_recomputed"] = accounting
    need(accounting["native_wall_s"] <= NATIVE_WALL_CAPS["hull"] + 1e-6,
         "sum of observed hull native solve wall time stays within frozen native wall budget")
    norm = normalize_hull_blob(stage, cell, budget)
    raw_receipt = stage["receipt"]
    need(raw_receipt.get("status") == result_package["result"].get("status")
         and raw_receipt.get("pass") is True and raw_receipt.get("returncode") == 0
         and raw_receipt.get("hard_timeout") is False
         and raw_receipt.get("evidence_issues") == [], "hull stage accepted receipt")
    need(0 <= result_package["elapsed_seconds"] <= ROUTINE_CAPS["hull"]
         and raw_receipt["elapsed_seconds"] <= CHILD_CAPS["hull"],
         "hull routine and child hard caps")
    result = result_package["result"]
    need(result.get("pricing_oracle") == ORACLE
         and result.get("extraction_policy") == POLICY
         and result.get("physical_identity") == case_id
         and result.get("market_identity") == market_id
         and result.get("arm") == "cold" and result.get("state_index") == 0,
         "hull result identity and policy")
    strict_resource_error = None
    try:
        audited = hull_audit.audit_cell(cell, norm, budget)
    except AssertionError as exc:
        if not diagnostic_budget_overrun:
            raise
        strict_resource_error = str(exc)
        audited = hull_audit.audit_cell(cell, norm, budget,
                                        diagnostic_budget_overrun=True)
    need(audited.get("polish_wall_budget_compliant") is False
         or audited.get("polish_wall_budget_compliant") is True,
         "hull timing compliance is explicitly classified")
    if strict_resource_error is None:
        need(audited["polish_wall_budget_compliant"],
             "strict hull aggregate polishing time budget")
    else:
        need(not audited["polish_wall_budget_compliant"]
             and audited["polish_wall_resource_violations"],
             "strict rejection retained alongside diagnostic mathematical reconstruction")
    for event in events:
        if event["event"] == "master_status":
            hull_audit.backend_grb(event["stats"], master=True)
            runtimes.append(event["stats"]["backend_runtime"])
        elif event["event"] == "pricing_native" and event["detail"].get("event") == "native_status":
            hull_audit.backend_grb(event["detail"]["stats"])
            runtimes.append(event["detail"]["stats"]["backend_runtime"])
    stored_bounds = [Q(result_package["assessment"]["lower_exact_stored"]),
                     Q(result_package["assessment"]["upper_exact_stored"])]
    need(stored_bounds == [Q(result["lower"]), Q(result["upper"])],
         "hull assessment exact stored endpoints equal final outward result endpoints")
    return {"stage": "hull", "status": result["status"],
            "bounds": stored_bounds,
            "bounds_exact_global_certificate": audited["saved_interval"], "audit": audited,
            "strict_resource_error": strict_resource_error,
            "strict_resource_compliant": audited["polish_wall_budget_compliant"],
            "receipt": raw_receipt, "result": result}


def final_intervals(planner, hull, response, prices):
    dl, du = planner["bounds"]
    hl, hu = hull["bounds"]
    pl, pu = response["bounds"]
    gap = (dl-hu, du-hl)
    need(gap[1] >= -NEGATIVE_GUARD and gap[0] <= gap[1],
         "planner/hull gap enclosure consistency")
    if gap[0] > RESOLUTION:
        classification = "resolvably_positive_above_five"
    elif gap[1] <= RESOLUTION and gap[0] >= -NEGATIVE_GUARD:
        classification = "gap_at_most_five_under_declared_numerical_policy"
    else:
        classification = "unresolved_at_five"
    plan = planner["plan"]
    load = planner["assessment"]["replay"]["load"]
    ops = Q(planner["assessment"]["replay"]["ops_cost"])
    own_value = ops + sum((Q(p)*Q(x) for p,x in zip(prices,load)),Q(0))
    regret = (own_value-pu, own_value-pl)
    need(regret[0] <= regret[1], "own-price regret interval ordering")
    return {"gap_interval_exact_stored": [str(gap[0]),str(gap[1])],
            "gap_classification": classification,
            "resolution": str(RESOLUTION), "negative_guard": str(NEGATIVE_GUARD),
            "own_price_vector": prices, "own_price_plan_value_exact_stored": str(own_value),
            "own_price_regret_interval_exact_stored": [str(regret[0]),str(regret[1])],
            "regret_subject": ("planner_optimum_under_declared_numerical_policy"
                               if planner["status"] == "certified" else "named_planner_incumbent"),
            "planner_plan_hash": digest_json(plan),
            "used_buses": len(plan["vehicles"]),
            "claim_scope": "synthetic one-cell numerical enclosure; independent result audit pending"}


def source_and_supervisor(attempt, frozen, manifest, manifest_sha):
    expected_hashes = frozen["source_hashes"]
    need(frozen["source_commit"] == SOURCE_COMMIT, "frozen pilot source commit")
    supervisor_launch = read_json(attempt/"supervisor_launch.json")
    supervisor_receipt = read_json(attempt/"supervisor_receipt.json")
    start = read_json(attempt/"STARTED.json")
    wrapper = read_json(attempt/"slurm_wrapper_receipt.json")
    need(start.get("protocol") == PROTOCOL
         and start.get("frozen_sha256") == digest_bytes((attempt/"frozen.json").read_bytes()),
         "supervisor start receipt/frozen identity")
    need(supervisor_launch.get("outer_cap_seconds") == TOTAL_CAP
         and supervisor_launch.get("command", [])[1:4]
             == ["-m", "experiments.sistig_nonlinear_pilot", "controller"]
         and supervisor_receipt.get("protocol") == PROTOCOL
         and supervisor_receipt.get("returncode") == 0
         and supervisor_receipt.get("child_returncode") == 0
         and supervisor_receipt.get("outer_timeout") is False
         and supervisor_receipt.get("source_hashes_unchanged") is True
         and supervisor_receipt.get("source_check_error") is None
         and supervisor_receipt.get("elapsed_seconds", math.inf) <= TOTAL_CAP,
         "supervisor complete-attempt receipt")
    need(wrapper.get("returncode") == 0 and wrapper.get("timeout_exit") is False
         and wrapper.get("outer_shell_cap_seconds") == 2070
         and wrapper.get("elapsed_whole_seconds", math.inf) <= 2070,
         "post-seal Slurm wrapper receipt and shell timeout")
    need("slurm_wrapper_receipt.json" not in manifest["files"],
         "wrapper receipt is explicitly post-seal and external to supervisor manifest")
    for stage in STAGES:
        folder = attempt/stage
        need(folder.is_dir(), "all stage folders present: "+stage)
        launch = read_json(folder/"launch.json")
        cmd = launch.get("command", [])
        need(launch.get("hard_cap_seconds") == CHILD_CAPS[stage]
             and cmd[0] == frozen.get("environment", {}).get("executable")
             and cmd[1:4] == ["-m", "experiments.sistig_nonlinear_pilot", "worker"]
             and cmd[cmd.index("--stage")+1] == stage
             and cmd[cmd.index("--attempt")+1].endswith(str(ATTEMPT_REL)),
             "child stage dispatch and hard cap: "+stage)
    return {"supervisor_receipt":supervisor_receipt,"wrapper_receipt":wrapper,
            "supervisor_source_hashes_verified_against_git":len(expected_hashes),
            "manifest_sha256":manifest_sha}


def complete_corruption_controls(case, market, market_id, case_id, frozen,
                                 planner_stage, hull_stage, own_stage):
    """Copy-only negative controls for the complete three-stage replay."""
    controls = []

    def reject(label, blob, audit):
        try:
            audit(blob)
        except (AssertionError, KeyError, TypeError, ValueError,
                ZeroDivisionError, IndexError) as exc:
            controls.append({"control": label, "rejected": True,
                             "reason": str(exc)[:240]})
        else:
            raise AssertionError("complete v2 auditor accepted corruption: " + label)

    altered = copy.deepcopy(planner_stage)
    altered["raw_result"]["result"]["lower"] += 1
    altered["result_package"]["result"]["lower"] += 1
    reject("planner propagated lower bound", altered,
           lambda x: audit_physical_stage("planner", {"case": case}, market,
                                          case_id, x, [], require_accepted=True))
    altered = copy.deepcopy(planner_stage)
    projection_event = next(e for e in reversed(altered["events"])
                            if e["event"] == "charge_projection"
                            and e.get("stage") == "final")
    projection_event["whole_incumbent_total_exact"] = "1"
    reject("planner combined charge correction ledger", altered,
           lambda x: audit_physical_stage("planner", {"case": case}, market,
                                          case_id, x, [], require_accepted=True))

    def check_hull(x):
        audit_hull_stage(case, case_id, market, market_id, frozen, x, [],
                         diagnostic_budget_overrun=True)

    altered = copy.deepcopy(hull_stage)
    global_bound = next(e for e in altered["events"] if e["event"] == "global_bound")
    global_bound["certificate"]["pricing_lower"] = "999999"
    reject("hull fresh global pricing lower certificate", altered, check_hull)
    altered = copy.deepcopy(hull_stage)
    altered["raw_result"]["result"]["lower"] += 1
    altered["result_package"]["result"]["lower"] += 1
    reject("hull solver-conditioned global interval", altered, check_hull)
    altered = copy.deepcopy(hull_stage)
    weights = altered["raw_result"]["result"]["mixture"]["simplex"]["weights_exact"]
    weights[0] = "0"
    altered["result_package"]["result"]["mixture"]["simplex"]["weights_exact"][0] = "0"
    reject("hull saved mixture simplex witness", altered, check_hull)

    altered = copy.deepcopy(own_stage)
    altered["raw_result"]["result"]["prices"][0] += 0.01
    altered["result_package"]["result"]["prices"][0] += 0.01
    reject("own-price fresh response vector", altered,
           lambda x: audit_physical_stage("own_price", {"case": case}, market,
                                          case_id, x, [], require_accepted=True))
    need(len(controls) == 6 and all(x["rejected"] for x in controls),
         "all targeted physical, bound, mixture, correction and own-price corruptions rejected")
    return controls


def audit_scheduler_evidence(repo: Path, scheduler: dict, frozen: dict):
    """Independently bind the external Slurm receipt to the attempt and source."""
    outer = repo.parent / "research-20260927/cluster/nonlinear-v2-559907"
    sacct_path = outer / "SACCT-final.txt"
    transport_path = outer / "transport_receipt.json"
    tar_path = outer / "nonlinear-v2-559907-transport.tar"
    need(digest_bytes(sacct_path.read_bytes()) == scheduler.get("sacct_sha256"),
         "external final SACCT bytes match review package pin")
    need(digest_bytes(transport_path.read_bytes()) == scheduler.get("transport_receipt_sha256"),
         "external transport receipt bytes match review package pin")
    need(digest_bytes(tar_path.read_bytes()) == scheduler.get("transport_tar_sha256"),
         "full remote/local transport archive SHA-256")
    transport = read_json(transport_path)
    need(transport.get("job_id") == "559907"
         and transport.get("source_commit") == SOURCE_COMMIT
         and transport.get("frozen_sha256") == digest_bytes((repo / ATTEMPT_REL / "frozen.json").read_bytes())
         and transport.get("raw_attempt_manifest_sha256") == scheduler.get("manifest_sha256")
         and transport.get("raw_attempt_exact_file_set", "").startswith("PASS")
         and transport.get("raw_or_job_logs_modified") == "false",
         "transport receipt matches frozen v2 attempt and unchanged raw record")
    rows = [line.split("|") for line in sacct_path.read_text().splitlines() if line.strip()]
    need(len(rows) == 3 and all(len(row) == 10 for row in rows),
         "fresh SACCT has exactly job, batch and extern rows")
    by_id = {row[0]: row for row in rows}
    need(set(by_id) == {"559907", "559907.batch", "559907.extern"},
         "one scheduled v2 job, with its batch and extern records")
    top, batch, extern = by_id["559907"], by_id["559907.batch"], by_id["559907.extern"]
    need(top[2:5] == ["COMPLETED", "0:0", "00:09:36"]
         and top[6] == "snavely-cpu-16"
         and batch[2:5] == ["COMPLETED", "0:0", "00:09:36"]
         and batch[5] == "379376K"
         and extern[2:4] == ["COMPLETED", "0:0"],
         "authoritative job/batch/extern terminal accounting and elapsed time")
    requested = dict(part.split("=", 1) for part in top[7].split(",") if "=" in part)
    allocated = dict(part.split("=", 1) for part in top[8].split(",") if "=" in part)
    need(requested.get("cpu") == "1" and requested.get("mem") == "8G"
         and allocated.get("cpu") == "2" and allocated.get("mem") == "8G",
         "scheduler request and actual allocation are distinguished")
    source = subprocess.check_output(
        ["git", "show", f"{SOURCE_COMMIT}:src/cluster/sistig_nonlinear_pilot.sbatch"],
        cwd=repo)
    need(digest_bytes(source) == frozen["source_hashes"].get("src/cluster/sistig_nonlinear_pilot.sbatch"),
         "batch script source equals its published frozen Git blob")
    directives = [line.strip() for line in source.decode().splitlines()
                  if line.strip().startswith("#SBATCH")]
    need("#SBATCH --cpus-per-task=1" in directives and "#SBATCH --mem=8G" in directives
         and "#SBATCH --time=00:36:00" in directives
         and "#SBATCH --exclude=scaglione-compute-01" in directives
         and "#SBATCH --no-requeue" in directives,
         "pinned request, job length, excluded node and no-requeue policy")
    need(scheduler.get("allocated_cpus") == 2 and scheduler.get("allocated_memory") == "8G"
         and scheduler.get("requested_cpus") == 1 and scheduler.get("requested_memory") == "8G"
         and scheduler.get("elapsed") == "00:09:36"
         and scheduler.get("node") == "snavely-cpu-16"
         and scheduler.get("requeue") is False
         and scheduler.get("excluded_node") == "scaglione-compute-01",
         "review evidence summary matches independent external reconstruction")
    return {"job_id": "559907", "state": top[2], "exit_code": top[3],
            "elapsed": top[4], "node": top[6], "requested_cpus": 1,
            "requested_memory": "8G", "allocated_cpus": 2,
            "allocated_memory": "8G", "batch_max_rss": batch[5],
            "requeue": False, "excluded_node": "scaglione-compute-01",
            "sacct_sha256": scheduler["sacct_sha256"],
            "transport_receipt_sha256": scheduler["transport_receipt_sha256"],
            "transport_tar_sha256": scheduler["transport_tar_sha256"]}


def failure_scheduler_evidence(repo, frozen):
    """Parse the archived submission/SACCT record and pinned batch directives."""
    submission_dir = repo.parent / "research-20260927/cluster/nonlinear-559683/unpacked/nonlinear-submission-20260927"
    intent = read_json(submission_dir / "INTENT.json")
    submitted = read_json(submission_dir / "SUBMITTED.json")
    job_id = str(submitted.get("job_id"))
    lines = (submission_dir / "SACCT-final.txt").read_text().splitlines()
    rows = [line.split("|") for line in lines if line.strip()]
    need(all(len(row) == 8 for row in rows), "archived SACCT field shape")
    by_id = {row[0]: row for row in rows}
    need(set(by_id) == {job_id, job_id+".batch", job_id+".extern"},
         "one submitted job with batch/extern accounting rows")
    top, batch, extern = by_id[job_id], by_id[job_id+".batch"], by_id[job_id+".extern"]
    source_path = "src/cluster/sistig_nonlinear_pilot.sbatch"
    source = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{source_path}"], cwd=repo)
    need(digest_bytes(source) == frozen["source_hashes"].get(source_path),
         "Slurm directives are from the frozen published source")
    directives = [line.strip() for line in source.decode().splitlines()
                  if line.strip().startswith("#SBATCH")]
    need("#SBATCH --cpus-per-task=1" in directives
         and "#SBATCH --mem=8G" in directives
         and "#SBATCH --time=00:36:00" in directives
         and "#SBATCH --exclude=scaglione-compute-01" in directives
         and "#SBATCH --no-requeue" in directives,
         "pinned scheduler resource/exclusion/no-requeue directives")
    need(intent.get("prior_scheduler_submissions") == 0
         and intent.get("queue_and_accounting_empty") is True
         and submitted.get("source_commit") == SOURCE_COMMIT,
         "single authorized submission intent and source commit")
    need(top[1] == batch[1] == "FAILED" and top[2] == batch[2] == "1:0"
         and top[3] == batch[3] == "00:04:22" and top[4] == batch[4] == "2"
         and extern[1:3] == ["COMPLETED", "0:0"],
         "final SACCT job/batch/extern state, exit, elapsed and allocated CPUs")
    return {"job_id": job_id, "state": top[1], "exit_code": top[2],
            "requested_cpus": 1, "requested_memory": "8G",
            "allocated_cpus": int(top[4]), "allocated_memory": None,
            "elapsed": top[3], "max_rss": batch[5], "requeue": False,
            "excluded_node": "scaglione-compute-01",
            "submission_utc": submitted.get("submitted_utc"),
            "source_commit": submitted.get("source_commit"),
            "sacct_rows": {key: by_id[key][1:6] for key in sorted(by_id)},
            "directives_sha256": digest_bytes(source),
            "scontrol_snapshot_state": "PENDING before allocation; used only for requested TRES"}


def partial_physical_corruptions(stage_blob, stage, case, market, case_id):
    """Copy-only checks that the partial physical audit rejects key tampering."""
    checks = []
    def run(label, mutate):
        altered = copy.deepcopy(stage_blob)
        mutate(altered)
        try:
            audit_physical_stage(stage, {"case": case}, market, case_id,
                                 altered, [], require_accepted=False)
        except (AssertionError, KeyError, TypeError, ValueError, ZeroDivisionError, IndexError) as exc:
            checks.append({"control": label, "rejected": True,
                           "reason": str(exc)[:240]})
        else:
            raise AssertionError("partial physical auditor accepted corruption: " + label)
    def raw_repr(blob):
        snap=next(e for e in blob["events"] if e["event"]=="native_incumbent")
        snap["variables"][0]["solution"]["repr"]="not-a-number"
    def correction(blob):
        event=next(e for e in reversed(blob["events"])
                   if e["event"]=="charge_projection" and e["stage"]=="final")
        event["whole_incumbent_total_exact"]="1"
    def soc(blob):
        plan=blob["raw_result"]["result"]["plan"]
        plan["replay"]["soc_trajectories"][0][-1]["soc_kwh"]=0
        replay=next(e for e in blob["events"] if e["event"]=="replayed_iteration")
        replay["plan"]["replay"]["soc_trajectories"][0][-1]["soc_kwh"]=0
    run("raw variable representation", raw_repr)
    run("final whole-incumbent charge correction", correction)
    run("replayed terminal SOC", soc)
    need(len(checks)==3 and all(x["rejected"] for x in checks),
         "all independent partial-physical corruption controls rejected")
    return checks


def audit_failed_attempt(attempt, repo, expected_manifest_sha, scheduler):
    """Integrity/stop audit for a failed or incomplete run; never emits PASS."""
    manifest, raw_bytes = verify_manifest(attempt, expected_manifest_sha)
    frozen = read_json(attempt / "frozen.json")
    case, market, case_id, market_id, _payload = frozen_inputs(repo, frozen)
    frozen_hash = digest_bytes((attempt / "frozen.json").read_bytes())
    launch = read_json(attempt / "supervisor_launch.json")
    supervisor = read_json(attempt / "supervisor_receipt.json")
    start = read_json(attempt / "STARTED.json")
    wrapper = read_json(attempt / "slurm_wrapper_receipt.json")
    summary = read_json(attempt / "summary.json")
    need(start.get("protocol") == PROTOCOL and start.get("frozen_sha256") == frozen_hash,
         "failed attempt start receipt/frozen identity")
    need(launch.get("outer_cap_seconds") == TOTAL_CAP
         and launch.get("command", [])[1:4]
             == ["-m", "experiments.sistig_nonlinear_pilot", "controller"],
         "failed attempt supervised launch identity/cap")
    need(supervisor.get("protocol") == PROTOCOL
         and supervisor.get("returncode") != 0
         and supervisor.get("child_returncode") == 1
         and supervisor.get("outer_timeout") is False
         and supervisor.get("source_hashes_unchanged") is True
         and supervisor.get("source_check_error") is None
         and supervisor.get("elapsed_seconds", math.inf) <= TOTAL_CAP,
         "failed attempt supervisor records nonzero outcome and stable sources")
    need(wrapper.get("returncode") == supervisor["returncode"]
         and wrapper.get("timeout_exit") is (wrapper.get("returncode") in (124, 137))
         and wrapper.get("outer_shell_cap_seconds") == 2070
         and wrapper.get("elapsed_whole_seconds", math.inf) <= 2070,
         "failed attempt post-seal shell receipt")
    need("slurm_wrapper_receipt.json" not in manifest["files"],
         "post-seal Slurm wrapper receipt is outside supervisor manifest")
    need(summary.get("protocol") == PROTOCOL and summary.get("complete") is False
         and summary.get("source_hashes_unchanged") is True
         and summary.get("frozen_sha256") == frozen_hash,
         "failed attempt controller summary and source identity")
    need(summary.get("report") is None
         and summary.get("elapsed_seconds", math.inf) <= TOTAL_CAP
         and summary.get("elapsed_seconds", 0) >= max(
             r.get("elapsed_seconds", 0) for r in summary.get("stages", []))
         and supervisor.get("elapsed_seconds", 0) >= summary.get("elapsed_seconds", math.inf),
         "failed attempt has no final interval report and coherent outer/controller time")
    rows = summary.get("stages")
    unstarted = summary.get("unstarted_stages")
    need(type(rows) is list and 0 < len(rows) <= len(STAGES)
         and [r.get("stage") for r in rows] == list(STAGES[:len(rows)])
         and unstarted == list(STAGES[len(rows):]),
         "attempted and unstarted stage sequence preserved")
    need(all(not (attempt / stage).exists() for stage in unstarted),
         "unstarted stages have no launched folders")
    stage_records = []
    for row in rows:
        stage = row["stage"]
        folder = attempt / stage
        need(folder.is_dir(), "attempted stage folder present: " + stage)
        receipt = read_json(folder / "receipt.json")
        need(receipt == row, "summary/controller stage receipt equality: " + stage)
        launch = read_json(folder / "launch.json")
        cmd = launch.get("command", [])
        need(launch.get("hard_cap_seconds") == CHILD_CAPS[stage]
             and cmd[0] == frozen.get("environment", {}).get("executable")
             and cmd[1:4] == ["-m", "experiments.sistig_nonlinear_pilot", "worker"]
             and cmd[cmd.index("--stage")+1] == stage
             and cmd[cmd.index("--attempt")+1].endswith(str(ATTEMPT_REL)),
             "attempted stage command/cap: " + stage)
        events = parse_events(folder)
        if stage == "hull":
            accounted = audit_hull_accounting(events)
            need(receipt["accounting"] == accounted,
                 "failed hull receipt agrees with reconstructed call ledger")
        else:
            starts = sum(e["event"] == "native_start" for e in events)
            returns = sum(e["event"] == "native_status" for e in events)
            need(receipt["accounting"].get("native_starts") == starts
                 and receipt["accounting"].get("native_returns") == returns
                 and receipt["accounting"].get("native_accounting_complete")
                     is (starts > 0 and starts == returns),
                 "failed physical receipt agrees with native start/status count")
            need(receipt["accounting"].get("native_accounting_complete") is True,
                 "failed physical stage preserved all returned native statuses")
        statuses = []
        for event in events:
            if stage == "hull" and event["event"] == "master_status":
                statuses.append(event["stats"])
            elif stage == "hull" and event["event"] == "pricing_native" \
                    and event.get("detail", {}).get("event") == "native_status":
                statuses.append(event["detail"]["stats"])
            elif stage != "hull" and event["event"] == "native_status":
                statuses.append(event["stats"])
        for stats in statuses:
            need(stats.get("backend") == "GRB" and stats.get("threads") == 1
                 and finite(stats.get("seconds_cap")) and 0 < stats["seconds_cap"] <= 180,
                 "failed-run native telemetry retains one-thread GRB phase budget")
            rt = stats.get("backend_runtime", {})
            need(rt.get("requested") == "GRB"
                 and str(rt.get("model_solver_name", "")).upper() in ("GRB", "GUROBI")
                 and rt.get("solver_module") == "mip.gurobi",
                 "failed-run native telemetry has no backend fallback")
        raw_result = read_json(folder / "raw_result.json") if (folder / "raw_result.json").is_file() else None
        result_package = read_json(folder / "result.json") if (folder / "result.json").is_file() else None
        exception = read_json(folder / "exception.json") if (folder / "exception.json").is_file() else None
        if raw_result is not None:
            need(raw_result.get("stage") == stage
                 and raw_result.get("frozen_sha256") == frozen_hash,
                 "failed-stage raw result identity")
        if result_package is not None:
            need(result_package.get("stage") == stage
                 and result_package.get("frozen_sha256") == frozen_hash,
                 "failed-stage assessed result identity")
        stage_record = {
            "stage": stage, "pass": row.get("pass"),
            "returncode": row.get("returncode"), "hard_timeout": row.get("hard_timeout"),
            "elapsed_seconds": row.get("elapsed_seconds"),
            "routine_cap_seconds": ROUTINE_CAPS[stage],
            "events": len(events), "event_types": [e["event"] for e in events],
            "native_statuses": [s.get("status") for s in statuses],
            "native_runtime_records": len(statuses),
            "raw_result_present": raw_result is not None,
            "result_package_present": result_package is not None,
            "exception": ({"type": exception.get("type"),
                           "message": str(exception.get("message", ""))[:1000]}
                          if exception else None),
        }
        if stage in ("planner", "own_price") and raw_result is not None:
            stage_blob = {"input": read_json(folder / "input.json"),
                          "launch": launch, "receipt": receipt, "events": events,
                          "raw_result": raw_result, "result_package": result_package,
                          "exception": exception, "frozen_sha256": frozen_hash}
            partial = audit_physical_stage(stage, {"case": case}, market, case_id,
                                           stage_blob, [], require_accepted=False)
            stage_record["independent_raw_reconstruction"] = {
                "status": partial["status"],
                "stored_interval_exact": [str(x) for x in partial["bounds"]],
                "rounds": [{"round": r["round"], "native_status": r["status"],
                            "lower_exact": str(r["lower"]), "upper_exact": str(r["upper"]),
                            "lower_display": float(r["lower"]), "upper_display": float(r["upper"]),
                            "solver_incumbent": r["solver_incumbent"],
                            "solver_lower_bound": r["solver_lower_bound"],
                            "raw_variables": r["raw_variables"],
                            "max_primal_residual_exact": str(r["max_primal_residual"]),
                            "phase_cap_seconds": r.get("phase_cap_seconds"),
                            "phase_wall_seconds": r.get("phase_wall_seconds"),
                            "phase_cap_excess_seconds": r.get("phase_cap_excess_seconds"),
                            "roundoff_projection": r["roundoff_projection"],
                            "physical_witness": {
                                "ops_cost": r["physical_witness"]["ops"],
                                "grid_load": r["physical_witness"]["load"],
                                "charge_sessions": r["physical_witness"]["sessions"],
                                "soc_events": r["physical_witness"]["soc_events"],
                                "worst_soc_residual_kwh": r["physical_witness"]["worst_soc_residual_kwh"],
                                "peak_grid_kw": r["physical_witness"]["peak_kw"]}}
                           for r in partial["rounds"]],
                "used_buses": len(partial["plan"].get("vehicles", [])),
                "routine_cap_exceeded": partial["routine_cap_exceeded"],
                "worker_elapsed_seconds": exception.get("elapsed_seconds") if exception else None,
                "routine_cap_excess_seconds": (max(0.0, exception["elapsed_seconds"]-ROUTINE_CAPS[stage])
                                                if exception and exception.get("elapsed_seconds") is not None else None),
                "child_elapsed_seconds": row.get("elapsed_seconds"),
                "child_hard_cap_seconds": CHILD_CAPS[stage],
                "physical_upper_is_replayed": True,
                "overall_result_admitted": False,
            }
            stage_record["copy_only_corruption_controls"] = partial_physical_corruptions(
                stage_blob, stage, case, market, case_id)
        stage_records.append(stage_record)
    need(any(row.get("pass") is False for row in rows)
         or len(rows) < len(STAGES) or summary.get("report_error"),
         "failed/incomplete attempt has a visible failure or unstarted stage")
    if scheduler is not None:
        need(str(scheduler.get("job_id")) == "559683"
             and scheduler.get("state") == "FAILED"
             and scheduler.get("exit_code") == "1:0",
             "authoritative Slurm failure for job 559683")
        need(scheduler.get("requested_cpus") == 1
             and scheduler.get("requested_memory") == "8G"
             and scheduler.get("allocated_cpus") == 2,
             "Slurm requested and allocated resources distinguished")
        need(scheduler.get("elapsed") == "00:04:22"
             and scheduler.get("requeue") is False
             and scheduler.get("excluded_node") == "scaglione-compute-01",
             "Slurm failure timing/no-requeue/exclusion receipt")
    return {"audit_status": "FAILED_OR_INCOMPLETE_ATTEMPT_INTEGRITY_AUDITED; NO SCIENTIFIC PASS",
            "scientific_admission": False, "attempt": str(attempt.relative_to(repo)),
            "source_commit": SOURCE_COMMIT, "manifest_sha256": expected_manifest_sha,
            "manifest_files": len(manifest["files"]), "manifest_bytes": raw_bytes,
            "stage_rows": stage_records, "unstarted_stages": unstarted,
            "supervisor_returncode": supervisor["returncode"],
            "supervisor_child_returncode": supervisor.get("child_returncode"),
            "supervisor_timed_out": supervisor.get("outer_timeout"),
            "supervisor_elapsed_seconds": supervisor.get("elapsed_seconds"),
            "controller_stop_reason": summary.get("stop_reason"),
            "controller_elapsed_seconds": summary.get("elapsed_seconds"),
            "native_runtime_records": sum(s["native_runtime_records"] for s in stage_records),
            "slurm_scheduler_evidence": scheduler,
            "license_stdout_or_stderr_content_read": False,
            "interpretation": "This is an integrity and failure-preservation report only. Failed or unstarted stages are not treated as scientific results; no optimization was retried."}


def read_stage(attempt, frozen_hash, stage):
    folder=attempt/stage
    input_=read_json(folder/"input.json")
    launch=read_json(folder/"launch.json")
    receipt=read_json(folder/"receipt.json")
    events=parse_events(folder)
    raw_result=read_json(folder/"raw_result.json") if (folder/"raw_result.json").exists() else None
    result_package=read_json(folder/"result.json") if (folder/"result.json").exists() else None
    exception=read_json(folder/"exception.json") if (folder/"exception.json").exists() else None
    return {"folder":folder,"input":input_,"launch":launch,"receipt":receipt,
            "events":events,"raw_result":raw_result,"result_package":result_package,
            "exception":exception,"frozen_sha256":frozen_hash}


def audit_complete(attempt, repo, expected_manifest_sha, scheduler=None, *, public_copy=False):
    manifest,raw_bytes=verify_manifest(attempt,expected_manifest_sha,public_copy=public_copy)
    frozen=read_json(attempt/"frozen.json")
    case,market,case_id,market_id,payload=frozen_inputs(repo,frozen)
    frozen_hash=digest_bytes((attempt/"frozen.json").read_bytes())
    outer=source_and_supervisor(attempt,frozen,manifest,expected_manifest_sha)
    stages={s:read_stage(attempt,frozen_hash,s) for s in STAGES}
    runtimes=[]
    planner=audit_physical_stage("planner",{"case":case},market,case_id,
                                 stages["planner"],runtimes)
    prices=own_price_vector(market,planner)
    need(stages["own_price"]["input"].get("prices")==prices,
         "own-price stage is freshly tied to planner replay load")
    hull=audit_hull_stage(case,case_id,market,market_id,frozen,stages["hull"],runtimes,
                          diagnostic_budget_overrun=True)
    response=audit_physical_stage("own_price",{"case":case},market,case_id,
                                  stages["own_price"],runtimes)
    stage_elapsed = math.fsum(stages[s]["receipt"]["elapsed_seconds"] for s in STAGES)
    need(stage_elapsed <= outer["supervisor_receipt"]["elapsed_seconds"] + 1e-6
         and stage_elapsed <= TOTAL_CAP,
         "sum of child stage elapsed times fits the outer supervised attempt")
    need(planner["native_solver_wall_seconds"] <= NATIVE_WALL_CAPS["planner"] + 1e-6
         and response["native_solver_wall_seconds"] <= NATIVE_WALL_CAPS["own_price"] + 1e-6,
         "both physical stages stay within their v2 native wall caps")
    need(len(runtimes)>0 and len({(x.get("requested"),x.get("model_solver_name"),
         x.get("solver_module"),x.get("solver_class"),x.get("native_library_sha256"),
         x.get("native_library_path")) for x in runtimes})==1,
         "one consistent recorded GRB runtime/library fingerprint")
    report=final_intervals(planner,hull,response,prices)
    controls = complete_corruption_controls(case, market, market_id, case_id, frozen,
                                            stages["planner"], stages["hull"],
                                            stages["own_price"])
    summary=read_json(attempt/"summary.json")
    need(summary.get("protocol")==PROTOCOL and summary.get("complete") is True
         and summary.get("source_hashes_unchanged") is True
         and summary.get("frozen_sha256")==frozen_hash
         and summary.get("unstarted_stages")==[],
         "controller summary complete and source-stable")
    need(summary.get("report")==report,
         "independent exact stored-endpoint report equals controller report; differing fields="
         + repr({k:{"independent":report.get(k),"controller":summary.get("report",{}).get(k)}
                 for k in set(report)|set(summary.get("report",{}))
                 if report.get(k)!=summary.get("report",{}).get(k)}))
    need(summary.get("stages")[0].get("status") == "bounded"
         and summary.get("stages")[1].get("status") == "budget_exhausted"
         and summary.get("stages")[2].get("status") == "certified",
         "preserve planner bounded, hull budget-exhausted, and own-price certified statuses")
    need(report.get("regret_subject") == "named_planner_incumbent"
         and report.get("gap_classification") == "unresolved_at_five",
         "bounded planner regret is attributed only to its named incumbent; gap remains unresolved")
    # Operator-collected scheduler evidence is external to the sealed raw tree.
    if scheduler is not None:
        scheduler = audit_scheduler_evidence(repo, scheduler, frozen)
    else:
        raise AssertionError("complete v2 audit requires external Slurm evidence")
    corruption_controls = controls
    strict_protocol_compliant = hull["strict_resource_compliant"]
    protocol_violations = []
    for issue in hull["audit"]["polish_wall_resource_violations"]:
        if issue["kind"] == "aggregate_polish_wall_exceeds_frozen_budget":
            protocol_violations.append({
                "stage":"hull", "resource":"cumulative polish wall time",
                "frozen_cap_seconds":issue["budget_seconds"],
                "observed_seconds":issue["observed_seconds"],
                "overrun_seconds":issue["overrun_seconds"],
                "strict_helper_rejection":hull["strict_resource_error"],
                "source_semantics":("native_hull.polish_pool sets available = polish_seconds - prior cumulative polish_wall_s; "
                                    "each completed phase adds its full elapsed time, so this is an aggregate cap"),
                "protocol_semantics":"The frozen pilot protocol retains the five-second cumulative exact-polish cap.",
                "phase_wall_seconds":[{"master_call":p["master_call"],"elapsed_seconds":p["elapsed_s"],
                                       "outcome":p["outcome"]}
                                      for p in hull["audit"]["phases"]],
                "last_step_crossed_remaining_budget":{
                    "master_call":2,"step":17,
                    "elapsed_seconds":4.966242655180395,
                    "remaining_seconds_at_phase_start":4.779784589540213,
                    "phase_finish_seconds":4.9706895081326365},
            })
    need(len(protocol_violations)==1 and not strict_protocol_compliant,
         "one concrete strict frozen timing breach is explicitly recorded")
    known_budget_violation = {
        "metric":"hull.polish_wall_s",
        "observed_s":protocol_violations[0]["observed_seconds"],
        "cap_s":protocol_violations[0]["frozen_cap_seconds"],
    }
    frozen_caps = {
        "routine_seconds":ROUTINE_CAPS,
        "native_wall_seconds":NATIVE_WALL_CAPS,
        "child_hard_seconds":CHILD_CAPS,
        "whole_supervisor_seconds":TOTAL_CAP,
        "hull_phase_seconds":frozen["budgets"]["hull"]["phase_seconds"],
        "hull_pricing_calls":frozen["budgets"]["hull"]["pricing_calls"],
        "hull_master_calls":frozen["budgets"]["hull"]["master_calls"],
        "hull_pool_columns":frozen["budgets"]["hull"]["pool_cap"],
        "hull_polish_steps":frozen["budgets"]["hull"]["polish_steps"],
        "hull_rational_bits":frozen["budgets"]["hull"]["rational_bits"],
        "hull_cumulative_polish_seconds":frozen["budgets"]["hull"]["polish_seconds"],
        "planner_rounds":frozen["budgets"]["planner"]["max_rounds"],
        "own_price_calls":frozen["budgets"]["own_price"]["max_rounds"],
    }
    actual_resource_use = {
        "child_elapsed_seconds":{s:stages[s]["receipt"]["elapsed_seconds"] for s in STAGES},
        "physical_native_solver_wall_seconds":{
            "planner":planner["native_solver_wall_seconds"],
            "own_price":response["native_solver_wall_seconds"]},
        "hull_native_solver_wall_seconds":hull["audit"]["counts"]["native_wall_s"]
            if "native_wall_s" in hull["audit"]["counts"] else stages["hull"]["accounting_recomputed"]["native_wall_s"],
        "hull_polish_wall_seconds":hull["audit"]["counts"]["polish_wall_s"],
        "hull_pricing_calls":hull["audit"]["counts"]["pricing_requests"],
        "hull_master_calls":hull["audit"]["counts"]["master_calls"],
        "hull_columns":hull["audit"].get("column_count", len(hull["result"]["columns"])),
        "hull_polish_steps":hull["audit"]["counts"]["polish_steps"],
        "hull_rational_bits":hull["audit"]["counts"]["max_rational_bits"],
        "planner_rounds":len(planner["rounds"]),
        "own_price_calls":len(response["rounds"]),
        "supervisor_elapsed_seconds":outer["supervisor_receipt"]["elapsed_seconds"],
    }
    numerical_status = "PASS"
    protocol_status = "FAIL"
    return {"overall_status":"NO OVERALL PASS",
            "numerical_evidence_audit_status":numerical_status,
            "protocol_compliance_status":protocol_status,
            "reporting_scope":"off_protocol_secondary_diagnostic",
            "numerical_evidence_scope":"conditional numerical reconstruction; native GRB lower bounds remain solver-conditioned",
            "audit_status":"CONDITIONAL NUMERICAL RECONSTRUCTION COMPLETE; STRICT PROTOCOL COMPLIANCE FAIL",
            "scientific_certificate_reconstruction_valid":True,
            "strict_protocol_compliant":strict_protocol_compliant,
            "scientific_admission":False,
            "strict_budget_failure":hull["strict_resource_error"],
            "protocol_violations":protocol_violations,
            "frozen_caps":frozen_caps,
            "actual_resource_use":actual_resource_use,
            "attempt":str(ATTEMPT_REL),
            "source_commit":SOURCE_COMMIT,
            "frozen_sha256":frozen_hash,
            "raw_manifest_sha256":expected_manifest_sha,
            "manifest_sha256":expected_manifest_sha,
            "known_budget_violation":known_budget_violation,
            "manifest_files":len(manifest["files"]),"manifest_bytes":raw_bytes,
            "source_hashes_checked":len(frozen["source_hashes"]),
            "public_copy_mode":public_copy,
            "public_manifest_sha256":PUBLIC_MANIFEST_SHA256 if public_copy else None,
            "solver_conditioned_scope":True,"physical":planner,"hull":hull,
            "own_price":response,"report":report,"runtime_records":len(runtimes),
            "slurm_scheduler_evidence":scheduler,
            "corruption_controls":corruption_controls,
            "stage_elapsed_sum_seconds":stage_elapsed,
            "native_wall_caps_seconds":NATIVE_WALL_CAPS,
            "interpretation":"GRB global MIP lower bounds are solver-conditioned. Physical replay and mixture uppers are independently reconstructed; no exact full 37-service optimum was enumerated or claimed. The planner is bounded, so own-price regret applies to the named planner incumbent only. The physical-versus-hull interval is unresolved at five; positive incumbent regret is not evidence of a positive public gap."}


def corruption_plan():
    """Meaningful post-run copy-only corruptions, applied only after a full run."""
    return ["manifest byte/size mismatch", "frozen source or case identity drift",
            "physical raw flow/SOC/energy-row variable corruption",
            "physical replay charge/connector/terminal SOC corruption",
            "planner tangent history or propagated global interval corruption",
            "hull global pricing lower/Fenchel certificate corruption",
            "hull column policy/key or mixture simplex/upper corruption",
            "own-price vector substitution or response interval corruption",
            "native backend/call accounting, phase/routine/child/outer timeout corruption",
            "supervisor source-drift or post-seal wrapper receipt corruption"]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository",type=Path,required=True)
    parser.add_argument("--attempt",type=Path,required=True)
    parser.add_argument("--manifest-sha256",required=True)
    parser.add_argument("--scheduler-json",type=Path)
    parser.add_argument("--public-copy",action="store_true",
                        help="validate only the exact pinned public subset; full raw mode remains the default")
    parser.add_argument("--out",type=Path,default=HERE/"audit-report.json")
    args=parser.parse_args(argv)
    repo=args.repository.resolve();attempt=args.attempt.resolve();out=args.out.resolve()
    if args.public_copy:
        need(attempt != repo/ATTEMPT_REL and (attempt/"PUBLIC_MANIFEST.json").is_file()
             and attempt.is_relative_to(repo),
             "public mode requires a separate in-repository public-copy layout with its pinned omission manifest")
    else:
        need(attempt==repo/ATTEMPT_REL,"full mode is restricted to the frozen exclusive v2 raw path")
    need(out.parent==HERE.resolve() and not out.exists() and not out.is_symlink(),
         "fresh audit output outside raw run")
    if not (attempt/"MANIFEST.json").is_file():
        print("NO SEALED ARCHIVE; result audit not performed; no PASS issued")
        return 3
    scheduler_path = args.scheduler_json or (HERE/"scheduler-evidence.json")
    scheduler=read_json(scheduler_path) if scheduler_path.is_file() else None
    started=time.perf_counter()
    summary=read_json(attempt/"summary.json")
    if summary.get("complete") is True:
        report=audit_complete(attempt,repo,args.manifest_sha256,scheduler,
                              public_copy=args.public_copy)
    else:
        if scheduler is None:
            scheduler=failure_scheduler_evidence(repo,read_json(attempt/"frozen.json"))
        report=audit_failed_attempt(attempt,repo,args.manifest_sha256,scheduler)
    report["audit_wall_seconds"]=time.perf_counter()-started
    serializable=base.pack(report)
    raw=json.dumps(serializable,sort_keys=True,indent=2,allow_nan=False).encode()+b"\n"
    out.write_bytes(raw)
    print(json.dumps({"audit_status":report["audit_status"],"out":str(out),
                      "manifest_sha256":args.manifest_sha256,
                      "native_runtime_records":report.get("native_runtime_records", report.get("runtime_records")),
                      "claim_scope":report["interpretation"]},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
