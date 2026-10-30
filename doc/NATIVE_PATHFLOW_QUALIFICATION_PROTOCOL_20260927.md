# Prospective compact path-flow qualification

27 September 2026. Protocol `native-pathflow-qualification-20260927-v2-energy-band`.
Formulation `egg-native-pathflow-v2-energy-band`.
Candidate implementation only: no optimizer run before independent source/test/
protocol preflight and published freeze. This gate does not change any archived
physical, half-minute or hull result.

## V2 scope and preserved first evidence

V1 source and first twenty-control results remain preserved at `ebb146e`, and
the first public pricing pilot remains at `282e00b`. V2 adds exactly two
aggregate energy inequalities and their raw proof ledger; the variable set,
objective, decoding, replay, solver admission and resource budgets are unchanged.
All twenty scientific inputs and targets are byte-equivalent after JSON
serialization to `result/native_pathflow/20260927-attempt1/frozen.json`.

The exact stored-number band combines intended per-leg energy conservation
with a separately derived envelope of V1 selected SOC-row constant rounding.
It is redundant for integer points of the exact old stored matrix, strengthens
its fractional relaxation, and contains the intended physical conservation
projection. It is not an equality assertion about floating native incumbents.
See `NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md` for both proofs, outward
endpoint materialization and the runtime expression-assembly checks. Native
feasibility tolerances remain unchanged; finite precision behavior requires
this new qualification.

## Why the compact formulation

The complete public 37-service case produces 751,914 and 705,294 candidate
charging variables with a vehicle index. This is a representation cost, not a
reason to discard services or directed movements. On the identical declared
physical set, one binary per movement selects disjoint service-DAG paths. Each
mandatory service has one selected incoming and outgoing movement. Pullouts
count used homogeneous buses and cannot exceed the original vehicle cap.

Trip-before/after SOC and mode/interval energy replace their vehicle-indexed
copies. Selected paths recover vehicle ownership for the unchanged independent
physical replay and serial connector decoder. The accompanying equivalence
review proves projection and lifting of integer feasible points, including
multi-leg reserve/capacity, full replenishment and shared resources. It does not
claim equal LP relaxations, native solver bounds, runtimes or numerical errors.
The two public variants have 20,322 and 19,062 compact charging variables, but
that dimension count alone is not a scalability result.

## Prospective controls and analytical target

Retain all nineteen control definitions from the separately frozen half-minute
gate unchanged, including their four infeasibility cases, plus the already
qualified twentieth control below. No new target or scientific instance is
added by V2:

**Three services, two native depot visits.** A, B and C run from P to Q at
[10,30], [90,110], [170,190] minutes, consuming 8 kWh each. Initial usable
battery is 20 kWh, reserve 1, efficiency 19/20, one bus allowed, and a single
30 kW connector is available on [0,240]. Each pullout is D→X→P, with two
five-minute, 1-kWh legs ending at the service start. Each pullin is Q→X→D with
the same two-leg duration/energy starting immediately after service. A→B and
B→C have four-leg depot modes: inbound immediately, outbound just in time,
two legs on each side of a verified depot split. There are no direct modes.
All service/terminal modes are present; the one-bus cap forces the unique
complete A→B→C structure. Hourly market edges remain [0,60,120,180,240].

Total service energy is 24 kWh and travel energy is 12 kWh. Driving duration is
60 minutes. With bus cost 7, driving cost 0.5/minute and unit energy prices,
the exact target is `7 + 30 + 36/(19/20) = 1423/19`. A witness buys `240/19`
grid kWh in each of [40,80], [120,160] and [200,240], under each 20-kWh window
capacity. It reaches the depot with inventory 8, charges to 20 and departs
with the subsequent two-leg draw; all reserve/capacity bounds hold. This is an
analytical acceptance target and proof witness, never a solver seed.

The full twenty-cell gate expects sixteen numerical certificates and four
infeasibilities. All twenty inputs and targets are compared exactly
before execution; the twentieth control covers repeated depot visits on one recovered
bus path and nonzero multi-leg energy, reserve, charging loss and driving cost.

## Immutable evidence and limits

Use a new exclusive attempt and actual published source label:

```sh
PYTHONPATH=src python -m experiments.native_pathflow_qualification \
  --output result/native_pathflow/20260927-attempt2 \
  --freeze-label ACTUAL_PUBLISHED_COMMIT --backend CBC
```

The controller preserves the earlier attempt/worker structure with explicit
dispatch to the compact module and its own source/dependency hashes. The
pricing/planner objective drivers, backend checks and bound policy preserve
the previously qualified implementation. Raw snapshots now record flat
movement/trip-SOC arrays and mode/interval charge keys, identified by the
separate V2 formulation name. Each raw snapshot additionally records the two
energy-row indices, all mode coefficient/constant defects, both exact bands
and their union, and the materialized outward endpoints. Physical row counts
increase by exactly two; all variable counts remain unchanged. Audit both new
rows as well as every original row. They must be audited with those semantics; the old
vehicle-indexed raw auditor is not silently reused.

Budget: one thread, 10 seconds per native phase, 45-second routine limit,
60-second hard child timeout, at most 48 planner rounds, certificate width
1e-4 and analytical-target agreement 2e-4. All twenty cells are attempted,
including after a prior failure. Preserve starts/statuses/raw variables,
normalization/decoding ledgers, plans, objective reconstructions, exceptions and
all process receipts. No retry or within-attempt tuning. Existing numerical
roundoff/replay policies remain unchanged; exact stored-number arithmetic must
not be called exact physical or exact MILP certification.

Independent preflight must check the source against the projection/lift proof,
fake extraction for repeated visits, both energy-band proofs and runtime
assembly checks, the exact fractional witness excluded by the new lower row,
all control definitions and unchanged
bound policy. After execution, manifest the raw directory before independent
result audit. Audit every compact raw constraint, graph recovery, physical
session, native objective and analytical/PWL lower bound; preserve all failed
or unresolved cells. Passing admits only this compact model on the declared
synthetic controls. A public-timetable pilot and any use inside hull pricing
need separately frozen executions and evidence reviews.
