# Exact nonlinear enclosure for the ideal depot-15 model

The independently reviewed uniform-price certificate and rational feasible witness imply
`424.365880667204… ≤ CH ≤ D ≤ 512.7694256264009…`
for the declared 37-service, 30-hour ideal stored-input case and synthetic quadratic objective. `CH` is the full-fleet convexified optimum and `D` the physical optimum. Exact fractions and assumptions are in the [independent review](../research-20260927/agent-notes/exact-public-hull-bound-review/REVIEW.md). The interval does not identify either optimum or establish a positive gap.

The lower certificate uses the audited two-path energy relaxation, exclusion of a one-bus schedule, a separate floor for fleets of at least three, and a uniform-price Fenchel inequality. The upper value prices the independently admitted exact two-bus witness under the same stored nonlinear coefficients. Neither value comes from the failed nonlinear pilot.

The unchanged [candidate package](../result/sistig_exact_hull_bound/20260927-uniform-price1/MANIFEST.json) has manifest SHA-256 `e4729fcffca456729d7464861228f1f6530b572a3b352fe5abbd63ebd25ec30f`. The [independent review package](../research-20260927/agent-notes/exact-public-hull-bound-review/MANIFEST.json) has manifest SHA-256 `fc7ebbe2d1b5636a430855083b817bc3baf3373f68041ab599c2bc22318a8b19`. The lead checked all six entries against their sealed bytes.

For portable reproduction from a later checkout, use the independent `verify_uniform_bound.py --repo REPO --output NEW_REPORT.json`; it reads pinned v1 source blobs from Git. The archived author checker remains unchanged and requires an explicit `--repo` pointing to the original source checkout at `80eb69544f568a7ed346f0d603004a10f61c481a`. Its worktree pins are intentionally not rewritten for v2.

Scope remains the synthetic objective and finite block, not recurring daily operation, the solver's rounded matrix, depot16, or operational savings. The failed v1 pilot stays failed; the matched nonlinear study remains separate.
