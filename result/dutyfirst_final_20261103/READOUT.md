# Duty assignment before grid pricing, 3 November

The two-window matching reduction survives the German feeder; arbitrary zero-price duties in general hourly schedules do not inherit that dominance. The new tests have stopped, and draft1 incorporates both outcomes.

## Primary German results

Use the 72 two-hour assignments as the headline, with 66 within €0.01 of the numerical hull lower estimate, two unresolved bound widths of €0.699 and €0.807, and four conic solver-infeasible hulls. On the 68 assignments with an operating point, minimum-bus duties pass exact rational schedule checks and independent Newton AC flow to tolerance. The 36 impossible one-hour Sistig assignments are a separate design limitation. The 36 one-hour homogeneous secondary assignments give 30 cent-scale brackets and six conic-infeasible outcomes. Across all valid windows there are 96 cent-scale comparisons and two wider estimates.

The first Gurobi pass on 25 inaccurate hulls recovered eight strict points (20.40 CPU/26.57 elapsed). A single engineering adjustment from 1e-10 to 1e-8 barrier convergence recovered twelve additional strict points on the remaining seventeen (17.43/24.21). Five native optimal primals still fail the unchanged cone screen. Keeping their conic lower estimate separate from a freshly constructed AC upper gives cent-scale cost brackets in all five as well. Two other repaired points pass the physical screen but retain wider native lower estimates. Original Clarabel and Gurobi failures remain. No exact-arithmetic dual feasibility, global nonlinear AC certificate or infeasibility ray is asserted. The separate 25-case AC recovery used 8.39 CPU/9.41 elapsed, observed RSS 222,380,032 bytes, 292 distinct native power flows. Never add its individual row times to the external process total.

## The actual grid-price loop

The cohort was fixed to the original 73 strict hull cells before this run, with 51 primary and 22 secondary. Later Gurobi repair outcomes did not add assignments. Each of the four rules uses the same exact fleet response and cached fixed-load grid oracle; Gurobi followed by one prescribed Clarabel check when necessary, with independent AC validation. All 73 records are retained.

| Rule | Primary fixed /51 | Primary grid-infeasible response | Primary grid-validation failure | Primary budget stop |
|---|---:|---:|---:|---:|
| Full step | 27 | 8 | 16 | 0 |
| Half step | 27 | 8 | 16 | 0 |
| Tenth step | 16 | 8 | 16 | 11 |
| Diminishing | 27 | 8 | 16 | 0 |

Across both window designs the full, half and diminishing rules each give 43 fixed points, eight infeasible fleet responses and 22 failed grid checks. The tenth step gives 27 fixed points, sixteen budget stops, eight infeasible responses and 22 grid failures. **No nontrivial cycle is established.** The original detector prematurely called slow contractions cycles when nearby consecutive prices fell inside its recurrence tolerance. Those raw labels are retained in the trace archive as original_outcome, withdrawn in the corrected readout, and the traces completed to at most 100 using already paid oracle calls. Exact binary floating-point load normalization from the original response is preserved. No new grid solve was used for the correction.

A fixed point requires the undamped price mismatch <=1e-4 EUR/MWh and fleet regret <=€0.01. The arithmetic extension uses the same cached response and grid values; its fixed-point price mismatch therefore implies the negligible fleet regret at the unchanged selected response. Two-sided 1 kWh price probes and their failures are in the archive. The four prespecified mechanism flags are positive support gap with a certificate, price ambiguity diagnostics, distinct-load fleet ties and independently verified step-only behavior. No failed path is assigned a definite cause. H1's proposed frequent cycling receives no positive observation here; H2's cycling-cause majority is unresolved without established cycles; H3's universal qualification and H4's universal finite-budget convergence are not established. This is a numerical finite-budget study, not a theorem about all initial prices. External loop meter 133.93 CPU/147.57 elapsed, peak RSS 465,977,344 bytes.

## Capacity economics

