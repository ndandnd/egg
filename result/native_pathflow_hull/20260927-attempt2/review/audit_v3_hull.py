#!/usr/bin/env python3
"""Independent solver-free reconstruction of V3 compact native-hull attempt 2.

Only Python standard library and colocated independent audit helpers are used.
No author module is imported; no native model or optimizer is instantiated.
"""
import argparse,copy,hashlib,itertools,json,math,subprocess,tempfile,time,uuid
from fractions import Fraction as Q
from pathlib import Path
import independent_hull_core as h
import independent_compact_core as compact
import independent_projection_audit as projection
base=compact.base
need,near=base.need,base.near
HERE=Path(__file__).resolve().parent
COMMIT='03d1da2f3629e722784e97891a8590060fa676ad'
MANIFEST_SHA='c3d9da88195161ddd2c054800e4d0a5944998a03b623730a771e7ce9bbb5644b'
ORACLE='egg-native-pathflow-v3-energy-band-orphan-projection'
FORMULATION=ORACLE
NATIVE_MATRIX='egg-native-pathflow-v2-energy-band'
POLICY='native-pathflow-orphan-projection-v1'
SHARED_POLICY='native-roundoff-qualification-v2'
OLD_FROZEN_SHA='eba73e27a69c66c64d777d3899acee46156e6ff8147109cd55c6ba6a2182a3da'
NAMES=['nominal_cold_s0','nominal_cold_s1','nominal_cold_s2','nominal_retained_s0','nominal_retained_s1','nominal_retained_s2','joint_cold','fixed_reserve_cold']
V3_MANIFEST_SHA=''

# Reuse only the independent mathematical helpers. They consume archived JSON
# and standard-library exact arithmetic; no project implementation is loaded.
h.base=base
h.need,h.near=need,near
h.native=compact
h.POLICY=POLICY
h.ORACLE=ORACLE
pair_min=h.exact_pair_min

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
    reference=base.scalar_min(nc)
    need(reference is not None,'independently feasible complete pricing branch')
    near(stats['incumbent'],float(reference[0]),'complete exact fleet-pricing minimum',1e-6)
    near(stats['lower_bound'],float(reference[0]),'complete exact fleet-pricing lower',1e-6)
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
    need(answer['objective']=='complete-fleet-linear',
         'saved pricing objective mode matches declared linear oracle')
    near(answer['lower'],stats['lower_bound']-1e-6,'single native lower guard',1e-12)
    near(answer['upper'],float(physical_objective)+1e-6,'replayed upper guard',1e-12)
    near(answer['gap'],answer['upper']-answer['lower'],'saved pricing gap arithmetic',1e-12)
    need(Q(answer['lower'])<=reference[0]<=Q(answer['upper']),
         'independent exact pricing minimum inside native enclosure')
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
            'complete_price_minimum':reference[0],'native_incumbent':stats['incumbent'],
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

