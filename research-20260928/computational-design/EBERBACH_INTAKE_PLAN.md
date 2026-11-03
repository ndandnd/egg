# Eberbach intake plan for the next development timetable

## Decision and scope

Use the 105-service Stadtwerke Eberbach timetable as the next **development**
base, alongside both Hildenbrand single-depot variants. Keep all variants of a
base timetable in one split group. Do not assign other public bases to test
until the grouped split is designed. This was an input-only review; no native
case was built, solver/optimizer was run, or experiment/training started.

The pinned public archive is CC BY 4.0, 267,312,231 bytes, SHA-256
`3c6c2ed7c45fc441f4cb6108d830769b60c0de5e44e1a3a6fc72bed4f5f07317`
(existing intake receipt). The six Eberbach source-member hashes below were
computed from the ZIP. Only these source inputs were opened; the route-course
MAT file was fingerprinted but not parsed. No publisher-generated schedule or
charging result contents were read.

| Eberbach source member | Bytes | SHA-256 |
|---|---:|---|
| `bus_route_info.xlsx` | 3,235 | `ffc981d98a9a50b5c5796fd8516b16c662e67bc8cdc974987181534b5140af50` |
| `bus_stops.xlsx` | 3,845 | `01c642c894dab75b0640299129975bb05487e963bed2996d6cd0ec8692f602e8` |
| `deadhead_trip_matrix.mat` | 2,409 | `de6c79a361f6d85deabda294e9acad62db8efde685b4f82385577300cabfb054` |
| `itineraries.xlsx` | 13,376 | `9fcce891904cdcc00b612afbf8b846336b62967cd26c0e1164a51285b99eebf2` |
| `itineraries_course.mat` (hash only) | 31,326 | `6a34368828fb7577203fba24feec8546771f74dc18fd65b4ecd5d1c09de14601` |
| `trip_set.xlsx` | 12,794 | `7e0f7b144637e184b4983d447233fb8c28d174f612ecaae48f41d2f8cc256f48` |

## Confirmed input semantics

The four Eberbach workbooks each have one `Sheet1`; their schemas match the
existing adapter's Hildenbrand input layout. `trip_set.xlsx` has 105 unique
rows, all `trip_type=1` and `bool_service=True`, with 19 fields:
`trip_id, day_type_id, bus_type_id, itinerary_id, bus_route_id, dep_time,
dep_time_sec, dep_stop_id, dep_stop_name, arr_time, arr_time_sec, arr_stop_id,
arr_stop_name, trip_type, duration, distance, height, num_bus_stops,
bool_service`. It contains one day type and one bus type, but no calendar date.
`dep_time`/`arr_time` use `dd:HH:MM:SS`; their numeric companion fields are
seconds and match exactly. `duration` is `HH:MM:SS` and equals arrival minus
departure for every row. All event and duration values lie on the 30-second
grid. The adapter's dataset semantics are distance in km and height difference
in metres; source energy is absent.

`bus_stops.xlsx` fields are `id, name, b_depot, depot_id, lat, lon, height`;
there are 14 unique stops and exactly one flagged depot, stop 36.
`bus_route_info.xlsx` fields are `bus_route_id, bus_route_name, num_trips,
service_mileage_km`; its 9 route counts sum to and match the 105 trip rows.
`itineraries.xlsx` fields are `id, name, bus_route_id, variant_id, dep_stop_id,
dep_stop_name, arr_stop_id, arr_stop_name, time, distance, height,
num_bus_stops, bool_service`; it has 49 unique IDs. Every trip's itinerary route
and endpoints match, all stop names resolve, and all route/stop/itinerary
references are present.

The deadhead MAT structure has 14 stop IDs and complete 14x14 arrays for
`distances`, `times`, and `height_difference`; IDs equal the workbook stop set.
All values are finite and nonnegative for distance/time, diagonal distance/time
is zero, times are integral seconds and multiples of 30, and every service
endpoint is covered. Reciprocal directions differ for 77/91 distance pairs,
43/91 time pairs, and 91/91 height-difference pairs: preserve directed arcs.
`elevation_diff` is an empty vector; use the nonempty `height_difference` field
as the existing adapter does. Units follow the adapter's source convention:
matrix distance in metres, time in seconds, height difference in metres.

All events are on day offset 0. Service starts range from 05:07 to 19:12 and
latest arrival is 19:37 (70,620 seconds); durations range from 5 to 42 minutes.
Under the current 30-hour horizon and the single directed depot, source travel
times permit all 105 pull-outs and pull-ins: earliest pull-out is 05:02 and the
latest pull-in is 19:43, leaving 10 h 17 min before the modeled 30:00 full-charge
deadline. A source-only chronology screen found 5,189 direct and 4,960 depot
detour inter-service connections feasible under the Hildenbrand timing rules,
and no direct-mode wait at the flagged depot. These counts are not a fleet
feasibility or solver result.

## Difference from the Hildenbrand adapter and minimal next work

| Source property | Eberbach | Hildenbrand adapter reference |
|---|---:|---:|
| Mandatory services | 105 | 37 |
| Stops / directed matrix arcs | 14 / 196 | 5 / 25 |
| Routes / itineraries | 9 / 49 | 2 / 3 |
| Flagged depots | 1 (36) | 2 (15, 16), modeled as separate variants |
| Latest service arrival | 19:37, day 0 | 24:24, day 1 |

The current adapter hardcodes Hildenbrand's member prefix, 37-row/two-depot
checks, `H` trip IDs, Hildenbrand case names, and a 37-bus cap. The next adapter
change should parameterize operator prefix/name and expected count/depot policy,
retain `extract_source`'s exact timestamp/reference/matrix checks, namespace
Eberbach trip IDs, and emit one case for depot 36 with an explicit loose
`max_vehicles=105`. The existing 30-hour horizon can be retained for comparison,
but it is an EGG terminal-replenishment policy, not an Eberbach source fact.
The `n(n-1)=10,920` ordered service pairs are 8.2 times Hildenbrand's 1,332;
movement generation can create roughly ten thousand inter-service options.
Keep this as a pre-solve size check, not a reason to alter the model silently.

Use the same EB-3 400 kWh usable battery, 360 kW single shared connector,
energy formulae, 100 synthetic vehicle cost, and 30-hour deadline only as named
EGG assumptions if the research lead intends cross-case comparability. The
single `bus_type_id` is not evidence that the operator uses that vehicle.
Neither trip nor deadhead energy nor actual charger configuration is supplied.
Keep modeled energy and charging separate from source-observed fields.

Before any solver run, the minimal pure gate is: rerun source/reference and
directional-matrix checks; confirm per-trip modeled energy is below usable
battery; construct the single-depot `NativeCase`; estimate model size from its
movement/resource intervals before allocating a large native model; and verify
the emitted directed connection modes and case identity. Try replaying a simple
full-coverage one-trip-per-bus charging witness under the chosen terminal policy.
Failure of that conservative construction is not a data error or proof that the
fleet problem is infeasible: extra depot travel and a shared connector may require
a chained fleet witness, obtained with a separately bounded feasibility solve.
No publisher schedule or charging output is needed. Remaining source limits
are the absent calendar date/day-of-week interpretation, no observed bus-energy
or charger data, and no modeled proof yet for a chained fleet plan.

**Review pins:** adapter SHA-256
`f47a7a926d102f948d73e6d450f25a46fe7ad84fc93e4ff7e877da76ffe0e3c9`;
existing Hildenbrand source-derived case file SHA-256
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`.
