"""Independent rational physical reference; no sampling or phase formulas.

The two unlabeled service partitions are AB and A|B. All durations are one
hour. Energy, SOC and power use kWh/kW; both buses start and end at SOC 20.
Convexification occurs only after the physical polytopes have been enumerated.
"""

from fractions import Fraction as F
from itertools import combinations


def _solve(rows, rhs, n):
    """Unique solution of a possibly overdetermined rational linear system."""
    a = [[F(v) for v in row] + [F(b)] for row, b in zip(rows, rhs)]
    pivots = []
    r = 0
    for c in range(n):
        pivot = next((i for i in range(r, len(a)) if a[i][c]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        d = a[r][c]
        a[r] = [v / d for v in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c]:
                d = a[i][c]
                a[i] = [v - d * w for v, w in zip(a[i], a[r])]
        pivots.append(c)
        r += 1
    if any(not any(row[:n]) and row[n] for row in a) or r != n:
        return None
    answer = [F(0)] * n
    for i, c in enumerate(pivots):
        answer[c] = a[i][n]
    return tuple(answer)


def _vertices(n, equalities, inequalities):
    """Enumerate active subsets; inequalities are row dot q <= rhs."""
    result = set()
    # Including redundant active constraints makes this independent of an
    # assumed equality rank or assumed dimension of a feasible face.
    for count in range(n + 1):
        for active in combinations(inequalities, count):
            rows = equalities + list(active)
            q = _solve([a for a, _ in rows], [b for _, b in rows], n)
            if q is not None and all(sum(a * v for a, v in zip(row, q)) <= b
                                     for row, b in inequalities):
                result.add(q)
    return sorted(result)


def _models(K):
    # AB: after A SOC=5, after early=5+x, after B=x-10,
    # after terminal=x-10+z=20. Each intermediate SOC lies in [0,20].
    one_eq = [((1, 1), 30)]
    one_le = [((-1, 0), 0), ((1, 0), 10), ((1, 0), 15),
              ((-1, 0), -10), ((1, 0), 30),
              ((0, -1), 0), ((0, 1), K)]
    # A|B: A after service=5, early=5+x, final=5+x+zA=20.
    # B cannot charge early: it starts full and has not served B yet.
    # B after service=5 and final=5+zB=20. Shared terminal energy <= K.
    two_eq = [((1, 1, 0), 15), ((0, 0, 1), 15)]
    two_le = [((-1, 0, 0), 0), ((1, 0, 0), 10),
              ((1, 0, 0), 15), ((0, -1, 0), 0),
              ((0, 0, -1), 0), ((0, 1, 0), K),
              ((0, 0, 1), K), ((0, 1, 1), K)]
    return [("AB", 1, _vertices(2, one_eq, one_le)),
            ("A|B", 2, _vertices(3, two_eq, two_le))]


def _witness(partition, x, K):
    """Build and independently replay a serial terminal connector schedule."""
    x, K = F(x), F(K)
    buses = ("AB",) if partition == "AB" else ("A", "B")
    service = [("AB", F(0), F(1)), ("AB", F(2), F(3))] if partition == "AB" else [
        ("A", F(0), F(1)), ("B", F(2), F(3))]
    early_bus = buses[0]
    charges = []
    if x:
        charges.append((early_bus, F(1), F(1) + x / 10, F(10)))
    needs = [("AB", 30 - x)] if partition == "AB" else [("A", 15 - x), ("B", F(15))]
    cursor = F(3)
    for bus, energy in needs:
        if energy:
            if K <= 0:
                raise ValueError("Positive terminal energy without connector power")
            end = cursor + energy / K
            charges.append((bus, cursor, end, K))
            cursor = end
    witness = {"services": service, "charges": charges}
    _validate_witness(partition, x, K, witness)
    return witness


def _validate_witness(partition, x, K, witness):
    buses = ("AB",) if partition == "AB" else ("A", "B")
    services, charges = witness["services"], witness["charges"]
    expected = [("AB", F(0), F(1)), ("AB", F(2), F(3))] if partition == "AB" else [
        ("A", F(0), F(1)), ("B", F(2), F(3))]
    assert services == expected
    cuts = sorted({F(0), F(1), F(2), F(3), F(4)} |
                  {t for _, s, e, _ in charges for t in (s, e)})
    soc = {bus: F(20) for bus in buses}
    early = late = F(0)
    for left, right in zip(cuts, cuts[1:]):
        assert 0 <= left < right <= 4
        powers = {bus: F(0) for bus in buses}
        for bus, start, end, power in charges:
            assert bus in buses and start < end and power >= 0
            assert (1 <= start < end <= 2 and power <= 10) or (3 <= start < end <= 4 and power <= K)
            if start <= left and right <= end:
                powers[bus] += power
        limit = F(10) if 1 <= left < 2 else K if 3 <= left < 4 else F(0)
        assert sum(powers.values()) <= limit
        for bus in buses:
            assert powers[bus] <= limit
            serving = any(b == bus and s <= left and right <= e for b, s, e in services)
            assert not (serving and powers[bus])
            delta = powers[bus] * (right - left)
            if 1 <= left < 2:
                early += delta
            if 3 <= left < 4:
                late += delta
            soc[bus] += delta - (15 * (right - left) if serving else 0)
            assert 0 <= soc[bus] <= 20
    assert all(v == 20 for v in soc.values())
    assert early == x and late == 30 - x and early + late == 30


def _energy(x):
    return 4 * x + (x * x + (30 - x) ** 2) / 10


def _hull(points):
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    if len(points) <= 1:
        return points
    lower, upper = [], []
    for chain, seq in ((lower, points), (upper, reversed(points))):
        for p in seq:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
    return lower[:-1] + upper[:-1]


def evaluate(K: F, fee: F) -> dict:
    """Return exact physical/hull minima and complete own-price responses.

    D is the physical objective minimum, CH its convexified counterpart.
    Every response endpoint is included, whether or not it minimizes price.
    For infeasible inputs D and CH are None and point lists are empty.
    """
    K, fee = F(K), F(fee)
    if not 0 <= K <= 30 or fee < 0:
        raise ValueError("Require 0 <= K <= 30 and fee >= 0")
    models = _models(K)
    vertices = []
    segments = []
    for partition, count, raw in models:
        xs = sorted({q[0] for q in raw})
        for q in raw:
            vertices.append({"partition": partition, "early": q[0],
                             "late": 30-q[0], "ops": fee*count,
                             "raw": q, "witness": _witness(partition, q[0], K)})
        if xs:
            segments.append((partition, count, xs[0], xs[-1]))
    if not vertices:
        return {"K": K, "fee": fee, "D": None, "CH": None,
                "physical_optima": [], "hull_min_points": [],
                "physical_vertices": [], "hull_vertices": []}
    candidates = []
    for partition, count, lo, hi in segments:
        x = min(hi, max(lo, F(5)))
        candidates.append((_energy(x)+fee*count, partition, count, x))
    D = min(c[0] for c in candidates)
    optima = []
    for value, partition, count, x in candidates:
        if value != D:
            continue
        pe, pl = 4+x/5, (30-x)/5
        responses = []
        for v in vertices:
            r = dict(v)
            r["price_cost"] = pe*v["early"] + pl*v["late"] + v["ops"]
            responses.append(r)
        best = min(r["price_cost"] for r in responses)
        own = pe*x + pl*(30-x) + fee*count
        response_sets = []
        for response_partition, response_count, lo, hi in segments:
            slope = pe - pl
            endpoint = lo if slope >= 0 else hi
            branch_min = pe*endpoint + pl*(30-endpoint) + fee*response_count
            if branch_min == best:
                interval = (lo, hi) if slope == 0 else (endpoint, endpoint)
                response_sets.append({"partition": response_partition,
                                      "early_interval": interval,
                                      "fee": fee,
                                      "ops": fee*response_count,
                                      "price_cost": branch_min})
        optima.append({"early": x, "late": 30-x, "ops": fee*count,
                       "partition": partition, "objective": value,
                       "prices": (pe, pl), "own_price_regret": own-best,
                       "endpoint_responses": responses,
                       "best_responses": [r for r in responses if r["price_cost"] == best],
                       "response_minimizer_sets": response_sets,
                       "witness": _witness(partition, x, K)})
    hull = _hull([(v["early"], v["ops"]) for v in vertices])
    hc = set(hull)
    # Since the objective increases strictly in ops, a two-dimensional hull
    # interior cannot minimize it. Checking every boundary edge also handles
    # vertical edges, degenerate line segments, and point hulls.
    for a, b in zip(hull, hull[1:] + hull[:1]):
        if a[0] == b[0]:
            continue
        slope = (b[1]-a[1])/(b[0]-a[0])
        lo, hi = sorted((a[0], b[0]))
        x = min(hi, max(lo, (2-slope)*F(5, 2)))
        hc.add((x, a[1]+slope*(x-a[0])))
    CH = min(_energy(x)+ops for x, ops in hc)
    return {"K": K, "fee": fee, "D": D, "CH": CH,
            "physical_optima": optima,
            "hull_min_points": [{"early": x, "late": 30-x, "ops": ops}
                                for x, ops in sorted(hc) if _energy(x)+ops == CH],
            "physical_vertices": vertices, "hull_vertices": hull}
