"""Independent raw per-bus polygon reference. Definitions only; stdlib only.

No minimum-matching-requirement aggregate formula is used. Every partial
matching and every bus polygon is retained, including empty degeneracies.
"""
from fractions import Fraction as F
from itertools import combinations
import re

LIMITS = dict(operations=2000000, fraction_bits=16384, vertices=4096,
              actions=16384, numeric_chars=4096)


class ReferenceLimit(RuntimeError):
    pass


def _need(ok, message):
    if not ok:
        raise ValueError(message)


class Meter:
    def __init__(self):
        self.operations = 0

    def tick(self, count=1):
        self.operations += count
        if self.operations > LIMITS['operations']:
            raise ReferenceLimit('Exact operation allowance exceeded')

    def q(self, value):
        self.tick()
        value = F(value)
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > LIMITS['fraction_bits']:
            raise ReferenceLimit('Fraction bit allowance exceeded')
        return value


def _number(value, meter):
    _need(type(value) in (str, int) or isinstance(value, F), 'Exact numeric token required')
    if type(value) is str:
        _need(len(value) <= LIMITS['numeric_chars'] and
              re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*)?', value) is not None,
              'Bounded integer/fraction string required')
    return meter.q(value)


def _spec(spec, meter):
    _need(type(spec) is dict and set(spec) ==
          {'id', 'B', 'a', 'b', 'alpha', 'delta', 'K', 'H', 'fee', 'd', 'edges'},
          'Literal schema mismatch')
    _need(type(spec['id']) is str and 0 < len(spec['id']) <= 256, 'Literal id')
    _need(type(spec['a']) is list and type(spec['b']) is list and
          len(spec['a']) == len(spec['b']) and 1 <= len(spec['a']) <= 2, 'Require equal batches, 1<=n<=2')
    out = {k: _number(spec[k], meter) for k in ('B', 'alpha', 'delta', 'K', 'H', 'fee', 'd')}
    out.update(id=spec['id'], a=[_number(v, meter) for v in spec['a']],
               b=[_number(v, meter) for v in spec['b']])
    _need(out['B'] > 0 and 0 < out['alpha'] <= 1 and 0 < out['delta'] <= 1,
          'Capacity/efficiency domain')
    _need(all(out[k] >= 0 for k in ('K', 'H', 'fee', 'd')), 'Nonnegative resources/fee/transition')
    _need(all(0 < v <= out['B'] for v in out['a'] + out['b']), 'Service energy domain')
    n = len(out['a'])
    _need(type(spec['edges']) is list and len(spec['edges']) <= n*n, 'Edge denominator')
    edges = []
    for edge in spec['edges']:
        _need(type(edge) in (list, tuple) and len(edge) == 2 and
              all(type(i) is int and 0 <= i < n for i in edge), 'Edge index')
        edge = tuple(edge)
        _need(edge not in edges, 'Duplicate allowed edge')
        _need(out['b'][edge[1]]+out['d'] <= out['B'], 'Allowed edge post-early consumption exceeds capacity')
        edges.append(edge)
    out['edges'] = tuple(sorted(edges))
    return out


def _matchings(s):
    def visit(i, pairs, used):
        if i == len(s['a']):
            yield tuple(pairs)
            return
        yield from visit(i+1, pairs, used)
        for j in range(len(s['b'])):
            if j not in used and (i, j) in s['edges']:
                yield from visit(i+1, pairs+[(i, j)], used | {j})
    return visit(0, [], set())


def _buses(s, pairs):
    used_a, used_b = {i for i, j in pairs}, {j for i, j in pairs}
    assigned = list(pairs) + [(i, None) for i in range(len(s['a'])) if i not in used_a]
    assigned += [(None, j) for j in range(len(s['b'])) if j not in used_b]
    result = []
    for index, (i, j) in enumerate(assigned):
        a = F(0) if i is None else s['a'][i]
        b = F(0) if j is None else s['b'][j]
        d = s['d'] if i is not None and j is not None else F(0)
        result.append(dict(id=index, A=i, B=j, a=a, b=b, d=d,
                           initial=s['B']-a, lower=a+b+d-s['B'], upper=a,
                           consumption=a+b+d))
    return result


