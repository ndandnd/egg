"""Sixty-second source contracts using symbolic inputs and fake native calls."""
import builtins
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import json
import math
from types import SimpleNamespace

import pytest

_original_import = builtins.__import__
def _guard(name, *args, **kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in comparison pipeline checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__ = _guard
try:
    from egglab import comparison_coordinator as pipeline
    from egglab import constructive_proposal as provider
    from egglab import recovery_coordinator as rc
    from test_constructive_controls import chain_case, Clock
finally:
    builtins.__import__ = _original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guard)


def raw_plan(tag='old'):
    return {'tag':tag}


def witness(tag='old', bill=10.):
    exact=Fraction(bill)
    return {'plan':raw_plan(tag),'replay':{'replay_ok':True},
            'true_bill':float(exact),'true_bill_exact':str(exact)}


class Storage:
    def __init__(self,clock,save_seconds=0.,result_seconds=0.,completion_seconds=0.):
        self.clock=clock;self.save_seconds=save_seconds
        self.result_seconds=result_seconds;self.completion_seconds=completion_seconds
        self.saved=[];self.result=None
    def save_fallback(self,value):
        self.saved.append(deepcopy(value));self.clock.now+=self.save_seconds
        return {'sha256':'saved-fallback'}
    def materialize(self,result,*,schedule,clock):
        self.result=deepcopy(result);self.clock.now+=self.result_seconds
        endpoint=clock();self.clock.now+=self.completion_seconds
        return {'finished_monotonic':endpoint,'completion_monotonic':clock(),
                'elapsed_s':endpoint-schedule.parent_monotonic,
                'censored':endpoint>schedule.deadline or clock()>schedule.deadline}


def proposal_ledger(active=2,undone=0):
    return {'status':'proposal','selected_ids':['outA','AB','inB'],
            'active_merge_count':active,'undone_count':undone}


def infeasible():
    return {'status':'infeasible','plan':None,'reverse_repair_allowed':True,'failures':[],
            'stages':[{'stage':'feasibility','stats':{'status':'INFEASIBLE','incumbent':None}}]}


def completed(tag='proposal'):
    return {'status':'feasible','plan':raw_plan(tag),'replay':{'replay_ok':True},
            'true_bill_exact':'10','true_bill':10.,'failures':[],'stages':[]}


def call_provider(clock,*,constructor=None,completer=None,undoer=None,allowance=None,events=None,allowed=None):
    return provider.propose(chain_case(2),[1.],[0.],
        schedule=SimpleNamespace(construction_end=106.,charging_stage_end=112.),
        allowance=allowance or rc.CompletionAllowance(limit=6.),budget=rc.pf.Budget(),
        clock=clock,allowed=(lambda:True) if allowed is None else allowed,events=[] if events is None else events,
        constructor=constructor or (lambda *args,**kw:proposal_ledger()),
        completer=completer or (lambda *args,**kw:completed()),undoer=undoer)


def test_provider_repairs_only_twice_lifo_under_one_original_deadline():
    clock=Clock(101.);calls=[];undos=[]
    def complete(*args,deadline,**kw):
        calls.append(deadline);clock.now+=1.
        return infeasible() if len(calls)<3 else completed()
    def undo(case,ledger,count,*,deadline,**kw):
        undos.append((count,deadline,ledger['active_merge_count']))
        clock.now+=.5
        return proposal_ledger(ledger['active_merge_count']-1,ledger['undone_count']+1)
    result=call_provider(clock,completer=complete,undoer=undo)
    assert result['plan']==raw_plan('proposal') and result['repairs']==2
    assert calls==[107.]*3 and undos==[(1,107.,2),(1,107.,1)]
    assert result['completion_deadline']==107. and not result['durable_fallback']
    assert result['global_lower_bound'] is None and not result['start_submitted']


