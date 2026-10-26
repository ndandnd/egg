# Adjacent EVSP-DR oracle boundary — static implementation

This package resolves the next call boundary after the completed EVSP-DR
correspondence and duty/market diagnostic. It does not rerun that diagnostic.
The adjacent implementation is used by reference at
`/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001`,
source revision `3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c`.

The concrete gap is a capacity-aware fixed-duty composition. The adjacent
`run_fixed_duty_terminal.main` is a file-driven historical entry point with
uniform charging power and no shared plug constraints. Its cost/terminal-energy
frontier cannot simply be supplemented with plug rows: it can discard schedules
with different station-time occupancy. The adjacent capacity-aware pricer and
master already provide the reusable routing machinery.

The selected local composition preserves that machinery and filters candidate
transitions before graph packing: a fixed-duty column starts at its prescribed
first trip, follows consecutive trips using any originally allowed direct or
station-charging realization, and returns only after its last trip. All inherited
charging-window alternatives and capacity-dual repricing remain in the adjacent
implementation. A full-routing arm uses the same unfiltered capacity network.
This is an interface adaptation, not a new pricing algorithm or theorem.

Read `API_CONTRACT.md`, `FIXED_DUTY_COMPOSITION.md` and
`SYNTHETIC_BRIDGE_DESIGN.md` for the precise source-defined boundary and deliberate
limitations. `boundary.py` is a static draft, not runtime-qualified code.
`REVIEW.md` records a focused static PASS; runtime compatibility is unqualified.

No imports, tests, hashes, case generation, original data, model assets, replay,
native calls or numerical experiments are authorized by this package. There is
no launch manifest or numerical attempt. A future synthetic bridge execution
requires its own exact fixture, source/import closure, request/command and paid
resource design. The sibling checkout is unchanged and its jobs are untouched.

The research question remains whether learning can improve a valuable, costly
route/column proposal step beyond competent conventional controls. Historical
warm-replanning continuation failures remain scoped negative results; they do
not establish permanent neural-route impossibility. This source adaptation
establishes neither learning value nor a computational bottleneck.
