"""Source-only policy checks: no backend, fixture, solver or numerical imports."""
import ast
import hashlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]


def isolated_source(name, **bindings):
    """Exercise real shim bodies with inert dependency bindings only."""
    path = ROOT/'src'/'experiments'/(name+'.py')
    tree = ast.parse(path.read_text(),filename=str(path))
    tree.body = [node for node in tree.body if not (
        isinstance(node,ast.ImportFrom) and node.module=='experiments')]
    scope = {'__name__':'isolated_'+name,**bindings}
    exec(compile(tree,str(path),'exec'),scope)
    return SimpleNamespace(**scope)


def harness():
    q = SimpleNamespace(stable=lambda value:hashlib.sha256(
        json.dumps(value,sort_keys=True).encode()).hexdigest(),ROOT=ROOT)
    q.write_new = lambda path,value:value
    adapter = SimpleNamespace(q=q,POLICY='original',PACKAGE_START=1.,PACKAGE_LIMIT=2.,
        PACKAGE_CAP=3.,ANALYSIS_FINAL_RESERVE_S=5.,SUPERVISION_RESERVE_S=40.,
        ENGINEERING_BASE_ID=50999,ENGINEERING_TRIPS=80,
        FIXTURE_POLICY='same previously frozen engineering50999/80; no generation',
        WORKER_ARGV_PREFIX=('original',),task_matrix=lambda cases:[],
        checked_sources=lambda directory:{'original':'check'},_LOCK=threading.Lock())
    worker = SimpleNamespace(POLICY='original-worker',task_matrix=lambda:[])
    prep = isolated_source('cf1_preparation_preflight',adapter=adapter,native_worker=worker)
    small = isolated_source('cf1_small_mechanism_preflight',preparation=prep)
    return adapter,worker,prep,small