@pytest.mark.parametrize('damage',['unresolved','fault','witness','no_reverse','objective_stage','wrong_status','incumbent'])
def test_unqualified_charging_outcomes_never_authorize_repair(damage):
    value=infeasible()
    if damage=='unresolved':value['status']='unresolved'
    elif damage=='fault':value['failures']=[{'error':'backend failed'}]
    elif damage=='witness':value['plan']=raw_plan('retained')
    elif damage=='no_reverse':value['reverse_repair_allowed']=False
    elif damage=='objective_stage':value['stages'][0]['stage']='objective1'
    elif damage=='wrong_status':value['stages'][0]['stats']['status']='NO_SOLUTION_FOUND'
    elif damage=='incumbent':value['stages'][0]['stats']['incumbent']=0.
    result=call_provider(Clock(101.),completer=lambda *args,**kw:value,
        undoer=lambda *args,**kw:pytest.fail('Unqualified repair'))
    assert result['repairs']==0


@pytest.mark.parametrize('returned',[107.,math.nextafter(107.,math.inf)])
def test_completed_helper_deadline_equality_vs_overrun(returned):
    clock=Clock(101.)
    def complete(*args,**kw):clock.now=returned;return completed()
    result=call_provider(clock,completer=complete)
    assert (result['plan'] is not None) is (returned==107.)
    assert bool(result['failures']) is (returned>107.)


@pytest.mark.parametrize('returned',[106.,math.nextafter(106.,math.inf)])
def test_completed_construction_deadline_equality_vs_overrun(returned):
    clock=Clock(100.);calls=[]
    def construct(*args,**kw):clock.now=returned;return proposal_ledger()
    def complete(*args,deadline,**kw):calls.append(deadline);return completed()
    result=call_provider(clock,constructor=construct,completer=complete)
    assert calls==([112.] if returned==106. else [])
    assert (result['plan'] is not None) is (returned==106.)


def test_remaining_native_quota_clamps_first_completion_window_without_wall_double_charge():
    allowance=rc.CompletionAllowance(spent=2.,limit=6.);clock=Clock(101.);seen=[]
    def complete(*args,deadline,**kw):seen.append(deadline);clock.now+=1.;return completed()
    result=call_provider(clock,completer=complete,allowance=allowance)
    assert seen==[105.] and result['completion_deadline']==105.
    assert allowance.spent==2.  # Fake setup/replay wall cost is not a native call.


def test_invalid_undo_stops_instead_of_renewing_or_repeating():
    calls=[]
    def complete(*args,**kw):calls.append(True);return infeasible()
    result=call_provider(Clock(101.),completer=complete,
        undoer=lambda case,ledger,*args,**kw:deepcopy(ledger))
    assert len(calls)==1 and result['plan'] is None and result['failures']


def test_expired_provider_entries_dispatch_no_constructor_or_helper():
    result=call_provider(Clock(106.),constructor=lambda *args,**kw:pytest.fail('Expired entry'))
    assert result['plan'] is None and result['failures']


@pytest.mark.parametrize('gate',[False,1])
def test_provider_requires_explicit_true_dispatch_gate(gate):
    result=call_provider(Clock(101.),allowed=lambda:gate,
        constructor=lambda *args,**kw:pytest.fail('Closed/nonboolean gate'))
    assert result['plan'] is None and result['failures']


def test_schedule60_is_explicit_and_keeps_absolute_limits():
    s=pipeline.Schedule60(100.,160.)
    assert (s.construction_end,s.charging_stage_end)==(106.,112.)
    assert (s.prefix_integer_end,s.prefix_search_end,s.prefix_handoff_end,s.prefix_end)==(124.,120.,126.,130.)
    assert (s.full_integer_end,s.full_search_end,s.full_handoff_end,s.planner_end)==(148.,144.,150.,154.)
    assert s.completion_limit_s==6. and s.finalization_reserve_s==6.
    assert s.planned_admission_headroom_s==4.
    with pytest.raises(ValueError):pipeline.Schedule60(100.,130.)


