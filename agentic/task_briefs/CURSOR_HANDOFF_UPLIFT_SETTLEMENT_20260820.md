# Cursor handoff: convex-hull settlement and lost-opportunity accounting

Date: 2026-08-20 (America/New_York)

This is an engineering task for the mechanisms track: a certificate-carrying
settlement calculator that turns existing certified objects (`z_D` interval,
`z_CH` interval, master duals, column pool) into convex-hull prices, a
two-part tariff, and lost-opportunity-cost accounting — all as intervals, all
on synthetic inputs. Code and tests only: no committed scientific artifacts,
no reading of committed result populations, no claims. Read this file
completely before changing anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `5b63e725d0fd85cfb0b83f462a612016e7f4321a`. If main has advanced through a
  reviewed merge, inspect the advancement and use the new clean main.
- Create a new branch such as `cursor/uplift-settlement`.
- Open exactly one new draft PR. Do not merge it.
- Do not read or touch anything under `src/runs/` or `result/` (including the
  committed B2/B3 populations — this task must stay outcome-blind), any A6
  path, or `runs/b3_factor_pilot`. Do not edit `doc/DECISION_LOG.md`,
  `doc/RESEARCH_STATUS.md`, or `doc/ENGINEERING_INCIDENTS.md`.
- Do not launch Slurm or any cluster job. Do not set `EGGLAB_REQUIRE_GRB`.
  All tests must pass with the CBC fallback backend.
- Live solves are allowed only inside tests, on burned development seeds
  `{0, 11, 15}` with `n_trips <= 8`. Never any seed `>= 16`.
- Do not modify any existing `src/egglab/` module or experiment driver. New
  files only.

## Objective

B3 measures internal uplift `z_D - z_CH` but does not yet say how it would be
settled. The settlement objects, for a single fleet against the synthetic
affine market, are:

- **convex-hull prices** `pi`: the final master duals on the load-link
  constraints from a certified `certified_cg` state (with convexity dual
  `sigma`);
- **fleet best-response value at `pi`**:
  `V(pi) = min over schedules S of ops_cost(S) + pi . load(S)`, held as a
  certified interval from one pricing-oracle call
  (`[sol.stats.bound, pricing_incumbent(...)]` discipline — dual bound low,
  replay-validated incumbent high);
- **lost-opportunity cost** of operating a designated integer schedule `S*`
  at prices `pi`: `LOC = (ops_cost(S*) + pi . load(S*)) - V(pi)`, an interval;
- **two-part tariff**: linear part `pi`, side payment equal to `LOC`, with
  the identity checks below.

Everything is interval arithmetic over certified endpoints. No midpoints, no
silent clamping: raw endpoints are preserved, and any theorem-tightened
nonnegative presentation value (`max(0, lo)`) is additional, never a
replacement — the same convention the B3 baseline uses.

## Design requirements

New files:

```text
doc/SETTLEMENT_SPEC.md
src/egglab/settlement.py
src/tests/test_settlement.py
```

`settlement.py` operates on plain data already produced by existing code:

- input A: a `certified_cg` return state (or a dict fixture shaped like one):
  columns, final duals `pi`/`sigma`, `outcome` interval (`lb_best`, `ub_ch`),
  `certified` flag, identity block;
- input B: a dictator certificate: `z_d_ub` and `tol_d` (as used throughout
  B2/B3), or a `solve_dictator` `Solution` from which those are read
  (`obj_true`, `stats.extra["adaptive_lb"]`);
- input C (optional): a designated integer schedule as a column dict
  (`b2a2.column_from_solution` shape) to be settled.

Required functions (names indicative):

- `ch_prices(state) -> dict` — extract `pi`, `sigma`, and the certification
  context; refuse (raise) if `state["outcome"]["certified"]` is false;
- `best_response_interval(inst, pi, **solver_kw) -> (lo, hi)` — one oracle
  call via `evsp.solve_evsp(inst, ('linear', pi))`, endpoints from
  `stats.bound` and a replay-validated incumbent (`evsp.validate_solution`
  must return no violations, else raise);
- `lost_opportunity(column, pi, br_interval) -> (lo, hi)`;
- `two_part_settlement(state, dictator_cert, column, ...) -> dict` — the full
  settlement record with every interval, every input hash
  (`instance_hash`, `market_hash`, `column_key`), and explicit consistency
  checks (below). The record must be JSON-serializable and deterministic.

Consistency identities to check and store as pass/fail fields (with the
operand-scaled-tolerance lesson from EI-026/EI-027 in mind — one coherent
tolerance policy, stated in the spec):

- `V(pi)` interval must lie weakly below `ops_cost(S) + pi . load(S)` for
  every column `S` in the pool (no negative reduced cost below tolerance
  against the certified duals: dual feasibility witness);
- the LOC interval of the dictator-optimal column must be consistent with the
  internal-uplift interval `[(z_d_ub - tol_d) - ub_ch, z_d_ub - lb_best]`:
  intervals may differ, but the spec must state the exact relation you assert
  and the code must check it;
- reversed intervals (`lo > hi` beyond tolerance) are hard errors, never
  swapped or clamped.

The spec must state the evidence tier explicitly: this is settlement
*machinery* over certified synthetic objects; applying it to the committed
B2/B3 populations is a separate, later, reviewed analysis task — not part of
this PR.

Known repo gotchas: certified lower endpoints come from `sol.stats.bound`,
never `obj_model`/`obj_true`; `synthetic_instance` has no horizon parameter;
tests self-bootstrap `sys.path` (no conftest.py) — copy an existing test-file
header and run from `src/`.

## Required adversarial tests

Use hand-computable micro fixtures plus at most a few tiny live solves:

- a fully hand-built 2-column fixture where every interval is verifiable by
  hand arithmetic in the test;
- an end-to-end tiny live case (seed 0 or 11, `n_trips <= 8`): run
  `certified_cg`, run `solve_dictator`, settle, and check every identity;
- uncertified CG state refused;
- tampered dual vector (dual infeasibility against the pool) detected;
- tampered column load/ops_cost changes `column_key` and is caught by the
  hash binding;
- replay-failing incumbent rejected in `best_response_interval`;
- reversed interval raises;
- NaN/infinity in any operand raises;
- LOC/uplift consistency check fails on a fixture built to violate it;
- determinism: identical inputs produce byte-identical settlement records;
- refusal to read any `src/runs/` or `result/` path (the module must not
  contain such defaults).

Tests must assert emitted record contents, not source strings.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_settlement.py -q
python3 -m pytest tests/ -q
git diff --check
```

## Final report

Include: branch, draft PR URL, exact commits; test counts; the tolerance
policy you chose and why it is coherent (one scale, operand-relative);
the exact identity relations asserted between LOC and internal uplift;
confirmation that no committed result population was read, no cluster job
ran, and no seed >= 16 was used. Do not merge; return the draft PR for
independent review.
