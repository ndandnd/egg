"""Prospective eight-trip grid-information physics; inert on import.

Local new-seed recipe derived from egglab.physical_learning_cases, with no
historical registration changes. Native solves use the existing exact-N MIQP
helper by reference. The owner freezes source/case provenance at paid runtime.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import math
from pathlib import Path
import resource
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MIQP_SOURCE = ROOT/'research-20261026/economic_recourse_pilot/miqp_control.py'
QP_SOURCE = ROOT/'research-20261025/warm_replication/qp_control.py'
GENERATOR = 'grid-information-eight-trip-new-groups-v1'
TRAIN_SEEDS = tuple(range(63001, 63013))
VALIDATION_SEEDS = tuple(range(63101, 63105))
TEST_SEEDS = tuple(range(63201, 63209))
SEEDS = TRAIN_SEEDS + VALIDATION_SEEDS + TEST_SEEDS
N_TRIPS = 8
FLEET_N = 4
MARKET_EDGES = tuple(range(0, 1801, 60))
SPEED_KMH = 36.0
CONSUMPTION_KWH_PER_KM = 1.45
IDLE_KW = 1.2
DEADHEAD_MINUTES = {('D', 'A'): 4, ('A', 'D'): 4,
                    ('D', 'B'): 6, ('B', 'D'): 6,
                    ('A', 'B'): 8, ('B', 'A'): 8}
NATIVE_WALL_S = 4.0
ADMISSION_RESERVE_S = 0.2
_HELPERS = {}


def split_of(seed):
    if type(seed) is not int:
        raise ValueError('An assigned integer construction seed is required')
    if seed in TRAIN_SEEDS:
        return 'train'
    if seed in VALIDATION_SEEDS:
        return 'validation'
    if seed in TEST_SEEDS:
        return 'test'
    raise ValueError('Unassigned grid-information group; no historical cohort reuse')


def _draw(seed, duty, field, count):
    token = f'{GENERATOR}|{seed}|{duty}|{field}'.encode('utf-8')
    return int.from_bytes(hashlib.sha256(token).digest()[:8], 'big') % count


def _drive_energy(minutes):
    return minutes*SPEED_KMH/60*CONSUMPTION_KWH_PER_KM


def _travel(origin, destination):
    minutes = 0 if origin == destination else DEADHEAD_MINUTES[origin, destination]
    return minutes, _drive_energy(minutes)


def make_case(seed):
    """Construct one fresh declared graph only when called by the paid owner."""
    split_of(seed)
    from egglab import native_recharge as nr
    trips = []
    for duty in range(FLEET_N):
        start = 360 + 30*duty + _draw(seed, duty, 'offset', 9)
        first = 20 + _draw(seed, duty, 'first_duration', 12)
        wait = 6 + _draw(seed, duty, 'intertrip_wait', 20)
        second = 20 + _draw(seed, duty, 'second_duration', 12)
        trips.extend((
            nr.Trip(f'T{2*duty+1:02d}', start, start+first, 'A', 'B', _drive_energy(first)),
            nr.Trip(f'T{2*duty+2:02d}', start+first+wait, start+first+wait+second,
                    'B', 'A', _drive_energy(second))))
    movements = []
    for trip in trips:
        out, oe = _travel('D', trip.start_place)
        back, be = _travel(trip.end_place, 'D')
        movements.extend((
            nr.Movement(f'out_{trip.id}', 'pullout', None, trip.id,
                (nr.Leg('D', trip.start_place, trip.start_min-out, trip.start_min, oe),)),
            nr.Movement(f'in_{trip.id}', 'pullin', trip.id, None,
                (nr.Leg(trip.end_place, 'D', trip.end_min, trip.end_min+back, be),))))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            travel, energy = _travel(before.end_place, after.start_place)
            arrival = before.end_min+travel
            if arrival <= after.start_min:
                legs = [nr.Leg(before.end_place, after.start_place, before.end_min, arrival, energy)]
                if arrival < after.start_min:
                    legs.append(nr.Leg(after.start_place, after.start_place, arrival,
                        after.start_min, IDLE_KW*(after.start_min-arrival)/60))
                movements.append(nr.Movement(f'direct_{before.id}_{after.id}',
                    'direct', before.id, after.id, tuple(legs)))
            inbound, ie = _travel(before.end_place, 'D')
            outbound, oe = _travel('D', after.start_place)
            dwell_start, dwell_end = before.end_min+inbound, after.start_min-outbound
            if dwell_end-dwell_start >= 15:
                movements.append(nr.Movement(f'depot_{before.id}_{after.id}', 'depot', before.id, after.id,
                    (nr.Leg(before.end_place, 'D', before.end_min, dwell_start, ie),
                     nr.Leg('D', after.start_place, dwell_end, after.start_min, oe)), 1))
    case = nr.NativeCase(name=f'grid_information_v1_s{seed}_n08_control80',
        trips=tuple(trips),movements=tuple(movements),resources=(nr.Resource(0,1800,90.,90.,1),),
        market_edges_min=MARKET_EDGES,depot='D',max_vehicles=FLEET_N,
        battery_kwh=100.,reserve_kwh=20.,terminal_open_min=1080,recharge_deadline_min=1800,
        vehicle_cost=100.,deadhead_cost_per_min=0.,efficiency=.9)
    nr.validate_case(case)
    return case


def make_witness(case):
    """Four paired duties with serial terminal refill; always independently replay."""
    from egglab import native_recharge as nr
    nr.validate_case(case)
    if (len(case.trips)!=N_TRIPS or case.max_vehicles!=FLEET_N or case.market_edges_min!=MARKET_EDGES
            or case.battery_kwh!=100. or case.reserve_kwh!=20. or case.efficiency!=.9
            or case.terminal_open_min!=1080 or case.recharge_deadline_min!=1800
            or len(case.resources)!=1 or case.resources[0]!=nr.Resource(0,1800,90.,90.,1)
            or case.vehicle_cost!=100. or case.deadhead_cost_per_min!=0.):
        raise ValueError('Witness requires the frozen eight-trip/four-fleet physical recipe')
    trips = {trip.id:trip for trip in case.trips}
    movements = {movement.id:movement for movement in case.movements}
    vehicles, charges = [], []
    cursor = float(case.terminal_open_min)
    for vehicle in range(FLEET_N):
        first, second = f'T{2*vehicle+1:02d}', f'T{2*vehicle+2:02d}'
        ids = [f'out_{first}', f'direct_{first}_{second}', f'in_{second}']
        energy = sum(trips[tid].energy_kwh for tid in (first,second))+sum(
            leg.energy_kwh for mid in ids for leg in movements[mid].legs)
        if case.battery_kwh-energy < case.reserve_kwh:
            raise ValueError('Paired duty breaches the fixed operating span')
        release = movements[ids[-1]].legs[-1].arrive_min
        start = max(cursor,float(release),float(case.terminal_open_min))
        grid = energy/case.efficiency
        end = start+grid*60/case.resources[0].grid_kw
        if end > case.recharge_deadline_min:
            raise ValueError('Serial refill misses the fixed deadline')
        vehicles.append(dict(vehicle=vehicle,trips=[first,second],movements=ids))
        charges.append(dict(vehicle=vehicle,movement=ids[-1],connector=0,
            start_min=start,end_min=end,grid_kwh=grid))
        cursor = end
    loads = [0.]*30
    for charge in charges:
        rate = charge['grid_kwh']*60/(charge['end_min']-charge['start_min'])
        for period,(left,right) in enumerate(zip(case.market_edges_min,case.market_edges_min[1:])):
            overlap = max(0.,min(charge['end_min'],right)-max(charge['start_min'],left))
            loads[period] += rate*overlap/60
    plan = dict(schema=nr.SCHEMA,case_identity=case.identity(),vehicles=vehicles,
        charges=charges,load=loads,ops_cost=FLEET_N*case.vehicle_cost)
    replay = nr.replay_native(case,plan)
    if replay.get('replay_ok') is not True or len(plan['vehicles'])!=FLEET_N:
        raise ValueError('Constructed fixed-fleet witness failed physical replay')
    return plan


def _helper(fixed):
    name = 'fixed_qp' if fixed else 'joint_miqp'
    path = QP_SOURCE if fixed else MIQP_SOURCE
    if name not in _HELPERS:
        spec = importlib.util.spec_from_file_location('grid_information_existing_'+name,path)
        if spec is None or spec.loader is None:
            raise ImportError('Existing physical optimization source unavailable')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if Path(module.__file__).resolve()!=path:
            raise ImportError('Existing physical optimization source origin differs')
        _HELPERS[name] = module
    return _HELPERS[name]


def _finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def _solve(case,a,b,witness,deadline,*,fixed):
    """Shared admission wrapper for one joint MIQP or fixed-topology QP.

    `a,b` already describe ops+a*L+.5*b*L². The caller converts any base-load
    market coefficients first. The deadline is absolute monotonic admission.
    Four seconds cap the requested native region including setup; an actual
    native overrun is reported and disqualifies strict delivery. Outer process
    interruption remains the owner's responsibility.
    """
    started = time.monotonic()
    events = []
    result = dict(strict_method_success=False,status='unavailable',admitted_plan=None,
        load=None,ops=None,value=None,value_exact=None,bound=None,
        bound_scope='Raw numerical original-matrix fixed-topology QP only' if fixed else
            'Raw numerical original-matrix exact-N4 MIQP only',native_status=None,
        optimization_scope='fixed_witness_topology' if fixed else 'joint_free_paths_exact_N4',
        certificate_claim=False,native_status_optimal=False,retained_endpoint_native_optimal=False,
        native_calls=0,native_wall_s=None,wall_s=None,failures=[],events=events,
        retained_witness=deepcopy(witness),witness_replay=None,witness_value=None,
        used_fallback=True,endpoint_source='unavailable',helper_result=None)

    def check():
        if not _finite(deadline) or time.monotonic()>=deadline:
            raise TimeoutError('Joint admission deadline exhausted')
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if threading.active_count()!=1 or peak>5*1024**3:
            raise RuntimeError('Joint physical control requires one Python thread and observed RSS at most5GiB')

    def record(event):
        check(); events.append(deepcopy(event)); check()

    try:
        check()
        from egglab import native_recharge as nr
        if len(case.trips)!=N_TRIPS or case.max_vehicles!=FLEET_N or len(witness.get('vehicles',[]))!=FLEET_N:
            raise ValueError('Joint solve requires eight services and exact fleet four')
        a,b = tuple(a),tuple(b)
        nr._check_market(case,a,b)
        fallback = nr.replay_native(case,witness)
        if fallback.get('replay_ok') is not True:
            raise ValueError('Common witness failed independent physical replay')
        fallback_value = Fraction(fallback['ops_cost'])+sum((Fraction(aa)*Fraction(load)+
            Fraction(bb)*Fraction(load)**2/2 for aa,bb,load in zip(a,b,fallback['load'])),Fraction(0))
        result.update(witness_replay=deepcopy(fallback),witness_value=float(fallback_value))
        check()
        native_deadline = min(started+NATIVE_WALL_S,deadline-ADMISSION_RESERVE_S)
        if native_deadline<=time.monotonic():
            raise TimeoutError('No funded native interval before admission reserve')
        helper = _helper(fixed)
        arguments = (case,a,b,deepcopy(witness),17,native_deadline,deadline,check,record)
        raw = helper.solve(*arguments) if fixed else helper.solve(*arguments,fleet_N=FLEET_N)
        result['helper_result'] = raw
        check()
        stats = raw.get('stats') or {}
        wall = stats.get('wall_s')
        result.update(native_calls=raw.get('native_calls',0),native_wall_s=wall,
            native_status=stats.get('Status'),
            native_status_optimal=stats.get('native_optimal') is True,
            bound=stats.get('native_lower_bound') if _finite(stats.get('native_lower_bound')) else None,
            used_fallback=raw.get('used_fallback',True),endpoint_source=raw.get('selected_source','unavailable'))
        result['failures'].extend(deepcopy(raw.get('failures',[])))
        if raw.get('native_calls',0)>1:
            raise ValueError('Existing helper exceeded the one-optimize policy')
        if raw.get('plan') is not None:
            admitted = nr.replay_native(case,raw['plan'])
            if admitted.get('replay_ok') is not True or len(raw['plan']['vehicles'])!=FLEET_N:
                raise ValueError('Returned endpoint failed independent exact-N physical replay')
            if fixed and {mid for v in raw['plan']['vehicles'] for mid in v['movements']}!={
                    mid for v in witness['vehicles'] for mid in v['movements']}:
                raise ValueError('Fixed diagnostic changed the witness topology')
            value = Fraction(admitted['ops_cost'])+sum((Fraction(aa)*Fraction(load)+
                Fraction(bb)*Fraction(load)**2/2 for aa,bb,load in zip(a,b,admitted['load'])),Fraction(0))
            if not _finite(raw.get('true_bill')) or abs(float(value)-raw['true_bill'])>nr.OBJECTIVE_TOL:
                raise ValueError('Returned endpoint and continuous nonlinear objective differ')
            check()
            result.update(admitted_plan=deepcopy(raw['plan']),load=list(admitted['load']),
                ops=admitted['ops_cost'],value=float(value),value_exact=str(value))
        success_key = 'qp_success' if fixed else 'strict_method_success'
        candidate_key = 'qp_candidate_admitted' if fixed else 'miqp_candidate_admitted'
        strict = bool(raw.get(success_key) is True and raw.get(candidate_key) is True
            and raw.get('native_calls')==1 and not raw.get('fatal_contract') and not raw.get('config_failure')
            and not result['failures'] and _finite(wall) and 0<=wall<=NATIVE_WALL_S
            and stats.get('native_overrun_s',0)==0 and result['admitted_plan'] is not None)
        check()
        result.update(strict_method_success=strict,status=raw.get('status') if strict else 'unqualified_endpoint_or_witness',
            retained_endpoint_native_optimal=bool(strict and stats.get('native_optimal') is True
                and raw.get('selected_source')==('direct_qp' if fixed else 'direct_miqp')))
    except Exception as exc:
        result['failures'].append(dict(stage='fixed_wrapper' if fixed else 'joint_wrapper',type=type(exc).__name__,message=str(exc)))
        result['strict_method_success']=False; result['retained_endpoint_native_optimal']=False
        result['status']='unqualified_endpoint_or_witness'
    finally:
        result['wall_s']=time.monotonic()-started
    return result


def joint_solve(case,a,b,witness,deadline):
    """One free-path exact-N4 continuous-charging MIQP; same admitted schema as fixed_solve."""
    return _solve(case,a,b,witness,deadline,fixed=False)


def fixed_solve(case,a,b,witness,deadline):
    """One continuous QP on the witness topology, with native OPTIMAL required for strict delivery.

    This matched diagnostic measures charging-only response. Its lower bound
    and optimum scope are conditional on that fixed topology, never joint.
    """
    return _solve(case,a,b,witness,deadline,fixed=True)
