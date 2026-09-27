"""Prospectively fixed three-service frontier for certified column reuse.

This is a synthetic, bounded experiment, not the protected evaluation campaign.
Only physical columns cross tariff transitions; every certificate is fresh.
See doc/REUSE_FRONTIER_PROTOCOL_20260927.md for the complete design and limits.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
from contextlib import contextmanager

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from experiments.reuse_qualification import (digest, write_json, runtime_evidence,
                                               replay_column, shifted_price)

SCHEMA = "egg-reuse-frontier-v1"
ARMS = ("cold", "retained", "retained_shift")
FIXTURES = ("depleted_f20", "depleted_f26", "replenished_two_bus")
CONFIG = {
    "schema": SCHEMA, "threads": 1, "process_cap_s": 900,
    "state_cap_s": 60, "reference_cap_s": 60, "solve_cap_s": 10,
    "pricing_call_cap": 48, "pool_cap": 240,
    "epsilon": 0.01, "pwl_tol": 0.001, "pricing_mip_gap": 1e-9,
    "projection_tolerance": 1e-7, "reference_structure_cap": 256,
    "reference_interval_guard": 1e-6, "seed": None,
    "states": ["base", "unchanged", "early_cheap", "late_cheap", "return_base"],
    "tariff_offsets": [0.0, 0.0, 0.25, -0.25, 0.0],
    "a_level": 0.3, "b": 0.2, "U": 0.0,
    "fixtures": list(FIXTURES), "arms": list(ARMS),
    "trip_intervals_min": [[0, 60], [180, 240], [360, 420]],
    "trip_energy_kwh": 15.0, "battery_kwh": 20.0,
    "charge_power_kw": 10.0, "slot_min": 60,
    "max_vehicles": 2, "terminal_markers_min": [600, 660],
    "vehicle_costs": {"depleted_f20": 20.0, "depleted_f26": 26.0,
                       "replenished_two_bus": 10.0},
}


def fixture(name):
    from egglab.instance import Instance, Trip
    if name not in FIXTURES:
        raise ValueError("Unknown frozen fixture")
    replenished = name == "replenished_two_bus"
    trips = [Trip(f"t{i}", start, end, "D", "D", 15.0)
             for i, (start, end) in enumerate(CONFIG["trip_intervals_min"])]
    if replenished:
        trips += [Trip(f"marker{i}", 600, 660, "D", "D", 0.0) for i in range(2)]
    return Instance(name=f"{SCHEMA}-{name}", trips=trips, depot="D", dh_min={}, dh_kwh={},
                    battery_kwh=20.0, soc0_kwh=20.0, soc_min_kwh=0.0,
                    soc_end_kwh=20.0 if replenished else 0.0,
                    charge_power_kw=10.0, n_slots=11 if replenished else 7,
                    slot_min=60, max_vehicles=2,
                    vehicle_fixed_cost=CONFIG["vehicle_costs"][name], dh_cost_per_min=1.0,
                    meta={"source": SCHEMA, "seed": None, "fixture": name,
                          "terminal_policy": "two explicit replenishment markers" if replenished
                          else "depletion allowed"})


def market_for_state(name, index):
    from egglab.market import AffineMarket
    if not 0 <= index < len(CONFIG["states"]):
        raise ValueError("Unknown frozen state")
    inst = fixture(name)
    # Early charging slots are cheaper at positive offset; later slots dearer.
    # The same split at slot 4 is used in every case and every arm.
    direction = [(-1.0 if 1 <= t <= 3 else 1.0 if t >= 4 else 0.0)
                 for t in range(inst.n_slots)]
    a = [CONFIG["a_level"] + CONFIG["tariff_offsets"][index] * v for v in direction]
    return AffineMarket(a, [CONFIG["b"]] * inst.n_slots, [0.0] * inst.n_slots,
                        name=f"{name}-{CONFIG['states'][index]}")


def import_previous(inst, previous, name, arm, index):
    from egglab import b2a2
    if (not isinstance(previous, dict) or previous.get("schema") != SCHEMA
            or previous.get("config_sha256") != digest(CONFIG)
            or previous.get("fixture") != name or previous.get("arm") != arm
            or previous.get("state_index") != index - 1
            or previous.get("status") != "certified"
            or previous.get("instance_hash") != inst.hash()
            or previous.get("market_hash") != b2a2.market_hash(market_for_state(name, index - 1))):
        raise ValueError("Previous state is not the same arm/fixture's certified predecessor")
    columns, keys = [], set()
    for col in previous["columns"]:
        checked = replay_column(inst, col)
        if checked["column_key"] not in keys:
            columns.append(checked)
            keys.add(checked["column_key"])
    if not columns or len(columns) > CONFIG["pool_cap"]:
        raise ValueError("Invalid retained pool size")
    return columns


def projection_novel(column, columns):
    tol = CONFIG["projection_tolerance"]
    return not any(abs(float(column["ops_cost"]) - float(old["ops_cost"])) <= tol
                   and len(column["load"]) == len(old["load"])
                   and max(abs(float(x) - float(y)) for x, y in
                           zip(column["load"], old["load"])) <= tol for old in columns)


def replay_master(inst, market, columns, rmp):
    """Rebuild each clean upper bound from physical columns and weights."""
    weights = rmp["lambdas"]
    if (len(weights) != len(columns) or any(not math.isfinite(w) or w < -1e-8 for w in weights)
            or abs(sum(weights) - 1.0) > 1e-7):
        raise ValueError("Invalid master convex weights")
    load = [sum(w * col["load"][t] for w, col in zip(weights, columns))
            for t in range(inst.n_slots)]
    ops = sum(w * col["ops_cost"] for w, col in zip(weights, columns))
    true = ops + market.system_delta_true(load)
    if (max(abs(x-y) for x, y in zip(load, rmp["L"])) > 1e-7
            or abs(true - rmp["ub"]) > 1e-6
            or rmp["z_model"] > true + 1e-6):
        raise ValueError("Master upper-bound replay mismatch")
    if inst.soc_end_kwh == inst.soc0_kwh and abs(sum(load)-45.0) > 1e-6:
        raise ValueError("Replenished fleet does not conserve total service energy")
    return {"load": load, "intrinsic_cost": ops, "true_objective": true}


@contextmanager
def bounded_solves(deadline, records, checkpoint=lambda: None):
    """Cap both LP-first and MIP phases; preserve original imported aliases."""
    from egglab import b2a2, evsp, solver
    original = solver.optimize
    aliases = [(module, module.optimize) for module in (solver, b2a2, evsp)]

    def optimize(model, *args, **kwargs):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("State admission deadline reached")
        cap = min(CONFIG["solve_cap_s"], remaining)
        model.threads = 1
        model.max_seconds = cap
        # Tight numerical tolerances preserve the physical replay contract.
        model.infeas_tol = 1e-8
        model.opt_tol = 1e-8
        kwargs["time_limit_s"] = min(cap, kwargs.get("time_limit_s") or cap)
        started = time.perf_counter()
        row = {"model": model.name, "model_time_cap_s": cap, "status": "started"}
        records.append(row)
        checkpoint()
        try:
            result = original(model, *args, **kwargs)
        except Exception as exc:
            row.update(elapsed_s=time.perf_counter() - started, status="EXCEPTION",
                       error=f"{type(exc).__name__}: {exc}")
            checkpoint()
            raise
        row.update(elapsed_s=time.perf_counter() - started, **result.to_dict())
        checkpoint()
        if result.backend != "CBC" or result.extra.get("threads") != 1:
            raise RuntimeError("Unexpected solver backend or thread count")
        if result.status != "OPTIMAL":
            raise RuntimeError(f"Unresolved solve: {result.status}")
        if time.monotonic() > deadline:
            raise TimeoutError("State deadline reached during solve")
        return result

    for module, _ in aliases:
        module.optimize = optimize
    try:
        yield
    finally:
        for module, saved in aliases:
            module.optimize = saved


def solve_state(name, arm, index, previous, output):
    from egglab import b2a2, solver
    from egglab.regimes import solve_taker
    solver._BACKEND_CACHE[:] = ["CBC"]  # Do not initialize Gurobi.
    inst, market = fixture(name), market_for_state(name, index)
    start, cpu_start = time.perf_counter(), time.process_time()
    result = {
        "schema": SCHEMA, "config_sha256": digest(CONFIG), "arm": arm,
        "fixture": name, "state_index": index, "instance_hash": inst.hash(),
        "instance": inst.canonical(),
        "market_hash": b2a2.market_hash(market), "status": "started",
        "market": {"a": list(market.a), "b": list(market.b), "U": list(market.U)},
        "columns": [], "oracle_events": [], "master_events": [],
        "iterations": [], "native_solves": [], "previous_state": None,
        "bound_source": "fresh clean RMP dual plus full-pricing lower bound only",
    }
    deadline = time.monotonic() + CONFIG["state_cap_s"] - 1.0
    try:
        replay_start = time.perf_counter()
        if arm != "cold" and index > 0:
            result["columns"] = import_previous(inst, previous, name, arm, index)
            result["previous_state"] = {"index": index - 1, "digest": digest(previous)}
        elif previous is not None:
            raise ValueError("Cold initialization cannot import a previous state")
        result["initial_replay_wall_s"] = time.perf_counter() - replay_start
        result["imported_column_keys"] = [c["column_key"] for c in result["columns"]]
        columns = result["columns"]
        keys = set(result["imported_column_keys"])
        # Fresh-state initialization is explicit; prior lower bounds/tangents
        # cannot enter this local state even if predecessor JSON contains them.
        tangents, lb_best, previous_ub = [], -math.inf, math.inf
        pricing_gap = CONFIG["pricing_mip_gap"]

        def pricing(prices, purpose):
            if len(result["oracle_events"]) >= CONFIG["pricing_call_cap"]:
                raise RuntimeError("Pricing-call budget exhausted")
            t0 = time.perf_counter()
            pending = {"call": len(result["oracle_events"]), "purpose": purpose,
                       "prices": list(map(float, prices)), "status": "started"}
            result["oracle_events"].append(pending)
            write_json(output, result)
            sol = solve_taker(inst, prices, max_mip_gap=pricing_gap,
                              time_limit_s=CONFIG["solve_cap_s"])
            b2a2.canonicalize_pricing_solution(inst, sol, prices)
            col = replay_column(inst, b2a2.column_from_solution(inst, sol))
            upper = b2a2.pricing_incumbent(col, sol, prices)
            lower = float(sol.stats.bound)
            if not math.isfinite(lower) or lower > upper + 1e-6:
                raise RuntimeError("Pricing bound does not enclose incumbent")
            event = {"call": pending["call"], "status": "completed", "purpose": purpose,
                     "prices": list(map(float, prices)), "upper": upper,
                     "lower": lower, "novel": col["column_key"] not in keys,
                     "projection_novel": projection_novel(col, columns), "column": col,
                     "column_key": col["column_key"],
                     "elapsed_s": time.perf_counter() - t0,
                     "replay_ok": True, "solver": sol.stats.to_dict(),
                     "used_for_lower_bound": purpose == "clean"}
            pending.update(event)
            return col, pending

        def admit(col):
            if col["column_key"] not in keys:
                if len(columns) >= CONFIG["pool_cap"]:
                    raise RuntimeError("Frozen pool cap reached; no hidden eviction")
                columns.append(col)
                keys.add(col["column_key"])

        with bounded_solves(deadline, result["native_solves"], lambda: write_json(output, result)):
            if not columns:
                col, _ = pricing(market.price([0.0] * market.n_slots), "cold_seed")
                admit(col)
            if arm == "retained_shift" and index > 0:
                q = shifted_price(previous["last_clean_price"],
                                  market_for_state(name, index - 1), market)
                col, event = pricing(q, "analytic_proposal")
                # No proposal lower bound or stale sigma enters the certificate.
                result["proposal"] = copy.deepcopy(event)
                admit(col)
            while len(result["oracle_events"]) < CONFIG["pricing_call_cap"]:
                rmp = b2a2.solve_rmp(inst, market, columns, tangents,
                                    pwl_tol=CONFIG["pwl_tol"],
                                    solve_id_prefix=f"{arm}-s{index}-i{len(result['iterations'])}")
                tangents = rmp["tangent_points"]
                rmp["column_keys"] = [c["column_key"] for c in columns]
                rmp["physical_replay"] = replay_master(inst, market, columns, rmp)
                # The local tangent list is extended after continuing pricing.
                # Freeze the log at solve return, before that later mutation.
                result["master_events"].append(copy.deepcopy(rmp))
                if rmp["ub"] > previous_ub + CONFIG["pwl_tol"] + 1e-6:
                    raise RuntimeError("Clean RMP upper bound increased")
                previous_ub = rmp["ub"]
                prices = [-float(pi) for pi in rmp["pi"]]
                col, event = pricing(prices, "clean")
                reduced_lower = event["lower"] - rmp["sigma"]
                reduced_upper = event["upper"] - rmp["sigma"]
                lower = rmp["z_model"] + min(0.0, reduced_lower)
                lb_best = max(lb_best, lower)
                gap = rmp["ub"] - lb_best
                if gap < -1e-6:
                    raise RuntimeError("Negative certificate interval")
                row = {"lower": lower, "lb_best": lb_best, "upper": rmp["ub"],
                       "gap": gap, "reduced_lower": reduced_lower,
                       "reduced_upper": reduced_upper, "oracle_call": event["call"],
                       "pwl_slack": rmp["ub"] - rmp["z_model"],
                       "master_dual_price": prices, "sigma": rmp["sigma"]}
                result["iterations"].append(row)
                result["last_clean_price"] = prices
                # Keep every replay-valid novel column, including a terminal
                # pricing column; this policy is identical in all three arms.
                admit(col)
                write_json(output, result)
                if gap <= CONFIG["epsilon"]:
                    result.update(status="certified", lower=lb_best, upper=rmp["ub"],
                                  gap=gap, final_load=rmp["L"],
                                  reference_validation="pending separate reference phase")
                    break
                if not event["novel"] and reduced_upper < -b2a2.RC_TOL:
                    raise RuntimeError("Duplicate has negative reduced cost")
                if reduced_lower < -b2a2.RC_TOL and reduced_upper >= -b2a2.RC_TOL:
                    pricing_gap = max(pricing_gap / 100.0, 1e-12)
                else:
                    tangents.append(list(rmp["L"]))
            else:
                raise RuntimeError("Pricing-call budget exhausted")
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc())
    finally:
        result["oracle_calls"] = len(result["oracle_events"])
        result["calls_clean"] = sum(e["purpose"] == "clean" for e in result["oracle_events"])
        result["calls_seed"] = sum(e["purpose"] == "cold_seed" for e in result["oracle_events"])
        result["calls_proposal"] = sum(e["purpose"] == "analytic_proposal" for e in result["oracle_events"])
        try:
            result["runtime"] = runtime_evidence()
        except Exception as exc:
            result["runtime_error"] = f"{type(exc).__name__}: {exc}"
            result["status"] = "failed"
        result["worker_wall_s"] = time.perf_counter() - start
        result["worker_cpu_s"] = time.process_time() - cpu_start
        result["optimizer_wrapper_elapsed_s"] = sum(s.get("elapsed_s", 0.0)
                                                    for s in result["native_solves"])
        result["solver_wall_s"] = sum(s.get("wall_s", 0.0) + s.get("lp_wall_s", 0.0)
                                      for s in result["native_solves"])
        write_json(output, result)
    return result


def solve_reference(name, index, output):
    """Separate complete-structure formulation; never feeds a comparison arm."""
    from experiments import physical_qualification as physical
    from egglab.enumerate_tiny import enumerate_structures
    inst, market = fixture(name), market_for_state(name, index)
    result = {"schema": SCHEMA, "fixture": name, "state_index": index,
              "instance": inst.canonical(), "instance_hash": inst.hash(),
              "market": {"a": list(market.a), "b": list(market.b), "U": list(market.U)},
              "status": "started", "calls": [], "config_sha256": digest(CONFIG)}
    start = time.perf_counter()
    try:
        structures = enumerate_structures(inst)
        if not structures or len(structures) > CONFIG["reference_structure_cap"]:
            raise ValueError("Reference enumeration admission cap exceeded")
        result["structures"] = structures
        write_json(output, result)
        result["ch"] = physical.solve(inst, market, structures, None, True,
                                       start + CONFIG["reference_cap_s"] - 1, result["calls"])
        if result["ch"]["status"] != "OPTIMAL":
            raise ValueError("Expected feasible reference was not optimal")
        result["status"] = "reference_complete"
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc())
    finally:
        result["wall_s"] = time.perf_counter() - start
        try:
            result["runtime"] = runtime_evidence()
        except Exception as exc:
            result["runtime_error"] = str(exc)
            result["status"] = "failed"
        write_json(output, result)
    return result


def check_reference(state, reference):
    """Overlap is required, with an explicit numerical guard, not exact proof."""
    from egglab import b2a2
    name, index = state["fixture"], state["state_index"]
    expected_market = market_for_state(name, index)
    expected_payload = {"a": list(expected_market.a), "b": list(expected_market.b),
                        "U": list(expected_market.U)}
    if (state.get("status") != "certified" or reference.get("status") != "reference_complete"
            or reference.get("fixture") != name or reference.get("state_index") != index
            or reference.get("instance_hash") != state.get("instance_hash")
            or state.get("instance_hash") != fixture(name).hash()
            or state.get("config_sha256") != digest(CONFIG)
            or reference.get("config_sha256") != digest(CONFIG)
            or state.get("market_hash") != b2a2.market_hash(expected_market)
            or state.get("market") != expected_payload
            or reference.get("market") != state.get("market")):
        raise ValueError("Reference identity/status mismatch")
    lower, upper = reference["ch"]["lower"], reference["ch"]["upper"]
    guard = CONFIG["reference_interval_guard"]
    values = [state["lower"], state["upper"], lower, upper]
    if (not all(math.isfinite(v) for v in values) or lower > upper
            or state["lower"] > state["upper"] + guard
            or state["upper"] - state["lower"] > CONFIG["epsilon"] + guard
            or state["lower"] > upper + guard or lower > state["upper"] + guard):
        raise ValueError("Fresh certificate disagrees with complete-structure reference")
    return {"reference_lower": lower, "reference_upper": upper,
            "intervals_overlap_with_guard": True, "guard": guard}


def frozen_sources():
    paths = [Path(__file__), REPO / "doc/REUSE_FRONTIER_PROTOCOL_20260927.md",
             REPO / "src/tests/test_reuse_frontier.py"]
    paths += [REPO / "src/experiments" / f"{name}.py" for name in
              ("reuse_qualification", "physical_qualification")]
    paths += [REPO / "src/egglab" / f"{name}.py" for name in
              ("b2a2", "b2a345", "checkpoint", "evsp", "instance", "market",
               "regimes", "solver", "enumerate_tiny")]
    rel = [str(p.relative_to(REPO)) for p in paths]
    # An accidental unfrozen launch fails before any native import or output.
    subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", "--", *rel],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", *rel], check=True)
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def supervise(output):
    sources = frozen_sources()
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / "frozen-config.json", CONFIG)
    write_json(root / "frozen-fixtures.json", [fixture(n).canonical() for n in FIXTURES])
    head = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    write_json(root / "provenance.json", {
        "head": head, "python": sys.version, "executable": sys.executable,
        "config_sha256": digest(CONFIG), "source_sha256": sources,
        "bound_scope": "numerical CBC/replay-tolerance conditional, not exact arithmetic"})
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1", SLURM_CPUS_PER_TASK="1")
    env.pop("EGGLAB_REQUIRE_GRB", None)
    start = time.monotonic()
    records, references, previous = [], [], {}

    def child(name, index, arm=None, predecessor=None):
        tag = f"{name}-{arm or 'reference'}-s{index}"
        cell = root / tag
        cell.mkdir()
        remain = CONFIG["process_cap_s"] - (time.monotonic() - start)
        row = {"fixture": name, "state_index": index, "arm": arm,
               "result": f"{tag}/state.json"}
        if remain <= 0:
            return {**row, "status": "skipped_budget"}
        result_path = cell / "state.json"
        args = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
                "--fixture", name, "--state", str(index), "--output", str(result_path)]
        if arm:
            args += ["--arm", arm]
        else:
            args += ["--reference"]
        if predecessor:
            args += ["--previous", str(predecessor)]
        t0 = time.perf_counter()
        with (cell / "stdout.txt").open("x") as out, (cell / "stderr.txt").open("x") as err:
            proc = subprocess.Popen(args, cwd=REPO, env=env, stdout=out, stderr=err,
                                    start_new_session=True)
            timed_out = False
            cap = CONFIG["state_cap_s" if arm else "reference_cap_s"]
            try:
                proc.wait(timeout=min(cap, remain))
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        data = {}
        parse_error = None
        if result_path.exists():
            try:
                data = json.loads(result_path.read_text())
            except (ValueError, OSError) as exc:
                parse_error = str(exc)
        target = "certified" if arm else "reference_complete"
        good = proc.returncode == 0 and data.get("status") == target
        row.update(worker_exit=proc.returncode, timed_out=timed_out,
                   complete_wall_s=time.perf_counter()-t0, subprocess_cap_s=min(cap, remain),
                   status=target if good else "failed", parse_error=parse_error,
                   accounting_complete=good)
        if arm:
            # Pending evidence is a lower bound on observed work after a kill;
            # never substitute zero calls for an uncompleted worker.
            row["pricing_attempts_observed"] = len(data.get("oracle_events", []))
            row["optimizer_wrapper_attempts_observed"] = len(data.get("native_solves", []))
        else:
            row["reference_native_calls_observed"] = len(data.get("calls", []))
        for key in ("lower", "upper", "gap", "oracle_calls", "calls_clean", "calls_seed",
                    "calls_proposal", "solver_wall_s", "worker_cpu_s", "runtime"):
            if key in data:
                row[key] = data[key]
        if arm and good:
            events = data["oracle_events"]
            row["clean_calls_after_first"] = max(0, data["calls_clean"] - 1)
            row["proposal_projection_novel"] = sum(e.get("projection_novel", False)
                for e in events if e["purpose"] == "analytic_proposal")
            row["optimizer_wrapper_calls"] = len(data["native_solves"])
            row["clean_master_lp_calls"] = sum(len(m["master_solves"]) for m in data["master_events"])
        write_json(cell / "process.json", row)
        return row

    # Complete all comparison arms before the references. No reference solution
    # can influence initialization, proposals, column admission or stopping.
    for name in FIXTURES:
        for index in range(len(CONFIG["states"])):
            # Prospectively rotate ordering to reduce one fixed arm-position bias.
            rotation = (FIXTURES.index(name) + index) % len(ARMS)
            order = ARMS[rotation:] + ARMS[:rotation]
            for arm in order:
                key = (name, arm)
                if arm != "cold" and index > 0 and previous.get(key) is None:
                    row = {"fixture": name, "arm": arm, "state_index": index,
                           "status": "skipped_predecessor"}
                else:
                    row = child(name, index, arm, previous.get(key) if arm != "cold" and index else None)
                    previous[key] = root / row["result"] if row["status"] == "certified" else None
                records.append(row)
                write_json(root / "summary.json", {"schema": SCHEMA, "complete": False,
                                                     "states": records, "references": references})
    for name in FIXTURES:
        for index in range(len(CONFIG["states"])):
            row = child(name, index)
            references.append(row)
            if row["status"] == "reference_complete":
                reference = json.loads((root / row["result"]).read_text())
                for state_row in records:
                    if (state_row["fixture"] == name and state_row["state_index"] == index
                            and state_row["status"] == "certified"):
                        try:
                            state = json.loads((root / state_row["result"]).read_text())
                            state_row["reference_check"] = check_reference(state, reference)
                        except Exception as exc:
                            state_row.update(status="reference_mismatch", reference_error=str(exc))
            write_json(root / "summary.json", {"schema": SCHEMA, "complete": False,
                                                 "states": records, "references": references})
    complete = (len(records) == len(FIXTURES)*len(CONFIG["states"])*len(ARMS)
                and all(r["status"] == "certified" and r.get("reference_check") for r in records)
                and all(r["status"] == "reference_complete" for r in references))
    summary = {"schema": SCHEMA, "complete": bool(complete), "states": records,
               "references": references, "total_wall_s": time.monotonic()-start,
               "scope": "three synthetic fixtures; no population speedup or ML efficacy claim"}
    write_json(root / "summary.json", summary)
    print(json.dumps(summary))
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--reference", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fixture", choices=FIXTURES, help=argparse.SUPPRESS)
    parser.add_argument("--arm", choices=ARMS, help=argparse.SUPPRESS)
    parser.add_argument("--state", type=int, choices=range(len(CONFIG["states"])), help=argparse.SUPPRESS)
    parser.add_argument("--previous", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.fixture is None or args.state is None or (not args.reference and args.arm is None):
            parser.error("Worker needs fixture, state and arm/reference")
        if args.reference:
            result = solve_reference(args.fixture, args.state, Path(args.output))
            return 0 if result["status"] == "reference_complete" else 1
        prev = json.loads(Path(args.previous).read_text()) if args.previous else None
        result = solve_state(args.fixture, args.arm, args.state, prev, Path(args.output))
        return 0 if result["status"] == "certified" else 1
    return supervise(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
