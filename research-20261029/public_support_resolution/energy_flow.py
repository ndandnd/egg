"""Per-leg perspective energy flow with a separate exact rational row ledger.

The direct Gurobi model rounds ledger coefficients to native floats. Its results
are diagnostics, not exact bounds or physical certificates. Imports of Gurobi
and model source occur only when build is explicitly called.
"""
from fractions import Fraction as Q
import json
import math
from pathlib import Path
import time


def _q(value):
    if isinstance(value,bool):
        raise ValueError('Boolean numerical coefficient')
    return Q(value)


def _emit(record, value):
    if record is not None:
        record(value)


def minimum_fleet_proof(case):
    """Derive semantic lower bounds from source coefficients, never old results.

    Services occupy half-open intervals. If one bus must serve chronologically
    disjoint services, its consecutive links must exist; if every such option
    is direct it cannot recharge between services. Nonnegative leg consumption
    then makes service energy exceeding B-reserve alone an obstruction.
    """
    services = sorted(case.trips,key=lambda t:(_q(t.start_min),_q(t.end_min),str(t.id)))
    starts = sorted({_q(t.start_min) for t in services})
    overlaps = [dict(time=t,count=sum(_q(s.start_min) <= t < _q(s.end_min) for s in services)) for t in starts]
    simultaneous = max((row['count'] for row in overlaps),default=0)
    lower = max(1,simultaneous)
    disjoint = all(_q(a.end_min) <= _q(b.start_min) for a,b in zip(services,services[1:]))
    consecutive = []
    if disjoint:
        for a,b in zip(services,services[1:]):
            modes = [m for m in case.movements if m.before == a.id and m.after == b.id]
            consecutive.append(dict(before=a.id,after=b.id,
                                    movement_ids=[m.id for m in modes],kinds=[m.kind for m in modes]))
    missing = disjoint and any(not row['movement_ids'] for row in consecutive)
    direct_only = disjoint and all(row['movement_ids'] and all(kind == 'direct' for kind in row['kinds'])
                                   for row in consecutive)
    service_energy = sum((_q(t.energy_kwh) for t in services),Q(0))
    usable = _q(case.battery_kwh)-_q(case.reserve_kwh)
    energy_obstruction = direct_only and service_energy > usable
    if missing or energy_obstruction:
        lower = max(lower,2)
    return dict(minimum_fleet=lower,half_open_overlap_bound=simultaneous,
                overlap_counts=overlaps,chronologically_disjoint=disjoint,
                consecutive_connections=consecutive,missing_consecutive_connection=missing,
                all_consecutive_options_direct=direct_only,service_energy=service_energy,
                usable_initial_above_reserve=usable,no_recharge_energy_obstruction=energy_obstruction,
                assumptions='mandatory positive-duration services; nonnegative per-leg energy; full initial inventory; no pullout/direct charging')


class _Assembly:
    def __init__(self,gp,model,continuous):
        self.gp,self.model,self.continuous = gp,model,continuous
        self.variables,self.rows,self.native = [],[],[]

    def variable(self,name,lower,upper,binary=False):
        lower,upper = _q(lower),_q(upper)
        if lower > upper:
            raise ValueError('Inverted variable bound')
        index = len(self.variables)
        kind = 'B' if binary and not self.continuous else 'C'
        self.variables.append(dict(index=index,name=name,lower=lower,upper=upper,kind=kind))
        self.native.append(self.model.addVar(lb=float(lower),ub=float(upper),vtype=kind,name=name))
        return index

    def row(self,name,terms,sense,rhs):
        coefficients = {}
        for index,value in terms:
            coefficients[index] = coefficients.get(index,Q(0))+_q(value)
        coefficients = sorted((i,c) for i,c in coefficients.items() if c)
        rhs = _q(rhs)
        expression = self.gp.LinExpr([float(c) for _,c in coefficients],
                                   [self.native[i] for i,_ in coefficients])
        if sense == '=':
            constraint = self.model.addConstr(expression == float(rhs),name=name)
        elif sense == '<=':
            constraint = self.model.addConstr(expression <= float(rhs),name=name)
        elif sense == '>=':
            constraint = self.model.addConstr(expression >= float(rhs),name=name)
        else:
            raise ValueError('Invalid row sense')
        self.rows.append(dict(index=len(self.rows),name=name,sense=sense,
                              coefficients=coefficients,rhs=rhs))
        return constraint


