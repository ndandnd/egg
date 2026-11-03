# Two-witness economic coherence — prospective 25 October 2026

Question: among two existing full schedules for the same FIT timetable, does
each teacher's own source context prefer its chosen witness? The completed
support audit found48 differing and31 identical connection-target pairs, with
equal fleet counts. This package tests restricted-catalog consistency before
further fitting. It neither repairs labels nor rescues the negative warm gate.

## Exact data, routing and cohort boundary

Consume only the completed selected metadata receipt
`research-20261025/train_readiness/attempt01/receipt.json`, the completed target
receipt `research-20261025/fit_target_support/attempt01/receipt.json`, and:

- `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl`,
  byte SHA256 `faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6`;
- `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl`,
  byte SHA256 `7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5`.

Parent explicitly authorizes full mixed TRAIN byte hashing and transient JSON
decoding for routing, as in the completed audit. On a non-FIT row consult only
top-level group/base routing identity, then discard it without semantic
inspection, retention, export or comparisons. This is not FIT-only byte access
or identifier-only parsing. No non-FIT label analysis, historical model outer
performance, sealed bank, other outcome/shard table or referenced path access.

Reconcile the same80 FIT groups,79 expected complete pairs,159 expected witnesses
and one incomplete group10037/source1 only. Keep all79 pairs, including all31
identical-membership pairs. Consume the old48/31 strata unchanged; do not select
only interesting routes or costs. No replacement, new teacher or automatic retry.

FIT case/source identity fields remain those in the completed target contract.
The new plan semantic allowance is EXACTLY what the unchanged physical replay
consumes, enumerated in REPLAY_SOURCE_CONTRACT.md: schema/case identity; vehicle
ID/trip/movement paths; charges with vehicle, movement, connector, start_min,
end_min and grid_kwh; and mandatory stored load/ops_cost consistency assertions.
The complete unmodified FIT source_plan is canonically hashed, then passed to
replay. Do not semantically inspect cached raw-solver/roundoff/nested replay
fields or the separate source_replay. No raw plans, sessions, load vectors or
SOC trajectories are exported. Other fields do not become data-discovery leads.

## Unchanged physical admission and source closure

Reconstruct dataclasses from the stored physical case, preserving values/order
and original defaults; do not regenerate cases or witnesses. Bind canonical
case, source-market and complete-plan identities. Use unchanged
`nr.replay_native(case, original_plan)` without prices, projection, clipping,
repair, completion solve or edits to stored assertions. Keep original physical
checks, TIME_TOL_MIN1e-7 minutes and ENERGY_TOL1e-6, including the source's use
of ENERGY_TOL for ops-cost consistency. Do not broaden those tolerances.

On success use replay's RECOMPUTED load and ops_cost. Never value cached load,
cached source_replay or stored objective. Record rejected witnesses/pairs with
their original identity and safe error category, no fabricated cost. An invalid
witness is not proof of infeasibility or of a particular teacher failure cause.
The incomplete group may be replayed for bookkeeping but has no paired endpoint.

The minimal pure project source closure is `src/egglab/__init__.py`,
`native_recharge.py`, `native_hull.py` and `physical_learning_cases.py`. These
provide only stored dataclass construction, identities, replay, source-market
mapping/validation and supply valuation. Bind their bytes once inside the actual
metered input batch, in addition to driver/protocol/launch and prior receipts.
No training loader, generation, solver/compiler/decoder path, QP, NumPy, sklearn,
python-mip or Gurobi is entered. Confirm imported module paths are the selected
worktree sources; no monitoring or generic parser/controller framework.

## Four valuations and exact represented arithmetic

Construct both source markets on the stored case and call `nh.validate_market`
before `nh.supply`. At tariff t and fixed witness j:

`F_t(P_j) = nh.rational(replay_j['ops_cost']) + nh.supply(market_t, replay_j['load'])`.

