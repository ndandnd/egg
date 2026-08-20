# B3 baseline: no-solver certified-uplift analysis (retrospective / exploratory)

Status: specification for the deterministic, solver-free B3 baseline
analyzer. This document is committed together with the analyzer and its
tests; the generated artifacts under `result/b3_baseline/<stamp>/` follow
in a second commit whose manifest names the correction commit's **full
40-character SHA** as `analysis_code_commit`.

## Objective

Produce the certified interval for the convex-hull uplift
\(z_D - z_{CH}\) on the completed B2 population, without running any
solver, cluster job, or new experiment. This is a **retrospective,
exploratory** baseline: it reuses already-certified evidence and makes no
new scientific claims beyond restating certified bounds, deduplicated to
one A2 baseline row per unique instance.

## Canonical input (never modified; pinned by hash)

- `result/b2_full/20260818T140356Z/cells.csv`, pinned SHA-256
  `45f946e4fabb42f01157666bd00df27c1c582b3e1d767c59ae53c25a4b6e80c6`.
- `result/b2_full/20260818T140356Z/MANIFEST.json`, pinned SHA-256
  `d9546f4e3e040a7dec5a1b0a397753602a9e505147435994b09f384cd4c37742`,
  schema `b2-full-population-v1`, `analysis_code_verified == true`.

Manifests record these **repository-relative** paths; the pinned hashes
make the identity independent of the absolute checkout root. The
production CLI is pinned to this input; alternate inputs exist only as
test-injection parameters. The analyzer refuses, before reading or
writing anything, any input or output path containing an A6 segment.

## Population validation (all gates abort the run)

1. Both pinned hashes match; the B2 manifest's own recorded `cells.csv`
   hash matches; schema and code-verification flags are as pinned.
2. Exactly 256 rows; required columns present; the exact CSV header and
   row count are recorded in the B3 manifest.
3. Methods exactly `{a2, a3, a4, a5}`; keys unique; the instance set is
   exactly seeds 0-15 x n_trips {8, 12} x b {0.01, 0.05}.
4. Every row: `outcome == certified`, `certified == True`,
   `epsilon == 0.01`, `tol_d == 0.01`, `budget == 240`; `backend` and
   `mip_version` must belong to the B2 manifest's solver declarations and
   `source_commit` to its `experiment_commits`. Historical rows with
   `mip_version == "unknown"` are declared in the B2 manifest, so they
   are **preserved and disclosed** (count reported in the manifest and
   SUMMARY), never silently rejected or hidden.

## Uplift recomputation

For every row the analyzer recomputes, from the serialized fields only:

```
uplift_lo = (z_d_ub - tol_d) - ub_ch
uplift_hi = z_d_ub - lb_best
```

Certified-interval semantics: `z_d_ub` is a dictator upper bound proved
within `tol_d` (so `z_D >= z_d_ub - tol_d`), `ub_ch >= z_CH >= lb_best`.
Therefore \(z_D - z_{CH} \in [\mathrm{uplift\_lo}, \mathrm{uplift\_hi}]\).

`cells.csv` serializes floats to 12 significant digits, so recomputed
values differ from the recorded `uplift_lo`/`uplift_hi` columns by up to
a few 1e-9 at the population's magnitudes (measured maximum deviation
9.6e-9). The analyzer requires `|recorded - recomputed| <=
SERIALIZATION_TOL = 5e-8` for both columns of every row, then reports
the **recomputed** values. Per-row sanity: `uplift_hi >= uplift_lo`,
width `<= tol_d + epsilon + SERIALIZATION_TOL`, and `uplift_hi >=
-SERIALIZATION_TOL`.

## Baseline, cross-method audit, classification

- **Baseline rows: A2 only, once per each of the 64 unique instances.**
- **Four-way intersection invariant.** Pairwise overlap with A2 does not
  imply a common intersection, so for every instance the analyzer
  computes

```
intersection_lo = max(lo_a2, lo_a3, lo_a4, lo_a5)
intersection_hi = min(hi_a2, hi_a3, hi_a4, hi_a5)
```

  and requires `intersection_lo <= intersection_hi`. All four methods
  certify the same quantity, so an empty four-way intersection proves an
  inconsistency in the committed population.
