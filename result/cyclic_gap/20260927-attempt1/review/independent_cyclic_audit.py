#!/usr/bin/env python3
"""Independent, standard-library exact audit; no imports from the experiment.

The two partitions are proved in CYCLIC_CANDIDATE_CHECK.md. Optimization here
uses the three projected physical vertices and quadratic interpolation along
their edges, rather than the author's closed-form minimizer implementation.
"""
import argparse
import copy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def rational(item):
    require(isinstance(item, dict) and set(item) == {"exact", "value"},
            "rational leaf schema")
    require(isinstance(item["exact"], str), "exact value must be a string")
    value = Q(item["exact"])
    require(type(item["value"]) in (int, float), "display value type")
    require(item["value"] == float(value), "exact/display mismatch")
    return value


def check_leaves(obj):
    if isinstance(obj, dict):
        if "exact" in obj or "value" in obj:
            rational(obj)
            return 1
        return sum(check_leaves(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(check_leaves(v) for v in obj)
    return 0


def leaf(item, value, name):
    require(rational(item) == value, name)


def supply(load, intercept):
    return intercept * load[0] + sum(z*z for z in load) / 10


def interpolate(first, second, weight):
    return tuple((1-weight)*a + weight*b for a, b in zip(first, second))


def best_edge(first, second, intercept):
    # Points are (intrinsic cost, early energy, terminal energy).
    def objective(t):
        point = interpolate(first, second, t)
        return point[0] + supply(point[1:], intercept)
    y0, ym, y1 = objective(Q(0)), objective(Q(1, 2)), objective(Q(1))
    quadratic = 2 * (y1 + y0 - 2*ym)
    linear = y1 - y0 - quadratic
    candidates = [Q(0), Q(1)]
    if quadratic > 0:
        stationary = -linear / (2*quadratic)
        if 0 <= stationary <= 1:
            candidates.append(stationary)
    weight = min(candidates, key=lambda t: (objective(t), t))
    return objective(weight), interpolate(first, second, weight)


def replay(schedule, counters):
    buses = schedule["buses"]
    require(len(buses) in (1, 2), "used bus count")
    services = []
    aggregate = [Q(0), Q(0)]
    for bus in buses:
        duty = bus["services"]
        require(duty in (["A"], ["B"], ["A", "B"]), "duty identity/order")
        services.extend(duty)
        early, terminal = rational(bus["early"]), rational(bus["terminal"])
        require(0 <= early <= 10 and 0 <= terminal <= 30, "individual power")
        soc = Q(20)
        expected = [soc]
        soc -= 15 * ("A" in duty)
        expected.append(soc)
        soc += early
        expected.append(soc)
        soc -= 15 * ("B" in duty)
        expected.append(soc)
        soc += terminal
        expected.append(soc)
        require(all(0 <= x <= 20 for x in expected), "event SOC capacity")
        require(soc == 20, "cyclic terminal SOC")
        require([rational(x) for x in bus["soc_after_events"]] == expected,
                "saved SOC differs from raw event replay")
        aggregate[0] += early
        aggregate[1] += terminal
        counters["bus_trajectories"] += 1
        counters["soc_event_values"] += len(expected)
    require(sorted(services) == ["A", "B"], "mandatory service coverage")
    require(aggregate[0] <= 10 and aggregate[1] <= 30, "shared power")
    require(sum(aggregate) == 30, "net energy conservation")
    require([rational(x) for x in schedule["load"]] == aggregate, "saved aggregate load")
    leaf(schedule["initial_energy"], 20*len(buses), "initial energy")
    leaf(schedule["terminal_energy"], 20*len(buses), "terminal energy")
    leaf(schedule["total_recharge"], 30, "recharge amount")
    counters["complete_schedules"] += 1
    return len(buses), tuple(aggregate)


def check_case(case, counters):
    f, a = rational(case["fleet_cost"]), rational(case["early_intercept"])
    require(f > 0, "positive used-bus cost")
    vertices = [(f, Q(10), Q(20)), (2*f, Q(0), Q(30)),
                (2*f, Q(10), Q(20))]
    one_value = f + supply((Q(10), Q(20)), a)
    two_value, two_point = best_edge(vertices[1], vertices[2], a)
    edges = [(vertices[i], vertices[j]) for i in range(3) for j in range(i+1, 3)]
    # Every interior point with a given x costs at least the lower-edge point;
    # supply cost only depends on x and f>0. Therefore boundary minimization is complete.
    hull_value, hull_point = min((best_edge(u, v, a) for u, v in edges),
                                key=lambda v: (v[0], v[1]))
    physical = min(one_value, two_value)
    weight = (2*f - hull_point[0])/f
    for key, value in [("physical_one", one_value), ("physical_two", two_value),
                       ("physical", physical), ("convexified", hull_value),
                       ("gap", physical-hull_value), ("one_bus_weight", weight),
                       ("two_bus_optimal_early", two_point[1])]:
        leaf(case[key], value, key)
    require([rational(z) for z in case["hull_load"]] == list(hull_point[1:]),
            "hull optimum load")
    require(physical >= hull_value, "nonnegative planning gap")
    require(len(case["physical_witnesses"]) == 2, "two physical branch witnesses")
    for witness, buses, value in zip(case["physical_witnesses"], [1, 2],
                                    [one_value, two_value]):
        actual_buses, load = replay(witness, counters)
        require(actual_buses == buses, "physical branch identity")
        require(buses*f + supply(load, a) == value, "physical witness cost")
    components = case["hull_components"]
    require(len(components) == 2, "hull component count")
    total_weight = Q(0)
    mean_cost = Q(0)
    mean_load = [Q(0), Q(0)]
    actual_one_weight = Q(0)
    for comp in components:
        w = rational(comp["weight"])
        require(0 <= w <= 1, "convex weights")
        buses, load = replay(comp["schedule"], counters)
        total_weight += w
        mean_cost += w*buses*f
        actual_one_weight += w*(buses == 1)
        mean_load = [old+w*new for old, new in zip(mean_load, load)]
        counters["positive_components"] += (w > 0)
    require(total_weight == 1, "weights sum to one")
    require(actual_one_weight == weight, "mixture one-bus weight")
    require(mean_cost == hull_point[0] and tuple(mean_load) == hull_point[1:],
            "mixture reconstructs hull point")
    require(mean_cost + supply(mean_load, a) == hull_value, "mixture objective")
    return (f, a), physical-hull_value


def check_prices(prices, nominal):
    f, a = Q(7), Q(4)
    loads = [Q(27, 4), Q(93, 4)]
    p = [a + loads[0]/5, loads[1]/5]
    require([rational(z) for z in prices["hull_price"]] == p, "hull gradient price")
    vertices = [(1, (Q(10), Q(20))), (2, (Q(0), Q(30))),
                (2, (Q(10), Q(20)))]
    def bill(n, load, price):
        return n*f + sum(x*y for x, y in zip(load, price))
    def response(price):
        return min(bill(n, load, price) for n, load in vertices)
    v = response(p)
    # Independent separable nonnegative-load conjugate, b/2=1/10.
    conjugate = Q(5, 2) * (max(Q(0), p[0]-a)**2 + max(Q(0), p[1])**2)
    leaf(prices["fleet_response_value"], v, "hull-price fleet response")
    leaf(prices["supply_conjugate"], conjugate, "nonnegative-load supply conjugate")
    leaf(prices["dual_value"], v-conjugate, "dual value")
    require(v-conjugate == rational(nominal["convexified"]), "strong duality accounting")
    records = prices["physical_branch_optima"]
    require(len(records) == 2, "price branch count")
    for record, n, load in zip(records, [1, 2], [(Q(10), Q(20)), (Q(5), Q(25))]):
        require(record["buses"] == n, "price branch bus count")
        require([rational(x) for x in record["load"]] == list(load), "price branch load")
        own = [a+load[0]/5, load[1]/5]
        require([rational(x) for x in record["own_price"]] == own, "own marginal price")
        regret = bill(n, load, own)-response(own)
        fleet_loc = bill(n, load, p)-v
        supplier_loc = supply(load, a)-sum(x*y for x, y in zip(p, load))+conjugate
        leaf(record["own_price_regret"], regret, "own-price regret")
        leaf(record["fleet_LOC_at_hull_price"], fleet_loc, "fleet LOC")
        leaf(record["supply_LOC_at_hull_price"], supplier_loc, "supply LOC")
        require(fleet_loc >= 0 and supplier_loc >= 0, "LOC nonnegativity")
        require(fleet_loc+supplier_loc == n*f+supply(load, a)-(v-conjugate),
                "total LOC primal-dual accounting")


def audit(result):
    count = {"complete_schedules": 0, "bus_trajectories": 0,
             "soc_event_values": 0, "positive_components": 0}
    count["rational_leaves"] = check_leaves(result)
    expected = {(Q(f), Q(a)) for f in [1, 3, 7, 10, 15, 20] for a in [0, 2, 4, 6]}
    require(len(result["cases"]) == 24, "complete Cartesian grid count")
    keys, gaps = [], []
    for case in result["cases"]:
        key, gap = check_case(case, count)
        keys.append(key)
        gaps.append(gap)
    require(len(set(keys)) == 24 and set(keys) == expected, "complete unique Cartesian grid")
    nominal_key, nominal_gap = check_case(result["nominal"], count)
    require(nominal_key == (Q(7), Q(4)), "nominal parameter identity")
    index = keys.index(nominal_key)
    require(result["nominal"] == result["cases"][index], "nominal/grid identity")
    require(nominal_gap == Q(169, 80), "nominal exact gap")
    check_prices(result["nominal_prices"], result["nominal"])
    count.update({"grid_cases": 24, "positive_gap_cases": sum(x > 0 for x in gaps),
                  "zero_gap_cases": sum(x == 0 for x in gaps),
                  "nominal_gap": str(nominal_gap), "nominal_physical": "97",
                  "nominal_convexified": "7591/80"})
    return count


def corrupt_controls(original):
    def alter(node):
        changed = Q(node["exact"])+1
        node.update(exact=str(changed), value=float(changed))
    def field(path):
        def change(r):
            node = r
            for p in path:
                node = node[p]
            alter(node)
        return change
    controls = {
        "physical_cost": field(["cases", 0, "physical"]),
        "event_SOC": field(["cases", 0, "physical_witnesses", 0, "buses", 0,
                             "soc_after_events", 2]),
        "convex_weight": field(["cases", 0, "hull_components", 1, "weight"]),
        "hull_price": field(["nominal_prices", "hull_price", 0]),
        "fleet_LOC": field(["nominal_prices", "physical_branch_optima", 0,
                             "fleet_LOC_at_hull_price"]),
        "supply_LOC": field(["nominal_prices", "physical_branch_optima", 0,
                              "supply_LOC_at_hull_price"]),
        "display_only": lambda r: r["cases"][0]["gap"].update(value=999),
        "missing_case": lambda r: r["cases"].pop(),
        "duplicate_case": lambda r: r["cases"].__setitem__(1, copy.deepcopy(r["cases"][0])),
        "mandatory_coverage": lambda r: r["cases"][0]["physical_witnesses"][0]
                                           ["buses"][0].update(services=["A"]),
    }
    outcomes = {}
    for name, mutate in controls.items():
        result = copy.deepcopy(original)
        mutate(result)
        try:
            audit(result)
        except (AssertionError, KeyError, ValueError, ZeroDivisionError) as e:
            outcomes[name] = {"rejected": True, "reason": str(e)}
        else:
            raise AssertionError("corruption not rejected: " + name)
    return outcomes


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    raw = args.result.read_bytes()
    result = json.loads(raw)
    frozen_head = "7bf913a87a455e77a4e309eaa58dfcf0b10f76c0"
    require(result["head"] == frozen_head, "frozen execution head")
    provenance = {}
    for field_name, relpath in [
        ("source_sha256", "src/experiments/cyclic_gap.py"),
        ("protocol_sha256", "doc/CYCLIC_GAP_PROTOCOL_20260927.md"),
    ]:
        source = subprocess.check_output(["git", "show", frozen_head+":"+relpath],
                                         cwd=args.repo)
        actual = digest(source)
        require(result[field_name] == actual, "frozen " + field_name)
        provenance[field_name] = actual
    report = {"status": "PASS", "method": "independent exact vertex-edge and raw-event reconstruction",
              "no_author_imports": True, "no_solver": True, "frozen_head": frozen_head,
              "result_sha256": digest(raw), "auditor_sha256": digest(Path(__file__).read_bytes()),
              "provenance": provenance, "checks": audit(result),
              "corruption_controls": corrupt_controls(result)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
