"""Once-only replay and two-witness coherence on fixed FIT; no optimization."""
import time
WALL0 = time.monotonic()
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading

sys.dont_write_bytecode = True
SOURCE = '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/catalog_coherence/run.py'
ROOT = Path(SOURCE).parents[2]
PRIOR = '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/train_readiness/attempt01/receipt.json'
FIT_PRIOR = '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fit_target_support/attempt01/receipt.json'
IDENTITIES = (SOURCE,
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/catalog_coherence/PROTOCOL.md',
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/catalog_coherence/LAUNCH.json')
PURE_SOURCES = tuple(str(ROOT/name) for name in ('src/egglab/__init__.py', 'src/egglab/native_recharge.py',
    'src/egglab/native_hull.py', 'src/egglab/physical_learning_cases.py'))
TABLES = {
    'cases': ('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl',
        'faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6'),
    'sources': ('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl',
        '7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5')}
FIELDS = {
    'case': 'name trips movements resources market_edges_min depot max_vehicles battery_kwh reserve_kwh terminal_open_min recharge_deadline_min vehicle_cost deadhead_cost_per_min efficiency graph_scope'.split(),
    'trip': 'id start_min end_min start_place end_place energy_kwh'.split(),
    'movement': 'id kind before after legs depot_split'.split(),
    'leg': 'origin destination depart_min arrive_min energy_kwh'.split(),
    'resource': 'start_min end_min per_bus_kw grid_kw connectors'.split()}
DEFAULTS = {'case': {'deadhead_cost_per_min': 0.0, 'efficiency': 1.0, 'graph_scope': 'declared-movement-modes-only'},
    'movement': {'depot_split': None}, 'resource': {'connectors': 1}}
KINDS, SOURCES = ('pullout', 'direct', 'depot', 'pullin'), ('source0', 'source1')
TAU = Q(1, 10**6)  # Reporting sign only, generator COST units; not a replay tolerance.


class Fault(ValueError):
    def __init__(self, code, details=None):
        self.code, self.details = code, details
        super().__init__(code)


def check():
    if time.process_time() >= 270 or time.monotonic()-WALL0 >= 540:
        raise TimeoutError('Target audit body allowance exhausted')
    if threading.active_count() != 1 or rss() > 5*1024**3:
        raise RuntimeError('One-thread/observed RSS bound failed')


def rss():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def save_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False, default=lambda v: str(v) if isinstance(v, Q) else v)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def stored(obj, kind):
    if not isinstance(obj, dict):
        raise Fault('stored_'+kind+'_not_mapping')
    extra = set(obj)-set(FIELDS[kind]); missing = set(FIELDS[kind])-set(obj)-set(DEFAULTS.get(kind, {}))
    if extra or missing:
        raise Fault('stored_'+kind+'_field_contract', dict(extra_key_names=sorted(extra), missing_key_names=sorted(missing)))
    return {key: obj[key] if key in obj else DEFAULTS[kind][key] for key in FIELDS[kind]}


def physical_case(raw, nr):
    case = stored(raw, 'case')
    case['trips'] = tuple(nr.Trip(**stored(t, 'trip')) for t in case['trips'])
    moves = []
    for item in case['movements']:
        move = stored(item, 'movement'); move['legs'] = tuple(nr.Leg(**stored(leg, 'leg')) for leg in move['legs'])
        moves.append(nr.Movement(**move))
    case['movements'] = tuple(moves); case['resources'] = tuple(nr.Resource(**stored(r, 'resource')) for r in case['resources'])
    if case['market_edges_min'] != list(range(0, 1801, 60)):
        raise Fault('source_market_grid_mismatch')
    case['market_edges_min'] = tuple(case['market_edges_min'])
    return nr.NativeCase(**case)


