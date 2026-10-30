# Cold baseline viability screen

This is a new six-cell **development calibration**, separate from the frozen
retrieval attempt and the earlier three-service budget-sizing diagnostic. It
asks whether a common cold iterative full-fleet hull configuration yields
usable bounds at 8, 16 and 24 services before a matched cold/retained/nearest-
neighbor study is designed. A stop, failure or null result remains evidence;
there is no automatic cap sweep or retry.

The physical cases are exactly `native_scale_dev_s1006_n08`, `n16`, and `n24`
from the reviewed pure generator/preflight. These are nested variants of one
development seed, **not independent timetables or ML test data**. Each has two
price-only markets from the existing retrieval design: `source0` has flat
intercept 0.20; `target` has 0.10 in hours 22–25 and 0.30 otherwise. Both use
30 hourly periods and curvature `1/900`. The case and market identities are
frozen before optimization. Source/target order alternates by case size.

Every cell uses cold complete-fleet hull optimization, compact path-flow
physical pricing, the native-LP master, GRB at seed 0 on one thread, 16
pricing calls, 8192 projected rational bits, 64 master calls and 64 pool
columns. Epsilon is `1e-4`, restricted-pool tolerance `1e-6`, with 64 exact
polishing steps and a 20 s soft polishing allowance. Coordinator wall is
180 s, native phase 160 s. A common 10 s pricing reserve gives a long pricing
call time to be followed by a master update. That reserve is an explicit new
design choice, so timings are not matched to the no-reserve toy factorial.
No retained columns, cache, route proposal, MIP start or learned method enters.

Each subprocess has a 210 s hard cap plus up to 10 s TERM and 2 s KILL grace.
Six worst-case children need at most 1332 s, below the 1500 s controller,
1600 s outer and 1800 s Slurm caps. Request one CPU/8 GB, exclude
`scaglione-compute-01`, and do not requeue or retry. Freeze and native seed/
runtime preflight run on the compute host before the first optimization.

Report all six rows, including failed, late and unstarted cells; full child
wall, native pricing/master time where recorded, polishing time, stop reason,
call counts, arithmetic growth, replayed global lower and feasible upper.
Unknown model-construction time stays unknown because the existing cold
oracle has no separate construction timer. Native bounds retain solver and
physical-replay tolerances. A certified cell is a configuration result for
this development case, not a speedup or broader performance claim.
