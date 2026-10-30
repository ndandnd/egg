"""New exact terminal-only witness construction; not a native retry or replay.

Pure stdlib. No tolerances, optimization, route changes, or verifier imports.
The caller must independently replay the newly constructed candidate before
using its cost as a physical upper bound. The input candidate is never mutated.
"""
from fractions import Fraction as Q


def _q(value):
    if isinstance(value,bool):
        raise ValueError('Boolean numerical input')
    return Q(value)


def _require(condition,message):
    if not condition:
        raise ValueError(message)


def construct(case_dict,rawcandidate):
    """Return (newcandidate, changes), or fail without an alternative attempt.

    Preserve every movement ID and every nonterminal allocation exactly. First
    remove terminal surpluses, then fill deficits, both latest-interval first.
    Only final full-replenishment allocations may change. Returned candidate
    deliberately drops reported SOC/load/ops: the new witness recomputes them.
    """
    case = case_dict
    trips = {t['id']:t for t in case['trips']}
    moves = {m['id']:m for m in case['movements']}
    _require(len(trips) == len(case['trips']) and len(moves) == len(case['movements']),
             'Duplicate source identifiers')
    B,reserve,eta = (_q(case[k]) for k in ('battery_kwh','reserve_kwh','efficiency'))
    _require(B > 0 and 0 <= reserve <= B and eta > 0,'Invalid inventory parameters')
    opening,deadline = (_q(case[k]) for k in ('terminal_open_min','recharge_deadline_min'))
    windows = {}
    for mid,movement in moves.items():
        legs = movement['legs']
        _require(bool(legs),'Empty source movement')
        _require(all(_q(l['energy_kwh']) >= 0 and _q(l['depart_min']) <= _q(l['arrive_min']) for l in legs),
                 'Negative consumption or invalid leg time')
        if movement['kind'] == 'depot':
            split = movement['depot_split']
            _require(isinstance(split,int) and 0 < split < len(legs),'Invalid depot split')
            _require(legs[split-1]['destination'] == case['depot'] and legs[split]['origin'] == case['depot'],
                     'Depot charge split is away from depot')
            windows[mid] = (_q(legs[split-1]['arrive_min']),_q(legs[split]['depart_min']))
        elif movement['kind'] == 'pullin':
            windows[mid] = (max(opening,_q(legs[-1]['arrive_min'])),deadline)
        else:
            _require(movement['kind'] in ('direct','pullout'),'Unknown source movement kind')
        if mid in windows:
            _require(windows[mid][0] <= windows[mid][1],'Invalid source charging window')
    market = list(map(_q,case['market_edges_min']))
    _require(len(market) >= 2 and all(a < b for a,b in zip(market,market[1:])), 'Invalid market edges')
    points = set(market)|{opening}
    for resource in case['resources']:
        points.update((_q(resource['start_min']),_q(resource['end_min'])))
    for window in windows.values():
        points.update(window)
    edges,intervals = sorted(points),[]
    for left,right in zip(edges,edges[1:]):
        resources = [r for r in case['resources'] if _q(r['start_min']) <= left and right <= _q(r['end_min'])]
        periods = [i for i,(a,b) in enumerate(zip(market,market[1:])) if a <= left and right <= b]
        _require(len(resources) == 1 and len(periods) == 1,'Uncovered or ambiguous resource interval')
        resource = resources[0]
        _require(resource['connectors'] in (0,1),'Single-connector construction required')
        rate = min(_q(resource['per_bus_kw']),_q(resource['grid_kw'])) if resource['connectors'] else Q(0)
        _require(rate >= 0,'Negative resource power')
        intervals.append(dict(start=left,end=right,capacity=rate*(right-left)/60,
             visits={mid for mid,(a,b) in windows.items() if a <= left and right <= b}))
    selected = list(rawcandidate['selected_movement_ids'])
    _require(len(selected) == len(set(selected)) and all(mid in moves for mid in selected),
             'Duplicate or unknown selected movement')
    incoming,outgoing,starts = {},{},[]
    for mid in selected:
        movement = moves[mid]
        before,after = movement['before'],movement['after']
        if before is None:
            _require(movement['kind'] == 'pullout' and after in trips,'Invalid path start')
            starts.append(mid)
        else:
            _require(before in trips and before not in outgoing,'Invalid or duplicate outgoing link')
            outgoing[before] = mid
        if after is None:
            _require(movement['kind'] == 'pullin' and before in trips,'Invalid path end')
        else:
            _require(after in trips and after not in incoming,'Invalid or duplicate incoming link')
            incoming[after] = mid
    _require(set(incoming) == set(trips) == set(outgoing),'Incomplete coverage')
    _require(1 <= len(starts) <= case['max_vehicles'],'Invalid fleet cardinality')
    routes,owners,visited = [],{},set()
    for start in sorted(starts):
        bus,route,mid = len(routes),[],start
        while True:
            _require(mid not in owners,'Movement cycle or repetition')
            owners[mid] = bus
            route.append(mid)
            movement = moves[mid]
            if movement['after'] is None:
                break
            tid = movement['after']
            _require(tid not in visited,'Service cycle or repetition')
            visited.add(tid)
            mid = outgoing[tid]
        routes.append(route)
    _require(set(owners) == set(selected) and visited == set(trips),'Disconnected selected component')
    allocations,order = {},[]
    for cell in rawcandidate['charge_by_interval']:
        mid,k = cell['movement'],cell['interval']
        _require(mid in moves and isinstance(k,int) and not isinstance(k,bool) and 0 <= k < len(intervals),
                 'Invalid allocation key')
        key = (mid,k)
        _require(key not in allocations,'Duplicate allocation cell')
        energy = _q(cell['energy'])
        _require(energy >= 0,'Negative allocation is not a terminal-only problem')
        _require(not energy or (mid in owners and mid in intervals[k]['visits']),
                 'Positive allocation outside selected charging window')
        allocations[key] = energy
        order.append(key)
    original = dict(allocations)
    totals = [sum((e for (mid,kk),e in allocations.items() if kk == k),Q(0)) for k in range(len(intervals))]
    _require(all(total <= interval['capacity'] for total,interval in zip(totals,intervals)),
             'Original shared interval capacity violation is outside this construction scope')
    def check_inventory(value,context):
        _require(reserve <= value <= B,'Nonterminal inventory violation: '+context)
    balances = []
    for bus,route in enumerate(routes):
        soc,consumption,nonterminal_grid = B,Q(0),Q(0)
        terminal_mid = route[-1]
        for mid in route:
            movement = moves[mid]
            legs = movement['legs']
            before,after = movement['before'],movement['after']
            lower = opening if before is None else _q(trips[before]['end_min'])
            upper = deadline if after is None else _q(trips[after]['start_min'])
            origin = case['depot'] if before is None else trips[before]['end_place']
            destination = case['depot'] if after is None else trips[after]['start_place']
            _require(legs[0]['origin'] == origin and legs[-1]['destination'] == destination and
                     lower <= _q(legs[0]['depart_min']) and _q(legs[-1]['arrive_min']) <= upper,
                     'Selected movement endpoint or timing problem')
            _require(all(a['destination'] == b['origin'] and _q(a['arrive_min']) <= _q(b['depart_min'])
                         for a,b in zip(legs,legs[1:])), 'Discontinuous selected movement')
            _require((before is None and movement['kind']=='pullout') or
                     (after is None and movement['kind']=='pullin') or
                     (before is not None and after is not None and movement['kind'] in ('direct','depot')),
                     'Selected movement kind mismatch')
            for leg_index,leg in enumerate(legs):
                if movement['kind'] == 'depot' and leg_index == movement['depot_split']:
                    grid = sum((e for (owner,k),e in allocations.items() if owner == mid),Q(0))
                    soc += eta*grid
                    nonterminal_grid += grid
                    check_inventory(soc,'after depot recharge '+str(mid))
                energy = _q(leg['energy_kwh'])
                soc -= energy
                consumption += energy
                check_inventory(soc,'after leg '+str(mid))
            if after is not None:
                trip = trips[after]
                _require(_q(trip['start_min']) < _q(trip['end_min']) and _q(trip['energy_kwh']) >= 0,
                         'Invalid selected service')
                soc -= _q(trip['energy_kwh'])
                consumption += _q(trip['energy_kwh'])
                check_inventory(soc,'after service '+str(after))
        _require(moves[terminal_mid]['kind'] == 'pullin','Route lacks terminal pull-in')
        terminal_original = sum((e for (mid,k),e in allocations.items() if mid == terminal_mid),Q(0))
        target = (B-soc)/eta
        _require(target >= 0,'Negative terminal refill requirement')
        balances.append(dict(vehicle=bus,movements=list(route),terminal_movement=terminal_mid,
             terminal_arrival_soc=soc,consumption=consumption,nonterminal_grid=nonterminal_grid,
             original_terminal_grid=terminal_original,target_terminal_grid=target,
             original_fullness_residual=eta*(nonterminal_grid+terminal_original)-consumption))
    latest = sorted(range(len(intervals)),key=lambda k:(intervals[k]['end'],intervals[k]['start'],k),reverse=True)
    # Surplus removal precedes every addition, making released shared capacity
    # available without making the answer depend on which deficit is encountered.
    for balance in balances:
        mid = balance['terminal_movement']
        surplus = max(Q(0),balance['original_terminal_grid']-balance['target_terminal_grid'])
        for k in latest:
            key = (mid,k)
            take = min(surplus,allocations.get(key,Q(0)))
            if take:
                allocations[key] -= take
                totals[k] -= take
                surplus -= take
            if not surplus:
                break
        _require(not surplus,'Insufficient terminal charge to remove surplus')
    for balance in balances:
        mid = balance['terminal_movement']
        current = sum((e for (owner,k),e in allocations.items() if owner == mid),Q(0))
        deficit = balance['target_terminal_grid']-current
        _require(deficit >= 0,'Surplus remained after deterministic removal')
        for k in latest:
            if mid not in intervals[k]['visits']:
                continue
            add = min(deficit,intervals[k]['capacity']-totals[k])
            if add:
                key = (mid,k)
                if key not in allocations:
                    allocations[key] = Q(0)
                    order.append(key)
                allocations[key] += add
                totals[k] += add
                deficit -= add
            if not deficit:
                break
        _require(not deficit,'Latest-first construction exhausted eligible capacity; no general infeasibility claim or fallback')
        final = sum((e for (owner,k),e in allocations.items() if owner == mid),Q(0))
        _require(final == balance['target_terminal_grid'],'Terminal equality construction failed')
        balance['new_terminal_grid'] = final
        balance['new_fullness_residual'] = eta*(balance['nonterminal_grid']+final)-balance['consumption']
        _require(balance['new_fullness_residual'] == 0,'Whole-bus exact conservation failed')
    changed = []
    for key in order:
        old,new = original.get(key,Q(0)),allocations[key]
        if old != new:
            _require(moves[key[0]]['kind'] == 'pullin' and key[0] in owners,'Nonterminal cell changed')
            changed.append(dict(movement=key[0],interval=key[1],original=old,new=new,delta=new-old,
                                newly_created_cell=key not in original))
    _require(all(total <= interval['capacity'] for total,interval in zip(totals,intervals)),
             'Constructed shared capacity violation')
    newcandidate = dict(selected_movement_ids=list(selected),charge_by_interval=[
        dict(movement=mid,interval=k,energy=allocations[mid,k]) for mid,k in order])
    changes = dict(scope='new exact terminal-only construction on unchanged native topology',
        independently_replayed=False,physical_upper_certified=False,repairs_are_explicit=True,
        failure_does_not_prove_topology_infeasible=True,
        policy='remove surplus latest positive pull-in cells, then fill deficits latest eligible shared residual cells',
        changed_cells=changed,per_bus=balances,
        dropped_reported_fields=sorted(k for k in rawcandidate if k not in ('selected_movement_ids','charge_by_interval')),
        original_candidate_mutated=False,all_other_allocations_preserved=True,
        original_total_grid=sum(original.values(),Q(0)),new_total_grid=sum(allocations.values(),Q(0)),
        exact_total_grid_change=sum(allocations.values(),Q(0))-sum(original.values(),Q(0)),
        next_step='Independently replay newcandidate against original exact per-leg/window/resource inputs before claiming an upper bound')
    return newcandidate,changes
