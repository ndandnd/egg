# Cursor handoff: finish PR #28 A6 engineering closeout

Date: 2026-08-19 (America/New_York)

This handoff is for a fresh Cursor agent. Read it completely before changing
anything. Continue the existing branch and pull request; do not create a new
implementation, branch, or PR.

## Exact Git state

- Repository: `https://github.com/ndandnd/egg`
- Draft PR: https://github.com/ndandnd/egg/pull/28
- Branch: `agent/a6-closeout-package-integration`
- Reviewed implementation baseline: `a6bb350494a01f4889f74c52b8c08d5ffc993816`
- The remote head may be one documentation-only commit later if this handoff
  itself was committed for a cloud agent. No production change after the
  reviewed baseline is authorized unless separately inspected.
- Base: `main` at `92c38a64bed6735eddb2f79dd292d8af9e244559`
- Last two amendment commits:
  - `018f28f Close EI-017 audit gap; explicit publication commit states; no post-commit import I/O`
  - `a6bb350 Incident ledger sync and pipeline-based evidence tests`

Start with:

```bash
set -euo pipefail

git fetch origin
git switch agent/a6-closeout-package-integration
git pull --ff-only origin agent/a6-closeout-package-integration

REVIEWED="a6bb350494a01f4889f74c52b8c08d5ffc993816"
git merge-base --is-ancestor "$REVIEWED" HEAD
test "$(git merge-base HEAD origin/main)" = \
  "92c38a64bed6735eddb2f79dd292d8af9e244559"
git diff --name-status "$REVIEWED"..HEAD
git status --short --branch
```

If the remote branch has advanced beyond `a6bb350`, inspect those new commits
before applying this handoff. Proceed only when the sole intervening change is
this handoff file; otherwise reconcile the new production work explicitly. Do
not reset, clean, or discard any uncommitted user files.

## Scientific boundary

- Do not launch anything.
- Do not inspect, summarize, score, hash-select, or otherwise look at A6 holdout
  outcome values.
- Do not touch raw `src/runs/a6_holdout` data or any transferred holdout bundle.
- This task is engineering closeout only.
- Preserve all three historical evidence limitations verbatim in emitted
  artifacts and documentation.

The following protected files must remain byte-identical to base `92c38a6`:

```text
src/egglab/a6.py
src/egglab/b2a2.py
src/egglab/b2a345.py
src/egglab/evsp.py
src/experiments/run_a6_holdout.py
src/experiments/select_a6_arm.py
```

## What is already correct at `a6bb350`

Do not reimplement or weaken these repairs:

1. The shared A6 replay chronologically derives the decision gap from the
   current UB and prior certified LB rather than trusting `gap_at_decision`.
2. Scheduler and recovery constants are pinned to producer constants; boolean
   fields and the positive-infinity boundary are strict.
3. The publisher rechecks ownership after `revalidate()` and has explicit
   publication-state metadata.
4. Receipt SHA-256 is retained under the import lock rather than recomputed
   afterward.
5. Evidence-language tests run miniature pipelines and inspect emitted files.
6. EI-021 through EI-023 are indexed and regression-covered.
7. Baseline verification at this head is `518 passed`; `git diff --check` and
   cluster-script `bash -n` are clean; the six protected files have zero drift.

The prior review independently reproduced those properties. The remaining
work below comes from a new adversarial pass against `a6bb350` itself.

## Remaining blocker E1: missing marker before commit is misclassified

Severity: P1. PR #28 must not merge until this is fixed.

Location: `src/experiments/package_a6_holdout.py`, around the outer exception
handler in `publish_flat_directory_no_replace` (approximately lines 1007-1014
at `a6bb350`).

Current state names are effectively `pre-rename`, `renamed-with-marker`, and
`committed`. The handler assumes that an absent marker while in
`renamed-with-marker` means the publisher's commit unlink succeeded. That is
false when the marker disappeared before the publisher attempted commit.

