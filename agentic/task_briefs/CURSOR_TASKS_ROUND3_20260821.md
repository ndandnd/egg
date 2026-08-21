# Dispatch round 3 — 2026-08-21 (final hardening round)

| Give to | Job |
| --- | --- |
| **GPT** | Round-5 review of #37 at `54d45c4`, scoped, plus judge the threat-model bound |
| **uplift** | Independent review of #45 at `5a53c11` (it did NOT write it) |
| **2cycle** | Independent review of #48, the replication comparator (it did NOT write it) |
| **branch and price** | Sweep the A6 packager for the four defect classes — time-sensitive, one-shot path |
| **remote/cloud** | Merge current main into every open PR so CI reports on exact heads |

Preflight for write jobs (`gh api user` returns 403 for Cursor's GitHub App
token by design — expected, not an authorization failure; authorship comes
from `git config`):

    git remote get-url origin | grep -q "ndandnd/egg"
    git config --local user.name "Nathan Cho"
    git config --local user.email "63525258+ndandnd@users.noreply.github.com"
    git push --dry-run origin HEAD

---

>>> JOB 1 — GPT

Round-5 review of PR #37 in ndandnd/egg, head 54d45c4, branch
cursor/b3-pilot-closeout-5fa0, diff 0af91df..54d45c4. Review only. Stay
outcome-blind: never read, list, or hash anything under runs/b3_factor_pilot;
the analysis has not been run and the decision is not frozen. No cluster
commands.

This is intended to be the LAST security round, so it has two parts.

PART A — verify the five blockers from your 2981ba4 review are closed:

1. DEVELOPER_DIR / xcrun dispatcher. git_env() no longer filters GIT_*; it
   builds an ALLOWLIST from scratch (PATH, LC_ALL, and pinned GIT_* only), so
   DEVELOPER_DIR/TOOLCHAINS/SDKROOT are dropped rather than enumerated.
   git_argv also disables core.fsmonitor, core.hooksPath and protocol.ext per
   invocation, and sets GIT_CONFIG_NOSYSTEM with GIT_CONFIG_GLOBAL and
   GIT_CONFIG_SYSTEM at /dev/null. Attack it again.

2. Grafts and linked worktrees. GIT_GRAFT_FILE is pinned to /dev/null for
   every invocation, so grafts are neutralised rather than raced; git_dir()
   follows a worktree gitfile; the hygiene check consults the common dir. Your
   probe C (gitfile swap after the precheck) is the one I most want retested.

3. The producer used bare git. The runner moved to a dependency-free module,
   experiments/provenance_git.py, so b3_factor_pilot and b3_factor_screen now
   share it. Bare-git count in the B3 path is zero, verified by grep. Confirm
   independently, and check whether the LAUNCHER shell script
   (cluster/launch_b3_factor_pilot.sh) still shells a bare git in a way that
   matters — it was in your finding and is shell, not Python.

4. run_commit_verified as an editable credential. The selector now
   re-resolves the producer commit itself, through the hardened runner, from
   the run-manifest bytes it has just digest-checked; the flag is diagnostic.
   Retry the flip-the-boolean laundering probe. Also check the PACKAGER: it
   still reads the flag — decide whether it too must re-resolve.

5. Packager validated one set of bytes and could copy another. Every cell read
   is now digest-authenticated against the inventory, inventory absence is a
   refusal, and audit() receives the inventory. audit() additionally refuses
   an inventory omitting the root manifest (your finding 7). Retry the
   substitute-during-validation probe. Your finding 8 (FIFO) is fixed by
   opening non-blocking and clearing O_NONBLOCK once the inode is known
   regular — check that a non-blocking read cannot return a short buffer.

PART B — judge a scoping decision, not code.

Four rounds have each found real false-acceptance paths, and every remaining
one requires a LOCAL SAME-UID caller: someone who can already write the
repository, the runs tree and the environment. You noted this yourself
("formal security severity is lower where same-UID access is required"), and
the confirmation driver's author reached the same wall independently
("environment cannot be made unforgeable on a shared UID").

There is no such adversary in this project. The real risks are accidental
corruption and well-meaning automated edits, which the consumption digests,
the frozen anchor and the event replay now cover. The proposal is therefore
to STOP hardening after this round and instead bound the claim honestly in
the specification: this pipeline detects accidental corruption and post-hoc
tampering by a party without write access to the repository, the runs tree or
the environment; it does not and cannot defend against a local same-UID
caller; and the certificate's scope is stated accordingly.

Answer three questions directly:
  (a) Is that boundary honest, or does it paper over a defect that a
      non-privileged party could still exploit?
  (b) Is there any finding in your four reviews that does NOT require
      same-UID write access and is still open?
  (c) What is the minimum wording the specification must carry for a
      journal referee to accept the certificate's scope?

