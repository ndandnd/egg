"""Bounded fake-clock admission allocation checks; no native backend or child."""
import builtins
from copy import deepcopy
from types import SimpleNamespace

import pytest

_original_import=builtins.__import__
def _guarded_import(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in admission reserve checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guarded_import
try:
    from experiments import recovery_qualification as q
    from egglab import recovery_coordinator as rc
finally:
    builtins.__import__=_original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guarded_import)


class Clock:
    def __init__(self,now=100.):
        self.now=now
    def __call__(self):
        return self.now


class Storage:
    def __init__(self):
        self.saved=[]
        self.result=None
    def save_fallback(self,witness):
        self.saved.append(deepcopy(witness))
        return {'sha256':'saved-witness'}
    def materialize(self,result,*,schedule,clock):
        self.result=deepcopy(result)
        return {'censored':clock()>schedule.deadline,'finished_monotonic':clock()}


def witness(tag='old',bill='7'):
    return {'plan':{'tag':tag},'replay':{'valid':True},
            'true_bill':float(bill),'true_bill_exact':bill}


def cases():
    return SimpleNamespace(identity=lambda:'prefix'),SimpleNamespace(identity=lambda:'full')


def test_schedule_retains_hard_limits_and_declares_planned_reserve():
    s=rc.Schedule(100.,130.)
    assert (s.prefix_integer_end,s.full_integer_end,s.prefix_end,s.planner_end)==(112.,124.,115.,127.)
    assert (s.prefix_search_end,s.full_search_end,s.prefix_handoff_end,s.full_handoff_end)==(110.,122.,113.,125.)
    assert s.admission_reserve_s==2.
    split=q.qualification_split()
    assert split['prefix_integer_s']==12. and split['full_integer_s']==24.
    assert split['prefix_search_s']==10. and split['full_search_s']==22.
    assert split['prefix_handoff_s']==13. and split['full_handoff_s']==25.
    assert split['planned_admission_headroom_s']==2.
    assert split['handoff_policy']=='anytime-hard-admission-v1'


@pytest.mark.parametrize('arm',['static','cold'])
@pytest.mark.parametrize('returned',[125.,125.001,127.,127.001])
def test_control_target_miss_is_diagnostic_until_hard_admission_deadline(monkeypatch,arm,returned):
    clock=Clock(104.)
    monkeypatch.setattr(q.time,'monotonic',clock)
    calls=[];lifts=[]
    def planner(case,a,b,budget,**kw):
        calls.append((budget,kw))
        clock.now=returned
        return {'plan':{'tag':'candidate'}}
    def lift(*a,**kw):
        lifts.append(clock.now)
        clock.now=126.9
        return witness()
    monkeypatch.setattr(rc,'lift_plan',lift)
    monkeypatch.setattr(rc,'_full_lower',lambda *a,**kw:(None,[]))
    store=Storage()
    q.control('full','target',[1.],[0.],{'id':'task','arm':arm},100.,store,
              rc.pf.Budget(phase_seconds=30.),planner,lambda:True)
    budget,kw=calls[0]
    assert kw['deadline']==125. and budget.wall_seconds==21. and budget.phase_seconds==18.
    assert lifts==([returned] if returned<127. else [])
    assert len(store.saved)==int(returned<127.)
    assert (store.result['selected'] is not None) is (returned<127.)
    assert store.result['schedule']==rc.Schedule(100.,130.).as_dict()
    returned_event=next(e for e in store.result['events'] if e['event']=='control_planner_return')
    assert returned_event['planner_target']==125.
    assert returned_event['target_overrun_s']==max(0.,returned-125.)
    assert returned_event['admission_cutoff']==127. and returned_event['admission_open'] is (returned<127.)


def test_actual_control_native_caps_share_handoff_and_completion(monkeypatch):
    clock=Clock()
    monkeypatch.setattr(q.time,'monotonic',clock)
    calls=[]
    def native(built,budget,deadline):
        calls.append((budget.phase_seconds,deadline))
        if built['x'][0].lb==built['x'][0].ub:
            clock.now += budget.phase_seconds
        return {'status':'NO_SOLUTION_FOUND'}
    monkeypatch.setattr(rc.pf,'_optimize_once',native)
    def planner(case,a,b,budget,**kw):
        built={'x':[SimpleNamespace(lb=0,ub=1)]}
        rc.pf._optimize_once(built,budget,kw['deadline'])
        clock.now=124.
        built['x'][0].ub=0
        rc.pf._optimize_once(built,budget,kw['deadline'])
        with pytest.raises(TimeoutError):
            rc.pf._optimize_once(built,budget,kw['deadline'])
        return {'status':'NO_SOLUTION_FOUND'}
    store=Storage()
    q.control('full','target',[1.],[0.],{'id':'task','arm':'static'},100.,store,
              rc.pf.Budget(phase_seconds=30.),planner,lambda:True)
    assert calls==[(22.,122.),(1.,125.)]
    assert store.result['completion_spent_s']==1.
    assert not store.result['failures']


