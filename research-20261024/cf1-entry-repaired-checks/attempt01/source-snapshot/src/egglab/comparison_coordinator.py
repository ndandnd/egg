"""Unqualified 60-second comparison composition; the qualified 30s path is unchanged.

No worker, backend, asset or case is launched/loaded here. Actual native start
processing requires separate attributable native evidence from a future runner.
"""
from copy import deepcopy
from dataclasses import dataclass, replace
from fractions import Fraction
import math
import time

from egglab import recovery_coordinator as rc

POLICY = 'comparison60-anytime-coordinator-v1'


@dataclass(frozen=True)
class Schedule60:
    parent_monotonic: float
    deadline: float

    def __post_init__(self):
        if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
                for v in (self.parent_monotonic,self.deadline)) or
                not math.isclose(self.deadline-self.parent_monotonic,60.,abs_tol=1e-9,rel_tol=0)):
            raise ValueError('Require supervisor deadline = parent_monotonic + 60 seconds')

    @property
    def anchor(self): return self.parent_monotonic
    @property
    def construction_end(self): return self.anchor+6.
    @property
    def charging_stage_end(self): return self.anchor+12.
    @property
    def prefix_integer_end(self): return self.anchor+24.
    @property
    def prefix_search_end(self): return self.anchor+20.
    @property
    def prefix_handoff_end(self): return self.anchor+26.
    @property
    def prefix_end(self): return self.anchor+30.
    @property
    def full_integer_end(self): return self.anchor+48.
    @property
    def full_search_end(self): return self.anchor+44.
    @property
    def full_handoff_end(self): return self.anchor+50.
    @property
    def planner_end(self): return self.anchor+54.
    @property
    def completion_limit_s(self): return 6.
    @property
    def planned_admission_headroom_s(self): return 4.
    @property
    def finalization_reserve_s(self): return 6.

    def as_dict(self):
        return {'policy':POLICY,**{name:getattr(self,name) for name in (
            'parent_monotonic','anchor','deadline','construction_end','charging_stage_end',
            'prefix_integer_end','prefix_search_end','prefix_handoff_end','prefix_end',
            'full_integer_end','full_search_end','full_handoff_end','planner_end',
            'completion_limit_s','planned_admission_headroom_s','finalization_reserve_s')}}


class RoundLimitClosed(RuntimeError):
    pass


class _Events(list):
    """Reserve MIP calls at native_limits' pre-optimizer append, without core edits."""
    def begin(self, stage, remaining):
        self.stage,self.remaining = stage,remaining
        self.starts,self.failed = set(),set()
        self.dispatches,self.malformed,self.blocked = 0,False,False

    def record(self, row):
        if row.get('event') in ('native_start','native_search_failed'):
            index = row.get('round')
            if type(index) is not int or index < 0:
                self.malformed = True
            else:
                observed = self.starts if row['event']=='native_start' else self.failed
                if index in observed:
                    self.malformed = True
                observed.add(index)
                attempts = self.starts | self.failed
                if attempts != set(range(max(attempts)+1)):
                    self.malformed = True
        self.append({'stage':self.stage,**deepcopy(row)})

    def append(self, row):
        if row.get('event')=='native_dispatch':
            fixed = row.get('fixed_topology')
            observed = self.starts | self.failed
            prospective = max(max(observed)+1 if observed else 0,
                              self.dispatches+int(fixed is False))
            if (self.malformed or type(fixed) is not bool or
                    prospective>self.remaining or fixed is False and self.stage=='cf1'):
                self.blocked = True
                super().append({'event':'mip_round_gate_closed','stage':self.stage,
                                'remaining':self.remaining,'unfixed_dispatches':self.dispatches,
                                'event_sequence':len(self)})
                raise RoundLimitClosed('No additional MIP dispatch allowed by shared round ledger')
            if fixed is False:
                self.dispatches += 1
        super().append({**row,'event_sequence':len(self)})

    def reconcile(self, result, *, raised=False):
        rounds = result.get('rounds') if isinstance(result,dict) else None
        valid = isinstance(rounds,list) and all(isinstance(row,dict) for row in rounds)
        observed = self.starts | self.failed
        contiguous = not observed or observed==set(range(max(observed)+1))
        used = max(len(self.starts),self.dispatches,len(rounds) if valid else 0,
                   max(observed)+1 if observed else 0)
        known = valid and not raised and not self.malformed and contiguous and not self.blocked
        return {'stage':self.stage,'native_start_count':len(self.starts),
                'unfixed_native_dispatch_count':self.dispatches,
                'result_round_count':len(rounds) if valid else None,
                'failed_round_count':len(self.failed),'used':used,
                'known':known and used<=self.remaining,'gate_blocked':self.blocked}


