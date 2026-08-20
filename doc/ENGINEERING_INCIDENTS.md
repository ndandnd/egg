# Engineering incidents and prevention ledger

This is the durable record of engineering failures and audit gaps that can
change whether experiment output is runnable, attributable, or scientifically
scoreable. It complements `DECISION_LOG.md` (research decisions) and
`UNICORN_RUNBOOK.md` (operator commands). Add an entry when a bug can corrupt,
strand, misattribute, or falsely certify evidence; do not rely on chat history.

Status vocabulary:

- **FIXED** — the invariant is enforced in committed production code and has
  regression coverage.
- **FOUND — IN PROGRESS** — the defect is demonstrated and a repair is being
  reviewed, but downstream evidence must still treat the old path as unsafe.
- **OPEN** — the defect is documented but no reviewed production repair exists.

Changing a status to **FIXED** requires naming the enforcing code and test. A
green test suite on a branch that happens to contain an unmerged dependency is
not sufficient.

## Incident index

| ID | Date found | Status | Short name |
|---|---|---|---|
| EI-001 | 2026-08-15 | **FIXED** | Replay rounding and audit tolerance |
| EI-002 | 2026-08-19 | **FIXED** | Negative aggregate-load residual made the A6 seed master infeasible |
| EI-003 | 2026-08-19 | **FOUND — IN PROGRESS** | Packager published apart from its production analyzer dependency |
| EI-004 | 2026-08-19 | **FOUND — IN PROGRESS** | Bidirectional Git-SHA prefix check failed open |
| EI-005 | 2026-08-19 | **FOUND — IN PROGRESS** | Stored replay and economic labels were trusted instead of recomputed |
| EI-006 | 2026-08-19 | **FOUND — IN PROGRESS** | Launch grid digest was repeated but not independently recomputed |
| EI-007 | 2026-08-19 | **FOUND — IN PROGRESS** | Successful transfer import leaves no durable receipt |
| EI-008 | 2026-08-19 | **FOUND — IN PROGRESS** | Closeout code and number of outcome looks were not frozen |
| EI-009 | 2026-08-19 | **FOUND — IN PROGRESS** | Launch array was not bound to per-record Slurm lineage |
| EI-010 | 2026-08-19 | **FOUND — IN PROGRESS** | Analysis output could be created inside its raw input tree |
| EI-011 | 2026-08-19 | **FOUND — IN PROGRESS** | Check-then-replace publication could overwrite a racing target |
| EI-012 | 2026-08-19 | **FOUND — IN PROGRESS** | CG certification was not independently derived from the event trace |
| EI-013 | 2026-08-19 | **FOUND — IN PROGRESS** | Retained columns were not reconciled to keys and oracle events |
| EI-014 | 2026-08-19 | **FOUND — IN PROGRESS** | Dictator evidence accepted negative gaps and reversed bounds |
| EI-015 | 2026-08-19 | **FOUND — IN PROGRESS** | Pricing evidence accepted a certified bound above its incumbents |
| EI-016 | 2026-08-19 | **FOUND — IN PROGRESS** | Archive byte-determinism contract omitted the embedded closeout claim |
| EI-017 | 2026-08-19 | **FOUND — IN PROGRESS** | A6 trigger replay trusted its recorded decision gap |
| EI-018 | 2026-08-19 | **FOUND — IN PROGRESS** | The seed pricing vector was not anchored to the frozen market |
| EI-019 | 2026-08-19 | **FOUND — IN PROGRESS** | Coordinated clean-price and master edits could fabricate a CG certificate |
| EI-020 | 2026-08-19 | **FOUND — IN PROGRESS** | Historical A4 replay cannot recover the omitted clean out-dual |
| EI-021 | 2026-08-19 | **FIXED** | A6 recovery bounds and requested pricing-gap state were not replayed |
| EI-022 | 2026-08-19 | **FIXED** | Inode recycling defeated (dev, ino) ownership signatures |
| EI-023 | 2026-08-19 | **FIXED** | Analyzer publication forked from the package contract |
| EI-024 | 2026-08-19 | **FOUND — IN PROGRESS** | Precommit incomplete-marker deletion was misclassified as a completed publication |
| EI-025 | 2026-08-19 | **FOUND — IN PROGRESS** | A6 shared replay omitted terminal/final outcome closure |
| EI-026 | 2026-08-20 | **FOUND — IN PROGRESS** | Operand-scaled bound/incumbent equality passed one gate but its derived gap failed a scale-1 zero gate; claimed pack aborted mid-validation |
| EI-027 | 2026-08-20 | **FOUND — IN PROGRESS** | Physical-incumbent reconstruction adjustment exceeded the operand tolerance and aborted the EI-026 recovery pack |

## EI-001 — Replay rounding and audit tolerance

**Status: FIXED.** Production enforcement is in `src/egglab/evsp.py` and
`src/egglab/loops.py`; regression coverage is in
`src/tests/test_replay_tolerance.py` and `src/tests/test_closeout.py`.

**Observed symptom and evidence.** Phase-1 job 51417 and boundary job 51831
reported replay failures such as `terminal SOC 6.00 < 6.0`. The legacy
extractor rounded charge/load values to six decimals before independent
replay, while replay admitted only `1e-6` kWh. Small rounding and solver
feasibility residuals accumulated along vehicle chains and crossed tight SOC
bounds. Legacy loop drivers also allowed replay-invalid records to be appended
and checkpoints advanced instead of failing the work unit.

**Root cause.** Presentation precision was used as evidence precision, and the
replay contract was not enforced transactionally before evidence was
committed.

**Why earlier tests missed it.** They did not exercise a tight multi-arc chain
where per-event rounding accumulates, and they did not assert that a replay
failure leaves the append-only log and checkpoint position unchanged.

**Invariant and fix.** Store all values used by replay or economics at full
float precision. Rounding is allowed only for hashes and presentation. The
independent replay uses the single documented audit-only tolerance
`REPLAY_TOL_KWH = 1e-4` kWh; this does not relax the MILP. A replay-invalid
iteration must raise before log append or checkpoint mutation.

**Scientific handling.** Raw legacy records remain immutable. Each stored
failure is resolved, if at all, through an exact-record-hash revalidation
sidecar; commit age or a globally changed tolerance never auto-waives it.
Audits distinguish raw stored failures from effective unresolved failures.

## EI-002 — Negative aggregate-load residual made the A6 seed master infeasible

**Status: FIXED.** The scoped repair is in `src/egglab/evsp.py`,
`src/egglab/b2a2.py`, `src/egglab/a6.py`, and the shared dictator driver; the
production holdout analyzer independently checks the reconstruction evidence.
Regression coverage includes the B2/A6 unit tests and A6 holdout tamper tests.

**Observed symptom and evidence.** The first frozen A6 holdout attempt, Slurm
job 218143 at experiment commit `2dba047`, completed 126 of 128 tasks. The two
matched failures, `a2_s26_n8_b0.05` and `a6_a4_s26_n8_b0.05`, both stopped at
the first clean restricted master as infeasible. Their identical seed column
contained `L[7] = -7.356248409800537e-06` kWh.

**Root cause.** The EVSP extractor stored the solver's redundant aggregate
load variable directly. Its tiny negative feasibility residual disagreed with
the nonnegative charge variables that define physical load. With one column,
the restricted master simultaneously imposed that negative coefficient and
its own `L >= 0` domain, so infeasibility occurred before A2 and A6 could
diverge.

**Why earlier tests missed it.** Pilot and unit instances did not produce this
backend residual, and the column boundary checked solver/replay labels without
asserting that each slot load equals the sum of nonnegative charging events.
There was no exact one-column regression for the exposed seed-26 instance.

**Invariant and fix.** In B2/A6 only, reconstruct canonical physical load from
charge events; retain the raw aggregate vector and per-slot residual as audit
evidence; fail if disagreement exceeds the replay tolerance. Recompute pricing
and dictator feasible objectives from canonical load, reject malformed or
negative columns before master construction, and version the checkpoint
identity. Generic Phase-1/boundary replay semantics remain unchanged.

**Scientific handling.** Job 218143 is an implementation incident and is never
scored. Its 126 completed cells are retained as incident evidence but cannot be
mixed with repaired cells. The decision to replace all 128 method-cells under
one pinned commit was made before reading a completed-cell outcome comparison;
there is no seed substitution or two-cell-only recovery.

## EI-003 — Packager published apart from its production analyzer dependency

**Status: FOUND — IN PROGRESS.** Do not use the A6 transfer packager for a
scientific closeout until the integrated production dependency and packager
are reviewed and merged together.

**Observed symptom and evidence.** Commit `bd63fae` adds
`src/experiments/package_a6_holdout.py`, whose default production path imports
launch and scientific validators from `analyze_a6_holdout.py`. Those validators
were introduced by its unmerged parent `5a2010e`; neither commit is contained
in main at `92c38a6`. Tests run on the stacked branch see both commits and can
therefore pass, while treating the packaging diff as standalone (for example,
cherry-picking only `bd63fae`) omits a production dependency.

**Root cause.** A stacked implementation was presented as one independently
integrable change without an explicit base/ancestry gate. Dependency injection
in tests further allowed the packager's orchestration to be exercised without
proving that its default production imports existed on the integration base.

**Why earlier tests missed it.** The test checkout already contained the
unmerged parent, so import and test success could not distinguish a
self-contained change from an accidentally complete stacked branch.

**Required invariant and regression.** A publishable PR must contain every
production dependency relative to its declared main base. Review must verify
the PR merge-base and run at least one default-callback import/packaging smoke
without injected validators. If changes are intentionally stacked, the parent
must merge first and the child must be rebased before it is called ready.

