"""Independent exhaustive canonical-mode and field-binding check, stdlib only.

Never imports or calls the extractor, producer, native builder, or backend.
No runtime qualification is claimed by this source-only implementation.
"""
from fractions import Fraction as Q
import math
import re
import sys

OD_REVISION='6f87f052c1a6e30ffb89a984743514e0b2744aa1'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
INITIAL='every used bus starts at full usable EB-3 inventory (400 kWh)'
TERMINAL='every used bus returns to its selected depot and must restore full usable inventory by 30:00 (1800 min); terminal opening is 00:00, so all post-pull-in time is available'
WAIT_POLICY='auxiliary applies only to off-depot wait; adapter fails closed if a direct wait occurs at a source-flagged depot'
POLICIES={
 'pullout':'latest feasible: leave selected depot at service start minus directed DHD travel time',
 'direct':'leave immediately after prior service; add explicit off-depot stationary wait at next service origin',
 'depot_detour':'inbound immediately after service, outbound latest feasible to arrive at next service start; fixes the depot charging window',
 'pullin':'leave immediately after final service; recharge at selected depot through the 30:00 deadline'}
MODE_POLICIES={
 'pullout':'latest feasible: service_start minus directed source DHD time',
 'direct':'immediate after prior service; any residual time is fixed destination wait',
 'depot':'inbound immediately after service; outbound latest feasible to arrive at next service start',
 'pullin':'immediate after service; arrival defines terminal depot availability'}


def require(ok,message):
    if not ok:raise ValueError(message)


def exact(value):
    require(type(value) in (int,str),'Retained exact numeric token required')
    if isinstance(value,str):
        require(len(value)<=4096,'Numeric token ceiling')
        if 'e' in value.lower():
            match=re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)[eE]([+-]?[0-9]+)',value)
            require(len(value)<=256 and match is not None and abs(int(match.group(1)))<=1000,'Bounded exponent required')
    result=Q(value)
    require(max(result.numerator.bit_length(),result.denominator.bit_length())<=4096,'Rational size ceiling')
    return result


def binary(value):
    exact(value)
    answer=float(value);require(math.isfinite(answer),'Finite binary64 token required')
    return Q(answer)


