"""DRAFT: necessary preterminal cuts from one closed, projected readout only."""
import time
START = time.monotonic()
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import threading

HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
INPUT = ROOT/'research-20261025/resource_recourse/READOUT.json'
GROUPS = ((10001, 20), (10006, 20), (10009, 28), (10005, 28))
H = Q(1080)
POLICY = 'necessary-preterminal-capacity-cuts-projected-readout-v1'


class Unavailable(ValueError):
    pass


def exact(row, field):
    value = row.get(field)
    if not isinstance(value, str):
        raise Unavailable('Missing/non-string exact field: '+field)
    try:
        return Q(value)
    except (ValueError, ZeroDivisionError):
        raise Unavailable('Invalid exact field: '+field) from None


def merge(intervals):
    output = []
    for lo, hi in sorted(intervals):
        if output and lo <= output[-1][1]:
            output[-1] = (output[-1][0], max(output[-1][1], hi))
        else:
            output.append((lo, hi))
    return output


def duration(intervals):
    return sum((hi-lo for lo, hi in intervals), Q(0))


def project_opportunity(value):
    if not isinstance(value, dict):
        return None
    out = {field: value.get(field) for field in ('available', 'unavailable_reasons',
        'all_return_by_terminal_open', 'common_terminal_start_min_exact',
        'common_terminal_capacity_grid_kwh_exact', 'total_ideal_grid_kwh_exact')}
    for name, fields in (
        ('per_vehicle', ('vehicle', 'total_consumption_exact', 'ideal_grid_kwh_exact',
                         'no_midday_soc_margin_kwh_exact', 'last_pullin_return_min_exact')),
        ('selected_depot_windows', ('vehicle', 'lo_min_exact', 'hi_min_exact'))):
        rows = value.get(name)
        out[name] = [{field: row.get(field) for field in fields} if isinstance(row, dict) else None
                     for row in rows] if isinstance(rows, list) else None
    return out


