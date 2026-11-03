"""ONE complete synthetic target/ledger interface fixture, future paid Q0 only."""
import copy
from fractions import Fraction as Q


def fixture():
    identity='SYNTHETIC_LITERAL:exact-target-one-service'
    trip=dict(id='T0',start_min=30,end_min=45,start_place='P17',end_place='P17',energy_kwh=5.5)
    out=dict(id='pullout_D15_T0',kind='pullout',before=None,after='T0',depot_split=None,
        legs=[dict(origin='P15',destination='P17',depart_min=15,arrive_min=30,energy_kwh=5.2)])
    incoming=dict(id='pullin_T0_D15',kind='pullin',before='T0',after=None,depot_split=None,
        legs=[dict(origin='P17',destination='P15',depart_min=45,arrive_min=60,energy_kwh=5.2)])
    original=dict(name='synthetic-exact-target',trips=[trip],movements=[out,incoming],
        resources=[dict(start_min=0,end_min=1800,per_bus_kw=360,grid_kw=360,connectors=1)],
        market_edges_min=list(range(0,1801,60)),depot='P15',max_vehicles=2,battery_kwh=400,
        reserve_kwh=0,terminal_open_min=0,recharge_deadline_min=1800,vehicle_cost=100,
        deadhead_cost_per_min=0,efficiency=1,graph_scope='declared-movement-modes-only')
    def native_tokens(value):
        if type(value) is float:return repr(value)
        if isinstance(value,dict):return {k:native_tokens(v) for k,v in value.items()}
        if isinstance(value,list):return [native_tokens(v) for v in value]
        return value
    selected=dict(selected_depot_id=15,case_identity=identity,
        trips=[dict(native=native_tokens(trip),source_times_sec=dict(start=1800,end=2700),source_distance_km='1.25')],
        movement_modes=native_tokens([out,incoming]),movement_provenance=[
            dict(movement_id='pullout_D15_T0',legs=[dict(leg_role='deadhead_pullout',origin_stop_id=15,
                destination_stop_id=17,depart_sec=900,arrive_sec=1800,duration_sec=900)]),
            dict(movement_id='pullin_T0_D15',legs=[dict(leg_role='deadhead_pullin',origin_stop_id=17,
                destination_stop_id=15,depart_sec=2700,arrive_sec=3600,duration_sec=900)])])
    document=dict(native_cases=[selected],source_data=dict(deadhead_stop_order_source=[15,17],
        deadhead_arcs_directed_row_major=[dict(origin_stop_id=a,destination_stop_id=b,
            distance_m_source='0.0' if a==b else '1250.0',time_sec_source=0 if a==b else 900)
            for a in (15,17) for b in (15,17)]))
    return document,original,identity


def full_interface_qualification(target,semantics,checker,original_reconstruct,project_selected):
    """No old/public matrix or certificate is used; all admission here is MOCK."""
    rows=[];document,original,identity=fixture()
    transfer=dict(revision=target.CANONICAL_REVISION,source_bound_pass=True,same_rich_input=True,
        same_descriptor=True,blocked_depot_wait_count=0,time_predicates_complete=True,mode_count=2,
        scope='MOCK SYNTHETIC FIXTURE; NO PUBLIC AUTHORITY')
    projected=project_selected(document)
    record=target.transform(projected,original,transfer,expected_counts=(1,2),old_identity=identity)
    source_objects=(projected,original,record);seals=tuple(checker.seal(x) for x in source_objects)
    def admitted(a,b,c):
        return all(x is y for x,y in zip((a,b,c),source_objects)) and tuple(checker.seal(x) for x in source_objects)==seals
    valid=checker.validate_semantics(projected,original,record,original_reconstruct,semantics._reconstruct,admitted)
    if not(valid['status']=='VALIDATED_TARGET_SEMANTICS' and record['case']['trips'][0]['energy_kwh']=='11/2'
           and all(m['legs'][0]['energy_kwh']=='26/5' for m in record['case']['movements']) and len(valid['ledger'])==6):
        raise ValueError('complete synthetic target/ledger anchor failed')
    rows.append(dict(id='complete-one-service-target-ledger',passed=True,services=1,modes=2,
                     exact_service='11/2',exact_travel='26/5'))
    controls=[]
    # Mutated records are admitted as synthetic test input, so the NEW checker
    # must reject their mathematical inconsistency rather than only identity.
    for name,mutation in (
        ('changed-target-energy',lambda r:r['case']['trips'][0].__setitem__('energy_kwh','6')),
        ('changed-nonenergy',lambda r:r['case'].__setitem__('max_vehicles',3)),
        ('changed-target-identity',lambda r:r.__setitem__('identity',identity+'::WRONG')),
        ('missing-mode',lambda r:r['case']['movements'].pop()),
    ):
        changed=copy.deepcopy(record);mutation(changed);snapshot=checker.seal(changed)
        def mock_admit(a,b,c):
            return a is projected and b is original and c is changed and checker.seal(changed)==snapshot
        try:checker.validate_semantics(projected,original,changed,original_reconstruct,semantics._reconstruct,mock_admit)
        except (ValueError,KeyError,TypeError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('synthetic corruption accepted: '+name)
    class OpaqueUnselected(dict):
        def __getitem__(self,key):
            if key=='selected_depot_id':return 16
            raise ValueError('unselected contents accessed')
        def __iter__(self):raise ValueError('unselected variant traversed')
        def items(self):raise ValueError('unselected items accessed')
        def keys(self):raise ValueError('unselected keys accessed')
        def values(self):raise ValueError('unselected values accessed')
        def __deepcopy__(self,memo):raise ValueError('unselected contents copied')
        def __reduce_ex__(self,protocol):raise ValueError('unselected contents serialized')
    with_opaque=dict(document);with_opaque['native_cases']=[OpaqueUnselected(),document['native_cases'][0]]
    narrowed=project_selected(with_opaque)
    if checker.seal(narrowed)!=checker.seal(projected):raise ValueError('opaque projection changed selected input')
    controls.append(dict(id='opaque-unselected-projection-not-traversed',passed=True))
    return dict(status='PASS',anchors=rows,controls=controls,native_calls=0,public_inputs_read=False,
        scope='ONE complete hand-authored synthetic target+old/new-six-tuple interface; MOCK source authority only')
