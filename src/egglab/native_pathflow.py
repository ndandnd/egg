"""Compact DAG path-flow realization of the native complete-fleet feasible set.

Research candidate only until its separate prospective qualification passes.
No optimizer import on module import; physical schema/replay are unchanged.
"""
from __future__ import annotations

from collections import defaultdict
import math
import time

from egglab import native_recharge as nr

FORMULATION = 'egg-native-pathflow-v1'
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
        model += sa[i] == sb[i]-t.energy_kwh
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
        model += residual <= M*(1-selected)
        model += residual >= -M*(1-selected)
    loads = [model.add_var(lb=0) for _ in range(len(case.market_edges_min)-1)]
    for t,L in enumerate(loads):
        model += L == mip.xsum(by_period[t])
    ops = case.vehicle_cost*mip.xsum(starts)+case.deadhead_cost_per_min*mip.xsum(
        x[j]*sum(l.arrive_min-l.depart_min for l in m.legs) for j,m in enumerate(case.movements))
    return {'model':model,'compiled':compiled,'x':x,'soc_before':sb,'soc_after':sa,
            'charge':charge,'loads':loads,'ops':ops,'physical_identity':case.identity(),
            'backend':backend,'backend_runtime':runtime,'formulation':FORMULATION,
            'constraint_count_before_objective':model.num_rows}


def capture_incumbent(case,built):
    def number(value):
        return {'value':float(value) if value is not None and math.isfinite(float(value)) else None,
                'repr':repr(value)}
    return {'case_identity':case.identity(),'formulation':FORMULATION,
        'extraction_policy':nr.EXTRACTION_POLICY,
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


def _extract(case,built,record=None,round_index=0):
    def value(var):
        if var.x is None or not math.isfinite(float(var.x)):
            raise ValueError('Missing/nonfinite native variable')
        return float(var.x)
    selected = [m.id for j,m in enumerate(case.movements) if value(built['x'][j])>0.5]
    vehicles,owners = recover_paths(case,selected)
    raw_energies = {key:value(var) for key,var in built['charge'].items()}
    def normalized_record(details):
        if record: record({'event':'charge_normalization','round':round_index,**details})
    normalized,correction = nr.normalize_charge_energy(raw_energies,normalized_record)
    energies = {}
    for (j,k),amount in normalized.items():
        if amount != 0:
            mid = case.movements[j].id
            if mid not in owners:
                raise ValueError('Positive charge on an unselected movement')
            energies[owners[mid],mid,k] = amount
    charges,decoding = nr.decode_serial(case,built['compiled'],energies,
        return_diagnostics=True,prior_correction_exact=correction['negative_l1_exact'])
    if record: record({'event':'serial_decoding','round':round_index,**decoding,'charges':charges})
    loads = [0.]*(len(case.market_edges_min)-1)
    for (_,_,k),amount in energies.items():
        loads[built['compiled']['intervals'][k]['period']] += amount
    raw_load = [value(v) for v in built['loads']]
    raw_charge_load = [math.fsum(amount for (_,k),amount in raw_energies.items()
        if built['compiled']['intervals'][k]['period']==t) for t in range(len(loads))]
    if any(abs(a-b)>nr.ENERGY_TOL for a,b in zip(raw_load,loads)):
        raise ValueError('Raw native aggregate disagrees with physical charge')
    lookup = {m.id:m for m in case.movements}
    ops = len(vehicles)*case.vehicle_cost+case.deadhead_cost_per_min*sum(
        l.arrive_min-l.depart_min for v in vehicles for mid in v['movements'] for l in lookup[mid].legs)
    plan = {'schema':nr.SCHEMA,'case_identity':case.identity(),'formulation':FORMULATION,
        'vehicles':vehicles,'charges':charges,'load':loads,'ops_cost':ops,
        'raw_solver_load':raw_load,'raw_charge_load':raw_charge_load,
        'roundoff':{'negative_correction':correction,'serial_decoding':decoding,
                   'load_delta_kwh':[a-b for a,b in zip(loads,raw_charge_load)]}}
    plan['replay'] = nr.replay_native(case,plan)
    return plan


# The two objective drivers below intentionally preserve the qualified native
# bound/extraction policy; only the builder and raw-variable mapping differ.
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
    result = {"case_identity": case.identity(), "objective": "complete-fleet-linear",
              "prices": list(prices), "stats": stats, "status": "unresolved"}
    if stats["status"] == "INFEASIBLE":
        return {**result, "status": "infeasible"}
    if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
        return result
    if record:
        record({"event": "native_incumbent", "round": 0, **capture_incumbent(case, built)})
    plan = _extract(case, built, record=record, round_index=0)
    replay = replay_native(case, plan, prices)
    delta = sum(p*(new-old) for p, new, old in zip(prices, plan["load"], plan.get("raw_charge_load", plan["load"])))
    if record:
        record({"event": "objective_reconstruction", "round": 0,
                "linear_objective": replay["pricing_objective"], "charge_correction_objective_delta": delta,
                "native_incumbent": stats["incumbent"]})
    lower, upper = admit_bound(stats, replay["pricing_objective"])
    result.update(plan=plan, lower=lower, upper=upper, gap=upper-lower,
                  charge_correction_objective_delta=delta,
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
            return {"case_identity": case.identity(), "status": "infeasible", "rounds": records}
        if stats["status"] not in ("OPTIMAL", "FEASIBLE") or stats.get("incumbent") is None:
            break
        if record:
            record({"event": "native_incumbent", "round": len(records)-1, **capture_incumbent(case, built)})
        plan = _extract(case, built, record=record, round_index=len(records)-1)
        true = plan["ops_cost"]+true_cost(a, b, plan["load"])
        envelope = plan["ops_cost"]+sum(max(slope*load+intercept for slope, intercept in rows)
                                        for load, rows in zip(plan["load"], snapshot))
        raw_charge_load = plan.get("raw_charge_load", plan["load"])
        raw_envelope = plan["ops_cost"]+sum(max(slope*load+intercept for slope, intercept in rows)
                                            for load, rows in zip(raw_charge_load, snapshot))
        objective_deltas = {"pwl_charge_correction_delta": envelope-raw_envelope,
            "true_charge_correction_delta": true-plan["ops_cost"]-true_cost(a, b, raw_charge_load)}
        if record:
            record({"event": "objective_reconstruction", "round": len(records)-1,
                    "true_cost": true, "pwl_objective": envelope,
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
        for t, load in enumerate(plan["load"]):
            tangents[t].append((float(a[t]+b[t]*load), float(-0.5*b[t]*load*load)))
    result = {"case_identity": case.identity(), "status": status, "a": list(a), "b": list(b), "rounds": records}
    if best is not None:
        result.update(plan=best, lower=lower, upper=upper, gap=upper-lower)
    return result
