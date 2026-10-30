# v9 scientific source checks

Package released for independent source/protocol review; no campaign fit,
real-pool feature extraction, native probe, SSH, deployment or submission ran.
Frozen v3/v6/v8 models and reviewed v9 features/inventory remain unchanged.
All inventory-bound source hashes were rechecked and match.

Focused command (synthetic CPU fixtures only):
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_route_graph_context_v9.py`

- Initial development check:12passed/1failed in6.66s. The failure exposed an
  incorrect loader reference to `core.nr`; fixed by explicitly importing
  `native_recharge`. This was a synthetic fixture failure, not a production
  attempt or evidence from any dataset. Its failure and time are retained here.
- After adding the fold-cap distinction/gate:15passed in3.27s.
- Final scientific source, including immutable scalar-stream start guard:
  15passed in2.84s. No failed check was suppressed or tolerance loosened.
- Root independently reported15passed in4.26s; wrapper/queue fixtures have
  separate owner evidence. These are fixture timings, not campaign allocations.

The suite checks identical paired initial tensors/RNG independence, D38 node78/
decoder134 dimensions and20545/20673 parameter counts under20700ceiling, balanced
hashed arm position, exact common17 transform/intercept column16, zero padding,
appended constant centering, fit-only inputs, disconnected graph inference and
equal group/source/edge weights. A manual full-gradient Adam update agrees
exactly with the trainer for both architectures. It checks portable selected
NPZ/probability replay, strict INNER ties/patience, every-epoch scalar/sparse-best
checkpoints, handled failures, incomplete-gradient discard, label/pool gating,
and mismatched-runtime failure before bank access.

Per-arm1600s caps are distinguished from global6900s fold caps in stop/receipt
metadata. A fold-censored selected checkpoint/predictions is retained but blocks
paired qualification, promotion and OUTER materialization/admission. Four saved
qualified arms and INNER promotion precede any OUTER load. Primary comparison
remains paired feature arms within architecture/fold/seed; timetable groups are
the independent units. There is no historical17-dimensional epoch/weight anchor,
physical feasibility/optimality, causal feature claim or end-to-end speedup claim.

Local qualification: macOS ARM64, Python3.12.2, NumPy1.26.4, torch2.4.1 CPU,
single torch/native threads. It does not establish Linux runtime compatibility;
the existing per-task node75 operator/autograd/NPZ probe remains mandatory.

Final SHA256 scientific source identities:

| File | SHA256 |
| --- | --- |
| src/egglab/physical_route_graph_context_v9.py | 636102eff2172b066ff70ff6b24f9a4cb45b93165b6a31b5ce4ea675682a1868 |
| src/experiments/train_physical_route_graph_context_v9.py | aa5bcd094b40ae09433a8bcd80f69fdb4411b5ad5dff3ff6e0a48f252b72b02d |
| src/tests/test_physical_route_graph_context_v9.py | 3bec1ffb44c60fb1e696b3026c8794977de273b985f5569ddfec7e9281a87f82 |

No further scientific source edits are planned absent a substantive review issue.
