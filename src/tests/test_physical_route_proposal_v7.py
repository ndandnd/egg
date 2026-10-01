import copy
import json
import signal
import sys
import time
import numpy as np
import pytest
from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_route_proposal_v7 as proposal
from egglab import route_fixed_repair as repair
from egglab import physical_route_model_v3 as previous
from experiments import native_recharge_qualification as qualification
from experiments import physical_route_proposal_pilot_v7 as pilot
from experiments import score_physical_route_proposal_v7 as scorer

SELECTED = {"out_A", "depot_AB", "in_B"}


def small_plan(case):
    return {"schema": nr.SCHEMA, "case_identity": case.identity(), "formulation": pf.FORMULATION,
        "native_matrix": pf.NATIVE_MATRIX, "extraction_policy": pf.EXTRACTION_POLICY,
        "vehicles": [{"vehicle": 0, "trips": ["A", "B"], "movements": ["out_A", "depot_AB", "in_B"]}],
        "charges": [{"vehicle": 0, "movement": "depot_AB", "connector": 0, "start_min": 60., "end_min": 120., "grid_kwh": 10.},
                    {"vehicle": 0, "movement": "in_B", "connector": 0, "start_min": 180., "end_min": 220., "grid_kwh": 20.}],
        "load": [0., 10., 0., 20.], "ops_cost": 7.}


def test_raw_matches_existing_input_rule_and_tie_break():
    case = qualification.cyclic_case()
    scores = np.array([10. if m.id in SELECTED else -10. for m in case.movements])
    class Fixed(edge.EdgePrior):
        def logits(self, case, prices): return scores
    prior = Fixed((), (), (), (), ())
    assert proposal.raw_decode(case, scores)["selected_movements"] == list(prior.propose_topology(case, [1.]*4))
    assert proposal.raw_decode(case, scores)["status"] == "structurally_valid"
    # Direct/depot parallel ties preserve original movement index.
    scores = [10. if m.id in SELECTED or m.id == "direct_AB" else -10. for m in case.movements]
    assert proposal.raw_decode(case, scores)["selected_movements"] == sorted(SELECTED)


def test_invalid_raw_topology_preserves_attempt_without_credit():
    case = qualification.cyclic_case()
    scores = [20. if m.id == "in_A" else 10. if m.id == "depot_AB" else 0. for m in case.movements]
    row = proposal.raw_decode(case, scores)
    assert row["status"] == "invalid_topology" and "depot_AB" in row["selected_movements"] and "in_A" in row["selected_movements"]
    assert row["physical_comparison_credit"] is False and "plan" not in row
    with pytest.raises(ValueError): proposal.raw_decode(case, [float("nan")]*len(case.movements))


def test_real_tiny_repair_then_charge_and_independent_replay_are_separate(monkeypatch):
    case = qualification.cyclic_case(); market = nh.Market("target", (1.,)*4, (0.,)*4)
    scores = [10. if m.id in SELECTED else -10. for m in case.movements]
    cover = proposal.stage("repair", case, market, [], {"logits": scores, "cover_policy": "cost_learned"})
    assert set(cover["selected_movements"]) == SELECTED
    plan = small_plan(case)
    def mock_charge(case, market, selected, budget):
        assert budget.threads == 1 and budget.wall_seconds == 55. and set(selected) == SELECTED
        return plan, nr.replay_native(case, plan), {"status": "OPTIMAL"}
    monkeypatch.setattr(repair, "_solve_fixed_charge", mock_charge)
    charged = proposal.stage("charge", case, market, [], cover)
    assert charged["physical_comparison_credit"] is False and "objective_exact" not in charged
    replayed = proposal.stage("replay", case, market, [], {**charged, "source_topologies": [sorted(SELECTED)]})
    assert replayed["objective_exact"] == "37" and replayed["vehicle_count"] == 1 and replayed["topology_novel"] is False
    assert proposal.replay_candidate(case, market, plan, SELECTED, [])["topology_novel"] is None


def test_bad_replay_and_changed_topology_have_no_credit():
    case = qualification.cyclic_case(); market = nh.Market("target", (1.,)*4, (0.,)*4)
    plan = small_plan(case); plan["load"][1] = 0.
    with pytest.raises(ValueError): proposal.replay_candidate(case, market, plan, SELECTED, [])
    with pytest.raises(ValueError): proposal.replay_candidate(case, market, small_plan(case), {"out_A", "direct_AB", "in_B"}, [])


