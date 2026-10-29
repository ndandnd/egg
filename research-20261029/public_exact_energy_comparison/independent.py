"""Independent retained-summary comparison via endpoint variance identity.

Pure arithmetic only. No physical replay, tree check, I/O, solver or search.
"""
from fractions import Fraction as Q
import re

IDENTITY='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7::exact-consumption-v1'
A=Q(float(.2))
BETA=Q(float(1/900))
SCALE=1000000


def need(ok,message):
    if not ok:raise ValueError(message)


def exact(value):
    need(type(value) in (int,str) or isinstance(value,Q),'Exact quantity required; bool/float forbidden')
    if isinstance(value,str):
        need(len(value)<=32768 and 'e' not in value.lower(),'Bounded nonexponential rational token required')
    result=Q(value)
    need(max(result.numerator.bit_length(),result.denominator.bit_length())<=32768,'Rational bit ceiling')
    return result


def seal(value):
    """Caller keeps these immutable projections separately, never reseals edits."""
    if isinstance(value,Q):return ('Q',value.numerator,value.denominator)
    if isinstance(value,dict):
        need(all(type(k) is str for k in value),'Projected summary keys must be strings')
        return ('dict',tuple((k,seal(value[k])) for k in sorted(value)))
    if isinstance(value,(list,tuple)):return (type(value).__name__,tuple(seal(x) for x in value))
    need(type(value) in (str,int,bool,type(None)),'Unsupported projected value, no opaque diagnostics allowed')
    return (type(value).__name__,value)


def _endpoint(point,identity):
    need(point['status']=='ADMITTED_TARGET_PRIMAL' and point['target_identity']==identity,'Wrong/unadmitted endpoint identity')
    need(type(point['face_attempts']) is int and point['face_attempts']==1
         and type(point['physical_replays']) is int and point['physical_replays']==1,'Exactly one new face and replay required')
    need(type(point['fleet_count']) is int and point['fleet_count']==2,'Frozen two-bus endpoint required')
    loads=tuple(map(exact,point['loads_exact']))
    need(len(loads)==30 and all(x>=0 for x in loads),'Complete nonnegative thirty-period loads required')
    need(tuple(map(exact,point['a_exact']))==(A,)*30 and tuple(map(exact,point['b_exact']))==(BETA,)*30,'Original binary supply coefficients changed')
    ops=exact(point['ops_exact']);objective=exact(point['objective_exact'])
    need(ops==200,'Frozen operating cost must be200')
    replay=point['replay']
    need(all(replay.get(key) is True for key in
         ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),'Missing admitted strict replay flags')
    need(tuple(map(exact,replay['loads_exact']))==loads and exact(replay['ops_exact'])==ops
         and exact(replay['objective_exact'])==objective,'Endpoint/replay value mismatch')
    need(objective==ops+sum((A*x+BETA*x*x/2 for x in loads),Q(0)),'Endpoint objective differs from original supply')
    return loads,objective


