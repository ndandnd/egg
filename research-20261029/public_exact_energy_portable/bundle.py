"""Local-only exact-target bundle assembly; definitions only, no solver/recovery."""
import copy
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import types

TARGET_SOURCE='6665c2b9f045410b4bbf19060b6780b0779f5534'
TARGET_OUTPUT='d27f9f13ff8e61721dda39ee680be612c01c8ecc'
COMPARISON='fdb85682cf6476227d6fa8fb8258613f512d65d4'
OLD_ID='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
CASE_TOKEN=OLD_ID+'::exact-consumption-v1'
MODEL='research-20261029/public_support_resolution/'
BASE='research-20261029/public_exact_energy_target/attempt01/'
PINS={
 'checkers/physical.py':('3278d50f8323618bd36809b1bbb1a0da081e23ff',MODEL+'independent_verify.py'),
 'checkers/semantic.py':(TARGET_SOURCE,'research-20261029/public_exact_energy_target/target_semantics.py'),
 'checkers/tree.py':('6a171357b65254b52cade63ed95dcce798485f36','research-20261029/public_support_tree/checker.py'),
 'assembly/target_graft.py':(TARGET_SOURCE,'research-20261029/public_exact_energy_target/checker.py'),
 'input/target.json.gz':(TARGET_OUTPUT,BASE+'TARGET.json.gz'),
 'input/physical.json.gz':(TARGET_OUTPUT,BASE+'INCUMBENT_ROUTES.json.gz'),
 'input/response.json.gz':(TARGET_OUTPUT,BASE+'RESPONSE_ROUTES.json.gz'),
 'input/tree.json.gz':('ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9','research-20261029/public_support_tree/attempt01/PUBLIC_TREE.json.gz'),
 'input/refinement.json.gz':('d8e22ffd3753fced3ec825c68714fd549d914230','research-20261029/public_physical_refinement/attempt01/PUBLIC_REFINEMENT.json.gz'),
 'input/comparison.json':(COMPARISON,'research-20261029/public_exact_energy_comparison/attempt01/COMPARISON.json')}
BYTE_LIMIT=512*1024**2


def need(ok,message):
    if not ok:raise ValueError(message)


def decode(raw):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'Duplicate JSON key');result[key]=value
        return result
    def invalid(value):raise ValueError('Nonfinite JSON token')
    def floating(token):
        need(len(token)<=128,'JSON number ceiling');value=float(token)
        need(math.isfinite(value),'Nonfinite JSON number');return value
    def integer(token):
        need(len(token)<=128,'JSON integer ceiling');return int(token)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=floating,parse_int=integer)


def q(value):
    need(type(value) in (int,str) or isinstance(value,Q),'Exact rational type')
    if type(value) is str:
        need(len(value)<=32768 and re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*)?',value) is not None,'Bounded rational syntax')
    result=Q(value);need(max(result.numerator.bit_length(),result.denominator.bit_length())<=32768,'Rational bit ceiling')
    return result


