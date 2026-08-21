# Cursor handoff: B3 certified uplift baseline from existing B2 evidence

Date: 2026-08-19 (America/New_York)

This is an independent, no-solver research-analysis task. It may run in
parallel with PR #28 only in a separate Cursor workspace/branch. Read this file
completely before changing anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `92c38a64bed6735eddb2f79dd292d8af9e244559`, unless main has advanced through
  a reviewed merge; if it has, inspect the advancement and use the new clean
  main without importing work from PR #28 manually.
- Create a new branch such as `cursor/b3-baseline-closeout-5fa0`.
- Open one new draft PR for this B3 task. Do not add these changes to PR #28.
- Do not read, import, list, hash, summarize, or touch `src/runs/a6_holdout`,
  any A6 transfer bundle, `result/a6_holdout`, or A6 analysis claims.
- Do not launch Slurm, Gurobi, CBC, or any new experiment.
- Use only the already committed canonical B2 population described below.
- Do not modify A2/A6 algorithms, experiment drivers, instance generators,
  market code, or existing committed result artifacts.

## Research objective

Close the lowest-hanging B3 result already present in certified evidence:

> quantify the schedule-column convexification gap `z_D - z_CH` as a certified
> internal-uplift interval across the existing default-physics B2 population.

This is the B3 settlement/indivisibility object. It is NOT the compact vehicle
MILP root-LP gap, solver MIP gap, price-taking loss, or an A6 performance
metric.

The analysis is explicitly retrospective/exploratory. The outcomes have
already been seen during research triage; do not call it preregistered or
confirmatory. A future untouched-seed factor experiment will supply
confirmation if warranted.

## Canonical input

Use exactly:

```text
result/b2_full/20260818T140356Z/cells.csv
```

Current committed structure, which the analyzer must validate rather than
blindly assume:

- 256 total rows;
- methods exactly `{a2, a3, a4, a5}`;
- 64 unique `(seed, n_trips, b)` instances;
- seeds `0..15`;
- `n_trips` in `{8, 12}`;
- `b` in `{0.01, 0.05}`;
- exactly one row per method and instance;
- shared `z_d_ub` and `tol_d` must agree exactly across methods;
- method-specific certified uplift intervals need not have identical endpoints,
  but their intersection must be nonempty for each instance.

Select the A2 row as the canonical B3 interval because A2 is the simplest
successful certificate producer. The other methods are consistency witnesses,
not additional observations; never count the same instance four times.

## Required specification-first protocol

Commit the analysis specification and code/tests before committing generated
scientific artifacts.

Recommended two-commit sequence:

1. `Specify and implement B3 baseline uplift analysis`
2. `Add deterministic B3 baseline artifacts`

The generated manifest must record the exact first commit as
`analysis_code_commit`, plus the input path, SHA-256, row count, and input
schema. Artifact regeneration with the same explicit stamp and commit must be
byte-identical.

## Required files

At minimum:

```text
doc/B3_UPLIFT_BASELINE_SPEC.md
src/experiments/analyze_b3_baseline.py
src/tests/test_b3_baseline_analysis.py
result/b3_baseline/<stamp>/MANIFEST.json
result/b3_baseline/<stamp>/instance_uplift.csv
result/b3_baseline/<stamp>/strata_summary.csv
result/b3_baseline/<stamp>/paired_effects.csv
result/b3_baseline/<stamp>/cross_method_audit.csv
result/b3_baseline/<stamp>/SUMMARY.md
```

Two compact deterministic figures are useful if they materially clarify the
result, for example certified uplift by `(n,b)` and the positive-lower-bound
rate. Do not add decorative figures or a large plotting framework.

## Required row-level validation

For every row, recompute and validate the stored certified interval from the
primitive columns:

```text
uplift_lo = (z_d_ub - tol_d) - ub_ch
uplift_hi = z_d_ub - lb_best
```

Require, at evidence precision:

- all required numeric fields finite;
- `uplift_lo <= uplift_hi`;
- stored and recomputed endpoints agree;
- `certified` and `outcome` are compatible with the B2 protocol;
- source commit/backend/solver metadata are present and internally consistent;
- no missing, duplicate, or unexpected method-instance cell;
- exact shared dictator evidence across methods;
- nonempty intersection of the four method-specific certified intervals.

Retain the raw lower endpoint, including small negative values caused by
certificate width. A theorem-tightened presentation interval may additionally
report `max(0, uplift_lo)`, but it must never overwrite or hide the raw value.

## Required outputs and metrics

### `instance_uplift.csv`

Exactly 64 rows, ordered deterministically by seed, `n_trips`, then `b`.
Include at least:

