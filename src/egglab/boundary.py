"""Phase-2 switch-boundary mapping (checkpointed sweeps).

Perturb the price of one slot (or a direction) over a grid, re-solve the
taker EVSP at each point, and record where the optimal schedule switches:
schedule hash, load, fleet size, objective, and margin data. This produces
the switch statistic that adjudicates whether duty-level learning (B31) is
worthwhile (handoff Section 8.3).
"""
from __future__ import annotations

import os

import numpy as np

from . import checkpoint
from .instance import Instance
from .market import AffineMarket
from .records import append_jsonl, make_record
from .regimes import solve_taker


def sweep_slot(
    inst: Instance,
    base_prices,
    slot: int,
    deltas,
    out_dir: str = "runs/sweep",
    tag: str = "sweep",
    experiment: str = "phase2",
    solver_kw: dict | None = None,
) -> dict:
    """1-D sweep: p' = base_prices + delta * e_slot for each delta in deltas.
    Resumable at grid-point granularity."""
    solver_kw = solver_kw or {}
    os.makedirs(out_dir, exist_ok=True)
    rec_path = os.path.join(out_dir, f"{tag}.jsonl")
    ckpt_path = os.path.join(out_dir, f"{tag}.ckpt.json")
    base = np.asarray(base_prices, dtype=float)
    deltas = list(map(float, deltas))

    state = checkpoint.load(
        ckpt_path, default={"next_idx": 0, "points": [], "done": False}
    )
    if state["done"]:
        return state

    for idx in range(state["next_idx"], len(deltas)):
        d = deltas[idx]
        p = base.copy()
        p[slot] += d
        sol = solve_taker(inst, p, **solver_kw)
        point = {
            "idx": idx,
            "delta": d,
            "schedule_hash": sol.schedule_hash(),
            "load_hash": sol.load_hash(),
            "obj": sol.obj_model,
            "fleet": sol.fleet,
            "load_slot": sol.load[slot],
            "load": sol.load,
            "energy_total": sol.energy_charged_kwh,
        }
        rec = make_record(
            experiment,
            inst,
            sol,
            prices=p,
            regime="taker-sweep",
            extra={"tag": tag, "sweep_slot": slot, "delta": d, "idx": idx},
        )
        append_jsonl(rec_path, rec)
        state["points"].append(point)
        state["next_idx"] = idx + 1
        checkpoint.save(ckpt_path, state)

    # switch detection: consecutive grid points with different schedule or
    # load. Tie-flips (hash changes with no load/objective movement) are
    # solver-arbitrary alternative optima, not economic switches — flag them.
    switches = []
    pts = state["points"]
    for a, b in zip(pts, pts[1:]):
        if a["schedule_hash"] != b["schedule_hash"] or a["load_hash"] != b["load_hash"]:
            la = np.asarray(a["load"], dtype=float)
            lb = np.asarray(b["load"], dtype=float)
            load_l1 = float(np.abs(la - lb).sum())
            switches.append(
                {
                    "between_deltas": [a["delta"], b["delta"]],
                    "load_jump_slot": b["load_slot"] - a["load_slot"],
                    "load_l1": load_l1,
                    "fleet_change": b["fleet"] - a["fleet"],
                    "schedule_changed": a["schedule_hash"] != b["schedule_hash"],
                    "tie_flip": load_l1 < 1e-6 and a["fleet"] == b["fleet"],
                }
            )
    state["switches"] = switches
    state["n_switches"] = len(switches)
    state["n_economic_switches"] = sum(1 for s in switches if not s["tie_flip"])
    state["done"] = True
    checkpoint.save(ckpt_path, state)
    return state
