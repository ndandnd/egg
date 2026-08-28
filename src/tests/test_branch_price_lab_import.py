"""Always-run checks for CBC-only installs of the optional exactness lab."""
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import egglab.branch_price_lab as branch_price_lab


SRC = Path(__file__).resolve().parents[1]


def test_repository_requirements_do_not_install_gurobi():
    requirements = (SRC / "requirements.txt").read_text().splitlines()
    assert not any(line.strip().startswith("gurobipy") for line in requirements)


def test_lab_imports_and_fails_locally_without_gurobi():
    code = """
import sys
sys.modules["gurobipy"] = None
import egglab.branch_price_lab as lab
assert not lab.gurobi_available()
assert not lab.gurobi_runtime_available()
assert lab.structural_arc("out", None, "trip")["kind"] == "out"
try:
    lab._new_model("must-not-start")
except lab.ExactnessLabError as exc:
    assert "optional 'gurobipy'" in str(exc)
else:
    raise AssertionError("missing optional dependency did not fail locally")
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=SRC,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_gurobi_suites_skip_under_simulated_cbc_only_install(tmp_path):
    # sitecustomize runs before pytest imports either Gurobi-only module.
    (tmp_path / "sitecustomize.py").write_text(
        'import sys\nsys.modules["gurobipy"] = None\n'
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path), str(SRC), environment.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_branch_price_lab.py",
            "tests/test_branch_price_lab_parity.py",
        ],
        cwd=SRC,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "skipped" in completed.stdout


def test_current_process_import_does_not_initialize_a_model():
    # Importability is independent of package/license availability.  Runtime
    # probing is reserved for the explicitly skipped Gurobi-only modules.
    assert branch_price_lab.SCHEMA_VERSION.startswith("tiny-branch-price-")
