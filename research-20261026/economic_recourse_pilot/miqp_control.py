"""Prospective exact-N convex MIQP, generalized from the fixed-QP copy primitive.

Gurobi variable-attribute reference:
https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html
Only LB<=-1e20 and UB>=1e20 denote unbounded sides. Other bounds stay exact.
"""
from copy import deepcopy
from fractions import Fraction
import math
import time

POLICY = 'economic-recourse-original-matrix-free-binary-exact-N-MIQP-v1'
BOUND_POLICY = 'Gurobi-LB-le-minus1e20-negative-infinity-UB-ge1e20-positive-infinity'
PARAMETERS = dict(Threads=1, Seed=17, Method=0, NodeMethod=0, NonConvex=0, MIPFocus=0,
    FeasibilityTol=1e-9, IntFeasTol=1e-9, OptimalityTol=1e-9, BarConvTol=1e-10,
    MIPGap=1e-9, MIPGapAbs=1e-6)


def _canonical(plan):
    return tuple(sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles']))


class CopyContractError(ValueError):
    """A fatal source/matrix/objective mapping inconsistency, never infeasibility."""


class _Value:
    """Only the raw .x access used by unchanged native_pathflow._extract."""
    __slots__ = ('x',)

    def __init__(self, value):
        self.x = value


def _bound_semantics(value, side):
    value = float(value)
    if side == 'LB' and value <= -1e20:
        return ('LB_negative_infinity', None)
    if side == 'UB' and value >= 1e20:
        return ('UB_positive_infinity', None)
    return ('exact_value', value)


def _bound_for_api(value, side, infinity):
    tag = _bound_semantics(value, side)[0]
    if tag == 'LB_negative_infinity':
        return -infinity
    if tag == 'UB_positive_infinity':
        return infinity
    return value


def _finite(value, name):
    value = float(value)
    if not math.isfinite(value):
        raise CopyContractError('Nonfinite '+name)
    return value


def _linear_terms(expression):
    result = {}
    for var, coefficient in expression.expr.items():
        value = _finite(coefficient, 'stored linear coefficient')
        if value != 0:
            result[var.idx] = value
    return result


def _gp_linear_terms(expression):
    result = {}
    for k in range(expression.size()):
        index = expression.getVar(k).index
        coefficient = _finite(expression.getCoeff(k), 'read-back linear coefficient')
        if coefficient == 0:
            continue
        if index in result:
            raise CopyContractError('Duplicate index in read-back linear expression')
        result[index] = coefficient
    return result


def _attribute(model, name):
    try:
        value = model.getAttr(name)
        if isinstance(value, (int, float)):
            return value if math.isfinite(value) else None
        return str(value)
    except Exception:
        return None  # Some continuous-QP status/quality/bound attributes are unavailable.


def solve(case, a, b, prior_plan, seed, native_deadline, admission_deadline, check, record=None, *, fleet_N):
    """One full-graph convex MIQP with exact N and a protected physical fallback.

    No extra QP, feasibility/completion call, private bridge or replacement decoder.
    Mixed-integer compatibility is new, not inherited fixed-QP qualification.
    """
    result = dict(policy=POLICY, plan=None, replay=None, true_bill_exact=None,
        true_bill=None, fallback_bill_exact=None, selected_source='fallback', used_fallback=True,
        miqp_success=False, miqp_candidate_admitted=False, strict_method_success=False,
        native_calls=0, native_call_attempts=0, candidate_route_changed_from_prior=None,
        retained_route_changed_from_prior=False,
        stats={}, copy_contract={}, failures=[], config_failure=False, fatal_contract=False,
        global_lower_bound=None, bound_scope='Numerical original-matrix full-declared-graph exact-N convex MIQP only',
        certificate_claim=False, native_deadline=native_deadline,
        admission_deadline=admission_deadline, admitted_monotonic=None,
        native_start=dict(kind='partial_binary_only', submitted=False, processing='UNKNOWN',
                          full_feasible_start_claim=False, continuous_values_set=0))
    stage, qp, proposal = 'fallback_validation', None, None
    fallback_plan, fallback_replay, fallback_bill = None, None, None
    native_optimal = False

    def guard(deadline):
        check()
        if time.monotonic() >= deadline:
            raise TimeoutError('Economic MIQP absolute '+('native' if deadline == native_deadline else 'admission')+' deadline')

    def emit(event):
        guard(admission_deadline)
        if record is not None:
            record(event)
        guard(admission_deadline)

    try:
        if (type(seed) is not int or seed != 17 or type(fleet_N) is not int
                or not 1 <= fleet_N <= case.max_vehicles
                or any(type(x) not in (int, float) or not math.isfinite(x)
                       for x in (native_deadline, admission_deadline))
                or native_deadline > admission_deadline):
            raise CopyContractError('Require seed17, positive exact N and ordered finite absolute deadlines')
        guard(admission_deadline)
        from egglab import native_pathflow as pf, native_recharge as nr, native_hull as nh
        a, b = tuple(a), tuple(b)
        nr.validate_case(case)
        nr._check_market(case, a, b)
        if prior_plan.get('case_identity') != case.identity():
            raise CopyContractError('Common prior physical identity differs')
        fallback_replay = nr.replay_native(case, prior_plan)
        if fallback_replay.get('replay_ok') is not True:
            raise CopyContractError('Common prior failed independent original-case replay')
        if len(prior_plan['vehicles']) != fleet_N:
            raise CopyContractError('Common prior differs from exact fleet N')
        fallback_plan = deepcopy(prior_plan)
        fallback_replay = deepcopy(fallback_replay)
        market = nh.Market('economic-recourse-MIQP-target', a, b)
        fallback_bill = Fraction(fallback_replay['ops_cost'])+nh.supply(market, fallback_replay['load'])
        guard(admission_deadline)
        prior_ids_list = [mid for vehicle in fallback_plan['vehicles'] for mid in vehicle['movements']]
        prior_ids = set(prior_ids_list)
        if len(prior_ids_list) != len(prior_ids) or not prior_ids <= {m.id for m in case.movements}:
            raise CopyContractError('Prior movement IDs are duplicated or outside the original universe')
        result.update(plan=fallback_plan, replay=fallback_replay,
            true_bill_exact=str(fallback_bill), true_bill=float(fallback_bill),
            fallback_bill_exact=str(fallback_bill), admitted_monotonic=time.monotonic())

        stage = 'original_model'
        guard(native_deadline)
        original_optimizer, original_builder = pf._optimize_once, pf.build_feasible_model
        if original_optimizer is not nr._optimize_once:
            raise CopyContractError('Unexpected original native optimizer hook')
        built = pf.build_feasible_model(case, 'GRB')
        guard(native_deadline)
        original = built['model']
        base_physical_rows = built['constraint_count_before_objective']
        if (built['physical_identity'] != case.identity() or built['compiled']['identity'] != case.identity()
                or original.num_rows != base_physical_rows or len(built['x']) != len(case.movements)):
            raise CopyContractError('Original physical matrix identity/dimensions differ')
        x_indices = {var.idx for var in built['x']}
        if len(x_indices) != len(case.movements):
            raise CopyContractError('Original routing map aliases variables')
        for movement, var in zip(case.movements, built['x']):
            guard(native_deadline)
            if str(var.var_type) != 'B' or var.lb != 0 or var.ub != 1:
                raise CopyContractError('Original routing variable is not free binary0/1')
        import mip
        starts = [var for movement, var in zip(case.movements, built['x']) if movement.kind == 'pullout']
        original += mip.xsum(starts) == fleet_N
        physical_rows = original.num_rows
        if physical_rows != base_physical_rows+1:
            raise CopyContractError('Exact-N equality row was not added once')
        built['constraint_count_before_objective'] = physical_rows
        pf.attach_objective(built, 'linear', a)
        if original.num_rows != physical_rows:
            raise CopyContractError('Linear objective unexpectedly changed physical rows')

        stage = 'copy_contract'
        guard(native_deadline)
        import gurobipy as gp
        guard(native_deadline)
        qp = gp.Model('original_physics_free_binary_exact_N_MIQP')
        qp.Params.OutputFlag = 0
        for name, value in PARAMETERS.items():
            setattr(qp.Params, name, value)
        if any(getattr(qp.Params, name) != value for name, value in PARAMETERS.items()):
            raise CopyContractError('Prospective MIQP parameter read-back differs')
        qp.ModelSense = gp.GRB.MINIMIZE
        originals = list(original.vars)
        mapped, bounds = [], []
        infinite_bound_count, infinite_variable_count, infinity_examples = 0, 0, []
        result['copy_contract'].update(bound_policy=BOUND_POLICY, infinite_bound_count=0,
            infinite_variable_count=0, infinite_bound_examples=infinity_examples)
        for index, var in enumerate(originals):
            guard(native_deadline)
            if var.idx != index:
                raise CopyContractError('Original variable indices are not dense and ordered')
            lower, upper = float(var.lb), float(var.ub)
            if math.isnan(lower) or math.isnan(upper) or lower > upper:
                raise CopyContractError('Invalid stored source bounds')
            if index in x_indices:
                if lower != 0 or upper != 1 or str(var.var_type) != 'B':
                    raise CopyContractError('Free binary routing bounds/type changed before copying')
            elif str(var.var_type) != 'C':
                raise CopyContractError('Unexpected unfixed integer outside routing map')
            infinite_sides = int(_bound_semantics(lower, 'LB')[0] != 'exact_value')
            infinite_sides += int(_bound_semantics(upper, 'UB')[0] != 'exact_value')
            infinite_bound_count += infinite_sides
            infinite_variable_count += bool(infinite_sides)
            result['copy_contract'].update(infinite_bound_count=infinite_bound_count,
                infinite_variable_count=infinite_variable_count)
            bounds.append((lower, upper))
            mapped.append(qp.addVar(lb=_bound_for_api(lower, 'LB', gp.GRB.INFINITY),
                ub=_bound_for_api(upper, 'UB', gp.GRB.INFINITY),
                vtype=gp.GRB.BINARY if index in x_indices else gp.GRB.CONTINUOUS, name=str(var.name)))
        qp.update()
        if qp.NumVars != len(originals):
            raise CopyContractError('Copied variable count differs')
        for index, (var, bound) in enumerate(zip(mapped, bounds)):
            guard(native_deadline)
            read_back = (float(var.LB), float(var.UB))
            original_tags = (_bound_semantics(bound[0], 'LB'), _bound_semantics(bound[1], 'UB'))
            copied_tags = (_bound_semantics(read_back[0], 'LB'), _bound_semantics(read_back[1], 'UB'))
            expected_type = gp.GRB.BINARY if index in x_indices else gp.GRB.CONTINUOUS
            mismatch = (var.index != index or var.VType != expected_type
                or copied_tags != original_tags)
            example = any(tag[0] != 'exact_value' for tag in original_tags) and len(infinity_examples) < 5
            if mismatch or example:
                diagnostic = dict(original_index=index, original_name=str(originals[index].name),
                    original_type=str(originals[index].var_type), copied_index=var.index,
                    copied_name=str(var.VarName), copied_type=str(var.VType),
                    original_raw_bounds_repr=[repr(value) for value in bound],
                    copied_readback_bounds_repr=[repr(value) for value in read_back],
                    original_canonical_tags_repr=repr(original_tags),
                    copied_canonical_tags_repr=repr(copied_tags),
                    raw_bounds_exactly_equal=read_back == bound,
                    canonical_equal=copied_tags == original_tags)
            if example:
                infinity_examples.append(diagnostic)
            if mismatch:
                result['copy_contract']['bound_mismatch'] = diagnostic
                raise CopyContractError('Nonequivalent bound/index/preserved-type read-back: '+repr(diagnostic))

        senses = {'<': gp.GRB.LESS_EQUAL, '>': gp.GRB.GREATER_EQUAL, '=': gp.GRB.EQUAL}
        copied_rows, coefficients = [], 0
        for index, row in enumerate(original.constrs):
            guard(native_deadline)
            if row.idx != index:
                raise CopyContractError('Original row indices are not dense and ordered')
            expression = row.expr
            terms = _linear_terms(expression)
            if expression.sense not in senses or any(i < 0 or i >= len(mapped) for i in terms):
                raise CopyContractError('Unknown source sense or coefficient variable index')
            rhs = -_finite(expression.const, 'stored row constant')
            lhs = gp.LinExpr(list(terms.values()), [mapped[i] for i in terms])
            copied_rows.append(qp.addLConstr(lhs, senses[expression.sense], rhs, name=str(row.name)))
            coefficients += len(terms)
        qp.update()
        if qp.NumConstrs != physical_rows or qp.NumQConstrs != 0:
            raise CopyContractError('Copied physical constraint counts differ')
        # Read every actual stored row back. No tolerances or text round trips.
        read_coefficients = 0
        for index, (old_row, new_row) in enumerate(zip(original.constrs, copied_rows)):
            guard(native_deadline)
            old_expr = old_row.expr
            actual = _gp_linear_terms(qp.getRow(new_row))
            expected = _linear_terms(old_expr)
            if (new_row.index != index or new_row.Sense != senses[old_expr.sense]
                    or float(new_row.RHS) != -float(old_expr.const) or actual != expected):
                raise CopyContractError('Physical row coefficient/RHS/sense read-back differs')
            read_coefficients += len(actual)

        objective = original.objective
        linear = _linear_terms(objective)
        constant = _finite(objective.const, 'stored objective constant')
        native_linear = gp.LinExpr(list(linear.values()), [mapped[i] for i in linear])
        native_linear.addConstant(constant)
        native_quadratic = gp.QuadExpr(native_linear)
        expected_quad = {}
        if len(built['loads']) != len(b):
            raise CopyContractError('Load/curvature dimensions differ')
        for var, bb in zip(built['loads'], b):
            guard(native_deadline)
            coefficient = .5*_finite(bb, 'curvature')
            if coefficient < 0 or (var.idx, var.idx) in expected_quad:
                raise CopyContractError('Negative curvature or aliased load variable')
            if coefficient:
                expected_quad[var.idx, var.idx] = coefficient
                native_quadratic.addTerms(coefficient, mapped[var.idx], mapped[var.idx])
        qp.setObjective(native_quadratic, gp.GRB.MINIMIZE)
        qp.update()
        got = qp.getObjective()
        got_linear = got.getLinExpr() if isinstance(got, gp.QuadExpr) else got
        got_quad = {}
        if isinstance(got, gp.QuadExpr):
            for k in range(got.size()):
                first, second = got.getVar1(k).index, got.getVar2(k).index
                key = tuple(sorted((first, second)))
                if key in got_quad:
                    raise CopyContractError('Duplicate read-back quadratic term')
                got_quad[key] = _finite(got.getCoeff(k), 'read-back quadratic coefficient')
        if (_gp_linear_terms(got_linear) != linear or float(qp.ObjCon) != constant
                or got_quad != expected_quad or qp.ModelSense != gp.GRB.MINIMIZE
                or qp.NumVars != len(originals) or qp.NumConstrs != physical_rows
                or original.num_rows != physical_rows or original.num_cols != len(originals)):
            raise CopyContractError('Objective/matrix read-back differs from integrated supply MIQP')
        if qp.NumBinVars != len(x_indices):
            raise CopyContractError('Copied free-binary route count differs')
        result['copy_contract'] = dict(passed=True, original_variables=len(originals),
            original_physical_rows=base_physical_rows, exact_fleet_rows_added=1, fleet_N=fleet_N,
            copied_variables=qp.NumVars,
            copied_physical_rows=qp.NumConstrs, source_nonzeros=coefficients,
            read_back_nonzeros=read_coefficients, free_routing_binaries=len(x_indices),
            continuous_unfixed_variables=len(originals)-len(x_indices),
            linear_objective_terms=len(linear), diagonal_quadratic_terms=len(got_quad),
            mapping='original var.idx equals copied Var.index, dense zero-based; all checked',
            bounds='side-specific documented unbounded sentinels canonicalized; every other bound exact',
            bound_policy=BOUND_POLICY, infinite_bound_count=infinite_bound_count,
            infinite_variable_count=infinite_variable_count, infinite_bound_examples=infinity_examples,
            physical_rows='all stored coefficients/RHS/senses checked by original index, no tolerance',
            objective='original ops+a*load linear expression plus .5*b*load^2; sparse read-back checked',
            original_cffi_variables_retained=True, text_round_trip=False,
            extraction_view='raw .x-only values for x/charge/loads; compiled/model metadata unchanged')

        stage = 'partial_start'
        guard(native_deadline)
        qp.NumStart = 1
        qp.Params.StartNumber = 0
        for movement, var in zip(case.movements, built['x']):
            mapped[var.idx].Start = int(movement.id in prior_ids)
        qp.update()
        if qp.NumStart != 1 or qp.Params.StartNumber != 0:
            raise CopyContractError('Partial binary start slot read-back differs')
        expected_start = {var.idx: int(movement.id in prior_ids) for movement, var in zip(case.movements, built['x'])}
        for index, var in enumerate(mapped):
            guard(native_deadline)
            expected = expected_start.get(index, gp.GRB.UNDEFINED)
            if var.Start != expected:
                raise CopyContractError('Partial start mapping/read-back differs or continuous start was set')
        result['native_start'].update(submitted=True, mapping_readback_passed=True,
            binary_values_set=len(expected_start), continuous_values_set=0)

        stage = 'native_MIQP'
        guard(native_deadline)
        remaining = native_deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('No remaining native QP time')
        qp.Params.TimeLimit = remaining
        guard(native_deadline)
        if (qp.Params.Threads != 1 or qp.Params.Seed != seed or qp.Params.Method != 0
                or qp.Params.TimeLimit != remaining):
            raise CopyContractError('MIQP thread/seed/method/time-limit read-back differs')
        entered, cpu = time.monotonic(), time.process_time()
        result['native_call_attempts'] = result['native_calls'] = 1
        try:
            qp.optimize()
        except Exception as exc:
            if not isinstance(exc, TimeoutError):
                result['config_failure'] = result['fatal_contract'] = True
                result['copy_contract'].update(passed=False, failure_stage='native_MIQP_API',
                    native_api_exception=dict(type=type(exc).__name__, message=str(exc)))
            raise
        finally:
            returned = time.monotonic()
            result['stats'].update(entered_monotonic=entered, returned_monotonic=returned,
                wall_s=returned-entered, cpu_s=time.process_time()-cpu,
                native_overrun_s=max(0., returned-native_deadline))
            for name in ('Status', 'SolCount', 'ObjVal', 'ObjBound', 'ObjBoundC', 'MIPGap', 'NodeCount', 'IsMIP', 'Runtime', 'Work',
                         'IterCount', 'BarIterCount', 'MaxVio', 'ConstrVio', 'BoundVio',
                         'DualVio', 'ComplVio', 'ConstrResidual', 'DualResidual'):
                result['stats'][name] = _attribute(qp, name)
            result['stats'].update(solver='gurobipy', package_version=getattr(gp, '__version__', None),
                native_version=list(gp.gurobi.version()), threads=qp.Params.Threads, seed=qp.Params.Seed,
                Method=qp.Params.Method,
                parameters={name: getattr(qp.Params, name) for name in PARAMETERS},
                FeasibilityTol=qp.Params.FeasibilityTol, OptimalityTol=qp.Params.OptimalityTol,
                BarConvTol=qp.Params.BarConvTol, TimeLimit=qp.Params.TimeLimit,
                native_lower_bound=_attribute(qp, 'ObjBound'),
                lower_bound_scope='Raw numerical full-declared-graph exact-N MIQP attribute; no physical/global certificate')
        guard(admission_deadline)
        admitted_statuses = {gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SUBOPTIMAL,
            gp.GRB.ITERATION_LIMIT, gp.GRB.INTERRUPTED, gp.GRB.WORK_LIMIT}
        if qp.Status not in admitted_statuses or qp.SolCount < 1:
            raise RuntimeError('One MIQP returned no admissible incumbent/status; no retry')
        native_optimal = qp.Status == gp.GRB.OPTIMAL
        result['stats']['native_optimal'] = native_optimal

        stage = 'unchanged_extraction'
        guard(admission_deadline)
        raw = [_finite(value, 'MIQP solution value') for value in qp.getAttr('X', mapped)]
        if len(raw) != len(originals):
            raise CopyContractError('MIQP solution vector length differs from original index map')
        binary_distance = max(abs(raw[index]-round(raw[index])) for index in x_indices)
        result['stats']['max_binary_integrality_distance'] = binary_distance
        if binary_distance > qp.Params.IntFeasTol:
            raise ValueError('Native routing integrality exceeds the fixed MIQP setting')
        values = [_Value(value) for value in raw]
        view = dict(built)
        view['x'] = [values[var.idx] for var in built['x']]
        view['charge'] = {key: values[var.idx] for key, var in built['charge'].items()}
        view['loads'] = [values[var.idx] for var in built['loads']]
        raw_exact = Fraction(constant)+sum((Fraction(c)*Fraction(raw[i]) for i, c in linear.items()), Fraction(0))
        raw_exact += sum((Fraction(bb)*Fraction(raw[var.idx])**2/2
            for var, bb in zip(built['loads'], b)), Fraction(0))
        if abs(float(raw_exact)-float(qp.ObjVal)) > nr.OBJECTIVE_TOL:
            raise CopyContractError('Native MIQP objective differs from copied integrated-cost expression')
        plan = pf._extract(case, view, record=emit, round_index=0)
        guard(admission_deadline)
        replay = nr.replay_native(case, plan)
        actual = [mid for vehicle in plan['vehicles'] for mid in vehicle['movements']]
        if (replay.get('replay_ok') is not True or len(actual) != len(set(actual))
                or not set(actual) <= {movement.id for movement in case.movements}
                or len(plan['vehicles']) != fleet_N
                or plan.get('case_identity') != case.identity()):
            raise CopyContractError('MIQP candidate violated exact N/original universe/case or failed replay')
        bill = Fraction(replay['ops_cost'])+nh.supply(market, replay['load'])
        result['stats'].update(raw_objective_exact=str(raw_exact),
            replay_objective_exact=str(bill), native_to_physical_cost_delta=float(bill)-float(qp.ObjVal),
            raw_to_physical_cost_delta_exact=str(bill-raw_exact))
        if abs(bill-raw_exact) > Fraction(nr.OBJECTIVE_TOL):
            raise ValueError('Physical replay and raw MIQP objective differ beyond existing OBJECTIVE_TOL')
        guard(admission_deadline)
        proposal = (deepcopy(plan), deepcopy(replay), bill)
        if pf._optimize_once is not original_optimizer or pf.build_feasible_model is not original_builder:
            raise CopyContractError('Unexpected mutation of original native API')
        guard(admission_deadline)
        result.update(miqp_candidate_admitted=True, candidate_bill_exact=str(bill),
            candidate_route_changed_from_prior=_canonical(plan) != _canonical(fallback_plan),
            admitted_monotonic=time.monotonic())
        # Protect the best physical endpoint immediately, including if later cleanup fails.
        if bill < fallback_bill:
            result.update(plan=proposal[0], replay=proposal[1], true_bill_exact=str(bill),
                true_bill=float(bill), selected_source='direct_miqp', used_fallback=False,
                retained_route_changed_from_prior=result['candidate_route_changed_from_prior'])
    except Exception as exc:
        result['failures'].append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))
        if isinstance(exc, CopyContractError) or stage in ('copy_contract', 'partial_start') and not isinstance(exc, TimeoutError):
            result['config_failure'] = result['fatal_contract'] = True
            result['copy_contract'].update(passed=False, failure_stage=stage)
    finally:
        if qp is not None:
            try:
                qp.dispose()
            except Exception as exc:
                result['failures'].append(dict(stage='MIQP_disposal', type=type(exc).__name__, message=str(exc)))
    # An independently replayed fallback survives native/copy/extraction failure.
    # Caller owns publication and rejects any return beyond its inclusive clock.
    if result['miqp_candidate_admitted'] and not result['failures'] and not result['fatal_contract']:
        try:
            guard(admission_deadline)
            result.update(miqp_success=True, strict_method_success=True)
        except Exception as exc:
            result['failures'].append(dict(stage='final_admission', type=type(exc).__name__, message=str(exc)))
            result['miqp_success'] = result['strict_method_success'] = False
    result.update(status='MIQP_OPTIMAL_physical_candidate_admitted' if result['miqp_success'] and native_optimal else
        'MIQP_supported_status_physical_candidate_admitted' if result['miqp_success'] else
        'MIQP_physical_candidate_retained_with_qualification_limits' if result['miqp_candidate_admitted'] else 'fallback_or_unavailable',
        returned_monotonic=time.monotonic())
    return result