def test_source_policy_retains_direct_if_linear_recharge_worsens_curved_bill():
    direct = [{"source": "source0", "direct_bill_exact": "10"}, {"source": "source1", "direct_bill_exact": "12"}]
    assert proposal.source_policy(direct, {"source0_recharged": {"status": "replayed", "objective_exact": "11"}})["selected_arm"] == "source0_direct"
    best = proposal.source_policy(direct, {"source0_recharged": None, "source1_recharged": {"status": "replayed", "objective_exact": "9"}})
    assert best["selected_arm"] == "source1_recharged" and best["uses_all_direct_admission_and_attempted_source_charge_replay_stages"]


def test_all_sixteen_groups_use_seed17_outer_models_and_no_inner_leakage():
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
    for group in proposal.GROUP_IDS:
        fold = (group-10000)%4; parts = previous.grouped_split(groups, fold)
        result = dict(zip(("fit_groups", "inner_groups", "outer_groups"), parts))
        result.update(seed=17, fold=fold, task_id=fold*3)
        scorer.validate_partition(group, result)
        changed = copy.deepcopy(result); changed["seed"] = 29
        with pytest.raises(ValueError): scorer.validate_partition(group, changed)
        changed = copy.deepcopy(result); changed["fit_groups"] = list(changed["fit_groups"])+[f"physical_v2_s{group}"]
        with pytest.raises(ValueError): scorer.validate_partition(group, changed)


def test_stage_signal_receipt_and_no_automatic_retry(tmp_path):
    supervisor = pilot.Supervisor(tmp_path, tmp_path/"manifest.json", time.monotonic()+20.)
    row = supervisor.execute("probe", [sys.executable, "-c", "import os,signal;os.kill(os.getpid(),signal.SIGTERM)"], 1.)
    assert row is None
    receipt = json.loads((tmp_path/"probe.receipt.json").read_text())
    assert receipt["status"] == "failed" and receipt["signal"] == signal.SIGTERM and receipt["attempted"]
    assert (tmp_path/"probe.start.json").exists() and receipt["wall_seconds"] > 0
    with pytest.raises(FileExistsError): supervisor.execute("probe", [sys.executable, "-c", "pass"], 1.)


def test_stage_timeout_and_overall_budget_skip(tmp_path):
    supervisor = pilot.Supervisor(tmp_path, tmp_path/"manifest.json", time.monotonic()+20.)
    assert supervisor.execute("slow", [sys.executable, "-c", "import time;time.sleep(5)"], .05) is None
    receipt = json.loads((tmp_path/"slow.receipt.json").read_text())
    assert receipt["timed_out"] and receipt["status"] == "failed" and receipt["wall_seconds"] > 0
    supervisor.deadline = time.monotonic()
    assert supervisor.execute("capped", [sys.executable, "-c", "raise Exception('must not execute')"], 1.) is None
    assert supervisor.receipts["capped"]["status"] == "skipped" and not supervisor.receipts["capped"]["attempted"]


def test_hash_guard_and_path_escape(tmp_path):
    path = tmp_path/"artifact"; path.write_text("a")
    with pytest.raises(ValueError): scorer.checked_path("../../outside")
    with pytest.raises(ValueError): scorer.verify_files({"src/egglab/physical_route_proposal_v7.py": "0"*64})


def test_budgets_fit_total_and_native_one_thread():
    caps = pilot.CAPS
    total = caps["inputs"]+3*caps["score"]+caps["sources"]+4*caps["repair"]+9*caps["charge"]+10*caps["replay"]+3*caps["raw_decode"]+caps["cold_planner"]+caps["cold_hull"]+caps["retained_hull"]+caps["accounting"]
    assert total == 1490. < pilot.TASK_SECONDS < 1700.
    assert proposal.charge_budget().threads == 1