def build(case,continuous=False):
    """Build all declared arcs and fleet counts; every variable has finite bounds.

    The clock starts before lazy imports and source compilation. The source
    partition is compiled once; its interval indices are retained, while every
    resource capacity is independently recomputed with exact rational arithmetic.
    """
    started = time.monotonic()
    import gurobipy as gp
    from egglab import native_recharge as nr
    compiled = nr.compile_case(case)
    model = gp.Model('public-depot15-per-leg-energy-flow')
    model.Params.OutputFlag = 0
    model.Params.Threads = 1
    model.Params.FeasibilityTol = 1e-8
    model.Params.OptimalityTol = 1e-8
    model.Params.IntFeasTol = 1e-8
    model.Params.MIPGap = 0
    model.Params.MIPGapAbs = 0
    assembly = _Assembly(gp,model,bool(continuous))
    B,reserve,eta = _q(case.battery_kwh),_q(case.reserve_kwh),_q(case.efficiency)
    if not (B > 0 and 0 <= reserve <= B and eta > 0):
        raise ValueError('Invalid inventory parameters')
    intervals = []
    for k,interval in enumerate(compiled['intervals']):
        left,right = _q(interval['start']),_q(interval['end'])
        resources = [r for r in case.resources if _q(r.start_min) <= left and right <= _q(r.end_min)]
        if len(resources) != 1 or resources[0].connectors not in (0,1):
            raise ValueError('Single shared connector with unique resource coverage required')
        resource = resources[0]
        rate = min(_q(resource.per_bus_kw),_q(resource.grid_kw)) if resource.connectors else Q(0)
        cap = rate*(right-left)/60
        if cap < 0:
            raise ValueError('Negative resource capacity')
        intervals.append(dict(index=k,start=left,end=right,rate=rate,capacity=cap,
                              period=interval['period'],visits=list(interval['visits'])))
    y = [assembly.variable('y'+str(j),0,1,binary=True) for j in range(len(case.movements))]
    charge = {}
    for j,movement in enumerate(case.movements):
        for interval in intervals:
            if movement.id in interval['visits'] and interval['capacity'] > 0:
                k,cap = interval['index'],interval['capacity']
                variable = assembly.variable('q'+str(j)+'_'+str(k),0,cap)
                charge[j,k] = variable
                assembly.row('charge_selection_'+str(j)+'_'+str(k),[(variable,1),(y[j],-cap)],'<=',0)
    for interval in intervals:
        k = interval['index']
        assembly.row('shared_'+str(k),[(v,1) for (j,kk),v in charge.items() if kk == k],
                     '<=',interval['capacity'])
    entries,exits,states = [],[],[]
    for j,movement in enumerate(case.movements):
        owned = [(v,eta) for (jj,k),v in charge.items() if jj == j]
        local = []
        def state(suffix):
            index = assembly.variable('s'+str(j)+'_'+suffix,0,B)
            assembly.row('headroom_'+str(j)+'_'+suffix,[(index,1),(y[j],-B)],'<=',0)
            assembly.row('reserve_'+str(j)+'_'+suffix,[(index,1),(y[j],-reserve)],'>=',0)
            local.append(index)
            return index
        current = state('entry')
        entries.append(current)
        if movement.kind == 'pullout':
            assembly.row('full_start_'+str(j),[(current,1),(y[j],-B)],'=',0)
        for leg_index,leg in enumerate(movement.legs):
            if movement.kind == 'depot' and leg_index == movement.depot_split:
                after = state('depot_departure')
                assembly.row('depot_charge_'+str(j),[(after,1),(current,-1)]+[(v,-c) for v,c in owned],'=',0)
                current = after
            after = state('leg'+str(leg_index)+'_arrival')
            assembly.row('leg_'+str(j)+'_'+str(leg_index),
                         [(after,1),(current,-1),(y[j],_q(leg.energy_kwh))],'=',0)
            current = after
        if movement.kind == 'pullin':
            after = state('terminal_full')
            assembly.row('terminal_charge_'+str(j),[(after,1),(current,-1)]+[(v,-c) for v,c in owned],'=',0)
            assembly.row('full_end_'+str(j),[(after,1),(y[j],-B)],'=',0)
            current = after
        exits.append(current)
        states.append(local)
    starts = [y[j] for j,m in enumerate(case.movements) if m.kind == 'pullout']
    ends = [y[j] for j,m in enumerate(case.movements) if m.kind == 'pullin']
    fleet_proof = minimum_fleet_proof(case)
    assembly.row('fleet_limit',[(v,1) for v in starts],'<=',case.max_vehicles)
    assembly.row('derived_minimum_fleet',[(v,1) for v in starts],'>=',fleet_proof['minimum_fleet'])
    assembly.row('fleet_balance',[(v,1) for v in starts]+[(v,-1) for v in ends],'=',0)
    for i,trip in enumerate(case.trips):
        incoming = [j for j,m in enumerate(case.movements) if m.after == trip.id]
        outgoing = [j for j,m in enumerate(case.movements) if m.before == trip.id]
        assembly.row('cover_in_'+str(i),[(y[j],1) for j in incoming],'=',1)
        assembly.row('cover_out_'+str(i),[(y[j],1) for j in outgoing],'=',1)
        assembly.row('service_energy_'+str(i),[(exits[j],1) for j in incoming]+
                     [(entries[j],-1) for j in outgoing],'=',_q(trip.energy_kwh))
    loads = []
    for t in range(len(case.market_edges_min)-1):
        cap = sum((interval['capacity'] for interval in intervals if interval['period'] == t),Q(0))
        variable = assembly.variable('load'+str(t),0,cap)
        loads.append(variable)
        assembly.row('market_load_'+str(t),[(variable,1)]+
                     [(v,-1) for (j,k),v in charge.items() if intervals[k]['period'] == t],'=',0)
    ops = []
    for j,movement in enumerate(case.movements):
        cost = _q(case.vehicle_cost) if movement.kind == 'pullout' else Q(0)
        cost += _q(case.deadhead_cost_per_min)*sum(
            (_q(leg.arrive_min)-_q(leg.depart_min) for leg in movement.legs),Q(0))
        if cost:
            ops.append((y[j],cost))
    model.update()
    ledger = dict(schema='exact-per-leg-perspective-energy-flow-v1',
                  variables=assembly.variables,rows=assembly.rows,objective=None,
                  intervals=intervals,operating_cost=ops,
                  minimum_fleet_proof=fleet_proof,
                  arithmetic='Fraction of each stored source coefficient; no summed-energy rows',
                  native_interpretation='Each ledger coefficient and bound is separately converted to float')
    return dict(case=case,gp=gp,model=model,assembly=assembly,ledger=ledger,
                y=y,entries=entries,exits=exits,states=states,charge=charge,loads=loads,
                ops=ops,continuous=bool(continuous),started=started,consumed=False,
                build_elapsed_s=time.monotonic()-started)