def _cross(o, a, b, meter):
    return meter.q((a['C']-o['C'])*(b['X']-o['X']) -
                   (a['X']-o['X'])*(b['C']-o['C']))


def _hull(points, meter):
    unique = {}
    for point in points:
        meter.tick()
        unique.setdefault((point['C'], point['X']), point)
    ordered = [unique[k] for k in sorted(unique)]
    if len(ordered) > LIMITS['vertices']:
        raise ReferenceLimit('Vertex allowance exceeded')
    if len(ordered) <= 1:
        return ordered
    lower, upper = [], []
    for chain, source in ((lower, ordered), (upper, reversed(ordered))):
        for point in source:
            while len(chain) >= 2 and _cross(chain[-2], chain[-1], point, meter) <= 0:
                chain.pop()
            chain.append(point)
    return lower[:-1] + upper[:-1]


def _raw_bus(s, bus, meter):
    # Each row is a*C+b*X<=rhs, directly from this bus's endpoint SOC.
    alpha, delta = s['alpha'], s['delta']
    rows = [(-F(1), F(0), F(0), 'purchase_nonnegative'),
            (F(0), -F(1), F(0), 'export_nonnegative'),
            (-alpha, F(1)/delta, -bus['lower'], 'post_service_reserve'),
            (alpha, -F(1)/delta, bus['upper'], 'post_early_capacity'),
            (F(1), F(1), s['K'], 'individual_gross_necessary')]
    points = []
    for first, second in combinations(rows, 2):
        a, b, rhs, _ = first
        c, d, target, _ = second
        determinant = meter.q(a*d-b*c)
        if determinant == 0:
            continue
        C = meter.q((rhs*d-b*target)/determinant)
        X = meter.q((a*target-rhs*c)/determinant)
        if all(meter.q(u*C+v*X-w) <= 0 for u, v, w, name in rows):
            points.append(dict(C=C, X=X, allocation=[dict(C=C, X=X)]))
    return rows, _hull(points, meter)


def _blend(a, b, t, meter):
    _need(len(a['allocation']) == len(b['allocation']), 'Allocation interpolation dimension')
    return dict(C=meter.q((1-t)*a['C']+t*b['C']),
                X=meter.q((1-t)*a['X']+t*b['X']),
                allocation=[{k: meter.q((1-t)*x[k]+t*y[k]) for k in ('C', 'X')}
                            for x, y in zip(a['allocation'], b['allocation'])])


def _clip(points, a, b, rhs, meter):
    if not points:
        return []
    residuals = [meter.q(a*p['C']+b*p['X']-rhs) for p in points]
    kept = [p for p, residual in zip(points, residuals) if residual <= 0]
    if len(points) >= 2:
        for i, first in enumerate(points):
            j = (i+1) % len(points)
            x, y = residuals[i], residuals[j]
            if (x < 0 < y) or (y < 0 < x):
                kept.append(_blend(first, points[j], meter.q(x/(x-y)), meter))
    return _hull(kept, meter)


