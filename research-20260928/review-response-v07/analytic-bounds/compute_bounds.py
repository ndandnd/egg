"""Read-only exact energy-floor bounds and curated development-screen comparison.

Run from any directory: python3 compute_bounds.py --repo PATH > bounds.json
Only frozen inputs, independently reviewed summary values, curated result.json
assessments, and analysis.json are read. No model code or optimizer is called.
"""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import zipfile


FLOW = Path("result/sistig_cardinality_flow/20260927-attempt1")
SCREEN = Path("research-20260928/computational-results/attempt1")
ORIGINAL = Path("result/sistig_exact_hull_bound/20260927-uniform-price1/RESULT.json")
LATER_CELLS = Path("research-20260928/solver-baseline-comparison/results-attempt1/analysis/cells.csv")
CASES = ("public_depot15", "public_depot16")
SCREEN_CASES = ("synthetic_cyclic", "synthetic_multivisit", *CASES)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frac_list(items):
    return [Q(value) for value in items]


def cent_string(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    magnitude = abs(cents)
    return f"{sign}{magnitude // 100}.{magnitude % 100:02d}"


def outward_cents(lower: Q, upper: Q) -> list[str]:
    assert lower <= upper
    lo_cents = (100 * lower.numerator) // lower.denominator
    hi_cents = -((-100 * upper.numerator) // upper.denominator)
    return [cent_string(lo_cents), cent_string(hi_cents)]


def bounds_from_floor(flow_case, benchmark_case, flow_lower, market):
    case = benchmark_case["case"]
    assert flow_case == case
    assert Q(case["vehicle_cost"]) == 100
    assert Q(case["deadhead_cost_per_min"]) == 0
    assert Q(case["efficiency"]) == 1
    assert Q(case["battery_kwh"]) == 400
    assert Q(case["recharge_deadline_min"]) == 1800
    assert all(Q(trip["energy_kwh"]) >= 0 for trip in case["trips"])
    assert all(Q(leg["energy_kwh"]) >= 0 for mode in case["movements"] for leg in mode["legs"])

    a = frac_list(market["a"])
    b = frac_list(market["b"])
    assert len(a) == len(b) == 30
    assert len(set(b)) == 1 and b[0] > 0
    f, curvature = Q(case["vehicle_cost"]), b[0]
    service_energy = sum((Q(t["energy_kwh"]) for t in case["trips"]), Q(0))
    assert service_energy > Q(case["battery_kwh"])

    # The reviewed flow lower is for the state's common flat coefficient.
    # Its two-path relaxation has objective 2f + flat_a * energy because
    # monetary travel cost is zero and the buses return full at efficiency 1.
    flat_a = Q(benchmark_case["markets"][0]["a"][0])
    assert flat_a > 0
    assert all(Q(value) == flat_a for value in benchmark_case["markets"][0]["a"])
    emin = (flow_lower - 2 * f) / flat_a
    assert emin > service_energy

    # For a uniform test price p above every market intercept, the conjugate
    # of each quadratic is (p-a_t)^2/(2b). Maximize the resulting dual lower.
    periods = len(a)
    p = sum(a, Q(0)) / periods + curvature * emin / periods
    assert p >= max(a) and p > 0
    margin_three = 3 * f + p * service_energy - (2 * f + p * emin)
    assert margin_three > 0
    conjugate = sum(((p - intercept) ** 2 / (2 * curvature) for intercept in a), Q(0))
    lower = 2 * f + p * emin - conjugate
    return {
        "flow_lower_exact": str(flow_lower),
        "service_energy_exact": str(service_energy),
        "two_bus_energy_floor_exact": str(emin),
        "uniform_price_exact": str(p),
        "uniform_price_decimal": float(p),
        "max_intercept_decimal": float(max(a)),
        "three_plus_bus_margin_exact": str(margin_three),
        "three_plus_bus_margin_decimal": float(margin_three),
        "conjugate_exact": str(conjugate),
        "hull_lower_exact": str(lower),
        "hull_lower_decimal": float(lower),
        "hull_lower_outward_2dp": outward_cents(lower, lower)[0],
    }


def curated_result(z: zipfile.ZipFile, case: str, state: int, stage: str):
    path = f"{case}/state{state}/{stage}/result.json"
    return json.loads(z.read(path))


def supply_cost_and_conjugate(market, loads, prices):
    """Exact arithmetic on saved binary64 inputs; nonnegative supply domain."""
    cost, conjugate = Q(0), Q(0)
    for aa, bb, ll, pp in zip(market["a"], market["b"], loads, prices):
        a, b, load, price = Q(aa), Q(bb), Q(ll), Q(pp)
        assert b >= 0 and load >= 0
        cost += a * load + b * load * load / 2
        if b > 0:
            conjugate += max(Q(0), price - a) ** 2 / (2 * b)
        else:
            # A linear supply term has finite nonnegative-load conjugate
            # only when the posted price does not exceed its slope.
            if price > a:
                return cost, None
    return cost, conjugate


def screen_comparison(z, analysis, benchmark, analytic):
    rows = {(r["case"], r["state"], r["stage"]): r for r in analysis["rows"]}
    posthoc = {(r["case"], r["state"]): r for r in analysis["posthoc_two_column_public_cold"]}
    output = {}
    for case in SCREEN_CASES:
        for state in (0, 1):
            key = (case, state)
            planner = curated_result(z, case, state, "planner")
            response = curated_result(z, case, state, "response")
            hull = curated_result(z, case, state, "cold_hull")
            prices = json.loads(z.read(f"{case}/state{state}/response/prices.json"))
            assert planner["case"] == response["case"] == hull["case"] == case
            assert planner["state"] == response["state"] == hull["state"] == state
            assert all(r["assessment"]["complete_evidence"] for r in (planner, response, hull))
            stage_bounds = {}
            for name, result in (("planner", planner), ("response", response), ("cold_hull", hull)):
                selected = rows[(case, state, name)]
                assert result["assessment"]["bounds"] == [selected["lower_exact"], selected["upper_exact"]]
                stage_bounds[name] = {
                    "lower_exact": selected["lower_exact"],
                    "upper_exact": selected["upper_exact"],
                    "lower_decimal": float(Q(selected["lower_exact"])),
                    "upper_decimal": float(Q(selected["upper_exact"])),
                    "status": selected["outcome"],
                    "outward_2dp": outward_cents(Q(selected["lower_exact"]), Q(selected["upper_exact"])),
                }

            market = benchmark["cases"][case]["markets"][state]
            loads = planner["assessment"]["replay"]["load"]
            ops = Q(planner["assessment"]["replay"]["ops_cost"])
            assert len(loads) == len(prices) == len(market["a"])
            assert planner["assessment"]["replay"]["replay_ok"]
            assert response["assessment"]["replay"]["replay_ok"]
            gradient_residual = max(abs(price - (a + b * load)) for price, a, b, load in
                                    zip(prices, market["a"], market["b"], loads))
            assert gradient_residual < 1e-12
            gradient_binary_residual = max(abs(Q(price) - (Q(a) + Q(b) * Q(load))) for
                                           price, a, b, load in zip(prices, market["a"],
                                                                    market["b"], loads))
            assert gradient_binary_residual < Q(1, 10**12)
            posted_bill = ops + sum((Q(price) * Q(load) for price, load in zip(prices, loads)), Q(0))
            v_lower = Q(stage_bounds["response"]["lower_exact"])
            v_upper = Q(stage_bounds["response"]["upper_exact"])
            regret = [posted_bill - v_upper, posted_bill - v_lower]
            supply_cost, conjugate = supply_cost_and_conjugate(market, loads, prices)
            assert conjugate is not None
            incumbent_system_cost = ops + supply_cost
            supply_loc = supply_cost - (posted_bill - ops) + conjugate
            assert supply_loc >= 0
            response_fenchel_lower = v_lower - conjugate
            assert incumbent_system_cost - response_fenchel_lower == regret[1] + supply_loc

            d_lower = Q(stage_bounds["planner"]["lower_exact"])
            d_upper = Q(stage_bounds["planner"]["upper_exact"])
            ch_lower_screen = Q(stage_bounds["cold_hull"]["lower_exact"])
            ch_upper_screen = Q(stage_bounds["cold_hull"]["upper_exact"])
            ch_lower_exact = (Q(analytic[case][str(state)]["hull_lower_exact"])
                              if case in analytic else None)
            ch_lower_native = max(ch_lower_screen, response_fenchel_lower)
            ch_upper_native = min(ch_upper_screen, d_upper)
            d_lower_native = max(d_lower, ch_lower_native)
            assert ch_lower_native <= ch_upper_native and d_lower_native <= d_upper
            native_gap_lower = max(Q(0), d_lower_native - ch_upper_native)
            native_gap_upper = d_upper - ch_lower_native
            ch_lower_combined = max(ch_lower_native, ch_lower_exact) if ch_lower_exact is not None else ch_lower_native
            d_lower_combined = max(d_lower, ch_lower_combined)
            assert ch_lower_combined <= ch_upper_native and d_lower_combined <= d_upper
            mixed_gap_lower = max(Q(0), d_lower_combined - ch_upper_native)
            mixed_gap_upper = d_upper - ch_lower_combined
            posthoc_upper = Q(posthoc[key]["posthoc_upper_exact"]) if key in posthoc else None
            if posthoc_upper is not None:
                assert posthoc_upper <= ch_upper_screen
            raw_gap_lower_screen = d_lower - ch_upper_screen
            raw_gap_lower_posthoc = d_lower - posthoc_upper if posthoc_upper is not None else None

            output[f"{case}_state{state}"] = {
                "case_identity": benchmark["cases"][case]["case_identity"],
                "development_screen": stage_bounds,
                "response_price_matches_planner_gradient_max_abs": gradient_residual,
                "response_price_vs_exact_binary_gradient_max_abs": float(gradient_binary_residual),
                "saved_binary_supply_conjugate_exact": str(conjugate),
                "saved_binary_supplier_loc_exact": str(supply_loc),
                "saved_binary_supplier_loc_decimal": float(supply_loc),
                "response_fenchel_hull_lower_exact": str(response_fenchel_lower),
                "response_fenchel_hull_lower_decimal": float(response_fenchel_lower),
                "response_fenchel_hull_lower_outward_2dp": outward_cents(response_fenchel_lower, response_fenchel_lower)[0],
                "named_planner_incumbent_system_cost_exact": str(incumbent_system_cost),
                "incumbent_cost_minus_response_fenchel_exact": str(incumbent_system_cost - response_fenchel_lower),
                "named_planner_incumbent_posted_bill_exact": str(posted_bill),
                "named_planner_incumbent_regret_exact": [str(v) for v in regret],
                "named_planner_incumbent_regret_decimal": [float(v) for v in regret],
                "named_planner_incumbent_regret_outward_2dp": outward_cents(*regret),
                "analytic_hull_lower_decimal": float(ch_lower_exact) if ch_lower_exact is not None else None,
                "combined_analytic_and_screen_hull_lower_decimal": float(ch_lower_combined),
                "same_screen_signed_gap_lower_decimal": float(raw_gap_lower_screen),
                "same_screen_nonnegative_gap_lower_decimal": float(max(Q(0), raw_gap_lower_screen)),
                "native_combined": {
                    "physical_lower_exact": str(d_lower_native),
                    "physical_upper_exact": str(d_upper),
                    "hull_lower_exact": str(ch_lower_native),
                    "hull_upper_exact": str(ch_upper_native),
                    "physical_outward_2dp": outward_cents(d_lower_native, d_upper),
                    "hull_outward_2dp": outward_cents(ch_lower_native, ch_upper_native),
                    "gap_exact": [str(native_gap_lower), str(native_gap_upper)],
                    "gap_outward_2dp": outward_cents(native_gap_lower, native_gap_upper),
                },
                "mixed_exact_floor_and_native": {
                    "physical_lower_exact": str(d_lower_combined),
                    "physical_upper_exact": str(d_upper),
                    "hull_lower_exact": str(ch_lower_combined),
                    "hull_upper_exact": str(ch_upper_native),
                    "physical_outward_2dp": outward_cents(d_lower_combined, d_upper),
                    "hull_outward_2dp": outward_cents(ch_lower_combined, ch_upper_native),
                    "gap_exact": [str(mixed_gap_lower), str(mixed_gap_upper)],
                    "gap_outward_2dp": outward_cents(mixed_gap_lower, mixed_gap_upper),
                },
                "posthoc_two_column_hull_upper_decimal": float(posthoc_upper) if posthoc_upper is not None else None,
                "posthoc_signed_gap_lower_decimal": float(raw_gap_lower_posthoc) if raw_gap_lower_posthoc is not None else None,
                "posthoc_is_outside_frozen_budget": True if posthoc_upper is not None else None,
                "claim_scope": "Development screen and named incumbent at saved machine-rounded prices; native endpoints conditional, exact floor (public only) ideal stored-input, no certified positive public gap or optimum regret.",
            }
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.repo.resolve()
    flow_frozen_path = repo / FLOW / "frozen.json"
    flow_summary_path = repo / FLOW / "summary.json"
    screen_zip_path = repo / SCREEN / "scientific_evidence.zip"
    analysis_path = repo / SCREEN / "analysis.json"
    original_path = repo / ORIGINAL
    later_cells_path = repo / LATER_CELLS
    flow_frozen = json.loads(flow_frozen_path.read_text())
    flow_summary = json.loads(flow_summary_path.read_text())
    analysis = json.loads(analysis_path.read_text())
    original = json.loads(original_path.read_text())
    assert flow_summary["status"] == "completed"
    assert flow_summary["native_optimizer_invoked"] is False
    assert len(flow_frozen["cases"]) == len(flow_summary["lower_exact"]) == 2
    with zipfile.ZipFile(screen_zip_path) as z:
        benchmark = json.loads(z.read("frozen.json"))
        analytic = {}
        for i, case in enumerate(CASES):
            bcase = benchmark["cases"][case]
            assert flow_frozen["case_identities"][i] == bcase["case_identity"]
            assert flow_frozen["cases"][i] == bcase["case"]
            analytic[case] = {}
            for state, market in enumerate(bcase["markets"]):
                analytic[case][str(state)] = bounds_from_floor(
                    flow_frozen["cases"][i], bcase, Q(flow_summary["lower_exact"][i]), market)
        assert analytic["public_depot15"]["0"]["hull_lower_exact"] == original["CH_lower"]
        comparisons = screen_comparison(z, analysis, benchmark, analytic)
    with later_cells_path.open(newline="") as stream:
        later_rows = list(csv.DictReader(stream))
    later_context = {}
    for case in CASES:
        matched = [r for r in later_rows if r["case"] == case and r["state"] == "1"
                   and r["arm"] == "qp_cache_feasible_hull"]
        assert len(matched) == 1 and matched[0]["outcome"] == "budget_exhausted"
        row = matched[0]
        lower = Q(row["lower_exact"])
        analytic_lower = Q(analytic[case]["1"]["hull_lower_exact"])
        later_context[case] = {
            "later_campaign_lower_exact": str(lower),
            "later_campaign_lower_decimal": float(lower),
            "later_campaign_upper_decimal": float(Q(row["upper_exact"])),
            "later_campaign_interval_outward_2dp": outward_cents(lower, Q(row["upper_exact"])),
            "analytic_minus_later_lower_decimal": float(analytic_lower - lower),
            "namespace": "separate ordered solver-baseline campaign; no merged timing or interval claim",
        }
    report = {
        "status": "exact analytic floor PASS; screen comparison conditional",
        "inputs_sha256": {str(path.relative_to(repo)): digest(path) for path in
                          (flow_frozen_path, flow_summary_path, screen_zip_path, analysis_path, original_path, later_cells_path)},
        "screen_source_commit": benchmark["source_commit"],
        "method": "Uniform Fenchel price with two-bus flow energy floor, one-bus obstruction, and explicit three-plus-bus margin.",
        "analytic_bounds": analytic,
        "development_screen_comparison": comparisons,
        "later_campaign_context": later_context,
        "excluded_conditional_423_27": "The retrospective native flat optimum is solver/tolerance conditional and is not an exact ideal two-bus energy floor; it is not used in any exact bound.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
