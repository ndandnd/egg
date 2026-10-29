"""New exact-consumption transformation; source-only until separately frozen."""
import copy
from fractions import Fraction as Q
import re

OLD_ID='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
TARGET_ID=OLD_ID+'::exact-consumption-v1'
CANONICAL_REVISION='76c83d55fe2983138da7b87f9d4d7c5fd36e9573'
POLICY=dict(service_distance_kwh_per_km='6/5',travel_distance_kwh_per_m='24/25000',
            elapsed_seconds_kwh='1/225',distance_semantics='exact encoded JSON decimal',
            supply_semantics='unchanged original binary-stored a=.2,b=1/900',
            parked_depot_draw='0',version='exact-consumption-v1')


def need(ok,message):
    if not ok:raise ValueError(message)


def decimal(value):
    need(type(value) is int or isinstance(value,str),'source JSON decimal token required, no bool/float')
    if isinstance(value,str):
        need(len(value)<=256 and re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',value),
             'finite source decimal syntax')
        exponent=re.search(r'[eE]([+-]?[0-9]+)',value)
        need(exponent is None or abs(int(exponent.group(1)))<=1000,'source exponent bound')
    result=Q(value);need(result.numerator.bit_length()<=4096 and result.denominator.bit_length()<=4096,'source numeric size')
    return result


def binary_source(value):
    need(type(value) in (int,float),'original descriptor must preserve binary numeric fields')
    return Q(value)


def service_energy(distance_km,duration_seconds):
    distance,duration=decimal(distance_km),decimal(duration_seconds)
    need(distance>=0 and duration>0,'service distance/duration')
    return Q(6,5)*distance+duration/225


def travel_energy(distance_m,duration_seconds):
    distance,duration=decimal(distance_m),decimal(duration_seconds)
    need(distance>=0 and duration>=0,'travel distance/duration')
    return Q(24,25000)*distance+duration/225


def wait_energy(duration_seconds):
    duration=decimal(duration_seconds);need(duration>=0,'wait duration');return duration/225


def _without_energy(case):
    result=copy.deepcopy(case)
    for trip in result['trips']:trip['energy_kwh']=None
    for movement in result['movements']:
        for leg in movement['legs']:leg['energy_kwh']=None
    return result


