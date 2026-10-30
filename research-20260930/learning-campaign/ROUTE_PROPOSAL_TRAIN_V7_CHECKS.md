# v7 bounded implementation checks

Design/code release only; no input manifest generated, production case solved, model fitted, SSH action or submission. No current graph outer outcomes inspected. Frozen training sources, campaign state/checkpoint and original attempts remain unchanged by this package.

Local check:

```sh
PYTHONPATH=src /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
  -m pytest -q src/tests/test_physical_route_proposal_v7.py
```

Result: **13 passed in1.50s**. These are tiny/mock fixtures, not qualification of the pinned Linux native environments. Checks cover raw decoder equivalence/parallel-mode ties; invalid topology preservation; a real tiny SciPy path-cover solve with mocked charging followed by independent physical replay; changed-topology/bad-load rejection; direct-source retention when recharge raises curved bill; all16groups' exact outer-only seed17 partitions; source censoring, primary/raw order and deferred acquisition reads in the mocked supervisor; signal/timeout receipts and exclusive no-retry artifacts; path/hash guards; original-success/recovery task mapping; 1490s cap sum within1650/1700s limits; and executed lazy-QP/runtime-backend dependencies included in source pins. No campaign estimator fit is called.

Python compilation succeeds for the three new Python source files. `bash -n src/cluster/physical_route_proposal_pilot_v7.sbatch` succeeds. Every physical/scoring stage is a capped process-group child; task supervisor uses only stdlib imports. Wrapper records actual allocation and installs failure receipt trap before its source/runtime guards. Successful charge extraction remains provisional until separately saved independent replay.

The approved budget is16tasks%4 on node75,1requested CPU/8GB/30min each, native workers1,8requested CPUh ceiling, no retries. Root owns manifest freezing, review, deployment, launch and actual resource accounting. Follow the protocol's minimal deployment list: exact `manifest.models[*][*].files` plus three attestations, exact pool tables and deferred shard08/09 accounting tables. Graph epoch history and graph result JSON are unnecessary on the inference checkout.

Known scope limits: nearest-price retrieval is within each timetable's two-source bank; only cold/retained-source hull controls are included; hull mixtures remain distinct from physical fleets. The fixed-route LP optimizes linear tariff coefficients, while comparison uses independently replayed exact curved bill. Graph scoring passes raw model logits; tabular/family probabilities clip to[1e-9,1-1e-9] before logit conversion, as the existing decoder convention. Pinned Linux inference/native guards must still pass on actual deployment; native overall timeout evidence can be wrapper/start artifacts when a task is killed before Python writes its last receipt.