def cuts(opportunity, grid):
    out = dict(available=False, unavailable_reasons=[], per_bus=[], necessary_cut_violation=None,
        feasibility_claim=False, native_or_global_certificate=False, reporting_epsilon=None)
    try:
        if not isinstance(opportunity, dict) or opportunity.get('available') is not True:
            raise Unavailable('Exported opportunity diagnostic missing/unavailable')
        if opportunity.get('all_return_by_terminal_open') is not True:
            raise Unavailable('All-return-by-opening assumption unavailable/false')
        if exact(opportunity, 'common_terminal_start_min_exact') != H:
            raise Unavailable('Common terminal start is not1080')
        total_energy = exact(opportunity, 'total_ideal_grid_kwh_exact')
        terminal_capacity = exact(opportunity, 'common_terminal_capacity_grid_kwh_exact')
        if total_energy < 0 or terminal_capacity < 0:
            raise Unavailable('Negative exported energy/capacity')
        vehicles = opportunity.get('per_vehicle')
        windows = opportunity.get('selected_depot_windows')
        if not isinstance(vehicles, list) or not vehicles or not isinstance(windows, list):
            raise Unavailable('Missing bus/window lists')
        by_vehicle, parsed, efficiencies, usable = {}, [], set(), set()
        for ordinal, row in enumerate(vehicles, 1):
            vehicle = row.get('vehicle')
            if type(vehicle) is not int or vehicle < 0 or vehicle in by_vehicle:
                raise Unavailable('Missing/duplicate local bus join')
            demand = exact(row, 'total_consumption_exact')
            energy = exact(row, 'ideal_grid_kwh_exact')
            margin = exact(row, 'no_midday_soc_margin_kwh_exact')
            returned = exact(row, 'last_pullin_return_min_exact')
            if demand < 0 or energy < 0 or not 0 <= returned <= H:
                raise Unavailable('Negative demand/energy or return outside preterminal assumptions')
            if demand == 0:
                if energy != 0 or margin < 0:
                    raise Unavailable('Inconsistent zero-demand bus')
                lower = Q(0)
            else:
                if energy <= 0:
                    raise Unavailable('Positive consumption lacks positive grid demand')
                efficiency = demand/energy
                if not 0 < efficiency <= 1:
                    raise Unavailable('Reconstructed efficiency outside(0,1]')
                efficiencies.add(efficiency)
                lower = energy*max(Q(0), -margin)/demand
            if demand+margin < 0:
                raise Unavailable('Negative implied usable battery')
            usable.add(demand+margin)
            by_vehicle[vehicle] = ordinal
            parsed.append(dict(ordinal=ordinal, demand=demand, energy=energy, lower=lower,
                               windows=[], raw_window_count=0))
        if len(efficiencies) > 1 or len(usable) != 1:
            raise Unavailable('Inconsistent common efficiency/usable-battery margins')
        if sum((row['energy'] for row in parsed), Q(0)) != total_energy:
            raise Unavailable('Exported total energy differs from bus sum')
        for row in windows:
            vehicle = row.get('vehicle')
            if type(vehicle) is not int or vehicle not in by_vehicle:
                raise Unavailable('Depot window lacks a known local bus join')
            lo, hi = exact(row, 'lo_min_exact'), exact(row, 'hi_min_exact')
            if lo < 0 or hi < lo:
                raise Unavailable('Invalid chronological depot window')
            bus = parsed[by_vehicle[vehicle]-1]
            bus['raw_window_count'] += 1
            left, right = max(Q(0), lo), min(H, hi)
            if left < right:
                bus['windows'].append((left, right))
        rate = min(Q(90), Q(grid))
        all_intervals, sum_lower, sum_bus_union = [], Q(0), Q(0)
        for row in parsed:
            merged = merge(row['windows'])
            minutes = duration(merged)
            capacity = rate*minutes/60
            signed = capacity-row['lower']
            out['per_bus'].append(dict(bus_ordinal=row['ordinal'], ell_grid_kwh_exact=str(row['lower']),
                preterminal_capacity_grid_kwh_exact=str(capacity), capacity_minus_ell_exact=str(signed),
                necessary_cut_violated=signed < 0, selected_window_count=row['raw_window_count'],
                clipped_nonempty_window_count=len(row['windows']), merged_interval_count=len(merged),
                union_minutes_exact=str(minutes), overlap_minutes_exact=str(duration(row['windows'])-minutes)))
            all_intervals.extend(merged)
            sum_lower += row['lower']
            sum_bus_union += minutes
        shared = merge(all_intervals)
        union_minutes = duration(shared)
        shared_capacity = rate*union_minutes/60
        terminal_shortfall = max(Q(0), total_energy-terminal_capacity)
        required = max(sum_lower, terminal_shortfall, Q(0))
        signed = shared_capacity-required
        out.update(available=True, bus_count=len(parsed), effective_power_kw_exact=str(rate),
            reconstructed_efficiency_exact=str(next(iter(efficiencies))) if efficiencies else None,
            efficiency_scope='Reconstructed consistently from positive-demand buses; unidentified if all demands zero',
            total_ideal_grid_kwh_exact=str(total_energy), terminal_capacity_grid_kwh_exact=str(terminal_capacity),
            sum_bus_ell_grid_kwh_exact=str(sum_lower), terminal_energy_shortfall_grid_kwh_exact=str(terminal_shortfall),
            shared_required_grid_kwh_exact=str(required), shared_union_capacity_grid_kwh_exact=str(shared_capacity),
            shared_capacity_minus_required_exact=str(signed),
            shared_capacity_minus_sum_ell_exact=str(shared_capacity-sum_lower),
            shared_capacity_minus_terminal_shortfall_exact=str(shared_capacity-terminal_shortfall),
            shared_union_minutes_exact=str(union_minutes), shared_merged_interval_count=len(shared),
            cross_bus_overlap_minutes_exact=str(sum_bus_union-union_minutes),
            necessary_cut_violation=signed < 0 or any(row['necessary_cut_violated'] for row in out['per_bus']),
            interpretation='Necessary ideal-model cuts only; nonnegative margins do not prove feasibility. '
                'Exact represented violations are not tolerance-qualified code/native/global certificates.')
    except Unavailable as exc:
        out['unavailable_reasons'].append(str(exc))
    except (KeyError, TypeError, ValueError, AttributeError, ZeroDivisionError):
        out['unavailable_reasons'].append('Malformed permitted projection; no fallback input was opened')
    return out


