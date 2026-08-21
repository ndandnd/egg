# Cursor handoff: exact branch-and-price for the dictator over schedule columns

Date: 2026-08-20 (America/New_York)

This is an engineering-infrastructure task: build a certificate-bearing
branch-and-price (B&P) solver whose root node certifies `z_CH` and whose tree
closure certifies `z_D`, cross-validated against the existing independent
oracles. It produces code and tests only — no scientific artifacts, no cluster
runs, no claims. Read this file completely before changing anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `5b63e725d0fd85cfb0b83f462a612016e7f4321a`. If main has advanced through a
  reviewed merge, inspect the advancement and use the new clean main.
- Create a new branch such as `cursor/bnp-dictator`.
- Open exactly one new draft PR. Do not merge it.
- Do not read, import, list, hash, or touch anything under `src/runs/`,
  `result/`, any A6 holdout or transfer path, any `*CLAIM*.json`, or
  `runs/b3_factor_pilot`.
- Do not edit `doc/DECISION_LOG.md`, `doc/RESEARCH_STATUS.md`, or
  `doc/ENGINEERING_INCIDENTS.md`.
- Do not launch Slurm or any cluster job. Do not set `EGGLAB_REQUIRE_GRB`.
  All tests must pass with the CBC fallback backend.
- Solve-based tests may use only burned development seeds `{0, 11, 15}` and
  tiny sizes (`n_trips <= 6` for enumeration tests, `n_trips <= 8` for smoke).
  Never use any seed `>= 16`.
- Do not modify `src/egglab/evsp.py`, `b2a2.py`, `b2a345.py`, `a6.py`,
  `regimes.py`, `market.py`, `instance.py`, `solver.py`, or any existing
  experiment driver. All new logic goes in new files that call the existing
  public functions.

## Objective

The dictator problem is

```text
z_D  = min over integer complete fleet schedules S of ops_cost(S) + Delta(load(S))
z_CH = the schedule-column master optimum over convex combinations of columns
```

where `Delta` is the convex true market system-cost delta
(`AffineMarket.system_delta_true`). The existing evidence machinery computes
`z_D` via `egglab.regimes.solve_dictator` (adaptive tangent MILP) and `z_CH`
via `egglab.b2a2.certified_cg`. This task builds a third, structurally
independent path: a B&P tree whose **root node is the certified column-master
relaxation (`z_CH`)** and whose **closure certifies `z_D`**, so internal
uplift `z_D - z_CH` falls out of one coherent certified object.

Why this is tractable here: the pricing problem is already a MILP oracle
(`egglab.evsp.solve_evsp`), not a labeling algorithm, so branching
constraints can be absorbed as linear constraints in pricing instead of
destroying a label-domination structure.

## Design requirements

New files:

```text
doc/BNP_DICTATOR_SPEC.md
src/egglab/bnp.py
src/tests/test_bnp.py
```

Reuse, do not reimplement:

- master LP: `b2a2.solve_rmp(inst, market, columns, tangent_points, ...)`;
- column construction/identity: `b2a2.column_from_solution`,
  `b2a2.column_key`, `b2a2.canonicalize_pricing_solution`,
  `b2a2.pricing_incumbent`;
- pricing: `evsp.solve_evsp` (follow the dual-to-price convention used inside
  `b2a2.certified_cg`; read that function before writing any pricing code);
- charging re-realization: `evsp.solve_fixed_sequences`;
- physical replay: `evsp.validate_solution`;
- checkpointing (if used): `checkpoint.save` / `checkpoint.load`, writing only
  under a caller-supplied output directory (tests use `tmp_path`).

Certificate discipline (nonnegotiable; there are existing regression tests in
`test_b2a2.py` guarding exactly this distinction — imitate them):

- every lower bound must be built from certified dual bounds
  (`sol.stats.bound`, `min_rc_lb`-style Lagrangian bounds), never from
  incumbents (`obj_model`, `obj_true`, `min_rc_ub`);
- node lower bound: master `z_model` plus `min(0, min_rc_lb)` computed with
  the node's branching constraints imposed in the pricing MILP, exactly
  parallel to `certified_cg`'s bound at b2a2.py;
- global upper bound: only from an integer incumbent that passes
  `validate_solution` with an empty violation list;
