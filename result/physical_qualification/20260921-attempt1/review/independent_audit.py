"""Solver-free, non-author audit of the frozen physical qualification outputs.

Reads saved JSON only; does not import the experiment or any solver package.
Independent analytic controls are fixed below, not fitted to output values.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path

TOL = 1e-7
EXPECTED = {
    'linear_split': (Fraction(8), Fraction(8), 3, 2),
    'convex_split': (Fraction(13), Fraction(61, 5), 3, 2),
    'forced_one_bus': (Fraction(13), Fraction(13), 2, 1),
    'capacity_filters_structure': (Fraction(14), Fraction(14), 3, 1),
    'replenished_terminal': (Fraction(1, 2), Fraction(1, 2), 2, 1),
    'replenished_infeasible': (None, None, 2, 0),
    'two_bus_uncapped': (Fraction(36), Fraction(36), 8, 2),
    'two_bus_shared_power': (Fraction(184, 5), Fraction(184, 5), 8, 2),
}


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def close(x, y, message, tolerance=TOL):
    check(math.isfinite(x) and math.isfinite(y) and abs(x-y) <= tolerance,
          message + ': ' + repr((x, y)))


def signature(s):
    return tuple(sorted((tuple(seq), tuple(kinds))
                        for seq, kinds in zip(s['sequences'], s['kinds'])))


def independently_enumerate(inst):
    """Restricted independent enumerator for the explicit all-depot fixtures."""
    trips = sorted(inst['trips'], key=lambda t: (t['start_min'], t['id']))
    partitions = [[]]
    for trip in trips:
        newer = []
        for part in partitions:
            for j in range(len(part)):
                if part[j][-1]['end_min'] <= trip['start_min']:
                    newer.append([chain + [trip] if k == j else chain[:]
                                  for k, chain in enumerate(part)])
            if len(part) < inst['max_vehicles']:
                newer.append([chain[:] for chain in part] + [[trip]])
        partitions = newer
    out = set()
    for part in partitions:
        n_edges = sum(len(chain)-1 for chain in part)
        for choices in itertools.product(('dir', 'dep'), repeat=n_edges):
            edge_iter = iter(choices)
            chains = []
            for chain in part:
                chains.append((tuple(t['id'] for t in chain),
                               tuple(next(edge_iter) for _ in chain[1:])))
            out.add(tuple(sorted(chains)))
    return out


def replay_raw(inst, structure, events, weight, cap, tolerance=TOL):
    check(math.isfinite(weight) and weight >= -tolerance, 'invalid weight')
    trips = {t['id']: t for t in inst['trips']}
    sequences, kinds = structure['sequences'], structure['kinds']
    check(len(sequences) == len(kinds) <= inst['max_vehicles'], 'fleet shape')
    check(Counter(sum(sequences, [])) == Counter(trips.keys()), 'trip coverage')
    assigned = {}
    for event in events:
        key = event['chain'], event['edge'], event['slot']
        check(all(isinstance(i, int) and not isinstance(i, bool) for i in key), 'event index type')
        check(key not in assigned, 'duplicate event')
        amount = event['energy']
        check(math.isfinite(amount) and amount >= -tolerance, 'invalid energy')
        assigned[key] = amount
    consumed = set()
    aggregate = [0.0] * inst['n_slots']
    trajectories = []
    for chain_index, (sequence, edges) in enumerate(zip(sequences, kinds)):
        check(sequence and len(edges) == len(sequence)-1, 'chain shape')
        soc = inst['soc0_kwh'] * weight
        trajectory = [soc]
        for index, trip_id in enumerate(sequence):
            trip = trips[trip_id]
            if index:
                previous = trips[sequence[index-1]]
                check(previous['end_min'] <= trip['start_min'], 'trip chronology')
                check(edges[index-1] in ('dir', 'dep'), 'unknown edge')
                if edges[index-1] == 'dep':
                    for slot in range(inst['n_slots']):
                        slot_lo = slot*inst['slot_min']
                        slot_hi = slot_lo+inst['slot_min']
                        overlap = max(0, min(slot_hi, trip['start_min'])
                                         - max(slot_lo, previous['end_min']))
                        if overlap:
                            key = chain_index, index-1, slot
                            amount = assigned.get(key, 0.)
                            check(amount <= weight*inst['charge_power_kw']*overlap/60+tolerance,
                                  'per-bus power')
                            soc += amount
                            aggregate[slot] += amount
                            consumed.add(key)
                            check(soc <= inst['battery_kwh']*weight+tolerance, 'battery overfill')
                            trajectory.append(soc)
            check(inst['soc_min_kwh']*weight-tolerance <= soc <= inst['battery_kwh']*weight+tolerance,
                  'SOC before service')
            soc -= trip['energy_kwh']*weight
            check(soc >= inst['soc_min_kwh']*weight-tolerance, 'SOC after service')
            trajectory.append(soc)
        check(soc >= inst['soc_end_kwh']*weight-tolerance, 'terminal SOC')
        trajectories.append(trajectory)
    check(not (set(assigned)-consumed), 'event outside depot arc/window')
    if cap is not None:
        check(all(load <= limit*weight+tolerance for load, limit in zip(aggregate, cap)), 'shared power')
    ops = len(sequences)*inst['vehicle_fixed_cost']
    close(ops, structure['ops_cost'], 'stored operating cost')
    return aggregate, ops*weight, trajectories


def audit_solve(result, inst, market, cap, expected, expected_structures):
    if expected is None:
        check(result['status'] == 'INFEASIBLE', 'expected infeasibility')
        return {'components': 0, 'positive_components': 0}
    check(result['status'] == 'OPTIMAL', 'expected optimal solve')
    witness = result['witness']
    check(len(witness) == len(expected_structures), 'wrong witness block count')
    check({signature(w['structure']) for w in witness} == expected_structures,
          'wrong witness structures')
    close(sum(w['weight'] for w in witness), 1., 'weight sum')
    aggregate = [0.]*inst['n_slots']
    ops = 0.
    positive = 0
    for component in witness:
        load, intrinsic, _ = replay_raw(inst, component['structure'], component['charges'],
                                        component['weight'], cap)
        for k, value in enumerate(load):
            aggregate[k] += value
            close(value, component['replay']['load'][k], 'stored component load')
        ops += intrinsic
        close(intrinsic, component['replay']['scaled_ops'], 'stored component ops')
        if component['weight'] > 1e-10:
            positive += 1
            normalized = [dict(e, energy=e['energy']/component['weight']) for e in component['charges']]
            replay_raw(inst, component['structure'], normalized, 1., cap, tolerance=1e-6)
        else:
            check(abs(component['weight']) <= 1e-10, 'unexpected tiny weight')
    for t, amount in enumerate(aggregate):
        close(amount, result['load'][t], 'stored aggregate')
    objective = ops + sum((a+b*u)*load+b*load*load/2
                          for a, b, u, load in zip(market['a'], market['b'], market['U'], aggregate))
    close(objective, result['exact_evaluation'], 'true objective recomputation')
    check(result['lower']-1e-10 <= float(expected) <= result['upper']+1e-10,
          'analytic optimum outside interval')
    allowance = result['numerical_allowance']
    close(allowance, 1e-7*max(1., abs(result['model_value']), abs(result['solver_bound']), abs(objective)),
          'numerical allowance', tolerance=1e-12)
    close(result['lower'], min(result['model_value'], result['solver_bound'])-allowance, 'lower arithmetic')
    close(result['upper'], objective+allowance, 'upper arithmetic')
    check(result['upper']-result['lower'] <= 1e-5+2*allowance+1e-8, 'unconverged enclosure')
    return {'components': len(witness), 'positive_components': positive}


def physical_expected(name, structure):
    if any(kind == 'dir' for chain in structure['kinds'] for kind in chain):
        return None
    if name == 'replenished_infeasible':
        return None
    if name == 'capacity_filters_structure' and len(structure['sequences']) == 1:
        return None
    if name.startswith('two_bus_'):
        return EXPECTED[name][0]
    if name == 'replenished_terminal':
        return Fraction(1, 2)
    if len(structure['sequences']) == 2:
        return Fraction(14)
    return Fraction(8 if name == 'linear_split' else 13)


def audit_case(data):
    name = data['name']
    expected_d, expected_ch, n_structures, n_feasible = EXPECTED[name]
    inst, market, cap = data['instance'], data['market'], data['shared_power_slot_kwh']
    marker = name.startswith('replenished_')
    double = name.startswith('two_bus_')
    expected_times = [0, 0, 180, 180] if double else [0, 180]
    check([t['start_min'] for t in inst['trips']] == expected_times and
          [t['end_min'] for t in inst['trips']] == [t+60 for t in expected_times], 'frozen trip times')
    check([t['energy_kwh'] for t in inst['trips']] == ([1., 0.] if marker else [15.]*len(expected_times)),
          'frozen trip energies')
    for key, expected in {'battery_kwh': 1. if marker else 20.,
                          'soc0_kwh': 1. if marker else 20., 'soc_min_kwh': 0.,
                          'soc_end_kwh': 1. if marker else 0.,
                          'charge_power_kw': 1. if marker else 10.,
                          'vehicle_fixed_cost': 0. if marker else 7.,
                          'max_vehicles': 1 if marker or name == 'forced_one_bus' else 2,
                          'dh_cost_per_min': 1.}.items():
        check(inst[key] == expected, 'frozen instance parameter '+key)
    check(market == {'a': [0. if marker else .1]*4,
                     'b': [2. if marker else (0. if name == 'linear_split' else .2)]*4,
                     'U': [0.]*4}, 'frozen market')
    expected_cap = {'capacity_filters_structure': [0., 4., 4., 0.],
                    'replenished_infeasible': [0., .4, .4, 0.],
                    'two_bus_shared_power': [0., 8., 12., 0.]}.get(name)
    check(cap == expected_cap, 'frozen shared cap')
    check(hashlib.sha256(json.dumps(inst, sort_keys=True).encode()).hexdigest()[:12] == data['instance_hash'],
          'instance hash')
    check(inst['depot'] == 'D' and inst['dh_min'] == [] and inst['dh_kwh'] == [], 'outside all-depot audit scope')
    check(all(t['start_loc'] == 'D' == t['end_loc'] for t in inst['trips']), 'outside depot scope')
    check(inst['n_slots'] == 4 and inst['slot_min'] == 60, 'unexpected grid')
    independently_found = independently_enumerate(inst)
    recorded = {signature(s) for s in data['structures']}
    check(len(data['structures']) == len(recorded) == n_structures, 'count/duplicate structures')
    check(recorded == independently_found, 'incomplete enumeration')
    for call in data['calls']:
        check(call['status'] in ('OPTIMAL', 'INFEASIBLE') and call['threads'] == 1,
              'unresolved status or wrong threads')
    check(data['wall_s'] <= 40., 'case wall-clock budget')
    ch_counts = audit_solve(data['ch'], inst, market, cap, expected_ch, independently_found)
    check(len(data['physical']) == n_structures, 'missing physical solves')
    physical_counts = []
    for structure, solve in zip(data['structures'], data['physical']):
        physical_counts.append(audit_solve(solve, inst, market, cap,
                                           physical_expected(name, structure), {signature(structure)}))
    feasible = [p for p in data['physical'] if p['status'] == 'OPTIMAL']
    check(len(feasible) == n_feasible, 'feasible structure count')
    if expected_d is not None:
        check(data['status'] == 'OPTIMAL', 'overall status')
        close(data['d_lower'], min(p['lower'] for p in feasible), 'D lower minimum')
        close(data['d_upper'], min(p['upper'] for p in feasible), 'D upper minimum')
        check(data['d_lower'] <= float(expected_d) <= data['d_upper'], 'D analytic inclusion')
        close(data['gap_interval'][0], data['d_lower']-data['ch']['upper'], 'gap lower arithmetic')
        close(data['gap_interval'][1], data['d_upper']-data['ch']['lower'], 'gap upper arithmetic')
        expected_gap = float(expected_d-expected_ch)
        check(data['gap_interval'][0] <= expected_gap <= data['gap_interval'][1], 'analytic gap inclusion')
    else:
        check(data['status'] == 'INFEASIBLE' and 'gap_interval' not in data, 'infeasible gap output')
    return {'name': name, 'structures': n_structures, 'feasible_structures': n_feasible,
            'solver_calls': len(data['calls']), 'expected_d': str(expected_d),
            'expected_ch': str(expected_ch), 'ch_components': ch_counts,
            'physical_components': sum(p['components'] for p in physical_counts), 'pass': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_directory', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    process = json.loads((args.output_directory/'process.json').read_text())
    check(process['exit'] == 0 and not process['timed_out'] and process['wall_s'] <= 240., 'process outcome/budget')
    reports = []
    hashes = {}
    saved_cases = {}
    frozen = {record['instance']['name']: record for record in
              json.loads((args.output_directory/'frozen-fixtures.json').read_text())}
    check(set(frozen) == set(EXPECTED), 'frozen fixture names')
    for name in EXPECTED:
        path = args.output_directory/(name+'.json')
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        data = json.loads(path.read_text())
        saved_cases[name] = data
        check(data['instance'] == frozen[name]['instance'] and
              data['market'] == {key: frozen[name][key] for key in ('a', 'b', 'U')} and
              data['shared_power_slot_kwh'] == frozen[name]['shared_power_slot_kwh'],
              'frozen configuration differs from run')
        reports.append(audit_case(data))
    mutations = []
    for mutation in ('missing_structure', 'event_outside_window', 'forged_load',
                     'forged_objective', 'forged_gap', 'unresolved_status', 'removed_capacity'):
        name = 'capacity_filters_structure' if mutation == 'removed_capacity' else 'convex_split'
        corrupt = copy.deepcopy(saved_cases[name])
        if mutation == 'missing_structure':
            corrupt['structures'].pop()
        elif mutation == 'event_outside_window':
            next(w for w in corrupt['ch']['witness'] if w['weight'] > .1 and w['charges'])['charges'][0]['slot'] = 0
        elif mutation == 'forged_load':
            corrupt['ch']['load'][1] += .1
        elif mutation == 'forged_objective':
            corrupt['ch']['exact_evaluation'] += .1
        elif mutation == 'forged_gap':
            corrupt['gap_interval'][0] += .1
        elif mutation == 'unresolved_status':
            next(p for p in corrupt['physical'] if p['status'] == 'OPTIMAL')['status'] = 'FEASIBLE'
        else:
            corrupt['shared_power_slot_kwh'] = None
        try:
            audit_case(corrupt)
        except AssertionError as exc:
            mutations.append({'mutation': mutation, 'rejected': True, 'reason': str(exc)})
        else:
            raise AssertionError('auditor accepted corruption '+mutation)
    report = {'scope': 'solver-free non-author raw-event and analytic audit', 'pass': True,
              'auditor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'process': process, 'cases': reports, 'result_sha256': hashes,
              'corrupted_output_rejections': mutations}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'pass': True, 'cases': len(reports),
                      'structures': sum(r['structures'] for r in reports),
                      'solver_calls': sum(r['solver_calls'] for r in reports)}))


if __name__ == '__main__':
    main()
