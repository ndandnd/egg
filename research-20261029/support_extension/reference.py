"""Exact physical enumeration and convexification, independent of phase formulas.

Types are available twice each; at most two buses are used. Optional movement
consumes 2 kWh after B, during [3,31/10], and delays that bus's charging.
All inventories start and end full. No execution is performed at import time.
"""
from fractions import Fraction as F
from itertools import combinations, product


def _solve(rows, rhs, n):
    a = [[F(v) for v in row] + [F(b)] for row, b in zip(rows, rhs)]
    r, pivots = 0, []
    for c in range(n):
        p = next((i for i in range(r, len(a)) if a[i][c]), None)
        if p is None:
            continue
        a[r], a[p] = a[p], a[r]
        d = a[r][c]
        a[r] = [v/d for v in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c]:
                d = a[i][c]
                a[i] = [v-d*w for v, w in zip(a[i], a[r])]
        pivots.append(c)
        r += 1
    if r != n or any(not any(row[:n]) and row[n] for row in a):
        return None
    q = [F(0)]*n
    for i, c in enumerate(pivots):
        q[c] = a[i][n]
    return tuple(q)


def _vertices(n, eq, le):
    out = set()
    for k in range(n+1):
        for active in combinations(le, k):
            rows = eq + list(active)
            q = _solve([a for a, _ in rows], [b for _, b in rows], n)
            if q is not None and all(sum(v*t for v, t in zip(a, q)) <= b for a, b in le):
                out.add(q)
    return sorted(out)


def _value(p):
    e, z, c = p
    return 4*e + (e*e+z*z)/10+c


def _branches(types, detour):
    branches = []
    for w in ([F(0), F(2)] if detour else [F(0)]):
        release = F(31, 10) if w else F(3)
        for name, capacity, fee in types:
            eq = [((1, 1), 30+w)]
            le = [((-1, 0), 0), ((1, 0), 10), ((1, 0), 15),
                  ((-1, 0), capacity-30-w), ((0, -1), 0),
                  ((0, 1), 30*(4-release)), ((0, 0), capacity-15)]
            branches.append(dict(label="AB:"+name+":w="+str(w),
                capacities=(capacity,), ops=fee, w=w, release=release,
                eq=eq, le=le, raw=_vertices(2, eq, le)))
        for ta, tb in product(types, repeat=2):
            na, ca, fa = ta
            nb, cb, fb = tb
            eq = [((1, 1, 0), 15), ((0, 0, 1), 15+w)]
            le = [((-1, 0, 0), 0), ((1, 0, 0), 10), ((1, 0, 0), 15),
                  ((0, -1, 0), 0), ((0, 0, -1), 0),
                  ((0, 1, 1), 30), ((0, 1, 0), 30),
                  ((0, 0, 1), 30*(4-release)),
                  ((0, 0, 0), ca-15), ((0, 0, 0), cb-15-w)]
            branches.append(dict(label="A:"+na+"|B:"+nb+":w="+str(w),
                capacities=(ca, cb), ops=fa+fb, w=w, release=release,
                eq=eq, le=le, raw=_vertices(3, eq, le)))
    return branches


def _witness(branch, x):
    caps, w = branch["capacities"], branch["w"]
    two = len(caps) == 2
    bbus = 1 if two else 0
    services = [(0, F(0), F(1), F(15)), (bbus, F(2), F(3), F(15))]
    movements = [(bbus, F(3), F(31, 10), F(20))] if w else []
    charges = [(0, F(1), F(1)+x/10, F(10))] if x else []
    if two:
        needs = [(0, 15-x), (1, 15+w)]
        cursor = F(3)
    else:
        needs = [(0, 30+w-x)]
        cursor = branch["release"]
    for bus, energy in needs:
        if energy:
            start = max(cursor, branch["release"] if bus == bbus else F(3))
            end = start+energy/30
            charges.append((bus, start, end, F(30)))
            cursor = end
    witness = dict(services=services, movements=movements, charges=charges)
    replay(branch, x, witness)
    return witness


def replay(branch, early, witness):
    """Independently check canonical service, movement, inventory and power."""
    caps, w = branch["capacities"], branch["w"]
    bbus = len(caps)-1
    expected = [(0, F(0), F(1), F(15)), (bbus, F(2), F(3), F(15))]
    move = [(bbus, F(3), F(31, 10), F(20))] if w else []
    assert witness["services"] == expected and witness["movements"] == move
    charges = witness["charges"]
    for bus, start, end, power in charges:
        assert 0 <= bus < len(caps) and start < end and power >= 0
        assert (1 <= start < end <= 2 and power <= 10) or (3 <= start < end <= 4 and power <= 30)
    cuts = sorted({F(0), F(1), F(2), F(3), F(4)} |
                  {t for records in (expected, move, charges) for _, s, e, _ in records for t in (s, e)})
    soc, e_total, z_total = list(caps), F(0), F(0)
    for left, right in zip(cuts, cuts[1:]):
        assert 0 <= left < right <= 4
        powers = [F(0)]*len(caps)
        drains = [F(0)]*len(caps)
        for bus, s, e, power in charges:
            if s <= left and right <= e:
                powers[bus] += power
        for bus, s, e, power in expected+move:
            if s <= left and right <= e:
                drains[bus] += power
        limit = F(10) if 1 <= left < 2 else F(30) if 3 <= left < 4 else F(0)
        assert sum(powers) <= limit
        for bus in range(len(caps)):
            assert powers[bus] <= limit and not (powers[bus] and drains[bus])
            soc[bus] += (powers[bus]-drains[bus])*(right-left)
            assert 0 <= soc[bus] <= caps[bus]
        if 1 <= left < 2:
            e_total += sum(powers)*(right-left)
        if 3 <= left < 4:
            z_total += sum(powers)*(right-left)
    assert tuple(soc) == caps
    assert e_total == early and e_total+z_total == 30+w
    return True


