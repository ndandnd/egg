## Analytical benchmark integrated — 28 September 2026

The reviewed public energy-floor calculation is now available as an optional reporting baseline. It reproduces the four original and changed-market bounds without solving again, verifies the complete physical case and reviewed proof records, and rejects unsupported markets.

All 32 archived native result rows remain unchanged. Exact ideal-model lower bounds are shown separately; combinations with numerical upper witnesses are explicitly conditional on ideal-model feasibility. Missing or conflicting evidence stays unavailable. This strengthens the benchmark for future computations without changing historical statuses, timings or the manuscript. The public optimality gaps still include zero, and there is no new speedup or learning claim.

Sol implemented the change, Luna independently reviewed it, and the final ten focused tests and curated replay passed. The implementation is backed up on the existing draft branch. No optimization or cluster allocation was used.

Next is a bounded diagnostic design for pricing-call and arithmetic stopping limits before another comparative run. The pending replacement-run decision remains separate; independent timetable evaluation and common-quality comparisons still precede machine learning.

[Implementation and scope](https://github.com/ndandnd/egg/tree/88daef8482aadd27bcf7605c4aced765fbffb205/research-20260928/analytic-baseline-integration)

[Independent review](https://github.com/ndandnd/egg/blob/88daef8482aadd27bcf7605c4aced765fbffb205/research-20260928/analytic-baseline-integration/INDEPENDENT_REVIEW.md)
