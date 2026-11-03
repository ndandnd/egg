#!/usr/bin/env python3
"""Independent solver-free reconstruction of V3 compact native-hull attempt 2.

Only Python standard library and colocated independent audit helpers are used.
No author module is imported; no native model or optimizer is instantiated.
"""
import argparse,copy,hashlib,itertools,json,math,re,subprocess,tempfile,time,uuid,csv
from fractions import Fraction as Q
from pathlib import Path
import independent_hull_core as h
import independent_compact_core as compact
import independent_projection_audit as projection
base=compact.base
need,near=base.need,base.near
HERE=Path(__file__).resolve().parent
COMMIT='62976f11ecf35c837b0573079892ae5095e846b9'
MANIFEST_SHA='a8e1a883f03c5f8e1d6a710ec70500836f950404b3158331a2ffe668c753acf4'
ATTEMPT_REL=Path('result/native_pathflow_hull_grb/20260927-attempt1')
CBC_V3_FROZEN_SHA='d8bea15e39d1bf0b69f7c7623b401788d8c842bc8e490ce27d6ac00438dfe175'
PHYSICAL_ADMISSION_SHA='ccbd76102a1efafff53da5cff71a6fbebf7290231047cf57eb0cc20306a49248'
ORACLE='egg-native-pathflow-v3-energy-band-orphan-projection'
FORMULATION=ORACLE
NATIVE_MATRIX='egg-native-pathflow-v2-energy-band'
POLICY='native-pathflow-orphan-projection-v1'
SHARED_POLICY='native-roundoff-qualification-v2'
NAMES=['nominal_cold_s0','nominal_cold_s1','nominal_cold_s2','nominal_retained_s0','nominal_retained_s1','nominal_retained_s2','joint_cold','fixed_reserve_cold']
RUNTIME_ROWS=[]

# Reuse only the independent mathematical helpers. They consume archived JSON
# and standard-library exact arithmetic; no project implementation is loaded.
h.base=base
h.need,h.near=need,near
h.native=compact
h.POLICY=POLICY
h.ORACLE=ORACLE
pair_min=h.exact_pair_min

def backend_grb(stats,master=False):
    rt=stats['backend_runtime'];name=str(rt.get('model_solver_name','')).upper()
    normalized='GRB' if name=='GUROBI' else name
    need(stats.get('backend')=='GRB' and stats.get('threads')==1
         and 0<float(stats.get('seconds_cap',0))<=180,
         'explicit one-thread GRB phase budget within 180 seconds')
    need(rt.get('requested')=='GRB' and normalized=='GRB'
         and rt.get('solver_module')=='mip.gurobi'
         and 'gurobi' in str(rt.get('solver_class','')).lower(),
         'actual GRB runtime identity; no CBC fallback')
    need(isinstance(rt.get('native_library_sha256'),str)
         and re.fullmatch(r'[0-9a-f]{64}',rt['native_library_sha256'])
         and isinstance(rt.get('native_library_path'),str) and rt['native_library_path'],
         'reported GRB native-library fingerprint/path')
    need(stats.get('status') in ('OPTIMAL','FEASIBLE') and math.isfinite(float(stats.get('wall_s')))
         and 0<=stats['wall_s']<=stats['seconds_cap']+1e-6,
         'observed optimal native return within recorded phase cap')
    if master:need(stats['n_int']==0,'pure LP master')
    RUNTIME_ROWS.append(rt)

h.backend=backend_grb

def dot(a,b):return sum((x*y for x,y in zip(a,b)),Q(0))
def bits(xs):return max((max(x.numerator.bit_length(),x.denominator.bit_length()) for x in xs),default=0)

def linear_solve(A,b):
    n=len(b);v=[list(map(Q,row))+[Q(x)] for row,x in zip(A,b)]
    for j in range(n):
        k=next((k for k in range(j,n) if v[k][j]),None)
        if k is None:return None
        v[j],v[k]=v[k],v[j];d=v[j][j];v[j]=[x/d for x in v[j]]
        for k in range(n):
            if k!=j:
                d=v[k][j];v[k]=[x-d*y for x,y in zip(v[k],v[j])]
    return [row[-1] for row in v]

def pool_min(cell,columns,rows=None):
    if len(columns)!=3:return pair_min(cell,columns,rows)
    # Exact three-column reference. Eliminate lambda_2; never assume the raw
    # projected loads lie on an ideal collinear total-energy line.
    m=cell['market'];last=columns[2]
    ds=[[Q(a)-Q(b) for a,b in zip(c['load'],last['load'])] for c in columns[:2]]
    cs=[Q(c['ops_cost'])-Q(last['ops_cost']) for c in columns[:2]]
    if rows is None:
        best=pair_min(cell,columns)[0]
        grad=[Q(a)+Q(b)*Q(x) for a,b,x in zip(m['a'],m['b'],last['load'])]
        g=[cs[i]+dot(grad,ds[i]) for i in range(2)]
        H=[[sum((Q(b)*ds[i][t]*ds[j][t] for t,b in enumerate(m['b'])),Q(0)) for j in range(2)] for i in range(2)]
        w=linear_solve(H,[-v for v in g])
        if w is not None and min(w)>=0 and sum(w)<=1:
            load=[Q(x)+sum((w[i]*ds[i][t] for i in range(2)),Q(0)) for t,x in enumerate(last['load'])]
            best=min(best,Q(last['ops_cost'])+dot(w,cs)+h.supply(m,load))
        return (best,)
    active=[1,3]
    need(all(not Q(r['slope']) and not Q(r['intercept']) for t,rr in enumerate(rows) if t not in active for r in rr),'other epigraphs exactly zero in these fixtures')
    # v=(lambda0,lambda1,z_early,z_late); each A.v<=b.
    inequalities=[([-Q(1),Q(0),Q(0),Q(0)],Q(0)),([Q(0),-Q(1),Q(0),Q(0)],Q(0)),([Q(1),Q(1),Q(0),Q(0)],Q(1))]
    for k,t in enumerate(active):
        for row in rows[t]:
            slope=Q(row['slope']);a=[slope*ds[0][t],slope*ds[1][t],Q(0),Q(0)];a[2+k]=-Q(1)
            inequalities.append((a,-slope*Q(last['load'][t])-Q(row['intercept'])))
    candidates=[]
    for eq in itertools.combinations(inequalities,4):
        v=linear_solve([r[0] for r in eq],[r[1] for r in eq])
        if v is not None and all(dot(a,v)<=b for a,b in inequalities):
            candidates.append(Q(last['ops_cost'])+dot(cs,v[:2])+sum(v[2:],Q(0)))
    need(candidates,'exact bounded LP has feasible vertex')
    return (min(candidates),)
# check_master calls this independently derived extension; complete_hull has
# four ideal branch endpoints and continues using its proved pair reduction.
h.master_min=pool_min

