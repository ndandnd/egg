"""Independent exact box-residual lower certificates for energy-flow proposals.

Only stdlib Fraction is used. No builder/compiler/backend is imported. Public
entry point verify_and_bound consumes plain dictionaries and returns JSON-safe
exact strings. Native status, RC and claimed optimality are never proof inputs.
Source-only authored; execution qualification is a separate paid task.
"""
from fractions import Fraction


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
        start, end, energy = _time(trip['start_min']), _time(trip['end_min']), _source_number(trip['energy_kwh'])
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
            depart, arrive, energy = _time(leg['depart_min']), _time(leg['arrive_min']), _source_number(leg['energy_kwh'])
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


def _check_fleet_proof(actual,expected):
    _require(isinstance(actual,dict), 'Missing minimum-fleet proof metadata')
    for name in ('minimum_fleet','half_open_overlap_bound'):
        _require(_integer(actual[name]) and actual[name] == expected[name], 'Minimum-fleet integer mismatch: '+name)
    for name in ('chronologically_disjoint','missing_consecutive_connection',
                 'all_consecutive_options_direct','no_recharge_energy_obstruction'):
        _require(isinstance(actual[name],bool) and actual[name] is expected[name],
                 'Minimum-fleet condition mismatch: '+name)
    for name in ('service_energy','usable_initial_above_reserve'):
        _require(_q(actual[name]) == expected[name], 'Minimum-fleet energy mismatch: '+name)
    _require(actual['consecutive_connections'] == expected['consecutive_connections'],
             'Minimum-fleet consecutive-connection proof mismatch')
    overlap = actual['overlap_counts']
    _require(isinstance(overlap,list) and len(overlap) == len(expected['overlap_counts']),
             'Minimum-fleet overlap proof count mismatch')
    for a,e in zip(overlap,expected['overlap_counts']):
        _require(_q(a['time']) == e['time'] and _integer(a['count']) and a['count'] == e['count'],
                 'Minimum-fleet half-open overlap proof mismatch')


def _json_exact(value):
    if isinstance(value,Fraction):
        return str(value)
    if isinstance(value,dict):
        return {name:_json_exact(item) for name,item in value.items()}
    if isinstance(value,(list,tuple)):
        return [_json_exact(item) for item in value]
    return value


def _indexed_terms(terms,index_to_name):
    _require(isinstance(terms,(list,tuple)), 'Malformed indexed coefficient list')
    output = {}
    for term in terms:
        _require(isinstance(term,(list,tuple)) and len(term) == 2, 'Malformed coefficient pair')
        index,value = term
        _require(_integer(index) and index in index_to_name, 'Unknown coefficient variable index')
        name = index_to_name[index]
        output[name] = output.get(name,Fraction(0))+_q(value)
    return {name:value for name,value in output.items() if value}