@pytest.fixture
def pipeline_cases(monkeypatch):
    full=chain_case(2);source=replace(full,movements=full.movements[:-1]);lifted=[]
    def lift(origin,target,plan,**kw):
        lifted.append((origin,target,deepcopy(plan)))
        return witness(plan['tag'],plan.get('bill',10.))
    monkeypatch.setattr(rc,'lift_plan',lift)
    monkeypatch.setattr(rc,'_full_lower',lambda *args,**kw:(None,[]))
    return source,full,lifted


def run60(source,full,clock,store,**kw):
    kw.setdefault('budget',rc.pf.Budget(phase_seconds=60.,wall_seconds=60.,max_rounds=8))
    return pipeline.coordinate60(source,full,[1.],[0.],parent_monotonic=100.,deadline=160.,
                                 storage=store,clock=clock,**kw)


def test_anchor_charges_loading_and_scoring_durable_before_binary_only_start(pipeline_cases):
    source,full,lifts=pipeline_cases;clock=Clock(119.);store=Storage(clock,save_seconds=.2);calls=[]
    def planner(case,a,b,budget,**kw):
        calls.append((case,budget,kw))
        if case is source:
            assert budget.phase_seconds==1. and budget.wall_seconds==7. and kw['deadline']==126.
            clock.now=129.
            return {'plan':raw_plan('prefix'),'rounds':[{},{}]}
        assert store.saved and clock.now==129.2
        assert kw['start_plan']==store.saved[0]['plan'] and kw['start_case'] is full
        assert kw['deadline']==150. and budget.wall_seconds==pytest.approx(20.8)
        assert budget.phase_seconds==pytest.approx(14.8) and budget.max_rounds==6
        xs=[SimpleNamespace(idx=i,var_type='B') for i in range(len(full.movements))]
        continuous=SimpleNamespace(idx=len(xs),var_type='C')
        model=SimpleNamespace(vars=xs+[continuous],start=None)
        rc.pf._attach_pricing_start(full,{'x':xs,'model':model},{'outA','AB','inB'})
        assert len(model.start)==len(xs) and all(var.var_type=='B' and value in (0,1) for var,value in model.start)
        assert all(var is not continuous for var,_ in model.start)
        clock.now=151.
        return {'plan':raw_plan('full'),'rounds':[{}]}
    outcome=run60(source,full,clock,store,planner=planner)
    result=outcome['result']
    assert len(calls)==2 and result['selected'] and result['fallback_artifact']
    assert not result['failures'] and not outcome['censored']
    assert result['start_proposal']['proposed'] is True
    assert result['start_proposal']['native_processing']=='unknown'
    assert result['start_proposal']['requires_external_native_evidence'] is True


