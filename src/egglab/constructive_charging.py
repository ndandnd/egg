"""Candidate CF1 fixed-discrete charging completion; no unrestricted bound.

The caller computes ONCE, before initial setup/build:
min(t0+.2*T, first_completion_anchor+max(2,.1*T)). That exact absolute
deadline is reused across repairs/rebuilds; a fresh now+6 or stageend alone
is not the cumulative policy. This helper cannot verify the caller anchor/T.
This module neither persists a fallback nor submits a full-search start.
"""
from copy import deepcopy
from fractions import Fraction
import math
import time

from egglab import native_pathflow as pf
from egglab import native_recharge as nr

POLICY = 'cf1-fixed-discrete-charging-v1'


def _row_signature(row):
    expression = row.expr
    return (row.idx, row.name, expression.sense, expression.const,
            tuple(sorted((var.idx, coefficient) for var, coefficient in expression.expr.items())))


def _inventory(case, built, selected, physical_rows=None):
    model = built['model']
    if built['physical_identity'] != case.identity() or built['compiled']['identity'] != case.identity():
        raise ValueError('Fixed charging model identity mismatch')
    count = built['constraint_count_before_objective']
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError('Invalid physical row inventory')
    rows = tuple(_row_signature(row) for row in model.constrs[:count])
    if len(rows) != count or model.num_rows != len(model.constrs):
        raise ValueError('Missing physical constraints')
    if physical_rows is None and model.num_rows != count:
        raise ValueError('Unexpected objective rows before fixed charging')
    if physical_rows is not None and rows != physical_rows:
        raise ValueError('Physical rows changed during fixed charging')
    variables = list(model.vars)
    indices = [var.idx for var in variables]
    x = list(built['x'])
    mapped = [var.idx for var in x]
    if len(indices) != len(set(indices)) or len(x) != len(case.movements) or len(mapped) != len(set(mapped)):
        raise ValueError('Movement variable mapping is not one-to-one')
    lookup = {var.idx:var for var in variables}
    for movement,var in zip(case.movements,x):
        if var.idx not in lookup or lookup[var.idx] is not var or str(var.var_type) != 'B':
            raise ValueError('Missing/nonbinary movement variable')
        expected = int(movement.id in selected)
        if physical_rows is None and (var.lb != 0 or var.ub != 1):
            raise ValueError('Original full movement bounds are not binary0/1')
        if physical_rows is not None and (var.lb != expected or var.ub != expected):
            raise ValueError('Fixed movement bounds changed')
    unmapped = [var for var in variables if var.idx not in set(mapped)]
    if any(str(var.var_type) != 'C' for var in unmapped):
        raise ValueError('Unmapped discrete variable in charging model')
    return rows, {'case_identity':case.identity(),'physical_constraints':count,
        'physical_rows_preserved':True,'movement_ids':[m.id for m in case.movements],
        'mapped_binary_indices':mapped,'fixed_values':[int(m.id in selected) for m in case.movements],
        'remaining_variable_indices':[var.idx for var in unmapped],
        'all_unfixed_continuous':True,'native_lp_certified':False,
        'subproblem':'fixed-discrete charging; binary types retained',
        'variable_count':len(variables),'constraint_count':model.num_rows}


