"""Frozen GIRO subset contract, tamper refusals, and compatibility pins."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from egglab.frozen import (
    INSTANCE_FILENAME,
    MANIFEST_FILENAME,
    PROVENANCE_SCHEMA,
    FrozenSubsetError,
    canonical_json_bytes,
    freeze_subset,
)
from egglab.instance import Instance, Trip, load_frozen_subset, synthetic_instance


def _instance_parameters(inst):
    return {
        "depot": inst.depot,
        "battery_kwh": inst.battery_kwh,
        "soc0_kwh": inst.soc0_kwh,
        "soc_min_kwh": inst.soc_min_kwh,
        "soc_end_kwh": inst.soc_end_kwh,
        "charge_power_kw": inst.charge_power_kw,
        "n_slots": inst.n_slots,
        "slot_min": inst.slot_min,
        "max_vehicles": inst.max_vehicles,
        "vehicle_fixed_cost": inst.vehicle_fixed_cost,
        "dh_cost_per_min": inst.dh_cost_per_min,
    }


def _write_inputs(root: Path, *, instance=None):
    root.mkdir(parents=True)
    inst = instance or synthetic_instance(seed=7, n_trips=4)
    candidate = root / "reviewed-instance.json"
    candidate.write_bytes(canonical_json_bytes(inst.canonical()))
    provenance = root / "reviewed-provenance.json"
    provenance.write_bytes(
        canonical_json_bytes(
            {
                "schema": PROVENANCE_SCHEMA,
                "contract": "Partille",
                "service_day": None,
                "variant_choice": {
                    "policy": "fixture: one selected variant per base task",
                    "selected": ["fixture-m"],
                },
                "trip_selection": {
                    "rule": "Identifier == Regular",
                    "source_rows": list(
                        range(101, 101 + len(inst.trips))
                    ),
                    "trip_ids": [trip.id for trip in inst.trips],
                },
                "deadhead_fidelity": {
                    "level": "exact-directed-base",
                    "directed": True,
                    "time_dependent": False,
                    "same_reference_policy": "no zero-cost inference",
                    "missing_link_policy": "unavailable arcs remain absent",
                },
                "physics": {
                    "service_energy_policy": "accept source Usage kWh",
                    "instance_parameters": _instance_parameters(inst),
                },
            }
        )
    )
    source = root / "source.csv"
    source.write_bytes(
        b"Identifier,Start1\n"
        + b"".join(
            f"Regular,{4 + index:02d}:45\n".encode()
            for index in range(len(inst.trips))
        )
    )
    return inst, candidate, provenance, source


def _freeze(root: Path, *, name="frozen"):
    inst, candidate, provenance, source = _write_inputs(root / "inputs")
    result = freeze_subset(
        candidate,
        provenance,
        root / name,
        source_files={"vehicle_details": source},
    )
    return inst, Path(result["directory"]), result


def _rewrite_manifest(artifact: Path, mutate) -> dict:
    path = artifact / MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    mutate(manifest)
    path.write_bytes(canonical_json_bytes(manifest))
    return manifest


def test_instance_hash_and_synthetic_generator_are_pinned():
    """The loader work must not perturb either identity implementation."""
    manual = Instance(
        name="hash-pin",
        trips=[Trip("t0", 300, 345, "A", "B", 12.5)],
        depot="D",
        dh_min={("D", "A"): 10, ("B", "D"): 12},
        dh_kwh={("D", "A"): 2.0, ("B", "D"): 2.4},
        battery_kwh=60.0,
        soc0_kwh=60.0,
        soc_min_kwh=6.0,
        soc_end_kwh=6.0,
        charge_power_kw=150.0,
    )
    assert manual.hash() == "0a4ee2c55954"
    assert synthetic_instance().hash() == "6fe69ed30df4"
    assert synthetic_instance(seed=7, n_trips=4).hash() == "abd9af259a38"


def test_freeze_and_load_round_trip_from_all_supported_paths(tmp_path):
    original, artifact, result = _freeze(tmp_path)
    assert {path.name for path in artifact.iterdir()} == {
        INSTANCE_FILENAME,
        MANIFEST_FILENAME,
    }
    manifest_bytes = (artifact / MANIFEST_FILENAME).read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    assert result["manifest_sha256"] == manifest_sha

    loaded_from_dir = load_frozen_subset(
        artifact, expected_manifest_sha256=manifest_sha
    )
    loaded_from_instance = load_frozen_subset(artifact / INSTANCE_FILENAME)
    loaded_from_manifest = load_frozen_subset(artifact / MANIFEST_FILENAME)
    loaded_explicit = load_frozen_subset(
        artifact / INSTANCE_FILENAME,
        artifact / MANIFEST_FILENAME,
    )
    for loaded in (
        loaded_from_dir,
        loaded_from_instance,
        loaded_from_manifest,
        loaded_explicit,
    ):
        assert loaded.canonical() == original.canonical()
        assert loaded.hash() == original.hash()


def test_sparse_directed_matrix_and_independent_policy_knobs_round_trip(tmp_path):
    """The freeze must preserve Instance semantics, not complete GIRO arcs."""
    sparse = Instance(
        name="sparse-policy-pin",
        trips=[Trip("source-row-101", 300, 345, "A", "B", 0.0)],
        depot="D",
        dh_min={("D", "A"): 10, ("B", "D"): 12},
        dh_kwh={("D", "A"): 2.0, ("B", "D"): 2.4},
        battery_kwh=60.0,
        soc0_kwh=60.0,
        soc_min_kwh=12.0,
        soc_end_kwh=6.0,
        charge_power_kw=0.0,
    )
    _inst, candidate, provenance, source = _write_inputs(
        tmp_path / "inputs", instance=sparse
    )
    artifact = tmp_path / "frozen"
    freeze_subset(
        candidate,
        provenance,
        artifact,
        source_files={"vehicle_details": source},
    )
    loaded = load_frozen_subset(artifact)
    assert loaded.canonical() == sparse.canonical()
    assert loaded.hash() == sparse.hash()


def test_manifest_binds_sources_without_copying_confidential_bytes(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    manifest = json.loads((artifact / MANIFEST_FILENAME).read_text())
    source_record = manifest["inputs"]["source_files"][0]
    source_bytes = (
        b"Identifier,Start1\n"
        b"Regular,04:45\n"
        b"Regular,05:45\n"
        b"Regular,06:45\n"
        b"Regular,07:45\n"
    )
    assert source_record == {
        "role": "vehicle_details",
        "file": "source.csv",
        "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "size_bytes": len(source_bytes),
    }
    assert "Regular,04:45" not in (artifact / MANIFEST_FILENAME).read_text()
    assert not (artifact / "source.csv").exists()


def test_freeze_is_byte_deterministic(tmp_path):
    inputs = tmp_path / "inputs"
    inst, candidate, provenance, source = _write_inputs(inputs)
    first = tmp_path / "first"
    second = tmp_path / "second"
    freeze_subset(
        candidate,
        provenance,
        first,
        source_files=[("vehicle_details", source)],
    )
    freeze_subset(
        candidate,
        provenance,
        second,
        source_files=[("vehicle_details", source)],
    )
    assert inst.hash() == load_frozen_subset(first).hash()
    for filename in (INSTANCE_FILENAME, MANIFEST_FILENAME):
        assert (first / filename).read_bytes() == (second / filename).read_bytes()


def test_freeze_refuses_to_replace_an_existing_destination(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    before = {
        path.name: path.read_bytes()
        for path in artifact.iterdir()
    }
    _inst, candidate, provenance, source = _write_inputs(tmp_path / "other-inputs")
    with pytest.raises(FrozenSubsetError, match="refusing existing"):
        freeze_subset(
            candidate,
            provenance,
            artifact,
            source_files={"vehicle_details": source},
        )
    assert {
        path.name: path.read_bytes()
        for path in artifact.iterdir()
    } == before


def test_freeze_requires_at_least_one_hashed_giro_source(tmp_path):
    _inst, candidate, provenance, _source = _write_inputs(tmp_path / "inputs")
    with pytest.raises(FrozenSubsetError, match="source file is required"):
        freeze_subset(candidate, provenance, tmp_path / "frozen")
    with pytest.raises(FrozenSubsetError, match="source file is required"):
        freeze_subset(
            candidate,
            provenance,
            tmp_path / "frozen",
            source_files=[],
        )


def test_loader_refuses_unmanifested_legacy_json(tmp_path):
    instance = synthetic_instance(seed=7, n_trips=4)
    path = tmp_path / "legacy.json"
    path.write_bytes(canonical_json_bytes(instance.canonical()))
    with pytest.raises(FrozenSubsetError, match="manifest is required"):
        load_frozen_subset(path)


def test_loader_refuses_instance_byte_tampering(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    instance_path = artifact / INSTANCE_FILENAME
    instance_path.write_bytes(instance_path.read_bytes() + b" ")
    with pytest.raises(FrozenSubsetError, match="size does not match"):
        load_frozen_subset(artifact)


def test_loader_refuses_noncanonical_bytes_even_if_manifest_is_rehashed(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    instance_path = artifact / INSTANCE_FILENAME
    value = json.loads(instance_path.read_text())
    noncanonical = json.dumps(value, sort_keys=True).encode()
    instance_path.write_bytes(noncanonical)

    def mutate(manifest):
        manifest["artifact"]["sha256"] = hashlib.sha256(noncanonical).hexdigest()
        manifest["artifact"]["size_bytes"] = len(noncanonical)

    _rewrite_manifest(artifact, mutate)
    with pytest.raises(FrozenSubsetError, match="not canonical JSON"):
        load_frozen_subset(artifact)


def test_loader_refuses_noncanonical_manifest_bytes(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    manifest_path = artifact / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    with pytest.raises(FrozenSubsetError, match="manifest bytes are not canonical"):
        load_frozen_subset(artifact)


def test_loader_refuses_unmanifested_artifact_entries(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    (artifact / "UNTRACKED.txt").write_text("not in manifest\n")
    with pytest.raises(FrozenSubsetError, match="directory entries"):
        load_frozen_subset(artifact)


def test_loader_refuses_manifest_model_tampering(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    _rewrite_manifest(
        artifact,
        lambda manifest: manifest["model"].__setitem__(
            "battery_kwh", manifest["model"]["battery_kwh"] + 1
        ),
    )
    with pytest.raises(FrozenSubsetError, match="model parameters"):
        load_frozen_subset(artifact)


def test_loader_refuses_manifest_selection_tampering(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    _rewrite_manifest(
        artifact,
        lambda manifest: manifest["selection"].__setitem__(
            "trip_count", manifest["selection"]["trip_count"] + 1
        ),
    )
    with pytest.raises(FrozenSubsetError, match="trip selection"):
        load_frozen_subset(artifact)


def test_loader_refuses_manifest_schema_and_unknown_fields(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    _rewrite_manifest(
        artifact,
        lambda manifest: manifest.__setitem__("schema", "future-schema"),
    )
    with pytest.raises(FrozenSubsetError, match="unsupported.*schema"):
        load_frozen_subset(artifact)

    # Restore by making a second artifact, then add an unrecognized field.
    _inst, second, _result = _freeze(tmp_path / "second-root")
    _rewrite_manifest(
        second, lambda manifest: manifest.__setitem__("unverified", True)
    )
    with pytest.raises(FrozenSubsetError, match="keys do not match"):
        load_frozen_subset(second)


def test_loader_refuses_wrong_or_malformed_manifest_pin(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    with pytest.raises(FrozenSubsetError, match="manifest SHA-256 mismatch"):
        load_frozen_subset(
            artifact, expected_manifest_sha256="0" * 64
        )
    with pytest.raises(FrozenSubsetError, match="64-character"):
        load_frozen_subset(artifact, expected_manifest_sha256="deadbeef")


def test_loader_refuses_duplicate_json_keys(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    manifest_path = artifact / MANIFEST_FILENAME
    original_body = manifest_path.read_text().strip()[1:]
    manifest_path.write_text(
        '{"schema":"one","schema":"two",' + original_body
    )
    with pytest.raises(FrozenSubsetError, match="duplicate JSON key"):
        load_frozen_subset(artifact)


def test_freeze_refuses_mismatched_deadhead_matrices(tmp_path):
    instance = synthetic_instance(seed=7, n_trips=4)
    candidate = instance.canonical()
    candidate["dh_min"] = candidate["dh_min"][:-1]
    root = tmp_path / "inputs"
    _inst, candidate_path, provenance, _source = _write_inputs(root)
    candidate_path.write_bytes(canonical_json_bytes(candidate))
    with pytest.raises(FrozenSubsetError, match="identical arcs"):
        freeze_subset(candidate_path, provenance, tmp_path / "frozen")


def test_freeze_refuses_incomplete_provenance_disclosure(tmp_path):
    _inst, candidate, provenance, _source = _write_inputs(tmp_path / "inputs")
    value = json.loads(provenance.read_text())
    del value["variant_choice"]
    provenance.write_bytes(canonical_json_bytes(value))
    with pytest.raises(FrozenSubsetError, match="provenance keys"):
        freeze_subset(candidate, provenance, tmp_path / "frozen")


@pytest.mark.parametrize("field", ["source_rows", "trip_ids"])
def test_freeze_binds_declared_trip_lineage_to_instance(tmp_path, field):
    _inst, candidate, provenance, source = _write_inputs(tmp_path / "inputs")
    value = json.loads(provenance.read_text())
    value["trip_selection"][field] = value["trip_selection"][field][:-1]
    provenance.write_bytes(canonical_json_bytes(value))
    with pytest.raises(
        FrozenSubsetError,
        match="source_rows count|trip_ids do not match",
    ):
        freeze_subset(
            candidate,
            provenance,
            tmp_path / "frozen",
            source_files={"vehicle_details": source},
        )


def test_freeze_binds_declared_physics_to_instance(tmp_path):
    _inst, candidate, provenance, source = _write_inputs(tmp_path / "inputs")
    value = json.loads(provenance.read_text())
    value["physics"]["instance_parameters"]["battery_kwh"] += 1
    provenance.write_bytes(canonical_json_bytes(value))
    with pytest.raises(FrozenSubsetError, match="physics do not match"):
        freeze_subset(
            candidate,
            provenance,
            tmp_path / "frozen",
            source_files={"vehicle_details": source},
        )


def test_cli_freezes_and_reports_hashes(tmp_path):
    _inst, candidate, provenance, source = _write_inputs(tmp_path / "inputs")
    output = tmp_path / "cli-frozen"
    script = Path(__file__).resolve().parents[1] / "experiments" / (
        "freeze_giro_subset.py"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(candidate),
            "--provenance",
            str(provenance),
            "--output",
            str(output),
            "--source",
            f"vehicle_details={source}",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    assert result["directory"] == str(output)
    assert result["instance_hash"] == load_frozen_subset(output).hash()


def test_loader_refuses_a_symlinked_artifact_path(tmp_path):
    _original, artifact, _result = _freeze(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(artifact, target_is_directory=True)
    with pytest.raises(FrozenSubsetError, match="must not be a symlink"):
        load_frozen_subset(alias)
