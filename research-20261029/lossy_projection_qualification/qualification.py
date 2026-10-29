"""Exact full-segment coverage against independent physical vertex branches."""
import copy
from fractions import Fraction as Q
from itertools import product

def need(ok,message):
    if not ok:raise ValueError(message)

def key(matching):return tuple(sorted(tuple(e) for e in matching))

def cover(intervals,left,right):
    intervals=sorted((max(left,a),min(right,b)) for a,b in intervals if max(left,a)<=min(right,b))
    need(bool(intervals) and intervals[0][0]==left,'Missing segment start')
    reached=left
    for a,b in intervals:
        need(a<=reached,'Uncovered open segment gap')
        reached=max(reached,b)
    need(reached==right,'Missing segment end')
    return True

def check_curve(reference,physical,curve,branches):
    vertices=[v for _,branch in branches for v in branch['vertices']]
    need(curve['feasible']==bool(vertices),'Feasible/infeasible cardinality mismatch')
    if not vertices:
        need(not curve['segments'],'Infeasible curve has segments');return dict(vertices=0,segments=0)
    need(min(v['early'] for v in vertices)==curve['lower']
         and max(v['early'] for v in vertices)==curve['upper'],'Raw projected interval mismatch')
    for index,branch in branches:
        need(branch['N']==curve['N'],'Fleet count')
        for v in branch['vertices']:
            need(v['ops']==curve['ops'],'Vehicle operations')
            need(curve['lower']<=v['early']<=curve['upper'],'Raw vertex outside interval')
            need(all(v['late']>=a+b*v['early'] for a,b in curve['planes']),'Raw vertex below proposed plane')
            audit=reference.replay(physical,index,v['witness'])
            need((audit['early'],audit['late'],audit['ops'])==(v['early'],v['late'],v['ops']),'Raw witness replay mismatch')
    for segment in curve['segments']:
        a,b=segment['intercept'],segment['slope'];intervals=[]
        need((a,b) in curve['planes'],'Segment not on declared lower plane')
        need(all(a+b*E==max(c+d*E for c,d in curve['planes']) for E in (segment['left'],segment['right'])),
             'Segment does not follow lower envelope')
        for index,branch in branches:
            # A supporting plane's zero face is spanned by its zero vertices.
            zero=[v for v in branch['vertices'] if v['late']==a+b*v['early']]
            if not zero:continue
            lo=min(zero,key=lambda v:v['early']);hi=max(zero,key=lambda v:v['early'])
            left=max(segment['left'],lo['early']);right=min(segment['right'],hi['early'])
            if left>right:continue
            intervals.append((left,right))
            for E in (left,right):
                theta=Q(0) if hi['early']==lo['early'] else (E-lo['early'])/(hi['early']-lo['early'])
                x=tuple((1-theta)*x+theta*y for x,y in zip(lo['x'],hi['x']))
                witness=reference.witness(physical['spec'],branch['buses'],x)
                audit=reference.replay(physical,index,witness)
                need(audit['early']==E and audit['late']==a+b*E,'Segment face witness')
        cover(intervals,segment['left'],segment['right'])
    # Piece intervals themselves must cover the entire curve domain.
    cover([(s['left'],s['right']) for s in curve['segments']],curve['lower'],curve['upper'])
    return dict(vertices=len(vertices),segments=len(curve['segments']),full_segments_covered=True)

def compare(reference,physical,candidate):
    expected={key(m) for m in physical['assignments']}
    need({key(b['matching']) for b in physical['branches']}==expected,'Raw matching branches omitted')
    for matching in expected:
        n=2*len(physical['A'])-len(matching)
        branches=[b for b in physical['branches'] if key(b['matching'])==matching]
        need(len(branches)==2**n and {tuple(b['signs']) for b in branches}==set(product((-1,1),repeat=n)),
             'Raw sign-branch denominator changed')
        need(all(b['feasible']==bool(b['vertices']) for b in branches),'Raw feasible status')
    need(len(physical['branches'])==physical['raw_branch_count']
         and len(expected)==physical['raw_assignment_count'],'Raw declared denominator')
    need(len(candidate['assignments'])==len(expected)
         and {key(r['matching']) for r in candidate['assignments']}==expected,'Complete assignment identities')
    details=[]
    for row in candidate['assignments']:
        branches=[(i,b) for i,b in enumerate(physical['branches']) if key(b['matching'])==key(row['matching'])]
        details.append(check_curve(reference,physical,row,branches))
    counts={len(m) for m in physical['assignments']}
    need([r['m'] for r in candidate['cardinalities']]==sorted(counts),'All cardinalities retained')
    for row in candidate['cardinalities']:
        branches=[(i,b) for i,b in enumerate(physical['branches']) if len(b['matching'])==row['m']]
        details.append(check_curve(reference,physical,row,branches))
    return dict(status='MATCHED',assignment_count=len(expected),cardinality_count=len(counts),details=details,
                scope='all raw vertices and full affine segments; not numerical support outcomes')