def check_master_public(cell,columns,start,status,snapshot,replay):
    """Reconstruct LP primal feasibility/objective, without claiming LP optimality."""
    need(1<=len(columns)<=48,'master column pool within frozen cap')
    stats=status['stats'];backend_grb(stats,True);h.check_tangents(cell,columns,start)
    records=snapshot['variables'];mapping=snapshot['mapping'];n=len(columns);T=len(cell['market']['a'])
    need([r['index'] for r in records]==list(range(n+2*T)) and len(records)==stats['n_vars'],
         'all raw master variables')
    need(mapping=={'lambda':list(range(n)),'load':list(range(n,n+T)),
                   'epigraph':list(range(n+T,n+2*T))},'raw master semantic mapping')
    need(stats['master_base_constraints']==T+1
         and stats['n_constraints']==T+1+sum(map(len,start['tangent_rows'])),
         'exact master constraint counts')
    values=[compact.value_record(r['solution']) for r in records]
    need(all(v is not None for v in values),'finite raw master primal')
    residuals=[]
    def le(a,b):residuals.append(max(Q(0),a-b))
    for k,r in enumerate(records):
        need(r['type']=='C','continuous master variable')
        lo,hi=compact.value_record(r['lower']),compact.value_record(r['upper'])
        if k<n:need(lo==0 and hi==1,'simplex declared bounds')
        elif k<n+T:need(lo==0 and hi==max(Q(c['load'][k-n]) for c in columns),
                         'current pool load box')
        else:need(lo<-Q(10)**100 and hi>Q(10)**100,'free-below epigraph')
        le(lo,values[k]);le(values[k],hi)
    weights,loads,epi=values[:n],values[n:n+T],values[n+T:]
    mass=sum(weights,Q(0));le(mass,1);le(1,mass)
    for t,x in enumerate(loads):
        target=sum((w*Q(c['load'][t]) for w,c in zip(weights,columns)),Q(0))
        le(x,target);le(target,x)
        for row in start['tangent_rows'][t]:le(Q(row['slope'])*x+Q(row['intercept']),epi[t])
    need(max(residuals,default=Q(0))<=Q(1e-6),'raw LP primal reconstruction residual')
    raw_objective=(sum((w*Q(c['ops_cost']) for w,c in zip(weights,columns)),Q(0))
                   +sum(epi,Q(0)))
    near(float(raw_objective),stats['incumbent'],'raw master objective',1e-6)
    need(math.isfinite(float(stats['lower_bound']))
         and stats['lower_bound']<=stats['incumbent']+1e-6,
         'solver-conditioned master bound below incumbent')
    need(replay['raw_tangent_objective']==stats['incumbent']
         and replay['mixture']['simplex']['raw']==list(map(float,weights)),
         'master raw-to-mixture provenance')
    mix=mixture(cell,columns,replay['mixture'])
    gap=h.pool_bound(cell,columns,mix,replay['pool'])
    return {'call':start['call'],'objective':mix['objective'],'load':mix['load'],
            'weights':mix['weights'],'pool_gap':gap,'pool_true_optimum':None,
            'true_pool_suboptimality':None,'solver_conditioned_lower':Q(stats['lower_bound']),
            'raw_LP_residual':max(residuals,default=Q(0)),'raw_variables':len(records),
            'tangent_points':len(start['tangent_points']),
            'unique_tangent_points':len(set(tuple(p) for p in start['tangent_points'])),
            'positive_weights':sum(w>0 for w in mix['weights'])}

h.check_master=check_master_public

def check_column(cell,column):
    need(column['schema']==h.SCHEMA and column['physical_identity']==cell['physical_identity']
         and column['extraction_policy']==POLICY,'V3 column physical/policy identity')
    need(column['source']['pricing_oracle']==ORACLE
         and column['plan']['formulation']==FORMULATION
         and column['plan']['native_matrix']==NATIVE_MATRIX
         and column['plan']['extraction_policy']==POLICY,'V3 column source/plan provenance')
    need(column['witness_hash']==h.digest_object(column['plan']),'immutable whole-fleet witness hash')
    witness=base.physical(h.native_cell(cell,[0]*len(cell['market']['a'])),column['plan'])
    need(column['ops_cost']==column['plan']['ops_cost'],
         'column intrinsic cost equals saved physical plan')
    for a,b in zip(column['load'],column['plan']['load']):
        near(a,b,'column load versus saved physical plan',1e-9)
    need(column['ops_cost']==witness['ops'],'independently replayed column intrinsic cost')
    for a,b in zip(column['load'],witness['load']):
        near(a,b,'independently replayed column load',1e-9)
    need(column['key']==h.projection_key(column['load'],column['ops_cost']),
         'exact projection key including intrinsic cost')
    return witness

def audit_pricing(cell,request,events,result_event,bound_event):
    prices=request['prices'];nc=h.native_cell(cell,prices)
    types=[e['event'] for e in events]
    expected=['native_start','native_status','native_incumbent','charge_normalization',
              'charge_projection','charge_projection','serial_decoding',
              'charge_projection','charge_projection','objective_reconstruction']
    need(types==expected,'complete V3 pricing/projection/decode evidence order')
    need(all(e['round']==events[0]['round'] for e in events),'one native phase per price request')
    start,stats,snapshot=events[0],events[1]['stats'],events[2]
    h.backend(stats)
    answer=result_event['result'];plan=answer['plan']
    need(answer['formulation']==FORMULATION and answer['native_matrix']==NATIVE_MATRIX
         and answer['extraction_policy']==POLICY,'V3 pricing result identity')
    need(plan['formulation']==FORMULATION and plan['native_matrix']==NATIVE_MATRIX
         and plan['extraction_policy']==POLICY,'V3 physical plan identity')
    need(answer['status'] in ('certified','bounded') and answer['case_identity']==cell['physical_identity']
         and answer['prices']==prices and answer['stats']==stats,'native price identity/status')
    raw=compact.raw_primal(nc,start,stats,snapshot)
    raw['case']=cell['case']
    norm=events[3];decoded=events[6];obj=events[9]
    exp=projection.projection_records(raw,snapshot,nc,norm)
    exp['grid']=raw['grid'];exp['cell']=nc
    need(snapshot['native_matrix']==NATIVE_MATRIX and snapshot['formulation']==FORMULATION
         and snapshot['extraction_policy']==POLICY
         and snapshot['shared_negative_normalizer_policy']==SHARED_POLICY,
         'raw snapshot matrix/formulation/extraction identity')
    projections=[e for e in events if e['event']=='charge_projection']
    before,predecode,prereplay,final=projections
    H=[projection.qfloat(v) for v in plan['load']]
    T=[projection.qfloat(v) for v in plan['replay']['load']]
    projection.verify_projection_stage(before,exp,'before_budget')
    plan_l1=projection.verify_projection_stage(predecode,exp,'before_decoding',H)
    I,J=projection.verify_decoder(raw,exp,decoded,plan)
    projection.verify_projection_stage(prereplay,exp,'before_replay',H,I=I,J=J)
    projection.verify_projection_stage(final,exp,'final',H,I=I,J=J,T=T)
    witness=base.physical(nc,plan)
    objective=projection.objective_check(nc,raw,start,stats,plan,obj)
    need(plan['vehicles']==raw['paths'],'raw selected graph to physical path mapping')
    need(plan['roundoff']['projection']=={k:v for k,v in final.items()
         if k not in ('event','round','stage')},'plan/final complete correction-ledger equality')
    need(plan['roundoff']['negative_correction']=={k:v for k,v in norm.items()
         if k not in ('event','round')},'plan negative-normalization ledger equality')
    need(plan['roundoff']['serial_decoding']=={k:v for k,v in decoded.items()
         if k not in ('event','round','charges')},'plan decoder-ledger equality')
    for t,(hload,projected,native_load,replay_load) in enumerate(zip(H,exp['P'],exp['L'],T)):
        raw_charge=Q(plan['raw_charge_load'][t])
        near(float(raw_charge),float(exp['R'][t]),'saved signed raw charge sum',1e-12)
        near(plan['roundoff']['load_delta_kwh'][t],float(hload-raw_charge),
             'materialized/raw-charge load ledger',1e-12)
        near(plan['roundoff']['native_load_delta_kwh'][t],float(replay_load-native_load),
             'replayed/native load ledger',1e-12)
    witness_objective=Q(witness['ops'])+sum((Q(p)*Q(load) for p,load in zip(prices,witness['load'])),Q(0))
    physical_objective=objective['physical_objective']
    near(float(witness_objective),float(physical_objective),
         'independent physical plan/replay pricing objective',1e-9)
    near(stats['incumbent'],float(physical_objective),'native pricing incumbent versus replay',1e-6)
    need(math.isfinite(float(stats['lower_bound']))
         and stats['lower_bound']<=stats['incumbent']+1e-6,
         'finite solver-conditioned global MIP bound below incumbent')
    need(answer['objective']=='complete-fleet-linear',
         'saved pricing objective mode matches declared linear oracle')
    near(answer['lower'],stats['lower_bound']-1e-6,'single native lower guard',1e-12)
    near(answer['upper'],float(physical_objective)+1e-6,'replayed upper guard',1e-12)
    near(answer['gap'],answer['upper']-answer['lower'],'saved pricing gap arithmetic',1e-12)
    # The raw GRB lower bound is solver-conditioned. We independently verify
    # its recorded runtime, raw matrix/primal, bound ordering, replayed upper,
    # and the downstream Fenchel arithmetic, but make no exact 37-service
    # combinatorial-optimum claim.
    column=bound_event['column']
    need(column['plan']==plan and column['source']=={
         'state_identity':cell['state_identity'],'pricing_call':request['call'],'pricing_oracle':ORACLE},
         'column provenance from native pricing call')
    checked=check_column(cell,column)
    need(checked['ops']==witness['ops'] and len(checked['load'])==len(witness['load']),
         'pricing and saved column physical replay dimensions/cost')
    for a,b in zip(checked['load'],witness['load']):
        near(a,b,'pricing and saved column physical replay loads',1e-9)
    lower=h.global_bound(cell,prices,answer['lower'],bound_event['certificate'])
    return {'call':request['call'],'seed':request['seed'],'prices':prices,
            'complete_price_minimum':None,'native_incumbent':stats['incumbent'],
            'native_lower':stats['lower_bound'],'fenchel_lower':lower,
            'raw_variables':raw['variables'],'max_raw_constraint_residual':raw['max_constraint_residual'],
            'energy_band':raw['energy_band'],'projection':{
                'negative_l1':exp['N'],'orphan_positive_l1':exp['O'],
                'raw_to_projected_l1':exp['raw_to_projected'],'raw_row_l1':exp['raw_row_l1'],
                'plan_l1':plan_l1,'interval_capacity_excess':I,
                'session_capacity_excess':J,
                'whole_incumbent_total':Q(final['whole_incumbent_total_exact'])},
            'correction':{'combined_correction':Q(final['whole_incumbent_total_exact']),
                          'negative_l1':exp['N'],'orphan_positive_l1':exp['O'],
                          'interval_capacity_excess':I,'materialized_session_excess':J},
            'physical_witness':witness,'physical_objective':physical_objective}

