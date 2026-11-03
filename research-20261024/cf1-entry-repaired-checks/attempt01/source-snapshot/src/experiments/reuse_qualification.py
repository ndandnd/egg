"""Bounded, seed-free qualification of columns reused under tariff changes.

This deliberately does not resume production A2 checkpoints. Each state has a
fresh clean master and fresh bounds; only physical columns and the previous
clean price can cross a transition. See the prospective protocol in doc/.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import platform
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
from contextlib import contextmanager

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

SCHEMA = "egg-reuse-qualification-v1"
ARMS = ("cold", "retained", "retained_shift")
CONFIG = {
    "schema": SCHEMA, "threads": 1, "process_cap_s": 300,
    "state_cap_s": 40, "solve_cap_s": 10, "pricing_call_cap": 24,
    "pool_cap": 96, "epsilon": 0.01, "pwl_tol": 0.001,
    "pricing_mip_gap": 1e-9, "tariff_tilts": [0.0, 0.0, 0.2, -0.2],
    "arms": list(ARMS), "seed": None,
    "fixture": {
        "name": "seed-free-two-trip-two-window-reuse",
        "trip_intervals_min": [[0, 60], [180, 240]],
        "trip_energy_kwh": 15.0, "all_locations": "D",
        "battery_kwh": 20.0, "soc0_kwh": 20.0,
        "soc_min_kwh": 0.0, "soc_end_kwh": 0.0,
        "charge_power_kw": 10.0, "n_slots": 4, "slot_min": 60,
        "max_vehicles": 1, "vehicle_fixed_cost": 10.0,
        "dh_cost_per_min": 1.0, "a_level": 0.3, "b": 0.2, "U": 0.0,
    },
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     allow_nan=False).encode()).hexdigest()


def write_json(path, value):
    """Replace only this invocation's files; the output root is exclusive."""
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True,
                               allow_nan=False) + "\n")
    temp.replace(path)


def runtime_evidence():
    """Inspect the actually loaded CBC module; never initialize it here."""
    cbc = sys.modules.get("mip.cbc")
    selected = None
    if cbc is not None and getattr(cbc, "has_cbc", False):
        path = Path(cbc.libfile).resolve()
        selected = {"path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"versions": {name: importlib.metadata.version(name)
                         for name in ("mip", "cbcbox", "numpy")},
            "platform": platform.platform(), "machine": platform.machine(),
            "selected_cbc_library": selected}


def fixture():
    from egglab.instance import Instance, Trip
    return Instance(
        name=CONFIG["fixture"]["name"],
        trips=[Trip("t0", 0, 60, "D", "D", 15.0),
               Trip("t1", 180, 240, "D", "D", 15.0)],
        depot="D", dh_min={}, dh_kwh={}, battery_kwh=20.0,
        soc0_kwh=20.0, soc_min_kwh=0.0, soc_end_kwh=0.0,
        charge_power_kw=10.0, n_slots=4, slot_min=60, max_vehicles=1,
        vehicle_fixed_cost=10.0, dh_cost_per_min=1.0,
        meta={"source": SCHEMA, "seed": None})


def market_for_state(index):
    from egglab.market import AffineMarket
    tilt = CONFIG["tariff_tilts"][index]
    return AffineMarket([0.3, 0.3 + tilt, 0.3 - tilt, 0.3],
                        [0.2] * 4, [0.0] * 4,
                        name=f"reuse-qualification-state-{index}")


def analytic_solution(market):
    """Independent one-dimensional continuous solution for this fixture.

    One vehicle must buy >=10 kWh in slots 1/2. Positive marginal costs make
    equality optimal. Each slot admits 0..10 kWh. This feasible load segment
    is already convex, so the physical and convex-hull optima coincide.
    """
    x = min(10.0, max(0.0, (float(market.a[2] - market.a[1]) + 2.0) / 0.4))
    load = [0.0, x, 10.0 - x, 0.0]
    objective = 10.0 + sum(float(a) * e + 0.1 * e * e
                           for a, e in zip(market.a, load))
    return {"objective": objective, "load": load,
            "explanation": "one bus; x+(10-x)=10 kWh; 0<=x<=10"}


def shifted_price(previous_price, previous_market, current_market):
    if len(previous_price) != current_market.n_slots:
        raise ValueError("Previous clean price has wrong dimension")
    if any(float(x) != float(y) for x, y in zip(previous_market.b, current_market.b)):
        raise ValueError("Supply slopes changed")
    if any(float(x) != float(y) for x, y in zip(previous_market.U, current_market.U)):
        raise ValueError("Base load changed")
    result = [float(q) + float(a) - float(old)
              for q, a, old in zip(previous_price, current_market.a,
                                   previous_market.a)]
    if not all(math.isfinite(q) for q in result):
        raise ValueError("Nonfinite shifted price")
    return result


