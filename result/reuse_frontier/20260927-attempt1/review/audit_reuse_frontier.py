#!/usr/bin/env python3
"""Non-author audit of frozen reuse-frontier JSON. Standard library only.

No production imports, optimizer, or scientific reruns. The pricing DP uses
integer SOC and exact binary-rational prices; see REVIEW.md for the integrality
argument and the numerical scope of the remaining witness/KKT checks.
"""
import argparse
import copy
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
FROZEN = "7d3d76472ddf412e7af9e3b533d2d1fdcdac73ac"
ORIGINAL_MANIFEST_SHA256 = "895766dac3ef3b79df7b1634fe016a06a58dd0507507e6b9df70d2d83c6609e8"
NAMES = ("depleted_f20", "depleted_f26", "replenished_two_bus")
ARMS = ("cold", "retained", "retained_shift")
COUNTS = Counter()
RESIDUALS = {}
TANGENT_MUTATIONS = []
INDEPENDENT_INTERVALS = []


def discover_repository():
    """Locate the containing checkout without depending on its directory name."""
    return next((p for p in HERE.parents if (p/".git").exists()
                 and (p/"src/experiments/reuse_frontier.py").is_file()), None)


def require(ok, text):
    if not ok:
        raise AssertionError(text)


def near(x, y, text, tol=1e-6):
    require(math.isfinite(x) and math.isfinite(y), text + ": nonfinite")
    residual = abs(x-y)
    RESIDUALS[text] = max(RESIDUALS.get(text, 0.0), residual)
    require(residual <= tol, f"{text}: {x} != {y}, difference {residual}")


def vector(x, y, text, tol=1e-7):
    require(len(x) == len(y), text + ": length")
    for a, b in zip(x, y):
        near(a, b, text, tol)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def key(col):
    value = {"v": "b2a2-col-v2", "load": [format(float(x)+0.0, ".17g") for x in col["load"]],
             "ops_cost": format(float(col["ops_cost"])+0.0, ".17g")}
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def expected(name):
    replenished = name == NAMES[2]
    trips = {"t0": (0, 1, 15), "t1": (3, 4, 15), "t2": (6, 7, 15)}
    if replenished:
        trips.update(marker0=(10, 11, 0), marker1=(10, 11, 0))
    return trips, 11 if replenished else 7, {NAMES[0]: 20, NAMES[1]: 26, NAMES[2]: 10}[name], 20 if replenished else 0


@lru_cache(None)
def partitions(name):
    trips, _, _, _ = expected(name)
    ids = sorted(trips, key=lambda t: (trips[t][0], t))
    out = []
    # Quotient bus-label symmetry by placing the first service on bus zero.
    for tail in itertools.product(range(2), repeat=len(ids)-1):
        labels = (0,) + tail
        seqs = tuple(tuple(t for t, bus in zip(ids, labels) if bus == b) for b in range(2))
        seqs = tuple(s for s in seqs if s)
        if all(all(trips[a][1] <= trips[b][0] for a, b in zip(s, s[1:])) for s in seqs):
            out.append(seqs)
    return tuple(out)


def structural_set(name):
    _, _, fixed, _ = expected(name)
    out = set()
    for seqs in partitions(name):
        for choices in itertools.product(("dir", "dep"), repeat=sum(len(s)-1 for s in seqs)):
            iterator = iter(choices)
            kinds = tuple(tuple(next(iterator) for _ in s[1:]) for s in seqs)
            out.add((seqs, kinds, fixed*len(seqs)))
    return out


def struct_key(s):
    return tuple(tuple(x) for x in s["sequences"]), tuple(tuple(x) for x in s["kinds"]), s["ops_cost"]


@lru_cache(None)
def price_exact(name, prices):
    """Global continuous linear pricing, via integral vertices of inventory flow.

    Depot arcs weakly dominate direct arcs in these zero-deadhead fixtures.
    This dominance is not assumed for arbitrary EGG instances.
    """
    trips, slots, fixed, terminal = expected(name)
    require(len(prices) == slots, "pricing length")
    q = tuple(Fraction(x) for x in prices)
    denom = math.lcm(*(p.denominator for p in q))
    ticks = [int(p*denom) for p in q]
    chain_cache = {}

    def chain(seq):
        if seq in chain_cache:
            return chain_cache[seq]
        states = {20: 0}
        for j, tid in enumerate(seq):
            demand = trips[tid][2]
            states = {soc-demand: cost for soc, cost in states.items() if soc >= demand}
            if j+1 < len(seq):
                for slot in range(trips[tid][1], trips[seq[j+1]][0]):
                    nxt = {}
                    for soc, cost in states.items():
                        for energy in range(min(10, 20-soc)+1):
                            ns, nc = soc+energy, cost+ticks[slot]*energy
                            if ns not in nxt or nc < nxt[ns]:
                                nxt[ns] = nc
                    states = nxt
        candidates = [cost for soc, cost in states.items() if soc >= terminal]
        result = min(candidates) if candidates else None
        chain_cache[seq] = result
        return result

    values = []
    for seqs in partitions(name):
        cs = [chain(s) for s in seqs]
        if all(c is not None for c in cs):
            values.append(fixed*len(seqs)*denom+sum(cs))
    require(values, "global pricing infeasible")
    return Fraction(min(values), denom)


