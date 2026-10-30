"""Frozen all-declared-mode ideal outer cuts; eight fixed owned files, stdlib only."""
import time
START = time.monotonic()
from fractions import Fraction as Q
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading

ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = Path(__file__).resolve().parent
SOURCE = ROOT/'research-20261025/resource_recourse/attempt01'
CASES = ((10001, 20, 1), (10006, 20, 4), (10009, 28, 5), (10005, 28, 8))
H = Q(1080)
POLICY = 'all-declared-mode-fixed-N-ideal-capacity-outer-cuts-v1'
MAX_RSS = 5*1024**3


class Unavailable(ValueError):
    def __init__(self, message, **findings):
        super().__init__(message)
        self.findings = findings


def number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise Unavailable('Missing/nonfinite represented scalar: '+name)
    # Fraction(float) is exact on the stored binary coefficient, not rational recovery.
    return Q(value)


def merge(intervals):
    output = []
    for left, right in sorted(intervals):
        if output and left <= output[-1][1]:
            output[-1] = (output[-1][0], max(output[-1][1], right))
        else:
            output.append((left, right))
    return output


def project_case(raw):
    """Do not inspect costs, plans, prices, reference IDs or reconstruct case identity."""
    if not isinstance(raw, dict):
        raise Unavailable('Missing case projection')
    result = {field: raw.get(field) for field in ('depot', 'graph_scope', 'battery_kwh',
        'reserve_kwh', 'efficiency', 'terminal_open_min', 'recharge_deadline_min', 'market_edges_min')}
    for name, fields in (
        ('trips', ('id', 'start_min', 'end_min', 'energy_kwh')),
        ('resources', ('start_min', 'end_min', 'per_bus_kw', 'grid_kw', 'connectors'))):
        rows = raw.get(name)
        if not isinstance(rows, list):
            raise Unavailable('Missing physical list: '+name)
        result[name] = [{field: row.get(field) for field in fields} for row in rows]
    result['movements'] = []
    rows = raw.get('movements')
    if not isinstance(rows, list):
        raise Unavailable('Missing declared movement list')
    for row in rows:
        movement = {field: row.get(field) for field in ('id', 'kind', 'before', 'after', 'depot_split')}
        legs = row.get('legs')
        if not isinstance(legs, list):
            raise Unavailable('Missing movement legs')
        movement['legs'] = [{field: leg.get(field) for field in
            ('origin', 'destination', 'depart_min', 'arrive_min', 'energy_kwh')} for leg in legs]
        result['movements'].append(movement)
    return result