def replay_column(inst, column):
    """Replay imported and newly generated physical evidence, not flags.

    The production replay checks SOC/timing. Additional structural, ownership,
    aggregate-window, load, and intrinsic-cost checks close gaps that matter
    when deserializing a retained column. No prior pricing bound is reused.
    """
    from egglab import b2a2, evsp
    from egglab.solver import SolveStats

    col = copy.deepcopy(column)
    if col.get("instance_hash") != inst.hash():
        raise ValueError("Column instance changed")
    seqs, kinds = col["sequences"], col["arc_kinds"]
    if (not seqs or len(seqs) != len(kinds) or len(seqs) > inst.max_vehicles
            or col["fleet"] != len(seqs)):
        raise ValueError("Invalid fleet/sequence shape")
    tripmap = {trip.id: trip for trip in inst.trips}
    if sorted(t for seq in seqs for t in seq) != sorted(tripmap):
        raise ValueError("Invalid trip coverage")
    allowed = {}
    dh_minutes = 0.0
    for vi, (seq, arcs) in enumerate(zip(seqs, kinds)):
        if not seq or len(arcs) != len(seq) - 1:
            raise ValueError("Invalid arc count")
        dh_minutes += inst.dhm(inst.depot, tripmap[seq[0]].start_loc)
        dh_minutes += inst.dhm(tripmap[seq[-1]].end_loc, inst.depot)
        for before, after, kind in zip(seq, seq[1:], arcs):
            left, right = tripmap[before], tripmap[after]
            if kind == "dir":
                dh_minutes += inst.dhm(left.end_loc, right.start_loc)
            elif kind == "dep":
                dh_minutes += (inst.dhm(left.end_loc, inst.depot)
                               + inst.dhm(inst.depot, right.start_loc))
                start = left.end_min + inst.dhm(left.end_loc, inst.depot)
                end = right.start_min - inst.dhm(inst.depot, right.start_loc)
                for slot, overlap in evsp.slot_overlaps(inst, start, end):
                    allowed[(vi, before, after, slot)] = inst.charge_power_kw * overlap / 60.0
            else:
                raise ValueError("Invalid arc kind")
    physical_load = [0.0] * inst.n_slots
    by_window = {}
    for charge in col["charges"]:
        slot = charge["slot"]
        if (not isinstance(slot, int) or isinstance(slot, bool)
                or not 0 <= slot < inst.n_slots):
            raise ValueError("Invalid charge slot")
        identity = (charge["vehicle"], charge["after_trip"],
                    charge["before_trip"], slot)
        energy = float(charge["kwh"])
        if identity not in allowed or not math.isfinite(energy) or energy < 0:
            raise ValueError("Invalid charge ownership, window, or energy")
        by_window[identity] = by_window.get(identity, 0.0) + energy
        if by_window[identity] > allowed[identity] + evsp.REPLAY_TOL_KWH:
            raise ValueError("Aggregate charge exceeds its window")
        physical_load[slot] += energy
    if (len(col["load"]) != inst.n_slots
            or any(not math.isfinite(float(x)) or abs(float(x) - y) > 1e-10
                   for x, y in zip(col["load"], physical_load))):
        raise ValueError("Stored load differs from physical charges")
    intrinsic = (inst.vehicle_fixed_cost * len(seqs)
                 + inst.dh_cost_per_min * dh_minutes)
    if not math.isfinite(float(col["ops_cost"])) or abs(col["ops_cost"] - intrinsic) > 1e-10:
        raise ValueError("Stored operating cost differs from intrinsic cost")
    if col.get("column_key") != b2a2.column_key(col):
        raise ValueError("Column key does not match physical projection")
    stats = SolveStats(**col["oracle_stats"])
    sol = evsp.Solution(sequences=seqs, arc_kinds=kinds, charges=col["charges"],
                        load=physical_load, fleet=len(seqs), ops_cost=intrinsic,
                        dh_min_total=dh_minutes, stats=stats)
    violations = evsp.validate_solution(inst, sol)
    if violations:
        raise ValueError(f"Imported column replay failed: {violations}")
    # Checks original oracle status, bound presence, and reconstruction policy.
    rebuilt = b2a2.column_from_solution(inst, sol)
    if rebuilt["column_key"] != col["column_key"]:
        raise ValueError("Replay changed column projection")
    return col


