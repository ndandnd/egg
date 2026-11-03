"""Exact flat-price path-cover relaxation; no native optimizer dependency.

The bound concerns the ideal full-recharge model with each stored input number
interpreted exactly. It is not a certificate for the rounded native matrix.
SOC, charging windows/capacity and the fleet cap are relaxed, never fabricated.
"""
from __future__ import annotations

from fractions import Fraction as Q
import math

from egglab import native_recharge as nr

SCHEMA = "egg-flat-energy-matching-v1"


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Q)):
        raise ValueError("Expected a finite stored number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Expected a finite stored number")
    return Q(value)


def _matrix(costs):
    if not costs or not costs[0]:
        raise ValueError("Empty assignment matrix")
    n, m = len(costs), len(costs[0])
    if m < n or any(len(row) != m for row in costs):
        raise ValueError("Rectangular assignment needs at least as many columns")
    return [[None if x is None else rational(x) for x in row] for row in costs]


def verify_assignment(costs, certificate):
    """Check exact primal and dual witnesses without rerunning the algorithm."""
    a = _matrix(costs)
    n, m = len(a), len(a[0])
    assignment = certificate["assignment"]
    if (len(assignment) != n or any(type(j) is not int or not 0 <= j < m
                                  for j in assignment)
            or len(set(assignment)) != n):
        raise ValueError("Invalid assignment")
    u, v = [Q(x) for x in certificate["row_potentials"]], [Q(x) for x in certificate["column_potentials"]]
    if len(u) != n or len(v) != m or any(x > 0 for x in v):
        raise ValueError("Invalid dual dimensions or column sign")
    if any(a[i][j] is None for i, j in enumerate(assignment)):
        raise ValueError("Selected forbidden edge")
    if any(u[i] + v[j] > a[i][j] for i in range(n) for j in range(m)
           if a[i][j] is not None):
        raise ValueError("Dual inequality violated")
    primal = sum((a[i][j] for i, j in enumerate(assignment)), Q(0))
    dual = sum(u, Q(0)) + sum(v, Q(0))
    if primal != dual or primal != Q(certificate["objective"]):
        raise ValueError("Primal/dual objective mismatch")
    return primal


