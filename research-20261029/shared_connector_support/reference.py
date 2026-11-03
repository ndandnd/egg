"""Exact raw-SOC reference, n<=3, one fixed connector in each window.

No matching threshold or clipped-frontier formula is used. Vertex arithmetic
is adapted from the qualified heterogeneous_support reference; physics is new.
"""
from fractions import Fraction as F
from itertools import combinations


def _solve(rows, rhs, n):
    a = [[F(v) for v in row]+[F(b)] for row, b in zip(rows, rhs)]
    for c in range(n):
        pivot = next((i for i in range(c, n) if a[i][c]), None)
        if pivot is None:
            return None
        a[c], a[pivot] = a[pivot], a[c]
        d = a[c][c]
        a[c] = [v/d for v in a[c]]
        for i in range(n):
            if i != c and a[i][c]:
                d = a[i][c]
                a[i] = [v-d*w for v, w in zip(a[i], a[c])]
    return tuple(row[-1] for row in a)


def _vertices(n, constraints):
    reduced = {}
    for item in constraints:
        row, rhs = item['row'], item['rhs']
        if not any(row):
            if rhs < 0:
                return []
            continue
        reduced[row] = min(rhs, reduced.get(row, rhs))
    inequalities = sorted(reduced.items())
    result = set()
    for active in combinations(inequalities, n):
        point = _solve([r for r, _ in active], [b for _, b in active], n)
        if point is not None and all(sum(c*x for c, x in zip(r, point)) <= b
                                     for r, b in inequalities):
            result.add(point)
    return sorted(result)


def _matchings(n):
    def extend(i, available, pairs):
        if i == n:
            yield tuple(pairs)
            return
        yield from extend(i+1, available, pairs)
        for j in sorted(available):
            yield from extend(i+1, available-{j}, pairs+[(i, j)])
    return list(extend(0, set(range(n)), []))


def _model(A, B, capacity, K, H, fee, pairs):
    n = len(A)
    paired, used = dict(pairs), {j for _, j in pairs}
    buses = [dict(bus=i, A=i, B=paired.get(i)) for i in range(n)]
    buses += [dict(bus=n+j, A=None, B=j) for j in range(n) if j not in used]
    rows, equalities = [], []
    def le(row, rhs, description):
        rows.append(dict(row=tuple(map(F, row)), rhs=F(rhs), description=description))
    total, terminal_row = F(0), [F(0)]*n
    for bus in buses:
        i, j = bus['A'], bus['B']
        row = [F(0)]*n
        demand = (A[i] if i is not None else 0)+(B[j] if j is not None else 0)
        if i is not None:
            row[i] = 1
            le([-v for v in row], 0, 'early charge nonnegative')
            le([0]*n, capacity-A[i], 'SOC after A nonnegative')
            le(row, A[i], 'early battery headroom')
            le([-v for v in row], capacity-demand, 'SOC after B nonnegative')
        else:
            le([0]*n, capacity-demand, 'B-only SOC nonnegative')
        # Raw full-refill equation z_bus=demand-q_i, eliminated exactly.
        equalities.append(dict(bus=bus['bus'], terminal_constant=demand,
                               terminal_early_row=tuple(-v for v in row), full_soc=capacity))
        le(row, demand, 'terminal charge nonnegative')
        le([-v for v in row], capacity-demand, 'terminal battery headroom')
        terminal_row = [v-w for v, w in zip(terminal_row, row)]
        total += demand
    le([1]*n, K, 'one shared early connector energy')
    le(terminal_row, H-total, 'one shared terminal connector energy')
    vertices = _vertices(n, rows)
    return dict(pairs=pairs, buses=buses, ops=fee*len(buses), constraints=rows,
                equalities=equalities, vertices=vertices,
                interval=(min(map(sum, vertices)), max(map(sum, vertices))) if vertices else None)


def _allocation(model, E):
    lo = min(model['vertices'], key=lambda x: (sum(x), x))
    hi = max(model['vertices'], key=lambda x: (sum(x), x))
    assert sum(lo) <= E <= sum(hi)
    w = (E-sum(lo))/(sum(hi)-sum(lo)) if sum(hi) != sum(lo) else F(0)
    return tuple((1-w)*x+w*y for x, y in zip(lo, hi))


