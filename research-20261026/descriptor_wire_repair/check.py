"""One frozen literal stdlib check; no EGG/sibling/fixture/backend imports."""
import time
START=time.monotonic()
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BUDGET=dict(total_cpu_s=5,total_wall_s=10,body_cpu_s=3,body_wall_s=7,
            publication_cpu_s=2,publication_wall_s=3)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--source-revision',required=True)
    args=parser.parse_args(); revision=args.source_revision
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise SystemExit('Full lowercase source revision required')
    stopped=None; publishing=False; pub_wall=pub_cpu=None
    report=dict(policy='descriptor-json-wire-literal-check-v1',source_revision=revision,
        passed=False,outcomes=[],failures=[],consumed_sha256={},data_inputs=[],
        scope='Descriptor wire normalization only; no physical/native/scientific qualification')

    def stop(signum,frame):
        nonlocal stopped
        stopped=signum; raise TimeoutError('Literal check stop signal '+str(signum))

    def check():
        use=resource.getrusage(resource.RUSAGE_SELF); cpu=use.ru_utime+use.ru_stime
        if (stopped is not None or cpu>=(5 if publishing else 3) or time.monotonic()-START>=(10 if publishing else 7)
                or publishing and (cpu-pub_cpu>=2 or time.monotonic()-pub_wall>=3)
                or threading.active_count()!=1):
            raise RuntimeError('Literal check CPU/wall/thread limit')
        try: os.waitpid(-1,os.WNOHANG)
        except ChildProcessError: return
        raise RuntimeError('Unexpected literal-check child')

    def consume(name):
        check(); path=HERE/name; before=path.stat()
        if path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>256*1024:
            raise ValueError('Exact regular bounded local source/control file required')
        with path.open('rb') as stream: raw=stream.read(256*1024+1)
        after=path.stat()
        if len(raw)!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('Source/control file changed during read')
        report['consumed_sha256'][name]=hashlib.sha256(raw).hexdigest()
        return raw

    resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU): signal.signal(sig,stop)
    signal.setitimer(signal.ITIMER_REAL,max(.001,10-(time.monotonic()-START)))
    manifest=json.loads(consume('LAUNCH.json'))
    if (manifest.get('mode')!='FROZEN' or manifest.get('review_disposition')!='PASS'
            or manifest.get('source_revision')!=revision or manifest.get('source_freeze_assumption')!='parent-approved-frozen-commit'
            or manifest.get('workdir')!=str(ROOT) or Path.cwd().resolve()!=ROOT or not manifest.get('command')
            or manifest.get('budget')!=BUDGET or manifest.get('data_inputs')!=[] or manifest.get('namespace')!='attempt01'):
        raise SystemExit('DRAFT/PENDING or mismatched frozen literal-check control')
    output=HERE/'attempt01'; output.mkdir(exist_ok=False)
    try:
        for name in ('check.py','descriptor.py','PROTOCOL.md'): consume(name)
        sys.dont_write_bytecode=True
        spec=importlib.util.spec_from_file_location('frozen_descriptor_wire',HERE/'descriptor.py')
        helper=importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        if Path(helper.__file__).resolve()!=HERE/'descriptor.py': raise ValueError('Own helper import origin differs')
        expected={'name':'illustrative-only','prices':{'S':{2:.125,10:.25}},
            'duties':[[2,10],[3,11]],'physics':{'battery':80.,'reserve':10.,'power':60.},
            'hours':[2,10],'enabled':True}
        loaded=json.loads(json.dumps(expected,allow_nan=False))
        old=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
        report['old_strings']={'fresh':old(expected),'loaded':old(loaded)}

        def outcome(name,passed):
            check(); report['outcomes'].append(dict(name=name,passed=bool(passed)))

        outcome('old_comparison_mismatches_integer_2_10_wire_keys',old(expected)!=old(loaded))
        outcome('normalized_descriptor_matches_round_trip',helper.descriptor_equal(loaded,expected))
        changed=deepcopy(loaded); changed['prices']['S']['2']=.20
        outcome('changed_price_rejected',not helper.descriptor_equal(changed,expected))
        changed=deepcopy(loaded); del changed['prices']['S']['10']
        outcome('missing_hour_rejected',not helper.descriptor_equal(changed,expected))
        changed=deepcopy(loaded); changed['duties'].reverse()
        outcome('reordered_duties_rejected',not helper.descriptor_equal(changed,expected))
        changed=deepcopy(loaded); changed['physics']['battery']=90.
        outcome('changed_battery_rejected',not helper.descriptor_equal(changed,expected))
        rejected=False
        try: helper.normalize_descriptor({2:.125,'2':.25})
        except ValueError: rejected=True
        outcome('wire_key_collision_rejected',rejected)
        outcome('boolean_does_not_equal_integer',not helper.descriptor_equal({'x':True},{'x':1}))
        outcome('integer_does_not_equal_float_encoding',not helper.descriptor_equal({'x':1},{'x':1.}))
        check()
    except Exception as exc:
        report['failures'].append(dict(type=type(exc).__name__,message=str(exc)))
    pub_wall=time.monotonic(); use=resource.getrusage(resource.RUSAGE_SELF); pub_cpu=use.ru_utime+use.ru_stime
    publishing=True
    report['all_checks_completed']=len(report['outcomes'])==9
    report['passed']=bool(report['all_checks_completed'] and all(row['passed'] for row in report['outcomes']) and not report['failures'])
    use=resource.getrusage(resource.RUSAGE_SELF)
    report.update(stop_signal=stopped,resources=dict(cpu_s=use.ru_utime+use.ru_stime,user_s=use.ru_utime,
        system_s=use.ru_stime,elapsed_s=time.monotonic()-START,
        peak_rss_bytes=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024,
        rss_convention='macOS bytes; other platforms KiB converted to bytes',python_threads=threading.active_count(),prepublication_only=True))
    check()
    with (output/'receipt.json').open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps(dict(passed=report['passed'],completed=len(report['outcomes']),failed=[r['name'] for r in report['outcomes'] if not r['passed']])),flush=True)
    check(); signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
