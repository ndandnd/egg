# B3 baseline: no-solver certified-uplift analysis (retrospective / exploratory)

Status: specification for the deterministic, solver-free B3 baseline
analyzer. This document is committed together with the analyzer and its
tests (commit 1 of the two-commit protocol); the generated artifacts under
`result/b3_baseline/<stamp>/` follow in a second commit whose manifest
names commit 1 as `analysis_code_commit`.

## Objective

Produce the certified interval for the convex-hull uplift
\(z_D - z_{CH}\) on the completed B2 population, without running any
solver, cluster job, or new experiment. This is a **retrospective,
exploratory** baseline: it reuses already-certified evidence and makes no
new scientific claims beyond restating certified bounds, deduplicated to
one baseline row per unique instance.

## Canonical input (never modified)

- `result/b2_full/20260818T140356Z/cells.csv` — the certified 256-row
  full-population table (4 methods x 64 instances).
- `result/b2_full/20260818T140356Z/MANIFEST.json` — its manifest; the
  analyzer recomputes the SHA-256 of `cells.csv` and requires equality
  with the manifest's recorded output hash before reading a single row.

The B2 population's `analysis_code_commit`
(`71d4c378768a7c3a882a2236e9c2ce92d98e8b23`) is copied into the B3
manifest as input provenance.

## Population validation (all gates abort the run)

1. Exactly 256 rows; required columns present.
2. Methods exactly `{a2, a3, a4, a5}`; keys `(method, seed, n_trips, b)`
   unique; the instance set is exactly the frozen 64-instance grid
   seeds 0-15 x n_trips {8, 12} x b {0.01, 0.05}.
3. Every row: `outcome == certified`, `certified == True`,
   `epsilon == 0.01`, `tol_d == 0.01`, all numeric fields finite.

## Uplift recomputation

For every row the analyzer recomputes, from the serialized fields only:

```
uplift_lo = (z_d_ub - tol_d) - ub_ch
uplift_hi = z_d_ub - lb_best
```

Certified-interval semantics: `z_d_ub` is a dictator upper bound proved
within `tol_d` (so `z_D >= z_d_ub - tol_d`), `ub_ch >= z_CH >= lb_best`.
Therefore \(z_D - z_{CH} \in [\mathrm{uplift\_lo}, \mathrm{uplift\_hi}]\).

### Serialization tolerance

`cells.csv` serializes floats to 12 significant digits, so recomputed
values differ from the recorded `uplift_lo`/`uplift_hi` columns by up to
a few 1e-9 at the population's magnitudes (measured maximum deviation
9.6e-9). The analyzer requires

```
|recorded - recomputed| <= SERIALIZATION_TOL = 5e-8
```

for both columns of every row, then reports the **recomputed** values so
the entire artifact regenerates from the committed CSV alone.

Additional per-row sanity: `uplift_hi >= uplift_lo` (interval width is
`ub_ch - lb_best + tol_d > 0`), width `<= tol_d + epsilon +
SERIALIZATION_TOL`, and `uplift_hi >= -SERIALIZATION_TOL` (a negative
upper bound would contradict `z_D >= z_CH`).

## Baseline and witnesses

- **Baseline rows: A2 only, once per each of the 64 unique instances.**
  A2 is the plain certified column-generation method; its interval is the
  baseline measurement.
- **A3-A5 are consistency witnesses only.** They never contribute
  baseline rows. Per instance the analyzer requires:
  - `z_d_ub` and `tol_d` numerically identical across all four methods
    (the dictator stage is shared evidence);
  - every witness interval intersects the A2 interval (all four certify
    the same quantity, so disjoint intervals would prove an inconsistency
    in the committed population).

## Outputs (`result/b3_baseline/<stamp>/`)

| file | contents |
| --- | --- |
| `uplift_baseline.csv` | 64 A2 rows: seed, n_trips, b, ub_ch, lb_best, z_d_ub, tol_d, recomputed uplift_lo/uplift_hi, width, positive_uplift_certified (`uplift_lo > 0`) |
| `witness_consistency.csv` | 192 rows (64 instances x A3/A4/A5): witness interval, A2 interval, intersection flag, z_d_ub equality flag |
| `strata_summary.csv` | overall + four `n x b` strata: count, min/median/max of uplift_lo, uplift_hi, width; counts of positive-lo and negative-hi rows |
| `SUMMARY.md` | labeled retrospective/exploratory; key numbers and caveats |
| `MANIFEST.json` | schema, stamp, analysis_code_commit, input paths + SHA-256 hashes (cells.csv and the B2 manifest), B2 `analysis_code_commit`, tolerances, population counts, output hashes |

## Determinism and hygiene

- Stdlib only (`csv`, `json`, `hashlib`, `statistics`, ...): no egglab
  import, no python-mip, no Gurobi/CBC, no numpy/pandas/matplotlib. A
  regression asserts the module's import closure contains no solver or
  numerical stack.
- Byte-identical regeneration for a fixed `--stamp`: rows sorted, floats
  emitted with `repr`, JSON with sorted keys, no wall-clock content.
- The analyzer refuses an existing output directory, stages into a
  temporary sibling, and renames into place.
- `--analysis-code-commit` is verified against `HEAD` and a clean tree
  (disable flags exist for tests only).
- No A6 path is read and no committed input is modified.

## Interpretation caveats (stated in every SUMMARY)

- With `tol_d = epsilon = 0.01`, intervals have width up to 0.02;
  `uplift_lo > 0` is the only certification of strictly positive uplift.
- The population is small synthetic instances (n_trips 8/12); this is a
  baseline restatement, not a new measurement, and carries the
  full-population caveats of `doc/MEASUREMENT_RESULTS.md`.