- seed, `n_trips`, `b`;
- A2 raw lower and upper endpoints;
- theorem-tightened lower endpoint;
- interval width;
- classification: strictly positive / crosses zero / exactly zero boundary;
- lower and upper uplift per trip;
- `z_d_ub`, `tol_d`, A2 `lb_best`, and A2 `ub_ch`;
- the four-method intersection endpoints and maximum cross-method endpoint
  spread as audit fields.

Do not make percentage of total integrated cost the primary normalization:
fixed vehicle cost dominates that denominator. If reported, label it secondary
and explain the limitation.

### `strata_summary.csv`

For each `(n_trips,b)` stratum and the overall sample, report:

- number of unique instances;
- count/share with raw lower endpoint strictly above zero;
- count/share crossing zero;
- median and mean raw lower/upper endpoints;
- median interval width;
- maximum upper endpoint;
- median per-trip interval.

### `paired_effects.csv`

Use interval arithmetic, not midpoint subtraction. Report:

1. Within each `(seed,n_trips)`, the `b=0.05` minus `b=0.01` contrast:
   `[lo_high - hi_low, hi_high - lo_low]`.
2. Within each `(seed,b)`, the `n=12` minus `n=8` contrast using the same rule.

Summarize how many paired contrast intervals are strictly positive, strictly
negative, or cross zero. These are descriptive paired effects, not causal
estimates from a randomized design.

### `cross_method_audit.csv`

One row per unique instance. Include each method's interval, the four-way
intersection, endpoint spreads, shared dictator-evidence checks, and a pass
flag. It is an audit table, not four independent samples.

### `SUMMARY.md`

Lead with the honest descriptive ledger and exact denominator. State the
synthetic/default-physics boundary prominently.

The current triage values may be used only as expected smoke checks, not as
hard-coded outputs:

- 38 of 64 A2 intervals have a strictly positive raw lower bound;
- overall median raw interval is approximately `[0.1523, 0.1627]`;
- at `n=12, b=0.05`, the median is approximately `[3.5795, 3.5901]`, with
  13 of 16 strictly positive;
- at `n=8, b=0.01`, the median interval crosses zero.

If the independently generated results disagree materially, stop and diagnose;
do not force the expected values.

## Claim boundaries that must appear in spec and summary

- All 64 instances are synthetic.
- Battery capacity and per-vehicle charge power are fixed in this slice.
- There is no shared charger-count/depot-capacity constraint.
- There is no V2G.
- The affine/duck-shaped price environment is not a solar-generation model.
- `n_trips` is workload/problem size, not controlled fleet size.
- There is no distribution network or locational charging.
- This is a minimal default-physics uplift slice, not the full B3 atlas from
  the brainstorm.
- It establishes certified synthetic signal and heterogeneity, not external
  validity or manuscript-grade novelty by itself.

## Required adversarial tests

Use miniature committed-style CSV fixtures. Cover at least:

- missing A2 row;
- duplicate method-instance row;
- unexpected method, seed, `n_trips`, or `b`;
- dictator bound/tolerance mismatch across methods;
- stored uplift endpoint tamper;
- reversed interval;
- nonoverlapping method intervals;
- NaN/infinity/string numeric field;
- incomplete population presented as complete;
- method rows mistakenly counted as independent instances;
- interval-difference arithmetic on known examples;
- deterministic ordering and byte-identical regeneration;
- input SHA or analysis-code-commit mismatch;
- refusal to read or write any A6 path.

The tests must assert emitted CSV/JSON contents, not inspect source strings.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_b3_baseline_analysis.py -q
python3 -m pytest tests/ -q
git diff --check
```

Run the analyzer twice with the same explicit stamp and commit into two clean
temporary output roots and prove every emitted byte matches. Then generate the
committed artifact once using the first implementation commit.

Final report must include:

- branch, PR URL, and exact commits;
- test counts and deterministic-regeneration result;
- exact canonical input SHA-256 and validated population dimensions;
- artifact path and inventory;
- principal descriptive results with exact denominators;
- all claim limitations above;
- confirmation that no solver or cluster job ran and no A6 path was accessed.

Do not merge. Return the draft PR for independent Codex review.

## What comes after this task

Do not implement the B3 factor pilot here. After this baseline PR is reviewed,
the intended development pilot is a separately frozen 32-cell design on burned
development seeds `{0,11}` across workload, battery, per-vehicle power, and
market slope, preceded by an outcome-blind feasibility census. Untouched seeds
`32..47` are reserved for a later confirmatory factorial only if the pilot and
specification pass review.
