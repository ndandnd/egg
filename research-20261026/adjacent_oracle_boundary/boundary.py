"""DRAFT thin in-memory boundary; imports no sibling/project/solver modules.

Caller owns prospective source binding, paid fresh-process imports and outer clock.
No loader, fixture generator or master is implemented here.
"""
import math
from pathlib import Path
import sys
from types import SimpleNamespace

REGISTERED = Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
SOURCE_REVISION = '3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c'
DEPOT = 'PARX_0'
STATIONS = ('2190L_0', '4808_0', 'PARX_1', '3127L_0', '7880C_0', 'JON_A_0')
BASES = ('2190L', '4808', 'PARX', '3127L', '7880C', 'JON_A')
HORIZON_MIN = 1560.
KINDS = {'trip_trip', 'trip_station', 'station_trip', 'depot_trip', 'trip_depot', 'station_depot'}
_FACTORY_TOKEN = object()


def problem_view(*, trips, adjacency, start_min, end_min, trip_energy, frame):
    """Pricing attributes and caller-provided synthetic frame; no data loading.

    This is a duck-typed view, not a runtime-qualified ProblemData constructor.
    It preserves caller arcs rather than building/rounding/inventing transfers.
    """
    if frame is None:
        raise ValueError('Caller-provided synthetic frame required; no silent dummy frame')
    trips = tuple(trips)
    if not trips or any(type(t) is not int for t in trips) or len(set(trips)) != len(trips):
        raise ValueError('Require distinct integer trip IDs')
    for mapping in (start_min, end_min, trip_energy):
        if set(mapping) != set(trips):
            raise ValueError('Trip dictionaries must have the same exact domain')
    for t in trips:
        values = (start_min[t], end_min[t], trip_energy[t])
        if (any(type(x) not in (int,float) or not math.isfinite(x) for x in values)
                or not 0 <= start_min[t] < end_min[t] <= HORIZON_MIN or trip_energy[t] < 0):
            raise ValueError('Invalid literal trip time/energy')
    copied = {}
    for source, arcs in adjacency.items():
        copied[source] = []
        for successor, travel, energy, kind in arcs:
            if (kind not in KINDS or type(travel) not in (int,float) or type(energy) not in (int,float)
                    or not math.isfinite(travel) or not math.isfinite(energy) or travel < 0 or energy < 0):
                raise ValueError('Invalid explicit transfer tuple')
            copied[source].append((successor, travel, energy, kind))
    return SimpleNamespace(frame=frame, trips=trips, adjacency=copied,
        start_min=dict(start_min), end_min=dict(end_min), trip_energy=dict(trip_energy))


def _registered_modules():
    names = ('audit_giro_known_columns', 'event_pricer_network', 'terminal_energy_pricer',
             'capacity_event_pricer', 'expanded_path_realization', 'config')
    modules = {}
    for name in names:
        module = sys.modules.get(name)
        if module is None or Path(getattr(module, '__file__', '')).resolve() != REGISTERED/'src'/(name+'.py'):
            raise ValueError('Caller has not supplied the registered fresh-process modules: '+name)
        modules[name] = module
    for name in ('audit_giro_known_columns', 'event_pricer_network'):
        if (modules[name].DEPOT != DEPOT or tuple(modules[name].STATIONS) != STATIONS
                or modules[name].HORIZON_MIN != HORIZON_MIN):
            raise ValueError('Registered labels/horizon changed; no global patching supported')
    return modules


def _supported_type(candidate, base):
    return candidate is base or (getattr(candidate, '__bases__', ()) == (base,)
        and candidate.__dict__.get('_boundary_factory_token') is _FACTORY_TOKEN)


