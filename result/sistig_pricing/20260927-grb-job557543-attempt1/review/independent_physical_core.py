"""Independent physical replay extracted verbatim from the qualified independent audit.
No author model, optimizer or fixture-specific optimum calculations are imported.
"""
from fractions import Fraction as F
import hashlib
import json
import math
ET, TT, OT, GUARD = 1e-6, 1e-7, 1e-6, 1e-6
def need(ok, message):
    if not ok: raise AssertionError(message)


def near(a, b, message, tol=ET):
    need(math.isfinite(float(a)) and math.isfinite(float(b)) and abs(a-b) <= tol,
         f'{message}: {a!r} versus {b!r}')


def digest(data): return hashlib.sha256(data).hexdigest()


def q(x): return F(x)


def read(path): return json.loads(path.read_bytes())


def overlap(a,b,c,d): return max(0., min(b,d)-max(a,c))


def cost(a,b,loads): return sum(x*y+z*y*y/2 for x,z,y in zip(a,b,loads))


def pack(v):
    if isinstance(v,F): return {'exact_binary_rational':str(v),'value':float(v)}
    if isinstance(v,dict): return {k:pack(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [pack(x) for x in v]
    return v


def physical(cell, plan):
    c=cell['case']; modes={m['id']:m for m in c['movements']}; trips={t['id']:t for t in c['trips']}
    need(plan['case_identity']==cell['case_identity'] and plan['schema']=='egg-native-recharge-v1','plan identity')
    vs=plan['vehicles']; need(0<len(vs)<=c['max_vehicles'],'fleet cardinality')
    need(all(type(v['vehicle']) is int for v in vs) and [v['vehicle'] for v in vs]==list(range(len(vs))),'vehicle identifiers')
    owned={}; events={}; busy={}; covered=[]; ops=c['vehicle_cost']*len(vs); consumed=0.; count_soc=0
    for v in vs:
        vi=v['vehicle']; seq=v['trips']; ids=v['movements']
        need(seq and len(ids)==len(seq)+1,'nonempty complete path')
        expected=[(None,seq[0])]+list(zip(seq,seq[1:]))+[(seq[-1],None)]
        events[vi]=[]; busy[vi]=[]
        for j,(mid,pair) in enumerate(zip(ids,expected)):
            m=modes[mid]; need((m['before'],m['after'])==pair,'movement ownership')
            need(m['kind'] in (('pullout',) if j==0 else ('pullin',) if j==len(ids)-1 else ('direct','depot')),'movement kind')
            owned[(vi,mid)]=m
            for leg in m['legs']:
                events[vi].append((leg['arrive_min'],-leg['energy_kwh'],'movement'))
                busy[vi].append((leg['depart_min'],leg['arrive_min']))
                consumed+=leg['energy_kwh']; ops+=c['deadhead_cost_per_min']*(leg['arrive_min']-leg['depart_min'])
        for tid in seq:
            t=trips[tid]; events[vi].append((t['end_min'],-t['energy_kwh'],'service'))
            consumed+=t['energy_kwh']; busy[vi].append((t['start_min'],t['end_min']))
        covered+=seq
    need(sorted(covered)==sorted(trips),'exact mandatory coverage')
    loads=[0.]*(len(c['market_edges_min'])-1); sessions=plan['charges']; peak=0.
    for s in sessions:
        vi,mid=s['vehicle'],s['movement']; need((vi,mid) in owned,'charge owner')
        m=owned[(vi,mid)]; a,b,e=s['start_min'],s['end_min'],s['grid_kwh']
        need(type(s['connector']) is int and s['connector']==0,'connector identity')
        need(all(math.isfinite(z) for z in (a,b,e)) and 0<=a<b and e>0,'positive finite session')
        if m['kind']=='depot': lo,hi=m['legs'][m['depot_split']-1]['arrive_min'],m['legs'][m['depot_split']]['depart_min']
        else:
            need(m['kind']=='pullin','eligible charging mode')
            lo,hi=max(m['legs'][-1]['arrive_min'],c['terminal_open_min']),c['recharge_deadline_min']
        need(a>=lo-TT and b<=hi+TT,'native charge window')
        need(all(overlap(a,b,x,y)<=TT for x,y in busy[vi]),'charging during service/travel')
        for k,(x,y) in enumerate(zip(c['market_edges_min'],c['market_edges_min'][1:])):
            loads[k]+=e*overlap(a,b,x,y)/(b-a)
        events[vi].append((b,c['efficiency']*e,'charge'))
    # Pairwise session disjointness is independent of the author's active-set sweep.
    for i,s in enumerate(sessions):
        for t in sessions[i+1:]:
            need(overlap(s['start_min'],s['end_min'],t['start_min'],t['end_min'])==0,'strict single connector disjointness')
        duration=s['end_min']-s['start_min']; covered_time=0.
        for r in c['resources']:
            dt=overlap(s['start_min'],s['end_min'],r['start_min'],r['end_min'])
            if dt:
                need(r['connectors']==1,'charge on closed connector')
                used=s['grid_kwh']*dt/duration
                need(used<=min(r['per_bus_kw'],r['grid_kw'])*dt/60+ET,'instantaneous resource energy')
                covered_time+=dt
        near(covered_time,duration,'resource horizon coverage',TT)
        peak=max(peak,s['grid_kwh']*60/duration)
    traces=[]; worst_soc=0.
    for vi in range(len(vs)):
        soc=float(c['battery_kwh']); trace=[{'time_min':0.,'soc_kwh':soc,'kind':'initial'}]
        for at,delta,kind in sorted(events[vi],key=lambda x:(x[0],x[2]!='charge')):
            soc+=delta; worst_soc=max(worst_soc,c['reserve_kwh']-soc,soc-c['battery_kwh'])
            need(c['reserve_kwh']-ET<=soc<=c['battery_kwh']+ET,'SOC reserve/capacity')
            trace.append({'time_min':float(at),'soc_kwh':soc,'kind':kind}); count_soc+=1
        near(soc,c['battery_kwh'],'full replenishment')
        traces.append(trace)
    for saved,actual in zip(plan['load'],loads): near(saved,actual,'period grid load')
    need(len(plan['load'])==len(loads),'load length')
    need(len(plan['raw_solver_load'])==len(loads),'native load length')
    for saved,actual in zip(plan['raw_solver_load'],loads): near(saved,actual,'native load versus physical')
    near(plan['ops_cost'],ops,'intrinsic cost'); near(c['efficiency']*sum(loads),consumed,'fleet grid/battery conservation')
    saved=plan['replay']; need(saved['replay_ok'] is True,'saved replay verdict')
    for key,val in [('ops_cost',ops),('grid_kwh',sum(loads)),('consumption_kwh',consumed),('max_grid_kw',peak)]: near(saved[key],val,'saved '+key)
    need(len(saved['load'])==len(loads),'saved replay load length')
    for x,y in zip(saved['load'],loads): near(x,y,'saved replay load')
    need(len(saved['soc_trajectories'])==len(traces),'saved SOC vehicle count')
    for a,b in zip(saved['soc_trajectories'],traces):
        need(len(a)==len(b),'saved SOC event count')
        for x,y in zip(a,b):
            need(x['kind']==y['kind'],'saved SOC event kind'); near(x['time_min'],y['time_min'],'saved SOC time',TT); near(x['soc_kwh'],y['soc_kwh'],'saved SOC value')
    return {'load':loads,'ops':ops,'sessions':len(sessions),'soc_events':count_soc,'worst_soc_residual_kwh':max(0.,worst_soc),'peak_kw':peak}

