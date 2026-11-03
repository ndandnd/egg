"""Independent exact OD gate; no extractor/producer/backend is imported.

Source-only authored; qualification is prospective, not executed here.
"""
from fractions import Fraction
import re

MAX_LOCATIONS=256
MAX_SOURCE_BYTES=20*1024**2
MAX_FRACTION_BITS=4096
MAX_ARITHMETIC_BITS=32768
FIELDS=('origin_stop_id','destination_stop_id','distance_m_source','time_sec_source')


class Unknown(ValueError):
    pass


def _need(condition,message):
    if not condition:raise Unknown(message)


def _quantity(value,bits=MAX_FRACTION_BITS):
    _need(type(value) in (str,int),'Exact string/integer source quantity required')
    _need(not isinstance(value,str) or len(value)<=bits,'Quantity text ceiling')
    if isinstance(value,str) and 'e' in value.lower():
        _need(len(value)<=256,'Exponential token text ceiling')
        matched=re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)[eE]([+-]?[0-9]+)',value)
        _need(matched is not None,'Malformed exponential token')
        exponent=matched.group(1)
        _need(abs(int(exponent))<=1000,
              'Exponential token bound before Fraction')
    try:answer=Fraction(value)
    except (ValueError,ZeroDivisionError,OverflowError) as exc:
        raise Unknown('Malformed/nonfinite rational') from exc
    _need(max(answer.numerator.bit_length(),answer.denominator.bit_length())<=bits,
          'Input rational-bit ceiling')
    return answer


def _identifier(value):
    _need(type(value) in (str,int),'String/integer source IDs required, not booleans')
    _need(not isinstance(value,str) or 0<len(value)<=256,'Source ID empty/text ceiling')
    _need(not isinstance(value,int) or value.bit_length()<=256,'Source ID integer ceiling')
    return type(value).__name__,value


def _same(left,right):
    if type(left) is not type(right):return False
    if isinstance(left,dict):return set(left)==set(right) and all(_same(left[k],right[k]) for k in left)
    if isinstance(left,list):return len(left)==len(right) and all(_same(x,y) for x,y in zip(left,right))
    return left==right


def independently_check(projected,claimed):
    """Check all l^2 entries and l^3 triangles in DECLARED source-ID order.

    A triangle(i,j,k) has slack M[i,k]+M[k,j]-M[i,j]. Separate first20
    negative-slack witnesses are retained per metric. Negative entries and
    nonzero diagonals have their own counts. Invalid/incomplete schema or
    arithmetic overflow gives UNKNOWN, never a partial PASS.
    """
    summary=dict(status='UNKNOWN',location_count=0,arc_count=0,expected_arc_count=0,
        triangle_count_per_metric=0,distance_triangle_checks=0,time_triangle_checks=0,
        distance_entries_checked=0,time_entries_checked=0,
        distance_min_slack=None,time_min_slack=None,distance_violation_count=0,time_violation_count=0,
        distance_violations=[],time_violations=[],distance_negative_count=0,time_negative_count=0,
        distance_nonzero_diagonal_count=0,time_nonzero_diagonal_count=0,schema_errors={},schema_error_count=0)
    result=dict(status='UNKNOWN',metric_status='UNKNOWN',summary_matches=False,
                scope='Exact source OD metrics only; no routing/support conclusion')
    try:
        _need(isinstance(projected,dict) and isinstance(claimed,dict),'Dictionary contract required')
        _need(set(projected)=={'locations','arcs','source_bytes','distance_unit','time_unit'},'Projected top-level schema differs')
        _need(type(projected.get('source_bytes')) is int and 0<=projected['source_bytes']<=MAX_SOURCE_BYTES,
              'Source byte count/ceiling')
        _need(projected.get('distance_unit')=='m' and projected.get('time_unit')=='s','Units differ')
        locations=projected['locations'];arcs=projected['arcs']
        _need(isinstance(locations,list) and 1<=len(locations)<=MAX_LOCATIONS,'Location count ceiling/empty set')
        identities=[_identifier(value) for value in locations]
        _need(len(set(identities))==len(identities),'Duplicate source ID')
        _need(len({str(value) for value in locations})==len(locations),'Aliased source IDs')
        n=len(locations);index={identity:i for i,identity in enumerate(identities)}
        summary.update(location_count=n,expected_arc_count=n*n,triangle_count_per_metric=n*n*n)
        _need(isinstance(arcs,list),'Arc list required');summary['arc_count']=len(arcs)
        _need(len(arcs)==n*n,'Full l-squared entry count required')
        matrices=([None]*(n*n),[None]*(n*n));seen=set()
        for arc in arcs:
            _need(isinstance(arc,dict) and set(arc)==set(FIELDS),'Projected arc schema differs')
            origin,destination=_identifier(arc[FIELDS[0]]),_identifier(arc[FIELDS[1]])
            _need(origin in index and destination in index,'Unknown arc endpoint')
            i,j=index[origin],index[destination];key=i*n+j
            _need(key not in seen,'Duplicate OD entry');seen.add(key)
            matrices[0][key]=_quantity(arc[FIELDS[2]])
            matrices[1][key]=_quantity(arc[FIELDS[3]])
        _need(len(seen)==n*n,'Missing OD entry')
        summary.update(distance_entries_checked=n*n,time_entries_checked=n*n)
        labels=('distance','time')
        for label,matrix in zip(labels,matrices):
            summary[label+'_negative_count']=sum(value<0 for value in matrix)
            summary[label+'_nonzero_diagonal_count']=sum(matrix[i*n+i]!=0 for i in range(n))
        minima=[None,None]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    for which,(label,matrix) in enumerate(zip(labels,matrices)):
                        slack=matrix[i*n+k]+matrix[k*n+j]-matrix[i*n+j]
                        _need(max(slack.numerator.bit_length(),slack.denominator.bit_length())<=MAX_ARITHMETIC_BITS,
                              'Arithmetic overflow rational-bit ceiling')
                        summary[label+'_triangle_checks']+=1
                        if minima[which] is None or slack<minima[which]:
                            minima[which]=slack;summary[label+'_min_slack']=str(slack)
                        if slack<0:
                            summary[label+'_violation_count']+=1
                            witnesses=summary[label+'_violations']
                            if len(witnesses)<20:witnesses.append(dict(indices=[i,j,k],origin=locations[i],
                                destination=locations[j],via=locations[k],slack=str(slack)))
        failed=any(summary[label+suffix]>0 for label in labels for suffix in
                   ('_negative_count','_nonzero_diagonal_count','_violation_count'))
        summary['status']='FAIL' if failed else 'PASS'
        mismatches=[]
        for key,value in summary.items():
            if key=='schema_errors':
                continue  # Diagnostic taxonomy is deliberately independent.
            elif key.endswith('_min_slack'):
                if _quantity(claimed[key],MAX_ARITHMETIC_BITS)!=_quantity(value,MAX_ARITHMETIC_BITS):mismatches.append(key)
            elif type(value) is int:
                if type(claimed.get(key)) is not int or claimed[key]!=value:mismatches.append(key)
            elif not _same(claimed.get(key),value):mismatches.append(key)
        result.update(status=summary['status'] if not mismatches else 'FAIL',metric_status=summary['status'],
            summary_matches=not mismatches,summary_mismatches=mismatches)
    except (Unknown,KeyError,TypeError,ValueError,IndexError,OverflowError,MemoryError) as exc:
        summary['status']='UNKNOWN';summary['schema_errors']={'independent_contract_or_resource':1}
        summary['schema_error_count']=1
        result.update(status='UNKNOWN',metric_status='UNKNOWN',summary_matches=False,
                      reason=type(exc).__name__+': '+str(exc))
    result['independent_summary']=summary
    return result


