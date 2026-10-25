"""Fixed old scorer, day-price GNN control and unpruned fixed-topology QP label."""
import importlib.util
from pathlib import Path
import time

POLICY = 'warm-replication-original-scorer-GNN-day-fixed-route-QP-v2'
OLD_SCORER = 'research-20261025/warm_replanning/scoring.py'


def _original(root):
    path = (Path(root).resolve()/OLD_SCORER).resolve()
    spec = importlib.util.spec_from_file_location('warm_replication_original_scoring', path)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load the frozen original scoring library')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ValueError('Original scoring library path differs')
    return module


def expected_assets(asset_lock, root):
    return _original(root).expected_assets(asset_lock, root)


def select(case, a, b, arm, *, root, asset_lock, case_key, random_seed,
           common_prior_ids=None, verified_asset_sha256=None, check=lambda: None):
    wall0, cpu0 = time.monotonic(), time.process_time()
    check()
    original = _original(root)
    ranking_a, delegate_arm = a, arm
    rank_input_tariff = 'caller_supplied'
    if arm == 'GNN_day':
        from egglab import physical_learning_cases as bank
        ranking_a = bank.market(case, 'day').a
        delegate_arm, rank_input_tariff = 'GNN', 'day'
    elif arm == 'fixed_route_QP':
        delegate_arm, rank_input_tariff = 'full', 'not_applicable_fixed_topology'
    check()
    result = original.select(case, ranking_a, b, delegate_arm, root=root,
        asset_lock=asset_lock, case_key=case_key, random_seed=random_seed,
        common_prior_ids=common_prior_ids, verified_asset_sha256=verified_asset_sha256,
        check=check)
    check()
    result.update(arm=arm, delegate_arm=delegate_arm, wrapper_policy=POLICY,
        rank_input_tariff=rank_input_tariff, rank_input_a=list(ranking_a),
        target_b_passed_unchanged=True, original_scoring_library=OLD_SCORER,
        cached_scores_or_model_objects=False)
    result['timings'].update(wrapper_wall_s=time.monotonic()-wall0,
        wrapper_cpu_s=time.process_time()-cpu0)
    return result