def controls(reference,candidate):
    raw=dict(A=[1],B=[1],capacity=2,eta_c='1/2',eta_d='1/2',K=1,H=6,fee=1,allowed=[])
    physical=reference.enumerate_physical(raw);value=candidate.derive(raw)
    compare(reference,physical,value)
    row=value['cardinalities'][0]
    need(row['lower']==Q(-1,2) and row['upper']==1 and row['planes']==[(4,Q(-1)),(4,Q(-4))],
         'Hand anchor planes/domain')
    # Both E0,L4 and E1,L3 are attained with zero exports; E−1/2,L6 uses discharge.
    for E,L in [(Q(-1,2),6),(0,4),(1,3)]:
        point=reference.slice_at(physical,E,2)[2];need(point['late']==L,'Hand slice anchor')
    negatives=[]
    def rejects(name,changed):
        try:compare(reference,physical,changed)
        except ValueError:negatives.append(dict(id=name,rejected=True))
        else:raise ValueError('Accepted corruption: '+name)
    changed=copy.deepcopy(value);changed['assignments']=[];rejects('omitted_assignment',changed)
    changed=copy.deepcopy(value);changed['cardinalities']=[];rejects('omitted_cardinality',changed)
    changed=copy.deepcopy(value);changed['cardinalities'][0]['lower']=0;rejects('missing_negative_interval',changed)
    changed=copy.deepcopy(value);changed['cardinalities'][0]['planes'][1]=(5,Q(-4));rejects('wrong_loss_plane',changed)
    changed=copy.deepcopy(value);changed['cardinalities'][0]['segments']=[];rejects('missing_full_segment',changed)
    changed=copy.deepcopy(value);changed['cardinalities'][0]['feasible']=False;rejects('false_infeasible',changed)
    changed=copy.deepcopy(value);changed['cardinalities'][0]['ops']+=1;rejects('changed_fee',changed)
    dropped=copy.deepcopy(physical);dropped['branches'].pop()
    try:compare(reference,dropped,value)
    except ValueError:negatives.append(dict(id='omitted_raw_sign_branch',rejected=True))
    else:raise ValueError('Accepted omitted raw sign branch')
    for name,mutate in [('terminal_refill',lambda w:w['terminal'][0].__setitem__('buy',0)),
        ('service_assignment',lambda w:w['buses'][0].__setitem__('a',0)),
        ('reported_inventory',lambda w:w['states'][0].__setitem__('final',0))]:
        index=next(i for i,b in enumerate(physical['branches']) if b['vertices'])
        witness=copy.deepcopy(physical['branches'][index]['vertices'][0]['witness']);mutate(witness)
        try:reference.replay(physical,index,witness)
        except ValueError:negatives.append(dict(id=name,rejected=True))
        else:raise ValueError('Accepted witness corruption: '+name)
    index,v=next((i,v) for i,b in enumerate(physical['branches']) for v in b['vertices'] if v['witness']['early'])
    witness=copy.deepcopy(v['witness']);event=witness['early'][0]
    event['end']=(event['start']+event['end'])/2
    try:reference.replay(physical,index,witness)
    except ValueError:negatives.append(dict(id='gross_connector_power',rejected=True))
    else:raise ValueError('Accepted gross connector corruption')
    try:cover([(Q(0),Q(1,3)),(Q(2,3),Q(1))],Q(0),Q(1))
    except ValueError:negatives.append(dict(id='interior_coverage_gap',rejected=True))
    else:raise ValueError('Accepted interior coverage gap')
    return dict(status='PASS',hand_anchors=4,negative_controls=negatives,native_calls=0)
