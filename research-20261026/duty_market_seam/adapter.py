"""Literal synthetic one-depot seam; no solver, dataset or sibling imports."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q

FIXTURE = 'duty-market-seam-v1'
CONTEXT_IDS = ('b0_all', 'posted', 'system', 'strategic')
PHASES = ('target_qp', 'fixed_duty', 'full')


def contexts():
    a = tuple(.125 if t in (4, 5, 12, 13) else .25 for t in range(16))
    U = tuple(32 if t < 8 else 64 for t in range(16))
    output = []
    for identity in CONTEXT_IDS:
        b = (0.,)*16 if identity == 'b0_all' else (1/1024,)*16
        posted = tuple(aa+bb*u for aa, bb, u in zip(a, b, U))
        beta = tuple(0. if identity in ('b0_all', 'posted') else
                     bb if identity == 'system' else 2*bb for bb in b)
        output.append(dict(id=identity, a=a, b=b, U=U, posted=posted, alpha=posted, beta=beta,
            institution={'b0_all': 'all_three_coincide', 'posted': 'exogenous_posted_payment',
                'system': 'incremental_integrated_system_cost',
                'strategic': 'atomic_uniform_price_payment'}[identity]))
    return output


def objective_identity(context):
    from egglab import native_recharge as nr
    return nr.digest(context)


def canonical(plan):
    return tuple(sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles']))


def duty_signature(plan):
    return tuple(sorted(tuple(v['trips']) for v in plan['vehicles']))


def task_id(context_id, phase):
    return f'T{3*CONTEXT_IDS.index(context_id)+PHASES.index(phase)+1:02d}-{phase}'


def make_fixture():
    from egglab import native_recharge as nr
    trips = []
    for wave, start in enumerate((60, 240, 420, 600)):
        trips.extend((nr.Trip(f'w{wave}_AB', start, start+45, 'A', 'B', 20.),
            nr.Trip(f'w{wave}_BA', start+10, start+55, 'B', 'A', 20.)))
    travel = {('D', 'A'): (10, 2.), ('A', 'D'): (10, 2.),
        ('D', 'B'): (15, 3.), ('B', 'D'): (15, 3.),
        ('A', 'B'): (10, 2.), ('B', 'A'): (10, 2.)}

    def leg(origin, destination, depart):
        minutes, energy = (0, 0.) if origin == destination else travel[origin, destination]
        return nr.Leg(origin, destination, depart, depart+minutes, energy)

    movements = []
    for trip in trips:
        duration = travel['D', trip.start_place][0]
        movements.extend((nr.Movement('out_'+trip.id, 'pullout', None, trip.id,
                (leg('D', trip.start_place, trip.start_min-duration),)),
            nr.Movement('in_'+trip.id, 'pullin', trip.id, None,
                (leg(trip.end_place, 'D', trip.end_min),))))
    for before in trips:
        for after in trips:
            if before.id == after.id:
                continue
            direct = leg(before.end_place, after.start_place, before.end_min)
            if direct.arrive_min <= after.start_min:
                legs = (direct,)
                if direct.arrive_min < after.start_min:
                    legs += (nr.Leg(after.start_place, after.start_place,
                        direct.arrive_min, after.start_min, 0.),)
                movements.append(nr.Movement(f'direct_{before.id}_{after.id}', 'direct',
                    before.id, after.id, legs))
            incoming = leg(before.end_place, 'D', before.end_min)
            outbound_minutes = travel['D', after.start_place][0]
            outgoing = leg('D', after.start_place, after.start_min-outbound_minutes)
            if incoming.arrive_min <= outgoing.depart_min:
                movements.append(nr.Movement(f'depot_{before.id}_{after.id}', 'depot',
                    before.id, after.id, (incoming, outgoing), 1))
    case = nr.NativeCase(name=FIXTURE, trips=tuple(trips), movements=tuple(movements),
        resources=(nr.Resource(0, 960, 60., 60., 1),), market_edges_min=tuple(range(0, 961, 60)),
        depot='D', max_vehicles=2, battery_kwh=80., reserve_kwh=10.,
        terminal_open_min=720, recharge_deadline_min=960, vehicle_cost=100.,
        deadhead_cost_per_min=0., efficiency=.9)
    nr.validate_case(case)
    duties = tuple(tuple(f'w{wave}_'+('AB' if (wave+vehicle) % 2 == 0 else 'BA')
                         for wave in range(4)) for vehicle in range(2))
    by_trip, modes = {t.id: t for t in trips}, {m.id: m for m in movements}
    vehicles, windows = [], []
    for vehicle, sequence in enumerate(duties):
        ids = ['out_'+sequence[0]]+[f'depot_{left}_{right}' for left, right in zip(sequence, sequence[1:])]+['in_'+sequence[-1]]
        vehicles.append(dict(vehicle=vehicle, trips=list(sequence), movements=ids))
        soc = Q(case.battery_kwh)-sum((Q(l.energy_kwh) for l in modes[ids[0]].legs), Q(0))
        for index, trip_id in enumerate(sequence):
            soc -= Q(by_trip[trip_id].energy_kwh)
            mode = modes[ids[index+1]]
            inbound = mode.legs[:mode.depot_split] if mode.kind == 'depot' else mode.legs
            for item in inbound:
                soc -= Q(item.energy_kwh)
            if soc < Q(case.reserve_kwh) or soc > Q(case.battery_kwh):
                raise ValueError('Literal reference violates precharge SOC; no fixture repair')
            lo, hi = nr._window(case, mode)
            energy = (Q(case.battery_kwh)-soc)/Q(case.efficiency)
            windows.append(dict(vehicle=vehicle, movement=mode.id, lo=lo, hi=hi, energy=energy))
            soc = Q(case.battery_kwh)
            if mode.kind == 'depot':
                soc -= sum((Q(l.energy_kwh) for l in mode.legs[mode.depot_split:]), Q(0))
    cursor, charges = 0., []
    for window in sorted(windows, key=lambda w: (w['lo'], w['vehicle'])):
        start = max(cursor, float(window['lo']))
        energy = float(window['energy'])
        end = start+energy*60/case.resources[0].grid_kw
        if not energy > 0 or end > window['hi']:
            raise ValueError('Literal serial refill misses its declared window; no alternate fixture')
        charges.append(dict(vehicle=window['vehicle'], movement=window['movement'], connector=0,
            start_min=start, end_min=end, grid_kwh=energy))
        cursor = end
    loads = [0.]*(len(case.market_edges_min)-1)
    for charge in charges:
        rate = charge['grid_kwh']*60/(charge['end_min']-charge['start_min'])
        for index, (left, right) in enumerate(zip(case.market_edges_min, case.market_edges_min[1:])):
            loads[index] += rate*max(0., min(right, charge['end_min'])-max(left, charge['start_min']))/60
    plan = dict(schema=nr.SCHEMA, case_identity=case.identity(), vehicles=vehicles,
        charges=charges, load=loads, ops_cost=len(vehicles)*case.vehicle_cost)
    return case, plan, duties


def restrict_duties(case, plan, duties):
    if plan.get('case_identity') != case.identity() or duty_signature(plan) != tuple(sorted(tuple(d) for d in duties)):
        raise ValueError('Input does not preserve the two committed ordered duties')
    allowed = {(None, d[0]) for d in duties} | {(d[-1], None) for d in duties}
    allowed |= {pair for d in duties for pair in zip(d, d[1:])}
    movements = tuple(m for m in case.movements if (m.before, m.after) in allowed)
    view = replace(case, name=case.name+'-fixed-duty-movement-subset', movements=movements)
    selected = {mid for v in plan['vehicles'] for mid in v['movements']}
    if not selected <= {m.id for m in movements}:
        raise ValueError('Common input is outside fixed-duty movement view')
    reidentified = deepcopy(plan)
    reidentified['case_identity'] = view.identity()
    return view, reidentified


def restore_plan(plan, full_case):
    restored = deepcopy(plan)
    restored['case_identity'] = full_case.identity()
    return restored


def value(case, plan, replay, context):
    from egglab import native_hull as nh
    if replay.get('replay_ok') is not True or plan.get('case_identity') != case.identity():
        raise ValueError('Value requires caller-replayed original physical case')
    loads = tuple(nh.rational(v) for v in replay['load'])
    if len(loads) != len(context['a']):
        raise ValueError('Literal market/load dimensions differ')
    ops = nh.rational(replay['ops_cost'])
    posted = sum((nh.rational(p)*L for p, L in zip(context['posted'], loads)), Q(0))
    quadratic = sum((nh.rational(b)*L*L/2 for b, L in zip(context['b'], loads)), Q(0))
    target_linear = sum((nh.rational(a)*L for a, L in zip(context['alpha'], loads)), Q(0))
    target_quad = sum((nh.rational(b)*L*L/2 for b, L in zip(context['beta'], loads)), Q(0))
    background = sum((nh.rational(a)*Q(u)+nh.rational(b)*Q(u)**2/2
                      for a,b,u in zip(context['a'], context['b'], context['U'])), Q(0))
    target = ops+target_linear+target_quad
    if context['id'] == 'b0_all':
        if not posted == posted+quadratic == posted+2*quadratic:
            raise ValueError('b0 context economic aliases do not coincide exactly')
        original_selected = ops+posted
    elif context['id'] == 'posted':
        original_selected = ops+posted
    elif context['id'] == 'system':
        original_selected = ops+posted+quadratic
    elif context['id'] == 'strategic':
        original_selected = ops+posted+2*quadratic
    else:
        raise ValueError('Unknown selected economic lens')
    bridge_residual = target-original_selected
    if bridge_residual != 0:
        raise ValueError('Solver coefficient bridge differs from original selected institution')
    modes = {m.id: m for m in case.movements}
    minutes = sum((nh.rational(l.arrive_min-l.depart_min) for v in plan['vehicles']
        for mid in v['movements'] for l in modes[mid].legs), Q(0))
    service = sum((nh.rational(t.energy_kwh) for t in case.trips), Q(0))
    movement = sum((nh.rational(l.energy_kwh) for v in plan['vehicles']
        for mid in v['movements'] for l in modes[mid].legs), Q(0))
    return dict(replay_ok=True, context_id=context['id'], institution=context['institution'],
        objective_identity=objective_identity(context), total_exact=str(target), target_bill_exact=str(target),
        source_original_lens_total_exact=str(original_selected), coefficient_bridge_residual_exact=str(bridge_residual),
        electricity_exact=str(target_linear+target_quad), linear_electricity_exact=str(target_linear),
        quadratic_electricity_exact=str(target_quad), ops_cost_exact=str(ops),
        fleet_count=len(plan['vehicles']), vehicle_cost_exact=str(Q(case.vehicle_cost)*len(plan['vehicles'])),
        deadhead_minutes_exact=str(minutes), deadhead_cost_exact=str(Q(case.deadhead_cost_per_min)*minutes),
        service_energy_exact=str(service), movement_energy_exact=str(movement),
        consumption_kwh_exact=str(nh.rational(replay['consumption_kwh'])),
        grid_kwh_exact=str(nh.rational(replay['grid_kwh'])), period_loads=list(replay['load']),
        max_grid_kw=replay['max_grid_kw'],
        lenses=dict(posted=dict(electricity_exact=str(posted), total_exact=str(ops+posted)),
            system_increment=dict(electricity_exact=str(posted+quadratic), total_exact=str(ops+posted+quadratic)),
            strategic=dict(electricity_exact=str(posted+2*quadratic), total_exact=str(ops+posted+2*quadratic))),
        system_background_exact=str(background), system_total_including_background_exact=str(ops+posted+quadratic+background),
        units='synthetic generator cost units; grid/battery kWh; minutes; no calibrated money')
