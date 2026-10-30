"""Replay four saved candidates and isolate shared interval charging numerically.

This script only reads frozen inputs and compact saved candidates. Its SciPy LPs
have fixed routes and continuous charging energy; no fleet optimization, GRB,
or cluster work is performed. Numerical infeasibility is not an exact proof.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import warnings

from scipy.optimize import OptimizeWarning, linprog
from scipy.sparse import lil_matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import learned_proposals as lp  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from diagnose_charging_windows import analyze_route  # noqa: E402


STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
ATTEMPT = ROOT / "result/learning_repair/20260930-charging-cap-attempt1"
OUT = Path(__file__).resolve().parent
CASES = ("learning_s2016_n20", "learning_s2017_n28")
POLICIES = ("cost_only", "cost_learned")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def fixed_route_lp(case, cover, *, shared=False, slack=False):
    """Continuous SOC/visit-energy feasibility on one selected path cover.

    Every interval's individual variable has its native per-visit upper bound.
    The optional shared row is the native aggregate interval capacity. A slack
    variable on each shared row measures total grid-kWh overload.
    """
    compiled = nr.compile_case(case)
    trips = {trip.id: trip for trip in case.trips}
    modes = {mode.id: mode for mode in case.movements}
    B, reserve, eta = case.battery_kwh, case.reserve_kwh, case.efficiency
    keys, caps, by_visit, by_interval = [], [], {}, {}
    for vi, vehicle in enumerate(cover["vehicles"]):
        for mid in vehicle["movements"]:
            if modes[mid].kind not in ("depot", "pullin"):
                continue
            for k, interval in enumerate(compiled["intervals"]):
                cap = interval["rate_kw"]*interval["hours"]
                if cap > 0 and mid in interval["visits"]:
                    index = len(keys)
                    keys.append((vi, mid, k))
                    caps.append(cap)
                    by_visit.setdefault((vi, mid), []).append(index)
                    by_interval.setdefault(k, []).append(index)
    n = len(keys)
    rows = []

    def add(coefficients, lower=-math.inf, upper=math.inf):
        rows.append((coefficients.copy(), lower, upper))

    for vi, vehicle in enumerate(cover["vehicles"]):
        consumed = 0.0
        charged = set()

        def soc(lower=reserve, upper=B):
            # SOC = B - consumption + eta * all completed charges.
            add({j: eta for j in charged}, lower-(B-consumed), upper-(B-consumed))

        for mid in vehicle["movements"]:
            mode = modes[mid]
            if mode.kind == "depot":
                inbound = sum(leg.energy_kwh for leg in mode.legs[:mode.depot_split])
                outbound = sum(leg.energy_kwh for leg in mode.legs[mode.depot_split:])
                consumed += inbound
                soc()  # reach the depot with reserve
                charged.update(by_visit.get((vi, mid), ()))
                soc()  # charge without exceeding battery capacity
                consumed += outbound
                soc()
            else:
                consumed += sum(leg.energy_kwh for leg in mode.legs)
                soc()
                if mode.kind == "pullin":
                    charged.update(by_visit.get((vi, mid), ()))
                    soc(B, B)  # the native model restores a full terminal battery
            if mode.after is not None:
                consumed += trips[mode.after].energy_kwh
                soc()
    interval_count = len(compiled["intervals"])
    slack_count = interval_count if slack else 0
    if shared or slack:
        for k, interval in enumerate(compiled["intervals"]):
            coefficients = {j: 1.0 for j in by_interval.get(k, ())}
            if slack:
                coefficients[n+k] = -1.0
            add(coefficients, upper=interval["rate_kw"]*interval["hours"])
    inequalities, rhs = [], []
    for coefficients, lower, upper in rows:
        if math.isfinite(upper):
            inequalities.append((coefficients, 1.0))
            rhs.append(upper)
        if math.isfinite(lower):
            inequalities.append((coefficients, -1.0))
            rhs.append(-lower)
    matrix = lil_matrix((len(inequalities), n+slack_count), dtype=float)
    for row, (coefficients, sign) in enumerate(inequalities):
        for col, value in coefficients.items():
            matrix[row, col] = sign*value
    objective = [0.0]*n + [1.0]*slack_count
    bounds = [(0.0, cap) for cap in caps] + [(0.0, None)]*slack_count
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected:",
                                category=OptimizeWarning)
        result = linprog(objective, A_ub=matrix.tocsr(), b_ub=rhs,
                         bounds=bounds, method="highs", options={"threads": 1})
    overloads = []
    if slack and result.x is not None:
        overloads = [{"interval": k,
                      "start_min": interval["start"],
                      "end_min": interval["end"],
                      "base_grid_cap_kwh": interval["rate_kw"]*interval["hours"],
                      "extra_grid_kwh": float(result.x[n+k])}
                     for k, interval in enumerate(compiled["intervals"])
                     if result.x[n+k] > 1e-6]
    return {"status": int(result.status), "message": str(result.message),
            "feasible": result.status == 0,
            "minimum_total_extra_grid_kwh": float(result.fun) if slack and result.fun is not None else None,
            "overloaded_intervals": overloads,
            "charge_variables": n, "compiled_intervals": interval_count}


def diagnose():
    frozen = json.loads(STAGE2.read_text())
    replay_rows, failure_rows = [], []
    for name in CASES:
        group = frozen["design"]["groups"][name]
        case = lp.case_from_dict(group["case"])
        market = nh.Market(**group["markets"]["target"])
        assert case.identity() == group["case_identity"]
        assert market.identity() == group["market_identities"]["target"]
        for policy in POLICIES:
            folder = ATTEMPT / name / "state0" / policy
            repair_path, result_path = folder / "repair.json", folder / "result.json"
            repair = json.loads(repair_path.read_text())["result"]
            result = json.loads(result_path.read_text())
            independent_path = folder / "independent_replay.json"
            archived = json.loads(independent_path.read_text())
            assert repair["case_identity"] == case.identity()
            assert repair["market_identity"] == market.identity()
            assert repair["energy_relaxation"] is True and repair["charging_caps"] is True
            assert result["cover_policy"] == policy
            if repair["repair_status"] == "replayed":
                plan = repair["plan"]
                candidate_path = repair_path
                candidate_kind = "repaired"
                assert repair["replay"] == nr.replay_native(case, plan)
            else:
                candidate_path = folder / "fallback.json"
                fallback = json.loads(candidate_path.read_text())
                plan = fallback["plan"]
                candidate_kind = "source_fallback"
            replay = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            assert replay["replay_ok"] is True
            exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            plan_hash = nr.digest(plan)
            assert plan_hash == result["candidate_plan_hash"] == archived["plan_hash"]
            assert str(exact) == result["candidate_objective_exact"] == archived["objective_exact"]
            assert replay == archived["replay"]
            replay_rows.append({"case": name, "policy": policy,
                "candidate_kind": candidate_kind, "candidate_json": relative(candidate_path),
                "candidate_sha256": sha(candidate_path),
                "repair_json": relative(repair_path), "repair_sha256": sha(repair_path),
                "result_json": relative(result_path), "result_sha256": sha(result_path),
                "archived_independent_replay_json": relative(independent_path),
                "archived_independent_replay_sha256": sha(independent_path),
                "case_identity": case.identity(), "market_identity": market.identity(),
                "plan_hash": plan_hash, "replay_ok": True,
                "replay_matches_saved": True, "exact_cost": str(exact),
                "cost_matches_saved": True, "grid_load_kwh": replay["load"],
                "ops_cost": replay["ops_cost"]})
            cover = repair["cover"]
            assert cover["charging_caps"] is True
            individual = [analyze_route(group["case"], vehicle)
                          for vehicle in cover["vehicles"]]
            assert all(not vehicle["individually_rejected"] for vehicle in individual)
            separate = fixed_route_lp(case, cover)
            shared = fixed_route_lp(case, cover, shared=True)
            overload = fixed_route_lp(case, cover, slack=True)
            assert separate["feasible"] and overload["feasible"]
            assert shared["feasible"] == (repair["repair_status"] == "replayed")
            failure_rows.append({"case": name, "policy": policy,
                "repair_json": relative(repair_path), "repair_sha256": sha(repair_path),
                "case_identity": case.identity(),
                "selected_bus_count": cover["pullout_count"],
                "cover_milp_status": cover["status"],
                "cover_mip_gap": cover["mip_gap"],
                "fixed_charge_native_status": repair["native_stats"]["status"],
                "per_route_optimistic_capacity_passed": True,
                "individual_route_lp": separate,
                "shared_interval_lp": shared,
                "minimum_overload_lp": overload})
    common = {"frozen_json": relative(STAGE2), "frozen_sha256": sha(STAGE2),
              "attempt_frozen_json": relative(ATTEMPT / "frozen.json"),
              "attempt_frozen_sha256": sha(ATTEMPT / "frozen.json")}
    replay_report = {"schema": "egg-independent-charging-cap-replay-v1", **common,
        "method": "Fresh native physical replay and checked pricing start; exact Fraction operations cost plus native_hull.supply from frozen target market; compare plan hash, replay and cost to saved receipts.",
        "cells": replay_rows}
    diagnosis = {"schema": "egg-charging-cap-fixed-cover-diagnosis-v1", **common,
        "method": "Fixed-route continuous charging LP with native per-visit interval caps, SOC/reserve/full-terminal rows; compare without and with native shared interval grid rows. Slack LP minimizes sum of extra interval grid kWh. Numerical HiGHS results are diagnostic, not exact infeasibility certificates.",
        "scope": "Only the four selected covers; no conclusion about alternate covers, minimum physical bus count, or global fleet feasibility.",
        "cells": failure_rows}
    return replay_report, diagnosis


def markdown(report):
    lines = ["# Charging-cap attempt: fixed-cover failure diagnosis", "",
        "All four saved candidates pass fresh physical replay and exact target-cost",
        "recalculation. Three candidates are archived source fallbacks; the 2017",
        "cost-learned candidate is a new replayed repair.", "",
        "Each selected cover passes an optimistic per-route charging-window sweep.",
        "A small continuous LP also finds a charging schedule for every cover when",
        "each bus gets its own interval capacity. Adding the shared interval grid",
        "limit makes the three failed covers infeasible; the replayed 2017 cover",
        "remains feasible. This isolates shared charging competition in the fixed",
        "covers, consistent with the saved native fixed-charge statuses.", "",
        "| Case | Cover | Buses | Cover status | Native fixed-charge | Separate routes | Shared intervals | Minimum added grid energy (kWh) |",
        "|---|---|---:|---|---|---|---|---:|"]
    for cell in report["cells"]:
        cover_status = "optimal" if cell["cover_milp_status"] == 0 else "time-limit incumbent"
        added = cell["minimum_overload_lp"]["minimum_total_extra_grid_kwh"]
        lines.append(f"| {cell['case']} | {cell['policy']} | {cell['selected_bus_count']} | "
                     f"{cover_status} | {cell['fixed_charge_native_status']} | "
                     f"feasible | {'feasible' if cell['shared_interval_lp']['feasible'] else 'infeasible'} | "
                     f"{added:.3f} |")
    lines.extend(["", "The [JSON diagnosis](CHARGING_CAP_FAILURE_DIAGNOSIS.json) records",
        "the compiled interval overloads, statuses, source hashes, and limits of",
        "this numerical comparison. [Independent replay](INDEPENDENT_REPLAY_CHARGING_CAP.json)",
        "records the exact cost and plan identity checks. Reproduce both with:", "",
        "```sh", "PYTHONPATH=src python3 research-20260930/learning-campaign/diagnose_charging_cap_failures.py --check", "```", "",
        "The added-grid values come from numerical LPs; they are diagnostic",
        "estimates, not exact infeasibility certificates. No global fleet solve was",
        "run, and these results do not rule out other feasible covers.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved output without writing")
    args = parser.parse_args()
    replay, diagnosis = diagnose()
    outputs = {
        OUT / "INDEPENDENT_REPLAY_CHARGING_CAP.json":
            json.dumps(replay, indent=2, sort_keys=True) + "\n",
        OUT / "CHARGING_CAP_FAILURE_DIAGNOSIS.json":
            json.dumps(diagnosis, indent=2, sort_keys=True) + "\n",
        OUT / "CHARGING_CAP_FAILURE_DIAGNOSIS.md": markdown(diagnosis)}
    for path, content in outputs.items():
        if args.check:
            assert path.read_text() == content, f"Outdated output: {path}"
        else:
            path.write_text(content)
    print(f"Verified {len(replay['cells'])} candidate replays and "
          f"{len(diagnosis['cells'])} fixed-cover LP comparisons")


if __name__ == "__main__":
    main()
