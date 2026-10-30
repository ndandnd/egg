# First learned fleet proposal, developmental

`src/experiments/train_fleet_proposals.py` fits a small, balanced logistic model
on movement choices in replayed complete-fleet incumbents from **train base
timetables only**. Source and cold target incumbents are provisional labels:
the native solver may have stopped with a gap, and this work does not call them
optimal routes. Features are declared case geometry, trip energy, charging
window, and the market price profile; no observed target cost or solve result
enters the feature vector. The model has 17 features, no hidden layers, and
uses NumPy on one CPU.

For an unseen development timetable, it first predicts an incoming and an
outgoing movement for every trip. This raw topology is **not assumed feasible**:
it may branch, exceed buses, or lack a workable charge schedule. A deterministic
projection chooses the candidate with the fewest symmetric-difference
movements from that timetable's source-solved complete fleets. Each source
fleet is checked for physical identity, replayed for continuous-time charging,
connector capacity, state of charge, and exact trip coverage, and checked by
the compact start-plan interface. The emitted plan is the original validated
source plan. The solver remains free to reject the binary hint. Thus the
projection is limited by source-pool coverage; it does not discover a new
feasible charging schedule for an arbitrary predicted route set.

Run after both training timetables have labels and the development source
tariffs have produced plans, **before** the development target cold solve:

```sh
PYTHONPATH=src python3 -m experiments.train_fleet_proposals \
  --catalog result/learning_campaign/20260930-attempt1/catalog.jsonl \
  --frozen result/learning_campaign/20260930-attempt1/frozen.json \
  --output-dir result/learning_campaign/20260930-attempt1/learned
```

`--frozen` reads the already fixed development case and target market and
creates a market-only inference row. It excludes any development cold label,
even if such a row has later appeared in the catalog. The catalog reader
rejects a base timetable that crosses splits. Reserved test groups are
rejected from this developmental run. Outputs are `model.json`,
`proposals.jsonl`, `report.json`, and `training_receipt.json`. The receipt
records the input catalog and frozen design hashes, model/trainer source hashes,
Python/NumPy runtime, elapsed time, status, and output hashes. Outputs are
created once and never overwritten. The proposal records the raw topology,
the projected complete plan, source row, exact rational cost of each source
plan under the target market, source acquisition time, and replay status.
The proposal also times online topology prediction, source validation and
scoring, and total inference separately from the training receipt's elapsed
time.

Controls are the first source plan, nearest source tariff, and the
source plan with lowest directly computable target bill. The last is an exact
stored-float rational comparison and a particularly important diagnostic:
outperforming a weaker control alone would not establish value from learning.
Leave-one-base-group-out outputs from the training groups are descriptive
development checks. A solve-time or best-feasible-objective gain requires
running the learned feasible-pool proposal and all controls under equal online budgets,
with source acquisition and replay costs counted. The first pipeline also evaluates the projected fleet in a bounded native target
solve, using the same candidate pool as nearest-price and cheapest-bill controls.
No solve-time savings are assumed before those results are reviewed.