def status(row):
    """Only admission/status context, never native objectives, costs or loads."""
    worker = row.get('worker') or {}
    context = {name: row.get(name) for name in ('attempted', 'parent_endpoint_accepted',
        'physical_new_prior_valid', 'cell_qualified', 'full_method_success', 'operational_source',
        'retained_route_changed_from_reference', 'unattempted_reason', 'missing_reference')}
    context.update({name: worker.get(name) for name in ('physical_witness_valid',
        'route_search_candidate_admitted', 'qp_success', 'qp_candidate_admitted', 'missing_reason')})
    context['acquisition_native_statuses'] = [(packet.get('stats') or {}).get('status')
                                             for packet in worker.get('acquisition_packets', [])]
    context['routing_native_statuses'] = [(packet.get('stats') or {}).get('status')
                                         for packet in worker.get('routing_packets', [])]
    context['QP_native_status'] = (worker.get('stats') or {}).get('Status')
    return context


def assignments():
    output = []
    for base, services in GROUPS:
        for grid in (90, 45):
            common = dict(group=f'physical_v2_s{base}', base_id=base, services=services, grid_kw=grid)
            output.append(dict(common, role='original_reference', target_source=None))
            for target in ('source0', 'source1'):
                output.append(dict(common, role='planned_adaptive', target_source=target))
    return output


def write(path, value, *, exclusive=False):
    target = path if exclusive else path.with_name(path.name+'.tmp')
    with target.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    if not exclusive:
        os.replace(target, path)


