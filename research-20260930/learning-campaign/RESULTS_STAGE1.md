# Stage 1 results

The first allocation completed successfully: all 17 declared cells have child
receipts, all returned code 0 without a hard timeout, and all contain a replayed
feasible whole-fleet plan. The native hull status is certified in 15 cells and
budget-exhausted in two source0 cells. All 17 saved hull assessments replayed
their global lower certificate and mixture; the two budget-exhausted cells keep
valid but nonclosing brackets. This is a small synthetic pipeline check.

Slurm accounting reports `COMPLETED`, exit 0, 91 seconds elapsed, and two
allocated logical CPUs on `snavely-cpu-16`; the job requested one CPU per task.
The native solver thread limit was one. The wrapper took 85 seconds, while the
sum of child solve times was 60.98 seconds. Memory allocation was 8,192 MB.
These receipts do not establish that only one logical CPU was allocated.

Each table row reports the best replayed single-fleet objective under that
cell's market, followed by the separately replayed global hull lower bound and
feasible mixture upper bound. Costs and bounds are rounded to three decimals.
The single-fleet label remains `optimality=unknown`; a hull certificate is not
reported as a physical integer-schedule certificate here.

| Group | Cell | Native hull | Seconds | Pricing / master calls | Feasible fleet cost | Hull lower – mixture upper |
|---|---|---:|---:|---:|---:|---:|
| 2001 | source0 | certified | 8.93 | 4 / 3 | 443.302 | 443.104 – 443.104 |
| 2001 | source1 | certified | 3.13 | 3 / 2 | 427.565 | 426.464 – 426.464 |
| 2001 | cold | certified | 2.88 | 2 / 1 | 426.464 | 426.464 – 426.464 |
| 2001 | retained | certified | 3.98 | 2 / 2 | 426.464 | 426.464 – 426.464 |
| 2001 | nearest price | certified | 3.08 | 2 / 2 | 426.464 | 426.464 – 426.464 |
| 2002 | source0 | budget exhausted | 3.58 | 4 / 4 | 347.989 | 347.274 – 347.540 |
| 2002 | source1 | certified | 3.03 | 3 / 2 | 330.694 | 329.877 – 329.877 |
| 2002 | cold | certified | 2.78 | 2 / 1 | 329.877 | 329.877 – 329.877 |
| 2002 | retained | certified | 3.88 | 2 / 2 | 329.877 | 329.877 – 329.877 |
| 2002 | nearest price | certified | 3.05 | 2 / 2 | 329.877 | 329.877 – 329.877 |
| 2003 | source0 | budget exhausted | 3.43 | 4 / 4 | 348.421 | 348.162 – 348.190 |
| 2003 | source1 | certified | 3.13 | 3 / 2 | 330.937 | 330.218 – 330.218 |
| 2003 | cold | certified | 2.88 | 2 / 1 | 330.218 | 330.218 – 330.218 |
| 2003 | retained | certified | 3.98 | 2 / 2 | 330.218 | 330.218 – 330.218 |
| 2003 | nearest price | certified | 2.98 | 2 / 2 | 330.218 | 330.218 – 330.218 |
| 2003 | cheapest bill | certified | 3.18 | 2 / 2 | 330.218 | 330.218 – 330.218 |
| 2003 | learned | certified | 3.08 | 2 / 2 | 330.218 | 330.218 – 330.218 |

The trainer ran before the development cold solve (`before_dev_cold=true`). It
fit six replayed, provisional fleet labels from only the two training groups:
source0, source1, and cold in each group. One included training source0 label
came from a budget-exhausted native hull run, but its complete fleet replayed
and its optimality stayed unknown. The frozen development input omitted the
later cold label. Training took 0.492 seconds inside a 1.023-second outer
learning receipt; the model produced one development proposal. Topology
prediction, source validation, and ranking took 0.045 seconds in total.

The development comparison had only two trainer-visible source fleets, one per
tariff. The source solves took 3.431 seconds (source0, budget-exhausted but
feasible) and 3.130 seconds (source1), for 6.561 seconds of source acquisition
shared by pool-based controls. The retained arm imported seven source
projections; learned, nearest-price, and cheapest-bill used the same two-plan
one-best-fleet-per-source pool.

| Development input / arm | Chosen source fleet | Direct target bill of proposal | Target solve result | Target seconds | Pricing / master calls |
|---|---|---:|---:|---:|---:|
| Cold | no source pool | — | 330.218 feasible fleet; hull 330.218 – 330.218 | 2.88 | 2 / 1 |
| Retained | all seven source projections | lowest source-plan bill: 355.448 | 330.218 feasible fleet; hull 330.218 – 330.218 | 3.98 | 2 / 2 |
| Nearest price | source0 | 355.448 | 330.218 feasible fleet; hull 330.218 – 330.218 | 2.98 | 2 / 2 |
| Cheapest bill | source0 | 355.448 | 330.218 feasible fleet; hull 330.218 – 330.218 | 3.18 | 2 / 2 |
| Learned | source1 | 376.779 | 330.218 feasible fleet; hull 330.218 – 330.218 | 3.08 | 2 / 2 |

The model was fit on the two training groups, predicted a 12-edge development
topology, then projected it onto one of those two source fleets. Both fleets
were at symmetric-difference distance five from the predicted topology; the
model selected source1. Its direct target bill was 21.331 higher than source0,
which was selected by both nearest-price and exact cheapest-bill controls. The
learned native arm did complete with a replayed hull certificate, but its
best-feasible fleet and hull bracket matched every other development arm. This
run shows a working prospective training-to-solver path, not a learning gain.

The main limitation is coverage: one development timetable and two training
timetables cannot support a generalization claim, and the current projection
cannot propose a feasible fleet outside the source-plan pool. Stage 2 should
add independent grouped timetables while preserving the reserved test seeds,
then measure whether route repair expands feasible proposal coverage. Compare
learned and exact cheapest controls under matched online budgets, counting
source acquisition, model fitting, proposal replay, and the target solve.

The source is the immutable attempt at
[`result/learning_campaign/20260930-attempt1`](../../result/learning_campaign/20260930-attempt1),
Slurm wrapper receipt
[`20260930-attempt1.slurm_wrapper_receipt.677817.json`](20260930-attempt1.slurm_wrapper_receipt.677817.json),
accounting receipt [`ACCOUNTING_677817.json`](ACCOUNTING_677817.json), and
download manifest [`RESULT_MANIFEST_STAGE1.json`](RESULT_MANIFEST_STAGE1.json).
The manifest records file hashes for 148 attempt artifacts; stdout/license
diagnostics follow the repository's local/remote retention convention.
