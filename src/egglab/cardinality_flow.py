"""Exact cardinality-gated matching flow; no native optimizer dependency.

The balance convention is outflow minus inflow = b, with b_s=n and b_t=-n.
Only the caller supplies costs. Public-case reconstruction is in the independent
verifier, which does not import this algorithm.
"""
from __future__ import annotations

from fractions import Fraction as Q


def network(n, gate, edges):
    if type(n) is not int or n < 1 or type(gate) is not int or not 0 <= gate <= n:
        raise ValueError("Invalid flow dimensions")
    if len(edges) != len(set(edges)) or any(type(i) is not int or type(j) is not int
                                        or not 0 <= i < n or not 0 <= j < n
                                        or i == j for i, j in edges):
        raise ValueError("Invalid real-edge set")
    arcs = []
    for i in range(n):
        arcs.append((f"source:{i}", "s", f"R{i}", 1, Q(0)))
        arcs.append((f"unmatched:{i}", f"R{i}", "t", 1, Q(0)))
    for (i, j), cost in sorted(edges.items()):
        arcs.append((f"real:{i}:{j}", f"R{i}", f"C{j}", 1, Q(cost)))
    for j in range(n):
        arcs.append((f"column:{j}", f"C{j}", "g", 1, Q(0)))
    arcs.append(("gate", "g", "t", gate, Q(0)))
    return arcs


def solve(n, gate, edges, *, max_relaxations=2_000_000):
    """Successive exact shortest augmenting paths with deterministic arc order.

    Bellman-Ford permits signed rational costs. The relaxation budget is a hard
    finite guard against unexpected graph/schema growth.
    """
    arcs = network(n, gate, edges)
    vertices = ["s", "t", "g"] + [f"R{i}" for i in range(n)] + [f"C{j}" for j in range(n)]
    flow = {a[0]: 0 for a in arcs}
    relaxations = 0

    def residual():
        result = []
        for key, tail, head, capacity, cost in arcs:
            if flow[key] < capacity:
                result.append((tail, head, cost, key, 1))
            if flow[key] > 0:
                result.append((head, tail, -cost, key, -1))
        return result

    def distances(start, all_zero=False):
        nonlocal relaxations
        d = {v: Q(0) for v in vertices} if all_zero else {start: Q(0)}
        predecessor = {}
        for _ in range(len(vertices)):
            changed = False
            for tail, head, cost, key, direction in residual():
                relaxations += 1
                if relaxations > max_relaxations:
                    raise TimeoutError("Exact flow relaxation budget exceeded")
                if tail in d and (head not in d or d[tail] + cost < d[head]):
                    d[head] = d[tail] + cost
                    predecessor[head] = (tail, key, direction)
                    changed = True
            if not changed:
                return d, predecessor
        raise ValueError("Negative residual cycle")

    for _ in range(n):
        _, predecessor = distances("s")
        if "t" not in predecessor:
            raise ValueError("No augmenting path")
        v, steps = "t", []
        while v != "s":
            if len(steps) > len(vertices):
                raise ValueError("Cyclic augmenting predecessor")
            tail, key, direction = predecessor[v]
            steps.append((key, direction))
            v = tail
        for key, direction in steps:
            flow[key] += direction
    distance, _ = distances("s", all_zero=True)
    potential = {v: str(-distance[v] + distance["t"]) for v in vertices}
    return {"arcs": [{"id": key, "tail": tail, "head": head,
                      "capacity": capacity, "cost": str(cost)}
                     for key, tail, head, capacity, cost in arcs],
            "flow": flow, "potential": potential,
            "network_cost": str(sum((cost * flow[key] for key, _, _, _, cost in arcs), Q(0))),
            "relaxations": relaxations}
