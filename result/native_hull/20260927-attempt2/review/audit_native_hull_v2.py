#!/usr/bin/env python3
"""Independent solver-free reconstruction of frozen native-hull attempt 2.

Only Python standard library and colocated independent audit helpers are used.
No author module is imported; no native model or optimizer is instantiated.
"""
import argparse,copy,hashlib,itertools,json,math,subprocess,tempfile,time,uuid
from fractions import Fraction as Q
from pathlib import Path
import independent_hull_core as h
base=h.base
need,near=base.need,base.near
HERE=Path(__file__).resolve().parent
COMMIT='186c9876805d5096632786c5504f507847a5201f'
MANIFEST_SHA='e1d8c201516d7a0be3edcfc866e92bab475d5daba918b80e9570631e96717e36'
NAMES=['nominal_cold_s0','nominal_cold_s1','nominal_cold_s2','nominal_retained_s0','nominal_retained_s1','nominal_retained_s2','joint_cold','fixed_reserve_cold']
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
    need(result['status']==rc['status']=='certified' and rc['pass'] and pack['assessment']['pass'],'observed scientific certificate status')
    need(rc['cell']==name and rc['returncode']==0 and not rc['timeout'] and rc['evidence_issues']==[],'cell exit/evidence provenance')
    need(ev[0]['event']=='state_start' and ev[-1]['event']=='state_finish' and ev[-1]['result']==result,'complete state lifecycle')
    for k in ('state_identity','market_identity'):need(ev[0][k]==cell[k] and result[k]==cell[k],'state identity '+k)
    need(result['physical_identity']==cell['physical_identity'] and result['schema']==h.SCHEMA and result['extraction_policy']==h.POLICY,'final physical/schema policy')
    need(result['arm']==cell['arm'] and result['state_index']==cell['state_index'],'arm/index')
    need(ev[0]['fresh_bounds'] is True,'fresh state bounds')
    if cell['predecessor']:
        need(prior is not None and prior['receipt']['pass'] and prior['receipt']['returncode']==0 and not prior['receipt']['timeout'] and not prior['receipt']['evidence_issues'],'admitted predecessor receipt')
        pe=prior['events'];pr=prior['receipt']
        ns=sum(e['event']=='master_start' or e['event']=='pricing_native' and e['detail']['event']=='native_start' for e in pe)
        nr=sum(e['event']=='master_status' or e['event']=='pricing_native' and e['detail']['event']=='native_status' for e in pe)
        need(pr['native_accounting_complete'] and pr['polish_accounting_complete'] and ns==nr==pr['native_starts']==pr['native_returns'] and ns>0,'independent nonzero predecessor native accounting')
        prev=prior['result']['result']
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
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None));ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen repository');repo=args.repository.resolve()
    out=args.out or Path(tempfile.gettempdir())/('egg-native-hull-v2-independent-'+uuid.uuid4().hex+'.json');resolved=out.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'report output outside any detected repository')
    need(not out.exists() and not out.is_symlink(),'exclusively new output path')
    started=time.perf_counter();attempt=args.attempt.resolve();manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA and manifest['source_commit']==COMMIT,'pinned raw manifest and scientific freeze')
    def verify_raw():
        for p,item in manifest['files'].items():
            data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'immutable raw '+p)
        actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
        need(actual==set(manifest['files']),'complete original raw manifest')
        need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'raw manifest preserved')
    verify_raw();frozen=base.read(attempt/'frozen.json');budget=frozen['budget']
    need(frozen['freeze_label']==COMMIT and frozen['protocol']=='native-hull-qualification-20260927-v2','frozen V2 protocol')
    for p,sha in frozen['source_hashes'].items():need(base.digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen source '+p)
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==NAMES,'all eight fixed cells/order')
    # Definitions remain precisely V1 apart from versioned state identities and
    # three additional prospective polishing caps. No target-specific changes.
    old=json.loads(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':result/native_hull/20260927-attempt1/frozen.json']))
    need({k:v for k,v in budget.items() if k not in ('polish_steps','polish_seconds','rational_bits')}==old['budget'],'unchanged original scientific caps')
    need((budget['polish_steps'],budget['polish_seconds'],budget['rational_bits'])==(256,5.,8192),'three fixed polishing caps')
    for c,o in zip(cells.values(),old['controls']):
        need({k:v for k,v in c.items() if k!='state_identity'}=={k:v for k,v in o.items() if k!='state_identity'},'all eight scientific definitions unchanged')
        need(c['physical_identity']==h.digest_object({'schema':'egg-native-recharge-v1','case':c['case']}) and c['market_identity']==h.digest_object(c['market']),'complete case/market identity')
        need(c['state_identity']==h.digest_object({'schema':h.SCHEMA,'case':c['physical_identity'],'market':c['market_identity'],'arm':c['arm'],'state_index':c['state_index'],'budget':budget,'extraction_policy':h.POLICY}),'exact state identity')
    summary=base.read(attempt/'summary.json');supervisor=base.read(attempt/'supervisor_receipt.json')
    need(summary['all_pass'] and summary['source_hashes_unchanged'] and supervisor['returncode']==0 and not supervisor['outer_timeout'],'successful unchanged complete controller/supervisor')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json')
        need(inp['control']==cells[name] and inp['budget']==budget and inp['source_hashes']==frozen['source_hashes'],'full frozen per-cell input')
        need(receipt==base.read(folder/'receipt.json'),'saved receipt provenance')
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()],'receipt':receipt,'result':base.read(folder/'result.json')}
    need(list(blobs)==NAMES,'every declared state attempted')
    records=[]
    for name,c in cells.items():records.append(audit_cell(c,blobs[name],budget,blobs.get(c['predecessor'])))
    controls=corruptions(cells,blobs,budget)
    pricing=[p for r in records for p in r['pricing']];masters=[m for r in records for m in r['masters']];steps=[s for r in records for s in r['steps']]
    report={'audit_status':'PASS all eight frozen V2 native hull certificates and complete saved numerical evidence',
      'frozen_commit':COMMIT,'original_manifest_sha256':MANIFEST_SHA,'raw_files':len(manifest['files']),'raw_bytes':sum(x['bytes'] for x in manifest['files'].values()),
      'auditor_sources':{p.name:base.digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},
      'counts':{'cells':8,'certified':8,'pricing_calls':len(pricing),'master_calls':len(masters),'native_calls':len(pricing)+len(masters),'polish_steps':len(steps),'polish_checks':sum(len(r['checks']) for r in records),'polish_phases':sum(len(r['phases']) for r in records),
        'native_raw_variables':sum(p['raw_variables'] for p in pricing),'master_raw_variables':sum(m['raw_variables'] for m in masters),'physical_witnesses':len(pricing),'physical_sessions':sum(p['physical_witness']['sessions'] for p in pricing),'SOC_events':sum(p['physical_witness']['soc_events'] for p in pricing),'independent_PWL_master_minima':len(masters),'independent_global_pricing_minima':len(pricing)},
      'max_native_constraint_residual':max(p['max_raw_constraint_residual'] for p in pricing),'max_master_constraint_residual':max(m['raw_LP_residual'] for m in masters),'max_native_PWL_objective_error':max(abs(m['native_PWL_incumbent_minus_exact']) for m in masters),'max_combined_physical_correction':max(p['correction']['combined_correction'] for p in pricing),
      'exact_width_range':[min(r['saved_width'] for r in records),max(r['saved_width'] for r in records)],'max_rational_bits':max(r['counts']['max_rational_bits'] for r in records),'cells':records,'corruption_controls':controls,
      'scope':'No author imports or optimizer. Complete saved raw pricing/LP primals, physical witnesses, exact one/two/three-column LP minima and restricted quadratic minima, complete analytical two-trip pricing/hull references, exact simplex transfers and serialized-price Fenchel arithmetic; unchanged tolerance-conditional physical evidence. Earlier failed attempt is not reclassified.',
      'audit_wall_s':time.perf_counter()-started}
    verify_raw()
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps({'status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'corruptions_rejected':len(controls),'wall_s':report['audit_wall_s']},indent=2))

if __name__=='__main__':main()
