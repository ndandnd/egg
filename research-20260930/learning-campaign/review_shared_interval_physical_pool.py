"""Read-only physical-plan review of two 2016 hulls and archived control.

Replays only saved columns. No optimizer, trace scan, refit, cluster action, or
reserved test case is used. Fractions represent stored finite float values.
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
CONTROL = ROOT / "result/learning_campaign/20260930-stage2-attempt1/learning_s2016_n20/state0/cheapest_bill/raw_result.json"
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-interval-attempt1"
HULLS = {
    policy: ATTEMPT / "learning_s2016_n20" / "state0" / policy / "raw_hull.json"
    for policy in ("cost_only", "cost_learned")}
OUTPUT_DIR = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def replay_rows(case, market, label, path):
    saved = json.loads(path.read_text())["result"]
    assert saved["physical_identity"] == case.identity()
    assert saved["market_identity"] == market.identity()
    rows = []
    for index, column in enumerate(saved["columns"]):
        plan = column["plan"]
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        assert replay["replay_ok"] is True
        assert column["physical_identity"] == case.identity()
        assert column["load"] == replay["load"]
        assert column["ops_cost"] == replay["ops_cost"]
        cost = Q(replay["ops_cost"]) + nh.supply(market, replay["load"])
        source = column["source"]
        rows.append({"origin": label, "column_index": index,
            "column_key": column["key"], "plan_hash": nr.digest(plan),
            "bus_count": len(plan["vehicles"]),
            "source_kind": source.get("source_kind"),
            "pricing_call": source.get("pricing_call"),
            "pricing_oracle": source.get("pricing_oracle"),
            "exact_target_cost": str(cost), "target_cost": float(cost),
            "ops_cost": replay["ops_cost"], "load_kwh": replay["load"]})
    return rows


def review():
    frozen = json.loads(FROZEN.read_text())
    group = frozen["design"]["groups"]["learning_s2016_n20"]
    case = lp.case_from_dict(group["case"])
    market = nh.Market(**group["markets"]["target"])
    assert case.identity() == group["case_identity"]
    assert market.identity() == group["market_identities"]["target"]
    rows = replay_rows(case, market, "archived_cheapest_bill", CONTROL)
    for policy, path in HULLS.items():
        rows.extend(replay_rows(case, market, "shared_interval_"+policy, path))
    assert len(rows) == 15
    new_rows = [row for row in rows if row["origin"].startswith("shared_interval_")]
    assert len(new_rows) == 10
    best = min(rows, key=lambda row: Q(row["exact_target_cost"]))
    best_new = min(new_rows, key=lambda row: Q(row["exact_target_cost"]))
    incumbent_load = list(best["load_kwh"])
    # Native hull supply is sum(a*x + b*x^2/2); its own-load gradient is a+b*x.
    prices = [Q(a)+Q(b)*Q(load) for a,b,load in
              zip(market.a, market.b, best["load_kwh"])]

    def linearized(row):
        return Q(row["ops_cost"]) + sum(
            (price*Q(load) for price,load in zip(prices,row["load_kwh"])), Q(0))

    for row in rows:
        bill = sum((price*Q(load) for price,load in
                    zip(prices,row["load_kwh"])), Q(0))
        row["own_price_energy_bill_exact"] = str(bill)
        row["own_price_energy_bill"] = float(bill)
        row["linearized_cost_at_incumbent_prices_exact"] = str(linearized(row))
    # Select after saving exact linearized costs; the gradient is fixed at best.
    response = min(rows, key=lambda row: Q(row["linearized_cost_at_incumbent_prices_exact"]))
    response_load = list(response["load_kwh"])
    for row in rows:
        row.pop("load_kwh")  # keep the persisted column table compact
    own_linearized = Q(best["linearized_cost_at_incumbent_prices_exact"])
    response_linearized = Q(response["linearized_cost_at_incumbent_prices_exact"])
    regret = own_linearized-response_linearized
    assert regret > 0
    best_new_cost = Q(best_new["exact_target_cost"])
    best_cost = Q(best["exact_target_cost"])
    assert best_new_cost > best_cost
    lower_candidates = []
    for policy,path in HULLS.items():
        receipt = json.loads(path.read_text())["result"]
        lower_candidates.append((Q(receipt["lower_certificate"]["lower_exact"]),policy))
    global_lower, lower_policy = max(lower_candidates)
    physical_gap_upper = best_cost-global_lower
    assert physical_gap_upper >= 0
    input_paths = [FROZEN, CONTROL, *HULLS.values()]
    return {"schema": "egg-shared-interval-physical-pool-review-v1",
        "case": "learning_s2016_n20", "case_identity": case.identity(),
        "market_identity": market.identity(),
        "inputs": [{"path": rel(path), "sha256": sha(path)} for path in input_paths],
        "method": "Fresh native physical replay and checked pricing start for 15 saved columns; exact Fraction target costs from stored finite floats. Own-load gradient a+b*load of best physical candidate; compare only replayed columns under its linearized cost.",
        "columns_replayed": len(rows), "new_hull_columns_replayed": len(new_rows),
        "best_physical_incumbent": best,
        "best_physical_incumbent_load_kwh": incumbent_load,
        "best_new_hull_column": best_new,
        "new_column_minus_best_incumbent_exact": str(best_new_cost-best_cost),
        "new_column_minus_best_incumbent": float(best_new_cost-best_cost),
        "own_load_gradient_prices_exact": [str(price) for price in prices],
        "own_load_gradient_prices": [float(price) for price in prices],
        "best_response_among_replayed_columns": response,
        "best_response_load_kwh": response_load,
        "fresh_global_lower_certificate_origin": "shared_interval_"+lower_policy,
        "fresh_global_lower_certificate_exact": str(global_lower),
        "fresh_global_lower_certificate": float(global_lower),
        "best_incumbent_minus_global_lower_exact": str(physical_gap_upper),
        "best_incumbent_minus_global_lower": float(physical_gap_upper),
        "incumbent_own_price_energy_bill_exact": best["own_price_energy_bill_exact"],
        "best_response_own_price_energy_bill_exact": response["own_price_energy_bill_exact"],
        "incumbent_linearized_cost_exact": str(own_linearized),
        "best_response_linearized_cost_exact": str(response_linearized),
        "witnessed_regret_lower_bound_exact": str(regret),
        "witnessed_regret_lower_bound": float(regret),
        "all_columns": rows,
        "scope": "The response minimizes only over these 15 replayed physical plans. Its positive difference lower-bounds oracle regret at this specific incumbent; it does not prove support failure of the unknown physical optimum. The incumbent-minus-saved-global-lower difference bounds its physical cost gap, which remains open."}


def markdown(report):
    best = report["best_physical_incumbent"]
    new = report["best_new_hull_column"]
    response = report["best_response_among_replayed_columns"]
    return "\n".join([
        "# Shared-interval 2016 physical pool review", "",
        "Fresh physical replay verifies all 10 columns from the two new 2016 hull",
        "receipts and all five archived cheapest-bill control columns. The best",
        f"new column costs **{new['target_cost']:.6f}** ({new['origin']}, column",
        f"{new['column_index']}). The archived control remains stronger at",
        f"**{best['target_cost']:.6f}** (column {best['column_index']}).",
        "Thus the report's historical physical incumbent is still the best",
        "individual plan in these compared receipts.", "",
        "At that incumbent's exact own-load gradient `a + b × load`, the best",
        f"linearized response among the 15 replayed plans is archived column",
        f"{response['column_index']} (plan `{response['plan_hash']}`). The witnessed",
        f"regret is **{report['witnessed_regret_lower_bound']:.6f}** cost units:",
        "the incumbent's linearized cost minus that response's. The exact",
        "fraction, gradient prices, plan hashes, provenance and per-column costs",
        "are in [the JSON review](SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.json).", "",
        f"The incumbent uses {best['bus_count']} buses and has true target cost",
        f"{best['target_cost']:.6f}; the {response['bus_count']}-bus price-taking",
        f"response has **higher** true target cost {response['target_cost']:.6f}.",
        f"At the incumbent's prices their energy bills are",
        f"{best['own_price_energy_bill']:.6f} and",
        f"{response['own_price_energy_bill']:.6f}; adding operations cost gives",
        f"linearized costs {float(Q(report['incumbent_linearized_cost_exact'])):.6f}",
        f"and {float(Q(report['best_response_linearized_cost_exact'])):.6f}.", "",
        f"The strongest fresh saved global lower certificate is",
        f"{report['fresh_global_lower_certificate']:.6f}. The feasible incumbent",
        f"is within **{report['best_incumbent_minus_global_lower']:.6f}** cost",
        "units of the physical optimum under that certificate; the gap is open.", "",
        "This is a lower bound on oracle regret **at the archived incumbent**",
        "because the oracle could choose at least that replayed response. It does",
        "not establish support failure of the unknown physical optimum; the",
        "physical optimality gap remains open.", "",
        "Reproduce with:", "",
        "```sh", "PYTHONPATH=src python3 research-20260930/learning-campaign/review_shared_interval_physical_pool.py --check", "```", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved outputs")
    args = parser.parse_args()
    report = review()
    outputs = {OUTPUT_DIR / "SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.json":
               json.dumps(report, indent=2, sort_keys=True) + "\n",
               OUTPUT_DIR / "SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.md": markdown(report)}
    for path, text in outputs.items():
        if args.check:
            assert path.read_text() == text, f"Outdated output: {path}"
        else:
            path.write_text(text)
    print(f"Replayed {report['columns_replayed']} columns; best cost "
          f"{report['best_physical_incumbent']['target_cost']:.6f}; witnessed regret "
          f"{report['witnessed_regret_lower_bound']:.6f}")


if __name__ == "__main__":
    main()