Both terms use the existing native-hull rational conversion policy, including
Fraction.from_float for finite represented numeric inputs. Preserve Fraction
totals without a float downcast; preserve original float expressions in the
source-market identity. This is exact arithmetic on represented replay numbers,
not an exact real-physics, integer-optimality or global regret certificate.

Set `D_t=F_t(P1)-F_t(P0)`; positive favorsP0. Prospectively classify signs using
tau=Fraction(1,1000000) generator COST units: positive above tau, negative below
-tau, otherwise a numerical tie. Keep exact differences inside the band. This
is separate from physical replay tolerances and is not a useful-effect gate.
Report all nine sign combinations, including own-context strict reversal(+,-),
opposite reversal(-,+), uniform preferences and one/two-sided ties. Flag own0
dominated whenD0<-tau and own1 whenD1>tau, allowing overlap. Raw gaps
R0=max(0,-D0), R1=max(0,D1) are not tau-excesses; a tiny positive raw gap can
coexist with a numerical tie. No automatic relabeling/promotion follows.

Report fleet count, vehicle cost, travel deadhead minutes/cost and grid energy;
at each tariff report linear/quadratic/total electricity and total system cost.
Keep replay's sequential ops scalar common across both markets; derive components
from validated paths with the same rational conversions and expose any residual
instead of forcing arithmetic equality or adding a new physical rejection rule.
Linear+quadratic must represent the unchanged supply expression, not atomic
uniform-price payments. Absolute generator units are primary.

Optional Ebar is one quarter of the four electricity valuations, only finite
strictly positive denominators allowed. It is not warm priorE0 or comparator
total bill. Individual normalized ratios can be exact; normalized aggregate
display summaries may use explicitly labeled finite-float conversion/rounding
to avoid enormous denominators. Raw costs/differences/gaps remain exact under
the source conversion. No arbitrary epsilon floor or numerical tie retuning.

## Denominators, output and limitations

Publish all80 statuses and79 expected pair endpoints, every failed replay,
missing/invalid witness and the source1-only comparison absence. Only physically
admitted witnesses contribute costs; never substitute a raw solver/cached value.
Display actual valid denominators and all failures. Available-pair descriptive
summaries do not become complete-cohort support or a positive learning gate.
Full result is primary; existing48changed/31identical strata may be descriptive.
Keep equal-group summaries, not independent edges, four valuations or sources.

Repricing fixed whole witnesses mixes route and charging differences. It is NOT
optimized fixed-route QP, a learned-information experiment, teacher-noise causal
identification or a new theorem. Own-context domination means weakness relative
to another observed feasible witness only; no full-space gap/optimality claim.
Successful replay/catalog consistency does not establish historical GNN lineage,
teacher comparability, population transfer or permission for more model families.

## Once-only resource and receipt contract

Total300CPU/600wall seconds, body270CPU/540wall and30CPU/60wall closure provision,
inclusive of startup/imports, admission, replays, valuation, reporting and exit.
One process/thread, observed peak RSS<=5GiB; no instantaneous memory guarantee.
JSONL cap512MiB each/16MiB per line; receipts/source identity files8MiB each.
Hash each original file once during the same filtering/read batch; canonical
case/market/plan hashes are separate identity checks, not duplicate file audits.

Fresh exclusive attempt01 owns its placeholder/final success/failure receipt.
Freeze reviewed source/API/field/input/command/namespace in LAUNCH.json before
dispatch; this protocol alone is not a launch manifest. No test matrix, source
edits while running, automatic retry or experiment expansion after a failure.
Human practical routine authority exists; no budget question is pending.

Carry displayed process sums19638.65CPU/20224.73elapsed-sum and retained tracking
19638.69CPU separately. Legacy conditional guard2546.091499549272/actual old review
CPU UNKNOWN remain separate; no reset/refund/exact sessionCPU or restored
historical compliance claim. No cluster or sealed-data permission follows.
