"""Phase-1 price fixed-point iteration with STATE-CORRECT detection.

The naive loop: post p^k -> solve the taker EVSP -> observe load L^k ->
p^{k+1} = (1-alpha) p^k + alpha * market.price(L^k). The dynamical state is
the price vector p^k (the load is a function of it), so:

- FIXED POINT requires p^{k+1} ~= p^k (price residual below tolerance) —
  NOT merely a repeated load: under damping, loads can repeat while prices
  are still converging inside one response region.
- CYCLE requires the price state to recur: ||p^k - p^j||_inf <= tol for some
  j <= k-2. Repeated (schedule, load) responses at different prices are NOT
  called cycles; they are recorded separately as response recurrences.
  (Note: for alpha = 1, p^{k+1} depends only on L^k, so a repeated response
  does imply a genuine cycle; the state test subsumes that case.)

Every iteration records price residual, load residual, schedule recurrence,
and response recurrence separately (reviewer-specified hardening), and the
full price history is checkpointed.
"""
from __future__ import annotations

import os

import numpy as np

from . import checkpoint
from .instance import Instance
from .market import AffineMarket
from .records import append_jsonl, make_record
from .regimes import solve_taker


def detect_outcome(
    price_history: list,
    p_curr,
    p_next,
    tol_price: float,
) -> dict | None:
    """Pure state-based detection (unit-tested). price_history contains the
    prior states p^0..p^{k-1}; p_curr is p^k; p_next is p^{k+1}.

    Returns {'type': 'fixed_point'} if p_next ~= p_curr;
            {'type': 'cycle', 'first_seen': j, 'length': k-j} if p_curr
            recurs a state j <= k-2; else None."""
    p_curr = np.asarray(p_curr, dtype=float)
    p_next = np.asarray(p_next, dtype=float)
    if float(np.max(np.abs(p_next - p_curr))) <= tol_price:
        return {"type": "fixed_point"}
    k = len(price_history)
    for j in range(k - 1):  # j <= k-2: excludes the immediate predecessor
        pj = np.asarray(price_history[j], dtype=float)
        if float(np.max(np.abs(p_curr - pj))) <= tol_price:
            return {"type": "cycle", "first_seen": j, "length": k - j}
    return None


def taker_fixed_point(
    inst: Instance,
    market: AffineMarket,
    alpha: float = 1.0,
    max_iters: int = 40,
    tol_price: float = 1e-4,
    out_dir: str = "runs/loop",
    tag: str = "loop",
    experiment: str = "phase1",
    solver_kw: dict | None = None,
    extra_params: dict | None = None,
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
            "price_history": [],  # full state history p^0..p^{k-1}
            "responses": [],  # (schedule_hash, load_hash) per iteration
            "loads": [],
            "tol_price": tol_price,
            "alpha": alpha,
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
        p_next = (1.0 - alpha) * p + alpha * market.price(L)

        price_residual = float(np.max(np.abs(p_next - p)))
        load_residual = (
            float(np.max(np.abs(L - np.asarray(state["loads"][-1], dtype=float))))
            if state["loads"]
            else None
        )
        schedule_recurred = any(r[0] == sh for r in state["responses"])
        response_recurred = [sh, lh] in state["responses"]
        outcome = detect_outcome(state["price_history"], p, p_next, tol_price)
        if outcome is not None:
            outcome["iter"] = k

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
                "tol_price": tol_price,
                "price_residual": price_residual,
                "load_residual": load_residual,
                "schedule_recurred": schedule_recurred,
                "response_recurred": response_recurred,
                "outcome": outcome,
                **(extra_params or {}),
            },
        )
        # FAIL FAST (measurement-closeout rule): a replay-invalid iteration
        # must never be appended to the record stream and must never advance
        # the scientific checkpoint. Raising here leaves state["iter"] == k
        # and the checkpoint file untouched, so a rerun retries this exact
        # iteration. (The pre-2026-08-16 code appended and advanced anyway,
        # which is how the 18+163 legacy replay_ok=false records were born.)
        if rec["replay_ok"] is False:
            raise RuntimeError(
                f"replay validation failed at iter {k} of '{tag}' "
                f"(record NOT appended, checkpoint NOT advanced; "
                f"state remains at iter {k}): {rec['replay_violations']}"
            )
        append_jsonl(rec_path, rec)

        state["price_history"].append([float(x) for x in p])
        state["responses"].append([sh, lh])
        state["loads"].append([float(x) for x in L])
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
