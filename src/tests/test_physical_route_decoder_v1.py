import json
import subprocess

import numpy as np
import pytest

from egglab import native_hull as nh
from egglab import native_recharge as nr
from egglab import native_pathflow as pf
from egglab import physical_route_decoder_v1 as decoder
from egglab import route_fixed_repair as repair
from experiments import computational_benchmark as base
from experiments import native_recharge_qualification as qualification
from experiments import physical_route_decoder_pilot_v1 as pilot
from experiments import route_repair_pilot as existing_repair


SELECTED = {"out_A", "depot_AB", "in_B"}


def small_plan(case):
    plan = {"schema": nr.SCHEMA, "case_identity": case.identity(),
        "formulation": pf.FORMULATION, "native_matrix": pf.NATIVE_MATRIX,
        "extraction_policy": pf.EXTRACTION_POLICY,
        "vehicles": [{"vehicle": 0, "trips": ["A", "B"],
                      "movements": ["out_A", "depot_AB", "in_B"]}],
        "charges": [{"vehicle": 0, "movement": "depot_AB", "connector": 0,
                     "start_min": 60., "end_min": 120., "grid_kwh": 10.},
                    {"vehicle": 0, "movement": "in_B", "connector": 0,
                     "start_min": 180., "end_min": 220., "grid_kwh": 20.}],
        "load": [0., 10., 0., 20.], "ops_cost": 7.}
    assert nr.replay_native(case, plan)["replay_ok"]
    return plan


def test_real_small_cover_then_mock_charge_then_independent_replay(monkeypatch):
    case = qualification.cyclic_case()
    market = nh.Market("target", (1.,)*4, (0.,)*4)
    plan = small_plan(case)
    logits = [10. if m.id in SELECTED else -10. for m in case.movements]
    def charge(_case, _market, selected, _budget):
        assert set(selected) == SELECTED
        return plan, nr.replay_native(case, plan), {"status": "OPTIMAL"}
    monkeypatch.setattr(repair, "_solve_fixed_charge", charge)
    result = decoder.decoded_candidate(case, market, logits, [SELECTED],
        cover_policy="cost_learned", path_seconds=1.,
        charge_budget=nr.Budget(backend="CBC", phase_seconds=1., wall_seconds=2.))
    assert result["status"] == "replayed"
    assert result["topology_novel"] is False
    assert result["native_stats"]["status"] == "OPTIMAL"
    assert result["objective_exact"] == "37"
    assert all(k in result["timing_seconds"] for k in ("cover", "charging", "independent_replay"))


def test_charge_failure_is_typed_and_no_global_claim(monkeypatch):
    case = qualification.cyclic_case()
    market = nh.Market("target", (1.,)*4, (0.,)*4)
    logits = [10. if m.id in SELECTED else -10. for m in case.movements]
    monkeypatch.setattr(repair, "_solve_fixed_charge", lambda *args: (_ for _ in ()).throw(
        ValueError("no charge schedule")))
    result = decoder.decoded_candidate(case, market, logits, [SELECTED],
        cover_policy="cost_learned", path_seconds=1.,
        charge_budget=nr.Budget(backend="CBC", phase_seconds=1., wall_seconds=2.))
    assert result["status"] == "failed"
    assert result["failure"]["stage"] == "charging"
    assert "plan" not in result and "objective_exact" not in result
    arms = pilot.summarize_arms({"learned": {"kind": "learned_decoder",
        "proposal": result, "global_verification": None},
        "cold": {"kind": "native_control", "global_verification": {
            "status": "checked", "assessment": {"status": "bounded"}}}})
    assert arms["learned"]["global_status"] is None
    assert arms["cold"]["proposal_status"] is None
    assert arms["cold"]["global_status"] == "checked"


def test_censored_group_source_controls_and_feasible_import():
    sha = base.sha(pilot.POOL64 / "pool_manifest.json")
    case, market, sources, eligibility = pilot.case_inputs(10037, sha)
    controls = decoder.admitted_source_controls(case, market, sources)
    assert eligibility["missing_source_labels"] == ["source0"]
    assert controls["observed_sources"] == 1
    assert controls["nearest_price"] == controls["cheapest_exact_bill"] == "source1"
    envelope, identity = decoder.feasible_envelope(case, market,
        [controls["candidates"][0]["plan"]], {"fixture": "source1"},
        existing_repair.hull_budget())
    assert envelope["state_identity"] == identity
    assert len(envelope["columns"]) == 1
    assert envelope["status"] == "bounded"


def test_pinned_logistic_artifact_ignores_outer_metric_values(tmp_path):
    group = "physical_v2_s10037"
    folder = tmp_path / "task03"
    folder.mkdir()
    result = {"policy": "physical-source-movement-scorer-exact-prefix-v3",
        "task_id": 3, "seed": 17, "fold": 1,
        "pool_manifest_sha256": "a"*64,
        "features": list(decoder.edge.FEATURES),
        "fit_groups": ["physical_v2_s10000"], "inner_groups": ["physical_v2_s10001"],
        "outer_groups": [group],
        "feature_mean_fit_only": [0.]*17,
        "feature_scale_fit_only": [1.]*17,
        "logistic": {"coef": [[0.]*17], "intercept": [0.],
            "config": {"C": 1., "solver": "lbfgs", "max_iter": 1000, "tol": 1e-6}},
        "outer_metrics": {"logistic": {"weighted_log_loss": 999.}}}
    result_path = folder / "result.json"
    result_path.write_text(json.dumps(result))
    receipt = {"status": "completed", "task_id": 3,
        "pool_manifest_sha256": "a"*64,
        "result_sha256": base.sha(result_path)}
    (folder / "receipt.json").write_text(json.dumps(receipt))
    scorer = decoder.load_scorer(tmp_path, prefix=64, name="logistic",
        group_id=10037, expected_pool_manifest_sha256="a"*64)
    assert scorer.fold == 1 and scorer.seed == 17
    assert scorer.outer_groups == (group,)
    case, market, _, _ = pilot.case_inputs(10037, base.sha(pilot.POOL64 / "pool_manifest.json"))
    assert np.allclose(scorer.logits(case, market.a), 0.)
    result["outer_metrics"] = {"logistic": {"weighted_log_loss": 0.001}}
    result_path.write_text(json.dumps(result))
    receipt["result_sha256"] = base.sha(result_path)
    (folder / "receipt.json").write_text(json.dumps(receipt))
    again = decoder.load_scorer(tmp_path, prefix=64, name="logistic",
        group_id=10037, expected_pool_manifest_sha256="a"*64)
    assert np.array_equal(scorer.logits(case, market.a), again.logits(case, market.a))


def test_score_child_error_preserves_stderr_and_failure_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot.subprocess, "run", lambda *args, **kwargs:
        subprocess.CompletedProcess(args[0], 7, "partial scores", "pinned model missing"))
    sha32 = base.sha(pilot.POOL32 / "pool_manifest.json")
    sha64 = base.sha(pilot.POOL64 / "pool_manifest.json")
    with pytest.raises(RuntimeError, match="exited 7"):
        pilot.run(0, sha32, sha64, "/nonexistent/score-python", tmp_path)
    folder = tmp_path / "task00"
    child = json.loads((folder / "score_child.json").read_text())
    assert child["returncode"] == 7 and "pinned model missing" in child["stderr"]
    assert json.loads((folder / "receipt.json").read_text())["status"] == "failed"
    assert (folder / "launch.json").is_file()
