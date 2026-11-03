"""Candidate pure physical lift and binary-start specification; no solver API."""
from copy import deepcopy
from dataclasses import fields
from fractions import Fraction
import math

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr

POLICY = 'candidate-recovery-physical-lift-binary-spec-v1'


def _unique(items, kind):
    mapping = {item.id: item for item in items}
    if len(mapping) != len(items):
        raise ValueError(f'Duplicate {kind} ID')
    return mapping


def lift_plan(source_case, full_case, source_plan, *, a, b):
    """Return independently replayed full witness, bill, ID/value hint and provenance.

    This function accepts no model/variable objects and never submits a start.
    Inputs are immutable by contract; returned physical events are deep copies.
    """
    source_modes = _unique(source_case.movements, 'source movement')
    full_modes = _unique(full_case.movements, 'full movement')
    source_trips = _unique(source_case.trips, 'source trip')
    full_trips = _unique(full_case.trips, 'full trip')
    nr.validate_case(source_case)
    nr.validate_case(full_case)
    for field in fields(source_case):
        if field.name not in ('name', 'trips', 'movements'):
            if getattr(source_case, field.name) != getattr(full_case, field.name):
                raise ValueError(f'Changed full-case policy/physics: {field.name}')
    if source_trips != full_trips:
        raise ValueError('Changed trip IDs/physics')
    for mid, movement in source_modes.items():
        if mid not in full_modes:
            raise ValueError(f'Unknown source movement ID in full case: {mid}')
        if movement != full_modes[mid]:
            raise ValueError(f'Changed movement physics for ID: {mid}')
    nr._check_market(full_case, a, b)
    source_replay = nr.replay_native(source_case, source_plan)
    selected = [mid for vehicle in source_plan['vehicles'] for mid in vehicle['movements']]
    if len(selected) != len(set(selected)):
        raise ValueError('Duplicate selected movement ID')
    pf.recover_paths(source_case, selected)
    pf.recover_paths(full_case, selected)
    # Deliberately omit source solver grids, variable indices, SOC and epigraphs.
    lifted = {'schema':nr.SCHEMA, 'case_identity':full_case.identity(),
              'vehicles':deepcopy(source_plan['vehicles']),
              'charges':deepcopy(source_plan.get('charges', []))}
    loads = [0.] * (len(full_case.market_edges_min)-1)
    for charge in lifted['charges']:
        rate = charge['grid_kwh']/(charge['end_min']-charge['start_min'])
        for t,(lo,hi) in enumerate(zip(full_case.market_edges_min,full_case.market_edges_min[1:])):
            loads[t] += rate*max(0.,min(hi,charge['end_min'])-max(lo,charge['start_min']))
    lifted['load'] = loads
    lifted['ops_cost'] = len(lifted['vehicles'])*full_case.vehicle_cost + full_case.deadhead_cost_per_min*sum(
        leg.arrive_min-leg.depart_min for mid in selected for leg in full_modes[mid].legs)
    full_replay = nr.replay_native(full_case, lifted)
    market = nh.Market('candidate-recovery-target', tuple(a), tuple(b))
    bill_exact = Fraction(full_replay['ops_cost'])+nh.supply(market,full_replay['load'])
    bill = float(bill_exact)
    if not math.isfinite(bill):
        raise ValueError('Nonfinite recomputed physical bill')
    source_bill_exact = Fraction(source_replay['ops_cost'])+nh.supply(market,source_replay['load'])
    specification = [{'movement_id':movement.id,'value':int(movement.id in selected)}
                     for movement in full_case.movements]
    return {'policy':POLICY,'status':'physical_fallback_only', 'plan':lifted,
            'replay':full_replay,'true_bill_exact':str(bill_exact),
            'true_bill':bill,'binary_start_spec':specification,
            'start_status':'not_submitted', 'global_lower_bound':None,
            'provenance':{'source_case_identity':source_case.identity(),
                'full_case_identity':full_case.identity(),'source_plan_hash':nr.digest(source_plan),
                'source_movement_ids':list(source_modes), 'full_movement_ids':list(full_modes),
                'selected_movement_ids':selected,'added_full_movement_ids':[
                    mid for mid in full_modes if mid not in source_modes],
                'source_replay_bill_at_target_market_exact':str(source_bill_exact),
                'target_market_hash':nr.digest({'a':list(a),'b':list(b)}),
                'source_extraction_policy':source_plan.get('extraction_policy'),
                'continuous_start_policy':'omit-all-continuous-variables'}}