- the returned result must be an interval `[lb, ub]` with an explicit
  `certified` flag; on any budget exhaustion (node limit, oracle-call limit)
  return `certified=False` with the honest partial interval — never a
  fabricated bound.

Branching rule:

- Ryan–Foster style on trip pairs: for trips `(i, j)`, branch
  "served consecutively by the same vehicle" versus "not". In the pricing
  MILP both sides are linear constraints on the sequencing variables. At each
  node, columns in the pool that violate the node's decisions are excluded
  from the master (filter by inspecting the column's `sequences`).
- Deterministic selection: among pairs whose lambda-weighted same-vehicle
  indicator is fractional, pick the one closest to 1/2, ties broken
  lexicographically by `(i, j)`. Deterministic node order (best-bound, ties
  by node id).
- **Charging subtlety you must handle and argue in the spec:** two columns can
  have identical duty structure (`sequences`/`arc_kinds`) and differ only in
  charging. Because charging is continuous for a fixed trip partition, a
  lambda-mix of such columns is integer-feasible: do not branch on it. Detect
  this case and round it to an incumbent via
  `solve_fixed_sequences(inst, sequences, energy_cost)` with the true convex
  energy cost (`('pwl', market.system_delta_segments(...))` plus exact
  re-evaluation through `system_delta_true`), following how
  `regimes.solve_dictator` evaluates true objectives.
- The spec must contain a short written correctness argument: why the
  branching scheme partitions the integer feasible set, why the node bound is
  valid under branching constraints, and why termination is finite.

Cross-validation gates (all as tests):

- root-node certified interval for `z_CH` must intersect the
  `certified_cg(...)["outcome"]` interval (`lb_best`, `ub_ch`) on the same
  instance/market with the same epsilon;
- final `z_D` interval must intersect the `solve_dictator` certificate
  (`stats.extra["adaptive_lb"]`, `obj_true`) on the same instance;
- on tiny instances (`n_trips <= 5`, small `max_vehicles`), enumerate all
  duty partitions exhaustively, realize charging exactly per partition with
  `solve_fixed_sequences`, and require the B&P interval to bracket the
  enumerated true `z_D` (imitate the `enum_truth` fixture pattern in
  `test_b2a2.py`).

Known repo gotchas:

- `synthetic_instance` has no horizon parameter; slot structure comes from
  `Instance` defaults (`n_slots=28`, `slot_min=60`). Construct `Instance`
  directly if you need a smaller horizon for enumeration tests.
- `solver.backend()` memoizes through `solver._BACKEND_CACHE`; tests must not
  set `EGGLAB_REQUIRE_GRB`.
- Tests self-bootstrap `sys.path` (there is no conftest.py); copy the header
  from an existing test file. Run from `src/`.

## Required adversarial tests

At minimum, asserting emitted values and state (never source strings):

- enumeration ground truth bracket on >= 3 tiny instances (seeds 0, 11, 15);
- root `z_CH` consistency with `certified_cg`;
- final `z_D` consistency with `solve_dictator`;
- branching constraints actually respected: after a "different vehicle"
  branch, pricing never returns a column violating it; after "same", never
  one separating the pair;
- column-pool filtering at a node excludes exactly the violating columns;
- a tampered incumbent (nonphysical load or charge) is rejected by replay and
  never becomes the upper bound;
- lower-bound discipline regression: a mocked pricing solution whose
  incumbent is better than its dual bound must not tighten the node bound
  beyond what `stats.bound` justifies;
- budget exhaustion returns `certified=False` with a valid partial interval;
- determinism: two runs with identical inputs produce identical node
  sequences, column keys, and final intervals;
- identical-duties/different-charging mix is rounded, not branched.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_bnp.py -q
python3 -m pytest tests/ -q
git diff --check
```

## Final report

Include: branch, draft PR URL, exact commits (spec/code first, any follow-up
second); test counts; the enumeration-bracket results actually observed; the
cross-validation intervals actually observed on seeds {0, 11, 15};
confirmation that no cluster job ran, no path under `src/runs/` or `result/`
was read or written, and no seed >= 16 was used. Label everything
"engineering infrastructure; no scientific claims." Do not merge; return the
draft PR for independent review.
