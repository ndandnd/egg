# Prospective route-fixed repair pilot

This two-cell pilot reuses only the stage-2 development timetables
`learning_s2016_n20` and `learning_s2017_n28`. It reads the frozen stage-2
model, frozen case/market inputs, and archived development catalog. It does
not refit the model, inspect reserved test cases, or expand the timetable
sweep. The stage-2 learned pool proposals selected source0 in both
development cases, the same candidate as nearest-price and cheapest-bill;
stage-2 target hull bounds did not close. The new pilot therefore tests
whether route prediction can yield a different replayed feasible fleet.
It does not prespecify a speedup or global optimality claim.

For each case, the experiment records these phases in order:

1. Frozen model predicts independent per-service incoming/outgoing
   movement choices. This raw topology can be inconsistent.
2. A bounded SciPy/HiGHS **MILP** (5 seconds, one thread) selects an
   integral declared-movement path cover. A legal cover alone establishes
   neither energy nor charging feasibility.
3. Every path-flow movement binary is fixed to the chosen 0/1 value in the
   existing native GRB model. The remaining charging/SOC problem is
   mathematically an LP under the **linear** target tariff `market.a`,
   with a 55-second native wall budget and one native thread. A missing
   incumbent or failed extraction becomes an explicit typed repair failure;
   there is no retry or implicit cold solve.
4. The experiment independently replays the complete repaired plan,
   checks native path-flow tags and exact route ownership, and computes
   `ops_cost + supply(market, load)` using exact rational arithmetic.
   This is the **nonlinear** target objective used for direct quality
   comparison. Its candidate correctness and timing files are written
   before a target hull solver starts.
5. If repair fails, the experiment selects the archived cheapest **source**
   fleet from the two development source-market rows, before any target
   solver result. It verifies the archived cheapest selection key, replays
   the source plan, and records its direct nonlinear target cost, source
   acquisition, selection time, and provenance. The raw repair failure is
   preserved in `failure.json`. This branch is named `source_fallback`;
   successful new repairs are named `repaired`.
6. The replayed repaired or source-fallback fleet is placed in a derived
   feasible-pool predecessor. The compact native target hull receives only
   that fleet
   and runs with the stage-2 target budget (70-second wall, QP master,
   one thread). Any target lower certificate comes from new target
   pricing; no source or repair lower bound is imported. Native result,
   fresh bounds, replay assessment, and full wall time are retained.

The archived stage-2 development `learned` pool-selected and
`cheapest_bill` rows are replayed and reported as **historical development
controls** with their recorded costs and wall times. They were run in a
different allocation, so their elapsed seconds are descriptive and not a
matched-runtime speedup comparison. Source acquisition, earlier training,
topology prediction, cover MILP, fixed-route charging, independent replay,
feasible-pool preparation, and target hull verification are distinct
costs. Either feasible fleet is an incumbent, not an optimal label.

The exclusive attempt is `result/learning_repair/20260930-attempt1`.
Freeze pins the execution commit, source hashes, native/runtime probe,
model/catalog/stage-2 receipts and frozen input hashes, both development
physical/market identities, phase budgets, and cell order. The wrapper
requests one CPU, 8 GB, one native solver thread, 30 minutes, no requeue,
and excludes `scaglione-compute-01`. It records requested and allocated
CPUs separately. Each child has a 240-second hard cap; the serial
controller has a 900-second launch guard and the shell a 1,100-second
external cap. All failures and elapsed time remain visible. Resume skips
receipted children; an interrupted unreceipted child is preserved for
postmortem. Scientific admission remains pending independent review.

Pure verification (no local native optimization):

```sh
PYTHONPATH=src python3 -m unittest src.tests.test_route_repair_pilot
PYTHONPATH=src python3 -m pytest -q src/tests/test_route_fixed_repair.py
bash -n src/cluster/route_repair_pilot.sbatch
```