**Repair under review.** The integration branch ports both stacked commits as
one diff from `main`; `test_default_production_callback_wiring_is_self_contained`
exercises the packager's runtime imports rather than injected substitutes.

**Scientific handling.** This was found during code integration, not from a
packaged scientific result. No transfer bundle or closeout artifact should be
accepted from the incomplete integration path.

## EI-004 — Bidirectional Git-SHA prefix check failed open

**Status: FOUND — IN PROGRESS.** The hardening is under review; until it is
merged, a user-supplied analysis or packaging commit string is not sufficient
attribution evidence by itself.

**Observed symptom and evidence.** Both
`analyze_b2_pilot.verify_analysis_code_commit` and the first A6 packager draft
accepted a claim when either `HEAD.startswith(claimed)` or
`claimed.startswith(HEAD)`. An empty claim satisfies the first expression; an
overlong string beginning with the full HEAD satisfies the second. Neither is
proved to name a Git object.

**Root cause.** String-prefix compatibility was substituted for Git object
resolution and exact identity.

**Why earlier tests missed it.** Coverage included ordinary short and full
SHAs but not empty, malformed, uppercase, nonhexadecimal, overlong, unresolved,
or wrong-resolved claims.

**Required invariant and regression.** Accept only 7--40 lowercase
hexadecimal characters, resolve `<claim>^{commit}` with Git, and require the
resolved full object ID to equal `HEAD^{commit}` exactly before checking a
clean tracked tree. Regression tests must cover valid short/full claims plus
every malformed class above, an unresolved claim, a different valid commit,
and a dirty tree.

**Repair under review.** Both analysis and packaging verifiers now implement
the exact Git-object contract. Their focused tests cover malformed,
unresolved, wrong-resolved, valid short/full, and dirty-tree cases.

**Scientific handling.** No artifact gains provenance from a prefix string
alone. Analysis and packaging remain blocked unless the claimed commit resolves
exactly and the tracked tree is clean.

## EI-005 — Stored replay and economic labels were trusted instead of recomputed

**Status: FOUND — IN PROGRESS.** The closeout/package audit must not be treated
as independently scoreable until this gap is closed.

**Observed symptom and evidence.** The A6 audit path required stored
`replay_ok=true` and checked several stored objective fields for mutual
consistency, but did not reconstruct a `Solution` from every retained column,
oracle record, and dictator record and independently replay the schedule. A
checkpoint and its JSONL materialization could therefore be changed together
while keeping their labels mutually consistent: duplicate/missing trips,
malformed arc vectors or kinds, a charge attached to the wrong vehicle or a
non-depot arc, false schedule/load hashes or `column_key`, and coordinated
deadhead/`ops_cost`/objective drift were not independently excluded. Raw-model
pricing arithmetic and adaptive-dictator UB/LB/gap arithmetic also lacked a
full independent cross-check.

**Root cause.** The audit confused agreement among producer-written fields
with independent derivation from primary schedule evidence.

**Why earlier tests missed it.** Tamper tests mostly changed one summary field
at a time. They did not mutate a producer label and all of its dependent
summaries coherently, which is the case an independent audit must reject.

**Required invariant and regression.** Validate record shape, exact coverage,
fleet count, and charge-to-vehicle/arc association before replay. Rebuild each
solution from primary schedule fields, run `validate_solution` under the frozen
policy, recompute schedule/load hashes, deadhead, operating cost, column key,
pricing raw-versus-physical objective/adjustment, and dictator raw objective
plus adaptive UB/LB/gap/tolerance arithmetic. Only then compare producer
labels. Add synchronized checkpoint-plus-JSONL tamper tests, including coherent
multi-field mutations that would pass simple equality checks.

**Repair under review.** `_validate_schedule_evidence` and
`_validate_cell_numeric_evidence` now reconstruct charge-derived load and every
retained solution, then recompute structure, hashes, deadhead, operating cost,
pricing economics, dictator economics, and adaptive bounds. The synchronized
tamper battery mutates checkpoints and JSONL materializations together. A
solver-generated burned-seed regression (`seed=29`, `n_trips=8`) serializes
and reloads a genuinely positive-charge schedule before replaying the same
load, schedule, and pricing checks; its paired charge tamper must fail.

**Scientific handling.** Stored `replay_ok` and economic fields are evidence to
cross-check, not audit authorities. Any mismatch halts the full population
unscored; it cannot be repaired by editing a summary or excluding a cell.

## EI-006 — Launch grid digest was repeated but not independently recomputed

**Status: FOUND — IN PROGRESS.** The launch records preserve a digest, but the
closeout gate must independently bind it to the frozen grid bytes before that
digest is provenance evidence.

**Observed symptom and evidence.** The launcher hashed its `--list` output and
wrote the same `grid_list_sha256` into `SUBMISSION_LOCK/INTENT.txt` and the
launch manifest. The analyzer checked that both copies matched and were shaped
like SHA-256, but did not recompute the expected digest. Coordinated replacement
of both fields with the same 64-character value therefore passed that check.

**Root cause.** Repetition was treated as independent verification; no
separately generated canonical grid byte representation was owned by the
analyzer.

**Why earlier tests missed it.** Tests mutated only one copy of the digest and
confirmed the cross-file mismatch. They did not mutate every repeated copy to
the same false value.

**Required invariant and regression.** Define one deterministic canonical
serialization of all 128 ordered method cells, independently regenerate it
from the frozen grid definition during analysis/package validation, hash its
exact bytes, and require equality with every launch record. Include a paired
tamper test that changes all stored digest copies together.

**Repair under review.** `canonical_grid_list_bytes` independently owns the
frozen driver representation and is pinned to production digest
`4ca11f7fe113c849c7a65921ddc78badce0a7fdb7b01b35db6a7fb8d72716bcd`.
Golden and coordinated-tamper regressions fail before scoring.

**Scientific handling.** The exact cell directories, preflight population,
and checkpoint identities remain separately gated, but the launch-grid digest
must not be cited as independently verified until recomputation passes.

## EI-007 — Successful transfer import leaves no durable receipt

**Status: FOUND — IN PROGRESS.** The integrated closeout branch writes and
validates an adjacent `a6_holdout.TRANSFER_RECEIPT.json`; it remains in
progress until that implementation and its analyzer consumer are reviewed
and merged together.

**Observed symptom and evidence.** After a successful import, closing the
terminal loses the returned archive digest and import result unless the
operator manually records them. The imported raw tree intentionally remains
byte-identical to the source, so adding a receipt inside that tree would also
invalidate its source inventory.

**Root cause.** Atomic data installation was implemented, but durable
destination-side provenance was not included in the import transaction.

**Why earlier tests missed it.** Round-trip tests assert byte identity,
tamper rejection, atomic rename, and no overwrite; they do not require a
persistent receipt outside the canonical source tree.

**Required invariant and regression.** On successful import, transactionally
write an adjacent, non-overwriting receipt that binds the destination path,
archive SHA-256, bundle-manifest SHA-256, canonical imported-tree SHA-256,
experiment and packaging commits, and import timestamp. Fsync the receipt and
parent directory; repeated import must overwrite neither target nor receipt. A
caught failure must remove publisher-owned target and receipt paths; if
rollback is interrupted or incomplete, the lock must remain and analysis must
refuse. Verify the receipt against the installed tree in a round-trip test.

**Repair under review.** `package_a6_holdout.import_bundle` uses the import
lock only as an in-progress/failure sentinel, publishes the raw directory and
canonical adjacent receipt without overwrite, rolls both back on caught
post-publication failures, and preserves the lock if rollback is interrupted
or incomplete. A successful transaction removes the lock; the adjacent
receipt, not the lock, is the durable commit record.
`analyze_a6_holdout.validate_transfer_receipt` independently recomputes the
installed-tree inventory, matches all campaign identities, and requires the
analysis HEAD to equal the receipt's packaging commit. Regression coverage is
in `test_import_round_trip_is_verified_transactional_and_no_overwrite`,
`test_receipt_publication_failure_rolls_back_target`,
`test_post_publish_validation_failure_rolls_back_both`, and
`test_import_receipt_is_required_and_bound_by_analyzer`.

**Scientific handling.** Until the repair is merged, retain the original
bundle directory and sidecar and do not treat a destination checkout as
self-proving. After merge, preserve the adjacent receipt and both closeout
claims with the raw tree. A remaining import lock means interrupted or
incompletely rolled-back work and must block analysis; never synthesize or
delete any provenance marker after extraction.

**2026-08-19 addendum (post-commit descriptor-close case).** A later
adversarial pass found that `import_bundle` removed and fsynced its lock,
then closed its descriptors, so a descriptor-close failure could still
report import failure after the target and receipt had durably committed and
the lock was gone. The import now tracks an explicit `import_committed` state
(set once the target and receipt are installed and fsynced): once committed,
a descriptor-close failure has no data consequence and must not report the
import as unsuccessful, while pre-commit close failures are still surfaced
honestly. Regression coverage:
`test_import_descriptor_close_after_commit_is_not_a_failure` and
`test_import_descriptor_close_before_commit_is_reported`.

## EI-008 — Closeout code and number of outcome looks were not frozen

**Status: FOUND — IN PROGRESS.** The repair is implemented on the integrated
closeout branch but is not production policy until review and merge.

**Observed symptom and evidence.** The first analyzer draft accepted any clean
descendant of the experiment commit and used a new timestamp for each output.
After importing the raw holdout, an operator could therefore modify scoring
or decision code, or rerun closeout after seeing the first decision, while all
Git-ancestry and output-path checks still passed.

**Root cause.** Run provenance and analysis provenance were treated as one
monotone ancestry chain. No artifact froze the exact reviewed closeout code,
and “no second look” existed only as runbook prose.

