# Exact candidate-density control — prospective protocol

25 October2026. New research-only pilot under `RESOURCE_DECISION.md` and the
completed matching-pool study's `NEXT_CONTROL_DECISION.md`. Freeze source,
protocol and exact command after one focused static integration review. No
imports, tests, hashes or numerical execution during static preparation. All
completed matching-pool/greedy/fleet-first sources and outcomes remain unchanged.

```
.venv-local/bin/python research-20261025/density_control/run.py --root /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017 --output research-20261025/density_control/attempt01
```

## Four frozen decisions, one seed

Order is exactly40/CA1,40/CoverCA1,80/CoverCA1,80/CA1 on exposed synthetic screen
cases `scale:50685:40` and `scale:50605:80`. Ordinals and folder names:

1. `01-scale-50685-40-CA1`
2. `02-scale-50685-40-CoverCA1`
3. `03-scale-50605-80-CoverCA1`
4. `04-scale-50605-80-CA1`

Rebuild each full case anew inside its decision clock and verify original case
identity/movement order against the existing `local-assets-v3.json` case record.
Use the original day market. No old learned assets, chosen routes, labels,
endpoints or raw logs enter selection. No training, cluster or protected
DEV/TEST/A6/B3/confirmation/GIRO. These cases are already exposed development
evidence; this is not independent evaluation or a comparison with historical
default-seed results.

Native solver seed is explicitly17: assign `built['model'].seed=17`, read it
back before solve and verify again after solve. Record requested/read-back
values per decision. One native thread and no seed search. The cover's frozen
seed17 hash diversification is a separate algorithmic convention.

## Selection: identical B and exact K

`selector.py` calls existing `classical_controls.ca1_score(case,a,b)` and
`select_connections(case,scores)` anew in each arm. The ordinary returned ledger
supplies the authoritative backbone B, flexible ordering, boundary set and
quota K. Do not separately reimplement or retune B/K. The unchanged selector
uses `K=min(M,max(ceil(.30*M),|B|))` for M original direct/depot modes.

CA1 retains exactly the ordinary selector's flexible set and all boundaries;
the implementation asserts exact equality with that returned set. It does not
compute a cover. CoverCA1 freshly calls the frozen function from
`matching_pool/pool.py` inside the arm clock, preserving its three global covers
and all parallel direct/depot modes for selected pairs. Let C be its flexible
union. Require `|B union C|<=K`; otherwise save the selection/design failure and
do not build/solve that decision. Never increase K, discard cover modes, or
adapt the pool after seeing a result.

For CoverCA1, protect B union C, then take the first remaining IDs in the same
ordinary CA1 flexible order until exactly K. Retain all original boundaries.
Validate count, protected membership, original movement identity and unchanged
B/K/boundaries across the two freshly computed arms of each case. This audit
comparison does not cache or reuse a score or construction result.

Preserve `selection.json` with all sets, fill order, exact counts, ordinary-CA1
overlap and direct/depot/boundary counts. `mode-ledger.jsonl` stores every
original movement's kind/endpoints, B/C/fill/selection membership, CA1 rank,
stress flag, proxy cost, margin and charging capacity feature. Save the freshly
computed `cover-ledger.json` only in CoverCA1 arms. CA1 features and route-only
covers are proxies, not electric-fleet feasibility or bounds.

## Same original physics and fleet objective

Reuse the completed matching-pool driver structure: original full physical
path-flow model, one physical matrix inventory per decision, and only excluded
movement upper bounds set to0. Retained routing stays binary with lower0/upper1;
no variable is fixed1. Save before/after bounds. Physical rows, SOC/reserve,
shared charging resources, load equations and full-case identity are unchanged.
Declared model dimensions do not shrink by this design, even if presolve later
simplifies the arm-restricted model.

Objective is pure vehicle count, the same as the last full/matching-pool
controls. One `_optimize_once` call per decision, cap<=60s, with no secondary
objective solve, warm start, repair, fallback or restored full search. Native
lower bounds are arm-restricted fleet-count bounds, not unrestricted bounds or
electricity-cost certificates. Electricity/system cost is evaluated after replay.

Save one native capture, use unchanged extraction/projection/serial-decoding
checks, independently replay on the original full case, require plan membership
in that arm's retained set and fleet/native incumbent agreement under existing
`BOUND_GUARD`. Recompute exact Fraction operating plus integrated supply cost.
Never admit from proxy scores, cover path counts or native status alone.

## Budget, provenance and receipts

Whole-process720CPU/600wall seconds; one Python/native thread, observed peak
RSS<=5GiB. Four120-second clocks: preparation/selection/model/inventory/bounds
through30, native deadline90 with cap60, capture/extraction/replay/durable output
through120. Cold/shared imports and all source/input work count to the package.
CPU hard limit720, wall alarm600, cooperative body705CPU/585wall retain15 seconds
closure. The persistent first-stop latch prevents a further decision after stop.
Parent owns external hard stop; native calls/Python alarms are not a hard
preemption guarantee.

Exclusive `attempt01` master/case receipts start incomplete and replace only
their own placeholders when finalized. Stream selection modes, physical
inventory, bounds, native capture, events and plan/replay as separate artifacts;
case receipts stay compact. Master `cases` contains the four ordinal/arm entries.
Receipt-inclusive `accepted_within_offline120` requires a physically checked
durable witness and elapsed<=120. Complete/zero-exit diagnostic is distinct from
competence: parent checks exposed-case targets<=3 buses40 and<=5 buses80 and
reports every assigned arm/failure. No-incumbent, late, extraction/replay failure
or design failure is preserved without automatic retry or a claimed opponent win.

Hash specifically consumed new source/protocol/resource/decision bytes, the
frozen old pool source, case lock and actually imported project-source closure
once in the metered process. Include dynamically imported
`experiments.codex_offline_rank` (the common-backbone dependency) as well as
`egglab` modules; do not duplicate source hashes or reopen old model assets.
A separate60CPU/90wall provision covers one compact summary/lossless archive,
not another solve. No new monitoring/inventory framework or test matrix.

The readout separates a sparse-density confound from fixed matching structure
at equal flexible count/B and native seed. One exposed pair/one seed cannot
establish generalization, robust superiority, novelty or learned electricity-
information value. A successful control only motivates a separately frozen
multi-group/multi-seed, paid-preprocessing, equal-total-budget study.

## Static review and finalization freeze

Parent reviewed the selector and complete driver diff; the one focused peer
review in STATIC_REVIEW.md found no substantive blocker on the stable files.
No executable source gate or repeat matrix was needed for this research-only
thin control. Sources are frozen from dispatch through completed receipts.
Finalization source is finalize.py (separate from the native process inputs):

```
PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -p -o research-20261025/density_control/finalization-time.txt .venv-local/bin/python research-20261025/density_control/finalize.py
```

It reads all four compact outcomes first, summarizes count/overlap/receipt
agreement, and archives large captures/inventories losslessly in one streaming
hash+gzip pass. It never replays, scores or invokes an optimizer. Original large
files remain local, with archival counterparts committed. Actual finalization
cost is added to the numerical-process sum; this does not measure whole-session
CPU or replace the separate historical conditional guard.
