"""Regression battery for the B2 208-cell matched expansion driver:
exact grid identity, disjointness from the certified pilots, settings
parity, and an end-to-end tiny-cell smoke."""
import itertools
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from egglab import checkpoint
from egglab.instance import synthetic_instance
from experiments.analyze_b2_pilot import PILOT_INSTANCES
import experiments.run_b2_expansion as exp_mod
import experiments.run_b2a2_pilot as a2_mod
import experiments.run_b2a345_pilot as a345_mod
from experiments.run_b2_expansion import (
    BUDGET,
    EPSILON,
    TOL_D,
    build_cells,
    expansion_instances,
    run_cell,
)


def test_exactly_208_cells_52_per_method():
    cells = build_cells()
    assert len(cells) == 208
    for m in ("a2", "a3", "a4", "a5"):
        assert sum(1 for c in cells if c[0] == m) == 52
    assert len(set(cells)) == 208  # no duplicates


def test_grid_is_full_population_minus_pilot():
    full = set(itertools.product(range(16), (8, 12), (0.01, 0.05)))
    assert len(full) == 64
    pilot = set(PILOT_INSTANCES)
    assert len(pilot) == 12
    expansion = set(expansion_instances())
    assert len(expansion) == 52
    # disjoint from the certified pilots; union is the full preregistered
    # moderate/strong-feedback population
    assert expansion & pilot == set()
    assert expansion | pilot == full


def test_pilot_seeds_never_appear():
    for (m, s, n, b) in build_cells():
        assert s not in (0, 11, 15), (m, s, n, b)


def test_settings_identical_to_pilots():
    assert EPSILON == a2_mod.EPSILON == a345_mod.EPSILON == 1e-2
    assert BUDGET == a2_mod.BUDGET == a345_mod.BUDGET == 240
    assert TOL_D == a2_mod.TOL_D == a345_mod.TOL_D == 1e-2


def test_cell_dirs_unique():
    dirs = [f"{m}_s{s}_n{n}_b{b:g}" for (m, s, n, b) in build_cells()]
    assert len(set(dirs)) == 208


def test_run_cell_end_to_end_tiny(tmp_path, monkeypatch):
    """One real cell through the expansion driver (tiny instance injected):
    dictator stage + certified CG, method identity recorded, resumable."""
    tiny = synthetic_instance(seed=1, n_trips=4, max_vehicles=2)
    monkeypatch.setattr(exp_mod, "synthetic_instance", lambda **_kw: tiny)
    args = types.SimpleNamespace(out=str(tmp_path), mip_gap=1e-6)
    cell = build_cells()[60]  # an a3 cell
    assert cell[0] == "a3"
    run_cell(cell, args)
    tag_dir = f"a3_s{cell[1]}_n{cell[2]}_b{cell[3]:g}"
    ck = checkpoint.load(os.path.join(str(tmp_path), tag_dir,
                                      "a3.cg.ckpt.json"))
    assert ck["done"] and ck["outcome"]["type"] in ("certified",
                                                    "budget_exhausted")
    assert ck["identity"]["method"] == "a3"
    assert ck["identity"]["budget"] == 240
    dck = checkpoint.load(os.path.join(str(tmp_path), tag_dir,
                                       "dictator.ckpt.json"))
    assert dck is not None and dck["z_d_ub"] == ck["identity"]["z_d_ub"]
    # rerun resumes (identity accepted, no duplicate work)
    run_cell(cell, args)
    ck2 = checkpoint.load(os.path.join(str(tmp_path), tag_dir,
                                       "a3.cg.ckpt.json"))
    assert ck2["oracle_calls"] == ck["oracle_calls"]


def test_list_output_order_is_deterministic(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--list"])
    exp_mod.main()
    out1 = capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["prog", "--list"])
    exp_mod.main()
    out2 = capsys.readouterr().out
    assert out1 == out2
    assert out1.strip().endswith("total: 208 cells")
