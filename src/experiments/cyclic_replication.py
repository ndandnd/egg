"""Exact verification of the replenished fleet replication protocol; no solver."""
from fractions import Fraction as Q
from pathlib import Path
import argparse
import hashlib
import json
import platform
import subprocess
import time


def supply(n, x):
    return 4*x + (x*x+(30*n-x)**2)/Q(10*n)


def hull_edges(points):
    cheapest = {}
    for x, c in points:
        cheapest[x] = min(c, cheapest.get(x, c))
    hull = []
    for point in sorted(cheapest.items()):
        while len(hull) >= 2:
            x0, c0 = hull[-2]
            x1, c1 = hull[-1]
            x2, c2 = point
            if (x1-x0)*(c2-c0)-(c1-c0)*(x2-x0) > 0:
                break
            hull.pop()
        hull.append(point)
    return hull


def physical_template(n, m, x):
    u = (x-10*m)/(n-m) if m < n else Q(0)
    if not 0 <= u <= 10 or not 10*m <= x <= 10*n:
        raise ValueError('invalid early allocation')
    groups = []
    for count, services, early, terminal in (
        (m, ['A', 'B'], Q(10), Q(20)),
        (n-m, ['A'], u, 15-u),
        (n-m, ['B'], Q(0), Q(15)),
    ):
        if count == 0:
            continue
        soc = Q(20)
        states = [soc]
        soc -= 15 if 'A' in services else 0
        states.append(soc)
        soc += early
        states.append(soc)
        soc -= 15 if 'B' in services else 0
        states.append(soc)
        soc += terminal
        states.append(soc)
        if min(states) < 0 or max(states) > 20 or soc != 20:
            raise ValueError('physical SOC failure')
        groups.append(dict(count=count, services=services, early=early,
                           terminal=terminal, soc=states))
    early = sum(g['count']*g['early'] for g in groups)
    terminal = sum(g['count']*g['terminal'] for g in groups)
    if early != x or early+terminal != 30*n or terminal > 30*n:
        raise ValueError('resource or inventory failure')
    return dict(groups=groups, load=[early, terminal], used_buses=2*n-m,
                terminal_connector_groups=dict(paired_service=m,
                    sequential_single_service=n-m), single_pair_terminal_energy=30-u)


def case(n):
    branches = []
    endpoints = []
    for m in range(n+1):
        c = Q(7*(2*n-m))
        low, high = Q(10*m), Q(10*n)
        x = max(low, min(high, Q(5*n)))
        branches.append(dict(m=m, x=x, cost=c+supply(n, x)))
        endpoints.extend([(low, c), (high, c)])
    physical = min(row['cost'] for row in branches)
    hull = hull_edges(endpoints)
    candidates = [(c+supply(n, x), x, c) for x, c in hull]
    for (x0, c0), (x1, c1) in zip(hull, hull[1:]):
        slope = (c1-c0)/(x1-x0)
        x = max(x0, min(x1, (2-slope)*Q(5*n, 2)))
        c = c0+slope*(x-x0)
        candidates.append((c+supply(n, x), x, c))
    convexified, hx, hc = min(candidates)
    hp = [4+hx/Q(5*n), (30*n-hx)/Q(5*n)]
    hv = min(c+hp[0]*x+hp[1]*(30*n-x) for x, c in endpoints)
    hstar = sum(max(Q(0), p-a)**2*Q(5*n, 2) for p, a in zip(hp, [4, 0]))
    if hv-hstar != convexified or convexified != Q(7591*n, 80):
        raise AssertionError('hull closed form or dual account failed')
    winners = []
    for row in branches:
        if row['cost'] != physical:
            continue
        m, x = row['m'], row['x']
        c = Q(7*(2*n-m))
        p = [4+x/Q(5*n), (30*n-x)/Q(5*n)]
        response = min(ci+p[0]*xi+p[1]*(30*n-xi) for xi, ci in endpoints)
        regret = c+p[0]*x+p[1]*(30*n-x)-response
        delta = Q(m)-Q(27*n, 40)
        closed_regret = 40*Q(m, n)*delta if delta >= 0 else 40*(1-Q(m, n))*(-delta)
        if (physical-convexified != 20*delta*delta/n or regret != closed_regret
                or x != 10*m or abs(delta) > Q(1, 2)):
            raise AssertionError('physical closed form failed')
        bill = hp[0]*x+hp[1]*(30*n-x)
        fleet_loc, supply_loc = c+bill-hv, supply(n, x)-bill+hstar
        if fleet_loc != 0 or supply_loc != physical-convexified:
            raise AssertionError('common-price LOC account failed')
        winners.append(dict(m=m, delta=delta, early=x, price=p,
                            own_price_regret=regret, regret_per_used_bus=regret/(2*n-m),
                            regret_over_physical_cost=regret/physical,
                            fleet_LOC_at_hull_price=fleet_loc,
                            supply_LOC_at_hull_price=supply_loc,
                            witness=physical_template(n, m, x)))
    return dict(n=n, branch_optima=branches, physical=physical,
                convexified=convexified, gap=physical-convexified,
                relative_gap=(physical-convexified)/convexified,
                hull_vertices=hull, hull_load=[hx, 30*n-hx], hull_price=hp,
                hull_intrinsic_cost=hc, hull_response=hv, hull_conjugate=hstar,
                physical_optimizers=winners)


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
    paths = [Path(__file__).resolve(), root/'doc/CYCLIC_REPLICATION_PROTOCOL_20260927.md']
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    hashes = {}
    for p in paths:
        rel = p.relative_to(root).as_posix()
        frozen = subprocess.check_output(['git', '-C', str(root), 'show', head+':'+rel])
        if frozen != p.read_bytes():
            raise RuntimeError('source/protocol must be committed before execution')
        hashes[rel] = hashlib.sha256(frozen).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    grid = list(range(1, 81))+[120, 200, 400, 401, 1000, 1001]
    rows = [case(n) for n in grid]
    result = dict(head=head, source_hashes=hashes, python=platform.python_version(),
                  grid=grid, cases=rows, wall_s=time.perf_counter()-started,
                  interpretation='exact analytical verification; one price-taking whole-fleet operator')
    (args.output/'results.json').write_text(json.dumps(encode(result), sort_keys=True, indent=2)+'\n')
    print(json.dumps({'cases':len(rows), 'branch_minima':sum(len(c['branch_optima']) for c in rows),
                      'wall_s':result['wall_s']}))


if __name__ == '__main__':
    main()
