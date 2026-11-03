"""CF1 price-blind greedy topology proposal; no charging solve or feasibility proof.

All construction/undo work uses a caller-supplied absolute deadline. Optimistic
single-vehicle capacity ignores shared contention. A proposal still requires
fixed-topology charging, independent replay and exact billing before admission.
"""
from __future__ import annotations

from copy import deepcopy
import math
import time

from egglab import classical_controls as cc

POLICY = 'cf1-priceblind-greedy-topology-v1'


class _Deadline(Exception):
    pass


def _clock_check(deadline, clock):
    at = clock()
    if isinstance(at,bool) or not isinstance(at,(int,float)) or not math.isfinite(at):
        raise ValueError('Invalid construction clock')
    if at >= deadline:
        raise _Deadline('Absolute construction deadline reached')
    return at


def _deadline_value(deadline):
    if (isinstance(deadline,bool) or not isinstance(deadline,(int,float))
            or not math.isfinite(deadline)):
        raise ValueError('Require finite absolute construction deadline')


def _minutes(movement):
    return math.fsum(leg.arrive_min-leg.depart_min for leg in movement.legs)


def _window_capacity(case, movement, slices, check):
    """Optimistic grid kWh in a depot gap or verified terminal pullin window."""
    if movement.kind=='depot':
        lo = movement.legs[movement.depot_split-1].arrive_min
        hi = movement.legs[movement.depot_split].depart_min
    elif movement.kind=='pullin':
        lo = max(movement.legs[-1].arrive_min,case.terminal_open_min)
        hi = case.recharge_deadline_min
    else:
        return 0.
    terms = []
    for start,end,_,rate in slices:
        check()
        terms.append(max(0.,min(hi,end)-max(lo,start))/60.*rate)
    capacity = math.fsum(terms)
    if not math.isfinite(capacity):
        raise ValueError('Nonfinite constructive charging capacity')
    return capacity


def _screen_route(case, route, lookup, trips, capacities, check):
    """Start full, check every leg/service, optimistically charge, end full."""
    soc, minimum = case.battery_kwh, case.battery_kwh
    first_failure = None
    seen = set()
    residuals = []
    for index,mid in enumerate(route['movements']):
        check()
        movement = lookup[mid]
        for leg_index,leg in enumerate(movement.legs):
            check()
            soc = math.fsum((soc,-leg.energy_kwh))
            minimum = min(minimum,soc)
            residual = math.fsum((case.reserve_kwh,-soc))
            if residual > cc.TAU_KWH and first_failure is None:
                first_failure = 'leg_reserve:'+mid+':'+str(leg_index)
            residuals.append(residual)
            if movement.kind=='depot' and leg_index+1==movement.depot_split:
                soc = min(case.battery_kwh,math.fsum((soc,case.efficiency*capacities[mid])))
        if movement.after is not None:
            tid = movement.after
            if tid in seen or tid != route['trips'][index]:
                raise ValueError('Constructive route service order is inconsistent')
            seen.add(tid)
            check()
            soc = math.fsum((soc,-trips[tid].energy_kwh))
            minimum = min(minimum,soc)
            residual = math.fsum((case.reserve_kwh,-soc))
            residuals.append(residual)
            if residual > cc.TAU_KWH and first_failure is None:
                first_failure = 'service_reserve:'+tid
    if seen != set(route['trips']) or len(route['movements']) != len(route['trips'])+1:
        raise ValueError('Constructive route does not cover its services exactly once')
    terminal = capacities[route['movements'][-1]]
    shortage = math.fsum((case.battery_kwh,-soc,-case.efficiency*terminal))
    if shortage > cc.TAU_KWH and first_failure is None:
        first_failure = 'terminal_replenishment'
    if not all(math.isfinite(v) for v in (soc,minimum,shortage,*residuals)):
        raise ValueError('Nonfinite optimistic SOC feature')
    return {'passed':first_failure is None,'failure':first_failure,'min_soc_kwh':minimum,
            'max_reserve_residual_kwh':max(residuals,default=0.),
            'terminal_arrival_soc_kwh':soc,'terminal_capacity_grid_kwh':terminal,
            'terminal_shortfall_kwh':max(0.,shortage),
            'terminal_soc_kwh':min(case.battery_kwh,math.fsum((soc,case.efficiency*terminal)))}


def _join(left, right, movement):
    if (left is right or movement.before!=left['trips'][-1]
            or movement.after!=right['trips'][0]
            or set(left['trips']) & set(right['trips'])):
        raise ValueError('Invalid constructive merge ownership')
    return {'trips':left['trips']+right['trips'],
            'movements':left['movements'][:-1]+[movement.id]+right['movements'][1:]}


