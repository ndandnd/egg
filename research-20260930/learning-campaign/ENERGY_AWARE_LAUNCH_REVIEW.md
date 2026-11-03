# Energy-aware pilot launch review

Root reviewed the necessary SOC inequalities and inactive big-M bounds. A
physically feasible plan supplies a post-trip SOC witness; actual charging
is relaxed to an optimistic full reset only at a positive-capacity depot
opportunity. Shared charging capacity, charge duration and terminal full
recharge still require the separate GRB subproblem and physical replay.
The cover minimum is scoped to this relaxation, not the physical optimum.

Luna found no unresolved substantive launch blocker. Its earlier missing-test
observation was transient and resolved. Root corrected continuous-variable
indexing in pullout counts and added finite-SOC/objective return rejection.
The existing structural row order remains unchanged when the flag is off.

Sol ran 27 focused tests and 2 subtests, wrapper syntax, frozen design/source
hash checks (31 unique source pins), diagnosis recomputation and diff checks.
Tests include small SciPy/HiGHS cover solves, physical SOC witnesses from
archived feasible sources, and mocked native pipeline checks; no local GRB
fleet optimization was run. No new experiment outcome has been inspected.

All four new cells use the same two development timetables and frozen model.
No refit or reserved test access. A repaired plan receives a fresh native hull
check. A failed repair retains its failure/time and independently replays the
archived source fallback, without another redundant native hull solve.
Historical bounds are labeled historical; no fresh bound is claimed there.

One serial job requests one CPU, 8 GB, 30 minutes, one native thread, no
retry/requeue, and excludes scaglione-compute-01. Root alone submits an
exclusive attempt after source backup and an active-EGG guard.