def bound(case, fleet_N, grid, reserve_at_opening):
    out = dict(available=False, unavailable_reasons=[], structural_findings={}, reporting_epsilon=None,
        native_certificate=False, unrestricted_EVSP_certificate=False, native_classification_changed=False)
    try:
        if type(fleet_N) is not int or fleet_N <= 0:
            raise Unavailable('Fixed N is not positive canonical metadata')
        if case['graph_scope'] != 'declared-movement-modes-only' or not isinstance(case['depot'], str) or not case['depot']:
            raise Unavailable('Missing declared-universe/depot geometry context')
        battery = number(case['battery_kwh'], 'battery')
        reserve = number(case['reserve_kwh'], 'reserve')
        eta = number(case['efficiency'], 'efficiency')
        opened = number(case['terminal_open_min'], 'terminal opening')
        deadline = number(case['recharge_deadline_min'], 'deadline')
        if not battery > reserve >= 0 or not 0 < eta <= 1 or opened != H or deadline < H:
            raise Unavailable('Battery/efficiency/opening/horizon assumptions unavailable')
        edges = [number(value, 'horizon edge') for value in case['market_edges_min']]
        if len(edges) < 2 or edges[0] != 0 or edges[-1] != deadline or any(a >= b for a, b in zip(edges, edges[1:])):
            raise Unavailable('Declared market horizon is incomplete/unordered')
        resources, end_previous = [], Q(0)
        for row in case['resources']:
            left, right = number(row['start_min'], 'resource start'), number(row['end_min'], 'resource end')
            per_bus, original_grid = number(row['per_bus_kw'], 'bus power'), number(row['grid_kw'], 'source grid power')
            if (left != end_previous or right <= left or per_bus != 90 or original_grid != 90
                    or type(row['connectors']) is not int or row['connectors'] != 1):
                raise Unavailable('Source p90 constant-power/one-connector resource assumptions differ')
            resources.append((left, right, min(per_bus, Q(grid))))
            end_previous = right
        if not resources or end_previous != deadline:
            raise Unavailable('Resource horizon does not cover declared deadline')
        trips, incoming, outgoing = {}, {}, {}
        service, completed_service, all_early = Q(0), Q(0), True
        for row in case['trips']:
            identifier = row['id']
            if not isinstance(identifier, str) or not identifier or identifier in trips:
                raise Unavailable('Missing/duplicate trip identity')
            start, end = number(row['start_min'], 'service start'), number(row['end_min'], 'service end')
            energy = number(row['energy_kwh'], 'service energy')
            if not 0 <= start < end <= deadline or energy < 0:
                raise Unavailable('Service chronology/nonnegative energy assumption differs')
            trips[identifier] = (start, end)
            incoming[identifier], outgoing[identifier] = [], []
            service += energy
            if end <= H:
                completed_service += energy
            all_early &= end <= H
        if not trips or fleet_N > len(trips):
            raise Unavailable('No nonempty fixed-N coverage under projected service count')
        seen, pullouts, pullins, windows = set(), [], [], []
        leg_count = depot_count = 0
        for row in case['movements']:
            identifier, kind, before, after = row['id'], row['kind'], row['before'], row['after']
            if not isinstance(identifier, str) or not identifier or identifier in seen:
                raise Unavailable('Missing/duplicate declared movement identity')
            seen.add(identifier)
            valid = ((kind == 'pullout' and before is None and after in trips)
                or (kind == 'pullin' and before in trips and after is None)
                or (kind in ('direct', 'depot') and before in trips and after in trips and before != after))
            if not valid or not row['legs']:
                raise Unavailable('Invalid kind/before/after incidence or empty movement')
            energy, legs, previous = Q(0), [], None
            for leg in row['legs']:
                depart = number(leg['depart_min'], 'leg departure')
                arrive = number(leg['arrive_min'], 'leg arrival')
                draw = number(leg['energy_kwh'], 'individual leg energy')
                if (not 0 <= depart <= arrive <= deadline or draw < 0
                        or not isinstance(leg['origin'], str) or not leg['origin']
                        or not isinstance(leg['destination'], str) or not leg['destination']):
                    raise Unavailable('Invalid leg chronology/endpoints/nonnegative draw')
                if previous is not None and (previous[1] > depart or previous[2] != leg['origin']):
                    raise Unavailable('Movement legs are not a chronological connected path')
                legs.append((depart, arrive, leg['origin'], leg['destination']))
                previous = (depart, arrive, leg['destination'])
                energy += draw
                all_early &= arrive <= H
                leg_count += 1
            if (before is not None and legs[0][0] < trips[before][1]
                    or after is not None and legs[-1][1] > trips[after][0]):
                raise Unavailable('Movement timing contradicts its service incidence')
            if after is not None:
                incoming[after].append(energy)
            if before is not None:
                outgoing[before].append(energy)
            if kind == 'pullout':
                pullouts.append(energy)
            if kind == 'pullin':
                pullins.append(energy)
            if kind == 'depot':
                depot_count += 1
                split = row['depot_split']
                if (type(split) is not int or not 1 <= split < len(legs)
                        or legs[split-1][3] != case['depot'] or legs[split][2] != case['depot']):
                    raise Unavailable('Depot split lacks validated depot endpoints')
                left, right = max(Q(0), legs[split-1][1]), min(H, legs[split][0])
                if left < right:
                    windows.append((left, right))
            elif row['depot_split'] is not None:
                raise Unavailable('Non-depot mode has a depot split')
        missing_in = sum(not values for values in incoming.values())
        missing_out = sum(not values for values in outgoing.values())
        if missing_in or missing_out or not pullouts or not pullins:
            raise Unavailable('Necessary incidence/start/end candidates missing; no finite minimum invented',
                missing_incoming_trip_count=missing_in, missing_outgoing_trip_count=missing_out,
                pullout_candidate_count=len(pullouts), pullin_candidate_count=len(pullins))
        lin = sum((min(values) for values in incoming.values()), Q(0))+fleet_N*min(pullins)
        lout = sum((min(values) for values in outgoing.values()), Q(0))+fleet_N*min(pullouts)
        movement_lb = max(lin, lout)  # They partition the SAME selected modes: never sum.
        demand_lb = service+movement_lb
        union = merge(windows)
        def capacity(intervals):
            return sum((rate*max(Q(0), min(right, end)-max(left, start))/60
                        for left, right in intervals for start, end, rate in resources), Q(0))
        pre_capacity, post_capacity = capacity(union), capacity([(H, deadline)])
        total_term = max(Q(0), demand_lb/eta-post_capacity)
        soc_scope = 'all-declared-consumption-early' if all_early else 'completed-mandatory-service-only'
        soc_energy = demand_lb if all_early else completed_service
        soc_term = max(Q(0), (soc_energy-fleet_N*(battery-reserve))/eta) if reserve_at_opening else None
        required = max(Q(0), total_term, soc_term if soc_term is not None else Q(0))
        signed = pre_capacity-required
        out.update(available=True, fleet_N=fleet_N, trip_count=len(trips), movement_count=len(seen),
            leg_count=leg_count, depot_mode_count=depot_count, preterminal_nonempty_window_count=len(windows),
            preterminal_merged_interval_count=len(union),
            preterminal_union_minutes_exact=str(sum((right-left for left, right in union), Q(0))),
            service_energy_exact=str(service), completed_service_by_open_energy_exact=str(completed_service),
            incoming_partition_movement_lb_exact=str(lin), outgoing_partition_movement_lb_exact=str(lout),
            movement_energy_lb_exact=str(movement_lb), total_consumption_lb_exact=str(demand_lb),
            total_grid_energy_lb_exact=str(demand_lb/eta), efficiency_exact=str(eta),
            aggregate_usable_battery_exact=str(fleet_N*(battery-reserve)), all_mode_consumption_by_open=bool(all_early),
            SOC_term_scope=soc_scope if soc_term is not None else 'unknown-reserve-at-opening',
            SOC_preterminal_grid_lb_exact=str(soc_term) if soc_term is not None else None,
            total_energy_postcap_preterminal_lb_exact=str(total_term),
            combined_preterminal_grid_lb_exact=str(required), preterminal_capacity_grid_kwh_exact=str(pre_capacity),
            postopening_capacity_grid_kwh_exact=str(post_capacity),
            capacity_minus_SOC_term_exact=str(pre_capacity-soc_term) if soc_term is not None else None,
            capacity_minus_total_energy_term_exact=str(pre_capacity-total_term),
            capacity_minus_combined_lb_exact=str(signed), ideal_outer_cut_violation=signed < 0,
            fixed_N_complete_path_cover_scope='Inherited validated-spec provenance; independent minima do not prove existence',
            interpretation='Conditional ideal exclusion only if signed margin is negative. '
                'Nonnegative leaves route feasibility unresolved; no native-precision or unrestricted certificate.')
    except Unavailable as exc:
        out['unavailable_reasons'].append(str(exc))
        out['structural_findings'] = exc.findings
    except (KeyError, TypeError, ValueError, AttributeError, IndexError, ZeroDivisionError):
        out['unavailable_reasons'].append('Malformed authorized physical projection')
    return out