def _schedule(s, buses, vertex, meter):
    early, terminal = [], []
    clock = F(1)
    for bus, allocation in zip(buses, vertex['allocation']):
        C, X = allocation['C'], allocation['X']
        exchange = meter.q(s['alpha']*C-X/s['delta'])
        base_C = max(exchange, F(0))/s['alpha']
        base_X = s['delta']*max(-exchange, F(0))
        residual = meter.q(C-base_C)
        _need(residual >= 0 and meter.q(X-base_X) == s['alpha']*s['delta']*residual,
              'Per-bus cycle decomposition')
        remaining = meter.q(s['alpha']*residual)
        charge_first = bus['initial'] <= s['B']/2
        def action(kind, energy):
            nonlocal clock
            if energy == 0:
                return
            if len(early) >= LIMITS['actions']:
                raise ReferenceLimit('Finite action allowance exceeded')
            _need(s['K'] > 0, 'Positive early energy at zero power')
            end = meter.q(clock+energy/s['K'])
            early.append(dict(bus=bus['id'], kind=kind, energy=energy,
                              start=clock, end=end, power=s['K']))
            clock = end
        while remaining > 0:
            meter.tick()
            depth = min(remaining, s['B']/2)
            cycle = [('charge', depth/s['alpha']), ('export', s['delta']*depth)]
            if not charge_first:
                cycle.reverse()
            for kind, energy in cycle:
                action(kind, meter.q(energy))
            remaining = meter.q(remaining-depth)
        action('charge', meter.q(base_C))
        action('export', meter.q(base_X))
    terminal_clock = F(4)
    for bus, allocation in zip(buses, vertex['allocation']):
        exchange = s['alpha']*allocation['C']-allocation['X']/s['delta']
        energy = meter.q((bus['consumption']-exchange)/s['alpha'])
        _need(energy >= 0, 'Negative terminal charge')
        if energy:
            _need(s['H'] > 0, 'Positive terminal energy at zero power')
            end = meter.q(terminal_clock+energy/s['H'])
            terminal.append(dict(bus=bus['id'], kind='charge', energy=energy,
                                 start=terminal_clock, end=end, power=s['H']))
            terminal_clock = end
    return dict(early=early, terminal=terminal,
                windows=dict(A=(F(0), F(1)), early=(F(1), F(2)),
                             transition=(F(2), F(3)), B=(F(3), F(4)), terminal=(F(4), F(5))))


def _finish(s, buses, point, meter):
    point = dict(point)
    total = sum((b['consumption'] for b in buses), F(0))
    point.update(Q=meter.q(s['alpha']*point['C']-point['X']/s['delta']),
                 E=meter.q(point['C']-point['X']), ops=s['fee']*len(buses))
    point['L'] = meter.q((total-point['Q'])/s['alpha'])
    point['witness'] = _schedule(s, buses, point, meter)
    return point


def enumerate_physical(spec):
    meter = Meter()
    s = _spec(spec, meter)
    records = []
    strict_replayed_vertices = 0
    for pairs in _matchings(s):
        meter.tick()
        buses = _buses(s, pairs)
        raw, points = [], [dict(C=F(0), X=F(0), allocation=[])]
        for bus in buses:
            rows, vertices = _raw_bus(s, bus, meter)
            raw.append(dict(bus=bus['id'], rows=rows, vertices=vertices))
            summed = []
            for p in points:
                for v in vertices:
                    meter.tick()
                    summed.append(dict(C=meter.q(p['C']+v['C']), X=meter.q(p['X']+v['X']),
                                       allocation=p['allocation']+v['allocation']))
            points = _hull(summed, meter)
        points = _clip(points, F(1), F(1), s['K'], meter)
        total = sum((b['consumption'] for b in buses), F(0))
        points = _clip(points, -s['alpha'], F(1)/s['delta'], -(total-s['alpha']*s['H']), meter)
        label = 'm'+str(len(pairs))+':' + (','.join(str(i)+'-'+str(j) for i, j in pairs) or 'empty')
        record = dict(id=label, pairs=pairs, cardinality=len(pairs), fleet=len(buses),
                      buses=buses, total_consumption=total, raw_bus_polygons=raw,
                      vertices=[_finish(s, buses, p, meter) for p in points])
        record['dimension'] = -1 if not points else 0 if len(points) == 1 else 1 if len(points) == 2 else 2
        for vertex in record['vertices']:
            outcome = replay(spec, record, vertex)
            meter.tick(outcome['operations'])
            _need(outcome['strict_pass'], 'Constructed vertex failed independent replay: '+str(outcome['violations']))
            strict_replayed_vertices += 1
        record['strict_replayed_vertices'] = len(record['vertices'])
        records.append(record)
    return dict(status='ENUMERATED', id=s['id'], records=records,
                matching_count=len(records), feasible_count=sum(bool(r['vertices']) for r in records),
                strict_replayed_vertices=strict_replayed_vertices,
                operations=meter.operations, limits=dict(LIMITS),
                provenance='Raw per-bus SOC polygons, Minkowski sums and exact halfplane clipping; no aggregate matching formula')


