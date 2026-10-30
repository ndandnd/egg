"""Approved singleton CF1 mechanism check using the existing inspected40 case.

Revision4 scopes the approved1920/1740/180 policy to restored serialized
contexts. A controller observation supplies sufficient timely ACK transport
evidence; missing or late observation leaves transport timing unestablished.
No fixture, numerical backend, dispatch or clock change occurs on import.
"""
from contextlib import contextmanager
from pathlib import Path
import argparse
import hashlib
import threading
import time

from experiments import cf1_small_mechanism_preflight as preflight

adapter, native_worker = preflight.adapter, preflight.native_worker
POLICY = 'cf1-small-approved-v4'
PACKAGE_START = 1509.9511370494984
PACKAGE_LIMIT = 165.
PACKAGE_CAP = 1674.9511370494984
ANALYSIS_FINAL_RESERVE_S, SUPERVISION_RESERVE_S = 30., 45.
ENGINEERING_BASE_ID, ENGINEERING_TRIPS = 50997, 40
FIXTURE_POLICY = preflight.FIXTURE_POLICY
SCOPE = preflight.SCOPE
NATIVE_DISPATCH_CLEARED = True
ACK_OBSERVATION = 'controller-ack-observation-v4.json'
_CONFIG_LOCK = threading.Lock()
_BASE_CHECKED = preflight.checked_sources


def task_matrix(cases=None):
    if cases is not None and (len(cases)!=1
            or cases[0].get('base_id')!=ENGINEERING_BASE_ID
            or cases[0].get('trips')!=ENGINEERING_TRIPS):
        raise ValueError('Revision4 requires inspected engineering50997/40 only')
    task = {'arm':'cf1','base_id':ENGINEERING_BASE_ID,'trips':ENGINEERING_TRIPS,
            'seed':17,'seconds':60.,'fault':None,'protocol_revision':4}
    return [{**task,'id':adapter.q.stable(task)[:20]}]


def checked_sources(directory):
    directory = Path(directory).resolve()
    expected = adapter.q.ROOT/'research-20261023/cf1-small-approved-checks/attempt01'
    if directory!=expected.resolve():
        raise ValueError('Revision4 requires its exact approved source-check attempt')
    checks = _BASE_CHECKED(directory)
    attempt = adapter.q.read(directory/'attempt.json')
    result = adapter.q.read(directory/'result.json')
    command = [str(adapter.q.ROOT/'.venv-local/bin/python'),'-m','pytest','-q',
               'src/tests/test_cf1_small_mechanism_approved.py']
    if (attempt.get('attempt_id')!='attempt01' or attempt.get('revision')!=4
            or attempt.get('command')!=command
            or attempt.get('command_sha256')!=adapter.q.stable(command)
            or attempt.get('executed_tests')!=['test_cf1_small_mechanism_approved.py']
            or result.get('attempt_id')!='attempt01' or result.get('revision')!=4
            or result.get('policy')!=POLICY):
        raise ValueError('Revision4 source-check execution identity differs')
    sources = attempt['source_hashes']
    # The inherited gate also binds its module/test and all earlier required
    # qualified dependencies. This gate adds only the affected v4 module/test.
    for name in ('src/experiments/cf1_small_mechanism_approved.py',
                 'src/tests/test_cf1_small_mechanism_approved.py',
                 'src/tests/test_constructive_controls.py'):
        values = [value for path,value in sources.items()
                  if Path(path).resolve()==(adapter.q.ROOT/name).resolve()]
        if values!=[adapter.q.sha(adapter.q.ROOT/name)]:
            raise ValueError('Passing check misses revision4 source: '+name)
    return checks


def _ack_bytes(ack):
    # Exactly the frozen native Worker's existing wire serialization.
    return (adapter.q.json.dumps(ack,sort_keys=True,separators=(',',':'),
                                 allow_nan=False)+'\n').encode()


def _observe_receive_ack(original, item):
    """Observe only a newly completed real read; retain original read failures."""
    before = item['ack_bytes']
    prior = item.get('acknowledgment')
    result = original(item)
    raw,ack = item['ack_bytes'],item.get('acknowledgment')
    if raw==before or ack is None:
        return result
    observed = time.monotonic()  # After the complete read, before disk audit.
    q = adapter.q
    folder,task,anchor = Path(item['folder']),item['task'],item['anchor']
    attempt = q.read(folder/'attempt.json')
    if (prior is not None or not isinstance(ack,dict) or task!=task_matrix()[0]
            or attempt.get('policy')!=POLICY or attempt.get('task')!=task
            or attempt.get('parent_monotonic')!=anchor
            or attempt.get('deadline')!=anchor+60.
            or ack.get('task_id')!=task['id']
            or ack.get('lock_sha256')!=attempt.get('lock_sha256')
            or not isinstance(ack.get('lock_sha256'),str) or not ack['lock_sha256']
            or ack.get('parent_monotonic')!=anchor
            or not q.finite(ack.get('completion_monotonic'),anchor)
            or not q.finite(observed,ack['completion_monotonic'])
            or raw!=_ack_bytes(ack)):
        raise ValueError('Controller ACK observation identity/payload mismatch')
    observation = {'policy':POLICY,'task_id':task['id'],
        'lock_sha256':attempt['lock_sha256'],'parent_monotonic':anchor,
        'raw_payload_sha256':hashlib.sha256(raw).hexdigest(),
        'controller_observed_monotonic':observed}
    # Exclusive flat write precedes finish's existing artifact inventory. An
    # EOF/repeated receive has unchanged raw bytes and never rewrites this file.
    q.write_new(folder/ACK_OBSERVATION,observation)
    return result