def _witness(A, B, capacity, K, H, model, E, allocation=None):
    q = _allocation(model, E) if allocation is None else tuple(allocation)
    paired = dict(model['pairs'])
    services = [(i, 'A', i, F(0), F(1), a) for i, a in enumerate(A)]
    services += [(next((i for i, jj in model['pairs'] if jj == j), len(A)+j),
                  'B', j, F(2), F(3), b) for j, b in enumerate(B)]
    charges = []
    for window, power, start, energies in (
            ('early', K, F(1), [(i, q[i]) for i in range(len(A))]),
            ('terminal', H, F(3), [(bus['bus'],
                (A[bus['A']] if bus['A'] is not None else 0)
                +(B[bus['B']] if bus['B'] is not None else 0)
                -(q[bus['A']] if bus['A'] is not None else 0)) for bus in model['buses']])):
        cursor = start
        for bus, energy in energies:
            assert energy >= 0
            if energy:
                assert power > 0
                end = cursor+energy/power
                charges.append((bus, window, 0, cursor, end, power))
                cursor = end
    answer = dict(early_allocation=q, services=services, charges=charges)
    replay(A, B, capacity, K, H, model['pairs'], E, answer)
    return answer


def replay(A, B, capacity, K, H, pairs, E, witness):
    """Raw chronological SOC, coverage, one connector, power and full refill."""
    A, B = tuple(map(F, A)), tuple(map(F, B))
    capacity, K, H, E = map(F, (capacity, K, H, E))
    n = len(A)
    assert len(B) == n and len({i for i, j in pairs}) == len(pairs) == len({j for i, j in pairs})
    assert all(0 <= i < n and 0 <= j < n for i, j in pairs)
    expected = [(i, 'A', i, F(0), F(1), a) for i, a in enumerate(A)]
    expected += [(next((i for i, jj in pairs if jj == j), n+j), 'B', j, F(2), F(3), b)
                 for j, b in enumerate(B)]
    assert sorted(witness['services']) == sorted(expected)
    buses = {row[0] for row in expected}
    charges = witness['charges']
    for bus, window, connector, start, end, power in charges:
        assert bus in buses and connector == 0 and start < end and power > 0
        assert (window == 'early' and 1 <= start < end <= 2 and power <= K) or (
                window == 'terminal' and 3 <= start < end <= 4 and power <= H)
    cuts = sorted({F(0), F(1), F(2), F(3), F(4)} |
                  {t for _, _, _, s, e, _ in charges for t in (s, e)})
    soc, early = {bus: capacity for bus in buses}, {bus: F(0) for bus in buses}
    late = F(0)
    for left, right in zip(cuts, cuts[1:]):
        active = [row for row in charges if row[3] <= left and right <= row[4]]
        assert len(active) <= 1
        for bus in buses:
            own = [row for row in active if row[0] == bus]
            serving = [row for row in expected if row[0] == bus and row[3] <= left and right <= row[4]]
            assert len(serving) <= 1 and not (own and serving)
            gain = sum((row[5]*(right-left) for row in own), F(0))
            if 1 <= left < 2:
                early[bus] += gain
            elif 3 <= left < 4:
                late += gain
            soc[bus] += gain-(serving[0][5]*(right-left) if serving else 0)
            assert 0 <= soc[bus] <= capacity
    assert all(v == capacity for v in soc.values())
    assert sum(early.values()) == E and E+late == sum(A)+sum(B)
    assert tuple(early[i] for i in range(n)) == tuple(witness['early_allocation'])
    assert all(early[bus] == 0 for bus in buses if bus >= n)
    return True


def _hull(points):
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for chain, sequence in ((lower, points), (upper, reversed(points))):
        for point in sequence:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
    return lower, lower[:-1]+upper[:-1] if len(points) > 1 else points


