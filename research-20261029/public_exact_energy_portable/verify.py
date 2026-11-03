"""Standalone NEW exact-consumption retained proof check; stdlib, no solver/Git."""
import argparse
import copy
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import resource
import sys
import time
import types

OLD_ID='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
CASE_TOKEN=OLD_ID+'::exact-consumption-v1'
DEFAULT_LIMITS=dict(seconds=500,checker_seconds=450,rss_bytes=2*1024**3,
    tree_nodes=375,tree_depth=375,compressed_bytes=512*1024**2,
    decompressed_bytes=512*1024**2,total_bytes=1024**3)
MEMBERS=('checkers/physical.py','checkers/semantic.py','checkers/tree.py',
    'evidence/case.json','evidence/physical.json','evidence/response.json',
    'evidence/tree.json.gz','evidence/claims.json','verify.py','README.md')


def need(ok,message):
    if not ok:raise ValueError(message)


def decode(raw):
    def pairs(items):
        out={}
        for key,value in items:
            need(key not in out,'Duplicate JSON key');out[key]=value
        return out
    def invalid(value):raise ValueError('Nonfinite JSON token')
    def floating(token):
        need(len(token)<=128,'JSON numeric token ceiling')
        value=float(token);need(math.isfinite(value),'Nonfinite JSON number');return value
    def integer(token):
        need(len(token)<=128,'JSON integer ceiling');return int(token)
    # Preserve original nonenergy int/float semantics. Energy/proof rationals
    # remain strings until their guarded parsers, never decimal-to-float energy.
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,
                      parse_float=floating,parse_int=integer)


def q(value):
    need(type(value) in (int,str) or isinstance(value,Q),'Exact rational type')
    if type(value) is str:
        need(len(value)<=32768 and re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*)?',value) is not None,
             'Bounded integer/fraction syntax only')
    value=Q(value)
    need(max(value.numerator.bit_length(),value.denominator.bit_length())<=32768,'Rational bit ceiling')
    return value


def binary_number(value):
    need(type(value) in (int,float) and (type(value) is int or math.isfinite(value)),
         'Original nonenergy numeric type')
    result=Q(value);need(max(result.numerator.bit_length(),result.denominator.bit_length())<=32768,'Nonenergy bit ceiling')
    return result


def seal(value):
    if isinstance(value,Q):return ('Q',value.numerator,value.denominator)
    if type(value) is float:
        need(math.isfinite(value),'Nonfinite model field');return ('float',value.hex())
    if type(value) is dict:
        need(all(type(k) is str for k in value),'Projected model keys must be strings')
        return ('dict',tuple((k,seal(value[k])) for k in sorted(value)))
    if type(value) in (list,tuple):return (type(value).__name__,tuple(seal(x) for x in value))
    need(type(value) in (str,int,bool,type(None)),'Unprojected model object')
    return (type(value).__name__,value)


def project_candidate(packet):
    """Read top-level NEW candidate only; do not traverse diagnostic objects."""
    need(packet['status']=='ADMITTED_TARGET_PRIMAL' and packet['target_identity']==CASE_TOKEN,'Target point identity')
    value=packet['candidate']
    ids=list(value['selected_movement_ids']);rows=value['charge_by_interval']
    need(0<len(ids)<=5000 and all(type(x) is str and 0<len(x)<=1024 for x in ids)
         and len(set(ids))==len(ids),'Selected movement identifiers')
    need(type(rows) is list and len(rows)<=10000,'Allocation denominator')
    records=[];seen=set()
    for row in rows:
        mid,k=row['movement'],row['interval']
        need(type(mid) is str and mid in ids and type(k) is int and k>=0,'Allocation key')
        need((mid,k) not in seen,'Duplicate allocation');seen.add((mid,k))
        energy=q(row['energy']);need(energy>=0,'Negative charge')
        records.append(dict(movement=mid,interval=k,energy=energy))
    claim={name:packet[name] for name in ('loads_exact','ops_exact','objective_exact','fleet_count')}
    need(type(claim['loads_exact']) is list and len(claim['loads_exact'])==30,'Point load dimension')
    claim['loads_exact']=[q(x) for x in claim['loads_exact']]
    claim['ops_exact']=q(claim['ops_exact']);claim['objective_exact']=q(claim['objective_exact'])
    need(type(claim['fleet_count']) is int and claim['fleet_count']==2,'Two-bus retained endpoint')
    return dict(target_identity=CASE_TOKEN,candidate=dict(selected_movement_ids=ids,charge_by_interval=records),claim=claim)


