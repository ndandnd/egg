#!/usr/bin/env python3
"""Independent standard-library audit of the frozen Sistig matching archive.

This script intentionally does not import the adapter, matching implementation,
native model, or any optimizer. It reconstructs from the frozen serialized
cases and independently checks the assignment primal/dual certificates.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
ATTEMPT = ROOT / "result/sistig_matching/20260927-attempt1"
REVIEW = ATTEMPT / "review"
PAYLOAD = ROOT / "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
NATIVE_SCHEMA = "egg-native-recharge-v1"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def stored(value) -> Fraction:
    """Exact rational representation of a parsed JSON number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Not a stored finite number: {value!r}")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Nonfinite stored float")
        return Fraction.from_float(value)
    return Fraction(value)


def rational_text(value: str) -> Fraction:
    return Fraction(value)


def canonical_identity(case: dict) -> str:
    material = {"schema": NATIVE_SCHEMA, "case": case}
    encoded = json.dumps(material, sort_keys=True, allow_nan=False).encode()
    return sha_bytes(encoded)


def fail_if(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def reconstruct(case: dict, price: Fraction) -> dict:
    trips = case["trips"]
    n = len(trips)
    trip_index = {trip["id"]: i for i, trip in enumerate(trips)}
    fail_if(len(trip_index) == n, "duplicate service IDs")
    by_out: dict[str, tuple[Fraction, str]] = {}
    by_in: dict[str, tuple[Fraction, str]] = {}
    by_arc: dict[tuple[str, str], tuple[Fraction, str]] = {}
    mode_cost: dict[str, Fraction] = {}
    deadhead_rate = stored(case["deadhead_cost_per_min"])
    efficiency = stored(case["efficiency"])

    for mode in case["movements"]:
        energy = sum((stored(leg["energy_kwh"]) for leg in mode["legs"]), Fraction(0))
        duration = sum((stored(leg["arrive_min"]) - stored(leg["depart_min"])
                        for leg in mode["legs"]), Fraction(0))
        weight = deadhead_rate * duration + price * energy / efficiency
        mode_id = mode["id"]
        fail_if(mode_id not in mode_cost, f"duplicate movement ID {mode_id}")
        mode_cost[mode_id] = weight
        item = (weight, mode_id)
        if mode["kind"] == "pullout":
            key = mode["after"]
            if key not in by_out or item < by_out[key]:
                by_out[key] = item
        elif mode["kind"] == "pullin":
            key = mode["before"]
            if key not in by_in or item < by_in[key]:
                by_in[key] = item
        elif mode["kind"] in ("direct", "depot"):
            before, after = mode["before"], mode["after"]
            i, j = trip_index[before], trip_index[after]
            fail_if(stored(trips[i]["end_min"]) <= stored(trips[j]["start_min"]),
                    f"nonchronological connection {before}->{after}")
            key = (before, after)
            if key not in by_arc or item < by_arc[key]:
                by_arc[key] = item
        else:
            raise AssertionError(f"unknown movement kind {mode['kind']!r}")

    fail_if(set(by_out) == set(trip_index), "incomplete pullout coverage")
    fail_if(set(by_in) == set(trip_index), "incomplete pullin coverage")
    service = price * sum((stored(t["energy_kwh"]) for t in trips), Fraction(0)) / efficiency
    fixed_bus = stored(case["vehicle_cost"])
    baseline = service + sum((fixed_bus + by_out[t["id"]][0] + by_in[t["id"]][0]
                              for t in trips), Fraction(0))
    matrix: list[list[Fraction | None]] = []
    selected_arc_mode: dict[tuple[int, int], str] = {}
    for i, ti in enumerate(trips):
        row: list[Fraction | None] = [None] * n + [Fraction(0)] * n
        for (before, after), (cost, mode_id) in by_arc.items():
            if before == ti["id"]:
                j = trip_index[after]
                row[j] = cost - by_in[before][0] - by_out[after][0] - fixed_bus
                selected_arc_mode[i, j] = mode_id
        matrix.append(row)
    allowed = sum(value is not None for row in matrix for value in row)
    scale = math.lcm(*(value.denominator for row in matrix for value in row
                       if value is not None))
    return {"matrix": matrix, "baseline": baseline, "service": service,
            "by_out": by_out, "by_in": by_in, "by_arc": by_arc,
            "mode_cost": mode_cost, "selected_arc_mode": selected_arc_mode,
            "trip_ids": [t["id"] for t in trips], "allowed_edges": allowed,
            "integer_scale": scale}


def verify_certificate(matrix: list[list[Fraction | None]], certificate: dict) -> dict:
    n, m = len(matrix), len(matrix[0])
    assignment = certificate["assignment"]
    fail_if(len(assignment) == n, "assignment row count")
    fail_if(all(type(j) is int and 0 <= j < m for j in assignment), "assignment index domain")
    fail_if(len(set(assignment)) == n, "assignment column uniqueness")
    fail_if(all(matrix[i][j] is not None for i, j in enumerate(assignment)),
            "assignment uses a forbidden edge")
    u = [rational_text(x) for x in certificate["row_potentials"]]
    v = [rational_text(x) for x in certificate["column_potentials"]]
    fail_if(len(u) == n and len(v) == m, "dual dimensions")
    fail_if(all(x <= 0 for x in v), "column-potential sign")
    edge_count = 0
    min_slack = None
    for i in range(n):
        for j in range(m):
            cost = matrix[i][j]
            if cost is None:
                continue
            edge_count += 1
            slack = cost - u[i] - v[j]
            fail_if(slack >= 0, f"dual inequality violated at ({i},{j})")
            min_slack = slack if min_slack is None else min(min_slack, slack)
    primal = sum((matrix[i][j] for i, j in enumerate(assignment)), Fraction(0))
    dual = sum(u, Fraction(0)) + sum(v, Fraction(0))
    declared = rational_text(certificate["objective"])
    scale = int(certificate["integer_scale"])
    expected_scale = math.lcm(*(x.denominator for row in matrix for x in row if x is not None))
    fail_if(scale == expected_scale, "reported integer scale")
    fail_if(primal == dual == declared, "exact primal/dual objective equality")
    selected_tight = sum(matrix[i][j] - u[i] - v[j] == 0
                         for i, j in enumerate(assignment))
    unused_columns = set(range(m)) - set(assignment)
    unused_zero = sum(v[j] == 0 for j in unused_columns)
    fail_if(selected_tight == n, "selected-edge complementary slackness")
    fail_if(unused_zero == len(unused_columns), "unused-column complementary slackness")
    return {"rows": n, "columns": m, "allowed_edges": edge_count,
            "unique_assigned_columns": len(set(assignment)),
            "assigned_real_successors": sum(j < n for j in assignment),
            "assigned_dummy_unmatched": sum(j >= n for j in assignment),
            "dual_inequalities_checked": edge_count,
            "nonpositive_column_potentials_checked": len(v),
            "selected_edges_tight": selected_tight,
            "unused_columns_with_zero_potential": unused_zero,
            "unused_columns": len(unused_columns),
            "minimum_dual_slack_exact": str(min_slack),
            "primal_exact": str(primal), "dual_exact": str(dual),
            "integer_scale": str(scale)}


def corruption_controls(matrix, certificate) -> list[dict]:
    n, m = len(matrix), len(matrix[0])
    checks = []

    def rejected(label, mutate):
        bad = deepcopy(certificate)
        mutate(bad)
        try:
            verify_certificate(matrix, bad)
        except (AssertionError, ValueError, TypeError, ZeroDivisionError):
            checks.append({"control": label, "rejected": True})
        else:
            raise AssertionError(f"Corrupted certificate unexpectedly passed: {label}")

    rejected("duplicate assignment column", lambda c: c["assignment"].__setitem__(1, c["assignment"][0]))
    missing = next((j for j in range(n) if matrix[0][j] is None and j not in certificate["assignment"]), None)
    fail_if(missing is not None, "could not construct forbidden-edge corruption")
    rejected("forbidden selected edge", lambda c: c["assignment"].__setitem__(0, missing))
    rejected("violated row dual inequality", lambda c: c["row_potentials"].__setitem__(0,
             str(rational_text(c["row_potentials"][0]) + 1)))
    rejected("positive column potential", lambda c: c["column_potentials"].__setitem__(0, "1"))
    rejected("wrong primal/dual objective", lambda c: c.__setitem__("objective",
             str(rational_text(c["objective"]) + 1)))
    unused_dummy = next(j for j in range(n, m) if j not in certificate["assignment"])
    rejected("nonzero dual on unused column", lambda c: c["column_potentials"].__setitem__(unused_dummy, "-1"))
    return checks


def main() -> None:
    frozen_path = ATTEMPT / "frozen.json"
    frozen = json.loads(frozen_path.read_text())
    report: dict = {"review": "independent exact reconstruction of frozen matching output",
                    "verdict": "PASS", "optimizer_invoked": False,
                    "author_adapter_or_relaxation_imported": False,
                    "attempt_relative_path": str(ATTEMPT.relative_to(ROOT)),
                    "frozen_sha256": sha_file(frozen_path),
                    "payload_sha256": sha_file(PAYLOAD), "cases": []}
    fail_if(frozen["protocol"] == "sistig-matching-relaxation-20260927-v1", "protocol ID")
    fail_if(frozen["algorithm_calls"] == 2, "frozen call count")
    fail_if(frozen["price_input"] == 0.2, "frozen price input")
    price = rational_text(frozen["price_exact"])
    fail_if(price == stored(frozen["price_input"]), "exact float price encoding")
    fail_if(report["payload_sha256"] == frozen["source_hashes"].get(
        "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"), "public payload hash")

    # Verify every dependency against both the committed object and the live file.
    source_checks = {}
    for name, expected in frozen["source_hashes"].items():
        live = ROOT / name
        live_sha = sha_file(live)
        blob = subprocess.check_output(["git", "show", f"{frozen['source_commit']}:{name}"], cwd=ROOT)
        blob_sha = sha_bytes(blob)
        source_checks[name] = {"frozen_sha256": expected, "live_sha256": live_sha,
                               "committed_blob_sha256": blob_sha,
                               "live_matches_frozen": live_sha == expected,
                               "commit_matches_frozen": blob_sha == expected}
        fail_if(live_sha == expected and blob_sha == expected, f"dependency mismatch: {name}")
    report["source_integrity"] = {"commit": frozen["source_commit"],
                                  "dependencies_checked": len(source_checks),
                                  "all_live_and_committed_hashes_match": True,
                                  "files": source_checks}

    public = json.loads(PAYLOAD.read_text())
    variants = public["native_cases"]
    fail_if(len(variants) == 2 and len(frozen["cases"]) == 2, "two full depot cases")
    fail_if([v["selected_depot_id"] for v in variants] == [15, 16], "public depot order")
    fail_if(frozen["case_identities"] == [v["case_identity"] for v in variants], "payload case IDs")

    for pos, depot in enumerate((15, 16)):
        case = frozen["cases"][pos]
        variant = variants[pos]
        identity = canonical_identity(case)
        fail_if(identity == frozen["case_identities"][pos] == variant["case_identity"],
                f"case {depot} identity")
        fail_if(case["name"] == variant["case_name"], "case name")
        fail_if(case["trips"] == [x["native"] for x in variant["trips"]], "service records differ from payload")
        fail_if(case["movements"] == variant["movement_modes"], "movement modes differ from payload")
        fail_if(case["resources"] == [variant["resource_policy"]], "resource identity")
        fail_if(case["market_edges_min"] == variant["market_edges_min"], "market edges")
        fail_if(case["depot"] == variant["selected_depot_native_place"], "selected depot")
        fail_if(len(case["trips"]) == variant["service_count"] == 37, "service coverage")
        fail_if(case["max_vehicles"] == variant["vehicle_cap"] == 37, "vehicle cap")
        fail_if(case["battery_kwh"] == 400.0 and case["reserve_kwh"] == 0.0
                and case["efficiency"] == 1.0, "frozen battery/efficiency")
        fail_if(case["terminal_open_min"] == 0 and case["recharge_deadline_min"] == 1800,
                "frozen terminal interval")
        fail_if(len(case["movements"]) == sum(variant["movement_mode_counts"].values()),
                "mode count coverage")

        result_path = ATTEMPT / f"depot_{depot}.json"
        result = json.loads(result_path.read_text())
        derived = reconstruct(case, price)
        fail_if(result["source_depot_id"] == depot and result["case_identity"] == identity,
                f"result {depot} identity")
        fail_if(result["flat_price"] == frozen["price_exact"], "result price")
        fail_if(rational_text(result["service_constant_exact"]) == derived["service"],
                "service energy cost")
        fail_if(rational_text(result["baseline_exact"]) == derived["baseline"], "singleton baseline")
        fail_if(result["certificate"]["integer_scale"] == str(derived["integer_scale"]),
                "matrix integer scale")
        certificate_summary = verify_certificate(derived["matrix"], result["certificate"])
        certificate = result["certificate"]
        n = len(case["trips"])
        assignment = certificate["assignment"]
        real_pairs = [(i, j) for i, j in enumerate(assignment) if j < n]
        incoming = {j for _, j in real_pairs}
        outgoing = {i for i, _ in real_pairs}
        selected_ids = [derived["selected_arc_mode"][pair] for pair in real_pairs]
        selected_ids += [derived["by_out"][derived["trip_ids"][i]][1]
                         for i in range(n) if i not in incoming]
        selected_ids += [derived["by_in"][derived["trip_ids"][i]][1]
                         for i in range(n) if i not in outgoing]
        fail_if(len(selected_ids) == len(set(selected_ids)), "duplicate decoded movement ID")
        fail_if(sorted(selected_ids) == result["selected_movement_ids"], "decoded selected movement IDs")
        objective = derived["baseline"] + rational_text(certificate_summary["primal_exact"])
        fail_if(objective == rational_text(result["lower_exact"]), "baseline plus assignment objective")
        direct = derived["service"] + stored(case["vehicle_cost"]) * (n - len(real_pairs))
        direct += sum((derived["mode_cost"][mid] for mid in selected_ids), Fraction(0))
        fail_if(direct == objective, "independent decoded movement objective")

        # Verify the selected directed matching is a complete acyclic path cover.
        successor = {i: j for i, j in real_pairs}
        fail_if(len(successor) == len(outgoing), "successor degree")
        fail_if(len(incoming) == len(real_pairs), "predecessor degree")
        starts = [i for i in range(n) if i not in incoming]
        visited = []
        for start in starts:
            node = start
            while True:
                fail_if(node not in visited, "selected connection cycle/repeated service")
                visited.append(node)
                if node not in successor:
                    break
                node = successor[node]
        fail_if(sorted(visited) == list(range(n)), "path cover omits or duplicates a service")
        fail_if(len(starts) == n - len(real_pairs), "relaxation path count")

        corruptions = corruption_controls(derived["matrix"], certificate)
        case_entry = {"depot": depot, "case_identity": identity,
                      "services": len(case["trips"]), "movement_modes": len(case["movements"]),
                      "movement_counts_by_kind": variant["movement_mode_counts"],
                      "unique_directed_connection_pairs": len(derived["by_arc"]),
                      "assignment": certificate_summary,
                      "baseline_exact": str(derived["baseline"]),
                      "service_constant_exact": str(derived["service"]),
                      "lower_exact": str(objective), "lower_float_display": float(objective),
                      "real_connections_selected": len(real_pairs),
                      "relaxation_paths": len(starts),
                      "selected_modes_count": len(selected_ids),
                      "independent_objective_equalities": 2,
                      "corruption_controls": corruptions,
                      "all_checks_passed": True}
        report["cases"].append(case_entry)

    summary = json.loads((ATTEMPT / "summary.json").read_text())
    started = json.loads((ATTEMPT / "STARTED.json").read_text())
    supervisor = json.loads((ATTEMPT / "supervisor_receipt.json").read_text())
    launch = json.loads((ATTEMPT / "supervisor_launch.json").read_text())
    original_manifest = json.loads((ATTEMPT / "MANIFEST.json").read_text())
    fail_if(started["frozen_sha256"] == report["frozen_sha256"], "STARTED frozen hash")
    fail_if(summary["frozen_sha256"] == report["frozen_sha256"], "summary frozen hash")
    fail_if(summary["algorithm_calls"] == 2 and summary["status"] == "completed", "summary status")
    fail_if(summary["lower_exact"] == [c["lower_exact"] for c in report["cases"]],
            "summary exact outputs")
    fail_if(summary["native_optimizer_invoked"] is False, "optimizer claim flag")
    fail_if(summary["source_hashes_unchanged"] is True, "runner source-integrity receipt")
    fail_if(supervisor["exit_code"] == 0 and not supervisor["timed_out"]
            and supervisor["exception"] is None and supervisor["hard_cap_seconds"] == 45,
            "supervisor completion receipt")
    fail_if(supervisor["source_hashes_unchanged"] is True, "supervisor source-integrity receipt")
    fail_if(summary["elapsed_seconds"] <= frozen["complete_seconds_cap"], "routine cap")
    fail_if(supervisor["elapsed_seconds"] <= frozen["external_process_seconds_cap"], "child cap")
    fail_if(len(launch["command"]) >= 4 and launch["command"][1:4] ==
            ["-m", "experiments.sistig_matching_relaxation", "run"], "supervisor command")
    fail_if(launch["frozen_sha256"] == report["frozen_sha256"], "launch frozen hash")
    fail_if((ATTEMPT / "stdout.txt").stat().st_size == 0
            and (ATTEMPT / "stderr.txt").stat().st_size == 0, "expected empty child logs")
    for c in report["cases"]:
        fail_if(c["all_checks_passed"] and len(c["corruption_controls"]) == 6
                and all(x["rejected"] for x in c["corruption_controls"]), "audit/corruption status")

    listed = original_manifest["files"]
    actual_names = sorted(str(p.relative_to(ATTEMPT)) for p in ATTEMPT.rglob("*")
                          if p.is_file() and p.name != "MANIFEST.json"
                          and p.relative_to(ATTEMPT).parts[0] != "review")
    fail_if(sorted(listed) == actual_names, "original manifest file set")
    for name, meta in listed.items():
        path = ATTEMPT / name
        fail_if(path.stat().st_size == meta["bytes"] and sha_file(path) == meta["sha256"],
                f"original manifest content: {name}")
    report["archive_integrity"] = {"original_manifest_entries": len(listed),
                                   "all_original_files_match_bytes_and_sha256": True,
                                   "stdout_bytes": (ATTEMPT / "stdout.txt").stat().st_size,
                                   "stderr_bytes": (ATTEMPT / "stderr.txt").stat().st_size,
                                   "routine_elapsed_seconds": summary["elapsed_seconds"],
                                   "supervised_elapsed_seconds": supervisor["elapsed_seconds"],
                                   "source_hashes_unchanged": True}

    command = launch["command"][0]
    probe = subprocess.check_output([command, "-c",
        "import json,platform,sys;print(json.dumps({'python':sys.version,'platform':platform.platform()}))"],
        text=True)
    actual_runtime = json.loads(probe)
    fail_if(actual_runtime["python"] == frozen["python"]
            and actual_runtime["platform"] == frozen["platform"], "launcher runtime identity")
    report["runtime"] = {"frozen_python": frozen["python"], "probed_python": actual_runtime["python"],
                         "frozen_platform": frozen["platform"],
                         "probed_platform": actual_runtime["platform"],
                         "interpreter_path": command, "exact_match": True}
    # The exact script hash is recorded for this independent audit implementation.
    report["independent_script_sha256"] = sha_file(Path(__file__))
    (REVIEW / "audit-report.json").write_text(json.dumps(report, sort_keys=True, indent=2,
                                                            allow_nan=False) + "\n")
    print(json.dumps({"verdict": report["verdict"],
                      "lower_bounds": [x["lower_float_display"] for x in report["cases"]],
                      "certificate_edges_checked": [x["assignment"]["dual_inequalities_checked"]
                                                     for x in report["cases"]],
                      "corruption_controls_per_case": [len(x["corruption_controls"])
                                                       for x in report["cases"]]}, sort_keys=True))


if __name__ == "__main__":
    main()
