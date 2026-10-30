"""Prospective exact OD proof gate; callable metadata only, no filesystem I/O."""
import copy
from fractions import Fraction as Q
import re

MAX_LOCATIONS=256
MAX_SOURCE_BYTES=20*1024**2
MAX_ARCS=MAX_LOCATIONS**2
MAX_INPUT_BITS=4096
MAX_INPUT_CHARS=4096
MAX_ARITHMETIC_BITS=32768
EXAMPLES=20
ARC_KEYS={'origin_stop_id','destination_stop_id','distance_m_source','time_sec_source'}
TOP_KEYS={'locations','arcs','source_bytes','distance_unit','time_unit'}

class OverflowUnknown(ValueError):pass

def exact(value):
    if isinstance(value,bool) or not isinstance(value,(int,str)):
        raise ValueError('Exact integer or rational string required')
    if isinstance(value,str) and len(value)>MAX_INPUT_CHARS:raise OverflowUnknown('Numeric string overflow')
    if isinstance(value,str) and 'e' in value.lower():
        if len(value)>256:raise OverflowUnknown('Exponential token text overflow')
        exponent=re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)[eE]([+-]?[0-9]+)',value)
        if exponent is None:raise ValueError('Malformed exponential token')
        if abs(int(exponent.group(1)))>1000:raise OverflowUnknown('Exponential token bound')
    if isinstance(value,int) and value.bit_length()>MAX_INPUT_BITS:raise OverflowUnknown('Integer overflow')
    number=Q(value)
    if max(number.numerator.bit_length(),number.denominator.bit_length())>MAX_INPUT_BITS:
        raise OverflowUnknown('Input fraction overflow')
    return number

def id_key(value):
    if type(value) is int:
        if value.bit_length()>256:raise OverflowUnknown('ID overflow')
        return ('int',value)
    if type(value) is str and 0<len(value)<=256:return ('str',value)
    raise ValueError('Invalid location ID')

def qualify_od(projected):
    """Exact complete-pair/triple gate, source-order indices(i,j,k), no repair.

    Slack is M[i,k]+M[k,j]-M[i,j]. UNKNOWN means no complete matrix
    conclusion; every checked triangle counter remains explicit on overflow.
    source_bytes is supplied/authenticated by the separately reviewed worker.
    """
    result=dict(status='UNKNOWN',location_count=0,arc_count=0,expected_arc_count=0,
        distance_entries_checked=0,time_entries_checked=0,
        triangle_count_per_metric=0,distance_triangle_checks=0,time_triangle_checks=0,
        distance_min_slack=None,time_min_slack=None,distance_violation_count=0,time_violation_count=0,
        distance_violations=[],time_violations=[],distance_negative_count=0,time_negative_count=0,
        distance_nonzero_diagonal_count=0,time_nonzero_diagonal_count=0,
        schema_errors={},schema_error_count=0,
        continuation=dict(canonical_coverage='UNATTEMPTED',charging_access='UNATTEMPTED',
                          energy_rounding='UNATTEMPTED',physical_dominance='NOT_ESTABLISHED'),
        scope='Necessary gate for the stated sufficient-proof route; no routing/support extension',
        native_calls=0)
    errors=result['schema_errors']
    def error(code,count=1):errors[code]=errors.get(code,0)+count
    def finish(status=None):
        if status is not None:result['status']=status
        result['schema_error_count']=sum(errors.values())
        return result
    if not isinstance(projected,dict) or set(projected)!=TOP_KEYS:
        error('projected_schema');return finish()
    locations,arcs=projected['locations'],projected['arcs']
    if isinstance(locations,list):
        n=len(locations);result.update(location_count=n,expected_arc_count=n*n,triangle_count_per_metric=n*n*n)
    else:error('locations_schema');return finish()
    if isinstance(arcs,list):result['arc_count']=len(arcs)
    else:error('arcs_schema');return finish()
    size=projected['source_bytes']
    if type(size) is not int or size<0:error('source_bytes_schema')
    elif size>MAX_SOURCE_BYTES:error('source_size_overflow')
    if projected['distance_unit']!='m' or projected['time_unit']!='s':error('units')
    if not 1<=n<=MAX_LOCATIONS:error('location_count_overflow_or_empty')
    if len(arcs)>MAX_ARCS:error('arc_count_overflow')
    if errors:return finish()
    positions={};aliases={}
    for i,value in enumerate(locations):
        try:k=id_key(value)
        except (ValueError,OverflowError):error('location_id_schema');continue
        if k in positions:error('duplicate_locations')
        else:positions[k]=i
        alias=str(value)
        if alias in aliases and aliases[alias]!=k:error('ambiguous_location_alias')
        aliases[alias]=k
    if errors:return finish()
    distance={};time={};present=set()
    for arc in arcs:
        if not isinstance(arc,dict) or set(arc)!=ARC_KEYS:error('arc_schema');continue
        try:
            origin=id_key(arc['origin_stop_id']);destination=id_key(arc['destination_stop_id'])
        except (ValueError,OverflowError):error('endpoint_schema');continue
        if origin not in positions or destination not in positions:error('unknown_endpoint');continue
        pair=(positions[origin],positions[destination])
        if pair in present:error('duplicate_arcs');continue
        present.add(pair)
        try:d,t=exact(arc['distance_m_source']),exact(arc['time_sec_source'])
        except OverflowUnknown:error('numeric_overflow');continue
        except (ValueError,ZeroDivisionError,OverflowError):error('numeric_schema');continue
        distance[pair]=d;time[pair]=t
    missing=n*n-len(present)
    if missing:error('missing_arcs',missing)
    if errors:return finish()
    result['distance_entries_checked']=n*n;result['time_entries_checked']=n*n
    for metric,matrix in (('distance',distance),('time',time)):
        result[metric+'_negative_count']=sum(v<0 for v in matrix.values())
        result[metric+'_nonzero_diagonal_count']=sum(matrix[i,i]!=0 for i in range(n))
        minimum=None
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    slack=matrix[i,k]+matrix[k,j]-matrix[i,j]
                    if max(slack.numerator.bit_length(),slack.denominator.bit_length())>MAX_ARITHMETIC_BITS:
                        error('arithmetic_overflow');return finish('UNKNOWN')
                    result[metric+'_triangle_checks']+=1
                    if minimum is None or slack<minimum:
                        minimum=slack;result[metric+'_min_slack']=str(slack)
                    if slack<0:
                        result[metric+'_violation_count']+=1
                        if len(result[metric+'_violations'])<EXAMPLES:
                            result[metric+'_violations'].append(dict(indices=[i,j,k],origin=locations[i],
                                destination=locations[j],via=locations[k],slack=str(slack)))
    failed=any(result[k] for k in ('distance_negative_count','time_negative_count',
        'distance_nonzero_diagonal_count','time_nonzero_diagonal_count',
        'distance_violation_count','time_violation_count'))
    return finish('FAIL' if failed else 'PASS')

