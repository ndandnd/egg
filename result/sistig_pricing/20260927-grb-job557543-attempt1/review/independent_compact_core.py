"""Independent compact raw matrix and normalization reconstruction.
Functions extracted verbatim from the independent twenty-control audit.
"""
from collections import Counter
from fractions import Fraction as Q
import math
import independent_physical_core as base
POLICY='native-roundoff-qualification-v2'
TOL=Q(1e-8)
need,near=base.need,base.near
def value_record(entry):
    value=entry['value']; representation=entry['repr']
    if value is None:
        need(representation in ('inf','-inf','None','nan'),'unknown absent numeric representation')
        return None
    need(math.isfinite(value) and float(representation)==value,'raw numeric representation')
    return Q(value)


def intervals(case):
    windows={}
    for m in case['movements']:
        if m['kind']=='depot': windows[m['id']]=(m['legs'][m['depot_split']-1]['arrive_min'],m['legs'][m['depot_split']]['depart_min'])
        elif m['kind']=='pullin': windows[m['id']]=(max(m['legs'][-1]['arrive_min'],case['terminal_open_min']),case['recharge_deadline_min'])
    edges=set(case['market_edges_min'])|{case['terminal_open_min']}
    for r in case['resources']: edges|={r['start_min'],r['end_min']}
    for a,b in windows.values(): edges|={a,b}
    out=[]
    for a,b in zip(sorted(edges),sorted(edges)[1:]):
        resource=next(r for r in case['resources'] if r['start_min']<=a and b<=r['end_min'])
        period=next(k for k,(x,y) in enumerate(zip(case['market_edges_min'],case['market_edges_min'][1:])) if x<=a and b<=y)
        rate=min(resource['per_bus_kw'],resource['grid_kw']) if resource['connectors'] else 0.
        out.append({'start':a,'end':b,'hours':(b-a)/60,'period':period,'rate_kw':rate,'visits':[mid for mid,(x,y) in windows.items() if x<=a and b<=y]})
    return out