def _prepare(case, check):
    check()
    cc._validate(case)
    check()
    lookup = {m.id:m for m in case.movements}
    trips = {t.id:t for t in case.trips}
    slices = cc._slices(case)
    capacities, minutes = {}, {}
    for m in case.movements:
        check()
        capacities[m.id] = _window_capacity(case,m,slices,check)
        minutes[m.id] = _minutes(m)
        if not math.isfinite(minutes[m.id]):
            raise ValueError('Nonfinite constructive movement duration')
    return lookup,trips,capacities,minutes


def _route_order(route, trips):
    first = trips[route['trips'][0]]
    return first.start_min,first.end_min,first.id


def _finalize_routes(case, routes, lookup, trips, capacities, check):
    ordered = sorted(routes,key=lambda route:_route_order(route,trips))
    for route in ordered:
        route['optimistic'] = _screen_route(case,route,lookup,trips,capacities,check)
    if len(ordered)>case.max_vehicles:
        return ordered,'no_proposal','vehicle_cap'
    if not ordered or any(not route['optimistic']['passed'] for route in ordered):
        return ordered,'no_proposal','optimistic_route_screen'
    check()
    from egglab.native_pathflow import recover_paths
    selected = {mid for route in ordered for mid in route['movements']}
    recovered,_ = recover_paths(case,[m.id for m in case.movements if m.id in selected])
    check()
    expected = {tuple(route['movements']) for route in ordered}
    if {tuple(route['movements']) for route in recovered} != expected:
        raise ValueError('Recovered native paths differ from constructive routes')
    return ordered,'proposal',None


def _seal(case, ledger, check):
    selected = {mid for route in ledger['routes'] for mid in route['movements']}
    ledger['candidate_selected_ids'] = [m.id for m in case.movements if m.id in selected]
    ledger['selected_ids'] = ledger['candidate_selected_ids'][:] if ledger['status']=='proposal' else []
    ledger['feasibility_certified'] = False
    ledger['shared_contention_checked'] = False
    ledger['ledger_sha256'] = cc._hash(ledger)
    try:
        check()
    except _Deadline:
        ledger['status'],ledger['reason'],ledger['selected_ids'] = 'deadline','absolute_deadline',[]
        ledger.pop('ledger_sha256')
        ledger['ledger_sha256'] = cc._hash(ledger)
    return ledger


def construct_routes(case, *, deadline, clock=time.monotonic):
    """Greedily join declared paths; proposal failure is never global infeasibility."""
    _deadline_value(deadline)
    check = lambda:_clock_check(deadline,clock)
    ledger = {'policy':POLICY,'case_identity':None,'construction_deadline':deadline,
              'deadline':deadline,'status':'no_proposal','reason':None,'initial_routes':[],
              'routes':[],'merge_history':[],'round_diagnostics':[],
              'active_merge_count':0,'undone_count':0,'repair_history':[],
              'diagnostics':{'tau_kwh':cc.TAU_KWH,'capacity_units':'grid_kwh',
                             'initial_invalid_routes':0,'price_blind':True}}
    try:
        check()
        ledger['case_identity'] = case.identity()
        pullouts,pullins = {},{}
        for movement in case.movements:
            check()
            if movement.kind=='pullout':
                pullouts.setdefault(movement.after,[]).append(movement)
            elif movement.kind=='pullin':
                pullins.setdefault(movement.before,[]).append(movement)
        ordered_trips = sorted(case.trips,key=lambda t:(t.start_min,t.end_min,t.id))
        for trip in ordered_trips:
            check()
            if not pullouts.get(trip.id) or not pullins.get(trip.id):
                ledger['reason'] = 'missing_boundary:'+trip.id
                return _seal(case,ledger,check)
        lookup,trips,capacities,minutes = _prepare(case,check)
        for trip in ordered_trips:
            check()
            outgoing,incoming = pullouts.get(trip.id,[]),pullins.get(trip.id,[])
            if not outgoing or not incoming:
                ledger['reason'] = 'missing_boundary:'+trip.id
                return _seal(case,ledger,check)
            pullout = min(outgoing,key=lambda m:(minutes[m.id],m.id))
            pullin = min(incoming,key=lambda m:(minutes[m.id],m.id))
            route = {'trips':[trip.id],'movements':[pullout.id,pullin.id]}
            route['optimistic'] = _screen_route(case,route,lookup,trips,capacities,check)
            ledger['diagnostics']['initial_invalid_routes'] += int(not route['optimistic']['passed'])
            ledger['initial_routes'].append(deepcopy(route))
            ledger['routes'].append(route)
        while True:
            check()
            starts = {r['trips'][0]:r for r in ledger['routes']}
            ends = {r['trips'][-1]:r for r in ledger['routes']}
            best = None
            diagnostic = {'round':len(ledger['merge_history']),'examined':0,
                          'eligible':0,'screen_failed':0,'completed':False}
            ledger['round_diagnostics'].append(diagnostic)
            for movement in case.movements:
                check()
                diagnostic['examined'] += 1
                if movement.kind not in ('direct','depot'):
                    continue
                left,right = ends.get(movement.before),starts.get(movement.after)
                if left is None or right is None or left is right:
                    continue
                joined = _join(left,right,movement)
                screen = _screen_route(case,joined,lookup,trips,capacities,check)
                if not screen['passed']:
                    diagnostic['screen_failed'] += 1
                    continue
                diagnostic['eligible'] += 1
                old_in,old_out = left['movements'][-1],right['movements'][0]
                delta_minutes = math.fsum((minutes[movement.id],-minutes[old_in],-minutes[old_out]))
                delta_capacity = math.fsum((capacities[movement.id],-capacities[old_in]))
                key = (delta_minutes,-delta_capacity,movement.id,left['trips'][0],right['trips'][0])
                if best is None or key < best[0]:
                    joined['optimistic'] = screen
                    best = key,left,right,joined,old_in,old_out,delta_capacity
            diagnostic['completed'] = True
            if best is None:
                break
            key,left,right,joined,old_in,old_out,delta_capacity = best
            ledger['merge_history'].append({'left_first':left['trips'][0],
                'right_first':right['trips'][0],'movement_id':key[2],
                'removed_pullin_id':old_in,'removed_pullout_id':old_out,
                'added_deadhead_minutes':key[0],'added_capacity_grid_kwh':delta_capacity,
                'rank_key':list(key),'optimistic':deepcopy(joined['optimistic'])})
            ledger['routes'] = [r for r in ledger['routes'] if r is not left and r is not right]+[joined]
            ledger['active_merge_count'] = len(ledger['merge_history'])
        ledger['routes'],ledger['status'],ledger['reason'] = _finalize_routes(
            case,ledger['routes'],lookup,trips,capacities,check)
    except _Deadline:
        ledger['status'],ledger['reason'] = 'deadline','absolute_deadline'
    return _seal(case,ledger,check)