def replay_values(case, plan, replay, markets, nh, paired):
    c = nh.rational(replay['ops_cost']); fleet = nh.rational(case.vehicle_cost)*len(plan['vehicles'])
    minutes = Q(0); by_id = {m.id: m for m in case.movements}
    for vehicle in plan['vehicles']:
        for mid in vehicle['movements']:
            for leg in by_id[mid].legs:
                duration = leg.arrive_min-leg.depart_min
                minutes += nh.rational(duration)
    deadhead = nh.rational(case.deadhead_cost_per_min)*minutes
    result = dict(vehicle_count=len(plan['vehicles']), replay_ops_cost=c, replay_ops_numeric_repr=repr(replay['ops_cost']), fleet_cost=fleet,
        movement_leg_minutes=minutes, deadhead_coefficient=nh.rational(case.deadhead_cost_per_min),
        deadhead_cost=deadhead, ops_component_residual=c-fleet-deadhead,
        grid_energy_kwh=nh.rational(replay['grid_kwh']), consumption_kwh=nh.rational(replay['consumption_kwh']), markets={})
    if paired:
        loads = [nh.rational(value) for value in replay['load']]
        for name, market in markets.items():
            nh.validate_market(case, market)
            electricity = nh.supply(market, replay['load'])
            linear = sum((nh.rational(a)*load for a, load in zip(market.a, loads)), Q(0))
            quadratic = sum((nh.rational(b)*load*load/2 for b, load in zip(market.b, loads)), Q(0))
            result['markets'][name] = dict(F=c+electricity, electricity=electricity, linear=linear,
                quadratic=quadratic, total_component_residual=c+electricity-fleet-deadhead-linear-quadratic)
    return result