def raw_primal(cell,start,stats,snapshot):
    case=cell['case'];trips=case['trips'];modes=case['movements'];mp=snapshot['mapping'];records=snapshot['variables']
    need(snapshot['case_identity']==cell['case_identity'] and snapshot['extraction_policy']==POLICY,'raw snapshot identity/policy')
    need(snapshot['formulation']=='egg-native-pathflow-v1','compact raw formulation identity')
    need([r['index'] for r in records]==list(range(len(records))) and len(records)==stats['n_vars'],'complete raw indices')
    need(mp['trip_ids']==[t['id'] for t in trips] and mp['movement_ids']==[m['id'] for m in modes],'semantic IDs')
    grid=intervals(case);need(mp['intervals']==grid,'independent elementary intervals')
    vals={r['index']:value_record(r['solution']) for r in records};need(all(v is not None for v in vals.values()),'finite raw incumbent')
    N,M,T=len(trips),len(modes),len(case['market_edges_min'])-1
    for key,size in [('movement_selection',M),('soc_before',N),('soc_after',N),('market_load',T)]:need(len(mp[key])==size,'flat mapping shape '+key)
    allidx=sum((mp[k] for k in ['movement_selection','soc_before','soc_after','market_load','epigraph']),[])+[r['variable'] for r in mp['grid_energy']]
    need(len(allidx)==len(set(allidx))==len(records) and set(allidx)==set(vals),'complete unique flat variable mapping')
    violations=[];constraints=Counter()
    def le(a,b,tag):
        v=max(Q(0),a-b);violations.append(v);constraints[tag]+=1
        need(v<=TOL,'compact '+tag+' residual '+str(float(v)))
    def eq(a,b,tag):le(a,b,tag);le(b,a,tag)
    def declared(idx,kind,lo,hi=None):
        r=records[idx];need(r['type']==kind,'raw type')
        lower,upper=value_record(r['lower']),value_record(r['upper']);need(lower==Q(lo),'raw declared lower')
        if hi is not None:need(upper==Q(hi),'raw declared upper')
        if lower is not None:le(lower,vals[idx],'variable lower')
        if upper is not None:le(vals[idx],upper,'variable upper')
        if kind=='B':need(min(abs(vals[idx]),abs(vals[idx]-1))<=TOL,'binary integrality')
    B,r,eta=Q(case['battery_kwh']),Q(case['reserve_kwh']),Q(case['efficiency'])
    x=[vals[i] for i in mp['movement_selection']];sb=[vals[i] for i in mp['soc_before']];sa=[vals[i] for i in mp['soc_after']]
    for idx in mp['movement_selection']:declared(idx,'B',0,1)
    for idx in mp['soc_before']+mp['soc_after']:declared(idx,'C',r,B)
    raw={tuple(z['key']):vals[z['variable']] for z in mp['grid_energy']};indices={tuple(z['key']):z['variable'] for z in mp['grid_energy']}
    need(len(raw)==len(mp['grid_energy']),'unique compact energy keys')
    expected={(j,k) for k,g in enumerate(grid) for j,m in enumerate(modes) if m['id'] in g['visits'] and g['rate_kw']>0}
    need(set(raw)==expected,'complete flat eligible energy variables')
    for (j,k),e in raw.items():
        cap=Q(grid[k]['rate_kw']*grid[k]['hours']);declared(indices[j,k],'C',0,cap);le(e,cap*x[j],'owned energy activation')
    for k,g in enumerate(grid):le(sum(e for (j,kk),e in raw.items() if kk==k),Q(g['rate_kw']*g['hours']),'shared interval capacity')
    starts=sum(x[j] for j,m in enumerate(modes) if m['kind']=='pullout');ends=sum(x[j] for j,m in enumerate(modes) if m['kind']=='pullin')
    le(starts,Q(case['max_vehicles']),'fleet path cap');eq(starts,ends,'start end count')
    tid={t['id']:i for i,t in enumerate(trips)}
    for i,t in enumerate(trips):
        eq(sum(x[j] for j,m in enumerate(modes) if m['after']==t['id']),Q(1),'incoming flow')
        eq(sum(x[j] for j,m in enumerate(modes) if m['before']==t['id']),Q(1),'outgoing flow')
        eq(sa[i],sb[i]-Q(t['energy_kwh']),'service SOC')
    for j,m in enumerate(modes):
        e=Q(sum(l['energy_kwh'] for l in m['legs']));big=B+e;selected=x[j];charge=sum(z for (jj,k),z in raw.items() if jj==j)
        if m['kind']=='pullout':res=sb[tid[m['after']]]-(B-e)
        elif m['kind']=='direct':res=sb[tid[m['after']]]-sa[tid[m['before']]]+e
        elif m['kind']=='depot':
            incoming=Q(sum(l['energy_kwh'] for l in m['legs'][:m['depot_split']]));arr=sa[tid[m['before']]]-incoming
            le(r-big*(1-selected),arr,'depot arrival reserve');le(arr+eta*charge,B+big*(1-selected),'depot battery capacity')
            res=sb[tid[m['after']]]-sa[tid[m['before']]]+e-eta*charge
        else:
            arr=sa[tid[m['before']]]-e;le(r-big*(1-selected),arr,'terminal arrival reserve');res=arr+eta*charge-B
        le(res,big*(1-selected),'movement SOC upper');le(-res,big*(1-selected),'movement SOC lower')
    loads=[vals[i] for i in mp['market_load']]
    for t,idx in enumerate(mp['market_load']):
        declared(idx,'C',0);eq(loads[t],sum(z for (j,k),z in raw.items() if grid[k]['period']==t),'market energy sum')
    base_rows=2+3*N+len(raw)+len(grid)+2*M+sum(2 if m['kind']=='depot' else 1 if m['kind']=='pullin' else 0 for m in modes)+T
    need(stats['physical_constraints']==base_rows,'complete compact physical row count')
    need(stats['n_int']==M,'compact integer dimension')
    need(stats['n_vars']==M+2*N+len(raw)+T+len(mp['epigraph']),'compact variable dimension')
    ops=Q(case['vehicle_cost'])*starts+Q(case['deadhead_cost_per_min'])*sum(x[j]*sum(Q(l['arrive_min'])-Q(l['depart_min']) for l in m['legs']) for j,m in enumerate(modes))
    if cell['objective']=='pricing':
        need(not mp['epigraph'],'pricing has no epigraph');objective=ops+sum(Q(p)*L for p,L in zip(cell['prices'],loads));expected_rows=base_rows
    else:
        need(len(mp['epigraph'])==T,'planner epigraph shape');expected_rows=base_rows+sum(len(row) for row in start['tangents'])
        for t,idx in enumerate(mp['epigraph']):
            rr=records[idx];need(rr['type']=='C' and value_record(rr['lower'])<-Q(10)**100,'free-below epigraph')
            for slope,intercept in start['tangents'][t]:le(Q(slope)*loads[t]+Q(intercept),vals[idx],'saved tangent row')
        objective=ops+sum(vals[i] for i in mp['epigraph'])
    need(stats['n_constraints']==expected_rows,'complete native row count including objective')
    near(float(objective),stats['incumbent'],'raw compact objective',1e-6)
    # Independent path traversal from the flat selected graph, without author helpers.
    chosen=[m for j,m in enumerate(modes) if x[j]>Q(1,2)];owners={};paths=[];covered=[]
    for first in [m for m in chosen if m['kind']=='pullout']:
        vi=len(paths);m=first;seq=[];path=[]
        while True:
            need(m['id'] not in owners,'no repeated/merged selected mode');owners[m['id']]=vi;path.append(m['id'])
            if m['after'] is None:need(m['kind']=='pullin','path ends at terminal');break
            t=m['after'];need(t not in covered,'unique selected service ownership');covered.append(t);seq.append(t)
            nxt=[n for n in chosen if n['before']==t];need(len(nxt)==1,'unique successor');m=nxt[0]
        paths.append({'vehicle':vi,'trips':seq,'movements':path})
    need(set(owners)=={m['id'] for m in chosen} and sorted(covered)==sorted(tid),'complete selected path partition')
    need(0<len(paths)<=case['max_vehicles'],'derived used fleet cap')
    return {'variables':len(records),'raw_objective':objective,'max_constraint_residual':max(violations,default=Q(0)),
            'constraint_checks':dict(constraints),'raw_energy':raw,'x':x,'grid':grid,'native_load':loads,
            'owners':owners,'paths':paths}


