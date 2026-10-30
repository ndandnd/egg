"""Summarize the frozen four-arm density diagnostic; archive, never rerun it."""
import time

WALL0, CPU0 = time.monotonic(), time.process_time()

from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
ATTEMPT = BASE/'attempt01'
DECISIONS = ((1, 'scale:50685:40', 'CA1'), (2, 'scale:50685:40', 'CoverCA1'),
             (3, 'scale:50605:80', 'CoverCA1'), (4, 'scale:50605:80', 'CA1'))
TARGETS = {'scale:50685:40': 3, 'scale:50605:80': 5}


def check():
    if time.process_time()-CPU0 > 55 or time.monotonic()-WALL0 > 85:
        raise TimeoutError('Finalization body allowance exhausted; retain5s publication reserve')


def read_json(path):
    check()
    with path.open('rb') as stream:
        raw = stream.read(16*1024*1024+1)
    if len(raw) > 16*1024*1024:
        raise ValueError('Compact input exceeds16MiB: '+str(path))
    return json.loads(raw)


def selection_counts(folder):
    selection = read_json(folder/'selection.json')
    sets = {name: set() for name in ('declared', 'flexible', 'boundary', 'selected', 'backbone', 'cover', 'fill')}
    counts = {name: Counter() for name in ('declared', 'selected', 'backbone', 'cover', 'fill')}
    errors, mode_rows = [], 0
    with (folder/'mode-ledger.jsonl').open('rb') as stream:
        while True:
            check()
            line = stream.readline(1024*1024+1)
            if not line:
                break
            if len(line) > 1024*1024:
                raise ValueError('Mode-ledger line exceeds1MiB')
            mode = json.loads(line)
            mid, kind = mode['movement'], mode['kind']
            if mid in sets['declared']:
                raise ValueError('Duplicate movement in mode ledger')
            mode_rows += 1
            sets['declared'].add(mid)
            counts['declared'][kind] += 1
            flexible = kind in ('direct', 'depot')
            if flexible:
                sets['flexible'].add(mid)
            for flag in ('boundary', 'selected', 'backbone', 'cover', 'fill'):
                if type(mode[flag]) is not bool:
                    raise ValueError('Nonboolean mode-ledger flag')
                if mode[flag]:
                    sets[flag].add(mid)
                    if flag in counts:
                        counts[flag][kind] += 1
            if mode['boundary'] == flexible:
                errors.append('boundary/flexible partition differs for '+str(mid))
    selected_flexible = sets['selected'] & sets['flexible']
    ordinary = set(selection['ordinary_CA1_flexible_ids'])
    protected = sets['backbone'] | sets['cover']
    comparisons = {
        'M': selection['M'] == len(sets['flexible']),
        'declared_movements': selection['declared_movements'] == mode_rows,
        'retained_movements': selection['retained_movements'] == len(sets['selected']),
        'backbone_count': selection['backbone_count'] == len(sets['backbone']),
        'cover_flexible_count': selection['cover_flexible_count'] == len(sets['cover']),
        'protected_count': selection['protected_count'] == len(protected),
        'fill_count': selection['fill_count'] == len(sets['fill']),
        'mode_counts': selection['mode_counts'] == {name: dict(value) for name, value in counts.items()},
        'backbone_cover_overlap': selection['backbone_cover_overlap'] == len(sets['backbone'] & sets['cover']),
        'ordinary_CA1_count': len(ordinary) == selection['K'] and ordinary <= sets['flexible'],
        'protected_is_flexible': protected <= sets['flexible'],
    }
    for field, expected in (('backbone_ids', sets['backbone']), ('boundary_ids', sets['boundary']),
            ('cover_flexible_ids', sets['cover']), ('protected_flexible_ids', protected),
            ('fill_order', sets['fill']), ('selected_flexible_ids', selected_flexible),
            ('retained_movement_ids', sets['selected'])):
        values = selection[field]
        comparisons[field] = len(values) == len(set(values)) and set(values) == expected
    overlap = {'intersection': len(ordinary & selected_flexible),
        'only_ordinary': len(ordinary-selected_flexible), 'only_arm': len(selected_flexible-ordinary),
        'union': len(ordinary | selected_flexible)}
    comparisons['ordinary_CA1_overlap'] = selection['ordinary_CA1_overlap'] == overlap
    comparisons['flexible_order'] = (len(selection['flexible_order']) == len(sets['flexible'])
        and set(selection['flexible_order']) == sets['flexible'])
    selected_ok = (len(selected_flexible) == selection['K'] and protected <= selected_flexible
        and sets['boundary'] <= sets['selected'] and sets['selected'] <= sets['declared'])
    comparisons['dispatch_or_preserved_design_failure'] = (
        selected_ok if selection['status'] == 'selected' else
        selection['status'] == 'design_failure_cover_union_exceeds_K'
        and len(protected) > selection['K'] and not sets['selected'])
    comparisons['unchanged_CA1'] = (selection['arm'] != 'CA1'
        or selected_flexible == ordinary and not sets['cover'])
    summary = {key: selection[key] for key in ('policy', 'arm', 'status', 'M', 'K', 'declared_movements',
        'retained_movements', 'backbone_count', 'cover_flexible_count', 'protected_count', 'fill_count',
        'ordinary_CA1_overlap', 'backbone_cover_overlap', 'mode_counts')}
    summary.update(actual_mode_rows=mode_rows, actual_selected_flexible=len(selected_flexible),
        actual_boundary_count=len(sets['boundary']), exact_K_selected=selected_ok,
        count_comparisons=comparisons, ledger_errors=errors,
        count_comparison_passed=all(comparisons.values()) and not errors)
    return summary, sets, selection


