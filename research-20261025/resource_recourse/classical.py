"""Prospective exact-fleet builder composition: one acquisition or two route calls.

No source/model mutation, completion solve, retry, or optimizer on module import.
"""
from fractions import Fraction as Q
import math
import time

POLICY = 'resource-recourse-exact-N-full-graph-two-routing-calls-v1'


class CompositionError(ValueError):
    pass


def opportunity(case, plan, nh):
    """Ideal path/resource diagnostics only, never a native feasibility certificate.

    Uses admitted path IDs, not charges or plan.case_identity. This permits the
    parent's explicit original-path/current-variant diagnostic without a lift.
    """
    out = dict(available=False, diagnostic_only=True, native_feasibility_certificate=False,
        projected_load_set_equality_claim=False, price_optimality_claim=False,
        source1_cheap_period_indices=[18, 19, 20, 21], unavailable_reasons=[])
    try:
        q = nh.rational
        battery, reserve, efficiency = q(case.battery_kwh), q(case.reserve_kwh), q(case.efficiency)
        opened, deadline = q(case.terminal_open_min), q(case.recharge_deadline_min)
        if not (battery > reserve >= 0 and 0 < efficiency <= 1 and 0 <= opened <= deadline):
            raise ValueError('Missing valid constant-efficiency/battery/terminal assumptions')
        edges = [q(value) for value in case.market_edges_min]
        if len(edges) != 31 or edges[0] != 0 or edges[-1] != deadline or any(
                a >= b for a, b in zip(edges, edges[1:])):
            raise ValueError('Missing declared30-period ordered market grid')
        resources, last_end = [], Q(0)
        for resource in case.resources:
            start, end = q(resource.start_min), q(resource.end_min)
            per_bus, grid = q(resource.per_bus_kw), q(resource.grid_kw)
            if (start != last_end or end <= start or min(per_bus, grid) < 0
                    or type(resource.connectors) is not int or resource.connectors not in (0, 1)):
                raise ValueError('Missing contiguous zero/one-connector resource assumptions')
            resources.append((start, end, min(per_bus, grid) if resource.connectors else Q(0)))
            last_end = end
        if not resources or last_end != deadline:
            raise ValueError('Resource horizon does not cover declared deadline')
        trips, modes = {t.id: t for t in case.trips}, {m.id: m for m in case.movements}
        per_vehicle, windows, returns = [], [], []
        total_grid = Q(0)
        if not plan['vehicles']:
            raise ValueError('No admitted vehicle paths')
        for vehicle in plan['vehicles']:
            service = sum((q(trips[tid].energy_kwh) for tid in vehicle['trips']), Q(0))
            chosen = [modes[mid] for mid in vehicle['movements']]
            if not chosen or chosen[-1].kind != 'pullin' or not chosen[-1].legs:
                raise ValueError('Admitted path has no terminal pullin')
            movement = sum((q(leg.energy_kwh) for mode in chosen for leg in mode.legs), Q(0))
            if service < 0 or movement < 0:
                raise ValueError('Negative energy violates the ideal prefix diagnostic assumptions')
            demand = service+movement
            grid_demand = demand/efficiency
            margin = battery-reserve-demand
            returned = q(chosen[-1].legs[-1].arrive_min)
            if returned > deadline:
                raise ValueError('Terminal return exceeds common deadline')
            returns.append(returned)
            total_grid += grid_demand
            per_vehicle.append(dict(vehicle=vehicle['vehicle'], service_energy_exact=str(service),
                movement_energy_exact=str(movement), total_consumption_exact=str(demand),
                ideal_grid_kwh_exact=str(grid_demand), no_midday_soc_margin_kwh_exact=str(margin),
                no_midday_soc_sufficient=margin >= 0, last_pullin_return_min_exact=str(returned)))
            for mode in chosen:
                if mode.kind == 'depot':
                    split = mode.depot_split
                    if type(split) is not int or not 1 <= split < len(mode.legs):
                        raise ValueError('Selected depot split unavailable')
                    lo, hi = q(mode.legs[split-1].arrive_min), q(mode.legs[split].depart_min)
                    if hi < lo:
                        raise ValueError('Selected depot window is not chronological')
                    windows.append(dict(vehicle=vehicle['vehicle'], movement=mode.id,
                                        lo_min_exact=str(lo), hi_min_exact=str(hi)))
        common_start = max([opened]+returns)

        def capacity(left, right):
            return sum((rate*max(Q(0), min(end, right)-max(start, left))/60
                        for start, end, rate in resources), Q(0))

        terminal_capacity = capacity(common_start, deadline)
        cheap_capacity = sum((capacity(edges[t], edges[t+1]) for t in (18, 19, 20, 21)), Q(0))
        terminal_cheap_capacity = sum((capacity(max(common_start, edges[t]), edges[t+1])
                                      for t in (18, 19, 20, 21)), Q(0))
        all_early = all(value <= opened for value in returns)
        all_no_midday = all(row['no_midday_soc_sufficient'] for row in per_vehicle)
        out.update(available=True, per_vehicle=per_vehicle, selected_depot_windows=windows,
            total_ideal_grid_kwh_exact=str(total_grid), common_terminal_start_min_exact=str(common_start),
            all_return_by_terminal_open=all_early, all_no_midday_soc_sufficient=all_no_midday,
            common_terminal_capacity_grid_kwh_exact=str(terminal_capacity),
            source1_cheap_resource_capacity_grid_kwh_exact=str(cheap_capacity),
            common_terminal_cheap_capacity_grid_kwh_exact=str(terminal_cheap_capacity),
            total_grid_le_common_terminal_capacity=total_grid <= terminal_capacity,
            total_grid_le_common_terminal_cheap_capacity=total_grid <= terminal_cheap_capacity,
            E_le_cheapcap_conditional=(total_grid <= terminal_cheap_capacity
                                       if all_early and all_no_midday else None),
            conditional_assumptions='Admitted paths; nonnegative consumption; full initial/final batteries; '
                'constant efficiency; common deadline; zero/one serial connector; all return by opening '
                'and each bus can reach terminal without midday charging',
            interpretation='Ideal demand/window/capacity diagnostics only. Optional daytime charging '
                'can still lower quadratic cost; no feasibility, set-equality or optimality claim.')
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, ZeroDivisionError) as exc:
        out['unavailable_reasons'].append(type(exc).__name__+': '+str(exc))
    return out