def test_runner_preserves_primary_source_raw_order_and_postchoice_accounting(tmp_path, monkeypatch):
    case = qualification.cyclic_case(); market = nh.Market("target", (1.,)*4, (0.,)*4); plan = small_plan(case)
    identity = {"group_id": 10064, "case_identity": case.identity(), "market_identity": market.identity(), "movement_ids": [m.id for m in case.movements]}
    manifest = tmp_path/"manifest.json"
    scorer.save(manifest, {"policy": scorer.POLICY, "group_ids": list(scorer.GROUP_IDS), "source_hashes": {}, "replay_attestations": {}})
    monkeypatch.setattr(scorer, "verify_files", lambda hashes: None)
    monkeypatch.setattr(pilot.subprocess, "check_output", lambda *a, **k: "frozen-commit")
    order = []
    def receipt(self, key):
        self.receipts[key] = {"status": "completed", "wall_seconds": .1}
    def execute(self, key, command, cap):
        order.append(key); receipt(self, key)
        return {**identity, "arm": key.removeprefix("score_"), "logits": [0.]*len(case.movements)}
    def stage(self, key, name, group, native, payload=None):
        order.append(key); receipt(self, key)
        if name == "inputs": data = {"group_eligibility": {"observed_source_count": 1}}
        elif name == "sources": data = {"candidates": [{"source": "source0", "topology": sorted(SELECTED), "plan": plan, "plan_hash": "p", "direct_bill_exact": "37"}], "observed_sources": 1, "intended_sources": 2}
        elif name == "repair": data = {"selected_movements": sorted(SELECTED)}
        elif name == "charge": data = {"plan": plan, "selected_movements": sorted(SELECTED)}
        elif name == "replay": data = {"status": "replayed", "plan": plan, "objective_exact": "38", "vehicle_count": 1}
        elif name == "raw_decode": data = {"status": "invalid_topology", "selected_movements": ["out_A"]}
        elif name == "cold_planner": data = {"status": "unresolved"}
        elif name == "accounting":
            assert (tmp_path/"out/task00/comparison.json").exists()
            assert json.loads((tmp_path/"out/task00/source_policy.json").read_text())["selected_arm"] == "source0_direct"
            data = {"paid_seconds_total": 99.}
        else: data = {"status": "checked"}
        return {**identity, "data": data}
    monkeypatch.setattr(pilot.Supervisor, "execute", execute); monkeypatch.setattr(pilot.Supervisor, "stage", stage)
    pilot.run(0, manifest, scorer.sha(manifest), "family", "graph", "native", output=tmp_path/"out")
    comparison = json.loads((tmp_path/"out/task00/comparison.json").read_text())
    assert comparison["source_policy"]["objective_exact"] == "37"
    assert all(row is None for row in comparison["raw_decode_diagnostics"].values())
    assert set(comparison["primary_repaired_proposals"]) == set((*scorer.ARMS, "cost_only"))
    assert order.index("cost_only_replay") < order.index("tabular_v3_raw_decode") < order.index("accounting")
    assert "source1_charge" not in order  # Censored source remains an explicit skipped attempt.
    receipt = json.loads((tmp_path/"out/task00/receipt.json").read_text())
    assert receipt["stage_receipts"]["source1_charge"]["status"] == "skipped"
    assert receipt["source_acquisition_accounting"]["data"]["paid_seconds_total"] == 99.
    with pytest.raises(FileExistsError): pilot.run(0, manifest, scorer.sha(manifest), "family", "graph", "native", output=tmp_path/"out")


def test_family_seed17_mapping_preserves_original_success_and_only_failed_recoveries():
    assert scorer.model_folder("families_v5", 3).parent.name == "20260930-route-model128-families-v5"
    for task in (0, 6, 9):
        assert scorer.model_folder("families_v5", task).parent.name == "20260930-route-model128-families-v5-recovery1"


def test_executed_lazy_qp_and_runtime_backend_dependencies_are_source_pinned():
    import ast
    source = ast.parse((scorer.ROOT/"src/egglab/native_hull.py").read_text())
    lazy = {alias.name for node in ast.walk(source) if isinstance(node, ast.ImportFrom) and node.module == "egglab" for alias in node.names}
    assert "restricted_qp_proposal" in lazy
    assert "src/egglab/restricted_qp_proposal.py" in scorer.SOURCE_FILES
    assert "from egglab.solver import backend" in (scorer.ROOT/"src/cluster/unicorn_env.sh").read_text()
    assert "src/egglab/solver.py" in scorer.SOURCE_FILES
