"""Bounded prefix/recovery coordination; no worker launch or backend import.

The optimizer hook is process-global: use only in the protocol's serialized worker.
All time limits derive from the supervisor's absolute monotonic anchor.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

from egglab import native_pathflow as pf
from egglab.recovery_lift import lift_plan

POLICY = 'recovery-shared-clock-coordinator-v1'
HANDOFF_POLICY = 'anytime-hard-admission-v1'
_HOOK_LOCK = threading.Lock()


@dataclass(frozen=True)
class Schedule:
    parent_monotonic: float
    deadline: float

    def __post_init__(self):
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in (self.parent_monotonic, self.deadline))
                or not math.isclose(self.deadline-self.parent_monotonic, 30., abs_tol=1e-9, rel_tol=0)):
            raise ValueError('Require supervisor deadline = parent_monotonic + 30 seconds')

    @property
    def prefix_integer_end(self):
        return self.parent_monotonic+12.

    @property
    def prefix_end(self):
        return self.parent_monotonic+15.

    @property
    def full_integer_end(self):
        return self.deadline-6.

    @property
    def planner_end(self):
        return self.deadline-3.

    @property
    def admission_reserve_s(self):
        """Compatibility alias: planned headroom, never a guaranteed reserve."""
        return self.planned_admission_headroom_s

    @property
    def planned_admission_headroom_s(self):
        return 2.

    @property
    def prefix_search_end(self):
        return self.prefix_integer_end-2.

    @property
    def full_search_end(self):
        return self.full_integer_end-2.

    @property
    def prefix_handoff_end(self):
        return self.prefix_end-self.planned_admission_headroom_s

    @property
    def full_handoff_end(self):
        return self.planner_end-self.planned_admission_headroom_s

    def as_dict(self):
        return {'parent_monotonic':self.parent_monotonic,'deadline':self.deadline,
                'prefix_integer_end':self.prefix_integer_end,'prefix_end':self.prefix_end,
                'full_integer_end':self.full_integer_end,'planner_end':self.planner_end,
                'prefix_search_end':self.prefix_search_end,'full_search_end':self.full_search_end,
                'prefix_handoff_end':self.prefix_handoff_end,'full_handoff_end':self.full_handoff_end,
                'handoff_policy':HANDOFF_POLICY,
                'planned_admission_headroom_s':self.planned_admission_headroom_s,
                'finalization_reserve_s':3.,'completion_limit_s':3.}


def admission_window(at, target, cutoff):
    """A planner target may be missed; admission must start before its hard limit."""
    if any(isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)
           for value in (at,target,cutoff)):
        raise ValueError('Invalid admission clock window')
    return {'planner_target':target,'target_overrun_s':max(0.,at-target),
            'admission_cutoff':cutoff,'admission_remaining_s':cutoff-at,
            'admission_open':at < cutoff}


@dataclass
class CompletionAllowance:
    """Three seconds cumulative native fixed-topology time, across both stages."""
    spent: float = 0.
    limit: float = 3.


@contextmanager
def native_limits(*, integer_end, planner_end, allowance, clock, allowed, events):
    """Clamp each existing native call, restoring the hook even after failures.

    Fixed routing is identified exactly as in the existing local campaign worker.
    The original native optimizer remains responsible for model setup/status.
    """
    if not _HOOK_LOCK.acquire(blocking=False):
        raise RuntimeError('Recovery optimizer hook requires one serialized worker')
    original = pf._optimize_once

    def optimize(built, budget, deadline):
        fixed = bool(built['x']) and all(v.lb == v.ub for v in built['x'])
        gate_open = allowed()
        now = clock()
        cutoff = min(deadline, planner_end,
                     now+max(0., allowance.limit-allowance.spent) if fixed else integer_end)
        if not gate_open or now >= cutoff:
            events.append({'event':'native_gate_closed','fixed_topology':fixed,
                           'at':now,'cutoff':cutoff})
            raise TimeoutError('No remaining native stage allowance')
        cap = min(budget.phase_seconds, cutoff-now)
        events.append({'event':'native_dispatch','fixed_topology':fixed,
                       'at':now,'deadline':cutoff,'seconds_cap':cap})
        before = clock()
        try:
            return original(built, replace(budget, phase_seconds=cap,
                                            wall_seconds=min(budget.wall_seconds, cutoff-now)), cutoff)
        finally:
            elapsed = max(0., clock()-before)
            if fixed:
                allowance.spent += elapsed
            events.append({'event':'native_return','fixed_topology':fixed,
                           'elapsed_s':elapsed,'completion_spent_s':allowance.spent})

    pf._optimize_once = optimize
    try:
        yield
    finally:
        pf._optimize_once = original
        _HOOK_LOCK.release()


def _bytes(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':'))+'\n').encode()


def _diagnostic(value):
    """Tag nonfinite diagnostic numbers without relaxing physical JSON admission."""
    if isinstance(value, float) and not math.isfinite(value):
        return {'nonfinite_float':('nan' if math.isnan(value) else
                                  'positive_infinity' if value > 0 else 'negative_infinity')}
    if isinstance(value, dict):
        return {key:_diagnostic(item) for key,item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_diagnostic(item) for item in value]
    return value


class DirectoryStorage:
    """Exclusive fsynced artifacts in a new attempt directory; never overwrite.

    The future supervisor owns attempt/native/ledger receipts and resume policy.
    An existing artifact raises, deliberately blocking unaudited incomplete resume.
    """
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _write(self, name, value):
        raw = _bytes(value)
        path = self.directory/name
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        descriptor = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}

    def save_fallback(self, witness):
        return self._write('fallback.json', witness)

    def materialize(self, result, *, schedule, clock):
        artifact = self._write('result.json', result)
        endpoint = clock()  # Result fsync, before completion serialization or cleanup.
        completion = {'policy':POLICY, 'parent_monotonic':schedule.parent_monotonic,
                      'deadline':schedule.deadline,'finished_monotonic':endpoint,
                      'elapsed_s':endpoint-schedule.parent_monotonic,
                      'result_sha256':artifact['sha256'],
                      'censored':endpoint > schedule.deadline}
        receipt = self._write('completion.json', completion)
        # Completion itself may be late, even when result materialization was timely.
        completion_end = clock()
        return {**completion, 'completion_monotonic':completion_end,
                'censored':completion['censored'] or completion_end > schedule.deadline,
                'result_artifact':artifact,'completion_artifact':receipt}


def _failure(stage, exc):
    return {'stage':stage,'error_type':type(exc).__name__,'error':str(exc)}


def _full_lower(result, full_case, a, b, clock, cutoff):
    """Re-admit original unrestricted MIP bounds; never use completion LP bounds."""
    if (result.get('case_identity') != full_case.identity()
            or result.get('formulation') != pf.FORMULATION
            or result.get('native_matrix') != pf.NATIVE_MATRIX
            or result.get('status') not in ('bounded', 'certified')):
        return None, []
    admitted = []
    for index, row in enumerate(result.get('rounds', [])):
        if clock() >= cutoff:
            break
        if 'lower' not in row or 'plan' not in row or 'stats' not in row:
            continue
        plan = deepcopy(row['plan'])
        # _candidate_score checks replay and the raw solver objective; the original
        # MIP stats supply lower_bound even when a fixed-route completion was used.
        stats = dict(row['stats'])
        if plan.get('completion_stats') is not None:
            stats['incumbent'] = plan['completion_stats']['incumbent']
        tangents = row['tangents']
        true = pf._candidate_score(full_case, plan, stats, ('tangents', (a, b, tangents)))
        load = plan['replay']['load']
        envelope = plan['ops_cost']+sum(max(slope*x+intercept for slope,intercept in rows)
                                       for x,rows in zip(load,tangents))
        lo, hi = pf.admit_bound(stats, true, envelope, allow_epigraph_slack=True)
        if clock() > cutoff:
            raise TimeoutError('Independent full bound admission exceeded planner cutoff')
        if row['lower'] != lo or row['upper'] != hi:
            raise ValueError('Full admitted round differs from unchanged objective guard')
        admitted.append({'round':index,'lower':lo,'scope':'full_unrestricted_mip',
                         'raw_lower_bound':row['stats']['lower_bound'],
                         'guard':pf.BOUND_GUARD})
    return (max(row['lower'] for row in admitted) if admitted else None), admitted


def coordinate(source_case, full_case, a, b, *, parent_monotonic, deadline, storage,
               budget=None, planner=None, clock=time.monotonic, allowed=lambda: True,
               physical_fallback=None):
    """Run at most one prefix and one full planner, retaining a durable witness.

    ``planner`` has the exact native_pathflow.solve_planner signature; injected
    implementations are for solver-free testing. ``allowed`` is a fail-closed
    supervisor/resource gate checked at planner entry and every native call.
    ``storage.save_fallback`` must durably persist before returning; materialize
    returns the completion endpoint/censorship receipt. No process is launched here.
    """
    schedule = Schedule(parent_monotonic, deadline)
    budget = pf.Budget() if budget is None else budget
    pf._check_budget(budget)
    planner = pf.solve_planner if planner is None else planner
    allowance = CompletionAllowance()
    events, failures = [], []
    fallback, selected, fallback_receipt = None, None, None
    full_result, prefix_result = None, None
    durable_failure = False
    dispatch_stopped = False
    lower, bound_provenance = None, []
    mode = 'not_started'

    def permitted():
        try:
            return allowed() is True
        except Exception as exc:
            failures.append(_failure('dispatch_gate', exc))
            return False

    def admit(source, plan, stage, cutoff, handoff=None):
        nonlocal fallback, selected, fallback_receipt, durable_failure, dispatch_stopped
        entered = clock()
        events.append({'event':'admission_lift_enter','stage':stage,'at':entered,
                       'anchor':parent_monotonic,'elapsed_s':entered-parent_monotonic,
                       'planner_handoff':handoff,'cutoff':cutoff,
                       **admission_window(entered,cutoff if handoff is None else handoff,cutoff)})
        if entered >= cutoff:
            dispatch_stopped = True
            raise TimeoutError('Physical admission entry reached hard stage cutoff')
        try:
            witness = lift_plan(source, full_case, deepcopy(plan), a=a, b=b)
        finally:
            exited = clock()
            events.append({'event':'admission_lift_exit','stage':stage,'at':exited,
                           'anchor':parent_monotonic,'elapsed_s':exited-parent_monotonic,
                           'planner_handoff':handoff,'cutoff':cutoff,
                           **admission_window(exited,cutoff if handoff is None else handoff,cutoff)})
        if clock() > cutoff:
            raise TimeoutError('Physical witness admission exceeded stage cutoff')
        if fallback is None:
            candidate_fallback, candidate_selected = deepcopy(witness), deepcopy(witness)
            durable_witness = deepcopy(witness)
            if clock() > cutoff:
                raise TimeoutError('Physical witness copy exceeded stage cutoff')
            try:
                artifact = storage.save_fallback(durable_witness)
            except Exception:
                durable_failure = True
                raise
            saved = clock()
            if saved > cutoff:
                events.append({'event':'rejected_durable_witness','stage':stage,
                               'at':saved,'cutoff':cutoff,'artifact':artifact,
                               'true_bill_exact':witness['true_bill_exact']})
                raise TimeoutError('Durable witness save exceeded stage cutoff')
            fallback, selected, fallback_receipt = candidate_fallback, candidate_selected, artifact
            events.append({'event':'durable_fallback_admitted','stage':stage,
                           'at':saved,'artifact':fallback_receipt,
                           'true_bill_exact':witness['true_bill_exact']})
        elif Fraction(witness['true_bill_exact']) < Fraction(selected['true_bill_exact']):
            candidate = deepcopy(witness)
            if clock() > cutoff:
                raise TimeoutError('Physical witness copy exceeded stage cutoff')
            selected = candidate
        return witness

    def solve(case, stage, integer_end, planner_end, start=None):
        nonlocal dispatch_stopped
        # Loading/build/setup costs before this call remain charged to the anchor.
        gate_open = permitted()
        now = clock()
        if now >= integer_end or not gate_open:
            events.append({'event':'planner_gate_closed','stage':stage,'at':now})
            return None
        inner = replace(budget, wall_seconds=min(budget.wall_seconds, planner_end-now),
                        phase_seconds=min(budget.phase_seconds, integer_end-now))
        events.append({'event':'planner_dispatch','stage':stage,'at':now,
                       'integer_end':integer_end,'planner_end':planner_end})
        with native_limits(integer_end=integer_end, planner_end=planner_end,
                           allowance=allowance, clock=clock, allowed=permitted, events=events):
            result = planner(case, a, b, inner, record=lambda row: events.append(
                {'stage':stage, **deepcopy(row)}), completion=True,
                start_plan=None if start is None else deepcopy(start['plan']),
                start_case=None if start is None else full_case, deadline=planner_end)
        returned = clock()
        cutoff = schedule.prefix_end if stage=='prefix' else schedule.planner_end
        events.append({'event':'planner_return','stage':stage,'at':returned,
                       'anchor':parent_monotonic,'elapsed_s':returned-parent_monotonic,
                       'planner_handoff':planner_end,
                       **admission_window(returned,planner_end,cutoff)})
        # Nonpreemptive candidate processing may miss its budget target. It
        # grants no new native call and still must leave an open admission gate.
        if returned >= cutoff:
            dispatch_stopped = True
            raise TimeoutError('Planner return reached hard admission cutoff')
        return result

    if physical_fallback is not None:
        try:
            admit(full_case, physical_fallback, 'initial_fallback', schedule.planner_end,
                  schedule.full_handoff_end)
        except Exception as exc:
            failures.append(_failure('initial_fallback', exc))
    if not durable_failure and physical_fallback is None:
        try:
            prefix_result = solve(source_case, 'prefix', schedule.prefix_search_end,
                                  schedule.prefix_handoff_end)
            if prefix_result is not None and prefix_result.get('plan') is not None:
                admit(source_case, prefix_result['plan'], 'prefix_lift', schedule.prefix_end,
                      schedule.prefix_handoff_end)
        except Exception as exc:
            failures.append(_failure('prefix', exc))
        finally:
            if (clock() > schedule.prefix_end and any(
                    row.get('event') == 'planner_dispatch' and row.get('stage') == 'prefix'
                    for row in events)):
                dispatch_stopped = True
                failures.append({'stage':'prefix_cutoff','error_type':'TimeoutError',
                                 'error':'Prefix physical/durable cutoff missed; stop full dispatch'})
    mode = 'warm_full' if fallback is not None else 'cold_full_no_prefix_witness'
    if not durable_failure and not dispatch_stopped:
        try:
            # A warm dispatch is impossible until save_fallback returned. Expired
            # lift/save work cannot reopen either absolute cutoff.
            full_result = solve(full_case, 'full', schedule.full_search_end,
                                schedule.full_handoff_end, fallback)
            if full_result is not None:
                if full_result.get('plan') is not None:
                    admit(full_case, full_result['plan'], 'full_candidate', schedule.planner_end,
                          schedule.full_handoff_end)
                lower, bound_provenance = _full_lower(full_result, full_case, a, b,
                                                     clock, schedule.planner_end)
        except Exception as exc:
            failures.append(_failure('full', exc))
    contradiction = bool(fallback is not None and full_result is not None and
                         full_result.get('status') in ('infeasible', 'model_replay_contradiction',
                                                      'bound_replay_contradiction'))
    if selected is not None and lower is not None and lower > selected['true_bill']+pf.BOUND_GUARD:
        contradiction = True
        failures.append({'stage':'bound','error_type':'ValueError',
                         'error':'Full lower bound contradicts retained physical bill'})
    if contradiction:
        lower, bound_provenance = None, []
    status = 'model_replay_contradiction' if contradiction else ('feasible' if selected else 'no_plan')
    if selected is not None and lower is not None:
        status = 'certified' if selected['true_bill']-lower <= budget.epsilon else 'bounded'
    if durable_failure:
        status = 'storage_failed'
    result = {'policy':POLICY,'status':status,'mode':mode,
              'schedule':schedule.as_dict(),
              'completion_spent_s':allowance.spent,'global_lower_bound':lower,
              'dispatch_stopped':dispatch_stopped,
              'bound_provenance':bound_provenance,'fallback':fallback,
              'fallback_artifact':fallback_receipt,'selected':selected,
              'restricted_prefix_lower':(prefix_result.get('lower') if prefix_result is not None
                  and isinstance(prefix_result.get('lower'), (int, float))
                  and math.isfinite(prefix_result['lower']) else None),
              'restricted_prefix_lower_diagnostic':_diagnostic(
                  None if prefix_result is None else prefix_result.get('lower')),
              'prefix_status':None if prefix_result is None else prefix_result.get('status'),
              'full_status':None if full_result is None else full_result.get('status'),
              'full_dispatched':any(row.get('event') == 'planner_dispatch'
                  and row.get('stage') == 'full' for row in events),
              'events':_diagnostic(events),'failures':failures,
              'pre_materialization_elapsed_s':clock()-parent_monotonic}
    try:
        receipt = storage.materialize(deepcopy(result), schedule=schedule, clock=clock)
    except Exception as exc:
        return {'result':result,'completion':None,'censored':True,
                'materialization_failure':_failure('materialize', exc)}
    return {'result':result,'completion':receipt,'censored':receipt['censored']}