def _json(value):
    def encode(x):
        if isinstance(x,Q):return str(x)
        raise TypeError(type(x).__name__)
    return json.dumps(value,default=encode,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'


def _candidate(packet):
    need(packet['status']=='ADMITTED_TARGET_PRIMAL' and packet['target_identity']==CASE_TOKEN,'Wrong target point')
    value=packet['candidate'];ids=list(value['selected_movement_ids']);rows=value['charge_by_interval']
    need(0<len(ids)<=5000 and len(ids)==len(set(ids)) and all(type(x) is str and 0<len(x)<=1024 for x in ids),'Movement IDs')
    need(type(rows) is list and len(rows)<=10000,'Allocation count')
    cells=[];seen=set()
    for row in rows:
        mid,k=row['movement'],row['interval'];need(type(mid) is str and mid in ids and type(k) is int and k>=0,'Allocation key')
        need((mid,k) not in seen,'Duplicate allocation');seen.add((mid,k))
        energy=q(row['energy']);need(energy>=0,'Negative charge');cells.append(dict(movement=mid,interval=k,energy=energy))
    claim={k:packet[k] for k in ('loads_exact','ops_exact','objective_exact','fleet_count')}
    need(type(claim['loads_exact']) is list and len(claim['loads_exact'])==30 and type(claim['fleet_count']) is int and claim['fleet_count']==2,'Point claim denominator')
    claim['loads_exact']=[q(x) for x in claim['loads_exact']]
    for k in ('ops_exact','objective_exact'):claim[k]=q(claim[k])
    return dict(target_identity=CASE_TOKEN,candidate=dict(selected_movement_ids=ids,charge_by_interval=cells),claim=claim)


def _certificate(cert,kind):
    multipliers=cert['multipliers'];need(type(multipliers) is dict and len(multipliers)<=100000,'Multiplier count')
    need(all(type(k) is str and 0<len(k)<=1024 for k in multipliers),'Multiplier key')
    result=dict(multipliers={k:q(v) for k,v in multipliers.items()})
    if kind=='bound':
        need(type(cert['tangent_loads']) in (list,tuple) and len(cert['tangent_loads'])==30,'Tangent count')
        result.update(tangent_loads=[q(v) for v in cert['tangent_loads']],claimed_lower=q(cert['claimed_lower']))
    return result


def _graft_inputs(original,refinement):
    need(original['case_token']==OLD_ID,'Original proposal case identity')
    nodes=original['tree']['nodes'];need(type(nodes) is dict and len(nodes)==303,'Original node count')
    projected={};proofs={}
    def node(entry,store,target):
        kind=entry['kind']
        if kind=='branch':
            children=entry['children'];need(type(children) is dict and set(children)=={'0','1'},'Two branch children')
            return dict(kind=kind,movement=entry['movement'],children=dict(children))
        if kind in ('base_bound','base_infeasible'):
            return dict(kind=kind,base_leaf_id=entry['base_leaf_id'])
        need(kind in ('bound','infeasible'),'No unproved proposal leaf')
        ref=entry['certificate_ref'];need(type(ref) is str,'Certificate reference type')
        target[ref]=dict(certificate=_certificate(store[ref]['certificate'],kind))
        return dict(kind=kind,certificate_ref=ref)
    for key,value in nodes.items():
        need(type(key) is str,'Original node ID');projected[key]=node(value,original['proofs'],proofs)
    local={};newproofs={}
    need(type(refinement['refinements']) is dict and len(refinement['refinements'])==152,'Original fringe count')
    for leaf,subtree in refinement['refinements'].items():
        need(type(leaf) is str and type(subtree['nodes']) is dict,'Local tree ID')
        local[leaf]=dict(root=subtree['root'],nodes={key:node(value,refinement['proofs'],newproofs) for key,value in subtree['nodes'].items()})
    return dict(case_token=OLD_ID,tree=dict(root=original['tree']['root'],nodes=projected),proofs=proofs),dict(refinements=local,proofs=newproofs)


def build(repo_root,out_dir,source_revision,source_buffers=None):
    """Assemble once; does NOT replay a candidate, reconstruct rows or check tree."""
    need(type(source_revision) is str and re.fullmatch('[0-9a-f]{40}',source_revision) is not None,'Immutable40hex source revision')
    need(source_buffers is None or (type(source_buffers) is dict and set(source_buffers)<= {'verify.py'}),'Cached source-buffer keys')
    repo=Path(repo_root).resolve();out=Path(out_dir).resolve();need(not out.exists(),'Fresh bundle directory required')
    pins=dict(PINS);pins['verify.py']=(source_revision,'research-20261029/public_exact_energy_portable/verify.py')
    cache={};inputs={};total=0
    for destination,(revision,path) in pins.items():
        raw=(source_buffers or {}).get(destination)
        if raw is None:raw=(repo/path).read_bytes()
        need(type(raw) is bytes and len(raw)<=BYTE_LIMIT,'Consumed member size/type')
        total+=len(raw);need(total<=1024**3,'Total consumed input byte ceiling')
        frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=repo,timeout=5)
        need(raw==frozen,'Pinned working/cached bytes differ: '+path)
        cache[destination]=raw;inputs[destination]=dict(revision=revision,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    def packet(name):
        raw=cache.pop(name)
        if name.endswith('.gz'):
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(BYTE_LIMIT+1)
            need(len(raw)<=BYTE_LIMIT,'Decompressed input ceiling')
        return decode(raw)
    raw_helper=cache.pop('assembly/target_graft.py');helper=types.ModuleType('frozen_target_graft')
    exec(compile(raw_helper,'frozen_target_graft','exec'),helper.__dict__)
    target=packet('input/target.json.gz')
    need(target['status']=='VALIDATED_TARGET_SEMANTICS' and target['old_gap_transferred'] is False and target['native_calls']==0,'Target packet status')
    record,validated=target['record'],target['validated']
    need(record['status']=='EXACT_TARGET_DEFINED' and record['identity']==validated['identity']==CASE_TOKEN
         and validated['status']=='VALIDATED_TARGET_SEMANTICS' and record['old_identity']==validated['old_identity']==OLD_ID,'Target identity/validation')
    case=copy.deepcopy(record['case'])
    need(case==validated['case'] and record['policy']==validated['policy']==helper.POLICY,'Target declared case/policy disagreement')
    need(validated['denominators']==dict(services=37,modes=1370,legs=2648),'Target metadata denominator')
    del target,record,validated
    left=_candidate(packet('input/physical.json.gz'));right=_candidate(packet('input/response.json.gz'))
    comparison=packet('input/comparison.json')
    claim={k:comparison[k] for k in ('status','target_identity','lambda_left','lambda_right','lower','upper','gap','physical_upper')}
    need(claim['status']=='POSITIVE_TARGET_GAP_CERTIFIED' and claim['target_identity']==CASE_TOKEN,'Comparison target identity')
    for key in ('lambda_left','lambda_right','lower','upper','gap','physical_upper'):claim[key]=q(claim[key])
    need(claim['lambda_left']>=0 and claim['lambda_right']>=0 and claim['lambda_left']+claim['lambda_right']==1,'Fixed weight simplex')
    original=packet('input/tree.json.gz');refinement=packet('input/refinement.json.gz')
    first,second=_graft_inputs(original,refinement);del original,refinement
    proof=helper.graft_proposals(first,second);del first,second
    need(len(proof['nodes'])==375,'Combined target proposal count')
    proof=dict(target_identity=CASE_TOKEN,**proof)
    exported={name:cache.pop(name) for name in ('checkers/physical.py','checkers/semantic.py','checkers/tree.py','verify.py')}
    exported.update({'evidence/case.json':_json(case),'evidence/physical.json':_json(left),
        'evidence/response.json':_json(right),'evidence/claims.json':_json(claim)})
    encoded=_json(proof);need(len(encoded)<=BYTE_LIMIT,'Normalized tree byte ceiling')
    exported['evidence/tree.json.gz']=gzip.compress(encoded,mtime=0)
    exported['README.md']=(
        'LOCAL AUTHOR REVIEW BUNDLE; REDISTRIBUTION/LICENSE STATUS UNRESOLVED. No license or publication is authorized.\n'
        'Requirements: qualified CPython and stdlib; no Git, network, solver or package installation to verify.\n'
        'Run: python3 -I -S -B verify.py --manifest-sha256 TRUSTED_DIGEST --output verification.json\n'
        'Obtain TRUSTED_DIGEST from the separately admitted builder receipt, not an untrusted manifest.\n'
        'Checks the NEW explicitly declared rational-consumption descriptor, two retained physical witnesses, fixed mixture and target375-node proof.\n'
        'Does not rerun raw-source transformation/OD/access qualification; broader paired-arc extension relies on the separately stated proof/premises.\n'
        'Original-law bounds/admission flags are not target proof. No V2G, empirical road realization or exact optimum claim.\n'
        'Author-written/author-run qualification is NOT external replication.\n').encode()
    files={}
    need(sum(len(value) for value in exported.values())<=1024**3,'Total exported byte ceiling')
    for name,raw in exported.items():
        need(len(raw)<=BYTE_LIMIT,'Exported member byte ceiling')
        if name in inputs:
            files[name]=dict(inputs[name])  # Identical cached bytes: no duplicate source hash.
        else:files[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),generated=True)
    manifest=dict(schema='exact-energy-sign-bundle-v1',case_token=CASE_TOKEN,purpose='local author review',
        redistribution_status='UNRESOLVED',files=files,input_authority=inputs,
        scope='NEW declared rational descriptor sign; no raw-source transformation or empirical road check',
        assembly=dict(base_nodes=303,base_fringe=152,new_children=72,combined_nodes=375,
                      historical_claims_stripped=True,candidate_auxiliary_fields_omitted=True))
    raw=_json(manifest);out.mkdir(parents=True,exist_ok=False)
    for name,value in exported.items():
        destination=out/name;destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:stream.write(value)
    with (out/'MANIFEST.json').open('xb') as stream:stream.write(raw)
    return dict(status='BUILT_LOCAL_REVIEW_ONLY',manifest_sha256=hashlib.sha256(raw).hexdigest(),manifest=manifest,
        source_revision=source_revision,redistribution_status='UNRESOLVED',native_calls=0,verification_performed=False)