def make_fixed_duty_network_type(base_type, duties):
    """Only filter inherited candidate generators; no solver/DP/packing copy.

    Validation against the actual problem precedes inherited graph construction.
    Station adjacency is unchanged, preserving originating-duty context.
    """
    modules = _registered_modules()
    if base_type is not modules['capacity_event_pricer'].CapacityTerminalNetwork:
        raise ValueError('Factory requires the registered unmodified capacity base')
    duties = tuple(tuple(duty) for duty in duties)
    flat = tuple(t for duty in duties for t in duty)
    if (not duties or any(not duty for duty in duties)
            or any(type(t) is not int for t in flat) or len(flat) != len(set(flat))):
        raise ValueError('Duties must be nonempty, nonoverlapping integer trip sequences')
    first = frozenset(duty[0] for duty in duties)
    following = {trip: (duty[index+1] if index+1 < len(duty) else None)
        for duty in duties for index, trip in enumerate(duty)}

    class FixedDutyNetwork(base_type):
        _boundary_factory_token = _FACTORY_TOKEN
        prescribed_duties = duties

        def __init__(self, problem, *args, **kwargs):
            if len(problem.trips) != len(flat) or set(problem.trips) != set(flat):
                raise ValueError('Duties must exactly partition the actual requested trips')
            if any(not problem.end_min[left] <= problem.start_min[right]
                    for duty in duties for left,right in zip(duty,duty[1:])):
                raise ValueError('Prescribed duties violate the requested service ordering')
            super().__init__(problem, *args, **kwargs)

        def _source_candidates(self):
            for node, cost, trip, action in super()._source_candidates():
                if trip in first:
                    yield node, cost, trip, action

        def _direct_candidates(self, trip, soc_exit, depart):
            for target, cost, successor, action in super()._direct_candidates(trip, soc_exit, depart):
                if successor == following[trip]:
                    yield target, cost, successor, action

        def _charge_candidates(self, trip, soc_exit, depart):
            for target, cost, successor, action in super()._charge_candidates(trip, soc_exit, depart):
                if successor == following[trip]:
                    yield target, cost, successor, action

    return FixedDutyNetwork


def construct(network_type, problem, station_prices, *, plugs, soc_step, block_min,
              battery_kwh, default_kw, reserve_kwh, expected_costs, station_kw=None):
    """Invoke the existing class by reference, only after caller's paid admission.

    Source revision is a prospective binding declaration, not checked by Git/hash
    here. Generic imports and fee bootstrap must already be isolated by caller.
    """
    modules = _registered_modules()
    if not _supported_type(network_type, modules['capacity_event_pricer'].CapacityTerminalNetwork):
        raise ValueError('Only the registered base or this candidate-filter factory is supported')
    if set(expected_costs) != {'BUS_COST_KX', 'CHARGE_START_COST', 'charge_cost_premium'}:
        raise ValueError('Explicit existing cost-constant expectations required')
    for module_name in ('config','event_pricer_network','capacity_event_pricer','expanded_path_realization'):
        for key, value in expected_costs.items():
            if getattr(modules[module_name], key) != value:
                raise ValueError('Imported cost constants disagree: '+module_name+'.'+key)
    if set(station_prices) != set(BASES) or set(plugs) != set(BASES):
        raise ValueError('Require the registered station-base price/plug domains')
    return network_type(problem, station_prices, plugs=plugs, soc_step=soc_step,
        block_min=block_min, g_kwh=battery_kwh, charge_kw=default_kw,
        reserve_kwh=reserve_kwh, strict_tariff_coverage=True,
        station_kw=station_kw, fixed_sequence_index=False)


def price(network, trip_duals, cap_surcharges, *, terminal_dual=0., route_dual=0.,
          objective='combined-cost', limit=30):
    """One existing batch call; returns unchanged rc/record data, not a fleet solve."""
    modules = _registered_modules()
    if not _supported_type(type(network), modules['capacity_event_pricer'].CapacityTerminalNetwork):
        raise ValueError('Network type is outside this draft boundary')
    if (objective not in {'combined-cost','charging-cost','artificial-elimination'}
            or type(limit) is not int or limit <= 0 or not math.isfinite(terminal_dual)
            or terminal_dual < 0 or not math.isfinite(route_dual)):
        raise ValueError('Invalid declared pricing call')
    if any(t not in network.problem.trips or not math.isfinite(v) for t,v in trip_duals.items()):
        raise ValueError('Invalid trip duals')
    for (station, minute), surcharge in cap_surcharges.items():
        if (station not in BASES or type(minute) is not int or not 0 <= minute < HORIZON_MIN
                or not math.isfinite(surcharge) or surcharge < 0):
            raise ValueError('Capacity argument is nonnegative occupied-minute surcharge, not raw master Pi')
    return network.capacity_terminal_batch(trip_duals, cap_surcharges,
        terminal_dual=terminal_dual, route_dual=route_dual, objective=objective, limit=limit)
