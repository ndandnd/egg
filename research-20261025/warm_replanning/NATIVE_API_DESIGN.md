# Native API for warm fixed-fleet tariff replanning

25 October2026. Static design and thin library implementation only. No imports,
tests, hashes, model loads or native calls were executed while preparing these
files. No completed source, controller, physical constraint or replay tolerance
is edited. Cohort/asset/source/command/budget freezing and execution remain the
parent's subsequent work.

## Exact caller API

`planner.py` provides:

```python
replan(full_case, a, b, *,
       fallback_plan, retained_ids=None, seed, fleet_count,
       native_deadline, admission_deadline, budget,
       use_native_start=True, fixed_route=False, completion=True,
       record=None, clock=time.monotonic)
```

The caller starts the inclusive decision clock before case loading/scoring,
retains and durably saves the predetermined common full-case fallback before
loading a scorer, and passes an absolute native cutoff at anchor+52seconds and
final admission cutoff at anchor+60. Cold imports/scoring/build/search/replay/
publication all count. `budget.threads=1`, `budget.max_rounds<=4`; the caller
chooses `phase_seconds` from remaining allowance divided by the frozen round
cap. All calls share the same absolute native cutoff. Parent owns the external
process/RSS/CPU limits; this module is not a timing or resource controller.

`fleet_count` is REQUIRED and equals the acquired prior's vehicle count. Every
active replanning arm—including full and fixed-route—adds exactly
`sum(original pullout binaries)==fleet_count`. Original SOC/shared-resource/
energy physics remain unchanged. This operational restriction isolates
electricity/deadhead improvement from another fleet-acquisition comparison.
It is not a full unrestricted-problem certificate. Prior acquisition remains a
separate pure-fleet operation and cost record; this module does not acquire it.

Result fields: top-level `plan`, `replay`, `true_bill_exact`, `true_bill`,
`selected_source`, `used_fallback`, `fallback_bill_exact`,
`fallback_in_search_space`, `conditional_fleet_count`, `fixed_route`, `status`,
`rounds`, `native_calls`, `start_reports`, `failures`, `admitted_monotonic`,
`returned_monotonic`, initial tangent points/cuts, and both deadlines. Round/call
records contain compact stats/errors/times, not nested complete plans or raw
captures. The caller writes the selected physical plan/replay separately and
assesses durable60-second publication; an admission timestamp is not an ACK or
deployment proof. If the helper is never entered or final publication is late,
the previously available common fallback remains the caller's operational state.

## Why a thin loop rather than the existing top-level planner

`native_pathflow.solve_planner` already implements integrated-cost tangents,
fallback lifting, raw/completed candidate retention and start submission
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:709)).
But it has no caller builder argument for explicit native seed, arm upper-bound
mask or fixed active fleet. It also couples initial fallback with start use.
A reduced-case workaround would change identity and can reject a valid full-case
prior because it contains excluded movement modes. Do not rewrite plan identity
or enlarge K to evade that issue.

The new loop keeps the original full case and uses existing primitives:

- `pf.build_feasible_model` for original physics; set/read native seed per build.
- Only UB=0 outside the supplied arm's retained IDs; ordinary retained x stays
  free. Add the common-fleet equality. No pool relaxation or learned asset access.
- `pf.attach_objective(built,'tangents',cuts)` for integrated system cost.
- Original `pf._optimize_once`, followed by unchanged `pf._candidate` with the
  current completion policy and objective reconstruction checks.
- Independent `nr.replay_native` and exact Fraction operating plus
  `nh.supply(target_market, replay['load'])` before accepting a returned candidate.

Rebuild each round: existing completion fixes all routing bounds, so reusing that
mutated model would accidentally turn later routing rounds into fixed-route
solves. No physical matrix inventory framework or repeated raw variable capture
is added. Existing projection/decoding/topology diagnostics can stream to the
caller's sink. A sink failure stops further dispatch and is retained separately.

## Fallback and native start are different objects

