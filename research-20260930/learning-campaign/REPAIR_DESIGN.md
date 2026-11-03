# Prospective route-fixed charging repair

`src/egglab/route_fixed_repair.py` turns a frozen edge prior into a complete
native fleet only if two separate stages pass. `repair_target(case, market,
model, *, budget, path_seconds=5, record=None)` returns
`repair_status='replayed'` with a tagged native `plan`, or
`repair_status='fallback'` with a typed failing stage. It does not silently
promote a raw edge set to a feasible fleet. A calling experiment should retain
its independently replayed source pool as the fallback and use an external
hard process cap.

First, a bounded SciPy MILP chooses binary declared movements. Every trip has
one incoming and one outgoing movement, and the number of pullouts cannot
exceed the case vehicle limit. The declared time DAG excludes subtours; the
result is still checked by `native_pathflow.recover_paths`. The MILP maximizes
learned edge log odds. It checks **route structure only**; state of charge and
charging are not inferred from its success. HiGHS is given one thread and an
explicit time cap; its status, gap, node count, and wall time are recorded.

Second, the module builds the existing compact native pathflow model and fixes
**every** movement binary to the decoded route choice. The remaining SOC and
charging variables are continuous, and the objective uses the target market's
linear `a` tariff. The fixed-route mathematical subproblem is therefore an
LP, although the Python-MIP/GRB interface still sees fixed binary variables.
This stage is not a quadratic optimization of the full target supply bill;
the target's `b` curvature is applied when reporting the repaired plan's true
cost after replay, including an exact rational value for the stored floats.
The native solve has explicit phase and wall caps supplied
by the calling experiment.

The module extracts charging through the existing native pathflow projection
and serial-session decoder, then independently calls `replay_native` and
checks that the extracted movement set exactly matches the fixed route. This
replay tests exact trip coverage, continuous-time connector use, charge power,
battery reserve/capacity, and terminal full recharge. The caller should replay
again before importing the plan into a one-column feasible-pool hull state.
Neither the route MILP objective nor the fixed-route native lower bound is a
global fleet certificate. Any global claim must come from the separate target
hull run and its usual bound checks. A failed cover, infeasible fixed-route
charge solve, extraction error, or replay error returns a fallback receipt and
no plan.
Fallback receipts retain the failing phase's elapsed time. A cover solver
without an integral incumbent also retains its HiGHS status, gap, node count,
and wall time; a returned native charging status is retained even when no
charge incumbent exists or later extraction/replay fails.

The repair is deliberately limited to one decoded route cover and one bounded
fixed-route charge solve. It does not search alternate route covers after a
charge failure. It has no local native optimization in its tests: focused
tests check legal path decoding, exact binary fixing, replay-gated success,
and typed fallback with a mocked native solve. The first prospective pilot
should run it on the frozen stage-two development cases only, with model and
case identities pinned before execution and source-pool fallback reported.
