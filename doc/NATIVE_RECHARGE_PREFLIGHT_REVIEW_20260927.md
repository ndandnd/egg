# Native-recharge independent preflight history and V2 review

27 September 2026. This document preserves the original V1 preflight and adds
an independent read-only review of V2. The reviewer did not edit implementation,
runner, tests or protocol and did not execute or initialize a native optimizer.
The reviewer saw the intended model, prospective targets and source; this is an
independent implementation review and reconstruction, not a blinded review.

**Pre-execution V2 verdict: ready for a new prospective source freeze and separate
local qualification, provided the files match the hashes below.** No remaining
blocking issue was identified for the declared single-connector synthetic gate.
This verdict does not say that V2 has passed a native experiment. Attempt1 stays
FAILED: nine certified controls, three expected infeasibilities and three
extraction/replay exceptions, for 12/15 passing overall.

## V2 reviewed snapshot

| File | SHA-256 |
|---|---|
| `src/egglab/native_recharge.py` | `52d4429299918ae1e98c2f523f0bfcef97d606de2a6d281d8addbe3d7459f9dd` |
| `src/experiments/native_recharge_qualification.py` | `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e` |
| `src/tests/test_native_recharge.py` | `500ae0e1164511c4e677167038f5decccf809657dc2091e991f5d49a2c6d7bc9` |
| `doc/NATIVE_RECHARGE_QUALIFICATION_PROTOCOL_20260927.md` | `5de2d7ad1ef5ae41c7069a6b3b0159009130e25c611eaf259ee50d667e5b617a` |

The first frozen implementation was
`d37878392f0848d34f28921c97b6e8d8e6533a77`. Comparing all four V2 files against
that commit shows the shared physical builder's constraints unchanged; its
return value now also exposes assignment and SOC variables for raw evidence.
The planner exposes epigraph variables for the same reason. The changes concern
incumbent capture, numerical witness conversion, associated objective accounting,
new event types, tests and the prospective V2 protocol.

The reviewer serialized the entire current `controls()` definition to JSON and
compared it with attempt1's `frozen.json`: all 15 complete cases, physical
identities, objective coefficients, expected statuses and targets are identical.
This comparison normalizes dataclass tuples into the JSON arrays used in the
archive; it does not alter any numeric value or physical input. Native budgets,
replay tolerances and certificate admission checks remain unchanged.

The principal researcher subsequently froze this reviewed V2 snapshot in commit
`997575d049a66d952a0cb8d79f974f7ba5f4ccf0`. Any run outcome is separate evidence
requiring artifact review; no optimizer was executed by the preflight reviewer.

## V2 endpoint and correction arguments

For each compiled interval `[a,b]`, every eligible recharge visit spans that
whole interval. Given retained positive energies `e_i`, their total `E`, and
common usable connector rate `P`, assign the first start exactly `a`, the last
end exactly `b`, and interior endpoints

`t_j = a + (b-a) * (e_1+...+e_j)/E`.

In exact arithmetic, every session has the same charging power
`60E/(b-a)` and all sessions are consecutive. When `E<=P(b-a)/60`, this gives a
physical schedule at or below the connector limit, even when the original
maximum-rate decoder would have left idle time. Each owner remains available
throughout the interval, and each monotone charging visit receives the same
total energy. Grid-period loads, SOC endpoint equations and objective values
therefore do not change solely because of this timing rule.

V2 computes the cumulative arithmetic using `Fraction.from_float` before
converting endpoints. It requires every positive session to have distinct,
increasing float endpoints inside the original interval. A positive head/tail
that cannot be represented fails; it is neither discarded nor moved to another
interval. Since the last endpoint is the exact interval boundary, no tail from
one interval spills into the next. The existing independent replay keeps strict
connector-overlap rejection and checks the actual emitted session power and SOC.

Floating endpoint conversion may leave a positive capacity residual. V2 measures
that residual separately for **each materialized session** in exact binary-rational
arithmetic, using its unchanged energy and actual emitted float duration. It
sums only positive excesses. The sum of these excesses plus all finite
negative-to-zero charge corrections must fit one `1e-8`-kWh budget for the
whole incumbent. This is stronger than an aggregate interval capacity check:
underallocated duration for one session cannot be hidden by slack in another.
Aggregate interval excess is also saved and checked against the same budget.
No allowance is multiplied by the number of intervals or variables.

