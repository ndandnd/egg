"""Phase-1 price fixed-point iteration with cycle detection (checkpointed).

The naive loop: post p^k -> solve the taker EVSP -> observe load L^k ->
recompute p^{k+1} = (1-alpha) p^k + alpha * market.price(L^k). alpha = 1 is
the undamped chicken-and-egg iteration (expected to cycle at kinks of the
value function); alpha < 1 is damped. Schedule hashes and load hashes are
logged every iteration so fixed points, two-cycles, and longer cycles are
distinguished from price-tolerance artifacts (handoff Section 8.2 warning:
"do not call price convergence schedule convergence").
"""
from __future__ import annotations

import os

import numpy as np

from . import checkpoint
from .instance import Instance
from .market import AffineMarket
from .records import append_jsonl, make_record
from .regimes import solve_taker


def taker_fixed_point(
    inst: Instance,
    market: AffineMarket,
    alpha: float = 1.0,
    max_iters: int = 40,
    tol_load_kwh: float = 1e-3,
    out_dir: str = "runs/loop",
    tag: str = "loop",
    experiment: str = "phase1",
    solver_kw: dict | None = None,
) -> dict:
    """Returns a summary dict; per-iteration records go to
    {out_dir}/{tag}.jsonl and the checkpoint to {out_dir}/{tag}.ckpt.json."""
    solver_kw = solver_kw or {}
    os.makedirs(out_dir, exist_ok=True)
    rec_path = os.path.join(out_dir, f"{tag}.jsonl")
    ckpt_path = os.path.join(out_dir, f"{tag}.ckpt.json")

    state = checkpoint.load(
        ckpt_path,
        default={
            "iter": 0,
            "prices": [float(x) for x in market.price(np.zeros(market.n_slots))],
            "history": [],  # [(schedule_hash, load_hash)]
            "loads": [],
            "done": False,
            "outcome": None,
        },
    )
    if state["done"]:
        return state

    while state["iter"] < max_iters:
        k = state["iter"]
        p = np.asarray(state["prices"], dtype=float)
        sol = solve_taker(inst, p, **solver_kw)
        L = np.asarray(sol.load, dtype=float)
        sh, lh = sol.schedule_hash(), sol.load_hash()

        outcome = None
        # fixed point: load reproduces itself (within tolerance)
        if state["loads"]:
            prev_L = np.asarray(state["loads"][-1], dtype=float)
            if np.max(np.abs(L - prev_L)) <= tol_load_kwh:
                outcome = {"type": "fixed_point", "iter": k}
        # cycle: exact (schedule, load) pair seen before
        key = [sh, lh]
        if outcome is None and key in state["history"]:
            first = state["history"].index(key)
            outcome = {"type": "cycle", "first_seen": first, "length": k - first}

        rec = make_record(
            experiment,
            inst,
            sol,
            market=market,
            prices=p,
            regime="taker-iteration",
            extra={
                "tag": tag,
                "iter": k,
                "alpha": alpha,
                "outcome": outcome,
            },
        )
        append_jsonl(rec_path, rec)

        state["history"].append(key)
        state["loads"].append([float(x) for x in L])
        p_next = (1.0 - alpha) * p + alpha * market.price(L)
        state["prices"] = [float(x) for x in p_next]
        state["iter"] = k + 1
        if outcome is not None:
            state["done"] = True
            state["outcome"] = outcome
            checkpoint.save(ckpt_path, state)
            return state
        checkpoint.save(ckpt_path, state)

    state["done"] = True
    state["outcome"] = {"type": "max_iters", "iter": state["iter"]}
    checkpoint.save(ckpt_path, state)
    return state
