# Stage-one learned proposal: observed result

The first model trained successfully on six feasible incumbent rows from two
independent eight-trip training timetables (both source markets and the target
cold arm per timetable). The development timetable was excluded from fitting.
The controller receipt reports 1.023 seconds for the trainer subprocess,
including startup; the trainer's own receipt reports 0.492 seconds for fitting,
descriptive leave-one-group-out refits, and development inference together.
The proposal reports 0.045 seconds of that same run for online topology
prediction, validation, and scoring. **The 0.045 seconds is included in the
trainer time, not added to it.** The two development source solves cost 6.561
seconds together before any target arm could use their plans.

The raw development topology was new, but it did **not** form a valid path
cover: independent incoming/outgoing edge choices failed `recover_paths`.
Projection onto the two physically replayed source fleets gave equal
five-movement symmetric-difference distances. The learned likelihood tie
breaker selected the source1 fleet. The cheapest directly computed target bill
and nearest source tariff both selected source0. Source0's direct target bill
was 355.448; learned source1's was 376.779. The learned choice therefore paid
21.331 more as a fixed fleet before target optimization. This is a genuine
choice difference, but no new route entered the target solver: learned imported source1's existing
feasible fleet column (key prefix `6184074f`), while cheapest bill imported
source0's (key prefix `98b0c5f3`).

All development target arms, including cold, learned, cheapest bill, nearest
price, and retained, finished with the same certified bound interval,
approximately [330.218017536, 330.218018536]. Their solver wall times were
2.878, 3.080, 3.180, 2.980, and 3.982 seconds respectively. On this one
small case the learned arm gained neither final objective quality nor clear
runtime: it was 0.100 seconds faster than cheapest bill but 0.202 seconds
slower than cold, differences too small and unreplicated to interpret. The
campaign fed the selected fleet as a **feasible-pool hull seed**, not as a
native MIP start. An online comparison should count source acquisition,
inference, and target solve time, with the exact same source pool available to
all candidate-selection controls. Fitting and refits are separate offline
costs; the combined trainer receipt must not be added to inference again.

The architectural limit is now visible. The model can predict route edges
across timetables, but its current projection can only return a route already
present in the current timetable's source pool. The next scoped improvement is
a **route-fixed charging repair**: first turn edge scores into one legal DAG
path cover using the declared movements and vehicle limit; then, with those
routes fixed, solve only the continuous charge amounts and timing on the
compiled availability intervals under target prices, battery bounds, shared
grid/connector capacity, and full terminal recharge. Materialize sessions
deterministically and admit a plan only after the independent continuous-time
`replay_native` check; otherwise record repair failure and fall back to the
source pool. This would let the learner propose a truly new whole-fleet route
while leaving global certification to the unchanged native solver. It is a
separate development experiment, not a result of this pilot.

The current trainer already iterates over multiple frozen development groups,
matches each source fleet by physical identity and base group, and uses a
fixed 17-feature representation while movement counts vary. The stage-two
generator yields 120–122 movements at 12 trips, 352–354 at 20 trips, and
715–719 at 28 trips. A local, synthetic 7,146-row NumPy loop matching seven
500-step fits took 0.324 seconds with one BLAS thread; this is only a fit-core
check and excludes catalog loading and physical replay. Stage two must
write **all** development source rows before the single immutable trainer
invocation. The 45-second trainer cap has not been measured on the larger
12-, 20-, and 28-trip complete-fleet plans; a completed stage-two receipt is
needed to establish that the full pipeline fits within that cap.