Only finite negative native charge values may be changed to zero. All positive
energies remain unchanged. The normalization records original variable keys and
before/after values, exact and decimal total L1 correction, and acceptance. A
nonfinite value or over-budget total fails. The native feasibility tolerance is
`1e-8`; this policy is a prospective numerical conversion convention, not a proof
that corrected plans meet exact real-arithmetic physical constraints. The full
unchanged replay, load comparisons and native-objective consistency checks still
apply. An economically material correction at a large price must therefore fail
the existing objective check even if its energy correction is numerically small.

The archived V1 failures do not contain the raw values needed to estimate their
actual corrections. No V2 cutoff or expected pass rate is inferred from missing
failed values. The numerical mechanism is demonstrated by constructed arithmetic
examples only; those examples do not reconstruct the failed incumbents.

## V2 evidence-capture review

For every admissible native incumbent, `native_status` is recorded first and a
`native_incumbent` snapshot is flushed before `_extract` runs. The snapshot
contains all native model variables, their indices, names, types, bounds, raw
numeric values and raw representations. Nonfinite or missing values are retained
as a null numeric field plus their representation, allowing JSON serialization.
Semantic index mappings identify trip assignments, used vehicles, movement
choices, SOC before/after, interval energy variables, market loads and epigraphs;
trip/movement identifiers and compiled intervals are included.

Normalization and successful serial decoding are separate events. The latter
contains actual sessions, exact/decimal correction-budget totals and interval
residuals. The final plan also retains raw charge aggregates, native load
variables and per-period load changes. Before bound admission, separate events
record the recomputed linear objective or PWL envelope/true cost and the charge
correction's objective effects. Thus a later extraction/replay/admission failure
leaves the original incumbent snapshot available. A decoder failure need not have
a successful `serial_decoding` event; its raw inputs and frozen conversion rule
are sufficient for an independent failure reconstruction.

The controller recognizes the new event types while preserving earlier raw status
and timeout accounting. It still attempts all declared cells and retains failed
cells. The raw snapshot is part of the qualifier's recording path; calling the
library functions without a record callback does not itself create persistent
files or promise a raw-evidence archive.

## V2 verification performed

The reviewer reran all tests with pytest plugin autoload disabled and a meta-path
hook raising on any `mip`, `mip.*`, `gurobipy` or `gurobipy.*` import: **62 pure/
fake-oracle tests passed in 0.08 seconds.** No native optimizer was imported,
initialized or run. The added checks cover finite negative-only normalization,
whole-incumbent budget aggregation, interval-contained endpoints, energy
preservation, rejection of unrepresentable positive sessions, saved correction
and load deltas, and raw variable/mapping snapshots. Existing corruption,
objective consistency, failure-continuation and backend identity tests also pass.

This remains preflight. Actual Python-MIP variable capture, native numerical
values and V2 outcomes need the new frozen local attempt and independent artifact
review. A subsequent cross-backend run must retain the first attempt and use its
own prospective protocol and evidence; this review makes no cluster execution
or scalability claim.

## Preserved V1 preflight

The following is the original review history. Its ready-for-qualification verdict
preceded the first native run and must not be read as a claim that the later V1
qualification passed. The separate first-run artifact review is
`result/native_recharge/20260927-attempt1/review/REVIEW.md`.

### Original V1 preflight

27 September 2026. Reviewer: the independent literature/theory and audit agent;
implementation author: the native-adapter/reuse-design agent. Read-only review
of the implementation, runner, tests and protocol; the reviewer did not edit
any of those files, initialize a native solver, or execute an optimizer.

**Verdict: ready for the prospectively frozen 15-cell synthetic qualification,
subject to matching the reviewed hashes below.** Three actionable findings were
sent to the author, repaired before freeze, and checked again. No blocking
scientific issue remains identified for this declared graph, homogeneous battery,
constant efficiency, zero/one-connector model. This is preflight, not a claim that
the native solver has qualified, reproduced any target, or scaled to real data.

## Reviewed snapshot

Paths are relative to `journal-research-work`. The implementation was in progress
when first inspected; the final review applies to these exact repaired files.

