"""One bounded metadata-only read; literal projections, no referenced-file access."""
import time
WALL0 = time.monotonic()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading

SOURCE = '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/train_readiness/audit_metadata.py'
IDENTITY_FILES = (SOURCE,
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/train_readiness/PROTOCOL.md',
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/train_readiness/LAUNCH.json')
WHITELIST = {
    '/Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/fit_only_preprocessing_and_groups.json': {
        'kind': 'GNN_preprocessing', 'values': ('features', 'fit_groups', 'inner_groups', 'outer_groups'),
        'structure_only': ('mean_fit_only', 'scale_fit_only', 'pool_manifest_sha256', 'seed')},
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261017/classical-training/attempt1/catboost/preprocessing.json': {
        'kind': 'CatBoost_preprocessing', 'values': ('features', 'fit_groups', 'inner_groups', 'outer_groups', 'pool_manifest_sha256'),
        'structure_only': ('mean_fit_only', 'scale_fit_only')},
    '/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261017/classical-training/attempt1/catboost/metadata.json': {
        'kind': 'CatBoost_metadata', 'values': ('arm', 'seed', 'qualification', 'features', 'model_sha256'),
        'selection': ('candidate_index', 'config'), 'digest_maps': ('training_source_hashes', 'pool_table_hashes')},
    '/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/pool_manifest.json': {
        'kind': 'TRAIN_manifest', 'values': ('policy', 'train_only', 'base_ids', 'independent_groups_intended',
            'groups_eligible_observed', 'groups_eligible_full_pair', 'source_fleets_intended',
            'source_fleets_observed', 'feature_policy', 'target_outcomes_not_exported'),
        'digest_maps': ('output_hashes', 'adapter_source_hashes'),
        'FIT_entry_values': ('base_id', 'base_group', 'intended_source_count', 'observed_source_count',
            'observed_sources', 'missing_source_labels', 'eligible_for_observed_source_supervision',
            'eligible_for_full_pair_supervision'),
        'shard_values': ('shard', 'dataset'), 'shard_digests': ('dataset_receipt_sha256',
            'case_table_sha256', 'source_table_sha256', 'health_sha256_from_receipt')},
}
EXPECTED_SHA256 = {
    'GNN_preprocessing': 'f4a5145f9b89ca487f52905d2cda153dd6bc1d1a930d441b577ec9357eae8095',
    'CatBoost_preprocessing': '5c0ac1277ab68024ddc58ad468cf35d2fca18959906ae739bd946b21512f1ea6',
    'CatBoost_metadata': '9f1fef8b98993e461d58d4ddb3e6bc061ac692159c922171ac0f09de8cc62c73',
}
TARIFF_FEATURE_NAMES = ('window_price_mean', 'window_price_min', 'market_mean', 'market_spread')
MAX_FILE, MAX_TOTAL = 8*1024*1024, 32*1024*1024


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def check():
    if time.process_time() >= 45 or time.monotonic()-WALL0 >= 60:
        raise TimeoutError('Metadata body provision exhausted')
    if threading.active_count() != 1 or rss_bytes() > 5*1024**3:
        raise RuntimeError('One-thread/final-observed RSS5GiB bound failed')


def save_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def structure(obj, key):
    if key not in obj:
        return dict(present=False, type='missing')
    value = obj[key]
    result = dict(present=True, type=type(value).__name__)
    if isinstance(value, (list, dict, str)):
        result['length'] = len(value)
    return result


def scalar(value):
    return value is None or type(value) in (str, bool, int) or type(value) is float and math.isfinite(value)


def flat(value):
    return scalar(value) or isinstance(value, list) and all(scalar(item) for item in value)


def project(obj, keys, unknowns, context):
    result = {}
    for key in keys:
        if key not in obj:
            result[key] = dict(present=False, status='unknown_not_supplied')
        elif flat(obj[key]):
            result[key] = dict(present=True, value=obj[key])
        else:
            result[key] = dict(present=True, type=type(obj[key]).__name__, status='unknown_unapproved_value_shape')
            unknowns.append(dict(context=context, key=key, reason='Nested values are not projected'))
    return result


def digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdefABCDEF' for c in value)


def digest_map(obj, key, unknowns, context):
    if key not in obj:
        return dict(present=False, status='unknown_not_supplied')
    value = obj[key]
    if not isinstance(value, dict):
        unknowns.append(dict(context=context, key=key, reason='Expected path/name to digest mapping'))
        return dict(present=True, type=type(value).__name__, status='unknown_unapproved_value_shape')
    valid = {name: pin for name, pin in value.items() if isinstance(name, str) and digest(pin)}
    invalid = [name for name, pin in value.items() if not isinstance(name, str) or not digest(pin)]
    return dict(present=True, declared_digests=valid, invalid_entry_key_names=invalid, referenced_files_verified=False)


