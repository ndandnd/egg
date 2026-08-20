# B3 baseline: certified uplift intervals (20260820T011147Z)

**Label: RETROSPECTIVE / EXPLORATORY.** This analysis restates already-certified evidence from the committed B2 full population (no solver was run, no new experiment was launched); it inherits every caveat of `doc/MEASUREMENT_RESULTS.md`.

- analysis_code_commit: `a7f1f67709da72ff73a74b3db2c1386798557a35`
- baseline: one **A2** row per each of the 64 unique instances; A3-A5 used only as consistency witnesses.
- certified interval per instance: `z_D - z_CH in [uplift_lo, uplift_hi]` with `uplift_lo = (z_d_ub - tol_d) - ub_ch` and `uplift_hi = z_d_ub - lb_best`, recomputed from the committed CSV fields.
- historical rows with `mip_version == "unknown"`: 12 of 256 method-cells (declared in the B2 manifest; preserved and disclosed, not rejected).

## Overall (64 instances)

- classification: 38 strictly positive, 21 strict zero crossings, 5 exact-zero boundaries
- uplift_lo (raw): mean 1.5499, median 0.15225
- uplift_hi (raw): mean 1.56041, median 0.162657, max 12.9548
- interval width: median 0.0104515 (bounded by tol_d + epsilon = 0.02)
- per-trip interval medians: [0.0152482, 0.0161098]

## Cross-method audit (four-way intersection)

- nonempty four-way intersections: 64 / 64
- maximum cross-method endpoint spread: 0.00759389
- shared dictator evidence and metadata checks pass on every instance.

## Paired effects (interval subtraction; descriptive)

- feedback contrast (b=0.05 minus b=0.01, 32 pairs): 23 strictly positive, 1 strictly negative, 8 crosses-or-touches zero
- workload contrast (n=12 minus n=8, 32 pairs): 19 strictly positive, 6 strictly negative, 7 crosses-or-touches zero
- Stratum-level certification rates rise with n and b, but matched effects are heterogeneous and descriptive rather than causal.

## Strata (n_trips x b)

| stratum | instances | positive | crossing | boundary | lo median | hi median | width median |
|---|---|---|---|---|---|---|---|
| n8_b0.01 | 16 | 5 | 8 | 3 | -0.0097065 | 0.000985255 | 0.0104784 |
| n8_b0.05 | 16 | 10 | 5 | 1 | 0.306237 | 0.316781 | 0.0105919 |
| n12_b0.01 | 16 | 10 | 5 | 1 | 0.055011 | 0.0656138 | 0.010401 |
| n12_b0.05 | 16 | 13 | 3 | 0 | 3.5795 | 3.59006 | 0.0104167 |

## Scientific boundary

- All 64 instances are synthetic (seeded generators); none is observed operator data.
- Battery capacity and per-vehicle charging power are fixed constants of the instance generator.
- There is no shared charger-count or depot-capacity constraint; vehicles charge independently.
- There is no V2G: energy flows only from grid to vehicle.
- The affine duck-shaped price environment is a stylized demand curve, not a solar-generation model.
- n_trips is workload/problem size, not a controlled fleet-size variable.
- There is no distribution network and no locational charging; prices are system-wide per slot.
- This is the minimal default-physics uplift slice, not the full B3 atlas.
- The result establishes certified synthetic signal and heterogeneity, not external validity or manuscript-grade novelty.

## Caveats

- With tol_d = epsilon = 0.01 the certified intervals are up to 0.02 wide; `uplift_lo > 0` is the only certification of strictly positive uplift. Intervals containing 0 do NOT establish that uplift is absent — only that it is below the certification resolution.
- Uplift as a percentage of total integrated cost is deliberately NOT the primary normalization; per-trip bounds are reported instead.