| File | SHA-256 |
|---|---|
| `src/egglab/native_recharge.py` | `3b7af6b5b9f19a659415ba443e5f14e2d745615ae41ce7a2dffeaa58aad9d32d` |
| `src/experiments/native_recharge_qualification.py` | `f475cc6d4078a28829b33e1d0371a7f4a2ec824614e71837694a859efab666de` |
| `src/tests/test_native_recharge.py` | `b39651280102187b01dd10eac4a9027cad95bc8fdc34765586549ae06b1a2e5c` |
| `doc/NATIVE_RECHARGE_QUALIFICATION_PROTOCOL_20260927.md` | `016c911e3f11e77710c5132c690ba1dc6e19f64d442ea38f794a60565f1b6dd4` |

## Findings and resolution

1. **Replay could omit an adjacent-float charging session.** The original
   midpoint sweep accepted 10 grid kWh between `60.0` and
   `math.nextafter(60.0, math.inf)`: duration approximately
   `7.105427357601002e-15` minutes, actual power approximately
   `8.44424930131968e16` kW. The midpoint rounded to the session start, so a
   strict midpoint-containment test found no active session. A separate valid
   20-kWh terminal session let the full SOC and energy checks pass, and the
   reported maximum power was only 30 kW. The repaired sweep uses positive
   interval intersection and endpoint containment in resource intervals.
   The independent reviewer reproduced the original acceptance before the fix;
   the new `nextafter` regression rejects it. This was a witness-checker
   vulnerability, not evidence that the correct MILP could produce 10 kWh in
   such an interval.
2. **A truncated worker artifact could abort the remaining campaign.** The
   controller previously decoded all event lines and the result without a
   per-cell parse guard. A hard kill during a write could raise JSON decoding
   outside worker handling, preventing later controls from being attempted.
   `read_worker_evidence` now preserves the valid event prefix, records the
   artifact/line issue, leaves the raw bytes intact, and makes that cell fail.
   The fake timeout control writes both a partial event and partial result,
   verifies incomplete call accounting, and verifies all 14 subsequent controls
   are attempted and pass under the fake worker.
3. **Bound admission lacked native-objective consistency.** Merely comparing
   the native lower bound to a replayed true upper bound could admit an
   inconsistent native incumbent or a planner lower bound greater than its
   own feasible PWL objective. Pricing now requires the native incumbent to
   equal the independently replayed linear objective within objective tolerance.
   Planner admission checks `lower <= current saved envelope <= true cost`,
   `lower <= native incumbent`, and `native incumbent >= envelope`, with the
   stated guards. Equality to the envelope is deliberately not required:
   a time-limited FEASIBLE epigraph solution may contain legitimate slack.
   The slack and envelope are saved. Regressions reject inconsistent
   incumbents/bounds and admit legitimate FEASIBLE epigraph slack.

The parent independently identified an earlier SOC event-ordering issue:
charge completion and an instantaneous outbound energy-consuming leg may have
identical times. The repaired ordering credits completed charge first. Its
regression uses a positive-energy outbound leg and passes. This finding is
attributed to the parent, not to this reviewer.

## Feasible-set reasoning

**Path coverage.** Each strictly positive-duration service must be owned exactly
once. Each owned service has exactly one entering and one exiting selected mode;
each used vehicle has one pull-out and one pull-in. Every inter-service mode
starts after its predecessor ends and reaches its successor by that service's
start. Service start times therefore increase strictly along each selected arc.
There is no directed service cycle to support a disconnected circulation. In a
finite acyclic graph, flow conservation plus those degree constraints forces
one nonempty connected service path per used vehicle. Empty used vehicles,
branching and disconnected cycles cannot supply extra initial battery energy.
The decoder also rejects malformed/disconnected selected paths, and replay
checks exact coverage and movement ownership again.

**Inactive big-M.** With battery bound `B`, movement energy `e >= 0`, inactive
charge is exactly zero because each charge variable is bounded by its selected
mode. `M=B+e` is sufficient. Over before/after SOC in `[0,B]`, the inactive
residual ranges are: pull-out `[e-B,e]`; direct/depot `[e-B,e+B]`; pull-in
`[-B-e,-e]`. All lie within `[-M,M]`. For a depot arrival with inbound energy
`e_in <= e`, the relaxed reserve inequality is valid because
`B+e-e_in >= reserve`; its relaxed capacity inequality is also redundant.
The same argument applies to the pull-in reserve constraint. Thus a costly or
energy-infeasible unselected alternative does not constrain another selected
path. This is an analytical code review of the formula, not an executed
native matrix/basis audit.

