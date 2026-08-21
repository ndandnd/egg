# Cursor handoff: repair PR #37 (B3 pilot closeout) — consolidated findings from two independent reviews

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` is unusable in this environment — GitHub App integration
tokens cannot call the `/user` endpoint. The remote check plus dry-run push
is the operative access gate.) Do not push if either fails.

No cluster commands, no live pilot outcome inspection (`runs/b3_factor_pilot`
stays unread), no seeds >= 16, no rebases, no force-pushes, no merges. The
task remains outcome-blind. Keep the PR draft. After this repair the PR gets
ANOTHER independent review before merge — do not self-declare it safe.

## Task

Continue PR #37 in place on `cursor/b3-pilot-closeout-5fa0`, current head
`2df274fc84a07c1521d6f45b2a13ddccc47de5f9`. Do not open another PR.

Two independent adversarial reviews both returned "not safe to merge". Both
reproduced working forgeries. Every reproduction below must become a
committed regression test. The verified-good parts (contrast arithmetic,
direction signs, ranking order, decision partition, confirmation constants,
no-replace installer reuse, A6 files untouched) stay as they are.

## A. `select_b3_confirmation.py` — the selector must recompute, not trust

1. **BLOCKER: recompute the decision from primitives.** The selector
   currently trusts `DECISION.json` state/count/median after checking only
   self-reported hashes. Both reviews forged GO from non-GO evidence
   (one by editing state/count/median + rehashing; one by swapping S1->S3
   with CSV flag edits). Repair: the selector must independently recompute
   the full preregistered decision — 60 cell intervals -> 48 matched
   contrasts -> direction signs -> zero-excluding counts -> signed medians
   -> count/median/factor-order ranking -> decision state — from the
   analysis artifact's primitive tables, and require exact agreement with
   both `DECISION.json` and `MANIFEST.json["decision"]`. Any disagreement
   refuses with the differing field named.
2. **Provenance must be real.** Require `analysis_code_verified == true`;
   resolve the analyzer commit to an actual object in this repository's
   history (ancestry check against the current branch), refusing
   `000...000` or any unresolvable value; validate screen/spec hashes
   against the frozen constants (screen SHA
   `27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603`), not
   merely for non-nullness.
3. **Transactional reads.** Read each input file's bytes exactly once;
   hash and parse those same bytes. No hash-close-reopen-parse windows.
4. **Atomic, isolated publication.** Write the selection to a temp file,
   fsync, then rename into place — never `O_EXCL`-create-then-write. Refuse
   `out_dir` inside the analysis dir (and vice versa) on resolved real
   paths; refuse symlinked parents; refuse any A6 path.

## B. `analyze_b3_factor_pilot.py` — bounds must be replayed, not read

5. **BLOCKER: evidence-replay all certified quantities.** Recompute
   `lb_best`/`ub_ch` from the chronological oracle/iteration event logs and
   the dictator endpoints from the adaptive evidence, and refuse on any
   mismatch with stored outcome fields. One review fabricated a 12/12
   median-0.1 GO for S1 by editing CH histories while solver evidence was
   unchanged — that must become impossible. This is the standing project
   lesson: replay certificates from chronological events; never trust
   stored summary labels.
6. **BLOCKER: dictator certificate validity.** Do not trust
   `adaptive_converged` alone. Require, per cell: recomputed
   `z_d_ub - z_d_lb <= tol_d`; recorded `adaptive_gap_abs` consistent with
   endpoints; dictator record replay validity; dictator solver identity
   matching the run manifest. Failure of any is `INVALID/HALT`, never a
   scored cell.
7. **Budget gate:** enforce `oracle_calls <= budget (240)` per cell, not
   just `oracle_calls == len(events)`.
8. **Interval sanity:** a tightened interval must satisfy `lo <= hi`;
   `U_hi` in `[-1e-6, 0)` with `U_lo_raw < U_hi` currently emits the
   impossible `[0, -5e-7]`. Impossible intervals are `INVALID/HALT`.
9. **Emit the required evidence:** add to `cell_intervals.csv` the
   cost-fraction endpoints (already computed, currently dropped) and both
   certificate gaps (dictator gap and CH gap) per cell, per spec §§1.1/7.
10. **Malformed input:** a corrupt/malformed checkpoint JSON must produce a
    structured `INVALID/HALT` decision, not an uncaught `JSONDecodeError`.
11. **Screen binding:** `--screen-dir` must not bypass the frozen screen
    SHA. If an override is kept for synthetic tests, its output must be
    marked non-scoreable and refused by the selector and packager.
12. **Solver gap field:** report the MIP gap from the bound-derived fields,
    not an unbound checkpoint field.

## C. `package_b3_pilot.py` — the bundle must prove itself

13. **BLOCKER: import must reapply the full contract.** Independently of
    the bundle's self-description, require the exact frozen population
    (60 cells, expected file counts/root digests, expected cell
    identities), the analysis contract (schema, required outputs, verified
    provenance, non-null run binding), and the raw/analysis cross-binding.
    Empty `runs/`, empty `analysis/`, or `cells: {}` must refuse. Reject
    absolute or `..` components in any tag/file key.
14. **BLOCKER: bind analysis to the exact raw job.** The design manifest is
    shared across jobs; both reviews packaged one job's raw results with
    another job's GO analysis. Cross-check the run-manifest SHA AND the
    Slurm job lineage / raw-tree digest between the analysis and the raw
    tree being packaged.
15. **Freeze, then package.** Inventory once into a frozen snapshot and
    package from that snapshot; no live rereads of `JOB.json`/manifest
    after inventory. Re-verify Slurm quiescence immediately before the
    publication rename, and validate the job id's canonical form; treat an
    unauthenticated or substituted job id as refusal.
16. **Failure must not look like success.** A post-rename failure must
    leave an explicit incomplete marker, and import must refuse any
    destination lacking the completion marker (follow the shared
    no-replace/incomplete-marker discipline in `package_a6_holdout.py`).
17. **Path and boundary isolation.** Refuse `out_base` inside the source
    tree and import destinations inside the bundle (resolved real paths);
    refuse A6 paths BEFORE any recursive read; add `package_a6_holdout.py`
    to the executed-code provenance list since its helpers execute.

## D. Tests

18. Turn every reproduction from both reviews into a regression test.
19. Pin the decision-rule boundaries exactly: median at exactly +0.04 and
    -0.04; count exactly 8 versus exactly 9; a contrast endpoint exactly
    zero; a count-versus-median ranking conflict; an exact factor-order
    tie; coordinated same-cardinality duplicate-row replacement. Remove the
    assertion that accepts either of two states
    (`test_b3_pilot_closeout.py` line ~619); a preregistered rule has one
    right answer per fixture.

## Report

Ordered commits (repairs first, tests alongside or after each repair, no
artifact commits — this PR generates no artifacts), focused and full test
counts as measured by CI on the PR (PR #43's workflow, if merged by then),
a finding-by-finding checklist mapping each item above to the commit that
closes it, and anything you disagree with — with the disagreement argued
from the spec text, not from convenience. Keep the PR draft; it will be
independently re-reviewed.