def physical(name, sequences, kinds, charges, weight=1.0, tol=1e-7):
    trips, slots, fixed, terminal = expected(name)
    require(math.isfinite(weight) and weight >= -tol, "physical weight")
    require(1 <= len(sequences) <= 2 and len(sequences) == len(kinds), "physical fleet")
    require(Counter(t for s in sequences for t in s) == Counter(trips.keys()), "physical coverage")
    for s, ks in zip(sequences, kinds):
        require(s and len(ks) == len(s)-1, "physical arc count")
        require(all(k in ("dir", "dep") for k in ks), "physical arc kind")
        require(all(trips[a][1] <= trips[b][0] for a, b in zip(s, s[1:])), "physical overlap")
    events = {}
    for ci, edge, slot, energy in charges:
        require(all(type(v) is int for v in (ci, edge, slot)), "event integer indexes")
        require(0 <= ci < len(sequences) and 0 <= edge < len(sequences[ci])-1, "event ownership")
        require(kinds[ci][edge] == "dep", "event depot arc")
        a, b = sequences[ci][edge:edge+2]
        require(trips[a][1] <= slot < trips[b][0] and 0 <= slot < slots, "event window")
        require((ci, edge, slot) not in events, "event duplicate")
        require(math.isfinite(energy) and -tol <= energy <= 10*weight+tol, "event power")
        events[ci, edge, slot] = energy
    load = [0.0]*slots
    for ci, seq in enumerate(sequences):
        soc = 20*weight
        for j, tid in enumerate(seq):
            require(-tol <= soc <= 20*weight+tol, "SOC before service")
            soc -= trips[tid][2]*weight
            require(-tol <= soc <= 20*weight+tol, "SOC after service")
            COUNTS["SOC_events"] += 2
            if j+1 < len(seq):
                for slot in range(trips[tid][1], trips[seq[j+1]][0]):
                    energy = events.get((ci, j, slot), 0.0)
                    soc += energy
                    load[slot] += energy
                    require(-tol <= soc <= 20*weight+tol, "SOC after charge")
                    COUNTS["SOC_events"] += 1
        require(soc >= terminal*weight-tol, "terminal SOC")
        COUNTS["buses_replayed"] += 1
    if terminal == 20:
        near(sum(load), 45*weight, "replenished energy conservation", tol*10)
        require(len(sequences) == 2 and {s[-1] for s in sequences} == {"marker0", "marker1"}, "terminal marker coverage")
    COUNTS["schedules_replayed"] += 1
    return load, fixed*len(sequences)*weight


def check_col(name, col, ihash):
    require(col["instance_hash"] == ihash, "column instance identity")
    events = []
    for e in col["charges"]:
        ci = e["vehicle"]
        require(type(ci) is int and 0 <= ci < len(col["sequences"]), "column vehicle")
        seq = col["sequences"][ci]
        require(e["after_trip"] in seq[:-1], "column charge after trip")
        edge = seq.index(e["after_trip"])
        require(seq[edge+1] == e["before_trip"], "column charge before trip")
        events.append((ci, edge, e["slot"], e["kwh"]))
    load, ops = physical(name, col["sequences"], col["arc_kinds"], events, tol=1e-7)
    vector(load, col["load"], "column load")
    near(ops, col["ops_cost"], "column operating cost", 1e-9)
    require(col["fleet"] == len(col["sequences"]), "column fleet")
    require(col["column_key"] == key(col), "column full-precision key")
    sh = hashlib.sha256(json.dumps(sorted(tuple(s) for s in col["sequences"])).encode()).hexdigest()[:12]
    lh = hashlib.sha256(json.dumps([round(float(x), 2)+0.0 for x in load]).encode()).hexdigest()[:12]
    require(col["schedule_hash"] == sh and col["load_hash"] == lh, "column diagnostic hashes")
    st = col["oracle_stats"]
    require(st["status"] == "OPTIMAL" and st["backend"] == "CBC" and st["extra"]["threads"] == 1, "column oracle metadata")
    objective = st["extra"]["pricing_objective_reconstruction"]
    val = ops+sum(q*x for q, x in zip(objective["prices"], load))
    near(objective["physical_obj"], val, "column original pricing objective")
    near(objective["model_obj"], st["obj"], "column model objective")
    near(objective["abs_adjustment"], abs(st["obj"]-val), "column objective adjustment")
    residual = st["extra"]["load_reconstruction"]
    vector([x-y for x, y in zip(residual["raw_load_kwh"], load)], residual["residual_kwh"], "column reconstruction residual")
    near(max(abs(x) for x in residual["residual_kwh"]), residual["max_abs_residual_kwh"], "column max residual")
    require(residual["max_abs_residual_kwh"] <= 1e-4, "column reconstruction tolerance")
    return load, ops