def main():
    if HERE != ROOT/'research-20261025/capacity_cut_diagnostic':
        raise ValueError('Wrong diagnostic namespace')
    launch_path = HERE/'LAUNCH.json'
    launch_raw = launch_path.read_bytes()
    launch = json.loads(launch_raw)
    budget = dict(body_cpu_s=15, body_wall_s=35, total_cpu_s=20, total_wall_s=45,
                  publication_cpu_reserve_s=5, publication_wall_reserve_s=10)
    if (launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS'
            or launch.get('budgets') != budget or not launch.get('tracking_prefix')
            or launch.get('input') != str(INPUT)):
        raise ValueError('DRAFT/unreviewed/unfunded diagnostic: no numerical input admitted')
    output = HERE/'attempt01'
    output.mkdir(exist_ok=False)
    receipt = output/'receipt.json'
    write(receipt, dict(receipt_complete=False, body_complete=False), exclusive=True)
    report = dict(policy=POLICY, receipt_complete=False, body_complete=False, failures=[],
        records=[dict(row, cut=dict(available=False, unavailable_reasons=['Body not completed']))
                 for row in assignments()], input_sha256={}, budgets=budget,
        tracking_prefix=launch['tracking_prefix'], independent_analytical_package=True,
        closed_resource_recourse_package_reopened=False, external_total_acceptance_pending=True,
        ideal_assumptions=dict(terminal_open_min_exact='1080', bus_power_kw_exact='90',
            constant_grid_levels_kw=[90, 45], one_serial_connector=True,
            full_initial_batteries=True, reserve_at_final_return=True, constant_efficiency=True,
            nonnegative_consumption=True, no_consumption_after_final_return=True,
            no_terminal_charging_before_open=True, divisible_preemptible_charging=True,
            scope='Inherited model assumptions; only exported identity-free diagnostics checked here'))
    stopped = None
    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        raise TimeoutError('Latched diagnostic stop')
    def check():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        if (stopped is not None or time.monotonic()-START >= 35
                or usage.ru_utime+usage.ru_stime >= 15 or threading.active_count() != 1):
            raise TimeoutError('Diagnostic body resource/stop boundary')
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (15, 20))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 35-(time.monotonic()-START)))
        for path, raw in ((Path(__file__).resolve(), None), (HERE/'PROTOCOL.md', None), (launch_path, launch_raw)):
            check()
            report['input_sha256'][str(path)] = hashlib.sha256(path.read_bytes() if raw is None else raw).hexdigest()
        check()
        before = INPUT.stat()
        raw = INPUT.read_bytes()
        after = INPUT.stat()
        if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ValueError('Closed derived input changed during its single read')
        digest = hashlib.sha256(raw).hexdigest()
        report['input_sha256'][str(INPUT)] = digest
        if launch.get('expected_input_sha256') is not None and digest != launch['expected_input_sha256']:
            raise ValueError('Derived input digest differs from prospective pin')
        source = json.loads(raw)
        del raw
        if (source.get('receipt_complete') is not True
                or source.get('policy') != 'resource-recourse-closed-owner-economic-readout-v1'):
            raise ValueError('Derived input is not a completed readout')
        variants, adaptive, acquisitions = {}, {}, {}
        allowed = {(f'physical_v2_s{base}', grid) for base, _ in GROUPS for grid in (90, 45)}
        for row in source.get('variants', []):
            key = row.get('group'), row.get('grid_kw')
            if key not in allowed or key in variants:
                raise ValueError('Unexpected/duplicate reference context before projection')
            variants[key] = dict(
                opportunity=project_opportunity(row.get('opportunity_diagnostics')),
                original_valid=(row.get('original_no_solve_reference') or {}).get('valid'))
        for row in source.get('acquisitions', []):
            key = row.get('group'), row.get('grid_kw')
            if key not in allowed or key in acquisitions:
                raise ValueError('Unexpected/duplicate acquisition context before projection')
            acquisitions[key] = status(row)
        for row in source.get('active', []):
            if row.get('phase') == 'adaptive':
                key = row.get('group'), row.get('grid_kw'), row.get('target_source')
                if key[:2] not in allowed or key[2] not in ('source0', 'source1') or key in adaptive:
                    raise ValueError('Unexpected/duplicate adaptive context before projection')
                context = status(row)
                accepted = (context.get('operational_source') == 'accepted_worker'
                    and context.get('parent_endpoint_accepted') is True
                    and context.get('physical_witness_valid') is True)
                adaptive[key] = dict(
                    context=context, accepted=accepted,
                    opportunity=project_opportunity(row.get('operational_opportunity_diagnostics')) if accepted else None)
        del source  # Unprojected costs/loads/other data are not retained for analysis.
        for index, assignment in enumerate(assignments()):
            check()
            identity = assignment['group'], assignment['grid_kw']
            record = dict(assignment)
            if assignment['role'] == 'original_reference':
                row = variants.get(identity, {})
                record['context'] = dict(acquisitions.get(identity, {}))
                record['context']['original_no_solve_valid'] = row.get('original_valid')
                opportunity = row.get('opportunity')
            else:
                row = adaptive.get(identity+(assignment['target_source'],), {})
                record['context'] = row.get('context', {})
                accepted = row.get('accepted') is True
                changed = record['context'].get('retained_route_changed_from_reference')
                record['retained_role'] = ('accepted_changed_route' if changed is True else
                    'accepted_unchanged_route' if changed is False else 'accepted_route_relation_unknown') if accepted else (
                    'acquired_prior_fallback_no_new_topology' if record['context'].get('operational_source') == 'acquired_prior_fallback'
                    else 'missing_unadmitted_adaptive_topology')
                opportunity = row.get('opportunity') if accepted else None
            record['cut'] = cuts(opportunity, assignment['grid_kw'])
            report['records'][index] = record
        report['body_complete'] = True
        check()
    except Exception as exc:
        report['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
        remaining = min(10., 45.-(time.monotonic()-START))
        if remaining <= 0:
            raise TimeoutError('No diagnostic publication reserve remains')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        report.update(receipt_complete=True, stopped_signal=stopped,
            administrative_body_pass=bool(report['body_complete'] and not report['failures'] and stopped is None),
            statistical_unit='Four exposed groups; resource/target repeats are not independent cases',
            interpretation='Necessary ideal-model cuts only; no sufficiency, native/global certificate, '
                'tolerance relabeling, cost/ML gate or automatic retry')
        report['counts'] = {role: dict(planned=sum(row['role'] == role for row in report['records']),
            available=sum(row['role'] == role and row['cut'].get('available') is True for row in report['records']),
            unavailable=sum(row['role'] == role and row['cut'].get('available') is not True for row in report['records']),
            ideal_necessary_cut_violations=sum(row['role'] == role and row['cut'].get('necessary_cut_violation') is True
                                              for row in report['records']))
            for role in ('original_reference', 'planned_adaptive')}
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['resources_prepublication'] = dict(user_s=usage.ru_utime, system_s=usage.ru_stime,
            elapsed_s=time.monotonic()-START, python_threads=threading.active_count())
        write(receipt, report)
        print(json.dumps(dict(counts=report['counts'], records=[dict(
            group=row['group'], grid_kw=row['grid_kw'], target=row['target_source'], role=row['role'],
            retained_role=row.get('retained_role'), available=row['cut'].get('available'),
            shared_capacity_minus_required_exact=row['cut'].get('shared_capacity_minus_required_exact'),
            necessary_cut_violation=row['cut'].get('necessary_cut_violation'),
            unavailable_reasons=row['cut'].get('unavailable_reasons')) for row in report['records']]), indent=2))
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['administrative_body_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
