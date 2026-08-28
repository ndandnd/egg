# B31 switch-boundary corpus builder (solver-free, commit 1: code/spec/tests)

Status: specification for the deterministic, solver-free B31 corpus
builder. This PR commits the builder, this specification, and the test
battery ONLY; no real corpus artifacts are generated or committed here
(fixtures exercise the output path in tests). No model is fitted and no
scientific claim is made.

## Objective

Reconstruct, from the committed Phase-2 fine-boundary evidence, a
machine-learning-ready corpus of ADJACENT-INTERVAL observations for the
B31 direction (boundary/column learning): for every pair of adjacent
sweep grid points, what changed — nothing (at hash resolution), a
degenerate tie, a charging-only response, a duty change, or a fleet
change — and with what certified margins. The corpus separates
predictive features from outcomes and defines a leakage-safe split.

## Canonical input (never modified; pinned)

- `result/boundary_fine/20260816T180507Z/checkpoints/*/sweep.ckpt.json`
  (64 sweeps), combined digest pinned to
  `b9807ab8f8b50094e5bd4ebceb507b87eabd1c546372fb54d35906e8420ba4a1`
  using the established recipe (sorted checkpoint relpaths; per file,
  update SHA-256 with the relpath bytes then the lowercase hex SHA-256
  of the file bytes — identical to `analyze_closeout.checkpoints_digest`
  and to the digest recorded by the committed
  `result/analysis/20260816T190835Z/MANIFEST.json`).
- Grid: seeds 0-7 x n_trips {8, 12} x sweep slots {8, 12, 16, 20};
  deltas -1.50 .. +1.50 in steps of 0.01 (301 points per sweep).
- The digest is recomputed BEFORE parsing and again AFTER
  reconstruction; any difference is input mutation and aborts.

## Exact totals (fail-closed gates on the canonical input)

| quantity | value |
| --- | --- |
| sweeps | 64 |
| points | 19,264 |
| adjacent intervals | 19,200 |
| stable at hash resolution | 16,460 |
| degenerate ties | 2,559 |
| margin ties (duty changes tied at the boundary) | 89 |
| economic charging-only | 35 |
| economic duty changes | 57 |
| economic fleet changes | 0 |

(2,740 non-stable intervals = 2,559 degenerate + 35 charging-only +
146 duty changes + 0 fleet changes; 89 of the 146 duty changes are
margin ties, leaving 57 economic duty changes.)

## Solver-free reconstruction (replicated producer semantics)

The builder imports NO solver, EVSP, or boundary module (no `egglab`,
`mip`, `gurobipy`, `numpy`, `pandas`, `matplotlib`); a subprocess
regression enforces the import closure. It replicates, in stdlib
Python, and RE-VERIFIES against the committed evidence:

- `schedule_hash`: SHA-256 of the JSON of the sorted duty sequences,
  first 12 hex characters (producer `Solution.schedule_hash`);
- `load_hash`: SHA-256 of the JSON of the per-slot load rounded to two
  decimals with negative zero normalized (producer `Solution.load_hash`
  with `_norm(x, 2)`);
- `classify_pair`: identical thresholds (`LOAD_TOL_KWH = 1.0`) and
  precedence (fleet_change > degenerate_tie > duty_change >
  charging_only), with the L1 load jump recomputed by sequential
  summation and validated against the stored `load_l1` within 1e-9;
- margin-tie logic: `tie_margin == (min(margins) <= MARGIN_TOL = 1e-3)`
  recomputed from the stored cross-realization margins.

Every stored switch record must align one-to-one, in order, with the
recomputed non-stable adjacent pairs; stored `counts_by_kind`,
`n_switches`, and `n_economic_switches` must equal the recomputation;
`done` and `margins_done` must be true on all 64 checkpoints.

## Evidence limits (preserved verbatim in the emitted manifest and schema)

1. "Stable" means stability at HASH RESOLUTION: equal schedule hash and
   equal two-decimal load hash. It is not a proof that the two optima
   are identical below two-decimal load resolution.
