#!/usr/bin/env python3
"""Independent solver-free audit for the sealed GRB V3 physical attempt.

The matrix, projection, decoder, exact fixture and physical-replay helpers are
copied from the earlier independent CBC V3 audit. This entry point adds GRB
runtime, wrapper, Slurm and backend-normalized parity checks. It imports no
project implementation and does not instantiate or call an optimizer.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

import independent_compact_core as compact
import independent_fixture_core as base
import independent_projection_audit as physical_audit

HERE = Path(__file__).resolve().parent
COMMIT = "227da22074201c583dbcfa971863c8f3c41d7391"
PROTOCOL = "native-v3-grb-replication-20260927-v1"
PHYSICAL_PROTOCOL = "native-pathflow-qualification-20260927-v3-orphan-projection"
FORMULATION = physical_audit.FORMULATION
POLICY = compact.POLICY
NATIVE_MATRIX = physical_audit.NATIVE_MATRIX
SHARED_POLICY = physical_audit.SHARED_POLICY
ATTEMPT_REL = Path("result/native_pathflow_grb/20260927-attempt1")
OLD_ATTEMPT_REL = Path("result/native_pathflow/20260927-attempt3")
OLD_FROZEN_SHA = "0d647431fd72bbe5f448e388dcee1c3441bcfea07c29a2969eec45cc85c37f87"
EXPECTED_INFEASIBLE = {
    "fixed_reserve_one_bus", "terminal_capacity_failure",
    "partial_overlap_failure", "halfminute_capacity_failure",
}
EXPECTED_IDS = list(base.TARGETS)
need, near = base.need, base.near


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path):
    return json.loads(path.read_bytes())


def check_grb_runtime(stats):
    need(stats.get("backend") == "GRB" and stats.get("threads") == 1
         and stats.get("seconds_cap") == 10,
         "explicit one-thread GRB native phase budget")
    rt = stats.get("backend_runtime", {})
    actual = str(rt.get("model_solver_name", "")).upper()
    normalized = "GRB" if actual == "GUROBI" else actual
    need(rt.get("requested") == "GRB" and normalized == "GRB"
         and rt.get("solver_module") == "mip.gurobi"
         and "gurobi" in str(rt.get("solver_class", "")).lower(),
         "actual GRB runtime identity; no CBC fallback")
    library_hash = rt.get("native_library_sha256")
    need(isinstance(library_hash, str) and re.fullmatch(r"[0-9a-f]{64}", library_hash),
         "recorded GRB native-library fingerprint")
    need(isinstance(rt.get("native_library_path"), str) and rt["native_library_path"],
         "recorded GRB native-library path")
    need(math.isfinite(float(stats.get("wall_s"))) and stats["wall_s"] >= 0
         and stats["wall_s"] <= stats["seconds_cap"] + 1e-6
         and stats.get("n_vars", 0) > 0
         and stats.get("n_constraints", 0) >= stats.get("physical_constraints", 0),
         "native call timing and model dimensions")
    return rt


def audit_cell_grb(cell, blob):
    """Adapt the earlier exact fixture audit for GRB and variable planner rounds."""
    c = cell["case"]
    identity = digest(json.dumps({"schema": "egg-native-recharge-v1", "case": c},
                                 sort_keys=True, allow_nan=False).encode())
    need(identity == cell["case_identity"], "input identity digest")
    model_min = base.scalar_min(cell)
    target = base.TARGETS[cell["id"]]
    need((model_min is None) == (target is None), "analytical feasibility target")
    if target is not None:
        near(float(model_min[0]), float(target), "independent analytical target", 1e-10)

    events = blob["events"]
    starts, statuses, replayed, oracle, witnesses = {}, {}, {}, [], []
    runtime_rows = []
    for e in events:
        r = e["round"]
        need(type(r) is int and r >= 0, "integer nonnegative native round")
        if e["event"] == "native_start":
            need(r == len(starts) and r not in starts, "sequential native starts")
            starts[r] = e
        elif e["event"] == "native_status":
            need(r in starts and r not in statuses, "one returned status per start")
            stats = e["stats"]
            runtime_rows.append(check_grb_runtime(stats))
            statuses[r] = stats
            tangent = starts[r].get("tangents")
            reference = base.scalar_min(cell, tangent)
            if reference is None:
                need(stats["status"] == "INFEASIBLE" and stats.get("incumbent") is None,
                     "independently infeasible target retains native status and no incumbent")
            else:
                need(stats["status"] == "OPTIMAL", "native feasible status preserved")
                near(stats["incumbent"], float(reference[0]), "independent global GRB objective", base.OT)
                near(stats["lower_bound"], float(reference[0]), "independent global GRB lower bound", base.OT)
            oracle.append({"round": r, "native_status": stats["status"],
                           "reference": None if reference is None else reference[0],
                           "native_incumbent": stats.get("incumbent"),
                           "native_lower_bound": stats.get("lower_bound"),
                           "physical_witness_saved": False})
        elif e["event"] == "replayed_iteration":
            need(r in statuses and r not in replayed, "replay after unique status")
            need(e["stats"] == statuses[r] and e["tangents"] == starts[r]["tangents"],
                 "immutable round snapshot")
            p, val, env = base.saved_bounds(cell, statuses[r], e["plan"], e["tangents"])
            near(e["lower"], statuses[r]["lower_bound"] - base.GUARD, "round widened lower")
            near(e["upper"], val + base.GUARD, "round widened true upper")
            near(e["replayed_tangent_objective"], env, "saved PWL envelope")
            near(e["native_epigraph_slack"], statuses[r]["incumbent"] - env, "saved epigraph slack")
            replayed[r] = e
            witnesses.append(p)
            oracle[r]["physical_witness_saved"] = True
        else:
            raise AssertionError("unknown native event: " + str(e.get("event")))

    need(len(starts) == len(statuses) and len(starts) >= 1,
         "all native starts returned; actual call count recorded")
    need(len(starts) <= 48, "native round count within frozen 48-round limit")
    if cell["objective"] == "planner":
        expected = [[[float(a), 0.0]] for a in cell["a"]]
        for r in range(len(starts)):
            actual = starts[r]["tangents"]
            need(len(actual) == len(expected)
                 and all(len(arow) == len(erow) for arow, erow in zip(actual, expected)),
                 "tangent history dimensions")
            # Tangent coefficients are rounded floats. Verify the independent
            # supporting-line update formula within 1e-12, then use the exact
            # stored coefficients (as binary rationals) for all native global
            # objective, envelope, and lower-bound reconstructions below.
            for t, (arow, erow) in enumerate(zip(actual, expected)):
                for i, (aline, eline) in enumerate(zip(arow, erow)):
                    near(aline[0], eline[0], f"saved tangent slope formula r{r}/t{t}/{i}", 1e-12)
                    near(aline[1], eline[1], f"saved tangent intercept formula r{r}/t{t}/{i}", 1e-12)
            if r in replayed:
                loads = replayed[r]["plan"]["load"]
                for t, x in enumerate(loads):
                    expected[t].append([float(cell["a"][t] + cell["b"][t] * x),
                                        float(-0.5 * cell["b"][t] * x * x)])
    elif cell["objective"] == "pricing":
        need(len(starts) == 1, "pricing oracle uses one explicit native solve")

    receipt = blob["receipt"]
    need(receipt["native_calls_started"] == len(starts)
         and receipt["native_calls_returned"] == len(statuses),
         "per-control actual native-call accounting")
    near(receipt["native_wall_s"], sum(s["wall_s"] for s in statuses.values()),
         "native elapsed accounting", 1e-9)
    need(receipt["native_accounting_complete"] and not receipt["hard_timeout"]
         and receipt["evidence_issues"] == [], "complete non-timeout native accounting")

    result_package = blob.get("result")
    need(result_package is not None and receipt["pass"] and receipt["returncode"] == 0,
         "successful per-control receipt/result")
    need(result_package["assessment"]["pass"] is True
         and result_package["cell"] == cell["id"], "result ownership and target assessment")
    result = result_package["result"]
    need(result["case_identity"] == cell["case_identity"], "result physical identity")
    if target is None:
        need(result["status"] == "infeasible", "expected infeasible result retained")
        need(all(s["status"] == "INFEASIBLE" for s in statuses.values()),
             "infeasible native statuses preserved")
    else:
        need(result["status"] == "certified", "certified GRB status")
        if cell["objective"] == "pricing":
            need(result["stats"] == statuses[0], "pricing result stats equal raw native status")
            p, val, env = base.saved_bounds(cell, statuses[0], result["plan"])
            witnesses.append(p)
            oracle[0]["physical_witness_saved"] = True
            lower, upper = statuses[0]["lower_bound"] - base.GUARD, val + base.GUARD
        else:
            need(len(result["rounds"]) == len(replayed), "all planner rounds archived")
            for r, saved in enumerate(result["rounds"]):
                need(saved == {k: v for k, v in replayed[r].items() if k not in ("event", "round")},
                     "event/result round equality")
            lower = max(e["lower"] for e in replayed.values())
            upper = min(e["upper"] for e in replayed.values())
            need(any(result["plan"] == e["plan"] and e["upper"] == upper for e in replayed.values()),
                 "best physical witness selection")
        near(result["lower"], lower, "final lower")
        near(result["upper"], upper, "final upper")
        near(result["gap"], upper - lower, "final interval width")
        need(0 <= result["gap"] <= 1e-4 and Q(result["lower"]) <= model_min[0] <= Q(result["upper"]),
             "independent exact fixture optimum inside admitted interval")

    runtime_keys = {
        (rt["requested"], rt["model_solver_name"], rt["solver_module"], rt["solver_class"],
         rt["native_library_sha256"], rt["native_library_path"])
        for rt in runtime_rows
    }
    need(len(runtime_keys) == 1, "one consistent recorded GRB native runtime across calls")
    return {"cell": cell["id"], "pass": receipt["pass"], "status": result["status"],
            "independent_true_optimum": None if model_min is None else model_min[0],
            "native_rounds": oracle, "actual_native_calls": len(starts),
            "physical_witnesses": witnesses,
            "certified_interval": None if target is None else [result["lower"], result["upper"]],
            "runtime_identity": {"requested": "GRB", "model_solver_name": runtime_rows[0]["model_solver_name"],
                                 "solver_module": runtime_rows[0]["solver_module"],
                                 "solver_class": runtime_rows[0]["solver_class"],
                                 "native_library_sha256": runtime_rows[0]["native_library_sha256"]}}


# The copied full audit reuses its raw matrix/projection/replay/corruption
# functions, while dispatching the native telemetry audit above for GRB.
base.audit_cell = audit_cell_grb


def compare_controls(frozen, old_frozen):
    need(frozen["protocol"] == PHYSICAL_PROTOCOL, "GRB physical protocol identity")
    need(frozen["target_tolerance"] == old_frozen["target_tolerance"], "unchanged target tolerance")
    need(frozen["budget"].get("backend") == "GRB", "GRB backend declared in frozen budget")
    need({k: v for k, v in frozen["budget"].items() if k != "backend"}
         == {k: v for k, v in old_frozen["budget"].items() if k != "backend"},
         "all physical budgets unchanged except backend")
    need([c["id"] for c in frozen["controls"]] == EXPECTED_IDS,
         "all 20 fixed control identifiers and order")
    need(len(frozen["controls"]) == 20 and frozen["controls"] == old_frozen["controls"],
         "all 20 serialized controls and targets exactly match CBC attempt3")
    infeasible = {c["id"] for c in frozen["controls"] if base.TARGETS[c["id"]] is None}
    need(infeasible == EXPECTED_INFEASIBLE, "four exact expected infeasibility controls")


def verify_raw_manifest(attempt: Path, expected_sha: str):
    data = (attempt / "MANIFEST.json").read_bytes()
    need(digest(data) == expected_sha, "pinned original GRB raw manifest")
    manifest = json.loads(data)
    need(manifest.get("protocol") == PROTOCOL and isinstance(manifest.get("files"), dict),
         "raw manifest protocol and file map")
    actual = {str(p.relative_to(attempt)) for p in attempt.rglob("*")
              if p.is_file() and p.name != "MANIFEST.json"}
    need(actual == set(manifest["files"]), "raw attempt contains exactly manifest-listed files")
    total = 0
    for rel, record in manifest["files"].items():
        path = attempt / rel
        blob = path.read_bytes()
        need(record == {"sha256": digest(blob), "bytes": len(blob)}, "raw file hash/size: " + rel)
        total += len(blob)
    return manifest, total


def verify_wrapper_and_slurm(attempt, sentinel, slurm_dir, frozen, manifest, commit):
    wrapper_launch = read(attempt / "grb_wrapper_launch.json")
    wrapper_receipt = read(attempt / "grb_wrapper_receipt.json")
    completion = read(sentinel / "completion.json")
    slurm = read(sentinel / "slurm_receipt.json")
    need(wrapper_launch["protocol"] == wrapper_receipt["protocol"] == PROTOCOL
         and wrapper_launch["stage"] == wrapper_receipt["stage"] == "physical",
         "physical wrapper launch/receipt identity")
    need(wrapper_launch["backend"] == "GRB" and wrapper_launch["source_commit"] == commit
         and wrapper_launch["outer_cap_seconds"] == 1320,
         "published full-commit GRB launch and physical outer cap")
    need(wrapper_receipt["returncode"] == 0 and wrapper_receipt["child_returncode"] == 0
         and wrapper_receipt["outer_timeout"] is False
         and wrapper_receipt["source_hashes_unchanged"] is True
         and wrapper_receipt["launch_error"] is None
         and wrapper_receipt["source_check_error"] is None
         and wrapper_receipt["stage_evidence_error"] is None
         and wrapper_receipt["elapsed_seconds"] <= 1320,
         "successful, bounded wrapper receipt with unchanged source")
    need(completion["attempt"] == str(ATTEMPT_REL)
         and completion["receipt_sha256"] == digest((attempt / "grb_wrapper_receipt.json").read_bytes())
         and completion["manifest_sha256"] == digest((attempt / "MANIFEST.json").read_bytes()),
         "sentinel completion pins sealed attempt receipt and manifest")
    need(slurm["job_id"] == "559429" and slurm["returncode"] == 0
         and slurm["timeout_exit"] is False and slurm["shell_cap_seconds"] == 1370
         and 0 <= slurm["elapsed_whole_seconds"] <= 1370,
         "successful Slurm job receipt/cap")
    need(slurm["start_utc"] and wrapper_launch["command"][1:3]
         == ["-m", "experiments.native_pathflow_qualification"]
         and wrapper_launch["command"][3] == "--output"
         and Path(wrapper_launch["command"][4]).as_posix().endswith(str(ATTEMPT_REL))
         and wrapper_launch["command"][5:] == ["--freeze-label", commit, "--backend", "GRB"],
         "wrapper command binds stage, path and full commit")
    source_hashes = wrapper_launch.get("source_hashes")
    need(isinstance(source_hashes, dict) and source_hashes, "complete wrapper source-hash list")
    for rel, sha in frozen["source_hashes"].items():
        need(source_hashes.get(rel) == sha, "wrapper/child source pin: " + rel)
    need(wrapper_receipt["launch_sentinel"] == str(sentinel.relative_to(attempt.parents[2])),
         "receipt refers to sibling launch sentinel")
    for stream in ("stdout", "stderr"):
        outside = (sentinel / f"{stream}.txt").read_bytes()
        inside = (attempt / f"grb_wrapper_{stream}.txt").read_bytes()
        need(inside == outside, "sealed copy of wrapper " + stream)
    log_receipts = {}
    for suffix in ("out", "err"):
        log = slurm_dir / "unpacked" / f"egg-v3-grb-physical-{slurm['job_id']}.{suffix}"
        need(log.is_file(), "retained Slurm scheduler log " + suffix)
        blob = log.read_bytes()
        log_receipts[log.name] = {"bytes": len(blob), "sha256": digest(blob),
                                  "content_embedded": False}
    intent_path = slurm_dir / "INTENT.json"
    submitted_path = slurm_dir / "SUBMITTED.txt"
    sacct_path = slurm_dir / "SACCT.txt"
    scontrol_path = slurm_dir / "SCONTROL.txt"
    intent = read(intent_path)
    need(intent == {"source_commit": commit, "stage": "physical", "backend": "GRB",
                    "controls": 20, "cpus": 1, "memory_gb": 8, "slurm_minutes": 30,
                    "exclude": "scaglione-compute-01", "no_requeue": True,
                    "attempt": str(ATTEMPT_REL),
                    "independent_preflight": "doc/NATIVE_V3_GRB_REPLICATION_IMPLEMENTATION_REVIEW_20260927.md"},
         "saved submission intent and resource/exclusion policy")
    need(submitted_path.read_text().strip() == "559429", "submitted job ID receipt")
    sacct_rows = list(csv.DictReader(sacct_path.open(newline=""), delimiter="|"))
    need([row["JobIDRaw"] for row in sacct_rows]
         == ["559429", "559429.batch", "559429.extern"], "fresh sacct job/step rows")
    need(all(row["State"] == "COMPLETED" and row["ExitCode"] == "0:0"
             and row["Elapsed"] == "00:00:49" and row["AllocCPUS"] == "1"
             and row["NodeList"] == "snavely-cpu-02" for row in sacct_rows),
         "fresh sacct completion, elapsed time, CPU count and allocated node")
    need(sacct_rows[1]["MaxRSS"] == "101884K", "fresh batch-step peak resident memory receipt")
    scontrol = scontrol_path.read_text()
    for field in ("JobId=559429", "JobName=egg-v3-grb-physical", "Requeue=0",
                  "TimeLimit=00:30:00", "NumCPUs=1", "MinMemoryNode=8G",
                  "ExcNodeList=scaglione-compute-01",
                  "WorkDir=/home/nc437/egg-grb-physical-v3-20260927"):
        need(field in scontrol, "pre-run scontrol submission policy: " + field)
    outer_records = {}
    for label, path in (("intent", intent_path), ("submitted", submitted_path),
                        ("sacct", sacct_path), ("scontrol", scontrol_path)):
        data = path.read_bytes()
        outer_records[label] = {"bytes": len(data), "sha256": digest(data)}
    return {"wrapper_receipt": wrapper_receipt, "wrapper_launch": wrapper_launch,
            "slurm_receipt": slurm, "launch_sentinel": str(sentinel),
            "scheduler_logs": log_receipts,
            "outer_submission_receipts": outer_records,
            "sacct_rows": [{k: row[k] for k in ("JobIDRaw", "State", "ExitCode", "Elapsed",
                                                   "AllocCPUS", "MaxRSS", "NodeList")}
                           for row in sacct_rows],
            "scontrol_snapshot": "initial submission snapshot (captured while PENDING); execution completion is verified from later sacct and wrapper receipts",
            "raw_manifest_files": len(manifest["files"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=next((p for p in HERE.parents if (p / ".git").exists()), None))
    parser.add_argument("--attempt", type=Path, default=None)
    parser.add_argument("--slurm-dir", type=Path, default=None)
    parser.add_argument("--manifest-sha256", required=True,
                        help="sealed raw MANIFEST.json SHA-256 supplied by the run owner")
    args = parser.parse_args()
    repo = args.repository.resolve()
    attempt = (args.attempt or (repo / ATTEMPT_REL)).resolve()
    slurm_dir = (args.slurm_dir or (repo.parent / "research-20260927/cluster/grb-physical-559429")).resolve()
    sentinel = Path(str(attempt) + ".launch")
    report_path = HERE / "audit-report.json"
    need(not report_path.exists(), "new review report path")
    start_time = time.perf_counter()
    manifest, total_bytes = verify_raw_manifest(attempt, args.manifest_sha256)

    frozen = read(attempt / "frozen.json")
    full_commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", COMMIT]).decode().strip()
    need(full_commit == COMMIT and frozen["freeze_label"] == COMMIT,
         "published full source commit in archived run")
    need(frozen["protocol"] == PHYSICAL_PROTOCOL
         and frozen["formulation"] == FORMULATION
         and frozen["extraction_policy"] == POLICY
         and frozen["native_matrix"] == NATIVE_MATRIX
         and frozen["shared_negative_normalizer_policy"] == SHARED_POLICY,
         "frozen V3 matrix, extraction and normalization identities")
    old_attempt = repo / OLD_ATTEMPT_REL
    old_frozen_bytes = (old_attempt / "frozen.json").read_bytes()
    need(digest(old_frozen_bytes) == OLD_FROZEN_SHA,
         "CBC attempt3 frozen input identity")
    old_frozen = json.loads(old_frozen_bytes)
    compare_controls(frozen, old_frozen)
    need(len(frozen["source_hashes"]) == len(old_frozen["source_hashes"]),
         "physical source-list cardinality unchanged")
    source_blob_hashes = {}
    for rel, expected in frozen["source_hashes"].items():
        blob = subprocess.check_output(["git", "-C", str(repo), "show", f"{COMMIT}:{rel}"])
        need(digest(blob) == expected, "frozen published source blob: " + rel)
        source_blob_hashes[rel] = expected

    summary = read(attempt / "summary.json")
    need(summary["protocol"] == PHYSICAL_PROTOCOL and summary["all_pass"] is True
         and summary["source_hashes_unchanged"] is True,
         "complete physical summary and unchanged child sources")
    need(len(summary["cells"]) == 20
         and [row["cell"] for row in summary["cells"]] == EXPECTED_IDS,
         "complete unique ordered 20-control summary")
    wrapper = verify_wrapper_and_slurm(attempt, sentinel, slurm_dir, frozen, manifest, COMMIT)

    summary_by_id = {r["cell"]: r for r in summary["cells"]}
    cells = {c["id"]: c for c in frozen["controls"]}
    blobs, records, backend_runtime_rows = {}, [], []
    for name in EXPECTED_IDS:
        folder = attempt / name
        inp = read(folder / "input.json")
        need(inp["budget"] == frozen["budget"] and inp["source_hashes"] == frozen["source_hashes"]
             and {k: v for k, v in inp.items() if k in cells[name]} == cells[name],
             "exact frozen control, budget and source input: " + name)
        receipt = read(folder / "receipt.json")
        need(receipt == summary_by_id[name] and receipt["pass"] is True
             and receipt["returncode"] == 0 and receipt["hard_timeout"] is False
             and receipt["native_accounting_complete"] is True
             and receipt["evidence_issues"] == [], "successful control receipt: " + name)
        need(receipt["wall_s"] <= frozen["budget"]["wall_seconds"] + 15,
             "per-control hard timeout: " + name)
        launch = read(folder / "launch.json")
        cmd = launch["command"]
        need(launch["hard_timeout_s"] == frozen["budget"]["wall_seconds"] + 15
             and cmd[1:5] == ["-m", "experiments.native_pathflow_qualification", "--worker", name],
             "worker launch command and cap: " + name)
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
        result_package = read(folder / "result.json")
        need(result_package["environment"].get("mip_version")
             and result_package["environment"].get("gurobipy_version"),
             "captured GRB Python runtime versions: " + name)
        blobs[name] = {"events": events, "receipt": receipt, "result": result_package}
        record = physical_audit.audit_cell(cells[name], blobs[name])
        record["environment"] = {k: result_package["environment"].get(k)
                                 for k in ("python", "platform", "mip_version", "gurobipy_version")}
        records.append(record)
        for event in events:
            if event["event"] == "native_status":
                backend_runtime_rows.append(event["stats"]["backend_runtime"])

    all_passed = all(r["pass"] and r["status"] in ("certified", "infeasible") for r in records)
    need(all_passed and sum(r["status"] == "certified" for r in records) == 16
         and sum(r["status"] == "infeasible" for r in records) == 4,
         "all 16 target certificates and four expected infeasibilities")
    status_counts = Counter(e["stats"]["status"] for blob in blobs.values() for e in blob["events"]
                            if e["event"] == "native_status")
    actual_calls = sum(r["actual_native_calls"] for r in records)
    need(actual_calls == sum(r["native_calls_returned"] for r in summary["cells"]),
         "variable actual call total equals all returned receipts")
    controls = physical_audit.corruptions(cells, blobs)
    need(len(controls) >= 25 and all(c["rejected"] for c in controls),
         "all inherited native/projection/replay corruption controls rejected")

    libraries = sorted({r["native_library_sha256"] for r in backend_runtime_rows})
    versions = sorted({(r["mip_version"], r["gurobipy_version"])
                       for r in [b["result"]["environment"] for b in blobs.values()]})
    need(len(libraries) == 1 and len(versions) == 1,
         "one recorded GRB runtime library and Python package versions across all controls")
    final_manifest, final_bytes = verify_raw_manifest(attempt, args.manifest_sha256)
    need(final_manifest == manifest and final_bytes == total_bytes,
         "raw physical archive remains unchanged after independent audit")
    report = {
        "audit_status": "PASS: independent GRB physical result audit; 20/20 controls admitted",
        "downstream_scope": "Physical GRB stage only; hull qualification remains unaudited.",
        "scope": "Solver-free reconstruction of the frozen GRB physical attempt: published source blobs, CBC-parity inputs/budgets, GRB wrapper/sentinel/Slurm receipts, raw native rows, V3 charge corrections, physical replay, global bounds, exact analytical targets, and expected infeasibilities. This does not qualify the hull stage or nonlinear pilot.",
        "frozen_commit": COMMIT,
        "original_manifest_sha256": args.manifest_sha256,
        "original_files": len(manifest["files"]),
        "original_bytes": total_bytes,
        "frozen_source_count": len(source_blob_hashes),
        "frozen_source_hashes_verified_against_git_blobs": source_blob_hashes,
        "source_unchanged_receipts": {"wrapper": wrapper["wrapper_receipt"]["source_hashes_unchanged"],
                                      "controller": summary["source_hashes_unchanged"]},
        "unchanged_from_cbc_attempt3": {"control_count": 20, "controls_exact": True,
                                        "budget_fields_except_backend": True,
                                        "target_tolerance": True},
        "counts": {"controls": 20, "certified": 16, "expected_infeasible": 4,
                   "native_calls_actual": actual_calls,
                   "native_calls_by_cell": {r["cell"]: r["actual_native_calls"] for r in records},
                   "native_status_counts": dict(status_counts),
                   "raw_incumbents": sum(len(r["independently_reconstructed_rounds"]) for r in records),
                   "physical_witnesses": sum(len(r["physical_witnesses"]) for r in records),
                   "corruption_controls_rejected": len(controls)},
        "grb_runtime": {"backend": "GRB", "solver_module": "mip.gurobi",
                        "native_library_fingerprints": libraries,
                        "library_bytes_reverified_locally": False,
                        "mip_and_gurobipy_versions": versions},
        "wrapper_and_slurm": wrapper,
        "cells": records,
        "corruption_controls": controls,
        "stdout_policy": "Full wrapper and scheduler logs are preserved and hashed; log content is not embedded in this report because it may contain license details. Any public package must record any authorized omission by hash and retain the complete local archive.",
        "independence": "Uses copied standard-library exact-arithmetic fixture, V3 compact-matrix, energy-band and projection/replay auditors. No project implementation module, solver package, optimizer, SSH or web access is imported or called.",
        "audit_elapsed_s": time.perf_counter() - start_time,
    }
    out = report_path
    with out.open("x", encoding="utf-8") as f:
        json.dump(base.pack(report), f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"audit_status": report["audit_status"], "out": str(out),
                      "counts": report["counts"], "original_files": report["original_files"],
                      "original_bytes": report["original_bytes"]}, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