def claims_record(packet):
    names=('status','target_identity','lambda_left','lambda_right','lower','upper','gap','physical_upper')
    result={k:packet[k] for k in names}
    need(result['status']=='POSITIVE_TARGET_GAP_CERTIFIED' and result['target_identity']==CASE_TOKEN,'Closed target claim identity')
    for name in names[2:]:result[name]=q(result[name])
    need(result['lambda_left']>=0 and result['lambda_right']>=0 and
         result['lambda_left']+result['lambda_right']==1,'Fixed mixture simplex')
    need(result['gap']==result['lower']-result['upper'] and result['gap']>0
         and result['lower']<=result['physical_upper'],'Closed claims consistency')
    return result


def validate_proof(packet,expected_nodes=375):
    need(type(packet) is dict and set(packet)=={'target_identity','root','nodes'}
         and packet['target_identity']==CASE_TOKEN,'Normalized target proof schema')
    nodes=packet['nodes'];need(type(nodes) is dict and len(nodes)==expected_nodes,'Fixed node denominator')
    output={}
    for name,node in nodes.items():
        need(type(name) is str and 0<len(name)<=4096 and type(node) is dict,'Node identity')
        kind=node['kind']
        if kind=='branch':
            need(set(node)=={'kind','movement','children'} and type(node['movement']) is str,'Branch schema')
            children=node['children']
            need(type(children) is dict and set(children)=={'0','1'} and
                 all(type(x) is str for x in children.values()) and children['0']!=children['1'],'Both binary children')
            output[name]=dict(kind=kind,movement=node['movement'],children=dict(children))
        else:
            need(kind in ('bound','infeasible') and set(node)=={'kind','certificate'},'Algebraic leaf only')
            cert=node['certificate'];expected={'multipliers'} if kind=='infeasible' else {'multipliers','tangent_loads'}
            need(type(cert) is dict and set(cert)==expected,'No inherited scalar/status may enter target certificate')
            multipliers=cert['multipliers'];need(type(multipliers) is dict and len(multipliers)<=100000,'Multiplier denominator')
            need(all(type(k) is str and 0<len(k)<=1024 for k in multipliers),'Multiplier row identity')
            clean=dict(multipliers={k:q(v) for k,v in multipliers.items()})
            if kind=='bound':
                need(type(cert['tangent_loads']) in (list,tuple) and len(cert['tangent_loads'])==30,'Tangent dimension')
                clean['tangent_loads']=[q(v) for v in cert['tangent_loads']]
            output[name]=dict(kind=kind,certificate=clean)
    seen=set();stack=[(packet['root'],0)]
    while stack:
        name,depth=stack.pop()
        need(name in output and name not in seen and depth<=expected_nodes,'Missing/shared/cyclic/deep node')
        seen.add(name);node=output[name]
        if node['kind']=='branch':stack.extend((child,depth+1) for child in node['children'].values())
    need(seen==set(output),'Unreachable proof node')
    return dict(root=packet['root'],nodes=output)


