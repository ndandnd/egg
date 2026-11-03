# Prospective TRAIN physical proposal comparison v7

Design/code only until source, input freeze and review are complete. Frozen before any target solve: groups10064–10079 inclusive, all admitted source variants together, deterministic `day` target market, seed17 and the group's original outer fold `(base_id-10000)%4` (saved training task0/3/6/9). These16 TRAIN timetables extend the previous decoder pilot10036–10039; they remain inside the exact128 learning bank but outside each selected model's fit and inner partitions. No DEV/TEST, new training, architecture search, retry, optimality or speedup inference. Group is the analysis unit; source variants are dependent observations.

## Fixed models and inputs

`tabular_v3` is the saved128 HistGradientBoosting baseline, declared here without consulting current outer metrics. `families_v5` uses the persisted INNER family promotion and selected candidate from original successful task3 and declared recovery task0/6/9. Successful original training tasks and all original failed attempts remain unchanged. `graph_v6` uses the persisted INNER architecture promotion and selected numeric NPZ. No current graph outer outcomes are read by the adapter. Group partitions,17 features, saved fit-only normalization, seed17, selected weights/checkpoints and native thread settings must match. Every chosen group must occur only in its saved model's outer partition.

Freeze verifies completed receipts, result/source identity bindings, selected model hashes and persisted INNER evidence. Review attestations for v3/v5/v6 and all input/code hashes are pinned in an exclusive manifest before submission. Graph inference does not open graph `result.json`; preprocessing/groups, selected-inner receipts and promotion suffice. v3/v5 result JSONs contain archival outer fields but only identity, preprocessing, partition and INNER fields are accessed; no labels or outer statistics select a proposal. Selected graph weights restore with `allow_pickle=False`; trusted hash-checked sklearn/joblib artifacts use the original pin set.

Native Gurobi, family and graph runtimes remain separate existing interpreters. Family runtime pins sklearn1.7.2/joblib1.5.2/NumPy1.26.4/SciPy1.13.1/XGBoost3.0.5/CatBoost1.2.8; graph adds torch2.4.1+cpu. No combined runtime or environment mutation. Native setup remains `unicorn_env.sh`, requiring GRB and one native worker.

## Arms and stage separation

The primary proposal arms are the three **repaired-only** learned scorers and cost-only. Each learned arm scores pure case/target tariff features, then the existing `cost_learned` path-cover MILP runs with energy relaxation, visit charging caps and shared charging capacity. Cost-only uses the identical cover constraints with no logits. The existing MILP has its5-second cap; its cover is necessary structural/energy information, not a replayed fleet. No new decoder architecture is introduced.

Each selected cover goes to a separate fixed-binary charging LP (linear `market.a` objective, all movement binaries fixed). A separate process independently replays the resulting plan and pricing-start witness, rejects changed topology, and computes the exact curved target bill from replayed load. Only that independent gate yields a physical candidate cost, vehicle count, or topology novelty. The charging API internally replays extraction as well; this work remains in the charging stage's time. Novelty is assessed against every admitted retained source topology; if source admission fails, novelty is unknown.

Raw incoming/outgoing argmax decoding reproduces `EdgePrior.propose_topology`, including original movement-order ties. It is a separate diagnostic **after** primary proposals and source controls, with its own structural validation, optional fixed charging and independent replay. Invalid raw topologies retain the attempted movement set and get no plan credit; no fallback converts them into learned successes. No combined best learned arm is defined.

Source admission independently replays the available source0/source1 plans. Direct retained source, first admitted source, nearest-tariff source, and cheapest exact direct bill are named controls. Nearest-tariff retrieval is only within the same timetable's admitted two-source bank, not cross-timetable retrieval. Each admitted source is separately recharged using the identical fixed-route LP and independent replay. The predeclared source policy chooses the minimum exact curved target bill among **all admitted direct sources and all replay-valid source recharge attempts** (arm name breaks exact ties). It retains direct charging if the linear LP worsens the curved bill. Every source admission, attempted recharge and replay stage is charged to this policy; censored/missing sources cannot enter it. No learned/source best-of policy is added.

A bounded cold physical planner (`native_pathflow.solve_planner`) starts without retained sources; any incumbent must pass a separate physical replay before comparison. Cold and retained-source hull checks use the existing validated import/certify API and numerical proposal controls. Retained hull imports only original admitted direct sources, not learned proposals or recharges. Hull mixture objectives/enclosures are relaxation results, kept separate from replayed physical fleet incumbents; neither a mixture nor a timeout is physical optimum evidence. Proposal-specific hulls are outside this pilot. Unequal stage budgets prevent a matched-speedup interpretation.

