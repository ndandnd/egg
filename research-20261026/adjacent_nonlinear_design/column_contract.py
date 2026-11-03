"""Pure projection of an ALREADY caller-admitted retained oracle column.

No physical validation, replay, price inference, optimization or I/O occurs here.
Grid/realized vectors retain represented source numbers, not exact physical data.
The future master must impose the declared common fleet and shared resource rows.
"""
import math


class ColumnContractError(ValueError):
    pass


def _number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ColumnContractError(name+' must be finite, nonnegative and numeric')
    return value


def _integer(value, name, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        raise ColumnContractError(name+' must be a nonnegative integer count/index')
    return value


def _sequence(value, name):
    if not isinstance(value, (list, tuple)):
        raise ColumnContractError(name+' must be an explicit list/tuple')
    return tuple(value)


def project_column(record, *, origin_id, record_id, trip_universe,
                   station_aliases, station_order, hour_order, minute_horizon,
                   bus_cost=100000, session_fee=0, target='realized'):
    """Return station-major/hour-minor vectors and counted occupancy triples.

    target selects only 'grid' or 'realized' projection, not an institution/lens.
    Alias keys are exact strings, including any desired identity aliases; no
    suffix stripping or station inference is performed. No columns are deduped.
    Physical admission of this record is an external prerequisite, not a result.
    """
    if not isinstance(record, dict):
        raise ColumnContractError('record must be a mapping')
    if any(not isinstance(v, str) or not v.strip() for v in (origin_id, record_id)):
        raise ColumnContractError('Explicit nonempty origin_id and record_id required')
    if target not in ('grid', 'realized'):
        raise ColumnContractError('Unsupported target; choose grid or realized')
    if (_number(bus_cost, 'bus_cost') != 100000
            or _number(session_fee, 'session_fee') != 0):
        raise ColumnContractError('Only inherited BUS_COST_KX=100000 and fee0 are supported')
    universe = _sequence(trip_universe, 'trip_universe')
    if (not universe or any(type(t) is not int for t in universe)
            or len(set(universe)) != len(universe)):
        raise ColumnContractError('Explicit unique integer trip universe required')
    stations = _sequence(station_order, 'station_order')
    if (not stations or any(not isinstance(s, str) or not s for s in stations)
            or len(set(stations)) != len(stations)):
        raise ColumnContractError('Explicit unique canonical station order required')
    hours = _sequence(hour_order, 'hour_order')
    if (not hours or any(type(h) is not int or h < 0 for h in hours)
            or len(set(hours)) != len(hours)):
        raise ColumnContractError('Explicit unique nonnegative integer hour order required')
    horizon = _integer(minute_horizon, 'minute_horizon', positive=True)
    if any(60*h >= horizon for h in hours):
        raise ColumnContractError('Hour starts outside declared minute horizon')
    if (not isinstance(station_aliases, dict) or not station_aliases
            or any(not isinstance(k, str) or not k or v not in stations
                   for k, v in station_aliases.items())
            or set(station_aliases.values()) != set(stations)):
        raise ColumnContractError('Explicit alias map must cover exactly the canonical stations')

    def station(value):
        if not isinstance(value, str) or value not in station_aliases:
            raise ColumnContractError('Unknown station alias')
        return station_aliases[value]

    try:
        trips = _sequence(record['trips'], 'record.trips')
        if (not trips or any(type(t) is not int or t not in universe for t in trips)
                or len(set(trips)) != len(trips)):
            raise ColumnContractError('Empty, foreign or repeated trip/service in column')
        stops = record['charging_stops']
        if not isinstance(stops, dict):
            raise ColumnContractError('Missing realized charging-stop mapping')
        stop_fields = {k: _sequence(stops[k], 'charging_stops.'+k)
                       for k in ('stations', 'cst', 'cet', 'kwh')}
        if len({len(v) for v in stop_fields.values()}) != 1:
            raise ColumnContractError('Ambiguous parallel charging-stop arrays')
        stop_stations = tuple(station(s) for s in stop_fields['stations'])
        for start, end, energy in zip(stop_fields['cst'], stop_fields['cet'], stop_fields['kwh']):
            _number(start, 'stop start'); _number(end, 'stop end'); _number(energy, 'stop kWh')
            if not start < end <= horizon:
                raise ColumnContractError('Charging stop outside declared time domain')
        terminal_grid = _number(record['terminal_energy_kwh'], 'grid terminal energy')
        terminal_realized = _number(record['continuous_terminal_energy_kwh'], 'realized terminal energy')
        blocks = _sequence(record['continuous_realized_charging_blocks'], 'tariff blocks')
        grid = {(s, h): 0 for s in stations for h in hours}
        realized = dict(grid)
        block_keys = set()
        for block in blocks:
            if not isinstance(block, dict):
                raise ColumnContractError('Tariff block must be a mapping')
            s = station(block['station']); h = _integer(block['tariff_hour'], 'tariff hour')
            if h not in hours:
                raise ColumnContractError('Unknown tariff hour')
            i = _integer(block['stop_index'], 'stop index')
            j = _integer(block['block_index'], 'block index')
            if i >= len(stop_stations) or s != stop_stations[i] or (i, j) in block_keys:
                raise ColumnContractError('Duplicate or ambiguous block/stop membership')
            block_keys.add((i, j))
            start = _number(block['start_min'], 'block start')
            end = _number(block['end_min'], 'block end')
            if not 60*h <= start < end <= min(horizon, 60*(h+1)):
                raise ColumnContractError('Block timing outside declared tariff-hour domain')
            grid[s, h] += _number(block['expanded_grid_kwh'], 'block grid kWh')
            realized[s, h] += _number(block['realized_kwh'], 'block realized kWh')
        # Missing energy-bearing stop blocks are not silently represented as zero.
        if any(energy > 0 and not any(i == index for i, _ in block_keys)
               for index, energy in enumerate(stop_fields['kwh'])):
            raise ColumnContractError('Energy-bearing stop has no projected blocks')
        occupancy = {}
        for entry in _sequence(record['capacity_occupancy'], 'capacity_occupancy'):
            values = _sequence(entry, 'occupancy triple')
            if len(values) != 3:
                raise ColumnContractError('Occupancy must be station/minute/COUNT triples')
            s = station(values[0]); m = _integer(values[1], 'occupancy minute')
            count = _integer(values[2], 'occupancy count', positive=True)
            if m >= horizon or (s, m) in occupancy:
                raise ColumnContractError('Unknown minute or duplicate canonical occupancy key')
            occupancy[s, m] = count
    except KeyError as exc:
        raise ColumnContractError('Required retained-column field missing: '+str(exc)) from exc

    grid_vector = tuple(grid[s, h] for s in stations for h in hours)
    realized_vector = tuple(realized[s, h] for s in stations for h in hours)
    for value in grid_vector+realized_vector:
        _number(value, 'accumulated load')
    return dict(origin_id=origin_id, record_id=record_id, trips=trips,
        station_order=stations, hour_order=hours, minute_horizon=horizon,
        vector_order='station-major/hour-minor', load_grid=grid_vector,
        load_realized=realized_vector, terminal_grid_kwh=terminal_grid,
        terminal_realized_kwh=terminal_realized,
        occupancy=tuple((s, m, occupancy[s, m]) for s, m in sorted(occupancy)),
        fleet_units=1, ops=bus_cost, session_fee=0, charge_stop_count=len(stop_stations),
        target=target, target_load=grid_vector if target == 'grid' else realized_vector,
        target_terminal_kwh=terminal_grid if target == 'grid' else terminal_realized,
        caller_physical_admission_required=True, physical_validation_performed=False,
        shared_fleet_validation_performed=False, pricing_certificate_claim=False,
        scope='One retained fixed schedule; no trip-set dedup, optimization or physical certification')