def same(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b


def independently_check(p,claimed):
    """Separate emitted-mode audit plus exhaustive presence/absence predicates.

    Input is the agreed selected-variant projection, not an authentication
    authority. The future outer worker must bind its buffers and prior OD PASS.
    """
    checks=[];predicates=[];den={};blocked=0
    def check(label,ok,reason='field mismatch'):
        checks.append(dict(id=label,passed=bool(ok),**({} if ok else {'reason':reason})))
    try:
        require(sys.float_info.radix==2 and sys.float_info.mant_dig==53 and sys.float_info.max_exp==1024,
                'Declared binary64 provenance evaluation unavailable')
        v,d=p['variant'],p['descriptor'];rows=v['trips'];n=p['expected_services'];D=15
        expected_identity=p.get('expected_case_identity',CASE_TOKEN)
        require(expected_identity==CASE_TOKEN or isinstance(expected_identity,str) and expected_identity.startswith('SYNTHETIC_LITERAL:'),
                'Only explicit literal identity override is supported')
        require(type(n) is int and 1<=n<=37 and len(rows)==len(d['trips'])==n,'Service denominator')
        locations=p['locations'];require(isinstance(locations,list) and 1<=len(locations)<=256,'Location ceiling')
        require(all(type(x) is int for x in locations) and len(set(locations))==len(locations),'Source IDs')
        require(isinstance(p['arcs'],list) and len(p['arcs'])==len(locations)**2,'OD input denominator')
        arcs={}
        for row in p['arcs']:
            key=(row['origin_stop_id'],row['destination_stop_id'])
            require(key not in arcs and all(x in locations for x in key),'Unique known OD endpoints')
            exact(row['distance_m_source']);exact(row['time_sec_source']);arcs[key]=row
        require(set(arcs)=={(a,b) for a in locations for b in locations},'Complete transferred OD pairs')
        transfer=p['od_transfer']
        check('prior-OD-binding',transfer.get('revision')==OD_REVISION and transfer.get('source_bound_pass') is True
              and transfer.get('same_rich_input') is True,'Outer source-bound prior PASS required; booleans alone are not authentication')
        flags={}
        for stop in p['stops']:
            require(type(stop['id']) is int and stop['id'] not in flags,'Unique stop mapping')
            flag=stop['b_depot'];require(type(flag) is bool or type(flag) is int and flag in (0,1),'Depot flag type')
            flags[stop['id']]=bool(flag)
        require(set(flags)==set(locations) and flags[D],'Stop/depot universe')
        policy=p['modeling_assumptions'];h0=exact(policy['time_horizon']['start_sec']);h1=exact(policy['time_horizon']['deadline_sec'])
        check('horizon-and-terminal-access',h0==0 and h1==108000 and exact(policy['terminal_open_sec'])==0
              and list(map(exact,v['availability_horizon_sec']))==[h0,h1])
        check('departure-policy',same(policy['departure_policies'],POLICIES))
        check('parked-depot-policy',policy['depot_idle_auxiliary']=='off while parked at depot' and policy['direct_wait_policy']==WAIT_POLICY)
        check('full-inventory-policy',v['initial_inventory_policy']==INITIAL and v['terminal_policy']==TERMINAL)
        check('selected-case-identity',v['case_identity']==expected_identity and v['selected_depot_id']==D and v['selected_depot_native_place']=='P15')
        check('time-representation',v['time_representation']=='source data remains integer seconds; every native minute value is an exact integer or half-minute conversion; no rounding')
        semantics=p['source_field_semantics']
        for field,value in [('deadhead_trip_matrix.distances','m; directional matrix values retained exactly'),
                            ('deadhead_trip_matrix.times','s; directional matrix values retained exactly'),
                            ('trip_set.distance','km'),('source_service_or_deadhead_energy','not provided')]:
            check('source-units:'+field,semantics[field]==value)
        native=dict(name=v['case_name'],trips=[r['native'] for r in rows],movements=v['movement_modes'],
            resources=[v['resource_policy']],market_edges_min=v['market_edges_min'],depot=v['selected_depot_native_place'],
            max_vehicles=v['vehicle_cap'],battery_kwh=v['charging_model']['usable_battery_kwh'],reserve_kwh=v['charging_model']['reserve_kwh'],
            terminal_open_min=0,recharge_deadline_min=1800,vehicle_cost=v['cost_policy']['vehicle_cost'],
            deadhead_cost_per_min=v['cost_policy']['deadhead_cost_per_min'],efficiency=v['charging_model']['efficiency'],graph_scope='declared-movement-modes-only')
        check('every-descriptor-field',same(native,d))
        check('market-partition',list(map(exact,v['market_edges_min']))==list(map(Q,range(0,1801,60))))
        for key,value in [('start_min',0),('end_min',1800),('per_bus_kw',360),('grid_kw',360),('connectors',1)]:
            check('resource:'+key,exact(v['resource_policy'][key])==value)
        for key,value in [('usable_battery_kwh',400),('reserve_kwh',0),('efficiency',1),('per_bus_kw',360),('shared_grid_kw',360),('connectors',1)]:
            check('charging:'+key,exact(v['charging_model'][key])==value)
        check('non-source-economics',exact(v['cost_policy']['vehicle_cost'])==100 and exact(v['cost_policy']['deadhead_cost_per_min'])==0
              and v['cost_policy']['not_source_economic_data'] is True)
        energy=v['energy_model']
        check('declared-energy-coefficients',binary(energy['service_traction_kwh_per_km'])==Q(float(1.2))
              and binary(energy['deadhead_traction_kwh_per_km'])==Q(float(.96)) and binary(energy['auxiliary_kwh_per_hour'])==16
              and energy['energy_values_are_modelled_not_observed'] is True and energy['source_energy_for_services_or_deadheads'] is None)
        check('declared-energy-formulas',energy['service_energy_formula']=='1.20 * source distance km + 16 * source service duration hours'
              and energy['movement_energy_formula']=='0.96 * source deadhead distance km + 16 * source deadhead travel hours'
              and energy['off_depot_stationary_wait_formula']=='16 * explicit stationary off-depot wait hours; added as same-place direct-mode leg'
              and energy['depot_parked_auxiliary']=="assumed off per research lead's selected EGG protocol")
        def stop(place):
            require(isinstance(place,str) and re.fullmatch(r'P[0-9]+',place) is not None,'Native source-place syntax')
            value=int(place[1:]);require(value in locations and place=='P'+str(value),'Native source-place identity');return value
        trips={};source_ids=set()
        for number,row in enumerate(rows):
            t=row['native'];tid=t['id'];require(type(tid) is str and tid not in trips,'Unique native service ID')
            require(type(row['source_trip_id']) is int and row['source_trip_id'] not in source_ids,'Unique source service mapping');source_ids.add(row['source_trip_id'])
            s,e=exact(row['source_times_sec']['start']),exact(row['source_times_sec']['end'])
            require(h0<=s<e<=h1 and s.denominator==e.denominator==1 and s%30==e%30==0,'Exact service horizon/lattice')
            check('service-time:'+tid,exact(t['start_min'])*60==s and exact(t['end_min'])*60==e)
            trips[tid]=dict(start=s,end=e,origin=stop(t['start_place']),destination=stop(t['end_place']))
            traction=1.20*float(row['source_distance_km']);auxiliary=16.0*(float(e-s)/3600.0);total=traction+auxiliary
            check('service-quantity:'+tid,exact(row['source_distance_km'])>=0 and 0<=binary(t['energy_kwh'])<=400)
            record=row['model_energy'];components=record['energy_components']
            check('service-energy:'+tid,all(binary(components[k])==Q(x) for k,x in [('traction_kwh',traction),('auxiliary_kwh',auxiliary),('total_kwh',total)])
                  and binary(record['modeled_energy_kwh'])==binary(t['energy_kwh'])==Q(total)
                  and record['source_energy_kwh'] is None and row['source_energy_kwh'] is None)
            check('service-formula:'+tid,components['formula']=='1.20 kWh/km * source service distance + 16 kWh/h * source service duration')
            check('service-source-row:'+tid,record['source_excel_physical_row']==row['source_excel_physical_row']
                  and isinstance(record['source_member'],str) and record['source_member'].endswith('trip_set.xlsx'))
        modes=v['movement_modes'];provenance=v['movement_provenance'];require(len(modes)<=2*n+2*n*(n-1),'Mode count ceiling')
        den=dict(services=n,pullout=n,pullin=n,direct=n*(n-1),depot=n*(n-1),modes=len(modes),legs=sum(len(m['legs']) for m in modes))
        meta={}
        for row in provenance:require(row['movement_id'] not in meta,'Duplicate movement provenance');meta[row['movement_id']]=row
        require(len({m['id'] for m in modes})==len(modes) and set(meta)=={m['id'] for m in modes},'Complete unique provenance IDs')
        emitted={};kind_counts={k:0 for k in ('pullout','pullin','direct','depot')};waits=0
        for m in modes:
            kind,before,after=m['kind'],m['before'],m['after'];key=(kind,before,after)
            require(kind in kind_counts and key not in emitted,'Extra kind or duplicate incidence');emitted[key]=m;kind_counts[kind]+=1
            require((before is None or before in trips) and (after is None or after in trips),'Movement service endpoints')
            r=meta[m['id']];check('incidence:'+m['id'],r['kind']==kind and r['before']==before and r['after']==after)
            check('movement-policy:'+m['id'],r['departure_policy']==MODE_POLICIES[kind])
            require(len(m['legs'])==len(r['legs']) and 1<=len(m['legs'])<=2,'Leg/provenance count')
            check('split:'+m['id'],m['depot_split']==(1 if kind=='depot' else None))
            for pos,(leg,proof) in enumerate(zip(m['legs'],r['legs'])):
                a,b=stop(leg['origin']),stop(leg['destination']);s,e=exact(proof['depart_sec']),exact(proof['arrive_sec'])
                check('leg-times:'+m['id']+':'+str(pos),h0<=s<=e<=h1 and exact(leg['depart_min'])*60==s
                      and exact(leg['arrive_min'])*60==e and exact(proof['duration_sec'])==e-s
                      and proof['origin_stop_id']==a and proof['destination_stop_id']==b)
                role=proof['leg_role'];iswait=role=='off_depot_stationary_wait'
                if iswait:
                    waits+=1;check('wait-location:'+m['id'],a==b and not flags[a])
                    tr=0.0;aux=16.0*float(e-s)/3600.0
                    check('wait-source:'+m['id'],exact(proof['source_distance_m'])==0 and exact(proof['source_travel_time_sec'])==0
                          and exact(proof['source_height_difference_m'])==0 and proof['source_member'] is None)
                else:
                    arc=arcs[a,b];distance=float(arc['distance_m_source']);duration=float(arc['time_sec_source'])
                    tr=.96*(distance/1000.0);aux=16.0*duration/3600.0
                    check('travel-source:'+m['id']+':'+str(pos),exact(proof['source_distance_m'])==exact(arc['distance_m_source'])
                          and exact(proof['source_travel_time_sec'])==exact(arc['time_sec_source']) and e-s==exact(arc['time_sec_source'])
                          and exact(proof['source_height_difference_m'])==exact(arc['height_difference_m_source'])
                          and isinstance(proof['source_member'],str) and proof['source_member'].endswith('deadhead_trip_matrix.mat'))
                components=proof['modeled_energy_components'];total=tr+aux
                check('leg-energy:'+m['id']+':'+str(pos),all(binary(components[k])==Q(x) for k,x in [('traction_kwh',tr),('auxiliary_kwh',aux),('total_kwh',total)])
                      and binary(proof['modeled_energy_kwh'])==binary(leg['energy_kwh'])==Q(total) and proof['source_energy_kwh'] is None)
                formula=('16 kWh/h * explicit off-depot stationary wait; zero traction' if iswait else
                         '0.96 kWh/km * source DHD distance + 16 kWh/h * source DHD travel time')
                check('leg-energy-provenance:'+m['id']+':'+str(pos),components['formula']==formula
                      and proof['energy_status']=='modeled from declared EB-3 assumptions; no source leg energy supplied')
        def seconds(a,b):return exact(arcs[a,b]['time_sec_source'])
        def expected(kind,before,after,feasible,segments,roles):
            nonlocal blocked
            key=(kind,before,after);m=emitted.pop(key,None)
            label=kind+':'+str(before)+':'+str(after)
            if not feasible:
                check('absence:'+label,m is None,'Time-infeasible mode must be absent')
                predicates.append(dict(kind=kind,before=before,after=after,state='ABSENT_TIME_INFEASIBLE' if m is None else 'FAILED_MAPPING'));return
            if kind=='direct' and len(segments)==2 and flags[segments[-1][0]]:
                blocked+=1;check('access:'+label,False,'BLOCKED_ACCESS_POLICY: source-flagged depot wait')
            check('presence:'+label,m is not None,'Feasible canonical mode omitted')
            predicates.append(dict(kind=kind,before=before,after=after,state='PRESENT_CANONICAL' if m is not None else 'FAILED_MAPPING'))
            if m is None:return
            identifier=('pullout_D15_'+after if kind=='pullout' else 'pullin_'+before+'_D15' if kind=='pullin' else
                        'direct_'+before+'_'+after if kind=='direct' else 'depot_D15_'+before+'_'+after)
            check('canonical-id:'+label,m['id']==identifier)
            check('canonical-legs:'+label,len(m['legs'])==len(segments))
            if len(m['legs'])!=len(segments):return
            for j,(leg,(a,b,s,e),role) in enumerate(zip(m['legs'],segments,roles)):
                proof=meta[m['id']]['legs'][j]
                check('canonical-endpoints:'+label+':'+str(j),stop(leg['origin'])==a and stop(leg['destination'])==b
                      and exact(leg['depart_min'])*60==s and exact(leg['arrive_min'])*60==e and proof['leg_role']==role)
            info=meta[m['id']]
            if kind=='depot':
                check('maximal-window:'+label,info['depot_id']==D and info['depot_split_after_leg']==1
                      and exact(info['depot_dwell_start_sec'])==segments[0][3] and exact(info['depot_dwell_end_sec'])==segments[1][2]
                      and info['depot_auxiliary_load_assumption']=='off while parked at depot')
            if kind=='pullin':check('terminal-window:'+label,list(map(exact,info['terminal_charge_window_sec']))==[segments[0][3],h1])
        for tid,t in trips.items():
            out=t['start']-seconds(D,t['origin']);inside=t['end']+seconds(t['destination'],D)
            expected('pullout',None,tid,h0<=out<=t['start']<=h1,[(D,t['origin'],out,t['start'])],['deadhead_pullout'])
            expected('pullin',tid,None,h0<=t['end']<=inside<=h1,[(t['destination'],D,t['end'],inside)],['deadhead_pullin'])
        for bid,before in trips.items():
            for aid,after in trips.items():
                if bid==aid:continue
                arrival=before['end']+seconds(before['destination'],after['origin'])
                seg=[(before['destination'],after['origin'],before['end'],arrival)];roles=['deadhead_direct']
                if arrival<after['start']:seg.append((after['origin'],after['origin'],arrival,after['start']));roles.append('off_depot_stationary_wait')
                expected('direct',bid,aid,arrival<=after['start'] and arrival<=h1,seg,roles)
                inbound=before['end']+seconds(before['destination'],D);outbound=after['start']-seconds(D,after['origin'])
                expected('depot',bid,aid,inbound<=outbound<=after['start'] and h0<=before['end']<=inbound<=h1,
                    [(before['destination'],D,before['end'],inbound),(D,after['origin'],outbound,after['start'])],
                    ['deadhead_depot_inbound','deadhead_depot_outbound'])
        check('no-extra-mode',not emitted)
        check('declared-mode-counts',same(v['movement_mode_counts'],kind_counts))
        check('declared-wait-count',v['direct_off_depot_wait_mode_count']==waits and v['direct_wait_at_flagged_depot_count']==0)
        status='PASS' if all(c['passed'] for c in checks) else 'FAIL'
        agreement=isinstance(claimed,dict) and claimed.get('status')==status and same(claimed.get('denominators'),den)
        return dict(status=status if agreement else 'FAIL',independent_status=status,summary_matches=agreement,
            checks=checks,denominators=den,predicates=predicates,blocked_access_count=blocked,
            energy_path_dominance='UNKNOWN',continuous_wait_binary_bridge='UNKNOWN',physical_extension='UNATTEMPTED',
            terminal_visit_label_seam='Opening0 bound here; access for larger opportunity classes is not inferred',
            scope='Independent canonical mapping/provenance only; no triangle repeat or physical replay')
    except (ValueError,KeyError,TypeError,IndexError,OverflowError,ZeroDivisionError) as exc:
        return dict(status='UNKNOWN',independent_status='UNKNOWN',summary_matches=False,checks=checks,denominators=den,
            reason=type(exc).__name__+': '+str(exc),energy_path_dominance='UNKNOWN',continuous_wait_binary_bridge='UNKNOWN',physical_extension='UNATTEMPTED')
