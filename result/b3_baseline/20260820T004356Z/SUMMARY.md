# B3 baseline: certified uplift intervals (20260820T004356Z)

**Label: RETROSPECTIVE / EXPLORATORY.** This analysis restates already-certified evidence from the committed B2 full population (no solver was run, no new experiment was launched); it inherits every caveat of `doc/MEASUREMENT_RESULTS.md`.

- analysis_code_commit: `a9db21f`
- baseline: one **A2** row per each of the 64 unique instances; A3-A5 used only as consistency witnesses (all witness intervals intersect the A2 interval; dictator evidence identical).
- certified interval per instance: `z_D - z_CH in [uplift_lo, uplift_hi]` with `uplift_lo = (z_d_ub - tol_d) - ub_ch` and `uplift_hi = z_d_ub - lb_best`, recomputed from the committed CSV fields.

## Overall (64 instances)

- uplift_lo: min -0.0100176, median 0.15225, max 12.9438
- uplift_hi: min 0, median 0.162657, max 12.9548
- interval width: median 0.0104515, max 0.0113417 (bounded by tol_d + epsilon = 0.02)
- instances with certified strictly positive uplift (uplift_lo > 0): 38 / 64
- instances contradicting z_D >= z_CH (uplift_hi < 0): 0 (must be 0)

## Strata (n_trips x b)

| stratum | instances | lo median | hi median | width median | positive lo |
|---|---|---|---|---|---|
| n8_b0.01 | 16 | -0.0097065 | 0.000985255 | 0.0104784 | 5 |
| n8_b0.05 | 16 | 0.306237 | 0.316781 | 0.0105919 | 10 |
| n12_b0.01 | 16 | 0.055011 | 0.0656138 | 0.010401 | 10 |
| n12_b0.05 | 16 | 3.5795 | 3.59006 | 0.0104167 | 13 |

## Caveats

- With tol_d = epsilon = 0.01 the certified intervals are up to 0.02 wide; `uplift_lo > 0` is the only certification of strictly positive uplift. Intervals containing 0 do NOT establish that uplift is absent — only that it is below the certification resolution.
- Small synthetic instances (n_trips 8/12, T=28); this baseline is a restatement, not a new measurement, and must not be quoted as a population estimate for larger fleets.
