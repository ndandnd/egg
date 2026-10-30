# Synthetic scaling design

Use a new generator that emits the current `NativeCase` contract, including
full terminal replenishment. Do not pool it with the legacy
`synthetic_instance` workload, whose 10% terminal-SOC requirement defines a
different feasible set. This note specifies a candidate family only; it does
not implement, generate, admit, or solve cases.

Use 15 independent generator seeds (1000–1014) crossed with 8, 16, and 24
mandatory services. Reserve by seed group before outcomes: rank
`sha256("egg-nativecase-scaling-split-2026-09-28-v1|" + seed_id)` ascending;
seeds 1011, 1013, 1010, and 1003 are test; 1006, 1012, and 1009 are
development; the other eight are train. Every service-count and physical or
market variant of a seed inherits its split. Keep test seeds unopened. The
first comparison may select only a few frozen development cells; the full
15-by-3 grid is not a prerequisite.

A simple construction can guarantee feasibility while leaving charging
prices consequential. For each even service count `n`, form `n/2` paired
vehicle duties over a depot stop A and a second stop B. Each duty runs A→B,
waits at B for at most 30 minutes, then runs B→A; stagger the pairs so every
service finishes before 18:00. Use a 100 kWh battery, 20 kWh reserve, and
full initial and terminal charge. Bound both service draws at 28 kWh each,
off-depot wait draw at 0.5 kWh, and pullout plus pullin at 4 kWh per duty.
Total duty draw is then at most 60.5 kWh, leaving at least 39.5 kWh before
terminal replenishment and above reserve throughout. Require the generator to
construct and physically replay this witness for each seed before admitting a
case; the bound is a design target, not an observed result.

Open terminal charging at 18:00 and require full replenishment by 30:00. With
one shared 90 kW connector and 90% efficiency, the worst-case 12-duty family
needs at most about 807 kWh from the grid, below the 1,080 kWh available over
12 hours. A four-hour low-price window has only 360 kWh capacity. Medium and large
witnesses at the stated upper-bound draw would exceed that window; this does
not prove that every generated case or optimized fleet does. Record realized
energy and charging pressure, including cases with no scarcity, without
filtering on outcomes. Pair each physical case with a flat tariff and a
tariff having that four-hour low window; keep trip data, vehicle assumptions,
and all other inputs fixed.

For price-only comparisons, stored physical fleets stay feasible. Evaluate
each retrieved or nearest-price fleet against the exact minimum current bill
over the same stored feasible-fleet pool; nearest-neighbor retrieval alone is
not evidence of an ML benefit. Cross-timetable route transfer needs explicit
trip correspondence and physical repair, and is outside this design. Report
the pool comparator, retrieval result, and any certified optimization result
separately. No labels, model training, outcomes, or solver runs are part of
this intake plan.