def _ledger(ledger,variables,rows,intervals,operations,loads,method,prices,fleet_proof):
    _require(isinstance(ledger,dict) and ledger.get('schema') == 'exact-per-leg-perspective-energy-flow-v1',
             'Unknown exact ledger schema')
    exported = ledger['variables']
    _require(isinstance(exported,list) and len(exported) == len(variables), 'Variable count mismatch')
    index_to_name = {}
    names = set()
    for position,v in enumerate(exported):
        index,name = v['index'],v['name']
        _require(_integer(index) and index == position and name in variables and name not in names,
                 'Variable index/name mismatch')
        _require(v['kind'] == 'C' and (_q(v['lower']),_q(v['upper'])) == variables[name],
                 'Variable bound/type mismatch')
        index_to_name[index] = name
        names.add(name)
    exported_rows = ledger['rows']
    _require(isinstance(exported_rows,list) and len(exported_rows) == len(rows), 'Row count mismatch')
    order,seen = [],set()
    for position,r in enumerate(exported_rows):
        name = r['name']
        _require(_integer(r['index']) and r['index'] == position and name in rows and name not in seen,
                 'Row index/name mismatch')
        actual = (r['sense'],_q(r['rhs']),_indexed_terms(r['coefficients'],index_to_name))
        _require(actual == rows[name], 'Semantic row mismatch: '+name)
        order.append(name)
        seen.add(name)
    exported_intervals = ledger['intervals']
    _require(len(exported_intervals) == len(intervals), 'Interval count mismatch')
    for actual,expected in zip(exported_intervals,intervals):
        _require(_integer(actual['index']) and _integer(actual['period']), 'Malformed interval indices')
        for key in ('index','period','visits'):
            _require(actual[key] == expected[key], 'Interval semantic mismatch: '+key)
        for key in ('start','end','rate','capacity'):
            _require(_q(actual[key]) == expected[key], 'Interval exact coefficient mismatch: '+key)
    _require(_indexed_terms(ledger['operating_cost'],index_to_name) == operations,
             'Operating-cost mapping mismatch')
    _check_fleet_proof(ledger['minimum_fleet_proof'],fleet_proof)
    objective = ledger['objective']
    _require(objective['method'] == method and _q(objective['constant']) == 0,
             'Objective method/constant mismatch')
    aa = [Fraction(float(.2))]*len(loads) if method == 'miqp' else prices
    bb = [Fraction(float(1/900))]*len(loads) if method == 'miqp' else [Fraction(0)]*len(loads)
    expected_linear = dict(operations)
    for name,a in zip(loads,aa):
        expected_linear[name] = expected_linear.get(name,Fraction(0))+a
    expected_linear = {n:v for n,v in expected_linear.items() if v}
    _require(_indexed_terms(objective['linear'],index_to_name) == expected_linear,
             'Objective linear coefficient mismatch')
    actual_quadratic = {}
    for term in objective['quadratic']:
        _require(isinstance(term,(list,tuple)) and len(term) == 3, 'Malformed quadratic term')
        i,j,value = term
        _require(_integer(i) and _integer(j) and i in index_to_name and j in index_to_name,
                 'Unknown quadratic variable index')
        names2 = tuple(sorted((index_to_name[i],index_to_name[j])))
        actual_quadratic[names2] = actual_quadratic.get(names2,Fraction(0))+_q(value)
    actual_quadratic = {k:v for k,v in actual_quadratic.items() if v}
    expected_quadratic = {(n,n):b/2 for n,b in zip(loads,bb) if b}
    _require(actual_quadratic == expected_quadratic, 'Objective quadratic coefficient mismatch')
    return order,aa,bb


