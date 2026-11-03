"""Affected v4 source checks using AST and inert bindings; no native imports."""
import ast
import hashlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]


def isolated_source(name, **bindings):
    path = ROOT/'src'/'experiments'/(name+'.py')
    tree = ast.parse(path.read_text(),filename=str(path))
    tree.body = [node for node in tree.body if not (
        isinstance(node,ast.ImportFrom) and node.module=='experiments')]
    scope = {'__name__':'isolated_'+name,**bindings}
    exec(compile(tree,str(path),'exec'),scope)
    return SimpleNamespace(**scope)


def stable(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def harness():
    store,writes = {},[]
    def read(path):
        return store[str(Path(path))]
    def write(path,value):
        key = str(Path(path))
        if key in store:
            raise FileExistsError(key)
        store[key] = value
        writes.append((key,value))
    q = SimpleNamespace(stable=stable,json=json,ROOT=ROOT,read=read,write_new=write,
        sha=lambda path:stable(store[str(Path(path))]) if str(Path(path)) in store
            else 'source:'+str(Path(path).relative_to(ROOT)),
        finite=lambda value,minimum=0.:type(value) in (int,float)
            and value==value and value not in (float('inf'),-float('inf')) and value>=minimum,
        CEILING=1800.,DISPATCH_STOP=1620.,SHUTDOWN_RESERVE=180.,receive_ack=lambda item:None)
    adapter = SimpleNamespace(q=q,POLICY='original',PACKAGE_START=1.,PACKAGE_LIMIT=2.,
        PACKAGE_CAP=3.,ANALYSIS_FINAL_RESERVE_S=5.,SUPERVISION_RESERVE_S=40.,
        ENGINEERING_BASE_ID=50999,ENGINEERING_TRIPS=80,FIXTURE_POLICY='original',
        WORKER_ARGV_PREFIX=('original',),task_matrix=lambda cases:[],
        checked_sources=lambda directory:{'inherited':'proof'},_LOCK=threading.Lock())
    worker = SimpleNamespace(POLICY='original-worker',task_matrix=lambda:[])
    prep = isolated_source('cf1_preparation_preflight',adapter=adapter,native_worker=worker)
    small = isolated_source('cf1_small_mechanism_preflight',preparation=prep)
    approved = isolated_source('cf1_small_mechanism_approved',preflight=small)
    approved._observe_receive_ack.__globals__['time'] = SimpleNamespace(monotonic=lambda:159.)
    return adapter,worker,small,approved,store,writes


def ack_case(approved,store):
    task, = approved.task_matrix()
    folder = Path('/inert-cf1-output')/task['id']
    attempt = {'policy':approved.POLICY,'task':task,'lock_sha256':'lockhash',
               'parent_monotonic':100.,'deadline':160.}
    store[str(folder/'attempt.json')] = attempt
    ack = {'task_id':task['id'],'lock_sha256':'lockhash','parent_monotonic':100.,
           'completion_monotonic':158.,'result_sha256':'result','completion_sha256':'completion',
           'worker_outcome_sha256':'outcome','worker_status':'feasible','worker_censored':False}
    item = {'folder':folder,'task':task,'anchor':100.,'ack_bytes':b'',
            'acknowledgment':None,'secondary_errors':[{'old':'retained'}],
            'primary_reason':'original failure'}
    return item,ack


class ApprovedMechanismTests(unittest.TestCase):
    def test_policy_singleton_and_old_clearance_stay_distinct(self):
        adapter,worker,small,approved,store,writes = harness()
        self.assertEqual(approved.POLICY,'cf1-small-approved-v4')
        self.assertTrue(approved.NATIVE_DISPATCH_CLEARED)
        self.assertFalse(small.NATIVE_DISPATCH_CLEARED)
        task, = approved.task_matrix([{'base_id':50997,'trips':40}])
        self.assertEqual({key:task[key] for key in ('arm','base_id','trips','seed','seconds',
            'fault','protocol_revision')},{'arm':'cf1','base_id':50997,'trips':40,
                'seed':17,'seconds':60.,'fault':None,'protocol_revision':4})
        self.assertNotEqual(task['id'],small.task_matrix()[0]['id'])
        for cases in ([],[{'base_id':50999,'trips':80}],
                      [{'base_id':50997,'trips':40}]*2):
            with self.assertRaises(ValueError):
                approved.task_matrix(cases)
        for entry in (small.freeze,small.run,small.worker):
            with self.assertRaisesRegex(RuntimeError,'prospective reserve is unapproved'):
                entry(None)

    def test_globals_limits_and_all_bindings_restore_after_failure(self):
        adapter,worker,small,approved,store,writes = harness()
        before_adapter,before_worker,before_q = vars(adapter).copy(),vars(worker).copy(),vars(adapter.q).copy()
        lock = adapter._LOCK
        with self.assertRaisesRegex(ValueError,'injected'):
            with approved.revision4():
                self.assertTrue(lock.locked())
                self.assertEqual((adapter.PACKAGE_START,adapter.PACKAGE_LIMIT,adapter.PACKAGE_CAP),
                                 (1509.9511370494984,165.,1674.9511370494984))
                self.assertEqual((adapter.ANALYSIS_FINAL_RESERVE_S,adapter.SUPERVISION_RESERVE_S),(30.,45.))
                self.assertEqual((adapter.q.CEILING,adapter.q.DISPATCH_STOP,adapter.q.SHUTDOWN_RESERVE),
                                 (1920.,1740.,180.))
                self.assertEqual(adapter.WORKER_ARGV_PREFIX,
                                 ('-m','experiments.cf1_small_mechanism_approved','worker'))
                self.assertEqual(worker.task_matrix(),approved.task_matrix())
                with self.assertRaisesRegex(RuntimeError,'serialized nonnested'):
                    with approved.revision4():
                        self.fail('Nested context entered')
                raise ValueError('injected')
        self.assertEqual(vars(adapter),before_adapter)
        self.assertEqual(vars(worker),before_worker)
        self.assertEqual(vars(adapter.q),before_q)
        self.assertFalse(lock.locked())
        with approved.revision4():
            pass

    def test_busy_supervisor_does_not_change_globals(self):
        adapter,worker,small,approved,store,writes = harness()
        adapter._LOCK.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError,'already active'):
                with approved.revision4():
                    self.fail('Busy supervisor entered')
            self.assertEqual(adapter.q.CEILING,1800.)
            self.assertEqual(adapter.POLICY,'original')
        finally:
            adapter._LOCK.release()

    def test_affected_and_inherited_source_hashes_are_required(self):
        adapter,worker,small,approved,store,writes = harness()
        names = ('src/experiments/cf1_small_mechanism_approved.py',
            'src/tests/test_cf1_small_mechanism_approved.py','src/tests/test_constructive_controls.py',
            'src/experiments/cf1_small_mechanism_preflight.py',
            'src/tests/test_cf1_small_mechanism_preflight.py',
            'src/experiments/cf1_preparation_preflight.py',
            'src/tests/test_cf1_preparation_preflight.py')
        sources = {str(ROOT/name):'source:'+name for name in names}
        directory = ROOT/'research-20261023/cf1-small-approved-checks/attempt01'
        command = [str(ROOT/'.venv-local/bin/python'),'-m','pytest','-q',
                   'src/tests/test_cf1_small_mechanism_approved.py']
        attempt = {'attempt_id':'attempt01','revision':4,'command':command,
            'command_sha256':stable(command),'executed_tests':['test_cf1_small_mechanism_approved.py'],
            'source_hashes':sources}
        result = {'attempt_id':'attempt01','revision':4,'policy':approved.POLICY}
        store[str(directory/'attempt.json')] = attempt
        store[str(directory/'result.json')] = result
        self.assertEqual(approved.checked_sources(directory),{'inherited':'proof'})
        for name in names:
            key = str(ROOT/name)
            original = sources[key]
            for replacement in (None,'stale'):
                if replacement is None:
                    sources.pop(key)
                else:
                    sources[key] = replacement
                with self.assertRaisesRegex(ValueError,'misses revision[234] source'):
                    approved.checked_sources(directory)
                sources[key] = original
        for other in ('checks',directory.parent/'attempt02',directory.parent/'historical-attempt01'):
            with self.assertRaisesRegex(ValueError,'exact approved source-check attempt'):
                approved.checked_sources(other)
        for record,key,replacement in (
                (attempt,'attempt_id','attempt02'),(attempt,'revision',3),
                (attempt,'command',command+['src/tests/test_constructive_controls.py']),
                (attempt,'command_sha256','wrong'),(attempt,'executed_tests',[]),
                (attempt,'executed_tests',['test_cf1_small_mechanism_preflight.py']),
                (result,'attempt_id','attempt02'),(result,'revision',3),
                (result,'policy','cf1-small-mechanism-v3')):
            original = record[key]
            record[key] = replacement
            with self.assertRaisesRegex(ValueError,'execution identity differs'):
                approved.checked_sources(directory)
            record[key] = original

    def test_observation_requires_new_complete_read_and_is_idempotent(self):
        adapter,worker,small,approved,store,writes = harness()
        item,ack = ack_case(approved,store)
        raw = approved._ack_bytes(ack)
        def receive(item):
            if item['ack_bytes']==b'':
                item['ack_bytes'] = raw[:8]
            elif item['acknowledgment'] is None:
                item['ack_bytes'],item['acknowledgment'] = raw,ack
        adapter.q.receive_ack = receive
        with approved.revision4():
            adapter.q.receive_ack(item)
            self.assertEqual(writes,[])
            adapter.q.receive_ack(item)
            self.assertEqual(len(writes),1)
            path,observation = writes[0]
            self.assertEqual(Path(path).name,approved.ACK_OBSERVATION)
            self.assertEqual(observation['controller_observed_monotonic'],159.)
            self.assertEqual(observation['raw_payload_sha256'],hashlib.sha256(raw).hexdigest())
            adapter.q.receive_ack(item)
            self.assertEqual(len(writes),1)
        self.assertEqual(item['primary_reason'],'original failure')
        self.assertEqual(item['secondary_errors'],[{'old':'retained'}])

    def test_preexisting_ack_or_no_read_never_gets_observation(self):
        adapter,worker,small,approved,store,writes = harness()
        item,ack = ack_case(approved,store)
        item.update(ack_bytes=approved._ack_bytes(ack),acknowledgment=ack)
        approved._observe_receive_ack(lambda item:None,item)
        self.assertEqual(writes,[])

    def test_wrong_identity_and_original_read_errors_are_not_suppressed(self):
        for field,value in (('task_id','other'),('lock_sha256','other'),('parent_monotonic',99.)):
            adapter,worker,small,approved,store,writes = harness()
            item,ack = ack_case(approved,store)
            ack[field] = value
            def receive(item):
                item.update(ack_bytes=approved._ack_bytes(ack),acknowledgment=ack)
            with self.assertRaisesRegex(ValueError,'identity/payload mismatch'):
                approved._observe_receive_ack(receive,item)
            self.assertEqual(writes,[])
            self.assertEqual(item['primary_reason'],'original failure')
        def failed(item):
            item['ack_bytes'] = b'bad read evidence'
            raise OSError('read failed')
        with self.assertRaisesRegex(OSError,'read failed'):
            approved._observe_receive_ack(failed,item)
        self.assertEqual(item['ack_bytes'],b'bad read evidence')

    def test_exclusive_observation_write_failure_is_retained(self):
        adapter,worker,small,approved,store,writes = harness()
        item,ack = ack_case(approved,store)
        def receive(item):
            item.update(ack_bytes=approved._ack_bytes(ack),acknowledgment=ack)
        def fail_write(path,value):
            raise OSError('observation durability failed')
        adapter.q.write_new = fail_write
        with self.assertRaisesRegex(OSError,'durability failed'):
            approved._observe_receive_ack(receive,item)
        self.assertEqual(item['acknowledgment'],ack)
        self.assertEqual(item['primary_reason'],'original failure')

    def test_analysis_demands_inventory_bound_timely_controller_observation(self):
        adapter,worker,small,approved,store,writes = harness()
        item,ack = ack_case(approved,store)
        folder = item['folder']
        def receive(item):
            item.update(ack_bytes=approved._ack_bytes(ack),acknowledgment=ack)
        approved._observe_receive_ack(receive,item)
        observation = store[str(folder/approved.ACK_OBSERVATION)]
        receipt = {'task':item['task'],'lock_sha256':'lockhash','parent_monotonic':100.,
            'completion_acknowledgment':ack,
            'artifacts':{approved.ACK_OBSERVATION:adapter.q.sha(folder/approved.ACK_OBSERVATION)}}
        store[str(folder/'supervisor.json')] = receipt
        args = SimpleNamespace(output=str(folder.parent))
        proof = approved._transport_evidence(args,item['task'],'lockhash')
        self.assertEqual(proof['status'],'observed_by_endpoint')
        for observed in (160.,160.01,99.,float('nan')):
            observation['controller_observed_monotonic'] = observed
            receipt['artifacts'][approved.ACK_OBSERVATION] = adapter.q.sha(folder/approved.ACK_OBSERVATION)
            proof = approved._transport_evidence(args,item['task'],'lockhash')
            self.assertEqual(proof['status'],'observed_by_endpoint' if observed==160. else 'timing_unestablished')
            if observed==160.01:
                self.assertIn('does_not_establish_send_time',proof['reason'])
        observation['controller_observed_monotonic'] = 159.
        receipt['artifacts'][approved.ACK_OBSERVATION] = 'changed'
        self.assertEqual(approved._transport_evidence(args,item['task'],'lockhash')['status'],
                         'timing_unestablished')
        store.pop(str(folder/approved.ACK_OBSERVATION))
        self.assertEqual(approved._transport_evidence(args,item['task'],'lockhash')['status'],
                         'timing_unestablished')

    def test_report_writer_blocks_missing_observation_and_restores_on_failure(self):
        adapter,worker,small,approved,store,writes = harness()
        task, = approved.task_matrix()
        args = SimpleNamespace(lock='/inert-lock',report='/inert-report',output='/inert-cf1-output')
        store[args.lock] = {'tasks':[task]}
        initial = {'passed':True,'issues':[],'rows':[{'task':task,'issues':[]}]}
        def analyze(args):
            adapter.q.write_new(args.report,initial)
            return initial
        adapter.analyze = analyze
        writer = adapter.q.write_new
        report = approved.analyze(args)
        self.assertFalse(report['passed'])
        self.assertEqual(report['scope'],approved.SCOPE)
        self.assertIn(task['id']+':ack_transport_timing_unestablished',report['issues'])
        self.assertEqual(report,store[args.report])
        self.assertIs(adapter.q.write_new,writer)
        self.assertTrue(initial['passed'])
        self.assertEqual(initial['issues'],[])
        def failed(args):
            raise ValueError('analysis injected')
        adapter.analyze = failed
        with self.assertRaisesRegex(ValueError,'analysis injected'):
            approved.analyze(args)
        self.assertIs(adapter.q.write_new,writer)
        self.assertEqual(adapter.q.CEILING,1800.)


if __name__=='__main__':
    unittest.main()