### Reproduced exploit at `a6bb350`

```python
def mutating_revalidate():
    (target / "A.txt").write_text("CORRUPT\n")
    (target / ".publication-incomplete").unlink()

publish_flat_directory_no_replace(
    staging,
    target,
    expected_names={"A.txt", "BUNDLE_MANIFEST.json"},
    revalidate=mutating_revalidate,
)
```

Observed behavior:

- the post-revalidation ownership gate detects the changed artifact and missing
  marker;
- the outer handler sees the missing marker and re-raises ordinary
  `PackagingError`;
- the destination is left markerless;
- `A.txt` contains `CORRUPT`;
- the corrupt directory therefore appears complete.

### Required state machine

Use four distinguishable states:

```text
pre-rename
renamed-guarded
commit-unlink-in-flight
committed
```

Set `commit-unlink-in-flight` immediately before the publisher's own marker
unlink call. Marker absence may prove commit only from that state.

Marker absence in `renamed-guarded` is corruption, never commit. The code still
holds the anchored directory FD. Restore a blocking marker safely through it:

- open relative to the anchored FD with `O_CREAT | O_EXCL | O_NOFOLLOW`;
- require a regular file with one link;
- write exactly `incomplete\n`;
- flush and fsync the marker;
- fsync the directory;
- never overwrite or unlink a competitor-created path.

If marker restoration loses a race or cannot be proved owned, preserve every
artifact and foreign entry and raise a louder incomplete/corrupt-publication
error. The destination must never be left markerless merely because a callback
removed the guard before the commit attempt.

### Required E1 regressions

Add all four cases:

1. `revalidate` removes only the marker and returns.
2. `revalidate` corrupts an expected artifact, removes the marker, and returns.
3. Case 1 followed by a callback exception.
4. Case 2 followed by a callback exception.

Every case must assert:

- the real renamed destination remains preserved;
- the corrupt/foreign evidence remains preserved;
- a blocking incomplete marker exists again, unless a competitor won marker
  creation, in which case its path is preserved and the failure is louder;
- the error truthfully reports `renamed=True`, `committed=False`, and the exact
  destination;
- no apparently complete markerless corrupt directory remains.

Retain the existing successful tests for mutation without marker deletion,
unlink-removes-then-raises, exception after the publisher's own unlink, target
replacement, and post-commit descriptor-close failure.

## Remaining blocker E2: replay does not close terminal/final state

Severity: P2, but fix before merge because `_cg_sane` still calls impossible
producer traces sane and the helper claims a complete replay.

Location: `src/experiments/a6_replay.py`, especially terminal handling around
lines 156-177 and final comparisons around lines 394-447 at `a6bb350`.

### Reproduced audit acceptances at `a6bb350`

The shared helper and `_cg_sane` still accept each of these coordinated edits:

1. A derived-certified trace whose `outcome.certified` is changed to `False`.
2. A trace whose top-level checkpoint `lb_best` and outcome LB/gap are
   coherently inflated by `5e-4`.
3. A fake terminal event plus matching history entries appended after a
   certificate was already derived.

The strict production analyzer rejects them later, so packaged science remains
protected, but the operational audit and the shared-helper contract are wrong.

### Required E2 replay closure

- Reject every event after a derived certificate, including a terminal event.
- Require zero terminal events for certified completion.
- Require exactly one final terminal event for budget-exhausted completion.
- Replay and validate terminal `n_columns`, `lb_best`, UB history, LB history,
  counters, and history lengths.
- Compare final top-level checkpoint `lb_best`, certified state, column count,
  counters, scheduler, and histories against replay.
- Compare outcome `type`, `certified` (exact boolean), `ub_ch`, `lb_best`,
  `gap`, `oracle_calls`, method, and recovery-at-end against replay.
- Cross-link oracle-event `extra.min_reduced_cost_ub`,
  `extra.min_reduced_cost_lb`, and `extra.column_novel` with the corresponding
  iteration fields. Oracle and iteration evidence may not disagree.