@pytest.mark.parametrize('returned',[113.,113.001,115.,115.001])
def test_coordinator_prefix_target_and_hard_admission_control_dispatch(monkeypatch,returned):
    source,full=cases();clock=Clock(104.);store=Storage()
    calls=[];lifts=[]
    def planner(case,a,b,budget,**kw):
        calls.append((case,budget,kw))
        if case is source:
            clock.now=returned
            return {'plan':{'tag':'prefix'}}
        return {'status':'unresolved'}
    def lift(*a,**kw):
        lifts.append(clock.now)
        clock.now=114.5
        return witness()
    monkeypatch.setattr(rc,'lift_plan',lift)
    outcome=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
                          storage=store,clock=clock,planner=planner)['result']
    assert calls[0][1].wall_seconds==9. and calls[0][1].phase_seconds==6.
    assert calls[0][2]['deadline']==113.
    if returned<115.:
        assert lifts==[returned] and len(calls)==2
        assert calls[1][2]['deadline']==125.
        assert calls[1][1].wall_seconds==10.5 and calls[1][1].phase_seconds==7.5
        assert outcome['selected']['true_bill_exact']=='7'
    else:
        assert lifts==[] and len(calls)==1 and outcome['dispatch_stopped']
        assert not outcome['full_dispatched'] and outcome['selected'] is None


@pytest.mark.parametrize('mode',['late_no_plan','late_candidate','lift_failure','postlift_overrun'])
def test_prior_durable_fallback_survives_failed_later_admission(monkeypatch,mode):
    source,full=cases();clock=Clock();store=Storage()
    lifts=[]
    def lift(source,full,plan,**kw):
        lifts.append(plan['tag'])
        if plan['tag']=='old':
            return witness()
        if mode=='lift_failure':
            raise ValueError('later candidate replay rejected')
        clock.now=127.001
        return witness('new','1')
    monkeypatch.setattr(rc,'lift_plan',lift)
    def planner(*a,**kw):
        assert store.saved==[witness()]
        clock.now=127.001 if mode.startswith('late_') else 125.
        return {'status':'unresolved'} if mode=='late_no_plan' else {'plan':{'tag':'new'}}
    result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
        storage=store,clock=clock,planner=planner,physical_fallback={'tag':'old'})['result']
    assert result['fallback']==witness() and result['selected']==witness()
    assert store.saved==[witness()] and result['failures']
    assert lifts==(['old'] if mode.startswith('late_') else ['old','new'])
    assert result['global_lower_bound'] is None


def test_late_bound_only_prefix_stops_full_without_importing_bound(monkeypatch):
    source,full=cases();clock=Clock();store=Storage();calls=[]
    def planner(case,*a,**kw):
        calls.append(case)
        clock.now=115.001
        return {'lower':1e9,'status':'bounded'}
    result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
        storage=store,clock=clock,planner=planner)['result']
    assert calls==[source] and result['dispatch_stopped'] and not result['full_dispatched']
    assert result['selected'] is None and result['global_lower_bound'] is None


def test_loading_past_planned_full_search_starts_no_planner():
    source,full=cases();clock=Clock(122.);store=Storage()
    result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
        storage=store,clock=clock,planner=lambda *a,**kw:pytest.fail('No fresh allowance'))['result']
    assert result['selected'] is None and not result['full_dispatched']
    assert result['schedule']==rc.Schedule(100.,130.).as_dict()


def test_eighty_trip_order_is_explicit_with_unchanged_task_identities():
    tasks=q.task_matrix(list(q.DESIGN))
    assert [row['trips'] for row in tasks]==[80]*4+[40]*4
    assert tasks==q.task_matrix(list(reversed(q.DESIGN)))
    assert [row['arm'] for row in tasks[:4]]==list(q.ARMS)
    for task in tasks:
        identity={key:value for key,value in task.items() if key!='id'}
        assert task['id']==q.stable(identity)[:20]


@pytest.mark.parametrize('path',['control','coordinator'])
@pytest.mark.parametrize('failure',['late','exception'])
def test_first_durable_save_failure_never_publishes_fallback(monkeypatch,path,failure):
    source,full=cases();clock=Clock();store=Storage()
    cutoff=127. if path=='control' else 115.
    def lift(*a,**kw):
        return witness()
    monkeypatch.setattr(rc,'lift_plan',lift)
    def save(candidate):
        store.saved.append(deepcopy(candidate))
        if failure=='exception':
            raise OSError('first fallback fsync failed')
        clock.now=cutoff+.001
        return {'sha256':'late-unadmitted-artifact'}
    store.save_fallback=save
    def planner(*a,**kw):
        return {'plan':{'tag':'first'}}
    if path=='control':
        monkeypatch.setattr(q.time,'monotonic',clock)
        q.control(full,source,[1.],[0.],{'id':'task','arm':'static'},100.,store,
                  rc.pf.Budget(),planner,lambda:True)
        result=store.result
    else:
        result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
            storage=store,clock=clock,planner=planner)['result']
        assert result['fallback_artifact'] is None and not result['full_dispatched']
    assert store.saved==[witness()]
    assert result['selected'] is None and result['fallback'] is None and result['failures']
    if failure=='late':
        rejected=[e for e in result['events'] if e['event'] in
                  ('rejected_durable_witness','control_durable_witness_rejected')]
        assert len(rejected)==1 and rejected[0]['artifact']=={'sha256':'late-unadmitted-artifact'}


@pytest.mark.parametrize('arm',['static','cold'])
def test_control_late_bound_only_return_is_failure_without_bound_admission(monkeypatch,arm):
    clock=Clock();store=Storage();admissions=[]
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(rc,'_full_lower',lambda *a,**kw:admissions.append(True))
    def planner(*a,**kw):
        clock.now=127.001
        return {'lower':1e9,'status':'bounded'}
    q.control('full','target',[1.],[0.],{'id':'task','arm':arm},100.,store,
              rc.pf.Budget(),planner,lambda:True)
    assert admissions==[] and store.result['failures']
    assert store.result['global_lower_bound'] is None and store.result['selected'] is None
