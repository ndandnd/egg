# Cursor handoff: ML training-data emission driver (engineering tier)

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` cannot be used here: Cursor agents authenticate with a GitHub
App integration token that GitHub forbids from calling `/user`, so it always
returns 403. That is not an authorization failure; commit authorship comes
from `git config`.) Do not push if the remote check or dry-run fails.

No cluster commands, no launching, no reading of `runs/b3_factor_pilot` or any
A6 path, no `result/` writes, no decision-log or research-status edits. Tests
must pass on CBC; do not set `EGGLAB_REQUIRE_GRB`. Keep the PR draft.

## Purpose and evidence tier

This produces **engineering-tier training data**, never scientific evidence.
Its only consumer is a future machine-learning experiment whose exact oracle
remains the sole certifier. Say so in the module docstring and the spec.

The target: warm-starting the certified column-generation negotiation across
the price-feedback loop, which is textbook parametric reoptimization (same
instance, shifting prices). The literature that this mirrors reports ~2x
speedups to a *certified* gap using predicted duals as a stabilization center.
Every candidate ML target — dual prediction, pricing-network reduction,
pricing-value regression — is trainable from the same solve logs, so the
logging schema is the real deliverable, not the instance count.

## Hard constraint: seed namespace

Every existing seed range is committed to a scientific population: 0-15 burned
by the B2/B3 populations, 16-31 the A6 holdout, 32-37 the frozen B3
confirmation, 38-47 reserved. **This driver must generate exclusively from
seeds >= 10000** and must refuse, with a named error, any requested seed below
10000. Add a test for that refusal. Contaminating a reserved range would
destroy a future confirmation experiment.

## Task

Branch from current `origin/main` (`ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4`)
as `cursor/ml-data-driver`. Open one draft PR.

Deliver:

```text
doc/ML_WARMSTART_DATA_SPEC.md
src/experiments/emit_cg_training_data.py
src/tests/test_cg_training_data.py
```

### Per-solve emission schema (the actual deliverable)

For each generated instance, run the existing certified pipeline
(`egglab.b2a2.certified_cg`, plus `regimes.solve_dictator` where cheap) and
emit one JSONL record per solve carrying at minimum:

- identity: instance hash, market hash, seed, `n_trips`, `b`, battery kWh,
  charge kW, epsilon, `tol_d`, budget, solver identity, code commit,
  schema version;
- the full posted price vector and its hash;
- **per master iteration**: the restricted-master duals, the convexity dual,
  the master objective, the incumbent upper bound, the certified lower bound,
  and the pricing problem's dual bound and incumbent;
- **per accepted column**: `column_key`, load vector, ops cost, reduced cost
  at acceptance, and the replay-validity flag;
- the final certificate: `ub_ch`, `lb_best`, gap, certified flag, oracle-call
  counts (clean and total);
- the dictator certificate where computed.

Two label-quality requirements, both load-bearing and both drawn from the
published methods:

1. **Canonicalize the duals.** Raw last-iterate simplex duals are the noisiest
   possible label because the dual optimum is typically a face, not a point.
   Emit a canonical representative — a barrier/interior solution without
   crossover if the backend exposes one, otherwise the average of duals over
   several optimal-face samples — and record which method produced it in the
   record. Never emit only the last simplex iterate.
2. **Emit margins, not just argmins.** For each accepted column also record
   the separation between it and the next-best alternative where available, so
   downstream training can apply margin filtering. This is the direct answer
   to the project's own measurement that degenerate tie changes outnumbered
   economically meaningful switches 2,559 to 92.

### Driver shape

Follow the repository's existing `run_*.py` conventions exactly (argparse with
parser named `ap`, hyphenated flags with snake_case dest, `--list`, `--cell K`,
`--all`, `--out` defaulting under `runs/`, `ap.error(...)` when no mode is
given). Add:

- a stratified grid over `n_trips` in `{8, 10, 12, 16}`, `b` in
  `{0.0, 0.01, 0.05}`, battery and charge-power levels reusing the frozen B3
  screen levels, and seeds from a `--seed-base` (>= 10000) plus `--count`;
- **a per-cell wall-clock cap** (`--time-limit-s`, default conservative) so a
  tranche cannot run unbounded, and a record marking any cell that hit it as
  incomplete rather than silently truncated;
- atomic checkpointing via `egglab.checkpoint` so a tranche resumes;
- a `--dry-run` that prints the exact cell list and estimated size without
  solving.

Sizing note for whoever launches it: the 60-cell B3 pilot consumed about 5.1
CPU-hours total with a 1h44m worst cell. A first tranche should be bounded to
land inside a known window — order 1,000-2,000 instances at `n_trips <= 16`,
not an open-ended campaign — and the launcher must respect that.

### Tests (adversarial, synthetic, CBC)

Seed below 10000 refused by name; emitted records re-verified from primitives
in the test (recompute reduced costs from load/ops_cost/duals; recompute the
certificate gap); dual canonicalization method recorded and consistent;
per-iteration count matches the checkpoint's oracle-call count; wall-clock cap
marks incomplete rather than truncating; resume produces byte-identical
records; deterministic ordering; refusal to write outside the supplied output
directory; no default path under `result/` or `runs/b3_factor_pilot`; no A6
path reachable.

Merge current `origin/main` into your branch before finishing so CI reports.

## Report

Branch, draft PR URL, ordered commits, CI-measured test counts, the final
JSONL schema (field list), the dual-canonicalization method chosen and why,
and the `--dry-run` output for a 1,000-instance tranche with its estimated
CPU-hours. Leave the PR draft; launch nothing.
