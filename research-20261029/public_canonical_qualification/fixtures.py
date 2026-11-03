"""Hand-declared synthetic schemas built ONLY inside a future paid Q0 call."""
import copy

INITIAL='every used bus starts at full usable EB-3 inventory (400 kWh)'
TERMINAL='every used bus returns to its selected depot and must restore full usable inventory by 30:00 (1800 min); terminal opening is 00:00, so all post-pull-in time is available'
WAIT='auxiliary applies only to off-depot wait; adapter fails closed if a direct wait occurs at a source-flagged depot'
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


def tokens(value):
    if isinstance(value,float):return repr(value)
    if isinstance(value,dict):return {k:tokens(v) for k,v in value.items()}
    if isinstance(value,list):return [tokens(v) for v in value]
    return value


def _build(label,services,mode_specs,expected):
    """Assemble explicit literal inputs, never call constructor or candidate.

    All distances zero; cross-depot travel900sec consumes exactly4kWh.
    Service900sec consumes exactly4kWh; each declared wait is an exact quarter
    hour multiple. Thus fixture energy anchors are hand-known binary values.
    """
    identity='SYNTHETIC_LITERAL:'+label
    arcs=[dict(origin_stop_id=a,destination_stop_id=b,distance_m_source=0.0,
               time_sec_source=0 if a==b else 900,height_difference_m_source=0.0)
          for a in (15,17) for b in (15,17)]
    records=[]
    for index,(tid,s,e,a,b) in enumerate(services):
        energy=16.0*((e-s)/3600.0)
        components=dict(traction_kwh=0.0,auxiliary_kwh=energy,total_kwh=energy,
            formula='1.20 kWh/km * source service distance + 16 kWh/h * source service duration')
        native=dict(id=tid,start_min=s/60,end_min=e/60,start_place='P'+str(a),end_place='P'+str(b),energy_kwh=energy)
        records.append(dict(native=native,source_trip_id=index+1,source_excel_physical_row=index+2,
            source_times_sec=dict(start=s,end=e),source_distance_km=0.0,source_energy_kwh=None,
            model_energy=dict(source_energy_kwh=None,modeled_energy_kwh=energy,energy_components=components,
                source_member='SYNTHETIC/trip_set.xlsx',source_excel_physical_row=index+2)))
    modes=[];provenance=[];counts=dict(pullout=0,pullin=0,direct=0,depot=0);waits=0;blocked=0
    for index,(kind,before,after,segments) in enumerate(mode_specs):
        mid=({'pullout':'pullout_D15_'+str(after),
              'pullin':'pullin_'+str(before)+'_D15',
              'direct':'direct_'+str(before)+'_'+str(after),
              'depot':'depot_D15_'+str(before)+'_'+str(after)})[kind]
        legs=[];metadata=[]
        for a,b,s,e,role in segments:
            stationary=role=='off_depot_stationary_wait';energy=16.0*(e-s)/3600.0
            components=dict(traction_kwh=0.0,auxiliary_kwh=energy,total_kwh=energy,
                formula=('16 kWh/h * explicit off-depot stationary wait; zero traction' if stationary else
                         '0.96 kWh/km * source DHD distance + 16 kWh/h * source DHD travel time'))
            legs.append(dict(origin='P'+str(a),destination='P'+str(b),depart_min=s/60,arrive_min=e/60,energy_kwh=energy))
            metadata.append(dict(origin_stop_id=a,destination_stop_id=b,depart_sec=s,arrive_sec=e,duration_sec=e-s,
                source_distance_m=0.0,source_travel_time_sec=0 if stationary else e-s,source_height_difference_m=0.0,
                source_energy_kwh=None,modeled_energy_kwh=energy,modeled_energy_components=components,leg_role=role,
                source_member=None if stationary else 'SYNTHETIC/deadhead_trip_matrix.mat',
                energy_status='modeled from declared EB-3 assumptions; no source leg energy supplied'))
            if stationary:waits+=1;blocked+=int(a==15)
        modes.append(dict(id=mid,kind=kind,before=before,after=after,legs=legs,depot_split=1 if kind=='depot' else None))
        prov=dict(movement_id=mid,kind=kind,before=before,after=after,departure_policy=MODE_POLICIES[kind],legs=metadata)
        if kind=='depot':prov.update(depot_id=15,depot_split_after_leg=1,depot_dwell_start_sec=segments[0][3],
            depot_dwell_end_sec=segments[1][2],depot_auxiliary_load_assumption='off while parked at depot')
        if kind=='pullin':prov['terminal_charge_window_sec']=[segments[-1][3],108000]
        provenance.append(prov);counts[kind]+=1
    variant=dict(case_name=label,case_identity=identity,selected_depot_id=15,selected_depot_native_place='P15',
        trips=records,movement_modes=modes,movement_provenance=provenance,movement_mode_counts=counts,
        direct_off_depot_wait_mode_count=waits,direct_wait_at_flagged_depot_count=blocked,vehicle_cap=2,
        resource_policy=dict(start_min=0,end_min=1800,per_bus_kw=360,grid_kw=360,connectors=1),
        charging_model=dict(usable_battery_kwh=400,reserve_kwh=0,efficiency=1,per_bus_kw=360,shared_grid_kw=360,connectors=1),
        cost_policy=dict(vehicle_cost=100,deadhead_cost_per_min=0,not_source_economic_data=True),
        market_edges_min=list(range(0,1801,60)),availability_horizon_sec=[0,108000],
        initial_inventory_policy=INITIAL,terminal_policy=TERMINAL,
        time_representation='source data remains integer seconds; every native minute value is an exact integer or half-minute conversion; no rounding',
        energy_model=dict(service_traction_kwh_per_km=1.2,deadhead_traction_kwh_per_km=.96,auxiliary_kwh_per_hour=16.0,
            energy_values_are_modelled_not_observed=True,source_energy_for_services_or_deadheads=None,
            service_energy_formula='1.20 * source distance km + 16 * source service duration hours',
            movement_energy_formula='0.96 * source deadhead distance km + 16 * source deadhead travel hours',
            off_depot_stationary_wait_formula='16 * explicit stationary off-depot wait hours; added as same-place direct-mode leg',
            depot_parked_auxiliary="assumed off per research lead's selected EGG protocol"))
    descriptor=dict(name=label,trips=[r['native'] for r in records],movements=modes,resources=[variant['resource_policy']],
        market_edges_min=variant['market_edges_min'],depot='P15',max_vehicles=2,battery_kwh=400,reserve_kwh=0,
        terminal_open_min=0,recharge_deadline_min=1800,vehicle_cost=100,deadhead_cost_per_min=0,efficiency=1,
        graph_scope='declared-movement-modes-only')
    document=dict(native_cases=[variant],source_data=dict(deadhead_stop_order_source=[15,17],
        deadhead_arcs_directed_row_major=arcs,stops=[dict(id=15,b_depot=True),dict(id=17,b_depot=False)]),
        source_field_semantics={'deadhead_trip_matrix.distances':'m; directional matrix values retained exactly',
            'deadhead_trip_matrix.times':'s; directional matrix values retained exactly','trip_set.distance':'km',
            'source_service_or_deadhead_energy':'not provided'},
        modeling_assumptions=dict(time_horizon=dict(start_sec=0,deadline_sec=108000),terminal_open_sec=0,
            departure_policies=POLICIES,depot_idle_auxiliary='off while parked at depot',direct_wait_policy=WAIT))
    return dict(id=label,document=tokens(document),descriptor=tokens(copy.deepcopy(descriptor)),
                expected_status=expected,expected_services=len(services),identity=identity)


