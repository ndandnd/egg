#!/usr/bin/env python3
"""Independent standard-library audit of compact path-flow attempt 3.

Imports only the colocated independent fixture, matrix, and energy-band
reconstructions. It does not import project code, invoke a solver, or edit
original run files. The report and audit helpers live under review/.
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
import sys
import time
import uuid

import independent_compact_core as compact
import independent_energy_band as energy

base = compact.base
need, near = base.need, base.near
HERE = Path(__file__).resolve().parent
COMMIT = "dd5ad16"
MANIFEST_SHA = "c855d220a34b931804cf43c7aedf89d432aae41746c4169f3b87888120b2081a"
POLICY = "native-pathflow-orphan-projection-v1"
FORMULATION = "egg-native-pathflow-v3-energy-band-orphan-projection"
NATIVE_MATRIX = "egg-native-pathflow-v2-energy-band"
SHARED_POLICY = "native-roundoff-qualification-v2"
CORRECTION_BUDGET = Q(1e-8)
EXPECTED_INFEASIBLE = {
    "fixed_reserve_one_bus", "terminal_capacity_failure",
    "partial_overlap_failure", "halfminute_capacity_failure",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def qfloat(x):
    """Exact rational represented by the stored binary float."""
    if isinstance(x, Q):
        return x
    if type(x) not in (int, float) or not math.isfinite(float(x)):
        raise AssertionError(f"not a finite stored number: {x!r}")
    return Q(x)


def qstr(obj, key, value, label):
    need(obj.get(key) == str(value), f"{label}: exact {key}")


def float_equal(obj, key, exact, label):
    need(obj.get(key) == float(exact), f"{label}: rendered {key}")


def projection_records(raw, snapshot, cell, norm):
    """Independently construct projected charges and exact aggregate ledgers."""
    modes = cell["case"]["movements"]
    grid = raw["grid"]
    x = raw["x"]
    raw_energy = raw["raw_energy"]
    raw_idx = {tuple(rec["key"]): rec["variable"] for rec in snapshot["mapping"]["grid_energy"]}
    load_records = [snapshot["variables"][i]["solution"] for i in snapshot["mapping"]["market_load"]]
    raw_load_repr = [rec["repr"] for rec in load_records]
    need(len(raw_load_repr) == len(raw["native_load"])
         and all(math.isfinite(float(rec["value"])) for rec in load_records)
         and [Q(rec["value"]) for rec in load_records] == raw["native_load"],
         "original native load values and preserved representations")
    N = -sum((v for v in raw_energy.values() if v < 0), Q(0))
    O = sum((v for (j, _), v in raw_energy.items() if v > 0 and x[j] <= Q(1, 2)), Q(0))
    negatives = {k: v for k, v in raw_energy.items() if v < 0}
    listed = {tuple(rec["key"]): Q(rec["before_kwh"]) for rec in norm["negative_to_zero"]}
    need(norm["event"] == "charge_normalization" and norm["policy"] == SHARED_POLICY,
         "shared negative normalizer identity")
    need(norm["accepted"] is True and norm["budget_kwh"] == 1e-8,
         "shared negative normalizer acceptance/budget")
    qstr(norm, "negative_l1_exact", N, "negative normalization")
    float_equal(norm, "negative_l1_kwh", N, "negative normalization")
    need(listed == negatives and len(listed) == len(norm["negative_to_zero"])
         and all(rec["after_kwh"] == 0 for rec in norm["negative_to_zero"]),
         "complete negative-to-zero list")
    need(N <= CORRECTION_BUDGET, "standalone negative correction under limit")

    projected = {}
    expected_changes = []
    for key, z in raw_energy.items():
        j, k = key
        selected = x[j] > Q(1, 2)
        r = z if z > 0 and selected else Q(0)
        projected[key] = r
        if r != z:
            v = snapshot["variables"][raw_idx[key]]["solution"]
            reason = "negative-to-zero" if z < 0 else "positive-unselected-to-zero"
            expected_changes.append({
                "interval": k, "key": [j, k], "mode": modes[j]["id"],
                "period": grid[k]["period"], "projected_kwh": float(r),
                "projected_repr": repr(float(r)), "raw_kwh": float(z),
                "raw_repr": v["repr"], "reason": reason, "selected": selected,
            })
    raw_to_projected = N + O
    need(raw_to_projected == sum((abs(projected[k] - v) for k, v in raw_energy.items()), Q(0)),
         "projection L1 equals N+O")

    R, P = [], []
    for t in range(len(cell["case"]["market_edges_min"]) - 1):
        R.append(sum((v for (j, k), v in raw_energy.items() if grid[k]["period"] == t), Q(0)))
        P.append(sum((v for (j, k), v in projected.items() if grid[k]["period"] == t), Q(0)))
    L = raw["native_load"]
    row_l1 = sum((abs(a - b) for a, b in zip(L, R)), Q(0))
    residuals = [a - b for a, b in zip(L, R)]
    return {
        "N": N, "O": O, "raw_to_projected": raw_to_projected,
        "projected": projected, "changes": expected_changes,
        "R": R, "P": P, "L": L, "raw_row_l1": row_l1,
        "raw_row_residuals": residuals, "raw_load_repr": raw_load_repr,
    }


def verify_periods(event, vals, H=None):
    """Check each serialized period row against independently derived values."""
    R, P, L = vals["R"], vals["P"], vals["L"]
    grid, cell = vals["grid"], vals["cell"]
    need(len(event["periods"]) == len(L), "period-ledger length")
    total_plan = Q(0)
    rows = []
    for t, row in enumerate(event["periods"]):
        need(row["period"] == t, "period index ordering")
        qstr(row, "raw_charge_sum_exact", R[t], "period raw charge sum")
        qstr(row, "projected_charge_sum_exact", P[t], "period projected charge sum")
        qstr(row, "native_minus_raw_charge_exact", L[t] - R[t], "period native/raw residual")
        qstr(row, "projected_minus_raw_charge_exact", P[t] - R[t], "period projection residual")
        expected_float = float(L[t])
        need(row["raw_solver_load_kwh"] == expected_float
             and row["raw_solver_load_repr"] == vals["raw_load_repr"][t]
             and math.isfinite(float(row["raw_solver_load_repr"]))
             and float(row["raw_solver_load_repr"]) == row["raw_solver_load_kwh"],
             "period raw native load representation")
        if H is not None:
            h = H[t]
            qstr(row, "plan_minus_projected_exact", h - P[t], "period plan/projected residual")
            qstr(row, "plan_minus_native_exact", h - L[t], "period plan/native residual")
            need(row["physical_plan_load_kwh"] == float(h)
                 and row["physical_plan_load_repr"] == repr(float(h)),
                 "period materialized load representation")
            total_plan += abs(h - P[t])
        rows.append(row)
    return total_plan


def verify_projection_stage(event, expected, stage, H=None, I=None, J=None, T=None):
    need(event["event"] == "charge_projection" and event["stage"] == stage,
         f"projection stage {stage}")
    need(event["policy"] == POLICY and event["shared_negative_normalizer_policy"] == SHARED_POLICY,
         "projection policy identities")
    need(event["budget_kwh"] == 1e-8 and Q(event["budget_exact"]) == CORRECTION_BUDGET,
         "projection exact budget")
    for key, value in [("negative_l1_exact", expected["N"]),
                       ("orphan_positive_l1_exact", expected["O"]),
                       ("raw_to_projected_l1_exact", expected["raw_to_projected"]),
                       ("raw_load_row_residual_l1_exact", expected["raw_row_l1"])]:
        qstr(event, key, value, f"{stage} projection")
    float_equal(event, "raw_to_projected_l1_kwh", expected["raw_to_projected"],
                f"{stage} projection")
    need(event["changes"] == expected["changes"], f"{stage} full changed-key ledger")
    if stage == "before_budget":
        verify_periods(event, expected)
        need("accepted" not in event and "pre_decode_total_exact" not in event,
             "pre-budget record remains pre-budget")
    else:
        plan_l1 = verify_periods(event, expected, H)
        qstr(event, "plan_sum_residual_l1_exact", plan_l1, f"{stage} plan sum")
        need(Q(event["pre_decode_total_exact"]) == expected["N"] + expected["O"]
             + expected["raw_row_l1"] + plan_l1,
             f"{stage} pre-decode total")
        need(event["pre_decode_accepted"] is
             (expected["N"] + expected["O"] + expected["raw_row_l1"] + plan_l1 <= CORRECTION_BUDGET),
             f"{stage} pre-decode admission")
    if I is not None:
        qstr(event, "interval_capacity_excess_exact", I, f"{stage} interval capacity")
        qstr(event, "session_capacity_excess_exact", J, f"{stage} session capacity")
        total = expected["N"] + expected["O"] + expected["raw_row_l1"] + plan_l1 + I + J
        qstr(event, "pre_replay_total_exact", total, f"{stage} pre-replay total")
        need(event["pre_replay_accepted"] is (total <= CORRECTION_BUDGET),
             f"{stage} pre-replay admission")
    if T is not None:
        replay_l1 = sum((abs(qfloat(t) - qfloat(h)) for t, h in zip(T, H)), Q(0))
        qstr(event, "replay_load_residual_l1_exact", replay_l1, "final replay load residual")
        total = expected["N"] + expected["O"] + expected["raw_row_l1"] + plan_l1 + I + J + replay_l1
        qstr(event, "whole_incumbent_total_exact", total, "whole-incumbent budget")
        float_equal(event, "whole_incumbent_total_kwh", total, "whole-incumbent budget")
        qstr(event, "remaining_budget_exact", CORRECTION_BUDGET - total, "remaining budget")
        need(event["accepted"] is True and total <= CORRECTION_BUDGET,
             "final whole-incumbent admission")
    return locals().get("plan_l1", Q(0))


def verify_decoder(raw, expected, decoded, plan):
    case = plan["_case"] if "_case" in plan else None
    # The caller removes the private context key before comparing serialized data.
    case = case or raw["case"]
    grid, modes = raw["grid"], case["movements"]
    owners = raw["owners"]
    expected_charges, interval_rows = [], []
    I = J = Q(0)
    for k, g in enumerate(grid):
        rows = []
        for (j, kk), amount in expected["projected"].items():
            if kk == k and amount > 0:
                mid = modes[j]["id"]
                need(mid in owners and raw["x"][j] > Q(1, 2), "projected energy has selected owner")
                rows.append((owners[mid], mid, amount))
        if not rows:
            continue
        rows.sort()
        energy_total = sum((row[2] for row in rows), Q(0))
        cap = Q(g["rate_kw"]) * (Q(g["end"]) - Q(g["start"])) / 60
        excess = max(Q(0), energy_total - cap)
        I += excess
        prefix = Q(0)
        start = float(g["start"])
        for n, (vehicle, mid, amount) in enumerate(rows):
            prefix += amount
            end = float(g["end"]) if n == len(rows)-1 else float(Q(g["start"]) +
                (Q(g["end"]) - Q(g["start"])) * prefix / energy_total)
            need(start < end <= g["end"], "positive representable serial interval")
            session_cap = Q(g["rate_kw"]) * (qfloat(end)-qfloat(start)) / 60
            session_excess = max(Q(0), amount-session_cap)
            J += session_excess
            expected_charges.append({"vehicle": vehicle, "movement": mid, "connector": 0,
                "start_min": start, "end_min": end, "grid_kwh": float(amount)})
            start = end
        interval_rows.append({"interval": k, "start_min": g["start"], "end_min": g["end"],
            "grid_kwh": float(energy_total), "capacity_kwh": float(cap),
            "capacity_excess_kwh": float(excess), "capacity_excess_exact": str(excess),
            "saturated_roundoff_adjustment": excess > 0})
    need(decoded["event"] == "serial_decoding"
         and decoded["endpoint_rule"] == "exact-energy-proportional-full-interval",
         "serial decoder identity")
    need(decoded["policy"] == SHARED_POLICY and decoded["budget_kwh"] == 1e-8,
         "serial decoder retains shared policy")
    need(decoded["charges"] == expected_charges == plan["charges"],
         "all retained projected energies and serial endpoints")
    need(decoded["intervals"] == interval_rows, "exact interval capacity ledger")
    for field, val in [("capacity_excess", I), ("materialized_session_excess", J),
                       ("combined_roundoff", expected["N"]+expected["O"]+J)]:
        qstr(decoded, field+"_exact", val, f"decoder {field}")
        float_equal(decoded, field+"_kwh", val, f"decoder {field}")
    need(expected["N"] + expected["O"] + I + J <= CORRECTION_BUDGET,
         "raw normalization and decoder capacity corrections within budget")
    return I, J


def objective_check(cell, raw, start, stats, plan, event):
    c = cell["case"]
    modes = c["movements"]
    starts = sum((raw["x"][j] for j, m in enumerate(modes) if m["kind"] == "pullout"), Q(0))
    duration = sum((raw["x"][j] * sum((Q(l["arrive_min"])-Q(l["depart_min"]) for l in m["legs"]), Q(0))
                    for j, m in enumerate(modes)), Q(0))
    ops = Q(c["vehicle_cost"])*starts + Q(c["deadhead_cost_per_min"])*duration
    L, T = raw["native_load"], [qfloat(v) for v in plan["replay"]["load"]]
    need(event["event"] == "objective_reconstruction" and event["round"] == start["round"],
         "objective event identity")
    near(event["native_incumbent"], stats["incumbent"], "objective event solver incumbent", 1e-6)
    if cell["objective"] == "pricing":
        prices = list(map(Q, cell["prices"]))
        raw_obj = ops + sum((p*l for p, l in zip(prices, L)), Q(0))
        replay_obj = ops + sum((p*t for p, t in zip(prices, T)), Q(0))
        delta = sum((p*(t-l) for p, t, l in zip(prices, T, L)), Q(0))
        qstr(event, "charge_correction_objective_delta_exact", delta, "pricing objective delta")
        near(event["charge_correction_objective_delta"], float(delta), "pricing objective delta", 1e-12)
        near(event["raw_solver_load_objective"], float(raw_obj), "raw pricing objective", 1e-6)
        near(event["linear_objective"], float(replay_obj), "replayed pricing objective", 1e-6)
        return {"raw_objective": raw_obj, "physical_objective": replay_obj,
                "charge_delta": delta, "pwl_delta": None, "true_delta": None, "ops": ops}
    tangents = start["tangents"]
    def envelope(load):
        return sum((max(Q(slope)*x+Q(intercept) for slope, intercept in rows)
                    for x, rows in zip(load, tangents)), Q(0))
    def true_cost(load):
        return sum((Q(a)*x+Q(b)*x*x/2 for a, b, x in zip(cell["a"], cell["b"], load)), Q(0))
    raw_pwl = ops + envelope(L)
    physical_pwl = ops + envelope(T)
    raw_true = ops + true_cost(L)
    physical_true = ops + true_cost(T)
    pwl_delta, true_delta = physical_pwl-raw_pwl, physical_true-raw_true
    qstr(event, "pwl_charge_correction_delta_exact", pwl_delta, "planner PWL objective delta")
    qstr(event, "true_charge_correction_delta_exact", true_delta, "planner true objective delta")
    near(event["pwl_charge_correction_delta"], float(pwl_delta), "planner PWL objective delta", 1e-12)
    near(event["true_charge_correction_delta"], float(true_delta), "planner true objective delta", 1e-12)
    near(event["raw_solver_load_pwl_objective"], float(raw_pwl), "raw PWL objective", 1e-6)
    near(event["pwl_objective"], float(physical_pwl), "replayed PWL objective", 1e-6)
    near(event["raw_solver_load_true_cost"], float(raw_true), "raw true objective", 1e-6)
    near(event["true_cost"], float(physical_true), "replayed true objective", 1e-6)
    return {"raw_objective": raw_pwl, "physical_objective": physical_true,
            "charge_delta": None, "pwl_delta": pwl_delta, "true_delta": true_delta, "ops": ops}


def audit_cell(cell, blob):
    events = blob["events"]
    filtered = copy.deepcopy(blob)
    filtered["events"] = [e for e in events if e["event"] in
                          ("native_start", "native_status", "replayed_iteration")]
    summary = base.audit_cell(cell, filtered)
    by_round = {}
    for e in events:
        by_round.setdefault(e["round"], []).append(e)
    raw_records = []
    for r, es in by_round.items():
        types = [e["event"] for e in es]
        need(types[:2] == ["native_start", "native_status"], "status evidence order")
        start, status = es[0], es[1]
        stats = status["stats"]
        if stats["status"] == "INFEASIBLE":
            need(types == ["native_start", "native_status"], "infeasible call has no fabricated incumbent/projection")
            continue
        expected_types = ["native_start", "native_status", "native_incumbent", "charge_normalization",
                          "charge_projection", "charge_projection", "serial_decoding",
                          "charge_projection", "charge_projection", "objective_reconstruction"]
        if cell["objective"] == "planner":
            expected_types.append("replayed_iteration")
        need(types == expected_types, "complete ordered raw/projection/decode/replay evidence")
        snapshot, norm = es[2], es[3]
        projections = [e for e in es if e["event"] == "charge_projection"]
        before, predecode, prereplay, final = projections
        plan = es[-1]["plan"] if cell["objective"] == "planner" else blob["result"]["result"]["plan"]
        raw = compact.raw_primal(cell, start, stats, snapshot)
        raw["case"] = cell["case"]
        exp = projection_records(raw, snapshot, cell, norm)
        exp["grid"] = raw["grid"]
        exp["cell"] = cell
        need(snapshot["native_matrix"] == NATIVE_MATRIX and snapshot["formulation"] == FORMULATION
             and snapshot["extraction_policy"] == POLICY and snapshot["shared_negative_normalizer_policy"] == SHARED_POLICY,
             "raw V2 matrix and V3 extraction identity")
        need(plan["case_identity"] == cell["case_identity"] and plan["formulation"] == FORMULATION
             and plan["native_matrix"] == NATIVE_MATRIX and plan["extraction_policy"] == POLICY,
             "physical plan V3 identity")
        need(len(plan["load"]) == len(exp["P"]) and len(plan["raw_solver_load"]) == len(exp["L"]),
             "materialized/native load dimensions")
        H = [qfloat(x) for x in plan["load"]]
        T = [qfloat(x) for x in plan["replay"]["load"]]
        for t, val in enumerate(exp["R"]):
            near(plan["raw_charge_load"][t], float(val), "plan raw period charge sum", 1e-12)
            need(plan["raw_solver_load"][t] == float(exp["L"][t]), "plan native period load")
        verify_projection_stage(before, exp, "before_budget")
        plan_l1 = verify_projection_stage(predecode, exp, "before_decoding", H)
        I, J = verify_decoder(raw, exp, es[6], plan)
        verify_projection_stage(prereplay, exp, "before_replay", H, I=I, J=J)
        verify_projection_stage(final, exp, "final", H, I=I, J=J, T=T)
        # The independent physical replay reconstructs SOC, connection ownership,
        # connector power, full replenishment, load, and intrinsic cost from plan data.
        plan_for_replay = dict(plan)
        physical = base.physical(cell, plan_for_replay)
        near(physical["ops"], float(objective_check(cell, raw, start, stats, plan, es[9])["ops"]),
             "independent physical/reconstructed intrinsic cost", 1e-8)
        obj = objective_check(cell, raw, start, stats, plan, es[9])
        # Replay-computed loads must reproduce the plan's saved physical replay.
        for a, b in zip(physical["load"], plan["replay"]["load"]):
            near(a, b, "independent physical replay load", 1e-9)
        # The complete final event and plan ledger are byte-for-byte semantically equal.
        projection_plan = plan["roundoff"]["projection"]
        projection_event = {k: v for k, v in final.items() if k not in ("event", "round", "stage")}
        need(projection_plan == projection_event, "plan/final projection ledger equality")
        norm_plan = {k: v for k, v in norm.items() if k not in ("event", "round")}
        need(plan["roundoff"]["negative_correction"] == norm_plan, "plan negative correction ledger")
        decode_plan = {k: v for k, v in es[6].items() if k not in ("event", "round", "charges")}
        need(plan["roundoff"]["serial_decoding"] == decode_plan, "plan serial decoding ledger")
        need(len(plan["roundoff"]["load_delta_kwh"]) == len(H)
             and len(plan["roundoff"]["native_load_delta_kwh"]) == len(H), "roundoff load vector dimensions")
        for t, (h, p, l, replay) in enumerate(zip(H, exp["P"], exp["L"], T)):
            near(plan["roundoff"]["load_delta_kwh"][t], float(h-qfloat(plan["raw_charge_load"][t])),
                 "materialized minus raw charge load", 1e-12)
            near(plan["roundoff"]["native_load_delta_kwh"][t], float(replay-l), "replay minus native load", 1e-12)
        raw_l1 = max(raw["max_constraint_residual"], Q(0))
        raw_records.append({
            "round": r, "raw_variable_count": raw["variables"],
            "max_raw_constraint_residual": float(raw_l1),
            "raw_objective": str(raw["raw_objective"]),
            "native_load_l1_residual": str(exp["raw_row_l1"]),
            "negative_correction": str(exp["N"]), "positive_orphan_correction": str(exp["O"]),
            "projection_l1": str(exp["raw_to_projected"]), "materialized_plan_l1": str(plan_l1),
            "interval_capacity_excess": str(I), "session_capacity_excess": str(J),
            "replay_load_l1": str(sum((abs(t-h) for t, h in zip(T, H)), Q(0))),
            "whole_incumbent_correction": final["whole_incumbent_total_exact"],
            "raw_to_replay_objective_delta": (str(obj["charge_delta"]) if obj["charge_delta"] is not None
                                                 else {"pwl": str(obj["pwl_delta"]), "true": str(obj["true_delta"])}),
            "physical_paths": raw["paths"], "physical_sessions": len(plan["charges"]),
            "replay_soc_events": physical["soc_events"],
            "max_replay_soc_residual_kwh": physical["worst_soc_residual_kwh"],
        })
    summary["independently_reconstructed_rounds"] = raw_records
    return summary


def load_corruption_inputs(attempt, cells):
    blobs = {}
    for name in cells:
        folder = attempt / name
        blob = {"events": [json.loads(s) for s in (folder / "events.jsonl").read_text().splitlines()],
                "receipt": read(folder / "receipt.json"), "result": read(folder / "result.json")}
        blobs[name] = blob
    return blobs


def corruptions(cells, blobs):
    tested = []
    def event(blob, name, round_num=None):
        return next(e for e in blob["events"] if e["event"] == name and
                    (round_num is None or e["round"] == round_num))
    def projection(blob, stage, round_num=0):
        return next(e for e in blob["events"] if e["event"] == "charge_projection"
                    and e["stage"] == stage and e["round"] == round_num)
    def reject(label, name, mutate):
        c, b = copy.deepcopy(cells[name]), copy.deepcopy(blobs[name])
        mutate(c, b)
        try:
            audit_cell(c, b)
        except (AssertionError, KeyError, TypeError, ValueError, ZeroDivisionError, IndexError) as exc:
            tested.append({"control": label, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("corruption accepted: " + label)
    def alter_first_raw_energy(c, b):
        snap = event(b, "native_incumbent")
        index = snap["mapping"]["grid_energy"][0]["variable"]
        value = float(snap["variables"][index]["solution"]["value"]) + 1.0
        snap["variables"][index]["solution"].update(value=value, repr=repr(value))
    reject("raw SOC equality", "cyclic_planner",
        lambda c,b: event(b,"native_incumbent")["variables"][event(b,"native_incumbent")["mapping"]["soc_after"][0]]["solution"].update(value=3.0,repr="3.0"))
    reject("raw selected coverage", "cyclic_planner",
        lambda c,b: event(b,"native_incumbent")["variables"][event(b,"native_incumbent")["mapping"]["movement_selection"][0]]["solution"].update(value=.5,repr="0.5"))
    reject("raw variable representation", "single_linear",
        lambda c,b: event(b,"native_incumbent")["variables"][0]["solution"].update(repr="9.0"))
    reject("duplicate raw variable mapping", "single_linear",
        lambda c,b: event(b,"native_incumbent")["mapping"]["market_load"].__setitem__(0,0))
    reject("shared interval capacity", "single_linear",
        lambda c,b: event(b,"native_incumbent")["mapping"]["intervals"][-1].update(rate_kw=99))
    reject("native aggregate energy row", "single_linear",
        lambda c,b: event(b,"native_incumbent")["energy_balance"].update(lower_rhs=0))
    reject("missing charge projection stage", "single_linear",
        lambda c,b: b["events"].remove(projection(b,"before_budget")))
    reject("projection policy identity", "joint_planner",
        lambda c,b: projection(b,"before_budget",1).update(policy="native-roundoff-qualification-v2"))
    reject("forged change-key added to zero-correction ledger", "joint_planner",
        lambda c,b: projection(b,"before_budget",1)["changes"].append({"key":[0,0]}))
    reject("raw grid-energy variable altered", "joint_planner", alter_first_raw_energy)
    reject("orphan projection amount altered", "joint_planner",
        lambda c,b: projection(b,"before_budget",1).update(orphan_positive_l1_exact="1"))
    reject("period native/raw residual altered", "joint_planner",
        lambda c,b: projection(b,"before_budget",1)["periods"][1].update(native_minus_raw_charge_exact="1"))
    reject("materialized load residual altered", "joint_planner",
        lambda c,b: projection(b,"before_decoding",1).update(plan_sum_residual_l1_exact="1"))
    reject("interval capacity correction altered", "cyclic_planner",
        lambda c,b: projection(b,"before_replay",0).update(interval_capacity_excess_exact="1"))
    reject("session capacity correction altered", "cyclic_planner",
        lambda c,b: event(b,"serial_decoding",0).update(materialized_session_excess_exact="1"))
    reject("whole incumbent budget altered", "joint_planner",
        lambda c,b: projection(b,"final",1).update(whole_incumbent_total_exact="1"))
    reject("projected positive selected charge removed", "serial_connector",
        lambda c,b: event(b,"serial_decoding",0)["charges"].clear())
    reject("objective correction delta altered", "joint_planner",
        lambda c,b: event(b,"objective_reconstruction",1).update(true_charge_correction_delta_exact="1"))
    reject("physical replay SOC altered", "single_linear",
        lambda c,b: b["result"]["result"]["plan"]["replay"]["soc_trajectories"][0][-1].update(soc_kwh=19))
    reject("native lower bound altered", "single_linear",
        lambda c,b: event(b,"native_status")["stats"].update(lower_bound=23))
    reject("certified interval altered", "single_linear",
        lambda c,b: b["result"]["result"].update(upper=21))
    reject("tangent history altered", "cyclic_planner",
        lambda c,b: event(b,"native_start",0)["tangents"][1][0].__setitem__(0,5))
    reject("rounded tangent formula drift above 1e-12 allowance", "joint_planner",
        lambda c,b: event(b,"native_start",1)["tangents"][1][1].__setitem__(1,
            event(b,"native_start",1)["tangents"][1][1][1]+1e-9))
    reject("expected infeasibility relabelled", "halfminute_capacity_failure",
        lambda c,b: b["result"]["result"].update(status="certified"))
    reject("infeasible cell fabricated incumbent", "terminal_capacity_failure",
        lambda c,b: b["events"].append({"event":"native_incumbent","round":0}))
    reject("infeasible input feasibility target altered", "fixed_reserve_one_bus",
        lambda c,b: c["case"].update(battery_kwh=c["case"]["battery_kwh"]+1))
    return tested


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repository", type=Path, default=next((p for p in HERE.parents if (p/".git").exists()), None))
    ap.add_argument("--attempt", type=Path, default=HERE.parent)
    ap.add_argument("--out", type=Path, default=HERE/"audit-report.json")
    args = ap.parse_args()
    repo, attempt, out = args.repository.resolve(), args.attempt.resolve(), args.out.resolve()
    need(not out.exists() and out.parent == (attempt/"review").resolve(),
         "review report must be a new file inside new review subtree")
    start_time = time.perf_counter()
    manifest_bytes = (attempt/"MANIFEST.json").read_bytes()
    need(digest(manifest_bytes) == MANIFEST_SHA, "pinned original attempt-3 manifest")
    manifest = json.loads(manifest_bytes)
    original_files = manifest["files"]
    def preserve():
        for rel, row in original_files.items():
            data = (attempt/rel).read_bytes()
            need(len(data) == row["bytes"] and digest(data) == row["sha256"], "original file " + rel)
        need(digest((attempt/"MANIFEST.json").read_bytes()) == MANIFEST_SHA, "original manifest remains unchanged")
    preserve()
    actual = {str(p.relative_to(attempt)) for p in attempt.rglob("*") if p.is_file()
              and "review" not in p.relative_to(attempt).parts and p.name != "MANIFEST.json"}
    need(actual == set(original_files), "manifest has exact original file coverage")
    need(len(original_files) == 142 and sum(x["bytes"] for x in original_files.values()) == 1309561,
         "sealed original archive dimensions")
    frozen = read(attempt/"frozen.json")
    full_commit = subprocess.check_output(["git","-C",str(repo),"rev-parse",COMMIT]).decode().strip()
    need(frozen["freeze_label"] == COMMIT and full_commit.startswith(frozen["freeze_label"])
         and frozen["protocol"] == "native-pathflow-qualification-20260927-v3-orphan-projection",
         "frozen commit/protocol identity")
    need(frozen["native_matrix"] == NATIVE_MATRIX and frozen["formulation"] == FORMULATION
         and frozen["extraction_policy"] == POLICY and frozen["shared_negative_normalizer_policy"] == SHARED_POLICY,
         "frozen V2 matrix / V3 extractor split")
    need(len(frozen["source_hashes"]) == 15, "complete pinned source inventory")
    for rel, sha in frozen["source_hashes"].items():
        committed = subprocess.check_output(["git","-C",str(repo),"show",full_commit+":"+rel])
        need(digest(committed) == sha, "source hash at frozen commit: "+rel)
        need(digest((repo/rel).read_bytes()) == sha, "source remains unchanged: "+rel)
    previous = read(repo/"result/native_pathflow/20260927-attempt2/frozen.json")
    need(frozen["controls"] == previous["controls"], "all 20 serialized controls unchanged from attempt 2")
    need(frozen["budget"] == previous["budget"], "all phase/CBC budget fields unchanged from attempt 2")
    need(frozen["target_tolerance"] == previous["target_tolerance"], "target tolerance unchanged from attempt 2")
    need([c["id"] for c in frozen["controls"]] == list(base.TARGETS), "all target controls and order")
    need(sum(1 for x in frozen["controls"] if base.TARGETS[x["id"]] is None) == 4,
         "four independently infeasible analytical targets")
    cells = {c["id"]: c for c in frozen["controls"]}
    summary = read(attempt/"summary.json")
    need(summary["all_pass"] is True and summary["source_hashes_unchanged"] is True,
         "runner summary reports complete pass and stable sources")
    need(summary["protocol"] == frozen["protocol"], "summary protocol identity")
    records = []
    blobs = {}
    target_status = {}
    for c in frozen["controls"]:
        name = c["id"]
        folder = attempt/name
        inp = read(folder/"input.json")
        need({k:v for k,v in inp.items() if k in c} == c and inp["budget"] == frozen["budget"],
             "exact input and full budget: "+name)
        need(inp["source_hashes"] == frozen["source_hashes"], "input source receipt: "+name)
        receipt = read(folder/"receipt.json")
        need(receipt == next(s for s in summary["cells"] if s["cell"] == name), "summary/receipt equality: "+name)
        launch = read(folder/"launch.json")
        need(launch["hard_timeout_s"] == 60 and launch["command"][1:5] ==
             ["-m", "experiments.native_pathflow_qualification", "--worker", name],
             "worker launch command and hard timeout: "+name)
        need(receipt["native_calls_started"] == receipt["native_calls_returned"] and
             receipt["native_accounting_complete"] and not receipt["hard_timeout"] and
             not receipt["evidence_issues"], "returned/accounted native calls: "+name)
        ev = [json.loads(line) for line in (folder/"events.jsonl").read_text().splitlines()]
        results = read(folder/"result.json")
        blob = {"events": ev, "receipt": receipt, "result": results}
        blobs[name] = blob
        expected_infeasible = base.TARGETS[name] is None
        expected_calls = sum(1 for e in ev if e["event"] == "native_start")
        need(expected_calls == receipt["native_calls_started"], "event/call count: "+name)
        statuses = [e["stats"]["status"] for e in ev if e["event"] == "native_status"]
        need(len(statuses) == expected_calls and all(x in ("OPTIMAL", "INFEASIBLE") for x in statuses),
             "native status count/labels: "+name)
        if expected_infeasible:
            need(name in EXPECTED_INFEASIBLE and statuses == ["INFEASIBLE"],
                 "expected infeasible status retained: "+name)
            need(results["result"]["status"] == "infeasible" and not any(e["event"] == "native_incumbent" for e in ev),
                 "infeasible result contains no fabricated incumbent: "+name)
        else:
            need(name not in EXPECTED_INFEASIBLE and statuses and all(x == "OPTIMAL" for x in statuses),
                 "expected numerical result status: "+name)
            need(results["result"]["status"] == "certified" and receipt["pass"] and receipt["returncode"] == 0,
                 "certified receipt/result: "+name)
        target_status[name] = statuses
        records.append(audit_cell(c, blob))
    need(set(EXPECTED_INFEASIBLE) == {name for name in cells if base.TARGETS[name] is None},
         "exact set of four expected infeasibilities")
    calls = sum(x["native_calls_returned"] for x in summary["cells"])
    need(calls == 35 and sum(target_status[n].count("INFEASIBLE") for n in target_status) == 4,
         "global 35-returned-call accounting and 4 infeasibilities")
    cell_wall = sum(r["wall_s"] for r in summary["cells"])
    need(0 <= summary["elapsed_s"] - cell_wall <= 1.0,
         "summary supervisor elapsed includes cell wall totals and bounded dispatch overhead")
    controls = corruptions(cells, blobs)
    need(len(controls) >= 25 and all(x["rejected"] for x in controls), "all corruption controls rejected")
    rounds = [r for cell in records for r in cell.get("independently_reconstructed_rounds", [])]
    positive = [r for cell in records for r in cell.get("independently_reconstructed_rounds", [])
                if Q(r["positive_orphan_correction"]) > 0]
    report = {
        "audit_status": "PASS: independent attempt-3 numerical result audit; 20/20 controls admitted",
        "compact_attempt3_gate_passed": True,
        "downstream_admission": False,
        "scope": "Independent no-author-import reconstruction of frozen inputs, V2 raw matrix, all native rows/objectives/bounds, V3 projection ledger, decoder/replay, and four expected infeasibilities. This admits only the synthetic compact attempt-3 policy; it does not qualify hull integration or operational use.",
        "frozen_commit": full_commit,
        "original_manifest_sha256": MANIFEST_SHA,
        "original_files": len(original_files),
        "original_bytes": sum(x["bytes"] for x in original_files.values()),
        "frozen_source_count": len(frozen["source_hashes"]),
        "source_hashes_unchanged": True,
        "unchanged_from_attempt2": {"controls": True, "budget": True, "target_tolerance": True},
        "counts": {"controls": len(records), "passed": sum(x["original_pass"] for x in records),
                   "certified": sum(x["status"] == "certified" for x in records),
                   "expected_infeasible": sum(x["status"] == "infeasible" for x in records),
                   "native_calls": calls, "raw_incumbents": len(rounds),
                   "raw_variable_values": sum(r["raw_variable_count"] for r in rounds),
                   "projected_positive_orphan_rounds": len(positive),
                   "corruption_controls_rejected": len(controls)},
        "positive_orphan_examples": [{k:r[k] for k in ("round", "positive_orphan_correction", "whole_incumbent_correction")}
                                     for cell in records for r in cell.get("independently_reconstructed_rounds", [])
                                     if Q(r["positive_orphan_correction"]) > 0],
        "native_status_counts": dict(Counter(s for values in target_status.values() for s in values)),
        "cells": records,
        "corruption_controls": controls,
        "independence": "Uses Python standard-library exact fractions and the preserved separate attempt-2 independent fixture/matrix/energy-band auditors, version-adjusted locally for the new extraction-policy tag. No egglab/experiments author module, solver, or optimization was imported or invoked. Four expected infeasible cells were checked for exact status/result preservation and absence of fabricated incumbent events.",
        "audit_elapsed_s": time.perf_counter() - start_time,
    }
    preserve()
    with out.open("x") as f:
        json.dump(base.pack(report), f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"audit_status": report["audit_status"], "out": str(out),
                      "counts": report["counts"], "original_files": report["original_files"],
                      "original_bytes": report["original_bytes"]}, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