def evaluate(A, B, capacity=F(20), K=F(10), H=F(30), fee=F(7)):
    """Exact joint projection, all optimal assignment labels and response sets.

    Allocation continua are represented by raw inequalities plus a sum equality;
    no finite list is claimed to enumerate all charging schedules.
    """
    A, B = tuple(map(F, A)), tuple(map(F, B))
    capacity, K, H, fee = map(F, (capacity, K, H, fee))
    n = len(A)
    if not 1 <= n <= 3 or len(B) != n or capacity <= 0 or min(K, H, fee) < 0:
        raise ValueError('Require n=1..3, capacity>0, K,H,fee>=0')
    if any(not 0 < v <= capacity for v in A+B):
        raise ValueError('Every service energy must lie in (0,capacity]')
    S = sum(A)+sum(B)
    energy = lambda E: 4*E+(E*E+(S-E)**2)/(10*n)
    models = [_model(A, B, capacity, K, H, fee, p) for p in _matchings(n)]
    candidates, points = [], []
    for index, model in enumerate(models):
        model.update(assignment_id=index, endpoints=[])
        for vertex in model['vertices']:
            E = sum(vertex)
            points.append((E, model['ops']))
            model['endpoints'].append(dict(early=E, late=S-E, ops=model['ops'], raw_early=vertex,
                witness=_witness(A, B, capacity, K, H, model, E, vertex)))
        if model['interval'] is not None:
            lo, hi = model['interval']
            E = min(hi, max(lo, (S-20*n)/2))
            candidates.append((energy(E)+model['ops'], index, E))
    provenance = dict(n=n, A=A, B=B, capacity=capacity, K=K, H=H, fee=fee,
        arithmetic='stdlib Fraction', early_connectors=1, terminal_connectors=1,
        windows=((1, 2), (3, 4)), objective='4E+(E^2+late^2)/(10n)',
        enumeration='complete partial crossmatchings; raw per-bus SOC active vertices')
    if not candidates:
        return dict(status='INFEASIBLE', D=None, CH=None, gap=None, physical_optima=[],
                    hull_optima=[], assignments=models, rawcount=len(models), provenance=provenance)
    D = min(v for v, _, _ in candidates)
    optima = []
    for value, index, E in candidates:
        if value != D:
            continue
        model = models[index]
        pe, pz = 4+E/(5*n), (S-E)/(5*n)
        responses = []
        for response in models:
            if response['interval'] is None:
                continue
            lo, hi = response['interval']
            x = lo if pe >= pz else hi
            interval = (lo, hi) if pe == pz else (x, x)
            responses.append(dict(assignment_id=response['assignment_id'], pairs=response['pairs'],
                early_interval=interval, ops=response['ops'],
                price_cost=response['ops']+pe*x+pz*(S-x),
                allocation_set=dict(inequalities=response['constraints'], sum_interval=interval)))
        best = min(row['price_cost'] for row in responses)
        optima.append(dict(assignment_id=index, pairs=model['pairs'], early=E, late=S-E,
            ops=model['ops'], value=value, prices=(pe, pz),
            regret=pe*E+pz*(S-E)+model['ops']-best,
            response_sets=[row for row in responses if row['price_cost'] == best],
            allocation_set=dict(inequalities=model['constraints'], sum_equality=([F(1)]*n, E)),
            witness=_witness(A, B, capacity, K, H, model, E)))
    lower, hull = _hull(points)
    hull_candidates = set(lower)
    for left, right in zip(lower, lower[1:]):
        if left[0] == right[0]:
            continue
        slope = (right[1]-left[1])/(right[0]-left[0])
        E = min(right[0], max(left[0], (S-20*n)/2-F(5*n, 2)*slope))
        hull_candidates.add((E, left[1]+slope*(E-left[0])))
    CH = min(energy(E)+ops for E, ops in hull_candidates)
    return dict(status='FEASIBLE', D=D, CH=CH, gap=D-CH, physical_optima=optima,
        hull_optima=[dict(early=E, late=S-E, ops=ops, value=CH)
                     for E, ops in sorted(hull_candidates) if energy(E)+ops == CH],
        hull_vertices=hull, lower_hull=lower, assignments=models, rawcount=len(models),
        provenance=provenance)
