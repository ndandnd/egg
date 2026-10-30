"""Bounded local portable-bundle construction and one retained-evidence check."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
import types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/public_certificate_bundle/'
ASSIGNED=('PREFLIGHT','BUNDLE','ADAPTER_Q0','PORTABLE_CHECK')
FILES=('worker.py','run.py','bundle.py','PROTOCOL.md','FIELD_AUTHORITY.md')
VERIFY_LIMITS=dict(seconds=500,checker_seconds=450,rss_bytes=2*1024**3,
    compressed_bytes=512*1024**2,decompressed_bytes=512*1024**2,total_bytes=1024**3,
    tree_nodes=375,tree_depth=375)
STAGES=dict(PREFLIGHT=(30,45),BUNDLE=(20,60),ADAPTER_Q0=(20,30),PORTABLE_CHECK=(400,530))
CLI_LIMITS=dict(cpu_s=400,wall_s=500,cleanup_wall_s=3)

class StageLimit(RuntimeError):pass
def require(ok,message):
    if not ok:raise ValueError(message)
def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,default=encode,allow_nan=False,indent=2);stream.write('\n')
def usage():
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime,
        self_cpu_s=own.ru_utime+own.ru_stime,
        peak_rss_bytes=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def module(name,path,raw):
    value=types.ModuleType(name);value.__file__=str(path)
    exec(compile(raw,str(path),'exec'),value.__dict__);return value
def expired(signum,frame):raise StageLimit('Complete frozen stage CPU/wall allowance exhausted')

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(550,550))
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGPROF,expired)
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();rows=[];failures=[];cache={};manifest={};builder=None;built=None;verifier=None;verified=None;cli_receipt=None
    def stopclocks():
        signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_PROF,0)
    def stage(name,action):
        cpu,wall=STAGES[name];u=usage()
        require(u['cpu_s']+cpu+60<550 and time.monotonic()-started+wall+90<780,
                'Full next stage plus final60CPU/90wall reserve not funded')
        require(u['peak_rss_bytes']<=5*1024**3,'Observed worker RSS exceeded')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic();before=usage()
        signal.setitimer(signal.ITIMER_PROF,cpu);signal.setitimer(signal.ITIMER_REAL,wall)
        try:
            value=action();write(out/(name+'.json'),value)
            now=usage();elapsed=time.monotonic()-anchor
            require(now['cpu_s']-before['cpu_s']<cpu and elapsed<wall,'Complete stage exceeded allowance')
            require(now['peak_rss_bytes']<=5*1024**3,'Observed worker RSS exceeded')
            row.update(status='DELIVERED',elapsed_s=elapsed,resources=now,summary=value.get('summary',dict(status=value.get('status'))))
        except BaseException as exc:
            row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
        finally:
            stopclocks();write(out/(name+'.status.json'),row)
        return value
    try:
        def preflight():
            nonlocal builder
            require(not sys.flags.optimize,'Assertions required')
            control_raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(control_raw)
            require(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision
                and re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None,'No frozen source authority')
            require(out==(HERE/'attempt01').resolve() and control.get('run_id')=='attempt01'
                and tuple(control.get('assigned',()))==ASSIGNED,'Namespace/denominator mismatch')
            require([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s')]
                ==[600,900,550,780] and control.get('native_calls')==0
                and control.get('observed_rss_bytes')==5*1024**3,'Resource/native declaration mismatch')
            require(control.get('stage_limits')=={k:list(v) for k,v in STAGES.items()}
                and control.get('final_reserve')==[60,90] and control.get('verify_limits')==VERIFY_LIMITS
                and control.get('cli_limits')==CLI_LIMITS,
                'Complete stage/checker limits changed')
            require(control.get('distribution_status')=='UNRESOLVED_LOCAL_REVIEW_ONLY','No distribution authority')
            manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=(HERE/name).read_bytes()
                frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',args.source_revision+':'+REL+name],cwd=ROOT,timeout=2)
                require(raw==frozen,'Frozen package source differs: '+name)
                cache[name]=raw;manifest[name]=dict(revision=args.source_revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            builder=module('portable_bundle_builder',HERE/'bundle.py',cache['bundle.py'])
            require(control.get('input_pins')=={k:dict(revision=r,path=p) for k,(r,p) in builder.PINS.items()},'Fixed six-input/three-checker pins changed')
            # Cache once without executing or preflight hashing: builder is the
            # sole source-byte admission/hash authority for exported verify.py.
            cache['verify.py']=(HERE/'verify.py').read_bytes()
            return dict(status='ADMITTED_WRAPPER_SOURCE',files=manifest,native_calls=0,
                verifier_source_admission='PENDING_BUNDLE',distribution_status='UNRESOLVED_LOCAL_REVIEW_ONLY')
        stage('PREFLIGHT',preflight)
        def build():
            nonlocal built,verifier
            built=builder.build(ROOT,out/'public-sign-verifier',args.source_revision,source_buffers={'verify.py':cache['verify.py']})
            require(built['status']=='BUILT_LOCAL_REVIEW_ONLY' and built['verification_performed'] is False
                and built['redistribution_status']=='UNRESOLVED','Unexpected bundle construction contract')
            # Compile only the source just authenticated by builder. The exported
            # identical program offers the documented -I -S -B portable command.
            verifier=module('portable_public_sign_verifier',out/'public-sign-verifier'/'verify.py',cache['verify.py'])
            return built
        stage('BUNDLE',build)
        def q0():
            result=verifier.literal_qualification()
            require(result['status']=='PASS' and result['native_calls']==0,'New adapter qualification failed')
            return result
        stage('ADAPTER_Q0',q0)
        def verify():
            nonlocal verified,cli_receipt
            directory=out/'public-sign-verifier';output=directory/'verification.json'
            command=[sys.executable,'-I','-S','-B',str(directory/'verify.py'),
                '--manifest-sha256',built['manifest_sha256'],'--output',str(output)]
            child=None;failure=None;anchor=time.monotonic();before=usage()
            def child_limits():
                # One trusted stdlib child, sharing this worker's owned group.
                resource.setrlimit(resource.RLIMIT_CPU,(CLI_LIMITS['cpu_s'],CLI_LIMITS['cpu_s']))
            try:
                with (out/'CLI.stdout.txt').open('x') as stdout,(out/'CLI.stderr.txt').open('x') as stderr:
                    child=subprocess.Popen(command,cwd=directory,stdout=stdout,stderr=stderr,
                        preexec_fn=child_limits,start_new_session=False)
                    child.wait(timeout=CLI_LIMITS['wall_s'])
            except BaseException as exc:
                failure=type(exc).__name__+': '+str(exc)
            finally:
                if child is not None and child.poll() is None:
                    try:child.kill()
                    except ProcessLookupError:pass
                    except OSError as exc:failure=(failure or '')+'; child kill: '+type(exc).__name__+': '+str(exc)
                    try:child.wait(timeout=CLI_LIMITS['cleanup_wall_s'])
                    except subprocess.TimeoutExpired:failure=(failure or '')+'; UNRESOLVED_CHILD'
                cli_receipt=dict(command=command,pid=child.pid if child else None,
                    exit_code=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
                    failure=failure,same_worker_process_group=True,elapsed_s=time.monotonic()-anchor,
                    before=before,after=usage(),full_retained_evidence_invocations=int(child is not None),
                    accounting='Waited CLI child CPU is already included in worker and owner observations')
                write(out/'cli_receipt.json',cli_receipt)
            require(cli_receipt['reaped'] and cli_receipt['exit_code']==0 and not failure,'Fresh CLI failed or remained unresolved')
            verified=json.loads(output.read_text())
            require(verified['status']=='PASS','Portable evidence did not pass: '+str(verified.get('reason')))
            return dict(status='PASS',report=verified,manifest_sha256=built['manifest_sha256'],
                summary=dict(status='PASS',manifest_sha256=built['manifest_sha256'],native_calls=0),
                full_retained_evidence_checks=1,distribution_status='UNRESOLVED_LOCAL_REVIEW_ONLY',
                external_replication=False)
        stage('PORTABLE_CHECK',verify)
    except BaseException as exc:failures.append(type(exc).__name__+': '+str(exc))
    finally:
        stopclocks()
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='Earlier source/qualification/resource failure'))
    u=usage();elapsed=time.monotonic()-started
    passed=u['cpu_s']<550 and elapsed<780 and u['peak_rss_bytes']<=5*1024**3
    status='COMPLETED' if passed and not failures and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    report=dict(status=status,assigned=list(ASSIGNED),rows=rows,failures=failures,resource_pass=passed,
        resources=u,elapsed_s=elapsed,native_calls=0,portable_pass=status=='COMPLETED',
        distribution_status='UNRESOLVED_LOCAL_REVIEW_ONLY',external_replication=False,cli_receipt=cli_receipt)
    write(out/'results.json',report);write(out/'worker_receipt.json',dict(report,rows=None,resources=usage(),elapsed_s=time.monotonic()-started))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
