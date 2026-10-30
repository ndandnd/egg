# Independent compact path-flow preflight

27 September 2026. **Ready for the separate, prospectively frozen twenty-cell
qualification.** No optimizer was executed in this review. No native source,
raw result or protocol was edited by this independent reviewer. This is a
mathematical/source and pure-test preflight, not an executed qualification or
an operational scalability result.

## Independent mathematical assessment

The candidate preserves the original model's complete integer physical
cost/load projection, up to homogeneous vehicle relabeling, under its current
validated assumptions. The source implements one selected incoming and outgoing
movement for each mandatory service, a pullout vehicle count bounded by the
original cap, before/after service SOC, selected movement SOC equations,
activation of mode/interval charge, common fleet charging capacity, full terminal
recharge and the original intrinsic cost. It retains every declared movement
mode and mandatory service.

Positive service duration and the validated directed movement timing make every
interservice arc strictly increase service start time. Thus selected degree-one
arcs cannot form a disconnected cycle. Each component starts with a pullout,
ends with a pullin, and is a nonempty disjoint service path. Assign those paths
to a used prefix of the old vehicle labels. Copy the service SOC and charge
values to each path's owner, and set all unused label variables to zero. This
constructs a feasible old indexed solution. Conversely, unique service ownership
makes the sum of vehicle-indexed selections for each movement binary, so summing
owned energies and copying the unique service SOC produces a compact solution.
Both directions preserve used-vehicle count, all movement durations and costs,
and period grid loads.

The removed per-vehicle overlapping-visit row is redundant for an integer path:
a charging visit preceding a service ends no later than that service's start,
and a subsequent visit begins no earlier than its strictly later end. Terminal
charging starts only after the last service and return. Hence one recovered bus
cannot own two positive-duration charging visits in the same elementary
interval. The shared interval energy inequality is still present. Because each
eligible visit covers the whole elementary interval and there is one homogeneous
connector of rate `min(per_bus_kw,grid_kw)`, sequential allocation of energies
fits the interval whenever their sum fits the common capacity. The unchanged
serial decoder then materializes ownership and the unchanged physical replay
checks the result.

For each inactive movement, energy activation forces its charge to zero. The
compact before/after SOC variables belong to `[reserve,battery]`.
`M=battery+total_movement_energy` bounds every inactive pullout, direct, depot
and pullin residual. Depot inbound energy is nonnegative and no larger than
whole-movement energy; its relaxed arrival reserve and postcharge capacity rows
are redundant too. The same bounds protect the old unassigned zero-SOC rows
when lifting. Nonnegative leg energies make SOC monotone along each leg sequence;
endpoint reserve constraints therefore protect intermediate legs. Charging is
monotone upward, and its postcharge capacity constraint protects the whole gap.

This equivalence requires the existing homogeneous fleet, nonnegative consumption,
fixed acyclic timing, one homogeneous connector, permitted interval serialization
and common full start/end SOC. It does not claim equal LP relaxations, solver
bounds, numerical outcomes or runtime. Heterogeneous vehicles, multiple connectors,
vehicle-specific restrictions or additional nonpreemptive session rules need a
new argument. Future compact result audits must reconstruct the compact raw
mapping; the old vehicle-indexed raw auditor cannot be used unchanged.

## Source and admission review

`recover_paths` rejects unknown/duplicate modes, wrong degree/coverage, repeated
services or movements, too many paths and disconnected selections. Extraction
records raw flat selection/SOC/energy mappings before decoding, preserves the
qualified negative-energy correction budget and retains every positive charge.
Any positive charge on an unselected mode is rejected. Its recovered path owner
is supplied to the unchanged physical decoder/replay. Grid units, efficiency,
terminal windows, half-minute source times and continuous decoded session times
retain the prior policy.

The pricing and planner driver ASTs are **identical** to the qualified native
drivers. Their dependencies are explicit aliases to the existing objective,
backend/status, bound and replay functions; the changed builder/extractor are
local. Thus native global lower bounds, true physical upper bounds, admissible
FEASIBLE pricing and raw failure preservation keep the same policy. The worker
controller's evidence parser and main function are AST-identical to the timing
runner. The worker changes only oracle dispatch from the indexed module to the
compact module; the controller changes only the worker module string.

