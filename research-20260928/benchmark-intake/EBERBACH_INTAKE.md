# Stadtwerke Eberbach native intake

This development case adapts the 105 fixed services of Stadtwerke Eberbach from
Sistig et al., [public dataset DOI 10.6084/m9.figshare.26088190.v1](https://doi.org/10.6084/m9.figshare.26088190.v1),
licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The pinned
archive SHA-256 is `3c6c2ed7c45fc441f4cb6108d830769b60c0de5e44e1a3a6fc72bed4f5f07317`.
The derived case is `data/public/sistig_26088190_v1/eberbach_native_case.json`
(SHA-256 `5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19`).
The compact machine-readable receipt is `EBERBACH_PREFLIGHT.json`. Both preserve
source-member provenance; only six operator input members were read or
fingerprinted. The route-course MAT member was hashed, not parsed. Publisher
schedule and charging outputs were not read.

## Source and transformation

The source has 105 unique service rows, 14 stops, one flagged depot (36), nine
routes, 49 itineraries, and a complete directed 14×14 deadhead matrix. Source
timestamps, durations, references, and matrix values passed the adapter's
existing exact checks. Service and deadhead energy, an actual vehicle fleet,
charging hardware, and a calendar date are absent from these inputs. The
adapter preserves all source services and all 196 directed matrix arcs. Its
`E`-prefixed trip IDs and 10,359 fixed movement modes are EGG transformations.

The EGG case selects the source-flagged depot 36 and assumes the paper's EB-3
concept: 400 kWh usable battery, 1.20 kWh/km service traction, 0.96 kWh/km
deadhead traction, and 16 kWh/h auxiliary use. It assumes one shared 360 kW
connector, no depot parked auxiliary load, full initial inventory, full terminal
replenishment by 30:00, a loose 105-bus cap, synthetic vehicle cost 100, and
zero deadhead travel cost. These are modeled comparison choices, not observed
Stadtwerke Eberbach vehicles, chargers, energy use, or economics. The largest
modeled single-service energy is 35.365 kWh, below the 400 kWh inventory.

## Pure preflight result

The native case validates and compiles into 186 resource intervals. The mode
counts are 5,189 direct, 4,960 depot detour, 105 pullout, and 105 pullin.
The case identity is
`9dc30e1034953808e0c98cd467ae02272eaf6ddde2428a326d26b08b6db94c48`.
From the current compact path-flow construction, a combinatorial count gives
10,359 movement binaries, 210 service state-of-charge variables, 281,038
charge-interval variables, and 30 market-load variables: 291,637 variables and
approximately 312,316 rows before objective attachment. No MIP model was
allocated. One local regeneration (archive verification through JSON
serialization) took 7.417 seconds; this is a preparation observation, not a
model-build or solve time. A future bounded solve must measure model-build
time within its cap.

The conservative construction assigning one service to each of 105 buses
replayed successfully with the single shared connector and full terminal
replenishment. It uses 2,398.194 modeled kWh including pullout and pullin,
has a maximum individual path energy of 70.289 kWh, and completes its last
terminal charge at minute 1189.267 (19:49), before the minute-1800 deadline.
This establishes a feasible 105-bus upper-bound construction under the stated
EGG assumptions. It does not establish an optimal fleet count or reproduce a
publisher result. No optimizer, cluster job, or scientific campaign was run.

The focused Eberbach and existing adapter regression tests passed (11 tests).
Hildenbrand regeneration remained byte-identical to its existing 8,046,032-byte
artifact (SHA-256 `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`).