**Why earlier tests missed it.** Tests verified wrong-ancestor rejection and
non-overwrite of one timestamped output, but did not try a different clean
descendant or a second timestamp.

**Additional review finding.** The packager itself called the holdout-root and
scientific-population validators before the destination-side analysis claim
existed. Those validators read checkpoint outcomes and construct cell scores,
even though they stop short of the final decision. Packaging was therefore an
unrecorded source-side look at the data; a failed package could be retried with
changed code before the nominal one-shot analysis.

**Invariant and repair under review.** There are two distinct one-look gates,
and neither substitutes for the other:

- Before the source packager invokes any outcome-aware root, population,
  audit, extraction, or scoring validation, it exclusively creates the
  persistent adjacent `a6_holdout.CLOSEOUT_CLAIM.json`. That source claim
  binds the canonical raw-tree snapshot, exact packaging code, frozen launch
  and selection identities from which the package name is deterministically
  derived. A failed or partial source claim blocks repackaging.
- The successful import receipt freezes that exact package and packaging
  commit. Before the destination analyzer interprets any checkpoint outcome,
  it exclusively creates the persistent adjacent
  `a6_holdout.ANALYSIS_CLAIM.json`, binding the imported tree, receipt, exact
  analysis commit, stamp, and intended output. A failed or partial destination
  claim blocks a second analysis.

The analysis HEAD must equal the receipt's packaging commit rather than merely
descend from it. Claim creation must use an exclusive, non-overwriting write,
and orchestration tests must prove both claims precede their respective first
outcome-aware callback. The integrated regression battery covers persistent
claims, refusal on a second attempt, and production callback order.

**Scientific handling.** Never delete or rewrite either claim merely to obtain
another result. A failed claimed package or analysis is an incident: preserve
the claim, raw tree, and any completed receipt, diagnose without reading a new
decision, and authorize any recovery explicitly in this ledger before another
look.

## EI-009 — Launch array was not bound to per-record Slurm lineage

**Status: FOUND — IN PROGRESS.** Current-run task-index enforcement is under
review. Exact parent-array binding is unavailable for the already-running
holdout because the launch-era recorder did not serialize
`SLURM_ARRAY_JOB_ID`.

**Observed symptom and evidence.** Oracle, iteration, and dictator records
stored `slurm_job_id` and `slurm_array_task_id`, but closeout ignored them. A
manual per-cell run or a recovery array could therefore retain matching
scientific identities while no longer being demonstrably produced by the
frozen task assignment.

**Root cause.** Launch provenance and execution-record provenance were audited
separately but never joined on cell index. The parent-array environment field
was omitted from the record schema.

**Why earlier tests missed it.** Cell-provenance tests changed the stored cell
index, not the Slurm fields in the materialized solver records.

**Invariant and repair under review.** For every cell, all oracle, iteration,
and dictator records must have a non-null task ID equal to the frozen
method-major cell index and one consistent task job ID. Synchronized
checkpoint/JSONL tampering must halt unscored. Future records now also preserve
`slurm_array_job_id`, with regression coverage in
`test_provenance_records_slurm_array_parent`; current validation is covered by
`test_slurm_task_lineage_tampering_halts_unscored`. Because the historical
records at experiment commit `92c38a6` do not contain the parent field, this
repair cannot retroactively prove that their task job IDs descend from the
parent array named by the launch manifest.

**Scientific handling.** For this holdout, report exact task-index and
within-cell job consistency, plus the independently preserved launch job ID;
do not claim that record bytes prove the parent-array join. Future campaigns
must require the new parent-array field before launch.

## EI-010 — Analysis output could be created inside its raw input tree

**Status: FOUND — IN PROGRESS.** The path-separation guard and regression are
implemented on the integrated branch pending review and merge.

**Observed symptom and evidence.** Supplying an output such as
`runs/a6_holdout/analysis` created the staging directory beneath the raw input.
The later input-tree hash could then inventory generated figures and tables as
if they were source evidence, while concurrent output writes changed that tree.

**Root cause.** The packager enforced source/output separation, but the
analyzer independently joined unvalidated `root`, `out`, and `stamp` strings.

**Why earlier tests missed it.** Tests used separate temporary input and output
roots and checked only collision at the final timestamp.

**Invariant and repair under review.** Resolve raw root, output base, and final
stamp path before any validation or write; reject unsafe stamps and every
output path beneath the raw tree. Production output must also be empty before
the one-look claim. Regression coverage is
`test_analysis_output_inside_raw_root_refuses_before_writing`.

**Scientific handling.** Any artifact produced with output nested inside raw
evidence has ambiguous input hashes and is not an acceptable closeout result.

## EI-011 — Check-then-replace publication could overwrite a racing target

**Status: FOUND — IN PROGRESS.** No-replace publication hardening is under
review for the package, importer, and analyzer; it is not production policy
until merged with collision-injection regressions.

**Observed symptom and evidence.** Each publisher first checked that its final
path did not exist and later called a replacing rename operation
(`os.replace`, or a platform rename with overwrite semantics). Another process
could create the final path between those operations. The publisher would then
replace an archive directory, imported raw root, receipt, or analysis output
that it did not create.

**Root cause.** A preflight existence check was treated as an atomic
no-overwrite guarantee. The final publication primitive itself still permitted
replacement.

**Why earlier tests missed it.** Tests supplied an already-existing target
before the precheck. They did not inject a target after validation and
immediately before publication, nor check that rollback preserves a path owned
by another process.

**Additional review finding.** Exclusive reservation of the final directory
did not by itself protect entries created inside that directory. A competitor
could add an unexpected file or replace a linked artifact after reservation;
the publisher removed its incomplete marker and returned success without a
final exact-population/inode check. Import rollback also used blind recursive
deletion and receipt unlinking, so a competitor path appearing after
reservation could be deleted during cleanup.

The same review exposed four deeper namespace races that are not repaired by
checking only the final leaf or by adding `O_NOFOLLOW` to a later file open:

- A publisher could create its final directory, then have that directory root
  replaced before it captured or rechecked the root inode. Subsequent
  path-based links followed the replacement namespace and populated a
  competitor-owned directory (or a directory reached through a symlink).
- A source staging/frozen root could be replaced after validation but before a
  path-based hard link. The operation then imported or published competitor
  bytes and incremented the competitor file's link count, even though the
  original source snapshot had passed.
- Import-lock release removed a pathname without proving that the current lock
  directory was the exact inode the importer had created. A replacement lock
  could therefore be removed as if it were importer-owned state.
- Outer `finally` blocks recursively deleted a staging or frozen pathname after
  failure without first proving root ownership. If that pathname had been
  swapped, cleanup could recursively delete a competitor tree. The analyzer's
  separate flat publisher had the same path-root weakness as the package and
  import paths.

**Expanded root cause and impact.** The implementation retained path strings
as authority after a check, instead of retaining an open directory handle or
recorded root inode as authority for every later mutation and cleanup. A leaf
inode check cannot protect an ancestor that has already been exchanged. These
races can publish bytes that were never validated, mutate a competitor through
hard-link side effects, delete a competitor during rollback, or return success
from a namespace different from the one that was reserved. Such an artifact is
not merely operationally untidy: its manifest and receipt need not describe
the bytes actually installed.

**Required invariant and regression.** Every final package directory, imported
raw root, receipt, and analysis output must be published with an atomic
no-clobber primitive or an exclusively reserved final directory. No success
path may use replace semantics for a user-visible target. Inject a competing
file, directory, and symlink at the last publication boundary; the operation
must fail closed and must neither modify nor delete the competitor. Partial
publisher-owned state must remain distinguishable from a committed artifact.
Immediately before removing an incomplete sentinel, revalidate the exact
directory population, types, link counts, root inode, and every artifact inode.
Rollback may unlink or remove only recorded publisher-owned inodes; any
missing, replaced, or extra path preserves the competitor and the incomplete
sentinel/import lock for incident review. Tests must inject changes both before
exclusive reservation and after files have been linked inside it. In addition,
tests must exchange each final-directory root after creation but before
ownership capture, exchange each source staging root immediately before its
first hard link, replace the import-lock inode before release, and exchange a
staging/frozen root before outer cleanup. Every case must fail closed, preserve
the competitor byte-for-byte, and avoid changing its link count. A native
atomic no-replace directory move, or operations anchored to already-open
directory descriptors with exact inode/population checks, is required; a
path-based `lstat` followed by another path-based mutation is still a race.

**Repair under review.** Package and analysis artifact publishers now
exclusively reserve the final directory, leave an incomplete sentinel until
all expected regular files are linked without overwrite, and publish the
manifest last. The importer exclusively reserves the raw-root directory while
its durable import lock is held; the adjacent receipt is itself committed with
an exclusive hard link. Collision regressions inject a file, directory, and
symlink at each final boundary and require the competitor to survive
byte-for-byte. Post-reservation regressions additionally replace a linked
artifact or add an unexpected entry immediately before commit; final ownership
revalidation must refuse success, and conservative rollback must leave the
competitor plus the fail-closed sentinel/lock intact.

The expanded root-swap regressions remain part of the merge gate. Publication,
source linking, lock release, and recursive cleanup are not considered fixed
until those tests exercise the package publisher, nested importer, and the
analyzer's independent publisher rather than only a shared helper in
isolation.

**Scientific handling.** A publication produced by the old check-then-replace
path is not proven to have preserved a pre-existing target. Keep the source
tree and bundle evidence; do not infer atomic non-overwrite merely because no
collision was observed.

## EI-012 — CG certification was not independently derived from the event trace

**Status: FOUND — IN PROGRESS.** Independent trace replay is implemented on
the integration branch and awaits review and merge.

