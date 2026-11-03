"""Read-only, stdlib-only audit: no experiment/EGG imports or solver calls."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True, help='Checkout containing the frozen source files')
parser.add_argument('--run', type=Path, required=True, help='Frozen result directory, absolute or relative to --repo')
parser.add_argument('--report', type=Path, required=True, help='New audit JSON path; refuses to overwrite any existing file')
parser.add_argument('--cbc-library', type=Path, help='Optional historical CBC dylib to rehash; never loaded or executed')
args = parser.parse_args()
REPO = args.repo.resolve()
RUN = (args.run if args.run.is_absolute() else REPO / args.run).resolve()
REPORT = args.report.resolve()
if REPORT.exists():
    parser.error('--report already exists; choose a new output path')
EXPECTED_CBC_SHA256 = 'fe44771023b133390daf7b72790c2ce65d1ccb2e5ac77c7a04c8d8f8648aff7d'
if args.cbc_library is not None:
    assert hashlib.sha256(args.cbc_library.read_bytes()).hexdigest() == EXPECTED_CBC_SHA256
TOL = 2e-7

def close(a, b):
    assert abs(a-b) < TOL, (a, b)

def cost(a, load):
    return 10 + sum(ai*x + .1*x*x for ai,x in zip(a,load))

def audit_cell(d, previous):
    assert d['status'] == 'certified'
    arm, index = d['arm'], d['state_index']
    tilt = [0,0,.2,-.2][index]
    a = [.3,.3+tilt,.3-tilt,.3]
    for x,y in zip(a,d['market']['a']): close(x,y)
    assert d['market']['b'] == [.2]*4 and d['market']['U'] == [0.0]*4
    # Analytic minimizer of 10+a1*x+a2*(10-x)+.1*(x^2+(10-x)^2).
    xstar = (a[2]-a[1]+2)/.4
    truth = cost(a,[0,xstar,10-xstar,0])
    close(d['analytic']['objective'],truth)
    assert d['lower'] <= truth + TOL <= d['upper'] + 2*TOL
    columns = {c['column_key']: c for c in d['columns']}
    assert len(columns) == len(d['columns'])
    for c in d['columns']:
        assert c['sequences'] == [['t0','t1']] and c['arc_kinds'] == [['dep']]
        close(c['ops_cost'],10); assert c['fleet']==1
        load=[0.0]*4
        for event in c['charges']:
            assert event['vehicle']==0 and event['after_trip']=='t0' and event['before_trip']=='t1'
            assert event['slot'] in (1,2) and event['kwh'] >= 0
            load[event['slot']] += event['kwh']
        assert load[1] <= 10+TOL and load[2] <= 10+TOL
        assert 10-TOL <= sum(load) <= 15+TOL  # SOC after first trip is 5; battery cap is 20.
        for x,y in zip(load,c['load']): close(x,y)
        # The actual returned columns charge exactly 10; some clean dual prices are zero.
        close(sum(load),10)
    imported=d['imported_column_keys']
    if index>0 and arm!='cold':
        assert imported == [c['column_key'] for c in previous['columns']]
    else: assert imported==[]
    near=[]
    for e in d['oracle_events']:
        c=columns[e['column_key']]
        close(e['upper'],10+sum(q*x for q,x in zip(e['prices'],c['load'])))
        assert min(e['prices'][1:3])>=0
        exact_pricing=10+10*min(e['prices'][1:3])
        assert e['lower'] <= exact_pricing+TOL and exact_pricing <= e['upper']+TOL
        assert e['used_for_lower_bound'] == (e['purpose']=='clean')
        assert e['solver']['status']=='OPTIMAL' and e['solver']['backend']=='CBC'
        if e['purpose']=='analytic_proposal':
            for q,old,new_a,old_a in zip(e['prices'],previous['last_clean_price'],a,previous['market']['a']):
                close(q,old+new_a-old_a)
            nearest=min(max(abs(x-y) for x,y in zip(c['load'],columns[key]['load'])) for key in imported)
            near.append({'state':index,'exact_key_novel':e['novel'],'nearest_imported_load_linf_kwh':nearest})
    clean=[e for e in d['oracle_events'] if e['purpose']=='clean']
    assert len(clean)==len(d['master_events'])==len(d['iterations'])
    best=float('-inf')
    for e,m,it in zip(clean,d['master_events'],d['iterations']):
        for p,pi in zip(e['prices'],m['pi']): close(p,-pi)
        lambdas=m['lambdas']; assert min(lambdas)>=-TOL; close(sum(lambdas),1)
        selected=d['columns'][:len(lambdas)]
        load=[sum(l*c['load'][t] for l,c in zip(lambdas,selected)) for t in range(4)]
        for x,y in zip(load,m['L']): close(x,y)
        close(m['ub'],cost(a,load))
        # Solve this fixture's PWL RMP independently through all line breakpoints.
        # A convex mixture ranges over the interval between retained endpoint loads.
        lo=min(c['load'][1] for c in selected); hi=max(c['load'][1] for c in selected)
        lines=[]
        for slot in (1,2):
            points=[10*k/7 for k in range(8)]+[p[slot] for p in m['tangent_points']]
            raw=[(0.0,0.0)]+[(a[slot]+.2*x,-.1*x*x) for x in points]
            lines.append(raw if slot==1 else [(-s,10*s+c) for s,c in raw])
        candidates=[lo,hi]
        for group in lines:
            for (s1,c1),(s2,c2) in itertools.combinations(group,2):
                if abs(s1-s2)>1e-14:
                    x=(c2-c1)/(s1-s2)
                    if lo<=x<=hi: candidates.append(x)
        independent_model=min(10+sum(max(s*x+c for s,c in group) for group in lines) for x in candidates)
        close(m['z_model'],independent_model)
        close(m['ub']-m['z_model'],it['pwl_slack'])
        assert -TOL <= it['pwl_slack'] <= .001+TOL
        lower=m['z_model']+min(0,e['lower']-m['sigma'])
        best=max(best,lower)
        close(it['lower'],lower); close(it['lb_best'],best); close(it['gap'],m['ub']-best)
        close(it['reduced_lower'],e['lower']-m['sigma'])
        close(it['reduced_upper'],e['upper']-m['sigma'])
        assert best<=truth+TOL
    close(d['lower'],best); close(d['upper'],d['master_events'][-1]['ub'])
    close(d['gap'],d['upper']-d['lower']); assert -TOL <= d['gap'] <= .01+TOL
    for field,purpose in [('calls_clean','clean'),('calls_seed','cold_seed'),('calls_proposal','analytic_proposal')]:
        assert d[field]==sum(e['purpose']==purpose for e in d['oracle_events'])
    assert d['oracle_calls']==len(d['oracle_events'])<=24
    assert d['calls_proposal']==int(arm=='retained_shift' and index>0)
    assert d['calls_seed']==int(arm=='cold' or index==0)
    close(d['solver_wall_s'],sum(s['wall_s']+s['lp_wall_s'] for s in d['native_solves']))
    assert len(d['native_solves'])==len(d['oracle_events'])+sum(len(m['master_solves']) for m in d['master_events'])
    assert all(s['status']=='OPTIMAL' and s['backend']=='CBC' and s['extra']['threads']==1 for s in d['native_solves'])
    assert d['runtime']['versions']=={'mip':'1.17.6','cbcbox':'2.929','numpy':'2.5.3'}
    # Historical absolute paths are provenance, not locations to read on this checkout.
    lib=d['runtime']['selected_cbc_library']; assert lib['sha256']==EXPECTED_CBC_SHA256
    return near

summary=json.loads((RUN/'summary.json').read_text()); assert summary['complete'] is True
assert len(summary['states'])==12
previous={}; near=[]; totals={}; sources={}; cells={}
for row in summary['states']:
    assert row['arm'] in ('cold','retained','retained_shift') and row['state_index'] in range(4)
    cell_relative=Path(f"{row['arm']}-s{row['state_index']}")/'state.json'
    # Resolve the known cell layout under --run, never a stored machine-specific path.
    assert Path(row['result']).parts[-2:] == cell_relative.parts
    path=RUN/cell_relative; d=json.loads(path.read_text())
    assert d['arm']==row['arm'] and d['state_index']==row['state_index']
    assert (d['arm'],d['state_index']) not in cells
    cells[(d['arm'],d['state_index'])]=d
    sources[str(Path('result/reuse_qualification/20260921-attempt1')/cell_relative)]=hashlib.sha256(path.read_bytes()).hexdigest()
    near.extend(audit_cell(d,previous.get(d['arm'])))
    assert row['status']=='certified' and row['worker_exit']==0 and row['timed_out'] is False
    for key in ['lower','upper','gap','oracle_calls','calls_clean','calls_seed','calls_proposal','solver_wall_s','worker_cpu_s']: close(row[key],d[key])
    assert row['complete_wall_s'] >= d['worker_wall_s'] and row['complete_wall_s'] < 40
    previous[d['arm']]=d
    total=totals.setdefault(d['arm'],{'oracle_calls':0,'clean':0,'seed':0,'proposal':0,'complete_wall_s':0,'solver_wall_s':0})
    for outkey,key in [('oracle_calls','oracle_calls'),('clean','calls_clean'),('seed','calls_seed'),('proposal','calls_proposal'),('complete_wall_s','complete_wall_s'),('solver_wall_s','solver_wall_s')]: total[outkey]+=row[key]
provenance=json.loads((RUN/'provenance.json').read_text())
assert provenance['head']=='9c57b459e2f10a967f5ffc9e2a09fc5255de4f79'
for path,sha in provenance['source_sha256'].items(): assert hashlib.sha256((REPO/path).read_bytes()).hexdigest()==sha
# Deliberate output corruptions must fail the independent audit.
rejected=[]
for field in ['lower','upper','gap','calls_clean','ops_cost','proposal_price']:
    d=copy.deepcopy(cells[('retained_shift',2)])
    if field=='ops_cost': d['columns'][0]['ops_cost']+=1
    elif field=='proposal_price': d['oracle_events'][0]['prices'][1]+=1
    else: d[field]+=1
    try: audit_cell(d,cells[('retained_shift',1)])
    except AssertionError: rejected.append(field)
    else: raise AssertionError('Corrupted field escaped: '+field)
result={'status':'PASS','cells':12,'clean_certificates':sum(len(d['iterations']) for d in cells.values()),
        'native_solve_records':sum(len(d['native_solves']) for d in cells.values()),
        'arm_totals':totals,'proposal_physical_proximity':near,'corruptions_rejected':rejected,
        'source_commit':provenance['head'],'cell_sha256':sources,
        'native_library_verification': {
            'expected_sha256': EXPECTED_CBC_SHA256,
            'recorded_hash_matches_in_all_cells': True,
            'binary_rehashed': args.cbc_library is not None,
            'scope': 'actual bytes and historical recorded hashes' if args.cbc_library is not None else 'historical recorded hashes only; pass --cbc-library to rehash actual bytes'},
        'method':'stdlib-only independent physical replay, continuous oracle optimum, PWL line-intersection RMP optimum and clean lower-bound reconstruction; no author functions or native solves'}
with REPORT.open('x') as report:
    report.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
