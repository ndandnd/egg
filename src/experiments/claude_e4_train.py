"""E4 step 2: does tariff-diverse labelling make edge scores price-responsive?

Trains the v6/v8 graph-attention scorer (same architecture, optimizer, batching and
grouped TRAIN folds; v8 budget of up to 900 epochs, patience 30) on one of two label
sets, then evaluates on the held-out `day` tariff, which no training label uses:

* ``bank2``  - the frozen exact128 pool: two source incumbents per timetable
               (`source0` flat, `source1` cheap 18-22), i.e. the v8 data;
* ``multi8`` - the same pool plus six E4 cold incumbents per timetable under
               deterministic training tariffs (no >= 2 cheap hours inside 10-14).

Evaluation (OUTER groups of the fold only): edge ranking against the E4 `day_eval`
cold incumbents, and saved day-tariff logits for every OUTER group, for the physical
decode/charge comparison. Preprocessing uses FIT only; checkpoint selection uses
INNER only (INNER loss on the arm's own label set). Run with the graph environment.

Usage: python -m experiments.claude_e4_train --arm multi8 --fold 0 --seed 17 \
           --pool DIR --labels DIR --output DIR
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
import torch

from egglab import learned_proposals as edge
from egglab import physical_learning_cases as bank
from egglab import physical_route_graph_v6 as graph
from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous

ARMS = ("bank2", "multi8")


def label_samples(labels_dir, role):
    """Build graph samples from E4 labels.jsonl files (TRAIN groups only)."""
    samples, missing = [], []
    for group_id in bank.TRAIN_IDS:
        path = Path(labels_dir) / f"g{group_id}" / "labels.jsonl"
        if not path.is_file():
            missing.append((group_id, "no_file")); continue
        case = bank.make_case(group_id)
        topo = graph.topology(case)
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["role"] != role:
                continue
            if row.get("case_identity") != case.identity():
                raise ValueError("E4 label case identity differs from generator")
            if not row.get("plan"):
                missing.append((group_id, row["tariff_name"])); continue
            ids = {m for v in row["plan"]["vehicles"] for m in v["movements"]}
            y = np.asarray([float(m.id in ids) for m in case.movements])
            samples.append({"x": edge.edge_features(case, row["tariff"]["a"]), "y": y,
                            "group": f"physical_v2_s{group_id}", "source": "e4_" + row["tariff_name"],
                            "trip_count": len(case.trips), "graph": topo,
                            "movement_ids": [m.id for m in case.movements]})
    return samples, missing


def evaluate(model, samples, mean, scale):
    if not samples:
        return None
    batches = graph.batches(samples, mean, scale, labelled=False)
    p = graph.predict(model, batches)
    per_group, cursor = [], 0
    for s in samples:
        n = len(s["y"])
        per_group.append(frozen._metrics(s["y"], p[cursor:cursor+n], np.ones(n)/n, [s])); cursor += n
    return previous._macro_metrics(per_group), p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--pool", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-epochs", type=int, default=900)
    ap.add_argument("--candidate-seconds", type=float, default=4*3600.)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    graph.configure_cpu()
    graph.MAX_EPOCHS, graph.CANDIDATE_SECONDS = args.max_epochs, args.candidate_seconds
    data = graph.load_pool(args.pool, expected_manifest_sha256=graph.POOL_SHA)
    pool_samples = data["samples"]
    train_samples = list(pool_samples)
    e4_missing = []
    if args.arm == "multi8":
        extra, e4_missing = label_samples(args.labels, "training")
        train_samples += extra
    day_samples, day_missing = label_samples(args.labels, "evaluation_only")
    fit_groups, inner_groups, outer_groups = previous.grouped_split(data["groups"], args.fold)
    fit = [s for s in train_samples if s["group"] in fit_groups]
    inner = [s for s in train_samples if s["group"] in inner_groups]
    fit_x, _, _ = previous._stack(fit)
    mean, scale = frozen._preprocess(fit_x)
    fit_batches = graph.batches(fit, mean, scale, labelled=True)
    inner_batches = graph.batches(inner, mean, scale, labelled=True)
    model, row = graph.fit_candidate("graph_attention", fit_batches, inner_batches, args.seed)
    curves = row.pop("train_curves")
    graph.save_model(model, args.output / "model.npz")
    outer_day = [s for s in day_samples if s["group"] in outer_groups]
    outer_pool = [s for s in pool_samples if s["group"] in outer_groups]
    day_metrics, day_p = evaluate(model, outer_day, mean, scale) or (None, None)
    pool_metrics, _ = evaluate(model, outer_pool, mean, scale) or (None, None)
    # Day-tariff logits for every OUTER group (physical decode evaluation).
    logits = {}
    for gname in outer_groups:
        gid = int(gname.removeprefix("physical_v2_s"))
        case = bank.make_case(gid)
        sample = {"x": edge.edge_features(case, bank.market(case, "day").a), "graph": graph.topology(case),
                  "group": gname, "source": "day_scoring", "trip_count": len(case.trips)}
        with torch.no_grad():
            z = model(graph.batches([sample], mean, scale, labelled=False)[0]).numpy()
        logits[gid] = {"movement_ids": [m.id for m in case.movements], "logits": z.tolist()}
    result = {"arm": args.arm, "fold": args.fold, "seed": args.seed,
              "fit_groups": fit_groups, "inner_groups": inner_groups, "outer_groups": outer_groups,
              "train_samples": {"fit": len(fit), "inner": len(inner)}, "e4_missing": e4_missing,
              "day_eval_missing": day_missing, "candidate": row,
              "outer_day_heldout_tariff_metrics": day_metrics,
              "outer_source_tariff_metrics": pool_metrics,
              "mean_fit_only": mean.tolist(), "scale_fit_only": scale.tolist(),
              "wall_seconds": time.monotonic()-started}
    (args.output / "result.json").write_text(json.dumps(result, indent=1, default=str))
    (args.output / "curves.json").write_text(json.dumps(curves))
    (args.output / "day_logits.json").write_text(json.dumps(logits))
    print(json.dumps({"arm": args.arm, "fold": args.fold, "selected_epoch": row["selected_epoch"],
                      "completed": row["completed_epochs"], "day": day_metrics}, default=str))


if __name__ == "__main__":
    main()