### Required E2 regressions

At helper, `_cg_sane`, and analyzer entry points as applicable:

1. Flip `outcome.certified` after a derived certificate.
2. Coordinate top-level and outcome LB/gap inflation.
3. Append a terminal event/history after certification.
4. Delete the required budget terminal.
5. Add a second budget terminal.
6. Falsify terminal `n_columns` or `lb_best`.
7. Make oracle and iteration reduced-cost fields disagree.
8. Make oracle and iteration novelty disagree.

Do not create a second replay implementation. Keep audit and analyzer on the
same authoritative chronological path.

## Remaining E3: complete exception metadata and import commit handling

Severity: P2.

### `install_tree_no_replace`

The post-rename error path around lines 1399-1411 raises
`IncompletePublicationError` without truthful `renamed` and `destination`
metadata, violating the new exception contract. Populate all state metadata
and add pre-rename and post-rename regressions.

### `import_bundle`

The import removes and fsyncs its lock, then closes descriptors around lines
2512-2514. A descriptor-close error can still report import failure after the
target and receipt have durably committed and the lock is gone.

Track import commit state explicitly. Once lock removal and parent fsync have
committed the import, descriptor-close failure must not report the import as
unsuccessful. Add a regression analogous to the publisher post-commit close
test. Preserve pre-commit close failures honestly.

## Remaining E4: durable incident documentation

The user explicitly wants bug discoveries recorded so they are not repeated.

Add:

- EI-024: precommit incomplete-marker deletion was misclassified as completed
  publication.
- EI-025: A6 shared replay omitted terminal/final outcome closure.

Add regression-map rows and exact scientific handling. Add short addenda to the
existing publication/import incidents for truthful exception metadata and the
post-commit import-close case.

Do not prematurely promote EI-003 through EI-020 while this PR is unmerged.
Once the PR is merged, a documentation-only follow-up may promote incidents
whose repairs are actually present and reviewed on `main`.

## Verification and acceptance

Run from `src/`:

```bash
python3 -m pytest tests/ -q
python3 -m pytest tests/test_a6_recovery_replay.py -q
python3 -m pytest tests/test_a6_holdout_analysis.py -q
python3 -m pytest tests/test_a6_holdout_package.py -q
python3 -m pytest tests/test_a6_evidence_language.py -q

git diff --check
bash -n cluster/*.sh cluster/*.sub
```

Protected-file gate from the repository root:

```bash
BASE=92c38a64bed6735eddb2f79dd292d8af9e244559
git diff --exit-code "$BASE"..HEAD -- \
  src/egglab/a6.py \
  src/egglab/b2a2.py \
  src/egglab/b2a345.py \
  src/egglab/evsp.py \
  src/experiments/run_a6_holdout.py \
  src/experiments/select_a6_arm.py
```

Final report must include:

- new exact commit SHA;
- full and focused test counts;
- explicit statement that each exploit above was reproduced against
  `a6bb350` before repair and rejected afterward;
- `git diff --check`, `bash -n`, and protected-file results;
- exact remaining limitations;
- confirmation that nothing was launched and no holdout outcomes were
  inspected;
- confirmation that PR #28 was amended in place and no new PR was opened.

Do not merge PR #28. Return it for independent Codex review.

## Research work queued after closeout

Do not begin this in PR #28.

After PR #28 passes independent review and is merged, the next fresh branch
from `main` should implement the no-solver B3 baseline uplift analysis from the
already committed canonical B2 population. It should deduplicate to one A2 row
per unique instance, validate cross-method interval consistency, report
certified `z_D-z_CH` intervals and `n x b` strata, label the result explicitly
as retrospective/exploratory, hash all inputs, and regenerate byte-identically.
No new cluster experiment should start until that baseline analysis and its
factor-pilot specification are reviewed.
