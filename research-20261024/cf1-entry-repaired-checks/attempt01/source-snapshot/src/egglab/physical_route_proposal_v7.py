"""Small fixed TRAIN proposal comparison using the existing physical decoder."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import time
import numpy as np
from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import physical_route_decoder_v1 as decoder
from egglab import route_fixed_repair as repair
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool

POLICY = "physical-route-proposals-heldout-train-v7"
GROUP_IDS = tuple(range(10064, 10080))
ARMS = ("tabular_v3", "families_v5", "graph_v6")
POOL_SHA = "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"


def read(path):
    return json.loads(Path(path).read_text())


def inputs(group_id, manifest):
    if group_id not in GROUP_IDS or manifest["policy"] != POLICY:
        raise ValueError("Undeclared prospective TRAIN group")
    folder = base.ROOT / manifest["pool_path"]
    if base.sha(folder / "pool_manifest.json") != POOL_SHA:
        raise ValueError("Changed exact128 TRAIN pool")
    pooled = read(folder / "pool_manifest.json")
    if pooled["base_ids"] != list(range(10000, 10128)):
        raise ValueError("Wrong TRAIN prefix")
    for name in pool.TABLES:
        if base.sha(folder / name) != pooled["output_hashes"][name]:
            raise ValueError("Changed admitted input table")
    cases = [json.loads(s) for s in (folder / "cases.jsonl").read_text().splitlines()]
    rows = [r for r in cases if r["base_id"] == group_id]
    if len(rows) != 1 or rows[0]["split"] != "train":
        raise ValueError("Missing unique TRAIN timetable")
    row = rows[0]; case = edge.case_from_dict(row["case"])
    if case.identity() != row["case_identity"] or case.identity() != physical.make_case(group_id).identity():
        raise ValueError("Case identity differs from frozen generator")
    sources = [json.loads(s) for s in (folder / "source_inputs.jsonl").read_text().splitlines()]
    sources = [s for s in sources if s["base_group"] == row["base_group"]]
    eligibility = pooled["group_eligibility"][group_id-10000]
    if eligibility["base_group"] != row["base_group"] or eligibility["observed_source_count"] != len(sources):
        raise ValueError("Source eligibility differs")
    return case, physical.market(case, "day"), sources, eligibility


def raw_decode(case, logits):
    """Same input-only incoming/outgoing argmax rule as EdgePrior; no repair."""
    logits = np.asarray(logits, dtype=float)
    if logits.shape != (len(case.movements),) or not np.isfinite(logits).all():
        raise ValueError("Invalid movement logits")
    chosen = set()
    for trip in case.trips:
        for side in ("after", "before"):
            choices = [i for i, m in enumerate(case.movements) if getattr(m, side) == trip.id]
            if not choices:
                raise ValueError("Missing incoming/outgoing movement")
            chosen.add(case.movements[max(choices, key=lambda i: (logits[i], -i))].id)
    selected = sorted(chosen)
    # Branching or incomplete topologies fail here and receive no plan credit.
    try:
        paths = pf.recover_paths(case, selected)
    except ValueError as exc:
        return {"status": "invalid_topology", "selected_movements": selected, "physical_comparison_credit": False,
                "failure": {"type": type(exc).__name__, "message": str(exc)}}
    return {"status": "structurally_valid", "selected_movements": selected, "paths": paths,
            "physical_comparison_credit": False}


def charge_budget():
    return nr.Budget(backend="GRB", threads=1, phase_seconds=45., wall_seconds=55., max_rounds=1, epsilon=1e-4)


def replay_candidate(case, market, plan, selected, source_topologies):
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    actual = {mid for v in plan["vehicles"] for mid in v["movements"]}
    if actual != set(selected):
        raise ValueError("Fixed route changed during charging")
    exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
    return {"status": "replayed", "plan": plan, "plan_hash": nr.digest(plan), "replay": replay,
            "objective_exact": str(exact), "vehicle_count": len(plan["vehicles"]),
            "topology_novel": all(actual != set(s) for s in source_topologies) if source_topologies else None}


def source_policy(direct, recharged):
    """Predeclared best direct-or-recharged source policy; failures add no credit."""
    rows = [(c["source"]+"_direct", c["direct_bill_exact"]) for c in direct]
    rows += [(name, r["objective_exact"]) for name, r in recharged.items() if r and r.get("status") == "replayed"]
    if not rows:
        return {"status": "unavailable"}
    name, value = min(rows, key=lambda p: (Fraction(p[1]), p[0]))
    return {"status": "replayed", "selected_arm": name, "objective_exact": value,
            "choice_rule": "minimum exact curved target bill; arm name breaks exact ties",
            "uses_all_direct_admission_and_attempted_source_charge_replay_stages": True}


def stage(name, case, market, source_rows, payload):
    if name == "sources":
        return decoder.admitted_source_controls(case, market, source_rows)
    if name == "raw_decode":
        return raw_decode(case, payload["logits"])
    if name == "repair":
        return repair.decode_path_cover(case, payload.get("logits"), time_limit_seconds=5.,
            cover_policy=payload["cover_policy"], energy_relaxation=True, charging_caps=True, shared_charging=True)
    if name == "charge":
        selected = payload["selected_movements"]
        plan, internal_replay, stats = repair._solve_fixed_charge(case, market, selected, charge_budget())
        return {"selected_movements": selected, "plan": plan, "native_stats": stats,
                "internal_charge_replay": internal_replay, "physical_comparison_credit": False}
    if name == "replay":
        return replay_candidate(case, market, payload["plan"], payload["selected_movements"], payload["source_topologies"])
    if name == "cold_planner":
        budget = nr.Budget(backend="GRB", threads=1, phase_seconds=55., wall_seconds=70., max_rounds=4, epsilon=1e-4)
        row = pf.solve_planner(case, market.a, market.b, budget)
        row["physical_comparison_credit"] = False
        return row
    if name in ("cold_hull", "retained_hull"):
        budget = nh.Budget(backend="GRB", threads=1, phase_seconds=55., wall_seconds=70.,
            pricing_calls=4, master_calls=6, pool_cap=32, epsilon=1e-4, pool_tol=1e-6,
            polish_steps=64, rational_bits=4096, polish_seconds=15.)
        return decoder.verify_global(case, market, None if name == "cold_hull" else payload["plans"],
                                     payload.get("lineage", {"policy": POLICY}), budget)
    raise ValueError("Undeclared stage")
