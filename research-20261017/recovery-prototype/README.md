# Candidate recovery lift prototype

**Candidate only; not imported by the running solver or frozen screenv3 workers.**
This pure mapping/replay helper is useful with any ranking. It does not promote a
recovery experiment, bypass the complete-screen recovery gate, launch jobs, submit
starts, build a model, optimize, or change solver bounds/constraints. No src/model
files were edited for this package. See ../RECOVERY_IMPLEMENTATION_CONTRACT.md.

`lift_plan(source_case, full_case, source_plan, a=..., b=...)` checks unique IDs,
identical trip/physical policy definitions and exact same-ID movement definitions,
with source movements a subset of full movements. It independently replays the source,
checks route ownership, copies only physical route/charge events, recomputes full
load/operating cost from those events, independently replays the full case, and
recomputes the true bill at the supplied target market with the campaign's canonical
`Fraction(replay['ops_cost']) + native_hull.supply(market, replay['load'])`.
`true_bill_exact` is the authoritative rational string for comparison/accounting;
`true_bill` is a float display only. Exactness describes arithmetic on the replayed
numeric witness, not an additional proof of floating-point physical feasibility. Cases may differ in names,
movement order/extra edges, and trip order. Resources, market edges and physical/cost
policies must match exactly; this is deliberately narrower than a general translator.

Output includes a full-case physical fallback, replay evidence, target-market bill,
source/full identities, source-plan/market hashes, subset/selected/added IDs, and an
ordered list of `{movement_id, value}` entries. Every full movement is included;
unselected/extra edges have zero. No positional interval, charge/SOC/load/epigraph
variable assignments are emitted. Full elementary intervals can split when restored
edges introduce new charging-window endpoints; saved source `(j,k)` arrays are ignored.
Inputs are not mutated; returned physical event records are independent deep copies.

The specification is **not a Python-MIP start submission**. A later adapter must validate
full model variable inventory, map IDs to live binaries, and submit values without fixing
bounds. Continuous variables remain unspecified. Native-matrix feasibility, solver start
acceptance, search/certification, common-clock/reserve enforcement, fallback integration,
completion, solver logging and experiment attribution are outside this prototype.
Output is explicitly `physical_fallback_only`, `not_submitted`, with no global lower bound.
It is not stamped as a solver-extracted plan and cannot be passed through the current
strict native start validator without the contract's explicit future lift adapter.

Handcrafted tests use one 15 kWh service and an explicitly constructed valid terminal
charge; no dataset reads, solver-generated fixtures, monkeypatching or live integration.
One extra unused pullin introduces a 75-minute interval boundary. Tests check movement
permutation/all-zero extras, interval splitting without charge-index transfer, changed/
unknown/duplicate IDs, invalid replay, target-market recomputation, input immutability,
and an API with no model/continuous/bounds assignment capability. A test import guard
forbids mip/gurobipy imports. Tests establish pure mapping/physical replay behavior only.

Exact command (from worktree root):

```sh
PYTHONPATH=src:research-20261017/recovery-prototype .venv-local/bin/python -m pytest -q research-20261017/recovery-prototype/test_recovery_lift.py
```

Parent verification in the campaign runtime: **10 passed in 0.03 s**. No solver/training/cluster calls or screen result reads.
No experiment launch or commit.