def system(market, load):
    return sum((a+b*u)*x+0.5*b*x*x for a, b, u, x in zip(market["a"], market["b"], market["U"], load))


def exact_fenchel_lower(name, market, prices):
    q = tuple(Fraction(x) for x in prices)
    conjugate = sum(max(Fraction(0), p-Fraction(a)-Fraction(b)*Fraction(u))**2/(2*Fraction(b))
                    for p, a, b, u in zip(q, market["a"], market["b"], market["U"]))
    return price_exact(name, q)-conjugate


def check_identity(state, fixtures, config_hash):
    name, index = state["fixture"], state["state_index"]
    require(name in NAMES and 0 <= index < 5, "state identity")
    require(state["schema"] == "egg-reuse-frontier-v1" and state["config_sha256"] == config_hash, "config identity")
    require(state["instance"] == fixtures[name], "frozen instance")
    require(state["instance_hash"] == digest(fixtures[name])[:12], "instance hash")
    _, slots, _, _ = expected(name)
    d = (0.0, 0.0, 0.25, -0.25, 0.0)[index]
    market = {"a": [0.3+d*(-1 if 1 <= t <= 3 else 1 if t >= 4 else 0) for t in range(slots)],
              "b": [0.2]*slots, "U": [0.0]*slots}
    require(state["market"] == market, "frozen market path")
    if "market_hash" in state:
        formatted = {k: [format(float(x), ".17g") for x in market[k]] for k in ("a", "b", "U")}
        require(state["market_hash"] == hashlib.sha256(json.dumps(formatted).encode()).hexdigest(), "market hash")


def check_master(state, master, iteration, columns, tag):
    keys, w = master["column_keys"], master["lambdas"]
    require(len(keys) == len(w) and len(set(keys)) == len(keys), "master key and weight lengths")
    require(all(k in columns for k in keys), "master key membership")
    require(all(math.isfinite(x) and x >= -1e-8 for x in w), "master nonnegative weights")
    near(sum(w), 1, "master weight sum", 1e-7)
    cols = [columns[k] for k in keys]
    load = [sum(x*c["load"][t] for x, c in zip(w, cols)) for t in range(len(master["L"]))]
    ops = sum(x*c["ops_cost"] for x, c in zip(w, cols))
    vector(load, master["L"], "master physical load")
    vector(load, master["physical_replay"]["load"], "master stored replay load")
    near(ops, master["physical_replay"]["intrinsic_cost"], "master intrinsic cost")
    ub = ops+system(state["market"], load)
    near(ub, master["ub"], "master UB")
    near(ub, master["physical_replay"]["true_objective"], "master replay UB")
    require(-1e-6 <= ub-master["z_model"] <= 0.001+1e-6, "master tangent slack")
    if state["fixture"] == NAMES[2]:
        near(sum(load), 45, "master replenished energy")
    # Driver aliasing appends one future cut to certain saved master snapshots.
    tangents = copy.deepcopy(master["tangent_points"])
    appended = (iteration is not None and iteration["gap"] > .01 and
                not (iteration["reduced_lower"] < -1e-6 and iteration["reduced_upper"] >= -1e-6))
    if appended:
        vector(tangents[-1], master["L"], "post-solve appended tangent")
        tangents.pop()
        TANGENT_MUTATIONS.append(tag)
    # Independently reconstruct the separable PWL value and optimality KKT.
    pwl, intercept = 0.0, 0.0
    prices = [-p for p in master["pi"]]
    for t, (x, q, a) in enumerate(zip(load, prices, state["market"]["a"])):
        points = [20.0*j/7 for j in range(8)] + [v[t] for v in tangents]
        lines = [(0.0, 0.0)] + [(a+0.2*p, -0.1*p*p) for p in points]
        vals = [s*x+b for s, b in lines]
        value = max(vals)
        active = [s for (s, _), y in zip(lines, vals) if value-y <= 1e-7]
        require(q <= max(active)+2e-6, "master PWL subgradient upper")
        if x > 1e-7:
            require(q >= min(active)-2e-6, "master PWL subgradient lower")
        pwl += value
        intercept += value-q*x
    near(ops+pwl, master["z_model"], "master reconstructed PWL value", 3e-6)
    near(master["sigma"]+intercept, master["z_model"], "master primal-dual value", 3e-6)
    for weight, col in zip(w, cols):
        reduced = col["ops_cost"]+sum(q*x for q, x in zip(prices, col["load"]))-master["sigma"]
        require(reduced >= -3e-6, "master column dual feasibility")
        near(weight*reduced, 0.0, "master column complementarity", 3e-6)
    solves = master["master_solves"]
    require(len(solves) == master["n_refinements"]+1, "master refinement count")
    require(all(s["status"] == "OPTIMAL" and s["backend"] == "CBC" and s["threads"] == 1 and s["n_int"] == 0 for s in solves), "master solve metadata")
    near(solves[-1]["obj"], master["z_model"], "master last native value")
    near(sum(s["wall_s"] for s in solves), master["master_wall_s"], "master wall sum", 1e-8)
    COUNTS["masters_reconstructed"] += 1
    return prices


