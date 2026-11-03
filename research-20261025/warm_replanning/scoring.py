"""Thin, fresh-score adapters; no fitting, saved plans, solver or replay calls."""
import hashlib
import importlib.util
import math
from pathlib import Path
import time

POLICY = 'warm-replanning-fixed-model-prior-protected-Bw-exact-K-v2'
ARMS = ('GNN', 'CatBoost', 'CA1', 'CoverCA1', 'random', 'full')
RANDOM_SALT = 'warm-replanning-priceblind-random-v1'
GNN_ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/claude-local/v8')
GNN_ASSET_SHA256 = {
    'task00/inner_progress/graph_attention_selected.npz':
        '2ce500d711540284e62f0f365475892aa318d79601b5f74b5f10a7caed749f6d',
    'task00/inner_progress/fit_only_preprocessing_and_groups.json':
        'f4a5145f9b89ca487f52905d2cda153dd6bc1d1a930d441b577ec9357eae8095',
}
CATBOOST_ASSET_SHA256 = {
    'catboost/model.cbm': '1b3d6e00149aa4f712d84b8ba0e859496b295f9f266c593cf62164f92bbac237',
    'catboost/metadata.json': '9f1fef8b98993e461d58d4ddb3e6bc061ac692159c922171ac0f09de8cc62c73',
    'catboost/preprocessing.json': '5c0ac1277ab68024ddc58ad468cf35d2fca18959906ae739bd946b21512f1ea6',
}


def expected_assets(asset_lock, root):
    """Check recorded expectations only; caller verifies file bytes once in-run."""
    root = Path(root).resolve()
    classical = root/'research-20261017/classical-training/attempt1'
    if (Path(asset_lock['v8_root']).resolve() != GNN_ROOT
            or Path(asset_lock['classical_root']).resolve() != classical):
        raise ValueError('Locked selected-model roots differ')
    expected = {str(GNN_ROOT/name): digest for name, digest in GNN_ASSET_SHA256.items()}
    expected.update({str(classical/name): digest for name, digest in CATBOOST_ASSET_SHA256.items()})
    if any(asset_lock.get('assets', {}).get(path) != digest for path, digest in expected.items()):
        raise ValueError('Recorded selected-model asset digest differs')
    return expected


