# Dispatch round 2 — 2026-08-21

| # | Give to | Job |
| --- | --- | --- |
| 1 | **GPT** | 4th review of PR #37 at `2981ba4` |
| 2 | **remote/cloud agent** (`-eea3`, wrote #45) | Repair #45's 4 blockers + 1 major |
| 3 | **2cycle** | Harden PR #47, now with #45's launcher/worker lessons |
| 4 | **branch and price** | Write and freeze the replication comparator |

Each block below is self-contained. `gh api user` returns 403 for Cursor's
GitHub App token by design — that is expected, not an authorization failure;
commit authorship comes from `git config`. Preflight for the write jobs:

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

---

>>> JOB 1 — GPT: fourth review of PR #37

You have reviewed this twice (at 376f130 and db0a894) and requested changes
both times. Re-review at head 2981ba4, branch cursor/b3-pilot-closeout-5fa0,
diff range 0af91df..2981ba4. CI is green on this branch.

Review only: no commits, no pushes, no PR comments. Stay outcome-blind —
never read, list, or hash anything under runs/b3_factor_pilot; the analysis
has deliberately not been run and the decision is not frozen. No cluster
commands.

WHAT CHANGED SINCE db0a894, all in response to you:

1. Your audit-sidecar BLOCKER. The frozen inventory is now threaded into
   audit() itself: the run manifest, all 60 cell-identity sidecars and all
   120 checkpoints are digest-checked in the same read that parses them, and
   membership in the inventory is required. ATTACK: find any file the audit
   or the replay still consumes without an expected digest. The author
   already swept for this once and missed the sidecars, so assume another
   read site exists — check _validate_manifest, market-hash extraction, the
   screen loader, anything reached through bp.*, and the packager/selector
   read paths.

2. Your bare-git BLOCKER. The author's first attempt hardened only the
   analyzer; a self-directed sweep then found 6 more bare-git sites in the
   selector and 7 in the packager. There is now ONE runner in
   b3_pilot_evidence (trusted_git/git_argv/git_env/assert_no_history_rewrites)
   used by all three modules, and zero bare-git invocations remain in the B3
   path. ATTACK: the trusted path is /usr/bin:/bin only and the executable
   must be a non-symlinked, non-group/world-writable regular file — try to
   defeat that; try GIT_CONFIG_COUNT/GIT_CONFIG_KEY, core.fsmonitor,
   aliases, includeIf, and a repository-local .git/config; and check whether
   any OTHER module on the decision path (b3_factor_pilot.py itself,
   analyze_b3_baseline.py) still shells a bare git in a way that matters.

3. Your replace-ref BLOCKER. Every provenance query passes
   --no-replace-objects with GIT_NO_REPLACE_OBJECTS=1, and the analyzer,
   selector and packager each fail closed when replacement refs or a legacy
   graft file exist. ATTACK: refs/replace created after the check, a graft
   file created mid-run, replace refs in a worktree vs the common dir.

4. Your unenforced-flag MAJOR. run_commit_verified is now required by both
   the selector and the packager, placed beside the other raw-provenance
   checks so an incomplete or non-frozen artifact is still refused for the
   more informative reason. It now records that verification actually ran
   rather than inferring it from the invocation mode. ATTACK: can a
   seam-derived artifact still reach a bundle or an authorization by any
   route — the importer, the confirmation driver, a re-analysis?

5. Your broad-except MINOR. Partially addressed: the audit call still
   catches AttributeError/TypeError/IndexError. Say whether you consider
   that acceptable now or still want programmer errors to propagate.

ALSO NOTE a design change you should judge: enforcing the flag broke 48
fixtures, which the author read as evidence that the test seam itself was
wrong. Synthetic run manifests now carry a REAL commit (HEAD), so production
run_commit resolution runs against the fixtures and the seam is exercised
only by the tests that are about the seam. Decide whether that is sound or
whether it makes the fixtures depend on repository state in a fragile way.

ASSUME A FOURTH GAP EXISTS. Three reviews have each found a real defect,
twice in a fix the author was confident in. Do not accept the framing above.

Run tests from src/: python -m pytest tests/ -q.

DELIVERABLE: per finding, severity, file:line, the exact probe and its
output, and a concrete failure scenario. State which of your prior findings
are now closed. End with a verdict: is 2981ba4 safe to merge and then use to
generate and freeze a one-shot flagship decision?

<<< JOB 1

---

>>> JOB 2 — remote/cloud agent: repair PR #45

Continue PR #45 in place on cursor/b3-confirmation-driver-eea3, head
d872e78. No new PR, no rebase, no force-push. Keep it draft. No cluster
commands, nothing launched, and never read/list/hash anything under
runs/b3_factor_pilot.

An independent review re-exploited four of your six repairs and found one
new major. Seeds 32-37 are a one-shot resource, so all five are blocking.

BLOCKER A — unverified pilot provenance still authorizes confirmation
(b3_confirmation.py:397-422). The gate never checks
pilot.run_commit_verified; a committed selection carrying
run_commit_verified: false was accepted. PR #37 now records that flag and
its selector/packager refuse when it is false. Require it here too:
refuse unless the selection artifact's analysis recorded
run_commit_verified == true.

BLOCKER B — self-test hooks still reach release
(launch_b3_confirmation.sh:59-75,117-182). Your guard checks only
`command -v sbatch`, so EGG_LAUNCH_SELFTEST=1 plus an absolute EGG_SBATCH
outside PATH released a real array with a fake pilot. Probe output:
`path_sbatch=<none> returncode=0 events=['SBATCH','RELEASE'] released=True`.
Refuse the hooks whenever ANY plausible scheduler is reachable — not just
one on PATH: check EGG_SBATCH itself, the common absolute locations, and
SLURM_* variables in the environment. A safer inversion: require an explicit
positive marker that the hooks are permitted (a file only the test harness
creates under a temp dir) rather than trying to detect a real cluster.

BLOCKER C — worker authorization is forgeable
(b3_confirmation.py:783-806, submit_b3_confirmation.sub:39-50).
SLURM_ARRAY_JOB_ID is ordinary caller-controlled environment state, so a
direct .sub run with a copied JOB.json and spoofed variables authorized
itself. EGG_RUN_OUT also accepted absolute, "..", symlinked, comma and
control-character paths on that direct path. Environment cannot be identity:
bind the worker to something the caller cannot forge — at minimum require
the bound JOB.json to be non-writable and its digest to match a value
recorded at bind time, validate the output path with the same resolver the
launcher uses, and treat any mismatch as a refusal that writes nothing.
State plainly in the PR what remains forgeable by a local same-UID caller,
because some of it may be irreducible.

BLOCKER D — duplicate JSON keys turn NO-GO into GO
(b3_confirmation.py:316-328). Committed bytes containing both
"state": "NO-GO" and "state": "GO" were accepted, because plain json.loads
keeps the last duplicate. THIS REPOSITORY ALREADY HAS THE FIX: use
experiments.b3_pilot_evidence.strict_json_loads, which rejects duplicate
keys via object_pairs_hook, and read bytes through
evidence.read_regular_bytes_once. Use the existing primitive everywhere the
driver, launcher, audit or library parses JSON — do not write a new one.

MAJOR E — the artifact path is not bound to the declared repository path
(b3_confirmation.py:264-302,316-322). An external copy, and a path through
a symlinked parent, were both accepted even though the declared path is
checked against HEAD. Require the supplied filesystem path to resolve to
exactly the declared repository-relative file inside REPO_ROOT: resolve
both, compare, and refuse anything outside.

Keep every control the review confirmed still passing: boundary_adjacent
refusal, literal anchor constants, the exact 48-cell/24-contrast population,
all CLI modes routing through the selection loader, and the fresh-grid
screen (confirmed 24/24 with the screen SHA recorded) — but note the review
found the direct-worker bypass can still skip the screen, which BLOCKER C
must close.

Re-run every listed exploit as a committed regression. Tests pass on CBC.
Merge current origin/main so CI reports; quote CI-measured counts. Leave the
PR draft for another independent review.

<<< JOB 2

---

>>> JOB 3 — 2cycle: harden PR #47

Continue PR #47 in place on cursor/b3-submit-out-fix, head ef951273. No new
PR, no rebase, no force-push. Keep it draft. No cluster commands. Never
read, list, or hash anything under runs/b3_factor_pilot.

Keep the EGG_RUN_OUT correction exactly as it is; it is correct and its four
tests were shown to fail against the unfixed scripts. Fix the following, and
state in the PR description which items are regressions introduced by #47
and which are pre-existing properties of the pilot pipeline that also
applied to the canonical run — the scoping matters and should be honest.

NEW in #47:
1. EGG_PYTHON=/usr/bin/true with EGG_ENV_SCRIPT=/dev/null makes the real
   submit script exit 0 while producing no evidence — a silently successful
   array that computes nothing. Honor those two overrides only when no
   plausible scheduler is reachable, or better, only when an explicit
   test-harness marker is present. Add a regression that the rc=0/no-output
   exploit now fails loudly.
2. The resolved run directory is interpolated into Slurm's comma-delimited
   --export grammar unvalidated. Reject commas, control characters,
   absolute paths, symlinks, and anything resolving outside the runs root.

PRE-EXISTING, and worth fixing while you are here — note that an
independent review of the sibling confirmation launcher (PR #45) found
exactly these two and they apply to the pilot launcher too:
3. Workers never authenticate JOB.json against SLURM_ARRAY_JOB_ID. Be
   careful: that variable is caller-controlled environment state and cannot
   by itself be identity. Require the bound JOB.json to exist, be
   non-writable, and match a digest recorded at bind time, and refuse
   without writing anything on mismatch. Say in the PR what remains
   forgeable by a local same-UID caller.
4. The submit file is directly submittable outside the guarded launcher.
   Refuse execution that did not come from a bound, released launch, before
   invoking Python.

Also bind JOB.json exclusively (O_EXCL or link-no-replace) and re-read and
authenticate the manifest and job binding immediately before
`scontrol release`.

Merge current origin/main so CI reports; quote CI-measured counts. Leave
the PR draft.

<<< JOB 3

---

>>> JOB 4 — branch and price: freeze the replication comparator

Branch from current origin/main as cursor/replication-comparator. One draft
PR. No cluster commands. Never read, list, or hash anything under
runs/b3_factor_pilot — this must be written blind, before any replication
exists.

CONTEXT. The 60-cell B3 factor pilot completed and passed its audit. A
replication of the same 60 cells into a separate output directory is planned
as a verification-tier check on whether the pipeline reproduces its own
certificates, because the analyzer replays recorded evidence rather than
re-solving it. Right now "certified intervals agree within tolerance" exists
only as prose, which means a disagreement could be rationalized after it is
seen. Your job is to remove that freedom BEFORE any replication runs.

Deliver doc/B3_REPLICATION_COMPARATOR_SPEC.md,
src/experiments/compare_b3_replication.py, and adversarial tests. The spec
must freeze, as committed constants:

- which cells are compared (all 60, matched by cell identity) and what
  happens when one is missing on either side;
- which fields: at minimum lb_best, ub_ch, both raw endpoints of the uplift
  interval, the dictator bounds, and the certification flag;
- the tolerance per field, whether absolute or operand-scaled, with
  justification — the project's physical replay tolerance is 1e-4 kWh and
  the CG epsilon is 1e-2, and a comparator tighter than the machinery's own
  noise floor is not meaningful;
- what counts as agreement, as an explicit required count (for example
  60/60) rather than a vague majority, stated before any data exists;
- what a single disagreeing cell triggers: an engineering incident to
  investigate, never a choice of which run to score;
- that the ORIGINAL run remains canonical regardless of outcome and may
  never be substituted;
- that run manifests and run_commit are EXPECTED to differ between the two
  runs, so provenance fields are excluded from the comparison while
  solve-path equivalence is asserted separately.

Implementation constraints: keep the checker importable without a solver so
its tests are fast; parse every input with
experiments.b3_pilot_evidence.strict_json_loads (duplicate JSON keys must be
refused — this repository has had a real duplicate-key vulnerability) and
read bytes with evidence.read_regular_bytes_once; refuse to run if either
side is an incomplete population; never write into either input directory;
emit a deterministic machine-readable verdict.

Tests: hand-computable fixtures for pass, one-cell disagreement, missing
cell, extra cell, reversed interval, non-finite field, duplicate JSON keys,
and byte-identical regeneration.

Merge current origin/main so CI reports; quote CI-measured counts. Leave the
PR draft.

<<< JOB 4
