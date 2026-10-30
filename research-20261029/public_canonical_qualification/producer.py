"""Exhaustive canonical signature/provenance predicates; never writes modes."""
from fractions import Fraction as Q
import math


def need(ok,message):
    if not ok:raise ValueError(message)


def q(v):
    need(not isinstance(v,(bool,float)),'exact encoded JSON numeric token required')
    return Q(v)


def binary(v):
    need(not isinstance(v,(bool,float)),'retained numeric token required')
    value=float(v);need(math.isfinite(value),'finite binary64 required');return Q(value)


def same(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    if type(a) is bool or type(b) is bool:return type(a) is type(b) and a==b
    return a==b


def qualify(p):
    checks=[];n=p['expected_services'];v=p['variant'];d=p['descriptor']
    den=dict(services=n,pullout=n,pullin=n,direct=n*(n-1),depot=n*(n-1),
             modes=len(v.get('movement_modes',[])),legs=sum(len(m.get('legs',[])) for m in v.get('movement_modes',[])))
    def check(name,action):
        try:need(action(),'predicate false');checks.append(dict(id=name,passed=True))
        except Exception as exc:checks.append(dict(id=name,passed=False,reason=type(exc).__name__+': '+str(exc)))
    try:
        trips=[row['native'] for row in v['trips']];ids=[t['id'] for t in trips]
        need(len(ids)==n and len(set(ids))==n,'service IDs');lookup=dict(zip(ids,trips))
        arcs={(r['origin_stop_id'],r['destination_stop_id']):r for r in p['arcs']}
        need(len(arcs)==len(p['locations'])**2,'OD mapping')
        flags={s['id']:s['b_depot'] in (True,1) for s in p['stops']};D=15
        need(flags.get(D) is True,'selected depot flag')
        policies=p['modeling_assumptions'];h0=q(policies['time_horizon']['start_sec']);h1=q(policies['time_horizon']['deadline_sec'])
        modes=v['movement_modes'];meta=v['movement_provenance'];by={};provenance={}
        need(len({m['id'] for m in modes})==len(modes),'duplicate movement ID')
        for m in modes:
            key=(m['kind'],m['before'],m['after']);need(key not in by,'duplicate mode signature');by[key]=m
        for row in meta:need(row['movement_id'] not in provenance,'duplicate provenance ID');provenance[row['movement_id']]=row
        need(set(provenance)=={m['id'] for m in modes},'all mode provenance')
        den=dict(services=n,pullout=n,pullin=n,direct=n*(n-1),depot=n*(n-1),modes=len(modes),
                 legs=sum(len(m['legs']) for m in modes))
        # Exact rich-to-descriptor identity; original adapter's explicit boundaries.
        native=dict(name=v['case_name'],trips=trips,movements=modes,resources=[v['resource_policy']],
            market_edges_min=v['market_edges_min'],depot=v['selected_depot_native_place'],max_vehicles=v['vehicle_cap'],
            battery_kwh=v['charging_model']['usable_battery_kwh'],reserve_kwh=v['charging_model']['reserve_kwh'],
            terminal_open_min=0,recharge_deadline_min=1800,vehicle_cost=v['cost_policy']['vehicle_cost'],
            deadhead_cost_per_min=v['cost_policy']['deadhead_cost_per_min'],efficiency=v['charging_model']['efficiency'],
            graph_scope='declared-movement-modes-only')
        check('complete-descriptor-identity',lambda:same(native,d))
        check('horizon-terminal-policy',lambda:h0==0 and h1==108000 and q(policies['terminal_open_sec'])==0
              and list(map(q,v['availability_horizon_sec']))==[h0,h1])
        check('charging-resource',lambda:all(q(v['resource_policy'][k])==x for k,x in
              [('start_min',0),('end_min',1800),('per_bus_kw',360),('grid_kw',360),('connectors',1)])
              and all(q(v['charging_model'][k])==x for k,x in
              [('usable_battery_kwh',400),('reserve_kwh',0),('efficiency',1),('per_bus_kw',360),('shared_grid_kw',360)]))
        check('cost-policy',lambda:q(v['cost_policy']['vehicle_cost'])==100 and q(v['cost_policy']['deadhead_cost_per_min'])==0)
        energy=v['energy_model']
        check('energy-coefficients',lambda:binary(energy['service_traction_kwh_per_km'])==Q(float(1.2))
              and binary(energy['deadhead_traction_kwh_per_km'])==Q(float(.96)) and binary(energy['auxiliary_kwh_per_hour'])==16
              and energy['energy_values_are_modelled_not_observed'] is True)
        check('depot-wait-policy',lambda:policies['depot_idle_auxiliary']=='off while parked at depot'
              and policies['direct_wait_policy']=='auxiliary applies only to off-depot wait; adapter fails closed if a direct wait occurs at a source-flagged depot')
        check('full-inventory-policy',lambda:v['initial_inventory_policy']=='every used bus starts at full usable EB-3 inventory (400 kWh)'
              and v['terminal_policy']=='every used bus returns to its selected depot and must restore full usable inventory by 30:00 (1800 min); terminal opening is 00:00, so all post-pull-in time is available')
        def seconds(t,key):return q(t[key])*60
        def place(i):return 'P'+str(i)
        def location(s):
            need(isinstance(s,str) and s.startswith('P'),'native place mapping');value=int(s[1:]);need(value in p['locations'],'unknown place');return value
        def travel(a,b,start,end):
            arc=arcs[a,b];need(end-start==q(arc['time_sec_source']),'travel duration')
            dist=float(arc['distance_m_source']);time=float(arc['time_sec_source'])
            traction=.96*(dist/1000.0);aux=16.0*time/3600.0
            return dict(origin=place(a),destination=place(b),depart_min=start/60,arrive_min=end/60,
                        energy_kwh=Q(traction+aux)),(Q(traction),Q(aux),Q(traction+aux))
        def wait(a,start,end):
            value=Q(16.0*float(end-start)/3600.0)
            return dict(origin=place(a),destination=place(a),depart_min=start/60,arrive_min=end/60,energy_kwh=value),(Q(0),value,value)
        expected_keys=set();wait_states=[]
        def predicate(kind,before,after,feasible,legs,parts,roles):
            key=(kind,before,after);expected_keys.add(key)
            actual=by.get(key)
            if not feasible:return actual is None
            need(actual is not None,'missing time-feasible mode')
            need(actual['depot_split']==(1 if kind=='depot' else None) and len(actual['legs'])==len(legs),'leg/split shape')
            for got,expected in zip(actual['legs'],legs):
                need(set(got)==set(expected),'leg fields')
                need(all((binary(got[k])==value if k=='energy_kwh' else q(got[k])==value if k in ('depart_min','arrive_min') else got[k]==value)
                         for k,value in expected.items()),'exact canonical leg')
            prov=provenance[actual['id']]
            need((prov['kind'],prov['before'],prov['after'])==key and len(prov['legs'])==len(legs),'provenance incidence')
            policies_by_kind={
                'pullout':'latest feasible: service_start minus directed source DHD time',
                'direct':'immediate after prior service; any residual time is fixed destination wait',
                'depot':'inbound immediately after service; outbound latest feasible to arrive at next service start',
                'pullin':'immediate after service; arrival defines terminal depot availability'}
            need(prov['departure_policy']==policies_by_kind[kind],'mode departure policy')
            if kind=='depot':
                need(prov['depot_id']==D and prov['depot_split_after_leg']==1
                     and q(prov['depot_dwell_start_sec'])==legs[0]['arrive_min']*60
                     and q(prov['depot_dwell_end_sec'])==legs[1]['depart_min']*60
                     and prov['depot_auxiliary_load_assumption']=='off while parked at depot','depot gap metadata')
            if kind=='pullin':
                need(list(map(q,prov['terminal_charge_window_sec']))==[legs[-1]['arrive_min']*60,h1],
                     'terminal charging access')
            for row,leg,part,role in zip(prov['legs'],legs,parts,roles):
                need(row['leg_role']==role and q(row['depart_sec'])==leg['depart_min']*60
                     and q(row['arrive_sec'])==leg['arrive_min']*60,'provenance role/times')
                origin,destination=location(leg['origin']),location(leg['destination'])
                need(row['origin_stop_id']==origin and row['destination_stop_id']==destination
                     and q(row['duration_sec'])==(leg['arrive_min']-leg['depart_min'])*60,'provenance endpoint/duration')
                if role=='off_depot_stationary_wait':
                    need(q(row['source_distance_m'])==0 and q(row['source_travel_time_sec'])==0,'stationary source mapping')
                else:
                    need(q(row['source_distance_m'])==q(arcs[origin,destination]['distance_m_source'])
                         and q(row['source_travel_time_sec'])==q(arcs[origin,destination]['time_sec_source']),
                         'provenance OD source mapping')
                need(binary(row['modeled_energy_kwh'])==part[2],'provenance total')
                components=row['modeled_energy_components']
                need(all(binary(components[k])==x for k,x in zip(('traction_kwh','auxiliary_kwh','total_kwh'),part)),
                     'ordered binary64 energy components')
            return True
        for record in v['trips']:
            t=record['native'];tid=t['id'];s=seconds(t,'start_min');e=seconds(t,'end_min')
            def service(record=record,t=t,s=s,e=e):
                need(q(record['source_times_sec']['start'])==s and q(record['source_times_sec']['end'])==e,'service source time')
                traction=1.2*float(record['source_distance_km']);aux=16.0*(float(e-s)/3600.0)
                model=record['model_energy'];parts=model['energy_components']
                return (binary(t['energy_kwh'])==binary(model['modeled_energy_kwh'])==Q(traction+aux)
                    and all(binary(parts[k])==x for k,x in zip(('traction_kwh','auxiliary_kwh','total_kwh'),
                                                             (Q(traction),Q(aux),Q(traction+aux)))))
            check('service:'+tid,service)
            a=location(t['start_place']);z=location(t['end_place'])
            dep=s-q(arcs[D,a]['time_sec_source']);arr=e+q(arcs[z,D]['time_sec_source'])
            leg,part=travel(D,a,dep,s);check('pullout:'+tid,lambda tid=tid,leg=leg,part=part,dep=dep,s=s:
                predicate('pullout',None,tid,h0<=dep<=s<=h1,[leg],[part],['deadhead_pullout']))
            leg,part=travel(z,D,e,arr);check('pullin:'+tid,lambda tid=tid,leg=leg,part=part,e=e,arr=arr:
                predicate('pullin',tid,None,h0<=e<=arr<=h1,[leg],[part],['deadhead_pullin']))
        for before in trips:
            for after in trips:
                if before['id']==after['id']:continue
                bid,aid=before['id'],after['id'];a=location(before['end_place']);z=location(after['start_place'])
                end=seconds(before,'end_min');start=seconds(after,'start_min');arr=end+q(arcs[a,z]['time_sec_source'])
                feasible=arr<=start and arr<=h1;legs=[];parts=[];roles=[]
                if feasible:
                    leg,part=travel(a,z,end,arr);legs.append(leg);parts.append(part);roles.append('deadhead_direct')
                    if arr<start:
                        blocked=flags[z];wait_states.append(dict(before=bid,after=aid,source_depot_destination=blocked))
                        check('direct-wait-access:'+bid+':'+aid,lambda blocked=blocked:not blocked)
                        leg,part=wait(z,arr,start);legs.append(leg);parts.append(part);roles.append('off_depot_stationary_wait')
                check('direct:'+bid+':'+aid,lambda bid=bid,aid=aid,feasible=feasible,legs=legs,parts=parts,roles=roles:
                    predicate('direct',bid,aid,feasible,legs,parts,roles))
                arrival=end+q(arcs[a,D]['time_sec_source']);departure=start-q(arcs[D,z]['time_sec_source'])
                feasible=arrival<=departure<=start and h0<=end<=arrival<=h1
                legs=[];parts=[]
                if feasible:
                    for x,y,s,e in ((a,D,end,arrival),(D,z,departure,start)):
                        leg,part=travel(x,y,s,e);legs.append(leg);parts.append(part)
                check('depot:'+bid+':'+aid,lambda bid=bid,aid=aid,feasible=feasible,legs=legs,parts=parts:
                    predicate('depot',bid,aid,feasible,legs,parts,['deadhead_depot_inbound','deadhead_depot_outbound']))
        check('no-unexpected-mode',lambda:set(by)<=expected_keys)
        return dict(status='PASS' if all(c['passed'] for c in checks) else 'FAIL',checks=checks,denominators=den,
            wait_classifications=wait_states,binary64_energy_provenance_only=True,
            continuous_wait_binary_bridge='UNKNOWN',energy_path_dominance='UNKNOWN',empirical_paired_path='UNKNOWN',
            broader_opportunity_extension='UNATTEMPTED',native_calls=0)
    except Exception as exc:
        return dict(status='FAIL',checks=checks,denominators=den,reason=type(exc).__name__+': '+str(exc),
                    broader_opportunity_extension='UNATTEMPTED',native_calls=0)
