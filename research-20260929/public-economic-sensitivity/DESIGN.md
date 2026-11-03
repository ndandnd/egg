# Public economic sensitivity, first development block

Two one-depot Hildenbrand variants of the same 37-service timetable are
evaluated at four declared synthetic economic scenarios each: bus fee and
curvature multiplier `(100,1)`, `(40,1)`, `(20,1)`, `(40,2)`.
The hourly linear intercept remains 0.20 and the base quadratic coefficient
is `1/900`. These eight cells are development sensitivity cases, not eight
independent transport networks. No scenario will be selected or dropped
based on its gap outcome, and no held-out or protected data are opened.

Each cell gets a newly named and hashed case/market, even the f=100 control.
Only `vehicle_cost` changes from the pinned depot physical case; the
charging/route feasible set is preserved. Physical planning, cold QP
complete-fleet hull and fixed-price response are solved afresh. No old
f=100 native bound or witness cost is imported. The response is eligible
only after a bounded, on-time, replayed planner incumbent and evaluates
the gradient of that named incumbent's load on the same physical case.

The planner and hull each have 180 s coordinator wall and 160 s native phase;
planner has 16 tangent rounds. QP hull has 16 pricing calls, 64 master calls
and columns, 8192 projected rational bits, epsilon `1e-4`, pool tolerance
`1e-6`, 64 polishing steps, 20 s soft polish allowance, 10 s pricing reserve,
denominator `10^9`, at most 500 QP proposal iterations. Response has 60/45 s
wall/native and one round. Hard stage caps are 210/210/90 s with 10 s TERM
and 2 s KILL grace. The 24 potential stages require at most 4368 s including
grace, within controller 5400 s, outer 5700 s and Slurm 6000 s. Use one
CPU, 8 GB, GRB seed 0/thread 1, no retries/requeue, and exclude
`scaglione-compute-01`.

Report every stage outcome, cost and stop. Show raw `D`/`CH`, their compatible
combined enclosure and nonnegative gap, planner width and named-incumbent
regret. The precomputed availability/cardinality floor for each scenario is
reported separately as an ideal-model analytical bound; it is never a
native pricing cut or silent lower-bound replacement. All native results
retain solver and physical-replay tolerances.