def conversion(cell,raw,norm,decoded,obj,plan,start,stats):
    case=cell['case']; grid=raw['grid']; modes=case['movements']; raw_energy=raw['raw_energy']
    need(plan['vehicles']==raw['paths'],'flat selection to independent path ownership')
    need(plan['formulation']=='egg-native-pathflow-v1','plan formulation identity')
    need(norm['policy']==decoded['policy']==POLICY and norm['accepted'] is True,'normalization policy/acceptance')
    need(norm['budget_kwh']==decoded['budget_kwh']==1e-8,'fixed combined budget')
    negatives={key:e for key,e in raw_energy.items() if e<0}; total=-sum(negatives.values(),Q(0))
    need(Q(norm['negative_l1_exact'])==total and norm['negative_l1_kwh']==float(total),'negative exact L1 ledger')
    listed={tuple(x['key']):Q(x['before_kwh']) for x in norm['negative_to_zero']}
    need(listed==negatives and len(listed)==len(norm['negative_to_zero']) and all(x['after_kwh']==0 for x in norm['negative_to_zero']),'exact negative correction list')
    need(total<=TOL,'whole-incumbent negative budget')
    owners=raw['owners']
    normalized={key:max(Q(0),e) for key,e in raw_energy.items()}
    expected=[]; details=[]; session_excess=Q(0); interval_excess=Q(0)
    for k,g in enumerate(grid):
        rows=[]
        for (j,kk),e in normalized.items():
            if kk==k and e>0:
                need(modes[j]['id'] in owners and raw['x'][j]>Q(1,2),'every positive belongs to a selected used mode')
                rows.append((owners[modes[j]['id']],modes[j]['id'],e))
        if not rows: continue
        rows.sort(); E=sum(e for _,_,e in rows); capacity=Q(g['rate_kw'])*(g['end']-g['start'])/60
        excess=max(Q(0),E-capacity); interval_excess+=excess; prefix=Q(0); a=float(g['start'])
        for i,(v,mid,e) in enumerate(rows):
            prefix+=e; b=float(g['end']) if i==len(rows)-1 else float(Q(g['start'])+Q(g['end']-g['start'])*prefix/E)
            need(a<b<=g['end'],'positive representable contained session')
            cap=Q(g['rate_kw'])*(Q(b)-Q(a))/60; session_excess+=max(Q(0),e-cap)
            expected.append({'vehicle':v,'movement':mid,'connector':0,'start_min':a,'end_min':b,'grid_kwh':float(e)}); a=b
        details.append({'interval':k,'start_min':g['start'],'end_min':g['end'],'grid_kwh':float(E),'capacity_kwh':float(capacity),'capacity_excess_kwh':float(excess),'capacity_excess_exact':str(excess),'saturated_roundoff_adjustment':excess>0})
    need(decoded['endpoint_rule']=='exact-energy-proportional-full-interval' and decoded['charges']==expected==plan['charges'],'exact retained energies and emitted endpoints')
    need(decoded['intervals']==details,'interval correction ledger')
    for key,exact in [('capacity_excess',interval_excess),('materialized_session_excess',session_excess),('combined_roundoff',total+session_excess)]:
        need(Q(decoded[key+'_exact'])==exact and decoded[key+'_kwh']==float(exact),'exact '+key+' ledger')
    need(total+session_excess<=TOL and total+interval_excess<=TOL,'combined fleet correction budget')
    need(plan['roundoff']['negative_correction']=={k:v for k,v in norm.items() if k not in ('event','round')},'plan normalization ledger')
    need(plan['roundoff']['serial_decoding']=={k:v for k,v in decoded.items() if k not in ('event','round','charges')},'plan decoding ledger')
    old=[sum(e for (j,k),e in raw_energy.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
    new=[sum(e for (j,k),e in normalized.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
    for t,(a,b) in enumerate(zip(old,new)):
        near(plan['raw_charge_load'][t],float(a),'raw charge period sum',1e-12); near(plan['load'][t],float(b),'normalized period sum',1e-12)
        near(plan['roundoff']['load_delta_kwh'][t],plan['load'][t]-plan['raw_charge_load'][t],'load delta ledger',1e-15)
    if cell['objective']=='pricing':
        exact_delta=sum(Q(p)*(b-a) for p,a,b in zip(cell['prices'],old,new))
        near(obj['charge_correction_objective_delta'],float(exact_delta),'linear correction objective delta',1e-12)
        near(obj['linear_objective'],plan['ops_cost']+sum(p*x for p,x in zip(cell['prices'],plan['load'])),'objective event pricing')
    else:
        def envelope(load): return sum(max(Q(m)*x+Q(z) for m,z in row) for row,x in zip(start['tangents'],load))
        exact_delta=envelope(new)-envelope(old)
        true_delta=sum(Q(a)*(y-x)+Q(b)*(y*y-x*x)/2 for a,b,x,y in zip(cell['a'],cell['b'],old,new))
        near(obj['pwl_charge_correction_delta'],float(exact_delta),'PWL correction objective delta',1e-12)
        near(obj['true_charge_correction_delta'],float(true_delta),'true correction objective delta',1e-12)
        near(obj['pwl_objective'],plan['ops_cost']+float(envelope(new)),'objective event PWL')
        near(obj['true_cost'],plan['ops_cost']+base.cost(cell['a'],cell['b'],plan['load']),'objective event true cost')
    near(obj['native_incumbent'],stats['incumbent'],'objective event native incumbent')
    return {'negative_variables':len(negatives),'negative_l1':total,'interval_capacity_excess':interval_excess,
            'materialized_session_capacity_excess':session_excess,'combined_correction':total+session_excess,
            'charge_correction_objective_delta':exact_delta,'positive_sessions_retained':len(expected)}

