"""Exact continuous reserve/loss/one-connector verification; no optimizer."""
from fractions import Fraction as Q
from pathlib import Path
import argparse
import hashlib
import json
import platform
import subprocess
import time


def cost(x, total):
    return 4*x+(x*x+(total-x)**2)/10


def physical(n, x, reserve, efficiency, early_power, terminal_power):
    total = 30/efficiency
    if n == 1:
        groups = [dict(services=['A', 'B'], early=x, terminal=total-x)]
    else:
        groups = [dict(services=['A'], early=x, terminal=15/efficiency-x),
                  dict(services=['B'], early=Q(0), terminal=15/efficiency)]
    for bus in groups:
        soc = Q(20)
        states = [soc]
        soc -= 15 if 'A' in bus['services'] else 0
        states.append(soc)
        soc += efficiency*bus['early']
        states.append(soc)
        soc -= 15 if 'B' in bus['services'] else 0
        states.append(soc)
        soc += efficiency*bus['terminal']
        states.append(soc)
        if min(states) < reserve or max(states) > 20 or soc != 20:
            raise AssertionError('SOC/reserve/full-recharge failure')
        if not 0 <= bus['early'] <= early_power or bus['terminal'] < 0:
            raise AssertionError('charge sign/power failure')
        bus['soc'] = states
    terminal = sum(bus['terminal'] for bus in groups)
    if sum(bus['early'] for bus in groups) != x or terminal+x != total:
        raise AssertionError('grid energy conservation failure')
    if terminal > terminal_power:
        raise AssertionError('terminal shared power failure')
    sessions = []
    cursor = Q(3)
    if terminal:
        for index, bus in enumerate(groups):
            if bus['terminal']:
                end = cursor+bus['terminal']/terminal
                sessions.append(dict(bus=index, connector=0, start=cursor, end=end,
                                     power=terminal, energy=bus['terminal']))
                cursor = end
        if cursor != 4:
            raise AssertionError('terminal session horizon failure')
    return dict(buses=groups, load=[x, terminal], grid_total=total,
                battery_delivery=efficiency*total, terminal_sessions=sessions,
                margins=dict(early_power=early_power-x,
                             terminal_power=terminal_power-terminal,
                             reserve=min(s for bus in groups for s in bus['soc'])-reserve,
                             capacity=20-max(s for bus in groups for s in bus['soc'])))


def lower_hull(points):
    cheapest = {}
    for x, c, n in points:
        if x not in cheapest or c < cheapest[x][0]:
            cheapest[x] = (c, n)
    hull = []
    for x, (c, n) in sorted(cheapest.items()):
        while len(hull) >= 2:
            x0, c0, _ = hull[-2]
            x1, c1, _ = hull[-1]
            if (x1-x0)*(c-c0)-(c1-c0)*(x-x0) > 0:
                break
            hull.pop()
        hull.append((x, c, n))
    return hull