def import_previous(inst, previous, arm, index):
    """Only the immediately preceding certified state of the same arm."""
    from egglab import b2a2
    if (previous.get("schema") != SCHEMA or previous.get("config_sha256") != digest(CONFIG)
            or previous.get("arm") != arm or previous.get("state_index") != index - 1
            or previous.get("status") != "certified"
            or previous.get("instance_hash") != inst.hash()
            or previous.get("market_hash") != b2a2.market_hash(market_for_state(index - 1))):
        raise ValueError("Previous state is not the same arm's certified predecessor")
    columns, keys = [], set()
    for col in previous["columns"]:
        checked = replay_column(inst, col)
        if checked["column_key"] not in keys:
            columns.append(checked)
            keys.add(checked["column_key"])
    if not columns or len(columns) > CONFIG["pool_cap"]:
        raise ValueError("Invalid retained pool size")
    # No previous tangent, sigma, bound, event, or retry counter is returned.
    return columns


@contextmanager
def bounded_solves(deadline, records):
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
        result = original(model, *args, **kwargs)
        records.append({"model": model.name, "elapsed_s": time.perf_counter() - started,
                        "model_time_cap_s": cap, **result.to_dict()})
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


def solve_state(arm, index, previous, output):
    from egglab import b2a2, solver
    from egglab.regimes import solve_taker
    solver._BACKEND_CACHE[:] = ["CBC"]  # Do not initialize Gurobi.
    inst, market = fixture(), market_for_state(index)
    start, cpu_start = time.perf_counter(), time.process_time()
    result = {
        "schema": SCHEMA, "config_sha256": digest(CONFIG), "arm": arm,
        "state_index": index, "instance_hash": inst.hash(),
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
            result["columns"] = import_previous(inst, previous, arm, index)
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
            sol = solve_taker(inst, prices, max_mip_gap=pricing_gap,
                              time_limit_s=CONFIG["solve_cap_s"])
            b2a2.canonicalize_pricing_solution(inst, sol, prices)
            col = replay_column(inst, b2a2.column_from_solution(inst, sol))
            upper = b2a2.pricing_incumbent(col, sol, prices)
            lower = float(sol.stats.bound)
            if not math.isfinite(lower) or lower > upper + 1e-6:
                raise RuntimeError("Pricing bound does not enclose incumbent")
            event = {"call": len(result["oracle_events"]), "purpose": purpose,
                     "prices": list(map(float, prices)), "upper": upper,
                     "lower": lower, "novel": col["column_key"] not in keys,
                     "column_key": col["column_key"],
                     "elapsed_s": time.perf_counter() - t0,
                     "replay_ok": True, "solver": sol.stats.to_dict(),
                     "used_for_lower_bound": purpose == "clean"}
            result["oracle_events"].append(event)
            return col, event

        def admit(col):
            if col["column_key"] not in keys:
                if len(columns) >= CONFIG["pool_cap"]:
                    raise RuntimeError("Frozen pool cap reached; no hidden eviction")
                columns.append(col)
                keys.add(col["column_key"])

        with bounded_solves(deadline, result["native_solves"]):
            if not columns:
                col, _ = pricing(market.price([0.0] * market.n_slots), "cold_seed")
                admit(col)
            if arm == "retained_shift" and index > 0:
                q = shifted_price(previous["last_clean_price"],
                                  market_for_state(index - 1), market)
                col, event = pricing(q, "analytic_proposal")
                # No proposal lower bound or stale sigma enters the certificate.
                result["proposal"] = copy.deepcopy(event)
                admit(col)
            while len(result["oracle_events"]) < CONFIG["pricing_call_cap"]:
                rmp = b2a2.solve_rmp(inst, market, columns, tangents,
                                    pwl_tol=CONFIG["pwl_tol"],
                                    solve_id_prefix=f"{arm}-s{index}-i{len(result['iterations'])}")
                tangents = rmp["tangent_points"]
                result["master_events"].append(rmp)
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
                    truth = analytic_solution(market)
                    if not lb_best - 1e-6 <= truth["objective"] <= rmp["ub"] + 1e-6:
                        raise RuntimeError("Certificate misses independent analytic optimum")
                    load_error = max(abs(x - y) for x, y in zip(rmp["L"], truth["load"]))
                    # f(L)-f(L*) = b/2 ||L-L*||^2; interval objective check
                    # is primary, this loose load check catches gross mistakes.
                    if load_error > math.sqrt(2 * CONFIG["epsilon"] / 0.2) + 1e-4:
                        raise RuntimeError("Final load misses independent analytic optimum")
                    result.update(status="certified", lower=lb_best, upper=rmp["ub"],
                                  gap=gap, final_load=rmp["L"], analytic=truth,
                                  max_load_error=load_error)
                    break
                if not event["novel"] and reduced_upper < -b2a2.RC_TOL:
                    raise RuntimeError("Duplicate has negative reduced cost")
                if reduced_lower < -b2a2.RC_TOL and reduced_upper >= -b2a2.RC_TOL:
                    pricing_gap = max(pricing_gap / 100.0, 1e-12)
                else:
                    tangents.append(list(rmp["L"]))
            else:
                raise RuntimeError("Pricing-call budget exhausted")
        result["oracle_calls"] = len(result["oracle_events"])
        result["calls_clean"] = sum(e["purpose"] == "clean" for e in result["oracle_events"])
        result["calls_seed"] = sum(e["purpose"] == "cold_seed" for e in result["oracle_events"])
        result["calls_proposal"] = sum(e["purpose"] == "analytic_proposal" for e in result["oracle_events"])
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc())
    finally:
        result["runtime"] = runtime_evidence()
        result["worker_wall_s"] = time.perf_counter() - start
        result["worker_cpu_s"] = time.process_time() - cpu_start
        result["solver_wall_s"] = sum(s["wall_s"] + s["lp_wall_s"]
                                      for s in result["native_solves"])
        write_json(output, result)
    return result