class SmallMechanismPolicyTests(unittest.TestCase):
    def test_uncleared_native_entry_points_reject_before_delegation(self):
        adapter,worker,prep,small = harness()
        self.assertEqual(small.POLICY,'cf1-small-mechanism-v3')
        self.assertFalse(small.NATIVE_DISPATCH_CLEARED)
        def forbidden(args):
            self.fail('Unapproved native entry delegated work')
        adapter.freeze = adapter.run = worker.worker = forbidden
        for entry in (small.freeze,small.run,small.worker):
            with self.assertRaisesRegex(RuntimeError,'prospective reserve is unapproved'):
                entry(None)
        self.assertEqual(adapter.POLICY,'original')
        self.assertEqual(worker.POLICY,'original-worker')

    def test_original_freezer_case_defaults_remain_engineering80(self):
        q = SimpleNamespace(stable=lambda value:hashlib.sha256(
            json.dumps(value,sort_keys=True).encode()).hexdigest(),launch=lambda:None)
        original = isolated_source('comparison_native_preflight',q=q)
        self.assertEqual((original.ENGINEERING_BASE_ID,original.ENGINEERING_TRIPS),(50999,80))
        self.assertEqual(original.FIXTURE_POLICY,
            'same previously frozen engineering50999/80; no generation')
        tasks = original.task_matrix([{'base_id':50999,'trips':80}])
        self.assertEqual([task['arm'] for task in tasks],['cf1','recovery'])
        self.assertTrue(all(task['base_id']==50999 and task['trips']==80 for task in tasks))
        with self.assertRaises(ValueError):
            original.task_matrix([{'base_id':50997,'trips':40}])

    def test_distinct_singleton_preserves_sixty_seconds(self):
        adapter,worker,prep,small = harness()
        task, = small.task_matrix([{'base_id':50997,'trips':40}])
        self.assertEqual({key:task[key] for key in ('arm','base_id','trips','seed','seconds',
            'fault','protocol_revision')},{'arm':'cf1','base_id':50997,'trips':40,
                'seed':17,'seconds':60.,'fault':None,'protocol_revision':3})
        self.assertEqual(task['id'],adapter.q.stable({key:value for key,value in task.items()
            if key!='id'})[:20])
        self.assertNotEqual(task['id'],prep.task_matrix()[0]['id'])
        for cases in ([],[{'base_id':50999,'trips':80}],[{'base_id':50997,'trips':80}],
                      [{'base_id':50997,'trips':40}]*2):
            with self.assertRaises(ValueError):
                small.task_matrix(cases)

    def test_policy_and_worker_bindings_restore_after_failure(self):
        adapter,worker,prep,small = harness()
        before_adapter,before_worker = vars(adapter).copy(),vars(worker).copy()
        original_lock = adapter._LOCK
        with self.assertRaisesRegex(ValueError,'injected'):
            with small.revision3():
                self.assertTrue(original_lock.locked())
                self.assertEqual((adapter.ENGINEERING_BASE_ID,adapter.ENGINEERING_TRIPS),(50997,40))
                self.assertEqual((adapter.PACKAGE_LIMIT,adapter.SUPERVISION_RESERVE_S,
                    adapter.ANALYSIS_FINAL_RESERVE_S),(115.,40.,5.))
                self.assertEqual(worker.task_matrix(),small.task_matrix())
                self.assertEqual(adapter.POLICY,small.POLICY)
                self.assertEqual(adapter.WORKER_ARGV_PREFIX,
                    ('-m','experiments.cf1_small_mechanism_preflight','worker'))
                with self.assertRaisesRegex(RuntimeError,'serialized nonnested'):
                    with small.revision3():
                        self.fail('Nested revision3 entered')
                raise ValueError('injected')
        self.assertEqual(vars(adapter),before_adapter)
        self.assertEqual(vars(worker),before_worker)
        self.assertFalse(original_lock.locked())
        with small.revision3():
            pass

    def test_busy_reviewed_supervisor_rejects_and_restores(self):
        adapter,worker,prep,small = harness()
        adapter._LOCK.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError,'already active'):
                with small.revision3():
                    self.fail('Busy supervision entered')
            self.assertEqual(adapter.POLICY,'original')
            self.assertTrue(adapter._LOCK.locked())
        finally:
            adapter._LOCK.release()
        with small.revision3():
            pass

    def test_new_sources_are_required_in_addition_to_inherited_checks(self):
        adapter,worker,prep,small = harness()
        names = ('src/experiments/cf1_small_mechanism_preflight.py',
                 'src/tests/test_cf1_small_mechanism_preflight.py')
        sources = {str(ROOT/name):'current:'+name for name in names}
        adapter.q.read = lambda path:{'source_hashes':sources}
        adapter.q.sha = lambda path:'current:'+str(Path(path).relative_to(ROOT))
        inherited = []
        # Function globals remain the actual isolated module namespace.
        small.checked_sources.__globals__['_BASE_CHECKED'] = lambda directory:(
            inherited.append(directory) or {'inherited':'proof'})
        self.assertEqual(small.checked_sources('checks'),{'inherited':'proof'})
        self.assertEqual(inherited,['checks'])
        for name in names:
            saved = sources.pop(str(ROOT/name))
            with self.assertRaisesRegex(ValueError,'misses revision3 source'):
                small.checked_sources('checks')
            sources[str(ROOT/name)] = saved

    def test_analysis_scope_and_writer_restore_on_failure(self):
        adapter,worker,prep,small = harness()
        written = []
        adapter.q.write_new = lambda path,value:written.append((path,value))
        writer = adapter.q.write_new
        args = SimpleNamespace(report='/tmp/small-mechanism-report.json')
        def analyze(args):
            adapter.q.write_new(args.report,{'scope':'old80','passed':False})
            raise ValueError('analysis injected')
        adapter.analyze = analyze
        with self.assertRaisesRegex(ValueError,'analysis injected'):
            small.analyze(args)
        self.assertEqual(written,[(args.report,{'scope':small.SCOPE,'passed':False})])
        self.assertIs(adapter.q.write_new,writer)
        self.assertEqual(adapter.POLICY,'original')


if __name__=='__main__':
    unittest.main()
