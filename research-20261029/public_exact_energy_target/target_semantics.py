"""NEW exact-consumption target semantics, not the old binary-energy model.

Transparent source fork of exact_dual.py: energy fields alone use the explicit
target rational parser. Nonenergy source-number/time validation and all row
construction are retained. Old sources and old scientific bounds are untouched.

Only stdlib Fraction/regular-expression parsing is used. No builder/compiler/
backend is imported. _reconstruct consumes a target dictionary and returns its
exact six-tuple ledger. Unused original verification APIs have been removed;
this module cannot certify an old or new bound by itself.
Source-only authored; execution qualification is a separate paid task.
"""
from fractions import Fraction
import re


class _Reject(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise _Reject(message)


def _q(value):
    _require(not isinstance(value, bool) and isinstance(value, (int, float, str, Fraction)),
             'Expected a finite rational-compatible coefficient')
    try:
        return Fraction(value)
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise _Reject('Nonfinite or malformed rational coefficient') from exc


def _source_number(value):
    _require(not isinstance(value, bool) and isinstance(value, (int, float)),
             'Case must preserve numeric asdict inputs, not string coefficients')
    return _q(value)


def _energy_number(value):
    _require(not isinstance(value,bool) and isinstance(value,(int,str,Fraction)),
             'Target energy must be an explicit exact rational, never float')
    if isinstance(value,str):
        _require(len(value)<=4096,'Target energy token too long')
        _require(re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?',value) is not None,
                 'Canonical integer/fraction syntax only; no exponents')
        _require(value==str(Fraction(value)),'Target energy must use canonical rational text')
    result=_q(value)
    _require(result>=0 and result.numerator.bit_length()<=32768
             and result.denominator.bit_length()<=32768,'Target energy sign/size')
    return result


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _time(value):
    value = _source_number(value)
    _require(0 <= value <= 2**20 and (2*value).denominator == 1,
             'Time outside exact source half-minute lattice')
    return value


def _text(value):
    _require(isinstance(value, str) and bool(value), 'Missing identifier/place')
    return value


def _keys(value, names):
    _require(isinstance(value, dict) and set(value) == set(names.split()),
             'Descriptor fields do not match the admitted case schema')


def _case(case):
    """Validate declarative paths independently; never infer or delete an arc."""
    _keys(case, 'name trips movements resources market_edges_min depot max_vehicles '
                'battery_kwh reserve_kwh terminal_open_min recharge_deadline_min '
                'vehicle_cost deadhead_cost_per_min efficiency graph_scope')
    _text(case['name'])
    depot = _text(case['depot'])
    _require(case['graph_scope'] == 'declared-movement-modes-only', 'Unknown graph scope')
    _require(_integer(case['max_vehicles']) and case['max_vehicles'] >= 1, 'Invalid fleet cap')
    B, reserve, eta = map(_source_number,
        (case['battery_kwh'], case['reserve_kwh'], case['efficiency']))
    fee, travel = map(_source_number, (case['vehicle_cost'], case['deadhead_cost_per_min']))
    _require(B > 0 and 0 <= reserve < B and 0 < eta <= 1 and fee >= 0 and travel >= 0,
             'Invalid physics/cost parameters')
    opening, deadline = map(_time, (case['terminal_open_min'], case['recharge_deadline_min']))
    edges = list(map(_time, case['market_edges_min']))
    _require(len(edges) >= 2 and edges[0] == 0 and edges[-1] == deadline
             and 0 <= opening <= deadline and all(a < b for a,b in zip(edges,edges[1:])),
             'Invalid market horizon')
    trips, trip_by_id = [], {}
    for trip in case['trips']:
        _keys(trip, 'id start_min end_min start_place end_place energy_kwh')
        name = _text(trip['id'])
        _require(name not in trip_by_id, 'Duplicate service ID')
        start, end, energy = _time(trip['start_min']), _time(trip['end_min']), _energy_number(trip['energy_kwh'])
        _require(0 <= start < end <= deadline and 0 <= energy <= B-reserve,
                 'Invalid mandatory service')
        item = dict(id=name,start=start,end=end,energy=energy,
                    origin=_text(trip['start_place']),destination=_text(trip['end_place']))
        trips.append(item)
        trip_by_id[name] = item
    _require(bool(trips), 'No mandatory services')
    resources, cursor = [], Fraction(0)
    for resource in case['resources']:
        _keys(resource, 'start_min end_min per_bus_kw grid_kw connectors')
        start, end = _time(resource['start_min']), _time(resource['end_min'])
        per_bus, grid = _source_number(resource['per_bus_kw']), _source_number(resource['grid_kw'])
        connectors = resource['connectors']
        _require(start == cursor and start < end <= deadline and per_bus >= 0 and grid >= 0
                 and _integer(connectors) and connectors in (0,1), 'Invalid single-connector resources')
        resources.append(dict(start=start,end=end,rate=min(per_bus,grid) if connectors else Fraction(0)))
        cursor = end
    _require(cursor == deadline and bool(resources), 'Resources do not cover the horizon')
    movements, known = [], set()
    for movement in case['movements']:
        _keys(movement, 'id kind before after legs depot_split')
        name, kind = _text(movement['id']), movement['kind']
        _require(name not in known and kind in ('pullout','pullin','direct','depot'), 'Invalid movement ID/kind')
        known.add(name)
        before, after = movement['before'], movement['after']
        valid = ((kind == 'pullout' and before is None and after in trip_by_id)
                 or (kind == 'pullin' and before in trip_by_id and after is None)
                 or (kind in ('direct','depot') and before in trip_by_id and after in trip_by_id and before != after))
        _require(valid, 'Invalid movement service endpoints')
        legs = []
        for leg in movement['legs']:
            _keys(leg, 'origin destination depart_min arrive_min energy_kwh')
            depart, arrive, energy = _time(leg['depart_min']), _time(leg['arrive_min']), _energy_number(leg['energy_kwh'])
            _require(0 <= depart <= arrive <= deadline and energy >= 0, 'Invalid movement leg')
            legs.append(dict(origin=_text(leg['origin']),destination=_text(leg['destination']),
                             depart=depart,arrive=arrive,energy=energy))
        _require(bool(legs), 'Movement without legs')
        _require(all(l['destination'] == r['origin'] and l['arrive'] <= r['depart']
                     for l,r in zip(legs,legs[1:])), 'Broken movement path')
        origin = depot if before is None else trip_by_id[before]['destination']
        destination = depot if after is None else trip_by_id[after]['origin']
        earliest = Fraction(0) if before is None else trip_by_id[before]['end']
        latest = deadline if after is None else trip_by_id[after]['start']
        _require(legs[0]['origin'] == origin and legs[-1]['destination'] == destination
                 and legs[0]['depart'] >= earliest and legs[-1]['arrive'] <= latest,
                 'Movement chronology/direction invalid; no DAG interpretation')
        split, window = movement['depot_split'], None
        if kind == 'depot':
            _require(_integer(split) and 1 <= split < len(legs)
                     and legs[split-1]['destination'] == depot and legs[split]['origin'] == depot,
                     'Invalid depot gap')
            window = (legs[split-1]['arrive'], legs[split]['depart'])
        else:
            _require(split is None, 'Unexpected depot split')
            if kind == 'pullin':
                window = (max(legs[-1]['arrive'],opening),deadline)
        movements.append(dict(id=name,kind=kind,before=before,after=after,
                              legs=legs,split=split,window=window))
    _require(bool(movements), 'No declared movements')
    # Reachability checks only reject an invalid descriptor; they add no rows.
    forward = {m['after'] for m in movements if m['kind'] == 'pullout'}
    backward = {m['before'] for m in movements if m['kind'] == 'pullin'}
    for _ in trips:
        forward |= {m['after'] for m in movements if m['before'] in forward and m['after'] is not None}
        backward |= {m['before'] for m in movements if m['after'] in backward and m['before'] is not None}
    _require(forward == set(trip_by_id) and backward == set(trip_by_id), 'Graph lacks service reachability')
    return dict(B=B,reserve=reserve,eta=eta,fee=fee,travel=travel,
                cap=case['max_vehicles'],trips=trips,movements=movements,
                edges=edges,resources=resources,opening=opening)


def _reconstruct(case):
    """Build semantic variables/rows without using compiler or ledger indices."""
    data = _case(case)
    variables, rows = {}, {}
    def variable(name,lo,hi):
        _require(name not in variables and lo <= hi, 'Internal variable collision/bounds')
        variables[name] = (Fraction(lo),Fraction(hi))
        return name
    def row(name,terms,sense,rhs=0):
        _require(name not in rows, 'Internal row collision')
        coefficients = {}
        for name2,value in terms:
            _require(name2 in variables, 'Internal unknown variable')
            coefficients[name2] = coefficients.get(name2,Fraction(0))+Fraction(value)
        rows[name] = (sense,Fraction(rhs),{n:v for n,v in coefficients.items() if v})
    moves, B, reserve, eta = data['movements'], data['B'], data['reserve'], data['eta']
    boundaries = set(data['edges']) | {data['opening']}
    for resource in data['resources']:
        boundaries.update((resource['start'],resource['end']))
    for movement in moves:
        if movement['window'] is not None:
            boundaries.update(movement['window'])
    boundaries = sorted(boundaries)
    intervals = []
    for k,(left,right) in enumerate(zip(boundaries,boundaries[1:])):
        resource = next(r for r in data['resources'] if r['start'] <= left < r['end'])
        period = next(t for t,(a,b) in enumerate(zip(data['edges'],data['edges'][1:])) if a <= left < b)
        _require(right <= resource['end'] and right <= data['edges'][period+1], 'Incomplete boundary partition')
        visits = [m['id'] for m in moves if m['window'] is not None
                  and m['window'][0] <= left and right <= m['window'][1]]
        intervals.append(dict(index=k,start=left,end=right,rate=resource['rate'],
                              capacity=resource['rate']*(right-left)/60,period=period,visits=visits))
    y = [variable('y'+str(j),0,1) for j in range(len(moves))]
    allocations = {}
    for j,movement in enumerate(moves):
        for interval in intervals:
            k,cap = interval['index'],interval['capacity']
            if cap > 0 and movement['id'] in interval['visits']:
                q = variable('q'+str(j)+'_'+str(k),0,cap)
                allocations[j,k] = q
                row('charge_selection_'+str(j)+'_'+str(k),[(q,1),(y[j],-cap)],'<=')
    for interval in intervals:
        k = interval['index']
        row('shared_'+str(k),[(q,1) for (j,kk),q in allocations.items() if kk == k],
            '<=',interval['capacity'])
    entry,exit = [],[]
    for j,movement in enumerate(moves):
        def state(suffix):
            name = variable('s'+str(j)+'_'+suffix,0,B)
            row('headroom_'+str(j)+'_'+suffix,[(name,1),(y[j],-B)],'<=')
            row('reserve_'+str(j)+'_'+suffix,[(name,1),(y[j],-reserve)],'>=')
            return name
        current = state('entry')
        entry.append(current)
        if movement['kind'] == 'pullout':
            row('full_start_'+str(j),[(current,1),(y[j],-B)],'=')
        for l,leg in enumerate(movement['legs']):
            if movement['kind'] == 'depot' and l == movement['split']:
                following = state('depot_departure')
                row('depot_charge_'+str(j),[(following,1),(current,-1)]+
                    [(q,-eta) for (jj,k),q in allocations.items() if jj == j],'=')
                current = following
            following = state('leg'+str(l)+'_arrival')
            row('leg_'+str(j)+'_'+str(l),[(following,1),(current,-1),(y[j],leg['energy'])],'=')
            current = following
        if movement['kind'] == 'pullin':
            following = state('terminal_full')
            row('terminal_charge_'+str(j),[(following,1),(current,-1)]+
                [(q,-eta) for (jj,k),q in allocations.items() if jj == j],'=')
            row('full_end_'+str(j),[(following,1),(y[j],-B)],'=')
            current = following
        exit.append(current)
    starts = [y[j] for j,m in enumerate(moves) if m['kind'] == 'pullout']
    ends = [y[j] for j,m in enumerate(moves) if m['kind'] == 'pullin']
    fleet_proof = _minimum_fleet(data)
    row('fleet_limit',[(n,1) for n in starts],'<=',data['cap'])
    row('derived_minimum_fleet',[(n,1) for n in starts],'>=',fleet_proof['minimum_fleet'])
    row('fleet_balance',[(n,1) for n in starts]+[(n,-1) for n in ends],'=')
    for i,trip in enumerate(data['trips']):
        incoming = [j for j,m in enumerate(moves) if m['after'] == trip['id']]
        outgoing = [j for j,m in enumerate(moves) if m['before'] == trip['id']]
        row('cover_in_'+str(i),[(y[j],1) for j in incoming],'=',1)
        row('cover_out_'+str(i),[(y[j],1) for j in outgoing],'=',1)
        row('service_energy_'+str(i),[(exit[j],1) for j in incoming]+
            [(entry[j],-1) for j in outgoing],'=',trip['energy'])
    loads = []
    for t in range(len(data['edges'])-1):
        cap = sum((k['capacity'] for k in intervals if k['period'] == t),Fraction(0))
        name = variable('load'+str(t),0,cap)
        loads.append(name)
        row('market_load_'+str(t),[(name,1)]+
            [(q,-1) for (j,k),q in allocations.items() if intervals[k]['period'] == t],'=')
    operations = {}
    for j,movement in enumerate(moves):
        value = data['travel']*sum((l['arrive']-l['depart'] for l in movement['legs']),Fraction(0))
        if movement['kind'] == 'pullout':
            value += data['fee']
        if value:
            operations[y[j]] = value
    return variables,rows,intervals,operations,loads,fleet_proof


def _minimum_fleet(data):
    """Prove a fleet floor from services/graph; no native or archived evidence.

    The sweep applies end/start changes at a shared time together, hence
    service intervals are half open. For a possible one-bus chronology every
    consecutive service link must exist. If every such link is direct, there
    is no declared recharge opportunity before all services have completed.
    """
    events,starting_times = {},set()
    for trip in data['trips']:
        starting_times.add(trip['start'])
        for time,change in ((trip['start'],1),(trip['end'],-1)):
            events[time] = events.get(time,0)+change
    active,overlap_counts = 0,[]
    for time in sorted(events):
        active += events[time]
        if time in starting_times:
            overlap_counts.append(dict(time=time,count=active))
    overlap = max(item['count'] for item in overlap_counts)
    sequence = sorted(data['trips'],key=lambda t:(t['start'],t['end'],t['id']))
    disjoint = all(a['end'] <= b['start'] for a,b in zip(sequence,sequence[1:]))
    connections = []
    if disjoint:
        for a,b in zip(sequence,sequence[1:]):
            options = [m for m in data['movements'] if m['before'] == a['id'] and m['after'] == b['id']]
            connections.append(dict(before=a['id'],after=b['id'],
                movement_ids=[m['id'] for m in options],kinds=[m['kind'] for m in options]))
    missing = disjoint and any(not link['movement_ids'] for link in connections)
    direct_only = disjoint and all(link['movement_ids'] and set(link['kinds']) == {'direct'}
                                   for link in connections)
    service_energy = sum((t['energy'] for t in sequence),Fraction(0))
    usable = data['B']-data['reserve']
    energy_obstruction = direct_only and service_energy > usable
    minimum = max(1,overlap,2 if missing or energy_obstruction else 1)
    return dict(minimum_fleet=minimum,half_open_overlap_bound=overlap,
        overlap_counts=overlap_counts,chronologically_disjoint=disjoint,
        consecutive_connections=connections,missing_consecutive_connection=missing,
        all_consecutive_options_direct=direct_only,service_energy=service_energy,
        usable_initial_above_reserve=usable,no_recharge_energy_obstruction=energy_obstruction)