def paths():
    return [SOURCE/f'{ordinal:03d}-acquisition'/name for _, _, ordinal in CASES
            for name in ('external-receipt.json', 'spec.json')]


def write(path, value, *, exclusive=False):
    temporary = path if exclusive else path.with_name(path.name+'.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    if not exclusive:
        os.replace(temporary, path)


def main():
    if HERE != ROOT/'research-20261025/all_mode_capacity':
        raise ValueError('Wrong all-mode diagnostic namespace')
    launch_path = HERE/'LAUNCH.json'
    launch_raw = launch_path.read_bytes()
    launch = json.loads(launch_raw)
    budget = dict(body_cpu_s=25, body_wall_s=50, total_cpu_s=30, total_wall_s=60,
                  publication_cpu_reserve_s=5, publication_wall_reserve_s=10)
    if (launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS'
            or not launch.get('tracking_prefix') or launch.get('budgets') != budget
            or launch.get('inputs') != [str(path) for path in paths()]):
        raise ValueError('DRAFT/unreviewed/unfunded all-mode package: no artifact input admitted')
    output = HERE/'attempt01'
    output.mkdir(exist_ok=False)
    receipt = output/'receipt.json'
    write(receipt, dict(receipt_complete=False, body_complete=False), exclusive=True)
    records = [dict(group=f'physical_v2_s{base}', base_id=base, services=services, grid_kw=grid,
                   bound=dict(available=False, unavailable_reasons=['Body not completed']))
               for base, services, _ in CASES for grid in (90, 45)]
    report = dict(policy=POLICY, receipt_complete=False, body_complete=False, failures=[], records=records,
        input_sha256={}, group_bindings=[], budgets=budget, tracking_prefix=launch['tracking_prefix'],
        separate_new_package=True, closed_resource_packages_reopened=False, external_total_acceptance_pending=True,
        ideal_assumptions=dict(full_initial_and_terminal_batteries=True, nonnegative_consumption=True,
            constant_efficiency=True, no_unmodeled_consumption=True, grid_to_battery_only=True,
            no_terminal_charge_before_1080=True, reserve_at_opening=launch.get('reserve_at_opening_assumed') is True,
            source='Inherited physical model/provenance; selected projection checks only'))
    stopped = None
    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        raise TimeoutError('Latched all-mode diagnostic stop')
    def check():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
        if (stopped is not None or time.monotonic()-START >= 50
                or usage.ru_utime+usage.ru_stime >= 25 or threading.active_count() != 1
                or rss > MAX_RSS):
            raise TimeoutError('All-mode body resource/stop boundary')
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (25, 30))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 50-(time.monotonic()-START)))
        for path, raw in ((Path(__file__).resolve(), None), (HERE/'PROTOCOL.md', None), (launch_path, launch_raw)):
            check()
            report['input_sha256'][str(path)] = hashlib.sha256(path.read_bytes() if raw is None else raw).hexdigest()
        for index, (base, services, ordinal) in enumerate(CASES):
            check()
            folder = SOURCE/f'{ordinal:03d}-acquisition'
            group = f'physical_v2_s{base}'
            binding = dict(group=group, metadata_bound=False, spec_digest_matches_external=False)
            try:
                external_path = folder/'external-receipt.json'
                raw = external_path.read_bytes()
                report['input_sha256'][str(external_path)] = hashlib.sha256(raw).hexdigest()
                external = json.loads(raw)
                del raw
                expected = dict(task_id=f'A{ordinal:03d}-g{base}-p90', phase='acquisition', group=group,
                                base_id=base, services=services, grid_kw=90.)
                if (any(external.get(field) != value for field, value in expected.items())
                        or external.get('ordinal') != ordinal or external.get('folder') != str(folder)):
                    raise Unavailable('Fixed p90 acquisition metadata differs')
                pin = external.get('spec_sha256')
                if not isinstance(pin, str) or len(pin) != 64 or any(c not in '0123456789abcdef' for c in pin):
                    raise Unavailable('External spec digest binding missing')
                binding['metadata_bound'] = True
                del external
                spec_path = folder/'spec.json'
                raw = spec_path.read_bytes()
                actual = hashlib.sha256(raw).hexdigest()
                report['input_sha256'][str(spec_path)] = actual
                if actual != pin:
                    raise Unavailable('Consumed spec SHA256 differs from fixed external binding')
                binding['spec_digest_matches_external'] = True
                spec = json.loads(raw)
                del raw
                if (any(spec.get(field) != value for field, value in expected.items())
                        or spec.get('root') != str(ROOT) or type(spec.get('fleet_N')) is not int
                        or spec['fleet_N'] <= 0):
                    raise Unavailable('Bound spec routing/root/fixed-N metadata differs')
                identity = spec.get('expected_case_identity')
                if not isinstance(identity, str) or len(identity) != 64 or any(c not in '0123456789abcdef' for c in identity):
                    raise Unavailable('Inherited case-identity metadata missing')
                binding['expected_case_identity'] = identity
                binding['case_identity_scope'] = 'Inherited bound-spec token; not recomputed'
                fleet_N = spec['fleet_N']
                case = project_case(spec.get('case'))
                if len(case['trips']) != services:
                    raise Unavailable('Projected trip count differs from fixed service metadata')
                del spec  # Excluded plans/reference IDs/costs/prices are not retained for analysis.
                for offset, grid in enumerate((90, 45)):
                    check()
                    report['records'][2*index+offset]['bound'] = bound(case, fleet_N, grid,
                        launch.get('reserve_at_opening_assumed') is True)
            except (Unavailable, KeyError, TypeError, ValueError, AttributeError, OSError) as exc:
                binding['unavailable_reason'] = type(exc).__name__+': '+str(exc)
                for offset in (0, 1):
                    report['records'][2*index+offset]['bound'] = dict(available=False,
                        unavailable_reasons=[binding['unavailable_reason']], native_certificate=False,
                        unrestricted_EVSP_certificate=False)
            report['group_bindings'].append(binding)
        report['body_complete'] = True
        check()
    except Exception as exc:
        report['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        remaining = min(10., 60.-(time.monotonic()-START))
        if remaining <= 0:
            raise TimeoutError('No all-mode publication reserve remains')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        report.update(receipt_complete=True, stopped_signal=stopped,
            administrative_body_pass=bool(report['body_complete'] and not report['failures'] and stopped is None),
            statistical_unit='Four exposed groups; two resource levels are paired controls, not independent cases',
            interpretation='max(L_in,L_out), not their sum; SOC full-demand term requires all-mode-early '
                'condition, otherwise completed-service term only; total-demand/postcap term is separate. '
                'No sufficiency, native/global EVSP certificate, reclassification or automatic retry.')
        report['counts'] = dict(planned_groups=4, planned_controls=8,
            available_controls=sum(row['bound'].get('available') is True for row in records),
            unavailable_controls=sum(row['bound'].get('available') is not True for row in records),
            ideal_outer_cut_violations=sum(row['bound'].get('ideal_outer_cut_violation') is True for row in records))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['resources_prepublication'] = dict(user_s=usage.ru_utime, system_s=usage.ru_stime,
            elapsed_s=time.monotonic()-START, python_threads=threading.active_count(),
            observed_self_peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
            rss_limit_bytes=MAX_RSS, rss_observation_convention='ru_maxrss: bytes on macOS; KiB converted to bytes elsewhere',
            rss_scope='Observed self high-water only; no containment claim')
        write(receipt, report)
        print(json.dumps(dict(counts=report['counts'], records=records), indent=2, allow_nan=False))
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