h.check_column=check_column
h.audit_pricing=audit_pricing

def mixture(cell,columns,saved):
    for c in columns:h.check_column(cell,c)
    if saved['simplex'].get('source')!='exact-pairwise-polish':return h.mixture(cell,columns,saved)
    d=saved['simplex'];w=list(map(Q,d['weights_exact']))
    need(len(w)==len(columns) and min(w)>=0 and sum(w)==1,'exact polished simplex')
    need(d=={'source':'exact-pairwise-polish','weights_exact':[str(x) for x in w],'positive_weights':sum(x>0 for x in w),'mass_exact':'1'},'polished simplex metadata')
    need(saved['column_keys']==[c['key'] for c in columns] and saved['replayed_columns']==len(columns),'exact mixture full ordered pool')
    load=[sum((x*Q(c['load'][t]) for x,c in zip(w,columns)),Q(0)) for t in range(len(cell['market']['a']))]
    ops=sum((x*Q(c['ops_cost']) for x,c in zip(w,columns)),Q(0));F=h.supply(cell['market'],load);obj=ops+F
    need(list(map(Q,saved['load_exact']))==load and saved['load']==list(map(float,load)),'polished exact load/display')
    need(Q(saved['ops_exact'])==ops and Q(saved['supply_exact'])==F and Q(saved['objective_exact'])==obj,'polished exact nonlinear objective')
    need(saved['upper']==h.outward(obj,True),'outward polished UB')
    return {'weights':w,'load':load,'ops':ops,'objective':obj}

