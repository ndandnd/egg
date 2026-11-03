"""Explicit inspected50997/40 mechanism qualification; parent-reviewed launch only.

Revision3 supplies no scalability or engineering80 success evidence. The115s
package is a source-only proposal: independent review rejected its5s final
reserve, so native dispatch is blocked pending a sufficient prospective budget.
No fixture generation, clock change, solver invocation or dispatch on import.
"""
from contextlib import contextmanager
from pathlib import Path
import argparse
import threading

from experiments import cf1_preparation_preflight as preparation

adapter, native_worker = preparation.adapter, preparation.native_worker
POLICY = 'cf1-small-mechanism-v3'
PACKAGE_START = 1503.9811370494986
PACKAGE_LIMIT = 115.
PACKAGE_CAP = PACKAGE_START+PACKAGE_LIMIT
ANALYSIS_FINAL_RESERVE_S, SUPERVISION_RESERVE_S = 5., 40.
ENGINEERING_BASE_ID, ENGINEERING_TRIPS = 50997, 40
FIXTURE_POLICY = 'same previously inspected engineering50997/40; no generation'
NATIVE_DISPATCH_CLEARED = False
SCOPE = 'single inspected CF1 engineering40 mechanism qualification only; no engineering80 success, comparative quality, optimality or generalization claim'
_CONFIG_LOCK = threading.Lock()
_BASE_CHECKED = preparation.checked_sources


def task_matrix(cases=None):
    if cases is not None and (len(cases)!=1
            or cases[0].get('base_id')!=ENGINEERING_BASE_ID
            or cases[0].get('trips')!=ENGINEERING_TRIPS):
        raise ValueError('Revision3 requires inspected engineering50997/40 only')
    task = {'arm':'cf1','base_id':ENGINEERING_BASE_ID,'trips':ENGINEERING_TRIPS,
            'seed':17,'seconds':60.,'fault':None,'protocol_revision':3}
    return [{**task,'id':adapter.q.stable(task)[:20]}]


def checked_sources(directory):
    checks = _BASE_CHECKED(directory)
    sources = adapter.q.read(Path(directory)/'attempt.json')['source_hashes']
    for name in ('src/experiments/cf1_small_mechanism_preflight.py',
                 'src/tests/test_cf1_small_mechanism_preflight.py'):
        values = [value for path,value in sources.items()
                  if Path(path).resolve()==(adapter.q.ROOT/name).resolve()]
        if values!=[adapter.q.sha(adapter.q.ROOT/name)]:
            raise ValueError('Passing check misses revision3 source: '+name)
    return checks


@contextmanager
def revision3():
    """Reuse reviewed serialized supervision and restore every policy binding."""
    if not _CONFIG_LOCK.acquire(blocking=False):
        raise RuntimeError('Revision3 requires serialized nonnested use')
    try:
        with preparation.revision2():
            changes = {'POLICY':POLICY,'PACKAGE_START':PACKAGE_START,
                'PACKAGE_LIMIT':PACKAGE_LIMIT,'PACKAGE_CAP':PACKAGE_CAP,
                'ANALYSIS_FINAL_RESERVE_S':ANALYSIS_FINAL_RESERVE_S,
                'SUPERVISION_RESERVE_S':SUPERVISION_RESERVE_S,
                'ENGINEERING_BASE_ID':ENGINEERING_BASE_ID,'ENGINEERING_TRIPS':ENGINEERING_TRIPS,
                'FIXTURE_POLICY':FIXTURE_POLICY,
                'WORKER_ARGV_PREFIX':('-m','experiments.cf1_small_mechanism_preflight','worker'),
                'task_matrix':task_matrix,'checked_sources':checked_sources}
            old_adapter = {name:getattr(adapter,name) for name in changes}
            old_worker = {name:getattr(native_worker,name) for name in ('POLICY','task_matrix')}
            try:
                for name,value in changes.items():
                    setattr(adapter,name,value)
                native_worker.POLICY,native_worker.task_matrix = POLICY,task_matrix
                yield
            finally:
                for name,value in old_worker.items():
                    setattr(native_worker,name,value)
                for name,value in old_adapter.items():
                    setattr(adapter,name,value)
    finally:
        _CONFIG_LOCK.release()


def freeze(args):
    require_native_dispatch_clearance()
    with revision3():
        return {**adapter.freeze(args),'tasks':1}


def run(args):
    require_native_dispatch_clearance()
    with revision3():
        return adapter.run(args)


def analyze(args):
    with revision3():
        original = adapter.q.write_new
        def write(path,value):
            if Path(path).resolve()==Path(args.report).resolve():
                value = {**value,'scope':SCOPE}
            return original(path,value)
        adapter.q.write_new = write
        try:
            return adapter.analyze(args)
        finally:
            adapter.q.write_new = original


def worker(args):
    require_native_dispatch_clearance()
    with revision3():
        return native_worker.worker(args)


def require_native_dispatch_clearance():
    if not NATIVE_DISPATCH_CLEARED:
        raise RuntimeError('Native dispatch blocked: prospective reserve is unapproved; '
            'requires sufficient approved budget and source-bound requalification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('freeze')
    p.add_argument('--design','--manifest',dest='design',required=True)
    for name in ('lock','checks','accounting'):
        p.add_argument('--'+name,required=True)
    for name in ('run','analyze','worker'):
        p = commands.add_parser(name)
        for option in ('lock','output'):
            p.add_argument('--'+option,required=True)
        if name=='run':
            p.add_argument('--freeze-receipt',required=True)
        elif name=='analyze':
            p.add_argument('--report',required=True)
        else:
            p.add_argument('--parent-pid',type=int,required=True)
            p.add_argument('--ack-fd',type=int,required=True)
    args = parser.parse_args()
    result = {'freeze':freeze,'run':run,'analyze':analyze,'worker':worker}[args.command](args)
    if args.command!='worker':
        print(adapter.q.json.dumps(result,indent=2))


if __name__=='__main__':
    main()