def _responses(branches, pe, pz):
    candidates = []
    for branch in branches:
        if not branch["raw"]:
            continue
        lo, hi = branch["interval"]
        slope = pe-pz
        x = lo if slope >= 0 else hi
        z = 30+branch["w"]-x
        cost = pe*x+pz*z+branch["ops"]
        interval = (lo, hi) if slope == 0 else (x, x)
        candidates.append(dict(label=branch["label"], early_interval=interval,
            total_energy=30+branch["w"], ops=branch["ops"], price_cost=cost,
            endpoint_witnesses=[_witness(branch, v) for v in sorted(set(interval))]))
    best = min(c["price_cost"] for c in candidates)
    return best, [c for c in candidates if c["price_cost"] == best], candidates


def _hull_minimum(points):
    # A minimizer lies on a supporting face because the c derivative is one.
    # A face has dimension at most two, hence needs at most three vertices.
    # Every simplex and every boundary is checked, without assuming hull facets.
    # If a simplex KKT system is singular, any stationary minimizer has a
    # zero-curvature feasible direction to its boundary; smaller subsets then
    # contain a minimizer with the identical projected (E,Z,c) point.
    points = sorted(set(points))
    candidates = set(points)
    for k in (2, 3):
        for simplex in combinations(points, k):
            rows, rhs = [], []
            for pi in simplex:
                rows.append([(pi[0]*pj[0]+pi[1]*pj[1])/5 for pj in simplex]+[F(1)])
                rhs.append(-4*pi[0]-pi[2])
            rows.append([F(1)]*k+[F(0)])
            rhs.append(F(1))
            solution = _solve(rows, rhs, k+1)
            if solution is not None and all(v >= 0 for v in solution[:k]):
                candidates.add(tuple(sum(solution[i]*simplex[i][j] for i in range(k)) for j in range(3)))
    value = min(_value(p) for p in candidates)
    return value, sorted(p for p in candidates if _value(p) == value)


def evaluate(B=None, fee=None, detour=False):
    """Return exact minima, all branches and continuous response argmin sets.

    B/fee must both be supplied or both omitted. Detour adds both movement
    choices, rather than requiring the energy-consuming movement.
    """
    types = [("old", F(20), F(7))]
    if (B is None) != (fee is None):
        raise ValueError("Supply both B and fee")
    if B is not None:
        B, fee = F(B), F(fee)
        if not 20 <= B <= 30 or fee < 7:
            raise ValueError("Require 20 <= B <= 30 and fee >= 7")
        types.append(("new", B, fee))
    branches = _branches(types, detour)
    endpoints, physical_candidates = [], []
    for branch in branches:
        raw = branch["raw"]
        branch["interval"] = (raw[0][0], raw[-1][0]) if raw else None
        branch["endpoints"] = []
        for q in raw:
            point = (q[0], sum(q[1:]), branch["ops"])
            record = dict(label=branch["label"], early=point[0], late=point[1],
                          ops=point[2], raw=q, witness=_witness(branch, q[0]))
            endpoints.append(record)
            branch["endpoints"].append(record)
        if raw:
            lo, hi = branch["interval"]
            x = min(hi, max(lo, (30+branch["w"]-20)/2))
            p = (x, 30+branch["w"]-x, branch["ops"])
            physical_candidates.append((_value(p), branch, p))
    D = min(v for v, _, _ in physical_candidates)
    optima = []
    for value, branch, p in physical_candidates:
        if value == D:
            e, z, c = p
            pe, pz = 4+e/5, z/5
            best, sets, all_responses = _responses(branches, pe, pz)
            optima.append(dict(label=branch["label"], early=e, late=z, ops=c,
                value=value, regret=pe*e+pz*z+c-best, response_sets=sets,
                prices=(pe, pz), all_branch_responses=all_responses,
                witness=_witness(branch, e)))
    CH, hull = _hull_minimum([(p["early"], p["late"], p["ops"]) for p in endpoints])
    old_best, old_sets, old_responses = _responses(branches, F(6), F(4))
    return dict(D=D, CH=CH, physical_optima=optima, hull_points=hull,
                old_plan_regret=F(147)-old_best, old_plan_response_sets=old_sets,
                old_plan_all_branch_responses=old_responses,
                branches=branches, physical_vertices=endpoints)