def audit_cell(cell,blob,budget,prior=None):
    ev=blob['events'];rc=blob['receipt'];pack=blob['result'];result=pack['result'];name=cell['id']
    need(cell['pricing_oracle']==result['pricing_oracle']==ev[0]['pricing_oracle']==ORACLE,
         'explicit compact state oracle identity')
    need(result['status']==rc['status']=='certified' and rc['pass'] and pack['assessment']['pass'],'observed scientific certificate status')
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
    target=h.complete_hull(cell)
    support=[Q(a)+Q(b)*x for a,b,x in zip(cell['market']['a'],cell['market']['b'],target['load'])]
    scores=[Q(v['ops_cost'])+dot(support,list(map(Q,v['load']))) for v in target['vertices']]
    exactdual=min(scores)-h.conjugate(cell['market'],support)
    need(exactdual==target['objective'],'complete analytical hull supporting price equality')
    target.update(support_prices_exact=support,global_price_minimum=min(scores),supporting_hull_lower=exactdual)
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
            step0,check0=len(steps),len(checks);elapsed=0.0
            while True:
                ck=ev[i];need(ck['event']=='pool_polish_check' and ck['master_call']==call and ck['step']==len(steps) and ck['mixture']==current,'ordered polish check and exact current mixture')
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
                need(elapsed<=st['elapsed_s']<start['remaining_seconds'],'transfer elapsed budget');elapsed=st['elapsed_s']
                steps.append({'master_call':call,'step':st['step'],'gamma':gamma,'decrease':d,'curvature':H,'before':mix['objective'],'after':pred,'max_bits':maxbits})
                eligible.append(pred);current=st['mixture'];i+=1
            finish=ev[i];need(finish['event']=='pool_polish_finish' and finish['master_call']==call and finish['outcome']=='qualified','qualified polish phase termination')
            need(finish['steps_completed']==len(steps)-step0 and finish['checks_completed']==len(checks)-check0,'phase exact step/check accounting')
            need(elapsed<=finish['elapsed_s']<=start['remaining_seconds'],'phase end fixed time');polishwall+=finish['elapsed_s'];phases.append(finish);i+=1
            prog=ev[i];added=current['load'] not in points
            need(prog=={'event':'master_progress','call':call,'new_tangent_added':added,'repeated_raw_tangent_point':repeat,'polished_load_exact':current['load_exact']},'master progress exact history')
            if added:points.append(current['load'])
            i+=1
        else:raise AssertionError('unknown/out-of-order event '+e['event'])
    need(result['columns']==pool and len(pool)<=budget['pool_cap'],'complete final physical column pool')
    counts={'master_calls':len(masters),'pricing_requests':len(pricing),'seed_requests':sum(p['seed'] for p in pricing),'polish_steps':len(steps),'polish_checks':len(checks),'polish_wall_s':polishwall,'max_rational_bits':maxbits}
    need(result['counts']==counts,'exact complete saved counts')
    need(len(masters)<=budget['master_calls'] and len(pricing)<=budget['pricing_calls'] and len(steps)<=budget['polish_steps'] and polishwall<=budget['polish_seconds'],'all cumulative caps')
    for k,v in [('master_starts',len(masters)),('pricing_starts',len(pricing)),('pricing_requests',len(pricing)),('seed_requests',counts['seed_requests']),('native_starts',len(masters)+len(pricing)),('native_returns',len(masters)+len(pricing)),('polish_starts',len(phases)),('polish_returns',len(phases)),('polish_checks',len(checks)),('polish_steps',len(steps))]:need(rc[k]==v,'receipt '+k)
    need(rc['native_accounting_complete'] and rc['polish_accounting_complete'],'complete native and polish accounting');near(rc['native_wall_s'],math.fsum(walls),'native wall accounting',1e-12);near(rc['polish_wall_s'],polishwall,'polish wall accounting',1e-12)
    need(pack['elapsed_s']<=budget['wall_seconds'] and rc['elapsed_s']>=pack['elapsed_s'],'observed state duration within frozen deadline')
    lower=max(Q(c['lower_exact']) for c in certs);upper=min(eligible);need(result['lower_certificate'] in certs and Q(result['lower_certificate']['lower_exact'])==lower,'best fresh lower has current pricing provenance')
    fm=mixture(cell,[allcols[k] for k in result['mixture']['column_keys']],result['mixture']);need(fm['objective']==upper,'streamed best feasible UB')
    gap=upper-lower;need(0<=gap<=Q(budget['epsilon']) and result['reason'] is None and result['epsilon']==budget['epsilon'],'unchanged final certificate gate')
    need(result['lower']==h.outward(lower,False) and result['upper']==h.outward(upper,True) and Q(result['gap_exact'])==gap and result['gap']==h.outward(gap,True),'exact final interval arithmetic')
    need(lower<=target['objective']+Q(1e-10) and target['objective']<=upper+Q(1e-10),'complete fixture optimum enclosed within unchanged physical witness tolerance')
    for a,b in zip(fm['load'],target['load']):near(float(a),float(b),'known complete hull optimal load',1e-4)
    return {'cell':name,'status':'certified','complete_hull':target,'saved_interval':[lower,upper],'saved_width':gap,'final_load':fm['load'],'final_weights':fm['weights'],'imported_columns':len(ev[0]['imported_column_keys']),'counts':counts,'pricing':pricing,'masters':masters,'steps':steps,'checks':checks,'phases':phases}

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
    reject('native fallback hidden',lambda c,b,p:event(b,'master_status')['stats']['backend_runtime'].__setitem__('requested','GRB'))
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
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None));ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen repository');repo=args.repository.resolve()
    attempt=args.attempt.resolve();review_dir=attempt/'review'
    out=(args.out or review_dir/'audit-report.json').resolve()
    need(out.parent==review_dir.resolve(),'audit output must be a fresh file in this review subtree')
    need(not out.exists() and not out.is_symlink(),'exclusively new audit output path')
    started=time.perf_counter();manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'pinned original raw manifest')
    def verify_raw():
        for p,item in manifest['files'].items():
            data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'immutable raw '+p)
        actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
        need(actual==set(manifest['files']),'complete original raw manifest')
        need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'raw manifest preserved')
    verify_raw();frozen=base.read(attempt/'frozen.json');budget=frozen['budget']
    need(frozen['freeze_label']==COMMIT and frozen['protocol']=='native-pathflow-hull-qualification-20260927-v3-orphan-projection'
         and frozen['pricing_oracle']==ORACLE and frozen['extraction_policy']==POLICY,'frozen V3 protocol/oracle/policy')
    need(len(frozen['source_hashes'])==19,'complete 19-entry frozen source manifest')
    source_blob_hashes={}
    for p,sha in frozen['source_hashes'].items():
        blob=subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p])
        actual_hash=base.digest(blob);need(actual_hash==sha,'frozen Git blob source '+p)
        source_blob_hashes[p]=actual_hash
    # Deliberately do not require the live working tree to remain at COMMIT;
    # the completed run's saved source-unchanged receipt is checked below.
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==NAMES,'all eight fixed cells/order')
    # Compare against the archived original V2 compact-hull attempt. Only the
    # expected V3 oracle/policy metadata and resulting state digest may differ.
    old_path=repo/'result/native_pathflow_hull/20260927-attempt1/frozen.json'
    old_bytes=old_path.read_bytes();need(base.digest(old_bytes)==OLD_FROZEN_SHA,'archived attempt1 frozen input identity')
    old=json.loads(old_bytes)
    need(budget==old['budget'],'exact same scientific/budget controls as original attempt1')
    for c,o in zip(cells.values(),old['controls']):
        need({k:v for k,v in c.items() if k not in ('state_identity','pricing_oracle','extraction_policy')}
             =={k:v for k,v in o.items() if k not in ('state_identity','pricing_oracle','extraction_policy')},
             'all eight scientific inputs/targets unchanged')
        need(c['physical_identity']==h.digest_object({'schema':'egg-native-recharge-v1','case':c['case']}) and c['market_identity']==h.digest_object(c['market']),'complete case/market identity')
        need(c['pricing_oracle']==ORACLE and c['extraction_policy']==POLICY,'frozen per-control V3 identities')
        need(c['state_identity']==h.digest_object({'schema':h.SCHEMA,'case':c['physical_identity'],'market':c['market_identity'],
             'arm':c['arm'],'state_index':c['state_index'],'budget':budget,'extraction_policy':POLICY,
             'pricing_oracle':ORACLE}),'exact V3 state identity')
    summary=base.read(attempt/'summary.json');supervisor=base.read(attempt/'supervisor_receipt.json')
    need(summary['protocol']==frozen['protocol'] and summary['all_pass'] and summary['source_hashes_unchanged'],
         'successful controller and preserved source-unchanged receipt')
    need(supervisor['protocol']==frozen['protocol'] and supervisor['returncode']==0
         and not supervisor['outer_timeout'] and supervisor['elapsed_s']<=frozen['outer_seconds'],
         'successful bounded supervisor receipt')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json')
        need(inp['control']==cells[name] and inp['budget']==budget and inp['source_hashes']==frozen['source_hashes'],'full frozen per-cell input')
        need(receipt==base.read(folder/'receipt.json'),'saved receipt provenance')
        need(receipt['pass'] and receipt['returncode']==0 and not receipt['timeout']
             and not receipt['evidence_issues'] and receipt['elapsed_s']<=frozen['worker_seconds'],
             'bounded successful cell receipt')
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()],'receipt':receipt,'result':base.read(folder/'result.json')}
    need(list(blobs)==NAMES,'every declared state attempted')
    records=[]
    for name,c in cells.items():records.append(audit_cell(c,blobs[name],budget,blobs.get(c['predecessor'])))
    controls=corruptions(cells,blobs,budget)
    pricing=[p for r in records for p in r['pricing']];masters=[m for r in records for m in r['masters']];steps=[s for r in records for s in r['steps']]
    report={'audit_status':'PASS all eight frozen V3 compact native hull certificates and complete saved numerical evidence',
      'frozen_commit':COMMIT,'frozen_source_hashes_verified_against_git_blobs':source_blob_hashes,
      'source_unchanged_receipt':summary['source_hashes_unchanged'],
      'attempt1_frozen_sha256':OLD_FROZEN_SHA,
      'original_manifest_sha256':MANIFEST_SHA,'raw_files':len(manifest['files']),'raw_bytes':sum(x['bytes'] for x in manifest['files'].values()),
      'auditor_sources':{p.name:base.digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},
      'counts':{'cells':8,'certified':8,'pricing_calls':len(pricing),'master_calls':len(masters),'native_calls':len(pricing)+len(masters),'polish_steps':len(steps),'polish_checks':sum(len(r['checks']) for r in records),'polish_phases':sum(len(r['phases']) for r in records),
        'native_raw_variables':sum(p['raw_variables'] for p in pricing),'master_raw_variables':sum(m['raw_variables'] for m in masters),'physical_witnesses':len(pricing),'physical_sessions':sum(p['physical_witness']['sessions'] for p in pricing),'SOC_events':sum(p['physical_witness']['soc_events'] for p in pricing),'independent_PWL_master_minima':len(masters),'independent_global_pricing_minima':len(pricing)},
      'max_native_constraint_residual':max(p['max_raw_constraint_residual'] for p in pricing),'max_master_constraint_residual':max(m['raw_LP_residual'] for m in masters),'max_native_PWL_objective_error':max(abs(m['native_PWL_incumbent_minus_exact']) for m in masters),'max_combined_physical_correction':max(p['correction']['combined_correction'] for p in pricing),
      'exact_width_range':[min(r['saved_width'] for r in records),max(r['saved_width'] for r in records)],'max_rational_bits':max(r['counts']['max_rational_bits'] for r in records),'cells':records,'corruption_controls':controls,
      'scope':'No scientific implementation imports or optimizer. The V3 raw-matrix, energy-band and projection checks reuse the prior solver-free independent physical audit helpers; hull arithmetic, master and mixture reconstruction, global and pool Fenchel certificates, retained identities, receipt/accounting checks and corruption tests are recomputed here without author imports. Frozen source hashes are checked against Git blobs at the pinned commit, not the mutable working tree; the run-level source-unchanged receipt remains required. Earlier V2 attempt evidence is not reclassified.',
      'audit_wall_s':time.perf_counter()-started}
    verify_raw()
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    review_manifest={'files':{p.name:{'bytes':p.stat().st_size,'sha256':base.digest(p.read_bytes())}
        for p in sorted(HERE.glob('*.py'))},'report':{'bytes':out.stat().st_size,'sha256':base.digest(out.read_bytes())},
        'attempt_raw_manifest_sha256':MANIFEST_SHA,'scope':'Independent review artifacts only; excludes and does not alter original attempt evidence.'}
    with (HERE/'REVIEW_MANIFEST.json').open('x') as f:json.dump(review_manifest,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'status':report['audit_status'],'out':str(out),'counts':report['counts'],'corruptions_rejected':len(controls),'wall_s':report['audit_wall_s']},indent=2))

if __name__=='__main__':main()