def complete_topology(case, selected_ids, a, b, budget, *, deadline,
                      record=None, clock=time.monotonic):
    """Return the cheapest independently replayed witness from at most 3 calls.

    Initial feasibility has zero objective; at most two target-market tangent
    objectives follow. Only initial qualified INFEASIBLE authorizes a caller's
    reverse merge repair. All returned bounds are explicitly non-global.
    """
    result = {'policy':POLICY,'status':'unresolved','plan':None,'replay':None,
              'true_bill':None,'true_bill_exact':None,'stages':[], 'inventory':None,
              'failures':[],'events':[],'reverse_repair_allowed':False,
              'repair_allowed':False,'global_lower_bound':None,'native_lp_certified':False,
              'deadline_policy':'caller-fixed-cumulative-window; not independently qualified',
              'deadline':deadline if nr._finite(deadline,-math.inf) else None}
    stage = 'validation'
    last_clock = None
    best_bill = None

    def check():
        nonlocal last_clock
        at = clock()
        if isinstance(at,bool) or not isinstance(at,(int,float)) or not math.isfinite(at):
            raise ValueError('Invalid monotonic clock')
        if last_clock is not None and at < last_clock:
            raise ValueError('Monotonic clock moved backwards')
        last_clock = at
        if at >= deadline:
            raise TimeoutError('Shared fixed charging deadline exhausted')
        return at

    def emit(event):
        check()
        event = deepcopy(event)
        result['events'].append(event)
        if record is not None:
            record(deepcopy(event))
        check()

    try:
        if isinstance(deadline,bool) or not isinstance(deadline,(int,float)) or not math.isfinite(deadline):
            raise ValueError('Finite absolute deadline required')
        check()
        nr.validate_case(case)
        nr._check_market(case,a,b)
        nr._check_budget(budget)
        # Freeze iterable inputs before native work; no mutation of caller objects.
        a,b = list(a),list(b)
        selected_ids = list(selected_ids)
        pf.recover_paths(case,selected_ids)
        selected = set(selected_ids)
        result['case_identity'] = case.identity()
        result['selected_ids'] = [m.id for m in case.movements if m.id in selected]
        check()
        stage = 'model_build'
        built = pf.build_feasible_model(case,budget.backend)
        check()
        stage = 'inventory'
        physical_rows, inventory = _inventory(case,built,selected)
        for movement,var in zip(case.movements,built['x']):
            value = int(movement.id in selected)
            var.lb = value
            var.ub = value
        _,result['inventory'] = _inventory(case,built,selected,physical_rows)
        emit({'event':'fixed_topology_inventory','policy':POLICY,**result['inventory']})
        tangents = [[(float(aa),0.)] for aa in a]
        for index in range(3):
            stage = 'feasibility' if index == 0 else 'objective'+str(index)
            check()
            if index == 0:
                built['model'].objective = 0.
            else:
                pf.attach_objective(built,'tangents',deepcopy(tangents))
            check()
            _,result['inventory'] = _inventory(case,built,selected,physical_rows)
            emit({'event':'fixed_topology_solve','stage':stage,'round':index,'deadline':deadline,
                  'objective':'zero' if index == 0 else 'target_tangent',
                  'tangents':None if index == 0 else deepcopy(tangents)})
            stats = pf._optimize_once(built,budget,deadline)
            check()
            _,result['inventory'] = _inventory(case,built,selected,physical_rows)
            scoped_stats = deepcopy(stats)
            scoped_stats['fixed_topology_lower_bound'] = scoped_stats.pop('lower_bound',None)
            scoped_stats['bound_scope'] = 'fixed topology only; never unrestricted'
            row = {'stage':stage,'round':index,'stats':scoped_stats,'witness_admitted':False}
            result['stages'].append(row)
            emit({'event':'fixed_topology_status',**row})
            if stats['status'] == 'INFEASIBLE':
                if index == 0 and stats.get('incumbent') is None:
                    result.update(status='infeasible',reverse_repair_allowed=True,repair_allowed=True)
                else:
                    raise ValueError('Objective-stage INFEASIBLE cannot authorize topology repair')
                break
            if stats['status'] not in ('OPTIMAL','FEASIBLE') or stats.get('incumbent') is None:
                result['failures'].append({'stage':stage,'error_type':'UnresolvedNativeStatus',
                    'error':'No qualified incumbent: '+str(stats['status'])})
                break
            if not nr._finite(stats['incumbent'],-math.inf):
                raise ValueError('Nonfinite fixed charging incumbent')
            stage = row['stage']+':capture'
            emit({'event':'native_incumbent','round':index,
                  'completion_policy':POLICY,**pf.capture_incumbent(case,built)})
            stage = row['stage']+':extract'
            check()
            _,result['inventory'] = _inventory(case,built,selected,physical_rows)
            plan = pf._extract(case,built,record=emit,round_index=index)
            check()
            # Extraction cannot replace independent coverage/topology and physical replay.
            actual = [mid for vehicle in plan['vehicles'] for mid in vehicle['movements']]
            if len(actual) != len(set(actual)) or set(actual) != selected:
                raise ValueError('Extracted plan changed fixed topology')
            replay = nr.replay_native(case,plan)
            check()
            if replay.get('replay_ok') is not True or len(replay['load']) != len(a):
                raise ValueError('Physical replay did not validate fixed charging')
            bill = Fraction(replay['ops_cost'])+sum(
                (Fraction(aa)*Fraction(load)+Fraction(bb)*Fraction(load)**2/2
                 for aa,bb,load in zip(a,b,replay['load'])),Fraction(0))
            if not math.isfinite(float(bill)):
                raise ValueError('Nonfinite exact physical bill')
            check()
            emit({'event':'fixed_topology_witness','round':index,'stage':row['stage'],
                  'true_bill_exact':str(bill),'true_bill':float(bill)})
            # Commit only after capture/extraction/replay/billing/recording finish in time.
            if best_bill is None or bill < best_bill:
                candidate_plan,candidate_replay = deepcopy(plan),deepcopy(replay)
                _,result['inventory'] = _inventory(case,built,selected,physical_rows)
                check()
                result.update(plan=candidate_plan,replay=candidate_replay,
                              true_bill_exact=str(bill),true_bill=float(bill),status='feasible')
                best_bill = bill
            row.update(witness_admitted=True,true_bill_exact=str(bill))
            if index == 1:
                for rows,aa,bb,load in zip(tangents,a,b,replay['load']):
                    slope = float(aa)+float(bb)*load
                    intercept = -float(bb)*load*load/2.
                    if not all(math.isfinite(v) for v in (slope,intercept)):
                        raise ValueError('Nonfinite target tangent')
                    rows.append((slope,intercept))
    except Exception as exc:
        result['failures'].append({'stage':stage,'error_type':type(exc).__name__,'error':str(exc)})
        if result['plan'] is None:
            result['status'] = 'unresolved' if isinstance(exc,TimeoutError) else 'failed'
        result['reverse_repair_allowed'] = result['repair_allowed'] = False
    return result
