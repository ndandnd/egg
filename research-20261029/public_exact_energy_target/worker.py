"""ONE prospective exact-energy target attempt; no native search or old replay."""
import argparse
import copy
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REL='research-20261029/public_exact_energy_target/'
MODEL='research-20261029/public_support_resolution/'
SEM='3278d50f8323618bd36809b1bbb1a0da081e23ff';CANON='76c83d55fe2983138da7b87f9d4d7c5fd36e9573'
ASSIGNED=('SOURCE_ADMISSION','Q0','TARGET','LOWER','INCUMBENT_ROUTES','RESPONSE_ROUTES','COMPARISON')
RESOURCES=dict(package_cpu_s=1200,package_wall_s=1800,worker_cpu_s=1140,worker_wall_s=1740,
    worker_self_hard_cpu_s=1080,closure_cpu_s=60,closure_wall_s=60,observed_rss_bytes=5*1024**3,native_calls=0)
STAGES=dict(SOURCE_ADMISSION=(40,60),Q0=(40,60),TARGET=(100,150),LOWER=(600,900),INCUMBENT_ROUTES=(100,150),RESPONSE_ROUTES=(100,150),COMPARISON=(20,30))
TREE_LIMITS=dict(nodes=375,depth=375,operations=100000000,fraction_bits=32768,seconds=850)
FACE_LIMITS=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=90)
SOURCES=dict(affine=(SEM,MODEL+'exact_fixed_topology.py'),original_semantics=(SEM,MODEL+'exact_dual.py'),
    physical=(SEM,MODEL+'independent_verify.py'),recovery=('425bf35452eb3f5444f20058ad6fd6b540ffed88','research-20261029/public_rational_recovery/recovery.py'),
    tree=('6a171357b65254b52cade63ed95dcce798485f36','research-20261029/public_support_tree/checker.py'))
INPUTS=dict(rich=('2f386362aa241a8a4f197a88a50fa150b6d47d9c','data/public/sistig_26088190_v1/hildenbrand_native_cases.json'),
    original=('253c1e29295e766b3889fc8f5c28d9808e00b3d6',MODEL+'attempt01/case_descriptor.json'),
    canonical=(CANON,'research-20261029/public_canonical_qualification/attempt01/results.json'),
    canonical_metadata=(CANON,'research-20261029/public_canonical_qualification/attempt01/PUBLIC_METADATA.json'),
    canonical_owner=(CANON,'research-20261029/public_canonical_qualification/attempt01/owner_receipt.json'),
    oldtree=('ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9','research-20261029/public_support_tree/attempt01/PUBLIC_TREE.json.gz'),
    refinement=('d8e22ffd3753fced3ec825c68714fd549d914230','research-20261029/public_physical_refinement/attempt01/PUBLIC_REFINEMENT.json.gz'),
    INCUMBENT_ROUTES=('0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee','research-20261029/public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz'),
    RESPONSE_ROUTES=('f5ec2aa5770188d173af7297620a5fcea99fef9a','research-20261029/public_price_witness/attempt01/EXACT_PRIMAL.json.gz'),
    weights=('f5ec2aa5770188d173af7297620a5fcea99fef9a','research-20261029/public_price_witness/attempt01/MIXTURE.json.gz'))
FILES=('worker.py','run.py','witnesses.py','target.py','target_semantics.py','checker.py','fixtures.py','PROTOCOL.md','FIELD_AUTHORITY.md','API_HANDOFF.md','WITNESSES_API.md')

class ResourceStop(RuntimeError):pass
def need(ok,message):
    if not ok:raise ValueError(message)
def usage():
    a,b=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime,self_cpu_s=a.ru_utime+a.ru_stime,peak_rss_bytes=max(a.ru_maxrss,b.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)
def write(path,value,packed=False):
    raw=json.dumps(value,default=encode,indent=2,allow_nan=False).encode()+b'\n'
    with path.open('xb') as stream:stream.write(gzip.compress(raw,mtime=0) if packed else raw)
def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result,'Duplicate JSON key');result[key]=value
    return result
def nonfinite(value):raise ValueError('Nonfinite token')
def decode(raw,decimal=False):
    return json.loads(raw,parse_float=str if decimal else float,parse_constant=nonfinite,object_pairs_hook=unique)