**Observed symptom and evidence.** The closeout analyzer accepted producer
checkpoint fields such as `ub_history`, `lb_history`, `lb_best`, terminal
`outcome`, certification status, final gap, and calls-to-certificate after
checking them mainly against one another. A coordinated edit of the stored
histories, terminal label, and score could therefore remain internally
consistent without following from the committed clean-master and pricing
events.

**Root cause.** Redundant checkpoint summaries were treated as primary
certificate evidence instead of claims to be regenerated chronologically from
solver events. Candidate calls were not independently excluded from creating
a certified lower bound.

**Why earlier tests missed it.** The tamper battery changed individual bounds
or labels, not the whole mutually consistent terminal story or the first call
at which the stopping condition became true.

**Required invariant and regression.** Replay every oracle and iteration in
order. Validate each serialized clean restricted-master LP transcript,
recompute the pricing lower bound from the certified solver bound, monotone
`LB_best`, every certificate gap, the first clean call satisfying epsilon, and
the budget-exhausted terminal master. Candidate calls may carry but never
improve the certified lower bound. Compare the reconstructed trajectories and
terminal classification to every stored summary and derive the analysis score
only from the replayed first-certificate call (or the frozen
budget-exhaustion score). Coordinated history/outcome/score tampering must halt
the population unscored.

**Repair under review.** `_replay_cg_certificate_evidence` rebuilds the
derivable trace from committed master solves and linked pricing-oracle solver
bounds, then treats checkpoint histories and outcomes as redundant
assertions. `_validate_clean_bound_safety` also rebuilds every chronological
retained-column prefix and independently brackets the exact convex restricted
master: a feasible simplex point supplies an upper bound, while its
Frank--Wolfe gap supplies a rigorous lower bound. The recorded clean UB must
lie within that independently derived bracket and the frozen PWL tolerance;
any claimed certificate must remain closed when evaluated against the
independent feasible upper bound. Thus missing historical lambdas do not make
certificate safety unverifiable.

One launch-era evidence boundary remains explicit. The records do not
serialize the producer's RMP lambdas, aggregate load, link dual vector, or
per-iteration tangent set. The auditor can independently bound the same exact
restricted-master optimum and establish a safe feasible UB, but it cannot
claim to have reproduced the producer's exact primal mixture, exact stored UB,
dual path, or tangent-refinement path. A6-A4 candidate iterations also omit
the contemporaneous clean out-dual; EI-020 records the narrower consequence
for mechanism replay. Future campaigns must persist the RMP lambdas,
reconstructed load, clean link duals, and candidate out-dual if exact
algorithm-path replay is a scientific requirement.

**Scientific handling.** Until merged, a stored `certified=true` or
calls-to-certificate value is producer output, not an independent closeout
certificate. After the repair is reviewed, describe the result as an
independently bounded certificate and replayed stopping trajectory, not as a
byte-for-byte reproduction of the historical primal/dual execution path.

## EI-013 — Retained columns were not reconciled to keys and oracle events

**Status: FOUND — IN PROGRESS.** Column-lineage reconstruction is implemented
on the integration branch and awaits review and merge.

**Observed symptom and evidence.** The analyzer validated retained columns
individually but did not prove that `checkpoint["keys"]` exactly described
those columns or that the retained list was precisely the seed column followed
by the novel columns committed by chronological oracle events. A synchronized
checkpoint edit could add, omit, reorder, or substitute a valid-looking column
without an event that explains its admission.

**Root cause.** Column validity and column provenance were audited separately;
the append-only construction rule was not replayed.

**Why earlier tests missed it.** Tests corrupted a column's physics or hash,
not a coherent retained-column/key/event lineage.

**Required invariant and regression.** Recompute every retained column key and
require exact ordered equality with the stored key list, with no duplicates.
Project the seed oracle record into the first retained column, then replay every
later oracle event's recomputed novelty flag and require exactly one appended
column for each novel event and none for a duplicate, except for the producer's
documented final clean certifying return (which returns before its novel column
is appended). Compare the complete projected columns, not only their hashes.
Add coherent add/drop/reorder and novelty-label tamper cases, including that
terminal branch.

**Repair under review.** `_validate_retained_column_lineage` reconstructs the
ordered column stream from the oracle records and cross-links their call IDs,
keys, and novelty flags to iteration evidence.

**Scientific handling.** A physically valid column is not admissible evidence
unless its key and chronological oracle event also prove how it entered the
master.

## EI-014 — Dictator evidence accepted negative gaps and reversed bounds

**Status: FOUND — IN PROGRESS.** Bound-order and per-round gap reconstruction
are implemented on the integration branch and await review and merge.

**Observed symptom and evidence.** Adaptive-dictator convergence used the
stored arithmetic `adaptive_ub - adaptive_lb <= tolerance` without first
requiring the certified lower bound to be no greater than the independently
recomputed feasible upper bound. A negative gap therefore passed convergence.
Per-round solver rows also carried incumbent, bound, and gap fields without a
complete independent ordering and arithmetic check.

**Root cause.** The stopping inequality was evaluated without enforcing the
mathematical domain of a minimization certificate: each certified bound must
not exceed its incumbent, and the final best lower bound must not exceed the
physical feasible objective, except for the documented numeric equality
tolerance.

**Why earlier tests missed it.** Tests covered nonfinite or individually
mismatched adaptive fields, but not a coordinated `LB > UB` story whose
negative gap still satisfied the one-sided convergence comparison.

**Required invariant and regression.** For every adaptive subsolve, recompute
`gap = incumbent - bound` and reject a bound above its incumbent beyond the
evidence tolerance. Recompute the final lower bound from the certified
subsolve bounds, bind the upper bound to the independently reconstructed
physical dictator objective, require `LB <= UB`, and only then evaluate the
frozen tolerance. Include negative row-gap and final `LB > UB` tamper tests.

**Scientific handling.** A negative reported optimality gap is an invalid
certificate, not stronger convergence; the full holdout remains unscored.

## EI-015 — Pricing evidence accepted a certified bound above its incumbents

**Status: FOUND — IN PROGRESS.** Pricing-bound ordering and objective linkage
are implemented on the integration branch and await review and merge.

**Observed symptom and evidence.** A coordinated clean-pricing event could set
the minimization solver bound above both the solver/model incumbent and the
independently reconstructed physical feasible objective, then propagate the
inflated lower bound through `min_reduced_cost_lb`, `lb_ch`, histories, and the
terminal certificate. Its stored pricing gap was negative, but the prior trace
replay accepted the internally consistent story.

**Root cause.** Certificate replay consumed the solver bound without first
binding the solver objective to the independently reconstructed raw-load model
objective or enforcing `bound <= incumbent` for both model and physical
feasible objectives. The pricing-gap fields were compared downstream without
first requiring their mathematical domain to be nonnegative.

**Why earlier tests missed it.** They changed individual objective, bound, or
history fields and expected a cross-file mismatch. They did not coherently
change every dependent lower-bound and certificate claim while preserving
their internal arithmetic.

**Required invariant and regression.** For every pricing oracle, independently
reconstruct the model and physical objectives, require the stored solver
objective to equal the model objective, require the certified minimization
bound not to exceed either incumbent beyond the evidence tolerance, and
recompute a nonnegative absolute/relative pricing gap before the bound can
contribute to `LB_best`. Regression
`test_coordinated_pricing_bound_above_incumbents_halts` changes the complete
downstream story and must halt the population unscored.

**Scientific handling.** A negative pricing optimality gap or a lower bound
above a feasible incumbent is invalid evidence, not a stronger certificate.

## EI-016 — Archive byte-determinism contract omitted the embedded closeout claim

**Status: FOUND — IN PROGRESS.** The corrected manifest contract and regression
are implemented on the integration branch and await review and merge.

**Observed symptom and evidence.** The bundle manifest said archive bytes were
determined by the source inventory, packaging commit, Python, and zlib runtime.
The archive also embeds the exact source closeout claim, including its claim
timestamp, so otherwise identical inputs with different claim bytes produce
different archive bytes.

**Root cause.** The reproducibility description was not updated when the
one-look closeout claim became an embedded provenance input.

**Why earlier tests missed it.** Determinism tests reused one injected claim and
therefore proved stable bytes only conditional on that claim; they did not vary
the claim while holding the other named inputs fixed.

**Required invariant and regression.** State the byte-determinism contract as
conditional on the exact closeout claim as well as source inventory, packaging
commit, Python, and zlib runtime. Regression
`test_closeout_claim_is_part_of_archive_determinism_contract` varies only the
claim, requires different archive bytes, and checks that the manifest names
the dependency.

**Scientific handling.** Compare archive hashes only when all named
determinism inputs, including the exact closeout claim, are identical.

## EI-017 — A6 trigger replay trusted its recorded decision gap

**2026-08-19 addendum.** The analyzer-side repair below was joined by the
audit side: the shared recovery replay (`experiments/a6_replay.py`) now
derives every `gap_at_decision` chronologically from the recomputed UB and
the prior certified LB chain and never uses the recorded gap to regenerate
T1 or the certificate decision; both the audit and the analyzer consume
that one path. Coordinated regression:
`test_coordinated_decision_gap_trigger_tamper_rejected` (helper + audit)
and `test_coordinated_scheduler_gap_and_trigger_story_halts` (analyzer).

**Status: FOUND — IN PROGRESS.** Scheduler-gap anchoring is implemented on the
integration branch and awaits review and merge.

**Observed symptom and evidence.** The A6 audit regenerated `triggers_fired`
and the frozen-priority selection from each iteration's stored
`gap_at_decision`, but did not regenerate that gap itself. A coordinated edit
could set the gap to zero and add `T1` to the fired set while leaving `T4` as
the correctly selected higher-priority trigger. The trigger list, oracle copy,
and priority rule remained mutually consistent, so the old audit accepted a
scheduler state that did not follow from the preceding certified bound.