def check_state(state, all_states, fixtures, config_hash, tag):
    check_identity(state, fixtures, config_hash)
    name, arm, index = state["fixture"], state["arm"], state["state_index"]
    columns = {c["column_key"]: c for c in state["columns"]}
    require(len(columns) == len(state["columns"]) <= 240, "pool unique keys/cap")
    for c in columns.values():
        check_col(name, c, state["instance_hash"])
        COUNTS["column_occurrences"] += 1
    imported = state["imported_column_keys"]
    if index and arm != "cold":
        prior = all_states[name, arm, index-1]
        require(prior["status"] == "certified", "certified predecessor")
        require(state["previous_state"] == {"index": index-1, "digest": digest(prior)}, "predecessor digest")
        require(imported == [c["column_key"] for c in prior["columns"]], "complete inherited pool")
        require(state["columns"][:len(imported)] == prior["columns"], "imported column evidence")
    else:
        require(state["previous_state"] is None and imported == [], "cold fresh pool")
    seen = list(imported)
    masters = iter(state["master_events"])
    completed_iterations = iter(state["iterations"])
    prior_tangents = []
    prior_ub = math.inf
    best = -math.inf
    independent_best = None
    native_pricing = [n for n in state["native_solves"] if n["model"] == "evsp"]
    require(len(native_pricing) == len(state["oracle_events"]), "native pricing attempt count")
    for j, (event, native) in enumerate(zip(state["oracle_events"], native_pricing)):
        require(event["call"] == j, "oracle sequential call")
        purpose = event["purpose"]
        master = row = None
        if purpose == "cold_seed":
            require(j == 0 and not imported, "cold seed location")
            vector(event["prices"], state["market"]["a"], "cold seed price")
        elif purpose == "analytic_proposal":
            require(arm == "retained_shift" and index > 0 and j == 0, "proposal location")
            prior = all_states[name, arm, index-1]
            vector(event["prices"], [q+a-b for q, a, b in zip(prior["last_clean_price"], state["market"]["a"], prior["market"]["a"])], "shifted proposal price")
            require(state["proposal"] == event, "proposal event copy")
        else:
            require(purpose == "clean", "oracle purpose")
            master = next(masters)
            require(master["column_keys"] == seen, "master pool chronology")
            row = next(completed_iterations) if event["status"] == "completed" else None
            appended = (row is not None and row["gap"] > .01 and
                        not (row["reduced_lower"] < -1e-6 and row["reduced_upper"] >= -1e-6))
            require(master["tangent_points"][:len(prior_tangents)] == prior_tangents, "within-state tangent history")
            require(len(master["tangent_points"]) == len(prior_tangents)+master["n_refinements"]+int(appended), "fresh-state tangent accounting")
            require(master["ub"] <= prior_ub+.001+1e-6, "within-state master UB monotonicity")
            prior_tangents = master["tangent_points"]
            prior_ub = master["ub"]
            q = check_master(state, master, row, columns, tag+f"/call{j}")
            vector(q, event["prices"], "clean pricing dual price")
        exact = price_exact(name, tuple(event["prices"]))
        COUNTS["pricing_attempts_globally_audited"] += 1
        require(native["backend"] == "CBC" and native["extra"]["threads"] == 1, "native pricing backend")
        require(native["bound"] <= float(exact)+2e-6, "native pricing lower vs independent optimum")
        require(native["obj"] >= float(exact)-2e-6, "native pricing incumbent vs independent optimum")
        if event["status"] != "completed":
            require(state["status"] == "failed" and native["status"] != "OPTIMAL" and j == len(state["oracle_events"])-1, "pending failed pricing")
            require("upper" not in state and "lower" not in state and "gap" not in state, "failed cell has no final certificate")
            continue
        require(native["status"] == "OPTIMAL", "completed pricing native optimal")
        col = event["column"]
        check_col(name, col, state["instance_hash"])
        COUNTS["event_columns_replayed"] += 1
        require(event["column_key"] == col["column_key"] and event["column_key"] in columns, "event projected column retained")
        if event["column_key"] not in seen:
            require(col == columns[event["column_key"]], "novel event column evidence retained")
        val = col["ops_cost"]+sum(q*x for q, x in zip(event["prices"], col["load"]))
        near(val, event["upper"], "pricing reconstructed incumbent")
        near(float(exact), event["upper"], "pricing independent exact optimum", 2e-6)
        require(event["lower"] <= float(exact)+2e-6, "pricing lower vs independent exact optimum")
        near(event["lower"], native["bound"], "pricing bound native match")
        require(event["solver"] == col["oracle_stats"], "pricing solver evidence")
        require(event["used_for_lower_bound"] == (purpose == "clean"), "only clean bound flag")
        require(event["novel"] == (col["column_key"] not in seen), "full key novelty")
        projected = not any(abs(col["ops_cost"]-columns[k]["ops_cost"]) <= 1e-7 and max(abs(x-y) for x, y in zip(col["load"], columns[k]["load"])) <= 1e-7 for k in seen)
        require(event["projection_novel"] == projected, "projection novelty")
        if row is not None:
            independent_lower = exact_fenchel_lower(name, state["market"], event["prices"])
            independent_best = independent_lower if independent_best is None else max(independent_best, independent_lower)
            lower = master["z_model"]+min(0, event["lower"]-master["sigma"])
            best = max(best, lower)
            near(row["lower"], lower, "fresh lower candidate")
            near(row["lb_best"], best, "within-state best lower")
            near(row["reduced_lower"], event["lower"]-master["sigma"], "reduced lower")
            near(row["reduced_upper"], event["upper"]-master["sigma"], "reduced upper")
            near(row["upper"], master["ub"], "iteration upper")
            near(row["gap"], master["ub"]-best, "iteration gap")
            near(row["pwl_slack"], master["ub"]-master["z_model"], "iteration PWL slack")
            near(row["sigma"], master["sigma"], "iteration sigma")
            vector(row["master_dual_price"], event["prices"], "iteration dual price")
            require(row["oracle_call"] == j, "iteration oracle index")
            COUNTS["certificate_iterations_reconstructed"] += 1
        if col["column_key"] not in seen:
            seen.append(col["column_key"])
    require(next(masters, None) is None and next(completed_iterations, None) is None, "master/iteration count")
    require(seen == list(columns), "no hidden/evicted columns")
    events = state["oracle_events"]
    require(len(events) == state["oracle_calls"] <= 48, "oracle accounting/cap")
    for field, purpose in (("calls_clean", "clean"), ("calls_seed", "cold_seed"), ("calls_proposal", "analytic_proposal")):
        require(state[field] == sum(e["purpose"] == purpose for e in events), "pricing purpose accounting")
    require(state["calls_proposal"] == int(arm == "retained_shift" and index > 0), "exactly one shifted proposal")
    require(state["calls_seed"] == int(arm == "cold" or index == 0), "seed accounting")
    native = state["native_solves"]
    lp = [n for n in native if n["model"] == "b2a2-rmp"]
    require(len(native) == len(events)+len(lp), "wrapper model accounting")
    master_solves = [s for m in state["master_events"] for s in m["master_solves"]]
    require(len(lp) == len(master_solves), "master wrapper count")
    require(len({s["solve_id"] for s in master_solves}) == len(master_solves), "cell-local master solve identities")
    for n, m in zip(lp, master_solves):
        for field in ("obj", "bound", "wall_s", "n_vars", "n_int", "n_constrs"):
            near(n[field], m[field], "master/native "+field, 1e-8)
    near(sum(n["elapsed_s"] for n in native), state["optimizer_wrapper_elapsed_s"], "wrapper elapsed accounting", 1e-8)
    near(sum(n.get("wall_s", 0)+n.get("lp_wall_s", 0) for n in native), state["solver_wall_s"], "solver wall accounting", 1e-8)
    require(all(n["model_time_cap_s"] <= 10 and n.get("time_limit_s", 10) <= 10 for n in native), "native configured cap")
    if state["status"] == "certified":
        require(all(n["status"] == "OPTIMAL" for n in native), "frozen OPTIMAL status gate")
        final = state["iterations"][-1]
        for field in ("upper", "gap"):
            near(state[field], final[field], "final "+field)
        near(state["lower"], best, "final lower")
        require(-1e-6 <= state["gap"] <= .01, "final certificate threshold")
        vector(state["last_clean_price"], events[-1]["prices"], "final clean price")
        vector(state["final_load"], state["master_events"][-1]["L"], "final load")
        require(float(independent_best) <= state["upper"]+1e-6, "independent global Fenchel direction")
        require(state["lower"] <= float(independent_best)+1e-6, "saved bound below independent Fenchel bound")
        require(state["upper"]-float(independent_best) <= .01+1e-6, "independent global certificate width")
        INDEPENDENT_INTERVALS.append({"fixture": name, "arm": arm, "state_index": index,
            "exact_clean_Fenchel_lower": str(independent_best),
            "independent_lower_float": float(independent_best), "physical_upper": state["upper"],
            "independent_width": state["upper"]-float(independent_best),
            "saved_lower": state["lower"]})
    COUNTS["states_audited"] += 1