def literal_qualification():
    """NEW adapter seams only; no public data, physical replay or tree algebra."""
    import copy
    controls=[]
    def rejects(name,action):
        try:action()
        except (ValueError,KeyError,TypeError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('Adapter corruption accepted: '+name)
    parsed=decode(b'{"capacity":400.0,"energy":"26/5"}')
    need(type(parsed['capacity']) is float and parsed['energy']=='26/5','Descriptor numeric-type anchor')
    point=dict(status='ADMITTED_TARGET_PRIMAL',target_identity=CASE_TOKEN,
        candidate=dict(selected_movement_ids=['m'],charge_by_interval=[dict(movement='m',interval=0,energy='0')]),
        loads_exact=['0']*30,ops_exact='200',objective_exact='200',fleet_count=2,
        problem={0:object()},recovery=object())
    projected=project_candidate(point);need(projected['candidate']['charge_by_interval'][0]['energy']==0,'Top-level candidate/zero-record anchor')
    leaf=dict(kind='bound',certificate=dict(multipliers={},tangent_loads=['0']*30))
    proof=dict(target_identity=CASE_TOKEN,root='r',nodes={'r':dict(kind='branch',movement='m',children={'0':'a','1':'b'}),'a':copy.deepcopy(leaf),'b':copy.deepcopy(leaf)})
    validate_proof(proof,3)
    rejects('duplicate-json',lambda:decode(b'{"x":1,"x":2}'))
    rejects('nonfinite-json',lambda:decode(b'{"x":1e9999}'))
    rejects('exponent-rational',lambda:q('1e999999999'))
    rejects('boolean-rational',lambda:q(True))
    wrong=dict(point);wrong.pop('candidate');rejects('historical-wrapper-not-target',lambda:project_candidate(wrong))
    wrong=copy.deepcopy(projected);wrong['candidate']['charge_by_interval'][0]['interval']=True
    bad=dict(point,candidate=wrong['candidate']);rejects('boolean-interval',lambda:project_candidate(bad))
    bad=dict(point,candidate=dict(selected_movement_ids=['m'],charge_by_interval=[dict(movement='m',interval=0,energy='0')]*2))
    rejects('duplicate-allocation',lambda:project_candidate(bad))
    wrong=copy.deepcopy(proof);wrong['nodes']['a']['certificate']['claimed_lower']='0';rejects('old-scalar-leaf',lambda:validate_proof(wrong,3))
    wrong=copy.deepcopy(proof);del wrong['nodes']['r']['children']['1'];rejects('omitted-binary-child',lambda:validate_proof(wrong,3))
    wrong=copy.deepcopy(proof);wrong['nodes']['r']['children']['1']='a';rejects('shared-child',lambda:validate_proof(wrong,3))
    claim=dict(status='POSITIVE_TARGET_GAP_CERTIFIED',target_identity=CASE_TOKEN,lambda_left='1/2',lambda_right='1/2',lower='2',upper='1',gap='1',physical_upper='3')
    wrong=dict(claim,target_identity=OLD_ID);rejects('old-law-claim',lambda:claims_record(wrong))
    wrong=dict(claim,lambda_right='1/3');rejects('changed-fixed-simplex',lambda:claims_record(wrong))
    return dict(status='PASS',anchors=3,negative_controls=controls,native_calls=0,
                scope='New target descriptor/top-level-candidate/stripped-proof adapter only; no scientific recheck')


def _module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result


def verify_bundle(directory,expected_manifest_sha256,limits=None):
    limits=dict(DEFAULT_LIMITS,**(limits or {}));started=time.monotonic();root=Path(directory).resolve();steps=[]
    def gate():
        need(time.monotonic()-started<limits['seconds'],'Verification wall checkpoint')
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        need(rss<=limits['rss_bytes'],'Observed RSS ceiling')
    try:
        need(type(expected_manifest_sha256) is str and re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256) is not None,'Trusted64hex manifest digest')
        gate();path=root/'MANIFEST.json'
        need(not path.is_symlink() and path.stat().st_size<=1024**2,'Manifest path/size')
        raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==expected_manifest_sha256,'Manifest integrity')
        manifest=decode(raw)
        need(manifest['schema']=='exact-energy-sign-bundle-v1' and manifest['case_token']==CASE_TOKEN
             and manifest['purpose']=='local author review' and manifest['redistribution_status']=='UNRESOLVED','Manifest model/scope')
        need(set(manifest['files'])==set(MEMBERS),'Exact member closure')
        buffers={};total=0
        for name in MEMBERS:
            gate();path=root/name
            need(not path.is_symlink() and path.resolve().is_relative_to(root),'Unsafe member path')
            need(path.stat().st_size<=limits['compressed_bytes'],'Member byte ceiling')
            value=path.read_bytes();total+=len(value);need(total<=limits['total_bytes'],'Total byte ceiling')
            authority=manifest['files'][name]
            need(type(authority['sha256']) is str and re.fullmatch('[0-9a-f]{64}',authority['sha256']) is not None,'Member digest syntax')
            need(len(value)==authority['bytes'] and hashlib.sha256(value).hexdigest()==authority['sha256'],'Member integrity: '+name)
            buffers[name]=value
        def packet(name):
            gate();value=buffers.pop(name)
            if name.endswith('.gz'):
                with gzip.GzipFile(fileobj=io.BytesIO(value)) as stream:value=stream.read(limits['decompressed_bytes']+1)
                need(len(value)<=limits['decompressed_bytes'],'Decompressed byte ceiling')
            return decode(value)
        physical=_module('portable_target_physical',buffers.pop('checkers/physical.py'))
        semantic=_module('portable_target_semantic',buffers.pop('checkers/semantic.py'))
        tree=_module('portable_target_tree',buffers.pop('checkers/tree.py'))
        case=packet('evidence/case.json');claims=claims_record(packet('evidence/claims.json'))
        need(len(case['trips'])==37 and len(case['movements'])==1370 and
             sum(len(m['legs']) for m in case['movements'])==2648,'Target model denominator')
        case_seal=seal(case)
        gate();ledger=semantic._reconstruct(case)
        need(ledger[5]['minimum_fleet']>=2,'Uncovered zero/one-bus fleets')
        steps.append(dict(stage='target-ledger',status='RECONSTRUCTED',minimum_fleet=ledger[5]['minimum_fleet']))
        points=[]
        for name in ('evidence/physical.json','evidence/response.json'):
            item=packet(name);need(item['target_identity']==CASE_TOKEN,'Point target identity')
            gate();audit=physical.verify(case,item['candidate'])
            need(seal(case)==case_seal,'Physical checker mutated model')
            need(all(audit.get(k) is True for k in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),'Strict target physical failure')
            loads=list(map(q,audit['loads_exact']));ops=q(audit['ops_exact']);objective=q(audit['objective_exact']);claim=item['claim']
            need(len(loads)==30 and all(x>=0 for x in loads) and ops==200 and claim['fleet_count']==2,'Physical endpoint scope')
            need(loads==list(map(q,claim['loads_exact'])) and ops==q(claim['ops_exact']) and objective==q(claim['objective_exact']),'Fresh replay/point claim mismatch')
            points.append(dict(loads=loads,ops=ops,objective=objective))
            steps.append(dict(stage=name,status='STRICT_PHYSICAL_PASS'))
        wl,wr=claims['lambda_left'],claims['lambda_right'];a,b=Q(float(.2)),Q(float(1/900))
        loads=[wl*x+wr*y for x,y in zip(points[0]['loads'],points[1]['loads'])]
        upper=wl*points[0]['ops']+wr*points[1]['ops']+sum((a*x+b*x*x/2 for x in loads),Q(0))
        need(upper==claims['upper'],'Fresh fixed-mixture claim mismatch')
        steps.append(dict(stage='fixed-mixture',status='FEASIBLE_HULL_UPPER',value=upper))
        proof=validate_proof(packet('evidence/tree.json.gz'),limits['tree_nodes'])
        # Already freshly reconstructed once; no serialized ledger is authority.
        def reconstructed(supplied):
            need(supplied is case and seal(case)==case_seal,'Foreign/mutated descriptor')
            return copy.deepcopy(ledger)
        context=tree.prepare(case,reconstructed,mode='quadratic',fleet_count=2,case_token=CASE_TOKEN)
        floor=dict(case_token=CASE_TOKEN,minimum_fleet=3,proof_kind='quadratic_affine_service_floor',scope='physical_ge_3',
            lower_bound=3*binary_number(case['vehicle_cost'])+a*sum((q(t['energy_kwh']) for t in case['trips']),Q(0))/binary_number(case['efficiency']))
        allowance=min(limits['checker_seconds'],limits['seconds']-(time.monotonic()-started));need(allowance>0,'Tree funding exhausted')
        audit=tree.verify_tree(context,proof,exclusion=floor,admit_transfer=lambda x:x is floor,
            limits=dict(nodes=limits['tree_nodes'],depth=limits['tree_depth'],operations=100000000,fraction_bits=32768,seconds=allowance))
        need(audit.get('status')=='COMPLETE' and audit.get('complete') is True and audit.get('checked_nodes')==375
             and isinstance(audit.get('global_lower_bound'),Q),'Complete target coverage unavailable')
        need(seal(case)==case_seal,'Tree checker mutated model')
        lower=audit['global_lower_bound'];physical_upper=min(p['objective'] for p in points)
        need(lower==claims['lower'] and physical_upper==claims['physical_upper'] and lower-upper==claims['gap'],'New target bound claims differ')
        need(lower>upper and lower<=physical_upper,'Target strict separation/physical consistency')
        gate();steps.append(dict(stage='target-tree',status='GLOBAL_PHYSICAL_LOWER',value=lower,checked_nodes=375))
        scale=10**6;floor6=lambda x:x.numerator*scale//x.denominator;ceil6=lambda x:-((-x.numerator*scale)//x.denominator)
        return dict(status='PASS',case_token=CASE_TOKEN,physical_lower=lower,physical_upper=physical_upper,
            hull_upper=upper,gap_lower=lower-upper,steps=steps,native_calls=0,physical_replays=2,tree_checks=1,
            outward=dict(scale=scale,physical_lower_floor_units=floor6(lower),physical_upper_ceil_units=ceil6(physical_upper),hull_upper_ceil_units=ceil6(upper),gap_lower_floor_units=floor6(lower-upper)),
            declared_rational_descriptor_only=True,raw_source_transformation_rechecked=False,external_replication=False,
            redistribution_status='UNRESOLVED',elapsed_s=time.monotonic()-started)
    except Exception as exc:
        return dict(status='FAIL_OR_UNRESOLVED',reason=type(exc).__name__+': '+str(exc),steps=steps,native_calls=0,elapsed_s=time.monotonic()-started)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    result=verify_bundle(Path(__file__).resolve().parent,args.manifest_sha256)
    with Path(args.output).open('x') as stream:json.dump(result,stream,default=str,indent=2,allow_nan=False);stream.write('\n')
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
