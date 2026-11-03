"""Project already delivered exact-target admissions; never inspect diagnostics."""
import copy
from fractions import Fraction as Q
import re

IDENTITY='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7::exact-consumption-v1'
KEYS=('status','target_identity','loads_exact','ops_exact','objective_exact','fleet_count','a_exact','b_exact','face_attempts','physical_replays')
REPLAY=('strict_pass','physical_strict_pass','objective_is_certified_physical_upper','loads_exact','ops_exact','objective_exact')

def need(ok,message):
    if not ok:raise ValueError(message)
def q(value):
    need(type(value) is int or type(value) is str or isinstance(value,Q),'Exact scalar required')
    if type(value) is str:need(len(value)<=16384 and re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*)?',value) is not None,'Bounded integer/fraction token required')
    x=Q(value);need(max(x.numerator.bit_length(),x.denominator.bit_length())<=16384,'Fraction bound');return x

def project(point,closed_summary):
    # Explicit key reads are intentional: no deepcopy/seal/iteration of point.
    result={k:point[k] for k in KEYS};result['replay']={k:point['replay'][k] for k in REPLAY}
    need(result['status']=='ADMITTED_TARGET_PRIMAL' and result['target_identity']==IDENTITY,'Target admission identity')
    need(type(result['fleet_count']) is int and result['fleet_count']==2 and type(result['face_attempts']) is int and result['face_attempts']==1 and type(result['physical_replays']) is int and result['physical_replays']==1,'Fixed endpoint method denominator')
    need(all(result['replay'][k] is True for k in REPLAY[:3]),'Delivered strict target flags')
    for k in ('loads_exact','a_exact','b_exact'):
        need(type(result[k]) is list and len(result[k])==30,'Complete load/supply vector');result[k]=[q(v) for v in result[k]]
    need(all(v>=0 for v in result['loads_exact']),'Charge-only loads')
    result['ops_exact']=q(result['ops_exact']);result['objective_exact']=q(result['objective_exact'])
    for k in ('loads_exact',):
        need(type(result['replay'][k]) is list and len(result['replay'][k])==30,'Replay vector');result['replay'][k]=[q(v) for v in result['replay'][k]]
    for k in ('ops_exact','objective_exact'):result['replay'][k]=q(result['replay'][k])
    need(result['loads_exact']==result['replay']['loads_exact'] and result['ops_exact']==result['replay']['ops_exact'] and result['objective_exact']==result['replay']['objective_exact'],'Summary/replay mismatch')
    need(result['ops_exact']==200 and result['a_exact']==[Q(float(.2))]*30 and result['b_exact']==[Q(float(1/900))]*30,'Original supply/operating costs')
    objective=result['ops_exact']+sum((a*e+b*e*e/2 for a,b,e in zip(result['a_exact'],result['b_exact'],result['loads_exact'])),Q(0))
    need(result['objective_exact']==objective,'Transferred point objective identity')
    for k in ('status','target_identity','fleet_count','face_attempts','physical_replays'):need(result[k]==closed_summary[k],'Closed endpoint summary differs '+k)
    need(result['objective_exact']==q(closed_summary['objective_exact']),'Closed objective differs')
    return copy.deepcopy(result)

def direct(left,right,weights,lower):
    wl,wr=q(weights['lambda_left']),q(weights['lambda_right']);need(wl>=0 and wr>=0 and wl+wr==1,'Fixed weight simplex')
    loads=[wl*x+wr*y for x,y in zip(left['loads_exact'],right['loads_exact'])]
    ops=wl*left['ops_exact']+wr*right['ops_exact']
    upper=ops+sum((a*e+b*e*e/2 for a,b,e in zip(left['a_exact'],left['b_exact'],loads)),Q(0))
    lower=q(lower);physical_upper=min(left['objective_exact'],right['objective_exact']);need(lower<=physical_upper,'Physical lower contradicts admitted upper')
    gap=lower-upper;scale=10**6
    floor=lambda x:x.numerator*scale//x.denominator
    ceil=lambda x:-((-x.numerator*scale)//x.denominator)
    return dict(status='POSITIVE_TARGET_GAP_CERTIFIED' if gap>0 else 'TARGET_GAP_UNRESOLVED',target_identity=IDENTITY,
        lower=lower,upper=upper,gap=gap,physical_upper=physical_upper,loads=loads,ops=ops,lambda_left=wl,lambda_right=wr,
        outward=dict(scale=scale,physical_lower_floor_units=floor(lower),hull_upper_ceil_units=ceil(upper),gap_lower_floor_units=floor(gap),physical_upper_ceil_units=ceil(physical_upper)),
        exact_optima_known=False,scope='Adopted NEW target physical lower and feasible mixture upper; no repeated physical/proof check')

def literal_qualification(checker):
    # A full diagnostic object with opaque integer-keyed contents must be ignored.
    loads=[Q(1)]*30;a=[Q(float(.2))]*30;b=[Q(float(1/900))]*30
    objective=Q(200)+sum((aa+bb/2 for aa,bb in zip(a,b)),Q(0))
    point=dict(status='ADMITTED_TARGET_PRIMAL',target_identity=IDENTITY,loads_exact=loads,ops_exact=Q(200),objective_exact=objective,
        fleet_count=2,a_exact=a,b_exact=b,face_attempts=1,physical_replays=1,
        replay=dict(strict_pass=True,physical_strict_pass=True,objective_is_certified_physical_upper=True,loads_exact=loads,ops_exact=Q(200),objective_exact=objective),
        problem={0:object()},recovery=object())
    summary={k:point[k] for k in ('status','target_identity','fleet_count','face_attempts','physical_replays','objective_exact')}
    projected=project(point,summary);need('problem' not in projected and 'recovery' not in projected,'Diagnostic projection')
    controls=[]
    for key,value in (('loads_exact',[Q(2)]*30),('ops_exact',201),('objective_exact',objective+1),('target_identity','wrong'),('physical_replays',2)):
        changed=dict(point);changed[key]=value
        try:project(changed,summary)
        except (ValueError,KeyError,TypeError):controls.append(dict(id='changed-'+key,rejected=True))
        else:raise ValueError('Projection corruption accepted '+key)
    return dict(status='PASS',anchors=1,controls=controls,native_calls=0,scope='NEW projection boundary only; no old replay or public data')
