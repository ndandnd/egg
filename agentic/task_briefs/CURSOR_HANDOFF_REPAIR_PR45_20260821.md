# Cursor handoff: PR #45 repair — three criticals block any launch

Date: 2026-08-21 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` returns 403 for Cursor's GitHub App token by design; that is not
an authorization failure. Commit authorship comes from `git config`.)

No cluster commands. No launching. Never read, list, or hash anything under
`runs/b3_factor_pilot`. Keep the PR draft.

## Context: why this is strict

Continue PR #45 in place on `cursor/b3-confirmation-driver-eea3`, head
`da2cdb6`. Do not open another PR.

This driver spends **seeds 32-37, a one-shot scientific resource.** They are
the only reserved fresh-seed range for the B3 confirmation; if they are
consumed on an invalid design or a forged authorization, the confirmation
cannot be re-run and the flagship result loses its confirmatory arm
permanently. Every finding below is therefore treated as blocking, including
the ones labelled High.

An independent adversarial review found six defects. Its passing controls
should be preserved exactly: the Python loader unconditionally refuses
`boundary_adjacent == true`; the frozen raw-tree values are literal constants
never recomputed from the pilot tree; the population is exactly seeds
{32-37} x n{8,12} x b{0.01,0.05} x {S0, selected} = 48 cells / 24 contrasts;
and every CLI mode routes through `load_selection_artifact`.

## CRITICAL 1 — fabricated, uncommitted selection artifacts pass as GO

`b3_confirmation.py:248-259,324-331` validates JSON contents and
self-declared ancestor SHAs but never proves the artifact bytes are **tracked
and committed** at `selection_code_commit`. The reviewer passed an uncommitted
artifact carrying invented 64-hex pilot hashes, `count=999`,
`direction_sign=true`, non-finite boundary values, and no `campaign` or
`baseline_level`, and it was accepted. No genuine GO evidence is required.

Repair: require the artifact to be a committed, tracked object. Resolve the
declared `selection_code_commit`, confirm it is an ancestor of HEAD, and
require the artifact's bytes to equal the blob at its declared repository path
in that commit (`git cat-file` / `git show <commit>:<path>` equivalence on
exact bytes, not a re-serialized comparison). Refuse when the path is
untracked, the blob differs, or the commit does not resolve. Tests that need
synthetic artifacts must commit them into a throwaway temporary repository
rather than relaxing the check.

## CRITICAL 2 — launcher environment hooks bypass the whole gate

`launch_b3_confirmation.sh:42-48` permits production overrides including
`EGG_PILOT`, and `EGG_LAUNCH_SELFTEST` disables safety guards (`:67-82`). A
replacement pilot command can report dry-run, manifest, list, and bind success
without doing any of it, so **even `boundary_adjacent == true` is bypassable at
launcher level** despite the Python loader correctly refusing it. The launcher
also never confirms `MANIFEST.json` and `JOB.json` exist before releasing the
hold (`:103-135`).

Repair: the tool overrides may exist only when `EGG_LAUNCH_SELFTEST` is set,
and `EGG_LAUNCH_SELFTEST` itself must be refused whenever `sbatch` is a real
executable on `PATH` — i.e. it can never be honored on a cluster login node.
In production the launcher must invoke the real driver by its literal path with
no indirection. Before `scontrol release`, assert on disk that `MANIFEST.json`
and `JOB.json` both exist, that `JOB.json` names the exact job id just
submitted, and that the run manifest SHA recorded in `JOB.json` matches the
manifest file's hash. Any failure cancels the held job and never releases it.

## CRITICAL 3 — an unbound array can become runnable

Four separate holes:

- `bind_job_id` uses a non-atomic exists-then-replace sequence
  (`b3_confirmation.py:592-609`); two concurrent launchers can both bind and
  release, leaving one surviving `JOB.json`.
- The worker never reads `JOB.json` nor compares it against
  `SLURM_ARRAY_JOB_ID` (`submit_b3_confirmation.sub:43-45`,
  `run_b3_confirmation.py:267-290`).
- `submit_b3_confirmation.sub` is directly submittable and runnable without
  `--hold`.
- **`EGG_RUN_OUT` controls launcher binding while the worker hardcodes
  `runs/b3_confirmation`** — the identical defect that exists in
  `submit_b3_factor_pilot.sub` and that is being fixed separately on
  `cursor/b3-submit-out-fix`. Do not reproduce it here.

Repair: make binding atomic and exclusive — create `JOB.json` with `O_EXCL`
(or `os.link` from a temp file, matching the selector's publication pattern) so
a second concurrent bind fails rather than overwriting. Make the worker
self-defending: on entry it must read `JOB.json`, require
`SLURM_ARRAY_JOB_ID` to equal the bound job id, require the run manifest SHA
to match, and exit nonzero without writing anything when they disagree — so a
directly submitted or stale array cannot produce evidence. Thread the output
directory through the `.sub` (`--out "${EGG_RUN_OUT:-runs/b3_confirmation}"`
with the launcher exporting it explicitly via
`sbatch --export="ALL,EGG_RUN_OUT=..."`), and add a shell-level test that
executes the `.sub` with a stub interpreter and asserts the recorded argv
targets the overridden path.

## HIGH 4 — the mandatory fresh-grid structural screen is missing

`doc/B3_FACTOR_PILOT_SPEC_DRAFT.md:569-575` requires reapplying the
generator-only structural screen to the fresh instances and halting as
`DESIGN-NOT-FROZEN` if any fresh instance fails. The code only constructs and
hashes instances (`b3_confirmation.py:196-208,455-473`). Without this,
**seeds 32-37 can be spent before an invalid frozen design is detected** —
the exact irrecoverable loss this whole gate exists to prevent.

Repair: run the screen over all fresh instances before any submission, refuse
with state `DESIGN-NOT-FROZEN` on any failure, and record the screen outcome
(per-instance pass/fail plus the screen artifact SHA) in the run manifest. Add
a test with a deliberately infeasible fresh instance proving the launcher
refuses and submits nothing.

## HIGH 5 — field-presence and type validation is incomplete

Missing `campaign` and `baseline_level` pass; `direction_sign=true` is accepted
as `+1`; counts above the possible 12 pilot cells pass; and `NaN`/`Infinity`
pass for `boundary_margin` and `signed_median_full_precision`. The other 16
top-level fields refuse correctly.

Repair: require `campaign` and `baseline_level`; reject `bool` where an integer
sign is expected (in Python `True` is an `int`, so check
`type(x) is bool` and refuse explicitly); require
`0 <= count <= 12`; require every numeric field to be finite via
`math.isfinite`. One named refusal per field, one test per case.

## HIGH 6 — the post-run audit does not require the GO artifact

`audit_b3_confirmation.py:109-118` makes selection validation optional, so an
internally consistent run tree audits clean without proving its manifest came
from a genuine GO selection.

Repair: make selection validation mandatory in the audit — the run manifest
must reference a selection artifact that revalidates under the same rules as
the driver's gate, including the committed-bytes check from Critical 1.

## Verification

Adversarial synthetic fixtures only; tests must pass on CBC. Merge current
`origin/main` into the branch so CI reports, and quote CI-measured counts.
Re-run the reviewer's forgeries as committed regressions: the uncommitted
fabricated artifact, the `EGG_PILOT` substitution, the concurrent double bind,
the directly submitted array, the infeasible fresh instance, the boolean
`direction_sign`, the non-finite boundary fields, and the audit without a
selection artifact.

## Report

Ordered commits, CI-measured test counts, the exact refusal message for each
of the six findings, and confirmation that no pilot outcome was read and
nothing was launched. Leave the PR draft; it needs another independent review
before it may ever launch.