@contextmanager
def revision4():
    """Reuse reviewed v3/v2 ownership while restoring all bindings on failure."""
    if not _CONFIG_LOCK.acquire(blocking=False):
        raise RuntimeError('Revision4 requires serialized nonnested use')
    try:
        with preflight.revision3():
            changes = {'POLICY':POLICY,'PACKAGE_START':PACKAGE_START,
                'PACKAGE_LIMIT':PACKAGE_LIMIT,'PACKAGE_CAP':PACKAGE_CAP,
                'ANALYSIS_FINAL_RESERVE_S':ANALYSIS_FINAL_RESERVE_S,
                'SUPERVISION_RESERVE_S':SUPERVISION_RESERVE_S,
                'ENGINEERING_BASE_ID':ENGINEERING_BASE_ID,'ENGINEERING_TRIPS':ENGINEERING_TRIPS,
                'FIXTURE_POLICY':FIXTURE_POLICY,
                'WORKER_ARGV_PREFIX':('-m','experiments.cf1_small_mechanism_approved','worker'),
                'task_matrix':task_matrix,'checked_sources':checked_sources}
            old_adapter = {name:getattr(adapter,name) for name in changes}
            old_worker = {name:getattr(native_worker,name) for name in ('POLICY','task_matrix')}
            q = adapter.q
            old_q = {name:getattr(q,name) for name in
                     ('CEILING','DISPATCH_STOP','SHUTDOWN_RESERVE','receive_ack')}
            try:
                for name,value in changes.items():
                    setattr(adapter,name,value)
                native_worker.POLICY,native_worker.task_matrix = POLICY,task_matrix
                q.CEILING,q.DISPATCH_STOP,q.SHUTDOWN_RESERVE = 1920.,1740.,180.
                q.receive_ack = lambda item:_observe_receive_ack(old_q['receive_ack'],item)
                yield
            finally:
                for name,value in old_q.items():
                    setattr(q,name,value)
                for name,value in old_worker.items():
                    setattr(native_worker,name,value)
                for name,value in old_adapter.items():
                    setattr(adapter,name,value)
    finally:
        _CONFIG_LOCK.release()


def freeze(args):
    with revision4():
        return {**adapter.freeze(args),'tasks':1}


def run(args):
    with revision4():
        return adapter.run(args)


def _transport_evidence(args, task, locksha):
    """Independently crosscheck saved observation against the terminal inventory."""
    q = adapter.q
    folder = Path(args.output)/task['id']
    proof = {'task_id':task['id'],'status':'timing_unestablished',
             'controller_observed_monotonic':None}
    try:
        receipt = q.read(folder/'supervisor.json')
        attempt = q.read(folder/'attempt.json')
        path = folder/ACK_OBSERVATION
        if path.is_symlink() or path.resolve().parent!=folder.resolve():
            raise ValueError('Observation escapes task folder')
        observation = q.read(path)
        ack,anchor = receipt['completion_acknowledgment'],receipt['parent_monotonic']
        observed = observation['controller_observed_monotonic']
        if (receipt.get('task')!=task or receipt.get('lock_sha256')!=locksha
                or attempt.get('policy')!=POLICY or attempt.get('task')!=task
                or attempt.get('lock_sha256')!=locksha
                or attempt.get('parent_monotonic')!=anchor or attempt.get('deadline')!=anchor+60.
                or not q.finite(anchor) or not isinstance(ack,dict)
                or ack.get('task_id')!=task['id'] or ack.get('lock_sha256')!=locksha
                or ack.get('parent_monotonic')!=anchor
                or not q.finite(ack.get('completion_monotonic'),anchor)
                or observation.get('policy')!=POLICY or observation.get('task_id')!=task['id']
                or observation.get('lock_sha256')!=locksha
                or observation.get('parent_monotonic')!=anchor
                or observation.get('raw_payload_sha256')!=hashlib.sha256(_ack_bytes(ack)).hexdigest()
                or receipt.get('artifacts',{}).get(ACK_OBSERVATION)!=q.sha(path)
                or not q.finite(observed,ack['completion_monotonic'])):
            raise ValueError('Saved controller ACK observation mismatch')
        proof['controller_observed_monotonic'] = observed
        proof['status'] = 'observed_by_endpoint' if observed<=anchor+60. else 'timing_unestablished'
        proof['reason'] = ('complete_ACK_read_by_controller_by_anchor_plus_60' if observed<=anchor+60.
            else 'late_controller_observation_does_not_establish_send_time')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        proof['reason'] = 'missing_or_invalid_controller_observation:'+type(exc).__name__
    return proof


def analyze(args):
    with revision4():
        q = adapter.q
        original,written = q.write_new,[]
        def write(path,value):
            if Path(path).resolve()==Path(args.report).resolve():
                lock,locksha = q.read(args.lock),q.sha(args.lock)
                proofs = [_transport_evidence(args,task,locksha) for task in lock['tasks']]
                issues = list(value.get('issues',[]))
                issues.extend(proof['task_id']+':ack_transport_timing_unestablished'
                              for proof in proofs if proof['status']!='observed_by_endpoint')
                by_id = {proof['task_id']:proof for proof in proofs}
                rows = [{**row,'ack_transport':by_id.get(row['task']['id'])}
                        for row in value.get('rows',[])]
                value = {**value,'scope':SCOPE,'rows':rows,'issues':issues,
                    'ack_transport':proofs,'passed':value.get('passed') is True and not issues}
                result = original(path,value)
                written.append(value)
                return result
            return original(path,value)
        q.write_new = write
        try:
            result = adapter.analyze(args)
            return written[0] if written else result
        finally:
            q.write_new = original


def worker(args):
    with revision4():
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
