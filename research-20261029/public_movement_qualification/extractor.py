"""Public shared-OD metadata projection only; no variants, trips or file I/O.

Caller authenticates <=20MiB JSON bytes and decodes once using parse_float=str,
parse_int=int, duplicate-key rejection and nonfinite-token rejection.
"""
from fractions import Fraction as Q
import re

MAX_SOURCE_BYTES=20*1024**2
MAX_LOCATIONS=256
SELECTED_DEPOT=15
NUMERIC=re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z')


def need(ok,message):
    if not ok:raise ValueError(message)


def number(value):
    """Exact encoded decimal value plus retained parser token, no float input."""
    need(type(value) is int or isinstance(value,str),'numeric representation/bool/float')
    if isinstance(value,str):
        need(len(value)<=256 and NUMERIC.fullmatch(value) is not None,'finite JSON numeric token')
        exponent=re.search(r'[eE]([+-]?[0-9]+)',value)
        need(exponent is None or abs(int(exponent.group(1)))<=1000,'numeric exponent bound')
    result=Q(value)
    need(result.numerator.bit_length()<=4096 and result.denominator.bit_length()<=4096,'numeric bit bound')
    return result


def identifier(value):
    need(type(value) is int and 0<=value<=2**31-1,'integer source location ID')
    return value


def depot_flag(value):
    # A boolean is a legitimate categorical flag, never a numeric quantity.
    if type(value) is bool:return value
    need(type(value) is int and value in (0,1),'source depot flag')
    return bool(value)


def project_od(document):
    """Fail closed on schema/OD incompleteness; do not test triangles here.

    Missing/invalid fields raise ValueError/KeyError. The caller records FAILED
    or UNKNOWN and preserves downstream UNATTEMPTED stages, never imputing.
    """
    need(isinstance(document,dict),'document object')
    units=document['source_field_semantics']
    expected={
        'deadhead_trip_matrix.distances':'m; directional matrix values retained exactly',
        'deadhead_trip_matrix.times':'s; directional matrix values retained exactly'}
    need(all(units[k]==v for k,v in expected.items()),'explicit OD unit semantics')
    source=document['source_data']
    locations=[identifier(v) for v in source['deadhead_stop_order_source']]
    need(0<len(locations)<=MAX_LOCATIONS and len(set(locations))==len(locations),'location universe')
    stop_rows=source['stops'];need(isinstance(stop_rows,list) and len(stop_rows)==len(locations),'stop denominator')
    flags={}
    for row in stop_rows:
        stop=identifier(row['id']);need(stop not in flags,'duplicate stop ID')
        flags[stop]=depot_flag(row['b_depot'])
    need(set(flags)==set(locations),'stop/matrix identity')
    need(SELECTED_DEPOT in flags and flags[SELECTED_DEPOT] is True,'selected depot15 absent/not flagged')
    raw=source['deadhead_arcs_directed_row_major']
    n=len(locations);need(isinstance(raw,list) and len(raw)==n*n,'all directed OD entries required')
    arcs=[];seen=set()
    for position,row in enumerate(raw):
        origin,destination=identifier(row['origin_stop_id']),identifier(row['destination_stop_id'])
        need((origin,destination)==(locations[position//n],locations[position%n]),'row-major OD identity/order')
        need((origin,destination) not in seen,'duplicate OD pair');seen.add((origin,destination))
        # This first gate qualifies matrix properties, not physical/native-time
        # admissibility. Preserve finite negative or fractional values so the
        # complete independent property checks can count/report their failures.
        number(row['distance_m_source']);number(row['time_sec_source'])
        arcs.append(dict(origin_stop_id=origin,destination_stop_id=destination,
                         distance_m_source=row['distance_m_source'],time_sec_source=row['time_sec_source']))
    return dict(status='OD_METADATA_PROJECTED',locations=locations,arcs=arcs,
        location_count=n,od_denominator=n*n,triangle_denominator=n*n*n,
        selected_depot=SELECTED_DEPOT,selected_depot_source_flag=True,distance_unit='m',time_unit='s',
        source_units=expected,source_fields=dict(order='source_data.deadhead_stop_order_source',
            arcs='source_data.deadhead_arcs_directed_row_major',stops='source_data.stops'),
        numeric_semantics='Exact rational of retained JSON decimal token; raw token preserved. Not an energy-model binary-rounding audit.',
        paired_leg_realizability='UNKNOWN',
        paired_leg_source_claim='Aligned OD distance/time cells are consumed together by the constructor; no common physical path witness or separate-minima guarantee is recorded in these fields.',
        scope='shared public OD/location metadata only; native_cases and service rows unaccessed',
        triangle_status='UNATTEMPTED',mode_coverage_status='UNATTEMPTED',energy_dominance_status='UNATTEMPTED',
        charging_access_status='UNATTEMPTED',physical_witness_replay=False)
