"""Independent strict rational replay of new interval-allocation candidates.

Only stdlib is imported. This module never imports the native builder/replay or
repairs an allocation. A failed numeric candidate is not an infeasible topology.
"""
from collections import Counter
from fractions import Fraction as Q


def _q(value):
    if isinstance(value, bool):
        raise ValueError('Boolean energy/time')
    return Q(value)


def verify(variant, candidate):
    """Check NativeCase-shaped dict and native_probe candidate dict.

    Core fields: selected_movement_ids, charge_by_interval [{movement,interval,
    energy}]. Optional load, ops, and soc [{trip,before,after}] are checked for
    exact agreement, separately from physical constraints. Returns rational
    violations and reconstructed quantities; no tolerance is silently admitted.
    """
    errors, traces, sessions = [], [], []
    result = dict(strict_pass=False, physical_strict_pass=False,
                  objective_is_certified_physical_upper=False,
                  classification='candidate-not-yet-verified', violations=errors,
                  exact_semantics='Fraction of stored float, or supplied rational string',
                  repairs_applied=False, tolerance_feasibility='not assessed',
                  inference_limit='Candidate failure does not prove topology infeasibility')

    def fail(kind, context, amount=None, representation=False):
        row = dict(kind=kind, context=context, representation_only=representation)
        if amount is not None:
            row['amount_exact'] = amount
        errors.append(row)

    def require(condition, context):
        if not condition:
            raise ValueError(context)

    try:
        trips = {t['id']:t for t in variant['trips']}
        moves = {m['id']:m for m in variant['movements']}
        require(len(trips) == len(variant['trips']), 'Duplicate source trip ID')
        require(len(moves) == len(variant['movements']), 'Duplicate source movement ID')
        B, reserve, eta = (_q(variant[k]) for k in ('battery_kwh','reserve_kwh','efficiency'))
        opening, deadline = (_q(variant[k]) for k in ('terminal_open_min','recharge_deadline_min'))
        require(B > 0 and 0 <= reserve <= B and eta > 0, 'Invalid source inventory parameters')
        depot = variant['depot']
        for t in trips.values():
            require(_q(t['start_min']) < _q(t['end_min']) and _q(t['energy_kwh']) >= 0,
                    'Invalid service '+str(t['id']))
        windows = {}
        for mid,m in moves.items():
            legs = m['legs']
            require(bool(legs), 'Empty movement '+str(mid))
            for leg in legs:
                require(_q(leg['depart_min']) <= _q(leg['arrive_min']) and _q(leg['energy_kwh']) >= 0,
                        'Invalid source movement leg '+str(mid))
            if m['kind'] == 'depot':
                split = m['depot_split']
                require(isinstance(split,int) and 0 < split < len(legs), 'Invalid depot split')
                require(legs[split-1]['destination'] == depot and legs[split]['origin'] == depot,
                        'Depot split away from depot')
                windows[mid] = (_q(legs[split-1]['arrive_min']),_q(legs[split]['depart_min']))
            elif m['kind'] == 'pullin':
                windows[mid] = (max(_q(legs[-1]['arrive_min']),opening),deadline)
            else:
                require(m['kind'] in ('pullout','direct'), 'Unknown source movement kind')
            if mid in windows:
                require(windows[mid][0] <= windows[mid][1], 'Negative charging window')
        market = list(map(_q,variant['market_edges_min']))
        require(all(a < b for a,b in zip(market,market[1:])), 'Invalid market partition')
        points = set(market)|{opening}
        for resource in variant['resources']:
            points.update((_q(resource['start_min']),_q(resource['end_min'])))
        for window in windows.values():
            points.update(window)
        edges, intervals = sorted(points), []
        for left,right in zip(edges,edges[1:]):
            resources = [r for r in variant['resources'] if _q(r['start_min']) <= left and right <= _q(r['end_min'])]
            periods = [i for i,(a,b) in enumerate(zip(market,market[1:])) if a <= left and right <= b]
            require(len(resources) == 1 and len(periods) == 1, 'Uncovered/ambiguous interval')
            r = resources[0]
            require(r['connectors'] in (0,1), 'Verifier is scoped to at most one shared connector')
            rate = min(_q(r['per_bus_kw']),_q(r['grid_kw'])) if r['connectors'] else Q(0)
            require(rate >= 0, 'Negative resource power')
            intervals.append(dict(start=left,end=right,rate=rate,period=periods[0],
                                  visits={mid for mid,(a,b) in windows.items() if a <= left and right <= b}))
        selected = candidate['selected_movement_ids']
        require(len(selected) == len(set(selected)) and all(mid in moves for mid in selected),
                'Duplicate/unknown selected movement')
        incoming, outgoing = {}, {}
        starts = []
        for mid in selected:
            m = moves[mid]
            before,after = m['before'],m['after']
            if before is None:
                require(m['kind'] == 'pullout' and after in trips, 'Invalid selected start')
                starts.append(mid)
            else:
                require(before in trips and before not in outgoing, 'Invalid/duplicate outgoing movement')
                outgoing[before] = mid
            if after is None:
                require(m['kind'] == 'pullin' and before in trips, 'Invalid selected end')
            else:
                require(after in trips and after not in incoming, 'Invalid/duplicate incoming movement')
                incoming[after] = mid
        require(set(incoming) == set(trips) == set(outgoing), 'Incomplete service path cover')
        require(1 <= len(starts) <= variant['max_vehicles'], 'Invalid fleet count')
        routes, owners, covered = [], {}, []
        for first in sorted(starts):
            bus, mids, tids, mid = len(routes), [], [], first
            while True:
                require(mid not in owners, 'Repeated movement/cycle')
                owners[mid] = bus
                mids.append(mid)
                m = moves[mid]
                if m['after'] is None:
                    break
                tid = m['after']
                require(tid not in covered, 'Repeated service/cycle')
                covered.append(tid)
                tids.append(tid)
                mid = outgoing[tid]
            routes.append(dict(vehicle=bus,movements=mids,trips=tids))
        require(set(owners) == set(selected) and Counter(covered) == Counter(trips.keys()), 'Disconnected selected component')
        for route in routes:
            for mid in route['movements']:
                m,legs = moves[mid],moves[mid]['legs']
                before,after = m['before'],m['after']
                origin = depot if before is None else trips[before]['end_place']
                destination = depot if after is None else trips[after]['start_place']
                lower = opening if before is None else _q(trips[before]['end_min'])
                upper = deadline if after is None else _q(trips[after]['start_min'])
                require(legs[0]['origin'] == origin and legs[-1]['destination'] == destination,
                        'Movement endpoint mismatch '+str(mid))
                require(lower <= _q(legs[0]['depart_min']) and _q(legs[-1]['arrive_min']) <= upper,
                        'Movement timing mismatch '+str(mid))
                for a,b in zip(legs,legs[1:]):
                    require(a['destination'] == b['origin'] and _q(a['arrive_min']) <= _q(b['depart_min']),
                            'Discontinuous movement '+str(mid))
                require((before is None and m['kind']=='pullout') or
                        (after is None and m['kind']=='pullin') or
                        (before is not None and after is not None and m['kind'] in ('direct','depot')),
                        'Movement ownership/kind mismatch')
        allocations, seen = [], set()
        for allocation in candidate['charge_by_interval']:
            mid,k = allocation['movement'],allocation['interval']
            require(isinstance(k,int) and not isinstance(k,bool) and 0 <= k < len(intervals), 'Invalid charge interval index')
            require(mid in moves and (mid,k) not in seen, 'Duplicate/unknown charge allocation')
            seen.add((mid,k))
            energy = _q(allocation['energy'])
            if energy < 0:
                fail('negative-charge',str((mid,k)),-energy)
            if energy and (mid not in owners or mid not in intervals[k]['visits']):
                fail('charge-outside-selected-window',str((mid,k)),abs(energy))
            allocations.append((mid,k,energy))
        loads = [Q(0)]*(len(market)-1)
        # A shared-power allocation in each elementary interval can be realized
        # serially at its exact resource rate. This is an explicit new witness,
        # not a repair: every allocated energy is kept exactly unchanged.
        for k,interval in enumerate(intervals):
            rows = [(mid,e) for mid,kk,e in allocations if kk == k and e > 0]
            total = sum((e for _,e in rows),Q(0))
            cap = interval['rate']*(interval['end']-interval['start'])/60
            if total > cap:
                fail('shared-interval-capacity',str(k),total-cap)
            cursor = interval['start']
            for mid,energy in sorted(rows,key=lambda row:(owners.get(row[0],-1),str(row[0]))):
                if mid not in owners or mid not in interval['visits'] or not interval['rate']:
                    continue
                end = cursor+60*energy/interval['rate']
                sessions.append(dict(vehicle=owners[mid],movement=mid,interval=k,
                    start=cursor,end=end,power=interval['rate'],energy=energy))
                cursor = end
            loads[interval['period']] += sum((e for _,kk,e in allocations if kk == k),Q(0))
        total_consumption = Q(0)
        computed_soc = {}
        for route in routes:
            bus,events = route['vehicle'],[]
            for mid in route['movements']:
                for leg_index,leg in enumerate(moves[mid]['legs']):
                    energy = _q(leg['energy_kwh'])
                    total_consumption += energy
                    events.append((_q(leg['arrive_min']),1,'movement:'+str(mid)+':'+str(leg_index),-energy))
            for tid in route['trips']:
                t = trips[tid]
                energy = _q(t['energy_kwh'])
                total_consumption += energy
                events.append((_q(t['start_min']),2,'before:'+str(tid),Q(0)))
                events.append((_q(t['end_min']),1,'service:'+str(tid),-energy))
                events.append((_q(t['end_min']),2,'after:'+str(tid),Q(0)))
            for i,s in enumerate(sessions):
                if s['vehicle'] == bus:
                    events.append((s['end'],0,'charge:'+str(i),eta*s['energy']))
            soc = B
            bus_trace = []
            for when,_,event,delta in sorted(events):
                soc += delta
                if when > deadline:
                    fail('event-after-deadline',str((bus,event)),when-deadline)
                if soc < reserve:
                    fail('inventory-below-reserve',str((bus,event)),reserve-soc)
                if soc > B:
                    fail('inventory-above-capacity',str((bus,event)),soc-B)
                if event.startswith('before:') or event.startswith('after:'):
                    which,tid = event.split(':',1)
                    computed_soc.setdefault(tid,{})[which] = soc
                bus_trace.append(dict(time=when,event=event,delta=delta,soc=soc))
            if soc != B:
                fail('terminal-fullness',str(bus),soc-B)
            traces.append(dict(vehicle=bus,events=bus_trace,terminal_soc=soc))
        total_grid = sum(loads,Q(0))
        if eta*total_grid != total_consumption:
            fail('whole-fleet-conservation','all',eta*total_grid-total_consumption)
        ops = _q(variant['vehicle_cost'])*len(routes)+_q(variant.get('deadhead_cost_per_min',0))*sum(
            (_q(l['arrive_min'])-_q(l['depart_min']) for mid in selected for l in moves[mid]['legs']),Q(0))
        if 'load' in candidate:
            require(len(candidate['load']) == len(loads), 'Reported load dimension mismatch')
            for i,(reported,exact) in enumerate(zip(candidate['load'],loads)):
                if _q(reported) != exact:
                    fail('reported-load-residual',str(i),_q(reported)-exact,True)
        if 'ops' in candidate and _q(candidate['ops']) != ops:
            fail('reported-ops-residual','all',_q(candidate['ops'])-ops,True)
        if 'soc' in candidate:
            require(Counter(str(s['trip']) for s in candidate['soc']) == Counter(str(tid) for tid in trips), 'Reported SOC service coverage mismatch')
            for row in candidate['soc']:
                tid = str(row['trip'])
                for which in ('before','after'):
                    difference = _q(row[which])-computed_soc[tid][which]
                    if difference:
                        fail('reported-soc-residual',tid+':'+which,difference,True)
        a,b = Q(float(.2)),Q(float(1/900))
        cost = ops+sum((a*x+b*x*x/2 for x in loads),Q(0))
        result.update(routes=routes,intervals=[{k:v for k,v in interval.items() if k!='visits'} for interval in intervals],
                      sessions=sessions,soc_traces=traces,loads_exact=loads,
                      ops_exact=ops,total_grid_exact=total_grid,total_consumption_exact=total_consumption,
                      objective_exact=cost,market_a_exact=a,market_b_exact=b)
        result['physical_strict_pass'] = not any(not e['representation_only'] for e in errors)
        result['objective_is_certified_physical_upper'] = result['physical_strict_pass']
        result['strict_pass'] = not errors
        result['classification'] = 'exact-feasible-candidate' if not errors else 'strict-candidate-replay-failure'
    except (KeyError,TypeError,ValueError,IndexError,ZeroDivisionError,OverflowError) as exc:
        fail('malformed-or-structurally-invalid',str(exc))
        result['classification'] = 'strict-candidate-replay-failure'
    return result