**SOC and cyclic conservation.** Selected pull-out equations start each used
bus full. Service equations debit mandatory battery consumption. Depot visits
check arrival reserve, post-charge capacity, and the next service's SOC;
pull-in equations require final battery exactly full. Every movement leg has
nonnegative consumption, so its intermediate SOC is bounded by its endpoints.
Within a charging visit SOC rises monotonically, so arrival and total-charge
capacity constraints cover any serial distribution of that energy. Without
regeneration, self-discharge or overlapping movement/charging, event endpoints
suffice. Replay independently visits each leg and service event and enforces
reserve/capacity/full replenishment. Fleet grid charge times efficiency equals
service plus travel energy; more used buses do not donate net initial energy.

**Grid units.** Every charge variable, period load and price payment is grid
kWh. Only the battery equation applies `efficiency * grid_kWh`. Supply cost is
also evaluated on grid load. A loss factor consequently changes grid demand
and available battery replenishment, not just a reported price coefficient.

**Exact partial windows and finite connector.** The elementary partition
contains every candidate recharge-window endpoint, resource change, market
change and terminal opening. Each eligible visit covers its entire elementary
interval. For a single homogeneous connector and common usable rate
`min(per_bus_kw, grid_kw)`, nonnegative session energies with total at most rate
times interval duration have a constructive consecutive schedule. The decoder
emits exactly such sessions at that rate. Each vehicle has at most one selected
available visit in the interval; there is no hidden simultaneous use of that
vehicle or plug. Battery capacity depends on total charge in each monotone
visit, so serialization does not invalidate SOC. Replay re-derives windows and
checks actual resource/session overlaps instead of trusting compiled capacities.
This exactness requires preemption across intervals, continuous charge control
and zero switching time. It does not extend this formulation to two connectors,
heterogeneous per-vehicle charging rates, minimum sessions or charging taper.

**The cyclic fixture retains the full two-bus family.** Native terminal opening
is zero, while early and late resource windows are separate. An A-only bus may
therefore recharge after A in the early window; its native visit remains owned
by its pull-in. The family `(x,30-x), 0<=x<=10` has physical two-bus minimum 99.
Changing terminal opening to 180 would remove that family and change the minimum
to 104; this would be a different feasible set. The repaired protocol and tests
explicitly preserve this distinction.

## Bound, status and accounting reasoning

Pricing and planning call the same builder and attach different objectives;
there is no separate relaxed fleet feasibility in the planner. Linear pricing
supports any finite price vector. Quadratic planning requires nonnegative
curvature. Its tangent epigraph is a global underestimator in exact arithmetic;
each round uses a fresh common model and saves an immutable tangent snapshot.
The native global bound gives a conditional lower bound; a decoded/replayed
physical plan gives a true-cost upper bound. The tighter saved-envelope check
now catches an internally inconsistent reported native bound before combining
rounds. Floating tangents, CBC/GRB bounds and `1e-6` outward guards are numerical
certification conventions, not rational proofs of a global interval.

`OPTIMAL` and `FEASIBLE` remain distinct raw statuses. Either may supply an
incumbent and finite global bound; only an outward-widened width at most `1e-4`
gets the wrapper status `certified`. A wider valid interval stays `bounded`.
Missing incumbents/statuses remain unresolved; inconsistent bounds or physical
witnesses fail. `INFEASIBLE` is explicitly solver-conditional. A later planner
infeasibility after an already replayed feasible plan raises an inconsistency.
This prospective policy does not change the older reuse protocol's OPTIMAL-only
gate or turn its recorded FEASIBLE failure into a success.

Backend name and loaded Python-MIP backend module must agree with the explicit
request. Available native library identity/hash is saved, and missing identity
is not invented. The solve routine requests one thread and a 10-second maximum
native phase, with 45-second routine budget; the worker process is externally
capped at 60 seconds. Model-building/serialization overhead and solver time-limit
responsiveness mean45seconds is not a strict process runtime bound. The outer
60-second process cap supplies the campaign limit. There is no hidden LP-first
solve. Calls started are entry attempts logged immediately before the remaining
budget check; if that check raises before `optimize`, the start has no returned
status. This is conservatively incomplete accounting, not a completed solve.

