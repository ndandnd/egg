# Where the bill gain comes from — exploratory analysis, 23 October 2026

This analysis uses the immutable completed development screen. It introduces no new solver runs, model fits or timetables. The 342 accepted endpoints were independently replayed in the earlier audit; this analysis checks terminal admission flags and decomposes their saved exact bills.

The generator charges 100 cost units per vehicle and zero movement operating cost. Thus the exact bill difference separates into fleet-count cost and electricity cost. A reduction in fleet count can dominate the result even without superior electricity-price response.

| Comparator | Trips | Paired cells | Median vehicles: graph / comparator | Median paired vehicle reduction | Fleet share of summed bill saving |
|---|---:|---:|---:|---:|---:|
| nonlearned | 40 | 30 | 3 / 3 | 0 | 0.0% |
| nonlearned | 80 | 30 | 4 / 27.5 | 23 | 91.9% |
| catboost_v5 | 40 | 30 | 3 / 3 | 0 | -0.0% |
| catboost_v5 | 80 | 30 | 4 / 13 | 9 | 85.9% |
| random | 40 | 30 | 3 / 6 | 2 | 97.3% |
| random | 80 | 29 | 4 / 6 | 2 | 73.1% |
| full4 | 40 | 30 | 3 / 3 | 0 | 0.0% |
| full4 | 80 | 14 | 4 / 22.5 | 18.5 | 84.8% |
| cold | 40 | 30 | 3 / 3 | 0 | 0.0% |
| cold | 80 | 29 | 4 / 27 | 23 | 85.9% |

Shares use sums of matched cost differences, not the published median group percentage. They may exceed 100% or be negative when component changes offset. Conditional comparisons retain missing endpoints; no finite penalty is imputed. Seed repeats are not independent timetables.

Interpretation: use these decompositions to design the next experiment, not to retrofit a mechanism claim. Fleet-count gains can result from easier search, a better retained feasible set, or both. Distinguishing those explanations requires matched recovery/time-budget and stronger baseline experiments. A claim about tariff-responsive learning requires tariff shifts and price-blind ablations, which this fixed-tariff screen did not include.

Accounting: 0.1533 CPU seconds for this compact receipt analysis. Full exact deltas and source hashes are in decomposition.json.
