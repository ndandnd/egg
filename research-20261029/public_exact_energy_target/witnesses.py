"""Two fixed-route, one-face NEW target primal attempts; no I/O or native API.

Caller admits cached source/input bytes and supplies qualified modules. Historical
charges are proposals only; every admitted point gets one new physical screen.
"""
import copy
from fractions import Fraction as Q
import time

TARGET_IDENTITY='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7::exact-consumption-v1'
ENDPOINTS=('INCUMBENT_ROUTES','RESPONSE_ROUTES')
DEFAULT_LIMITS=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=90)

def need(ok,message):
    if not ok:raise ValueError(message)

def exact(value):
    need(type(value) in (int,str) or isinstance(value,Q),'Proposal energy must be exact, not bool/float')
    if isinstance(value,str):need(len(value)<=16384 and 'e' not in value.lower(),'Proposal token bound/exponent forbidden before Fraction')
    result=Q(value)
    need(max(result.numerator.bit_length(),result.denominator.bit_length())<=16384,'Proposal fraction bound')
    return result

def proposal_from_packet(packet):
    """Project ONLY historical route IDs and rational charge records, no scores.

    Both fixed admitted packet schemas have a recovery.candidate. Caller binds
    the packet to its predetermined Git path/revision before calling this.
    """
    candidate=packet['recovery']['candidate']
    ids=list(candidate['selected_movement_ids']);records=candidate['charge_by_interval']
    need(0<len(ids)<=5000 and all(type(mid) is str for mid in ids) and len(ids)==len(set(ids)),'Proposal route IDs')
    need(isinstance(records,list) and len(records)<=10000,'Proposal coordinate count')
    projected=[];seen=set()
    for row in records:
        need(type(row['movement']) is str and row['movement'] in ids and type(row['interval']) is int and row['interval']>=0,'Proposal coordinate identity')
        key=(row['movement'],row['interval']);need(key not in seen,'Duplicate proposal coordinate');seen.add(key)
        projected.append(dict(movement=key[0],interval=key[1],energy=exact(row['energy'])))
    return dict(selected_movement_ids=ids,charge_by_interval=projected,
        use='Historical routes and charge values as ONE active-face proposal only; no old admission/score transferred')

def construct_witness(target_case,proposal,target_identity,affine,recovery,semantic_reconstruct,physical_verify,limits=None):
    """Return an admitted NEW physical upper or unresolved, never infeasibility.

    affine.build_problem is the frozen exact_fixed_topology builder; recovery is
    the frozen rational helper. semantic_reconstruct is the new target's exact
    six-tuple semantic API. physical_verify is independent_verify.verify.
    Caller freezes exactly one proposal per endpoint, never retries this API.
    """
    started=time.monotonic();calls=0;problem=None;attempt=None
    cap=dict(DEFAULT_LIMITS);cap.update(limits or {})
    result=dict(status='TARGET_PRIMAL_UNRESOLVED',target_identity=target_identity,
        face_attempts=0,physical_replays=0,native_calls=0,topology_infeasibility_claim=False,
        fixed_topology_optimum_claim=False,global_physical_optimum_claim=False)
    try:
        need(target_identity==TARGET_IDENTITY,'Wrong explicit target model')
        need(set(cap)==set(DEFAULT_LIMITS) and all(type(v) is int and 0<v<=DEFAULT_LIMITS[k] for k,v in cap.items()),'Unfrozen/enlarged work limit')
        need(len(target_case['trips'])==37 and len(target_case['movements'])<=5000,'Target domain guard')
        # Freeze a private target copy; callbacks and algebra may not mutate it.
        case=copy.deepcopy(target_case);sealed=copy.deepcopy(case)
        problem=affine.build_problem(case,proposal['selected_movement_ids'],semantic_reconstruct)
        need(case==sealed,'Builder mutated target descriptor')
        need(len(problem['variables'])<=10000 and len(problem['rows'])<=20000,'Fixed problem size guard')
        by_key={}
        for row in proposal['charge_by_interval']:
            key=(row['movement'],row['interval']);need(key not in by_key,'Duplicate charge coordinate');by_key[key]=exact(row['energy'])
        keys=[(v['movement'],v['interval']) for v in problem['variables']]
        need(len(set(keys))==len(keys) and set(keys)==set(by_key),'Old/new charge-coordinate mapping differs')
        values=[by_key[key] for key in keys]
        def screen(c,candidate):
            nonlocal calls
            calls+=1;need(calls==1 and c is case and case==sealed,'Duplicate/mutated/wrong-target physical screen')
            audit=physical_verify(c,candidate)
            need(case==sealed,'Physical screen mutated target descriptor');return audit
        result['face_attempts']=1
        attempt=recovery.recover_primal(problem,dict(values=values),affine,screen,cap)
        result['recovery']=attempt
        need(case==sealed,'Recovery mutated target descriptor')
        if attempt.get('status')!='ADMITTED_PRIMAL':
            need(attempt.get('status')=='PRIMAL_UNRESOLVED','Unknown recovery outcome')
            result['reason']=attempt.get('reason','The single proposed face did not admit a target primal')
        else:
            audit=attempt['replay']
            need(calls==1 and all(audit.get(k) is True for k in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),'Missing NEW strict physical admission')
            loads=list(map(Q,attempt['loads_exact']));need(loads==list(map(Q,audit['loads_exact'])),'Physical/algebraic loads differ')
            objective=Q(attempt['objective_exact']);need(objective==Q(audit['objective_exact']),'Physical/algebraic objectives differ')
            a,b=list(map(Q,problem['a'])),list(map(Q,problem['b']))
            need(len(loads)==len(a)==len(b),'Supply dimension')
            ops=Q(problem['ops']);need(objective==ops+sum((aa*e+bb*e*e/2 for aa,bb,e in zip(a,b,loads)),Q(0)),'Original supply objective identity')
            result.update(status='ADMITTED_TARGET_PRIMAL',physical_upper_certified=True,
                loads_exact=loads,ops_exact=ops,objective_exact=objective,fleet_count=len(problem['routes']),
                a_exact=a,b_exact=b,selected_movement_ids=list(problem['selected_movement_ids']),
                candidate=attempt['candidate'],values=attempt['values'],replay=audit,
                scope='NEW feasible physical upper on ONE frozen topology; no target optimum/support claim')
        result['problem']=problem
    except (ValueError,KeyError,TypeError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(status='TARGET_PRIMAL_UNRESOLVED',reason=type(exc).__name__+': '+str(exc))
        if attempt is not None:result['recovery']=attempt
        if problem is not None:result['problem']=problem
    result.update(physical_replays=calls,elapsed_s=time.monotonic()-started,limits=cap)
    return result

def construct_two(target_case,proposals,target_identity,affine,recovery,semantic_reconstruct,physical_verify,limits=None,checkpoint=None):
    """Exactly two assigned attempts; ordinary failure never erases the other.

    The enclosing worker owns time/resource funding and serialization. Its
    checkpoint(label) may raise a resource fatal before a stage; no retry occurs.
    """
    need(set(proposals)==set(ENDPOINTS),'Both predetermined endpoint proposals required')
    rows=[]
    for label in ENDPOINTS:
        if checkpoint is not None:checkpoint(label)
        result=construct_witness(target_case,proposals[label],target_identity,affine,recovery,semantic_reconstruct,physical_verify,limits)
        rows.append(dict(id=label,status=result['status'],result=result))
    return dict(assigned=list(ENDPOINTS),rows=rows,native_calls=0)
