# Cursor handoff: repair PR #42 (column proposer — boundary violations)

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` is unusable in this environment: Cursor agents authenticate
with a GitHub App integration token, which cannot call the `/user` endpoint.
The remote check plus dry-run push is the operative access gate.)

Do not push if the remote check or the dry-run push fails. No cluster commands, no
campaigns, no live B3/A6 outcome inspection, no seeds >= 16, no rebases,
no force-pushes, no merges. Keep the PR draft.

## Task

Continue PR #42 in place on `cursor/local-column-proposer-6ec0`, current
head `b8f9cb668e091dedd5be0f7b0c0cba5e626522b8`. Do not open another PR.

The implementation architecture (standalone shadow proposer, strict replayed
reduced-cost admission, full pricing as sole certificate source) passed
review and stays. What must be repaired is the PR's protocol violations —
it committed files the task boundary forbade:

1. **Remove from the PR entirely** (revert with forward commits; do not
   rewrite history):
   - `doc/DECISION_LOG.md` changes — the decision log records ratified gate
     closures only; an exploratory proposer lab closes no gate;
   - `doc/RESEARCH_STATUS.md` changes — same protocol;
   - the entire `result/column_proposer/20260820T174254Z/` tree
     (`MANIFEST.json`, the ~29k-line `REPORT.json`, `SUMMARY.md`) and the
     `result/README.md` edit. `result/` holds reviewed, curated,
     provenance-bound scientific artifacts committed through the
     code-first/artifact-second protocol — never an agent's first-run
     output. Diagnostic numbers belong in the PR description and in
     deterministic test assertions, not in `result/`.

2. **Keep**: `src/egglab/column_proposer.py`, `src/tests/test_column_proposer.py`,
   `doc/LOCAL_MOVE_COLUMN_PROPOSER_LAB.md`, and the one-line README pointers
   in `doc/README.md` / `src/README.md` if they merely index the lab doc.

3. **`src/experiments/run_column_proposer.py`:** keep it only if it is a
   local diagnostic runner that writes exclusively under a caller-supplied
   output directory with no default under `src/runs/` or `result/`; verify
   and add a test asserting that. Otherwise remove it.

4. The lab doc must state the evidence tier plainly: finite-pool diagnostic
   on burned synthetic seeds {0, 11, 15}; no speedup claim, no
   generalization claim; integration into any driver is a separate reviewed
   task.

5. Re-run the focused and full suites after the removals and confirm nothing
   in the kept code imported from or referenced the removed artifacts.

## Report

The exact revert commits, the final PR file list (which must contain nothing
under `result/` and no decision-log/status edits), focused and full test
counts, and the headline diagnostic numbers (proposals, acceptance rate,
duplicate and degeneracy counts) stated in the PR description only. Leave
the PR draft for independent review.
