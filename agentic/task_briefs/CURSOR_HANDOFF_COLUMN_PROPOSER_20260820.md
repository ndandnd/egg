# Cursor handoff: economically filtered column proposer (diagnostic only)

Date: 2026-08-20 (America/New_York)

This is an exploratory engineering task with a real chance of a negative
result, and that is acceptable: build a cheap heuristic that proposes
candidate schedule columns from local moves on incumbents, evaluated *only*
by whether the exact machinery accepts them. The exact oracle remains the
sole feasibility and certification authority. Code and tests only; no
scientific claims beyond "finite-pool diagnostic" language. Read this file
completely before changing anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `5b63e725d0fd85cfb0b83f462a612016e7f4321a`. If main has advanced through a
  reviewed merge, inspect the advancement and use the new clean main.
- Create a new branch such as `cursor/column-proposer`.
- Open exactly one new draft PR. Do not merge it.
- Do not read or touch anything under `src/runs/`, `result/`, any A6 path, or
  `runs/b3_factor_pilot`. Do not edit `doc/DECISION_LOG.md`,
  `doc/RESEARCH_STATUS.md`, or `doc/ENGINEERING_INCIDENTS.md`.
- Do not launch Slurm or any cluster job. Do not set `EGGLAB_REQUIRE_GRB`.
  All tests must pass with the CBC fallback backend.
- Live solves only inside tests, on burned development seeds `{0, 11, 15}`,
  `n_trips <= 8`. Never any seed `>= 16`.
- Do not modify `b2a2.py` or any other existing module. The proposer must be
  a pure add-on that `certified_cg` does not know about.
- **Certification must never depend on the proposer.** Proposed columns may
  only ever be added to a column pool as extra columns whose reduced cost was
  verified; every bound in any downstream use still comes from clean oracle
  calls. This is the A3-A5 lesson: helpers that add calls must not
  contaminate certificates.

## Objective

Section 5 of the research program allows learning/heuristics only as
proposal acceleration with the exact oracle as backstop, and the Phase 2
evidence showed raw schedule hashes are dominated by degeneracy noise
(2,559 degenerate tie changes vs 92 economic switches). So the deliverable
is a proposer whose output is measured purely economically:

> given `(inst, market, incumbent columns, duals pi/sigma)`, propose K
> candidate schedules cheaply; a proposal counts as **accepted** only if its
> exactly-evaluated reduced cost against `(pi, sigma)` is negative beyond a
> stated margin AND it passes physical replay.

The diagnostic questions: what fraction of proposals are accepted, and how
much cheaper is a proposal than an oracle pricing call, on tiny instances?
An honest "acceptance is near zero" answer is a valid outcome.

## Design requirements

New files:

```text
doc/COLUMN_PROPOSER_SPEC.md
src/egglab/proposer.py
src/tests/test_proposer.py
```

Proposal moves (deterministic, seeded by explicit integer arguments only —
no wall-clock or global RNG state):

- trip relocation: move one trip between two vehicles' sequences;
- trip swap: exchange two trips between vehicles;
- vehicle merge/split where `max_vehicles` allows;
- after any structural move, re-realize charging exactly with
  `evsp.solve_fixed_sequences(inst, sequences, ('linear', p))` at the dual
  prices (this is the economic filter: charging is re-optimized, never
  copied), discarding moves it reports infeasible (`None`).

Acceptance evaluation (exact, reusing existing helpers):

- build the candidate column with `b2a2.column_from_solution`; require
  `replay_ok`;
- reduced cost from `b2a2.pricing_incumbent(col, sol, prices)` minus `sigma`,
  with the acceptance margin `rc <= -margin` (default margin: reuse
  `b2a2.RC_TOL` scale; state the choice in the spec);
- dedupe against the existing pool by `b2a2.column_key`, and separately
  report near-duplicates that differ only within load-rounding noise (the
  degeneracy lesson: count them, do not celebrate them).

Diagnostic harness: a function (not a cluster driver) returning a
deterministic dict per instance: proposals made, infeasible discarded,
duplicates, degenerate near-duplicates, accepted count, accepted reduced
costs, and wall-time per proposal versus one `evsp.solve_evsp` pricing call
on the same duals. Tests run it on the three burned seeds and assert
structural invariants, not performance numbers.

The spec must carry the tier language verbatim-in-spirit: finite-pool
diagnostic on burned synthetic seeds; no speedup claim, no generalization
claim; any future integration into a driver is a separate reviewed task.

Known repo gotchas: `synthetic_instance` has no horizon parameter
(`n_slots=28` default from `Instance`); certified bounds come from
`sol.stats.bound`, never incumbents — the proposer must never touch bound
logic at all; tests self-bootstrap `sys.path` (no conftest.py), run from
`src/`.

## Required adversarial tests

- every accepted column: `replay_ok` true, reduced cost verified negative by
  recomputation in the test from primitives (load, ops_cost, pi, sigma);
- a hand-built proposal with a tampered load is rejected by replay;
- a proposal duplicating an existing `column_key` is reported as duplicate,
  never accepted;
- a degenerate near-duplicate (same schedule cost within tie tolerance,
  different hash) is counted in the degeneracy bucket;
- infeasible structural move (SOC-impossible relocation) is discarded via
  `solve_fixed_sequences` returning `None`, not by proposer-side guessing;
- determinism: identical inputs and seed argument produce identical proposal
  sequences and identical diagnostic dicts;
- the proposer never mutates its input columns or instance (assert deep
  equality after the call);
- no filesystem writes outside an explicitly passed output directory
  (tests use `tmp_path`), and no defaults under `src/runs/` or `result/`.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_proposer.py -q
python3 -m pytest tests/ -q
git diff --check
```

## Final report

Include: branch, draft PR URL, exact commits; test counts; the observed
acceptance/duplicate/degeneracy counts on seeds {0, 11, 15} stated plainly
even if unfavorable; wall-time comparison caveats (CBC, tiny instances);
confirmation that no cluster job ran, no bound/certification code path was
modified, and no seed >= 16 was used. Do not merge; return the draft PR for
independent review.
