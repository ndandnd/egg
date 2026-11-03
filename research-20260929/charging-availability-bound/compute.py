"""Exact, reporting-only public energy bound; no optimizer or native model calls."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from egglab import analytic_energy_floor as old


def hourly_caps(case):
    """Union of ALL declared recharge windows, intersected with resource periods.

    This is a superset of any fleet's selected visits. Pullout/direct movements
    admit no charging in the pinned physical model. Full initial inventory and
    zero parked draw admit no initial charging. Multiple windows are unioned,
    never added; the single connector supplies at most min(bus, grid) power.
    """
    windows = []
    for m in case['movements']:
        if m['kind'] == 'depot':
            k = m['depot_split']
            windows.append((Q(m['legs'][k-1]['arrive_min']), Q(m['legs'][k]['depart_min'])))
        elif m['kind'] == 'pullin':
            windows.append((max(Q(m['legs'][-1]['arrive_min']), Q(case['terminal_open_min'])),
                            Q(case['recharge_deadline_min'])))
    edges = list(map(Q, case['market_edges_min']))
    points = sorted(set(edges + [x for w in windows for x in w] +
                        [Q(r[k]) for r in case['resources'] for k in ('start_min', 'end_min')]))
    caps = [Q(0)] * (len(edges)-1)
    for lo, hi in zip(points, points[1:]):
        if hi <= lo or not any(a <= lo and hi <= b for a, b in windows):
            continue
        r = next(r for r in case['resources'] if Q(r['start_min']) <= lo < Q(r['end_min']))
        assert r['connectors'] == 1, 'Proof scoped to pinned single-connector cases'
        period = next(t for t in range(len(caps)) if edges[t] <= lo < edges[t+1])
        caps[period] += min(Q(r['grid_kw']), Q(r['per_bus_kw'])) * (hi-lo)/60
    return caps, min(a for a, b in windows if b > a)


def conjugate(p, a, b, cap):
    load = min(cap, max(Q(0), (p-a)/b))
    return (p-a)*load - b*load*load/2


def dual_bound(f, e2, esvc, aa, bb, caps):
    """Maximize min(2f+pE2,3f+pEsvc)-sum capped conjugates for p>=0.

    All breakpoints and stationary candidates are rational. The two cardinality
    lines form a lower bound, not a physical two-/three-bus value comparison.
    """
    assert f > 0 and e2 >= esvc > 0 and all(b > 0 for b in bb)
    assert len(aa) == len(bb) == len(caps) and sum(caps) > e2
    cross = f/(e2-esvc) if e2 > esvc else None
    breaks = {Q(0)} | {a for a in aa} | {a+b*c for a,b,c in zip(aa,bb,caps)}
    if cross is not None:
        breaks.add(cross)
    points = sorted(breaks)
    candidates = set(points)
    # Beyond the last breakpoint all caps bind and the objective decreases.
    for lo, hi in zip(points, points[1:]):
        p = (lo+hi)/2
        energy = e2 if cross is None or p < cross else esvc
        active = [(a,b) for a,b,c in zip(aa,bb,caps) if a < p < a+b*c]
        saturated = sum((c for a,b,c in zip(aa,bb,caps) if p >= a+b*c), Q(0))
        if active:
            stationary = (energy-saturated+sum((a/b for a,b in active),Q(0)))/sum((1/b for a,b in active),Q(0))
            if lo <= stationary <= hi:
                candidates.add(stationary)
    def value(p):
        return min(2*f+p*e2,3*f+p*esvc)-sum((conjugate(p,a,b,c) for a,b,c in zip(aa,bb,caps)),Q(0))
    p = max(sorted(candidates), key=value)
    loads = [min(c,max(Q(0),(p-a)/b)) for a,b,c in zip(aa,bb,caps)]
    return {'lower_exact':str(value(p)), 'lower_outward_2dp':old._lower_decimal(value(p),2),
            'test_price_exact':str(p), 'certificate_crossover_price_exact':str(cross),
            'two_bus_dual_margin_exact':str(f-p*(e2-esvc)),
            'capped_conjugate_loads_exact':list(map(str,loads)),
            'positive_caps_binding':[t for t,(x,c) in enumerate(zip(loads,caps)) if c>0 and x==c]}


def main():
    frozen, flow, _ = old._catalog(ROOT)
    source = ROOT/'research-20260928/computational-results/attempt1/scientific_evidence.zip'
    with zipfile.ZipFile(source) as z:
        screen = json.loads(z.read('frozen.json'))
    rows, sensitivity = [], []
    for i, case in enumerate(frozen['cases']):
        name = f'public_depot{15+i}'
        assert screen['cases'][name]['case'] == case
        identity = frozen['case_identities'][i]
        caps, first = hourly_caps(case)
        for state, market in enumerate(screen['cases'][name]['markets']):
            previous = old.evaluate(case, identity, market, repo=ROOT)
            e2, esvc = Q(previous['energy_floor_exact']), Q(previous['service_energy_exact'])
            aa, bb = list(map(Q,market['a'])), list(map(Q,market['b']))
            result = dual_bound(Q(100),e2,esvc,aa,bb,caps)
            assert Q(result['lower_exact']) >= Q(previous['ch_lower_exact'])
            rows.append({'case':name,'state':state,'case_identity':identity,
                         'market':market,'earliest_possible_charge_min_exact':str(first),
                         'hourly_grid_caps_exact':list(map(str,caps)),
                         'old_lower_exact':previous['ch_lower_exact'],
                         'improvement_exact':str(Q(result['lower_exact'])-Q(previous['ch_lower_exact'])),**result})
            for f in (20,40,100):
                for multiplier in (1,2):
                    bound = dual_bound(Q(f),e2,esvc,aa,[b*multiplier for b in bb],caps)
                    sensitivity.append({'case':name,'state':state,'bus_cost':f,
                                        'curvature_multiplier':multiplier,**bound})
    inputs = [source,ROOT/'src/egglab/analytic_energy_floor.py',ROOT/'src/egglab/native_recharge.py']
    output = {'scope':'exact ideal stored-input hull lower bounds; reporting only; no native solves',
              'lineage_sha256':{key:val[1] for key,val in old.PINNED.items()},
              'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'rows':rows,'analytical_sensitivity_only':sensitivity}
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__ == '__main__':
    main()