def check_reference(ref, fixtures, config_hash):
    check_identity(ref, fixtures, config_hash)
    name = ref["fixture"]
    require(ref["status"] == "reference_complete" and ref["ch"]["status"] == "OPTIMAL", "reference status")
    actual = [struct_key(s) for s in ref["structures"]]
    require(len(actual) == len(set(actual)) and set(actual) == structural_set(name), "complete independent structural enumeration")
    ch = ref["ch"]
    require(len(ch["witness"]) == len(actual), "reference witness count")
    weights, ops, load = [], 0.0, [0.0]*len(ch["load"])
    for s, w in zip(ref["structures"], ch["witness"]):
        require(w["structure"] == s, "reference structure order")
        events = [(e["chain"], e["edge"], e["slot"], e["energy"]) for e in w["charges"]]
        part, cost = physical(name, s["sequences"], s["kinds"], events, w["weight"])
        near(s["ops_cost"], expected(name)[2]*len(s["sequences"]), "reference structure ops")
        vector(part, w["replay"]["load"], "reference scaled replay load")
        near(cost, w["replay"]["scaled_ops"], "reference scaled replay cost")
        load = [x+y for x, y in zip(load, part)]
        ops += cost
        weights.append(w["weight"])
        COUNTS["reference_scaled_blocks"] += 1
    near(sum(weights), 1.0, "reference convex weight sum", 1e-7)
    vector(load, ch["load"], "reference aggregate load")
    value = ops+system(ref["market"], load)
    near(value, ch["exact_evaluation"], "reference objective replay")
    allowance = 1e-7*max(1, abs(value), abs(ch["model_value"]), abs(ch["solver_bound"]))
    near(ch["numerical_allowance"], allowance, "reference allowance")
    near(ch["lower"], min(ch["model_value"], ch["solver_bound"])-allowance, "reference guarded lower arithmetic")
    near(ch["upper"], value+allowance, "reference guarded upper arithmetic")
    require(-allowance <= value-min(ch["model_value"], ch["solver_bound"]) <= 1e-5, "reference tangent slack")
    require(len(ref["calls"]) == ch["refinements"]+1 and all(c["status"] == "OPTIMAL" and c["threads"] == 1 for c in ref["calls"]), "reference native accounting")
    # Exact independent support bound at the recorded primal gradient. It does
    # not independently reproduce the native reference's tighter PWL bound.
    q = tuple(Fraction(a)+Fraction(b)*Fraction(x) for a, b, x in zip(ref["market"]["a"], ref["market"]["b"], load))
    support = price_exact(name, q)-sum(Fraction(b)*Fraction(x)**2/2 for b, x in zip(ref["market"]["b"], load))
    require(float(support) <= value+2e-6, "independent reference support direction")
    require(float(support) <= ch["upper"]+2e-6, "reference interval vs independent support")
    COUNTS["references_audited"] += 1
    return {"fixture": name, "state_index": ref["state_index"], "structures": len(actual),
            "independent_support_lower": float(support), "physical_upper": value,
            "independent_primal_dual_width": value-float(support),
            "native_guarded_lower": ch["lower"], "native_guarded_upper": ch["upper"]}


