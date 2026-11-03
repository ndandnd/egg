# Independent compact-receipt check: primary bill mechanism

23 October 2026. **PASS: no numerical disagreement** for graph (`v8`) versus nonlearned ranking at 40 and 80 trips.

I independently rebuilt the comparison from the original compact `result.json`, `supervisor.json` and `replay.json` receipts for these two arms only: 120 endpoints, 360 files. All source SHA-256 hashes match `bill-mechanism/decomposition.json`; all 120 admission flags, supervisor endpoint flags and replay flags pass. Each receipt's saved operating cost equals 100 times vehicle count. No raw traces, physical full cases, sealed data, solver or training process were read or run.

The computation did not import or execute `analyze_bill_mechanism.py`. It parsed rational bill strings using 100-digit Decimal arithmetic, paired endpoints by `(case_key, seed)`, computed fleet savings directly from integer vehicle-count differences, and obtained electricity savings as the residual. Each primary pair's three reconstructed components agrees with the report's rational deltas to absolute tolerance `1e-85`. This independently checks receipt arithmetic and aggregation; it does not repeat physical replay or prove that tariff optimization caused the residual.

| Quantity | 40 trips | 80 trips |
|---|---:|---:|
| Paired endpoints / timetable groups | 30 / 10 | 30 / 10 |
| Sum of paired bill savings | 122.5140708138 | 74415.4948767200 |
| Sum of fleet-count cost savings | 0 | 68400 |
| Sum of electricity cost savings | 122.5140708138 | 6015.4948767200 |
| Fleet share of summed bill savings | 0% | 91.9163409627% |
| Median vehicles: graph / nonlearned | 3 / 3 | 4 / 27.5 |
| Median paired vehicle reduction | 0 | 23 |
| Graph uses fewer / same vehicles | 0 / 30 | 30 / 0 |
| Median of within-group median relative bill gains | 0.4702002593% | 68.3622196229% |

**Aggregation distinction:** 91.916% is `sum(fleet savings)/sum(bill savings)` over 30 paired cells. It is not a decomposition of the 68.362% median group relative gain. Likewise, the difference of marginal vehicle medians, 27.5 minus 4 = 23.5, differs from the median paired reduction of 23. Seeds are nested within ten timetables at each size.

At 40 trips both arm medians are three vehicles, and vehicle counts are identical within every pair; this does not mean every endpoint uses exactly three vehicles. All paired bill differences are therefore electricity-cost differences, including any negative pair differences. Electricity cost can change through route/energy requirements, charging opportunities and timing. This fixed-tariff comparison does not isolate price responsiveness.

At 80 trips the dominant accounting component is fleet-count cost, supporting route-construction/search explanations for the large bill gain. It cannot distinguish a better retained feasible set from faster search, establish optimal fleet counts, or show tariff-aware learning. The FT50 strategy now incorporates this finding and prioritizes route/search controls before claiming an electricity-price mechanism.

Sources: `bill-mechanism/RESULTS.md`, `bill-mechanism/decomposition.json`, and their hashed primary compact receipts under `research-20261017/local-screen-v3`. Original campaign files remain untouched.