def audit_cell(cell,blob,budget,prior=None,*,diagnostic_budget_overrun=False):
    ev=blob['events'];rc=blob['receipt'];pack=blob['result'];result=pack['result'];name=cell['id']
    need(cell['pricing_oracle']==result['pricing_oracle']==ev[0]['pricing_oracle']==ORACLE,
         'explicit compact state oracle identity')
    assessment=pack['assessment']
    need(result['status']==rc['status'] and result['status'] in
         ('certified','stalled_bounded','budget_exhausted') and rc['pass']
         and assessment.get('status')==result['status'],
         'observed admitted certified/bounded status')
    need(assessment.get('bounded_budget_limited') is (result['status']=='budget_exhausted'),
         'budget-exhausted label is separately preserved by the assessment')
    need(Q(assessment['global_lower_exact'])==Q(result['lower_certificate']['lower_exact'])
         and Q(assessment['mixture_exact'])==Q(result['mixture']['objective_exact'])
         and result['lower']==h.outward(Q(assessment['lower_exact_stored']),False)
         and result['upper']==h.outward(Q(assessment['upper_exact_stored']),True),
         'assessment endpoints reconstruct the saved global certificate and feasible mixture')
    need(rc['cell']==name and rc['returncode']==0 and not rc['timeout'] and rc['evidence_issues']==[],'cell exit/evidence provenance')
    need(ev[0]['event']=='state_start' and ev[-1]['event']=='state_finish' and ev[-1]['result']==result,'complete state lifecycle')
    for k in ('state_identity','market_identity'):need(ev[0][k]==cell[k] and result[k]==cell[k],'state identity '+k)
    need(result['physical_identity']==cell['physical_identity'] and result['schema']==h.SCHEMA
         and result['extraction_policy']==POLICY,
         'final physical/schema/extraction policy')
    need(result['arm']==cell['arm'] and result['state_index']==cell['state_index'],'arm/index')
    need(ev[0]['fresh_bounds'] is True,'fresh state bounds')
    if cell['predecessor']:
        need(prior is not None and prior['receipt']['pass'] and prior['receipt']['returncode']==0 and not prior['receipt']['timeout'] and not prior['receipt']['evidence_issues'],'admitted predecessor receipt')
        pe=prior['events'];pr=prior['receipt']
        ns=sum(e['event']=='master_start' or e['event']=='pricing_native' and e['detail']['event']=='native_start' for e in pe)
        nr=sum(e['event']=='master_status' or e['event']=='pricing_native' and e['detail']['event']=='native_status' for e in pe)
        need(pr['native_accounting_complete'] and pr['polish_accounting_complete'] and ns==nr==pr['native_starts']==pr['native_returns'] and ns>0,'independent nonzero predecessor native accounting')
        prev=prior['result']['result']
        need(prev['pricing_oracle']==ORACLE and prev['extraction_policy']==POLICY,
             'retained same compact oracle and extraction policy')
        need(prev['status']=='certified' and prev['arm']=='retained' and prev['state_index']==cell['state_index']-1 and prev['physical_identity']==cell['physical_identity'],'immediate same-physics retained predecessor')
        pool=copy.deepcopy(prev['columns'])
    else:need(prior is None,'cold cannot import');pool=[]
    need(ev[0]['imported_column_keys']==[c['key'] for c in pool],'exact whole-pool retained import')
    for c in pool:h.check_column(cell,c)
    allcols={c['key']:c for c in pool};masters=[];pricing=[];certs=[];eligible=[];steps=[];checks=[];phases=[];walls=[]
    points=[[0.]*len(cell['market']['a'])];lastpool=None;current=None;i=1;maxbits=0;polishwall=0.0
    timing_violations=[]
    while i<len(ev)-1:
        e=ev[i]
        if e['event']=='pricing_request':
            call=len(pricing);need(e['call']==call,'sequential pricing request')
            need(e['pricing_oracle']==ORACLE,
                 'compact request oracle provenance')
            seed=not pool and call==0;need(e['seed']==seed,'cold generic seed versus retained no-seed')
            need(e['prices']==(cell['market']['a'] if seed else lastpool['prices']),'fresh serialized-gradient pricing')
            if not seed:need(Q(lastpool['pool_gap_exact'])<=Q(budget['pool_tolerance']),'qualified inner pool before pricing')
            inner=[];i+=1
            while ev[i]['event']=='pricing_native':need(ev[i]['call']==call,'nested native owner');inner.append(ev[i]['detail']);i+=1
            answer,bound=ev[i:i+2]
            need(answer['event']=='pricing_result' and bound['event']=='global_bound' and answer['call']==bound['call']==call,'pricing result/bound lifecycle')
            p=h.audit_pricing(cell,e,inner,answer,bound);pricing.append(p);walls.append(inner[1]['stats']['wall_s']);certs.append(bound['certificate']);c=bound['column'];i+=2
            if seed:
                pool.append(c);allcols[c['key']]=c;eligible.append(Q(c['ops_cost'])+h.supply(cell['market'],list(map(Q,c['load']))))
            if i<len(ev)-1 and ev[i]['event']=='column_added':
                add=ev[i];need(c['key'] not in {x['key'] for x in pool} and add['key']==c['key'] and add['size']==len(pool)+1,'new complete physical column')
                gap=min(eligible)-max(Q(z['lower_exact']) for z in certs)
                need(bool(add.get('after_certificate'))==(gap<=Q(budget['epsilon'])),'post-certificate column admission label')
                pool.append(c);allcols[c['key']]=c;i+=1
            elif not seed:
                need(min(eligible)-max(Q(z['lower_exact']) for z in certs)<=Q(budget['epsilon']),'cannot continue uncertified without new column')
        elif e['event']=='master_start':
            call=len(masters);need(e['call']==call and e['column_keys']==[c['key'] for c in pool] and e['tangent_points']==points,'master pool/tangent immutable history')
            status,snapshot,replay=ev[i+1:i+4]
            need([x['event'] for x in (status,snapshot,replay)]==['master_status','master_incumbent','master_replay'] and all(x['call']==call for x in (status,snapshot,replay)),'master phase evidence')
            rec=h.check_master(cell,pool,e,status,snapshot,replay);masters.append(rec);walls.append(status['stats']['wall_s']);current=replay['mixture'];eligible.append(rec['objective'])
            repeat=current['load'] in points;need(replay['repeated_tangent_point']==repeat,'raw tangent repeat flag');i+=4
            start=ev[i];need(start['event']=='pool_polish_start' and start['master_call']==call and start['cumulative_steps']==len(steps),'unique polish phase start/count')
            near(start['remaining_seconds'],budget['polish_seconds']-polishwall,'cumulative remaining polish time',1e-12);i+=1
            step0,check0=len(steps),len(checks);elapsed=0.0;finish=None
            while True:
                ck=ev[i]
                if ck['event']=='pool_polish_finish':
                    # The implementation checks its deadline at the top of
                    # the next polishing iteration. A costly exact transfer
                    # may therefore be the last event before LimitReached.
                    # Preserve that event and its cap violation in diagnostic
                    # mode; the default strict audit still rejects it.
                    need(diagnostic_budget_overrun and ck.get('outcome')=='LimitReached',
                         'polishing terminated between recorded checks')
                    timing_violations.append({'kind':'polishing_deadline_reached_before_next_check',
                        'master_call':call,'last_step_elapsed_s':elapsed,
                        'remaining_seconds_at_phase_start':start['remaining_seconds']})
                    finish=ck;i+=1;break
                need(ck['event']=='pool_polish_check' and ck['master_call']==call and ck['step']==len(steps) and ck['mixture']==current,'ordered polish check and exact current mixture')
                mix=mixture(cell,pool,current);gap=h.pool_bound(cell,pool,mix,ck['pool']);maxbits=max(maxbits,bits(mix['weights']+mix['load']+[mix['objective']]))
                need(elapsed<=ck['elapsed_s']<start['remaining_seconds'],'check elapsed and fixed local deadline');elapsed=ck['elapsed_s'];checks.append({'master_call':call,'step':len(steps),'pool_gap':gap});eligible.append(mix['objective']);lastpool=ck['pool'];i+=1
                if gap<=Q(budget['pool_tolerance']):break
                st=ev[i];need(st['event']=='pool_polish_step' and st['master_call']==call and st['step']==len(steps)+1 and st['column_keys']==[c['key'] for c in pool],'unique sequential within-phase transfer')
                w=mix['weights'];grad=[Q(a)+Q(b)*x for a,b,x in zip(cell['market']['a'],cell['market']['b'],mix['load'])]
                scores=[Q(c['ops_cost'])+dot(grad,list(map(Q,c['load']))) for c in pool]
                toward=min(range(len(pool)),key=lambda j:(scores[j],j));away=max((j for j,x in enumerate(w) if x>0),key=lambda j:(scores[j],-j))
                d=scores[away]-scores[toward];direction=[Q(b)-Q(a) for a,b in zip(pool[away]['load'],pool[toward]['load'])];H=sum((Q(b)*x*x for b,x in zip(cell['market']['b'],direction)),Q(0));need(d>0 and H>=0,'positive transfer decrease/convex curvature')
                gamma=min(w[away],d/H) if H else w[away];updated=w[:];updated[away]-=gamma;updated[toward]+=gamma
                need(st['away']==away and st['toward']==toward and st['away_key']==pool[away]['key'] and st['toward_key']==pool[toward]['key'],'exact deterministic pair selection')
                for k,x in [('weights_before_exact',w),('weights_after_exact',updated),('gradient_exact',grad),('scores_exact',scores),('direction_exact',direction)]:need(list(map(Q,st[k]))==x,'transfer '+k)
                for k,x in [('directional_decrease_exact',d),('curvature_exact',H),('gamma_exact',gamma),('objective_before_exact',mix['objective'])]:need(Q(st[k])==x,'transfer '+k)
                new=mixture(cell,pool,st['mixture']);pred=mix['objective']-gamma*d+H*gamma*gamma/2
                need(new['weights']==updated and new['objective']==Q(st['objective_after_exact'])==pred and pred<mix['objective'],'exact feasible line-search quadratic decrease')
                maxbits=max(maxbits,bits(grad+scores+direction+[d,H]),bits(updated+[gamma]),bits(new['load']+[pred]))
                need(st['max_rational_bits']==maxbits<=budget['rational_bits'],'declared rational bit cap')
                need(bits(new['load']+[new['ops'],Q(st['mixture']['supply_exact']),pred])<=budget['rational_bits'],'projected rational bit cap')
                within_step_budget=elapsed<=st['elapsed_s']<start['remaining_seconds']
                if not within_step_budget:
                    timing_violations.append({'kind':'step_elapsed_at_or_after_remaining_aggregate_budget',
                        'master_call':call,'step':st['step'],'elapsed_s':st['elapsed_s'],
                        'remaining_seconds_at_phase_start':start['remaining_seconds']})
                    need(diagnostic_budget_overrun,
                         'transfer elapsed budget')
                elapsed=st['elapsed_s']
                steps.append({'master_call':call,'step':st['step'],'gamma':gamma,'decrease':d,'curvature':H,'before':mix['objective'],'after':pred,'max_bits':maxbits})
                eligible.append(pred);current=st['mixture'];i+=1
            if finish is None:
                finish=ev[i]
                need(finish['event']=='pool_polish_finish' and finish['master_call']==call,
                     'polish phase finish attribution')
                i+=1
            need(finish['outcome'] in ('qualified','LimitReached'),
                 'polish phase termination status is preserved')
            if finish['outcome']=='LimitReached':
                timing_violations.append({'kind':'polishing_phase_terminated_at_limit',
                    'master_call':call,'finish_elapsed_s':finish['elapsed_s']})
                need(diagnostic_budget_overrun,
                     'limited polish phase only allowed for diagnostic reconstruction')
            need(finish['steps_completed']==len(steps)-step0 and finish['checks_completed']==len(checks)-check0,'phase exact step/check accounting')
            within_finish_budget=elapsed<=finish['elapsed_s']<=start['remaining_seconds']
            if not within_finish_budget:
                timing_violations.append({'kind':'phase_finish_exceeds_remaining_aggregate_budget',
                    'master_call':call,'finish_elapsed_s':finish['elapsed_s'],
                    'remaining_seconds_at_phase_start':start['remaining_seconds']})
                need(diagnostic_budget_overrun,
                     'phase end fixed time')
            polishwall+=finish['elapsed_s'];phases.append(finish)
            if finish['outcome']=='LimitReached':
                need(diagnostic_budget_overrun and i==len(ev)-1
                     and ev[i]['event']=='state_finish',
                     'budget-limited final polish terminates directly at saved state result')
                i=len(ev)-1
            else:
                prog=ev[i];added=current['load'] not in points
                need(prog=={'event':'master_progress','call':call,'new_tangent_added':added,'repeated_raw_tangent_point':repeat,'polished_load_exact':current['load_exact']},'master progress exact history')
                if added:points.append(current['load'])
                i+=1
        else:raise AssertionError('unknown/out-of-order event '+e['event'])
    need(result['columns']==pool and len(pool)<=budget['pool_cap'],'complete final physical column pool')
    counts={'master_calls':len(masters),'pricing_requests':len(pricing),'seed_requests':sum(p['seed'] for p in pricing),'polish_steps':len(steps),'polish_checks':len(checks),'polish_wall_s':polishwall,'max_rational_bits':maxbits}
    need(result['counts']==counts,'exact complete saved counts')
    within_aggregate_polish_cap=polishwall<=budget['polish_seconds']
    if not within_aggregate_polish_cap:
        timing_violations.append({'kind':'aggregate_polish_wall_exceeds_frozen_budget',
            'observed_seconds':polishwall,'budget_seconds':budget['polish_seconds'],
            'overrun_seconds':polishwall-budget['polish_seconds']})
        need(diagnostic_budget_overrun,
             'cumulative polishing wall-time cap')
    need(len(masters)<=budget['master_calls'] and len(pricing)<=budget['pricing_calls'] and len(steps)<=budget['polish_steps'],'all cumulative count caps')
    for k,v in [('master_starts',len(masters)),('pricing_starts',len(pricing)),('pricing_requests',len(pricing)),('seed_requests',counts['seed_requests']),('native_starts',len(masters)+len(pricing)),('native_returns',len(masters)+len(pricing)),('polish_starts',len(phases)),('polish_returns',len(phases)),('polish_checks',len(checks)),('polish_steps',len(steps))]:need(rc[k]==v,'receipt '+k)
    need(rc['native_accounting_complete'] and rc['polish_accounting_complete'],'complete native and polish accounting');near(rc['native_wall_s'],math.fsum(walls),'native wall accounting',1e-12);near(rc['polish_wall_s'],polishwall,'polish wall accounting',1e-12)
    need(pack['elapsed_s']<=budget['wall_seconds'] and rc['elapsed_s']>=pack['elapsed_s'],'observed state duration within frozen deadline')
    lower=max(Q(c['lower_exact']) for c in certs);upper=min(eligible);need(result['lower_certificate'] in certs and Q(result['lower_certificate']['lower_exact'])==lower,'best fresh lower has current pricing provenance')
    fm=mixture(cell,[allcols[k] for k in result['mixture']['column_keys']],result['mixture']);need(fm['objective']==upper,'streamed best feasible UB')
    gap=upper-lower
    need(gap>=0 and result['epsilon']==budget['epsilon'],'nonnegative exact global stored-input interval')
    if result['status']=='certified':
        need(gap<=Q(budget['epsilon']) and result['reason'] is None,
             'certified status obeys global epsilon gate')
    else:
        need(result['status'] in ('stalled_bounded','budget_exhausted')
             and isinstance(result.get('reason'),str) and result['reason'],
             'bounded status and reason preserved')
    need(result['lower']==h.outward(lower,False) and result['upper']==h.outward(upper,True) and Q(result['gap_exact'])==gap and result['gap']==h.outward(gap,True),'exact final interval arithmetic')
    return {'cell':name,'status':result['status'],'saved_interval':[lower,upper],
            'saved_width':gap,'final_load':fm['load'],'final_weights':fm['weights'],
            'imported_columns':len(ev[0]['imported_column_keys']),'counts':counts,
            'pricing':pricing,'masters':masters,'steps':steps,'checks':checks,'phases':phases,
            'polish_budget_seconds':budget['polish_seconds'],
            'polish_wall_budget_compliant':within_aggregate_polish_cap and not timing_violations,
            'polish_wall_resource_violations':timing_violations,
            'global_bound_scope':'solver-conditioned GRB pricing lower plus independently replayed feasible fleet mixture; no exact full-problem optimum claim'}

