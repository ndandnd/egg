# Matched pilot results and next baseline — 28 September 2026

The 24-calculation pilot is complete: four physical cases, two markets and three methods. Seven calculations reached numerical certification; seventeen stopped at work limits with valid bounds. All returned on time. The two public depot variants are one Hildenbrand timetable, and every case remains development data.

Reserving ten seconds inside the pricing budget let all four public cold runs process their second fleet plan. Upper cost bounds improved by about 18–69 units. Including both market runs, elapsed time was about 350 seconds per public case versus 369 seconds for legacy cold solving. This is a descriptive comparison of final bounds and time; no time-to-common-quality speedup has been established.

Reusing feasible plans certified the shifted three-service example where both cold methods stopped at an arithmetic limit. Public reuse was mixed: upper costs improved, but fresh lower bounds weakened. Depot 15's interval narrowed and depot 16's widened; reuse took slightly more total time than reserved-time cold solving. Both public reused runs reached the rational-polishing bit limit, and neither closed its global gap.

A separate saved-evidence calculation found a stronger baseline to test. When the physical model is unchanged, a saved pricing bound at its original posted price can be re-evaluated under the new electricity supply cost using the new Fenchel conjugate. This reduces the two shifted public gaps to about 64 and 70 cost units, compared with the recorded 154 and 161. No new routing solve was used. These posthoc bounds do not change any recorded timing or outcome and retain the original numerical solver qualification.

The next bounded work is an explicit, checked cache of physical pricing bounds, followed by the existing numerical restricted-master proposal to address rational-polishing stops. Fresh target-market pricing remains required before certification. These stronger baselines should precede broader timetable and retrieval/learning comparisons.

The analysis includes all 24 outcomes, paid preparation time, two figures, compact pricing traces and an independently checked bound note: https://github.com/ndandnd/egg/blob/b2b160046cd56dfcab87986b961011b0041d8345/research-20260928/feasible-pool-pilot/results-attempt1/README.md

The complete run took 36 minutes 49 seconds. Slurm allocated two CPUs despite the one-CPU request; the runner and solvers were configured for one native thread. The full original archive is preserved privately, and a curated public package contains the scientific inputs, witnesses and receipts. No new optimization was launched during this analysis.
