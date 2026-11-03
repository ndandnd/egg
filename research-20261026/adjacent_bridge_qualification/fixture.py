"""One literal synthetic registered-namespace fixture; no import-time generation."""
FIXTURE_ID = 'adjacent-six-trip-v1'
ARMS = ('fixed_duty', 'full')
DUTIES = ((0, 2, 4), (1, 3, 5))
PHYSICS = dict(battery_kwh=80., reserve_kwh=10., soc_step=10., block_min=30,
    default_kw=60., station_kw={'4808': 120.}, terminal_target_kwh=80., fleet_cap=2)
EXPECTED_COSTS = dict(BUS_COST_KX=100000., CHARGE_START_COST=0., charge_cost_premium=1.)


def make_fixture(boundary, pandas):
    """Caller has admitted/paid imports; no CSV, reference builder or old witness."""
    trips = tuple(range(6))
    starts = dict(zip(trips, (60, 75, 240, 255, 420, 435)))
    ends = {t: starts[t]+45 for t in trips}
    energy = {t: 40. for t in trips}
    adjacency = {t: [] for t in trips}
    adjacency[boundary.DEPOT] = []
    for station in boundary.STATIONS:
        adjacency[station] = []
    active = ('2190L_0', '4808_0')
    for t in trips:
        adjacency[boundary.DEPOT].append((t, 10., 4., 'depot_trip'))
        adjacency[t].append((boundary.DEPOT, 10., 4., 'trip_depot'))
        for following in trips:
            if following == t:
                continue
            travel, kwh = (12., 7.) if following % 2 == t % 2 else (18., 9.)
            if ends[t]+travel <= starts[following]:
                adjacency[t].append((following, travel, kwh, 'trip_trip'))
        for station in active:
            near = (station == '2190L_0') == (t % 2 == 0)
            travel, kwh = (5., 2.) if near else (15., 4.)
            adjacency[t].append((station, travel, kwh, 'trip_station'))
            adjacency[station].append((t, travel, kwh, 'station_trip'))
    for station in active:
        adjacency[station].append((boundary.DEPOT, 10., 4., 'station_depot'))
    prices = {station: {hour: (.10 if station == '2190L' else .15)
        if hour in (3,4,7,8) and station in ('2190L','4808') else .20
        for hour in range(26)} for station in boundary.BASES}
    plugs = {station: 1 for station in boundary.BASES}
    frame = pandas.DataFrame([dict(Ordered_Trip_ID=t,
        SL=f'synthetic_origin_parity{t%2}', EL=f'synthetic_destination_parity{t%2}',
        ST=f'{starts[t]//60:02d}:{starts[t]%60:02d}',
        ET=f'{ends[t]//60:02d}:{ends[t]%60:02d}', **{'Energy used': energy[t]}) for t in trips])
    frame = frame.astype({'Ordered_Trip_ID':'int64', 'Energy used':'float64'})
    frame.index = pandas.RangeIndex(0, len(trips), 1)
    if (tuple(frame.index) != trips or tuple(frame['Ordered_Trip_ID']) != trips
            or tuple(sorted(t for duty in DUTIES for t in duty)) != trips
            or len(DUTIES) != PHYSICS['fleet_cap']
            or any(ends[left] > starts[right] for duty in DUTIES for left,right in zip(duty,duty[1:]))):
        raise ValueError('Literal synthetic frame/duty timing contract differs')
    overlap = max(starts[0], starts[1]) < min(ends[0], ends[1])
    if not overlap:
        raise ValueError('Prospective cap2 lower-bound witness is absent; no alternate fixture')
    problem = boundary.problem_view(trips=trips, adjacency=adjacency,
        start_min=starts, end_min=ends, trip_energy=energy, frame=frame)
    descriptor = dict(fixture_id=FIXTURE_ID, trips=list(trips), duties=[list(d) for d in DUTIES],
        start_min=starts, end_min=ends, trip_energy=energy, horizon_min=boundary.HORIZON_MIN,
        depot=boundary.DEPOT, active_stations=list(active), prices=prices, plugs=plugs,
        physics=PHYSICS, expected_costs=EXPECTED_COSTS,
        fleet_lower_bound_witness=dict(trips=[0,1], starts=[starts[0],starts[1]],
            ends=[ends[0],ends[1]], positive_overlap=True, lower_bound=2,
            scope='Mandatory simultaneous service only; not charging/SOC feasibility'),
        frame_schema=dict(index='RangeIndex0..5', Ordered_Trip_ID='int64',
            SL='synthetic origin string', EL='synthetic destination string',
            ST='HH:MM string', ET='HH:MM string', Energy_used='float64 kWh'),
        unused_stations='No transfer arcs; rates, plugs and full-horizon prices still explicit')
    return problem, prices, plugs, DUTIES, dict(PHYSICS), descriptor
