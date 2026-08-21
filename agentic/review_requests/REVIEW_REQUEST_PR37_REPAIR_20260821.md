# Review request: PR #37 repair (freeze-before-score + real run_commit)

Paste this whole block to the reviewer. It is self-contained.

---

You are reviewing a security/integrity repair to the code that will decide a
one-shot scientific gate. **Review only — no commits, no branch changes, no
pushes, no PR comments.** Report findings as your final answer.

**Assume the author was careless.** The author of this diff is the same
assistant that is coordinating the project, so it cannot review its own work;
you are the independent check. Do not accept the author's framing of what the
diff accomplishes — verify or falsify each claim below yourself.

## Constraints

- Stay outcome-blind: never read, list, or hash anything under
  `runs/b3_factor_pilot`. The preregistered analysis has deliberately **not**
  been run so that reviews of this code stay blind, and the decision has not
  been frozen.
- No cluster commands, no `sbatch`, no `ssh`.
- If you probe by editing files, revert with `git checkout --` afterwards.

## What to review

Repository `ndandnd/egg`, branch `cursor/b3-pilot-closeout-5fa0`.
Diff range: `0af91df3658b5d7cf2dcce21d05689178db63d9b..3a5e67c` (4 commits,
3 files).

**Read this first.** A prior adversarial pass already falsified two of the
claims below and the author has since patched them, so do not treat the list
as untested. Specifically it found, and the author fixed: the frozen copy was
hashed once before the audit and never re-hashed, so a swap published a
`raw_binding` attesting to bytes that were not scored (BLOCKER); checkpoint
error labels embedded the random temp path, leaking TMPDIR and breaking
byte-identical regeneration (MAJOR); and `verify_run_commit` shelled a bare
`git`, so an exported `GIT_DIR` resolved commits from a foreign repository
(MAJOR). **Re-attack all three specifically** — a patch written by the same
author who missed them the first time deserves no benefit of the doubt.

    gh pr diff 37 --repo ndandnd/egg
    # or
    git fetch origin cursor/b3-pilot-closeout-5fa0
    git diff 0af91df..FETCH_HEAD

Changed files: `src/experiments/analyze_b3_factor_pilot.py` and
`src/tests/test_b3_pilot_closeout.py`.

Run tests from `src/`: `python -m pytest tests/ -q`. The two relevant files are
`tests/test_b3_pilot_closeout.py` and `tests/test_b3_factor_pilot.py`.

## The two blockers this is supposed to close

A prior independent review found, at head `0af91df`:

1. `MANIFEST.run_commit` was accepted on shape alone (40 hex characters) and
   never resolved as a real commit or ancestry-checked.
2. The analyzer audited and **scored the live runs tree** and only afterwards
   computed the anchor it bound, so a transient mutate → score → restore could
   score bytes other than the anchored population.

## Claims to falsify

**Claim A — `verify_run_commit` makes a fabricated commit impossible.** Attack:
40-hex values that do not exist; real but unreachable commits; uppercase;
whitespace- or newline-padded values; a ref or tag name instead of a SHA; a SHA
that resolves to a tree or blob rather than a commit; abbreviated SHAs; whether
a `git` binary earlier on `PATH` could subvert it; whether inherited
stdout/stderr masks anything.

**Claim B — after the freeze, nothing reads the live tree during audit,
replay, or scoring.** Attack: grep every use of `runs_dir` after the freeze
point in `analyze()` and `_score_frozen_population()`; look for any path
resolved relative to the original directory; write a probe that mutates the
live tree from inside `load_population` and confirm both what was actually
scored and what verdict results.

**Claim C — a freeze that drops or alters files is caught.** Attack: symlinks,
multiply-hard-linked files, fifos, names needing escaping, unreadable files,
very deep paths. Does the analyzer turn each into a structured `INVALID/HALT`
rather than an uncaught crash?

**Claim D — the temp frozen tree is always cleaned up and never leaks.** Check
the emitted `MANIFEST.json` and `DECISION.json` for absolute temp paths.

**Claim E — no threshold, comparison operator, ordering, or decision state
changed.** Diff the decision logic against `0af91df` and confirm the state
block and the selection ranking are byte-identical.

## Also specifically examine

- **Exception-type gaps.** The new code catches
  `(_PkgError, OSError, evidence.EvidenceError)`. Find an exception that
  escapes that and crashes instead of producing `INVALID/HALT` — `ValueError`,
  `KeyError`, `shutil` errors, `RecursionError`.
- **`audit_sha` non-None while `raw_binding` is None** in any path that still
  publishes a scoreable artifact.
- **The new `run_commit_verifier` parameter must be unreachable from the
  production CLI.** Confirm `main()` exposes no override.
- **The test seam.** `_synthetic_run_commit_ok` was added so 47 pre-existing
  fixtures (which carry fabricated commit SHAs and call the analyzer with
  `verify_code_commit=True`) keep passing. Decide whether that seam weakens any
  pre-existing assertion, and whether injecting it in the single `_analyze`
  helper was the right call versus rewriting the fixtures to build real
  temporary Git history.
- **Whether the six new regressions actually prove what their names claim**, or
  pass for an incidental reason.

## Deliverable

Per finding: severity (BLOCKER / MAJOR / MINOR / NOTE), file:line, the exact
probe you ran and its output, and a concrete failure scenario. Then state which
of claims A–E you could and could not falsify — say so plainly where you found
nothing. End with the test counts you observed and an explicit verdict: is this
diff safe to merge and then use to generate and freeze the flagship decision?