def cases():
    # Every mode/time is hand-declared. Reverse T1→T0 is absent/infeasible.
    first=('T0',1800,2700,17,17)
    basic=[('pullout',None,'T0',[(15,17,900,1800,'deadhead_pullout')]),
           ('pullin','T0',None,[(17,15,2700,3600,'deadhead_pullin')])]
    one=_build('one-service',[first],basic,'PASS')
    second=('T1',6300,7200,17,17)
    gap=basic+[
        ('pullout',None,'T1',[(15,17,5400,6300,'deadhead_pullout')]),
        ('pullin','T1',None,[(17,15,7200,8100,'deadhead_pullin')]),
        ('direct','T0','T1',[(17,17,2700,2700,'deadhead_direct'),(17,17,2700,6300,'off_depot_stationary_wait')]),
        ('depot','T0','T1',[(17,15,2700,3600,'deadhead_depot_inbound'),(15,17,5400,6300,'deadhead_depot_outbound')])]
    two=_build('two-service-gap',[first,second],gap,'PASS')
    zero=basic+[
        ('pullout',None,'T1',[(15,17,3600,4500,'deadhead_pullout')]),
        ('pullin','T1',None,[(17,15,5400,6300,'deadhead_pullin')]),
        ('direct','T0','T1',[(17,17,2700,2700,'deadhead_direct'),(17,17,2700,4500,'off_depot_stationary_wait')]),
        ('depot','T0','T1',[(17,15,2700,3600,'deadhead_depot_inbound'),(15,17,3600,4500,'deadhead_depot_outbound')])]
    clipped=_build('zero-depot-gap',[first,('T1',4500,5400,17,17)],zero,'PASS')
    blocked=basic+[
        ('pullout',None,'T1',[(15,15,6300,6300,'deadhead_pullout')]),
        ('pullin','T1',None,[(17,15,7200,8100,'deadhead_pullin')]),
        ('direct','T0','T1',[(17,15,2700,3600,'deadhead_direct'),(15,15,3600,6300,'off_depot_stationary_wait')]),
        ('depot','T0','T1',[(17,15,2700,3600,'deadhead_depot_inbound'),(15,15,6300,6300,'deadhead_depot_outbound')])]
    access=_build('blocked-depot-wait',[first,('T1',6300,7200,15,17)],blocked,'FAIL')
    return [one,two,clipped,access]