def transform(document,original,canonical_transfer,expected_counts=(37,1370),old_identity=OLD_ID):
    """Only service/leg energies change; no mode/route/access regeneration.

    document uses decimal token decoding; original uses original JSON int/float
    decoding. The consumer authenticates the canonical transfer and both inputs.
    """
    need(canonical_transfer['revision']==CANONICAL_REVISION and canonical_transfer['source_bound_pass'] is True
         and canonical_transfer['same_rich_input'] is True and canonical_transfer['same_descriptor'] is True,
         'canonical source-bound input transfer')
    need(canonical_transfer['blocked_depot_wait_count']==0 and canonical_transfer['time_predicates_complete'] is True,
         'canonical access/time prerequisites')
    need(old_identity==OLD_ID or (isinstance(old_identity,str) and old_identity.startswith('SYNTHETIC_LITERAL:')),
         'target identity scope')
    selected=[v for v in document['native_cases'] if v['selected_depot_id']==15]
    need(len(selected)==1,'unique selected variant');variant=selected[0]
    need(variant['case_identity']==old_identity,'source case identity')
    n,m=expected_counts
    need(len(original['trips'])==len(variant['trips'])==n and len(original['movements'])==len(variant['movement_modes'])==m,
         'fixed target service/mode denominator')
    need(canonical_transfer['mode_count']==m,'canonical mode count')
    trip_rows={r['native']['id']:r for r in variant['trips']}
    metadata={r['movement_id']:r for r in variant['movement_provenance']}
    need(len(trip_rows)==n and len(metadata)==m,'unique source mapping')
    need([r['native']['id'] for r in variant['trips']]==[r['id'] for r in original['trips']]
         and [r['id'] for r in variant['movement_modes']]==[r['id'] for r in original['movements']],
         'original ID/index mapping')
    target=copy.deepcopy(original);changes=[]
    for trip in target['trips']:
        row=trip_rows[trip['id']];s,e=decimal(row['source_times_sec']['start']),decimal(row['source_times_sec']['end'])
        need(s.denominator==e.denominator==1 and e>s,'source service times must be integral seconds')
        need(binary_source(trip['start_min'])*60==s and binary_source(trip['end_min'])*60==e,'service source/native time')
        value=service_energy(row['source_distance_km'],str(e-s))
        need(value<=binary_source(original['battery_kwh'])-binary_source(original['reserve_kwh']),'target service capacity')
        changes.append(dict(kind='service',id=trip['id'],old_binary_energy=str(binary_source(trip['energy_kwh'])),
                            exact_energy=str(value)))
        trip['energy_kwh']=str(value)
    arcs={(r['origin_stop_id'],r['destination_stop_id']):r for r in document['source_data']['deadhead_arcs_directed_row_major']}
    for movement in target['movements']:
        rows=metadata[movement['id']]['legs'];need(len(rows)==len(movement['legs']),'leg mapping denominator')
        for index,(leg,row) in enumerate(zip(movement['legs'],rows)):
            duration=(binary_source(leg['arrive_min'])-binary_source(leg['depart_min']))*60
            need(duration>=0 and duration.denominator==1 and decimal(row['duration_sec'])==duration,
                 'leg source/native integral-second duration')
            if row['leg_role']=='off_depot_stationary_wait':
                need(leg['origin']==leg['destination'] and leg['origin']!='P15','off-depot wait access')
                value=wait_energy(str(duration))
            else:
                origin,destination=row['origin_stop_id'],row['destination_stop_id'];arc=arcs[origin,destination]
                need(leg['origin']=='P'+str(origin) and leg['destination']=='P'+str(destination)
                     and decimal(arc['time_sec_source'])==duration,'primitive arc mapping')
                value=travel_energy(arc['distance_m_source'],str(duration))
            changes.append(dict(kind='leg',id=movement['id'],leg=index,
                old_binary_energy=str(binary_source(leg['energy_kwh'])),exact_energy=str(value)))
            leg['energy_kwh']=str(value)
    need(_without_energy(target)==_without_energy(original),'nonenergy fields changed')
    return dict(status='EXACT_TARGET_DEFINED',identity=old_identity+'::exact-consumption-v1',old_identity=old_identity,
        case=target,policy=dict(POLICY),changes=changes,canonical_transfer=dict(canonical_transfer),
        denominators=dict(services=n,modes=m,legs=sum(len(r['legs']) for r in original['movements'])),
        old_gap_transferred=False,old_physical_admission_transferred=False,
        scope='New exact-consumption declared-mode model; broader modeled-path extension requires separate proof')


def literal_definitions():
    """Prospective arithmetic/parser anchors; no calls occur on import."""
    return dict(service_anchor=dict(distance_km='1.25',seconds=900,expected='11/2'),
        travel_anchor=dict(distance_m=1250,seconds=900,expected='26/5'),
        wait_anchor=dict(seconds=900,expected='4'),
        negative_controls=('boolean-source','float-source','nonfinite-source','rational-not-decimal-source',
            'negative-target-energy','float-target-energy','noncanonical-target-energy','huge-target-exponent'),
        execution_status='UNATTEMPTED')


def literal_qualification(semantics):
    """Source-defined future Q0 only; never consumes a public descriptor."""
    checks=[]
    for name,actual,expected in (
        ('exact-service',service_energy('1.25',900),Q(11,2)),
        ('exact-travel',travel_energy(1250,900),Q(26,5)),
        ('exact-wait',wait_energy(900),Q(4)),
        ('target-rational-parser',semantics._energy_number('1/3'),Q(1,3))):
        need(actual==expected,'literal anchor '+name);checks.append(dict(id=name,passed=True))
    for name,action in (
        ('boolean-source',lambda:decimal(True)),('float-source',lambda:decimal(1.25)),
        ('nonfinite-source',lambda:decimal('NaN')),('rational-not-decimal-source',lambda:decimal('1/3')),
        ('negative-target-energy',lambda:semantics._energy_number('-1/3')),
        ('float-target-energy',lambda:semantics._energy_number(.5)),
        ('noncanonical-target-energy',lambda:semantics._energy_number('0.5')),
        ('huge-target-exponent',lambda:semantics._energy_number('1e999999999'))):
        try:action()
        except (ValueError,KeyError,TypeError):checks.append(dict(id=name,rejected=True))
        else:raise ValueError('literal negative accepted: '+name)
    return dict(status='PASS',checks=checks,public_inputs_read=False,native_calls=0)
