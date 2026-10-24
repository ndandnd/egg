"""Candidate CF1 provider; raw proposals require coordinator admission.

No durable fallback, native start or unrestricted bound is produced here. The
60-second comparison schedule and its actual native behavior remain unqualified.
"""
from copy import deepcopy
import math

from egglab import constructive_control as cf
from egglab import constructive_charging as ch
from egglab import native_recharge as nr
from egglab import recovery_coordinator as rc

POLICY = 'cf1-cumulative-construction-charging-provider-v1'


def _finite(value):
    return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)


def _repairable(completion):
    stages = completion.get('stages',[])
    return (completion.get('plan') is None and completion.get('status') == 'infeasible'
            and completion.get('reverse_repair_allowed') is True
            and not completion.get('failures') and bool(stages)
            and stages[0].get('stage') == 'feasibility'
            and stages[0].get('stats',{}).get('status') == 'INFEASIBLE'
            and stages[0].get('stats',{}).get('incumbent') is None)


def propose(case, a, b, *, schedule, allowance, budget, clock, allowed, events,
            constructor=None, completer=None, undoer=None):
    """Construct once, then complete/undo at most twice under one fixed window.

    ``allowance`` is the very same cumulative object used by later full search.
    Only the unchanged native_limits hook debits native fixed-call time; wall
    setup/replay/repair is additionally bounded by the fixed completion deadline.
    """
    constructor = cf.construct_routes if constructor is None else constructor
    completer = ch.complete_topology if completer is None else completer
    undoer = cf.undo_merges if undoer is None else undoer
    result = {'policy':POLICY,'status':'no_proposal','plan':None,'failures':[],
              'stages':[],'construction':None,'completion_deadline':None,
              'first_completion_anchor':None,'repairs':0,'global_lower_bound':None,
              'durable_fallback':False,'start_submitted':False,
              'native_qualification_established':False}
    last = None
    stage = 'validation'

    def check(cutoff, *, completed=False):
        nonlocal last
        at = clock()
        if not _finite(at) or last is not None and at < last:
            raise ValueError('Invalid/nonmonotonic proposal clock')
        last = at
        if allowed() is not True:
            raise TimeoutError('Proposal dispatch gate closed')
        if (at > cutoff if completed else at >= cutoff):
            raise TimeoutError('Proposal stage absolute deadline exhausted')
        return at

    def emit(event, cutoff, *, completed=False):
        check(cutoff,completed=completed)
        events.append({'provider_policy':POLICY,**deepcopy(event)})
        check(cutoff,completed=completed)

    try:
        construction_end,charging_end = schedule.construction_end,schedule.charging_stage_end
        if (not all(_finite(v) for v in (construction_end,charging_end,allowance.limit,allowance.spent))
                or construction_end >= charging_end or allowance.limit <= 0 or allowance.spent < 0):
            raise ValueError('Invalid schedule or cumulative completion allowance')
        check(construction_end)
        nr._check_market(case,a,b)
        nr._check_budget(budget)
        stage = 'construction'
        emit({'event':'cf1_construction_enter','deadline':construction_end},construction_end)
        ledger = constructor(case,deadline=construction_end,clock=clock)
        check(construction_end,completed=True)
        result['construction'] = deepcopy(ledger)
        result['stages'].append({'stage':'construction','result':deepcopy(ledger)})
        check(construction_end,completed=True)
        if ledger.get('status') != 'proposal' or not ledger.get('selected_ids'):
            return result
        stage = 'completion_window'
        first = check(charging_end)
        remaining = max(0.,allowance.limit-allowance.spent)
        completion_deadline = min(charging_end,first+remaining)
        result.update(first_completion_anchor=first,completion_deadline=completion_deadline,
                      completion_allowance_at_entry_s=remaining)
        check(completion_deadline)
        # One hook scope; every rebuild and undo shares one unchanged deadline.
        with rc.native_limits(integer_end=completion_deadline,planner_end=completion_deadline,
                              allowance=allowance,clock=clock,allowed=allowed,events=events):
            for attempt in range(3):
                stage = 'charging'+str(attempt)
                check(completion_deadline)
                emit({'event':'cf1_charging_enter','attempt':attempt,
                      'deadline':completion_deadline},completion_deadline)
                completed = completer(case,ledger['selected_ids'],a,b,budget,
                    deadline=completion_deadline,clock=clock,
                    record=lambda row:emit(row,completion_deadline))
                # Explicit provider policy: even an earlier helper witness cannot
                # rescue a helper that returns after this method's stage endpoint.
                check(completion_deadline,completed=True)
                result['stages'].append({'stage':stage,'result':deepcopy(completed)})
                check(completion_deadline,completed=True)
                result['failures'].extend(deepcopy(completed.get('failures',[])))
                if completed.get('plan') is not None:
                    candidate = deepcopy(completed['plan'])
                    candidate_replay = deepcopy(completed.get('replay'))
                    check(completion_deadline,completed=True)
                    emit({'event':'cf1_raw_proposal','attempt':attempt,
                          'deadline':completion_deadline},completion_deadline,completed=True)
                    result.update(status='proposal',plan=candidate,
                        true_bill_exact=completed.get('true_bill_exact'),
                        true_bill=completed.get('true_bill'),replay=candidate_replay)
                    # Coordinator must independently lift/replay/save within its
                    # own physical admission window before this is a fallback.
                    break
                if not _repairable(completed) or attempt == 2:
                    result['status'] = 'unresolved'
                    break
                if type(ledger.get('active_merge_count')) is not int or ledger['active_merge_count'] <= 0:
                    break
                stage = 'repair'+str(attempt+1)
                check(completion_deadline)
                repaired = undoer(case,ledger,1,deadline=completion_deadline,clock=clock)
                check(completion_deadline,completed=True)
                result['repairs'] += 1
                result['stages'].append({'stage':stage,'result':deepcopy(repaired)})
                check(completion_deadline,completed=True)
                if repaired.get('status') != 'proposal' or not repaired.get('selected_ids'):
                    break
                if (repaired.get('active_merge_count') != ledger['active_merge_count']-1
                        or type(ledger.get('undone_count')) is not int
                        or repaired.get('undone_count') != ledger['undone_count']+1):
                    raise ValueError('Repair did not undo exactly one cumulative merge')
                ledger = repaired
        check(completion_deadline,completed=True)
    except Exception as exc:
        result['plan'] = None
        result['status'] = 'unresolved' if isinstance(exc,TimeoutError) else 'failed'
        result['failures'].append({'stage':stage,'error_type':type(exc).__name__,'error':str(exc)})
    return result