def exact_assignment(costs):
    """Rectangular Hungarian augmentation using integer-scaled exact weights.

    None marks an absent edge. Every row must have an assigned distinct column.
    The returned potentials obey u_i + v_j <= cost_ij and v_j <= 0.
    A verifier, rather than trust in this implementation, establishes optimality.
    """
    q = _matrix(costs)
    n, m = len(q), len(q[0])
    scale = math.lcm(*(x.denominator for row in q for x in row if x is not None))
    a = [[None if x is None else int(x * scale) for x in row] for row in q]
    u, v, owner, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for row in range(1, n + 1):
        owner[0], column = row, 0
        distance, used = [None] * (m + 1), [False] * (m + 1)
        while True:
            used[column] = True
            current = owner[column]
            delta, next_column = None, None
            for j in range(1, m + 1):
                if used[j]:
                    continue
                weight = a[current - 1][j - 1]
                if weight is not None:
                    reduced = weight - u[current] - v[j]
                    if distance[j] is None or reduced < distance[j]:
                        distance[j], way[j] = reduced, column
                if distance[j] is not None and (delta is None or distance[j] < delta):
                    delta, next_column = distance[j], j
            if delta is None:
                raise ValueError("No complete row assignment")
            for j in range(m + 1):
                if used[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                elif distance[j] is not None:
                    distance[j] -= delta
            column = next_column
            if owner[column] == 0:
                break
        while column:
            previous = way[column]
            owner[column] = owner[previous]
            column = previous
    assignment = [-1] * n
    for j in range(1, m + 1):
        if owner[j]:
            assignment[owner[j] - 1] = j - 1
    result = {
        "assignment": assignment,
        "row_potentials": [str(Q(x, scale)) for x in u[1:]],
        "column_potentials": [str(Q(x, scale)) for x in v[1:]],
        "objective": str(sum((q[i][j] for i, j in enumerate(assignment)), Q(0))),
        "integer_scale": str(scale),
    }
    verify_assignment(q, result)
    return result


def path_cover_problem(case, price):
    """Construct a relaxation from all declared modes; no optimization here.

    This reduction requires at least one pullout and pullin for every trip.
    Missing endpoint modes are rejected, not replaced by zero-cost arcs.
    Service cost is constant; replacing two endpoints with a connecting mode
    changes cost by connection - pullin_before - pullout_after - vehicle_cost.
    """
    nr.validate_case(case)
    p, eta = rational(price), rational(case.efficiency)
    f, rate = rational(case.vehicle_cost), rational(case.deadhead_cost_per_min)
    trips = list(case.trips)
    indices = {t.id: i for i, t in enumerate(trips)}
    out, into, connections, coefficients = {}, {}, {}, {}
    for mode in case.movements:
        energy = sum((rational(leg.energy_kwh) for leg in mode.legs), Q(0))
        duration = sum((rational(leg.arrive_min) - rational(leg.depart_min)
                        for leg in mode.legs), Q(0))
        weight = rate * duration + p * energy / eta
        coefficients[mode.id] = weight
        if mode.kind == "pullout":
            bucket, key = out, mode.after
        elif mode.kind == "pullin":
            bucket, key = into, mode.before
        else:
            # validate_case enforces service and movement timing. This explicit
            # check protects the acyclic path-cover reduction from schema drift.
            i, j = indices[mode.before], indices[mode.after]
            if not trips[i].end_min <= trips[j].start_min:
                raise ValueError("Connection graph must be acyclic in service time")
            bucket, key = connections, (mode.before, mode.after)
        candidate = (weight, mode.id)
        if key not in bucket or candidate < bucket[key]:
            bucket[key] = candidate
    if any(t.id not in out or t.id not in into for t in trips):
        raise ValueError("Every service needs declared pullout and pullin modes")
    service = p * sum((rational(t.energy_kwh) for t in trips), Q(0)) / eta
    baseline = service + sum((f + out[t.id][0] + into[t.id][0] for t in trips), Q(0))
    n = len(trips)
    matrix = [[None] * n + [Q(0)] * n for _ in trips]
    chosen_mode = {}
    for (before, after), (weight, mid) in connections.items():
        i, j = indices[before], indices[after]
        matrix[i][j] = weight - into[before][0] - out[after][0] - f
        chosen_mode[i, j] = mid
    return {"matrix": matrix, "baseline": baseline, "service_constant": service,
            "trip_ids": [t.id for t in trips], "pullout": out, "pullin": into,
            "connections": chosen_mode, "mode_coefficients": coefficients}


def solve_relaxation(case, price):
    problem = path_cover_problem(case, price)
    certificate = exact_assignment(problem["matrix"])
    n = len(problem["trip_ids"])
    pairs = [(i, j) for i, j in enumerate(certificate["assignment"]) if j < n]
    incoming, outgoing = {j for _, j in pairs}, {i for i, _ in pairs}
    selected = [problem["connections"][i, j] for i, j in pairs]
    selected += [problem["pullout"][t][1] for i, t in enumerate(problem["trip_ids"]) if i not in incoming]
    selected += [problem["pullin"][t][1] for i, t in enumerate(problem["trip_ids"]) if i not in outgoing]
    objective = problem["baseline"] + verify_assignment(problem["matrix"], certificate)
    direct = problem["service_constant"] + rational(case.vehicle_cost) * (n - len(pairs))
    direct += sum((problem["mode_coefficients"][mid] for mid in selected), Q(0))
    if objective != direct:
        raise ValueError("Decoded path cost differs from matching objective")
    return {"schema": SCHEMA, "case_identity": case.identity(), "flat_price": str(rational(price)),
            "interpretation": "exact ideal stored-input relaxation; not native-matrix or physical-feasibility certificate",
            "lower_exact": str(objective), "baseline_exact": str(problem["baseline"]),
            "service_constant_exact": str(problem["service_constant"]),
            "used_paths_in_relaxation": n - len(pairs), "selected_movement_ids": sorted(selected),
            "certificate": certificate}
