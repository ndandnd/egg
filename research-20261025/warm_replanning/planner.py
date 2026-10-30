"""Fixed-fleet warm integrated-cost replanning with an external physical fallback."""
from copy import deepcopy
from fractions import Fraction
import math
import threading
import time

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr

POLICY = 'warm-fixed-fleet-integrated-cost-external-retention-v1'
_NATIVE_LOCK = threading.Lock()


def replan(case, a, b, *, fallback_plan, retained_ids=None, seed, fleet_count,
           native_deadline, admission_deadline, budget, use_native_start=True,
           fixed_route=False, completion=True, record=None, clock=time.monotonic):
    """Return a full-case physical witness, never a new unrestricted certificate.

    Caller retains/persists the common fallback before scoring and owns the
    inclusive clock/durable endpoint. This function independently validates it
    again. A rejected native hint or failed search never erases that fallback.
    No model/resource/controller hook is installed except the finally-restored
    count-only native-call wrapper; native budgets/deadlines pass unchanged.
    """
    a, b = tuple(a), tuple(b)
    nr.validate_case(case)
    nr._check_market(case, a, b)
    if (type(fleet_count) is not int or not 1 <= fleet_count <= case.max_vehicles
            or len(fallback_plan.get('vehicles', [])) != fleet_count):
        raise ValueError('Common fallback and required fixed active fleet differ')
    if (not nr._finite(native_deadline) or not nr._finite(admission_deadline)
            or native_deadline > admission_deadline):
        raise ValueError('Require ordered absolute native/admission deadlines')
    market = nh.Market('warm-target', a, b)
    last_clock = None
    def now():
        nonlocal last_clock
        at = clock()
        if not nr._finite(at) or last_clock is not None and at < last_clock:
            raise ValueError('Invalid or decreasing planner clock')
        last_clock = at
        return at
    def before(deadline):
        if now() >= deadline:
            raise TimeoutError('Warm planner absolute deadline exhausted')
    before(admission_deadline)
    fallback_replay = nr.replay_native(case, fallback_plan)
    if fallback_replay.get('replay_ok') is not True:
        raise ValueError('Common full-case fallback is not physically valid')
    fallback_bill = Fraction(fallback_replay['ops_cost'])+nh.supply(market, fallback_replay['load'])
    common = deepcopy(fallback_plan)
    common_replay = deepcopy(fallback_replay)
    before(admission_deadline)
    common_ids = {mid for vehicle in common['vehicles'] for mid in vehicle['movements']}
    original_ids = {movement.id for movement in case.movements}
    allowed = original_ids if retained_ids is None else set(retained_ids)
    best = {'plan': common, 'replay': common_replay, 'bill': fallback_bill,
            'source': 'fallback', 'admitted': now()}
    rounds, calls, starts, failures = [], [], [], []
    sink_failure = None
    pool_hint, pool_hint_bill, pool_hint_source = None, None, None
    if common_ids <= allowed:
        pool_hint, pool_hint_bill, pool_hint_source = common, fallback_bill, 'common_fallback'
    original_native, installed, locked = None, False, False
    current_round, call_role = None, None
    def diagnostic(stage, exc):
        return {'stage': stage, 'error_type': type(exc).__name__, 'error': str(exc)}
    def emit(event):
        nonlocal sink_failure
        if sink_failure is not None:
            raise RuntimeError('Diagnostic sink previously failed; no further dispatch')
        if record is not None:
            try:
                record(event)
            except Exception as exc:
                sink_failure = diagnostic('record', exc)
                raise
    def counted_native(built, inner_budget, deadline):
        entry = {'index': len(calls)+1, 'round': current_round, 'role': call_role,
            'fixed_topology': bool(built['x']) and all(v.lb == v.ub for v in built['x']),
            'deadline': deadline, 'phase_seconds': inner_budget.phase_seconds, 'dispatched': False}
        calls.append(entry)
        at, cpu = now(), time.process_time()
        entry['entered_monotonic'] = at
        try:
            if threading.get_ident() != owner_thread or len(calls) > 12:
                raise RuntimeError('Unexpected native thread or more than12 call attempts')
            if deadline > native_deadline or inner_budget.threads != 1 or sink_failure is not None:
                raise RuntimeError('Native deadline/thread/sink contract differs')
            before(native_deadline)
            entry['dispatched'] = True
            stats = original_native(built, inner_budget, deadline)
            entry['stats'] = deepcopy(stats)
            return stats
        except Exception as exc:
            entry['failure'] = diagnostic('native_call', exc)
            raise
        finally:
            entry['returned_monotonic'] = now()
            entry['wall_s'] = entry['returned_monotonic']-at
            entry['cpu_s'] = time.process_time()-cpu
    def admit(plan, source):
        nonlocal best, pool_hint, pool_hint_bill, pool_hint_source
        before(admission_deadline)
        replay = nr.replay_native(case, plan)
        ids = {mid for vehicle in plan['vehicles'] for mid in vehicle['movements']}
        if (replay.get('replay_ok') is not True or len(plan['vehicles']) != fleet_count
                or not ids <= allowed or fixed_route and ids != common_ids):
            raise ValueError('Candidate violates original replay/pool/fixed-fleet/topology contract')
        bill = Fraction(replay['ops_cost'])+nh.supply(market, replay['load'])
        copied_plan, copied_replay = deepcopy(plan), deepcopy(replay)
        before(admission_deadline)
        admitted = now()
        # Retain BEFORE any subsequent diagnostic or bound processing.
        if bill < best['bill']:
            best = {'plan': copied_plan, 'replay': copied_replay, 'bill': bill,
                    'source': source, 'admitted': admitted}
        if pool_hint_bill is None or bill < pool_hint_bill:
            pool_hint, pool_hint_bill, pool_hint_source = copied_plan, bill, source
        return ({'source': source, 'true_bill_exact': str(bill), 'admitted_monotonic': admitted,
                 'selected_as_best': best['source'] == source}, tuple(replay['load']))
    initial_tangents = []
    for aa, bb, load in zip(a, b, common_replay['load']):
        slope, intercept = float(aa)+float(bb)*load, -.5*float(bb)*load*load
        if not all(math.isfinite(value) for value in (slope, intercept)):
            raise ValueError('Nonfinite common-fallback initial tangent')
        initial_tangents.append([(float(aa), 0.), (slope, intercept)])
    try:
        nr._check_budget(budget)
        if (budget.threads != 1 or type(seed) is not int or seed < 0
                or not 1 <= budget.max_rounds <= 4 or not allowed <= original_ids
                or fixed_route and not common_ids <= allowed):
            raise ValueError('One-thread/seed/four-round/original-pool contract differs')
        if threading.active_count() != 1 or not _NATIVE_LOCK.acquire(blocking=False):
            raise RuntimeError('Warm native counting scope requires serialized single-thread use')
        locked, owner_thread = True, threading.get_ident()
        original_native = pf._optimize_once
        if original_native is not nr._optimize_once:
            raise RuntimeError('Unexpected preinstalled native hook; none is bypassed')
        pf._optimize_once, installed = counted_native, True
        tangents = deepcopy(initial_tangents)
        for index in range(budget.max_rounds):
            if now() >= native_deadline:
                break
            current_round = index
            row = {'round': index, 'conditional_fleet_count': fleet_count}
            rounds.append(row)
            try:
                before(native_deadline)
                built = pf.build_feasible_model(case, budget.backend)
                before(native_deadline)
                model = built['model']
                model.seed = seed
                if model.seed != seed:
                    raise ValueError('Native seed readback differs')
                row['native_seed_readback'] = model.seed
                for movement, var in zip(case.movements, built['x']):
                    if fixed_route:
                        var.lb = var.ub = int(movement.id in common_ids)
                    elif movement.id not in allowed:
                        var.ub = 0
                import mip
                model += mip.xsum(var for movement, var in zip(case.movements, built['x'])
                    if movement.kind == 'pullout') == fleet_count
                row['original_physical_rows'] = built['constraint_count_before_objective']
                snapshot = deepcopy(tangents)
                pf.attach_objective(built, 'tangents', snapshot)
                before(native_deadline)
                if use_native_start and pool_hint is not None:
                    report = {'round': index, 'source': pool_hint_source, 'status': 'not_submitted'}
                    starts.append(report)
                    try:
                        checked = pf._checked_pricing_start(case, pool_hint)
                        if not checked <= allowed:
                            raise ValueError('Native hint includes excluded pool modes')
                        before(native_deadline)
                        report.update(pf._attach_pricing_start(case, built, checked),
                            status='submitted', solver_start_status='unknown')
                    except Exception as exc:
                        report.update(status='rejected', failure=diagnostic('start_attach', exc))
                        raise
                else:
                    starts.append({'round': index, 'status': 'not_submitted',
                        'reason': 'disabled' if not use_native_start else 'no pool-representable admitted hint'})
                before(native_deadline)
                call_role = 'fixed_route_primary' if fixed_route else 'search'
                stats = pf._optimize_once(built, budget, native_deadline)
                row['native'] = deepcopy(stats)
                if stats['status'] not in ('OPTIMAL', 'FEASIBLE') or not nr._finite(stats.get('incumbent'), -math.inf):
                    row['search_status'] = 'no_admissible_native_incumbent'
                    break
                call_role = 'candidate_completion'
                candidate, admission_stats = pf._candidate(case, built, budget, native_deadline,
                    stats, completion, emit, index, ('tangents', (a, b, snapshot)))
                row['candidate_native'] = deepcopy(admission_stats)
                row['candidate_failures'] = deepcopy(candidate.get('candidate_failures', []))
                row['admission'], loads = admit(candidate, 'round'+str(index))
                # A later sink failure cannot erase the admission above.
                emit({'event': 'warm_candidate_admitted', 'round': index, **row['admission']})
                if sink_failure is not None:
                    raise RuntimeError('Diagnostic sink failed')
                for cuts, aa, bb, load in zip(tangents, a, b, loads):
                    slope, intercept = float(aa)+float(bb)*load, -.5*float(bb)*load*load
                    if not all(math.isfinite(value) for value in (slope, intercept)):
                        raise ValueError('Nonfinite target-market tangent')
                    cuts.append((slope, intercept))
            except Exception as exc:
                row['failure'] = diagnostic('round'+str(index), exc)
                failures.append(row['failure'])
                break
    except Exception as exc:
        failures.append(diagnostic('planner_setup', exc))
    finally:
        if installed:
            if pf._optimize_once is not counted_native:
                failures.append({'stage': 'native_restore', 'error': 'Unexpected hook mutation'})
            pf._optimize_once = original_native
        if locked:
            _NATIVE_LOCK.release()
    if sink_failure is not None:
        failures.append(sink_failure)
    returned = now()
    return {'policy': POLICY, 'status': 'improved' if best['bill'] < fallback_bill else 'fallback_only',
        'plan': best['plan'], 'replay': best['replay'], 'true_bill_exact': str(best['bill']),
        'true_bill': float(best['bill']), 'selected_source': best['source'], 'used_fallback': best['source'] == 'fallback',
        'fallback_bill_exact': str(fallback_bill), 'fallback_in_search_space': common_ids <= allowed,
        'conditional_fleet_count': fleet_count, 'fixed_route': fixed_route,
        'completion_enabled': completion, 'initial_tangent_points': [0., list(common_replay['load'])],
        'initial_tangents': initial_tangents,
        'native_deadline': native_deadline, 'admission_deadline': admission_deadline,
        'admitted_monotonic': best['admitted'], 'returned_monotonic': returned,
        'rounds': rounds, 'native_calls': calls, 'native_call_attempts': len(calls),
        'native_calls_dispatched': sum(entry['dispatched'] for entry in calls),
        'start_reports': starts, 'failures': failures,
        'global_lower_bound': None, 'certificate_claim': False,
        'bound_scope': 'raw native fixed-fleet and arm-restricted/fixed-topology bounds only',
        'availability': 'unchanged common fallback union arm-search candidates; fallback may be outside pool',
        'native_start_meaning': 'binary hint submission is distinct from solver acceptance and retained physical fallback'}
