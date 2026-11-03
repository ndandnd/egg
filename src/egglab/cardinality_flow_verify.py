"""Independent exact certificate verifier; never imports cardinality_flow.

Reconstructs every public arc and coefficient from the original pinned JSON.
Balances use outflow minus inflow = b; reduced cost is c-pi_tail+pi_head.
"""
from __future__ import annotations

from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path

PAYLOAD_SHA256 = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
CASE_IDENTITIES = (
    "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7",
    "216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d",
)


def number(value):
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise ValueError("Invalid stored number")
    return Q(value)


def fraction(value):
    if type(value) is not str:
        raise ValueError("Certificate rational must be a string")
    try:
        q = Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("Malformed certificate rational") from exc
    if str(q) != value:
        raise ValueError("Noncanonical certificate rational")
    return q


def expected_arcs(n, gate, edges):
    if type(n) is not int or n < 1 or type(gate) is not int or not 0 <= gate <= n:
        raise ValueError("Invalid dimensions")
    if len(edges) != len(set(edges)) or any(type(i) is not int or type(j) is not int
                                        or not 0 <= i < n or not 0 <= j < n or i == j
                                        for i, j in edges):
        raise ValueError("Invalid real-edge set")
    arcs = []
    for i in range(n):
        arcs.extend(((f"source:{i}", "s", f"R{i}", 1, Q(0)),
                     (f"unmatched:{i}", f"R{i}", "t", 1, Q(0))))
    for (i, j), cost in sorted(edges.items()):
        arcs.append((f"real:{i}:{j}", f"R{i}", f"C{j}", 1, Q(cost)))
    for j in range(n):
        arcs.append((f"column:{j}", f"C{j}", "g", 1, Q(0)))
    arcs.append(("gate", "g", "t", gate, Q(0)))
    return arcs


def verify(n, gate, edges, baseline, certificate):
    """Check exact primal flow, residual dual, and equality from independent arcs."""
    arcs = expected_arcs(n, gate, edges)
    expected = [{"id": key, "tail": tail, "head": head, "capacity": cap,
                 "cost": str(cost)} for key, tail, head, cap, cost in arcs]
    if certificate.get("arcs") != expected:
        raise ValueError("Arc set, capacity, or cost mismatch")
    keys = {a[0] for a in arcs}
    vertices = {"s", "t", "g"} | {f"R{i}" for i in range(n)} | {f"C{j}" for j in range(n)}
    f, pi = certificate.get("flow"), certificate.get("potential")
    if type(f) is not dict or set(f) != keys or type(pi) is not dict or set(pi) != vertices:
        raise ValueError("Flow or potential dimensions mismatch")
    if any(type(f[key]) is not int or not 0 <= f[key] <= cap for key, _, _, cap, _ in arcs):
        raise ValueError("Arc capacity or integral-flow violation")
    potential = {v: fraction(pi[v]) for v in vertices}
    if potential["t"] != 0:
        raise ValueError("Sink potential must be zero")
    balance = {v: 0 for v in vertices}
    primal = Q(0)
    dual_tail = Q(n) * potential["s"] - Q(n) * potential["t"]
    dual_capacity = Q(0)
    for key, tail, head, cap, cost in arcs:
        amount = f[key]
        balance[tail] += amount
        balance[head] -= amount
        primal += cost * amount
        reduced = cost - potential[tail] + potential[head]
        if (amount < cap and reduced < 0) or (amount > 0 and reduced > 0):
            raise ValueError("Residual reduced-cost sign violation")
        dual_capacity += cap * min(Q(0), reduced)
    if balance != {v: n if v == "s" else -n if v == "t" else 0 for v in vertices}:
        raise ValueError("Outflow-minus-inflow conservation violation")
    if f["gate"] != sum(f[f"real:{i}:{j}"] for i, j in edges):
        raise ValueError("Real-edge count differs from gate")
    if sum(f[f"unmatched:{i}"] for i in range(n)) + f["gate"] != n:
        raise ValueError("Unmatched count differs from gate")
    if primal != dual_tail + dual_capacity:
        raise ValueError("Primal/dual equality violation")
    if fraction(certificate.get("network_cost")) != primal:
        raise ValueError("Network objective mismatch")
    return {"network_cost": primal, "lower": Q(baseline) + primal,
            "real_count": f["gate"], "path_count": n - f["gate"],
            "pairs": [(i, j) for i, j in sorted(edges) if f[f"real:{i}:{j}"]]}


