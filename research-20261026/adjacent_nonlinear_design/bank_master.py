"""Source-only finite-bank model builder; no solver imports, I/O or optimize.

Caller supplies an empty model/API, projected/admitted columns and exact policy.
Physical replay, solver parameters, deadlines, solution admission and fees are
caller responsibilities. This builder establishes no pricing certificate.
"""
import math


def _finite(value, name, *, nonnegative=False):
    if isinstance(value, (str, bytes, bool)):
        raise ValueError(name+' must be a numeric coefficient')
    value = float(value)
    if not math.isfinite(value) or nonnegative and value < 0:
        raise ValueError(name+' must be finite'+(' and nonnegative' if nonnegative else ''))
    return value


def build(model, api, columns, *, market, load_map, station_adders,
          trip_universe, fleet_cap, plugs, grid_terminal_target,
          realized_terminal_target, mode, institution, representation='realized',
          posted_prices=None, duties=None):
    """Add one explicit relaxation or binary finite-bank model, never solve it.

    columns are plain dicts from column_contract.project_column. load_map has
    rows in market-period order, columns in station-major/hour-minor order;
    station_adders use that same column order. AffineMarket provides a,b,U.
    Both terminal targets remain constraints in either representation.
    """
    if mode not in ('relaxation', 'binary') or institution not in ('system', 'strategic', 'posted'):
        raise ValueError('Explicit supported mode and institution required')
    if representation not in ('realized', 'grid'):
        raise ValueError('Primary realized or explicit grid diagnostic required')
    if type(fleet_cap) is not int or fleet_cap <= 0:
        raise ValueError('Positive integer fleet CAP required; not exact N')
    columns = tuple(columns); trips = tuple(trip_universe)
    if not columns or not trips or len(set(trips)) != len(trips):
        raise ValueError('Nonempty bank and unique explicit trip universe required')
    if duties is not None:
        duties = tuple(tuple(d) for d in duties)
        flat = tuple(t for d in duties for t in d)
        if (not duties or any(not d for d in duties) or len(flat) != len(set(flat))
                or set(flat) != set(trips)):
            raise ValueError('Fixed duties must partition the declared trip universe')
    station_order = tuple(columns[0]['station_order'])
    hour_order = tuple(columns[0]['hour_order'])
    width = len(station_order)*len(hour_order)
    if not width or set(plugs) != set(station_order):
        raise ValueError('Explicit plug policy for every canonical station required')
    for station, count in plugs.items():
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError('Plug counts must be nonnegative integers or declared unlimited None')
    a = tuple(_finite(v,'market.a') for v in market.a)
    b = tuple(_finite(v,'market.b',nonnegative=True) for v in market.b)
    background = tuple(_finite(v,'market.U',nonnegative=True) for v in market.U)
    matrix = tuple(tuple(_finite(v,'load-map coefficient',nonnegative=True) for v in row) for row in load_map)
    if (not a or len(a) != len(b) or len(a) != len(background) or len(matrix) != len(a)
            or any(len(row) != width for row in matrix)):
        raise ValueError('Market vectors and explicit load-map dimensions differ')
    adders = tuple(_finite(v,'station adder') for v in station_adders)
    if len(adders) != width:
        raise ValueError('Station adders must match the declared energy basis')
    grid_target = _finite(grid_terminal_target,'grid terminal target',nonnegative=True)
    real_target = _finite(realized_terminal_target,'realized terminal target',nonnegative=True)
    if institution == 'posted':
        if posted_prices is None:
            raise ValueError('Posted objective requires separately frozen quotes')
        alpha = tuple(_finite(v,'posted quote') for v in posted_prices)
        if len(alpha) != len(a):
            raise ValueError('Posted quote dimension differs')
        quadratic = (0.,)*len(a)
    else:
        alpha = tuple(_finite(aa+bb*u,'a+bU') for aa,bb,u in zip(a,b,background))
        quadratic = tuple(bb/2 if institution == 'system' else bb for bb in b)
    ids, loads, nonenergy, occupancy = set(), [], [], {}
    for index, column in enumerate(columns):
        identity = (column['origin_id'], column['record_id'])
        if identity in ids:
            raise ValueError('Duplicate origin/record identity; no silent deduplication')
        ids.add(identity)
        if (tuple(column['station_order']) != station_order or tuple(column['hour_order']) != hour_order
                or column['vector_order'] != 'station-major/hour-minor'
                or column['minute_horizon'] != columns[0]['minute_horizon'] or column['fleet_units'] != 1):
            raise ValueError('Projected column basis/fleet conventions differ')
        service = tuple(column['trips'])
        if not service or len(set(service)) != len(service) or not set(service) <= set(trips):
            raise ValueError('Column service membership differs from partition universe')
        if duties is not None and service not in duties:
            raise ValueError('Caller must supply the complete ordered-duty subset, not other routes')
        energy = tuple(_finite(v,'column load',nonnegative=True) for v in column['load_'+representation])
        if len(energy) != width:
            raise ValueError('Projected column energy dimension differs')
        loads.append(tuple(_finite(sum(w*e for w,e in zip(row,energy)),'mapped column load',nonnegative=True) for row in matrix))
        nonenergy.append(_finite(_finite(column['ops'],'nonenergy operations')+
            sum(s*e for s,e in zip(adders,energy)),'nonenergy plus station adders'))
        _finite(column['terminal_grid_kwh'],'column grid terminal',nonnegative=True)
        _finite(column['terminal_realized_kwh'],'column realized terminal',nonnegative=True)
        for station, minute, count in column['occupancy']:
            if station not in plugs or type(minute) is not int or type(count) is not int or count <= 0:
                raise ValueError('Invalid counted occupancy projection')
            occupancy.setdefault((station,minute),[]).append((index,count))
    # Flush pending caller edits first; reject a nonempty model rather than mix rows.
    model.update()
    if model.NumVars or model.NumConstrs or model.NumQConstrs or model.NumSOS:
        raise ValueError('Caller must supply a genuinely empty model')
    weights = [model.addVar(lb=0.,ub=1.,vtype=api.GRB.BINARY if mode == 'binary' else api.GRB.CONTINUOUS,
                           name=f'column_{j}') for j in range(len(columns))]
    period_loads = [model.addVar(lb=0.,name=f'market_load_{t}') for t in range(len(a))]
    rows = dict(partition={},duties={},plugs={},load_link=[])
    for trip in trips:
        rows['partition'][trip] = model.addLConstr(api.LinExpr(
            [1. for c in columns if trip in c['trips']],
            [weights[j] for j,c in enumerate(columns) if trip in c['trips']]),api.GRB.EQUAL,1.,name=f'trip_{trip}')
    if duties is not None:
        for index,duty in enumerate(duties):
            members = [j for j,c in enumerate(columns) if tuple(c['trips']) == duty]
            rows['duties'][index] = model.addLConstr(api.LinExpr([1.]*len(members),[weights[j] for j in members]),
                api.GRB.EQUAL,1.,name=f'ordered_duty_{index}')
    rows['fleet_cap'] = model.addLConstr(api.LinExpr([1.]*len(weights),weights),
        api.GRB.LESS_EQUAL,float(fleet_cap),name='fleet_CAP_not_equality')
    rows['terminal_grid'] = model.addLConstr(api.LinExpr(
        [float(c['terminal_grid_kwh']) for c in columns],weights),api.GRB.GREATER_EQUAL,grid_target,name='grid_terminal_target')
    rows['terminal_realized'] = model.addLConstr(api.LinExpr(
        [float(c['terminal_realized_kwh']) for c in columns],weights),api.GRB.GREATER_EQUAL,real_target,name='realized_terminal_target')
    for (station,minute), entries in sorted(occupancy.items()):
        if plugs[station] is not None:
            rows['plugs'][station,minute] = model.addLConstr(api.LinExpr(
                [float(count) for j,count in entries],[weights[j] for j,count in entries]),
                api.GRB.LESS_EQUAL,float(plugs[station]),name=f'plug_{station}_{minute}')
    for t in range(len(a)):
        # L - A*E*lambda == 0: minimization equality Pi has marginal-load sign.
        rows['load_link'].append(model.addLConstr(api.LinExpr(
            [1.]+[-loads[j][t] for j in range(len(columns))],[period_loads[t]]+weights),
            api.GRB.EQUAL,0.,name=f'load_link_{t}'))
    linear = api.LinExpr(nonenergy+list(alpha),weights+period_loads)
    objective = api.QuadExpr(linear)
    for t, coefficient in enumerate(quadratic):
        if coefficient:
            objective.addTerms(coefficient,period_loads[t],period_loads[t])
    model.setObjective(objective,api.GRB.MINIMIZE)
    model.update()
    return dict(model=model,weights=weights,period_loads=period_loads,rows=rows,
        column_ids=tuple((c['origin_id'],c['record_id']) for c in columns),mode=mode,
        institution=institution,representation=representation,alpha=alpha,quadratic_coefficients=quadratic,
        station_order=station_order,hour_order=hour_order,load_map=matrix,station_adders=adders,
        mapped_column_loads=tuple(loads),linear_column_coefficients=tuple(nonenergy),
        fleet_policy='cap',duties=duties,grid_terminal_target=grid_target,realized_terminal_target=real_target,
        source_value_convention='AffineMarket incremental system or atomic bill; background constant excluded',
        dual_convention='For the solved continuous minimization only: load-link Pi is marginal load; trip Pi rewards, plug Pi nonpositive, both terminal Pi nonnegative. Caller checks numerical/KKT validity.',
        physical_validation_performed=False,optimization_performed=False,pricing_certificate_claim=False,
        scope='Retained fixed-column bank only; caller owns solve, physical admission, true-cost keeper and all bounds')
