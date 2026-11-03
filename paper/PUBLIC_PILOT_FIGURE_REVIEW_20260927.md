# Independent review of public pilot Figure 7

27 September 2026. **PASS** for `make_public_pilot_figure.py`, its saved PNG/provenance and the Figure 7 caption in `manuscript.md`. No optimizer was imported or executed. Scientific raw files and published figure files were not edited.

The reviewer checked the four archived input/result files against their original manifest hashes and the figure provenance, then reproduced the figure into an isolated temporary directory using the existing plotting environment. Native imports were externally blocked. The reproduced PNG is byte-identical to the saved PNG. This is a figure-source check on the audited numerical files, not a new verification of omitted private stdout or a repetition of the complete earlier physical-model audit.

For each scenario, the archived vehicle IDs are exactly 0 and 1. Every mandatory service occurs once and all 37 source IDs are covered. Every displayed charge's movement belongs to its indicated bus and connector 0. The reviewer compared every rendered bar's position, width, lane and height with the saved service, positive-duration movement/wait leg or charging session. Bus colors consistently identify those owners. Zero-duration movement legs have no positive-width gray bar, while their saved SOC events remain included.

| Scenario | Service bars | Charging sessions | Total bar patches | SOC points | Initial | Service | Movement | Charge completion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Depot 15 | 37 | 19 | 80 | 116 | 2 | 37 | 58 | 19 |
| Depot 16 | 37 | 22 | 84 | 119 | 2 | 37 | 58 | 22 |

All scatter coordinates were compared directly with the saved trajectories, separated by bus and marker kind. There are **235 plotted records: four initial states and 231 subsequent audited events**. Coincident initial points overlap visually; both buses' initial records are nevertheless included. Both start at 400 kWh and finish at 400 kWh within the unchanged replay tolerance. The SOC axes extend from -0.3 to 30.3 hours, so complete initial/deadline markers remain visible. No line interpolation or within-leg trajectory is invented.

Both saved result statuses are `bounded` and both native statuses are `FEASIBLE`. The caption explicitly calls them incumbents, not proven cost optima, and identifies the synthetic costs, modeled energy, single-depot/one-connector assumptions and source day offset. It does not imply a minimum fleet, a publisher schedule reproduction or operational savings.

Visual inspection found the four-panel layout readable, with distinct bus colors, gray movement/wait bars, hatched connector sessions, circle/triangle event markers and an identifiable dotted 24-hour line. Some very short positive charging sessions appear as thin marks; this preserves the saved data without widening or deleting them. No clipping or caption/data inconsistency was found. Final manuscript page placement remains part of the separate document layout review.

## Inspected hashes

- `paper/make_public_pilot_figure.py`: `2caff23a90c25e977f774b49bf98d6ed4de3b613127994cb3a78850191b1c944`
- `paper/figures/public_pilot_witnesses.png`: `426415449c12da9437f128ed1540016f403e6244a7aad72769cb9ff34daefa4f`
- `paper/figures/public_pilot_witnesses_provenance.json`: `b20fe8d223c46e7e02686acb42d53b4dc04eb45cba779984aa617a7008885d35`
- `paper/manuscript.md`: `906a6e9b73ba31f252b93cc78c9da1cf9c4bddef7d65bcdea48f11a9c900ebab`