def reconstruct_variant(variant, price):
    """Recompute baseline and all cheapest parallel modes from raw payload rows."""
    trips = [row["native"] for row in variant["trips"]]
    ids = [t["id"] for t in trips]
    if len(ids) != len(set(ids)) or len(ids) != variant["service_count"]:
        raise ValueError("Service coverage mismatch")
    index = {tid: i for i, tid in enumerate(ids)}
    eta = number(variant["charging_model"]["efficiency"])
    vehicle = number(variant["cost_policy"]["vehicle_cost"])
    rate = number(variant["cost_policy"]["deadhead_cost_per_min"])
    if eta <= 0:
        raise ValueError("Invalid efficiency")
    out, into, connections, coefficients = {}, {}, {}, {}
    for mode in variant["movement_modes"]:
        mid, kind = mode["id"], mode["kind"]
        if mid in coefficients:
            raise ValueError("Duplicate movement ID")
        legs = mode["legs"]
        energy = sum((number(leg["energy_kwh"]) for leg in legs), Q(0))
        duration = sum((number(leg["arrive_min"]) - number(leg["depart_min"])
                        for leg in legs), Q(0))
        weight = rate * duration + price * energy / eta
        coefficients[mid] = weight
        before, after = mode["before"], mode["after"]
        if kind == "pullout" and before is None and after in index:
            bucket, key = out, after
        elif kind == "pullin" and before in index and after is None:
            bucket, key = into, before
        elif kind in ("direct", "depot") and before in index and after in index:
            i, j = index[before], index[after]
            if i == j or number(trips[i]["end_min"]) > number(trips[j]["start_min"]):
                raise ValueError("Connection chronology mismatch")
            bucket, key = connections, (i, j)
        else:
            raise ValueError("Invalid movement ownership")
        candidate = (weight, mid)
        if key not in bucket or candidate < bucket[key]:
            bucket[key] = candidate
    if any(tid not in out or tid not in into for tid in ids):
        raise ValueError("Missing endpoint mode")
    service = price * sum((number(t["energy_kwh"]) for t in trips), Q(0)) / eta
    baseline = service + sum((vehicle + out[tid][0] + into[tid][0] for tid in ids), Q(0))
    edges = {(i, j): weight - into[ids[i]][0] - out[ids[j]][0] - vehicle
             for (i, j), (weight, _) in connections.items()}
    return {"ids": ids, "edges": edges, "baseline": baseline, "service": service,
            "out": out, "into": into, "connections": connections,
            "coefficients": coefficients, "vehicle": vehicle}


def verify_public(payload_path: Path, result: dict):
    """Verify a public result against the frozen original JSON, never saved costs."""
    data = payload_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Frozen payload hash mismatch")
    variants = json.loads(data)["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15, 16]:
        raise ValueError("Public case sequence mismatch")
    depot = result.get("source_depot_id")
    if depot not in (15, 16):
        raise ValueError("Unexpected depot")
    variant = variants[[15, 16].index(depot)]
    if variant["case_identity"] != CASE_IDENTITIES[[15, 16].index(depot)]:
        raise ValueError("Pinned case identity mismatch")
    # Independent case digest checks all native fields used by the public graph.
    from experiments.sistig_native_case import native_case_from_payload
    from egglab.native_recharge import validate_case
    case = native_case_from_payload(variant)
    validate_case(case)
    if case.identity() != variant["case_identity"] or len(case.trips) != 37:
        raise ValueError("Rebuilt native case identity mismatch")
    price = number(.2)
    if result.get("flat_price") != str(price) or result.get("case_identity") != case.identity():
        raise ValueError("Result price or case identity mismatch")
    source = reconstruct_variant(variant, price)
    n = len(source["ids"])
    checked = verify(n, n - 2, source["edges"], source["baseline"], result["certificate"])
    if (result.get("lower_exact") != str(checked["lower"])
            or result.get("baseline_exact") != str(source["baseline"])
            or result.get("service_constant_exact") != str(source["service"])
            or result.get("used_paths_in_relaxation") != checked["path_count"]):
        raise ValueError("Decoded objective or path count mismatch")
    pairs = checked["pairs"]
    incoming, outgoing = {j for _, j in pairs}, {i for i, _ in pairs}
    selected = [source["connections"][i, j][1] for i, j in pairs]
    selected += [source["out"][tid][1] for i, tid in enumerate(source["ids"]) if i not in incoming]
    selected += [source["into"][tid][1] for i, tid in enumerate(source["ids"]) if i not in outgoing]
    if result.get("selected_movement_ids") != sorted(selected):
        raise ValueError("Decoded movement IDs mismatch")
    direct = source["service"] + source["vehicle"] * checked["path_count"]
    direct += sum((source["coefficients"][mid] for mid in selected), Q(0))
    if direct != checked["lower"]:
        raise ValueError("Direct selected-mode objective mismatch")
    return checked
