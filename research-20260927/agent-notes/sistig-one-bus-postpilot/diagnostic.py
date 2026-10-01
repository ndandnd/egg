#!/usr/bin/env python3
"""Post-pilot chronological no-recharge obstruction; no author/native imports.

Uses exact rational arithmetic on the already frozen full input. This is a new
post-result proof check, not an amendment to the original optimization receipts.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

FROZEN_SHA='35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b'
SOURCE='282e00b80b6fd9457006429b089269b2a9e2be92'
ROOT=Path(__file__).resolve().parents[3]

def need(value,message):
    if not value:raise AssertionError(message)
def energy(mode):return sum((Q(l['energy_kwh']) for l in mode['legs']),Q(0))
def record(q):return {'exact_stored_number':str(q),'value':float(q)}

def analyze(case):
    trips=sorted(case['trips'],key=lambda t:(t['start_min'],t['end_min'],t['id']))
    need(len({t['id'] for t in trips})==len(trips),'unique mandatory services')
    need(all(t['start_min']<t['end_min'] for t in trips),'positive service duration')
    need(all(a['end_min']<=b['start_min'] for a,b in zip(trips,trips[1:])),'strict chronological one-bus order')
    lookup={t['id']:t for t in trips};edges=[]
    for m in case['movements']:
        need(all(Q(l['energy_kwh'])>=0 for l in m['legs']),'nonnegative represented consumption')
        if m['before'] is not None and m['after'] is not None:
            a,b=lookup[m['before']],lookup[m['after']]
            need(a['end_min']<=m['legs'][0]['depart_min'] and m['legs'][-1]['arrive_min']<=b['start_min'],'source movement respects service DAG')
    for a,b in zip(trips,trips[1:]):
        modes=[m for m in case['movements'] if m['before']==a['id'] and m['after']==b['id']]
        need(modes,'at least one chronological consecutive mode')
        opportunities=[];candidates=[]
        for m in modes:
            candidate={'id':m['id'],'kind':m['kind'],'energy':record(energy(m)),
                'legs':[{k:l[k] for k in ('origin','destination','depart_min','arrive_min','energy_kwh')} for l in m['legs']]}
            if m['kind']=='depot':
                split=m['depot_split'];lo=Q(m['legs'][split-1]['arrive_min']);hi=Q(m['legs'][split]['depart_min'])
                candidate['depot_window']=[str(lo),str(hi)]
                cap=sum((max(Q(0),min(hi,Q(r['end_min']))-max(lo,Q(r['start_min'])))*Q(min(r['per_bus_kw'],r['grid_kw']))/60
                    for r in case['resources'] if r['connectors']>0),Q(0))
                candidate['grid_capacity']=record(cap)
                if cap>0:opportunities.append(m['id'])
            else:need(m['kind']=='direct','consecutive mode has direct/depot semantics')
            candidates.append(candidate)
        edges.append({'before':a['id'],'after':b['id'],'gap_min':record(Q(b['start_min'])-Q(a['end_min'])),
            'candidates':candidates,'charge_capable_modes':opportunities,'minimum_battery_energy':record(min(energy(m) for m in modes))})
    # This deliberately simple proof is applicable only when every forced
    # adjacent transition has no positive declared recharge opportunity.
    none=all(not e['charge_capable_modes'] for e in edges)
    service=sum((Q(t['energy_kwh']) for t in trips),Q(0))
    movement=sum((Q(e['minimum_battery_energy']['exact_stored_number']) for e in edges),Q(0))
    inventory=Q(case['battery_kwh'])-Q(case['reserve_kwh'])
    proven=none and service+movement>inventory
    prefix=Q(0);first_overflow=None
    for i,t in enumerate(trips):
        if i:prefix+=Q(edges[i-1]['minimum_battery_energy']['exact_stored_number'])
        prefix+=Q(t['energy_kwh'])
        if first_overflow is None and prefix>inventory:
            first_overflow={'service_count':i+1,'through_trip':t['id'],'through_end_min':t['end_min'],'energy_lower':record(prefix)}
    return {'chronological_service_ids':[t['id'] for t in trips],'first_start_min':trips[0]['start_min'],'last_end_min':trips[-1]['end_min'],
        'service_count':len(trips),'forced_adjacent_transitions':edges,'no_recharge_on_every_forced_transition':none,
        'available_battery_above_reserve':record(inventory),'mandatory_service_energy':record(service),
        'consecutive_movement_energy_lower':record(movement),'route_segment_energy_lower':record(service+movement),
        'battery_excess_lower':record(service+movement-inventory),'first_prefix_above_inventory':first_overflow,
        'one_bus_infeasible_proved':proven,'minimum_used_buses_lower':2 if proven else None,
        'scope':'Declared complete one-depot movement graph only; no route/matching/native optimizer; full37 services retained'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',type=Path,default=ROOT/'result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json')
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    data=args.frozen.read_bytes();need(hashlib.sha256(data).hexdigest()==FROZEN_SHA,'exact first-pilot full frozen input')
    f=json.loads(data);need(f['freeze_label']==SOURCE,'original source freeze')
    need(not args.out.exists(),'exclusive post-pilot diagnostic output')
    results=[]
    for c in f['controls']:
        case=c['case'];identity=hashlib.sha256(json.dumps({'schema':'egg-native-recharge-v1','case':case},sort_keys=True,allow_nan=False).encode()).hexdigest()
        need(identity==c['case_identity'] and len(case['trips'])==37,'full original physical case')
        result=analyze(case);result.update(cell=c['id'],case_identity=identity)
        need(result['one_bus_infeasible_proved'],'prospective obstruction form actually holds')
        # Countercheck: the same fixed obstruction must disappear if inventory
        # is larger than its consumption. This checks the implication direction.
        altered={**case,'battery_kwh':2000}
        need(not analyze(altered)['one_bus_infeasible_proved'],'larger-capacity countercheck')
        results.append(result)
    output={'classification':'Separately dated post-pilot exact no-recharge capacity proof; original native bounds unchanged',
        'source_commit':SOURCE,'frozen_input_sha256':FROZEN_SHA,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'optimizer_imported':False,'matching_called':False,'cases':results,'counterchecks_passed':2}
    with args.out.open('x') as stream:json.dump(output,stream,indent=2,sort_keys=True);stream.write('\n')
    need(hashlib.sha256(args.frozen.read_bytes()).hexdigest()==FROZEN_SHA,'raw input preserved')
    print(json.dumps({'out':str(args.out),'cases':[{'cell':r['cell'],'proved':r['one_bus_infeasible_proved'],'energy_lower_kwh':r['route_segment_energy_lower']['value'],'first_prefix':r['first_prefix_above_inventory']} for r in results]},indent=2))

if __name__=='__main__':main()
