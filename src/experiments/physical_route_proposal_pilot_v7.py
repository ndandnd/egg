"""Bounded append-only proposal comparison; stdlib supervisor isolates every stage."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from experiments import score_physical_route_proposal_v7 as frozen

ROOT = frozen.ROOT
OUTPUT = ROOT / "result/physical_learning/20260930-route-proposal-train-v7"
CAPS = {"inputs": 20., "score": 120., "sources": 20., "raw_decode": 10., "repair": 15.,
        "charge": 65., "replay": 15., "cold_planner": 80., "cold_hull": 85., "retained_hull": 85., "accounting": 15.}
TASK_SECONDS = 1650.


class Supervisor:
    def __init__(self, destination, manifest, deadline):
        self.dest, self.manifest, self.deadline = Path(destination), Path(manifest), deadline
        self.receipts = {}

    def skip(self, key, reason):
        receipt = {"stage_key": key, "status": "skipped", "reason": reason, "wall_seconds": 0., "attempted": False}
        frozen.save(self.dest / f"{key}.receipt.json", receipt); self.receipts[key] = receipt
        return None

    def execute(self, key, command, cap):
        if time.monotonic()+cap+10. > self.deadline:
            return self.skip(key, "overall_budget_reserve")
        frozen.save(self.dest / f"{key}.start.json", {"stage_key": key, "cap_seconds": cap, "started_unix": time.time()})
        started = time.monotonic(); code, timed_out, error = None, False, None
        with (self.dest / f"{key}.stdout").open("xb") as out, (self.dest / f"{key}.stderr").open("xb") as err:
            try:
                process = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
                try:
                    code = process.wait(timeout=cap)
                except subprocess.TimeoutExpired:
                    import signal
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL); code = process.wait()
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
        output = self.dest / f"{key}.json"
        receipt = {"stage_key": key, "status": "completed" if code == 0 and output.is_file() else "failed",
            "attempted": True, "returncode": code, "signal": -code if code is not None and code < 0 else None,
            "timed_out": timed_out, "error": error, "wall_seconds": time.monotonic()-started,
            "cap_seconds": cap, "stdout_sha256": frozen.sha(self.dest / f"{key}.stdout"),
            "stderr_sha256": frozen.sha(self.dest / f"{key}.stderr")}
        if receipt["status"] == "completed":
            try:
                row = frozen.read(output)
                if not isinstance(row, dict): raise ValueError("Stage output must be an object")
                receipt["output_sha256"] = frozen.sha(output)
                receipt["scientific_status"] = row.get("data", {}).get("status")
            except Exception as exc:
                receipt.update(status="failed", error={"type": type(exc).__name__, "message": str(exc)})
        failure_path = self.dest / f"{key}.failure.json"
        if failure_path.is_file():
            receipt["failure"] = frozen.read(failure_path)
            receipt["failure_sha256"] = frozen.sha(failure_path)
        frozen.save(self.dest / f"{key}.receipt.json", receipt); self.receipts[key] = receipt
        return frozen.read(output) if receipt["status"] == "completed" else None

    def stage(self, key, stage, group_id, native_python, payload=None):
        path = self.dest / f"{key}.input.json"; frozen.save(path, payload or {})
        return self.execute(key, [native_python, "-m", "experiments.physical_route_proposal_pilot_v7", "stage",
            "--stage", stage, "--group-id", str(group_id), "--manifest", str(self.manifest),
            "--payload", str(path), "--output", str(self.dest / f"{key}.json")], CAPS[stage])


def acquisition(group_id):
    # This table is opened after every proposal and source policy is persisted.
    from experiments import pool_physical_route_training_v3 as pool
    from experiments import computational_benchmark as base
    folder = pool._dataset((group_id-10000)//8)
    receipt = frozen.read(folder / "dataset_receipt.json"); path = folder / "source_outcomes.jsonl"
    if receipt.get("status") != "complete" or receipt["output_hashes"][path.name] != base.sha(path):
        raise ValueError("Source acquisition accounting differs")
    rows = [json.loads(s) for s in path.read_text().splitlines()]
    rows = [r for r in rows if r["base_id"] == group_id]
    if len(rows) != 2 or {r["source"] for r in rows} != {"source0", "source1"}:
        raise ValueError("Missing intended source attempts")
    return {"intended_source_cells": 2, "paid_seconds_total": sum(float(r["paid_seconds"]) for r in rows),
        "source_outcomes_sha256": base.sha(path), "dataset_receipt_sha256": base.sha(folder / "dataset_receipt.json"),
        "by_source": {r["source"]: {"status": r["status"], "paid_seconds": r["paid_seconds"], "native_status": r.get("native_status")} for r in rows}}


def stage_child(args):
    from egglab import physical_route_proposal_v7 as proposal
    manifest = frozen.read(args.manifest); frozen.verify_files(manifest["source_hashes"])
    case, market, sources, eligibility = proposal.inputs(args.group_id, manifest)
    payload = frozen.read(args.payload); started = time.monotonic()
    if args.stage == "inputs":
        row = {"group_eligibility": eligibility}
    elif args.stage == "accounting":
        row = acquisition(args.group_id)
    else:
        row = proposal.stage(args.stage, case, market, sources, payload)
    frozen.save(args.output, {"stage": args.stage, "group_id": args.group_id,
        "case_identity": case.identity(), "market_identity": market.identity(),
        "movement_ids": [m.id for m in case.movements], "stage_compute_seconds": time.monotonic()-started, "data": row})


def run(task_id, manifest_path, manifest_sha, family_python, graph_python, native_python=sys.executable, output=OUTPUT):
    if task_id not in range(16) or frozen.sha(manifest_path) != manifest_sha:
        raise ValueError("Undeclared task or manifest hash")
    manifest = frozen.read(manifest_path)
    if manifest["policy"] != frozen.POLICY or manifest["group_ids"] != list(frozen.GROUP_IDS):
        raise ValueError("Not the reviewed prospective input freeze")
    destination = Path(output) / f"task{task_id:02d}"
    destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic(); group_id = frozen.GROUP_IDS[task_id]
    frozen.save(destination / "launch.json", {"policy": frozen.POLICY, "group_id": group_id, "task_id": task_id,
        "manifest_sha256": manifest_sha, "started_unix": time.time(), "no_retry": True})
    supervisor = Supervisor(destination, manifest_path, started+TASK_SECONDS)
    try:
        frozen.verify_files(manifest["source_hashes"])
        for attestation in manifest["replay_attestations"].values():
            if frozen.sha(frozen.checked_path(attestation["path"])) != attestation["sha256"]:
                raise ValueError("Reviewed replay attestation changed")
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        frozen.save(destination / "source_identity.json", {"source_commit": commit, "source_hashes": manifest["source_hashes"],
            "manifest_sha256": manifest_sha, "native_python": native_python, "family_python": family_python, "graph_python": graph_python})
        identity = supervisor.stage("inputs", "inputs", group_id, native_python)
        if identity is None: raise ValueError("Input admission stage failed")
        scores = {}
        for arm in frozen.ARMS:
            row = supervisor.execute("score_"+arm, [graph_python if arm == "graph_v6" else family_python,
                "-m", "experiments.score_physical_route_proposal_v7", "score", "--arm", arm, "--group-id", str(group_id),
                "--manifest", str(manifest_path), "--output", str(destination / ("score_"+arm+".json"))], CAPS["score"])
            if row is not None and any(row[k] != identity[k] for k in ("case_identity", "market_identity", "movement_ids", "group_id")):
                raise ValueError("Scoring target/movement identity mismatch")
            scores[arm] = row
        sources = supervisor.stage("sources", "sources", group_id, native_python)
        controls = sources["data"] if sources else {"candidates": [], "observed_sources": 0, "intended_sources": 2}
        topologies = [c["topology"] for c in controls["candidates"]]
        proposals = {}

        def charge_replay(key, selected):
            if selected is None:
                supervisor.skip(key+"_charge", "preceding_topology_unavailable")
                supervisor.skip(key+"_replay", "preceding_topology_unavailable"); return None
            charged = supervisor.stage(key+"_charge", "charge", group_id, native_python, {"selected_movements": selected})
            if charged is None:
                supervisor.skip(key+"_replay", "charging_failed"); return None
            replay = supervisor.stage(key+"_replay", "replay", group_id, native_python,
                {**charged["data"], "source_topologies": topologies})
            return replay["data"] if replay else None

        # Repaired-only learned arms are primary and always precede raw diagnostics.
        for arm in (*frozen.ARMS, "cost_only"):
            if arm != "cost_only" and scores[arm] is None:
                supervisor.skip(arm+"_repair", "scoring_failed"); selected = None
            else:
                repaired = supervisor.stage(arm+"_repair", "repair", group_id, native_python,
                    {"logits": None if arm == "cost_only" else scores[arm]["logits"],
                     "cover_policy": "cost_only" if arm == "cost_only" else "cost_learned"})
                selected = repaired["data"]["selected_movements"] if repaired else None
            proposals[arm] = charge_replay(arm, selected)
        recharged = {}
        by_source = {c["source"]: c for c in controls["candidates"]}
        for source in ("source0", "source1"):
            selected = by_source[source]["topology"] if source in by_source else None
            recharged[source+"_recharged"] = charge_replay(source, selected)
        # Source policy is fixed before raw diagnostics, hulls, or accounting reads.
        from fractions import Fraction
        choices = [(c["source"]+"_direct", c["direct_bill_exact"]) for c in controls["candidates"]]
        choices += [(name, row["objective_exact"]) for name, row in recharged.items() if row]
        choice = min(choices, key=lambda p: (Fraction(p[1]), p[0])) if choices else None
        source_policy = {"status": "replayed" if choice else "unavailable", "selected_arm": choice[0] if choice else None,
            "objective_exact": choice[1] if choice else None, "uses_all_direct_and_attempted_source_charge_replay_stages": True}
        frozen.save(destination / "source_policy.json", source_policy)
        raw = {}
        for arm in frozen.ARMS:
            key = arm+"_raw"
            if scores[arm] is None:
                supervisor.skip(key+"_decode", "scoring_failed"); selected = None
            else:
                decoded = supervisor.stage(key+"_decode", "raw_decode", group_id, native_python, {"logits": scores[arm]["logits"]})
                selected = decoded["data"]["selected_movements"] if decoded and decoded["data"]["status"] == "structurally_valid" else None
            raw[arm] = charge_replay(key, selected)
        cold = supervisor.stage("cold_planner", "cold_planner", group_id, native_python)
        if cold and cold["data"].get("plan"):
            plan = cold["data"]["plan"]
            replay = supervisor.stage("cold_planner_replay", "replay", group_id, native_python,
                {"plan": plan, "selected_movements": sorted({m for v in plan["vehicles"] for m in v["movements"]}), "source_topologies": topologies})
            cold_physical = replay["data"] if replay else None
        else:
            supervisor.skip("cold_planner_replay", "cold_solver_has_no_incumbent"); cold_physical = None
        cold_hull = supervisor.stage("cold_hull", "cold_hull", group_id, native_python)
        if controls["candidates"]:
            retained = supervisor.stage("retained_hull", "retained_hull", group_id, native_python,
                {"plans": [c["plan"] for c in controls["candidates"]], "lineage": {"policy": frozen.POLICY, "group_id": group_id,
                    "source_plan_hashes": [c["plan_hash"] for c in controls["candidates"]]}})
        else:
            supervisor.skip("retained_hull", "no_replayed_sources"); retained = None
        frozen.save(destination / "comparison.json", {"policy": frozen.POLICY, "task_id": task_id, "group_id": group_id,
            "case_identity": identity["case_identity"], "market_identity": identity["market_identity"],
            "eligibility": identity["data"]["group_eligibility"], "primary_repaired_proposals": proposals,
            "raw_decode_diagnostics": raw, "direct_source_controls": controls, "source_recharges": recharged,
            "source_policy": source_policy, "cold_physical_incumbent": cold_physical,
            "cold_hull_relaxation": cold_hull, "retained_source_hull_relaxation": retained,
            "no_training_or_optimality_or_speedup_claim": True})
        accounting = supervisor.stage("accounting", "accounting", group_id, native_python)
        frozen.save(destination / "receipt.json", {"status": "completed_with_preserved_stage_failures", "task_id": task_id,
            "group_id": group_id, "manifest_sha256": manifest_sha, "comparison_sha256": frozen.sha(destination / "comparison.json"),
            "source_acquisition_accounting": accounting, "stage_receipts": supervisor.receipts,
            "all_attempted_stage_wall_seconds": sum(r["wall_seconds"] for r in supervisor.receipts.values()),
            "wall_seconds": time.monotonic()-started})
        return {"task_id": task_id, "stage_failures": [k for k, r in supervisor.receipts.items() if r["status"] == "failed"]}
    except BaseException as exc:
        frozen.save(destination / "failure.json", {"type": type(exc).__name__, "message": str(exc), "stage_receipts": supervisor.receipts})
        frozen.save(destination / "receipt.json", {"status": "failed", "task_id": task_id, "group_id": group_id,
            "wall_seconds": time.monotonic()-started, "failure_sha256": frozen.sha(destination / "failure.json")})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="mode", required=True)
    run_parser = sub.add_parser("run"); run_parser.add_argument("--task-id", type=int, required=True)
    run_parser.add_argument("--manifest", type=Path, required=True); run_parser.add_argument("--manifest-sha", required=True)
    run_parser.add_argument("--family-python", required=True); run_parser.add_argument("--graph-python", required=True)
    child = sub.add_parser("stage"); child.add_argument("--stage", choices=tuple(CAPS), required=True)
    child.add_argument("--group-id", type=int, required=True); child.add_argument("--manifest", type=Path, required=True)
    child.add_argument("--payload", type=Path, required=True); child.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "stage":
        try:
            stage_child(args)
        except Exception as exc:
            row = {"stage": args.stage, "type": type(exc).__name__, "message": str(exc)}
            if hasattr(exc, "telemetry"): row["telemetry"] = exc.telemetry
            frozen.save(args.output.with_suffix(".failure.json"), row)
            raise
    else: print(json.dumps(run(args.task_id, args.manifest, args.manifest_sha, args.family_python, args.graph_python)))


if __name__ == "__main__": main()
