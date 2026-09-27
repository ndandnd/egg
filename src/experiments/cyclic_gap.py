"""Exact, fully replenished fleet-gap construction; see frozen protocol."""
from fractions import Fraction as Q
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import time


def clip(x):
    return max(Q(0), min(Q(10), x))


def charging_cost(x, a):
    return a*x + (x*x+(30-x)*(30-x))/10


def schedule(n, x):
    x = Q(x)
    if n == 1:
        if x != 10:
            raise ValueError('one bus requires exactly 10 early kWh')
        chains = [{'services': ['A','B'], 'early': x, 'terminal': Q(20)}]
    elif n == 2 and 0 <= x <= 10:
        chains = [{'services': ['A'], 'early': x, 'terminal': 15-x},
                  {'services': ['B'], 'early': Q(0), 'terminal': Q(15)}]
    else:
        raise ValueError('invalid structure or early charge')
    for bus in chains:
        soc = Q(20)
        states = [soc]
        if 'A' in bus['services']:
            soc -= 15
        states.append(soc)
        soc += bus['early']
        states.append(soc)
        if 'B' in bus['services']:
            soc -= 15
        states.append(soc)
        soc += bus['terminal']
        states.append(soc)
        if not all(0 <= v <= 20 for v in states) or soc != 20:
            raise ValueError('SOC replay failed')
        if not 0 <= bus['early'] <= 10 or not 0 <= bus['terminal'] <= 30:
            raise ValueError('individual charging power exceeded')
        bus['soc_after_events'] = states
    load = [sum(b['early'] for b in chains), sum(b['terminal'] for b in chains)]
    if load[0] > 10 or load[1] > 30 or sum(load) != 30:
        raise ValueError('shared power or energy balance failed')
    return {'buses': chains, 'load': load, 'total_recharge': sum(load),
            'initial_energy': Q(20*n), 'terminal_energy': Q(20*n)}


def exact_case(f, a):
    f, a = Q(f), Q(a)
    x_two = clip(15-Q(5,2)*a)
    x_hull = clip(15-Q(5,2)*a+f/4)
    one = f+charging_cost(Q(10),a)
    two = 2*f+charging_cost(x_two,a)
    lam = x_hull/10
    hull = 2*f-f*x_hull/10+charging_cost(x_hull,a)
    physical = min(one,two)
    if physical < hull:
        raise ValueError('negative exact convexification gap')
    return {'fleet_cost':f,'early_intercept':a,
            'physical_one':one,'physical_two':two,'physical':physical,
            'convexified':hull,'gap':physical-hull,'one_bus_weight':lam,
            'hull_load':[x_hull,30-x_hull], 'two_bus_optimal_early':x_two,
            'physical_witnesses':[schedule(1,10),schedule(2,x_two)],
            'hull_components':[{'weight':lam,'schedule':schedule(1,10)},
                               {'weight':1-lam,'schedule':schedule(2,0)}]}


def price_diagnostics(case):
    f,a=case['fleet_cost'],case['early_intercept']
    x=case['hull_load'][0]
    p=[a+x/5,(30-x)/5]
    vertices=[(1,Q(10)),(2,Q(0)),(2,Q(10))]
    def response(price):
        return min(n*f+price[0]*early+price[1]*(30-early) for n,early in vertices)
    vp=response(p)
    conjugate=sum(max(Q(0),v-base)**2/Q(2,5) for v,base in zip(p,[a,Q(0)]))
    rows=[]
    for n,early in [(1,Q(10)),(2,case['two_bus_optimal_early'])]:
        load=[early,30-early]
        own=[a+early/5,(30-early)/5]
        bill=sum(pi*li for pi,li in zip(p,load))
        rows.append({'buses':n,'load':load,
                     'own_price':own,
                     'own_price_regret':n*f+sum(pi*li for pi,li in zip(own,load))-response(own),
                     'fleet_LOC_at_hull_price':n*f+bill-vp,
                     'supply_LOC_at_hull_price':charging_cost(early,a)-bill+conjugate})
    return {'hull_price':p,'fleet_response_value':vp,'supply_conjugate':conjugate,
            'dual_value':vp-conjugate,'physical_branch_optima':rows}


def encode(value):
    if isinstance(value,Q):
        return {'exact':str(value),'value':float(value)}
    if isinstance(value,dict):
        return {k:encode(v) for k,v in value.items()}
    if isinstance(value,list):
        return [encode(v) for v in value]
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    root=Path(__file__).resolve().parents[2]
    protocol=root/'doc/CYCLIC_GAP_PROTOCOL_20260927.md'
    cases=[exact_case(f,a) for f in (1,3,7,10,15,20) for a in (0,2,4,6)]
    nominal=next(c for c in cases if c['fleet_cost']==7 and c['early_intercept']==4)
    result={'cases':cases,'nominal':nominal,'nominal_prices':price_diagnostics(nominal),
            'head':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
            'arithmetic':'exact rational; synthetic complete four-period model',
            'wall_s':time.perf_counter()-started}
    (args.output/'results.json').write_text(json.dumps(encode(result),indent=2,sort_keys=True)+'\n')
    print(json.dumps(encode({'cases':len(cases),'nominal_D':nominal['physical'],
                            'nominal_CH':nominal['convexified'],'nominal_gap':nominal['gap']})))


if __name__=='__main__':
    main()