def case(reserve, efficiency, early_power, terminal_power):
    reserve, efficiency, early_power, terminal_power = map(Q,
        (reserve, efficiency, early_power, terminal_power))
    if not 0 <= reserve <= 5 or not 0 < efficiency <= 1:
        raise ValueError('outside the declared physical domain')
    total = 30/efficiency
    low, high = max(Q(0), total-terminal_power), min(early_power, 15/efficiency)
    intervals = [(1, max(low, (10+reserve)/efficiency), high), (2, low, high)]
    result = dict(reserve=reserve, efficiency=efficiency, early_power=early_power,
                  terminal_power=terminal_power, grid_total=total,
                  branches=[], feasible=False)
    points = []
    for n, lo, hi in intervals:
        row = dict(buses=n, lower=lo, upper=hi, feasible=lo <= hi)
        if lo <= hi:
            x = max(lo, min(hi, total/2-10))
            row.update(early=x, objective=7*n+cost(x, total),
                       witness=physical(n, x, reserve, efficiency, early_power, terminal_power))
            points.extend([(lo, Q(7*n), n), (hi, Q(7*n), n)])
        result['branches'].append(row)
    if not points:
        result.update(classification='infeasible', physical=None, convexified=None, gap=None)
        return result
    hull = lower_hull(points)
    candidates = [(c+cost(x, total), x, c, [(Q(1), n, x)]) for x, c, n in hull]
    for (x0, c0, n0), (x1, c1, n1) in zip(hull, hull[1:]):
        slope = (c1-c0)/(x1-x0)
        x = max(x0, min(x1, (total-20-5*slope)/2))
        weight = (x1-x)/(x1-x0)
        c = weight*c0+(1-weight)*c1
        candidates.append((c+cost(x, total), x, c,
                           [(weight, n0, x0), (1-weight, n1, x1)]))
    ch, xh, ch_cost, components = min(candidates, key=lambda row:row[0])
    d = min(row['objective'] for row in result['branches'] if row['feasible'])
    if d < ch:
        raise AssertionError('negative hull gap')
    hp = [4+xh/5, (total-xh)/5]
    hv = min(c+hp[0]*x+hp[1]*(total-x) for x, c, _ in points)
    hstar = sum(max(Q(0), p-a)**2*Q(5, 2) for p, a in zip(hp, [4, 0]))
    if hv-hstar != ch:
        raise AssertionError('hull price/dual identity failure')
    for row in result['branches']:
        if not row['feasible']:
            continue
        x, c = row['early'], Q(7*row['buses'])
        p = [4+x/5, (total-x)/5]
        own_v = min(ci+p[0]*xi+p[1]*(total-xi) for xi, ci, _ in points)
        bill = hp[0]*x+hp[1]*(total-x)
        row.update(own_price=p, own_price_regret=c+p[0]*x+p[1]*(total-x)-own_v,
                   fleet_LOC_at_hull_price=c+bill-hv,
                   supply_LOC_at_hull_price=cost(x,total)-bill+hstar)
        if (row['fleet_LOC_at_hull_price'] < 0 or row['supply_LOC_at_hull_price'] < 0
                or row['fleet_LOC_at_hull_price']+row['supply_LOC_at_hull_price'] != row['objective']-ch):
            raise AssertionError('branch participant accounting failure')
    result.update(feasible=True, classification='positive' if d > ch else 'zero',
                  physical=d, convexified=ch, gap=d-ch, hull_vertices=hull,
                  hull_load=[xh, total-xh], hull_intrinsic_cost=ch_cost,
                  hull_price=hp, hull_response=hv, hull_conjugate=hstar,
                  endpoint_witnesses=[dict(early=x, intrinsic_cost=c, buses=n,
                      witness=physical(n,x,reserve,efficiency,early_power,terminal_power))
                      for x, c, n in sorted(set(points))],
                  physical_optimal_bus_counts=[row['buses'] for row in result['branches']
                       if row['feasible'] and row['objective'] == d],
                  hull_components=[dict(weight=w, buses=n,
                      witness=physical(n, x, reserve, efficiency, early_power, terminal_power))
                      for w, n, x in components if w > 0])
    if sum(c['weight'] for c in result['hull_components']) != 1:
        raise AssertionError('mixture weight failure')
    return result


def encode(v):
    if isinstance(v, Q):
        return {'exact':str(v), 'value':float(v)}
    if isinstance(v, dict):
        return {k:encode(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [encode(x) for x in v]
    return v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    paths = [Path(__file__).resolve(), root/'doc/CYCLIC_ROBUSTNESS_PROTOCOL_20260927.md',
             root/'doc/CYCLIC_ROBUSTNESS_DESIGN_20260927.md']
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    hashes = {}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        raw = subprocess.check_output(['git', '-C', str(root), 'show', head+':'+rel])
        if raw != path.read_bytes():
            raise RuntimeError('source/design/protocol must be frozen before execution')
        hashes[rel] = hashlib.sha256(raw).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    grid = [(r, eta, pe, Q(30)) for r in (Q(0), Q(1))
            for eta in (Q(1), Q(19, 20)) for pe in (Q(10), Q(11), Q(12))]
    grid += [(Q(0), Q(1), Q(10), k) for k in (Q(10), Q(20), Q(47, 2), Q(24))]
    rows = [case(*parameters) for parameters in grid]
    counts = {label:sum(row['classification'] == label for row in rows)
              for label in ('positive', 'zero', 'infeasible')}
    result = dict(head=head, source_hashes=hashes, python=platform.python_version(),
                  units=dict(time='hours', grid_energy='kWh purchased',
                             battery_energy='kWh stored/consumed', power='grid kW',
                             costs='synthetic currency', efficiency='battery kWh per grid kWh'),
                  grid=grid, cases=rows, classifications=counts,
                  analytical_prediction=dict(positive=9, zero=6, infeasible=1),
                  prediction_matches=counts == dict(positive=9, zero=6, infeasible=1),
                  wall_s=time.perf_counter()-started)
    (args.output/'results.json').write_text(json.dumps(encode(result), sort_keys=True, indent=2)+'\n')
    print(json.dumps({'cases':len(rows), 'classifications':counts,
                      'prediction_matches':result['prediction_matches'], 'wall_s':result['wall_s']}))


if __name__ == '__main__':
    main()