def verify_and_bound(case_dict,result):
    """Return a checked lower bound or an explicit stage-specific rejection.

    Missing Pi is an explicit unavailable outcome. A deliberately supplied
    all-zero vector is valid, but is never silently substituted for absent
    native evidence. Malformed Pi is rejected. Linear results require explicit prices
    vector; prices are never inferred from the objective being checked.
    """
    stage = 'CASE_SEMANTICS'
    try:
        variables,rows,intervals,operations,loads,fleet_proof = _reconstruct(case_dict)
        stage = 'PROPOSAL_CONFIGURATION'
        _require(isinstance(result,dict) and result.get('continuous') is True,
                 'Requires the continuous energy-flow relaxation result')
        method = result.get('method')
        _require(method in ('miqp','linear'), 'Unsupported objective method')
        prices = None
        if method == 'linear':
            _require(isinstance(result.get('prices'),(list,tuple)) and len(result['prices']) == len(loads),
                     'Explicit admitted prices are required for linear objective reconstruction')
            prices = list(map(_q,result['prices']))
        stage = 'LEDGER_MATCH'
        order,aa,bb = _ledger(result['exactledger'],variables,rows,intervals,operations,loads,method,prices,fleet_proof)
        stage = 'TANGENT_PROPOSAL'
        if method == 'miqp':
            proposed = result.get('tangent_loads')
            if proposed is None:
                proposed = result.get('candidate',{}).get('load')
            if proposed is None:
                tangent = [Fraction(0)]*len(loads)
                tangent_source = 'missing_proposal_zero_tangent'
            else:
                _require(isinstance(proposed,(list,tuple)) and len(proposed) == len(loads),
                         'Tangent proposal dimension mismatch')
                tangent = list(map(_q,proposed))
                tangent_source = 'explicit_or_native_loads_exact_binary_fraction_no_feasibility_assumed'
        else:
            tangent = [Fraction(0)]*len(loads)
            tangent_source = 'linear_objective_no_tangent'
        slopes = [a+b*v for a,b,v in zip(aa,bb,tangent)]
        constant = -sum((b*v*v/2 for b,v in zip(bb,tangent)),Fraction(0))
        objective = dict(operations)
        for name,slope in zip(loads,slopes):
            objective[name] = objective.get(name,Fraction(0))+slope
        stage = 'DUAL_PROPOSAL'
        proposal = result.get('Pi')
        if proposal is None:
            return dict(status='CERTIFICATE_UNAVAILABLE',stage='DUAL_PROPOSAL',
                        reason='No Pi proposal supplied; no automatic zero fallback',
                        semantic_validation='PASS',ledger_match='PASS',lower_bound=None,
                        native_status_used=False,native_optimality_claim=False,
                        physical_candidate_verified=False)
        _require(isinstance(proposal,(list,tuple)) and len(proposal) == len(order),
                 'Multiplier dimension mismatch')
        proposal_source = 'supplied_Pi_proposal_only'
        residual = {name:objective.get(name,Fraction(0)) for name in variables}
        dual_rhs,projected_count = Fraction(0),0
        multipliers = []
        for name,raw in zip(order,proposal):
            proposed_y = _q(raw)
            sense,rhs,coefficients = rows[name]
            y = max(Fraction(0),proposed_y) if sense == '>=' else min(Fraction(0),proposed_y) if sense == '<=' else proposed_y
            projected_count += int(y != proposed_y)
            dual_rhs += y*rhs
            for variable,coefficient in coefficients.items():
                residual[variable] -= coefficient*y
            multipliers.append(dict(row=name,proposal=str(proposed_y),value=str(y),sense=sense))
        stage = 'EXACT_BOUND'
        compensation,terms = Fraction(0),[]
        for name,(lower,upper) in variables.items():
            value = residual[name]
            endpoint = lower if value >= 0 else upper
            term = value*endpoint
            compensation += term
            terms.append(dict(variable=name,lower=str(lower),upper=str(upper),
                              residual=str(value),chosen_endpoint=str(endpoint),term=str(term)))
        bound = constant+dual_rhs+compensation
        return dict(status='CERTIFIED_LOWER_BOUND',semantic_validation='PASS',ledger_match='PASS',
            target=('binary_stored_quadratic_physical_and_complete_fleet_hull_lower_bound'
                    if method == 'miqp' else 'explicit_price_complete_fleet_response_lower_bound'),
            lower_bound=str(bound),objective_tangent_constant=str(constant),
            L_CH=str(bound) if method == 'miqp' else None,
            L_D=str(bound) if method == 'miqp' else None,
            V_lower=str(bound) if method == 'linear' else None,
            relaxation='continuous_per_leg_perspective_energy_flow_not_complete_fleet_hull_equality',
            dual_rhs_sum=str(dual_rhs),box_residual_compensation=str(compensation),
            tangent_source=tangent_source,tangent_loads=list(map(str,tangent)),
            market_a=list(map(str,aa)),market_b=list(map(str,bb)),
            tangent_slopes=list(map(str,slopes)),proposal_source=proposal_source,
            sign_projected_rows=projected_count,multipliers=multipliers,residual_terms=terms,
            counts=dict(variables=len(variables),rows=len(rows),intervals=len(intervals),loads=len(loads)),
            minimum_fleet_proof=_json_exact(fleet_proof),
            arithmetic='Exact Fraction; floats interpreted as their binary rationals; no denominator limiting',
            native_status_used=False,native_optimality_claim=False,physical_candidate_verified=False,
            hull_relaxation_not_equality=True,
            proof='tangent <= objective; sign-valid y; LB=k+y.rhs+sum_j min(residual_j*l_j,residual_j*u_j)',
            limitations='Conditional on supplied admitted case descriptor; not an independent source-data provenance audit')
    except (_Reject,KeyError,TypeError,IndexError,AttributeError,ValueError,OverflowError) as exc:
        return dict(status='REJECTED',stage=stage,reason=str(exc),lower_bound=None,
                    native_status_used=False,native_optimality_claim=False,
                    physical_candidate_verified=False)