def test_exact_replay_bill_selection_can_improve_without_float_bill_change(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock)
    old=Fraction(10.)+Fraction(.1);new=Fraction(10.)+Fraction(math.nextafter(.1,0.))
    assert float(old)==float(new) and new<old
    def planner(case,*args,**kw):
        return {'plan':{'tag':'prefix' if case is source else 'full','bill':str(old if case is source else new)},'rounds':[{}]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert result['selected']['plan']['tag']=='full' and Fraction(result['selected']['true_bill_exact'])==new
    assert result['fallback']['plan']['tag']=='prefix' and len(store.saved)==1


@pytest.mark.parametrize('later',['reject','timeout','late'])
def test_prior_durable_fallback_survives_full_start_or_search_failure(pipeline_cases,later):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock)
    def planner(case,*args,**kw):
        if case is source:return {'plan':raw_plan('prefix'),'rounds':[{}]}
        assert store.saved and kw['start_plan']==store.saved[0]['plan']
        if later=='reject':raise ValueError('binary start rejected')
        if later=='timeout':raise TimeoutError('full search timed out')
        clock.now=154.001
        return {'plan':raw_plan('late'),'rounds':[{}]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert result['selected']==result['fallback']==witness('prefix')
    assert result['failures'] and result['global_lower_bound'] is None


@pytest.mark.parametrize('arm',['cold','cf1'])
def test_cold_and_empty_cf1_provider_skip_restricted_search(pipeline_cases,arm):
    source,full,_=pipeline_cases;clock=Clock(105.);store=Storage(clock);calls=[];providers=[]
    def proposal(*args,**kw):providers.append(kw);return {'status':'no_proposal','plan':None,'failures':[]}
    def planner(case,*args,**kw):
        calls.append(case);assert case is full and kw['start_plan'] is None
        return {'status':'unresolved','rounds':[{}]}
    result=run60(source,full,clock,store,arm=arm,planner=planner,proposal_provider=proposal)['result']
    assert calls==[full] and len(providers)==int(arm=='cf1')
    assert result['selected'] is None and result['global_lower_bound'] is None


def test_late_prefix_cannot_renew_clock_or_dispatch_full(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);calls=[]
    def planner(case,*args,**kw):calls.append(case);clock.now=130.001;return {'plan':raw_plan(),'rounds':[{}]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert calls==[source] and not result['full_dispatched'] and result['selected'] is None and result['failures']


def test_loading_past_all_search_gates_dispatches_no_new_budget(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(144.);store=Storage(clock)
    result=run60(source,full,clock,store,planner=lambda *args,**kw:pytest.fail('No fresh search budget'))['result']
    assert result['selected'] is None and not result['full_dispatched']
    assert result['schedule']['deadline']==160.


def test_loading_past_unused_prefix_can_use_only_original_cold_full_remainder(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(131.);store=Storage(clock);calls=[]
    def planner(case,a,b,budget,**kw):
        calls.append(case)
        assert case is full and kw['start_plan'] is None and kw['deadline']==150.
        assert budget.phase_seconds==13. and budget.wall_seconds==19. and budget.max_rounds==8
        return {'status':'unresolved','rounds':[]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert calls==[full] and result['full_dispatched'] and result['selected'] is None


@pytest.mark.parametrize('late',['result','completion'])
def test_output_and_completion_fsync_costs_belong_to_original_endpoint(pipeline_cases,late):
    source,full,_=pipeline_cases;clock=Clock(101.)
    store=Storage(clock,result_seconds=60. if late=='result' else 58.9,
                  completion_seconds=.2 if late=='completion' else 0.)
    outcome=run60(source,full,clock,store,planner=lambda *args,**kw:{'status':'unresolved','rounds':[]})
    assert outcome['censored'] and outcome['completion']['completion_monotonic']>160.
    if late=='completion':assert outcome['completion']['finished_monotonic']<160.


def test_late_first_fallback_fsync_is_evidence_not_admission(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(129.);store=Storage(clock,save_seconds=2.);calls=[]
    # Simulate earlier setup ending just before the prefix search gate, then a long planner result.
    clock.now=119.
    def planner(case,*args,**kw):calls.append(case);clock.now=129.;return {'plan':raw_plan(),'rounds':[{}]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert store.saved and result['fallback'] is None and result['fallback_artifact'] is None
    assert result['selected'] is None and calls==[source] and result['failures']


@pytest.mark.parametrize('bound',[9.,11.])
def test_only_full_unrestricted_bounds_are_admitted_and_contradictions_clear(pipeline_cases,monkeypatch,bound):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);bound_calls=[]
    def planner(case,*args,**kw):
        return {'plan':raw_plan(),'rounds':[{}],'lower':1e99 if case is source else bound}
    def lower(result,case,a,b,clock,cutoff):
        bound_calls.append((result,case,cutoff));assert case is full
        return bound,[{'scope':'full_unrestricted_mip','lower':bound}]
    monkeypatch.setattr(rc,'_full_lower',lower)
    result=run60(source,full,clock,store,planner=planner)['result']
    assert len(bound_calls)==1 and bound_calls[0][0]['lower']==bound and bound_calls[0][2]==154.
    if bound==9.:assert result['global_lower_bound']==9. and result['bound_provenance']
    else:assert result['global_lower_bound'] is None and not result['bound_provenance']


def test_actual_optimizer_hook_shares_six_seconds_between_provider_and_full(pipeline_cases,monkeypatch):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);native_calls=[];allowances=[]
    built={'x':[SimpleNamespace(lb=1.,ub=1.)]}
    def optimize(built,budget,deadline):
        native_calls.append((budget.phase_seconds,deadline));clock.now+=budget.phase_seconds
        return {'status':'NO_SOLUTION_FOUND'}
    monkeypatch.setattr(rc.pf,'_optimize_once',optimize)
    def complete(*args,**kw):
        rc.pf._optimize_once(built,replace(rc.pf.Budget(),phase_seconds=4.),kw['deadline'])
        return completed('cf1')
    def proposal(case,a,b,**kw):
        allowances.append(kw['allowance'])
        return provider.propose(case,a,b,**kw,constructor=lambda *args,**kw:proposal_ledger(),completer=complete)
    def planner(case,a,b,budget,**kw):
        assert case is full and store.saved and kw['start_plan'] is not None
        rc.pf._optimize_once(built,replace(budget,phase_seconds=10.),kw['deadline'])
        with pytest.raises(TimeoutError):rc.pf._optimize_once(built,budget,kw['deadline'])
        return {'status':'unresolved','rounds':[]}
    result=run60(source,full,clock,store,arm='cf1',planner=planner,proposal_provider=proposal)['result']
    assert [cap for cap,_ in native_calls]==[4.,2.]
    assert allowances[0].spent==6. and result['completion_spent_s']==6.
    assert result['selected'] and rc.pf._optimize_once is optimize


def test_cf1_provider_subproblem_bound_never_becomes_global(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(105.);store=Storage(clock)
    def proposal(*args,**kw):
        return {'status':'proposal','plan':raw_plan('cf1'),'failures':[],
                'global_lower_bound':1e99,'true_bill_exact':'0','completion_deadline':112.}
    result=run60(source,full,clock,store,arm='cf1',proposal_provider=proposal,
        planner=lambda *args,**kw:{'status':'unresolved','rounds':[]})['result']
    assert result['selected']['true_bill_exact']=='10'  # Coordinator replay, not the provider's claimed bill.
    assert result['global_lower_bound'] is None and not result['bound_provenance']


def test_eight_round_total_budget_cannot_be_renewed_for_full_search(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);calls=[]
    def planner(case,*args,**kw):
        calls.append(case);assert case is source
        return {'plan':raw_plan('prefix'),'rounds':[{}]*8}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert calls==[source] and result['selected'] and not result['full_dispatched']
    assert result['mip_rounds_used']==8


@pytest.mark.parametrize('rounds',[None,{},[{},{}]*5])
def test_unknown_or_over_budget_round_accounting_stops_dispatch(pipeline_cases,rounds):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);calls=[]
    def planner(case,*args,**kw):calls.append(case);return {'plan':raw_plan(),'rounds':rounds}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert calls==[source] and not result['full_dispatched'] and result['failures']


def test_actual_integer_hook_rejects_extra_backend_call_at_total_round_limit(pipeline_cases,monkeypatch):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);native_calls=[]
    def optimize(*args):native_calls.append(True);return {'status':'NO_SOLUTION_FOUND'}
    monkeypatch.setattr(rc.pf,'_optimize_once',optimize)
    def planner(case,a,b,budget,**kw):
        assert case is source and budget.max_rounds==3
        built={'x':[SimpleNamespace(lb=0.,ub=1.)]}
        for _ in range(3):rc.pf._optimize_once(built,budget,kw['deadline'])
        with pytest.raises((TimeoutError,ValueError,RuntimeError)):
            rc.pf._optimize_once(built,budget,kw['deadline'])
        return {'status':'unresolved','rounds':[{}]*3}
    result=run60(source,full,clock,store,planner=planner,
        budget=rc.pf.Budget(phase_seconds=60.,wall_seconds=60.,max_rounds=3))['result']
    assert len(native_calls)==3 and result['mip_rounds_used']==3 and not result['full_dispatched']


def test_budget_above_eight_mip_rounds_rejected_before_planner(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock)
    with pytest.raises(ValueError):
        run60(source,full,clock,store,planner=lambda *args,**kw:pytest.fail('Invalid round budget'),
            budget=rc.pf.Budget(max_rounds=9))


def test_capture_event_sequence_disambiguates_repaired_round_zero_without_payload_loss(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);attempts=[]
    def complete(*args,record,**kw):
        index=len(attempts);attempts.append(index)
        record({'event':'native_incumbent','round':0,'variables':[{'name':'x','value':index}]})
        value=infeasible() if index<2 else completed()
        value['events']=[{'duplicate':'must-not-repeat-in-provider-audit'}]
        return value
    def undo(case,ledger,*args,**kw):return proposal_ledger(ledger['active_merge_count']-1,ledger['undone_count']+1)
    def proposal(case,a,b,**kw):
        return provider.propose(case,a,b,**kw,constructor=lambda *args,**kw:proposal_ledger(),
                                completer=complete,undoer=undo)
    def planner(*args,record,**kw):
        record({'event':'native_incumbent','round':0,'variables':[{'name':'x','value':3}]})
        return {'status':'unresolved','rounds':[{}]}
    result=run60(source,full,clock,store,arm='cf1',proposal_provider=proposal,planner=planner)['result']
    captures=[row for row in result['events'] if row['event']=='native_incumbent']
    assert [row['variables'][0]['value'] for row in captures]==[0,1,2,3]
    assert len({row['event_sequence'] for row in captures})==4
    assert [row['event_sequence'] for row in result['events']]==list(range(len(result['events'])))
    audit=result['provider_audit']
    assert audit['construction'] and all(row['stage']!='construction' for row in audit['stages'])
    assert all(not {'plan','replay','events'} & row['result'].keys() for row in audit['stages'])


@pytest.mark.parametrize('declared',[112.001,float('inf'),True])
def test_raw_cf1_deadline_cannot_claim_time_outside_charging_stage(pipeline_cases,declared):
    source,full,lifts=pipeline_cases;clock=Clock(105.);store=Storage(clock)
    def proposal(*args,**kw):
        return {'status':'proposal','plan':raw_plan('bad-window'),'completion_deadline':declared,'failures':[]}
    result=run60(source,full,clock,store,arm='cf1',proposal_provider=proposal,
        planner=lambda *args,**kw:{'status':'unresolved','rounds':[]})['result']
    assert result['fallback'] is None and result['selected'] is None and not lifts
    assert result['failures'] and result['global_lower_bound'] is None


@pytest.mark.parametrize('invalid',[float('nan'),True,99.])
def test_invalid_initial_clock_rejected_before_any_work(pipeline_cases,invalid):
    source,full,_=pipeline_cases;clock=Clock(invalid);store=Storage(clock)
    with pytest.raises(ValueError):
        run60(source,full,clock,store,planner=lambda *args,**kw:pytest.fail('Invalid initial clock'))
    assert not store.saved and store.result is None


def test_nan_native_return_closes_sticky_gate_even_if_raw_clock_recovers(pipeline_cases,monkeypatch):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);backend=[]
    def optimize(*args):backend.append(True);clock.now=float('nan');return {'status':'NO_SOLUTION_FOUND'}
    monkeypatch.setattr(rc.pf,'_optimize_once',optimize)
    def planner(case,a,b,budget,**kw):
        if case is source:return {'plan':raw_plan('prefix'),'rounds':[{}]}
        built={'x':[SimpleNamespace(lb=0.,ub=1.)]}
        with pytest.raises(ValueError):rc.pf._optimize_once(built,budget,kw['deadline'])
        clock.now=102.
        with pytest.raises((ValueError,TimeoutError)):
            rc.pf._optimize_once(built,budget,kw['deadline'])
        return {'status':'unresolved','rounds':[{}]}
    outcome=run60(source,full,clock,store,planner=planner)
    assert len(backend)==1 and outcome['censored']
    assert outcome['result']['status']=='clock_failed' and outcome['result']['fallback']==witness('prefix')
    assert outcome['result']['global_lower_bound'] is None and rc.pf._optimize_once is optimize


def test_backward_clock_after_durable_admission_retains_fallback_but_never_certifies(pipeline_cases):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock)
    def planner(case,*args,**kw):
        if case is source:return {'plan':raw_plan('prefix'),'rounds':[{}]}
        clock.now=100.5  # Still after anchor100, but earlier than an already observed101.
        return {'plan':raw_plan('bad-clock'),'rounds':[{}],'lower':1e99}
    outcome=run60(source,full,clock,store,planner=planner)
    assert outcome['censored'] and outcome['result']['status']=='clock_failed'
    assert outcome['result']['fallback']==witness('prefix') and outcome['result']['global_lower_bound'] is None


@pytest.mark.parametrize('indices',[[2],[0,0]])
def test_malformed_callback_indices_block_backend_dispatch(pipeline_cases,monkeypatch,indices):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);backend=[]
    monkeypatch.setattr(rc.pf,'_optimize_once',lambda *args:backend.append(True))
    def planner(case,a,b,budget,record,**kw):
        assert case is source
        for index in indices:record({'event':'native_start','round':index})
        with pytest.raises(RuntimeError):
            rc.pf._optimize_once({'x':[SimpleNamespace(lb=0.,ub=1.)]},budget,kw['deadline'])
        return {'status':'unresolved','rounds':[]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert not backend and not result['full_dispatched'] and result['failures']


def test_callback_dispatch_and_returned_round_describe_one_attempt_not_three(pipeline_cases,monkeypatch):
    source,full,_=pipeline_cases;clock=Clock(101.);store=Storage(clock);backend=[]
    def optimize(*args):backend.append(True);return {'status':'NO_SOLUTION_FOUND'}
    monkeypatch.setattr(rc.pf,'_optimize_once',optimize)
    def planner(case,a,b,budget,record,**kw):
        assert budget.max_rounds==(8 if case is source else 7)
        record({'event':'native_start','round':0})
        rc.pf._optimize_once({'x':[SimpleNamespace(lb=0.,ub=1.)]},budget,kw['deadline'])
        return {'plan':raw_plan('prefix' if case is source else 'full'),'rounds':[{}]}
    result=run60(source,full,clock,store,planner=planner)['result']
    assert len(backend)==2 and result['mip_rounds_used']==2
    assert [entry['used'] for entry in result['round_ledger']]==[1,1]
    assert not result['failures']


def test_terminal_clock_fault_clears_returned_certificate_without_overwriting_artifact(pipeline_cases,monkeypatch,tmp_path):
    source,full,_=pipeline_cases;clock=Clock(101.)
    monkeypatch.setattr(rc,'_full_lower',lambda *args:(10.,[{'scope':'full_unrestricted_mip','lower':10.}]))
    path=tmp_path/'already-written-result.json';written=[]
    class FaultStorage(Storage):
        def materialize(self,result,*,schedule,clock):
            endpoint=clock()
            raw=json.dumps(result,sort_keys=True).encode()
            path.write_bytes(raw);written.append(raw)
            self.clock.now=float('nan')
            # An injected sink can swallow an exception; the coordinator's sticky state still governs.
            try:clock()
            except ValueError:pass
            return {'finished_monotonic':endpoint,'completion_monotonic':endpoint,'censored':False}
    store=FaultStorage(clock)
    outcome=run60(source,full,clock,store,
        planner=lambda *args,**kw:{'plan':raw_plan(),'rounds':[{}]})
    assert json.loads(written[0])['status']=='certified'
    assert path.read_bytes()==written[0]
    assert outcome['censored'] and outcome['result']['status']=='clock_failed'
    assert outcome['result']['global_lower_bound'] is None and not outcome['result']['bound_provenance']
    assert outcome['result']['fallback']==store.saved[0] and outcome['result']['clock_failure']
