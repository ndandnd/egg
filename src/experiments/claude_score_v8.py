"""Score movements of bank or scaled cases with a saved v8 graph-attention model.

For a bank TRAIN group the model is the seed-17 task of the fold in which the group is
OUTER (never fitted or selected on it). Scaled `claude-scale-v1` cases are outside the
bank, so any fold's model is held out; fold 0 / seed 17 (task 0) is used.
Run with the graph environment. Writes {case_key: {movement_ids, logits, seconds}}.

Usage: python -m experiments.claude_score_v8 --v8-root DIR --tariff day \
           --case bank:10069 --case scale:50000:40 ... --output FILE
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
import torch

from egglab import claude_cases
from egglab import claude_scale_cases as scale
from egglab import learned_proposals as edge
from egglab import physical_learning_cases as bank
from egglab import physical_route_graph_v6 as graph
from egglab import physical_route_model_v3 as previous


def task_for(case_key, groups):
    kind, *rest = case_key.split(":")
    if kind in ("scale", "public"):
        return 0  # outside the TRAIN bank: every fold's model is held out
    gname = f"physical_v2_s{int(rest[0])}"
    for fold in range(previous.FOLDS):
        if gname in previous.grouped_split(groups, fold)[2]:
            return fold*3  # seed 17 is the first seed of each fold
    raise ValueError("group not in any OUTER fold")




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v8-root", type=Path, required=True)
    ap.add_argument("--tariff", default="day")
    ap.add_argument("--case", action="append", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    graph.configure_cpu()
    groups = [f"physical_v2_s{i}" for i in range(10000, 10128)]
    out, cache = {}, {}
    for key in args.case:
        t0 = time.monotonic()
        task = task_for(key, groups)
        if task not in cache:
            folder = args.v8_root / f"task{task:02d}" / "inner_progress"
            pre = json.loads((folder / "fit_only_preprocessing_and_groups.json").read_text())
            cache[task] = (graph.restore_model(folder / "graph_attention_selected.npz"),
                           np.asarray(pre["mean_fit_only"]), np.asarray(pre["scale_fit_only"]))
        model, mean, sc = cache[task]
        case = claude_cases.make(key)
        prices = bank.market(case, args.tariff).a
        sample = {"x": edge.edge_features(case, prices), "graph": graph.topology(case),
                  "group": key, "source": "scoring", "trip_count": len(case.trips)}
        with torch.no_grad():
            z = model(graph.batches([sample], mean, sc, labelled=False)[0]).numpy()
        out[key] = {"case_identity": case.identity(), "v8_task": task, "tariff": args.tariff,
                    "movement_ids": [m.id for m in case.movements], "logits": z.tolist(),
                    "score_seconds": time.monotonic()-t0}
        print(key, task, len(z), round(out[key]["score_seconds"], 2), flush=True)
    args.output.write_text(json.dumps(out))


if __name__ == "__main__":
    main()
