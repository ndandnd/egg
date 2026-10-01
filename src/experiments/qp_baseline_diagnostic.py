"""Six-cell development diagnosis of the existing numerical-QP hull master."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_hull as hull
from egglab import native_pathflow_hull as compact
from experiments import budget_sizing_diagnostic as sizing
from experiments import computational_benchmark as base
from experiments import native_scaling_cases as scaling
from experiments import retrieval_comparison as retrieval
from experiments.feasible_pool_pilot_report import extract_trace


ROOT = base.ROOT
ATTEMPT = ROOT / "result/qp_baseline_diagnostic/20260929-attempt1"
PROTOCOL = "egg-qp-baseline-diagnostic-development-20260929-v1"
CASES = tuple(f"native_scale_dev_s1006_n{n:02d}" for n in (8, 16, 24))
KINDS = ("source0", "target")
PREFLIGHT = "research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json"
CHILD_HARD_SECONDS = 210
CONTROLLER_CAP_SECONDS = 1500
RESERVE_SECONDS = 10.0
QP_DENOMINATOR = 1_000_000_000
QP_MAXITER = 500
SOURCE_FILES = (
    "src/experiments/qp_baseline_diagnostic.py",
    "src/tests/test_qp_baseline_diagnostic.py",
    "src/cluster/qp_baseline_diagnostic.sbatch",
    "research-20260929/qp-baseline-diagnostic/DESIGN.md",
    "research-20260929/qp-baseline-diagnostic/README.md",
    "src/experiments/cold_baseline_viability.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/feasible_pool_pilot_report.py",
    "src/experiments/native_scaling_cases.py",
    "src/experiments/retrieval_comparison.py",
    PREFLIGHT,
    "src/egglab/native_hull.py",
    "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py",
    "src/egglab/native_recharge.py",
    "src/egglab/restricted_qp_proposal.py",
    "src/egglab/solver.py",
    "src/cluster/unicorn_env.sh",
)


def state(kind):
    if kind not in KINDS:
        raise ValueError("Unknown market")
    return KINDS.index(kind)


def cells():
    """Alternate market execution order across the three case sizes."""
    return tuple((name, kind) for index, name in enumerate(CASES)
                 for kind in (KINDS if index % 2 == 0 else KINDS[::-1]))


def cases():
    preflight = json.loads((ROOT / PREFLIGHT).read_text())
    if (preflight.get("generator_source_sha256") != base.sha(ROOT / "src/experiments/native_scaling_cases.py")
            or preflight.get("generator_version") != scaling.GENERATOR_VERSION
            or preflight.get("failed_cells") != []):
        raise ValueError("Reviewed pure scaling preflight changed")
    rows = {row.get("name"): row for row in preflight.get("cases", [])}
    if not set(CASES) <= set(rows):
        raise ValueError("Selected development case omitted from preflight")
    built = {name: scaling.make_case(1006, n) for n, name in zip((8, 16, 24), CASES)}
    for name, case in built.items():
        if (case.name != name or case.identity() != rows[name].get("case_identity")
                or rows[name].get("split") != "development"
                or rows[name].get("status") != "pure_validation_and_replay_passed"):
            raise ValueError("Selected physical case differs from reviewed development preflight")
    return built


def market(name, kind):
    if name not in CASES or kind not in KINDS:
        raise ValueError("Undeclared case/market")
    return retrieval.market(name, kind)


def budget():
    return hull.Budget(backend="GRB", threads=1, phase_seconds=160,
                       wall_seconds=180, pricing_calls=16, master_calls=64,
                       pool_cap=64, epsilon=1e-4, pool_tolerance=1e-6,
                       polish_steps=64, rational_bits=8192, polish_seconds=20)


def design():
    built = cases()
    return {"cases": {name: {"case": asdict(item), "case_identity": item.identity(),
                            "base_group": "native_scale_dev_s1006",
                            "markets": {kind: asdict(market(name, kind)) for kind in KINDS},
                            "market_identities": {kind: market(name, kind).identity()
                                                  for kind in KINDS}}
                      for name, item in built.items()},
            "order": [{"case": name, "market": kind, "state_index": state(kind)}
                      for name, kind in cells()],
            "budget": asdict(budget()), "hard_child_seconds": CHILD_HARD_SECONDS,
            "pricing_reserve_seconds": RESERVE_SECONDS,
            "arm": "cold", "master_policy": "numerical_qp_proposal",
            "qp_denominator": QP_DENOMINATOR, "qp_maxiter": QP_MAXITER,
            "bound_cache_policy": "none",
            "development_only": True, "independent_test_data": False}


def software_runtime():
    """Baseline portable runtime plus dependencies used by the QP proposal."""
    return {**sizing.software_runtime(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy")}


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the separate exclusive QP attempt is allowed")
    return target


def freeze(path):
    target = _attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "software_runtime": software_runtime(),
            "freeze_host_environment": sizing.host_environment(),
            "native_probe": sizing.native_probe(), "design": design(),
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS, "declared_cells": 6,
            "scientific_admission": "pending independent review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit:
        raise ValueError("Frozen protocol/commit differs")
    if spec.get("source_hashes") != source_hashes():
        raise ValueError("Frozen source hashes differ")
    if not sizing.runtime_compatible(spec.get("software_runtime"), software_runtime()):
        raise ValueError("Frozen portable runtime differs")
    if spec.get("native_probe") != sizing.native_probe():
        raise ValueError("Frozen native backend/seed differs")
    if (base.canonical(spec.get("design")) != base.canonical(design())
            or spec.get("controller_cap_seconds") != CONTROLLER_CAP_SECONDS
            or spec.get("declared_cells") != 6):
        raise ValueError("Frozen QP design differs")
    return spec


def folder(path, name, kind):
    return Path(path) / name / f"state{state(kind)}" / "cold_hull"


def worker(path, name, kind):
    target = _attempt(path)
    if (name, kind) not in cells():
        raise ValueError("Undeclared QP cell")
    dest = folder(target, name, kind)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if not (dest / "launch.json").is_file():
            raise ValueError("Missing child launch receipt")
        item, m, cfg = cases()[name], market(name, kind), budget()
        declared = spec["design"]
        if (declared["cases"][name]["case_identity"] != item.identity()
                or declared["cases"][name]["market_identities"][kind] != m.identity()
                or declared["budget"] != asdict(cfg)):
            raise ValueError("Cell differs from frozen case/market/budget")
        def record(event):
            with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        result = compact.certify(item, m, cfg, arm="cold", state_index=state(kind),
                                 record=record, pricing_reserve_seconds=RESERVE_SECONDS,
                                 master_policy="numerical_qp_proposal",
                                 qp_denominator=QP_DENOMINATOR, qp_maxiter=QP_MAXITER)
        if (result.get("state_identity") != compact.state_identity(
                    item, m, "cold", state(kind), cfg,
                    pricing_reserve_seconds=RESERVE_SECONDS,
                    master_policy="numerical_qp_proposal",
                    qp_denominator=QP_DENOMINATOR, qp_maxiter=QP_MAXITER)
                or result.get("arm") != "cold" or result.get("state_index") != state(kind)
                or result.get("pricing_reserve_seconds") != RESERVE_SECONDS
                or result.get("master_policy") != "numerical_qp_proposal"
                or result.get("qp_denominator") != QP_DENOMINATOR
                or result.get("qp_maxiter") != QP_MAXITER):
            raise ValueError("Returned hull state/control identity differs")
        base.save_new(dest / "raw_result.json", {"result": result, "case": name, "market": kind})
        assessment = base.assess(item, m, "cold_hull", result)
        base.save_new(dest / "result.json", {"assessment": assessment,
                                              "case": name, "market": kind,
                                              "elapsed_seconds": time.monotonic() - started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
                                                  "message": str(exc),
                                                  "traceback": traceback.format_exc(),
                                                  "elapsed_seconds": time.monotonic() - started})
        return 2


def result_row(path, name, kind, receipt=None):
    dest = folder(path, name, kind)
    row = {"case": name, "base_group": "native_scale_dev_s1006", "market": kind,
           "state_index": state(kind), "outcome": "unstarted", "native_status": None,
           "master_policy": "numerical_qp_proposal",
           "complete_evidence": False, "stop_reason": None,
           "lower_exact": None, "upper_exact": None, "gap_exact": None,
           "pricing_requests": None, "master_calls": None, "max_rational_bits": None,
           "polish_wall_s": None, "pricing_solver_wall_recorded_s": None,
           "qp_proposal_calls": None, "qp_non_success": None,
           "qp_proposal_wall_s": None, "qp_replay_wall_s": None,
           "pricing_solver_wall_complete": None,
           "master_solver_wall_recorded_s": None,
           "master_solver_wall_complete": None,
           "native_lp_master_time_applicable": False,
           "model_construction_s": None, "child_wall_s": None, "on_time": None}
    if receipt is None and (dest / "receipt.json").is_file():
        try:
            receipt = json.loads((dest / "receipt.json").read_text())
        except (OSError, ValueError, TypeError):
            row["outcome"] = "receipt_unreadable"
    if receipt is not None:
        row["on_time"], row["child_wall_s"] = receipt.get("on_time"), receipt.get("elapsed_seconds")
        row["outcome"] = ("hard_timeout" if receipt.get("hard_timeout") else
                          "failed" if receipt.get("returncode") != 0 else
                          "late" if receipt.get("on_time") is not True else "returned")
    elif row["outcome"] == "unstarted" and (dest / "launch.json").exists():
        row["outcome"] = "interrupted_unreceipted"
    raw_path = dest / "raw_result.json"
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text())["result"]
            counts = raw.get("counts", {})
            row.update(native_status=raw.get("status"), stop_reason=raw.get("reason"),
                       pricing_requests=counts.get("pricing_requests"),
                       master_calls=counts.get("master_calls"),
                       max_rational_bits=counts.get("max_rational_bits"),
                       polish_wall_s=counts.get("polish_wall_s"),
                       qp_proposal_calls=counts.get("qp_proposal_calls"),
                       qp_non_success=counts.get("qp_non_success"),
                       qp_proposal_wall_s=counts.get("qp_proposal_wall_s"),
                       qp_replay_wall_s=counts.get("qp_replay_wall_s"))
        except (OSError, ValueError, TypeError, KeyError):
            row["raw_read_error"] = True
    events = dest / "events.jsonl"
    if events.is_file():
        try:
            trace = extract_trace([json.loads(line) for line in events.read_text().splitlines()])
            for key in ("pricing_solver_wall_recorded_s", "pricing_solver_wall_complete"):
                row[key] = trace[key]
            row["pricing_solver_wall_complete"] &= trace["pricing_results"] == row["pricing_requests"]
            # The trace helper only times native-LP master events; QP proposal and
            # exact replay times come from the QP-specific counters above.
            row["events_sha256"] = base.sha(events)
        except (OSError, ValueError, TypeError, KeyError):
            row["events_read_error"] = True
    assessed_path = dest / "result.json"
    if row["outcome"] == "returned" and assessed_path.is_file():
        try:
            result = json.loads(assessed_path.read_text())
            assessment = result["assessment"]
            if (result.get("case"), result.get("market")) != (name, kind):
                raise ValueError("Assessment cell identity differs")
            if (assessment.get("complete_evidence") is True and assessment.get("bounds")
                    and assessment.get("status") in
                    ("certified", "budget_exhausted", "stalled_bounded")):
                raw = json.loads(raw_path.read_text())["result"]
                if (assessment.get("status") != raw.get("status")
                        or assessment["bounds"] != base.finite_bounds(raw)
                        or raw.get("master_policy") != "numerical_qp_proposal"
                        or raw.get("qp_denominator") != QP_DENOMINATOR
                        or raw.get("qp_maxiter") != QP_MAXITER
                        or raw.get("pricing_reserve_seconds") != RESERVE_SECONDS):
                    raise ValueError("Assessed and raw result differ")
                lo = Fraction(raw["lower_certificate"]["lower_exact"])
                hi = Fraction(raw["mixture"]["objective_exact"])
                if lo > hi:
                    raise ValueError("Native global enclosure reversed")
                row.update(complete_evidence=True, native_status=assessment["status"],
                           outcome=assessment["status"], lower_exact=str(lo),
                           upper_exact=str(hi), gap_exact=str(hi - lo))
            else:
                row["outcome"] = "incomplete_evidence"
        except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError):
            row["outcome"] = "partial_result"
            row["complete_evidence"] = False
    elif row["outcome"] == "returned":
        row["outcome"] = "returned_unassessed"
    return row


def controller(path):
    target = _attempt(path)
    frozen(target)
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    for name, kind in cells():
        dest = folder(target, name, kind)
        dest.mkdir(parents=True, exist_ok=False)
        command = [sys.executable, "-m", "experiments.qp_baseline_diagnostic", "worker",
                   "--attempt", str(target), "--case", name, "--market", kind]
        receipt = base.launch_child(target, name, state(kind), "cold_hull",
                                    CHILD_HARD_SECONDS, command=command)
        rows.append(result_row(target, name, kind, receipt))
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                                             "declared_cells": 6, "accounted_cells": len(rows),
                                             "all_declared_cells_accounted": len(rows) == 6,
                                             "scientific_admission": "pending independent result review"})
    return 0


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if json.loads((target / "summary.json").read_text()).get("accounted_cells") == 6:
                return
        except (OSError, ValueError, TypeError):
            pass
    rows = [result_row(target, name, kind) for name, kind in cells()]
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
                                                       "declared_cells": 6,
                                                       "accounted_cells": len(rows),
                                                       "scientific_admission": "none; abnormal controller termination"})


def supervise(path):
    target = _attempt(path)
    source_error, child_rc, timed_out, launch_error, quiescent = None, None, False, None, True
    try:
        frozen(target)
    except Exception as exc:
        source_error = repr(exc)
    started = time.monotonic()
    if source_error is None:
        command = [sys.executable, "-m", "experiments.qp_baseline_diagnostic", "controller",
                   "--attempt", str(target)]
        base.save_new(target / "supervisor_launch.json", {"command": command,
                                                            "hard_seconds": CONTROLLER_CAP_SECONDS})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with (target / "controller_stdout.txt").open("xb") as out, \
                    (target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                child_rc, timed_out, quiescent = base.wait_process_group(process, CONTROLLER_CAP_SECONDS)
        except Exception as exc:
            launch_error, child_rc = repr(exc), 1
    else:
        base.save_new(target / "supervisor_launch.json", {"command": None,
                                                            "blocked_before_child": True})
    try:
        unchanged = source_hashes() == json.loads((target / "frozen.json").read_text())["source_hashes"]
    except Exception as exc:
        unchanged, source_error = False, repr(exc)
    if quiescent and (timed_out or child_rc != 0 or source_error or launch_error):
        reconcile_partial(target)
    rc = 124 if timed_out else 1 if source_error or not unchanged or launch_error or not quiescent else child_rc or 0
    base.save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
                                                        "child_returncode": child_rc,
                                                        "returncode": rc, "hard_timeout": timed_out,
                                                        "process_group_quiescent": quiescent,
                                                        "stable_seal": quiescent,
                                                        "source_hashes_unchanged": unchanged,
                                                        "source_check_error": source_error,
                                                        "launch_error": launch_error,
                                                        "elapsed_seconds": time.monotonic() - started})
    if quiescent:
        files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": base.sha(p)}
                 for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
        base.save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--market", choices=KINDS)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), indent=2, sort_keys=True))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": software_runtime(), "host": sizing.host_environment(),
                          "native_probe": sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "controller":
        return controller(args.attempt)
    if args.case is None or args.market is None:
        parser.error("worker requires --case and --market")
    return worker(args.attempt, args.case, args.market)


if __name__ == "__main__":
    raise SystemExit(main())