def replay(spec, record, vertex):
    """Strict reconstruction from assignment and timed actions; never repairs."""
    meter = Meter()
    s = _spec(spec, meter)
    failures = []
    def check(ok, name):
        if not ok:
            failures.append(name)
    pairs = tuple(tuple(p) for p in record['pairs'])
    _need(all(len(p) == 2 and all(type(i) is int for i in p) for p in pairs), 'Assignment index types')
    _need(pairs in tuple(_matchings(s)), 'Unknown/nonmatching assignment')
    buses = _buses(s, pairs)
    check(record['buses'] == buses, 'canonical_bus_assignment')
    check(record['cardinality'] == len(pairs) and record['fleet'] == len(buses), 'fleet_metadata')
    check(len(vertex['allocation']) == len(buses), 'allocation_denominator')
    soc = [s['B'] for bus in buses]
    for bus in buses:
        soc[bus['id']] -= bus['a']
        check(0 <= soc[bus['id']] <= s['B'], 'after_A:'+str(bus['id']))
    totals = [dict(C=F(0), X=F(0)) for bus in buses]
    witness = vertex['witness']
    check(witness['windows'] == dict(A=(F(0), F(1)), early=(F(1), F(2)),
                                     transition=(F(2), F(3)), B=(F(3), F(4)),
                                     terminal=(F(4), F(5))), 'reported_windows')
    for section, start, stop, capacity in (('early', F(1), F(2), s['K']),
                                            ('terminal', F(4), F(5), s['H'])):
        if section == 'terminal':
            for bus in buses:
                index = bus['id']
                soc[index] = meter.q(soc[index]-bus['d'])
                check(0 <= soc[index] <= s['B'], 'after_transition:'+str(index))
                soc[index] = meter.q(soc[index]-bus['b'])
                check(0 <= soc[index] <= s['B'], 'after_B:'+str(index))
        actions = witness[section]
        _need(type(actions) is list and len(actions) <= LIMITS['actions'], 'Action denominator')
        last = start
        for action in actions:
            meter.tick()
            index = action['bus']
            _need(type(index) is int and 0 <= index < len(buses), 'Unknown action bus')
            kind = action['kind']
            _need(kind in ('charge', 'export') and (section == 'early' or kind == 'charge'), 'Direction/window')
            energy, a, b, power = (_number(action[k], meter) for k in ('energy', 'start', 'end', 'power'))
            check(energy > 0 and start <= a < b <= stop, 'action_window')
            check(a >= last, 'shared_connector_overlap')
            check(0 < power <= capacity and energy == power*(b-a), 'power_energy_identity')
            last = b
            if kind == 'charge':
                soc[index] = meter.q(soc[index]+s['alpha']*energy)
                if section == 'early':
                    totals[index]['C'] = meter.q(totals[index]['C']+energy)
            else:
                soc[index] = meter.q(soc[index]-energy/s['delta'])
                totals[index]['X'] = meter.q(totals[index]['X']+energy)
            check(0 <= soc[index] <= s['B'], 'action_SOC:'+str(index))
        if section == 'early':
            for actual, claimed in zip(totals, vertex['allocation']):
                check(actual == claimed, 'per_bus_C_X')
    C = meter.q(sum((x['C'] for x in totals), F(0)))
    X = meter.q(sum((x['X'] for x in totals), F(0)))
    L = meter.q(sum((_number(a['energy'], meter) for a in witness['terminal']), F(0)))
    Q = meter.q(s['alpha']*C-X/s['delta'])
    total = sum((b['consumption'] for b in buses), F(0))
    for key, actual in dict(C=C, X=X, Q=Q, E=C-X, L=L, ops=s['fee']*len(buses)).items():
        check(_number(vertex[key], meter) == actual, 'reported_'+key)
    check(C+X <= s['K'] and L <= s['H'], 'total_resources')
    check(s['alpha']*L == total-Q, 'full_inventory_accounting')
    check(all(value == s['B'] for value in soc), 'every_bus_terminal_full')
    check(record['total_consumption'] == total, 'reported_total_consumption')
    return dict(strict_pass=not failures, violations=failures, C=C, X=X, Q=Q,
                E=C-X, L=L, ops=s['fee']*len(buses), operations=meter.operations)