def git(rev,path):
    raw=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',rev+':'+path],cwd=ROOT,timeout=10)
    need(len(raw)<=512*1024**2,'Consumed buffer cap');return raw
def module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result
def compact(value):
    keys=('status','identity','target_identity','reason','denominators','lower','upper','physical_lower','hull_upper','gap_lower','physical_upper','face_attempts','physical_replays','objective_exact','fleet_count','old_model_result_unchanged')
    return {k:value[k] for k in keys if k in value}

def project_selected(document):
    """Discard other variants before any recursive seal/deepcopy/validation."""
    selected=[]
    for variant in document['native_cases']:
        if variant['selected_depot_id']==15:selected.append(variant)
    need(len(selected)==1,'Unique depot15 source variant')
    v=selected[0];s=document['source_data']
    return dict(native_cases=[{k:v[k] for k in ('selected_depot_id','case_identity','trips','movement_modes','movement_provenance')}],
        source_data={k:s[k] for k in ('deadhead_stop_order_source','deadhead_arcs_directed_row_major')})

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(1080,1080))
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out);rows=[];failure=None;manifest={};cache={};modules={};bound=None;points={};comparison=None;validated=None;validation_seal=None
    def expired(signum,frame):raise ResourceStop('Stage wall/self CPU ceiling')
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGPROF,expired)
    def stage(name,action):
        cpu,wall=STAGES[name];before=usage();elapsed=time.monotonic()-started
        if before['cpu_s']+cpu+60>=1140 or before['self_cpu_s']+cpu+60>=1080 or elapsed+wall+60>=1740 or before['peak_rss_bytes']>5*1024**3:raise ResourceStop('Full next stage plus closure not funded under inclusive and hard self ceilings')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        signal.setitimer(signal.ITIMER_REAL,wall);signal.setitimer(signal.ITIMER_PROF,cpu)
        try:
            value=action();write(out/(name+('.json.gz' if name in ('TARGET','LOWER','INCUMBENT_ROUTES','RESPONSE_ROUTES') else '.json')),value,name in ('TARGET','LOWER','INCUMBENT_ROUTES','RESPONSE_ROUTES'))
            after=usage();delta=after['cpu_s']-before['cpu_s'];duration=time.monotonic()-anchor
            if delta>cpu or duration>wall or after['peak_rss_bytes']>5*1024**3:
                row.update(status='LATE',reason='Delivered evidence exceeded stage resources');raise ResourceStop(row['reason'])
            row.update(status='DELIVERED',cpu_s=delta,elapsed_s=duration,summary=compact(value));return value
        except BaseException as exc:
            if row['status']=='ATTEMPTED':row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc))
            raise
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_PROF,0)
    try:
        need(sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize,'Required isolated stdlib command')
        need(sys.implementation.name=='cpython' and sys.version_info[:3]==(3,12,2),'Frozen runtime')
        need((sys.float_info.radix,sys.float_info.mant_dig,sys.float_info.max_exp,sys.float_info.rounds)==(2,53,1024,1),'Binary64 profile')
        raw_control=(HERE/'LAUNCH.json').read_bytes();control=decode(raw_control)
        need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision and re.fullmatch('[0-9a-f]{40}',args.source_revision),'No frozen source')
        need(control.get('run_id')=='attempt01' and out.resolve()==(HERE/'attempt01').resolve() and tuple(control.get('assigned',()))==ASSIGNED,'Namespace/denominator')
        need(control.get('resources')==RESOURCES and control.get('stages')=={k:list(v) for k,v in STAGES.items()} and control.get('tree_limits')==TREE_LIMITS and control.get('face_limits')==FACE_LIMITS,'Frozen resources/work caps')
        need(control.get('inputs')=={k:list(v) for k,v in INPUTS.items()} and control.get('external_sources')=={k:list(v) for k,v in SOURCES.items()},'Input/source pins')
        need(control.get('native_threads')==1 and all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')),'Thread environment')
        def admission():
            manifest['LAUNCH.json']=dict(bytes=len(raw_control),sha256=hashlib.sha256(raw_control).hexdigest(),binding='separate frozen control')
            specs={name:(args.source_revision,REL+name) for name in FILES};specs.update(SOURCES)
            for key,(rev,path) in specs.items():
                raw=git(rev,path)
                if key in FILES:need(raw==(HERE/key).read_bytes(),'Working source differs '+key)
                cache[key]=raw;manifest[key]=dict(revision=rev,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return dict(status='SOURCE_ADMITTED',manifest=manifest,public_inputs_read=False,native_calls=0)
        stage('SOURCE_ADMISSION',admission)
        for key in ('target.py','target_semantics.py','checker.py','witnesses.py','fixtures.py'):
            modules[key[:-3]]=module('new_'+key[:-3],cache[key])
        for key in SOURCES:modules[key]=module('pinned_'+key,cache[key])
        cache.clear();target,sem,checker,witness=(modules[k] for k in ('target','target_semantics','checker','witnesses'))
        def q0():
            a=target.literal_qualification(sem);b=checker.literal_qualification()
            c=modules['fixtures'].full_interface_qualification(target,sem,checker,modules['original_semantics']._reconstruct,project_selected)
            need(a.get('status')=='PASS' and b.get('status')=='PASS' and c.get('status')=='PASS','New literal qualification failed')
            return dict(status='PASS',target=a,checker=b,full_interface=c,native_calls=0)
        stage('Q0',q0)
        packets={}
        def consume(key,decimal=False):
            rev,path=INPUTS[key];raw=git(rev,path)
            if key=='rich':
                prior=packets['canonical_metadata']['manifest']['rich']
                need(prior['revision']==rev and prior['path']==path and prior['bytes']==len(raw)==8046032 and prior['prior_sha256']=='af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6','Pinned rich prior byte authority')
                manifest[key]=dict(revision=rev,path=path,bytes=len(raw),prior_sha256=prior['prior_sha256'],binding='Same exact Git object; closed prior SHA adopted without rehash')
            else:manifest[key]=dict(revision=rev,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if path.endswith('.gz'):
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:unpacked=stream.read(512*1024**2+1)
                need(len(unpacked)<=512*1024**2,'Decompressed input cap');raw=unpacked
            return decode(raw,decimal)
        def build_target():
            nonlocal validated,validation_seal
            for k in ('canonical','canonical_metadata','canonical_owner'):packets[k]=consume(k)
            r,m,o=(packets[k] for k in ('canonical','canonical_metadata','canonical_owner'))
            prior=('SOURCE_ADMISSION','Q0','PUBLIC_METADATA','CANONICAL','INDEPENDENT')
            need(r['status']=='COMPLETED' and r['resource_pass'] is True and r['scientific_status']=='PASS' and tuple(r['assigned'])==prior and tuple(x['id'] for x in r['rows'])==prior and all(x['status']=='DELIVERED' for x in r['rows']),'Canonical closed PASS')
            need(o['failure'] is None and o['resource_pass'] is True and o['child_exit']==0 and o['reaped'] is True and o['ledger']==r['rows'],'Canonical owner closure')
            need(o['source_revision']=='eee9c52066ea8c6d6d746e9bd2cc627864f85a57' and o['native_calls']==0 and r['native_calls']==0 and m['status']=='PROJECTED','Canonical source/native/projection authority')
            need(r['claim']['status']=='PASS' and r['independent']['status']=='PASS' and r['independent']['independent_status']=='PASS' and r['independent']['summary_matches'] is True and r['independent']['blocked_access_count']==0,'Canonical independent/access agreement')
            den=r['claim']['denominators'];need(den==dict(services=37,pullout=37,pullin=37,direct=37*36,depot=37*36,modes=1370,legs=2648) and r['independent']['denominators']==den,'Full canonical predicates and independent denominators')
            source_manifest=m['manifest'];need(source_manifest['rich']['revision']==INPUTS['rich'][0] and source_manifest['rich']['path']==INPUTS['rich'][1] and source_manifest['rich']['bytes']==8046032 and source_manifest['descriptor']['revision']==INPUTS['original'][0] and source_manifest['descriptor']['path']==INPUTS['original'][1],'Same rich/descriptor provenance')
            rich_full=consume('rich',True);rich=project_selected(rich_full);del rich_full
            original=consume('original')
            need(manifest['rich']['bytes']==8046032 and manifest['rich']['prior_sha256']=='af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6','Rich input identity')
            transfer=dict(revision=CANON,source_bound_pass=True,same_rich_input=True,same_descriptor=True,time_predicates_complete=True,blocked_depot_wait_count=0,mode_count=1370)
            record=target.transform(rich,original,transfer)
            originals=(rich,original,record);seals=tuple(checker.seal(x) for x in originals)
            def admitted(a,b,c):return all(x is y for x,y in zip((a,b,c),originals)) and tuple(checker.seal(x) for x in originals)==seals
            validated=checker.validate_semantics(rich,original,record,modules['original_semantics']._reconstruct,sem._reconstruct,admitted)
            validation_seal=checker.seal(validated)
            return dict(status='VALIDATED_TARGET_SEMANTICS',record=record,validated=validated,manifest=manifest,old_gap_transferred=False,native_calls=0)
        stage('TARGET',build_target)
        cached=checker.cached_reconstruct(validated,validation_seal)
        def lower_action():
            old=consume('oldtree');new=consume('refinement');saved=(checker.seal(old),checker.seal(new))
            def admitted(a,b):return a is old and b is new and (checker.seal(old),checker.seal(new))==saved
            try:return checker.verify_retained_tree(validated,validation_seal,old,new,modules['tree'],TREE_LIMITS,admitted)
            except ResourceStop:raise
            except Exception as exc:return dict(status='UNRESOLVED',reason=type(exc).__name__+': '+str(exc),target_identity=validated['identity'])
        bound=stage('LOWER',lower_action)
        for label in ('INCUMBENT_ROUTES','RESPONSE_ROUTES'):
            def point_action(label=label):
                packet=consume(label)
                try:
                    proposal=witness.proposal_from_packet(packet)
                    return witness.construct_witness(validated['case'],proposal,validated['identity'],modules['affine'],modules['recovery'],cached,modules['physical'].verify,FACE_LIMITS)
                except ResourceStop:raise
                except Exception as exc:return dict(status='TARGET_PRIMAL_UNRESOLVED',reason=type(exc).__name__+': '+str(exc),target_identity=validated['identity'],physical_replays=0)
            points[label]=stage(label,point_action)
        def compare():
            packet=consume('weights');weights=packet['mixture']
            weight_record=dict(lambda_left=weights['lambda_left'],lambda_right=weights['lambda_right'],source_pin=INPUTS['weights'])
            weight_seal=checker.seal(weight_record);point_seals={k:checker.seal(v) for k,v in points.items()}
            def admitted_point(x):return any(x is p and checker.seal(p)==point_seals[k] for k,p in points.items())
            def admitted_weight(x):return x is weight_record and checker.seal(x)==weight_seal
            if any(p.get('status')!='ADMITTED_TARGET_PRIMAL' for p in points.values()):
                return dict(status='TARGET_GAP_UNRESOLVED',reason='Both new target endpoints required; no old witness fallback',target_identity=validated['identity'])
            mixture=checker.check_mixture(points['INCUMBENT_ROUTES'],points['RESPONSE_ROUTES'],weight_record['lambda_left'],weight_record['lambda_right'],validated['identity'],admitted_point,weight_record=weight_record,admit_weights=admitted_weight)
            conclusion=checker.conclude(bound,mixture) if bound['status']=='COMPLETE_TARGET_BOUND' else dict(status='TARGET_GAP_UNRESOLVED',reason='Target lower unresolved',target_identity=validated['identity'])
            return dict(conclusion,mixture=mixture)
        comparison=stage('COMPARISON',compare)
        need(checker.seal(validated)==validation_seal,'Final target validation seal changed')
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_PROF,0)
    for name in ASSIGNED[len(rows):]:rows.append(dict(id=name,status='UNATTEMPTED',reason=failure or 'Missing dependency'))
    observed=usage();elapsed=time.monotonic()-started;passed=observed['cpu_s']<1140 and observed['self_cpu_s']<1080 and elapsed<1740 and observed['peak_rss_bytes']<=5*1024**3
    status='COMPLETED' if failure is None and passed and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    result=dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resources=observed,elapsed_s=elapsed,resource_pass=passed,
        scientific_status=comparison['status'] if status=='COMPLETED' else 'NOT_CERTIFIED',comparison=compact(comparison) if comparison else None,
        lower=compact(bound) if bound else None,points={k:compact(v) for k,v in points.items()},manifest=manifest,native_calls=0,
        old_model_unchanged=True,scope='NEW exact-energy target only; no empirical paired-road realization, old-gap transfer or native search.')
    write(out/'results.json',result);write(out/'worker_receipt.json',dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resource_pass=passed,resources=usage(),elapsed_s=time.monotonic()-started,native_calls=0))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
