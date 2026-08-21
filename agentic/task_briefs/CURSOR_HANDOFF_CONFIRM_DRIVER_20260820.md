# Cursor handoff: B3 confirmation driver (outcome-blind, GO-gated)

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` is unusable here: Cursor agents authenticate with a GitHub App
integration token, which cannot call `/user` and always returns 403. That is
not an authorization failure. Commit authorship comes from `git config`, not
from the push credential.) Do not push if the remote check or dry-run fails.

No cluster commands. No launching. No seeds outside the frozen confirmation
set. Keep the PR draft.

## Outcome blindness is mandatory

The 60-cell pilot population is complete and its hardened audit has PASSED.
The preregistered analysis has **not** been run. You must not read, list,
hash, or summarize anything under `runs/b3_factor_pilot`, and you must not
attempt to infer which factor setting will be selected. Build everything
parameterized on the selected factor as an input value.

## Task

Branch from current `origin/main` (`ed8b06f3d7e8e4a7ecc5fbfd74ff0b819ac24fa4`)
as `cursor/b3-confirmation-driver`. Open one draft PR.

Build the fresh-seed B3 confirmation driver and its guarded launcher, mirroring
the existing pilot machinery rather than inventing new patterns. Read first:
`src/experiments/b3_factor_pilot.py`, `run_b3_factor_pilot.py`,
`audit_b3_factor_pilot.py`, the launcher under `src/cluster/`, and
`doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`.

### The frozen confirmation population

```text
seeds: {32, 33, 34, 35, 36, 37}
settings: S0_baseline versus the SELECTED factor only (input, not hardcoded)
n_trips: {8, 12}
b: {0.01, 0.05}
matched contrasts: 24
method-cells: 48
epsilon = 0.01, tol_d = 0.01, budget = 240
Gurobi only (EGGLAB_REQUIRE_GRB=1 on the cluster)
gate: >= 18/24 direction-consistent zero-excluding AND signed median > 0.04
```

The selected factor's frozen direction sign comes from the pilot spec table
(`S1_batt_low` non-negative, `S2_batt_high` non-positive, `S3_pow_low`
non-negative, `S4_pow_high` non-positive) and must be read from the frozen
artifact, not re-derived.

### The GO gate is structural, not advisory

The driver and the launcher must **refuse to run** unless handed a committed
GO selection artifact that validates:

- the artifact's own hashes recompute;
- its decision state is exactly `GO`;
- the selected factor named in it is the factor being run;
- the analyzer commit it names resolves to a real commit that is an ancestor
  of the current HEAD;
- the frozen screen SHA is `27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603`
  and the pilot spec hash matches the frozen constant;
- the selection artifact is not itself INVALID/HALT-derived.

Any failure is a hard refusal naming the field. There must be no flag,
environment variable, or test hook that bypasses this in a real run; if tests
need to construct a synthetic GO artifact, they must build a complete
internally-consistent fake one, not disable the gate.

Note in the PR description that this deviates from the letter of the project
rule "only a committed GO authorizes confirmation implementation" by building
the implementation before the decision exists, and argue why the structural
gate preserves the rule's intent. Do not hide the deviation.

### Bindings and provenance

Every cell binds, exactly as the pilot does: run commit, run-manifest SHA
computed over exact bytes, instance hash, market hash, solver identity, Slurm
lineage, cell identity, plus the selection-artifact SHA. Reuse the pilot's
held-submit launcher pattern: submit held, atomically bind `JOB.json` to the
run manifest, then release; bind or release failure cancels the exact held job.
Concurrency cap 12.

### Also deliver

- an audit script for the confirmation population (48 cells, 24 contrasts),
  built on the hardened pilot audit's checks rather than a weaker copy;
- adversarial tests only, using synthetic fixtures: missing/duplicate cells,
  wrong seed set, wrong settings pair, tampered selection artifact (each
  validated field, one test each), non-GO artifact, INVALID/HALT-derived
  artifact, budget overrun, identity mismatch, deterministic cell ordering,
  refusal to read `runs/b3_factor_pilot`, and refusal to launch anything.

Tests must pass on CBC (the repository's CI is CBC-only; do not set
`EGGLAB_REQUIRE_GRB` in tests) and must assert emitted values, not source
strings. Merge current `origin/main` into your branch before finishing so CI
reports on the PR.

## Report

Branch, draft PR URL, ordered commits, CI-measured test counts (not
self-reported), the exact refusal behavior of the GO gate, and confirmation
that no pilot outcome was read and nothing was launched. Leave the PR draft.
