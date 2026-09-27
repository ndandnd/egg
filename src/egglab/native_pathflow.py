"""Compact DAG path-flow realization of the native complete-fleet feasible set.

Research candidate only until its separate prospective qualification passes.
No optimizer import on module import; physical schema/replay are unchanged.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import math
import time

from egglab import native_recharge as nr

FORMULATION = 'egg-native-pathflow-v3-energy-band-orphan-projection'
NATIVE_MATRIX = 'egg-native-pathflow-v2-energy-band'
EXTRACTION_POLICY = 'native-pathflow-orphan-projection-v1'
ENERGY_BALANCE_POLICY = 'stored-row-and-physical-conservation-band-v1'
Budget = nr.Budget
BOUND_GUARD = nr.BOUND_GUARD
_check_prices = nr._check_prices
_check_market = nr._check_market
_check_budget = nr._check_budget
attach_objective = nr.attach_objective
_optimize_once = nr._optimize_once
replay_native = nr.replay_native
true_cost = nr.true_cost
admit_bound = nr.admit_bound


def energy_balance_spec(case):
    """Outward band valid for physical conservation AND the stored V1 matrix.

    All arithmetic in the proof ledger is exact on stored floats. This is not
    an additional feasibility tolerance or a claim of exact native solves.
    """
    nr.validate_case(case)
    Q = Fraction
    B = Q(case.battery_kwh)
    service = sum((Q(t.energy_kwh) for t in case.trips), Q(0))
    service_float = sum(t.energy_kwh for t in case.trips)
    if not math.isfinite(service_float):
        raise ValueError('Nonfinite aggregate service coefficient')
    modes, physical_lo, physical_hi, row_lo, row_hi = [], [], [], [], []
    for index, mode in enumerate(case.movements):
        energy = sum(leg.energy_kwh for leg in mode.legs)
        big_m = case.battery_kwh+energy
        if not math.isfinite(energy) or not math.isfinite(big_m):
            raise ValueError('Nonfinite aggregate movement coefficient')
        semantic = sum((Q(leg.energy_kwh) for leg in mode.legs), Q(0))
        if mode.kind == 'pullout':
            constant = -(case.battery_kwh-energy)
            ideal_constant = -B+Q(energy)
        elif mode.kind == 'pullin':
            constant = -energy-case.battery_kwh
            ideal_constant = -B-Q(energy)
        else:
            constant = energy
            ideal_constant = Q(energy)
        # In Python-MIP the normalized big-M row constants are fl(C +/- M).
        # At y=1 these two inequalities bound phi+C, not necessarily zero.
        plus, minus = constant+big_m, constant-big_m
        if not all(math.isfinite(v) for v in (constant, plus, minus)):
            raise ValueError('Nonfinite stored SOC row constant')
        defect = Q(constant)-ideal_constant
        lower = Q(constant)+Q(big_m)-Q(plus)-defect
        upper = Q(constant)-Q(big_m)-Q(minus)-defect
        signed_lower, signed_upper = (-upper, -lower) if mode.kind == 'pullin' else (lower, upper)
        difference = semantic-Q(energy)
        physical_lo.append(min(Q(0), difference)); physical_hi.append(max(Q(0), difference))
        row_lo.append(min(Q(0), signed_lower)); row_hi.append(max(Q(0), signed_upper))
        modes.append({'index':index,'id':mode.id,'kind':mode.kind,'energy_float':energy,
            'semantic_energy_exact':str(semantic),'energy_aggregation_defect_exact':str(difference),
            'big_m_float':big_m,'residual_constant_float':constant,
            'normalized_plus_constant_float':plus,'normalized_minus_constant_float':minus,
            'residual_constant_defect_exact':str(defect),
            'selected_intended_residual_lower_exact':str(lower),
            'selected_intended_residual_upper_exact':str(upper),
            'signed_contribution_lower_exact':str(signed_lower),
            'signed_contribution_upper_exact':str(signed_upper)})
    selected_cap = 2*len(case.trips)
    physical_lower = service+sum(sorted(physical_lo)[:selected_cap], Q(0))
    physical_upper = service+sum(sorted(physical_hi, reverse=True)[:selected_cap], Q(0))
    stored_lower = service-sum(sorted(row_hi, reverse=True)[:selected_cap], Q(0))
    stored_upper = service-sum(sorted(row_lo)[:selected_cap], Q(0))
    lower, upper = min(physical_lower, stored_lower), max(physical_upper, stored_upper)
    def outward(value, direction):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Nonfinite aggregate energy endpoint')
        if (direction < 0 and Q(result) > value) or (direction > 0 and Q(result) < value):
            result = math.nextafter(result, -math.inf if direction < 0 else math.inf)
        if not math.isfinite(result):
            raise ValueError('Nonfinite outward aggregate energy endpoint')
        return result
    return {'policy':ENERGY_BALANCE_POLICY,'charge_coefficient':case.efficiency,
        'service_energy_exact':str(service),'service_energy_float':service_float,
        'service_aggregation_defect_exact':str(service-Q(service_float)),
        'selected_mode_cap':selected_cap,'modes':modes,
        'physical_lower_exact':str(physical_lower),'physical_upper_exact':str(physical_upper),
        'stored_matrix_lower_exact':str(stored_lower),'stored_matrix_upper_exact':str(stored_upper),
        'union_lower_exact':str(lower),'union_upper_exact':str(upper),
        'lower_rhs':outward(lower,-1),'upper_rhs':outward(upper,1),
        'additional_constraints':2,
        'interpretation':'Union of intended per-leg conservation and exact binary-stored integer matrix bands; native tolerances unchanged'}


def recover_paths(case, selected_ids):
    """Recover all paths, or fail on any missing/branching/disconnected arc."""
    nr.validate_case(case)
    ids = list(selected_ids)
    lookup = {m.id:m for m in case.movements}
    if len(ids) != len(set(ids)) or any(mid not in lookup for mid in ids):
        raise ValueError('Unknown or duplicate selected movement')
    selected = [m for m in case.movements if m.id in set(ids)]
    incoming, outgoing = defaultdict(list), defaultdict(list)
    for m in selected:
        if m.after is not None:
            incoming[m.after].append(m)
        if m.before is not None:
            outgoing[m.before].append(m)
    if any(len(incoming[t.id]) != 1 or len(outgoing[t.id]) != 1 for t in case.trips):
        raise ValueError('Selected path flow does not cover every service exactly once')
    starts = [m for m in selected if m.kind == 'pullout']
    if not 1 <= len(starts) <= case.max_vehicles:
        raise ValueError('Invalid selected path count')
    vehicles, owners, visited_trips = [], {}, set()
    for start in starts:
        v, seq, mids, m = len(vehicles), [], [], start
        while True:
            if m.id in owners:
                raise ValueError('Selected movement repeats across paths/cycle')
            owners[m.id] = v
            mids.append(m.id)
            if m.after is None:
                if m.kind != 'pullin':
                    raise ValueError('Path does not end with pullin')
                break
            if m.after in visited_trips:
                raise ValueError('Service repeats across paths/cycle')
            visited_trips.add(m.after)
            seq.append(m.after)
            m = outgoing[m.after][0]
        vehicles.append({'vehicle':v,'trips':seq,'movements':mids})
    if set(owners) != set(ids) or visited_trips != {t.id for t in case.trips}:
        raise ValueError('Disconnected selected movement or service')
    return vehicles, owners


def build_feasible_model(case, backend='CBC'):
    """One selected incoming/outgoing movement per service, unlabelled paths."""
    compiled = nr.compile_case(case)
    balance = energy_balance_spec(case)
    if backend not in ('CBC','GRB'):
        raise ValueError('Explicit CBC/GRB backend required')
    import mip
    model = mip.Model(name=FORMULATION, sense=mip.MINIMIZE, solver_name=backend)
    runtime = nr._backend_identity(model, backend)
    model.verbose, model.threads, model.infeas_tol, model.opt_tol = 0, 1, 1e-8, 1e-8
    B, r, eta = case.battery_kwh, case.reserve_kwh, case.efficiency
    tripidx = {t.id:i for i,t in enumerate(case.trips)}
    modeidx = {m.id:j for j,m in enumerate(case.movements)}
    x = [model.add_var(var_type=mip.BINARY) for _ in case.movements]
    sb = [model.add_var(lb=r, ub=B) for _ in case.trips]
    sa = [model.add_var(lb=r, ub=B) for _ in case.trips]
    incoming, outgoing = defaultdict(list), defaultdict(list)
    for j,m in enumerate(case.movements):
        if m.after is not None: incoming[m.after].append(x[j])
        if m.before is not None: outgoing[m.before].append(x[j])
    starts = [x[j] for j,m in enumerate(case.movements) if m.kind=='pullout']
    ends = [x[j] for j,m in enumerate(case.movements) if m.kind=='pullin']
    model += mip.xsum(starts) <= case.max_vehicles
    model += mip.xsum(starts) == mip.xsum(ends)
    for i,t in enumerate(case.trips):
        model += mip.xsum(incoming[t.id]) == 1
        model += mip.xsum(outgoing[t.id]) == 1
        service_row = sa[i] == sb[i]-t.energy_kwh
        if service_row.const != t.energy_kwh:
            raise ValueError('Native service row assembly differs from proved energy band')
        model += service_row
    charge, by_mode, by_period = {}, defaultdict(list), defaultdict(list)
    for k,interval in enumerate(compiled['intervals']):
        cap = interval['rate_kw']*interval['hours']
        terms = []
        if cap > 0:
            for mid in interval['visits']:
                j = modeidx[mid]
                z = model.add_var(lb=0,ub=cap)
                charge[j,k] = z
                model += z <= cap*x[j]
                terms.append(z); by_mode[j].append(z); by_period[interval['period']].append(z)
        model += mip.xsum(terms) <= cap
    for j,m in enumerate(case.movements):
        selected = x[j]
        energy = sum(l.energy_kwh for l in m.legs)
        M = B+energy
        q = mip.xsum(by_mode[j])
        if m.kind=='pullout':
            residual = sb[tripidx[m.after]]-(B-energy)
        elif m.kind=='direct':
            residual = sb[tripidx[m.after]]-sa[tripidx[m.before]]+energy
        elif m.kind=='depot':
            inbound = sum(l.energy_kwh for l in m.legs[:m.depot_split])
            arrival = sa[tripidx[m.before]]-inbound
            model += arrival >= r-M*(1-selected)
            model += arrival+eta*q <= B+M*(1-selected)
            residual = sb[tripidx[m.after]]-sa[tripidx[m.before]]+energy-eta*q
        else:
            arrival = sa[tripidx[m.before]]-energy
            model += arrival >= r-M*(1-selected)
            residual = arrival+eta*q-B
        # Python-MIP may return the original Var from Var-0. Normalize its
        # representation without changing any coefficient or constant.
        residual = mip.xsum([residual])
        if residual.const != balance['modes'][j]['residual_constant_float']:
            raise ValueError('Native expression assembly differs from proved energy band')
        upper_row = residual <= M*(1-selected)
        lower_row = residual >= -M*(1-selected)
        if (upper_row.const != balance['modes'][j]['normalized_minus_constant_float']
                or lower_row.const != balance['modes'][j]['normalized_plus_constant_float']):
            raise ValueError('Native big-M row normalization differs from proved energy band')
        model += upper_row
        model += lower_row
    aggregate = eta*mip.xsum(charge.values())-mip.xsum(
        entry['energy_float']*x[j] for j,entry in enumerate(balance['modes']))
    actual_coefficients = {v.idx:a for v,a in aggregate.expr.items() if a != 0}
    expected_coefficients = {v.idx:eta for v in charge.values()}
    expected_coefficients.update({x[j].idx:-entry['energy_float'] for j,entry in enumerate(balance['modes']) if entry['energy_float'] != 0})
    if aggregate.const != 0 or actual_coefficients != expected_coefficients:
        raise ValueError('Native aggregate coefficients differ from proved energy band')
    balance_rows = [model.num_rows, model.num_rows+1]
    lower_energy_row = aggregate >= balance['lower_rhs']
    upper_energy_row = aggregate <= balance['upper_rhs']
    if lower_energy_row.const != -balance['lower_rhs'] or upper_energy_row.const != -balance['upper_rhs']:
        raise ValueError('Native aggregate endpoints differ from proved energy band')
    model += lower_energy_row
    model += upper_energy_row
    loads = [model.add_var(lb=0) for _ in range(len(case.market_edges_min)-1)]
    for t,L in enumerate(loads):
        model += L == mip.xsum(by_period[t])
    ops = case.vehicle_cost*mip.xsum(starts)+case.deadhead_cost_per_min*mip.xsum(
        x[j]*sum(l.arrive_min-l.depart_min for l in m.legs) for j,m in enumerate(case.movements))
    return {'model':model,'compiled':compiled,'x':x,'soc_before':sb,'soc_after':sa,
            'charge':charge,'loads':loads,'ops':ops,'physical_identity':case.identity(),
            'backend':backend,'backend_runtime':runtime,'formulation':FORMULATION,
            'energy_balance':balance,
            'energy_balance_row_indices':balance_rows,
            'constraint_count_before_objective':model.num_rows}


def capture_incumbent(case,built):
    def number(value):
        return {'value':float(value) if value is not None and math.isfinite(float(value)) else None,
                'repr':repr(value)}
    return {'case_identity':case.identity(),'formulation':FORMULATION,
        'native_matrix':NATIVE_MATRIX,'extraction_policy':EXTRACTION_POLICY,
        'shared_negative_normalizer_policy':nr.EXTRACTION_POLICY,
        'energy_balance':{**built['energy_balance'], 'constraint_indices':built['energy_balance_row_indices']},
        'variables':[{'index':v.idx,'name':v.name,'type':v.var_type,
            'lower':number(v.lb),'upper':number(v.ub),'solution':number(v.x)} for v in built['model'].vars],
        'mapping':{'trip_ids':[t.id for t in case.trips],
            'movement_ids':[m.id for m in case.movements],'intervals':built['compiled']['intervals'],
            'movement_selection':[v.idx for v in built['x']],
            'soc_before':[v.idx for v in built['soc_before']],
            'soc_after':[v.idx for v in built['soc_after']],
            'grid_energy':[{'key':list(key),'variable':v.idx} for key,v in built['charge'].items()],
            'market_load':[v.idx for v in built['loads']],
            'epigraph':[v.idx for v in built.get('epigraph',[])]}}


def _project_charge_energy(case, compiled, owners, raw, raw_load, record=None, round_index=0):
    """Disclosed compact-only projection under one exact incumbent-wide budget."""
    Q = Fraction
    def emit(stage, ledger):
        if record:
            record({'event':'charge_projection','round':round_index,'stage':stage,**ledger})
    def normalized_record(details):
        if record:
            record({'event':'charge_normalization','round':round_index,**details})
    normalized, negative = nr.normalize_charge_energy(raw, normalized_record)
    periods = len(case.market_edges_min)-1
    raw_sums, projected_sums = [Q(0) for _ in range(periods)], [Q(0) for _ in range(periods)]
    projected, changes = {}, []
    orphan = Q(0)
    for key, amount in raw.items():
        if (not isinstance(key, tuple) or len(key) != 2
                or any(type(v) is not int for v in key)):
            raise ValueError('Malformed compact charge key')
        j,k = key
        if not (0 <= j < len(case.movements) and 0 <= k < len(compiled['intervals'])):
            raise ValueError('Unknown compact charge key')
        mode = case.movements[j].id
        interval = compiled['intervals'][k]
        if mode not in interval['visits']:
            raise ValueError('Compact charge key has unavailable visit')
        t = interval['period']
        if not 0 <= t < periods:
            raise ValueError('Compact charge key has invalid market period')
        raw_sums[t] += Q(amount)
        value = normalized[key]
        if value > 0 and mode not in owners:
            orphan += Q(value)
            value = 0.0
            reason = 'positive-unselected-to-zero'
        elif amount < 0:
            reason = 'negative-to-zero'
        else:
            reason = None
        projected[key] = value
        projected_sums[t] += Q(value)
        if reason:
            changes.append({'key':list(key),'mode':mode,'interval':k,'period':t,
                'selected':mode in owners,'reason':reason,'raw_kwh':amount,
                'raw_repr':repr(amount),'projected_kwh':value,'projected_repr':repr(value)})
    n = Q(negative['negative_l1_exact'])
    cap = Q(nr.ROUNDOFF_BUDGET_KWH)
    load_residual = sum((abs(Q(v)-r) for v,r in zip(raw_load,raw_sums)),Q(0))
    projection = n+orphan
    ledger = {'policy':EXTRACTION_POLICY,'shared_negative_normalizer_policy':nr.EXTRACTION_POLICY,
        'budget_kwh':nr.ROUNDOFF_BUDGET_KWH,'budget_exact':str(cap),
        'negative_l1_exact':str(n),'orphan_positive_l1_exact':str(orphan),
        'raw_to_projected_l1_exact':str(projection),'raw_to_projected_l1_kwh':float(projection),
        'raw_load_row_residual_l1_exact':str(load_residual),
        'changes':changes,'periods':[{'period':t,'raw_solver_load_kwh':raw_load[t],
            'raw_solver_load_repr':repr(raw_load[t]),'raw_charge_sum_exact':str(raw_sums[t]),
            'projected_charge_sum_exact':str(projected_sums[t]),
            'native_minus_raw_charge_exact':str(Q(raw_load[t])-raw_sums[t]),
            'projected_minus_raw_charge_exact':str(projected_sums[t]-raw_sums[t])}
            for t in range(periods)]}
    emit('before_budget',ledger)
    if projection+load_residual > cap:
        raise ValueError('Whole-incumbent charge projection exceeds roundoff budget')
    return projected, negative, ledger, projection+load_residual, projected_sums


def _extract(case,built,record=None,round_index=0):
    def value(var):
        if var.x is None or not math.isfinite(float(var.x)):
            raise ValueError('Missing/nonfinite native variable')
        return float(var.x)
    selected = [m.id for j,m in enumerate(case.movements) if value(built['x'][j])>0.5]
    vehicles,owners = recover_paths(case,selected)
    raw_energies = {key:value(var) for key,var in built['charge'].items()}
    raw_load = [value(v) for v in built['loads']]
    projected,correction,ledger,spent,projected_sums = _project_charge_energy(
        case,built['compiled'],owners,raw_energies,raw_load,record,round_index)
    energies = {}
    for (j,k),amount in projected.items():
        if amount != 0:
            mid = case.movements[j].id
            energies[owners[mid],mid,k] = amount
    loads = [0.]*(len(case.market_edges_min)-1)
    for (_,_,k),amount in energies.items():
        loads[built['compiled']['intervals'][k]['period']] += amount
    H_defect = sum((abs(Fraction(h)-p) for h,p in zip(loads,projected_sums)),Fraction(0))
    spent += H_defect
    for row,load in zip(ledger['periods'],loads):
        row['physical_plan_load_kwh'] = load
        row['physical_plan_load_repr'] = repr(load)
        row['plan_minus_projected_exact'] = str(Fraction(load)-Fraction(row['projected_charge_sum_exact']))
        row['plan_minus_native_exact'] = str(Fraction(load)-Fraction(row['raw_solver_load_kwh']))
    ledger['plan_sum_residual_l1_exact'] = str(H_defect)
    ledger['pre_decode_total_exact'] = str(spent)
    ledger['pre_decode_accepted'] = spent <= Fraction(nr.ROUNDOFF_BUDGET_KWH)
    if record: record({'event':'charge_projection','round':round_index,'stage':'before_decoding',**ledger})
    if not ledger['pre_decode_accepted']:
        raise ValueError('Whole-incumbent charge/load correction exceeds roundoff budget')
    charges,decoding = nr.decode_serial(case,built['compiled'],energies,
        return_diagnostics=True,prior_correction_exact=ledger['raw_to_projected_l1_exact'])
    if record: record({'event':'serial_decoding','round':round_index,**decoding,'charges':charges})
    spent += Fraction(decoding['capacity_excess_exact'])+Fraction(decoding['materialized_session_excess_exact'])
    ledger['interval_capacity_excess_exact'] = decoding['capacity_excess_exact']
    ledger['session_capacity_excess_exact'] = decoding['materialized_session_excess_exact']
    ledger['pre_replay_total_exact'] = str(spent)
    ledger['pre_replay_accepted'] = spent <= Fraction(nr.ROUNDOFF_BUDGET_KWH)
    if record: record({'event':'charge_projection','round':round_index,'stage':'before_replay',**ledger})
    if not ledger['pre_replay_accepted']:
        raise ValueError('Whole-incumbent charge/decoding correction exceeds roundoff budget')
    raw_charge_load = [math.fsum(amount for (_,k),amount in raw_energies.items()
        if built['compiled']['intervals'][k]['period']==t) for t in range(len(loads))]
    if any(abs(a-b)>nr.ENERGY_TOL for a,b in zip(raw_load,loads)):
        raise ValueError('Raw native aggregate disagrees with physical charge')
    lookup = {m.id:m for m in case.movements}
    ops = len(vehicles)*case.vehicle_cost+case.deadhead_cost_per_min*sum(
        l.arrive_min-l.depart_min for v in vehicles for mid in v['movements'] for l in lookup[mid].legs)
    plan = {'schema':nr.SCHEMA,'case_identity':case.identity(),'formulation':FORMULATION,
        'native_matrix':NATIVE_MATRIX,'extraction_policy':EXTRACTION_POLICY,
        'vehicles':vehicles,'charges':charges,'load':loads,'ops_cost':ops,
        'raw_solver_load':raw_load,'raw_charge_load':raw_charge_load,
        'roundoff':{'negative_correction':correction,'serial_decoding':decoding,
                   'projection':ledger,'load_delta_kwh':[a-b for a,b in zip(loads,raw_charge_load)],
                   'native_load_delta_kwh':[a-b for a,b in zip(loads,raw_load)]}}
    plan['replay'] = nr.replay_native(case,plan)
    replay_defect = sum((abs(Fraction(a)-Fraction(b)) for a,b in
        zip(plan['replay']['load'],loads)),Fraction(0))
    spent += replay_defect
    ledger['replay_load_residual_l1_exact'] = str(replay_defect)
    ledger['whole_incumbent_total_exact'] = str(spent)
    ledger['whole_incumbent_total_kwh'] = float(spent)
    ledger['remaining_budget_exact'] = str(Fraction(nr.ROUNDOFF_BUDGET_KWH)-spent)
    ledger['accepted'] = spent <= Fraction(nr.ROUNDOFF_BUDGET_KWH)
    if record: record({'event':'charge_projection','round':round_index,'stage':'final',**ledger})
    if not ledger['accepted']:
        raise ValueError('Whole-incumbent replay load correction exceeds roundoff budget')
    return plan


# The native matrix and bound guards stay unchanged; compact extraction has a
# separate prospective identity and objective-correction ledger.
def solve_pricing(case, prices, budget=Budget(), record=None):
    _check_prices(case, prices)
    _check_budget(budget)
    deadline = time.monotonic()+budget.wall_seconds
    built = build_feasible_model(case, budget.backend)
    attach_objective(built, "linear", prices)
    if record:
        record({"event": "native_start", "round": 0})
    stats = _optimize_once(built, budget, deadline)
    if record:
        record({"event": "native_status", "round": 0, "stats": stats})
    result = {"case_identity": case.identity(), "formulation": FORMULATION,
              "native_matrix": NATIVE_MATRIX,"extraction_policy":EXTRACTION_POLICY,
              "objective": "complete-fleet-linear",
              "prices": list(prices), "stats": stats, "status": "unresolved"}
    if stats["status"] == "INFEASIBLE":
        return {**result, "status": "infeasible"}
    if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
        return result
    if record:
        record({"event": "native_incumbent", "round": 0, **capture_incumbent(case, built)})
    plan = _extract(case, built, record=record, round_index=0)
    replay = replay_native(case, plan, prices)
    raw_load = plan['raw_solver_load']
    physical_load = replay['load']
    raw_objective = plan['ops_cost']+sum(p*l for p,l in zip(prices,raw_load))
    delta_exact = sum((Fraction(p)*(Fraction(h)-Fraction(l))
        for p,h,l in zip(prices,physical_load,raw_load)),Fraction(0))
    delta = replay['pricing_objective']-raw_objective
    if not math.isfinite(raw_objective) or abs(stats['incumbent']-raw_objective)>nr.OBJECTIVE_TOL:
        raise ValueError('Native linear incumbent differs from saved solver-load objective')
    if record:
        record({"event": "objective_reconstruction", "round": 0,
                "linear_objective": replay["pricing_objective"],
                "raw_solver_load_objective":raw_objective,
                "charge_correction_objective_delta": delta,
                "charge_correction_objective_delta_exact":str(delta_exact),
                "native_incumbent": stats["incumbent"]})
    lower, upper = admit_bound(stats, replay["pricing_objective"])
    result.update(plan=plan, lower=lower, upper=upper, gap=upper-lower,
                  charge_correction_objective_delta=delta,
                  charge_correction_objective_delta_exact=str(delta_exact),
                  status="certified" if upper-lower <= budget.epsilon else "bounded")
    return result


def solve_planner(case, a, b, budget=Budget(), record=None):
    _check_market(case, a, b)
    _check_budget(budget)
    deadline = time.monotonic()+budget.wall_seconds
    tangents = [[(float(aa), 0.0)] for aa in a]
    lower, upper, best, records = -math.inf, math.inf, None, []
    status = "unresolved"
    for _ in range(budget.max_rounds):
        if time.monotonic() >= deadline:
            break
        built = build_feasible_model(case, budget.backend)
        attach_objective(built, "tangents", tangents)
        snapshot = [[list(p) for p in rows] for rows in tangents]
        if record:
            record({"event": "native_start", "round": len(records), "tangents": snapshot})
        stats = _optimize_once(built, budget, deadline)
        if record:
            record({"event": "native_status", "round": len(records), "stats": stats})
        iteration = {"stats": stats, "tangents": snapshot}
        records.append(iteration)
        if stats["status"] == "INFEASIBLE":
            if best is not None:
                raise ValueError("Tangent model infeasible after a replay-valid native plan")
            return {"case_identity": case.identity(), "formulation":FORMULATION,
                    "native_matrix":NATIVE_MATRIX,"extraction_policy":EXTRACTION_POLICY,
                    "status": "infeasible", "rounds": records}
        if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
            break
        if record:
            record({"event": "native_incumbent", "round": len(records)-1, **capture_incumbent(case, built)})
        plan = _extract(case, built, record=record, round_index=len(records)-1)
        physical_load = plan['replay']['load']
        true = plan["ops_cost"]+true_cost(a, b, physical_load)
        envelope = plan["ops_cost"]+sum(max(slope*load+intercept for slope, intercept in rows)
                                        for load, rows in zip(physical_load, snapshot))
        raw_charge_load = plan['raw_solver_load']
        raw_envelope = plan["ops_cost"]+sum(max(slope*load+intercept for slope, intercept in rows)
                                            for load, rows in zip(raw_charge_load, snapshot))
        raw_true = plan['ops_cost']+true_cost(a,b,raw_charge_load)
        Q = Fraction
        raw_q, physical_q = [Q(v) for v in raw_charge_load], [Q(v) for v in physical_load]
        exact_envelope = lambda loads: sum((max(Q(slope)*load+Q(intercept) for slope,intercept in rows)
            for load,rows in zip(loads,snapshot)),Q(0))
        exact_true = lambda loads: sum((Q(aa)*load+Q(bb)*load*load/2
            for aa,bb,load in zip(a,b,loads)),Q(0))
        objective_deltas = {"pwl_charge_correction_delta": envelope-raw_envelope,
            "pwl_charge_correction_delta_exact":str(exact_envelope(physical_q)-exact_envelope(raw_q)),
            "true_charge_correction_delta": true-raw_true,
            "true_charge_correction_delta_exact":str(exact_true(physical_q)-exact_true(raw_q))}
        if not math.isfinite(raw_envelope) or stats['incumbent'] < raw_envelope-nr.OBJECTIVE_TOL:
            raise ValueError('Native tangent incumbent differs from saved solver-load envelope')
        if record:
            record({"event": "objective_reconstruction", "round": len(records)-1,
                    "true_cost": true, "pwl_objective": envelope,
                    "raw_solver_load_true_cost":raw_true,
                    "raw_solver_load_pwl_objective":raw_envelope,
                    "native_incumbent": stats["incumbent"], **objective_deltas})
        lo, hi = admit_bound(stats, true, envelope, allow_epigraph_slack=True)
        iteration.update(objective_deltas)
        iteration["replayed_tangent_objective"] = envelope
        iteration["native_epigraph_slack"] = stats["incumbent"]-envelope
        iteration.update(plan=plan, lower=lo, upper=hi)
        if record:
            record({"event": "replayed_iteration", "round": len(records)-1, **iteration})
        lower = max(lower, lo)
        if hi < upper:
            upper, best = hi, plan
        if lower > upper+BOUND_GUARD:
            raise ValueError("Planner enclosure reversed")
        status = "bounded"
        if upper-lower <= budget.epsilon:
            status = "certified"
            break
        for t, load in enumerate(physical_load):
            tangents[t].append((float(a[t]+b[t]*load), float(-0.5*b[t]*load*load)))
    result = {"case_identity": case.identity(), "formulation":FORMULATION,
              "native_matrix":NATIVE_MATRIX,"extraction_policy":EXTRACTION_POLICY,
              "status": status, "a": list(a), "b": list(b), "rounds": records}
    if best is not None:
        result.update(plan=best, lower=lower, upper=upper, gap=upper-lower)
    return result
