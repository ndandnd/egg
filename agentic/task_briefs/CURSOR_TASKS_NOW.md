# Cursor tasks to hand out right now — 2026-08-21

Five tasks. Each block between the `>>>` and `<<<` markers is **self-contained**:
select the whole block, paste, done. Nothing needs combining.

| # | Give it to | Task | Why it matters |
| --- | --- | --- | --- |
| 1 | **egg** (the one whose branches end `-5fa0`; it wrote the B3 closeout) | Repair the closeout: real `run_commit`, freeze-before-score | The B3 decision freeze waits on this |
| 2 | **the remote/cloud one** (branches end `-eea3`; it wrote the confirmation driver) | Repair the confirmation driver: 3 criticals, 3 highs | Protects one-shot seeds 32–37 |
| 3 | **whoever did `cursor/b3-submit-out-fix`** | Harden the submit path: rc=0 bypass, worker binding | Blocks any replication |
| 4 | **2cycle** (or any agent that has never touched A6) | A6 recovery preflight — produce, do not execute | Converts existing compute into a scoreable result |
| 5 | **branch and price** (or any idle agent) | Write and freeze the replication comparator | No replication may launch without it |

Reviews come later and must go to an agent that did **not** write the code:
when task 1 returns, give its review to **uplift** or **proposer**; when task 2
returns, give its review to **giro loader** or **2cycle**.

To print one block in your terminal instead of scrolling:
`awk '/^>>> TASK 1/,/^<<< TASK 1/' CURSOR_TASKS_NOW.md`

---

>>> TASK 1 — paste to: egg (branches end -5fa0)

Continue the B3 pilot closeout PR in place from exact head
`0af91df3658b5d7cf2dcce21d05689178db63d9b` on `cursor/b3-pilot-closeout-5fa0`.
No new PR, no rebase, no force-push. Keep it draft.

Access gate (`gh api user` returns 403 for Cursor's GitHub App token by design —
that is expected, not an authorization failure; commit authorship comes from
`git config`):

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

Stay outcome-blind: never read, list, or hash anything under
`runs/b3_factor_pilot`. The preregistered analysis has deliberately not been run
yet so that reviews of this code stay blind. No cluster commands.

An independent fifth review found two remaining blockers. Fix both without
changing any threshold, comparison operator, ordering, or decision semantics —
those must stay byte-for-byte identical.

1. `MANIFEST.run_commit` is accepted on shape alone (40 hex characters). Require
   it to resolve to a real commit object in the repository and to be an ancestor
   of the analysis commit / current HEAD. Replace the `"a"*40` test fixtures with
   real temporary Git commits, or an explicitly injected test verifier.
   Production must never accept a shape-only hash.

2. The analyzer audits and scores the **live** runs tree before freezing the
   immutable snapshot it later binds, so a transient mutate → score → restore
   sequence could score bytes other than the anchored population. Instead:
   freeze the live tree **once** using the reviewed regular-file-only
   `freeze_source` machinery; verify that frozen copy against
   `FROZEN_RAW_ANCHOR`; run audit, population load, replay and scoring against
   only that immutable copy; derive `raw_binding` from those exact bytes; and
   re-verify the live source is unchanged after scoring and before publication.

Add regressions for: an unresolved commit; a real but unrelated commit;
mutation before the freeze; mutation between freeze and scoring; mutation after
scoring but before publication; and proof that audit and scoring never read the
live tree once the freeze has happened.

Merge current `origin/main` into the branch so CI reports, and quote
CI-measured counts rather than local ones. Report the ordered commits, the exact
refusal message for each new check, and confirmation that no rule or threshold
moved. Leave it draft for a different independent reviewer.

<<< TASK 1

---

>>> TASK 2 — paste to: the remote/cloud one (branches end -eea3)

Continue the B3 confirmation driver PR in place on
`cursor/b3-confirmation-driver-eea3`, head `da2cdb6`. No new PR, no rebase, no
force-push. Keep it draft.

Access gate (`gh api user` 403 is expected for Cursor's GitHub App token and is
not an authorization failure; authorship comes from `git config`):

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

Stay outcome-blind: never read, list, or hash anything under
`runs/b3_factor_pilot`. No cluster commands. No launching.

Why this is strict: this driver spends seeds 32–37, the only reserved fresh-seed
range for the B3 confirmation. If they are consumed on an invalid design or a
forged authorization, the confirmation cannot be re-run and the flagship result
loses its confirmatory arm permanently. Every finding below is blocking.

Preserve the controls that already pass: the Python loader unconditionally
refuses `boundary_adjacent == true`; the frozen raw-tree values are literal
constants never recomputed from the pilot tree; the population is exactly seeds
{32–37} × n{8,12} × b{0.01,0.05} × {S0, selected} = 48 cells / 24 contrasts; and
every CLI mode routes through the selection loader.