2. Charging-only changes NEVER received the margin test: the producer
   ran cross-realization margins only for duty and fleet changes, so
   economic charging-only counts carry no margin certification.
3. Exactly one degenerate row does not change the route partition
   (`schedule_changed == false`): a two-decimal load-hash flip with an
   unchanged duty partition. All other degenerate rows flip the
   schedule hash.
4. Tiny negative margins down to solver noise are allowed: the
   committed minimum is about -4.5e-13; validation admits margins
   >= -1e-9 and rejects anything more negative.

## Corpus outputs (`result/b31_corpus/<stamp>/`; fixtures only in this PR)

| file | contents |
| --- | --- |
| `sweeps.csv` | 64 rows: sweep identity (seed, n_trips, slot), split, point/interval counts, per-kind counts, margin ties, economic count |
| `intervals.csv` | 19,200 rows: sweep identity + split, interval identity (`idx_left`, `delta_left`, `delta_right`), FEATURES (left endpoint + exogenous only), OUTCOMES (stability, kind, schedule_changed, fleet_change, load_l1, load_jump_slot, tie_margin, economic flag, margins) |
| `feature_schema.json` | the explicit feature/outcome split, the leakage rule, and the evidence limits |
| `SPLIT_MANIFEST.json` | whole-seed split: train seeds 0-4, validation seed 5, test seeds 6-7; per-split sweep ids and interval counts |
| `MANIFEST.json` | schema, stamp, full-SHA `analysis_code_commit`, pinned input digest and top-level file hashes, exact totals, evidence limits, CSV headers, output hashes |

### Features versus outcomes (leakage rule)

Features may derive ONLY from the LEFT endpoint of the interval and
exogenous design variables: `seed`, `n_trips`, `slot`, `idx_left`,
`delta_left`, `delta_right` (exogenous grid geometry), `left_obj`,
`left_fleet`, `left_load_slot`, `left_energy_total`,
`left_schedule_hash`, `left_load_hash`. RIGHT-ENDPOINT solution values
are outcomes-only; a builder-level guard and a regression forbid any
feature column carrying right-endpoint information. Outcomes:
`stable`, `kind`, `schedule_changed`, `fleet_change`, `load_l1`,
`load_jump_slot`, `tie_margin`, `economic`, `margin_b_at_a`,
`margin_a_at_b`.

### Split (leakage-safe)

Whole-seed assignment — every sweep and interval of a seed belongs to
exactly one split: train = seeds 0-4 (40 sweeps), validation = seed 5
(8 sweeps), test = seeds 6-7 (16 sweeps). No interval, sweep, or seed
appears in two splits.

## Hygiene and provenance

- Fail-closed validation everywhere: pinned digest, grid geometry
  (301 points, idx 0..300, delta = -1.5 + 0.01*idx within 1e-9), exact
  totals, switch alignment, margin bounds, checkpoint completion flags.
- Atomic no-overwrite publication: refuse an existing output directory,
  stage into a temporary sibling, rename into place; failures remove
  only the files this run wrote.
- Deterministic bytes: sorted rows, `repr` floats, LF-only CSVs, JSON
  with sorted keys, no wall-clock content beyond the caller-supplied
  stamp; regeneration is byte-identical.
- `--validate-only`: a READ-ONLY integration gate against the canonical
  input — full reconstruction and every gate, no file created, no
  commit verification required.
- Build provenance: `--analysis-code-commit` must be the full
  40-character SHA that resolves, is an ancestor of (or equal to) HEAD,
  with the builder, this specification, and the test battery
  byte-identical to it; the frozen base
  `740ab0c1578b454268102c0bb15b1104d9ac8d9d` must be an ANCESTOR of
  HEAD (not necessarily equal); tracked dirtiness refuses.
- The production CLI is pinned to the canonical input; alternate inputs
  exist only as test-injection parameters used by the fixture battery.

## Non-goals of this PR

- No real corpus generation or artifact commit (that is the next,
  separately reviewed step).
- No model fitting, no learning-curve or accuracy claims, no scientific
  interpretation beyond the counted evidence above.
- No solver, cluster, or A6 access.