Run tests from src/: python -m pytest tests/ -q.

DELIVERABLE: Part A as findings (severity, file:line, probe, output). Part B
as a direct answer to (a), (b), (c). End with: is 54d45c4 safe to merge and
use to generate and freeze the flagship decision, GIVEN the stated boundary?

<<< JOB 1

---

>>> JOB 2 — uplift

Adversarially review draft PR #45 in ndandnd/egg, branch
cursor/b3-confirmation-driver-eea3, head 5a53c11 (CI green, 773 tests). Diff
d872e78..5a53c11 for this round; da2cdb6..5a53c11 for both repair rounds.

You did NOT write this code and you have not reviewed it before. Review only:
no commits, no pushes, no PR comments. Stay outcome-blind: never read, list,
or hash anything under runs/b3_factor_pilot. No cluster commands. Nothing
launched.

WHY STRICT: this driver spends seeds 32-37, the only reserved fresh-seed
range for the B3 confirmation. Consumed on an invalid design or a forged
authorization, they cannot be regenerated and the flagship permanently loses
its confirmatory arm.

Two prior review rounds found six then five defects. The author reports all
closed. Build your own exploits; do not merely re-run the committed
regressions, which only prove what the author thought of.

Claimed controls to attack:
- the selection artifact must be a COMMITTED tracked file whose exact bytes
  equal the blob at its declared repository-relative path, and the supplied
  filesystem path must resolve to that same file inside REPO_ROOT (external
  copies and symlinked parents were previously accepted);
- duplicate JSON keys are refused via the shared strict_json_loads (a
  committed artifact containing both "state": "NO-GO" and "state": "GO" was
  previously accepted, last-key-wins);
- pilot.run_commit_verified must be true;
- EGG_LAUNCH_SELFTEST requires an existing permission-marker file AND is
  refused whenever any scheduler is reachable (PATH sbatch, an absolute
  EGG_SBATCH, or SLURM_* in the environment);
- JOB.json is written 0444, and the worker refuses a writable binding, a
  relocated binding, or a mismatched SLURM_ARRAY_JOB_ID;
- output paths reject commas, control characters, "..", and symlinked
  components;
- the fresh-grid structural screen runs over all 24 instances before any
  submission and halts as DESIGN-NOT-FROZEN on failure;
- the audit requires the committed GO artifact.

The author states plainly that a local same-UID caller can still chmod the
binding, rewrite it and export a matching SLURM_ARRAY_JOB_ID, and that this
is irreducible without an external secret. Do NOT spend the review proving
that again. Spend it on: anything exploitable WITHOUT same-UID write access;
anything where the code claims more than it delivers; and whether the frozen
population, thresholds and boundary_adjacent refusal are still exactly as
specified.

Run tests from src/: python -m pytest tests/ -q.

DELIVERABLE: per finding, severity, file:line, the exact probe and its
output, and a concrete failure scenario. End with a verdict: is 5a53c11 safe
to merge and then use to launch a one-shot experiment?

<<< JOB 2

---

>>> JOB 3 — 2cycle

Adversarially review draft PR #48 in ndandnd/egg, branch
cursor/replication-comparator. You did NOT write it. Review only: no
commits, no pushes, no PR comments. Never read, list, or hash anything under
runs/b3_factor_pilot. No cluster commands.

WHAT IT IS. The 60-cell B3 factor pilot has completed and passed its audit. A
replication of the same 60 cells into a separate directory is planned as a
verification-tier check on whether the pipeline reproduces its own
certificates, because the analyzer REPLAYS recorded evidence rather than
re-solving it. This PR freezes the comparison rule BEFORE any replica exists,
so that a disagreement cannot be rationalized after it is seen.

The claimed frozen contract: all 60 cells matched by identity; agreement is
60/60; missing or extra cells refuse the numeric comparison as
INCOMPLETE_POPULATION; compared fields are lb_best, ub_ch, both raw uplift
endpoints, the dictator bounds and certified; SEK tolerance is operand-scaled
with a floor of 1e-2 (the CG epsilon / tol_d), with 1e-4 kWh documented as an
energy figure and explicitly NOT a tighter SEK bar; one disagreeing cell is
an engineering incident; the original run stays canonical; provenance
(run_commit, manifests) is excluded from comparison while solve-path identity
is compared separately.

ATTACK THE CONTRACT, not just the code. Specifically:
- Can the comparator be made to report agreement when the two populations
  differ in a way that would change the preregistered DECISION? Construct
  two synthetic populations that agree within the frozen tolerance on every
  compared field but yield different GO/NO-GO/UNDER-RESOLVED outcomes. If
  that is possible, the comparator is measuring the wrong thing and that is
  a BLOCKER.