The relevant operator is e-regio Netz. Its 2026 RLM medium-voltage price sheet gives annual capacity rates €12.22/kW-year below 2,500 utilization hours and €88.64 at or above 2,500, with respective energy rates 3.79 and 0.73 ct/kWh. A separate connection contribution is €95.64/kW. These are published tariffs, not a quote for any depot or the actual operator of the synthetic SimBench network. [Service territory](https://www.e-regio.de/netze/netzbetrieb/stromnetz) · [Annual tariffs, page 2](https://cms.e-regio.de/assets/global/Dokumente/Netznutzungsentgelte/2025-12-19-Netzentgelte-Strom-e-regio-Netz-2026.pdf) · [Connection contribution](https://cms.e-regio.de/assets/global/Dokumente/e-regio-netz.de/01012026/Fachunternehmer/Preisblatt-BKZ-e-regio-Netz-GmbH-01.01.2026.pdf)

The correct depot peak is min max(E/h1,(S−E)/h2) over the chosen duty interval, with h1=1 and h2=2. Every feasible minimum-bus matching in each of the twelve primary fleet/site/size designs admits E=S/3, including the maximum-forced-charge matching. The minimum peaks are 453–4,660 kW regardless of pairing. Thus the observed 54–549 kWh difference in minimum early charge produces **zero demonstrated capacity or connection saving** in these designs. A recurring reduction in one particular hour would matter only if it also lowers the annual metered maximum or contracted capacity. Repeating these three-hour daily windows alone yields 1,095 annual utilization hours, placing that illustration in the lower capacity-price regime. No annual saving is obtained by multiplying the annual rate by service days. Feeder feasibility and local backup remain separate. Standalone table calculation meter 9.03 CPU/6.88 elapsed; its library-import threads were not measured.

## Boundary on the 64 flagship instances

All 64 are the original synthetic development descriptors: seeds 0–15, 8/12 trips, slopes .01/.05, original hourly model, SEK. Instance and market sources were checked against original d89c672. Reuse the original certified joint interval; do not rerun joint discovery. Choose a duty partition at zero electricity price and reoptimize all subsequent charging and direct/depot transitions using adaptive supporting-line MILPs. A separate stronger control minimizes total charging energy among the admitted zero-price operating-cost optima. It also has no access to the time-varying prices when selecting duties. Both controls solve all 64 recourse problems to <=.01 SEK and pass physical replay.

| Control | Regret lower >.01 SEK /64 | Mean regret interval SEK | Largest upper SEK | Largest total-cost percentage upper |
|---|---:|---:|---:|---:|
| Zero price, original solver tie | 53 | [12.192,12.207] | 54.094 | 2.043% |
| Zero price, minimum-energy tie | 48 | [7.753,7.769] | 46.126 | 2.043% |

The electricity-only denominator field in the raw first-pass packets was a surrogate obtained by subtracting the committed operating cost from the joint total. It is not an observed joint electricity bill and is excluded from every reported ratio. The percentages above use the matching original total joint cost only. An independently written direct evaluation of the affine objective matched all 128 recorded physical upper costs within 9.1e-13 SEK. All regret endpoint arithmetic and the stronger control's zero-price operating-cost restriction passed. No fixed-duty interval beats the original joint interval. Correlated slopes share the same 32 underlying physical instances; this is no population inference and does not exclude a better price-independent rule.

One initial dispatch failed before loading python-mip (0.20 CPU/1.21 elapsed); the installed research environment resolved the import. Successful zero-price comparison 23.42/25.61, peak RSS 177,373,184; stronger control 47.97/51.30, peak RSS 156,336,128. Both use one native thread. NumPy optional-module compatibility warnings remain in raw stderr; every prescribed solve and physical check completed. All resource figures are process meters, with historical work and this turn's editing/rendering overhead outside these totals.

## Reproduction and remaining gaps

Sources and commands are in doc/opf/NEXT_COMPARISONS.md plus the named launchers. Native inputs and full raw histories remain under src/runs. This directory contains lossless compact outcomes, the final summary and capacity values. A failed table-only attempt and an intermediate incorrect loop/peak summary are preserved under src/runs/dutyfirst-intermediate-summaries, with the original logs. The final table was repaired before manuscript integration. All native workers have exited. No further scientific cohort is proposed before review of the revised draft. Remaining gaps are two practical hull bounds, 22 grid-validation failures in the frozen loop cohort, sixteen slow-step budget stops across both window designs, no exact AC dual certificate and external review of novelty/significance.
