"""E4 step 3: score saved E4 models on held-out `day` labels of their OUTER groups.

Usage: python -m experiments.claude_e4_eval --runs DIR --labels DIR --output FILE
(graph environment). DIR holds <arm>-f<fold>/ folders written by claude_e4_train.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from egglab import physical_route_graph_v6 as graph
from experiments.claude_e4_train import evaluate, label_samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    graph.configure_cpu()
    day, missing = label_samples(args.labels, "evaluation_only")
    out = {"day_label_missing": missing, "runs": {}}
    for folder in sorted(p for p in args.runs.iterdir() if (p / "result.json").is_file()):
        res = json.loads((folder / "result.json").read_text())
        model = graph.restore_model(folder / "model.npz")
        mean, scale = np.asarray(res["mean_fit_only"]), np.asarray(res["scale_fit_only"])
        outer = [s for s in day if s["group"] in set(res["outer_groups"])]
        metrics, p = evaluate(model, outer, mean, scale)
        per_group, cursor = {}, 0
        from egglab import physical_route_model_v2 as frozen
        for s in outer:
            n = len(s["y"]); per_group[s["group"]] = frozen._metrics(s["y"], p[cursor:cursor+n], np.ones(n)/n, [s]); cursor += n
        out["runs"][folder.name] = {"arm": res["arm"], "fold": res["fold"], "seed": res["seed"],
            "selected_epoch": res["candidate"]["selected_epoch"], "outer_day_metrics": metrics,
            "outer_source_metrics": res["outer_source_tariff_metrics"], "per_group_day": per_group}
        print(folder.name, json.dumps({k: metrics[k] for k in ("weighted_log_loss", "average_precision",
              "input_trip_count_topk_recall_mean_by_fleet")}), flush=True)
    args.output.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
