"""Prospective literal-rule workload; importing this module generates nothing."""
from copy import deepcopy
import hashlib
import json

FIXTURE_ID = 'capacity-pricing-workload-v1'
SEEDS = (61001, 61002, 61003, 61004)
SIZES = (12, 24)
QUOTES = ('flat', 'source_shape')
DEPOT = 'PARX_0'
STATIONS = ('2190L_0', '4808_0', 'PARX_1', '3127L_0', '7880C_0', 'JON_A_0')
BASES = ('2190L', '4808', 'PARX', '3127L', '7880C', 'JON_A')
ACTIVE = ('2190L_0', '4808_0')
PHYSICS = dict(battery_kwh=80., reserve_kwh=10., soc_step=10., block_min=30,
    default_kw=60., station_kw={'4808': 120.}, terminal_target_kwh=160., fleet_cap=4)
EXPECTED_COSTS = dict(BUS_COST_KX=100000., CHARGE_START_COST=0., charge_cost_premium=1.)


def _wire(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def make_descriptor(seed, n, quote):
    """Generate only when explicitly called inside the caller's paid clock."""
    if type(seed) is not int or seed not in SEEDS or type(n) is not int or n not in SIZES or quote not in QUOTES:
        raise ValueError('Unassigned seed, size or quote; no replacement workload')
    trips = list(range(n))
    starts = {}
    for w in range(n // 4):
        token = f'capacity-workload-v1|{seed}|{w}|start'.encode('utf-8')
        u = int.from_bytes(hashlib.sha256(token).digest()[:8], 'big', signed=False)
        jitter = 5 * (u % 3)
        for d in range(4):
            starts[str(4*w+d)] = 60 + 180*w + 10*d + jitter
    ends = {str(t): starts[str(t)]+45 for t in trips}
    energy = {str(t): 40. for t in trips}
    duties = [list(range(d, n, 4)) for d in range(4)]
    adjacency = {str(t): [] for t in trips}
    adjacency.update({node: [] for node in (DEPOT,)+STATIONS})
    for t in trips:
        adjacency[DEPOT].append([t, 10., 4., 'depot_trip'])
        adjacency[str(t)].append([DEPOT, 10., 4., 'trip_depot'])
        for successor in trips:
            if successor == t:
                continue
            travel, kwh = (12., 7.) if successor % 2 == t % 2 else (18., 9.)
            if ends[str(t)]+travel <= starts[str(successor)]:
                adjacency[str(t)].append([successor, travel, kwh, 'trip_trip'])
        for station in ACTIVE:
            near = (station == '2190L_0') == (t % 2 == 0)
            travel, kwh = (5., 2.) if near else (15., 4.)
            adjacency[str(t)].append([station, travel, kwh, 'trip_station'])
            adjacency[station].append([t, travel, kwh, 'station_trip'])
    for station in ACTIVE:
        adjacency[station].append([DEPOT, 10., 4., 'station_depot'])
    prices = {station: {str(hour): ((.10 if station == '2190L' else .15)
        if quote == 'source_shape' and station in ('2190L', '4808') and hour in (3, 4, 7, 8)
        else .20) for hour in range(26)} for station in BASES}
    descriptor = dict(fixture_id=FIXTURE_ID, seed=seed, n=n, quote=quote, trips=trips,
        duties=duties, start_min=starts, end_min=ends, trip_energy=energy, adjacency=adjacency,
        horizon_min=1560., depot=DEPOT, stations=list(STATIONS), active_stations=list(ACTIVE),
        prices=prices, plugs={base: 1 for base in BASES}, physics=deepcopy(PHYSICS),
        expected_costs=dict(EXPECTED_COSTS), frame_schema=dict(index='RangeIndex0..n-1',
            Ordered_Trip_ID='int64', SL='synthetic_origin_parity', EL='synthetic_destination_parity',
            ST='HH:MM', ET='HH:MM', Energy_used='float64 kWh'),
        fleet_lower_bound_witness=dict(trips=[0, 1, 2, 3], lower_bound=4,
            scope='Mandatory overlapping service only; charging feasibility unproven'))
    _contract(descriptor)
    return descriptor


def _contract(descriptor):
    """Check the declared constructor contract, never certify charging feasibility."""
    n = descriptor['n']
    if (descriptor['fixture_id'] != FIXTURE_ID or type(n) is not int or n not in SIZES
            or type(descriptor['seed']) is not int or descriptor['seed'] not in SEEDS
            or descriptor['quote'] not in QUOTES or descriptor['trips'] != list(range(n))
            or descriptor['duties'] != [list(range(d, n, 4)) for d in range(4)]
            or descriptor['horizon_min'] != 1560. or descriptor['depot'] != DEPOT
            or descriptor['stations'] != list(STATIONS) or descriptor['active_stations'] != list(ACTIVE)
            or _wire(descriptor['physics']) != _wire(PHYSICS)
            or _wire(descriptor['expected_costs']) != _wire(EXPECTED_COSTS)
            or descriptor['plugs'] != {base: 1 for base in BASES}):
        raise ValueError('Literal workload/resource/duty contract differs')
    domain = {str(t) for t in range(n)}
    if any(set(descriptor[key]) != domain for key in ('start_min', 'end_min', 'trip_energy')):
        raise ValueError('Trip dictionary domain differs')
    for w in range(n // 4):
        first = descriptor['start_min'][str(4*w)]
        if first - (60+180*w) not in (0, 5, 10):
            raise ValueError('Wave jitter outside frozen support')
        for d in range(4):
            t = str(4*w+d)
            if (type(descriptor['start_min'][t]) is not int or descriptor['start_min'][t] != first+10*d
                    or descriptor['end_min'][t] != descriptor['start_min'][t]+45
                    or descriptor['trip_energy'][t] != 40.):
                raise ValueError('Service/start/energy recipe differs')
        if max(descriptor['start_min'][str(4*w+d)] for d in range(4)) >= min(descriptor['end_min'][str(4*w+d)] for d in range(4)):
            raise ValueError('Four-way service overlap missing; no fleet relaxation')
    if max(descriptor['end_min'].values()) > descriptor['horizon_min']:
        raise ValueError('Service outside registered horizon')
    if set(descriptor['prices']) != set(BASES) or any(set(v) != {str(h) for h in range(26)} for v in descriptor['prices'].values()):
        raise ValueError('Full registered hourly quote domain required')


def physical_alias(descriptor):
    """Canonical physical descriptor excluding seed/quote labels and quote values.

    Compare aliases before outcomes; retain collisions and union group membership.
    The returned string is an equality key, not an independence certificate.
    """
    _contract(descriptor)
    return _wire({key: value for key, value in descriptor.items() if key not in ('seed', 'quote', 'prices')})


def assert_nested(small, large):
    """The small graph must be the induced prefix of its own larger variant."""
    _contract(small); _contract(large)
    if (small['n'], large['n']) != SIZES or small['seed'] != large['seed'] or small['quote'] != large['quote']:
        raise ValueError('Assigned same-group 12/24 quote pair required')
    for key in ('fixture_id', 'horizon_min', 'depot', 'stations', 'active_stations', 'prices', 'plugs',
                'physics', 'expected_costs', 'frame_schema', 'fleet_lower_bound_witness'):
        if _wire(small[key]) != _wire(large[key]):
            raise ValueError('Resources or declared schema changed between sizes: '+key)
    for key in ('start_min', 'end_min', 'trip_energy'):
        if any(_wire(value) != _wire(large[key][t]) for t, value in small[key].items()):
            raise ValueError('Existing prefix trip changed: '+key)
    if any(left != right[:len(left)] for left, right in zip(small['duties'], large['duties'])):
        raise ValueError('Duty prefix changed')
    permitted = set(small['trips']) | {DEPOT} | set(STATIONS)
    for source, arcs in small['adjacency'].items():
        induced = [arc for arc in large['adjacency'][source] if arc[0] in permitted]
        if _wire(arcs) != _wire(induced):
            raise ValueError('Existing induced transfer tuple changed')
    return True


def make_fixture(boundary, pandas, descriptor):
    """Construct this paid synthetic input, without reading data or solving."""
    _contract(descriptor)
    if (boundary.DEPOT != DEPOT or tuple(boundary.STATIONS) != STATIONS
            or tuple(boundary.BASES) != BASES or boundary.HORIZON_MIN != 1560.):
        raise ValueError('Registered literal namespace differs')
    trips = tuple(descriptor['trips'])
    starts = {t: descriptor['start_min'][str(t)] for t in trips}
    ends = {t: descriptor['end_min'][str(t)] for t in trips}
    energy = {t: descriptor['trip_energy'][str(t)] for t in trips}
    trip_keys = {str(t): t for t in trips}
    adjacency = {trip_keys.get(source, source): [tuple(arc) for arc in arcs]
                 for source, arcs in descriptor['adjacency'].items()}
    frame = pandas.DataFrame([dict(Ordered_Trip_ID=t, SL=f'synthetic_origin_parity{t%2}',
        EL=f'synthetic_destination_parity{t%2}', ST=f'{starts[t]//60:02d}:{starts[t]%60:02d}',
        ET=f'{ends[t]//60:02d}:{ends[t]%60:02d}', **{'Energy used': energy[t]}) for t in trips])
    frame = frame.astype({'Ordered_Trip_ID': 'int64', 'Energy used': 'float64'})
    frame.index = pandas.RangeIndex(0, len(trips), 1)
    if tuple(frame.index) != trips or tuple(frame['Ordered_Trip_ID']) != trips:
        raise ValueError('Synthetic frame/index identity differs')
    problem = boundary.problem_view(trips=trips, adjacency=adjacency, start_min=starts,
        end_min=ends, trip_energy=energy, frame=frame)
    prices = {base: {int(hour): value for hour, value in quotes.items()} for base, quotes in descriptor['prices'].items()}
    duties = tuple(tuple(duty) for duty in descriptor['duties'])
    return problem, prices, dict(descriptor['plugs']), duties, deepcopy(descriptor['physics']), descriptor