def corruptions(cells,blobs,budget):
    out=[]
    event=lambda b,k:next(e for e in b['events'] if e['event']==k)
    def reject(label,change,name='nominal_cold_s0'):
        c=copy.deepcopy(cells[name]);b=copy.deepcopy(blobs[name]);prior=copy.deepcopy(blobs[c['predecessor']]) if c['predecessor'] else None
        change(c,b,prior)
        try:audit_cell(c,b,budget,prior)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError,IndexError) as exc:out.append({'control':label,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('corruption accepted: '+label)
    reject('missing master return',lambda c,b,p:b['events'].remove(event(b,'master_status')))
    reject('raw master weight',lambda c,b,p:event(b,'master_incumbent')['variables'][0]['solution'].update(value=.8,repr='0.8'))
    reject('raw master semantic mapping',lambda c,b,p:event(b,'master_incumbent')['mapping']['lambda'].__setitem__(0,1))
    reject('native lower bound invented',lambda c,b,p:event(b,'master_status')['stats'].__setitem__('lower_bound',999))
    reject('native fallback hidden',lambda c,b,p:event(b,'master_status')['stats']['backend_runtime'].__setitem__('requested','CBC'))
    reject('tangent intercept raised',lambda c,b,p:event(b,'master_start')['tangent_rows'][1][0].__setitem__('intercept',1))
    reject('mixture exact weight removed',lambda c,b,p:event(b,'master_replay')['mixture']['simplex']['weights_exact'].__setitem__(0,'0'))
    reject('mixture nonlinear supply omitted',lambda c,b,p:event(b,'master_replay')['mixture'].__setitem__('supply_exact','0'))
    reject('pool gap fabricated',lambda c,b,p:event(b,'master_replay')['pool'].__setitem__('pool_gap_exact','0'))
    reject('global conjugate omitted',lambda c,b,p:next(e for e in b['events'] if e['event']=='global_bound' and e['call']==1)['certificate'].__setitem__('conjugate_exact','0'))
    reject('global lower fabricated',lambda c,b,p:event(b,'global_bound')['certificate'].__setitem__('pricing_lower',1000))
    reject('column intrinsic cost corrupted',lambda c,b,p:event(b,'global_bound')['column'].__setitem__('ops_cost',0))
    reject('physical SOC corrupted',lambda c,b,p:event(b,'pricing_result')['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',0))
    reject('polish gamma corrupted',lambda c,b,p:event(b,'pool_polish_step').__setitem__('gamma_exact','0'))
    reject('polish direction corrupted',lambda c,b,p:event(b,'pool_polish_step')['direction_exact'].__setitem__(1,'0'))
    reject('polish pair selection corrupted',lambda c,b,p:event(b,'pool_polish_step').__setitem__('away',99))
    reject('polish weight corrupted',lambda c,b,p:event(b,'pool_polish_step')['weights_after_exact'].__setitem__(0,'0'))
    reject('polish quadratic objective corrupted',lambda c,b,p:event(b,'pool_polish_step').__setitem__('objective_after_exact','0'))
    reject('polish step phase misattributed',lambda c,b,p:event(b,'pool_polish_step').__setitem__('master_call',0))
    reject('polish cumulative step duplicated',lambda c,b,p:event(b,'pool_polish_step').__setitem__('step',0))
    reject('polish phase finish count corrupted',lambda c,b,p:event(b,'pool_polish_finish').__setitem__('checks_completed',99))
    reject('polish overdeadline result admitted',lambda c,b,p:event(b,'pool_polish_check').__setitem__('elapsed_s',6.))
    reject('polish rational bit count corrupted',lambda c,b,p:event(b,'pool_polish_step').__setitem__('max_rational_bits',1))
    reject('final narrower interval invented',lambda c,b,p:b['result']['result'].__setitem__('lower',95))
    reject('final cumulative polish count corrupted',lambda c,b,p:b['receipt'].__setitem__('polish_steps',99))
    reject('failed predecessor imported',lambda c,b,p:p['receipt'].__setitem__('pass',False),'nominal_retained_s1')
    reject('timed out predecessor imported',lambda c,b,p:p['receipt'].__setitem__('timeout',True),'nominal_retained_s1')
    reject('predecessor native accounting incomplete',lambda c,b,p:p['receipt'].__setitem__('native_returns',999),'nominal_retained_s1')
    reject('retained imported pool incomplete',lambda c,b,p:p['result']['result']['columns'].pop(),'nominal_retained_s1')
    reject('retained bounds marked stale',lambda c,b,p:b['events'][0].__setitem__('fresh_bounds',False),'nominal_retained_s1')
    reject('retained state falsely cold seeded',lambda c,b,p:event(b,'pricing_request').__setitem__('seed',True),'nominal_retained_s1')
    native_event=lambda b,k:next(e['detail'] for e in b['events'] if e['event']=='pricing_native' and e['detail']['event']==k)
    def change_raw(b,mapping,value):
        snap=native_event(b,'native_incumbent');idx=snap['mapping'][mapping][0]
        snap['variables'][idx]['solution']={'value':value,'repr':repr(value)}
    reject('compact returned formulation changed',lambda c,b,p:event(b,'pricing_result')['result'].__setitem__('formulation','indexed'))
    reject('compact state oracle changed',lambda c,b,p:b['events'][0].__setitem__('pricing_oracle','indexed'))
    reject('compact request oracle changed',lambda c,b,p:event(b,'pricing_request').__setitem__('pricing_oracle','indexed'))
    reject('compact raw formulation changed',lambda c,b,p:native_event(b,'native_incumbent').__setitem__('formulation','indexed'))
    reject('compact raw mapping duplicated',lambda c,b,p:native_event(b,'native_incumbent')['mapping']['market_load'].__setitem__(0,0))
    reject('compact raw SOC violated',lambda c,b,p:change_raw(b,'soc_after',3.0))
    reject('compact raw path coverage violated',lambda c,b,p:change_raw(b,'movement_selection',.5))
    reject('compact interval capacity changed',lambda c,b,p:native_event(b,'native_incumbent')['mapping']['intervals'][1].__setitem__('rate_kw',99))
    reject('compact positive session removed',lambda c,b,p:native_event(b,'serial_decoding')['charges'].pop())
    reject('compact correction ledger changed',lambda c,b,p:native_event(b,'serial_decoding').__setitem__('combined_roundoff_exact','1'))
    reject('retained foreign oracle imported',lambda c,b,p:p['result']['result'].__setitem__('pricing_oracle','indexed'),'nominal_retained_s1')
    reject('V3 final policy changed',lambda c,b,p:b['result']['result'].__setitem__('extraction_policy','native-roundoff-qualification-v2'))
    reject('V3 state identity policy changed',lambda c,b,p:c.__setitem__('state_identity','0'))
    reject('V3 pricing plan policy changed',lambda c,b,p:event(b,'pricing_result')['result']['plan'].__setitem__('extraction_policy','native-roundoff-qualification-v2'))
    reject('V3 raw policy changed',lambda c,b,p:native_event(b,'native_incumbent').__setitem__('extraction_policy','native-roundoff-qualification-v2'))
    reject('V3 saved column policy changed',lambda c,b,p:event(b,'global_bound')['column'].__setitem__('extraction_policy','native-roundoff-qualification-v2'))
    reject('V3 retained predecessor policy changed',lambda c,b,p:p['result']['result'].__setitem__('extraction_policy','native-roundoff-qualification-v2'),'nominal_retained_s1')
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--attempt',type=Path,default=None)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None))
    ap.add_argument('--outer-dir',type=Path,default=None)
    ap.add_argument('--manifest-sha256',required=True)
    ap.add_argument('--out',type=Path,default=HERE/'audit-report.json')
    args=ap.parse_args()
    need(args.repository is not None,'repository path required')
    repo=args.repository.resolve()
    attempt=(args.attempt or (repo/ATTEMPT_REL)).resolve()
    outer=(args.outer_dir or (repo.parent/'research-20260927/cluster/grb-hull-559602')).resolve()
    out=args.out.resolve()
    need(out.parent==HERE.resolve() and not out.exists() and not out.is_symlink(),
         'audit report must be a fresh output outside raw evidence')
    started=time.perf_counter()
    manifest_bytes=(attempt/'MANIFEST.json').read_bytes()
    need(base.digest(manifest_bytes)==args.manifest_sha256==MANIFEST_SHA,
         'pinned raw GRB manifest')
    manifest=json.loads(manifest_bytes)
    need(manifest.get('protocol')=='native-v3-grb-replication-20260927-v1'
         and isinstance(manifest.get('files'),dict),'GRB raw manifest protocol/file map')
    def verify_raw():
        actual={str(p.relative_to(attempt)) for p in attempt.rglob('*')
                if p.is_file() and p.name!='MANIFEST.json'}
        need(actual==set(manifest['files']),'raw attempt contains exactly manifest-listed files')
        for rel,item in manifest['files'].items():
            data=(attempt/rel).read_bytes()
            need(item=={'sha256':base.digest(data),'bytes':len(data)},'immutable raw file '+rel)
        need(base.digest((attempt/'MANIFEST.json').read_bytes())==args.manifest_sha256,
             'raw manifest unchanged')
    verify_raw()
    frozen=base.read(attempt/'frozen.json');budget=frozen['budget']
    full_commit=subprocess.check_output(['git','-C',str(repo),'rev-parse',COMMIT]).decode().strip()
    need(full_commit==COMMIT and frozen['freeze_label']==COMMIT
         and frozen['protocol']=='native-pathflow-hull-qualification-20260927-v3-orphan-projection'
         and frozen['pricing_oracle']==ORACLE and frozen['extraction_policy']==POLICY,
         'published source commit and frozen V3 oracle/policy identity')
    need(budget.get('backend')=='GRB' and len(frozen['source_hashes'])==20,
         'GRB backend and complete 20-entry frozen source list')
    source_blob_hashes={}
    for rel,expected in frozen['source_hashes'].items():
        blob=subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+rel])
        need(base.digest(blob)==expected,'frozen source Git blob '+rel)
        source_blob_hashes[rel]=expected
    need(frozen['budget'].get('phase_seconds')==10.0 and frozen['budget'].get('threads')==1
         and frozen.get('worker_seconds')==75.0 and frozen.get('outer_seconds')==650.0,
         'frozen native, worker and supervisor budgets')
    cells={c['id']:c for c in frozen['controls']}
    need(list(cells)==NAMES and len(cells)==8,'all eight frozen cells and order')
    cbc_path=repo/'result/native_pathflow_hull/20260927-attempt2/frozen.json'
    cbc_bytes=cbc_path.read_bytes()
    need(base.digest(cbc_bytes)==CBC_V3_FROZEN_SHA,'pinned CBC V3 attempt-2 frozen controls')
    cbc=json.loads(cbc_bytes)
    need({k:v for k,v in budget.items() if k!='backend'}
         =={k:v for k,v in cbc['budget'].items() if k!='backend'},
         'all V3 hull budget fields unchanged except backend')
    need([c['id'] for c in cbc['controls']]==NAMES,'CBC V3 control names/order')
    for c,o in zip(cells.values(),cbc['controls']):
        need({k:v for k,v in c.items() if k!='state_identity'}
             =={k:v for k,v in o.items() if k!='state_identity'},
             'all eight scientific controls, target data and V3 identities unchanged')
        need(c['physical_identity']==h.digest_object({'schema':'egg-native-recharge-v1','case':c['case']})
             and c['market_identity']==h.digest_object(c['market']),
             'complete independent physical and market identities')
        need(c['state_identity']==h.digest_object({'schema':h.SCHEMA,'case':c['physical_identity'],
             'market':c['market_identity'],'arm':c['arm'],'state_index':c['state_index'],
             'budget':budget,'extraction_policy':POLICY,'pricing_oracle':ORACLE}),
             'exact GRB state identity derived from backend budget')
    summary=base.read(attempt/'summary.json')
    supervisor=base.read(attempt/'supervisor_receipt.json')
    need(summary['protocol']==frozen['protocol'] and summary['all_pass'] is True
         and summary['source_hashes_unchanged'] is True and len(summary['cells'])==8
         and [r['cell'] for r in summary['cells']]==NAMES,
         'complete successful 8-control summary')
    need(supervisor['protocol']==frozen['protocol'] and supervisor['returncode']==0
         and supervisor['outer_timeout'] is False
         and supervisor['elapsed_s']<=frozen['outer_seconds'],
         'complete bounded hull controller receipt')
    wrapper_launch=base.read(attempt/'grb_wrapper_launch.json')
    wrapper_receipt=base.read(attempt/'grb_wrapper_receipt.json')
    sentinel=Path(str(attempt)+'.launch')
    completion=base.read(sentinel/'completion.json')
    slurm=base.read(sentinel/'slurm_receipt.json')
    need(wrapper_launch['protocol']==wrapper_receipt['protocol']=='native-v3-grb-replication-20260927-v1'
         and wrapper_launch['stage']==wrapper_receipt['stage']=='hull'
         and wrapper_launch['backend']=='GRB' and wrapper_launch['source_commit']==COMMIT
         and wrapper_launch['physical_admission_sha256']==PHYSICAL_ADMISSION_SHA
         and wrapper_launch['outer_cap_seconds']==720,
         'GRB hull wrapper identity and physical admission pin')
    need(wrapper_receipt['returncode']==0 and wrapper_receipt['child_returncode']==0
         and wrapper_receipt['outer_timeout'] is False
         and wrapper_receipt['source_hashes_unchanged'] is True
         and wrapper_receipt['launch_error'] is None
         and wrapper_receipt['source_check_error'] is None
         and wrapper_receipt['stage_evidence_error'] is None
         and wrapper_receipt['elapsed_seconds']<=720,
         'successful bounded hull wrapper and unchanged sources')
    cmd=wrapper_launch['command']
    need(cmd[1:3]==['-m','experiments.native_pathflow_hull_qualification']
         and cmd[3]=='--output' and Path(cmd[4]).as_posix().endswith(str(ATTEMPT_REL))
         and cmd[5:]==['--freeze-label',COMMIT,'--backend','GRB'],
         'wrapper child command pins hull stage/path/full commit/backend')
    wrapper_sources=wrapper_launch.get('source_hashes')
    need(isinstance(wrapper_sources,dict) and wrapper_sources
         and all(wrapper_sources.get(path)==sha for path,sha in frozen['source_hashes'].items()),
         'wrapper source inventory covers every child frozen source')
    need(wrapper_sources.get('doc/NATIVE_V3_GRB_PHYSICAL_ADMISSION_20260927.json')
         ==PHYSICAL_ADMISSION_SHA,'wrapper pins the passing physical admission')
    wrapper_source_blobs={}
    for rel,expected in wrapper_sources.items():
        blob=subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+rel])
        need(base.digest(blob)==expected,'wrapper frozen Git blob source '+rel)
        wrapper_source_blobs[rel]=expected
    need(wrapper_receipt['launch_sentinel']==str(sentinel.relative_to(repo))
         and completion['attempt']==str(ATTEMPT_REL)
         and completion['receipt_sha256']==base.digest((attempt/'grb_wrapper_receipt.json').read_bytes())
         and completion['manifest_sha256']==args.manifest_sha256,
         'sibling completion sentinel binds raw wrapper receipt and manifest')
    sentinel_names={p.name for p in sentinel.iterdir() if p.is_file()}
    need(sentinel_names=={'launch.json','stdout.txt','stderr.txt','completion.json','slurm_receipt.json'},
         'exact five-file wrapper launch sentinel')
    need((sentinel/'stdout.txt').read_bytes()==(attempt/'grb_wrapper_stdout.txt').read_bytes()
         and (sentinel/'stderr.txt').read_bytes()==(attempt/'grb_wrapper_stderr.txt').read_bytes(),
         'wrapper logs are preserved byte-identically inside sealed manifest')
    need(slurm['job_id']=='559602' and slurm['returncode']==0
         and slurm['timeout_exit'] is False and slurm['shell_cap_seconds']==770
         and 0<=slurm['elapsed_whole_seconds']<=870,
         'Slurm wrapper receipt and shell timeout')
    need(wrapper_launch['source_hashes'].get('src/experiments/native_v3_grb_replication.py')
         and wrapper_launch['source_hashes'].get('doc/NATIVE_V3_GRB_PHYSICAL_RESULT_AUDIT_20260927.md'),
         'wrapper includes physical admission/audit provenance')
    intent_path=outer/'20260927-attempt1.INTENT.json'
    submitted_path=outer/'20260927-attempt1.SUBMITTED.json'
    sacct_path=outer/'SACCT.txt';scontrol_path=outer/'SCONTROL.txt'
    transport_path=outer/'transport_receipt.json';tar_path=outer/'hull-559602-transport.tar'
    intent=base.read(intent_path);submitted=base.read(submitted_path);transport=base.read(transport_path)
    need(intent['source_commit']==submitted['source_commit']==transport['source_commit']==COMMIT
         and intent['stage']==submitted['stage']=='hull' and intent['backend']=='GRB'
         and submitted['slurm_job_id']=='559602','saved submission/transport intent identity')
    need(transport['job_id']=='559602' and transport['raw_files']==67
         and transport['raw_manifest_entries']==66 and transport['launch_files']==5
         and transport['raw_manifest_sha256']==args.manifest_sha256
         and transport['remote_tar_sha256']=='3e06140f72d5f511b30e730712eb1a32a2b93549e2f3e2b1cd7675a7b92f2924'
         and transport['transport_tar_sha256']==transport['remote_tar_sha256']
         and base.digest(tar_path.read_bytes())==transport['transport_tar_sha256'],
         'verified full local/remote transport tar and raw/launch inventory')
    need(base.digest(sacct_path.read_bytes())==transport['sacct_sha256']
         and base.digest(scontrol_path.read_bytes())==transport['scontrol_sha256'],
         'outer Slurm receipt transport hashes')
    rows=[line.split('|') for line in sacct_path.read_text().splitlines()]
    need([row[0] for row in rows]==['559602','559602.batch','559602.extern']
         and all(row[2]=='COMPLETED' and row[3]=='00:00:26' and row[4]=='0:0' and row[5]=='1'
                 for row in rows) and rows[0][6]=='8G',
         'fresh sacct completion, exit, elapsed time, CPU and memory')
    scontrol=scontrol_path.read_text()
    for field in ('JobId=559602','JobName=egg-v3-grb-hull','JobState=COMPLETED',
                  'Requeue=0','TimeLimit=00:15:00','NumCPUs=1','MinMemoryNode=8G',
                  'ExcNodeList=scaglione-compute-01','NodeList=snavely-cpu-02',
                  'WorkDir=/home/nc437/egg-journal-grb-hull-20260927'):
        need(field in scontrol,'scontrol scheduler receipt '+field)
    scheduler_logs={}
    log_dir=outer/'transport-extracted'
    for suffix in ('out','err'):
        log=log_dir/f'egg-v3-grb-hull-559602.{suffix}'
        need(log.is_file(),'retained scheduler log '+suffix)
        data=log.read_bytes()
        scheduler_logs[log.name]={'bytes':len(data),'sha256':base.digest(data),'content_embedded':False}
    outer_hashes={}
    for label,path in (('intent',intent_path),('submitted',submitted_path),('sacct',sacct_path),
                       ('scontrol',scontrol_path),('transport_receipt',transport_path),('transport_tar',tar_path)):
        data=path.read_bytes();outer_hashes[label]={'bytes':len(data),'sha256':base.digest(data)}
    blobs={}
    for index,receipt in enumerate(summary['cells']):
        name=receipt['cell'];folder=attempt/name;cell=cells[name]
        inp=base.read(folder/'input.json')
        need(inp['control']==cell and inp['budget']==budget
             and inp['source_hashes']==frozen['source_hashes'],'full frozen per-cell input '+name)
        need(receipt==base.read(folder/'receipt.json') and receipt['pass'] is True
             and receipt['returncode']==0 and receipt['timeout'] is False
             and receipt['evidence_issues']==[] and receipt['elapsed_s']<=frozen['worker_seconds'],
             'bounded successful cell receipt '+name)
        launch=base.read(folder/'launch.json')
        need(launch['worker_cap_s']==frozen['worker_seconds']
             and launch['command'][1:5]==['-m','experiments.native_pathflow_hull_qualification','--worker',name],
             'exact worker command and timeout '+name)
        result=base.read(folder/'result.json')
        need(result['environment'].get('mip_version') and result['environment'].get('gurobipy_version'),
             'recorded GRB Python package versions '+name)
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()],
                     'receipt':receipt,'result':result}
    need(list(blobs)==NAMES,'all eight per-cell raw output bundles in order')
    records=[]
    for name,cell in cells.items():
        records.append(audit_cell(cell,blobs[name],budget,blobs.get(cell['predecessor'])))
    need(len(records)==8 and all(r['status']=='certified' for r in records),
         'eight exact target/global-hull certificates')
    controls=corruptions(cells,blobs,budget)
    need(len(controls)>=40 and all(x['rejected'] for x in controls),
         'all independent native/master/Fenchel/mixture/polish/policy corruptions rejected')
    pricing=[p for r in records for p in r['pricing']]
    masters=[m for r in records for m in r['masters']]
    steps=[s for r in records for s in r['steps']]
    raw_runtime=[]
    for blob in blobs.values():
        for event in blob['events']:
            if event['event']=='master_status':raw_runtime.append(event['stats']['backend_runtime'])
            elif event['event']=='pricing_native' and event['detail']['event']=='native_status':
                raw_runtime.append(event['detail']['stats']['backend_runtime'])
    lib_hashes=sorted({x['native_library_sha256'] for x in raw_runtime})
    need(len(raw_runtime)==len(pricing)+len(masters) and len(lib_hashes)==1,
         'every native call has one stable GRB runtime/library fingerprint')
    runtime_ids={(x['requested'],x['model_solver_name'],x['solver_module'],x['solver_class'],
                  x['native_library_sha256'],x['native_library_path']) for x in raw_runtime}
    need(len(runtime_ids)==1,'consistent GRB solver identity across all native pricing/master calls')
    versions={(b['result']['environment']['mip_version'],b['result']['environment']['gurobipy_version'])
              for b in blobs.values()}
    need(len(versions)==1,'one recorded mip/gurobipy environment across all eight states')
    verify_raw()
    report={'audit_status':'PASS: independent GRB hull result audit; all eight controls admitted',
      'downstream_scope':'Hull qualification only; a separate nonlinear pilot admission review and source freeze remain required.',
      'frozen_commit':COMMIT,'frozen_source_count':len(source_blob_hashes),
      'frozen_source_hashes_verified_against_git_blobs':source_blob_hashes,
      'wrapper_source_count':len(wrapper_source_blobs),
      'wrapper_source_hashes_verified_against_git_blobs':wrapper_source_blobs,
      'source_unchanged_receipts':{'controller':summary['source_hashes_unchanged'],
                                   'wrapper':wrapper_receipt['source_hashes_unchanged']},
      'cbc_v3_frozen_sha256':CBC_V3_FROZEN_SHA,
      'unchanged_from_cbc_v3_attempt2':{'control_count':8,'scientific_controls_exact_except_state_identity':True,
                                        'budget_fields_exact_except_backend':True},
      'original_manifest_sha256':args.manifest_sha256,'raw_files':len(manifest['files']),
      'raw_bytes':sum(x['bytes'] for x in manifest['files'].values()),
      'counts':{'cells':8,'certified':8,'pricing_calls':len(pricing),'master_calls':len(masters),
        'native_calls':len(pricing)+len(masters),'pricing_native_calls':len(pricing),
        'master_native_calls':len(masters),'polish_steps':len(steps),
        'polish_checks':sum(len(r['checks']) for r in records),
        'polish_phases':sum(len(r['phases']) for r in records),
        'native_raw_variables':sum(p['raw_variables'] for p in pricing),
        'master_raw_variables':sum(m['raw_variables'] for m in masters),
        'physical_witnesses':len(pricing),
        'physical_sessions':sum(p['physical_witness']['sessions'] for p in pricing),
        'SOC_events':sum(p['physical_witness']['soc_events'] for p in pricing),
        'corruption_controls_rejected':len(controls)},
      'grb_runtime':{'backend':'GRB','solver_module':'mip.gurobi',
        'native_library_fingerprints':lib_hashes,'mip_and_gurobipy_versions':sorted(list(x) for x in versions),
        'library_bytes_reverified_locally':False},
      'max_native_constraint_residual':max(p['max_raw_constraint_residual'] for p in pricing),
      'max_master_constraint_residual':max(m['raw_LP_residual'] for m in masters),
      'max_native_PWL_objective_error':max(abs(m['native_PWL_incumbent_minus_exact']) for m in masters),
      'max_combined_physical_correction':max(p['correction']['combined_correction'] for p in pricing),
      'exact_width_range':[min(r['saved_width'] for r in records),max(r['saved_width'] for r in records)],
      'max_rational_bits':max(r['counts']['max_rational_bits'] for r in records),
      'cells':records,'corruption_controls':controls,
      'wrapper_and_slurm':{'wrapper_launch':wrapper_launch,'wrapper_receipt':wrapper_receipt,
        'supervisor_launch':base.read(attempt/'supervisor_launch.json'),'supervisor_receipt':supervisor,
        'launch_sentinel':str(sentinel),'slurm_receipt':slurm,'scheduler_logs':scheduler_logs,
        'outer_receipt_sha256_and_bytes':outer_hashes,
        'sacct_fields':[{'job_id':row[0],'state':row[2],'elapsed':row[3],'exit_code':row[4],
                         'cpus':row[5],'memory':row[6] if len(row)>6 else ''} for row in rows]},
      'stdout_policy':'Full wrapper, controller, worker, scheduler and transport logs are preserved and hashed; their contents are not embedded because they may contain license details.',
      'independence':'Standard-library exact arithmetic; copied independent physical/matrix/projection helpers and hull-specific exact master, mixture, Fenchel, retained-pool and polish reconstructions. No project implementation, solver package, optimizer or author import was called.',
      'audit_wall_s':time.perf_counter()-started}
    with out.open('x') as f:
        json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    review_manifest={'attempt_raw_manifest_sha256':args.manifest_sha256,
        'files':{p.name:{'bytes':p.stat().st_size,'sha256':base.digest(p.read_bytes())}
                 for p in sorted(HERE.glob('*.py'))},
        'report':{'bytes':out.stat().st_size,'sha256':base.digest(out.read_bytes())},
        'scope':'Independent review artifacts only; outside and excluded from original raw attempt.'}
    with (HERE/'REVIEW_MANIFEST.json').open('x') as f:
        json.dump(review_manifest,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'status':report['audit_status'],'out':str(out),
                      'counts':report['counts'],'raw_files':report['raw_files'],
                      'raw_bytes':report['raw_bytes'],'audit_wall_s':report['audit_wall_s']},indent=2))

if __name__=='__main__':main()
