# Cursor handoff: third independent review of PR #37 (repaired head) — report only

Date: 2026-08-20 (America/New_York)

This is a REVIEW-ONLY task. No identity gate is needed: you make no commits
and no pushes. Do not edit, rebase, merge, or post to the PR. Produce a single
markdown findings report as your final answer.

## Critical: you must stay outcome-blind

The 60-cell B3 factor pilot population is complete and its hardened audit has
PASSED (60/60 certified A2 cells, 60/60 converged dictators, 12 cells per
setting, screen SHA `27c04d82...`, run manifest SHA `9f7529fc...`, run commit
`5b63e725...`). **The preregistered analysis has deliberately NOT been run
yet, precisely so that this review is outcome-blind.**

Therefore:

- do NOT read, list, hash, or summarize anything under `runs/b3_factor_pilot`;
- do NOT run the analyzer, the selector, or the packager against real data;
- do NOT attempt to infer which factor setting wins;
- use only synthetic fixtures you construct yourself.

If you find yourself reasoning about what the real answer might be, stop.
Your job is to decide whether this code computes the frozen rule correctly and
refuses invalid evidence — not what it will output.

## Task

Review PR #37 on `cursor/b3-pilot-closeout-5fa0` at repaired head
`8144483eb292686477d0c24d2a12aa959e10a6f3`, which sits four commits above the
twice-reviewed `2df274f`. This is the code that will decide GO / NO-GO /
UNDER-RESOLVED on the flagship experiment, so it gets a third pair of eyes
before it is trusted.

Two prior independent reviews found 17 findings including three blockers, and
each built a working forgery: a non-GO analysis edited into a GO
authorization; a fabricated 12/12 GO from edited certificate histories while
solver evidence was untouched; and import accepting arbitrary self-described
trees. All 17 were repaired in four commits: `29b957a` (selector recomputes
the decision from primitives, real provenance, transactional reads, atomic
publication), `656dfe4` (analyzer replays bounds from chronological event
logs, recomputes dictator certificates, budget ceiling, interval sanity,
emits cost fractions and both certificate gaps), `6f88342` (packager freezes
one inventory, `raw_binding` of raw-tree digest + Slurm job id + JOB.json
hash required by pack and import, quiescence re-verified before rename,
incomplete marker plus completion record), `8144483` (float-exact boundary
pins).

Your review has three jobs, in priority order:

1. **Did the repairs actually close the findings?** For each of the three
   blockers, construct your own fresh forgery attempt — do not merely rerun
   the committed regressions, which the repair author wrote and which
   therefore only prove what he thought of. Try at least: a coordinated edit
   across every file the selector cross-checks; a decision whose primitives
   and summaries agree with each other but disagree with the frozen rule; a
   bundle whose `raw_binding` fields are internally consistent but describe a
   different job; and a replay-consistent but rule-violating certificate.
2. **Did the repairs introduce new defects?** Specifically examine the
   `os.link` publication path (link-then-verify semantics, failure modes on
   the same filesystem, what happens if the link target exists), the
   incomplete-marker plus completion-record protocol (can a crash between the
   two produce a state import misreads?), the single-read transactional inputs
   (is the parsed object really derived from the hashed bytes?), and the
   new `raw_binding` requirement (does it fail closed when fields are absent
   in a legitimately older artifact?).
3. **Is the frozen decision rule computed exactly?** Re-derive it from
   `doc/B3_FACTOR_PILOT_SPEC_DRAFT.md` independently and compare against the
   code: 12 matched interval contrasts per setting against S0, the setting's
   frozen direction sign, selection by highest direction-consistent
   zero-excluding count then larger direction-signed median midpoint then
   fixed factor order; `UNDER-RESOLVED` if `abs(median) <= 0.04`; `GO` if
   signed median `> 0.04` and count `>= 9/12`; else `NO-GO`; any
   incomplete/invalid population is `INVALID/HALT`. Pay particular attention
   to inclusive-versus-exclusive comparisons at exactly `0.04` and exactly
   `9`, and to interval (not midpoint) arithmetic.

Also assess the repair author's four recorded disagreements on their merits:
`os.link` rather than `rename` for no-replace; incomplete marker plus positive
completion record; the acknowledged limit that replay cannot catch a fully
consistent co-edit of the RMP side without re-solving MIPs; and INVALID/HALT
analyses being unpackable.

## Report format

Per finding: severity (BLOCKER / MAJOR / MINOR / NOTE), file:line, the defect,
a concrete failure scenario, and the spec text it violates. State explicitly
which of the three prior blockers you could and could not re-exploit. End with
a verdict: is this code safe to generate and freeze the flagship decision, and
list anything you could not verify. Report only; fix nothing.