**Root cause and impact.** A scheduler input was treated as independent
evidence even though it is derived state. At iteration `k`, the only admissible
decision gap is the current clean-master UB minus the previously established
`LB_best`; before the first certified lower bound it is positive infinity. A
false gap can change whether `T1` fires and therefore change the clean versus
candidate call sequence, calls-to-certificate, and the claimed behavior of the
frozen sparse scheduler.

**Disposition and required regression.** Replay bounds chronologically, save
the prior `LB_best`, and require every A6 `gap_at_decision` to equal
`ub_ch - prior_LB_best` at evidence precision. Admit infinity only for the
initial `+infinity` case; a stored finite substitute, negative infinity, or
NaN must halt. Only after that check may the audit regenerate triggers and
their priority. `test_coordinated_scheduler_gap_and_trigger_story_halts`
must alter the gap, trigger list, and oracle copy coherently and still leave
the complete population unscored.

**Scientific handling.** A trigger stream is attributable to the frozen A6
scheduler only when both its decisions and every derived decision input
replay. Internal agreement among stored trigger labels is not sufficient.

## EI-018 — The seed pricing vector was not anchored to the frozen market

**Status: FOUND — IN PROGRESS.** Seed-price reconstruction is implemented on
the integration branch and awaits review and merge.

**Observed symptom and evidence.** The analyzer checked the seed oracle's
schedule, full/rounded price copies, and objective arithmetic, but did not
require the full seed vector to be the posted affine-market price at zero
fleet load. On a zero-charge seed schedule, every price could be changed
coherently without changing the pricing objective, physical objective, or
column contents, so all former arithmetic checks still passed.

**Root cause and impact.** Agreement among multiple copies of a value was
mistaken for an external anchor. The A2/A6 protocol fixes oracle call zero as
`market.price(zeros(n_slots))`; it is not a free producer input. A forged seed
price misstates protocol initialization, the broadcast-price trajectory, and
the economic provenance of the first retained column even when a zero load
hides the error from objective arithmetic.

**Disposition and required regression.** Rebuild the market from the frozen
instance and market identity, compute the full-precision posted vector at
zero fleet load, and require the seed oracle to use exactly that vector at
evidence tolerance. Continue to require its rounded presentation copy and the
seed column's embedded oracle statistics to agree with the full vector.
`test_coordinated_seed_price_story_must_match_posted_vector` must change every
stored price copy while preserving the zero-load objective and must halt
before scoring.

**Scientific handling.** Seed evidence establishes initialization only after
the price is regenerated from the market. A self-consistent zero-load record
does not by itself prove which price was posted.

## EI-019 — Coordinated clean-price and master edits could fabricate a CG certificate

**Status: FOUND — IN PROGRESS.** The global lower-bound guard and independent
restricted-master reconstruction are implemented on the integration branch
and await review and merge.

**Observed symptom and evidence.** Two coordinated adversarial stories passed
the earlier analyzer. First, a clean oracle used an arbitrary full price, a
different but physically valid schedule, and a jointly edited convexity dual
`sigma`, reduced costs, lower-bound history, and outcome. Every serialized
pricing objective and local arithmetic identity agreed, yet the claimed
`LB_CH` exceeded the valid Lagrangian bound at that price by orders of
magnitude. Second, a clean master transcript, `z_rmp_model`, `ub_ch`, histories,
and outcome could be lowered together. In the one-column construction the
only possible exact master objective was known from that column, but the false
low UB still closed the stored gap. The same logical gap extends to
multi-column prefixes if the master is not independently bounded.

**Root cause and impact.** Certificate replay regenerated algebra from
producer-selected prices and master scalars without checking the global
mathematical inequalities that make those scalars bounds. A clean price was
not tied to convexity-dual tightness on the retained columns, a locally
consistent reduced cost was not capped by a price-independent global
Lagrangian certificate, and the historical absence of serialized lambdas was
incorrectly treated as preventing any independent check of the restricted
master. A false clean lower bound or infeasible low UB can falsely reduce the
reported gap, stop the trace early, and change the primary endpoint.

**Disposition and required invariant.** For each chronological retained-column
prefix:

- require the clean convexity dual to equal
  `min_j(ops_cost_j + price dot load_j)` within the frozen absolute
  `RC_TOL`; this is the retained-column dual-tightness condition;
- compute `theta_cert(price) = pricing_solver_bound - conj_true(market, price)`
  and require the claimed clean `LB_CH` not to exceed that global valid lower
  bound beyond `RC_TOL`; candidate calls still may not improve `LB_best`;
- independently minimize the exact affine-quadratic restricted master over
  the retained-column simplex. The feasible Frank--Wolfe iterate is a safe
  upper bound and its Frank--Wolfe gap supplies a rigorous lower bound. Require
  convergence to `MASTER_FW_TOL`, bracket the recorded `ub_ch` and
  `z_rmp_model` with the frozen PWL tolerance, and require every claimed
  certificate to remain closed against the independently feasible upper
  bound; and
- require each stored `n_columns` to equal the chronologically reconstructed
  prefix size, including the producer's documented final-certifying-return
  behavior.

The numerical allowances above are the already frozen reduced-cost,
outer-approximation, and independent-master tolerances; they are not inferred
from the observed holdout outcomes.

**Regression expectations.** At minimum, keep
`test_coordinated_dual_sigma_story_must_be_tight_on_retained_columns`,
`test_arbitrary_clean_price_cannot_support_false_certificate`,
`test_one_column_master_ub_must_recompute_from_retained_column`,
`test_independent_master_bounds_close_on_interior_convex_combination`, and
`test_multi_column_terminal_ub_is_bounded_independently`. The multi-column
case must use a genuinely fractional optimum so that selecting the best
single column cannot accidentally satisfy the test.

**Scientific handling and evidence boundary.** These checks establish
certificate safety even though the exact producer dual vector is absent: a
valid global lower bound and an independently feasible restricted-master UB
are sufficient. They do not prove that the producer obtained its recorded
price, primal mixture, or UB through the exact historical LP/tangent path.
Report that distinction and preserve the future-recording requirements in
EI-012.

## EI-020 — Historical A4 replay cannot recover the omitted clean out-dual

**Status: FOUND — IN PROGRESS.** Derivable A4-state replay and its explicit
evidence limitation are implemented on the integration branch and await
review and merge.

**Observed symptom and evidence.** A6-A4 candidate events store the candidate
price, certified pricing bound, serious/null label, direction signal, alpha
transition, and final stabilization state. The earlier analyzer counted some
of those labels but did not recompute their deterministic relationships. It
also risked describing such a replay as proof of the complete Wentges
mechanism path even though the candidate's contemporaneous clean-RMP out-dual
`pi_out` was never serialized.

**Root cause and impact.** The recorder persisted derived mechanism outputs
but omitted one of the inputs needed to anchor the candidate price to the
actual clean master. Given the stored candidate price, prior center, and
alpha, an auditor can algebraically infer an out point and replay the remaining
updates; it cannot prove that the inferred point is the clean dual actually
returned in that iteration. Without this distinction, correct transition
arithmetic could be overstated as exact algorithm-fidelity evidence.

**Disposition and required regression.** Starting from the frozen A4 initial
state, replay clean-point `theta_best` updates and, for every candidate,
recompute `theta_cert`, serious/null classification, direction signal, alpha
before/after, center movement, counters, and the final stabilization state.
Require a positive producer-generated trace containing at least one real A4
candidate, not only a hand-written zero-candidate fixture, and coordinated
tamper tests such as
`test_coordinated_a6_a4_serious_counter_story_is_rejected`. The code and
summary must state that these candidate transitions are conditional on the
serialized candidate price. Future records must persist `pi_out` (and the
corresponding clean-master identity) to permit an unconditional candidate
price-path replay.

**Scientific handling.** It is valid to report recomputed A4 diagnostics and
state transitions conditional on the recorded candidate prices. It is not
valid to claim that the closeout independently reproduced the exact historical
A4 dual-generation path. This limitation does not weaken the separate global
certificate-safety checks in EI-019 because candidate calls never create the
certified lower bound.

## EI-021 — A6 recovery bounds and requested pricing-gap state were not replayed

**Status: FIXED — regression-covered.** The complete recovery-state replay
is implemented as the shared pure helper `experiments/a6_replay.py`, used
by both the audit and the production analyzer.

**Observed symptom and evidence.** The scheduler audit reconstructed whether
recovery was active and whether its kind was `duplicate`, `ambiguous`, or
`refinement`, but it did not reconstruct the bounded counters that govern
those branches. It also did not verify each clean iteration's requested
`pricing_max_mip_gap`, the divide-by-100/floor progression after ambiguity, or
the final checkpoint scheduler/counter state. A mutually consistent stream of
trigger and recovery-kind labels could therefore contain more retries than the
producer is allowed to commit, or claim a different pricing-gap escalation
path, without failing the old replay.

**Root cause and impact.** The audit replayed the scheduler's categorical
state but not its complete state machine. The frozen A6 algorithm has bounded
duplicate and refinement retries, bounded pricing escalations, deterministic
counter resets after a novel improving column, and a deterministic requested
MIP-gap update after an ambiguous clean call. Those are stopping and failure
rules, not diagnostics. Accepting an over-cap trace fabricates oracle calls
that the implementation should have rejected before commit and can directly
change calls-to-certificate, recovery frequency, and the primary comparison.

