"""Classical native diagnostics; no exact or physical certificate is claimed.

Backend imports occur only on explicit build. Every original movement and bus
count is retained. Default starts are cold. Each build is for one diagnostic.
"""
import json
import math
from pathlib import Path
import time


def _emit(record, event):
    if record is not None:
        record(event)


def _linear(gp, expression, variables):
    return gp.LinExpr([float(c) for c in expression.expr.values()],
                      [variables[v.idx] for v in expression.expr])+float(expression.const)


def build(case, continuous=False):
    """Translate the existing compact GRB matrix without an MPS round trip.

    Continuous relaxation changes every binary/integer variable to continuous,
    retaining its original bounds. The source model is retained for provenance.
    """
    started = time.monotonic()
    import gurobipy as gp
    from egglab import native_pathflow as pf
    source = pf.build_feasible_model(case, backend='GRB')
    model = gp.Model('public-depot15-classical-probe')
    model.Params.OutputFlag = 0
    model.Params.Threads = 1
    model.Params.FeasibilityTol = 1e-8
    model.Params.OptimalityTol = 1e-8
    model.Params.IntFeasTol = 1e-8
    model.Params.MIPGap = 0
    model.Params.MIPGapAbs = 0
    variables = [model.addVar(lb=float(v.lb), ub=float(v.ub),
                 vtype=gp.GRB.CONTINUOUS if continuous else v.var_type,
                 name='v'+str(v.idx)) for v in source['model'].vars]
    model.update()
    rows = []
    for i, constraint in enumerate(source['model'].constrs):
        expression = constraint.expr
        lhs = _linear(gp, expression, variables)
        sense = expression.sense
        name = 'r'+str(i)
        if sense in ('<', '<='):
            model.addConstr(lhs <= 0, name=name)
        elif sense in ('>', '>='):
            model.addConstr(lhs >= 0, name=name)
        elif sense in ('=', '=='):
            model.addConstr(lhs == 0, name=name)
        else:
            raise ValueError('Unknown source row sense: '+str(sense))
        rows.append(dict(name=name, sense=sense, constant=float(expression.const),
                         coefficients=[(v.idx,float(c)) for v,c in expression.expr.items()]))
    model.update()
    mapped = lambda items: [variables[v.idx] for v in items]
    return dict(model=model, gp=gp, case=case, source=source, variables=variables,
                selection=mapped(source['x']), loads=mapped(source['loads']),
                soc_before=mapped(source['soc_before']), soc_after=mapped(source['soc_after']),
                charge={key:variables[v.idx] for key,v in source['charge'].items()},
                ops=_linear(gp,source['ops'],variables), rows=rows, oa_rows=[],
                source_ops=dict(constant=float(source['ops'].const),
                    coefficients=[(v.idx,float(c)) for v,c in source['ops'].expr.items()]),
                load_variable_indices=[v.idx for v in source['loads']],
                source_variable_names=[v.name for v in source['model'].vars],
                matrix_revision=0, objective_mapping=None,
                continuous=bool(continuous), started=started,
                build_elapsed_s=time.monotonic()-started, consumed=False)


def _market(built, a, b):
    n = len(built['loads'])
    # Exactly the Python binary-stored coefficients used by the original cell.
    aa = [float(.2)]*n if a is None else [float(v) for v in a]
    bb = [float(1/900)]*n if b is None else [float(v) for v in b]
    if len(aa) != n or len(bb) != n or any(not math.isfinite(v) for v in aa+bb) or any(v < 0 for v in bb):
        raise ValueError('Invalid convex market')
    return aa, bb


def _begin(built, seconds, record, start):
    if built['consumed']:
        raise ValueError('Build a fresh model for each diagnostic')
    built['consumed'] = True
    if not math.isfinite(seconds) or seconds <= 0 or seconds > 300:
        raise ValueError('Require 0 < seconds <= 300')
    deadline = built['started']+seconds
    if start is not None:
        if built['continuous'] or set(start) != {'selected_movement_ids'}:
            raise ValueError('Only integer movement-selection starts are supported')
        selected = start['selected_movement_ids']
        from egglab.native_pathflow import recover_paths
        recover_paths(built['case'],selected)
        selected = set(selected)
        for movement, variable in zip(built['case'].movements,built['selection']):
            variable.Start = 1.0 if movement.id in selected else 0.0
        # Every SOC, charge and load start remains Gurobi UNDEFINED. Admission
        # of a complete path cover does not establish native start acceptance.
    built['start_policy'] = 'cold' if start is None else 'common-movement-binary-start'
    _emit(record, dict(event='begin', continuous=built['continuous'],
          build_elapsed_s=built['build_elapsed_s'], seconds=seconds,
          start_policy=built['start_policy'], native_start_acceptance='UNKNOWN',
          start_values=start, formulation=built['source']['formulation']))
    return deadline