def supervise(output):
    """Sequential subprocesses give each state an enforceable wall-time cap."""
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / "frozen-config.json", CONFIG)
    code_paths = [Path(__file__), REPO / "doc/REUSE_QUALIFICATION_PROTOCOL_20260921.md"]
    code_paths += [REPO / "src/egglab" / f"{name}.py" for name in
                   ("b2a2", "b2a345", "checkpoint", "evsp", "instance", "market", "regimes", "solver")]
    head = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    write_json(root / "provenance.json", {
        "head": head, "python": sys.version, "executable": sys.executable,
        "runtime": runtime_evidence(),
        "config_sha256": digest(CONFIG), "source_sha256": {
            str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths}})
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1", SLURM_CPUS_PER_TASK="1")
    env.pop("EGGLAB_REQUIRE_GRB", None)
    start = time.monotonic()
    records, previous = [], {}
    for index in range(len(CONFIG["tariff_tilts"])):
        for arm in ARMS:
            cell = root / f"{arm}-s{index}"
            cell.mkdir()
            remain = CONFIG["process_cap_s"] - (time.monotonic() - start)
            if remain <= 0 or (arm != "cold" and index > 0 and previous.get(arm) is None):
                records.append({"arm": arm, "state_index": index, "status": "skipped_budget_or_predecessor"})
                continue
            args = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker",
                    "--arm", arm, "--state", str(index), "--output", str(cell / "state.json")]
            if arm != "cold" and index > 0:
                args += ["--previous", str(previous[arm])]
            t0 = time.perf_counter()
            with (cell / "stdout.txt").open("x") as out, (cell / "stderr.txt").open("x") as err:
                proc = subprocess.Popen(args, cwd=REPO, env=env, stdout=out, stderr=err,
                                        start_new_session=True)
                timed_out = False
                try:
                    proc.wait(timeout=min(CONFIG["state_cap_s"], remain))
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
            result_path = cell / "state.json"
            data = json.loads(result_path.read_text()) if result_path.exists() else {}
            good = proc.returncode == 0 and data.get("status") == "certified"
            previous[arm] = result_path if good else None
            record = {"arm": arm, "state_index": index, "worker_exit": proc.returncode,
                      "timed_out": timed_out, "complete_wall_s": time.perf_counter() - t0,
                      "status": "certified" if good else "failed", "result": str(result_path)}
            for key in ("lower", "upper", "gap", "oracle_calls", "calls_clean", "calls_seed",
                        "calls_proposal", "solver_wall_s", "worker_cpu_s"):
                if key in data:
                    record[key] = data[key]
            records.append(record)
            write_json(root / "summary.json", {"schema": SCHEMA, "complete": False, "states": records})
    complete = len(records) == 12 and all(r["status"] == "certified" for r in records)
    summary = {"schema": SCHEMA, "complete": complete, "states": records,
               "total_wall_s": time.monotonic() - start,
               "scope": "one seed-free engineering fixture; no runtime generalization or ML gate"}
    write_json(root / "summary.json", summary)
    write_json(root / "worker-runtimes.json", {
        "schema": SCHEMA, "selected_library_recorded_after_native_solves": True,
        "states": [{"arm": row["arm"], "state_index": row["state_index"],
                    "runtime": json.loads(Path(row["result"]).read_text()).get("runtime")}
                   for row in records if row.get("result") and Path(row["result"]).exists()]})
    print(json.dumps(summary))
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--arm", choices=ARMS, help=argparse.SUPPRESS)
    parser.add_argument("--state", type=int, choices=range(4), help=argparse.SUPPRESS)
    parser.add_argument("--previous", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.arm is None or args.state is None:
            parser.error("Worker needs arm and state")
        prev = json.loads(Path(args.previous).read_text()) if args.previous else None
        result = solve_state(args.arm, args.state, prev, Path(args.output))
        return 0 if result["status"] == "certified" else 1
    return supervise(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
