# Cursor handoff: adversarial review of PR #37 (B3 pilot closeout) — report only

Date: 2026-08-20 (America/New_York)

This is a REVIEW-ONLY task — no identity gate is needed because you make no
commits and no pushes. Do not commit, push, edit, rebase, or merge
anything. Do not post to the PR. Produce a single markdown findings report
as your final answer. No cluster commands, no live run/outcome inspection,
no seeds >= 16.

## Why this outranks everything else

PR #37 (`cursor/b3-pilot-closeout-5fa0`, head
`2df274fc84a07c1521d6f45b2a13ddccc47de5f9`) is the outcome-blind closeout
tooling for the live 60-cell B3 factor pilot: analyzer, confirmation-
selection freeze, and transfer package. Once the pilot's hardened audit
passes on Unicorn, THIS code decides GO / NO-GO / UNDER-RESOLVED. A defect
here contaminates the flagship experiment's frozen decision.

## Scope

Review the exact diff of PR #37 against its base, alongside the merged
specification on main: `doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`, the merged
`src/experiments/b3_factor_pilot.py`, `run_b3_factor_pilot.py`,
`audit_b3_factor_pilot.py`, and the analyzer state before this PR's `-18`
lines. Check, at minimum:

1. **Preregistered decision rule fidelity.** The frozen rule is: per factor
   setting, 12 matched interval contrasts against S0 with the setting's
   frozen direction sign; select `f*` by highest direction-consistent
   zero-excluding count, then larger direction-signed median midpoint, then
   fixed factor order; `UNDER-RESOLVED` if `abs(median) <= 0.04`; `GO` iff
   signed median `> 0.04` AND count `>= 9/12`; otherwise `NO-GO`; any
   incomplete/invalid population is `INVALID/HALT`, never a scientific null.
   Verify the code implements exactly this — thresholds, tie-break order,
   sign conventions, interval (not midpoint) contrast arithmetic — and that
   tests pin each branch of the rule with adversarial fixtures.

2. **Outcome blindness.** The PR must contain no real pilot outcomes: no
   numbers, fixtures, or expectations derivable from the live run; no code
   path that reads `runs/b3_factor_pilot` at import or test time.

3. **Population validity gates.** Exactly 60 cells, 5 settings x 3 burned
   seeds {0,11,15} x n in {8,12} x b in {0.01,0.05}; 48 matched contrasts;
   epsilon/tol_d/budget bindings; refusal to score any incomplete, duplicate,
   or identity-mismatched population; binding to screen SHA
   (`27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603`),
   run manifest, instance/market hashes, solver identity.

4. **Selection freeze immutability.** The confirmation-selection artifact
   must be write-once (no-replace publication), bind the analyzer commit and
   input hashes, and hard-code the confirmation population (seeds 32-37, S0
   vs selected factor only, 24 contrasts / 48 method-cells, gate >= 18/24
   and signed median > 0.04) without any launch capability.

5. **Transfer package safety.** The pack/import path must reuse the reviewed
   no-replace publication discipline (compare with `package_a6_holdout.py`
   patterns), package a frozen snapshot rather than a live tree, and refuse
   on any hash mismatch. Confirm it cannot touch A6 paths.

6. **Test quality.** Are the adversarial tests asserting emitted artifacts
   and decisions, or inspecting source strings? Do they cover tampered
   inputs, wrong denominators, missing cells presented as complete,
   direction-sign errors, and boundary values at exactly 0.04 and exactly
   9/12? Boundary semantics at equality deserve special attention (`<=` vs
   `<`) against the spec text.

7. **Determinism and byte-identical regeneration** with explicit stamps.

## Report format

For each finding: severity (BLOCKER / MAJOR / MINOR / NOTE), file:line,
the defect, a concrete failure scenario, and the spec text it violates.
End with an overall verdict: whether the PR is safe to merge before the
pilot audit runs, and an explicit list of anything you could not verify.
Do not fix anything; report only.