def audit(root, repository, cbc_library=None):
    manifest_path = root/"MANIFEST.json"
    require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == ORIGINAL_MANIFEST_SHA256, "original manifest identity")
    original_manifest = json.loads(manifest_path.read_text())
    require(original_manifest["algorithm"] == "sha256" and len(original_manifest["files"]) == 244, "original manifest scope")
    for name, sha in original_manifest["files"].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, "original raw file "+name)
    config = json.loads((root/"frozen-config.json").read_text())
    provenance = json.loads((root/"provenance.json").read_text())
    fixtures = {x["meta"]["fixture"]: x for x in json.loads((root/"frozen-fixtures.json").read_text())}
    require(provenance["head"] == FROZEN and digest(config) == provenance["config_sha256"], "provenance frozen identity")
    for relative, sha in provenance["source_sha256"].items():
        data = subprocess.check_output(["git", "-C", str(repository), "show", FROZEN+":"+relative])
        require(hashlib.sha256(data).hexdigest() == sha, "frozen dependency "+relative)
    for name, inst in fixtures.items():
        trips, slots, fixed, terminal = expected(name)
        require({t["id"]: (t["start_min"]//60, t["end_min"]//60, t["energy_kwh"]) for t in inst["trips"]} == trips, "independent fixture trips")
        require(all(t["start_min"] % 60 == t["end_min"] % 60 == 0 and t["start_loc"] == t["end_loc"] == "D" for t in inst["trips"]), "aligned depot fixtures")
        require(inst["n_slots"] == slots and inst["vehicle_fixed_cost"] == fixed and inst["soc_end_kwh"] == terminal, "independent fixture cost/horizon")
        require(inst["battery_kwh"] == inst["soc0_kwh"] == 20 and inst["soc_min_kwh"] == 0 and inst["charge_power_kw"] == 10 and inst["max_vehicles"] == 2 and inst["slot_min"] == 60 and not inst["dh_min"] and not inst["dh_kwh"], "independent fixture physics")
    states = {(n, a, i): json.loads((root/f"{n}-{a}-s{i}/state.json").read_text()) for n in NAMES for a in ARMS for i in range(5)}
    refs = {(n, i): json.loads((root/f"{n}-reference-s{i}/state.json").read_text()) for n in NAMES for i in range(5)}
    for identity, state in states.items():
        check_state(state, states, fixtures, provenance["config_sha256"], "/".join(map(str, identity)))
    reference_evidence = [check_reference(ref, fixtures, provenance["config_sha256"]) for ref in refs.values()]
    summary = json.loads((root/"summary.json").read_text())
    require(len(summary["states"]) == 45 and len(summary["references"]) == 15, "summary full grid")
    for row in summary["states"]:
        s = states[row["fixture"], row["arm"], row["state_index"]]
        process = json.loads((root/row["result"]).with_name("process.json").read_text())
        require({k: v for k, v in row.items() if k != "reference_check"} == process, "summary process evidence")
        require(row["status"] == s["status"], "summary state status")
        require(row["pricing_attempts_observed"] == len(s["oracle_events"]) and row["optimizer_wrapper_attempts_observed"] == len(s["native_solves"]), "summary observed attempts")
        for k in ("calls_seed", "calls_clean", "calls_proposal", "oracle_calls", "solver_wall_s", "worker_cpu_s"):
            near(row[k], s[k], "summary "+k, 1e-8)
        require(row["complete_wall_s"] >= s["worker_wall_s"] and not row["timed_out"], "complete subprocess time")
        if s["status"] == "certified":
            require(row["worker_exit"] == 0 and row["accounting_complete"], "successful accounting status")
            ref = refs[row["fixture"], row["state_index"]]["ch"]
            require(s["lower"] <= ref["upper"]+1e-6 and ref["lower"] <= s["upper"]+1e-6, "reference overlap")
            check = row["reference_check"]
            require(check == {"reference_lower": ref["lower"], "reference_upper": ref["upper"], "guard": 1e-6, "intervals_overlap_with_guard": True}, "summary reference check")
            require(row["clean_master_lp_calls"] == sum(len(m["master_solves"]) for m in s["master_events"]), "summary master calls")
        else:
            require(row["worker_exit"] == 1 and not row["accounting_complete"] and "reference_check" not in row, "failed accounting status")
    for row in summary["references"]:
        ref = refs[row["fixture"], row["state_index"]]
        process = json.loads((root/row["result"]).with_name("process.json").read_text())
        require(row == process and row["status"] == ref["status"] == "reference_complete", "reference process/summary identity")
        require(row["reference_native_calls_observed"] == len(ref["calls"]), "reference observed native count")
        require(row["worker_exit"] == 0 and row["accounting_complete"] and not row["timed_out"], "reference successful accounting status")
        require(row["complete_wall_s"] >= ref["wall_s"], "reference complete subprocess wall")
    libraries = set()
    for state in list(states.values())+list(refs.values()):
        lib = state["runtime"]["selected_cbc_library"]
        libraries.add((lib["path"], lib["sha256"]))
    require(len(libraries) == 1, "single actually selected CBC runtime")
    recorded_path, sha = next(iter(libraries))
    library_path = cbc_library or Path(recorded_path)
    if library_path.is_file():
        require(hashlib.sha256(library_path.read_bytes()).hexdigest() == sha, "selected CBC current library hash")
        library_evidence = {"status": "recorded library hash verified", "recorded_sha256": sha,
                            "checked_path": str(library_path)}
    else:
        require(cbc_library is None, "explicit CBC library path is unavailable")
        library_evidence = {"status": "historical library unavailable on this host; metadata only",
                            "recorded_sha256": sha, "recorded_path": recorded_path}
    require(not summary["complete"] and Counter(s["status"] for s in states.values()) == {"certified": 44, "failed": 1}, "preserved incomplete run")
    return states, fixtures, provenance, reference_evidence, summary, library_evidence


def controls(states, fixtures, provenance, refs):
    baseline = states[NAMES[0], "retained_shift", 2]
    tests = []

    def reject(label, change):
        item = copy.deepcopy(baseline)
        change(item)
        try:
            check_state(item, states, fixtures, provenance["config_sha256"], "corruption/"+label)
        except (AssertionError, KeyError, StopIteration) as exc:
            tests.append({"control": label, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Corruption accepted: "+label)

    reject("operating cost", lambda s: s["columns"][0].__setitem__("ops_cost", 999.0))
    reject("physical charge energy", lambda s: s["columns"][0]["charges"][0].__setitem__("kwh", 19.0))
    reject("charge window", lambda s: s["columns"][0]["charges"][0].__setitem__("slot", 0))
    reject("column aggregate load", lambda s: s["columns"][0]["load"].__setitem__(1, 123.0))
    reject("master weight", lambda s: s["master_events"][0]["lambdas"].__setitem__(0, 0.3))
    reject("master sigma", lambda s: s["master_events"][0].__setitem__("sigma", 1000.0))
    reject("master PWL objective", lambda s: s["master_events"][0].__setitem__("z_model", s["master_events"][0]["z_model"]+0.02))
    def proposal_change(s, field, value):
        s["oracle_events"][0][field] = value
        s["proposal"][field] = value
    reject("pricing upper", lambda s: proposal_change(s, "upper", s["oracle_events"][0]["upper"]+1))
    reject("pricing lower", lambda s: proposal_change(s, "lower", s["oracle_events"][0]["upper"]+1))
    reject("proposal contaminated bound flag", lambda s: proposal_change(s, "used_for_lower_bound", True))
    reject("stale predecessor digest", lambda s: s["previous_state"].__setitem__("digest", "wrong"))
    reject("certificate lower", lambda s: s["iterations"][0].__setitem__("lower", 1e9))
    reject("pricing purpose count", lambda s: s.__setitem__("calls_proposal", 0))
    reject("frozen native status", lambda s: s["native_solves"][0].__setitem__("status", "FEASIBLE"))
    reference = refs[NAMES[0], 0]
    def reject_reference(label, change):
        item = copy.deepcopy(reference)
        change(item)
        try:
            check_reference(item, fixtures, provenance["config_sha256"])
        except (AssertionError, KeyError, StopIteration) as exc:
            tests.append({"control": label, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Reference corruption accepted: "+label)
    reject_reference("reference omitted structure", lambda s: s["structures"].pop())
    reject_reference("reference weight", lambda s: s["ch"]["witness"][0].__setitem__("weight", .1))
    reject_reference("reference SOC charge", lambda s: next(w for w in s["ch"]["witness"] if w["weight"] > 0)["charges"][0].__setitem__("energy", 0.0))
    reject_reference("reference objective", lambda s: s["ch"].__setitem__("exact_evaluation", s["ch"]["exact_evaluation"]+1))
    reject_reference("reference interval", lambda s: s["ch"].__setitem__("lower", s["ch"]["lower"]+1))
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE.parent,
                        help="First-run result directory (default: parent of this packaged reviewer).")
    parser.add_argument("--repository", type=Path, default=discover_repository(),
                        help="Git checkout containing the frozen commit; defaults to the containing checkout.")
    parser.add_argument("--cbc-library", type=Path,
                        help="Optional relocated historical CBC library to hash; CBC is never imported or run.")
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir())/"egg-reuse-independent-reproduced.json",
                        help="Derived output (default: system temporary directory/egg-reuse-independent-reproduced.json).")
    args = parser.parse_args()
    if args.repository is None:
        parser.error("Supply --repository with a Git checkout containing the frozen commit.")
    args.root = args.root.resolve()
    args.repository = args.repository.resolve()
    args.out = args.out.resolve()
    original_members = json.loads((args.root/"MANIFEST.json").read_text())["files"]
    protected = {(args.root/name).resolve() for name in original_members} | {(args.root/"MANIFEST.json").resolve()}
    require(args.out not in protected, "audit output must not overwrite original evidence")
    started = time.perf_counter()
    states, fixtures, provenance, refs, summary, library_evidence = audit(args.root, args.repository, args.cbc_library)
    counts = dict(COUNTS)
    residuals = dict(RESIDUALS)
    mutations = list(TANGENT_MUTATIONS)
    independent_intervals = list(INDEPENDENT_INTERVALS)
    reference_states = {(n, i): json.loads((args.root/f"{n}-reference-s{i}/state.json").read_text()) for n in NAMES for i in range(5)}
    controls_result = controls(states, fixtures, provenance, reference_states)
    json_names = sorted([name for name in original_members if name.endswith(".json")]+["MANIFEST.json"])
    manifest = {name: hashlib.sha256((args.root/name).read_bytes()).hexdigest() for name in json_names}
    failed = states[NAMES[0], "cold", 4]
    q = tuple(failed["oracle_events"][-1]["prices"])
    output = {"audit": "PASS with explicit evidence caveat and preserved failed cell", "frozen_commit": FROZEN,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "original_manifest_sha256": ORIGINAL_MANIFEST_SHA256,
              "original_files_verified": len(original_members),
              "cbc_library_verification": library_evidence,
              "raw_json_manifest_sha256": digest(manifest), "raw_json_manifest": manifest,
              "counts": counts, "maximum_residuals_by_check": residuals,
              "post_solve_tangent_appends_reconstructed": mutations,
              "references": refs, "corruption_controls": controls_result,
              "independent_global_clean_certificates": independent_intervals,
              "failed_cell": {"fixture": NAMES[0], "arm": "cold", "state_index": 4,
                              "status_remains": "failed", "pending_call": failed["oracle_events"][-1]["call"],
                              "independent_exact_optimum": str(price_exact(NAMES[0], q)),
                              "independent_optimum_float": float(price_exact(NAMES[0], q)),
                              "native": failed["native_solves"][-1]},
              "total_pricing_attempts": sum(s["oracle_calls"] for s in states.values()),
              "raw_run_total_wall_s": summary["total_wall_s"],
              "audit_wall_s": time.perf_counter()-started,
              "independence": "standard library; no author imports/native solver; exact integer-SOC pricing for frozen fixtures; numerical physical/KKT replay; reference native PWL bound not independently reproduced"}
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({k: output[k] for k in ("audit", "counts", "total_pricing_attempts", "audit_wall_s")}, indent=2))


if __name__ == "__main__":
    main()
