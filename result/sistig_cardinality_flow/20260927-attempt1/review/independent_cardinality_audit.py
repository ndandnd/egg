#!/usr/bin/env python3
"""Independent exact audit of the sealed Sistig cardinality-flow result.

Uses only the Python standard library. It reconstructs costs and the fixed-flow
network from frozen JSON, then checks the saved primal-dual certificate. It
never imports or calls the flow solver, its verifier, a native optimizer, or
an author runner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ATTEMPT = REPO / "result/sistig_cardinality_flow/20260927-attempt1"
PUBLIC = REPO / "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
OLD_MATCH = REPO / "result/sistig_matching/20260927-attempt1"
NATIVE_AUDIT = REPO / "result/sistig_pricing/20260927-grb-job557543-attempt1/review/numerical-audit.json"
EXPECTED_IDENTITIES = [
    "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7",
    "216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d",
]
EXPECTED_PAYLOAD_SHA256 = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"


def load(path: Path):
    return json.loads(path.read_text())


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def q(value) -> Fraction:
    """Exact rational for an integer, parsed binary float, or fraction string."""
    if isinstance(value, Fraction):
        return value
    return Fraction(value)


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def check_manifest(attempt: Path):
    manifest = load(attempt / "MANIFEST.json")
    require(manifest.get("protocol") is not None, f"{attempt}: missing protocol")
    entries = manifest["files"]
    expected_names = set(entries)
    actual_names = {
        p.name for p in attempt.iterdir()
        if p.is_file() and p.name != "MANIFEST.json"
    }
    require(actual_names == expected_names,
            f"{attempt}: manifest file set mismatch: "
            f"missing={sorted(expected_names-actual_names)}, "
            f"extra={sorted(actual_names-expected_names)}")
    for name, record in entries.items():
        data = (attempt / name).read_bytes()
        require(len(data) == record["bytes"], f"{attempt}/{name}: byte count mismatch")
        require(sha(data) == record["sha256"], f"{attempt}/{name}: SHA-256 mismatch")
    return {"files": len(entries), "all_bytes_and_hashes_match": True}


def movement_cost(movement, case, price: Fraction) -> Fraction:
    efficiency = q(case["efficiency"])
    deadhead = q(case["deadhead_cost_per_min"])
    total = Fraction(0)
    for leg in movement["legs"]:
        duration = q(leg["arrive_min"]) - q(leg["depart_min"])
        energy = q(leg["energy_kwh"])
        total += price * energy / efficiency + deadhead * duration
    return total


def expected_network(case, price, connection_kinds=("direct", "depot")):
    trips = case["trips"]
    n = len(trips)
    require(n == 37, f"{case['depot']}: expected 37 services, got {n}")
    trip_ids = [t["id"] for t in trips]
    require(len(set(trip_ids)) == n, f"{case['depot']}: duplicate service IDs")
    index = {trip_id: i for i, trip_id in enumerate(trip_ids)}
    movements = case["movements"]

    service_constant = sum(
        (q(t["energy_kwh"]) * price / q(case["efficiency"]) for t in trips),
        Fraction(0),
    )
    pullout_modes = {trip_id: [] for trip_id in trip_ids}
    pullin_modes = {trip_id: [] for trip_id in trip_ids}
    connection_modes = {}
    for m in movements:
        if m["kind"] == "pullout":
            require(m["after"] in pullout_modes, f"unknown pullout service in {m['id']}")
            pullout_modes[m["after"]].append((movement_cost(m, case, price), m["id"]))
        elif m["kind"] == "pullin":
            require(m["before"] in pullin_modes, f"unknown pullin service in {m['id']}")
            pullin_modes[m["before"]].append((movement_cost(m, case, price), m["id"]))
        elif m["kind"] in ("direct", "depot"):
            if m["kind"] not in connection_kinds:
                continue
            require(m["before"] in index and m["after"] in index,
                    f"unknown {m['kind']} endpoint in {m['id']}")
            pair = (index[m["before"]], index[m["after"]])
            connection_modes.setdefault(pair, []).append(
                (movement_cost(m, case, price), m["id"])
            )
        else:
            raise AssertionError(f"unrecognized movement kind {m['kind']!r}")

    require(all(pullout_modes[t] for t in trip_ids), "service without a pullout mode")
    require(all(pullin_modes[t] for t in trip_ids), "service without a pullin mode")
    cheapest_pullout = {
        t: min(pullout_modes[t], key=lambda pair: (pair[0], pair[1]))
        for t in trip_ids
    }
    cheapest_pullin = {
        t: min(pullin_modes[t], key=lambda pair: (pair[0], pair[1]))
        for t in trip_ids
    }
    vehicle = q(case["vehicle_cost"])
    baseline = (
        service_constant
        + n * vehicle
        + sum((x[0] for x in cheapest_pullout.values()), Fraction(0))
        + sum((x[0] for x in cheapest_pullin.values()), Fraction(0))
    )

    expected = {}
    nodes = {"s", "t", "g"}
    nodes.update(f"R{i}" for i in range(n))
    nodes.update(f"C{j}" for j in range(n))

    def add(arc_id, tail, head, capacity, cost):
        require(arc_id not in expected, f"duplicate reconstructed arc {arc_id}")
        expected[arc_id] = {
            "tail": tail, "head": head, "capacity": capacity, "cost": cost,
        }

    for i in range(n):
        add(f"source:{i}", "s", f"R{i}", 1, Fraction(0))
        add(f"unmatched:{i}", f"R{i}", "t", 1, Fraction(0))

    cheapest_connection = {}
    for (i, j), modes in connection_modes.items():
        mode_cost, movement_id = min(modes, key=lambda pair: (pair[0], pair[1]))
        # A connection replaces the predecessor's least pullin, successor's
        # least pullout, and one bus from the independent baseline.
        delta = (
            mode_cost
            - cheapest_pullin[trip_ids[i]][0]
            - cheapest_pullout[trip_ids[j]][0]
            - vehicle
        )
        cheapest_connection[(i, j)] = (delta, movement_id, len(modes))
        add(f"real:{i}:{j}", f"R{i}", f"C{j}", 1, delta)

    for j in range(n):
        add(f"column:{j}", f"C{j}", "g", 1, Fraction(0))
    gate_capacity = n - 2
    add("gate", "g", "t", gate_capacity, Fraction(0))

    return {
        "arcs": expected,
        "nodes": nodes,
        "trip_ids": trip_ids,
        "service_constant": service_constant,
        "baseline": baseline,
        "vehicle": vehicle,
        "cheapest_pullout": cheapest_pullout,
        "cheapest_pullin": cheapest_pullin,
        "cheapest_connection": cheapest_connection,
        "connection_pairs": len(connection_modes),
        "connection_modes": sum(len(modes) for modes in connection_modes.values()),
        "movement_counts": dict(Counter(m["kind"] for m in movements)),
    }


def verify_result(case, result, price, identity,
                  connection_kinds=("direct", "depot")):
    n = len(case["trips"])
    model = expected_network(case, price, connection_kinds)
    require(result["protocol"] == "sistig-cardinality-flow-20260927-v1",
            "result protocol mismatch")
    require(result["case_identity"] == identity, "result case identity mismatch")
    require(result["source_depot_id"] == int(case["depot"][1:]),
            "result depot mismatch")
    require(q(result["flat_price"]) == price, "result flat price mismatch")

    require(q(result["service_constant_exact"]) == model["service_constant"],
            "service constant differs from independent reconstruction")
    require(q(result["baseline_exact"]) == model["baseline"],
            "baseline differs from independent reconstruction")

    cert = result["certificate"]
    arcs = cert["arcs"]
    require(len(arcs) == len(model["arcs"]), "certificate arc count mismatch")
    cert_by_id = {}
    for arc in arcs:
        arc_id = arc["id"]
        require(arc_id not in cert_by_id, f"duplicate certificate arc {arc_id}")
        cert_by_id[arc_id] = arc
    require(set(cert_by_id) == set(model["arcs"]), "certificate arc set mismatch")
    for arc_id, expected in model["arcs"].items():
        actual = cert_by_id[arc_id]
        require(actual["tail"] == expected["tail"], f"{arc_id}: tail mismatch")
        require(actual["head"] == expected["head"], f"{arc_id}: head mismatch")
        require(type(actual["capacity"]) is int and
                actual["capacity"] == expected["capacity"],
                f"{arc_id}: capacity mismatch")
        require(q(actual["cost"]) == expected["cost"], f"{arc_id}: cost mismatch")

    flow = cert["flow"]
    require(set(flow) == set(model["arcs"]), "flow arc set mismatch")
    for arc_id, amount in flow.items():
        require(type(amount) is int, f"{arc_id}: flow is not an integer")
        cap = model["arcs"][arc_id]["capacity"]
        require(0 <= amount <= cap, f"{arc_id}: flow outside capacity")

    potential_raw = cert["potential"]
    require(set(potential_raw) == model["nodes"], "potential node set mismatch")
    potential = {node: q(value) for node, value in potential_raw.items()}
    require(potential["t"] == 0, "sink potential is not normalized to zero")
    balance = {node: 0 for node in model["nodes"]}
    primal = Fraction(0)
    dual = Fraction(0)
    for arc_id, arc in model["arcs"].items():
        amount = flow[arc_id]
        balance[arc["tail"]] += amount
        balance[arc["head"]] -= amount
        primal += arc["cost"] * amount
        reduced = arc["cost"] - potential[arc["tail"]] + potential[arc["head"]]
        if amount < arc["capacity"]:
            require(reduced >= 0, f"{arc_id}: negative forward residual cost")
        if amount > 0:
            require(reduced <= 0, f"{arc_id}: negative reverse residual cost")
        dual += arc["capacity"] * min(Fraction(0), reduced)

    supplies = {node: 0 for node in model["nodes"]}
    supplies["s"] = n
    supplies["t"] = -n
    require(balance == supplies, "flow conservation/supply mismatch")
    dual += sum((supplies[v] * potential[v] for v in model["nodes"]), Fraction(0))
    require(q(cert["network_cost"]) == primal, "saved network objective mismatch")
    require(primal == dual, "exact primal-dual certificate mismatch")

    expected_lower = model["baseline"] + primal
    require(q(result["lower_exact"]) == expected_lower,
            "published exact lower bound mismatch")

    selected_real = []
    for (i, j), (delta, movement_id, _) in model["cheapest_connection"].items():
        if flow[f"real:{i}:{j}"]:
            selected_real.append(movement_id)
    unmatched_rows = [i for i in range(n) if flow[f"unmatched:{i}"] == 1]
    unused_columns = [j for j in range(n) if flow[f"column:{j}"] == 0]
    require(len(unmatched_rows) == n - flow["gate"], "unmatched row count mismatch")
    require(len(unused_columns) == n - flow["gate"], "unused column count mismatch")
    require(flow["gate"] == sum(
        flow[arc_id] for arc_id in flow if arc_id.startswith("column:")
    ), "gate/column flow mismatch")
    paths = len(unmatched_rows)
    require(result["used_paths_in_relaxation"] == paths, "path count mismatch")
    require(paths == 2, "cardinality gate did not retain exactly two paths")

    selected_ids = list(result["selected_movement_ids"])
    require(len(selected_ids) == len(set(selected_ids)), "duplicate selected movement ID")
    expected_selected = list(selected_real)
    trip_ids = model["trip_ids"]
    expected_selected += [
        model["cheapest_pullin"][trip_ids[i]][1] for i in unmatched_rows
    ]
    expected_selected += [
        model["cheapest_pullout"][trip_ids[j]][1] for j in unused_columns
    ]
    require(Counter(selected_ids) == Counter(expected_selected),
            "decoded selected movement IDs mismatch")

    movement_by_id = {m["id"]: m for m in case["movements"]}
    decoded_objective = (
        model["service_constant"] + paths * model["vehicle"]
        + sum((movement_cost(movement_by_id[mid], case, price)
               for mid in selected_ids), Fraction(0))
    )
    require(decoded_objective == expected_lower,
            "decoded movement objective differs from certified lower bound")

    require(type(cert["relaxations"]) is int and
            0 <= cert["relaxations"] <= 8_000_000,
            "relaxation count outside frozen hard cap")
    return {
        "depot": int(case["depot"][1:]),
        "case_identity": identity,
        "services": n,
        "movement_modes": len(case["movements"]),
        "movement_counts": model["movement_counts"],
        "allowed_connection_pairs": model["connection_pairs"],
        "connection_modes_across_pairs": model["connection_modes"],
        "network_arcs": len(model["arcs"]),
        "real_edges_selected": len(selected_real),
        "unmatched_rows": len(unmatched_rows),
        "unused_columns": len(unused_columns),
        "gate_flow": flow["gate"],
        "paths_in_relaxation": paths,
        "relaxations": cert["relaxations"],
        "service_constant_exact": str(model["service_constant"]),
        "baseline_exact": str(model["baseline"]),
        "network_cost_exact": str(primal),
        "dual_value_exact": str(dual),
        "lower_exact": str(expected_lower),
        "lower_decimal_display": f"{float(expected_lower):.12f}",
        "selected_movement_count": len(selected_ids),
        "primal_dual_equal": primal == dual,
        "decoded_objective_equal": decoded_objective == expected_lower,
    }


def corruption_controls(case, result, price, identity):
    mutations = {
        "remove one expected arc": lambda x: x["certificate"]["arcs"].pop(),
        "change an arc capacity": lambda x: x["certificate"]["arcs"][0].update(capacity=2),
        "break gate flow balance": lambda x: x["certificate"]["flow"].update(gate=34),
        "corrupt one potential": lambda x: x["certificate"]["potential"].update(
            t=str(q(x["certificate"]["potential"]["t"]) + 1)
        ),
        "change network objective": lambda x: x["certificate"].update(network_cost="0"),
        "change published lower bound": lambda x: x.update(lower_exact="0"),
    }
    rejected = []
    for label, mutate in mutations.items():
        damaged = copy.deepcopy(result)
        mutate(damaged)
        try:
            verify_result(case, damaged, price, identity)
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected.append({"control": label, "rejected": True})
        else:
            rejected.append({"control": label, "rejected": False})
    require(all(row["rejected"] for row in rejected),
            "at least one corruption control was accepted")
    return rejected


def mode_omission_control(case, result, price, identity):
    """Ensure the verifier catches an accidental omission of depot connections."""
    try:
        verify_result(case, result, price, identity, connection_kinds=("direct",))
    except (AssertionError, KeyError, TypeError, ValueError):
        return {
            "control": "omit depot connection modes during reconstruction",
            "rejected": True,
        }
    raise AssertionError("omitting depot modes was not detected")


def parallel_mode_witness(case, result, price, i, j):
    """Expose one independently reconstructed min over direct/depot modes."""
    trips = case["trips"]
    before, after = trips[i]["id"], trips[j]["id"]
    modes = [
        (movement_cost(m, case, price), m["id"], m["kind"])
        for m in case["movements"]
        if m["kind"] in ("direct", "depot")
        and m["before"] == before and m["after"] == after
    ]
    require(modes, f"no declared connection modes for {before}->{after}")
    cheapest = min(modes, key=lambda row: (row[0], row[1]))
    pullin = min(
        (movement_cost(m, case, price), m["id"])
        for m in case["movements"]
        if m["kind"] == "pullin" and m["before"] == before
    )
    pullout = min(
        (movement_cost(m, case, price), m["id"])
        for m in case["movements"]
        if m["kind"] == "pullout" and m["after"] == after
    )
    reduction = cheapest[0] - pullin[0] - pullout[0] - q(case["vehicle_cost"])
    saved_arc = next(
        a for a in result["certificate"]["arcs"]
        if a["id"] == f"real:{i}:{j}"
    )
    require(q(saved_arc["cost"]) == reduction,
            "parallel-mode witness does not match saved arc cost")
    return {
        "pair": f"{before}->{after}",
        "mode_count": len(modes),
        "modes_sorted_by_exact_cost_then_id": [
            {"movement_id": mid, "kind": kind, "movement_cost_exact": str(cost)}
            for cost, mid, kind in sorted(modes, key=lambda row: (row[0], row[1]))
        ],
        "chosen_mode": {"movement_id": cheapest[1], "kind": cheapest[2]},
        "cheapest_pullin": {"movement_id": pullin[1], "cost_exact": str(pullin[0])},
        "cheapest_pullout": {"movement_id": pullout[1], "cost_exact": str(pullout[0])},
        "vehicle_cost_exact": str(q(case["vehicle_cost"])),
        "reconstructed_increment_exact": str(reduction),
        "saved_increment_exact": saved_arc["cost"],
        "minimum_and_arc_match": True,
    }


def verify_source_hashes(frozen):
    commit = frozen["source_commit"]
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    resolved_commit = subprocess.check_output(
        ["git", "rev-parse", f"{commit}^{{commit}}"], cwd=REPO, text=True
    ).strip()
    require(resolved_commit == commit, "frozen source commit is unavailable")
    reports = {}
    for relpath, expected in frozen["source_hashes"].items():
        live = (REPO / relpath).read_bytes()
        live_hash = sha(live)
        require(live_hash == expected, f"live source hash mismatch: {relpath}")
        committed = subprocess.check_output(
            ["git", "show", f"{commit}:{relpath}"], cwd=REPO
        )
        committed_hash = sha(committed)
        require(committed_hash == expected,
                f"committed source hash mismatch: {relpath}")
        reports[relpath] = {
            "frozen_sha256": expected,
            "live_matches": True,
            "commit_matches": True,
        }
    return {
        "commit": commit,
        "commit_is_available": True,
        "working_head": head,
        "head_matches_pinned_commit": head == commit,
        "dependencies": reports,
    }


def verify_public_payload(frozen, identities):
    raw = PUBLIC.read_bytes()
    require(sha(raw) == EXPECTED_PAYLOAD_SHA256,
            "public payload SHA-256 differs from protocol pin")
    public = json.loads(raw)
    native_by_id = {
        int(native["selected_depot_id"]): native
        for native in public["native_cases"]
    }
    require(frozen["case_identities"] == identities == EXPECTED_IDENTITIES,
            "frozen case identities differ from protocol pins")
    require(len(frozen["cases"]) == 2, "expected exactly two frozen cases")
    core_checks = []
    for case, identity in zip(frozen["cases"], identities):
        depot = int(case["depot"][1:])
        native = native_by_id[depot]
        require(native["case_identity"] == identity, f"P{depot}: public identity mismatch")
        require(case["trips"] == [row["native"] for row in native["trips"]],
                f"P{depot}: frozen trips differ from pinned public payload")
        require(case["movements"] == native["movement_modes"],
                f"P{depot}: frozen movements differ from pinned public payload")
        require(case["market_edges_min"] == native["market_edges_min"],
                f"P{depot}: market edge list differs from pinned public payload")
        require(case["name"] == native["case_name"], f"P{depot}: case name mismatch")
        require(case["vehicle_cost"] == native["cost_policy"]["vehicle_cost"],
                f"P{depot}: vehicle cost mismatch")
        require(case["deadhead_cost_per_min"] ==
                native["cost_policy"]["deadhead_cost_per_min"],
                f"P{depot}: deadhead cost mismatch")
        require(len(case["trips"]) == 37, f"P{depot}: not a full 37-service case")
        core_checks.append({
            "depot": depot,
            "identity": identity,
            "services": len(case["trips"]),
            "movement_modes": len(case["movements"]),
            "trips_match_public_payload": True,
            "movements_match_public_payload": True,
        })
    return {
        "payload_sha256": sha(raw),
        "cases": core_checks,
    }


def verify_attempt():
    raw_manifest = check_manifest(ATTEMPT)
    frozen_bytes = (ATTEMPT / "frozen.json").read_bytes()
    frozen_hash = sha(frozen_bytes)
    frozen = json.loads(frozen_bytes)
    summary = load(ATTEMPT / "summary.json")
    launch = load(ATTEMPT / "supervisor_launch.json")
    started = load(ATTEMPT / "STARTED.json")
    receipt = load(ATTEMPT / "supervisor_receipt.json")

    require(frozen["protocol"] == "sistig-cardinality-flow-20260927-v1",
            "frozen protocol mismatch")
    require(summary["protocol"] == frozen["protocol"], "summary protocol mismatch")
    require(summary["frozen_sha256"] == frozen_hash, "summary frozen hash mismatch")
    require(launch["frozen_sha256"] == frozen_hash, "launch frozen hash mismatch")
    require(started["frozen_sha256"] == frozen_hash, "STARTED frozen hash mismatch")
    require(receipt["child_exit_code"] == receipt["exit_code"] == 0,
            "supervisor/child exit was not successful")
    require(receipt["timed_out"] is False and receipt["exception"] is None,
            "supervisor timed out or recorded an exception")
    require(receipt["source_hash_exception"] is None and
            receipt["source_hashes_unchanged"] is True,
            "supervisor reports source drift")
    require(receipt["hard_cap_seconds"] == frozen["external_process_seconds_cap"] == 150,
            "supervisor hard cap mismatch")
    require(receipt["elapsed_seconds"] < receipt["hard_cap_seconds"],
            "supervised run exceeded wall cap")
    require(summary["elapsed_seconds"] < frozen["complete_seconds_cap"],
            "complete-run cap exceeded")
    require(summary["algorithm_calls"] == frozen["algorithm_calls"] == 2,
            "unexpected public algorithm call count")
    require(summary["status"] == "completed" and
            summary["source_hashes_unchanged"] is True,
            "summary did not complete cleanly")
    require(summary["native_optimizer_invoked"] is False,
            "archive claims native optimizer invocation")
    require(summary["physical_feasibility_or_native_matrix_optimality_claimed"] is False,
            "archive makes a physical/native optimum claim")
    require(launch["hard_cap_seconds"] == 150, "launch hard cap mismatch")
    require(launch["command"][-3:] == ["run", "--attempt", str(ATTEMPT)],
            "supervisor did not invoke the frozen run command")
    require((ATTEMPT / "stdout.txt").read_bytes() == b"", "stdout was not empty")
    require((ATTEMPT / "stderr.txt").read_bytes() == b"", "stderr was not empty")

    price = Fraction(frozen["price_exact"])
    require(q(frozen["price_input"]) == price,
            "stored float price and exact binary price disagree")
    identities = frozen["case_identities"]
    payload_report = verify_public_payload(frozen, identities)
    source_report = verify_source_hashes(frozen)

    case_rows = []
    for index, case in enumerate(frozen["cases"]):
        depot = int(case["depot"][1:])
        identity = identities[index]
        result = load(ATTEMPT / f"depot_{depot}.json")
        verified = verify_result(case, result, price, identity)
        verified["corruptions"] = corruption_controls(case, result, price, identity)
        verified["mode_omission_control"] = mode_omission_control(
            case, result, price, identity
        )
        case_rows.append(verified)

    require([row["lower_exact"] for row in case_rows] == summary["lower_exact"],
            "summary exact bounds differ from independently verified results")

    p15 = frozen["cases"][0]
    p15_result = load(ATTEMPT / "depot_15.json")
    mode_witness = parallel_mode_witness(p15, p15_result, price, 0, 4)

    # Compare with the independently audited archived V1 matching relaxation.
    old_manifest = check_manifest(OLD_MATCH)
    old_summary = load(OLD_MATCH / "summary.json")
    old_review = load(OLD_MATCH / "review/audit-report.json")
    require(old_review["verdict"] == "PASS", "archived V1 matching audit did not pass")
    old_cases = []
    for index, depot in enumerate((15, 16)):
        old_result = load(OLD_MATCH / f"depot_{depot}.json")
        require(old_result["case_identity"] == identities[index],
                f"P{depot}: archived matching case identity mismatch")
        require(old_result["lower_exact"] == old_summary["lower_exact"][index],
                f"P{depot}: matching summary/result mismatch")
        reviewed_case = old_review["cases"][index]
        require(reviewed_case["case_identity"] == identities[index] and
                reviewed_case["lower_exact"] == old_result["lower_exact"],
                f"P{depot}: reviewed matching value mismatch")
        old_cases.append({
            "depot": depot,
            "matching_lower_exact": old_result["lower_exact"],
            "matching_lower_decimal_display":
                f"{float(Fraction(old_result['lower_exact'])):.12f}",
            "matching_review_passed": True,
        })

    # Preserve the native two-bus numerical witnesses as a distinct evidence class.
    native_audit = load(NATIVE_AUDIT)
    require(native_audit["audit_status"] == "PASS numerical evidence",
            "archived native numerical audit did not pass")
    native_cases = []
    for depot in (15, 16):
        item = next(row for row in native_audit["cells"]
                    if row["cell"] == f"depot_{depot}_flat")
        native_cases.append({
            "depot": depot,
            "native_two_bus_witness_upper": item["auxiliary_upper"],
            "native_used_buses": item["used_buses"],
            "native_evidence_verdict": item["evidence_verdict"],
            "tolerance_qualified": True,
        })

    return {
        "verdict": "PASS independent exact certificate and provenance audit",
        "scope": (
            "Exact ideal stored-input lower bounds for the frozen declared "
            "movement graph; no physical optimum, exact native-matrix optimum, "
            "or physical optimality gap is asserted."
        ),
        "raw_archive_integrity": raw_manifest,
        "frozen_sha256": frozen_hash,
        "supervisor": {
            "exit_code": receipt["exit_code"],
            "child_exit_code": receipt["child_exit_code"],
            "timed_out": receipt["timed_out"],
            "elapsed_seconds": receipt["elapsed_seconds"],
            "hard_cap_seconds": receipt["hard_cap_seconds"],
            "algorithm_calls": summary["algorithm_calls"],
            "stdout_bytes": (ATTEMPT / "stdout.txt").stat().st_size,
            "stderr_bytes": (ATTEMPT / "stderr.txt").stat().st_size,
            "source_hashes_unchanged": receipt["source_hashes_unchanged"],
        },
        "source_integrity": source_report,
        "public_payload_and_case_checks": payload_report,
        "flat_price_exact": str(price),
        "cases": case_rows,
        "parallel_mode_minimum_witness": mode_witness,
        "archived_v1_matching_comparison": {
            "attempt": str(OLD_MATCH.relative_to(REPO)),
            "raw_archive_integrity": old_manifest,
            "audit_verdict": old_review["verdict"],
            "cases": old_cases,
        },
        "native_two_bus_numerical_witnesses": {
            "source": str(NATIVE_AUDIT.relative_to(REPO)),
            "audit_status": native_audit["audit_status"],
            "cases": native_cases,
            "note": (
                "Reported separately as tolerance-qualified numerical witnesses; "
                "not subtracted from exact stored-input bounds."
            ),
        },
    }


if __name__ == "__main__":
    report = verify_attempt()
    output = ATTEMPT / "review/audit-report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
