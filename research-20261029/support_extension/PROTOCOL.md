# Prospective exact support-extension qualification

This NEW experiment answers the 29 October human request to determine whether
the support failure survives additional feasible duty alternatives. It does
not rerun old discovery, old exact checks or any learned policy. The original
two-service model already exhausts its service partitions. Movement-only
extensions preserve equipment; adding a battery type explicitly changes it.

## Frozen scientific questions and assigned states

Check the written continuous-domain proof, then compare its closed-form
consequences against an independently written physical reference. There are
exactly 14 cases in cases.json, in the declared order. They include two sides
of the battery threshold, the supported battery25/fee7 fleet, the battery25/
fee8 non-erasure counterexample, a hull-boundary case, and the fee12 planner
tie. No favorable replacement, larger workload, pricing scan or model fit.

The reference enumerates both service partitions, every ordered bus-type
assignment, and all vertices of raw SOC/charging polytopes using rational
arithmetic. It minimizes the physical quadratic on every segment and the
convexified quadratic over all simplices with at most three physical vertices.
This is complete here because an optimum lies on an exposed face of dimension
at most two. Singular stationary simplices admit boundary minimizers.

The optional movement example retains the zero-movement choice and adds a
2 kWh movement on the B bus in [3,3.1], during which it cannot charge. Empty
branches are retained. Every endpoint, physical optimum and price-response
endpoint has a full service, shared-power and inventory witness replayed by
the independent reference. Mixed bus types and all continuous response sets
remain in raw output. Only identical projected optimum points and overlapping
response intervals with the same total energy and fee are merged for exact
comparison. This is not trip-set filtering or deletion of physical records.

The analytic implementation uses the derived phase formulas and dominance,
not the reference's SOC vertices or hull routine. Compare exact D, CH, hull
minimizer, all physical optima, own-price regrets, full projected response sets
and old-plan regret. Test controls that corrupt an objective, erase a planner
tie, collapse a flat response interval, remove terminal charging, change a
service, exceed power, shift movement timing, or violate input domains.
All 14 must agree and every negative control must reject. Finite agreement
qualifies these implementations; the written argument supplies the proof.

## Source, execution and funding

New source closure: reference.py, candidate.py, verify.py, run.py, cases.json,
PROTOCOL.md, PROOF.md. The launch control records a separate exact source
commit. The metered verifier reads each new source buffer once, compares it
with the frozen committed bytes, hashes that cached buffer once and executes
reference/candidate from those buffers. No old artifact/import/native solver
is consumed. Python stdlib only, isolated -I -S -B, assertions enabled.
The source-defined paths are the only input authority. No data-supplied paths.

Fresh namespace cycle01. Preparation is inside the one owner; there is no
separate preparation, probe, test invocation, export or finalizer. run.py
consumes LAUNCH.json; the exact external command is separately frozen there.
One process thread and environment thread controls are set. Only serial short
git source reads are child subprocesses of the numerical verifier.

NEW inclusive package allowance 60 CPU seconds / 90 wall seconds. The worker
has 40 seconds self-CPU RLIMIT, observed inclusive CPU <45, outer parent clock
60 seconds and observed RSS <=512 MiB. Parent self-CPU soft5/hard50, alarm87
seconds, with 3 seconds reserved for kill/reap. These are process ceilings and
observations, not claims of instantaneous RSS containment or exact hard whole-
session clocks. The outer POSIX time -p meter pays interpreter startup, source
admission, exact checks, replay, serialization, packet reading and exit.
Parent/self plus waited children is inclusive; child rows are never added
again. Static research, slide authoring and tools' actual CPU remain UNKNOWN,
separate from this numerical package. No refunds or restored old compliance.

Prior closed prefix: 21341.36 displayed CPU seconds, 22032.31 elapsed-sum,
21342.23 retained CPU seconds. Legacy conditional guard2546.091499549272 stays
separate. Elapsed-sum is not continuous session elapsed. Add this package once.

## Failure and interpretation

No automatic retry. Preserve every failed/late/missing/unattempted state and
all charged work. Source/configuration failures stop onward computation.
An unresolved child requires closure, not another dispatch. No old worker
session is polled. Reports are published inline during the single attempt.

The intended output is a conditional stability theorem and a changed-equipment
counterexample, not a universal claim about richer EVSP instances. No V2G,
field calibration, public-fleet prevalence, ML advantage or new general
convex-hull pricing theory is demonstrated by this qualification.
