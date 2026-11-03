"""Single repaired-CF1 native policy configuration; explicit parent launch only.

This is a fresh protocol revision, not an automatic retry or new timetable.
Reviewed v1 supervision/worker machinery is delegated under restored bindings.
"""
from contextlib import contextmanager
from pathlib import Path
import argparse
import threading

from experiments import comparison_native_preflight as adapter
from experiments import comparison_native_worker as native_worker

POLICY = 'cf1-preparation-native-v2'
PACKAGE_START = 1416.3727097992353
PACKAGE_LIMIT = 165.
PACKAGE_CAP = PACKAGE_START+PACKAGE_LIMIT
_CONFIG_LOCK = threading.Lock()
_BASE_CHECKED = adapter.checked_sources


def task_matrix(cases=None):
    if cases is not None and (len(cases)!=1 or cases[0].get('base_id')!=50999
                              or cases[0].get('trips')!=80):
        raise ValueError('Revision2 requires the same inspected engineering50999/80')
    task = {'arm':'cf1','base_id':50999,'trips':80,'seed':17,'seconds':60.,
            'fault':None,'protocol_revision':2}
    return [{**task,'id':adapter.q.stable(task)[:20]}]


class _DelegateLock:
    """One owner-thread bound60 delegate while the original lock remains held."""
    def __init__(self):
        self.owner = threading.get_ident()
        self.active = False

    def acquire(self, blocking=False):
        if threading.get_ident()!=self.owner or self.active:
            return False
        self.active = True
        return True

    def release(self):
        if threading.get_ident()!=self.owner or not self.active:
            raise RuntimeError('Invalid configured supervision lock release')
        self.active = False

    def locked(self):
        return self.active


def checked_sources(directory):
    checks = _BASE_CHECKED(directory)
    sources = adapter.q.read(Path(directory)/'attempt.json')['source_hashes']
    for name in ('src/experiments/cf1_preparation_preflight.py',
                 'src/tests/test_cf1_preparation_preflight.py'):
        values = [value for path,value in sources.items()
                  if Path(path).resolve()==(adapter.q.ROOT/name).resolve()]
        if values!=[adapter.q.sha(adapter.q.ROOT/name)]:
            raise ValueError('Passing check misses revision2 source: '+name)
    return checks


@contextmanager
def revision2():
    """Atomically install policy-only settings; reject nested/concurrent use."""
    if not _CONFIG_LOCK.acquire(blocking=False):
        raise RuntimeError('Revision2 requires serialized nonnested use')
    original_lock = adapter._LOCK
    held = False
    old_adapter,old_worker = {},{}
    try:
        if not original_lock.acquire(blocking=False):
            raise RuntimeError('Reviewed supervision is already active')
        held = True
        changes = {'POLICY':POLICY,'PACKAGE_START':PACKAGE_START,'PACKAGE_LIMIT':PACKAGE_LIMIT,
            'PACKAGE_CAP':PACKAGE_CAP,'ANALYSIS_FINAL_RESERVE_S':30.,'SUPERVISION_RESERVE_S':45.,
            'WORKER_ARGV_PREFIX':('-m','experiments.cf1_preparation_preflight','worker'),
            'task_matrix':task_matrix,'checked_sources':checked_sources,'_LOCK':_DelegateLock()}
        old_adapter = {name:getattr(adapter,name) for name in changes}
        old_worker = {name:getattr(native_worker,name) for name in ('POLICY','task_matrix')}
        for name,value in changes.items():
            setattr(adapter,name,value)
        native_worker.POLICY,native_worker.task_matrix = POLICY,task_matrix
        yield
    finally:
        for name,value in old_worker.items():
            setattr(native_worker,name,value)
        for name,value in old_adapter.items():
            setattr(adapter,name,value)
        if held:
            original_lock.release()
        _CONFIG_LOCK.release()


def freeze(args):
    with revision2():
        result = adapter.freeze(args)
        return {**result,'tasks':1}


def run(args):
    with revision2():
        return adapter.run(args)


def analyze(args):
    # Normalize only this single-path report's cosmetic scope, before its
    # exclusive durable write; every independent analysis check is delegated.
    with revision2():
        original = adapter.q.write_new
        def write(path,value):
            if Path(path).resolve()==Path(args.report).resolve():
                value['scope'] = 'single repaired-CF1 engineering80 preflight; no comparative quality/optimality/generalization claim'
            return original(path,value)
        adapter.q.write_new = write
        try:
            return adapter.analyze(args)
        finally:
            adapter.q.write_new = original


def worker(args):
    with revision2():
        return native_worker.worker(args)


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
