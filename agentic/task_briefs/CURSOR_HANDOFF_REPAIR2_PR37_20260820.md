# Cursor handoff: PR #37 second repair round (third-review findings)

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` returns 403 for Cursor's GitHub App token by design; that is
not an authorization failure. Commit authorship comes from `git config`.)

No cluster commands. **Stay outcome-blind: never read, list, or hash anything
under `runs/b3_factor_pilot`, and never run the analyzer or selector on real
data.** The preregistered analysis has deliberately not been run yet. Keep the
PR draft.

## Task

Continue PR #37 in place on `cursor/b3-pilot-closeout-5fa0`, current head
`8144483eb292686477d0c24d2a12aa959e10a6f3`. Do not open another PR.

A third independent review confirmed the frozen decision rule is implemented
exactly, confirmed all four of your recorded disagreements are justified
(`os.link` no-replace, marker plus completion record, the replay limitation,
INVALID/HALT unpackable), and could not re-exploit two of the three prior
blockers. It found two things to fix.

### 1. MAJOR — the selector authorizes an analysis directory with no link to `runs/`

`load_analysis_artifact` establishes provenance only from a self-described
`analysis_code_verified` boolean, two public frozen constants (screen SHA, spec
SHA), and `analysis_code_commit` being any real ancestor of HEAD. The reviewer
emitted a **fully fabricated GO analysis directory with no run behind it** and
the selector authorized it and wrote `SELECTION.json`. The selector ignores
`raw_binding` entirely, so a swapped or forged analysis directory at freeze
time is undetected.

Repair, mirroring `package_b3_pilot._cross_bind`: the selector must re-derive
the raw tree's identity and require the analysis manifest's `raw_binding` to
match it — `raw_tree_sha256` via `canonical_tree_sha256(snapshot_source(...))`,
plus the Slurm job id and `JOB.json` hash. Take the runs directory as an
explicit required argument, refuse when `raw_binding` is absent or any field
disagrees, and name the disagreeing field in the refusal. A missing
`raw_binding` must fail closed, not pass.

Add the reviewer's forgery as a regression: a well-formed GO analysis
directory with no matching raw tree must be refused.

### 1b. MAJOR — `validate_raw_tree` rejects the documented audit report

`validate_raw_tree` requires `actual_files == expected_files` exactly. The
project's own documented audit invocation writes its report **into** the raw
tree:

```bash
python experiments/audit_b3_factor_pilot.py \
    --runs runs/b3_factor_pilot --out runs/b3_factor_pilot/AUDIT.md
```

The operator has run exactly that, so the live tree now holds a root-level
`AUDIT.md` and the packager would refuse it with
`unexpected=['AUDIT.md']`. The raw tree must not be mutated to satisfy code
(the project rule is to preserve raw runs), so fix the code: accept a
root-level `AUDIT.md` as an **optional, explicitly named** member of the
expected file set. Do not introduce a wildcard or a "tolerate unknown files"
path — the exact-population check is the point; only this one documented
filename becomes optional.

Add tests both ways: a tree with `AUDIT.md` validates, a tree with any other
unexpected root file still refuses by name, and a tree missing a required cell
file still refuses.

### 1c. Bind to the captured pre-analysis anchor

The operator captured the raw-tree identity **before** running the analysis,
while still outcome-blind, using `canonical_tree_sha256(snapshot_source(...))`
from `experiments/package_a6_holdout.py`:

```text
tree_sha256:     efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4
file_count:      363
directory_count: 60
total_bytes:     17385781
```

That is 60 cell directories x 6 cell files = 360, plus `JOB.json`,
`MANIFEST.json`, and the `AUDIT.md` above.

Record these four values as named constants in the analyzer or a small frozen
constants module, and have the analyzer's `raw_binding` and the selector's new
binding check compare against them in addition to recomputing the digest live.
A live-recomputed digest that no longer matches the anchor must refuse and say
so — that is the signal that something wrote into the tree after the audit.

Note in the spec that future audit re-runs must direct `--out` **outside** the
raw tree so the anchor stays stable.

### 2. Emit a boundary-margin diagnostic (do this now, while outcome-blind)

The reviewer observed that a true median of exactly `0.04` is not
IEEE-754-representable, so a real result infinitesimally near the threshold
can fall on either side of `abs(median) <= 0.04` depending on accumulation
order. The comparison itself is spec-faithful and **must not change** — do not
touch the rule, the thresholds, or the operators.

Instead add a pure disclosure field, computed and emitted for the selected
factor in both `DECISION.json` and `SELECTION.json`:

- `boundary_margin = abs(median) - 0.04` at full precision;
- `boundary_adjacent = abs(boundary_margin) < 1e-9` (a reported boolean, with
  the threshold recorded as a constant in the artifact);
- the signed median itself emitted at full `repr()` precision.

`boundary_adjacent` must not alter the decision state. It exists so that a
knife-edge result is visibly a knife-edge to any human or downstream tool
rather than silently resolving one way. Document in the spec and in
`SELECTION.json` that a `boundary_adjacent` decision requires human review
before it authorizes anything.

This is legitimate to add only because no one has seen the outcome yet. Note
that fact in the commit message.

### 3. Document what the certificate actually attests

The reviewer's central conclusion is that the analyzer proves the recorded
event logs are internally consistent and reproduce the stored summary, but
cannot prove they reflect real solver runs: a fully self-consistent co-edit of
a cell's `z_rmp_model`, `duals_sigma`, `min_reduced_cost_lb`, `lb_ch`,
`lb_best`, and histories — leaving the pricing oracle's `solver.bound`
untouched — is accepted by the replay, and it moves `U_hi = z_D_ub - lb_best`
and therefore the decision.

Do not attempt to close this by re-solving MIPs in the analyzer. Instead:

- state the limitation explicitly in `doc/B3_FACTOR_PILOT_SPEC_DRAFT.md` (or a
  clearly linked note), in the analyzer module docstring, and as a field in
  `SELECTION.json` recording that decision integrity rests on the provenance
  of `runs/b3_factor_pilot` because certificates are **replayed, not
  re-solved**;
- record in the same place that the operator captured an independent
  pre-analysis raw-tree digest (see below), and require the selector's
  `raw_binding` check to compare against it.

### 4. Optional, only if 1-3 are done and tests pass

Add an opt-in `--verify-rmp` mode to the analyzer that re-solves each cell's
final restricted master **as an LP over the stored, replay-validated column
pool** and requires the recovered `z_rmp_model` and convexity dual to agree
with the recorded values within the module's declared tolerance. This closes
most of the co-edit surface at LP cost without any MIP re-solve. It must be
off by default, and the mode used must be recorded in the artifact. Do not
change any default behavior.

## Tests and verification

Adversarial synthetic fixtures only. Merge current `origin/main` into the
branch so CI reports on the PR, and report CI-measured counts rather than
local ones.

## Report

Ordered commits, CI-measured test counts, the exact refusal messages for the
new selector binding check, the emitted boundary-diagnostic fields, and
confirmation that no rule, threshold, or comparison operator was changed and
no pilot outcome was read. Leave the PR draft.
