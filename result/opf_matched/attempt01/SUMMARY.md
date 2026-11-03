# Matched German feeder dispatch

The frozen roster has 144 assignments. The cell states are evaluated (108), structural_infeasible (36).
The same two dates, grid, sites and fleet families recur across assignments. Each count below describes this design.

## Baseline completeness

| Arm | Assigned | Numerical objective | Qualified | Missing qualified |
|---|---:|---:|---:|---:|
| fixed | 144 | 98 | 6 | 138 |
| strong | 144 | 98 | 7 | 137 |
| joint | 144 | 98 | 3 | 141 |
| hull | 144 | 98 | 73 | 71 |

Fixed commits to the predetermined rank pairing. Strong commits to the widest interval at minimum fleet size. Joint may choose the physical duty count. Hull may mix whole schedules before the network serves the mean demand.

## Paired costs

The table counts differences above €0.01. The available mean uses only qualified pairs. A dash in the full mean records at least one missing pair. Differences within one cent leave exact support unresolved.

| EUR difference | All numerical pairs | Numerical > €0.01 | Qualified pairs / assigned | Qualified > €0.01 | Within ±€0.01 | Below −€0.01 | Available mean | Full mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| joint − hull | 98 | 0 | 3/144 | 0 | 3 | 0 | 0.000 | — |
| fixed − joint | 98 | 15 | 2/144 | 0 | 2 | 0 | -0.000 | — |
| strong − joint | 98 | 0 | 3/144 | 0 | 3 | 0 | 0.000 | — |

The one-bus-fee prediction could be compared with numerical objectives in 3/144 assignments. 0 fell outside the range [0, fee] by more than €0.01. 0 were within €0.01 of the upper boundary. The strict inequality follows from the stated layer assumptions. Native objectives alone cannot certify a strictly positive gap or equality.

## Where native limits bound the selected joint dispatch

| Counting unit | Admitted / assigned or distinct | Voltage | Thermal | Either | Both | Neither |
|---|---:|---:|---:|---:|---:|---:|
| Joint trajectories | 3/144 | 3 | 0 | 3 | 0 | 0 |
| Quarter occurrences | 36/1440 | 36 | 0 | 36 | 0 | 0 |
| Distinct quarter-dispatches | 36/36 | 36 | 0 | 36 | 0 | 0 |

A trajectory counts a limit if it is active in any selected quarter. Voltage and thermal may bind in different quarters of one trajectory. The quarter rows require a complete qualified dispatch, one time per date and site within each assignment. The sensitivity groups repeated observations by date, site, quarter and both depot and backup MW rounded to one watt. 0 rounded keys had conflicting labels. Native constraint activity alone cannot identify a nonzero shadow price. Marginal losses can affect prices when neither limit binds.

## Results by design factor

| Factor | Level | Assigned | Fixed qual. | Strong qual. | Joint qual. | Hull qual. | Joint−hull pairs | > €0.01 | Fixed−joint pairs | > €0.01 | Strong−joint pairs | > €0.01 | Any voltage / joint cells | Any thermal / joint cells |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| window | primary | 72 | 3 | 4 | 3 | 51 | 3 | 0 | 2 | 0 | 3 | 0 | 3/3 | 0/3 |
| window | secondary | 72 | 3 | 3 | 0 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| fleet | homogeneous | 72 | 4 | 4 | 1 | 46 | 1 | 0 | 1 | 0 | 1 | 0 | 1/1 | 0/1 |
| fleet | sistig | 72 | 2 | 3 | 2 | 27 | 2 | 0 | 1 | 0 | 2 | 0 | 2/2 | 0/2 |
| site | near | 72 | 2 | 2 | 0 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| site | far | 72 | 4 | 5 | 3 | 32 | 3 | 0 | 2 | 0 | 3 | 0 | 3/3 | 0/3 |
| size | 10 | 48 | 2 | 3 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| size | 40 | 48 | 2 | 1 | 0 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| size | 80 | 48 | 2 | 3 | 3 | 25 | 3 | 0 | 2 | 0 | 3 | 0 | 3/3 | 0/3 |
| date | 2024-01-17 | 72 | 6 | 7 | 3 | 45 | 3 | 0 | 2 | 0 | 3 | 0 | 3/3 | 0/3 |
| date | 2024-07-17 | 72 | 0 | 0 | 0 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| market | hard | 48 | 2 | 3 | 0 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| market | backup_low | 48 | 2 | 2 | 1 | 25 | 1 | 0 | 0 | 0 | 1 | 0 | 1/1 | 0/1 |
| market | backup_high | 48 | 2 | 2 | 2 | 27 | 2 | 0 | 2 | 0 | 2 | 0 | 2/2 | 0/2 |

## Wholesale-only control

| Difference | Available / assigned | Above €0.01 | Available mean EUR |
|---|---:|---:|---:|
| joint − hull | 108/144 | 0 | 0.000 |
| fixed − joint | 108/144 | 18 | 0.542 |
| strong − joint | 108/144 | 0 | 0.000 |

The wholesale control omits feeder losses, voltage and current constraints, and local generation. The per-cell JSON records schedule counts, energies and the control costs for comparisons on the same assignment.

The machine-readable companion retains the full roster, including failed and structurally infeasible cells, every native arm status, the conditional one-fee checks, within-assignment quarter counts, and incomplete trajectory diagnostics.

## Schedule choices in matched qualified comparisons

| Committed control | Defined / assigned | Joint uses more buses | More buses and saves > €0.01 | Equal bus count | Equal count and saves > €0.01 | Joint uses fewer buses |
|---|---:|---:|---:|---:|---:|---:|
| fixed | 2/144 | 0 | 0 | 2 | 0 | 0 |
| strong | 3/144 | 0 | 0 | 3 | 0 | 0 |

At the same count, a saving relative to the predefined pairing can be compared with the strong minimum-floor matching to assess the role of pair selection. These counts do not identify a globally unique pairing.
