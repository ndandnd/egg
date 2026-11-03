"""One new terminal-only construction per new raw candidate; no solver/retry."""
import argparse
import copy
from fractions import Fraction as Q
import gc
import gzip
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REL = 'research-20261029/public_energy_witnesses/'
CONSTRUCT = 'research-20261029/public_terminal_certificate/construct.py'
VERIFY = 'research-20261029/public_support_resolution/independent_verify.py'
PRODUCER = 'ef0b088193bc19527476f9db9e632c37379d9a2a'
PROTECTED = '929bd0052b064c2aa9ef10b77fa067b70c7653af'
CASE_REV = '253c1e29295e766b3889fc8f5c28d9808e00b3d6'
RAW_REV = 'f8a043132863db5ce631d5691d35b5d788bdf256'
CASE_ID = '1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
PATHS = dict(case='research-20261029/public_support_resolution/attempt01/case_descriptor.json',
    protected_candidate='research-20261029/public_terminal_certificate/cycle01/new_candidate.json',
    protected_replay='research-20261029/public_terminal_certificate/cycle01/independent_replay.json',
    transfer='research-20261029/public_terminal_certificate/TRANSFER_AUTHORITY.json',
    MIQP_new='research-20261029/public_energy_flow/attempt01/MIQP.json.gz',
    PRICE_MIP_new='research-20261029/public_energy_flow/attempt01/PRICE_MIP.json.gz')
INPUT_REV = dict(case=CASE_REV,protected_candidate=PROTECTED,protected_replay=PROTECTED,
                 transfer=PROTECTED,MIQP_new=RAW_REV,PRICE_MIP_new=RAW_REV)
NEW_IDS = ('MIQP_new','PRICE_MIP_new')
PAIRS = (('protected','MIQP_new'),('protected','PRICE_MIP_new'),('MIQP_new','PRICE_MIP_new'))


def encode(value):
    if isinstance(value,Q):
        return str(value)
    raise TypeError(type(value).__name__)


def write(path,value,compressed=False):
    if compressed:
        with path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as packed:
                import io
                with io.TextIOWrapper(packed,encoding='utf-8') as stream:
                    json.dump(value,stream,default=encode,allow_nan=False)
                    stream.write('\n')
    else:
        with path.open('x') as stream:
            json.dump(value,stream,indent=2,default=encode,allow_nan=False)
            stream.write('\n')


def rational(value):
    if isinstance(value,bool):
        raise ValueError('Boolean numeric input')
    return Q(value)


def market_component(loads,ops,a,b):
    loads = tuple(map(rational,loads))
    ops = rational(ops)
    if len(loads) != len(a) or len(a) != len(b) or any(e < 0 for e in loads):
        raise ValueError('Invalid component load')
    return dict(loads=loads,ops=ops,
                objective=ops+sum((at*x+bt*x*x/2 for at,bt,x in zip(a,b,loads)),Q(0)))


def mixture(left,right,a,b):
    """Analytic minimizer on this whole-plan segment, right weight lambda."""
    if len(left['loads']) != len(right['loads']) or len(a) != len(b) or len(a) != len(left['loads']) or any(v < 0 for v in b):
        raise ValueError('Invalid convex segment dimensions/curvature')
    delta = [y-x for x,y in zip(left['loads'],right['loads'])]
    A = right['ops']-left['ops']+sum(((at+bt*x)*d for at,bt,x,d in zip(a,b,left['loads'],delta)),Q(0))
    B = sum((bt*d*d/2 for bt,d in zip(b,delta)),Q(0))
    weight = min(Q(1),max(Q(0),-A/(2*B))) if B else Q(int(A < 0))
    loads = [(1-weight)*x+weight*y for x,y in zip(left['loads'],right['loads'])]
    ops = (1-weight)*left['ops']+weight*right['ops']
    value = left['objective']+A*weight+B*weight*weight
    return dict(lambda_right=weight,lambda_left=1-weight,loads=loads,ops=ops,objective=value,
        weight_minimizer_interval=(Q(0),Q(1)) if B == A == 0 else (weight,weight),
        linear_coefficient=A,quadratic_coefficient=B)


