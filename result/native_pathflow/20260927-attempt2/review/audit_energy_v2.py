#!/usr/bin/env python3
"""Read-only, solver-free audit of the failed twenty-control energy-V2 gate.

Example: python3 -B audit_energy_v2.py --repository /path/to/repo --out /tmp/new-report.json
Only a new output file outside any Git repository is allowed.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import independent_compact_core as compact
import independent_energy_band as energy

base=compact.base
need,near=base.need,base.near
HERE=Path(__file__).resolve().parent
COMMIT='66b7054510a8b90471d6abe07d32a9f7f509182d'
MANIFEST_SHA='dfd956c8da49d03bfec3db77a02396f8974ac4d6ba5ca3a95d713302fa33ebe3'
FAILED='joint_planner'
base.FAILURES={FAILED:'Positive charge on an unselected movement'}


def normalization(raw,norm):
    negatives={k:v for k,v in raw['raw_energy'].items() if v<0}
    amount=-sum(negatives.values(),Q())
    need(norm['policy']==compact.POLICY and norm['accepted'] is True and norm['budget_kwh']==1e-8,'failed normalization policy')
    need(Q(norm['negative_l1_exact'])==amount and norm['negative_l1_kwh']==float(amount),'failed normalization exact total')
    listed={tuple(r['key']):Q(r['before_kwh']) for r in norm['negative_to_zero']}
    need(len(listed)==len(norm['negative_to_zero']) and listed==negatives and all(r['after_kwh']==0 for r in norm['negative_to_zero']),'failed normalization exact entries')
    need(amount<=Q(1e-8),'failed normalization budget')
    return amount


def audit_cell(cell,blob):
    reduced=copy.deepcopy(blob)
    reduced['events']=[e for e in blob['events'] if e['event'] in ('native_start','native_status','replayed_iteration')]
    record=base.audit_cell(cell,reduced)
    by_round={}
    for e in blob['events']: by_round.setdefault(e['round'],[]).append(e)
    raw_records=[]
    for r,es in by_round.items():
        types=[e['event'] for e in es]
        need(types[:2]==['native_start','native_status'],'native evidence order')
        start,stats=es[0],es[1]['stats']
        need(stats['raw_incumbent_repr']==repr(stats['incumbent']) and stats['raw_lower_bound_repr']==repr(stats['lower_bound']), 'native numeric representations')
        c=cell['case']; grid=compact.intervals(c);N=len(c['trips']);M=len(c['movements']);T=len(c['market_edges_min'])-1
        Z=sum(len(g['visits']) for g in grid if g['rate_kw']>0)
        rows=4+3*N+Z+len(grid)+2*M+sum(2 if m['kind']=='depot' else 1 if m['kind']=='pullin' else 0 for m in c['movements'])+T
        epigraph=T if cell['objective']=='planner' else 0
        need(stats['physical_constraints']==rows and stats['n_vars']==M+2*N+Z+T+epigraph and stats['n_int']==M,'independent all-call dimensions including infeasible controls')
        need(stats['n_constraints']==rows+sum(len(t) for t in start.get('tangents',[])),'all-call tangent row count')
        if stats['status']=='INFEASIBLE':
            need(types==['native_start','native_status'],'infeasible trace has no incumbent');continue
        failed=(cell['id']==FAILED and r==1)
        expected=['native_start','native_status','native_incumbent','charge_normalization']
        if not failed:
            expected+=['serial_decoding','objective_reconstruction']
            if cell['objective']=='planner':expected+=['replayed_iteration']
        need(types==expected,'complete ordered evidence or exact failed prefix')
        raw=compact.raw_primal(cell,start,stats,es[2])
        common=dict(round=r,raw_variables=raw['variables'],raw_objective=raw['raw_objective'],
            max_raw_constraint_residual=raw['max_constraint_residual'],constraint_checks=raw['constraint_checks'],energy_band=raw['energy_band'])
        if failed:
            amount=normalization(raw,es[3]); modes=cell['case']['movements']
            orphans=[dict(key=list(k),movement=modes[k[0]]['id'],raw_grid_kwh=v,
                selection=raw['x'][k[0]],activation_violation=v-Q(raw['grid'][k[1]]['rate_kw']*raw['grid'][k[1]]['hours'])*raw['x'][k[0]])
                for k,v in raw['raw_energy'].items() if v>0 and raw['x'][k[0]]<=Q(1,2)]
            need(len(orphans)==1 and orphans[0]['key']==[1,1] and orphans[0]['movement']=='in_A','saved orphan identity')
            need(orphans[0]['selection']==0 and orphans[0]['raw_grid_kwh']==Q(1.2214110437041203e-12),'saved orphan exact magnitude')
            need(all(v in (0,1) for v in raw['x']),'failed round selections exactly integral')
            common.update(negative_l1=amount,negative_variables=len(es[3]['negative_to_zero']),positive_orphan=orphans,
                decoded=False,reason='Frozen policy preserves all positive energies; ownership rejection correctly prevents witness/certificate admission.')
        else:
            plan=es[-1]['plan'] if cell['objective']=='planner' else blob['result']['result']['plan']
            common.update(compact.conversion(cell,raw,es[3],es[4],es[5],plan,start,stats),decoded=True)
        raw_records.append(common)
    if cell['id']==FAILED:
        need(list(by_round)==[0,1] and len(record['physical_witnesses'])==1,'one saved prefix witness, two returned calls')
        need(blob['exception']['type']=='ValueError' and blob['exception']['cell']==FAILED,'failure exception ownership')
        need(record['certified_interval'] is None,'failed cell has no certified interval')
    record['raw_incumbent_audit']=raw_records
    return record


def corruptions(cells,blobs):
    # Reuse the established 25 scientific corruption families against V2.
    compact.audit_cell=audit_cell
    controls=compact.corruptions(cells,blobs)
    def reject(label,name,change):
        c,b=copy.deepcopy(cells[name]),copy.deepcopy(blobs[name]);change(c,b)
        try:audit_cell(c,b)
        except (AssertionError,KeyError,ValueError,TypeError,ZeroDivisionError) as exc:
            controls.append(dict(control=label,rejected=True,reason=str(exc)))
        else:raise AssertionError('corruption accepted: '+label)
    snap=lambda b:next(e for e in b['events'] if e['event']=='native_incumbent')
    reject('energy lower endpoint widened','single_linear',lambda c,b:snap(b)['energy_balance'].__setitem__('lower_rhs',0))
    reject('energy semantic coefficient changed','single_linear',lambda c,b:snap(b)['energy_balance']['modes'][0].__setitem__('energy_float',1))
    reject('energy stored rounding ledger forged','single_linear',lambda c,b:snap(b)['energy_balance']['modes'][0].__setitem__('normalized_plus_constant_float',1))
    reject('energy row indices misplaced','single_linear',lambda c,b:snap(b)['energy_balance']['constraint_indices'].__setitem__(0,0))
    reject('energy physical exact bound changed','single_linear',lambda c,b:snap(b)['energy_balance'].__setitem__('physical_lower_exact','0'))
    reject('V1 formulation relabelled as V2','single_linear',lambda c,b:snap(b).__setitem__('formulation','egg-native-pathflow-v1'))
    reject('failed cell relabelled pass',FAILED,lambda c,b:b['receipt'].__setitem__('pass',True))
    reject('failed native call omitted',FAILED,lambda c,b:b['receipt'].__setitem__('native_calls_returned',1))
    reject('failed raw snapshot omitted',FAILED,lambda c,b:b['events'].pop(-2))
    def remove_orphan(c,b):
        s=[e for e in b['events'] if e['event']=='native_incumbent'][-1]
        z=next(z for z in s['mapping']['grid_energy'] if z['key']==[1,1]);s['variables'][z['variable']]['solution']={'value':0.0,'repr':'0.0'}
    reject('positive orphan silently deleted',FAILED,remove_orphan)
    reject('failure reason changed',FAILED,lambda c,b:b['exception'].__setitem__('message','success'))
    reject('negative normalization amount changed in failed prefix',FAILED,lambda c,b:b['events'][-1].__setitem__('negative_l1_exact','1'))
    return controls


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None))
    ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen Git repository');repo=args.repository.resolve();attempt=args.attempt.resolve()
    out=args.out or Path(tempfile.gettempdir())/('egg-energy-v2-audit-'+uuid.uuid4().hex+'.json');resolved=out.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'output outside repositories')
    need(not out.exists() and not out.is_symlink(),'exclusively new output')
    started=time.perf_counter();manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'pinned original manifest')
    def preservation():
        for p,item in manifest['files'].items():
            data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'raw manifest '+p)
        need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'original manifest preserved')
    preservation()
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete raw evidence manifest')
    frozen=base.read(attempt/'frozen.json')
    need(frozen['freeze_label']==COMMIT and frozen['protocol']=='native-pathflow-qualification-20260927-v2-energy-band','prospective frozen identity')
    need(frozen['formulation']=='egg-native-pathflow-v2-energy-band','frozen V2 identity')
    for p,sha in frozen['source_hashes'].items():need(base.digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen Git source '+p)
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==list(base.TARGETS),'complete prospective input grid')
    old=base.read(repo/'result/native_pathflow/20260927-attempt1/frozen.json')
    need(frozen['controls']==old['controls'] and frozen['budget']==old['budget'],'all twenty definitions and budgets unchanged')
    need(all(energy.profile(c['case'])['union_lower_exact']==energy.profile(c['case'])['union_upper_exact'] for c in cells.values()),'all synthetic energy bands exact zero width')
    summary=base.read(attempt/'summary.json')
    need(summary['all_pass'] is False and summary['source_hashes_unchanged'] is True,'failed gate and stable source preserved')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json')
        need({k:inp[k] for k in cells[name]}==cells[name] and inp['budget']==frozen['budget'],'immutable input and budget')
        need(inp['source_hashes']==frozen['source_hashes'] and receipt==base.read(folder/'receipt.json'),'input/receipt provenance')
        launch=base.read(folder/'launch.json');need(launch['hard_timeout_s']==60 and launch['command'][1:5]==['-m','experiments.native_pathflow_qualification','--worker',name],'worker launch identity/cap')
        blob={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()],'receipt':receipt}
        if (folder/'result.json').exists():blob['result']=base.read(folder/'result.json')
        if (folder/'exception.json').exists():blob['exception']=base.read(folder/'exception.json')
        need((name==FAILED)==('exception' in blob) and (name!=FAILED)==('result' in blob),'exact failed/success artifact accounting')
        blobs[name]=blob
    need(list(blobs)==list(cells),'all twenty cells attempted in order')
    records=[audit_cell(c,blobs[n]) for n,c in cells.items()];controls=corruptions(cells,blobs)
    rounds=[r for c in records for r in c['raw_incumbent_audit']];decoded=[r for r in rounds if r['decoded']]
    witnesses=[w for c in records for w in c['physical_witnesses']]
    statuses=Counter(s['native_status'] for c in records for s in c['native_rounds'])
    widths=[c['certified_interval'][1]-c['certified_interval'][0] for c in records if c['certified_interval']]
    report=dict(audit_status='PARTIAL / FAIL qualification gate: 19 of 20 passed; joint_planner extraction exception independently confirmed',
        downstream_admission=False,frozen_commit=COMMIT,original_manifest_sha256=MANIFEST_SHA,
        counts=dict(raw_files=len(manifest['files']),raw_bytes=sum(x['bytes'] for x in manifest['files'].values()),controls=20,passed_controls=19,
            certified_controls=len(widths),expected_infeasibilities=statuses['INFEASIBLE'],failed_controls=1,native_calls=sum(statuses.values()),
            raw_incumbents=len(rounds),raw_variable_values=sum(r['raw_variables'] for r in rounds),decoded_incumbents=len(decoded),
            physical_witness_instances=len(witnesses),sessions=sum(w['sessions'] for w in witnesses),SOC_events=sum(w['soc_events'] for w in witnesses),
            corrected_negative_variables=sum(r['negative_variables'] for r in rounds),nonzero_correction_incumbents=sum(r['combined_correction']>0 for r in decoded)),
        native_status_counts=dict(statuses),certified_width_min_max=[min(widths),max(widths)],
        max_raw_constraint_residual=max(r['max_raw_constraint_residual'] for r in rounds),
        max_energy_row_residual=max(v for r in rounds for v in r['energy_band']['row_residuals']),
        total_negative_charge_correction=sum((r['negative_l1'] for r in rounds),Q()),
        max_combined_correction=max(r['combined_correction'] for r in decoded),
        max_SOC_residual_kwh=max(w['worst_soc_residual_kwh'] for w in witnesses),
        cells=records,corruption_controls=controls,
        reviewer_scope='No author imports or native optimizer. Independently reconstructs stored inputs, every compact physical row, energy band profiles, raw objectives, exact fixture-specific global PWL/true optima, retained positive energies, normalization/session ledgers and event SOC. The incomplete failed round has no admitted physical witness. Original independent fixture core is preserved verbatim; independent compact core extended only for the V2 identity/two energy rows. Reviewer contributed to analytical energy-band discussion, not scientific implementation.',
        qualifications='Finite numerical witnesses under the frozen tolerances and 1e-8-kWh correction policy, not exact repaired feasibility or arbitrary native lower-bound verification. Native bounds in these finite analytical fixtures are independently checked; no broader operational claim. A prefix feasible witness does not convert the failed planner cell into a certified result.',
        source_scripts={p.name:base.digest(p.read_bytes()) for p in HERE.glob('*.py')},audit_wall_s=time.perf_counter()-started)
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    preservation()
    print(json.dumps({'audit_status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'corruptions':len(controls)},indent=2))


if __name__=='__main__':main()