- Is the tolerance floor of 1e-2 defensible, or does it make the check
  vacuous? Work out what magnitude of certificate drift would pass. Compare
  against the pilot's own certificate widths (tol_d = 1e-2, epsilon = 1e-2)
  and say whether a comparator at that floor can detect anything meaningful.
- Is there any path by which the replication could be substituted for the
  original, or the verdict could be read as authorizing a decision?
- Does it parse with strict_json_loads everywhere (duplicate JSON keys must
  refuse — this repository has had a real duplicate-key vulnerability), read
  bytes once, refuse incomplete populations, and never write into either
  input directory?
- Is the verdict deterministic and byte-identical on regeneration?

Run tests from src/: python -m pytest tests/ -q.

DELIVERABLE: per finding, severity, file:line, the exact probe and its
output. Answer explicitly: can two populations that agree under this
comparator produce different preregistered decisions? End with a verdict on
whether this contract is safe to freeze.

<<< JOB 3

---

>>> JOB 4 — branch and price (TIME-SENSITIVE)

Read-only audit. No commits, no branch, no PR, no cluster commands, no
sbatch, no ssh. Do not inspect or infer any scientific outcome. Deliver a
findings report as your final answer.

WHY THIS IS URGENT: the operator may today run the A6 second-stage recovery,
`package_a6_holdout.py recover2-pack`. It is ONE-SHOT: an O_EXCL claim file
is created before any outcome validation, and every failure after that point
is permanent with no third stage. Four defect classes have just been found
and fixed across the sibling B3 code. If the A6 packager shares any of them,
the operator needs to know BEFORE consuming the one shot.

On current origin/main, audit src/experiments/package_a6_holdout.py (and
analyze_a6_holdout.py where it participates) for these four classes
specifically:

CLASS 1 — duplicate-JSON-key acceptance. Plain json.loads keeps the last
duplicate, so a document can encode two contradictory values for the same
key. The repository has a fix already: b3_pilot_evidence.strict_json_loads
uses an object_pairs_hook that refuses duplicates. Find every place the A6
packager parses JSON (claim files, PREFLIGHT.json, SELECTION.json, bundle
manifests, receipts) and report which use a duplicate-rejecting parser and
which do not. The claim files gate the one-shot, so this matters most there.

CLASS 2 — provenance answerable by the caller. The A6 packager shells `git`
for commit resolution, ancestry and `git show`. Report every site and whether
it is subvertible by: a `git` shim earlier on PATH; an inherited GIT_DIR; on
macOS an inherited DEVELOPER_DIR (since /usr/bin/git is an xcrun dispatcher);
repository-local core.fsmonitor or hooksPath (which make verification execute
programs); refs/replace; or .git/info/grafts. The B3 fix is
experiments/provenance_git.py on the PR #37 branch — reference it as the
pattern, but do NOT change any code.

CLASS 3 — validate-then-copy divergence. The packager freezes a snapshot and
validates it. Report whether every consumed byte is digest-checked in the
same read that parses it, or whether a file could be substituted during
validation and restored before the copy, so that the bundle records bytes
that were never validated. This is the class that took three rounds to close
on the B3 side.

CLASS 4 — guards that trust the environment. Report how Slurm quiescence is
established (it runs squeue), what happens when squeue is missing or shimmed,
and whether the three quiescence checks can be defeated between the check and
the publication.

For each finding: file:line, the class, whether it is reachable on the
recover2-pack path specifically, whether it is BEFORE or AFTER the one-shot
claim is created (before = retryable, after = permanent), and a one-line
statement of what the operator should do about it today.

End with a direct recommendation: is it safe to run recover2-pack today, or
should something be fixed first? If safe, say which of the four classes are
absent and how you established that.

<<< JOB 4

---

>>> JOB 5 — remote/cloud agent

Mechanical, low-risk. For each open draft PR in ndandnd/egg listed below,
merge current origin/main into its branch so that CI reports on the exact
head, then report the CI-measured test count and status per PR. Do NOT
rebase, force-push, or merge any PR into main. Do NOT change any code beyond
what a merge requires; if a merge conflicts, stop and report the conflict
rather than resolving it creatively.

Branches:
- cursor/b3-pilot-closeout-5fa0            (PR #37)
- cursor/tiny-branch-price-lab-352b        (PR #38)
- cursor/frozen-loader-9213                (PR #41)
- cursor/local-column-proposer-6ec0        (PR #42)
- cursor/b3-confirmation-driver-eea3       (PR #45)
- cursor/ml-data-driver-eea3               (PR #46)
- cursor/b3-submit-out-fix                 (PR #47)
- cursor/replication-comparator            (PR #48)

Why: three of these have never had CI on their exact heads, and this
project's rule is that a self-reported test count is not evidence. Leave
every PR draft. Report a table: PR, head after merge, CI conclusion,
CI-measured test count.

<<< JOB 5
