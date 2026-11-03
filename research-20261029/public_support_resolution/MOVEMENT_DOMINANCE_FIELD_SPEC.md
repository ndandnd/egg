# Movement-dominance metadata feasibility and field specification

Source-only schema assessment. Inspected NativeCase/Trip/Movement/Leg/Resource definitions, the public_case adapter/descriptor writer, and narrow build_depot_variant construction/provenance fields. No actual descriptor, timetable, matrix, plan, numerical values, imports, execution, hashes, tests or replay were read or performed.

**Verdict: the retained NativeCase-shaped descriptor alone is insufficient to verify the proposed OD dominance/completeness extension.** It supports useful internal consistency/window checks for present modes. It does not retain the full location universe or directed OD time/distance matrix needed to prove that absent modes and arbitrary intermediate-location routes are dominated. Do not remove the declared-movement scope from the manuscript on this descriptor alone.

## What the retained descriptor contains

`NativeCase` stores trips with ID, start/end times, start/end place and total modeled energy; movements with kind, before/after service IDs, fixed leg origin/destination/departure/arrival/total energy and optional depot_split; resources, market edges, selected depot, fleet cap, battery/reserve/efficiency, terminal opening/deadline and monetary costs. The public_support_resolution writer saves dataclasses.asdict(case).

The adapter projects richer public variant data into that schema. It drops movement_provenance, source_distance_m, leg roles, source matrix order/arcs, source depot flags, explicit availability horizon and energy-model formula/provenance fields. `Leg` has no distance or travel-versus-stationary-wait marker. Total energy is not an authoritative substitute for those missing fields.

## Requested checks and sufficiency

| Property | Descriptor alone | Exact missing field / limitation |
|---|---|---|
| Existing mode topology and service identity | Yes | Duplicate/unknown IDs and invalid endpoint incidence can be checked from trips/movements. This says nothing about absent modes. |
| Every feasible direct/one-depot mode is present | No | Need full directed OD travel time for each required endpoint pair, including pairs for which no movement was emitted, and the declared availability-horizon rule. Missing modes have no leg from which to recover their travel time. |
| Componentwise OD triangle inequalities | No | Need complete source-aligned location universe and every ordered OD distance AND travel-time value. Present selected-mode legs do not establish matrix completeness; a source location unused by retained movements could still be an intermediate route. |
| Canonical timing of an existing depot mode | Partly | Existing split/leg timestamps permit checking service end→inbound departure and outbound arrival→next start, and measuring its own gap. Proving earliest depot arrival/latest departure relative to all paths additionally needs OD time dominance. |
| Pullout/pullin canonical availability | Partly | Fixed service/leg timestamps and terminal_open/deadline permit internal consistency; comparing to all feasible departures/routes needs OD travel times and horizon policy. |
| Exact energy dominance from time/distance dominance | No | Need authoritative traction/auxiliary coefficients, waiting/depot-draw policies, leg-role/source-arc mapping, and exact relation to retained modeled energy. Stored floating total energies cannot uniquely reconstruct these quantities or their rounding provenance. |
| No extra charging opportunity along omitted routes | No | Need location/charging policy: selected depot versus other locations and source-flagged depots, plus explicit restriction that no other charger, energy recovery or task is admitted. A place name alone does not grant or exclude charging. |

The constructor source names the missing richer fields: `source.deadhead_stop_order_source`, `source.deadhead_arcs_directed_row_major` (origin/destination, distance_m_source, time_sec_source), source `stops`/`b_depot`, variant `movement_provenance` with source_distance_m and leg_role, `availability_horizon_sec`, and `energy_model`/charging policy. Those schemas exist outside the stripped case descriptor. Their existence is not confirmation of actual archived field completeness or a permission to reopen any source data.

## Minimal prospective public metadata transfer

If parent authorizes a new metadata check, first supply one compact immutable source-bound record with:

- complete ordered location IDs; selected depot and all charging/depot flags relevant to the proposed opportunity class;
- exactly one directed OD record for every ordered pair, including self pairs, with exact original distance/time representations and units;
- service endpoint/time identity mapped to descriptor IDs, availability horizon, terminal boundaries, and canonical mode-generation predicates;
- exact modeled energy coefficients/representation and explicit off-depot waiting, zero depot-parked draw, no unlisted charging/recovery/time dependence policies;
- mapping from every retained movement leg to its source OD arc or stationary wait, preserving original total energy and any binary-rounding seam;
- descriptor/input/source revisions and fixed paths, without data-controlled I/O.

Do not reverse-engineer missing distances from total energy or impute absent arcs from a shortest path. Do not silently replace the original direct matrix by its metric closure: that changes admitted travel/energy coefficients and could change D. No private/sealed/sibling data or new solve is needed in principle if this complete authoritative public metadata already exists, but its extraction/admission is new prospectively paid work requiring separate authorization.

## Fixed denominators and outcomes

Let n be the complete declared service count and l the complete declared location count from authoritative metadata. Freeze denominator formulas before reading outcomes:

- n service identity mappings and all declared resource/horizon/policy fields;
- l² ordered OD entries, with unique IDs, nonnegative finite values and self-arc treatment explicit;
- l³ ordered location triples for BOTH distance and time triangle comparisons, including trivial/zero cases rather than dropping them;
- n pullout and n pullin predicates;
- n(n−1) ordered distinct-service direct predicates and n(n−1) one-via-selected-depot predicates;
- every emitted leg's provenance/energy mapping and every expected present/absent mode outcome.

Each potential mode must be classified PRESENT_CANONICAL, ABSENT_TIME_INFEASIBLE, FAILED or UNKNOWN under the frozen predicates. Duplicate or unexpected modes fail; omission is not automatically infeasibility. Missing OD/policy/provenance is UNKNOWN and blocks a global dominance/completeness conclusion. Failed triangles remain explicit failed rows; they are not removed from the denominator or repaired. Internal canonical-window checks can pass while route dominance remains unknown. No statistical cohort or new physical witness is being created by these metadata rows.

## Scope after a possible PASS

Even complete OD triangle dominance addresses only paths composed of the declared location/arc universe with the stated time-independent additive consumption and charging policy. Canonical maximal depot windows use the same arcs and common zero parked draw; shared connector feasibility must be preserved by retaining original sessions inside enlarged windows. Binary stored-energy semantics must be checked separately where summing rounded leg energies could defeat an ideal real-coefficient argument. Fleet cap, mandatory services, capacity/reserve and terminal inventory remain explicit. Core's mathematical dominance proof must state these conditions; this field assessment does not prove it.

Present conclusion therefore stops at **NOT_READY_FOR_OD_DOMINANCE_CHECK: required full OD/provenance/policy fields absent from NativeCase descriptor**. No claim about whether the actual OD matrix satisfies triangles has been made. The existing exact result remains global only in its already declared finite movement-mode opportunity set.
