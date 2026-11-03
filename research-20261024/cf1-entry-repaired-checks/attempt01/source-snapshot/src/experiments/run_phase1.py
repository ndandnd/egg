#!/usr/bin/env python3
"""Phase 1: regime comparison + taker fixed-point loops on synthetic instances.

Each cell = (seed, n_trips, price shape, b_scale, alpha). Per cell:
  1. solve the four regimes (uncontrolled / taker @ posted / strategic /
     dictator) and record the welfare ladder;
  2. run the taker fixed-point iteration (damped by alpha) with cycle
     detection.
All work is checkpointed per cell; rerunning the same command (e.g. after
Slurm preemption/requeue) resumes automatically.

Usage:
  python experiments/run_phase1.py --list
  python experiments/run_phase1.py --cell 7 --out runs/phase1
  python experiments/run_phase1.py --all  --out runs/phase1
  (Slurm array: --cell $SLURM_ARRAY_TASK_ID)
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from egglab import checkpoint
from egglab.instance import synthetic_instance
from egglab.loops import taker_fixed_point
from egglab.market import make_affine_market
from egglab.records import append_jsonl, make_record
from egglab.regimes import (
    evaluate,
    solve_dictator,
    solve_strategic,
    solve_taker,
    solve_uncontrolled,
)


def build_cells(args):
    return list(
        itertools.product(args.seeds, args.n_trips, args.shapes, args.b_scales, args.alphas)
    )


def run_cell(cell, args):
    seed, n_trips, shape, b_scale, alpha = cell
    tag = f"s{seed}_n{n_trips}_{shape}_b{b_scale:g}_a{alpha:g}"
    out = os.path.join(args.out, tag)
    os.makedirs(out, exist_ok=True)
    ck_path = os.path.join(out, "cell.ckpt.json")
    state = checkpoint.load(ck_path, default={"static_done": [], "loop_done": False})

    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape=shape, b_scale=b_scale)
    posted = market.price(np.zeros(market.n_slots))
    rec_path = os.path.join(out, "static.jsonl")
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=args.time_limit)
    params = {
        "tag": tag,
        "cell": list(cell),
        "seed": seed,
        "shape": shape,
        "b_scale": b_scale,
        "alpha": alpha,
        "n_seg": args.n_seg,
        "pwl_tol": args.pwl_tol,
        "run_mode": "loop_only" if args.loop_only else (
            "static_only" if args.static_only else "full"
        ),
    }

    regimes = {
        "uncontrolled": lambda: solve_uncontrolled(inst, market, **kw),
        "taker": lambda: solve_taker(inst, posted, **kw),
        "strategic": lambda: solve_strategic(
            inst, market, n_seg=args.n_seg, tol_abs=args.pwl_tol, **kw
        ),
        "dictator": lambda: solve_dictator(
            inst, market, n_seg=args.n_seg, tol_abs=args.pwl_tol, **kw
        ),
    }
    if not args.loop_only:
        ladder = {}
        for name, fn in regimes.items():
            if name in state["static_done"]:
                continue
            sol = fn()
            rec = make_record(
                "phase1-static", inst, sol, market=market, prices=posted, regime=name,
                extra=params,
            )
            if rec["replay_ok"] is False:
                raise RuntimeError(
                    f"replay validation failed for {name} in {tag}: "
                    f"{rec['replay_violations']}"
                )
            append_jsonl(rec_path, rec)
            ladder[name] = evaluate(inst, sol, market)["total_system"]
            state["static_done"].append(name)
            checkpoint.save(ck_path, state)

    if not args.static_only and not state["loop_done"]:
        taker_fixed_point(
            inst,
            market,
            alpha=alpha,
            max_iters=args.max_iters,
            tol_price=args.tol_price,
            out_dir=out,
            tag="loop",
            experiment="phase1-loop",
            solver_kw=kw,
            extra_params={k: v for k, v in params.items() if k != "tag"},
        )
        state["loop_done"] = True
        checkpoint.save(ck_path, state)
    print(f"[done] cell {tag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--n-trips", dest="n_trips", type=int, nargs="+", default=[8, 12])
    ap.add_argument("--shapes", nargs="+", default=["duck"])
    ap.add_argument(
        "--b-scales", dest="b_scales", type=float, nargs="+",
        default=[0.0, 0.002, 0.01, 0.05],
    )
    ap.add_argument("--alphas", type=float, nargs="+", default=[1.0, 0.5, 0.25, 0.1])
    ap.add_argument("--n-seg", dest="n_seg", type=int, default=16)
    ap.add_argument("--pwl-tol", dest="pwl_tol", type=float, default=1e-2,
                    help="certified upper/lower gap for strategic/dictator")
    ap.add_argument("--tol-price", dest="tol_price", type=float, default=1e-4,
                    help="price-state tolerance for fixed-point/cycle detection")
    ap.add_argument("--max-iters", dest="max_iters", type=int, default=120,
                    help="damped runs converge ~1/alpha slower; budget generously")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=1e-6)
    ap.add_argument("--time-limit", dest="time_limit", type=float, default=None)
    ap.add_argument("--out", default="runs/phase1")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--loop-only", action="store_true",
        help="skip alpha-invariant static regimes and run only the price loop",
    )
    mode.add_argument(
        "--static-only", action="store_true",
        help="run the four static regimes and skip the price loop",
    )
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    cells = build_cells(args)
    if args.list:
        for k, c in enumerate(cells):
            print(k, c)
        print(f"total: {len(cells)} cells")
        return
    if args.cell is not None:
        run_cell(cells[args.cell], args)
    elif args.all:
        for c in cells:
            run_cell(c, args)
    else:
        ap.error("choose --list, --cell K, or --all")


if __name__ == "__main__":
    main()