- Shared dictator evidence: `z_d_ub` and `tol_d` numerically identical
  across all four methods per instance; metadata (`epsilon`) equal.
- **Classification** (exhaustive; anything else aborts):
  - `strictly-positive`: `uplift_lo > 0`;
  - `exact-zero-boundary`: `uplift_hi == 0` exactly (the serialized
    evidence has `z_d_ub == lb_best`; the certified interval is
    `[-tol_d, 0]`);
  - `strict-zero-crossing`: `uplift_lo < 0 < uplift_hi`.
- The theorem \(z_D \ge z_{CH}\) tightens the lower bound to
  `max(0, uplift_lo)`; the raw value is always disclosed alongside.

## Paired effects (interval subtraction; descriptive)

Certified difference intervals on the A2 baseline:

- **feedback contrast** (32 pairs): within each `(seed, n_trips)`,
  b = 0.05 minus b = 0.01: `[lo_high - hi_low, hi_high - lo_low]`;
- **workload contrast** (32 pairs): within each `(seed, b)`,
  n = 12 minus n = 8, same rule.

Classification: `strictly-positive` (`diff_lo > 0`), `strictly-negative`
(`diff_hi < 0`), else `crosses-or-touches-zero`. Interpretation rule:
stratum-level certification rates rise with n and b, but matched effects
are heterogeneous and **descriptive rather than causal**.

## Outputs (`result/b3_baseline/<stamp>/`)

| file | contents |
| --- | --- |
| `instance_uplift.csv` | exactly 64 A2 rows: identity, `z_d_ub`, `tol_d`, `lb_best`, `ub_ch`, raw `uplift_lo/hi`, theorem-tightened lower bound, width, classification, per-trip lower/upper bounds, four-way intersection endpoints, endpoint spreads |
| `cross_method_audit.csv` | exactly 64 rows: all four intervals, four-way intersection, lower/upper/max endpoint spreads, shared-dictator and metadata checks, final pass flag |
| `paired_effects.csv` | exactly 64 matched contrasts (32 feedback + 32 workload), deterministic ordering, certified difference intervals and classification |
| `strata_summary.csv` | overall + four `n x b` strata: counts and shares by classification, mean and median raw endpoints, median width, maximum upper endpoint, median per-trip lower/upper bounds |
| `SUMMARY.md` | labeled retrospective/exploratory; headline counts, four-way audit statistics, paired-effect families, complete scientific boundary |
| `MANIFEST.json` | schema, stamp, full-SHA `analysis_code_commit`, repository-relative pinned inputs with hashes, exact CSV header and row count, unknown-mip disclosure, tolerances, scientific boundary, output hashes |

Uplift as a percentage of total integrated cost is deliberately **not**
the primary normalization; per-trip bounds are reported instead.

## Scientific boundary (stated in the spec and in every emitted SUMMARY)

- All 64 instances are synthetic.
- Battery capacity and per-vehicle charging power are fixed.
- There is no shared charger-count/depot-capacity constraint.
- There is no V2G.
- The affine duck-shaped price environment is not a solar-generation
  model.
- `n_trips` is workload/problem size, not controlled fleet size.
- There is no distribution network or locational charging.
- This is the minimal default-physics uplift slice, not the full B3
  atlas.
- This establishes certified synthetic signal and heterogeneity, not
  external validity or manuscript-grade novelty.

## Provenance and portable determinism

- `--analysis-code-commit` must be the **full 40-character SHA** of the
  correction commit; it must resolve, be an ancestor of (or equal to)
  HEAD, and the analyzer, this specification, and the test battery in
  the working tree must be **byte-identical** to that commit. Tracked
  dirtiness refuses. Regeneration therefore succeeds from the artifact
  descendant commit while still naming the correction commit.
- Stdlib only; a regression asserts the import closure contains no
  solver or numerical stack.
- All CSVs are written with `lineterminator="\n"` (no CRLF).
- Byte-identical regeneration for a fixed `--stamp` across different
  absolute checkout and output roots, including `MANIFEST.json`
  (repository-relative input paths; no wall-clock content).
- The analyzer refuses an existing output directory and never modifies
  the committed input.
