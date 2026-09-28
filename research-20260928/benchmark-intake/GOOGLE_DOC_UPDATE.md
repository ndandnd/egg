## Preparing independent timetables and protecting evaluation — 28 September 2026

The 105-service Eberbach timetable now has a derived EGG input and a conservative feasible charging schedule. All 105 services are covered using one bus per service, with full battery replenishment completed before 20:00 within the 30:00 horizon. This proves feasibility under our assumptions; 105 is not a minimum fleet size or an optimized operating cost. The compact model is estimated at about 292,000 variables and 312,000 constraints, so the first bounded solve must measure model construction as well as optimization.

We are keeping timetable data and modeling choices distinct. The public source includes estimated deadhead movements, while battery capacity, depot charging resources, cost parameters and terminal replenishment are explicit EGG assumptions. The new input must pass the same physical rules as earlier examples; we will not change them silently to obtain a favorable result.

We reserved the 20 public operator groups prospectively: ten for future training, four for development and six for untouched evaluation. Hildenbrand and Eberbach remain development, with all depot, tariff and timing variants kept together. The reservation uses input fingerprints and metadata only; byte differences do not prove semantic independence. Any held-out group later found to overlap an exposed base must be quarantined, not described as a clean test. These reservations do not commit us to solving every large network. The synthetic design specifies 8, 16 and 24 services with entire generator seeds reserved together, under full terminal replenishment; no new synthetic cases have been generated or solved.

The computational first draft now has a finite completion plan: finish this intake, run one bounded cold/reuse/nearest-neighbor comparison, including cheapest-current-bill selection over the same stored pool for price-only changes, then consolidate the exact results, computational evidence, literature and figures into LaTeX. A trained ML method is optional for that first draft. Unresolved intervals and unfavorable comparisons will remain visible rather than generating an unlimited series of extra experiments. No solver or cluster job was launched during this intake package.

Intake and evidence: https://github.com/ndandnd/egg/blob/4e789e3cc2a0b050040e827a9996b64eeb1c7b54/research-20260928/benchmark-intake/README.md

Public grouping: https://github.com/ndandnd/egg/blob/4e789e3cc2a0b050040e827a9996b64eeb1c7b54/research-20260928/benchmark-intake/GROUPED_DESIGN.md

Synthetic scaling design: https://github.com/ndandnd/egg/blob/4e789e3cc2a0b050040e827a9996b64eeb1c7b54/research-20260928/benchmark-intake/SYNTHETIC_SCALING_DESIGN.md

First-draft completion plan: https://github.com/ndandnd/egg/blob/4e789e3cc2a0b050040e827a9996b64eeb1c7b54/doc/DRAFT_COMPLETION_PLAN_20260928.md