def verify_mixture(left,right,a,b,answer):
    """Independent direct quadratic evaluation and one-dimensional KKT test.

    Does not trust the analytic A/B coefficients or claimed endpoint cost.
    """
    if (len(left['loads']) != len(right['loads']) or len(a) != len(b)
            or len(a) != len(left['loads']) or any(value < 0 for value in b)):
        raise ValueError('Independent check requires matching dimensions and convex curvature')
    w = rational(answer['lambda_right'])
    if not 0 <= w <= 1 or rational(answer['lambda_left']) != 1-w:
        raise ValueError('Invalid weights')
    mean = tuple((1-w)*x+w*y for x,y in zip(left['loads'],right['loads']))
    cost = (1-w)*left['ops']+w*right['ops']
    value = cost+sum((at*e+bt*e*e/2 for at,bt,e in zip(a,b,mean)),Q(0))
    if tuple(map(rational,answer['loads'])) != mean or rational(answer['ops']) != cost or rational(answer['objective']) != value:
        raise ValueError('Direct segment objective/mean mismatch')
    derivative = right['ops']-left['ops']+sum(((at+bt*e)*(y-x)
        for at,bt,e,x,y in zip(a,b,mean,left['loads'],right['loads'])),Q(0))
    if not ((w == 0 and derivative >= 0) or (w == 1 and derivative <= 0) or (0 < w < 1 and derivative == 0)):
        raise ValueError('Segment KKT condition failed')
    curvature = sum((bt*(y-x)**2 for bt,x,y in zip(b,left['loads'],right['loads'])),Q(0))
    interval = (Q(0),Q(1)) if curvature == 0 and derivative == 0 else (w,w)
    if tuple(map(rational,answer['weight_minimizer_interval'])) != interval:
        raise ValueError('Weight tie interval mismatch')
    return dict(status='PASS',objective_exact=value,derivative=derivative,
                curvature=curvature,check='direct quadratic plus endpoint/interior KKT')


def rejected(name,action):
    try:
        action()
    except (ValueError,AssertionError):
        return dict(id=name,rejected=True)
    raise ValueError('Negative mixture control accepted: '+name)


def qualification():
    a,b = (Q(0),),(Q(1),)
    left = market_component((0,),1,a,b)
    right = market_component((2,),0,a,b)
    result = mixture(left,right,a,b)
    check = verify_mixture(left,right,a,b,result)
    if result['lambda_right'] != Q(1,4) or result['objective'] != Q(7,8):
        raise ValueError('Literal mixture arithmetic failed')
    wrong_weight = copy.deepcopy(result)
    # Recompute the wrong weight's mean/cost correctly so only KKT can reject.
    wrong_weight.update(lambda_right=Q(1,2),lambda_left=Q(1,2),loads=[Q(1)],
                        ops=Q(1,2),objective=Q(1),weight_minimizer_interval=(Q(1,2),Q(1,2)))
    wrong_objective = copy.deepcopy(result)
    wrong_objective['objective'] += Q(1,100)
    controls = [rejected('changed-weight-KKT',lambda:verify_mixture(left,right,a,b,wrong_weight)),
                rejected('changed-objective',lambda:verify_mixture(left,right,a,b,wrong_objective))]
    return dict(status='PASS',result=result,independent_check=check,negative_controls=controls,
                scope='New abstract mixture helper only; no old construction/replay qualification repeated')


