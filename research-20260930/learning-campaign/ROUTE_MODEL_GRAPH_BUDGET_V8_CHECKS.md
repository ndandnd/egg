# Graph budget v8 local source checks

Source-only package; no campaign fit, queue/SSH action, submission, commit, push or campaign-state edit. Existing v6 source/results are preserved. Root owns independent review, freeze and launch.

Final focused command from repository root:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_route_graph_budget_v8.py
bash -n src/cluster/physical_route_graph_budget_v8.sbatch
python3 -m py_compile src/egglab/physical_route_graph_budget_v8.py src/experiments/train_physical_route_graph_budget_v8.py
```

Nine fixtures passed in3.11seconds on the final source; shell syntax and Python compilation passed. Fixtures exercise both architectures' fresh initialization and exact tiny v6 shared scalar/prefix-best anchor reproduction, continuation beyond the fixture anchor, sparse periodic weights and every-epoch fsynced JSONL, typed anchor mismatch with best-state preservation, valid30epochinner patience without forcing the cap, interrupted-gradient discard and missing-anchor hold, saved decisions before outer graph/labels, immutable runtime-failure receipts, and scalar mismatch exactly at the configurable anchor retaining current/prefix-best NPZ plus failure ledger. The wrapper missing-required-commit fixture verifies a nonzero child exit equal to the early EXIT receipt's return code. Earlier local guard fixture exposed `${var:?}`/EXIT zero-status behavior under Bash3; explicit nonzero required-var guards and incomplete-guard-phase rejection repaired it.

Local interpreter is `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3` with torch2.4.1, numpy1.26.4, scipy1.13.1, sklearn1.6.0 and joblib1.4.2. These tiny synthetic checks do not qualify the proposed Linux torch2.4.1+cpu/sklearn1.7.2/joblib1.5.2 runtime or a real bank fit. Per-task isolated native probes and runtime pins remain mandatory before TRAIN materialization.

Read-only stdlib deployment selector `tmp/build-v8-deployment.py` verifies the original replay SHA, admitted task receipt/source pins, selected INNER files and exact128pool hashes. It reads no raw graph outer `result.json` or full weight history. Local invocation:

```sh
python3 tmp/build-v8-deployment.py --output /tmp/egg-v8-anchor-deployment-20261001.json
```

It selected150receipt-pinned artifact/input files,469,546,258uncompressed bytes;9v6current300weight snapshots are explicitly absent because v6saved improvements only. Each selected model's prefix-best state, all300scalar curves and fit/inner keyed predictions remain available. Required reviewed source-context files (including the original frozen replay gate report) are identified separately from the artifact projection. The selector never changes the complete admitted v6archive; compression/transfer and source deployment remain root's actions.