def undo_merges(case, ledger, count=1, *, deadline, clock=time.monotonic):
    """Rebuild after at most two cumulative LIFO removals; no solver/oracle call.

    The caller supplies the repair stage's absolute endpoint, not fresh seconds.
    An undo can exceed the vehicle cap or restore an optimistic-invalid route.
    """
    _deadline_value(deadline)
    check = lambda:_clock_check(deadline,clock)
    try:
        check()
    except _Deadline:
        result = deepcopy(ledger)
        result.pop('ledger_sha256',None)
        result['deadline'],result['status'],result['reason'] = deadline,'deadline','absolute_deadline'
        return _seal(case,result,check)
    if (ledger.get('policy')!=POLICY or ledger.get('case_identity')!=case.identity()
            or ledger.get('ledger_sha256')!=cc._hash({k:v for k,v in ledger.items() if k!='ledger_sha256'})):
        raise ValueError('Construction ledger identity/hash mismatch')
    active = ledger['active_merge_count']
    if (type(count) is not int or not 1<=count<=2 or count>active
            or ledger['undone_count']+count>2):
        raise ValueError('Undo requires at most two cumulative available last merges')
    result = deepcopy(ledger)
    result.pop('ledger_sha256')
    result['deadline'],result['status'],result['reason'] = deadline,'no_proposal',None
    try:
        lookup,trips,capacities,_ = _prepare(case,check)
        routes = {r['trips'][0]:{'trips':r['trips'][:],'movements':r['movements'][:]}
                  for r in result['initial_routes']}
        for event in result['merge_history'][:active-count]:
            check()
            left,right = routes.pop(event['left_first']),routes.pop(event['right_first'])
            if (left['movements'][-1]!=event['removed_pullin_id'] or
                    right['movements'][0]!=event['removed_pullout_id']):
                raise ValueError('Undo merge history boundary mismatch')
            joined = _join(left,right,lookup[event['movement_id']])
            routes[joined['trips'][0]] = joined
        result['routes'] = list(routes.values())
        result['active_merge_count'] = active-count
        result['undone_count'] += count
        result['repair_history'].append({'removed_merge_indices':list(range(active-1,active-count-1,-1)),
                                         'deadline':deadline,'count':count})
        result['routes'],result['status'],result['reason'] = _finalize_routes(
            case,result['routes'],lookup,trips,capacities,check)
    except _Deadline:
        result['status'],result['reason'] = 'deadline','absolute_deadline'
    return _seal(case,result,check)