def literal_qualification():
    """Prospective small exact source fixtures; never invoked on import."""
    locations=['a','b','c']
    good=dict(locations=locations,arcs=[dict(origin_stop_id=locations[i],destination_stop_id=locations[j],
        distance_m_source=abs(i-j),time_sec_source=2*abs(i-j)) for i in range(3) for j in range(3)],
        source_bytes=1,distance_unit='m',time_unit='s')
    checks=[]
    def expect(name,value,status,extra=lambda r:True):
        report=qualify_od(value)
        if report['status']!=status or not extra(report):raise ValueError('Literal gate expectation: '+name)
        checks.append(dict(id=name,status='PASS',gate_status=status))
    expect('positive-metric',good,'PASS',lambda r:r['distance_triangle_checks']==27 and r['time_triangle_checks']==27
        and r['distance_min_slack']=='0' and r['time_min_slack']=='0')
    for metric,field,value in [('distance','distance_m_source',3),('time','time_sec_source',5)]:
        changed=copy.deepcopy(good);changed['arcs'][2][field]=value
        expect(metric+'-only-failure',changed,'FAIL',lambda r,m=metric:r[m+'_violation_count']==1
            and r[m+'_violations'][0]['indices']==[0,2,1] and r[m+'_min_slack']=='-1'
            and r[('time' if m=='distance' else 'distance')+'_violation_count']==0)
    changed=copy.deepcopy(good);changed['arcs'].append(copy.deepcopy(changed['arcs'][0]));expect('duplicate-arc',changed,'UNKNOWN')
    changed=copy.deepcopy(good);changed['arcs'].pop();expect('missing-arc',changed,'UNKNOWN')
    changed=copy.deepcopy(good);changed['locations'].append('a');expect('duplicate-location',changed,'UNKNOWN')
    changed=copy.deepcopy(good);changed['arcs'][0]['distance_m_source']=1
    expect('nonzero-diagonal',changed,'FAIL',lambda r:r['distance_nonzero_diagonal_count']==1
        and r['distance_triangle_checks']==27 and r['time_triangle_checks']==27)
    changed=copy.deepcopy(good);changed['source_bytes']=MAX_SOURCE_BYTES+1;expect('source-overflow',changed,'UNKNOWN')
    changed=copy.deepcopy(good);changed['arcs'][1]['distance_m_source']=-1;expect('negative-entry',changed,'FAIL')
    return dict(status='PASS',literal_controls=checks,native_calls=0,
        scope='New exact gate implementation fixtures; no actual public metadata or dominance claim')
