# CF1 fixed-discrete charging helper: source implementation

24 October 2026. `src/egglab/constructive_charging.py` adds
`complete_topology(case, selected_ids, a, b, budget, *, deadline, record=None,
clock=time.monotonic)`. This is candidate source, not native qualification or a
claim of completion within six seconds. Qualified coordinator, schedule, replay,
pathflow, objective attachment and native optimizer sources are unchanged.

The caller must compute ONCE, **before initial setup/build**,
`completion_deadline=min(t0+.2*T, first_completion_anchor+max(2,.1*T))` and
reuse that exact absolute value across all repairs/rebuilds. Passing stageend
`t0+.2*T` alone or recomputing `now+6` is not the cumulative policy. All
activity inside the window counts conservatively. This helper has no T/anchor
input and cannot independently enforce or qualify the caller policy. The
composite CF1 orchestrator remains unimplemented/unqualified; no native launch
is authorized by this source-only package. No local six-second clock is created.
Validation, path recovery, original full-model build, inventory, objective
attachment, each solve, capture, extraction, independent replay, exact billing,
event recording and candidate copying are charged within it. Checks surround
these operations; the existing native `_optimize_once` receives that same
absolute deadline and caps each native call by the remaining time and the
validated phase budget. Python setup/extraction is not preempted internally:
the external supervised allocation remains necessary. Clock values must be
finite and nondecreasing; new work requires strictly positive remaining time.

`recover_paths` validates the complete proposed topology before model build.
The helper builds the original full compact pathflow model, requires both model
and compiled identities to match the case, and checks the original positive
physical-row count. It fingerprints original rows by index/name/sense/constant
and variable-index coefficients. Every movement has exactly one distinct binary
variable initially bounded [0,1]; every other variable must be continuous.
All movement bounds become the proposed exact 0/1 values, including unselected
movements. Repeated inventory checks verify fixed bounds and preserve all
physical rows, while allowing appended tangent epigraph rows/continuous columns.
Binary types remain binary; this is a **fixed-discrete charging subproblem**.
`native_lp_certified` remains false. Inventory/source checks do not certify a
backend implementation or prove unrestricted feasibility/optimality.

There are at most three sequential native calls: zero-objective feasibility;
first target tangent objective with (a,0); then a second objective retaining that
line and adding (a+bL,-bL²/2) from the first objective's independently replayed
load. No other refinement or retry occurs. Only a timely initial feasibility
INFEASIBLE with no incumbent, verified inventory and successfully recorded status
sets `reverse_repair_allowed`/`repair_allowed`. Other status/no incumbent,
objective-stage INFEASIBLE, timeout, extraction/replay/inventory failure and sink
failure never authorize reverse-merge repair. This helper does not itself undo
merges or rebuild a topology.

Before each extraction, `native_incumbent` records the complete raw capture via
the caller's sink (and the returned events). Extraction uses the existing
pathflow projector/decoder. The extracted movement IDs must still equal the
proposal, without duplicates. Independent native replay checks physical SOC,
charging/resource contention and terminal replenishment. The exact target bill
uses Fraction arithmetic on replayed binary64 operations cost, loads and a,b,
including the one-half quadratic term. Only an in-time, replay-valid candidate
whose witness event completed successfully becomes the best result. The cheapest
exact bill across feasibility and objective witnesses survives later timeout,
status, extraction, inventory or sink failures. No durable fallback or full-search
start is written/submitted here; a later orchestrator must handle those steps.

The JSON result contains status, plan/replay, true_bill/true_bill_exact, stages,
inventory, failures/events and repair flags. Native lower bounds in stage stats
are renamed `fixed_topology_lower_bound` with explicit scope;
`global_lower_bound` is always null. A feasible result with later failures means
only that an earlier physical witness remains available, not that later work
succeeded. CA1/CF1 are heuristic proposals, not certificates of fleet optimality,
quality, speedup, generalization or native qualification.

No test, runtime import, native solve, data/model access or process launch was
performed to create this implementation note. Parent owns any prospective
source-bound focused check and its complete accounting.