def distribution(values, planned):
    v = sorted(x for x in values if x is not None); n = len(v)
    return dict(planned=planned, defined=n, missing=planned-n, mean_over_admitted_groups=sum(v, Q(0))/n if n else None,
        complete_planned_mean=sum(v, Q(0))/planned if n == planned else None,
        median=None if not n else v[n//2] if n % 2 else (v[n//2-1]+v[n//2])/2,
        minimum=v[0] if n else None, maximum=v[-1] if n else None)


def coherence(p0, p1):
    d0 = p1['markets']['source0']['F']-p0['markets']['source0']['F']
    d1 = p1['markets']['source1']['F']-p0['markets']['source1']['F']
    sign = lambda d: 1 if d > TAU else -1 if d < -TAU else 0
    r0, r1 = max(Q(0), -d0), max(Q(0), d1)
    ebar = sum((p['markets'][s]['electricity'] for p in (p0, p1) for s in SOURCES), Q(0))/4
    return dict(D0=d0, D1=d1, signs=[sign(d0), sign(d1)], dominated_P0=d0 < -TAU,
        dominated_P1=d1 > TAU, R0_raw=r0, R1_raw=r1, Ebar=ebar,
        R0_over_Ebar=r0/ebar if ebar > 0 else None, R1_over_Ebar=r1/ebar if ebar > 0 else None,
        normalization_undefined_reason=None if ebar > 0 else 'Nonpositive Ebar; no floor',
        vehicle_counts_equal=p0['vehicle_count'] == p1['vehicle_count'])


def summarize(rows, planned):
    valid = [r['coherence'] for r in rows if r['coherence'] is not None]
    signs = {f'{a},{b}': 0 for a in (-1, 0, 1) for b in (-1, 0, 1)}
    for row in valid:
        signs[','.join(map(str, row['signs']))] += 1
    return dict(planned=planned, valid_pairs=len(valid), missing_or_invalid=planned-len(valid), sign_counts=signs,
        dominated_P0=sum(r['dominated_P0'] for r in valid), dominated_P1=sum(r['dominated_P1'] for r in valid),
        both_dominated=sum(r['dominated_P0'] and r['dominated_P1'] for r in valid),
        either_dominated=sum(r['dominated_P0'] or r['dominated_P1'] for r in valid),
        positive_raw_R0=sum(r['R0_raw'] > 0 for r in valid), positive_raw_R1=sum(r['R1_raw'] > 0 for r in valid),
        exact_raw_distributions={key: distribution([r[key] for r in valid], planned) for key in ('D0', 'D1', 'R0_raw', 'R1_raw')},
        normalized_aggregate_means='omitted; individual exact ratios retained without huge mixed-denominator sums')


def main():
    def expired(signum, frame):
        raise TimeoutError('Target audit body allowance exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (270, 300))
    signal.signal(signal.SIGXCPU, expired); signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 540-(time.monotonic()-WALL0)))
    if Path(__file__).resolve() != Path(SOURCE):
        raise ValueError('Only the literal frozen source may execute')
    attempt = Path(SOURCE).parent/'attempt01'; attempt.mkdir(exist_ok=False)
    target = attempt/'receipt.json'; save_new(target, dict(receipt_complete=False, audit_completed=False))
    out = dict(receipt_complete=False, audit_completed=False, checks_passed=False, catalog_report_complete=False,
        failures=[], findings=[], input_sha256={}, file_streams={}, groups=[], readiness_qualified=False)
    try:
        raw_prior = fit_prior = None
        for name in IDENTITIES+PURE_SOURCES+(PRIOR, FIT_PRIOR):
            check(); path = Path(name); before = path.stat()
            if before.st_size > 8*1024*1024:
                raise Fault('receipt_or_identity_file_exceeds8MiB')
            with path.open('rb') as stream:
                raw = stream.read(before.st_size)
            out['input_sha256'][name] = hashlib.sha256(raw).hexdigest()
            after = path.stat()
            if len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise Fault('frozen_receipt_or_identity_changed')
            if name == PRIOR:
                raw_prior = json.loads(raw)
            elif name == FIT_PRIOR:
                fit_prior = json.loads(raw)
        if raw_prior.get('checks_passed') is not True or raw_prior.get('audit_completed') is not True:
            raise Fault('prior_metadata_audit_not_admitted')
        lists = [raw_prior['files'][model+'_preprocessing']['selected']['fit_groups']['value'] for model in ('GNN', 'CatBoost')]
        if any(not isinstance(v, list) or len(v) != 80 or len(set(v)) != 80 or any(not isinstance(g, str) for g in v) for v in lists) or set(lists[0]) != set(lists[1]):
            raise Fault('two_declared_FIT_lists_not_same80_unique_groups')
        fit = set(lists[0]); bases, declared = {}, {}
        for row in raw_prior['FIT_group_provenance']:
            group, base = row['base_group']['value'], row['base_id']['value']
            if group in bases or group not in fit or type(base) is not int or group != f'physical_v2_s{base}':
                raise Fault('prior_FIT_base_mapping_invalid')
            bases[group] = base; declared[group] = row['observed_sources']['value']
        if set(bases) != fit or list(bases.values()).count(10037) != 1:
            raise Fault('prior_FIT_mapping_missing_or_incomplete_base_not_unique')
        expected = {g: {'source1'} if bases[g] == 10037 else set(SOURCES) for g in fit}
        if any(set(declared[g]) != expected[g] or len(declared[g]) != len(expected[g]) for g in fit):
            raise Fault('prior_expected79_pairs159_sources_not_reconciled')
        if fit_prior.get('checks_passed') is not True or fit_prior.get('support_report_complete') is not True:
            raise Fault('completed_target_support_receipt_not_admitted')
        for name, pin in TABLES.values():
            if fit_prior['input_sha256'].get(name) != pin:
                raise Fault('prior_target_receipt_table_binding_mismatch')
        old_groups = fit_prior['groups']
        if len(old_groups) != 80 or {r['group'] for r in old_groups} != fit:
            raise Fault('prior_target_group_denominator_mismatch')
        strata = {r['group']: 'source1_only' if bases[r['group']] == 10037 else
            'same_membership' if r['metrics']['all']['symmetric_difference'] == 0 else 'different_membership' for r in old_groups}
        if list(strata.values()).count('same_membership') != 31 or list(strata.values()).count('different_membership') != 48:
            raise Fault('prior_fixed48_31_membership_strata_mismatch')
        sys.path.insert(0, str(ROOT/'src'))
        import egglab
        from egglab import native_recharge as nr, native_hull as nh, physical_learning_cases as physical
        for module, name in zip((egglab, nr, nh, physical), PURE_SOURCES):
            if Path(module.__file__).resolve() != Path(name):
                raise Fault('pure_project_import_path_mismatch')
        cases, markets, values, case_seen, source_seen, identities, replay_status = {}, {}, {}, set(), set(), set(), {}
        out['replay_attempts'] = 0
        ordered_groups = sorted(fit); group_positions = {g: i for i, g in enumerate(ordered_groups)}
        out['groups'] = [dict(group=g, base_id=bases[g], membership_stratum=strata[g], coherence=None,
            missing_comparison_reason='unprocessed_or_table_admission_incomplete') for g in ordered_groups]

        def finding(table, line, group, code, details=None):
            out['findings'].append(dict(table=table, line=line, FIT_group=group, code=code, details=details))

        def case_row(row, group, line):
            if group in case_seen:
                cases[group] = None; raise Fault('duplicate_FIT_case')
            case_seen.add(group); cases[group] = None
            if (type(row['base_id']) is not int or row['base_id'] != bases[group] or row['split'] != 'train'
                    or row['generator'] != 'physical-fleet-learning-v2-full-factorial'):
                raise Fault('FIT_case_join_or_TRAIN_generator_mismatch')
            profile = row['physical_profile']
            if type(profile['base_id']) is not int or profile['base_id'] != bases[group] or profile['split'] != 'train':
                raise Fault('stored_profile_internal_join_mismatch')
            case = physical_case(row['case'], nr); identity = case.identity()
            if identity != row['case_identity']:
                raise Fault('canonical_case_identity_mismatch')
            ids = [m.id for m in case.movements]
            if not ids or any(not isinstance(mid, str) for mid in ids) or len(set(ids)) != len(ids):
                raise Fault('movement_universe_empty_duplicate_or_invalid')
            kinds = {m.id: m.kind for m in case.movements}
            if any(kind not in KINDS for kind in kinds.values()):
                raise Fault('unknown_movement_kind')
            cases[group] = case
            markets[group] = {s: physical.market(case, s) for s in SOURCES}

        def source_row(row, group, line):
            source = row['source']
            if source not in SOURCES:
                raise Fault('foreign_FIT_source_kind')
            key = (group, source)
            if key in source_seen:
                values[key] = None; identities.discard(key); replay_status[key] = 'duplicate_invalidated'
                raise Fault('duplicate_FIT_source')
            source_seen.add(key); values[key] = None; replay_status[key] = 'not_attempted'
            if source not in expected[group]:
                raise Fault('source_present_despite_declared_missing')
            case = cases.get(group)
            if case is None:
                raise Fault('source_has_no_admitted_common_case')
            if type(row['base_id']) is not int or row['base_id'] != bases[group] or row['case_identity'] != case.identity() or row['market_kind'] != source:
                raise Fault('source_case_or_market_kind_join_mismatch')
            if markets[group][source].identity() != row['market_identity']:
                raise Fault('canonical_source_market_identity_mismatch')
            plan = row['source_plan']
            if nr.digest(plan) != row['source_plan_hash']:  # Whole unmodified FIT plan hash; cached diagnostics not inspected.
                raise Fault('whole_source_plan_identity_mismatch')
            if not isinstance(plan, dict) or not isinstance(plan.get('vehicles'), list):
                raise Fault('plan_membership_projection_not_mapping_list')
            if plan['case_identity'] != case.identity():
                raise Fault('plan_case_identity_mismatch')
            flat = []
            for vehicle in plan['vehicles']:
                if not isinstance(vehicle, dict) or not isinstance(vehicle.get('movements'), list):
                    raise Fault('vehicle_membership_projection_not_list')
                flat.extend(vehicle['movements'])
            selected = row['selected_movements']
            if (not flat or not isinstance(selected, list) or any(not isinstance(mid, str) for mid in flat+selected)
                    or len(set(flat)) != len(flat) or len(set(selected)) != len(selected)):
                raise Fault('empty_duplicate_or_invalid_positive_membership')
            if selected != sorted(flat) or not set(selected) <= {m.id for m in case.movements}:
                raise Fault('selected_membership_disagrees_or_outside_universe')
            identities.add(key); check(); out['replay_attempts'] += 1
            try:
                replay = nr.replay_native(case, plan)  # Original load/ops assertions and guards remain untouched.
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                replay_status[key] = False
                raise Fault('unchanged_replay_rejected', dict(error_type=type(exc).__name__, message=str(exc)))
            replay_status[key] = replay.get('replay_ok') is True
            if not replay_status[key]:
                raise Fault('unchanged_replay_did_not_admit')
            check()
            values[key] = replay_values(case, plan, replay, markets[group], nh, bases[group] != 10037)

        def stream_table(label, handler):
            name, pin = TABLES[label]; path = Path(name); before = path.stat()
            if before.st_size > 512*1024*1024:
                raise Fault('JSONL_file_exceeds512MiB')
            h = hashlib.sha256(); size = lines = discarded = 0
            with path.open('rb') as stream:
                while True:
                    check(); raw = stream.readline(16*1024*1024)
                    if not raw:
                        break
                    h.update(raw); size += len(raw); lines += 1
                    if size > 512*1024*1024 or len(raw) == 16*1024*1024 and not raw.endswith(b'\n') and size < before.st_size:
                        raise Fault('JSONL_byte_or_line_cap_exceeded')
                    try:
                        row = json.loads(raw)
                    except (ValueError, UnicodeError):
                        finding(label, lines, None, 'malformed_JSON_unroutable'); continue
                    if not isinstance(row, dict) or not isinstance(row.get('base_group'), str):
                        finding(label, lines, None, 'missing_top_level_routing_group'); row = None; continue
                    group = row['base_group']
                    if group not in fit:
                        discarded += 1; row = None; continue  # No other non-FIT field is consulted.
                    try:
                        handler(row, group, lines)
                    except Fault as exc:
                        finding(label, lines, group, exc.code, exc.details)
                    except (KeyError, TypeError, ValueError) as exc:
                        finding(label, lines, group, 'malformed_FIT_contract', dict(error_type=type(exc).__name__))
                    row = None
            actual = h.hexdigest(); out['input_sha256'][name] = actual
            out['file_streams'][label] = dict(bytes=size, lines=lines, nonFIT_routing_discarded=discarded, pin_matched=actual == pin)
            after = path.stat()
            if actual != pin or size != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise Fault('whole_JSONL_pin_or_stability_mismatch')

        stream_table('cases', case_row); stream_table('sources', source_row)
        paired = []
        for group in ordered_groups:
            check(); case = cases.get(group); one, two = values.get((group, 'source0')), values.get((group, 'source1'))
            row = dict(group=group, base_id=bases[group], membership_stratum=strata[group], expected_pair=bases[group] != 10037,
                case_row_present=group in case_seen, case_contract_valid=case is not None, expected_sources=sorted(expected[group]),
                sources_present=[s for s in SOURCES if (group, s) in source_seen],
                source_identities_admitted=[s for s in SOURCES if (group, s) in identities],
                replay_status={s: replay_status.get((group, s), 'missing') for s in SOURCES},
                witnesses={s: values.get((group, s)) for s in SOURCES},
                unadmitted_expected_sources=[s for s in sorted(expected[group]) if values.get((group, s)) is None],
                findings=[f['code'] for f in out['findings'] if f['FIT_group'] == group], coherence=None)
            if row['expected_pair'] and case is not None and one is not None and two is not None:
                row['coherence'] = coherence(one, two)
                paired.append(row)
            else:
                row['missing_comparison_reason'] = 'predeclared_source1_only_group' if not row['expected_pair'] else 'missing_or_invalid_case/source'
            out['groups'][group_positions[group]] = row
        out['aggregate'] = dict(intended_groups=80, expected_pairs=79, expected_witnesses=159,
            present_expected_witnesses=sum((g, s) in source_seen for g in fit for s in expected[g]),
            identity_admitted_expected_witnesses=sum((g, s) in identities for g in fit for s in expected[g]),
            replay_valid_expected_witnesses=sum(replay_status.get((g, s)) is True for g in fit for s in expected[g]),
            replay_rejected_expected_witnesses=sum(replay_status.get((g, s)) is False for g in fit for s in expected[g]),
            valid_witness_bookkeeping=sum(v is not None for v in values.values()), valid_pairs=len(paired),
            full=summarize([r for r in out['groups'] if r['expected_pair']], 79),
            strata={label: summarize([r for r in out['groups'] if r['membership_stratum'] == label], planned)
                for label, planned in (('different_membership', 48), ('same_membership', 31))},
            unit='equal FIT physical groups; no available-only promotion', reporting_tau_cost_units=TAU)
        out['catalog_report_complete'] = len(paired) == 79 and not out['findings'] and sum(v is not None for v in cases.values()) == 80 and sum(v is not None for v in values.values()) == 159
        out.update(audit_completed=True, checks_passed=out['catalog_report_complete'])
        check()
    except BaseException as exc:
        out['checks_passed'] = out['catalog_report_complete'] = False
        out['failures'].append(dict(type=type(exc).__name__, code=exc.code if isinstance(exc, Fault) else 'audit_exception'))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN); signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 600-(time.monotonic()-WALL0)))
        own = resource.getrusage(resource.RUSAGE_SELF)
        out.update(receipt_complete=True, resources=dict(user_s=own.ru_utime, system_s=own.ru_stime, peak_rss_bytes=rss(),
            elapsed_before_publication_s=time.monotonic()-WALL0, body_cpu_s=270, body_wall_s=540, total_cpu_s=300, total_wall_s=600,
            prior_displayed_cpu_s=19638.65, prior_retained_tracking_cpu_s=19638.69, prior_elapsed_sum_s=20224.73,
            legacy_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN', external_meter_required=True),
            access_scope='Whole mixed TRAIN bytes hashed; all rows transiently decoded for routing; semantic analysis only fixed FIT',
            semantic_identity_algorithm='default-spaced json.dumps(sort_keys=True,allow_nan=False), without numeric coercion',
            JSONL_stream_hashes_completed=len(out['file_streams']), raw_charge_load_or_ID_vectors_exported=False,
            cached_source_replay_inspected=False, generation_calls=0, replay_calls=out.get('replay_attempts', 0), solver_calls=0,
            valuation_policy='nh.rational(recomputed ops_cost)+nh.supply(validated market,recomputed load), no float total downcast',
            difference_sign_convention='D_t=F_t(P1)-F_t(P0); positive favors P0; ties include both tau endpoints',
            limitations=['Two existing fixed schedules are not a physical relaxation, fixed-route reoptimization or full-space optimum',
                'Own-context domination does not identify teacher-noise/budget/initialization as its cause',
                'Identical membership can conceal charging and cost differences',
                'No model readiness, information-value, significance or automatic training gate'])
        if rss() > 5*1024**3 or threading.active_count() != 1:
            out['checks_passed'] = out['catalog_report_complete'] = False
            out['failures'].append(dict(type='ResourceBound', code='final_observed_RSS_or_thread_bound'))
        temporary = target.with_name('receipt.final.tmp.json'); save_new(temporary, out); os.replace(temporary, target)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