def _paths(plan):
    return tuple(sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles']))


def _guard(check, deadline):
    check()
    if time.monotonic() >= deadline:
        raise TimeoutError('Absolute classical stage cutoff exhausted')


def _build(case, fleet_N, fixed_ids, check, deadline):
    from egglab import native_pathflow as pf, native_recharge as nr
    _guard(check, deadline)
    if pf._optimize_once is not nr._optimize_once:
        raise CompositionError('Original optimizer alias changed')
    if type(fleet_N) is not int or not 1 <= fleet_N <= case.max_vehicles:
        raise CompositionError('Invalid exact fleet quantity')
    built = pf.build_feasible_model(case, 'GRB')
    _guard(check, deadline)
    import mip
    model = built['model']
    original_rows = model.num_rows
    if (built['physical_identity'] != case.identity()
            or len(built['x']) != len(case.movements)
            or original_rows != built['constraint_count_before_objective']):
        raise CompositionError('Original physical builder identity/dimensions differ')
    starts = [var for movement, var in zip(case.movements, built['x']) if movement.kind == 'pullout']
    model += mip.xsum(starts) == fleet_N
    if model.num_rows != original_rows+1:
        raise CompositionError('Exact-fleet equality row not added once')
    # Keep optimize diagnostics truthful about the one additional restriction.
    built['constraint_count_before_objective'] = model.num_rows
    built['resource_recourse_original_rows'] = original_rows
    if fixed_ids is not None:
        selected = set(fixed_ids)
        if len(selected) != len(fixed_ids) or not selected <= {m.id for m in case.movements}:
            raise CompositionError('Fixed reference IDs duplicated/unknown')
        for movement, var in zip(case.movements, built['x']):
            if str(var.var_type) != 'B' or var.lb != 0 or var.ub != 1:
                raise CompositionError('Original route variable is not free binary0/1')
            var.lb = var.ub = int(movement.id in selected)
    model.seed = 17
    model.threads = 1
    if model.seed != 17 or model.threads != 1:
        raise CompositionError('Native seed/thread setup differs')
    _guard(check, deadline)
    return built


def _one_call(built, native_end, admission_end, check, ledger, stage, record, index, packets):
    from egglab import native_pathflow as pf, native_recharge as nr
    _guard(check, native_end)
    budget = nr.Budget(backend='GRB', threads=1,
        phase_seconds=native_end-time.monotonic(), wall_seconds=admission_end-time.monotonic())
    ledger[stage] += 1
    entered = time.monotonic()
    packet = dict(stage=stage, index=index, entered_monotonic=entered,
        native_deadline=native_end, stats=None, physical_candidate_admitted=False,
        native_invocation_attempted=True, native_call_observed=None)
    packets.append(packet)
    try:
        packet['stats'] = pf._optimize_once(built, budget, native_end)
        packet['native_call_observed'] = 1
    except Exception:
        # An optimizer exception may precede or follow its actual native call.
        ledger[stage] = None
        raise
    finally:
        packet['returned_monotonic'] = time.monotonic()
        packet['native_overrun_s'] = max(0., packet['returned_monotonic']-native_end)
        if record:
            record({'event': 'classical_native_return', 'stage': stage})
    if built['model'].seed != 17 or built['model'].threads != 1:
        raise CompositionError('Native seed/thread changed')
    _guard(check, admission_end)
    return packet


def _extract(case, built, packet, fleet_N, check, deadline, record, fixed_paths=None):
    from egglab import native_pathflow as pf, native_recharge as nr
    stats = packet['stats']
    if (stats['status'] not in ('OPTIMAL', 'FEASIBLE')
            or type(stats.get('incumbent')) not in (int, float)
            or not math.isfinite(stats['incumbent'])):
        raise ValueError('Native stage has no finite admissible incumbent')
    _guard(check, deadline)
    plan = pf._extract(case, built, record=record, round_index=packet['index'])
    _guard(check, deadline)
    replay = nr.replay_native(case, plan)
    if (len(plan['vehicles']) != fleet_N or plan.get('case_identity') != case.identity()
            or fixed_paths is not None and _paths(plan) != fixed_paths):
        raise CompositionError('Physical candidate changed exact N/case/fixed paths')
    packet['physical_candidate_admitted'] = True
    _guard(check, deadline)
    return plan, replay


def acquire(case, reference_ids, fleet_N, *, native_end, end, check, ledger, record=None):
    """One all-x-fixed full-matrix zero-price linear/operations solve, no fallback."""
    from egglab import native_pathflow as pf, native_recharge as nr
    out = dict(policy=POLICY, plan=None, replay=None, packets=[], failures=[], fatal_contract=False,
        bound_scope='Native all-x-fixed current-physics zero-price model only; no full-space certificate')
    active = 'reference_path_recovery'
    try:
        vehicles, _ = pf.recover_paths(case, reference_ids)
        fixed_paths = _paths({'vehicles': vehicles})
        if len(vehicles) != fleet_N:
            raise CompositionError('Reference topology differs from frozen N')
        active = 'acquisition_build'
        built = _build(case, fleet_N, reference_ids, check, native_end)
        pf.attach_objective(built, 'linear', [0.]*len(built['loads']))
        active = 'acquisition_linear'
        packet = _one_call(built, native_end, end, check, ledger, active, record, 0, out['packets'])
        active = 'acquisition_extraction'
        plan, replay = _extract(case, built, packet, fleet_N, check, end, record, fixed_paths)
        if abs(packet['stats']['incumbent']-float(replay['ops_cost'])) > nr.OBJECTIVE_TOL:
            raise ValueError('Zero-price native operations do not agree with physical replay')
        _guard(check, end)
        out.update(plan=plan, replay=replay)
    except Exception as exc:
        out['failures'].append(dict(stage=active, type=type(exc).__name__, message=str(exc)))
        out['fatal_contract'] = isinstance(exc, CompositionError)
    return out


def _append_points(rows, a, b, loads):
    added = False
    for values, aa, bb, load in zip(rows, a, b, loads):
        point = (float(aa+bb*load), float(-.5*bb*load*load))
        if not all(math.isfinite(v) for v in point):
            raise CompositionError('Nonfinite tangent coefficient')
        if point not in values:
            values.append(point)
            added = True
    return added


def route(case, a, b, fleet_N, *, prior_plan, first_native_end, routing_end,
          check, ledger, record=None):
    """At most two target tangent MIPs; no identical retry/completion or QP here."""
    from egglab import native_pathflow as pf, native_recharge as nr, native_hull as nh
    out = dict(policy=POLICY, plan=prior_plan, replay=None, bill_exact=None,
        selected_route_source='acquired_reference' if prior_plan is not None else 'none',
        route_search_candidate_admitted=False, packets=[], failures=[], fatal_contract=False,
        bound_scope='Raw numerical tangent-model bound attribute only; no physical/global certificate')
    market = nh.Market('resource-recourse-target', tuple(a), tuple(b))
    rows = [[(float(aa), 0.)] for aa in a]
    best_bill = None
    active = 'routing_prior'
    try:
        nh.validate_market(case, market)
        if prior_plan is not None:
            replay = nr.replay_native(case, prior_plan)
            if len(prior_plan['vehicles']) != fleet_N:
                raise CompositionError('Current acquired prior differs from exact N')
            best_bill = nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])
            out.update(replay=replay, bill_exact=str(best_bill))
            _append_points(rows, a, b, replay['load'])
        for index, native_end in enumerate((first_native_end, routing_end)):
            active = 'routing_build_'+str(index+1)
            built = _build(case, fleet_N, None, check, native_end)
            snapshot = tuple(tuple(values) for values in rows)
            pf.attach_objective(built, 'tangents', snapshot)
            active = 'routing_MIP'
            packet = _one_call(built, native_end, routing_end, check, ledger, active, record,
                               index, out['packets'])
            packet['tangent_counts'] = [len(values) for values in snapshot]
            active = 'routing_extraction_'+str(index+1)
            plan, replay = _extract(case, built, packet, fleet_N, check, routing_end, record)
            raw_envelope = plan['ops_cost']+sum(max(slope*load+offset for slope, offset in values)
                for load, values in zip(plan['raw_solver_load'], snapshot))
            if (not math.isfinite(raw_envelope)
                    or packet['stats']['incumbent'] < raw_envelope-nr.OBJECTIVE_TOL):
                raise ValueError('Tangent native point is below reconstructed raw envelope')
            bill = nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])
            packet.update(physical_bill_exact=str(bill), raw_tangent_envelope=raw_envelope,
                          raw_tangent_native_slack=packet['stats']['incumbent']-raw_envelope)
            _guard(check, routing_end)
            out['route_search_candidate_admitted'] = True
            if best_bill is None or bill < best_bill:
                out.update(plan=plan, replay=replay, bill_exact=str(bill),
                           selected_route_source='routing_round_'+str(index+1))
                best_bill = bill
            # Only an admitted first physical candidate can create a second call.
            if index == 0 and not _append_points(rows, a, b, replay['load']):
                out['second_call_skipped'] = 'No new tangent; no identical restart'
                break
            _guard(check, routing_end)
    except Exception as exc:
        out['failures'].append(dict(stage=active, type=type(exc).__name__, message=str(exc)))
        out['fatal_contract'] = isinstance(exc, CompositionError)
    return out