def _attribute(model,name):
    try:
        value = float(getattr(model,name))
        return value if math.isfinite(value) else None
    except (AttributeError,RuntimeError):
        return None


def _encode(value):
    if isinstance(value,Q):
        return str(value)
    raise TypeError(type(value).__name__)


def solve(built,method='miqp',seconds=300,prices=None,startmovementids=None,
          record=None,out=None):
    """One native optimization; same inclusive build/solve clock, no retries.

    Continuous optimal solves export Pi/RC, but exact bound validity must be
    reconstructed independently against exactledger and its finite bounds.
    """
    if built['consumed']:
        raise ValueError('Build a fresh model for each diagnostic')
    if method not in ('miqp','linear') or not math.isfinite(seconds) or not 0 < seconds <= 300:
        raise ValueError('Require miqp/linear and 0 < seconds <= 300')
    built['consumed'] = True
    gp,model,assembly = built['gp'],built['model'],built['assembly']
    n = len(built['loads'])
    aa,bb = [_q(float(.2))]*n,[_q(float(1/900))]*n
    if method == 'linear':
        if prices is None or len(prices) != n:
            raise ValueError('Linear pricing requires one price per market interval')
        aa,bb = list(map(_q,prices)),[Q(0)]*n
    elif prices is not None:
        raise ValueError('Prices belong only to linear pricing')
    linear = dict(built['ops'])
    quadratic = []
    for index,a,b in zip(built['loads'],aa,bb):
        linear[index] = linear.get(index,Q(0))+a
        if b:
            quadratic.append((index,index,b/2))
    built['ledger']['objective'] = dict(linear=sorted(linear.items()),quadratic=quadratic,
                                       constant=Q(0),method=method)
    objective = gp.LinExpr([float(c) for c in linear.values()],
                          [assembly.native[i] for i in linear])
    if quadratic:
        objective = objective+gp.quicksum(float(c)*assembly.native[i]*assembly.native[j] for i,j,c in quadratic)
    model.setObjective(objective,gp.GRB.MINIMIZE)
    start_policy = 'cold'
    if startmovementids is not None:
        if built['continuous']:
            raise ValueError('Continuous root diagnostics are cold')
        chosen = set(startmovementids)
        known = {m.id for m in built['case'].movements}
        if len(chosen) != len(startmovementids) or not chosen <= known:
            raise ValueError('Unknown/duplicate movement start ID')
        for movement,index in zip(built['case'].movements,built['y']):
            assembly.native[index].Start = float(movement.id in chosen)
        start_policy = 'common-movement-binary-start'
    deadline = built['started']+seconds
    remaining = deadline-time.monotonic()
    _emit(record,dict(event='energy_flow_begin',method=method,continuous=built['continuous'],
          build_elapsed_s=built['build_elapsed_s'],remaining_s=max(0,remaining),
          start_policy=start_policy,native_start_acceptance='UNKNOWN'))
    called = remaining > 0
    if called:
        model.Params.TimeLimit = remaining
        model.optimize()
    result = dict(method=method,continuous=built['continuous'],native_only=True,
                  exact_certificate=False,physical_feasibility='unverified',
                  optimize_called=called,raw_status=int(model.Status),
                  solution_count=int(model.SolCount),start_policy=start_policy,
                  native_start_acceptance='UNKNOWN',all_bus_counts_retained=True,
                  raw_objective=None,raw_bound=None,raw_gap=None,
                  exactledger=built['ledger'],build_elapsed_s=built['build_elapsed_s'])
    if method == 'linear':
        result['prices'] = list(aa)
    else:
        result['market'] = dict(a=list(aa),b=list(bb),
                              semantics='exact rationals of original binary-stored coefficients')
    # Gurobi uses its own exception class for unavailable attributes.
    for key,attribute in [('raw_objective','ObjVal'),('raw_bound','ObjBound'),
                          ('raw_gap','MIPGap'),('runtime_s','Runtime'),('node_count','NodeCount')]:
        try:
            result[key] = _attribute(model,attribute)
        except gp.GurobiError:
            result[key] = None
    if model.SolCount:
        values = [float(v.X) for v in assembly.native]
        case = built['case']
        ops = sum(float(c)*values[i] for i,c in built['ops'])
        candidate = dict(selected_movement_ids=[m.id for m,i in zip(case.movements,built['y']) if values[i] > .5],
            selection=[values[i] for i in built['y']],
            charge_by_interval=[dict(movement=case.movements[j].id,interval=k,energy=values[i])
                                for (j,k),i in built['charge'].items()],
            load=[values[i] for i in built['loads']],ops=ops,
            soc=[dict(trip=t.id,before=sum(values[built['exits'][j]] for j,m in enumerate(case.movements) if m.after == t.id),
                      after=sum(values[built['entries'][j]] for j,m in enumerate(case.movements) if m.before == t.id))
                 for t in case.trips])
        result.update(candidate=candidate,variable_values=values)
        if built['continuous'] and model.Status == gp.GRB.OPTIMAL:
            result['Pi'] = [float(row.Pi) for row in model.getConstrs()]
            result['RC'] = [float(v.RC) for v in assembly.native]
            result['native_row_slacks'] = [float(row.Slack) for row in model.getConstrs()]
    result['inclusive_elapsed_s'] = time.monotonic()-built['started']
    result['interpretation'] = 'Rounded native solve; exact ledger and candidate require independent certification'
    _emit(record,dict(event='energy_flow_finish',method=method,raw_status=result['raw_status'],
                      inclusive_elapsed_s=result['inclusive_elapsed_s']))
    if out is not None:
        with Path(out).open('x') as stream:
            json.dump(result,stream,indent=2,default=_encode,allow_nan=False)
            stream.write('\n')
    return result