**Disposition and required regression.** Reconstruct from the seed forward:
`duplicate_retries`, `refine_retries`, `pricing_escalations`,
`pricing_max_mip_gap`, clean/candidate counters, `k_since_clean`, number of
clean pricing calls, last-candidate novelty, and recovery kind. Apply the
frozen reset/increment rules after each clean result; enforce
`MAX_DUPLICATE_RETRIES`, `MAX_PRICING_ESCALATIONS`, the configured gap divisor,
and the `1e-12` floor at the exact pre-commit boundary used by the producer.
Require every iteration's requested pricing gap and the completed
checkpoint's counters, scheduler object, and recovery-at-end outcome flag to
equal the replayed state. A coordinated regression must edit all visible
recovery labels and counters into an internally consistent over-cap trace and
still halt; separate cases must alter the divide-by-100 gap sequence and only
the final scheduler state.

**Scientific handling.** A recovery-labeled call stream is not evidence of
the frozen A6 algorithm until every bounded counter and requested solver-gap
transition replays. Until the complete state machine and adversarial tests are
reviewed, do not score its oracle-call count.

## EI-022 — Inode recycling defeated (dev, ino) ownership signatures

**Status: FIXED — regression-covered.**

**Observed symptom and evidence.** During integration testing of the
rollback-competitor regressions, an `unlink` immediately followed by a
re-create of the same path received the SAME inode number from the
filesystem (observed live on tmpfs). Ownership checks keyed on
`(st_dev, st_ino)` therefore classified a foreign replacement file as the
owned original, and import rollback destroyed operator-owned replacement
content instead of freezing it for review.

**Root cause and impact.** POSIX permits immediate inode reuse after the
last link drops. A 2-tuple identity is an ABA-vulnerable signature: any
"remove then recreate" replacement can silently reacquire the identity of
the file it replaced. Every rollback and publication gate keyed on the
2-tuple — installed-tree files, staging records, publication markers, the
import lock, and the transfer receipt — could remove or trust a
same-inode competitor.

**Disposition and required regression.** Regular-file ownership signatures
are now `(st_dev, st_ino, st_size, st_mtime_ns)`
(`package_a6_holdout._regular_signature`). Exact guarantee: a replacement
or rewrite is detected whenever it differs in byte length OR in
nanosecond mtime; kernels set `st_mtime_ns` on every write and creation,
so unlink+recreate and content rewrites are detected unless a same-UID
adversary deliberately restores both the exact length and the exact
nanosecond timestamp (`utimensat`) — outside the cooperative trust
boundary. Hard-linking/unlinking OTHER names changes neither field, so
the receipt link dance stays valid. Marker and import-lock signatures are
captured AFTER their final payload writes. Directory signatures remain
2-tuples (rollback safety for directories is enforced by population and
rmdir-on-nonempty semantics). Honest boundary: a malicious same-UID
process can restore mtime with utimensat; that adversary is outside the
documented cooperative-namespace trust boundary. Regressions:
`test_target_competitor_during_rollback_is_preserved_with_lock`,
`test_receipt_competitor_during_rollback_is_preserved_with_lock`, and
`test_install_staging_replacement_before_rename_gate_rejected` (an
unlink+rewrite of a nested staging file — inode reuse included — must be
caught by the pre-rename gate and preserved as evidence).

**Scientific handling.** No published artifact relied on the vulnerable
check; the gap was found and fixed before this integration branch became
scoreable.

## EI-023 — Analyzer publication forked from the package contract

**Status: FIXED — regression-covered.**

**Observed symptom and evidence.** `analyze_a6_holdout` carried its own
publication implementation: an exclusive-`mkdir` reservation populated by
per-file hard links, with staging removed via a blind `shutil.rmtree` in a
`finally` block. The package module had already converted to the native
atomic no-replace directory rename (`renamex_np`/`RENAME_EXCL` on macOS,
`renameat2`/`RENAME_NOREPLACE` on Linux) with an anchored
`.publication-incomplete` marker; the analyzer had not, and its blind
rmtree could destroy foreign or replaced staging entries on failure.

**Root cause and impact.** Two publication implementations drifted. The
analyzer's reservation window (mkdir, then link-in files) is not atomic;
its cleanup did not distinguish proven-owned inodes from foreign entries;
and no final revalidation ran between population and marker removal.

**Disposition and required regression.** The analyzer now publishes
through the ONE shared `publish_flat_directory_no_replace`, passing a
final raw-tree/receipt/analysis-claim revalidation callback; a second
ownership gate runs after the callback, immediately before the marker
unlink. The marker unlink is the final LOGICAL commit: fallible steps do
follow it (descriptor close, and the unlink syscall itself can fail after
removing the marker), but none of them may reclassify a verifiably
markerless committed destination as incomplete — commit state is tracked
explicitly (pre-rename / renamed-with-marker / committed) and marker
presence is inspected through the anchored descriptor. Staging
artifacts are ownership-recorded as they are written; failure cleanup
removes only proven-owned inodes and otherwise PRESERVES the staging tree
for incident review. Regressions:
`test_analyzer_publication_parity_with_package`,
`test_analyzer_revalidation_failure_preserves_marker`,
`test_output_publication_post_rename_mutation_fails_closed`,
`test_output_publication_race_never_replaces_appearing_path`,
`test_unmanifested_analysis_artifact_blocks_publication` (preserved
staging), and `test_atomic_output_failure_leaves_no_final_or_staging`
(owned cleanup).

**Scientific handling.** Publication mechanics only; no scientific tables
were derived from a mispublished directory.

**2026-08-19 addendum (truthful exception metadata and four commit states).**
A later adversarial pass found that the three-state description above was
insufficient (see EI-024): the publisher now distinguishes four states —
`pre-rename`, `renamed-guarded`, `commit-unlink-in-flight`, and `committed`
— and marker absence proves commit only from `commit-unlink-in-flight`. In
addition, `install_tree_no_replace`'s post-rename failures now populate the
full `IncompletePublicationError` contract (`renamed=True`,
`destination=<target>`, `committed=False`) instead of a bare message, so a
caught import failure after the exclusive rename is truthfully attributable.
Regression coverage:
`test_install_tree_post_rename_error_carries_truthful_metadata` and
`test_install_tree_pre_rename_error_leaves_no_target`.

## Regression-coverage map: EI-017 through EI-023

| incident | repair | regression coverage |
|---|---|---|
| EI-017 (trusted decision gap) | bounds rebuilt chronologically in `_replay_cg_certificate_evidence` | `test_a6_holdout_analysis.py` trigger/bound replay battery |
| EI-018 (seed prices unanchored) | seed vector rebuilt from the frozen market | seed-anchor tamper tests in `test_a6_holdout_analysis.py` |
| EI-019 (coordinated price/master edits) | independent exact restricted-master bracket | independent-master and coordinated-edit tests in `test_a6_holdout_analysis.py` |
| EI-020 (A4 out-dual omitted) | conditional replay + evidence limitation #2 | conditional A4 replay tests; limitation asserted in SUMMARY/MANIFEST/package metadata |
| EI-021 (recovery counters not replayed) | shared `experiments/a6_replay.py` used by audit AND analyzer | `test_a6_recovery_replay.py` (real recovery trace; coordinated /100 and cap tampers; final-state tampers) + analyzer rejections in `test_a6_holdout_analysis.py` |
| EI-022 (inode recycling) | `(dev, ino, size, mtime_ns)` signatures | rollback-competitor and staging-replacement regressions in `test_a6_holdout_package.py` |
| EI-023 (analyzer publication fork) | one shared no-replace publisher + owned staging cleanup | publication parity/revalidation/mutation regressions in `test_a6_holdout_analysis.py` |

## EI-024 — Precommit incomplete-marker deletion was misclassified as a completed publication

**Status: FOUND — IN PROGRESS.** The four-state publisher machine and safe
marker restoration are implemented on this branch with regression coverage,
pending independent review; until reviewed and merged, do not treat a
markerless destination as self-proving evidence of a committed publication.

**Observed symptom and evidence.** A new adversarial pass against `a6bb350`
reproduced the following against `publish_flat_directory_no_replace`: a
`revalidate` callback that corrupts an expected artifact and deletes the
`.publication-incomplete` marker, then returns, was misread as a successful
commit. The post-revalidation ownership gate detected the changed artifact
and missing marker and raised, but the outer handler — in state
`renamed-with-marker` — saw the marker absent and treated absence as proof
that the publisher's own commit unlink had already succeeded, re-raising an
ordinary `PackagingError`. The destination was left markerless with
`A.txt` = `CORRUPT`, so the corrupt directory appeared complete. Captured
before/after evidence: the same edit produced a markerless corrupt directory
plus an ordinary error before the repair, and a restored blocking marker plus
a truthful `IncompletePublicationError` after it.

**Root cause and impact.** The commit state machine conflated two distinct
ways the guard marker can vanish. Marker absence is proof of commit only when
the publisher's OWN unlink was in flight; a callback that removes the marker
before that point is corruption, not commit. A three-state machine
(`pre-rename`, `renamed-with-marker`, `committed`) cannot tell them apart, so
a precommit guard deletion produced an apparently complete, markerless,
possibly corrupt publication behind an ordinary error — exactly the state the
anchored marker exists to prevent.