The full-case fallback is independently replayed and repriced at the TARGET tariff
before search, without changing routes/charges. Tariffs alone do not alter its
physical feasibility. Retain it externally even if some selected modes are
outside the exact-K arm pool. Search candidates must satisfy the pool and fixed
fleet; the fallback need not belong to that search space.

The parent's strengthened CURRENT matched-study selector additionally protects
all common-prior flexible arcs in `Bw=B union prior_flexible`, inside UNCHANGED K,
and rejects a design that cannot fit. Thus every successful study pool contains
the known prior and is initially hint-eligible; there is no trivial known-plan-
loss confound or quota enlargement. Outside-pool fallback handling remains a
defensive generic API property, not the planned difference between study arms.

Only offer a hint when all its selected movement IDs fit the pool. Reuse
`pf._checked_pricing_start` and `_attach_pricing_start`, supplying binary values
only and leaving continuous values unset
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:424)).
Record `submitted` with solver acceptance UNKNOWN, or skipped/rejected with its
reason. Start rejection ends that search path but leaves the common fallback
intact. The best admitted pool-compatible candidate can become a subsequent
round's hint, independently of whether it beats the external fallback. This
avoids discarding a useful internal hint when the common cheaper fallback is
outside the pool. No new start-transport experiment is required or claimed.

The external keeper compares exact target costs and copies a cheaper independently
replayed candidate BEFORE subsequent logging or bound handling. Later native,
completion, diagnostic or bound failure does not erase an earlier admitted best.
Unreturned internal candidates are not credited. The caller similarly retains
the input fallback through scoring/worker failure, as its preexisting warm state.

## Objective, tangents and all native work

Optimize integrated system cost `c+a'L+.5*sum(bL²)`, not fleet count or uniform
marginal-price payment `c+a'L+sum(bL²)`. Every arm starts with the cut at load0
AND the tangent at the common fallback's replayed load, both under the target
coefficients: slope `a+bL0`, intercept `-.5*bL0²`. The common available prior load
is legitimate warm information. Record those points/cuts identically for all
arms. Add a cut at each admitted round candidate's load, with at most four new
primary solve/tangent rounds and no adaptive round increase.

With `completion=True`, `_candidate` first attempts a raw witness, then its
existing fixed-topology feasibility/objective completion (at most two additional
native calls) and retains its best admissible raw/completed candidate
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:552)).
Thus four rounds can involve up to12 native-call attempts; completion is not free.
A tiny single-thread serialized count-only scope wraps `pf._optimize_once` and
restores it in `finally`. It passes the original budget/deadline unchanged,
records dispatched/failed/blocked calls, actual elapsed/CPU, role, fixed-topology
flag and stats, and prohibits dispatch beyond the absolute52-second cutoff.
It bypasses no preinstalled hook and changes no native cap, physics or tolerance.
All completion calls are inside the same cutoff and charged by the parent.

No global lower bound/gap is emitted: `global_lower_bound=None` and no certificate
claim. Raw native bounds remain in call/round stats with fixed-fleet, pool or
fixed-topology scope. In particular a restricted lower bound can exceed the
external fallback cost when that fallback is outside the restricted model; this
is not an inconsistent physical witness or a bound for the union of choices.

## Fixed-route charging control and unchanged reference

`fixed_route=True` fixes every original routing binary to the common prior's
0/1 topology and adds the same active-fleet condition. The same target integrated
objective, two initial cuts, four-round cap, completion policy, clock, replay and
external keeper apply. This isolates charging adaptation on an unchanged route.
No route repair or additional charging oracle is invoked.

Do NOT use `route_fixed_repair._solve_fixed_charge` as the matched curved-cost
control: it minimizes only linear `market.a`, then evaluates curvature afterwards
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/route_fixed_repair.py:303)).
It is a valid separate linear diagnostic but answers a different objective.
The unchanged-plan reference uses the common prior's replayed target cost with
zero replanning, reporting acquisition cost separately. There is no cold-speedup,
price-information attribution, generalization or unrestricted certification claim.
