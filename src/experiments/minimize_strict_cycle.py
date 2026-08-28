#!/usr/bin/env python3
"""Build or check the canonical bounded strict-two-cycle witness."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.cycle_minimizer import (  # noqa: E402
    DEFAULT_MAX_ORACLE_EVALUATIONS,
    DEFAULT_MAX_WALL_SECONDS,
    build_witness,
    canonical_witness_bytes,
    minimize_fixture,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVENANCE_FILES = (
    "src/requirements.txt",
    "src/egglab/instance.py",
    "src/egglab/market.py",
    "src/egglab/solver.py",
    "src/egglab/evsp.py",
    "src/egglab/regimes.py",
    "src/egglab/b2a2.py",
    "src/egglab/cycle_minimizer.py",
    "src/egglab/enumerate_tiny.py",
    "src/experiments/minimize_strict_cycle.py",
    "src/tests/test_cycle_minimizer.py",
    "doc/STRICT_TWO_CYCLE_WITNESS.md",
)


def generate(max_oracle_evaluations: int, max_wall_seconds: float) -> bytes:
    reduction = minimize_fixture(
        max_oracle_evaluations=max_oracle_evaluations,
        max_wall_seconds=max_wall_seconds,
    )
    return canonical_witness_bytes(build_witness(reduction))


def verify_analysis_code_commit(claimed: str) -> str:
    if (
        len(claimed) != 40
        or any(character not in "0123456789abcdef" for character in claimed)
    ):
        raise RuntimeError(
            "analysis-code-commit must be a full lowercase 40-character SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"analysis code commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise RuntimeError(
            f"analysis code commit {claimed} resolves to {resolved}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            f"analysis code commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *PROVENANCE_FILES],
        cwd=REPO_ROOT,
    ).decode().strip()
    if dirty:
        raise RuntimeError(
            "analysis provenance files are dirty; commit code before publishing")
    for path in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{path}"],
            cwd=REPO_ROOT,
        )
        if committed != (REPO_ROOT / path).read_bytes():
            raise RuntimeError(
                f"{path} differs from analysis code commit {claimed}")
    return claimed


def artifact_payloads(
    witness_payload: bytes,
    analysis_code_commit: str,
) -> dict[str, bytes]:
    witness = json.loads(witness_payload)
    witness_sha = hashlib.sha256(witness_payload).hexdigest()
    manifest = {
        "schema": "egglab.strict-two-cycle-artifact.v1",
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": True,
        "generator": "src/experiments/minimize_strict_cycle.py",
        "outputs": {
            "WITNESS.json": {
                "bytes": len(witness_payload),
                "sha256": witness_sha,
            },
        },
    }
    comparison = witness[
        "computational_evidence"]["convex_hull_dictator_comparison"]
    strict = witness["computational_evidence"]["strict_best_response"]
    replay = witness["independent_replay"]
    summary = "\n".join([
        "# Strict two-cycle witness",
        "",
        f"- analysis_code_commit: `{analysis_code_commit}`",
        f"- witness_sha256: `{witness_sha}`",
        f"- trips: {witness['computational_evidence']['irreducibility']['n_trips']}",
        f"- structures: {replay['n_structures']}",
        (
            "- minimum certified structure margin: "
            f"{strict['minimum_global_discrete_structure_margin']}"
        ),
        (
            "- selected-load uniqueness bound (kWh): "
            f"{strict['maximum_certified_load_range_upper_kwh']}"
        ),
        (
            "- convex-hull uplift interval: "
            f"{comparison['uplift_interval']}"
        ),
        "- independent replay: pass",
        "",
        (
            "Computational evidence is scoped to the serialized synthetic "
            "instance. The fixed-point implication remains a separately "
            "identified algebraic lemma."
        ),
        "",
    ]).encode()
    manifest["outputs"]["SUMMARY.md"] = {
        "bytes": len(summary),
        "sha256": hashlib.sha256(summary).hexdigest(),
    }
    canonical_manifest = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {
        "WITNESS.json": witness_payload,
        "MANIFEST.json": canonical_manifest,
        "SUMMARY.md": summary,
    }


def _atomic_write(path: Path, payload: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically minimize the closed synthetic strict-cycle "
            "fixture; no seed/grid expansion is performed"))
    parser.add_argument("--out", required=True, help="witness JSON path")
    parser.add_argument(
        "--analysis-code-commit",
        required=True,
        help="full SHA of the committed code used to generate the artifact",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="regenerate and require byte identity without writing")
    parser.add_argument(
        "--max-oracle-evaluations", type=int,
        default=DEFAULT_MAX_ORACLE_EVALUATIONS)
    parser.add_argument(
        "--max-wall-seconds", type=float,
        default=DEFAULT_MAX_WALL_SECONDS)
    args = parser.parse_args(argv)

    analysis_code_commit = verify_analysis_code_commit(
        args.analysis_code_commit)
    path = Path(args.out)
    witness_payload = generate(
        args.max_oracle_evaluations, args.max_wall_seconds)
    payloads = artifact_payloads(witness_payload, analysis_code_commit)
    if args.check:
        for filename, payload in payloads.items():
            target = path if filename == "WITNESS.json" else path.parent / filename
            if not target.is_file():
                parser.error(f"--check target does not exist: {target}")
            if target.read_bytes() != payload:
                parser.error(
                    f"canonical artifact differs from regenerated output: {target}")
        return
    for filename, payload in payloads.items():
        target = path if filename == "WITNESS.json" else path.parent / filename
        _atomic_write(target, payload)


if __name__ == "__main__":
    main()