Attempt creation and receipt writes are exclusive. Source hashes are frozen
before worker launch and checked inside each worker. Native status events are
flushed before physical extraction. Truncated artifacts fail the cell while
preserving the valid prefix and allowing later controls. The controller records
all 15 targets, including expected failures, without retries or cap extensions.
The CLI freeze label is an operator assertion; it does not itself prove that
Git contains the label or that the checkout matches that commit. The protocol
explicitly assigns commit/hash verification before launch to the principal
researcher. This manual condition must be satisfied before interpreting a run
as prospectively frozen.

## Independent verification actually performed

The reviewer reran the entire repaired test module in the repaired research
Python environment with pytest plugin autoload disabled and a meta-path hook
that raises if `mip`, `mip.*`, `gurobipy` or `gurobipy.*` is imported. Result:
**57 passed in 0.09 seconds; zero native optimizer imports or executions.**
The tests cover pure fixture validation, replay, corruption controls, interval
compilation/serialization, budget/status checks, fake oracle behavior, backend
identity checks with dummy modules, and fake subprocess continuation. Passing
these tests does not test actual Python-MIP row construction, integrality,
backend installation, infeasibility correctness or native solver tolerances.

Reproduction from the reviewed worktree (the hook intentionally prevents the
next scientific step from occurring as a side effect of this command):

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.research-venv-repaired-1176/bin/python -B - <<'PYTEST_REPLAY'
import importlib.abc, sys
class BlockNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if (fullname == 'mip' or fullname.startswith('mip.')
                or fullname == 'gurobipy' or fullname.startswith('gurobipy.')):
            raise RuntimeError('Native optimizer import blocked: '+fullname)
sys.meta_path.insert(0, BlockNative())
import pytest
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider',
                             'src/tests/test_native_recharge.py']))
PYTEST_REPLAY
```

## What this gate can and cannot establish

The 15 fixed controls are appropriate for initial native qualification: nominal
linear/pricing/planning identities, grid losses, preserved versus fixed usable
capacity, the joint positive-reserve/loss witness, cyclic replenishment,
terminal-capacity infeasibility, insufficient partial-window capacity,
consecutive finite-connector sessions and directed multileg consumption/cost.
The expected 12 certified / 3 infeasible split is prospective, not an observed result
in this review. Native disagreements must remain in the first-run evidence.

After the freeze, an independent result review should reconstruct the received
case identities, all physical sessions, objectives, saved tangent envelopes,
roundwise bounds and call accounting from the archived artifacts. A separate
backend replication can test implementation sensitivity. Stronger later controls
could add a deliberately high-energy *unselected* movement to exercise the
analytically reviewed inactive-M argument through a real backend, and independent
enumeration of a heterogeneous small graph to test coverage beyond these
closed-form fixtures. These are useful next gates, not claims already established.

The module proves neither source-graph completeness nor economic generality.
It solves exactly the declared movement alternatives. It does not validate
missing GIRO energy, infer reverse arcs, qualify a production adapter, establish
scaling to 30 services, or turn synthetic objective units into real tariffs.
Replay is a different code path inside the author's module; this external review
and its import-blocked tests add scrutiny but are not a separately implemented
full native physical/pricing certificate.

Subsequent coordination note: the principal researcher froze these four files
in commit `d37878392f0848d34f28921c97b6e8d8e6533a77` and launched the first
dedicated native attempt after the preflight. Its results and any failures are
separate evidence requiring a new result audit; they do not retroactively change
what the preflight did or tested.

## Subsequent artifact-audit outcomes

The first frozen CBC attempt remains failed (12/15 passing: nine accepted
certificates, three expected infeasibilities and three extraction/replay
exceptions). Its independent archived-evidence audit is recorded in
`result/native_recharge/20260927-attempt1/review/REVIEW.md`.

The separately frozen V2 local attempt passed all 15 controls (12 accepted
certificates and three expected infeasibilities). Its independent audit checked
27 raw incumbents, 1,030 variable values, 60 physical sessions and all correction
ledgers, with 16 corrupted copies rejected. The maximum combined numerical
correction was 7.105427357601002e-15 kWh under the prospective 1e-8 kWh budget.
Full scope and limitations are in
`result/native_recharge/20260927-attempt2/review/REVIEW.md`. These are later
artifact outcomes, not tests retroactively attributed to either preflight.