All runtime dependencies, original fixture helpers, the compact protocol and
projection/lift review are source-hashed before worker launch. Fresh attempts
and worker time limits remain those in the separately documented protocol.
A top-level formulation name for an infeasible result would improve convenience;
the source hashes and dedicated runner already identify its formulation, so
this is not a correctness blocker.

## Pure and independent checks

- All 19 compact pure/fake tests passed with an external import blocker that
  rejects both `mip` and `gurobipy`; no native solver was imported.
- Independently compared serialized control definitions: all nineteen prior
  input/target/case-identity JSON objects are unchanged. The new twentieth
  fixture is the declared three-service, two-depot-visit case.
- Independently enumerated all 256 selected-arc masks of that three-service
  graph with fleet cap three. Recovery accepts exactly the four covers obtained
  by independently choosing whether to join A→B and B→C. The cap-one control
  leaves the unique complete joined path.
- Independently checked inactive compact big-M redundancy at 80 exact rational
  SOC-box corners, including movement energy larger than battery capacity.
  The checks supplement the general argument above, not a feasibility claim
  for those deliberately broad inactive-variable combinations.
- Verified objective-driver and controller AST identity/deltas as described
  above, and directly reviewed builder, extractor, raw snapshot mapping,
  source-hash list, fixed budgets and target protocol.

## Independent twentieth-target calculation

The unique one-bus path uses three services of 8 battery kWh each and four
selected movement modes with total travel energy 12 kWh and duration 60 minutes.
Full initial/final recharge and efficiency `19/20` force exactly
`36/(19/20)=720/19` grid kWh. Intrinsic cost is `7+0.5*60=37`, so unit-price
objective is `37+720/19=1423/19`, approximately 74.89473684210526.

A constructive feasible witness charges `240/19` grid kWh in each of the three
native windows `[40,80]`, `[120,160]` and `[200,240]`. Each forty-minute window
has grid capacity 20 kWh. Start SOC 20 falls to 18 after pullout, 10 after the
first service and 8 on depot arrival; each recharge restores 20, and the same
inventory pattern repeats. Reserve 1 and capacity 20 are respected at all
intermediate legs and service events. Final SOC is 20. This proves the exact
flat-price target because the mandatory energy and travel cost are fixed. The
witness is analytical test evidence only and is not a scientific solver seed.

Passing the upcoming gate would qualify the compact formulation only on its
twenty declared synthetic controls, with the unchanged numerical witness policy.
A full public-timetable pilot or use in hull pricing requires separately frozen
execution and independent result review. The reduction in raw variable count
is a dimension fact, not evidence of solve speed or eventual certification.

## Reviewed freeze-ready snapshot

| File | SHA-256 |
|---|---|
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/egglab/native_pathflow.py` | `45864e08bffb81dc29b27774449f944fd074cb6654a593ab0d482abdad935c7d` |
| `src/experiments/native_recharge_qualification.py` | `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e` |
| `src/experiments/native_halfminute_qualification.py` | `1ca683c897828c7033d7d21862aae49aa25f0244c10e12abbd2c19065aa90c63` |
| `src/experiments/native_pathflow_qualification.py` | `641773c79ef7bde14c427502fc16fb81d8b54a8db019025a7fe40a627634036a` |
| `src/tests/test_native_pathflow.py` | `203bef274806123a9991b4b13c7b0a8b24be9e9b4793b5dc4a2fb5e35b81531b` |
| `doc/NATIVE_PATHFLOW_QUALIFICATION_PROTOCOL_20260927.md` | `924e85c5fad45ba1c880a61393e98e07db8943967dad5c400ee3149acad48d22` |
| `doc/NATIVE_PATHFLOW_EQUIVALENCE_REVIEW_20260927.md` | `3592c5331540502269a782d99957dcc0819596c9e5c02e65a01e2342869f2336` |
