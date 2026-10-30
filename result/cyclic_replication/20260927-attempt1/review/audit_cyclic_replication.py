#!/usr/bin/env python3
"""Independent exact audit of cyclic-replication JSON; standard library only.

No author imports and no optimizer. Frozen Git files are hashed, never executed.
Reconstruction uses service counts, connector schedules, scalar derivatives,
the three-vertex complete hull, and complete linear endpoint responses.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
FROZEN = "ce84e9e62b8e3f33d32010d381fd845415eff458"
RAW_SHA256 = "87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a"
GRID = list(range(1, 81))+[120, 200, 400, 401, 1000, 1001]
COUNTS = Counter()


def require(value, message):
    if not value:
        raise AssertionError(message)


def equal(a, b, message):
    require(a == b, f"{message}: {a!r} != {b!r}")


def decode(value):
    if isinstance(value, dict) and ("exact" in value or "value" in value):
        require(set(value) == {"exact", "value"}, "rational encoding fields")
        q = Q(value["exact"])
        require(math.isfinite(value["value"]), "nonfinite decimal display")
        equal(value["value"], float(q), "rational/decimal agreement")
        COUNTS["rational_leaves"] += 1
        return q
    if isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def encode(value):
    if isinstance(value, Q):
        return {"exact": str(value), "value": float(value)}
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def electricity(n, early, terminal):
    require(early >= 0 and terminal >= 0, "nonnegative grid load")
    return 4*early+(early*early+terminal*terminal)/(10*n)


def objective(n, paired, early):
    return 7*(2*n-paired)+electricity(n, early, 30*n-early)


def scalar_minimum(n, paired):
    # Derive the stationary point of H = 104n - 7m - 2x + x^2/(5n).
    lo, hi = Q(10*paired), Q(10*n)
    stationary = -Q(-2)/(2*Q(1, 5*n))
    candidates = [lo, hi]
    if lo <= stationary <= hi:
        candidates.append(stationary)
    val, x = min((objective(n, paired, x), x) for x in candidates)
    return x, val


def replay_groups(n, paired, early, groups):
    require(type(n) is int and type(paired) is int and n >= 1 and 0 <= paired <= n, "integer service/partition counts")
    require(Q(10*paired) <= early <= 10*n, "partition early interval")
    expected_counts = {("A", "B"): paired, ("A",): n-paired, ("B",): n-paired}
    expected_counts = {k: v for k, v in expected_counts.items() if v}
    require(len(groups) == len(expected_counts), "physical group count")
    seen, aggregate_early, aggregate_terminal, buses = {}, Q(0), Q(0), 0
    for g in groups:
        services, count = tuple(g["services"]), g["count"]
        require(services in expected_counts and services not in seen, "physical service group")
        require(type(count) is int and count > 0, "positive integer group multiplicity")
        equal(count, expected_counts[services], "group multiplicity")
        e, t = g["early"], g["terminal"]
        require(0 <= e <= 10 and 0 <= t <= 30, "individual charger power")
        if "A" not in services:
            equal(e, Q(0), "full B-only bus cannot charge early")
        states = [Q(20)]
        states.append(states[-1]-(15 if "A" in services else 0))
        states.append(states[-1]+e)
        states.append(states[-1]-(15 if "B" in services else 0))
        states.append(states[-1]+t)
        equal(g["soc"], states, "battery event reconstruction")
        require(all(0 <= s <= 20 for s in states) and states[-1] == 20, "SOC bounds and replenishment")
        aggregate_early += count*e
        aggregate_terminal += count*t
        buses += count
        seen[services] = g
        COUNTS["SOC_group_events"] += len(states)
        COUNTS["SOC_bus_events_by_multiplicity"] += count*len(states)
    equal(sum(g["count"] for g in groups if "A" in g["services"]), n, "A coverage")
    equal(sum(g["count"] for g in groups if "B" in g["services"]), n, "B coverage")
    equal(buses, 2*n-paired, "used bus count")
    equal(aggregate_early, early, "aggregate early replay")
    equal(aggregate_terminal, 30*n-early, "aggregate terminal replay")
    require(aggregate_early <= 10*n and aggregate_terminal <= 30*n, "shared power")
    equal(aggregate_early+aggregate_terminal, Q(30*n), "whole fleet cyclic recharge")

    # n distinct A buses occupy at most n early connectors for the full hour.
    early_connectors = sum(g["count"] for g in groups if "A" in g["services"])
    equal(early_connectors, n, "finite early connectors")
    # m terminal connectors charge one A+B bus at constant 20 kW; each of the
    # other n-m connectors serves one A-only/B-only pair consecutively.
    terminal_peak = Q(0)
    if paired:
        g = seen[("A", "B")]
        equal((g["early"], g["terminal"]), (Q(10), Q(20)), "paired bus exact charging")
        terminal_peak += paired*g["terminal"]
    if paired < n:
        a, b = seen[("A",)], seen[("B",)]
        connector_power = a["terminal"]+b["terminal"]
        require(0 < connector_power <= 30, "single terminal connector rating")
        switch = a["terminal"]/connector_power
        require(0 <= switch <= 1, "terminal switch within window")
        # A: [3,3+switch]; B: [3+switch,4]. No overlapping plug use.
        equal(connector_power*switch, a["terminal"], "A terminal session energy")
        equal(connector_power*(1-switch), b["terminal"], "B terminal session energy")
        terminal_peak += (n-paired)*connector_power
        COUNTS["sequential_terminal_pair_templates"] += 1
    equal(paired+(n-paired), n, "finite terminal connectors")
    equal(terminal_peak, aggregate_terminal, "constant aggregate terminal power")
    require(terminal_peak <= 30*n, "terminal instantaneous shared power")
    COUNTS["physical_templates"] += 1
    return {"early": aggregate_early, "terminal": aggregate_terminal, "used_buses": buses}


def construct(n, paired, early):
    # Independent sufficiency witness for EVERY recorded branch optimum and
    # both endpoints, not just the physical winner templates stored by author.
    extra = (early-10*paired)/(n-paired) if paired < n else Q(0)
    specs = [(paired, ["A", "B"], Q(10), Q(20)),
             (n-paired, ["A"], extra, 15-extra),
             (n-paired, ["B"], Q(0), Q(15))]
    groups = []
    for count, services, e, t in specs:
        if not count:
            continue
        a = Q(20)-(15 if "A" in services else 0)
        b = a+e
        c = b-(15 if "B" in services else 0)
        groups.append({"count": count, "services": services, "early": e,
                       "terminal": t, "soc": [Q(20), a, b, c, c+t]})
    replay_groups(n, paired, early, groups)
    return groups


def response(n, prices):
    # A linear objective reaches its minimum at an interval endpoint. All
    # endpoints were independently constructed with finite connectors.
    candidates = []
    for paired in range(n+1):
        for early in {Q(10*paired), Q(10*n)}:
            value = 7*(2*n-paired)+prices[0]*early+prices[1]*(30*n-early)
            candidates.append((value, paired, early))
    minimum = min(v for v, _, _ in candidates)
    COUNTS["linear_endpoint_evaluations"] += len(candidates)
    return minimum, [(m, x) for v, m, x in candidates if v == minimum]


def conjugate(n, prices):
    # Supremum over NONNEGATIVE independent grid supplies, not fleet-feasible
    # loads. The fixed total 30n belongs to the fleet, not to the supplier.
    supply = [max(Q(0), (p-base)*5*n) for p, base in zip(prices, (4, 0))]
    val = sum(p*q for p, q in zip(prices, supply))-electricity(n, *supply)
    return val, supply


def audit_case(c):
    n = c["n"]
    require(type(n) is int and n in GRID, "frozen case n")
    rows = c["branch_optima"]
    equal([r["m"] for r in rows], list(range(n+1)), "complete partition coverage")
    endpoints, branch_values = [], []
    for row in rows:
        m = row["m"]
        require(type(m) is int, "integer paired count")
        x, value = scalar_minimum(n, m)
        equal(row["x"], x, "continuous branch minimizer")
        equal(row["cost"], value, "continuous branch minimum cost")
        branch_values.append(value)
        # The supporting half-space defines the lower triangle boundary.
        for point in (Q(10*m), Q(10*n), x):
            ops = Q(7*(2*n-m))
            require(ops+Q(7, 10)*point >= 14*n and ops <= 14*n, "complete hull inclusion")
            construct(n, m, point)
        endpoints.extend([(Q(10*m), Q(7*(2*n-m))), (Q(10*n), Q(7*(2*n-m)))])
        COUNTS["branch_minima"] += 1
    physical = min(branch_values)
    equal(c["physical"], physical, "physical global minimum")
    expected_winners = [m for m, value in enumerate(branch_values) if value == physical]
    equal([w["m"] for w in c["physical_optimizers"]], expected_winners, "ALL physical optimizer ties")

    # Three vertices (0,14n),(10n,7n),(10n,14n) are physically present; all
    # interval points lie in their triangle. Hence this is the COMPLETE hull.
    require(all(v in endpoints for v in [(Q(0), Q(14*n)), (Q(10*n), Q(7*n)), (Q(10*n), Q(14*n))]), "physical complete-hull vertices")
    equal(c["hull_vertices"], [[Q(0), Q(14*n)], [Q(10*n), Q(7*n)]], "recorded lower hull boundary")
    # H_CH(x)=104n-(27/10)x+x^2/(5n). Minimize its scalar polynomial.
    hx = Q(27, 10)/(2*Q(1, 5*n))
    require(0 < hx < 10*n, "interior hull minimizer")
    hc = 14*n-Q(7, 10)*hx
    ch = hc+electricity(n, hx, 30*n-hx)
    equal(c["hull_load"], [hx, 30*n-hx], "hull aggregate load")
    equal(c["hull_intrinsic_cost"], hc, "hull fleet cost")
    equal(c["convexified"], ch, "hull minimum cost")
    equal(ch, Q(7591*n, 80), "hull closed form")
    weight = hx/(10*n)
    equal(weight*7*n+(1-weight)*14*n, hc, "hull component intrinsic cost")
    equal(weight*20*n+(1-weight)*30*n, 30*n-hx, "hull component terminal load")
    construct(n, n, Q(10*n))
    construct(n, 0, Q(0))
    equal(c["gap"], physical-ch, "planning gap")
    equal(c["relative_gap"], (physical-ch)/ch, "relative gap denominator CH")
    require(Q(0) <= physical-ch <= Q(5, n), "absolute gap 5/n bound")
    hp = [4+hx/(5*n), (30*n-hx)/(5*n)]
    equal(c["hull_price"], hp, "hull marginal price")
    equal(hp, [Q(107, 20), Q(93, 20)], "constant hull marginal price")
    hv, _ = response(n, hp)
    hstar, support = conjugate(n, hp)
    equal(c["hull_response"], hv, "complete fleet hull-price response")
    equal(c["hull_conjugate"], hstar, "supplier conjugate")
    equal(hv-hstar, ch, "hull strong dual identity")
    equal(support, [hx, 30*n-hx], "supplier optimal supply at hull price")

    records = []
    for w in c["physical_optimizers"]:
        m, x = w["m"], w["early"]
        equal(x, rows[m]["x"], "optimizer early load")
        equal(x, Q(10*m), "optimizer minimum early endpoint")
        delta = Q(m)-Q(27*n, 40)
        equal(w["delta"], delta, "optimizer rounding residual")
        require(abs(delta) <= Q(1, 2), "nearest integer optimizer")
        equal(physical-ch, 20*delta*delta/n, "quadratic rounding gap")
        p = [4+x/(5*n), (30*n-x)/(5*n)]
        equal(w["price"], p, "own marginal price")
        private_value = 7*(2*n-m)+p[0]*x+p[1]*(30*n-x)
        best, replies = response(n, p)
        regret = private_value-best
        equal(w["own_price_regret"], regret, "complete own-price regret")
        closed = 40*Q(m, n)*delta if delta >= 0 else 40*(1-Q(m, n))*(-delta)
        equal(regret, closed, "closed-form own-price regret")
        require(0 <= regret <= 20, "uniform absolute regret bound")
        if delta > 0:
            require(all(k == 0 for k, _ in replies), "positive residual response partition")
        elif delta < 0:
            require(all(k == n for k, _ in replies), "negative residual response partition")
        else:
            equal({k for k, _ in replies}, set(range(n+1)), "zero residual response indifference")
        own_conjugate, own_supply = conjugate(n, p)
        equal(own_supply, [x, 30*n-x], "own-price supplier optimality")
        equal(electricity(n, x, 30*n-x)-sum(a*b for a, b in zip(p, own_supply))+own_conjugate, Q(0), "own-price supply LOC zero")
        hbill = hp[0]*x+hp[1]*(30*n-x)
        fleet_loc = 7*(2*n-m)+hbill-hv
        supply_loc = electricity(n, x, 30*n-x)-hbill+hstar
        equal(w["fleet_LOC_at_hull_price"], fleet_loc, "common-price fleet LOC")
        equal(w["supply_LOC_at_hull_price"], supply_loc, "common-price supply LOC")
        equal((fleet_loc, supply_loc), (Q(0), physical-ch), "common-price LOC decomposition")
        equal(w["regret_per_used_bus"], regret/(2*n-m), "regret actual used-bus denominator")
        equal(w["regret_over_physical_cost"], regret/physical, "relative regret denominator physical")
        witness = w["witness"]
        replay = replay_groups(n, m, x, witness["groups"])
        equal(witness["load"], [replay["early"], replay["terminal"]], "stored witness load")
        equal(witness["used_buses"], replay["used_buses"], "stored witness used buses")
        equal(witness["terminal_connector_groups"], {"paired_service": m, "sequential_single_service": n-m}, "stored terminal connector groups")
        u = (x-10*m)/(n-m) if m < n else Q(0)
        equal(witness["single_pair_terminal_energy"], 30-u, "stored paired-single connector energy")
        records.append({"m": m, "delta": delta, "regret": regret,
                        "per_used_bus": regret/(2*n-m), "relative_regret": regret/physical})
        COUNTS["physical_optimizers"] += 1

    if n % 40 == 0:
        equal(c["gap"], Q(0), "zero-residue gap")
        require(all(w["own_price_regret"] == 0 for w in c["physical_optimizers"]), "zero-residue regret")
    equal(len(expected_winners), 2 if n % 40 == 20 else 1, "tie residue completeness")
    if n % 40 == 1:
        equal(len(records), 1, "subsequence unique optimizer")
        w = records[0]
        equal(w["delta"], Q(13, 40), "40k+1 residual")
        equal(c["gap"], Q(169, 80*n), "40k+1 absolute gap")
        equal(c["relative_gap"], Q(169, 7591*n*n), "40k+1 relative gap")
        equal(w["regret"], Q(351, 40)+Q(169, 40*n), "40k+1 whole-fleet regret")
        equal(w["per_used_bus"], Q(351*n+169, n*(53*n-13)), "40k+1 per-used-bus regret")
        equal(w["relative_regret"], Q(2*(351*n+169), 7591*n*n+169), "40k+1 relative regret")
    COUNTS["cases"] += 1
    return {"n": n, "physical": physical, "hull": ch, "gap": physical-ch,
            "relative_gap": (physical-ch)/ch, "optimizers": records,
            "hull_all_paired_weight": weight}


def verify_raw(raw, repository):
    equal(raw["head"], FROZEN, "frozen commit")
    equal(raw["grid"], GRID, "complete prospective grid")
    equal([c["n"] for c in raw["cases"]], GRID, "case ordering and completeness")
    require(math.isfinite(raw["wall_s"]) and raw["wall_s"] >= 0, "recorded runtime metadata")
    equal(set(raw["source_hashes"]), {"doc/CYCLIC_REPLICATION_PROTOCOL_20260927.md", "src/experiments/cyclic_replication.py"}, "frozen dependency scope")
    for name, expected in raw["source_hashes"].items():
        data = subprocess.check_output(["git", "-C", str(repository), "show", FROZEN+":"+name])
        equal(hashlib.sha256(data).hexdigest(), expected, "frozen Git dependency "+name)


def corrupt_controls(raw):
    out = []
    def reject(label, change, n=20):
        c = copy.deepcopy(next(x for x in raw["cases"] if x["n"] == n))
        change(c)
        try:
            audit_case(decode(c))
        except (AssertionError, KeyError, ZeroDivisionError) as exc:
            out.append({"control": label, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Corrupted copy accepted: "+label)
    def bump(container, key, amount=1):
        q = Q(container[key]["exact"])+amount
        container[key] = {"exact": str(q), "value": float(q)}
    reject("branch objective", lambda c: bump(c["branch_optima"][3], "cost"))
    reject("continuous branch minimizer", lambda c: bump(c["branch_optima"][3], "x"))
    reject("missing partition", lambda c: c["branch_optima"].pop(3))
    reject("missing tied optimum", lambda c: c["physical_optimizers"].pop())
    reject("hull objective", lambda c: bump(c, "convexified"))
    reject("lower hull endpoint", lambda c: bump(c["hull_vertices"][0], 1))
    reject("physical SOC", lambda c: bump(c["physical_optimizers"][0]["witness"]["groups"][0]["soc"], 3))
    reject("terminal energy", lambda c: bump(c["physical_optimizers"][0]["witness"]["groups"][0], "terminal"))
    reject("group coverage count", lambda c: c["physical_optimizers"][0]["witness"]["groups"][0].__setitem__("count", 999))
    reject("terminal connector count", lambda c: c["physical_optimizers"][0]["witness"]["terminal_connector_groups"].__setitem__("paired_service", 12))
    reject("sequential terminal energy", lambda c: bump(c["physical_optimizers"][0]["witness"], "single_pair_terminal_energy"))
    reject("own price", lambda c: bump(c["physical_optimizers"][0]["price"], 0))
    reject("own-price regret", lambda c: bump(c["physical_optimizers"][0], "own_price_regret"))
    reject("regret normalized by capacity instead of used buses", lambda c: c["physical_optimizers"][0].__setitem__("regret_per_used_bus", encode(Q(c["physical_optimizers"][0]["own_price_regret"]["exact"])/(2*c["n"]))))
    reject("relative gap wrong denominator", lambda c: c.__setitem__("relative_gap", encode(Q(c["gap"]["exact"])/Q(c["physical"]["exact"]))))
    reject("fleet LOC", lambda c: bump(c["physical_optimizers"][0], "fleet_LOC_at_hull_price"))
    reject("supply LOC", lambda c: bump(c["physical_optimizers"][0], "supply_LOC_at_hull_price"))
    reject("supplier conjugate", lambda c: bump(c, "hull_conjugate"))
    reject("hull fleet response", lambda c: bump(c, "hull_response"))
    reject("decimal display detached from exact value", lambda c: c["gap"].__setitem__("value", 999))
    reject("40k+1 subsequence gap", lambda c: bump(c, "gap"), n=401)
    return out


def main():
    repository = next((p for p in HERE.parents if (p/".git").exists() and (p/"src/experiments/cyclic_replication.py").is_file()), None)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=HERE.parent/"results.json")
    parser.add_argument("--repository", type=Path, default=repository)
    parser.add_argument("--out", type=Path, help="New output file outside any Git repository (default: unique file in the system temporary directory).")
    args = parser.parse_args()
    if args.repository is None:
        parser.error("Supply --repository containing the frozen Git commit.")
    if args.out is None:
        args.out = Path(tempfile.gettempdir())/f"egg-cyclic-replication-audit-{uuid.uuid4().hex}.json"
    output = args.out.resolve()
    repository = args.repository.resolve()
    require(output != args.result.resolve(), "audit output cannot replace raw result")
    require(output != repository and repository not in output.parents,
            "audit output must be outside the source repository")
    require(not any((p/".git").exists() for p in (output, *output.parents)),
            "audit output must be outside every Git repository")
    require(not args.out.exists() and not args.out.is_symlink(),
            "audit output must be a new file; existing files and symlinks are refused")
    started = time.perf_counter()
    raw_bytes = args.result.read_bytes()
    equal(hashlib.sha256(raw_bytes).hexdigest(), RAW_SHA256, "original result identity")
    raw = json.loads(raw_bytes)
    verify_raw(raw, args.repository)
    decoded = decode(raw)
    records = [audit_case(c) for c in decoded["cases"]]
    counts = dict(COUNTS)
    equal(counts["branch_minima"], 6448, "complete branch-minimum count")
    equal(counts["cases"], 86, "complete case count")
    controls = corrupt_controls(raw)
    result = {"status": "PASS", "frozen_commit": FROZEN, "raw_result_sha256": RAW_SHA256,
              "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "exact rational branch/hull/price/physical-connector reconstruction; no author imports or optimizer; all ties retained",
              "counts": counts, "corruption_controls": controls,
              "cases": records,
              "tie_cases": [r for r in records if len(r["optimizers"]) == 2],
              "subsequence_40k_plus_1": [r for r in records if r["n"] % 40 == 1],
              "zero_gap_sizes": [r["n"] for r in records if r["gap"] == 0],
              "normalization": {"relative_gap_denominator": "CH_n", "relative_regret_denominator": "D_n", "per_bus_denominator": "actual used buses 2n-m"},
              "limits": {"whole_fleet_regret_on_40k_plus_1": Q(351, 40),
                         "absolute_gap": 0, "relative_gap": 0, "per_used_bus_regret": 0, "relative_regret": 0,
                         "whole_fleet_regret_all_n": "no single limit; n divisible by 40 has zero regret"},
              "audit_wall_s": time.perf_counter()-started}
    # Exclusive creation also refuses a file/symlink created after the preflight.
    with args.out.open("x") as handle:
        handle.write(json.dumps(encode(result), indent=2, sort_keys=True, allow_nan=False)+"\n")
    equal(hashlib.sha256(args.result.read_bytes()).hexdigest(), RAW_SHA256, "raw result preserved after audit")
    print(json.dumps({"status": result["status"], "output": str(output), "counts": counts, "corruption_controls_rejected": len(controls), "audit_wall_s": result["audit_wall_s"]}, indent=2))


if __name__ == "__main__":
    main()