**Required invariant and regression.** Use four distinguishable states:
`pre-rename`, `renamed-guarded`, `commit-unlink-in-flight`, and `committed`.
Set `commit-unlink-in-flight` immediately before the publisher's own marker
unlink; marker absence may prove commit only from that state. Marker absence
in `renamed-guarded` is corruption: restore a blocking marker through the
anchored directory fd (`O_CREAT | O_EXCL | O_NOFOLLOW`, a regular file with
one link, contents exactly `incomplete\n`, marker and directory fsynced,
never overwriting or unlinking a competitor-created path), preserve every
artifact and foreign entry, and raise a louder incomplete/corrupt-publication
error with truthful `renamed`/`destination`/`committed` metadata; if
restoration loses a race, preserve the competitor path and fail louder. The
destination must never be left markerless because a callback removed the
guard before the commit attempt. Regression coverage in
`test_a6_holdout_package.py`:
`test_precommit_marker_deletion_is_corruption_not_commit` (four cases:
marker-only vs. corrupt-artifact, each with and without a trailing callback
exception) and `test_precommit_marker_restore_race_preserves_competitor`. The
retained pre-existing cases (mutation without marker deletion,
unlink-removes-then-raises, exception after the publisher's own unlink,
target replacement, and post-commit descriptor-close) still pass.

**Scientific handling.** A markerless destination produced by the old
three-state path is not proof of a committed publication; it may be a
precommit-corrupted directory. Preserve any restored marker and the corrupt
or foreign evidence for incident review; never delete a marker or artifact to
make a directory look complete.

## EI-025 — A6 shared replay omitted terminal/final outcome closure

**Status: FOUND — IN PROGRESS.** The terminal/final/outcome closure is
implemented in the shared helper `experiments/a6_replay.py` (used by both the
audit and the production analyzer) with regression coverage, pending
independent review; until reviewed and merged, the operational audit's
acceptance of a completed A6 trace is not sufficient certificate evidence on
its own.

**Observed symptom and evidence.** A new adversarial pass against `a6bb350`
reproduced three coordinated edits that the shared recovery replay
(`replay_a6_recovery`) and the audit (`_cg_sane`) accepted, even though the
strict production analyzer rejected them downstream: (1) a derived-certified
trace whose `outcome.certified` was flipped to `False`; (2) a trace whose
top-level checkpoint `lb_best` and outcome LB/gap were coherently inflated by
`5e-4`; and (3) a fake terminal event plus matching history entries appended
after a certificate had already been derived. Captured before/after evidence:
helper and audit both accepted all three before the closure and reject all
three after it.

**Root cause and impact.** The shared helper replayed the recovery/counter
state machine but stopped short of closing the terminal and final/outcome
state. It handled a terminal event before rejecting post-certificate events,
never bound the number of terminal events to the completion type, and never
compared the top-level `lb_best`, column count, history lengths, or the
outcome (`type`, `certified`, `ub_ch`, `lb_best`, `gap`, `oracle_calls`,
`method`) against the replay. The operational audit therefore called
impossible producer traces sane and the helper claimed a complete replay it
had not performed.

**Required invariant and regression.** In the one shared chronological path,
reject every event after a derived certificate (including a terminal event);
require zero terminal events for certified completion and exactly one final
terminal event for budget-exhausted completion; replay and validate the
terminal master's `n_columns`, `lb_best`, and its UB/LB history entry; and
compare the top-level checkpoint `lb_best`, column count, and history lengths
plus the outcome (`type`, `certified` as an exact boolean, `ub_ch`,
`lb_best`, `gap`, `oracle_calls`, `method`, and recovery-at-end) against the
replay.

Oracle-call provenance is closed completely (F1): every oracle event carries
a present, unique call ID; `replay_calls` — one seed call plus one call per
priced iteration — must equal, as exact integers, `len(oracle_events)`,
`checkpoint.oracle_calls`, and `outcome.oracle_calls`; each priced iteration
binds its chronological `oracle_calls` index and the terminal event binds the
total count; and the non-seed oracle events are in one-to-one correspondence
with the priced iterations (orphan events, reused event IDs, and missing
events are all rejected). Because `outcome.oracle_calls` is now bound in the
shared audit path, arm selection no longer fabricates it: the selection
regression keeps every checkpoint coherent and injects synthetic scores by
monkeypatching `select_a6_arm.cell_score`, not by corrupting scientific
evidence.

Additionally, cross-link each clean call's oracle-event
`min_reduced_cost_ub`/`min_reduced_cost_lb` and every call's `column_novel`
with the corresponding iteration fields; oracle and iteration evidence may
not disagree. No second replay implementation was added; the audit and the
analyzer stay on the same authoritative path. Regression coverage in
`test_a6_recovery_replay.py`: `test_e2_flip_outcome_certified_after_derived_certificate`,
`test_e2_coordinated_lb_gap_inflation_rejected`,
`test_e2_terminal_after_certificate_rejected`,
`test_e2_budget_terminal_deleted_rejected`,
`test_e2_second_budget_terminal_rejected`,
`test_e2_falsified_terminal_lb_best_rejected`,
`test_e2_falsified_terminal_n_columns_rejected`,
`test_e2_oracle_iteration_reduced_cost_disagreement_rejected`, and
`test_e2_oracle_iteration_novelty_disagreement_rejected`, with the analyzer
consuming the same rejections in `test_a6_holdout_analysis.py`. Oracle-call
provenance (F1) is covered by `test_f1_outcome_oracle_calls_edit_rejected`,
`test_f1_checkpoint_oracle_calls_edit_rejected`,
`test_f1_iteration_oracle_calls_index_edit_rejected`,
`test_f1_terminal_oracle_calls_edit_rejected`,
`test_f1_orphan_oracle_event_rejected`,
`test_f1_reused_oracle_call_id_rejected`, and the `_cg_sane` regression
`test_f1_cg_sane_rejects_outcome_oracle_calls_edit`, all in
`test_a6_recovery_replay.py`; and end-to-end by
`test_selection_aborts_on_outcome_oracle_calls_edit` in `test_a6.py`
(a one-field `outcome.oracle_calls` edit aborts arm selection).

**Scientific handling.** A completed A6 trace is attributable to the frozen
algorithm only when its terminal/final/outcome closure replays, not merely
when its recovery counters do. The strict production analyzer already
rejected these edits, so no packaged science depended on the gap; but until
the shared-helper closure is reviewed and merged, the operational audit's
"complete and sane" verdict must not be cited as an independent certificate.

## Regression-coverage map: EI-024 through EI-025

| incident | repair | regression coverage |
|---|---|---|
| EI-024 (precommit marker deletion misclassified) | four-state publisher machine (`renamed-guarded` / `commit-unlink-in-flight`) + safe marker restoration through the anchored fd + truthful `install_tree_no_replace` metadata | `test_precommit_marker_deletion_is_corruption_not_commit`, `test_precommit_marker_restore_race_preserves_competitor`, `test_install_tree_post_rename_error_carries_truthful_metadata`, `test_install_tree_pre_rename_error_leaves_no_target` in `test_a6_holdout_package.py`; retained publisher edge-case tests still pass |
| EI-025 (replay terminal/final closure omitted) | terminal/final/outcome closure + full oracle-call provenance (F1: exact-integer `replay_calls == len(oracle_events) == checkpoint.oracle_calls == outcome.oracle_calls`, per-iteration/terminal index binding, one-to-one event↔iteration) + oracle/iteration cross-link in the shared `experiments/a6_replay.py` (audit AND analyzer) | `test_e2_*` and `test_f1_*` batteries (including `test_f1_cg_sane_rejects_outcome_oracle_calls_edit`) in `test_a6_recovery_replay.py`, `test_selection_aborts_on_outcome_oracle_calls_edit` in `test_a6.py`, + analyzer rejections in `test_a6_holdout_analysis.py` |
| import post-commit close (EI-007 addendum) | explicit `import_committed` state guards descriptor-close reporting | `test_import_descriptor_close_after_commit_is_not_a_failure`, `test_import_descriptor_close_before_commit_is_reported` in `test_a6_holdout_package.py` |

## EI-026 — Split tolerance scales aborted a claimed A6 holdout pack mid-validation

**Status: FOUND — IN PROGRESS.** The tolerance/certificate repair (Task A) and
the one-shot claimed-incident recovery command (Task B) passed independent
review and merged through PR #33 with regression coverage. The recovery
disposition remains IN PROGRESS until the reviewed recovery command has been
successfully used to repackage the claimed incident. The original claim and raw
tree must never be deleted or rewritten.

**Operational history.** An earlier `squeue` quiescence check failed from a
non-login shell (its Slurm client path was unavailable) **before** any claim
existed. The subsequent interactive packaging attempt created the source-side
`a6_holdout.CLOSEOUT_CLAIM.json` and then **failed during frozen scientific
validation** — specifically the certificate replay of one clean pricing event.
**No audit, archive, manifest, sidecar, bundle, decision, or score was
emitted, and no final package directory was created.** The exclusive claim
therefore remains on disk as a deliberate fail-closed recovery marker.

**Observed symptom and exact evidence.** Cell/event `a2 seed=16 n=12 b=0.01`,
iteration `a2-it31`, GRB / python-mip 1.17.6, OPTIMAL:

- original packaging/claim commit `740ab0c1578b454268102c0bb15b1104d9ac8d9d`;
- original claim SHA-256
  `1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675`;
- claimed source-tree SHA-256
  `2c60b3d2feb1f313cb08541556d5e8f95bf40dc76b2c539d78149dd93ad88749`;
- implicated checkpoint SHA-256
  `dc7a948a6966f20e6f25b9a8744a937741a7973e9c2ad64622b71512658f7669`;
- solver bound `3255.503129856506`;
- solver model incumbent `3255.503129876505` (model minus bound
  `+1.9999333744635805e-08`);
- reconstructed physical incumbent `3255.503129796989` (physical minus model
  `-7.951621228130534e-08`);
- raw physical gap `-5.951687853666954e-08` (recorded gap exactly equals the
  recomputed raw gap);
- operand-scaled tolerance `3.255503129856506e-07`;
- erroneous derived-gap/zero tolerance `1e-10`.

