# Cursor handoff: B1 minimal cycling example with machine-checked certificate

Date: 2026-08-20 (America/New_York)

This is a theory-support task: construct the smallest synthetic instance on
which undamped price iteration provably enters a 2-cycle and no price fixed
point exists, and prove both facts by exhaustive enumeration rather than
prose. The deliverable is a construction module, a certification harness, and
a spec that a thesis chapter can cite. No cluster runs, no scientific-result
artifacts. Read this file completely before changing anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `5b63e725d0fd85cfb0b83f462a612016e7f4321a`. If main has advanced through a
  reviewed merge, inspect the advancement and use the new clean main.
- Create a new branch such as `cursor/b1-minimal-cycle`.
- Open exactly one new draft PR. Do not merge it.
- Do not read or touch anything under `src/runs/`, `result/`, any A6 path,
  or `runs/b3_factor_pilot`. Do not edit `doc/DECISION_LOG.md`,
  `doc/RESEARCH_STATUS.md`, or `doc/ENGINEERING_INCIDENTS.md`.
- Do not launch Slurm or any cluster job. Do not set `EGGLAB_REQUIRE_GRB`.
  All tests must pass with the CBC fallback backend.
- Do not modify `src/egglab/loops.py`, `evsp.py`, `market.py`,
  `instance.py`, or any other existing module. Read `loops.py` first and
  reuse its iteration/cycle-detection API where it fits; otherwise implement
  a standalone iteration inside the new module.
- The example instance must be hand-constructed (explicit `Instance(...)`
  with explicit trips), not drawn from `synthetic_instance` seeds. If you
  also want a generated witness, only burned seeds `{0, 11, 15}` are allowed;
  never any seed `>= 16`.

## Objective

B1 interprets naive price iteration as unstabilized decomposition and locates
cycling at the kinks of an integer fleet response. The measurement campaign
already showed cycling empirically (all 49 undamped observed cycles had
length exactly 2). What is missing is the **minimal, fully certified
counterexample**: an explicit instance and affine market where

1. the undamped best-response iteration
   `p^{k+1} = market.price(load(BR(p^k)))` enters a 2-cycle from the
   uncontrolled/flat starting point, and
2. no schedule is a fixed point: for every feasible complete schedule `S`,
   `S` is not a best response to the prices its own load induces.

Both facts are decidable because the set of feasible complete schedules of a
tiny instance is finite. The harness must prove them by enumeration, with the
MILP oracle used only as an independent cross-check.

## Design requirements

New files:

```text
doc/B1_MINIMAL_CYCLE_SPEC.md
src/egglab/b1_example.py
src/tests/test_b1_minimal_cycle.py
```

`b1_example.py` must provide, at minimum:

- `minimal_cycle_instance() -> (Instance, AffineMarket)` — the explicit
  hand-built example. Aim for the genuinely smallest structure that works
  (start trying 2 trips / small horizon / 1-2 vehicles; document what you
  tried and why smaller fails, in the spec). Build the market with
  `make_affine_market` or a direct `AffineMarket(a, b, base_load)`.
- `enumerate_schedules(inst) -> list` — exhaustive enumeration of all
  feasible complete fleet schedules. Enumerate duty partitions/orders
  directly; realize charging per fixed partition with
  `evsp.solve_fixed_sequences` (charging is continuous once the partition is
  fixed, so this is exact for best response at fixed prices). Enumeration
  completeness must be argued in the spec and cross-checked in tests.
- `certify_two_cycle(inst, market) -> dict` — runs the undamped iteration and
  returns the cycle certificate: the two schedules, their loads, the two
  price vectors, and the strict-optimality margins of each best response.
- `certify_no_fixed_point(inst, market) -> dict` — for every enumerated
  schedule `S`, evaluates whether `S` is optimal at `p = market.price(load(S))`
  and returns, per schedule, the strictly better deviation and its margin.
  All margins must be reported explicitly; a margin below a stated tolerance
  is a construction failure, not something to round in your favor.

Degeneracy handling is the hard part and must be explicit: ties in the best
response make "no fixed point" ill-posed. The construction must have strict
margins (bounded away from zero; state the bound in the spec), and the
harness must fail loudly if any comparison falls inside the tolerance band.

MILP cross-check: at each of the two cycle price vectors, `evsp.solve_evsp`
with `('linear', p)` must return an objective equal to the enumerated best
response value (within `1e-6`-scale tolerance), confirming the enumeration
found the true optimum. Remember certified bounds come from `sol.stats.bound`;
incumbent-only equality is not sufficient for the cross-check gate.

The spec must state precisely what the example does and does not show: it
certifies nonexistence of a pure fixed point and existence of a 2-cycle for
this instance/market; it is a synthetic counterexample supporting the B1
kink/cycling narrative, not a general theorem.

Known repo gotchas: `synthetic_instance` has no horizon parameter — for a
tiny horizon construct `Instance` directly (`n_slots`, `slot_min` are
fields). Tests self-bootstrap `sys.path` (no conftest.py); copy the header of
an existing test file and run from `src/`.

## Required adversarial tests

- enumeration completeness: on an even tinier instance, enumeration count
  matches an independent brute-force over partitions, and the enumerated
  optimum at 3+ price vectors matches `solve_evsp`;
- the 2-cycle certificate: iteration from the flat start visits exactly the
  two claimed schedules in alternation for >= 6 steps, with strict margins;
- the no-fixed-point certificate: every enumerated schedule has a strictly
  improving deviation at its own induced prices;
- margin discipline: a synthetically perturbed market that creates a tie
  makes the harness raise/fail rather than certify;
- determinism: repeated runs produce byte-identical certificates
  (schedule hashes, margins, price vectors);
- the certificates returned are self-contained dicts whose numbers the tests
  re-verify from primitives (loads, `market.price`, ops costs), not trusted
  labels.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_b1_minimal_cycle.py -q
python3 -m pytest tests/ -q
git diff --check
```

## Final report

Include: branch, draft PR URL, exact commits; the example's exact structure
(trips, windows, energies, market coefficients); the two cycle schedules and
their margins; the smallest margin in the no-fixed-point sweep; what smaller
constructions you tried and why they failed; confirmation that no cluster job
ran and no `src/runs/`/`result/` path was touched. Do not merge; return the
draft PR for independent review.