CRITICAL 1 — fabricated, **uncommitted** selection artifacts pass as GO. The
gate validates JSON contents and self-declared ancestor SHAs but never proves
the artifact bytes are tracked and committed at the declared
`selection_code_commit`. An artifact with invented 64-hex hashes, `count=999`,
`direction_sign=true`, non-finite boundary values and missing required fields
was accepted. Require the artifact to be a committed, tracked object: resolve
the declared commit, confirm ancestry, and require the artifact's exact bytes to
equal the blob at its declared path in that commit. Tests needing synthetic
artifacts must commit them into a throwaway temporary repository rather than
relaxing the check.

CRITICAL 2 — launcher environment hooks bypass the whole gate. Production
permits an `EGG_PILOT` override and `EGG_LAUNCH_SELFTEST` disables guards, so a
substitute command can report dry-run, manifest, list and bind success without
doing any of it — meaning even `boundary_adjacent == true` is bypassable at
launcher level. The launcher also never confirms `MANIFEST.json` and `JOB.json`
exist before releasing the hold. Permit tool overrides only when
`EGG_LAUNCH_SELFTEST` is set, and refuse `EGG_LAUNCH_SELFTEST` itself whenever
`sbatch` is a real executable on `PATH`, so it can never be honored on a login
node. Before release, assert both files exist, that `JOB.json` names the exact
job id just submitted, and that the manifest SHA it records matches the manifest
file's hash. Any failure cancels the held job and never releases it.

CRITICAL 3 — an unbound array can become runnable: binding uses a non-atomic
exists-then-replace sequence so two concurrent launchers can both bind and
release; the worker never reads `JOB.json` nor compares it against
`SLURM_ARRAY_JOB_ID`; the submit file is directly submittable without `--hold`;
and `EGG_RUN_OUT` controls launcher binding while the worker hardcodes its
output path. Make binding atomic and exclusive (`O_EXCL` or link-no-replace).
Make the worker self-defending: on entry it reads `JOB.json`, requires
`SLURM_ARRAY_JOB_ID` and the manifest SHA and the run commit to match, and exits
nonzero writing nothing when they disagree. Thread the output directory through
the submit file with the launcher exporting it explicitly, and reject output
paths containing commas or control characters, absolute paths, symlinks, and
anything outside the runs directory.

HIGH 4 — the spec-mandated fresh-grid structural screen is missing. The frozen
spec requires reapplying the generator-only screen to the fresh instances and
halting as `DESIGN-NOT-FROZEN` on any fresh-instance failure; the code only
constructs and hashes instances. Without it, seeds 32–37 can be spent before an
invalid design is detected. Run the screen before any submission, refuse with
`DESIGN-NOT-FROZEN`, record per-instance outcomes and the screen artifact SHA in
the run manifest, and test that a deliberately infeasible fresh instance causes
a refusal with nothing submitted.

HIGH 5 — validation gaps: missing `campaign` and `baseline_level` pass;
`direction_sign=true` is accepted as `+1`; counts above the possible 12 pass;
`NaN`/`Infinity` pass for the boundary fields. Require both missing fields;
reject `bool` where an integer sign is expected (in Python `True` is an `int`,
so test `type(x) is bool` and refuse); require `0 <= count <= 12`; require every
numeric field to satisfy `math.isfinite`. One named refusal and one test each.

HIGH 6 — the post-run audit makes selection validation optional, so an
internally consistent run tree audits clean without proving it came from a
genuine GO. Make selection validation mandatory in the audit, including the
committed-bytes check from Critical 1.

Re-run every listed exploit as a committed regression. Tests must pass on CBC.
Merge current `origin/main` so CI reports; quote CI-measured counts. Leave the PR
draft — it needs another independent review before it may ever launch.

<<< TASK 2

---

>>> TASK 3 — paste to: whoever produced branch `cursor/b3-submit-out-fix`

Continue that PR in place at head `ef951273`. No new PR, no rebase, no
force-push. Keep it draft. No cluster commands. Never read, list, or hash
anything under `runs/b3_factor_pilot`.

Access gate (`gh api user` 403 is expected for Cursor's GitHub App token;
authorship comes from `git config`):

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

Keep the `EGG_RUN_OUT` correction exactly as it is — it is correct and its four
tests were shown to fail against the unfixed scripts. Two of the issues below
are new to this change; two are pre-existing properties of the pipeline that
also applied to the canonical pilot run. Fix all four, but say which is which in
the PR description so the scope is honest.

New to this change:

1. `EGG_PYTHON=/usr/bin/true` with `EGG_ENV_SCRIPT=/dev/null` makes the real
   submit script exit 0 while producing no evidence — a silently "successful"
   array that computes nothing. Honor those two overrides **only** when `sbatch`
   is absent from `PATH` (that is, off-cluster). On a real cluster they must be
   refused, not ignored.
2. The resolved run directory is interpolated into Slurm's comma-delimited
   `--export` grammar unvalidated. Reject any output path containing a comma or
   control character, and reject absolute paths, symlinks, and anything
   resolving outside the runs directory.

Pre-existing, and worth fixing here since you are in this code:

