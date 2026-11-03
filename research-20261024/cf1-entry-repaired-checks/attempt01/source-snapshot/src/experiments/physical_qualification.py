"""Bounded continuous-charging qualification; never reads experimental data.

Only full-slot availability is supported. Shared limits constrain every entire
fleet structure before convexification. Numerical enclosures remain conditional
on CBC optimality/feasibility tolerances; they are not rational certificates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import mip
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.enumerate_tiny import enumerate_structures
from egglab.instance import Instance, Trip
from egglab.market import AffineMarket

TOL = 1e-7
PWL_TOL = 1e-5
CALL_SECONDS = 10.0
CASE_SECONDS = 40.0
PROCESS_SECONDS = 240.0


def fixtures():
    def pair(name, b=.2, buses=2, cap=None, duplicate=False, replenish=False):
        if replenish:
            trips = [Trip('service', 0, 60, 'D', 'D', 1.),
                     Trip('terminal_marker', 180, 240, 'D', 'D', 0.)]
        else:
            trips = [Trip(f't{i}', st, st+60, 'D', 'D', 15.)
                     for i, st in enumerate([0, 0, 180, 180] if duplicate else [0, 180])]
        inst = Instance(name, trips, 'D', {}, {},
                        battery_kwh=1. if replenish else 20.,
                        soc0_kwh=1. if replenish else 20., soc_min_kwh=0.,
                        soc_end_kwh=1. if replenish else 0.,
                        charge_power_kw=1. if replenish else 10.,
                        n_slots=4, slot_min=60, max_vehicles=buses,
                        vehicle_fixed_cost=0. if replenish else 7., dh_cost_per_min=1.,
                        meta={'source': 'direct seed-free engineering fixture',
                              'terminal_marker': replenish})
        market = AffineMarket(np.full(4, 0. if replenish else .1),
                              np.full(4, b), np.zeros(4), name=name)
        return inst, market, cap
    return [pair('linear_split', b=0), pair('convex_split'),
            pair('forced_one_bus', buses=1),
            pair('capacity_filters_structure', cap=[0., 4., 4., 0.]),
            pair('replenished_terminal', b=2., buses=1, replenish=True),
            pair('replenished_infeasible', b=2., buses=1, replenish=True,
                 cap=[0., .4, .4, 0.]),
            pair('two_bus_uncapped', duplicate=True),
            pair('two_bus_shared_power', duplicate=True, cap=[0., 8., 12., 0.])]


def validate_grid(inst, cap):
    if (inst.slot_min <= 0 or inst.n_slots <= 0 or len({t.id for t in inst.trips}) != len(inst.trips)
            or any(t.start_min < 0 or t.end_min < t.start_min or
                   t.end_min > inst.horizon_min or t.start_min % inst.slot_min or
                   t.end_min % inst.slot_min for t in inst.trips)
            or any(v % inst.slot_min for v in inst.dh_min.values())):
        raise ValueError('qualification requires distinct trips and aligned in-horizon events')
    if cap is not None and (len(cap) != inst.n_slots or
                            any(not math.isfinite(v) or v < 0 for v in cap)):
        raise ValueError('invalid shared power energy caps')


def replay(inst, structure, charges, weight=1., cap=None):
    """Recompute physical trajectories from recorded energy, without model access.

    Scaled replay also checks lambda=0 blocks; no tiny-weight division is used.
    Tolerance is absolute in kWh. These checks support numerical qualification.
    """
    validate_grid(inst, cap)
    if not math.isfinite(weight) or weight < -TOL:
        raise ValueError('invalid structure weight')
    seqs, kinds = structure['sequences'], structure['kinds']
    if len(seqs) != len(kinds) or not 1 <= len(seqs) <= inst.max_vehicles:
        raise ValueError('invalid fleet/arc count')
    if Counter(t for seq in seqs for t in seq) != Counter(t.id for t in inst.trips):
        raise ValueError('trip coverage mismatch')
    tripmap = {t.id: t for t in inst.trips}
    energy = {}
    for event in charges:
        key = (event['chain'], event['edge'], event['slot'])
        value = event['energy']
        if key in energy or not math.isfinite(value) or value < -TOL:
            raise ValueError('invalid or duplicate charging event')
        energy[key] = value
    used, load, dh_minutes = set(), [0.]*inst.n_slots, 0.
    for ci, (seq, ck) in enumerate(zip(seqs, kinds)):
        if not seq or len(ck) != len(seq)-1:
            raise ValueError('empty chain or arc count mismatch')
        first, last = tripmap[seq[0]], tripmap[seq[-1]]
        dh_minutes += inst.dhm(inst.depot, first.start_loc) + inst.dhm(last.end_loc, inst.depot)
        if first.start_min < inst.dhm(inst.depot, first.start_loc):
            raise ValueError('pull-out precedes horizon')
        soc = (inst.soc0_kwh-inst.dhk(inst.depot, first.start_loc))*weight
        for j, tid in enumerate(seq):
            tr = tripmap[tid]
            if j:
                prev = tripmap[seq[j-1]]
                if ck[j-1] == 'dir':
                    travel = inst.dhm(prev.end_loc, tr.start_loc)
                    if prev.end_min+travel > tr.start_min:
                        raise ValueError('overlapping direct trips')
                    dh_minutes += travel
                    soc -= inst.dhk(prev.end_loc, tr.start_loc)*weight
                elif ck[j-1] == 'dep':
                    arrive = prev.end_min+inst.dhm(prev.end_loc, inst.depot)
                    depart = tr.start_min-inst.dhm(inst.depot, tr.start_loc)
                    if arrive > depart or arrive % inst.slot_min or depart % inst.slot_min:
                        raise ValueError('invalid aligned depot window')
                    dh_minutes += inst.dhm(prev.end_loc, inst.depot)+inst.dhm(inst.depot, tr.start_loc)
                    soc -= inst.dhk(prev.end_loc, inst.depot)*weight
                    if soc < inst.soc_min_kwh*weight-TOL:
                        raise ValueError('depot arrival SOC violation')
                    for slot in range(arrive//inst.slot_min, depart//inst.slot_min):
                        key = (ci, j-1, slot)
                        value = energy.get(key, 0.)
                        if not 0 <= slot < inst.n_slots or value > inst.charge_power_kw*inst.slot_min/60*weight+TOL:
                            raise ValueError('charging power/horizon violation')
                        used.add(key)
                        load[slot] += value
                        soc += value
                        if soc > inst.battery_kwh*weight+TOL:
                            raise ValueError('battery overfill')
                    soc -= inst.dhk(inst.depot, tr.start_loc)*weight
                else:
                    raise ValueError('unknown arc kind')
            if not inst.soc_min_kwh*weight-TOL <= soc <= inst.battery_kwh*weight+TOL:
                raise ValueError('trip start SOC violation')
            soc -= tr.energy_kwh*weight
            if soc < inst.soc_min_kwh*weight-TOL:
                raise ValueError('trip end SOC violation')
        soc -= inst.dhk(last.end_loc, inst.depot)*weight
        if soc < inst.soc_end_kwh*weight-TOL:
            raise ValueError('terminal SOC violation')
    if set(energy)-used:
        raise ValueError('charging outside declared depot window')
    if cap is not None and any(v > c*weight+TOL for v, c in zip(load, cap)):
        raise ValueError('shared power violation')
    ops = len(seqs)*inst.vehicle_fixed_cost + dh_minutes*inst.dh_cost_per_min
    if abs(ops-structure['ops_cost']) > TOL:
        raise ValueError('intrinsic operating cost mismatch')
    return {'load': load, 'scaled_ops': ops*weight, 'replay_ok': True}


def add_block(model, inst, structure, lam, cap):
    """Instrumented complete continuous polytope, restricted to aligned windows."""
    loads = [[] for _ in range(inst.n_slots)]
    events = []
    tripmap = {t.id: t for t in inst.trips}
    for ci, (seq, kinds) in enumerate(zip(structure['sequences'], structure['kinds'])):
        after = None
        for j, tid in enumerate(seq):
            trip = tripmap[tid]
            before = model.add_var(lb=0.)
            if j == 0:
                model += before == (inst.soc0_kwh-inst.dhk(inst.depot, trip.start_loc))*lam
            else:
                prev = tripmap[seq[j-1]]
                if kinds[j-1] == 'dir':
                    model += before == after-inst.dhk(prev.end_loc, trip.start_loc)*lam
                else:
                    arrive = prev.end_min+inst.dhm(prev.end_loc, inst.depot)
                    depart = trip.start_min-inst.dhm(inst.depot, trip.start_loc)
                    first_dh = inst.dhk(prev.end_loc, inst.depot)
                    second_dh = inst.dhk(inst.depot, trip.start_loc)
                    es = []
                    for slot in range(arrive//inst.slot_min, depart//inst.slot_min):
                        e = model.add_var(lb=0.)
                        model += e <= inst.charge_power_kw*inst.slot_min/60*lam
                        es.append(e)
                        loads[slot].append(e)
                        events.append((ci, j-1, slot, e))
                    ch = mip.xsum(es)
                    model += before == after-(first_dh+second_dh)*lam+ch
                    model += after-first_dh*lam >= inst.soc_min_kwh*lam
                    model += after-first_dh*lam+ch <= inst.battery_kwh*lam
            model += before >= inst.soc_min_kwh*lam
            model += before <= inst.battery_kwh*lam
            after = model.add_var(lb=0.)
            model += after == before-trip.energy_kwh*lam
            model += after >= inst.soc_min_kwh*lam
        model += after-inst.dhk(tripmap[seq[-1]].end_loc, inst.depot)*lam >= inst.soc_end_kwh*lam
    if cap is not None:
        for slot, limit in enumerate(cap):
            model += mip.xsum(loads[slot]) <= limit*lam
    return loads, events


def accept_status(status):
    if status not in ('OPTIMAL', 'INFEASIBLE'):
        raise RuntimeError('unresolved solver status: '+status)


def solve(inst, market, structures, cap, convex, deadline, calls):
    validate_grid(inst, cap)
    model = mip.Model(name='physical-qualification', solver_name=mip.CBC)
    model.verbose = 0
    model.threads = 1
    model.infeas_tol = 1e-9
    model.opt_tol = 1e-9
    lams = [model.add_var(lb=0., ub=1.) for _ in structures]
    model += mip.xsum(lams) == 1.
    if not convex and len(structures) != 1:
        raise ValueError('physical solve needs one complete structure')
    blocks = [add_block(model, inst, s, lam, cap) for s, lam in zip(structures, lams)]
    load = [model.add_var(lb=0.) for _ in range(inst.n_slots)]
    cost = [model.add_var(lb=0.) for _ in range(inst.n_slots)]
    for t in range(inst.n_slots):
        model += load[t] == mip.xsum(e for (ls, _) in blocks for e in ls[t])
    model.objective = mip.xsum(s['ops_cost']*w for s, w in zip(structures, lams))+mip.xsum(cost)
    # Valid tangent lower envelope. The true cost is nonnegative for this grid.
    for t, (slope, intercept) in enumerate(market.system_delta_tangents_at(np.zeros(inst.n_slots))):
        model += cost[t] >= slope*load[t]+intercept
    for iteration in range(160):
        remaining = deadline-time.perf_counter()
        if remaining <= 0:
            raise TimeoutError('fixture budget exhausted')
        started = time.perf_counter()
        status = model.optimize(max_seconds=min(CALL_SECONDS, remaining)).name
        calls.append({'status': status, 'wall_s': time.perf_counter()-started,
                      'threads': model.threads, 'iteration': iteration,
                      'phase': 'ch' if convex else 'physical',
                      'structures': len(structures)})
        accept_status(status)
        if status == 'INFEASIBLE':
            return {'status': status}
        value, bound = float(model.objective_value), float(model.objective_bound)
        if not all(math.isfinite(v) for v in (value, bound)):
            raise RuntimeError('nonfinite solver objective/bound')
        witness, aggregate, ops = [], np.zeros(inst.n_slots), 0.
        for s, weight_var, (_, variables) in zip(structures, lams, blocks):
            weight = float(weight_var.x)
            charges = [{'chain': ci, 'edge': edge, 'slot': slot, 'energy': float(var.x)}
                       for ci, edge, slot, var in variables]
            evidence = replay(inst, s, charges, weight, cap)
            aggregate += np.asarray(evidence['load'])
            ops += evidence['scaled_ops']
            witness.append({'structure': s, 'weight': weight, 'charges': charges,
                            'replay': evidence})
        if abs(sum(w['weight'] for w in witness)-1.) > TOL:
            raise RuntimeError('weights do not sum to one')
        if np.max(np.abs(aggregate-np.asarray([v.x for v in load]))) > TOL:
            raise RuntimeError('aggregate load differs from replay')
        true = ops+market.system_delta_true(aggregate)
        allowance = TOL*max(1., abs(value), abs(bound), abs(true))
        if value > true+allowance or bound > value+allowance:
            raise RuntimeError('objective enclosure direction violated')
        if true-min(value, bound) <= PWL_TOL:
            return {'status': status, 'lower': min(value, bound)-allowance,
                    'upper': true+allowance, 'exact_evaluation': true,
                    'model_value': value, 'solver_bound': bound,
                    'numerical_allowance': allowance, 'load': aggregate.tolist(),
                    'witness': witness, 'refinements': iteration}
        for t, (slope, intercept) in enumerate(market.system_delta_tangents_at(aggregate)):
            model += cost[t] >= slope*load[t]+intercept
    raise RuntimeError('tangent refinement cap exhausted')


def qualify(inst, market, cap):
    start = time.perf_counter()
    structures = enumerate_structures(inst)
    if not structures or len(structures) > 32:
        raise RuntimeError('structure admission cap exceeded')
    calls = []
    deadline = start+CASE_SECONDS
    ch = solve(inst, market, structures, cap, True, deadline, calls)
    physical = [solve(inst, market, [s], cap, False, deadline, calls) for s in structures]
    feasible = [v for v in physical if v['status'] == 'OPTIMAL']
    result = {'name': inst.name, 'instance': inst.canonical(), 'instance_hash': inst.hash(),
              'market': {'a': market.a.tolist(), 'b': market.b.tolist(), 'U': market.U.tolist()},
              'shared_power_slot_kwh': cap, 'structures': structures,
              'ch': ch, 'physical': physical, 'calls': calls,
              'bound_scope': 'numerical CBC and replay tolerance conditional'}
    if not feasible:
        if ch['status'] != 'INFEASIBLE':
            raise RuntimeError('CH feasible but every physical structure infeasible')
        result['status'] = 'INFEASIBLE'
    else:
        if ch['status'] != 'OPTIMAL':
            raise RuntimeError('physical feasible but CH infeasible')
        dl, du = min(v['lower'] for v in feasible), min(v['upper'] for v in feasible)
        result.update(status='OPTIMAL', d_lower=dl, d_upper=du,
                      gap_interval=[dl-ch['upper'], du-ch['lower']],
                      physical_best=min(range(len(physical)),
                                        key=lambda j: physical[j].get('upper', float('inf'))))
    result['wall_s'] = time.perf_counter()-start
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def run_worker(output):
    import importlib.metadata
    root = Path(__file__).resolve().parents[2]
    write_json(output/'environment.json', {
        'python': sys.version, 'executable': sys.executable,
        'versions': {p: importlib.metadata.version(p) for p in ('mip', 'numpy')},
        'head': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256': hashlib.sha256((root/'doc/PHYSICAL_QUALIFICATION_PROTOCOL_20260921.md').read_bytes()).hexdigest(),
        'threads': 1, 'feasibility_tolerance': TOL, 'solver_tolerance': 1e-9,
        'pwl_tolerance': PWL_TOL, 'case_seconds': CASE_SECONDS})
    for inst, market, cap in fixtures():
        try:
            result = qualify(inst, market, cap)
        except Exception as exc:
            write_json(output/(inst.name+'.json'), {'name': inst.name, 'status': 'FAILED',
                       'exception': type(exc).__name__, 'message': str(exc)})
            raise
        write_json(output/(inst.name+'.json'), result)
        print(json.dumps({'name': inst.name, 'status': result['status'],
                          'gap_interval': result.get('gap_interval'), 'wall_s': result['wall_s']}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        run_worker(args.output)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output/'frozen-fixtures.json', [
        {'instance': i.canonical(), 'a': m.a.tolist(), 'b': m.b.tolist(),
         'U': m.U.tolist(), 'shared_power_slot_kwh': c} for i, m, c in fixtures()])
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    start = time.perf_counter()
    with (args.output/'stdout.txt').open('x') as stdout, (args.output/'stderr.txt').open('x') as stderr:
        proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                                 '--worker', '--output', str(args.output.resolve())],
                                env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        timeout = False
        try:
            proc.wait(timeout=PROCESS_SECONDS)
        except subprocess.TimeoutExpired:
            timeout = True
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    write_json(args.output/'process.json', {'exit': proc.returncode, 'timed_out': timeout,
               'wall_s': time.perf_counter()-start, 'cap_s': PROCESS_SECONDS})
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