def literal_qualification(extractor,producer,checker):
    transfer=dict(revision=extractor.OD_REVISION,source_bound_pass=True,same_rich_input=True,
                  scope='SYNTHETIC INTERFACE FIXTURE ONLY; NOT PUBLIC AUTHORITY')
    rows=[]
    def evaluate(fixture):
        p=extractor.project(fixture['document'],fixture['descriptor'],transfer,
            expected_services=fixture['expected_services'],expected_case_identity=fixture['identity'])
        proposed=producer.qualify(p);audit=checker.independently_check(p,proposed)
        return proposed,audit
    fixtures=cases()
    for fixture in fixtures:
        proposed,audit=evaluate(fixture);expected=fixture['expected_status']
        ok=proposed['status']==expected and audit['independent_status']==expected and audit['summary_matches'] is True
        rows.append(dict(id=fixture['id'],passed=ok,expected=expected,producer=proposed,checker=audit))
    controls=[]
    def reject(name,fixture,mutation):
        changed=copy.deepcopy(fixture);mutation(changed)
        try:
            proposed,audit=evaluate(changed)
            rejected=proposed['status']!='PASS' and audit['status']!='PASS'
        except (ValueError,KeyError,TypeError):rejected=True
        controls.append(dict(id=name,rejected=rejected))
    base=fixtures[1]
    mutations=[
        ('missing-selected-variant',lambda f:f['document'].__setitem__('native_cases',[])),
        ('duplicate-selected-variant',lambda f:f['document']['native_cases'].append(copy.deepcopy(f['document']['native_cases'][0]))),
        ('wrong-literal-identity',lambda f:f['document']['native_cases'][0].__setitem__('case_identity','WRONG')),
        ('changed-descriptor',lambda f:f['descriptor'].__setitem__('max_vehicles',3)),
        ('missing-mode',lambda f:f['document']['native_cases'][0]['movement_modes'].pop()),
        ('duplicate-mode',lambda f:f['document']['native_cases'][0]['movement_modes'].append(copy.deepcopy(f['document']['native_cases'][0]['movement_modes'][0]))),
        ('changed-service-id',lambda f:f['document']['native_cases'][0]['trips'][1]['native'].__setitem__('id','T0')),
        ('changed-depot-split',lambda f:f['document']['native_cases'][0]['movement_modes'][-1].__setitem__('depot_split',None)),
        ('swapped-service-incidence',lambda f:f['document']['native_cases'][0]['movement_modes'][4].__setitem__('after','T0')),
        ('dropped-direct-wait',lambda f:f['document']['native_cases'][0]['movement_modes'][4]['legs'].pop()),
        ('changed-departure-policy',lambda f:f['document']['native_cases'][0]['movement_provenance'][0].__setitem__('departure_policy','other')),
        ('changed-resource',lambda f:f['document']['native_cases'][0]['resource_policy'].__setitem__('grid_kw',359)),
        ('changed-terminal',lambda f:f['document']['modeling_assumptions'].__setitem__('terminal_open_sec',60)),
        ('changed-OD-provenance',lambda f:f['document']['native_cases'][0]['movement_provenance'][0]['legs'][0].__setitem__('source_distance_m','1.0')),
        ('changed-leg-energy',lambda f:f['document']['native_cases'][0]['movement_modes'][0]['legs'][0].__setitem__('energy_kwh','4.000000000000001')),
        ('changed-service-energy',lambda f:f['document']['native_cases'][0]['trips'][0]['native'].__setitem__('energy_kwh','4.000000000000001')),
        ('changed-depot-draw',lambda f:f['document']['modeling_assumptions'].__setitem__('depot_idle_auxiliary','positive')),
    ]
    for name,mutation in mutations:reject(name,base,mutation)
    for key,value in [('revision','WRONG'),('same_rich_input',False)]:
        previous=transfer[key];transfer[key]=value
        try:
            evaluate(base);rejected=False
        except (ValueError,KeyError,TypeError):rejected=True
        finally:transfer[key]=previous
        controls.append(dict(id='changed-prior-OD-'+key,rejected=rejected))
    result=dict(status='PASS' if all(r['passed'] for r in rows) and all(c['rejected'] for c in controls) else 'FAIL',
                rows=rows,fixture_count=len(rows),negative_controls=controls,negative_control_count=len(controls),native_calls=0,
                scope='Four hand-authored synthetic metadata fixtures, no public identity/authority or physical dominance claim')
    if result['status']!='PASS':raise ValueError(result)
    return result
