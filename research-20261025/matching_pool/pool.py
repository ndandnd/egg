"""Three global route-only covers and their declared parallel-mode union."""
import hashlib
import math

import numpy as np
from scipy.optimize import linear_sum_assignment

from egglab import classical_controls as cc
from egglab import native_recharge as nr

POLICY = 'three-global-path-covers-parallel-mode-union-v1'
SEED = 17


def candidate_pool(case, *, check=lambda: None):
    """Return original movement IDs; no physical-feasibility or full-bound claim."""
    check()
    nr.validate_case(case)
    trips = sorted(case.trips, key=lambda t: (t.start_min, t.end_min, t.id))
    n = len(trips)
    if n not in (40, 80):
        raise ValueError('This pilot admits only the frozen40/80-trip cases')
    position, by_id = {t.id: i for i, t in enumerate(trips)}, {t.id: t for t in trips}
    slices = cc._slices(case)
    pairs, boundaries, nonchronological = {}, [], []
    for movement in case.movements:
        check()
        if movement.kind in ('pullout', 'pullin'):
            boundaries.append(movement.id)
            continue
        if movement.kind not in ('direct', 'depot'):
            raise ValueError('Unknown movement kind')
        before, after = by_id[movement.before], by_id[movement.after]
        if after.start_min < before.end_min or position[before.id] >= position[after.id]:
            nonchronological.append(movement.id)
            continue
        minutes = math.fsum(leg.arrive_min-leg.depart_min for leg in movement.legs)
        capacity = math.fsum(cc._capacity_by_period(case, movement, slices)) if movement.kind == 'depot' else 0.
        if not all(math.isfinite(v) and v >= 0 for v in (minutes, capacity)):
            raise ValueError('Invalid movement-time/single-vehicle-capacity proxy')
        key = (before.id, after.id)
        item = pairs.setdefault(key, {'movement_ids': [], 'minimum_movement_minutes': minutes,
            'maximum_depot_grid_kwh': capacity})
        item['movement_ids'].append(movement.id)
        item['minimum_movement_minutes'] = min(item['minimum_movement_minutes'], minutes)
        item['maximum_depot_grid_kwh'] = max(item['maximum_depot_grid_kwh'], capacity)
    if not pairs:
        raise ValueError('No declared chronological pair arcs')
    lo = min(p['minimum_movement_minutes'] for p in pairs.values())
    hi = max(p['minimum_movement_minutes'] for p in pairs.values())
    maximum_capacity = max(p['maximum_depot_grid_kwh'] for p in pairs.values())
    scores = {name: {} for name in ('shortest_movement', 'largest_depot_capacity', 'seed17_diversified')}
    identity = case.identity()
    for pair, item in sorted(pairs.items()):
        check()
        scores['shortest_movement'][pair] = ((item['minimum_movement_minutes']-lo)/(hi-lo)) if hi > lo else 0.
        scores['largest_depot_capacity'][pair] = 1.-item['maximum_depot_grid_kwh']/maximum_capacity if maximum_capacity else 0.
        raw = ('matching-pool-v1|'+identity+'|17|'+pair[0]+'|'+pair[1]).encode()
        scores['seed17_diversified'][pair] = int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')/2**64
    dummy, forbidden = float(n+1), float(n*(n+1)+1)
    covers, selected_pairs = [], set()
    for name, values in scores.items():
        check()
        matrix = np.full((n, 2*n), forbidden, dtype=np.float64)
        matrix[:, n:] = dummy
        for (before, after), value in values.items():
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Assignment secondary cost outside[0,1]')
            matrix[position[before], position[after]] = value
        rows, columns = linear_sum_assignment(matrix)
        check()
        if len(rows) != n or len(set(int(x) for x in columns)) != n:
            raise ValueError('Incomplete assignment')
        chosen = []
        for i, j in zip(rows, columns):
            if j < n:
                pair = (trips[int(i)].id, trips[int(j)].id)
                if pair not in pairs or position[pair[0]] >= position[pair[1]]:
                    raise ValueError('Assignment selected undeclared/nonchronological arc')
                chosen.append(pair)
        if len({p[0] for p in chosen}) != len(chosen) or len({p[1] for p in chosen}) != len(chosen):
            raise ValueError('Cover degree differs from path-cover contract')
        selected_pairs.update(chosen)
        covers.append({'secondary': name, 'pairs': sorted(chosen), 'matched_pairs': len(chosen),
            'route_only_path_count': n-len(chosen), 'secondary_sum': math.fsum(values[p] for p in chosen)})
    if len({c['matched_pairs'] for c in covers}) != 1:
        raise ValueError('Maximum-cardinality covers disagree on cardinality')
    retained = set(boundaries)
    for pair in selected_pairs:
        retained.update(pairs[pair]['movement_ids'])
    original = [m.id for m in case.movements]
    if not retained <= set(original) or not set(boundaries) <= retained:
        raise ValueError('Pool lost boundaries or invented a movement')
    return {'policy': POLICY, 'case_identity': identity, 'trip_order': [t.id for t in trips],
        'diversification_seed': SEED, 'covers': covers, 'selected_pairs': sorted(selected_pairs),
        'pair_features': [{'before': p[0], 'after': p[1], **value} for p, value in sorted(pairs.items())],
        'all_boundary_modes': boundaries, 'retained_movement_ids': [m for m in original if m in retained],
        'declared_movements': len(original), 'retained_movements': len(retained),
        'excluded_nonchronological_modes': nonchronological,
        'dummy_cost': dummy, 'forbidden_cost': forbidden, 'real_secondary_range': [0., 1.],
        'cardinality_priority': 'dummy=n+1 dominates at most n units of real-secondary variation',
        'physical_feasibility_certified': False, 'bound_scope': 'route-only diagnostic, not electric-fleet feasibility',
        'capacity_proxy': 'maximum single-vehicle depot window gridkWh; ignores accumulated SOC/shared contention',
        'method': 'global matching candidate union; not GRASP or a literature replication'}