def _provider_audit(result):
    """Keep method audit without duplicating captured variables or raw plans."""
    if result is None:
        return None
    if not isinstance(result,dict):
        return {'malformed_result_type':type(result).__name__}
    audit = deepcopy({k:v for k,v in result.items() if k not in ('plan','replay','stages','events')})
    audit['stages'] = []
    for entry in result.get('stages',[]):
        if entry['stage']=='construction':  # Already retained once as audit.construction.
            continue
        payload = entry['result']
        audit['stages'].append({'stage':entry['stage'],'result':deepcopy(
            {k:v for k,v in payload.items() if k not in ('plan','replay','events')})})
    return audit


def _status(result):
    return result.get('status') if isinstance(result,dict) else None


def coordinate60(source_case, full_case, a, b, *, arm='recovery', parent_monotonic,
                 deadline, storage, budget=None, planner=None, proposal_provider=None,
                 clock=time.monotonic, allowed=lambda:True):
    """One acquisition (prefix or CF1), then at most one full planner invocation.

    Provider returns a raw plan only. This coordinator independently lifts and
    durably admits it before proposing any full-model binary start. Storage has
    the unchanged DirectoryStorage interface; all materialization is inside60s.
    """
    if arm not in ('recovery','cold','cf1') or arm=='recovery' and source_case is None:
        raise ValueError('Require recovery source case or cold/cf1 arm')
    schedule = Schedule60(parent_monotonic,deadline)
    raw_clock,last_clock,clock_failed,clock_failures = clock,None,False,[]

    def checked_clock():
        nonlocal last_clock,clock_failed
        if clock_failed:
            raise ValueError('Comparison clock previously failed')
        try:
            at = raw_clock()
            if (isinstance(at,bool) or not isinstance(at,(int,float)) or not math.isfinite(at)
                    or at<parent_monotonic or last_clock is not None and at<last_clock):
                raise ValueError('Invalid/nonmonotonic comparison clock')
        except Exception as exc:
            clock_failed = True
            error = exc if isinstance(exc,ValueError) else ValueError('Comparison clock read failed')
            if not clock_failures:
                clock_failures.append(rc._failure('clock',error))
            raise error
        last_clock = at
        return at

    clock = checked_clock
    clock()  # Reject invalid initial timestamps before any planner/provider work.
    budget = rc.pf.Budget(wall_seconds=60.,phase_seconds=44.,max_rounds=8) if budget is None else budget
    rc.pf._check_budget(budget)
    if budget.max_rounds>8:
        raise ValueError('Comparison allows at most eight total MIP rounds')
    planner = rc.pf.solve_planner if planner is None else planner
    allowance = rc.CompletionAllowance(limit=schedule.completion_limit_s)
    events,failures,round_ledger = _Events(),[],[]
    fallback = selected = artifact = prefix_result = provider_result = full_result = None
    storage_failed,dispatch_stopped,rounds_used = False,False,0
    lower,provenance = None,[]
    start_proposed = False
    acquisition_attempted = False

    def permitted():
        if clock_failed:
            return False
        try:
            return allowed() is True
        except Exception as exc:
            failures.append(rc._failure('dispatch_gate',exc))
            return False

    def timing(event, stage, at, target, cutoff):
        events.append({'event':event,'stage':stage,'at':at,'anchor':parent_monotonic,
                       'elapsed_s':at-parent_monotonic,**rc.admission_window(at,target,cutoff)})

    def admit(source, plan, stage, target, cutoff):
        nonlocal fallback,selected,artifact,storage_failed,dispatch_stopped
        entered = clock()
        timing('admission_lift_enter',stage,entered,target,cutoff)
        if entered>=cutoff:
            dispatch_stopped = True
            raise TimeoutError('Admission entry reached hard comparison cutoff')
        try:
            witness = rc.lift_plan(source,full_case,deepcopy(plan),a=a,b=b)
        finally:
            timing('admission_lift_exit',stage,clock(),target,cutoff)
        if clock()>cutoff:
            dispatch_stopped = True
            raise TimeoutError('Independent comparison admission exceeded hard cutoff')
        if fallback is None:
            first,chosen,durable = deepcopy(witness),deepcopy(witness),deepcopy(witness)
            if clock()>cutoff:
                dispatch_stopped = True
                raise TimeoutError('Comparison witness copy exceeded hard cutoff')
            try:
                saved_artifact = storage.save_fallback(durable)
            except Exception:
                storage_failed = True
                raise
            saved = clock()
            if saved>cutoff:
                dispatch_stopped = True
                events.append({'event':'rejected_durable_witness','stage':stage,
                               'at':saved,'cutoff':cutoff,'artifact':saved_artifact})
                raise TimeoutError('Comparison durable save exceeded hard cutoff')
            fallback,selected,artifact = first,chosen,saved_artifact
            events.append({'event':'durable_fallback_admitted','stage':stage,'at':saved,
                           'artifact':artifact,'true_bill_exact':witness['true_bill_exact']})
        elif Fraction(witness['true_bill_exact']) < Fraction(selected['true_bill_exact']):
            chosen = deepcopy(witness)
            if clock()>cutoff:
                dispatch_stopped = True
                raise TimeoutError('Comparison selected witness copy exceeded hard cutoff')
            selected = chosen

    def solve(case, stage, search_end, target, cutoff, start=None):
        nonlocal rounds_used,dispatch_stopped,start_proposed,acquisition_attempted
        remaining = budget.max_rounds-rounds_used
        now = clock()
        if now>=search_end or remaining<=0 or not permitted():
            events.append({'event':'planner_gate_closed','stage':stage,'at':now,
                           'remaining_mip_rounds':remaining})
            return None
        events.begin(stage,remaining)
        if stage=='prefix':
            acquisition_attempted = True
        inner = replace(budget,max_rounds=remaining,
                        phase_seconds=min(budget.phase_seconds,search_end-now),
                        wall_seconds=min(budget.wall_seconds,target-now))
        events.append({'event':'planner_dispatch','stage':stage,'at':now,'integer_end':search_end,
                       'planner_end':target,'remaining_mip_rounds':remaining})
        if start is not None:
            start_proposed = True
            events.append({'event':'full_start_proposed','stage':stage,'at':now,
                           'fallback_artifact':artifact,'native_processing':'unknown',
                           'requires_external_native_evidence':True})
        result = None
        raised = True
        try:
            with rc.native_limits(integer_end=search_end,planner_end=target,allowance=allowance,
                                  clock=clock,allowed=permitted,events=events):
                result = planner(case,a,b,inner,record=events.record,completion=True,
                    start_plan=None if start is None else deepcopy(start['plan']),
                    start_case=None if start is None else full_case,deadline=target)
            raised = False
        finally:
            accounting = events.reconcile(result,raised=raised)
            rounds_used += accounting['used']
            round_ledger.append(accounting)
            if not accounting['known']:
                dispatch_stopped = True
                failures.append({'stage':stage+'_round_accounting','error_type':'ValueError',
                                 'error':'Unknown/malformed/exceeded shared MIP round accounting'})
        returned = clock()
        timing('planner_return',stage,returned,target,cutoff)
        if returned>cutoff:
            dispatch_stopped = True
            raise TimeoutError('Planner return exceeded hard comparison admission cutoff')
        return result

    if arm=='recovery':
        try:
            prefix_result = solve(source_case,'prefix',schedule.prefix_search_end,
                                  schedule.prefix_handoff_end,schedule.prefix_end)
            if not clock_failed and prefix_result is not None and prefix_result.get('plan') is not None:
                admit(source_case,prefix_result['plan'],'prefix_lift',
                      schedule.prefix_handoff_end,schedule.prefix_end)
        except Exception as exc:
            failures.append(rc._failure('prefix',exc))
    elif arm=='cf1':
        try:
            if permitted() and clock()<schedule.prefix_end:
                acquisition_attempted = True
                if proposal_provider is None:
                    from egglab.constructive_proposal import propose
                    proposal_provider = propose
                events.begin('cf1',budget.max_rounds)
                provider_result = proposal_provider(full_case,a,b,schedule=schedule,
                    allowance=allowance,budget=budget,clock=clock,allowed=permitted,events=events)
                returned = clock()
                timing('provider_return','cf1',returned,schedule.charging_stage_end,schedule.prefix_end)
                failures.extend({'stage':'cf1_provider',**deepcopy(row)}
                                for row in provider_result.get('failures',[]))
                if returned>schedule.prefix_end:
                    dispatch_stopped = True
                    raise TimeoutError('CF1 provider return exceeded hard prefix admission cutoff')
                if not clock_failed and provider_result.get('plan') is not None:
                    completion_end = provider_result.get('completion_deadline')
                    if (isinstance(completion_end,bool) or not isinstance(completion_end,(int,float))
                            or not math.isfinite(completion_end)
                            or completion_end>schedule.charging_stage_end or returned>completion_end):
                        raise TimeoutError('CF1 raw proposal returned after its fixed charging window')
                    admit(full_case,provider_result['plan'],'cf1_lift',
                          schedule.charging_stage_end,schedule.prefix_end)
        except Exception as exc:
            failures.append(rc._failure('cf1',exc))
        finally:
            if (getattr(events,'stage',None)=='cf1' and
                    (events.blocked or events.malformed or events.dispatches)):
                dispatch_stopped = True
                failures.append({'stage':'cf1_round_accounting','error_type':'ValueError',
                                 'error':'CF1 provider attempted unqualified/unfixed native dispatch'})
    try:
        if not clock_failed and acquisition_attempted and clock()>schedule.prefix_end:
            if not dispatch_stopped:
                failures.append({'stage':'acquisition_cutoff','error_type':'TimeoutError',
                                 'error':'Acquisition work exceeded hard prefix admission cutoff'})
            dispatch_stopped = True
    except ValueError:
        pass  # checked_clock has permanently closed dispatch and retained its cause.
    mode = 'warm_full' if fallback is not None else 'cold_full'
    if not storage_failed and not dispatch_stopped and not clock_failed:
        try:
            full_result = solve(full_case,'full',schedule.full_search_end,
                                schedule.full_handoff_end,schedule.planner_end,fallback)
            if not clock_failed and full_result is not None:
                if full_result.get('plan') is not None:
                    admit(full_case,full_result['plan'],'full_candidate',
                          schedule.full_handoff_end,schedule.planner_end)
                lower,provenance = rc._full_lower(full_result,full_case,a,b,clock,schedule.planner_end)
        except Exception as exc:
            failures.append(rc._failure('full',exc))
    contradiction = bool(fallback is not None and _status(full_result) in
        ('infeasible','model_replay_contradiction','bound_replay_contradiction'))
    if selected is not None and lower is not None and lower>selected['true_bill']+rc.pf.BOUND_GUARD:
        contradiction = True
        failures.append({'stage':'bound','error_type':'ValueError','error':'Full bound contradicts retained witness'})
    if contradiction:
        lower,provenance = None,[]
    status = 'model_replay_contradiction' if contradiction else ('feasible' if selected else 'no_plan')
    if selected is not None and lower is not None:
        status = 'certified' if selected['true_bill']-lower<=budget.epsilon else 'bounded'
    if storage_failed:
        status = 'storage_failed'
    try:
        provider_audit = _provider_audit(provider_result)
    except Exception as exc:
        provider_audit = None
        failures.append(rc._failure('provider_audit',exc))
    try:
        pre_materialization_elapsed = clock()-parent_monotonic
    except ValueError:
        pre_materialization_elapsed = None
    if clock_failed:
        status,dispatch_stopped = 'clock_failed',True
        lower,provenance = None,[]
        failures.extend(deepcopy(clock_failures))
    result = {'policy':POLICY,'native_qualification_established':False,'arm':arm,'mode':mode,'status':status,
        'schedule':schedule.as_dict(),'completion_spent_s':allowance.spent,
        'mip_round_limit':budget.max_rounds,'mip_rounds_used':rounds_used,'round_ledger':round_ledger,
        'fallback':fallback,'selected':selected,'fallback_artifact':artifact,'global_lower_bound':lower,
        'bound_provenance':provenance,'dispatch_stopped':dispatch_stopped,
        'prefix_status':_status(prefix_result),'provider_status':_status(provider_result),
        'provider_audit':rc._diagnostic(provider_audit),'full_status':_status(full_result),
        'restricted_prefix_lower_diagnostic':rc._diagnostic(
            prefix_result.get('lower') if isinstance(prefix_result,dict) else None),
        'start_proposal':{'proposed':start_proposed,'native_processing':'unknown',
                          'requires_external_native_evidence':True,
                          'reason':'Native processing requires external attributable log evidence'},
        'full_dispatched':any(row.get('event')=='planner_dispatch' and row.get('stage')=='full' for row in events),
        'events':rc._diagnostic(events),'failures':failures,
        'clock_failure':rc._diagnostic(clock_failures),'pre_materialization_elapsed_s':pre_materialization_elapsed}

    def terminal_clock_diagnostic():
        if clock_failed:
            superseded = result['status']
            result.update(status='clock_failed',global_lower_bound=None,bound_provenance=[],
                          dispatch_stopped=True,clock_failure=rc._diagnostic(clock_failures),
                          terminal_clock_diagnostic={'superseded_status':superseded,
                              'reason':'Terminal clock fault supersedes the returned status',
                              'persisted_artifacts_unchanged':True})
            for cause in clock_failures:
                if cause not in result['failures']:
                    result['failures'].append(deepcopy(cause))

    receipt = None
    try:
        receipt = storage.materialize(deepcopy(result),schedule=schedule,clock=clock)
        clock()  # Storage cannot hide/swallow a failed final endpoint observation.
    except Exception as exc:
        terminal_clock_diagnostic()
        return {'result':result,'completion':receipt,'censored':True,
                'materialization_failure':rc._failure('materialize',exc)}
    terminal_clock_diagnostic()
    return {'result':result,'completion':receipt,'censored':receipt['censored'] or clock_failed}