def admit_protected(authority,candidate,audit,n):
    expected = dict(status='QUALIFIED_TRANSFER',producer_source_revision=PRODUCER,
        producer_frozen_control='6ed44942',producer_namespace='research-20261029/public_terminal_certificate/cycle01',
        case_input_revision=CASE_REV,case_path=PATHS['case'],case_identity=CASE_ID,
        candidate_path=PATHS['protected_candidate'],replay_path=PATHS['protected_replay'],
        results_path='research-20261029/public_terminal_certificate/cycle01/results.json',
        verifier_source_path=VERIFY,candidate_fields=['selected_movement_ids','charge_by_interval'],
        fleet_count=2,producer_exit=0)
    if any(authority.get(k) != v for k,v in expected.items()):
        raise ValueError('Protected source-bound authority mismatch')
    for key in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper','worker_reaped','resource_pass'):
        if authority.get(key) is not True:
            raise ValueError('Protected transfer flag failed: '+key)
    if (any(audit.get(k) is not True for k in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper'))
        or rational(audit['objective_exact']) != rational(authority['upper_exact'])
        or len(audit['routes']) != 2 or set(candidate) != set(expected['candidate_fields'])):
        raise ValueError('Protected replay/upper contract mismatch')
    loads = tuple(map(rational,audit['loads_exact']))
    if len(loads) != n or any(x < 0 for x in loads):
        raise ValueError('Protected load dimensions/sign invalid')
    return dict(loads=loads,ops=rational(audit['ops_exact']),objective=rational(audit['objective_exact']),
                source='qualified immutable transfer; no repeated physical replay',is_new_delivery=False)


def usage():
    own,children = resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime,
                rss_bytes=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    cache,manifest,components = {},{},{}
    rows,pair_rows,fatals = [],[],[]
    q0 = dict(status='UNATTEMPTED')
    try:
        if sys.flags.optimize:
            raise ValueError('Assertions must be enabled')
        source_specs = [(REL+name,args.source_revision) for name in ('worker.py','run.py','PROTOCOL.md')]
        source_specs += [(CONSTRUCT,PRODUCER),(VERIFY,PRODUCER)]
        input_specs = [(PATHS[name],INPUT_REV[name]) for name in PATHS]
        for relative,revision in source_specs+input_specs:
            raw = (ROOT/relative).read_bytes()
            expected = subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+relative],cwd=ROOT,timeout=10)
            if raw != expected:
                raise ValueError('Stale or changed consumed buffer: '+relative)
            cache[relative] = raw
            manifest[relative] = dict(revision=revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        del expected
        write(out/'admission.json',manifest)
        q0 = qualification()
        write(out/'Q0.json',q0)
        namespaces = []
        for relative in (CONSTRUCT,VERIFY):
            namespace = {'__name__':relative,'__file__':str(ROOT/relative)}
            exec(compile(cache[relative],namespace['__file__'],'exec'),namespace)
            namespaces.append(namespace)
        construct,verify = namespaces[0]['construct'],namespaces[1]['verify']
        case = json.loads(cache[PATHS['case']])
        n = len(case['market_edges_min'])-1
        a,b = (Q(float(.2)),)*n,(Q(float(1/900)),)*n
        authority = json.loads(cache[PATHS['transfer']])
        protected_candidate = json.loads(cache[PATHS['protected_candidate']])
        protected_audit = json.loads(cache[PATHS['protected_replay']])
        components['protected'] = admit_protected(authority,protected_candidate,protected_audit,n)
        if rational(protected_audit['market_a_exact']) != a[0] or rational(protected_audit['market_b_exact']) != b[0]:
            raise ValueError('Protected market differs from original binary coefficients')
        del protected_candidate,protected_audit,authority
        for name in NEW_IDS:
            row = dict(id=name,status='ATTEMPTED',construction_attempts=0,independent_replays=0)
            rows.append(row)
            # Full decode is transient; no ledger/certificate/objective content
            # of the old raw packet is examined or used as proof.
            packet = json.loads(gzip.decompress(cache[PATHS[name]]))
            if packet.get('id') != name.replace('_new','') or not isinstance(packet.get('native'),dict):
                raise ValueError('Raw packet state/configuration mismatch')
            native = packet['native']
            row['recorded_native_status'] = {k:native.get(k) for k in ('raw_status','solution_count','optimize_called','physical_feasibility','exact_certificate')}
            old_replay = packet.get('replay',{})
            row['recorded_replay_status'] = {k:old_replay.get(k) for k in ('strict_pass','physical_strict_pass','classification','objective_is_certified_physical_upper')}
            rawcandidate = native.get('candidate')
            del packet,native,old_replay
            gc.collect()
            detail = dict(id=name,recorded_native_status=row['recorded_native_status'],recorded_replay_status=row['recorded_replay_status'])
            if rawcandidate is None:
                row.update(status='MISSING_RAW_CANDIDATE',reason='No candidate in the assigned immutable packet')
            else:
                row['construction_attempts'] = 1
                try:
                    new,changes = construct(case,rawcandidate)
                except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError,OverflowError) as exc:
                    row.update(status='CONSTRUCTION_FAILED',reason=type(exc).__name__+': '+str(exc))
                else:
                    detail.update(candidate=new,changes=changes)
                    row['independent_replays'] = 1
                    audit = verify(case,new)
                    detail['independent_replay'] = audit
                    if (audit.get('strict_pass') is True and audit.get('physical_strict_pass') is True
                            and audit.get('objective_is_certified_physical_upper') is True):
                        component = market_component(audit['loads_exact'],audit['ops_exact'],a,b)
                        if component['objective'] != rational(audit['objective_exact']):
                            raise ValueError('New admitted objective arithmetic mismatch')
                        component.update(is_new_delivery=True,source='one terminal-only construction plus one strict independent replay')
                        components[name] = component
                        row.update(status='ADMITTED',upper_exact=component['objective'],fleet_count=len(audit['routes']),
                                   changed_cells=len(changes['changed_cells']))
                    else:
                        row.update(status='STRICT_REPLAY_FAILED',reason='New construction failed independent strict admission')
            detail['outcome'] = dict(row)
            write(out/(name+'.json.gz'),detail,compressed=True)
            write(out/(name+'.status.json'),row)
            del rawcandidate,detail
            gc.collect()
        for left_name,right_name in PAIRS:
            label = left_name+'__'+right_name
            row = dict(id=label,left=left_name,right=right_name,status='ATTEMPTED')
            pair_rows.append(row)
            absent = [name for name in (left_name,right_name) if name not in components]
            if absent:
                row.update(status='MISSING_COMPONENT',missing=absent)
            else:
                answer = mixture(components[left_name],components[right_name],a,b)
                check = verify_mixture(components[left_name],components[right_name],a,b,answer)
                row.update(status='ADMITTED_HULL_UPPER',mixture=answer,independent_check=check,
                           hull_upper_exact=answer['objective'],physical_components_certified=True,
                           hull_optimality_claim=False,physical_executability_of_mean_claim=False)
            write(out/(label+'.json'),row)
    except BaseException as exc:
        reason = type(exc).__name__+': '+str(exc)
        fatals.append(reason)
        for row in rows+pair_rows:
            if row['status'] == 'ATTEMPTED':
                row.update(status='FATAL',reason=reason)
        if q0['status'] == 'UNATTEMPTED':
            q0 = dict(status='FAILED_OR_UNATTEMPTED',reason=reason)
    for name in NEW_IDS:
        if not any(row['id'] == name for row in rows):
            rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier source/configuration/qualification fatal'))
    for left,right in PAIRS:
        name = left+'__'+right
        if not any(row['id'] == name for row in pair_rows):
            pair_rows.append(dict(id=name,left=left,right=right,status='UNATTEMPTED',reason='earlier fatal'))
    observation = usage()
    elapsed = time.monotonic()-started
    resource_pass = observation['cpu_s'] < 100 and elapsed < 150 and observation['rss_bytes'] <= 5*1024**3
    all_delivered = all(r['status'] == 'ADMITTED' for r in rows) and all(r['status'] == 'ADMITTED_HULL_UPPER' for r in pair_rows)
    report = dict(status='FATAL' if fatals else 'PASS' if all_delivered else 'COMPLETED_WITH_FAILURES',
        administrative_complete=not fatals,scientific_all_delivered=all_delivered and not fatals,
        assigned_constructions=2,assigned_pairs=3,qualification=q0,candidate_rows=rows,pair_rows=pair_rows,
        components=components,fatals=fatals,resource_pass=resource_pass,elapsed_s=elapsed,**observation,
        scope='New witness constructions and exact two-plan hull upper bounds; no support-sign or optimality claim')
    write(out/'results.json',report)
    write(out/'worker_receipt.json',dict(status=report['status'],resource_pass=resource_pass,
          administrative_complete=not fatals,elapsed_s=time.monotonic()-started,**observation))
    return 0 if not fatals and resource_pass else 1


if __name__ == '__main__':
    raise SystemExit(main())