def main():
    def expired(signum, frame):
        raise TimeoutError('Metadata audit body allowance exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (45, 60))
    signal.signal(signal.SIGXCPU, expired); signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 60-(time.monotonic()-WALL0)))
    base = Path(SOURCE).parent
    if Path(__file__).resolve() != Path(SOURCE):
        raise ValueError('Execute only the frozen literal audit source')
    attempt = base/'attempt01'
    attempt.mkdir(exist_ok=False)
    target = attempt/'receipt.json'
    save_new(target, dict(receipt_complete=False, audit_completed=False, failure='No completed metadata audit'))
    out = dict(receipt_complete=False, audit_completed=False, checks_passed=False, failures=[], unknowns=[],
        input_sha256={}, input_bytes={}, files={}, whitelist=WHITELIST, readiness_qualified=False)
    try:
        paths = IDENTITY_FILES+tuple(WHITELIST)
        stats = {name: Path(name).stat() for name in paths}
        if len(paths) != len(set(paths)) or any(s.st_size > MAX_FILE for s in stats.values()) or sum(s.st_size for s in stats.values()) > MAX_TOTAL:
            raise ValueError('Exact input batch violates uniqueness/8MiB per-file/32MiB total bound')
        buffers = {}
        for name in paths:
            check()
            before = stats[name]
            with Path(name).open('rb') as stream:
                raw = stream.read(before.st_size)  # One bounded read; no path from metadata is ever followed.
            out['input_sha256'][name] = hashlib.sha256(raw).hexdigest()
            out['input_bytes'][name] = len(raw)
            after = Path(name).stat()
            if len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError('Frozen input changed during its single read: '+name)
            if name in WHITELIST:
                buffers[name] = raw
                expected = EXPECTED_SHA256.get(WHITELIST[name]['kind'])
                if expected is not None and out['input_sha256'][name] != expected:
                    raise ValueError('Selected metadata identity mismatch: '+name)
        documents = {}
        for name, rule in WHITELIST.items():
            check()
            obj = json.loads(buffers[name])
            if not isinstance(obj, dict):
                raise ValueError('Exact metadata root is not a mapping: '+name)
            kind = rule['kind']; documents[kind] = obj
            result = dict(top_level_keys_and_types={key: type(value).__name__ for key, value in obj.items()},
                selected=project(obj, rule['values'], out['unknowns'], kind),
                structure_only={key: structure(obj, key) for key in rule.get('structure_only', ())})
            for key in rule.get('digest_maps', ()):
                result['selected'][key] = digest_map(obj, key, out['unknowns'], kind)
            if kind == 'CatBoost_metadata':
                selection = obj.get('selection')
                result['selection_key_names_and_types'] = {k: type(v).__name__ for k, v in selection.items()} if isinstance(selection, dict) else None
                if isinstance(selection, dict):
                    result['selected']['selection'] = project(selection, ('candidate_index',), out['unknowns'], kind+'.selection')
                    config = selection.get('config')
                    result['selected']['selection']['config'] = dict(present='config' in selection,
                        value=config if isinstance(config, dict) and all(scalar(v) for v in config.values()) else None,
                        status='declared_flat_configuration' if isinstance(config, dict) and all(scalar(v) for v in config.values()) else 'unknown_not_supplied_or_nested')
            out['files'][kind] = result
        train = documents['TRAIN_manifest']; registry = train.get('group_eligibility')
        registry_name = next(name for name, rule in WHITELIST.items() if rule['kind'] == 'TRAIN_manifest')
        if out['input_sha256'][registry_name] != documents['CatBoost_preprocessing'].get('pool_manifest_sha256'):
            raise ValueError('Registry digest differs from selected CatBoost preprocessing pool pin')
        if train.get('train_only') is not True:
            raise ValueError('Bounded registry must explicitly declare train_only=true')
        if not isinstance(registry, list):
            raise ValueError('Registry group_eligibility is not the source-declared list')
        out['files']['TRAIN_manifest']['group_eligibility_item_key_names'] = sorted({key for row in registry if isinstance(row, dict) for key in row})
        fit_sets = {}
        for model in ('GNN', 'CatBoost'):
            values = documents[model+'_preprocessing'].get('fit_groups')
            fit_sets[model] = set(values) if isinstance(values, list) and all(isinstance(g, str) for g in values) else None
        if any(groups is None for groups in fit_sets.values()):
            raise ValueError('Declared FIT identifiers missing/unclear; no eligibility-value projection')
        fit_union = set().union(*fit_sets.values()); joined, ambiguous = {}, set()
        for row in registry:
            check()
            if not isinstance(row, dict):
                continue
            group = row.get('base_group')
            if group not in fit_union:
                continue  # No inner/outer eligibility values are accessed.
            if group in joined:
                ambiguous.add(group)
            joined[group] = row
        fit_rule = WHITELIST[registry_name]['FIT_entry_values']
        out['FIT_group_provenance'] = [project(joined[group], fit_rule, out['unknowns'], 'FIT.'+group)
            for group in sorted(fit_union & joined.keys()-ambiguous)]
        out['FIT_coverage'] = {model: dict(declared_unique_FIT_groups=len(groups),
            mapped_groups=len(groups & joined.keys()-ambiguous), missing_group_IDs=sorted(groups-joined.keys()),
            ambiguous_group_IDs=sorted(groups & ambiguous)) for model, groups in fit_sets.items()}
        out['FIT_source_availability'] = {}
        for model, groups in fit_sets.items():
            rows = {group: joined[group] for group in groups & joined.keys()-ambiguous}
            known_pairs = {group: row['eligible_for_full_pair_supervision'] for group, row in rows.items()
                if type(row.get('eligible_for_full_pair_supervision')) is bool}
            known_counts = {group: row['observed_source_count'] for group, row in rows.items()
                if type(row.get('observed_source_count')) is int and row['observed_source_count'] >= 0}
            out['FIT_source_availability'][model] = dict(planned_FIT_groups=len(groups),
                mapped_groups=len(rows), known_pair_flag_groups=len(known_pairs),
                declared_full_pair_eligible_groups=sum(value is True for value in known_pairs.values()),
                declared_incomplete_pair_group_IDs=sorted(group for group, value in known_pairs.items() if value is False),
                unknown_pair_flag_group_IDs=sorted(groups-known_pairs.keys()),
                known_observed_source_count_groups=len(known_counts),
                declared_observed_source_fleets_sum=sum(known_counts.values()) if len(known_counts) == len(groups) else None,
                interpretation='Declared FIT metadata availability, not verified tariffs, label differences or teacher quality')
        shards = train.get('admitted_shards')
        out['declared_shard_provenance'] = []
        if isinstance(shards, list):
            for row in shards:
                check()
                if not isinstance(row, dict):
                    continue
                item = project(row, WHITELIST[registry_name]['shard_values'], out['unknowns'], 'admitted_shards')
                item.update({key: row[key] if digest(row.get(key)) else None for key in WHITELIST[registry_name]['shard_digests']})
                out['declared_shard_provenance'].append(item)
        else:
            out['unknowns'].append(dict(context='TRAIN_manifest', key='admitted_shards', reason='Not supplied as a list'))
        out['readiness_limits'] = dict(GNN_training_pool_identity='unknown; preprocessing pin is not a TRAIN-pool lineage pin',
            actual_within_case_prices='unknown; source labels/availability do not verify numeric tariffs',
            conditional_binary_target_variation='unknown; no labels read', teacher_quality='unknown; no outcomes read',
            candidate_bank_and_search_provenance='declared digests only; referenced files not verified',
            alias_closure='unknown; no cross-generator crosswalk', matched_blind_training='not established by metadata')
        out.update(audit_completed=True, checks_passed=True)
        check()
    except BaseException as exc:
        out['checks_passed'] = False
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN); signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 90-(time.monotonic()-WALL0)))
        own = resource.getrusage(resource.RUSAGE_SELF)
        out.update(receipt_complete=True, resources=dict(user_s=own.ru_utime, system_s=own.ru_stime,
            elapsed_before_publication_s=time.monotonic()-WALL0, peak_rss_bytes=rss_bytes(), python_threads=threading.active_count(),
            body_cpu_s=45, body_wall_s=60, total_cpu_s=60, total_wall_s=90, max_rss_bytes=5*1024**3,
            prior_closed_cpu_s=19638.10, prior_closed_elapsed_sum_s=20223.65,
            legacy_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN', external_meter_needed_for_complete_cost=True),
            metadata_files_read=len([name for name in WHITELIST if name in out['input_sha256']]),
            hash_calls=len(out['input_sha256']), referenced_paths_followed=0, weight_reads=0, row_table_reads=0,
            subprocesses=0, solver_calls=0, inference_calls=0, normalization_values_exported=False)
        if rss_bytes() > 5*1024**3:
            out['checks_passed'] = False
            out['failures'].append(dict(type='ResourceBound', message='Final observed peak RSS exceeds5GiB'))
        temporary = target.with_name('receipt.final.tmp.json')
        save_new(temporary, out); os.replace(temporary, target)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
