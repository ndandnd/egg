# Cursor handoff: GitHub Actions CI (CBC-only test gate)

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
secrets, no Gurobi, no live run directories, no rebases, no force-pushes,
no merges. Keep the PR draft.

## Why

Every recent PR's test count is agent-self-reported; the project rule is
that a PR is never trusted on its self-reported test count. A minimal CI
makes that verification mechanical for every current and future draft PR.

## Task

Branch from exact current `origin/main`
(`5b63e725d0fd85cfb0b83f462a612016e7f4321a`; if main advanced through a
reviewed merge, inspect and use the new clean main) as `cursor/github-ci-cbc`.
Add a minimal GitHub Actions workflow only; do not change any scientific
algorithm, test, or experiment file.

Workflow requirements:

- trigger on `pull_request` and on `push` to `main`;
- Ubuntu, Python 3.12, `permissions: contents: read` (read-only token);
- pip dependency caching; install from `src/requirements.txt` (it pins
  `mip`, `numpy`, `pytest`; it must NOT contain gurobipy — if you find a
  gurobipy line on your base, stop and report rather than working around it);
- steps, in order:
  1. `git diff --check` over the merge-base diff;
  2. `bash -n` on every shell file under `src/cluster/`;
  3. the complete pytest suite run from `src/`:
     `python -m pytest tests/ -q`;
- an explicit job `timeout-minutes` (start at 60; report the observed
  runtime). If the suite genuinely cannot fit, do NOT silently skip or
  deselect tests — report the runtime and stop for review;
- a `concurrency` group canceling superseded runs per ref;
- no artifact uploads containing results, no network access beyond package
  installation, no write-enabled permissions anywhere.

Add a short documentation note (in the workflow file header or
`doc/README.md` one-liner) stating that CI verifies solver-independent/CBC
behavior only — it does not verify Gurobi performance or cluster-evidence
equivalence, which remain governed by `EGGLAB_REQUIRE_GRB` on Unicorn.

Open one new draft PR and demonstrate the workflow passing on its own PR
(link the green run in the PR description).

## Report

PR URL, the green workflow run URL, total suite runtime and test count as
measured by CI (not self-reported), and confirmation that no scientific file
changed. Leave the PR draft for independent review.
