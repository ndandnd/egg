# Actual EVSP-DR synthetic bridge — completed once

Source caf047b58047262ef24e3de069b810be0775b778, frozen control4c20be73.
Managed owner99190 exited0. Source preparation, two-arm owner and its inline
readout each ran once. No separate export, formatter, retry or fixture retuning.
The original adjacent solver was invoked by reference; the sibling was unchanged.

One synthetic six-trip base, one posted-price curve, two overlapping prescribed
duties, two reachable stations with60/120kW and one plug each. Both arms were
attempted and delivered timely physically admitted two-bus fleets. Coverage,
SOC/reserve, aggregate terminal energy and shared plug checks passed; no failed,
missing, late or unresolved arm. The full arm reassigned trips; fixed duty kept
(0,2,4)/(1,3,5). These are two methods on one base, not independent timetable cases.

| Returned quantity | Fixed duty | Full routing |
|---|---:|---:|
| Expanded-grid charging cost |39|39|
| Continuous realized charging cost |29.5|29.0|
| Expanded-grid charge kWh |280|280|
| Continuous realized charge kWh |212|208|
| Expanded-grid terminal kWh |82|82|
| Continuous terminal kWh |90|90|
| Generated columns |119|241|
| Cumulative pricing seconds |0.047649|0.086619|
| Complete parent-observed worker seconds |2.777786|1.039251|

Costs are synthetic units, with the common fleet surrogate200000 omitted from
the charging-cost rows. All26 hourly station-load arrays remain in the compact
readout. Both pricing loops reported completion of their conservative event-grid
capacity-LP pricing/row conditions; both returned numerical LP value200038.6 and
finite-pool charging MIP objective/bound39. The fixed-duty source field named
weighted_full_graph_capacity_lp_lower_bound concerns its restricted duty graph,
not unrestricted trip reassignment. Integer pool OPTIMAL is not a full route-space
integer certificate.

The model deliberately uses a coarse10-kWh SOC grid. Its conserved/rounded grid
charge and realized physical charge are different objects. The grid-value tie
coexists with a0.5-unit lower returned continuous cost and4kWh lower charge for
full routing. Neither continuous point was optimized/certified as the ideal
continuous optimum by this oracle; do not compare a grid lower bound with a
continuous upper point. Duty reassignment, movement energy, charging timing and
realization slack change jointly. This is not an isolated causal value of duty
reassignment or a rate of benefit across instances.

The result establishes one functioning EGG-local call boundary to the actual
multistation capacity oracle, including a capacity-aware fixed-duty control,
physical admission and honest output scopes. It does not establish empirical
Partille equivalence, nonlinear strategic/planner optimization, convergence of
price feedback, a learning benefit or a useful computation bottleneck. The tiny
pricing times particularly argue against training a speed surrogate for this
fixture. Full worker time includes imports/build/native/replay/publication and
has fixed arm order/cold-cache effects; it is not a comparative speedup result.

FINAL_RESOURCE_RECEIPT.json closes preparation plus owner at2.62 displayedCPU seconds,
4.83 elapsed-sum and2.68 retainedCPU, inside900CPU/1800wall. Maximum observed worker
RSS118767616bytes, one native thread. No numerical worker remains. Historical
global displayed19928.95CPU/20529.00elapsed-sum, retained19929.42CPU; separate
legacyguard2546.091499549272/actual old reviewCPU UNKNOWN remains unchanged.

See INTERPRETATION_REVIEW.md, ITERATION_AND_NEURAL_DIRECTION.md and
NEXT_NEURAL_DECISION.md. Historical learned-family continuation failures remain
unchanged and scoped. Neural route/column prediction is not permanently ruled out.