def _display(units):
    sign='-' if units<0 else '';number=abs(units)
    return sign+str(number//SCALE)+'.'+str(number%SCALE).zfill(6)


def check(left,right,weights,lower,target_identity,admit=None,seals=None):
    """Require separately source-admitted objects AND immutable content seals.

    admit(label,obj) must bind the actual fixed-source projected object and
    separately retained manifest/content seal. This pure API cannot authenticate
    a self-issued receipt or a digest supplied by the same untrusted packet.
    """
    need(target_identity==IDENTITY,'Explicit exact-consumption target identity required')
    objects=dict(left=left,right=right,weights=weights,lower=lower)
    need(admit is not None and isinstance(seals,dict) and set(seals)==set(objects),'All four source admissions/seals required')
    for label,obj in objects.items():
        need(seal(obj)==seals[label] and admit(label,obj) is True,'Unadmitted/edited source summary: '+label)
        need(seal(obj)==seals[label],'Admission callback mutated summary: '+label)
    x,ux=_endpoint(left,target_identity);y,uy=_endpoint(right,target_identity)
    wl,wr=exact(weights['lambda_left']),exact(weights['lambda_right'])
    need(0<=wl<=1 and 0<=wr<=1 and wl+wr==1,'Invalid frozen weights')
    need(type(weights['source_revision']) is str and re.fullmatch('[0-9a-f]{40}',weights['source_revision']) is not None
         and type(weights['path']) is str and 0<len(weights['path'])<=4096,'Fixed weight provenance required')
    need(lower['status']=='COMPLETE_TARGET_BOUND' and lower['target_identity']==target_identity,'Unqualified all-fleet target lower')
    bound=exact(lower['lower']);physical=min(ux,uy)
    need(bound<=physical,'Lower contradicts an admitted physical upper')
    variance=sum(((a-b)*(a-b) for a,b in zip(x,y)),Q(0))
    upper=wl*ux+wr*uy-(BETA/2)*wl*wr*variance
    loads=tuple(wl*a+wr*b for a,b in zip(x,y))  # For agreement only, not objective evaluation.
    gap=bound-upper
    floor=lambda v:(v.numerator*SCALE)//v.denominator
    ceil=lambda v:-((-v.numerator*SCALE)//v.denominator)
    units=dict(lower_floor_units=floor(bound),upper_ceil_units=ceil(upper),
               gap_floor_units=floor(gap),physical_upper_ceil_units=ceil(physical))
    for label,obj in objects.items():need(seal(obj)==seals[label],'Projected input changed during arithmetic: '+label)
    return dict(status='POSITIVE_TARGET_GAP_CERTIFIED' if gap>0 else 'TARGET_GAP_UNRESOLVED',
        target_identity=target_identity,lower=bound,upper=upper,gap=gap,physical_upper=physical,loads=list(loads),ops=Q(200),
        endpoint_variance=variance,lambda_left=wl,lambda_right=wr,**units,
        lower_outward=_display(units['lower_floor_units']),upper_outward=_display(units['upper_ceil_units']),
        gap_lower_outward=_display(units['gap_floor_units']),physical_upper_outward=_display(units['physical_upper_ceil_units']),
        objective_method='Weighted endpoint objectives minus exact quadratic variance',
        no_new_physical_replay=True,no_new_tree_check=True,exact_optima_known=False,
        physical_lower_not_CH=True,old_model_result_unchanged=True)


def literal_qualification():
    """New thirty-coordinate toy summaries only, MOCK admissions, no public work."""
    import copy
    controls=[]
    def endpoint(first,second=Q(0)):
        values=[Q(first),Q(second)]+[Q(0)]*28
        objective=200+A*(first+second)+BETA*(first*first+second*second)/2
        replay=dict(strict_pass=True,physical_strict_pass=True,objective_is_certified_physical_upper=True,
                    loads_exact=values,ops_exact=Q(200),objective_exact=objective)
        return dict(status='ADMITTED_TARGET_PRIMAL',target_identity=IDENTITY,loads_exact=values,
            ops_exact=Q(200),objective_exact=objective,fleet_count=2,a_exact=[A]*30,b_exact=[BETA]*30,
            face_attempts=1,physical_replays=1,replay=replay)
    left,right=endpoint(Q(0)),endpoint(Q(2))
    weights=dict(lambda_left='1/2',lambda_right='1/2',source_revision='a'*40,path='SYNTHETIC_LITERAL/weights')
    lower=dict(status='COMPLETE_TARGET_BOUND',target_identity=IDENTITY,lower=Q(200))
    base=dict(left=left,right=right,weights=weights,lower=lower)
    def evaluate(objects=base,identity=IDENTITY,allow=True,frozen=None):
        stored={k:seal(v) for k,v in objects.items()} if frozen is None else frozen
        callback=lambda label,obj:allow and obj is objects[label] and seal(obj)==stored[label]
        return check(objects['left'],objects['right'],objects['weights'],objects['lower'],identity,callback,stored)
    answer=evaluate()
    need(answer['upper']==200+A+BETA/2 and answer['gap']==-A-BETA/2
         and answer['status']=='TARGET_GAP_UNRESOLVED','Toy variance anchor')
    need(_display(-1)=='-0.000001','Negative outward display anchor')
    controls.append(dict(id='thirty-load-variance-and-negative-gap-anchor',passed=True))
    positive=dict(left=endpoint(Q(2)),right=endpoint(Q(0),Q(2)),weights=copy.deepcopy(weights),
        lower=dict(status='COMPLETE_TARGET_BOUND',target_identity=IDENTITY,lower=200+2*A+2*BETA))
    certified=evaluate(positive)
    need(certified['status']=='POSITIVE_TARGET_GAP_CERTIFIED' and certified['gap']==BETA
         and certified['upper']==200+2*A+BETA,'Positive variance-gap anchor')
    controls.append(dict(id='positive-variance-gap-anchor',passed=True))
    def reject(name,action):
        try:action()
        except (ValueError,KeyError,TypeError,ZeroDivisionError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('Literal corruption accepted: '+name)
    reject('wrong-target-identity',lambda:evaluate(identity='WRONG'))
    reject('source-admission-denied',lambda:evaluate(allow=False))
    for name,mutation in (
        ('changed-objective',lambda o:o['right'].__setitem__('objective_exact',0)),
        ('changed-replay-objective',lambda o:o['right']['replay'].__setitem__('objective_exact',0)),
        ('changed-supply',lambda o:o['left']['a_exact'].__setitem__(0,'1/5')),
        ('changed-weights',lambda o:o['weights'].__setitem__('lambda_right','1/3')),
        ('negative-load',lambda o:o['left']['loads_exact'].__setitem__(0,-1)),
        ('missing-load',lambda o:o['left']['loads_exact'].pop()),
        ('missing-strict-replay',lambda o:o['left']['replay'].__setitem__('strict_pass',False)),
        ('replay-count',lambda o:o['left'].__setitem__('physical_replays',2)),
        ('boolean-face-count',lambda o:o['left'].__setitem__('face_attempts',True)),
        ('lower-above-upper',lambda o:o['lower'].__setitem__('lower',201)),
    ):
        changed=copy.deepcopy(base);mutation(changed)
        reject(name,lambda changed=changed:evaluate(changed))
    edited=copy.deepcopy(base);old_seals={k:seal(v) for k,v in edited.items()};edited['weights']['path']='CHANGED'
    reject('edited-same-object-after-seal',lambda:evaluate(edited,frozen=old_seals))
    reject('missing-seals',lambda:check(left,right,weights,lower,IDENTITY,lambda label,obj:True,None))
    return dict(status='PASS',controls=controls,native_calls=0,public_inputs_read=False,
        scope='New summary/variance/admission literals only; no physical or target proof replay')