**Root cause.** `_replay_cg_certificate_evidence` first accepted the
bound/incumbent equality with an operand-scaled tolerance
`1e-10 * max(1, |bound|, |incumbent|) ≈ 3.26e-7`, then compared the small
derived gap `incumbent - bound` against zero with a scale of ≈ 1
(`1e-10 * max(1, |gap|, 0) = 1e-10`). The same numerical relationship therefore
passed the first gate (`|bound - incumbent| ≤ 3.26e-7`) and failed the second
(`|gap| = 5.95e-8 > 1e-10`), aborting the claimed pack even though bound and
incumbent are equal to solver precision at this ≈ 3255 magnitude.

**Invariant and reviewed repair (Task A).** One shared operand-scaled
ordering helper (`analyze_a6_holdout._ordering_tolerance`) is the sole authority
for ordering two solver quantities of the same magnitude; the derived gap is
judged against zero at that SAME operand scale. A negative raw pricing gap is
admitted only within that tolerance (derived from the original incumbent/bound
operands) and rejected beyond it; the recorded RAW absolute/relative gaps are
preserved and validated exactly, and a within-tolerance negative gap normalizes
to zero for diagnostic gap semantics only. Certification is not silently
strengthened: a SEPARATE conservative safety chain reduces the bound by the
operand tolerance (`bound - tau`), re-derives safe min-reduced-cost/LB-best, and
requires the terminal certificate to remain `<= epsilon`, kept independent of
the producer-trace replay. All existing coordinated bound-inflation/tamper
rejections are preserved, and the audit (`_cg_sane`) applies the SAME
operand-scaled ordering for parity. Regressions in `test_a6_holdout_analysis.py`
cover the exact EI-026 scalar case (numerical equality), just-inside/just-outside
tolerance at small and large scales, the full raw/model/physical
reconstruction, the exact raw-recorded-gap check, the conservative safe chain
(certifies or fails honestly), the retained inflated-bound rejection, and
audit/analyzer parity.

**One-shot recovery (Task B).** Normal `pack` still refuses the existing claim.
A separate, explicit **EI-026-only** recovery command
(`package_a6_holdout.recover_package_holdout` / `recover-pack`), never a generic
bypass, requires the full original claim SHA and incident ID `EI-026`; opens the
original claim as canonical, regular, single-link immutable evidence and
verifies its schema, SHA, original commit, launch identities, and claimed source
digest/count/bytes; requires a clean recovery HEAD equal to the recovery commit
with `740ab0c` as an ancestor; verifies the live raw tree still exactly matches
the original claim before any outcome validation; prepares and validates the
package output container (rejecting a file, symlink, unsafe nesting, or
uncreatable path) before consuming the one-shot recovery; exclusively creates a second
adjacent `a6_holdout.RECOVERY_CLAIM.json` (binding EI-026, the original claim
SHA/commit, the raw-tree digest, the recovery commit, and the failure
fingerprint) before validation, with exactly one recovery attempt permitted;
never modifies or replaces the original claim or raw root; uses fresh staging
only; checks Slurm quiescence before reading and again immediately before
publication; and records a versioned bundle-manifest/import-receipt/analyzer
contract (`…-v3-recovery` / `…-v2-recovery`) carrying the original claim
commit+SHA, the recovery claim commit+SHA, the experiment commit, and the actual
corrected packaging/analysis commit. The manifest/import/analyzer validators
require exact recovery-envelope and recovery-document key sets and bind schema,
status, base/experiment/packaging commits, launch identity, raw-tree digest,
failure fingerprint, and closeout-to-recovery chronology; merely rehashing a
semantically altered recovery document is insufficient. Import requires HEAD to
equal the recovery commit while separately verifying both immutable claims. Any recovery failure is
fail-closed, and a second recovery claim blocks all further attempts. Adversarial
regressions in `test_a6_holdout_package.py` cover wrong/missing/mutated/linked
claim, source drift, dirty/non-descendant recovery HEAD, wrong incident ID, an
existing recovery claim, an active Slurm job, destination HEAD mismatch, recovery
failure preservation, pre-claim output-file/symlink refusal, coordinated
recovery-document rehashing, that normal `pack` still refuses, and a complete
synthetic recover-pack/import/analyzer round trip.

**Scientific handling.** The original claim and raw tree are immutable incident
evidence and must never be deleted or rewritten. No score, decision, or artifact
was produced by the aborted attempt. Although the repair is reviewed and
merged, EI-026 remains IN PROGRESS and no packaged scientific result may be
cited from this campaign until the recovery command has successfully
repackaged the claimed incident under the versioned contract.

## EI-027 — Physical-incumbent reconstruction adjustment exceeded the operand tolerance and aborted the EI-026 recovery pack

**Status: FOUND — IN PROGRESS.** The numerical repair (Task A), the
second-stage recovery machinery (Task B), and this entry are implemented
on an unmerged branch with regression coverage; the status flips to FIXED
only after independent review, merge, and a successful second-stage
recovery repackaging. No operator command is published until then.

**Frozen evidence.**

- cell: `a2 seed=22 n=12 b=0.01`, iteration 24
- checkpoint SHA-256:
  `b9b58dfbc0042f49fb37637284e9ac98beae1bf5c7c612487555d9480fd25fda`
- solver bound = solver model incumbent = `2417.583855389641`
- physical incumbent = `2417.583844628412`
- model-to-physical reconstruction adjustment = `1.0761229077616008e-05`
- operand tau = `2.4175838553896413e-07`
- original claim SHA-256:
  `1b0acf0b8232d4b08e764564e2732fcfa9c28dd53456a1415085b77cb38f6675`
- first recovery claim SHA-256:
  `88c22f06ce6bc8dcff56c0d6737c91bbd39fe8da79c2b6ba6d2a987b6b6abe88`
- first recovery commit: `b81b15ace8ffd7301ce93f349fdb643cdefd5da6`
- raw source-tree SHA-256:
  `2c60b3d2feb1f313cb08541556d5e8f95bf40dc76b2c539d78149dd93ad88749`

**Observed symptom and evidence.** The one-shot EI-026 recovery pack
(`recover-pack`, first recovery claim above) aborted during certificate
replay on the cell above: the certified solver bound EXACTLY equals the
solver model incumbent (ordering trivially satisfied at operand tau), but
the PHYSICAL incumbent — the exact reconstructed objective of the
retained column — sits `1.0761229077616008e-05` BELOW the bound, which
exceeds the operand-scaled tolerance `2.4175838553896413e-07` by two
orders of magnitude. The EI-026 gate `bound <= physical_incumbent +
operand_tau` therefore rejected a legitimate record, and the recovery
attempt was consumed.

**Root cause and impact.** The model-to-physical objective
reconstruction (`pricing_objective_reconstruction.abs_adjustment`,
recorded by the producer) legitimately moves the physical incumbent away
from the model incumbent by more than the operand tolerance; treating
the physical incumbent as if it had to sit within operand tau of the
bound conflates solver arithmetic (bound vs model incumbent) with
reconstruction arithmetic (model vs physical objective). No incorrect
science was published — the pack failed closed — but the one-shot
EI-026 recovery claim is burned, so a second-stage mechanism is required
to repackage.

**Disposition (Task A — numerical root cause).** ONE shared pure gate
(`pricing_order_gate`, used by both the audit and the analyzer):
bound-versus-model-incumbent ordering stays governed by `operand_tau`;
`reconstruction_adjustment` is recomputed EXACTLY as
`abs(model_incumbent - physical_incumbent)`; the
`physical_bridge_allowance = operand_tau + reconstruction_adjustment`;
required orderings are `bound <= model_incumbent + operand_tau` AND
`bound <= physical_incumbent + physical_bridge_allowance`; claim-bearing
safe bounds use `safe_bound = bound - physical_bridge_allowance`. Raw
pricing gaps and recorded reconstruction fields are preserved exactly
(negative raw gaps admitted only within the bridge allowance). Every
claim-bearing output schema is version-bumped
(`a6-holdout-closeout-v4-physical-bridge`) and the formula is documented
in the emitted SUMMARY and manifest policy blocks. The exact frozen
scalars above are a regression with audit/analyzer parity; all raw-only
certificate rejections and inflated-bound tamper protections are
preserved (a coordinated model-incumbent tamper is now caught by the
exact reconstruction binding instead of the ordering gate).

**Disposition (Task B — recovery-after-recovery).** The EI-026
`recover-pack` one-shot refusal remains intact and is never weakened or
reused. A separate EI-027-only second-stage command
(`recover2-pack` / `recover2_package_holdout`) exclusively creates a
distinct `a6_holdout.RECOVERY2_CLAIM.json`; it freezes and validates the
exact original claim and first-recovery-claim hashes, documents,
commits, source digest, and incident identities; binds the COMPLETE
original, recovery-1, and recovery-2 claims into the versioned
`a6-holdout-transfer-bundle-v4-recovery2` /
`a6-holdout-transfer-receipt-v3-recovery2` / import / analyzer contract;
validates and prepares output paths BEFORE consuming the RECOVERY2
claim; requires a clean HEAD, the reviewed ancestry chain
(`740ab0c -> b81b15a -> 74a9c5d -> HEAD`), Slurm quiescence twice, an
unchanged raw tree, and the absence of any existing matching final
package; and revalidates all three claims immediately before
publication. NO third attempt or generic bypass exists. Adversarial
regressions cover coordinated rehash, mutation, chronology, ancestry,
output paths, preexisting packages, and a full synthetic round trip
through packaging, import, and the analyzer receipt contract.

**Scientific handling.** No outcome was scored; the failed pack and the
burned first recovery claim are preserved as immutable evidence. The
operator command is NOT published in the runbook until this branch is
independently reviewed and merged.
