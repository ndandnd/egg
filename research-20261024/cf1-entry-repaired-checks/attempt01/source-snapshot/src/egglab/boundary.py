"""Phase-2 switch-boundary mapping (checkpointed sweeps) — hardened.

Perturb the price of one slot over a grid, re-solve the taker EVSP at each
point, and classify response changes between adjacent grid points:

- degenerate_tie : hash flip with no material load change (alternative optima)
- charging_only  : material load change, same trip partition
- duty_change    : trip partition changes (with material load change)
- fleet_change   : fleet size changes

For duty/fleet changes an explicit MARGIN TEST separates genuine strict
preference changes from alternative optima: re-realize schedule B's trip
partition at point A's prices (fixed-sequence oracle) and vice versa; if the
cross cost differences are ~0 the two schedules are economically tied at the
boundary (tie_margin=True), not a real switch.
"""
from __future__ import annotations

import os

import numpy as np

from . import checkpoint
from .evsp import solve_fixed_sequences
from .instance import Instance
from .records import append_jsonl, make_record
from .regimes import solve_taker

LOAD_TOL_KWH = 1.0  # material-load-change threshold (reviewer-specified)
MARGIN_TOL = 1e-3  # economic-tie tolerance on cross-realization cost


def classify_pair(a: dict, b: dict, load_tol: float = LOAD_TOL_KWH) -> dict | None:
    """Classify the change between two adjacent sweep points (dicts holding
    schedule_hash, load_hash, load, fleet, obj). Returns None if identical."""
    if a["schedule_hash"] == b["schedule_hash"] and a["load_hash"] == b["load_hash"]:
        return None
    la = np.asarray(a["load"], dtype=float)
    lb = np.asarray(b["load"], dtype=float)
    load_l1 = float(np.abs(la - lb).sum())
    if b["fleet"] != a["fleet"]:
        kind = "fleet_change"
    elif load_l1 <= load_tol:
        kind = "degenerate_tie"
    elif a["schedule_hash"] != b["schedule_hash"]:
        kind = "duty_change"
    else:
        kind = "charging_only"
    return {
        "between_deltas": [a["delta"], b["delta"]],
        "kind": kind,
        "load_l1": load_l1,
        "load_jump_slot": b.get("load_slot", 0.0) - a.get("load_slot", 0.0),
        "fleet_change": b["fleet"] - a["fleet"],
        "schedule_changed": a["schedule_hash"] != b["schedule_hash"],
    }


def margin_test(inst: Instance, a: dict, b: dict, prices_at, solver_kw: dict) -> dict:
    """Cross-realization margins: cost of B's partition at A's prices minus
    A's optimum (and vice versa). Margins ~0 => economically tied schedules
    (alternative optima at the boundary)."""
    pa = prices_at(a["delta"])
    pb = prices_at(b["delta"])
    sol_b_at_a = solve_fixed_sequences(inst, b["sequences"], ("linear", pa), **solver_kw)
    sol_a_at_b = solve_fixed_sequences(inst, a["sequences"], ("linear", pb), **solver_kw)
    m_ab = None if sol_b_at_a is None else sol_b_at_a.obj_model - a["obj"]
    m_ba = None if sol_a_at_b is None else sol_a_at_b.obj_model - b["obj"]
    margins = [m for m in (m_ab, m_ba) if m is not None]
    return {
        "margin_b_at_a": m_ab,
        "margin_a_at_b": m_ba,
        "tie_margin": bool(margins and min(margins) <= MARGIN_TOL),
    }


def sweep_slot(
    inst: Instance,
    base_prices,
    slot: int,
    deltas,
    out_dir: str = "runs/sweep",
    tag: str = "sweep",
    experiment: str = "phase2",
    solver_kw: dict | None = None,
    extra_params: dict | None = None,
    run_margin_tests: bool = True,
) -> dict:
    """1-D sweep: p' = base_prices + delta * e_slot. Resumable at grid-point
    granularity; margin tests run in a second (also resumable) pass."""
    solver_kw = solver_kw or {}
    os.makedirs(out_dir, exist_ok=True)
    rec_path = os.path.join(out_dir, f"{tag}.jsonl")
    ckpt_path = os.path.join(out_dir, f"{tag}.ckpt.json")
    base = np.asarray(base_prices, dtype=float)
    deltas = list(map(float, deltas))

    def prices_at(d: float) -> np.ndarray:
        p = base.copy()
        p[slot] += d
        return p

    state = checkpoint.load(
        ckpt_path,
        default={"next_idx": 0, "points": [], "done": False, "margins_done": False},
    )
    if state["done"]:
        return state

    for idx in range(state["next_idx"], len(deltas)):
        d = deltas[idx]
        p = prices_at(d)
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
            "sequences": sol.sequences,
            "energy_total": sol.energy_charged_kwh,
        }
        rec = make_record(
            experiment,
            inst,
            sol,
            prices=p,
            regime="taker-sweep",
            extra={
                "tag": tag,
                "sweep_slot": slot,
                "delta": d,
                "idx": idx,
                **(extra_params or {}),
            },
        )
        if rec["replay_ok"] is False:
            raise RuntimeError(f"replay validation failed at delta={d}: {rec['replay_violations']}")
        append_jsonl(rec_path, rec)
        state["points"].append(point)
        state["next_idx"] = idx + 1
        checkpoint.save(ckpt_path, state)

    # classification + margin tests (resumable second pass)
    if not state.get("margins_done"):
        switches = []
        pts = state["points"]
        for a, b in zip(pts, pts[1:]):
            sw = classify_pair(a, b)
            if sw is None:
                continue
            if (
                run_margin_tests
                and sw["kind"] in ("duty_change", "fleet_change")
                and "sequences" in a
                and "sequences" in b  # absent in pre-hardening checkpoints
            ):
                sw.update(margin_test(inst, a, b, prices_at, solver_kw))
            switches.append(sw)
        state["switches"] = switches
        state["n_switches"] = len(switches)
        state["n_economic_switches"] = sum(
            1
            for s in switches
            if s["kind"] in ("charging_only", "duty_change", "fleet_change")
            and not s.get("tie_margin", False)
        )
        state["counts_by_kind"] = {
            k: sum(1 for s in switches if s["kind"] == k)
            for k in ("degenerate_tie", "charging_only", "duty_change", "fleet_change")
        }
        state["margins_done"] = True
    state["done"] = True
    checkpoint.save(ckpt_path, state)
    return state
