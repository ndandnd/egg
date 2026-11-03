"""Candidate CF1 fixed-discrete charging completion; no unrestricted bound.

The caller computes ONCE, before initial setup/build:
min(t0+.2*T, first_completion_anchor+max(2,.1*T)). That exact absolute
deadline is reused across repairs/rebuilds; a fresh now+6 or stageend alone
is not the cumulative policy. This helper cannot verify the caller anchor/T.
This module neither persists a fallback nor submits a full-search start.
"""
from copy import deepcopy
from contextlib import contextmanager, nullcontext
from fractions import Fraction
import math
import time

from egglab import native_pathflow as pf
from egglab import native_recharge as nr

POLICY = 'cf1-fixed-discrete-charging-v1'


def _row_signature(row, *, check=None):
    check = (lambda:None) if check is None else check
    check()
    expression = row.expr
    coefficients = []
    for index,(var,coefficient) in enumerate(expression.expr.items()):
        if index % 64 == 0:
            check()
        coefficients.append((var.idx,coefficient))
    signature = (row.idx,row.name,expression.sense,expression.const,tuple(sorted(coefficients)))
    check()
    return signature


def _inventory(case, built, selected, physical_rows=None, *, check=None, measure=None):
    """Repeat every physical audit; caller may bound its traversals absolutely."""
    check = (lambda:None) if check is None else check
    measure = (lambda label:nullcontext()) if measure is None else measure
    check()
    model = built['model']
    identity = case.identity()
    if built['physical_identity'] != identity or built['compiled']['identity'] != identity:
        raise ValueError('Fixed charging model identity mismatch')
    count = built['constraint_count_before_objective']
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError('Invalid physical row inventory')
    with measure('rows'):
        rows = tuple(_row_signature(row,check=check) for row in model.constrs[:count])
        if len(rows) != count or model.num_rows != len(model.constrs):
            raise ValueError('Missing physical constraints')
        if physical_rows is None and model.num_rows != count:
            raise ValueError('Unexpected objective rows before fixed charging')
        if physical_rows is not None and rows != physical_rows:
            raise ValueError('Physical rows changed during fixed charging')
    with measure('variables'):
        variables,indices,lookup = [],[],{}
        for var in model.vars:
            check()
            variables.append(var)
            indices.append(var.idx)
            lookup[var.idx] = var
        x,mapped = [],[]
        for var in built['x']:
            check()
            x.append(var)
            mapped.append(var.idx)
        mapped_set = set(mapped)
        if len(indices) != len(lookup) or len(x) != len(case.movements) or len(mapped) != len(mapped_set):
            raise ValueError('Movement variable mapping is not one-to-one')
    with measure('bounds'):
        movement_ids,fixed_values = [],[]
        for movement,var in zip(case.movements,x):
            check()
            if var.idx not in lookup or lookup[var.idx] is not var or str(var.var_type) != 'B':
                raise ValueError('Missing/nonbinary movement variable')
            expected = int(movement.id in selected)
            if physical_rows is None and (var.lb != 0 or var.ub != 1):
                raise ValueError('Original full movement bounds are not binary0/1')
            if physical_rows is not None and (var.lb != expected or var.ub != expected):
                raise ValueError('Fixed movement bounds changed')
            movement_ids.append(movement.id)
            fixed_values.append(expected)
    with measure('unmapped'):
        unmapped = []
        for var in variables:
            check()
            if var.idx not in mapped_set:
                if str(var.var_type) != 'C':
                    raise ValueError('Unmapped discrete variable in charging model')
                unmapped.append(var.idx)
    with measure('ledger'):
        result = {'case_identity':identity,'physical_constraints':count,
            'physical_rows_preserved':True,'movement_ids':movement_ids,
            'mapped_binary_indices':mapped,'fixed_values':fixed_values,
            'remaining_variable_indices':unmapped,
            'all_unfixed_continuous':True,'native_lp_certified':False,
            'subproblem':'fixed-discrete charging; binary types retained',
            'variable_count':len(variables),'constraint_count':model.num_rows}
    check()
    return rows,result


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
              'preparation_timings':[],
              'repair_allowed':False,'global_lower_bound':None,'native_lp_certified':False,
              'deadline_policy':'caller-fixed-cumulative-window; not independently qualified',
              'deadline':deadline if nr._finite(deadline,-math.inf) else None}
    stage = 'validation'
    last_clock = None
    best_bill = None

    def observe():
        nonlocal last_clock
        at = clock()
        if isinstance(at,bool) or not isinstance(at,(int,float)) or not math.isfinite(at):
            raise ValueError('Invalid monotonic clock')
        if last_clock is not None and at < last_clock:
            raise ValueError('Monotonic clock moved backwards')
        last_clock = at
        return at

    def check():
        at = observe()
        if at >= deadline:
            raise TimeoutError('Shared fixed charging deadline exhausted')
        return at

    @contextmanager
    def measure(label):
        # Retained locally even when the deadline prohibits another record call.
        row = {'stage':label,'deadline':result['deadline']}
        result['preparation_timings'].append(row)
        try:
            row['started_monotonic'] = observe()
            if row['started_monotonic']>=deadline:
                raise TimeoutError('Shared fixed charging deadline exhausted')
            yield
            check()
        except Exception as exc:
            row['error'] = {'error_type':type(exc).__name__,'error':str(exc)}
            raise
        finally:
            try:
                end = observe()
                row['finished_monotonic'] = end
                if 'started_monotonic' in row:
                    row['elapsed_s'] = end-row['started_monotonic']
                row['completed_before_deadline'] = 'error' not in row and end<deadline
            except Exception as exc:
                row['clock_error'] = {'error_type':type(exc).__name__,'error':str(exc)}
                row['completed_before_deadline'] = False
                if 'error' not in row:
                    raise

    inventory_count = 0

    def inventory(physical_rows=None):
        nonlocal inventory_count
        label = 'inventory'+str(inventory_count)
        inventory_count += 1
        with measure(label):
            return _inventory(case,built,selected,physical_rows,check=check,
                              measure=lambda part:measure(label+'.'+part))

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
        with measure('validation'):
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
        stage = 'model_build'
        with measure('model_build'):
            built = pf.build_feasible_model(case,budget.backend)
        stage = 'inventory'
        physical_rows, _ = inventory()
        with measure('binary_fix'):
            for movement,var in zip(case.movements,built['x']):
                check()
                value = int(movement.id in selected)
                var.lb = value
                var.ub = value
        _,result['inventory'] = inventory(physical_rows)
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
            _,result['inventory'] = inventory(physical_rows)
            emit({'event':'fixed_topology_solve','stage':stage,'round':index,'deadline':deadline,
                  'objective':'zero' if index == 0 else 'target_tangent',
                  'tangents':None if index == 0 else deepcopy(tangents)})
            stats = pf._optimize_once(built,budget,deadline)
            check()
            _,result['inventory'] = inventory(physical_rows)
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
            _,result['inventory'] = inventory(physical_rows)
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
                _,result['inventory'] = inventory(physical_rows)
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