def archive_once(source, output):
    """One original stream feeds both SHA256 and gzip; originals remain untouched."""
    check()
    archive = source.with_name(source.name+'.gz')
    entry = dict(source=str(source.relative_to(BASE)), archive=str(archive.relative_to(BASE)),
        archive_complete=False, source_sha256=None)
    output.append(entry)
    digest, size, newlines = hashlib.sha256(), 0, 0
    before = source.stat()
    try:
        with source.open('rb') as src, archive.open('xb') as dest:
            with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=6) as packed:
                while True:
                    check()
                    chunk = src.read(1024*1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                    newlines += chunk.count(b'\n')
                    packed.write(chunk)
            dest.flush()
            os.fsync(dest.fileno())
        after = source.stat()
        stable = (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
        if not stable or size != before.st_size:
            raise ValueError('Original changed or streamed byte count differs')
        entry.update(archive_complete=True, source_sha256=digest.hexdigest(), source_bytes=size,
            source_newline_count=newlines, original_stat_bytes=before.st_size,
            source_byte_count_matches_stat=True, archive_bytes=archive.stat().st_size)
    except BaseException as exc:
        entry.update(failure={'type': type(exc).__name__, 'message': str(exc)},
            streamed_prefix_bytes=size, streamed_prefix_sha256=digest.hexdigest(),
            original_stat_bytes=before.st_size,
            partial_archive_bytes=archive.stat().st_size if archive.exists() else None)
        raise


def main():
    if (BASE/'summary.json').exists():
        raise FileExistsError('Exclusive summary already exists')
    def expired(signum, frame):
        raise TimeoutError('Finalization resource allowance reached; preserve partial summary')
    resource.setrlimit(resource.RLIMIT_CPU, (55, 60))
    signal.signal(signal.SIGXCPU, expired)
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 85-(time.monotonic()-WALL0)))
    out = {'finalization_complete': False, 'cases': [], 'archives': [], 'cross_arm_comparisons': [],
        'failures': [], 'scope': 'four-arm exposed-case density diagnostic; no numerical or replay rerun'}
    master, selections = {}, {}
    try:
        master = read_json(ATTEMPT/'receipt.json')
        out.update(diagnostic_complete=master.get('complete'), diagnostic_passed=master.get('passed'),
            diagnostic_failure=master.get('failure'), diagnostic_scope=master.get('scope'),
            native_process_receipt={key: master.get(key) for key in
                ('cpu_s', 'wall_s', 'observed_peak_rss_bytes', 'rusage', 'budget', 'stop_signal')})
        entries = master.get('cases', [])
        expected_keys = set(DECISIONS)
        out['unexpected_master_entries'] = [entry for entry in entries
            if (entry.get('ordinal'), entry.get('case'), entry.get('arm')) not in expected_keys]
        for ordinal, case, arm in DECISIONS:
            check()
            folder = ATTEMPT/('%02d-' % ordinal+case.replace(':', '-')+'-'+arm)
            matching = [entry for entry in entries if (entry.get('ordinal'), entry.get('case'), entry.get('arm'))
                == (ordinal, case, arm)]
            result = dict(ordinal=ordinal, case=case, arm=arm, recorded_in_master=len(matching) == 1,
                competence_target=TARGETS[case], competence_passed=False, failures=[])
            out['cases'].append(result)
            try:
                if len(matching) != 1:
                    raise ValueError('Missing or duplicate frozen master decision')
                result.update(matching[0])
                receipt_path = folder/'receipt.json'
                if result['receipt'] != str(receipt_path.relative_to(ROOT)):
                    raise ValueError('Master receipt path differs from fixed ordinal folder')
                receipt = read_json(receipt_path)
                native = receipt.get('native', {})
                result.update(case_receipt_complete=receipt.get('complete'),
                    native_status=native.get('status'), restricted_fleet_lower_bound=native.get('lower_bound'),
                    native_fleet_incumbent=native.get('incumbent'), native_solve_wall_s=native.get('wall_s'),
                    native_threads=native.get('threads'), failures=receipt.get('failures', []),
                    stages=receipt.get('stages'), case_observed_peak_rss_bytes=receipt.get('observed_peak_rss_bytes'),
                    native_seed_requested=receipt.get('native_seed_requested'),
                    independent_replay_stages=[stage for stage in receipt.get('stages', [])
                        if stage.get('stage') == 'independent_replay'])
                comparisons = {key: result.get(key) == receipt.get(key) for key in
                    ('ordinal', 'case', 'arm', 'status', 'physical_witness_valid', 'vehicles',
                     'integrated_cost_exact', 'pool', 'native_seed_readback')}
                elapsed = result.get('elapsed_including_receipt_s')
                timely = isinstance(elapsed, (float, int)) and elapsed <= 120
                comparisons['timely_admission'] = result.get('accepted_within_offline120') == (
                    receipt.get('physical_witness_valid') is True and timely)
                comparisons['declared_matrix'] = result.get('declared_matrix') == receipt.get('inventory')
                result['receipt_comparisons'] = comparisons
                result['receipt_comparison_passed'] = all(comparisons.values())
                result['timely_completion'] = timely
                result['cost_float'] = (float(Fraction(result['integrated_cost_exact']))
                    if result.get('integrated_cost_exact') is not None else None)
                vehicles = result.get('vehicles')
                result['competence_passed'] = bool(result.get('accepted_within_offline120') is True
                    and receipt.get('physical_witness_valid') is True and type(vehicles) is int
                    and vehicles <= TARGETS[case] and result.get('native_seed_readback') == 17
                    and result['receipt_comparison_passed'])
                if (folder/'selection.json').exists():
                    counts, sets, selection = selection_counts(folder)
                    result['selection'] = counts
                    pool = result.get('pool')
                    pool_keys = ('policy', 'status', 'M', 'K', 'declared_movements', 'retained_movements',
                        'backbone_count', 'cover_flexible_count', 'protected_count', 'fill_count',
                        'ordinary_CA1_overlap', 'backbone_cover_overlap', 'mode_counts')
                    result['pool_equals_selection_summary'] = pool == {key: selection[key] for key in pool_keys}
                    result['selection_identity_matches_receipt'] = (selection['arm'] == arm
                        and selection['case_identity'] == receipt.get('case_identity'))
                    selections[(case, arm)] = (sets, selection)
                else:
                    result['selection_unavailable'] = True
            except TimeoutError:
                raise
            except Exception as exc:
                result['finalization_failure'] = {'type': type(exc).__name__, 'message': str(exc)}
        for case in TARGETS:
            check()
            left, right = selections.get((case, 'CA1')), selections.get((case, 'CoverCA1'))
            comparison = dict(case=case, available=left is not None and right is not None)
            if left is not None and right is not None:
                ls, lp = left
                rs, rp = right
                lf, rf = ls['selected'] & ls['flexible'], rs['selected'] & rs['flexible']
                common = dict(M=lp['M'] == rp['M'], K=lp['K'] == rp['K'],
                    backbone=ls['backbone'] == rs['backbone'], boundary=ls['boundary'] == rs['boundary'],
                    declared_modes=ls['declared'] == rs['declared'], case_identity=lp['case_identity'] == rp['case_identity'])
                comparison.update(common_contract=common, common_contract_passed=all(common.values()),
                    CA1_K=lp['K'], CoverCA1_K=rp['K'], B_count=len(ls['backbone']),
                    flexible_intersection=len(lf & rf), flexible_union=len(lf | rf),
                    only_CA1=len(lf-rf), only_CoverCA1=len(rf-lf),
                    retained_intersection=len(ls['selected'] & rs['selected']))
            out['cross_arm_comparisons'].append(comparison)
        for ordinal, case, arm in DECISIONS:
            folder = ATTEMPT/('%02d-' % ordinal+case.replace(':', '-')+'-'+arm)
            for name in ('physical-inventory.jsonl', 'native-capture.json'):
                source = folder/name
                if source.exists():
                    archive_once(source, out['archives'])
        out['finalization_complete'] = True
    except BaseException as exc:
        out['failures'].append({'type': type(exc).__name__, 'message': str(exc)})
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 90-(time.monotonic()-WALL0)))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        external = BASE/'process-time.txt'
        out.update(competence_passed=len(out['cases']) == 4 and all(row['competence_passed'] for row in out['cases']),
            finalization_passed=out['finalization_complete'] and not out['failures']
                and not out.get('unexpected_master_entries')
                and all(not row.get('finalization_failure') and row.get('receipt_comparison_passed')
                    and row.get('selection', {}).get('count_comparison_passed')
                    and row.get('pool_equals_selection_summary')
                    and row.get('selection_identity_matches_receipt') for row in out['cases'])
                and all(row.get('common_contract_passed') for row in out['cross_arm_comparisons']),
            postprocess_cpu_s=time.process_time()-CPU0, postprocess_wall_s=time.monotonic()-WALL0,
            postprocess_rusage={'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                'maxrss_platform_units': usage.ru_maxrss, 'platform': sys.platform},
            measured_native_process_time=external.read_text() if external.exists() else None,
            prior_reset_measured_cpu_s=160.91, prior_reset_measured_cpu_decimal='160.91',
            prior_reset_measured_elapsed_sum_s=175.97, prior_reset_measured_elapsed_decimal='175.97',
            legacy_conditional_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN',
            legacy_reset=False, whole_session_exact_cpu_claim=False,
            budget={'cpu_s': 60, 'wall_s': 90, 'cpu_soft_s': 55, 'body_cpu_s': 55,
                'body_wall_s': 85, 'publication_reserve_s': 5},
            timing_scope='through summary preparation; parent process meter includes encoding/write/exit',
            archive_policy='one original stream into SHA256+lossless gzip; originals retained/ignored; no second hash audit',
            interpretation='restricted fleet bounds only; exposed cases; competence is not ML superiority or generalization')
        with (BASE/'summary.json').open('x') as stream:
            json.dump(out, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({'finalization_complete': out['finalization_complete'],
        'finalization_passed': out['finalization_passed'], 'competence_passed': out['competence_passed'],
        'cases': [{key: row.get(key) for key in ('ordinal', 'case', 'arm', 'status', 'vehicles',
            'native_status', 'restricted_fleet_lower_bound', 'competence_passed')} for row in out['cases']]}))
    return 0 if out['finalization_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