def literal_qualification():
    """Own fixed literal claims, independent of the producer; not run on import."""
    import copy
    ids=['a','b','c']
    projected=dict(locations=ids,arcs=[dict(origin_stop_id=ids[i],destination_stop_id=ids[j],
        distance_m_source=abs(i-j),time_sec_source=2*abs(i-j)) for i in range(3) for j in range(3)],
        source_bytes=1,distance_unit='m',time_unit='s')
    claim=dict(status='PASS',location_count=3,arc_count=9,expected_arc_count=9,
        triangle_count_per_metric=27,distance_triangle_checks=27,time_triangle_checks=27,
        distance_entries_checked=9,time_entries_checked=9,
        distance_min_slack='0',time_min_slack='0',distance_violation_count=0,time_violation_count=0,
        distance_violations=[],time_violations=[],distance_negative_count=0,time_negative_count=0,
        distance_nonzero_diagonal_count=0,time_nonzero_diagonal_count=0,schema_errors={},schema_error_count=0)
    checks=[]
    def expect(name,p,c,status,agreement):
        audit=independently_check(p,c)
        if audit['status']!=status or audit['summary_matches'] is not agreement:
            raise ValueError('Independent literal expectation: '+name)
        checks.append(dict(id=name,status='PASS',metric_status=audit['metric_status']))
    expect('own-complete-metric-anchor',projected,claim,'PASS',True)
    bad=copy.deepcopy(projected);bad['arcs'][2]['distance_m_source']=3
    failed=dict(claim,status='FAIL',distance_min_slack='-1',distance_violation_count=1,
        distance_violations=[dict(indices=[0,2,1],origin='a',destination='c',via='b',slack='-1')])
    expect('own-distance-failure-anchor',bad,failed,'FAIL',True)
    for name,change in (
        ('changed-count',lambda c:c.__setitem__('distance_triangle_checks',26)),
        ('changed-minimum',lambda c:c.__setitem__('distance_min_slack','0')),
        ('changed-witness',lambda c:c['distance_violations'][0].__setitem__('via','a')),
        ('boolean-witness-index',lambda c:c['distance_violations'][0]['indices'].__setitem__(0,False)),
        ('false-PASS',lambda c:c.__setitem__('status','PASS'))):
        altered=copy.deepcopy(failed);change(altered);expect(name,bad,altered,'FAIL',False)
    for name,change in (
        ('missing-arc',lambda p:p['arcs'].pop()),
        ('duplicate-arc',lambda p:p['arcs'].__setitem__(1,copy.deepcopy(p['arcs'][0]))),
        ('float-quantity',lambda p:p['arcs'][0].__setitem__('distance_m_source',0.0)),
        ('huge-exponent',lambda p:p['arcs'][0].__setitem__('distance_m_source','1e999999999')),
        ('source-ceiling',lambda p:p.__setitem__('source_bytes',MAX_SOURCE_BYTES+1))):
        altered=copy.deepcopy(projected);change(altered);expect(name,altered,claim,'UNKNOWN',False)
    return dict(status='PASS',literal_controls=checks,native_calls=0,
        scope='Own fixed literals and summary-corruption controls; no producer or public data calls')
