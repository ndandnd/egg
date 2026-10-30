"""Read-only 2017 physical-column and compatible target-bound review.

Source-market columns are repriced at the frozen target market as feasible
physical plans; their source-market lower bounds are never compared to target
bounds. No optimizer, raw trace scan, refit, or reserved test data is used.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import learned_proposals as lp  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402


FROZEN = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1/learning_s2017_n28/state0"
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-budget-attempt1/learning_s2017_n28/state0"
OUTPUT_DIR = Path(__file__).resolve().parent
ARCHIVED = ("source0", "source1", "cold", "cheapest_bill", "retained")
NEW = ("cost_only", "cost_learned")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def review():
    frozen = json.loads(FROZEN.read_text())
    group = frozen["design"]["groups"]["learning_s2017_n28"]
    case = lp.case_from_dict(group["case"])
    target = nh.Market(**group["markets"]["target"])
    assert case.identity() == group["case_identity"]
    assert target.identity() == group["market_identities"]["target"]
    paths = ([(arm, STAGE2 / arm / "raw_result.json") for arm in ARCHIVED]
             + [("shared_budget_"+policy, ATTEMPT / policy / "raw_hull.json")
                for policy in NEW])
    input_records = [{"origin": origin, "path": rel(path), "sha256": sha(path)}
                     for origin,path in paths]
    rows, lower_records = [], []
    for origin,path in paths:
        saved = json.loads(path.read_text())["result"]
        assert saved["physical_identity"] == case.identity()
        market_kind = (origin if origin in ("source0", "source1") else "target")
        assert saved["market_identity"] == group["market_identities"][market_kind]
        if market_kind == "target":
            lower = Q(saved["lower_certificate"]["lower_exact"])
            lower_records.append({"origin": origin,
                "lower_exact": str(lower), "lower": float(lower),
                "status": saved["status"]})
        for index,column in enumerate(saved["columns"]):
            plan = column["plan"]
            replay = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            assert replay["replay_ok"] is True
            assert column["physical_identity"] == case.identity()
            assert column["load"] == replay["load"]
            assert column["ops_cost"] == replay["ops_cost"]
            cost = Q(replay["ops_cost"]) + nh.supply(target, replay["load"])
            rows.append({"origin": origin, "column_index": index,
                "source_market": market_kind, "column_key": column["key"],
                "plan_hash": nr.digest(plan), "bus_count": len(plan["vehicles"]),
                "source_kind": column["source"].get("source_kind"),
                "pricing_call": column["source"].get("pricing_call"),
                "exact_target_cost": str(cost), "target_cost": float(cost),
                "ops_cost": replay["ops_cost"], "load_kwh": replay["load"]})
    assert len(rows) == 21
    best = min(rows, key=lambda row: Q(row["exact_target_cost"]))
    archived_target_rows = [row for row in rows if row["origin"] in
                            ("cold", "cheapest_bill", "retained")]
    best_archived = min(archived_target_rows,
                        key=lambda row: Q(row["exact_target_cost"]))
    assert best["origin"].startswith("shared_budget_")
    improvement = Q(best_archived["exact_target_cost"])-Q(best["exact_target_cost"])
    assert improvement > 0
    strongest_lower = max(lower_records, key=lambda row: Q(row["lower_exact"]))
    archived_lower = max((row for row in lower_records if row["origin"] in
                          ("cold", "cheapest_bill", "retained")),
                         key=lambda row: Q(row["lower_exact"]))
    assert strongest_lower["origin"].startswith("shared_budget_")
    lower_gain = Q(strongest_lower["lower_exact"])-Q(archived_lower["lower_exact"])
    gap_upper = Q(best["exact_target_cost"])-Q(strongest_lower["lower_exact"])
    assert lower_gain > 0 and gap_upper > 0
    incumbent_load = list(best["load_kwh"])
    prices = [Q(a)+Q(b)*Q(load) for a,b,load in
              zip(target.a,target.b,incumbent_load)]
    for row in rows:
        bill = sum((p*Q(load) for p,load in zip(prices,row["load_kwh"])), Q(0))
        row["own_price_energy_bill_exact"] = str(bill)
        row["own_price_energy_bill"] = float(bill)
        row["own_price_linearized_cost_exact"] = str(Q(row["ops_cost"])+bill)
    response = min(rows, key=lambda row: Q(row["own_price_linearized_cost_exact"]))
    response_load = list(response["load_kwh"])
    regret = Q(best["own_price_linearized_cost_exact"])-Q(
        response["own_price_linearized_cost_exact"])
    assert regret > 0
    for row in rows:
        row.pop("load_kwh")
    return {"schema": "egg-shared-budget-physical-pool-review-v1",
        "case": "learning_s2017_n28", "case_identity": case.identity(),
        "target_market_identity": target.identity(),
        "frozen_json": rel(FROZEN), "frozen_sha256": sha(FROZEN),
        "inputs": input_records,
        "method": "Fresh physical replay of 21 saved columns, target-market Fraction cost for every plan, saved target-market lower certificates only, and exact own-load target gradient prices a+b*load. No optimization.",
        "columns_replayed": len(rows), "target_lower_certificates": lower_records,
        "best_physical_incumbent": best,
        "best_physical_incumbent_load_kwh": incumbent_load,
        "best_archived_target_control": best_archived,
        "physical_cost_improvement_exact": str(improvement),
        "physical_cost_improvement": float(improvement),
        "strongest_fresh_target_lower": strongest_lower,
        "strongest_archived_target_lower": archived_lower,
        "target_lower_improvement_exact": str(lower_gain),
        "target_lower_improvement": float(lower_gain),
        "incumbent_minus_global_lower_exact": str(gap_upper),
        "incumbent_minus_global_lower": float(gap_upper),
        "own_load_gradient_prices_exact": [str(p) for p in prices],
        "best_response_among_replayed_columns": response,
        "best_response_load_kwh": response_load,
        "witnessed_regret_lower_bound_exact": str(regret),
        "witnessed_regret_lower_bound": float(regret),
        "all_columns": rows,
        "scope": "Source-market columns are feasible physical plans repriced at target; their lower bounds are excluded from target bound comparison. The response minimizes only over 21 replayed plans, so regret lower-bounds oracle regret at this incumbent only. Neither the 5-bus incumbent nor physical optimum is certified; the incumbent-minus-lower gap remains wide."}


def markdown(report):
    best = report["best_physical_incumbent"]
    archived = report["best_archived_target_control"]
    lower = report["strongest_fresh_target_lower"]
    response = report["best_response_among_replayed_columns"]
    return "\n".join([
        "# Shared-budget 2017 physical pool and target bounds", "",
        "Fresh replay of 21 saved columns finds a new five-bus physical plan",
        f"at **{best['target_cost']:.6f}** (cost-only hull, pricing call",
        f"{best['pricing_call']}). It improves the best archived target-control",
        f"plan ({archived['target_cost']:.6f}) by",
        f"**{report['physical_cost_improvement']:.6f}** cost units. Both new",
        "candidate plans also independently replay; this best plan is a later",
        "saved hull column.", "",
        f"The strongest fresh target-market global lower certificate is",
        f"**{lower['lower']:.6f}**, improving the strongest archived target",
        f"lower by {report['target_lower_improvement']:.6f}. The best replayed",
        f"physical plan is within {report['incumbent_minus_global_lower']:.6f}",
        "cost units of the physical optimum under that certificate, so the",
        "optimality gap is still wide. Source-market lower certificates were",
        "excluded from this target-market bound comparison.", "",
        "At this new incumbent's exact own-load gradient, the best response",
        f"among the 21 replayed plans is {response['origin']} column",
        f"{response['column_index']}, witnessing regret of at least",
        f"**{report['witnessed_regret_lower_bound']:.6f}** cost units at this",
        "specific incumbent. Its true target cost is",
        f"{response['target_cost']:.6f}; the price-taking comparison does not",
        "establish support failure of the unknown physical optimum.", "",
        "The [JSON review](SHARED_BUDGET_PHYSICAL_POOL_REVIEW.json) gives exact",
        "fractions, plan hashes, source provenance, gradient prices and every",
        "replayed cost. Reproduce with:", "",
        "```sh", "PYTHONPATH=src python3 research-20260930/learning-campaign/review_shared_budget_pool.py --check", "```", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved outputs")
    args = parser.parse_args()
    report = review()
    outputs = {OUTPUT_DIR / "SHARED_BUDGET_PHYSICAL_POOL_REVIEW.json":
               json.dumps(report, indent=2, sort_keys=True) + "\n",
               OUTPUT_DIR / "SHARED_BUDGET_PHYSICAL_POOL_REVIEW.md": markdown(report)}
    for path,text in outputs.items():
        if args.check:
            assert path.read_text() == text, f"Outdated output: {path}"
        else:
            path.write_text(text)
    print(f"Replayed {report['columns_replayed']} columns; best physical "
          f"{report['best_physical_incumbent']['target_cost']:.6f}; "
          f"target lower {report['strongest_fresh_target_lower']['lower']:.6f}")


if __name__ == "__main__":
    main()