3. Workers never authenticate `JOB.json` against `SLURM_ARRAY_JOB_ID`. Make the
   worker read the binding on entry and require the job id, the manifest SHA and
   the run commit to match, exiting nonzero and writing nothing when they do not.
4. The submit file is directly submittable and runnable without going through
   the guarded launcher. Refuse execution that did not come from a bound,
   released launch — detect it before invoking Python.

Also bind `JOB.json` exclusively (`O_EXCL` or link-no-replace) and re-read and
authenticate the manifest and job binding immediately before `scontrol release`.

Add a regression for the rc=0/no-evidence exploit specifically: it must now fail
loudly. Merge current `origin/main` so CI reports; quote CI-measured counts.
Leave the PR draft.

<<< TASK 3

---

>>> TASK 4 — paste to: 2cycle (or any agent that has never touched A6)

Read-only assignment. Produce a plan; execute nothing. No commits, no branch, no
PR, no cluster commands, no `sbatch`, no `ssh`. Do not inspect or infer any
scientific outcome.

From current `origin/main`, read: `src/experiments/package_a6_holdout.py` (in
particular the second-stage `recover2-pack` path), `doc/ENGINEERING_INCIDENTS.md`
(especially EI-026 and EI-027), `doc/UNICORN_RUNBOOK.md`,
`doc/A6_SPARSE_STABILIZATION_SPEC.md`, the A6 tests, and both existing claim
files referenced by the incident ledger.

Deliver exactly two things:

1. One **read-only preflight** command block the operator can run on the cluster
   that verifies every precondition and changes nothing.
2. One **exact operator command** for the one-shot recovery — the real command
   from the merged code, not an invented one.

Both must pin and check: the original claim SHA-256
`1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675`; the first
recovery claim SHA-256
`88c22f06cc6bc8dcff56c0d6737c91bbd39fe8da79c2b6ba6d2a987b6b6abe88`; the source
tree digest; the EI-027 failure fingerprint; reviewed-commit ancestry; Slurm
quiescence; the absence of an existing second-stage recovery artifact; and the
absence of an already-published package prefix.

Hard constraints: there is no third recovery stage — do not design one. Do not
invent a command or a flag that does not exist in the merged code; if the path
you find cannot do what is needed, say so and stop. Wrap every cluster block in
a subshell `( ... )` so a failure cannot close the operator's login session, and
never put a top-level `set -e` into an interactive shell.

Report: the exact two blocks, the file and line for each precondition you check,
anything the merged code cannot verify, and an explicit statement of what
happens if the recovery fails midway.

<<< TASK 4

---

>>> TASK 5 — paste to: branch and price (or any idle agent)

Write and freeze the comparator for a pilot replication, as a specification plus
a deterministic checker. No cluster commands. Never read, list, or hash anything
under `runs/b3_factor_pilot` — this must be written before any replication
exists, and it must be written blind.

Access gate (`gh api user` 403 is expected; authorship comes from `git config`):

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

Branch from current `origin/main` as `cursor/replication-comparator`. One draft
PR.

Context: the 60-cell B3 factor pilot completed and passed its audit. A
replication of the same 60 cells into a separate output directory is planned as
a verification-tier check on whether the pipeline reproduces its own
certificates — because the analyzer replays recorded evidence rather than
re-solving it. Right now "certified intervals agree within tolerance" exists
only as prose, which means a disagreement could be rationalized after it is
seen. Your job is to remove that freedom **before** any replication runs.

Deliver `doc/B3_REPLICATION_COMPARATOR_SPEC.md` plus
`src/experiments/compare_b3_replication.py` and adversarial tests. The spec must
freeze, as committed constants:

- which cells are compared (all 60, matched by cell identity, and what happens
  if a cell is missing on either side);
- which fields are compared: at minimum `lb_best`, `ub_ch`, both raw endpoints
  of the uplift interval, the dictator bounds, and the certification flag;
- the tolerance for each field, whether it is absolute or operand-scaled, and
  the justification — note that the project's physical replay tolerance is
  `1e-4` kWh and the CG epsilon is `1e-2`, and a comparator whose tolerance is
  tighter than the machinery's own noise floor is not meaningful;
- what counts as agreement: state a required count (for example 60/60) rather
  than a vague majority, and state it before any data exists;
- what a single disagreeing cell triggers — an engineering incident to
  investigate, never a choice of which run to score;
- the explicit rule that **the original run remains canonical regardless of the
  outcome**, and that the replication may never be substituted for it;
- that run manifests and `run_commit` values are *expected* to differ between
  the two runs, so provenance fields are excluded from the comparison while
  solve-path equivalence is asserted separately.

The checker must be deterministic, emit a machine-readable verdict, refuse to
run if either side is an incomplete population, and never write into either
input directory. Tests: hand-computable fixtures for pass, one-cell fail,
missing cell, extra cell, reversed interval, non-finite field, and a
byte-identical regeneration check.

Merge current `origin/main` so CI reports; quote CI-measured counts. Leave the
PR draft.

<<< TASK 5