def _optimize(built, deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        return False
    built['model'].Params.TimeLimit = remaining
    built['model'].optimize()
    return True


def _objective_mapping(built, additions, quadratic_diagonal=()):
    """Explicit binary-float objective, indexed against the exported variables.

    The diagonal convention is one half times the listed coefficient times
    the squared variable, matching the market b rather than b/2.
    """
    linear = dict(built['source_ops']['coefficients'])
    for index, coefficient in additions:
        linear[index] = linear.get(index,0.0)+float(coefficient)
    built['objective_mapping'] = dict(
        sense='minimize', constant=built['source_ops']['constant'],
        linear_coefficients=sorted(linear.items()),
        quadratic_diagonal=list(quadratic_diagonal),
        convention='constant + sum(linear_i*x_i) + 0.5*sum(diagonal_i*x_i^2)',
        arithmetic='binary-float diagnostic coefficients; not ideal rational inputs')
    built['matrix_revision'] += 1


def _bound_value(value):
    value = float(value)
    return value if math.isfinite(value) else ('+infinity' if value > 0 else '-infinity')


def _no_optimize(reason):
    """No native status is inferred when optimize was never called."""
    return dict(raw_status=None, solution_count=0, runtime_s=None,
                raw_objective=None, raw_bound=None, raw_gap=None, node_count=None,
                optimization_called=False, diagnostic_outcome=reason,
                native_only=True, physical_feasibility='unverified', exact_certificate=False)


def _extract(built):
    model, case = built['model'], built['case']
    result = dict(raw_status=int(model.Status), solution_count=int(model.SolCount),
                  runtime_s=float(model.Runtime), native_only=True,
                  physical_feasibility='unverified', exact_certificate=False,
                  optimization_called=True, diagnostic_outcome='OPTIMIZED_NATIVE',
                  solved_matrix_revision=built['matrix_revision'])
    for output, attribute in [('raw_objective','ObjVal'),('raw_bound','ObjBound'),
                              ('raw_gap','MIPGap'),('node_count','NodeCount')]:
        try:
            value = float(getattr(model,attribute))
            result[output] = value if math.isfinite(value) else None
        except (AttributeError, built['gp'].GurobiError):
            result[output] = None
    if model.SolCount:
        selected = [m.id for m,v in zip(case.movements,built['selection']) if v.X > .5]
        result['candidate'] = dict(selected_movement_ids=selected,
            selection=[float(v.X) for v in built['selection']],
            charge_by_interval=[dict(movement=case.movements[j].id, interval=k, energy=float(v.X))
                                for (j,k),v in built['charge'].items()],
            load=[float(v.X) for v in built['loads']], ops=float(built['ops'].getValue()),
            soc=[dict(trip=t.id,before=float(sb.X),after=float(sa.X))
                 for t,sb,sa in zip(case.trips,built['soc_before'],built['soc_after'])],
            variable_values=[float(v.X) for v in built['variables']])
        if not built['continuous']:
            from egglab.native_pathflow import recover_paths
            try:
                paths, owners = recover_paths(case,selected)
                result['candidate']['paths'] = paths
                result['candidate']['movement_owners'] = owners
            except ValueError as exc:
                result['candidate']['path_recovery_failure'] = str(exc)
    if built['continuous'] and model.Status == built['gp'].GRB.OPTIMAL:
        result['duals'] = [dict(name=c.ConstrName, pi=float(c.Pi), slack=float(c.Slack))
                           for c in model.getConstrs()]
        result['reduced_costs'] = [dict(name=v.VarName, value=float(v.X), rc=float(v.RC),
                                       lb=_bound_value(v.LB), ub=_bound_value(v.UB), objective=float(v.Obj))
                                  for v in model.getVars()]
        result['source_linear_rows'] = built['rows']
    # Export the actual optimized formulation, not only its original rows.
    # These structures are copied so later OA additions cannot alter a saved
    # last-solved snapshot. Native bounds use the backend's own infinity encoding.
    result['solved_formulation'] = dict(
        matrix_revision=built['matrix_revision'],
        source_linear_rows=list(built['rows']), oa_cut_rows=list(built['oa_rows']),
        row_convention='sum(coefficients_i*x_i)+constant sense 0',
        objective=dict(built['objective_mapping']),
        source_operations=dict(built['source_ops']),
        load_variable_indices=list(built['load_variable_indices']),
        variables=[dict(index=i,name=v.VarName,
                        source_name=built['source_variable_names'][i]
                            if i < len(built['source_variable_names']) else None,
                        lower_bound=_bound_value(v.LB),upper_bound=_bound_value(v.UB),
                        variable_type=v.VType)
                   for i,v in enumerate(model.getVars())],
        bounds_semantics='native optimized variable bounds; finite backend infinity sentinels retained',
        native_infinity=float(built['gp'].GRB.INFINITY),
        physical_feasibility='unverified',exact_certificate=False)
    return result


def _finish(built, result, out, record):
    result.update(inclusive_elapsed_s=time.monotonic()-built['started'],
                  continuous=built['continuous'], all_bus_counts_retained=True,
                  start_policy=built['start_policy'], native_start_acceptance='UNKNOWN',
                  formulation=built['source']['formulation'],
                  interpretation='Native binary-float matrix diagnostic; independent ideal-model replay pending')
    _emit(record, dict(event='finish', method=result['method'],
                      elapsed_s=result['inclusive_elapsed_s'], raw_status=result.get('raw_status'),
                      diagnostic_outcome=result['diagnostic_outcome']))
    if out is not None:
        with Path(out).open('x') as stream:
            json.dump(result,stream,indent=2,allow_nan=False)
            stream.write('\n')
    return result


def solve(built, method='oa', seconds=300, a=None, b=None, record=None, out=None, start=None):
    """Cold OA or direct convex MIQP, sharing one inclusive build/solve cap.

    OA reuses one model for at most 32 optimize calls. Its cut lower bound and
    evaluated incumbent upper are native diagnostics, never rational proofs.
    """
    if method not in ('oa','miqp'):
        raise ValueError('Choose oa or miqp')
    aa, bb = _market(built,a,b)
    deadline = _begin(built,seconds,record,start)
    model, gp, loads = built['model'], built['gp'], built['loads']
    rounds, best_candidate, best_upper, best_bound = [], None, None, None
    best_candidate_round = best_bound_round = None
    last_snapshot = None
    model_modified_since_last_solve = True
    if method == 'miqp':
        objective = built['ops']+gp.quicksum(at*v+bt*v*v/2 for at,bt,v in zip(aa,bb,loads))
        model.setObjective(objective,gp.GRB.MINIMIZE)
        _objective_mapping(built,zip(built['load_variable_indices'],aa),
                           zip(built['load_variable_indices'],bb))
        if _optimize(built,deadline):
            last_snapshot = _extract(built)
            result = dict(last_snapshot)
            model_modified_since_last_solve = False
        else:
            result = _no_optimize('NO_OPTIMIZE_DEADLINE_EXHAUSTED')
    else:
        theta = [model.addVar(lb=-gp.GRB.INFINITY,name='cost'+str(t)) for t in range(len(loads))]
        model.setObjective(built['ops']+gp.quicksum(theta),gp.GRB.MINIMIZE)
        model.update()
        theta_indices = list(range(len(built['variables']),len(built['variables'])+len(theta)))
        _objective_mapping(built,((i,1.0) for i in theta_indices))
        points = [[0.0]*len(loads)]
        stop_reason = 'OA_ROUND_LIMIT'
        numerical_contradiction = False
        interval_closed = False
        for round_index in range(32):
            if deadline <= time.monotonic():
                stop_reason = ('NO_OPTIMIZE_DEADLINE_EXHAUSTED' if last_snapshot is None
                               else 'DEADLINE_EXHAUSTED_AFTER_SOLVED_ROUND')
                break
            point = points[-1]
            for t,(at,bt,v,q) in enumerate(zip(aa,bb,loads,point)):
                name = 'cut'+str(round_index)+'_'+str(t)
                model.addConstr(theta[t] >= (at+bt*q)*v-bt*q*q/2,
                                name=name)
                built['oa_rows'].append(dict(name=name,sense='>=',constant=bt*q*q/2,
                    coefficients=[(theta_indices[t],1.0),
                                  (built['load_variable_indices'][t],-(at+bt*q))],
                    generation_round=round_index,tangent_load=q))
            built['matrix_revision'] += 1
            model_modified_since_last_solve = True
            if not _optimize(built,deadline):
                stop_reason = ('NO_OPTIMIZE_DEADLINE_EXHAUSTED' if last_snapshot is None
                               else 'DEADLINE_EXHAUSTED_AFTER_MATRIX_MUTATION')
                break
            snapshot = _extract(built)
            last_snapshot = snapshot
            model_modified_since_last_solve = False
            bound = snapshot['raw_bound']
            if bound is not None and math.isfinite(bound):
                if best_bound is None or bound > best_bound:
                    best_bound, best_bound_round = bound, round_index
            upper = None
            if 'candidate' in snapshot:
                candidate = snapshot['candidate']
                upper = candidate['ops']+sum(at*x+bt*x*x/2 for at,bt,x in zip(aa,bb,candidate['load']))
                if best_upper is None or upper < best_upper:
                    best_upper, best_candidate = upper, candidate
                    best_candidate_round = round_index
                points.append(candidate['load'])
            interval_gap = (None if best_upper is None or best_bound is None
                            else best_upper-best_bound)
            numerical_contradiction = interval_gap is not None and interval_gap < 0
            event = dict(event='oa_round',round=round_index, upper=upper,
                         best_upper=best_upper,best_bound=best_bound,
                         best_candidate_round=best_candidate_round,
                         best_bound_round=best_bound_round,
                         raw_status=snapshot['raw_status'],
                         solution_count=snapshot['solution_count'],
                         runtime_s=snapshot['runtime_s'],
                         raw_objective=snapshot['raw_objective'],
                         raw_bound=snapshot['raw_bound'],raw_gap=snapshot['raw_gap'],
                         node_count=snapshot['node_count'],
                         solved_matrix_revision=snapshot['solved_matrix_revision'],
                         candidate_load=snapshot.get('candidate',{}).get('load'),
                         candidate_operations=snapshot.get('candidate',{}).get('ops'),
                         evaluated_nonlinear_gap=interval_gap,
                         negative_numerical_gap=numerical_contradiction,
                         raw_gap_semantics='piecewise-linear OA model, not original quadratic',
                         elapsed_s=time.monotonic()-built['started'])
            rounds.append(event)
            _emit(record,event)
            if numerical_contradiction:
                stop_reason = 'NEGATIVE_NUMERICAL_INTERVAL'
                break
            if upper is None:
                stop_reason = 'OA_NO_CANDIDATE'
                break
            if interval_gap is not None and 0 <= interval_gap <= 1e-6:
                interval_closed = True
                stop_reason = 'OA_NATIVE_INTERVAL_TOLERANCE'
                break
            if points[-1] in points[:-1]:
                stop_reason = 'OA_REPEATED_LOAD'
                break
        # A later cut attachment can invalidate live native attributes. Never
        # re-extract a mutated or never-optimized model for the final packet.
        result = dict(last_snapshot) if last_snapshot is not None else _no_optimize(stop_reason)
        result.update(oa_rounds=rounds, best_evaluated_upper=best_upper,
                      best_native_lower=best_bound, best_candidate=best_candidate,
                      best_candidate_round=best_candidate_round,best_bound_round=best_bound_round,
                      diagnostic_outcome=stop_reason,
                      native_interval_closed=interval_closed,
                      numerical_interval_contradiction=numerical_contradiction,
                      raw_final_fields_semantics='last actually solved OA model, not nonlinear optimum')
    result.update(last_solved_snapshot=last_snapshot,
                  current_matrix_revision=built['matrix_revision'],
                  model_modified_since_last_solve=model_modified_since_last_solve,
                  optimize_calls=(len(rounds) if method == 'oa' else int(last_snapshot is not None)),
                  deadline_exhausted=result['diagnostic_outcome'].startswith(
                      ('NO_OPTIMIZE_DEADLINE','DEADLINE_EXHAUSTED')),
                  final_optimization_skipped=result['diagnostic_outcome'].startswith(
                      ('NO_OPTIMIZE_DEADLINE','DEADLINE_EXHAUSTED')))
    result.update(method=method, market=dict(a=aa,b=bb,
                  semantics='binary-stored Python float coefficients'))
    return _finish(built,result,out,record)


def solve_pricing(built, prices, seconds=300, record=None, out=None, start=None):
    prices = [float(p) for p in prices]
    if len(prices) != len(built['loads']) or any(not math.isfinite(p) for p in prices):
        raise ValueError('Invalid price vector')
    deadline = _begin(built,seconds,record,start)
    built['model'].setObjective(built['ops']+built['gp'].quicksum(
        p*v for p,v in zip(prices,built['loads'])),built['gp'].GRB.MINIMIZE)
    _objective_mapping(built,zip(built['load_variable_indices'],prices))
    if _optimize(built,deadline):
        snapshot = _extract(built)
        result = dict(snapshot)
    else:
        snapshot = None
        result = _no_optimize('NO_OPTIMIZE_DEADLINE_EXHAUSTED')
    result.update(last_solved_snapshot=snapshot,
                  current_matrix_revision=built['matrix_revision'],
                  model_modified_since_last_solve=snapshot is None,
                  optimize_calls=int(snapshot is not None),
                  deadline_exhausted=snapshot is None,
                  final_optimization_skipped=snapshot is None)
    result.update(method='own-price-lp' if built['continuous'] else 'own-price-mip', prices=prices)
    return _finish(built,result,out,record)


def solve_root_qp(case, seconds=300, a=None, b=None, record=None, out=None):
    """Continuous compact relaxation, retaining all native linear rows."""
    return solve(build(case,continuous=True),method='miqp',seconds=seconds,
                 a=a,b=b,record=record,out=out)
