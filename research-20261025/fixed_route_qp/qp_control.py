"""One direct convex QP on a copied original fixed-topology physical matrix."""
from copy import deepcopy
from fractions import Fraction
import math
import time

POLICY = 'original-matrix-fixed-route-public-gurobipy-QP-v1'


class CopyContractError(ValueError):
    """A fatal source/matrix/objective mapping inconsistency, never infeasibility."""


class _Value:
    """Only the raw .x access used by unchanged native_pathflow._extract."""
    __slots__ = ('x',)

    def __init__(self, value):
        self.x = value


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


def solve(case, a, b, prior_plan, seed, native_deadline, admission_deadline, check, record=None):
    """Retain the best physical witness from one QP, otherwise the validated fallback.

    No MIP/LP optimization, tangent rounds, private solver bridge, timing
    controller or replacement decoder. Caller owns durable inclusive admission.
    Nonoptimal incumbents may be provisional; qp_success requires native OPTIMAL.
    """
    result = dict(policy=POLICY, plan=None, replay=None, true_bill_exact=None,
        true_bill=None, fallback_bill_exact=None, selected_source='fallback', used_fallback=True,
        qp_success=False, qp_candidate_admitted=False, native_calls=0, native_call_attempts=0,
        stats={}, copy_contract={}, failures=[], config_failure=False, fatal_contract=False,
        global_lower_bound=None, bound_scope='numerical original-matrix fixed-topology QP only',
        certificate_claim=False, native_deadline=native_deadline,
        admission_deadline=admission_deadline, admitted_monotonic=None)
    stage, qp, proposal = 'fallback_validation', None, None
    fallback_plan, fallback_replay, fallback_bill = None, None, None
    native_optimal = False

    def guard(deadline):
        check()
        if time.monotonic() >= deadline:
            raise TimeoutError('Fixed-route QP absolute '+('native' if deadline == native_deadline else 'admission')+' deadline')

    def emit(event):
        guard(admission_deadline)
        if record is not None:
            record(event)
        guard(admission_deadline)

    try:
        if (type(seed) is not int or seed != 17
                or any(type(x) not in (int, float) or not math.isfinite(x)
                       for x in (native_deadline, admission_deadline))
                or native_deadline > admission_deadline):
            raise CopyContractError('Require frozen seed17 and ordered finite absolute deadlines')
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
        fallback_plan = deepcopy(prior_plan)
        fallback_replay = deepcopy(fallback_replay)
        market = nh.Market('fixed-route-QP-target', a, b)
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
        physical_rows = built['constraint_count_before_objective']
        if (built['physical_identity'] != case.identity() or built['compiled']['identity'] != case.identity()
                or original.num_rows != physical_rows or len(built['x']) != len(case.movements)):
            raise CopyContractError('Original physical matrix identity/dimensions differ')
        x_indices = {var.idx for var in built['x']}
        if len(x_indices) != len(case.movements):
            raise CopyContractError('Original routing map aliases variables')
        for movement, var in zip(case.movements, built['x']):
            guard(native_deadline)
            if str(var.var_type) != 'B' or var.lb != 0 or var.ub != 1:
                raise CopyContractError('Original routing variable is not free binary0/1')
            var.lb = var.ub = int(movement.id in prior_ids)
        pf.attach_objective(built, 'linear', a)
        if original.num_rows != physical_rows:
            raise CopyContractError('Linear objective unexpectedly changed physical rows')

        stage = 'copy_contract'
        guard(native_deadline)
        import gurobipy as gp
        guard(native_deadline)
        qp = gp.Model('original_physics_fixed_route_QP')
        qp.Params.OutputFlag = 0
        qp.Params.Threads = 1
        qp.Params.Seed = seed
        qp.Params.NonConvex = 0
        # Prospectively fixed accuracy settings; physical rows/decoder stay unchanged.
        qp.Params.FeasibilityTol = 1e-9
        qp.Params.OptimalityTol = 1e-9
        qp.Params.BarConvTol = 1e-10
        if (qp.Params.FeasibilityTol != 1e-9 or qp.Params.OptimalityTol != 1e-9
                or qp.Params.BarConvTol != 1e-10):
            raise CopyContractError('Strong-control numerical parameter read-back differs')
        qp.ModelSense = gp.GRB.MINIMIZE
        originals = list(original.vars)
        mapped, bounds = [], []
        for index, var in enumerate(originals):
            guard(native_deadline)
            if var.idx != index:
                raise CopyContractError('Original variable indices are not dense and ordered')
            lower, upper = float(var.lb), float(var.ub)
            if math.isnan(lower) or math.isnan(upper) or lower > upper:
                raise CopyContractError('Invalid stored source bounds')
            if index in x_indices:
                if lower != upper or lower not in (0, 1) or str(var.var_type) != 'B':
                    raise CopyContractError('Routing singleton/type changed before copying')
            elif str(var.var_type) != 'C':
                raise CopyContractError('Unexpected unfixed integer outside routing map')
            bounds.append((lower, upper))
            mapped.append(qp.addVar(lb=lower, ub=upper, vtype=gp.GRB.CONTINUOUS, name=str(var.name)))
        qp.update()
        if qp.NumVars != len(originals):
            raise CopyContractError('Copied variable count differs')
        for index, (var, bound) in enumerate(zip(mapped, bounds)):
            guard(native_deadline)
            if (var.index != index or var.VType != gp.GRB.CONTINUOUS
                    or (float(var.LB), float(var.UB)) != bound):
                raise CopyContractError('Stored bound/index/continuous read-back differs')

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
            raise CopyContractError('Objective/matrix read-back differs from integrated supply QP')
        result['copy_contract'] = dict(passed=True, original_variables=len(originals),
            original_physical_rows=physical_rows, copied_variables=qp.NumVars,
            copied_physical_rows=qp.NumConstrs, source_nonzeros=coefficients,
            read_back_nonzeros=read_coefficients, fixed_routing_binaries=len(x_indices),
            continuous_unfixed_variables=len(originals)-len(x_indices),
            linear_objective_terms=len(linear), diagonal_quadratic_terms=len(got_quad),
            mapping='original var.idx equals copied Var.index, dense zero-based; all checked',
            bounds='stored source lower/upper copied and read back with exact float equality',
            physical_rows='all stored coefficients/RHS/senses checked by original index, no tolerance',
            objective='original ops+a*load linear expression plus .5*b*load^2; sparse read-back checked',
            original_cffi_variables_retained=True, text_round_trip=False,
            extraction_view='raw .x-only values for x/charge/loads; compiled/model metadata unchanged')

        stage = 'native_QP'
        guard(native_deadline)
        remaining = native_deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('No remaining native QP time')
        qp.Params.TimeLimit = remaining
        guard(native_deadline)
        if qp.Params.Threads != 1 or qp.Params.Seed != seed or qp.Params.TimeLimit != remaining:
            raise CopyContractError('QP thread/seed/time-limit read-back differs')
        entered, cpu = time.monotonic(), time.process_time()
        result['native_call_attempts'] = result['native_calls'] = 1
        try:
            qp.optimize()
        finally:
            returned = time.monotonic()
            result['stats'].update(entered_monotonic=entered, returned_monotonic=returned,
                wall_s=returned-entered, cpu_s=time.process_time()-cpu,
                native_overrun_s=max(0., returned-native_deadline))
            for name in ('Status', 'SolCount', 'ObjVal', 'ObjBound', 'Runtime', 'Work',
                         'IterCount', 'BarIterCount', 'MaxVio', 'ConstrVio', 'BoundVio',
                         'DualVio', 'ComplVio', 'ConstrResidual', 'DualResidual'):
                result['stats'][name] = _attribute(qp, name)
            result['stats'].update(solver='gurobipy', package_version=getattr(gp, '__version__', None),
                native_version=list(gp.gurobi.version()), threads=qp.Params.Threads, seed=qp.Params.Seed,
                FeasibilityTol=qp.Params.FeasibilityTol, OptimalityTol=qp.Params.OptimalityTol,
                BarConvTol=qp.Params.BarConvTol, TimeLimit=qp.Params.TimeLimit,
                native_lower_bound=_attribute(qp, 'ObjBound'),
                lower_bound_scope='raw numerical fixed-topology QP attribute, null if unsupported')
        guard(admission_deadline)
        admitted_statuses = {gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SUBOPTIMAL,
            gp.GRB.ITERATION_LIMIT, gp.GRB.INTERRUPTED, gp.GRB.WORK_LIMIT}
        if qp.Status not in admitted_statuses or qp.SolCount < 1:
            raise RuntimeError('One QP returned no admissible incumbent/status; no retry')
        native_optimal = qp.Status == gp.GRB.OPTIMAL
        result['stats']['native_optimal'] = native_optimal

        stage = 'unchanged_extraction'
        guard(admission_deadline)
        raw = [_finite(value, 'QP solution value') for value in qp.getAttr('X', mapped)]
        if len(raw) != len(originals):
            raise CopyContractError('QP solution vector length differs from original index map')
        values = [_Value(value) for value in raw]
        view = dict(built)
        view['x'] = [values[var.idx] for var in built['x']]
        view['charge'] = {key: values[var.idx] for key, var in built['charge'].items()}
        view['loads'] = [values[var.idx] for var in built['loads']]
        raw_exact = Fraction(constant)+sum((Fraction(c)*Fraction(raw[i]) for i, c in linear.items()), Fraction(0))
        raw_exact += sum((Fraction(bb)*Fraction(raw[var.idx])**2/2
            for var, bb in zip(built['loads'], b)), Fraction(0))
        if abs(float(raw_exact)-float(qp.ObjVal)) > nr.OBJECTIVE_TOL:
            raise CopyContractError('Native QP objective differs from copied integrated-cost expression')
        plan = pf._extract(case, view, record=emit, round_index=0)
        guard(admission_deadline)
        replay = nr.replay_native(case, plan)
        actual = [mid for vehicle in plan['vehicles'] for mid in vehicle['movements']]
        if (replay.get('replay_ok') is not True or len(actual) != len(set(actual))
                or set(actual) != prior_ids or len(plan['vehicles']) != len(fallback_plan['vehicles'])
                or plan.get('case_identity') != case.identity()):
            raise CopyContractError('QP candidate changed fixed topology/fleet/identity or failed replay')
        bill = Fraction(replay['ops_cost'])+nh.supply(market, replay['load'])
        result['stats'].update(raw_objective_exact=str(raw_exact),
            replay_objective_exact=str(bill), native_to_physical_cost_delta=float(bill)-float(qp.ObjVal),
            raw_to_physical_cost_delta_exact=str(bill-raw_exact))
        if abs(bill-raw_exact) > Fraction(nr.OBJECTIVE_TOL):
            raise ValueError('Physical replay and raw QP objective differ beyond existing OBJECTIVE_TOL')
        guard(admission_deadline)
        proposal = (deepcopy(plan), deepcopy(replay), bill)
        if pf._optimize_once is not original_optimizer or pf.build_feasible_model is not original_builder:
            raise CopyContractError('Unexpected mutation of original native API')
    except Exception as exc:
        result['failures'].append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))
        if isinstance(exc, CopyContractError) or stage == 'copy_contract' and not isinstance(exc, TimeoutError):
            result['config_failure'] = result['fatal_contract'] = True
            result['copy_contract'].update(passed=False, failure_stage=stage)
    finally:
        if qp is not None:
            try:
                qp.dispose()
            except Exception as exc:
                result['failures'].append(dict(stage='QP_disposal', type=type(exc).__name__, message=str(exc)))
    # An independently replayed fallback survives native/copy/extraction failure.
    # Caller owns publication and rejects any return beyond its inclusive clock.
    if proposal is not None and not result['failures']:
        try:
            guard(admission_deadline)
            result.update(qp_success=native_optimal, qp_candidate_admitted=True,
                candidate_bill_exact=str(proposal[2]), admitted_monotonic=time.monotonic())
            if proposal[2] < fallback_bill:
                result.update(plan=proposal[0], replay=proposal[1], true_bill_exact=str(proposal[2]),
                    true_bill=float(proposal[2]), selected_source='direct_qp', used_fallback=False)
        except Exception as exc:
            result['failures'].append(dict(stage='final_admission', type=type(exc).__name__, message=str(exc)))
            result['qp_success'] = result['qp_candidate_admitted'] = False
    result.update(status='QP_admitted' if result['qp_success'] else
        'QP_provisional_admitted' if result['qp_candidate_admitted'] else 'fallback_or_unavailable',
        returned_monotonic=time.monotonic())
    return result
