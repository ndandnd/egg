"""Input-only edge-score route covers and physically gated complete-fleet proposals."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import time

import numpy as np

from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import route_fixed_repair as repair
from experiments import computational_benchmark as base
from experiments import retrieval_comparison as retrieval

POLICY = "physical-route-decoder-heldout-train-v1"
GROUP_IDS = (10036, 10037, 10038, 10039)
MODEL_NAMES = ("logistic", "hist_boosted")
PREFIXES = (32, 64)
SEED = 17
TARGET_KIND = "day"
HULL_CONTROLS = dict(reuse_policy="feasible_pool", pricing_reserve_seconds=10.0,
                     master_policy="numerical_qp_proposal", bound_cache_policy="none")


@dataclass(frozen=True)
class FrozenScorer:
    prefix: int
    name: str
    fold: int
    seed: int
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    coef: tuple[float, ...] | None
    intercept: float | None
    tree: object | None
    result_sha256: str
    tree_sha256: str | None
    fit_groups: tuple[str, ...]
    inner_groups: tuple[str, ...]
    outer_groups: tuple[str, ...]

    def logits(self, case, prices):
        x = edge.edge_features(case, prices)
        z = (x - np.asarray(self.mean)) / np.asarray(self.scale)
        if self.name == "logistic":
            scores = z @ np.asarray(self.coef) + self.intercept
        else:
            p = np.clip(self.tree.predict_proba(z)[:, 1], 1e-9, 1-1e-9)
            scores = np.log(p) - np.log1p(-p)
        if scores.shape != (len(case.movements),) or not np.isfinite(scores).all():
            raise ValueError("Frozen model produced invalid movement scores")
        return scores


def load_scorer(root, *, prefix, name, group_id, expected_pool_manifest_sha256):
    """Use only frozen fit artifacts; outer metrics/labels never select a scorer."""
    import joblib
    from egglab import physical_route_model_v2 as model32
    from egglab import physical_route_model_v3 as model64
    if (prefix not in PREFIXES or name not in MODEL_NAMES or group_id not in GROUP_IDS
            or len(expected_pool_manifest_sha256) != 64):
        raise ValueError("Undeclared scorer/pilot group")
    fold = (group_id - 10000) % 4
    task_id = fold*3  # Seed 17 is the first of the frozen three seeds.
    folder = Path(root) / f"task{task_id:02d}"
    receipt = json.loads((folder / "receipt.json").read_text())
    result_path = folder / "result.json"
    result_sha = base.sha(result_path)
    if (receipt.get("status") != "completed" or receipt.get("task_id") != task_id
            or receipt.get("result_sha256") != result_sha
            or receipt.get("pool_manifest_sha256") != expected_pool_manifest_sha256):
        raise ValueError("Unadmitted or changed frozen model artifact")
    result = json.loads(result_path.read_text())
    policy = model32.POLICY if prefix == 32 else model64.POLICY
    if (result.get("policy") != policy or result.get("task_id") != task_id
            or result.get("seed") != SEED or result.get("fold") != fold
            or result.get("pool_manifest_sha256") != expected_pool_manifest_sha256
            or tuple(result.get("features", ())) != edge.FEATURES):
        raise ValueError("Model policy, seed, fold, feature whitelist, or pool changed")
    group = f"physical_v2_s{group_id}"
    if prefix == 64:
        if (group not in result.get("outer_groups", ())
                or group in result.get("fit_groups", ())
                or group in result.get("inner_groups", ())):
            raise ValueError("64-group model did not hold target timetable out")
    else:
        if any(group in result.get(key, ()) for key in ("fit_groups", "inner_groups", "outer_groups")):
            raise ValueError("32-group model unexpectedly saw out-of-bank timetable")
    mean = tuple(result["feature_mean_fit_only"])
    scale = tuple(result["feature_scale_fit_only"])
    if (len(mean) != len(edge.FEATURES) or len(scale) != len(mean)
            or not np.isfinite(mean).all() or not np.isfinite(scale).all()
            or any(s <= 0 for s in scale)):
        raise ValueError("Invalid fit-only normalization")
    tree, tree_sha = None, None
    if name == "logistic":
        config = result["logistic"]["config"]
        if config != {"C": model32.LOGISTIC_C, "solver": "lbfgs",
                      "max_iter": model32.LOGISTIC_MAX_ITER, "tol": model32.LOGISTIC_TOL}:
            raise ValueError("Frozen logistic configuration changed")
        coef = tuple(result["logistic"]["coef"][0])
        intercept = float(result["logistic"]["intercept"][0])
        if len(coef) != len(mean) or not np.isfinite(coef).all() or not np.isfinite(intercept):
            raise ValueError("Invalid frozen logistic coefficients")
    else:
        tree_path = folder / "hist_boosted.joblib"
        tree_sha = base.sha(tree_path)
        if receipt.get("hist_boosted_sha256") != tree_sha:
            raise ValueError("Frozen boosted tree hash changed")
        config = result["hist_boosted"]["config"]
        if (config["candidate_iterations"] != list(model32.TREE_ITERATIONS)
                or config["max_leaf_nodes"] != model32.TREE_MAX_LEAVES
                or config["min_samples_leaf"] != model32.TREE_MIN_LEAF
                or config["max_bins"] != model32.TREE_MAX_BINS
                or config["learning_rate"] != model32.TREE_LR
                or config["l2_regularization"] != model32.TREE_L2
                or config["early_stopping"] is not False):
            raise ValueError("Frozen boosted tree configuration changed")
        tree = joblib.load(tree_path)
        if type(tree).__name__ != "HistGradientBoostingClassifier":
            raise ValueError("Unknown frozen tree artifact")
        coef, intercept = None, None
    return FrozenScorer(prefix, name, fold, SEED, mean, scale, coef, intercept,
                        tree, result_sha, tree_sha,
                        tuple(result["fit_groups"]), tuple(result["inner_groups"]),
                        tuple(result["outer_groups"]))


def admitted_source_controls(case, market, source_rows):
    """Replay available same-case sources; rank with case/tariff inputs only."""
    nh.validate_market(case, market)
    candidates = []
    seen = set()
    for row in source_rows:
        source = row.get("source")
        if (row.get("case_identity") != case.identity()
                or source not in ("source0", "source1") or source in seen):
            raise ValueError("Foreign, duplicate, or unknown source fleet")
        seen.add(source)
        plan = row["source_plan"]
        if nr.digest(plan) != row.get("source_plan_hash"):
            raise ValueError("Source plan hash changed")
        source_market = physical.market(case, source)
        if row.get("market_identity") != source_market.identity():
            raise ValueError("Source market identity changed")
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        if replay != row.get("source_replay"):
            raise ValueError("Archived source replay differs from fresh replay")
        topology = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
        if topology != set(row.get("selected_movements", ())):
            raise ValueError("Source topology changed")
        exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        nearest = sum((a-b)**2 for a, b in zip(market.a, source_market.a))**.5
        candidates.append({"source": source, "plan": plan, "replay": replay,
            "plan_hash": nr.digest(plan), "topology": sorted(topology),
            "nearest_price_distance": nearest, "direct_bill_exact": str(exact)})
    candidates.sort(key=lambda c: c["source"])
    if not candidates:
        raise ValueError("No replayed source fleet; source controls unavailable")
    nearest = min(candidates, key=lambda c: (c["nearest_price_distance"], c["source"]))
    cheapest = min(candidates, key=lambda c: (Fraction(c["direct_bill_exact"]), c["source"]))
    return {"candidates": candidates,
        "first_source": candidates[0]["source"],
        "nearest_price": nearest["source"],
        "cheapest_exact_bill": cheapest["source"],
        "intended_sources": 2, "observed_sources": len(candidates)}


def decoded_candidate(case, market, logits, source_topologies, *,
                      cover_policy, path_seconds, charge_budget):
    """Keep path-cover, charging, and independent replay as distinct stages."""
    started = time.monotonic()
    result = {"cover_policy": cover_policy, "status": "failed", "failure": None,
              "timing_seconds": {}}
    stage = "cover"
    try:
        cover = repair.decode_path_cover(case, logits, time_limit_seconds=path_seconds,
            cover_policy=cover_policy, energy_relaxation=True,
            charging_caps=True, shared_charging=True)
        result["cover"] = cover
        result["timing_seconds"]["cover"] = time.monotonic()-started
        stage = "charging"
        charge_started = time.monotonic()
        plan, replay, native_stats = repair._solve_fixed_charge(case, market,
            cover["selected_movements"], charge_budget)
        result["timing_seconds"]["charging"] = time.monotonic()-charge_started
        stage = "independent_replay"
        replay_started = time.monotonic()
        independently_replayed = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        if independently_replayed != replay:
            raise ValueError("Fixed-charge replay differs from independent replay")
        actual = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
        if actual != set(cover["selected_movements"]):
            raise ValueError("Repaired route differs from decoded path cover")
        exact = Fraction(independently_replayed["ops_cost"]) + nh.supply(
            market, independently_replayed["load"])
        result.update(status="replayed", plan=plan, plan_hash=nr.digest(plan),
            replay=independently_replayed, native_stats=native_stats,
            objective_exact=str(exact),
            topology_novel=all(actual != set(source) for source in source_topologies))
        result["timing_seconds"]["independent_replay"] = time.monotonic()-replay_started
    except Exception as exc:
        result["failure"] = {"stage": stage, "type": type(exc).__name__,
                             "message": str(exc)}
        if isinstance(exc, repair.RepairStageFailure):
            result.update(exc.telemetry)
    result["timing_seconds"]["total"] = time.monotonic()-started
    return result


def feasible_envelope(case, market, plans, lineage, budget):
    """Replayed plans only; this is a feasible import and carries no old bound."""
    if not plans or len(plans) > budget.pool_cap:
        raise ValueError("Empty or oversized feasible import")
    for plan in plans:
        nr.replay_native(case, plan)
    digest = nr.digest(lineage)
    bridge = nh.Market("route-decoder-feasible-" + digest, market.a, market.b)
    identity = compact.state_identity(case, bridge, "retained", 0, budget, **HULL_CONTROLS)
    columns = []
    for index, plan in enumerate(plans):
        column = nh.native_column(case, plan,
            {"state_identity": identity, "pricing_oracle": compact.ORACLE_ID,
             "source_kind": "replayed_route_decoder_input", "input_index": index,
             "lineage_digest": digest}, compact.EXTRACTION_POLICY)
        nh.replay_column(case, column, compact.EXTRACTION_POLICY)
        if column["key"] not in {c["key"] for c in columns}:
            columns.append(column)
    mixtures = [nh.replay_mixture(case, market, [c], [1.0], compact.EXTRACTION_POLICY)
                for c in columns]
    best = min(mixtures, key=lambda x: Fraction(x["objective_exact"]))
    envelope = {"schema": nh.SCHEMA, "kind": "derived_feasible_pool_import",
        "status": "bounded", "arm": "retained", "state_index": 0,
        "state_identity": identity, "physical_identity": case.identity(),
        "market_identity": bridge.identity(), "pricing_oracle": compact.ORACLE_ID,
        "extraction_policy": compact.EXTRACTION_POLICY,
        "reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10.0,
        "master_policy": "numerical_qp_proposal", "qp_denominator": 1_000_000_000,
        "qp_maxiter": 500, "lineage": lineage, "lineage_digest": digest,
        "columns": columns, "mixture": best, "upper": best["upper"]}
    imported = nh.import_pool(case, envelope, identity, budget, previous_index=0,
        extraction_policy=compact.EXTRACTION_POLICY, reuse_policy="feasible_pool",
        oracle_id=compact.ORACLE_ID, pricing_reserve_seconds=10.0)
    if len(imported) != len(columns):
        raise ValueError("Feasible import changed source projection count")
    return envelope, identity


def verify_global(case, market, plans, lineage, budget):
    """Separate bounded target hull; lower bound exists only if certified/replayed."""
    started = time.monotonic()
    pool_import_wall = 0.0
    try:
        if plans is None:
            hull_started = time.monotonic()
            raw = compact.certify(case, market, budget, arm="cold", state_index=0,
                                  **HULL_CONTROLS)
            seed_count = 0
        else:
            pool_started = time.monotonic()
            envelope, identity = feasible_envelope(case, market, plans, lineage, budget)
            pool_import_wall = time.monotonic()-pool_started
            hull_started = time.monotonic()
            raw = compact.certify(case, market, budget, arm="retained", state_index=1,
                previous=envelope, expected_previous=identity, **HULL_CONTROLS)
            seed_count = len(envelope["columns"])
        hull_wall = time.monotonic()-hull_started
        assessment = retrieval.assess_hull(case, market, raw)
        return {"status": "checked", "source_seed_count": seed_count,
            "assessment": assessment, "raw_hull": raw,
            "pool_import_wall_seconds": pool_import_wall,
            "hull_wall_seconds": hull_wall,
            "wall_seconds": time.monotonic()-started}
    except Exception as exc:
        return {"status": "failed", "failure": {"type": type(exc).__name__,
            "message": str(exc)}, "pool_import_wall_seconds": pool_import_wall,
            "wall_seconds": time.monotonic()-started}