## Prospective resources and failures

Array0–15%4, node`unicorn-cpu-75`, exclude`scaglione-compute-01`,1requested CPU/task,8GB/task,30min/task, all native/BLAS/graph workers1, no requeue/retry. Ceiling:16*0.5=8requested CPU-hours; actual allocated CPU/time is reported later, including failures and wrapper overhead. Allocated CPUs are recorded rather than silently assumed to equal the request.

External stage caps (include interpreter/data admission): input20s; three saved-model scoring children120s each; source admission20s; four repairs15s each (MILP5s); nine fixed-charge stages65s each (native wall55/phase45); ten independent replays15s each; three raw decodes10s each; cold planner80s (native wall70/phase55/max4 rounds); cold hull85s and retained-source hull85s (native wall70/phase55/pricing4/master6/pool32); post-selection acquisition accounting15s. Worst declared cap sum is1490s. Supervisor deadline1650s reserves10s before starting each capped stage; shell hard cap1700s leaves room for final receipts within the30min allocation. Skips due to global reserve remain explicit; no shortened-stage retry.

Before each child: exclusive payload/start files. After each child: stdout/stderr, returncode/signal/timeout, elapsed wall time, output/failure hashes and typed exception diagnostics. Save cover, charged plan, independent replay and policy before advancing. Child process groups are killed on stage timeout. Wrapper EXIT trap writes a receipt for guard/runtime/task failure; whole-task termination can leave the latest start/stdout/stderr without a Python stage receipt, which remains a censored attempt in wrapper/accounting evidence. No failure receives objective/feasibility credit. Source-acquisition outcome tables (shards08/09 only) open **after** all choices/comparison are persisted; target outcome tables never open. Both original acquisition status/cost and new stage wall/allocated costs remain visible.

## Freeze and minimal deployment

From the reviewed checkout, before launch, run the stdlib-only freeze:

```sh
PYTHONPATH=src python3 -m experiments.score_physical_route_proposal_v7 freeze \
  --output research-20260930/learning-campaign/ROUTE_PROPOSAL_TRAIN_V7_INPUTS.json \
  --graph-replay research-20260930/learning-campaign/ROUTE_GRAPH_V6_REPLAY.json \
  --graph-replay-sha f2034510ef424b70200a075ac9e8d23bbefa51e54f1a21bf0563165fc458e9aa
```

The returned SHA is `EGG_V7_MANIFEST_SHA256`; `EGG_V7_MANIFEST` is the manifest path and `EGG_RUN_COMMIT` the reviewed committed source. No manifest is generated by this protocol authoring task. Freeze requires local graph result only to verify its archived completed receipt; graph results/epoch histories are unnecessary on the inference deployment checkout.

Copy each exact path in `manifest.models[arm][task].files`, plus `manifest.replay_attestations[*].path` and manifest/code paths. This is the authoritative model file list: v3 task00/03/06/09 receipt/source_identity/result/tree; v5 original task03 and recovery task00/06/09 receipt/source_identity/result, INNER promotion, all three INNER selections, both promoted-family candidate-inner metadata, **only promoted selected model**; graph task00/03/06/09 receipt/source_identity/launch, preprocessing/groups, INNER promotion, both selected-inner metadata, **only promoted selected NPZ**. Every copied file is rehashed before inference. No graph epoch history, training predictions, unselected model or old failure archive is needed in this sparse deployment; original archives remain preserved.

Additional data: exact pool128 `pool_manifest.json`, `cases.jsonl`, `source_inputs.jsonl`; shard08 and09 `dataset_receipt.json` and `source_outcomes.jsonl` for deferred accounting only. Copy the three replay attestations and all listed code dependencies (manifest.source_hashes). Runtime/start cost is part of each child receipt; source acquisition is sunk work reported separately. No SSH or submission is performed by this package.

Results will report group-paired physical replay availability/failures, exact target bills and fleet counts, cover/raw diagnostics, novelty with complete source-bank scope, source censoring, and separate stage/acquisition/allocated time. This is a small fixed TRAIN physical-proposal pilot, not a quality/speedup claim from learning metrics or a held-out DEV/TEST study.