def _research_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load frozen research selector: '+str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def select(case, a, b, arm, *, root, asset_lock, case_key, random_seed,
           common_prior_ids=None, verified_asset_sha256=None, check=lambda: None):
    """Return an original-order movement mask and paid scoring/selection ledger.

    The caller starts its decision clock before calling and validates byte hashes
    in its metered preflight. No loaded model, old score or selected plan is reused.
    Model library imports can be process-cached; model objects/preprocessors reload.
    """
    wall0, cpu0 = time.monotonic(), time.process_time()
    check()
    if arm not in ARMS or not isinstance(case_key, str) or not case_key:
        raise ValueError('Unknown scoring arm or missing prospective case key')
    if type(random_seed) is not int or random_seed < 0:
        raise ValueError('Require a prospectively frozen nonnegative integer random seed')
    from egglab import classical_controls as cc
    root = Path(root).resolve()
    ids = [movement.id for movement in case.movements]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Require unique nonempty original movement order')
    flexible = {m.id for m in case.movements if m.kind in ('direct', 'depot')}
    boundaries = set(ids)-flexible
    if arm != 'full' and common_prior_ids is None:
        raise ValueError('Restricted arms require explicit common prior IDs; acquisition uses []')
    prior = set() if common_prior_ids is None else set(common_prior_ids)
    if not prior <= set(ids):
        raise ValueError('Common prior contains movements outside original universe')
    prior_flexible = prior & flexible
    scores, model_metadata, timings, assets = None, None, {}, {}
    score_ledger, cover_ledger, ordinary = None, None, None
    check()
    if arm == 'full':
        from egglab.native_recharge import validate_case
        validate_case(case)
        selection = {'policy': 'unrestricted-original-movement-universe',
            'case_identity': case.identity(), 'M': len(flexible), 'K': None,
            'base_backbone_ids': None, 'warm_backbone_ids': None, 'backbone_ids': None,
            'prior_protected_flexible_ids': [mid for mid in ids if mid in prior_flexible],
            'protected_flexible_ids': None, 'cover_flexible_ids': [], 'rank_fill_ids': [],
            'status': 'selected', 'retained_movement_ids': list(ids),
            'common_prior_representable': True}
    elif arm in ('CA1', 'CoverCA1'):
        # Same frozen scores/covers as density_control; warm protection is new.
        at, acpu = time.monotonic(), time.process_time()
        score_ledger = cc.ca1_score(case, a, b)
        scores = score_ledger['scores']
        if arm == 'CoverCA1':
            cover = _research_module(root/'research-20261025/matching_pool/pool.py',
                'warm_replanning_frozen_cover_pool').candidate_pool
            cover_ledger = cover(case, check=check)
            if cover_ledger['case_identity'] != case.identity():
                raise ValueError('Fresh cover case identity differs')
        timings['fresh_CA1_and_cover_wall_s'] = time.monotonic()-at
        timings['fresh_CA1_and_cover_cpu_s'] = time.process_time()-acpu
    else:
        at, acpu = time.monotonic(), time.process_time()
        if arm in ('GNN', 'CatBoost'):
            all_assets = expected_assets(asset_lock, root)
            prefix = str(GNN_ROOT)+'/' if arm == 'GNN' else str(root/'research-20261017/classical-training/attempt1')+'/'
            assets = {path: digest for path, digest in all_assets.items() if path.startswith(prefix)}
            if (not isinstance(verified_asset_sha256, dict)
                    or any(verified_asset_sha256.get(path) != digest for path, digest in assets.items())):
                raise ValueError('Caller has not supplied matching in-run selected-asset byte verification')
            check()
            if arm == 'GNN':
                from experiments.codex_local_campaign import v8_scores
                scores = v8_scores(case, a, asset_lock['v8_root'])
                timings['cold_model_features_graph_inference_wall_s'] = time.monotonic()-at
                timings['cold_model_features_graph_inference_cpu_s'] = time.process_time()-acpu
            else:
                from experiments.codex_train_classical import score_case
                scored = score_case(case, a, asset_lock['classical_root'], 'catboost')
                if scored['movement_ids'] != ids or scored['case_identity'] != case.identity():
                    raise ValueError('CatBoost original movement/case alignment differs')
                scores = scored['logits']
                model_metadata = scored['model_metadata']
                timings.update({key: scored[key] for key in
                    ('score_seconds', 'cold_load_seconds', 'inference_seconds')})
                timings['cold_adapter_score_wall_s'] = time.monotonic()-at
                timings['cold_adapter_score_cpu_s'] = time.process_time()-acpu
        else:
            order = sorted(range(len(ids)), key=lambda i: (hashlib.sha256(
                f'{RANDOM_SALT}|{case_key}|{random_seed}|{ids[i]}'.encode()).hexdigest(), ids[i]))
            scores = [0]*len(ids)
            for rank, index in enumerate(order):
                check()
                scores[index] = -rank
            timings['fresh_random_scores_wall_s'] = time.monotonic()-at
            timings['fresh_random_scores_cpu_s'] = time.process_time()-acpu
    if arm != 'full':
        check()
        if len(scores) != len(ids) or not all(math.isfinite(float(value)) for value in scores):
            raise ValueError('Scoring API returned nonfinite or misaligned scores')
        at, acpu = time.monotonic(), time.process_time()
        ordinary = cc.select_connections(case, scores)
        base_backbone = set(ordinary['backbone_ids'])
        warm_backbone = base_backbone | prior_flexible
        cover_flexible = set() if cover_ledger is None else set(cover_ledger['retained_movement_ids']) & flexible
        protected = warm_backbone | cover_flexible
        quota = ordinary['K']
        if len(warm_backbone) > quota:
            status = 'design_failure_warm_backbone_exceeds_K'
        elif len(protected) > quota:
            status = 'design_failure_cover_union_exceeds_K'
        else:
            status = 'selected'
        fill = [mid for mid in ordinary['flexible_order'] if mid not in protected]
        fill = fill[:quota-len(protected)] if status == 'selected' else []
        selected_flexible = protected | set(fill) if status == 'selected' else set()
        retained = boundaries | selected_flexible if status == 'selected' else set()
        selection = {'policy': POLICY, 'case_identity': case.identity(), 'M': ordinary['M'], 'K': quota,
            'base_backbone_ids': ordinary['backbone_ids'],
            'warm_backbone_ids': [mid for mid in ids if mid in warm_backbone],
            'backbone_ids': [mid for mid in ids if mid in warm_backbone],
            'prior_protected_flexible_ids': [mid for mid in ids if mid in prior_flexible],
            'protected_flexible_ids': [mid for mid in ids if mid in protected],
            'cover_flexible_ids': [mid for mid in ids if mid in cover_flexible],
            'rank_fill_ids': fill, 'status': status,
            'retained_movement_ids': [mid for mid in ids if mid in retained],
            'common_prior_representable': prior <= retained,
            'ordinary_selector_ledger': ordinary}
        timings['common_warm_selection_wall_s'] = time.monotonic()-at
        timings['common_warm_selection_cpu_s'] = time.process_time()-acpu
    check()
    selected = set(selection['retained_movement_ids'])
    if len(selected) != len(selection['retained_movement_ids']) or not selected <= set(ids):
        raise ValueError('Selected IDs are duplicated or outside original universe')
    selection_ok = selection['status'] == 'selected'
    if selection_ok:
        if not boundaries <= selected:
            raise ValueError('Selection omitted original boundary modes')
        if arm != 'full' and (len(selected & flexible) != selection['K']
                or not set(selection['warm_backbone_ids']) <= selected or not prior <= selected):
            raise ValueError('Common prior-protected Bw/exact K invariant differs')
    elif selection['status'] not in ('design_failure_warm_backbone_exceeds_K',
            'design_failure_cover_union_exceeds_K'):
        raise ValueError('Unexpected selection failure')
    retained_mask = [mid in selected for mid in ids]
    return {'adapter_policy': POLICY, 'arm': arm, 'case_key': case_key,
        'case_identity': case.identity(), 'original_movement_ids': ids,
        'retained_movement_ids': [mid for mid in ids if mid in selected],
        'retained_mask': retained_mask, 'selected_flexible_ids': [mid for mid in ids if mid in selected & flexible],
        'boundary_ids': [mid for mid in ids if mid in boundaries],
        'backbone_ids': selection['backbone_ids'], 'base_backbone_ids': selection['base_backbone_ids'],
        'warm_backbone_ids': selection['warm_backbone_ids'],
        'prior_protected_flexible_ids': selection['prior_protected_flexible_ids'],
        'protected_flexible_ids': selection['protected_flexible_ids'],
        'cover_flexible_ids': selection['cover_flexible_ids'], 'rank_fill_ids': selection['rank_fill_ids'],
        'ordinary_selector_ledger': ordinary, 'common_prior_representable': selection['common_prior_representable'],
        'M': len(flexible), 'K': selection['K'],
        'status': 'selected' if selection_ok else selection['status'],
        'native_dispatch_permitted': selection_ok, 'selection_policy': selection['policy'],
        'selection': selection, 'scores': scores, 'model_metadata': model_metadata,
        'CA1_score_ledger': score_ledger, 'cover_ledger': cover_ledger,
        'expected_used_asset_sha256': assets,
        'asset_bytes_hashed_by_adapter': False,
        'caller_verified_assets_required': arm in ('GNN', 'CatBoost'),
        'fresh_scores': arm != 'full', 'model_reloaded_this_call': arm in ('GNN', 'CatBoost'),
        'learned_price_inputs': ['a'] if arm in ('GNN', 'CatBoost') else [],
        'curvature_b_used_for_ranking': arm in ('CA1', 'CoverCA1'),
        'random_policy': {'salt': RANDOM_SALT, 'seed': random_seed, 'tariff_and_stage_in_key': False}
            if arm == 'random' else None,
        'timings': {**timings, 'adapter_wall_s': time.monotonic()-wall0,
            'adapter_cpu_s': time.process_time()-cpu0},
        'fit_calls': 0, 'native_solver_calls': 0, 'replay_calls': 0, 'saved_plan_or_score_reads': 0,
        'learned_inference_calls': int(arm in ('GNN', 'CatBoost')),
        'route_only_assignment_calls': len(cover_ledger['covers']) if cover_ledger is not None else 0,
        'physical_feasibility_certified': False, 'full_bound_certified': False}
