# Three-cover classical matching-pool pilot

25 October2026. Prospective static source/protocol. `RESOURCE_DECISION.md`
records the parent's new budget; no prior attempt is resumed. Parent reviews
these bytes and one static peer review, then freezes the exact command before
one execution. No tests, controller expansion or production-source edits.

```
.venv-local/bin/python research-20261025/matching_pool/run.py --root /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017 --output research-20261025/matching_pool/attempt01
```

## Question and immutable inputs

Can a coherent conventional candidate union improve global physical fleet
acquisition compared with an irreversible local greedy construction or an
unrestricted fleet-first solve? This is a small competence diagnostic, not a
matched learned-versus-classical study, new method, full GRASP implementation or
literature replication. Two exposed inspected development cases only:
`scale:50685:40`, `scale:50605:80`. Their lexicographic screen selection and exact
case identity/movement order are checked against `local-assets-v3.json`.
The old model files, chosen routes, result endpoints and raw logs are not read.
No model inference, training, cluster or sealed DEV/TEST/A6/B3/confirmation/GIRO.

## Candidate algorithm frozen before outcomes

`pool.py` uses the original declared direct/depot trip-pair modes. An eligible
pair must be chronological: following trip starts no earlier than prior trip
ends and advances the fixed `(start,end,id)` trip order. Never invent an edge.
Group parallel modes by `(before,after)` and derive two conventional proxies:
minimum total movement-leg minutes and maximum single-vehicle depot-window grid
kWh. The latter reuses `classical_controls._capacity_by_period` on validated case
inputs and original resource/market partitions. It ignores accumulated route SOC
and shared contention; it is not charging feasibility or an energy-price proxy.

Compute exactly three maximum-cardinality bipartite covers, with secondary costs:

1. Smallest pair movement minutes, affinely normalized to[0,1].
2. Largest pair depot capacity, cost `1-capacity/max_capacity` (all zero if none).
3. Seed17 deterministic pair hash, SHA256 of
   `matching-pool-v1|case_identity|17|before|after`, first64 bits divided by2^64.

Use `scipy.optimize.linear_sum_assignment` on an `N × 2N` matrix. Original trip
columns accept eligible pairs at real secondary cost[0,1]. N dummy columns cost
`D=N+1`; forbidden pairs cost `N*D+1`. All-unmatched is feasible at N*D, so a
forbidden pair cannot improve it. D exceeds the entire possible real-secondary
variation, giving maximum cardinality priority. Record SciPy/NumPy versions,
fixed trip order, selected pairs, cardinality and costs. Ties use the deterministic
ordered matrix and installed algorithm; this is not cross-version bitwise proof.

One outgoing/incoming matched pair per trip and chronology give disjoint
route-only paths. `N-matched_pairs` is a topological diagnostic only. Require
all three covers to agree on maximum cardinality. Take their union and retain
**every original direct/depot mode** for each selected pair, plus **every original
pullout/pullin mode**. This protects parallel charging alternatives; no fixed
cover is treated as the final schedule. No additional CA1 fill, random draws,
outcome-dependent arc additions, retries or post-failure pool expansion.
The pool is tariff-blind and charging-opportunity-aware, not price-responsive.

## One original-physics joint selection/charging solve

Build `native_pathflow.build_feasible_model(case,'GRB')` on the original full
case. Stream one physical matrix inventory, with original binary/continuous
mapping and row signatures, using the frozen fleet-first pattern. Then set only
excluded movement upper bounds to0; retain lower0 throughout and upper1 for
retained movements. Record all movement bounds before/after and assert these
invariants; no binary is fixed1. Physical row coefficients/parameters remain
unchanged. Check declared row/column dimensions remain unchanged after bounds
and objective assignment. This is a restricted allowed-arc model on a full
declared matrix, not a claim that the constructed matrix is smaller.

Use the same pure fleet objective as the previous full control:
`mip.xsum(x[j] for j,m in enumerate(case.movements) if m.kind=='pullout')`.
One native call, default solver seed unmodified/numeric default unknown,
budget threads1 and phase cap<=60seconds. Solver may recombine cover alternatives
and charge under all original SOC/resource constraints. Any native lower bound
is **pool-restricted fleet count**, never an unrestricted full-model bound.

Require admissible finite-incumbent native status and one thread. Save one
separate native capture; call unchanged `pf._extract` once, preserving its
roundoff/projection/serial-decoding checks. Independently call
`native_recharge.replay_native` on the original full case, require plan movement
IDs subset of the pool and count agreement with selected pullouts/native fleet
incumbent using existing `BOUND_GUARD`. Evaluate the exact integrated system cost
with Fraction operating cost plus `native_hull.supply(day_market,load)`.
This cost is evaluated after the solve, not minimized by the fleet objective.
No physical witness is inferred from a matching or from solver status alone.

## Budget, outcomes and preservation

New package360CPU/300wall seconds; one Python process/native thread, observed
peak RSS<=5GiB. Two120-second case clocks: preparation/pool/model/one inventory/
bounds through30, native deadline90 with at most60 native seconds, single
capture/extraction/replay/durable output through120. Shared imports and input/
source binding plus closure use remaining package headroom. CPU hard limit360,
alarm300, cooperative body345CPU/285wall retain15seconds closure. Persistent
stop latch prevents subsequent case dispatch. Parent owns external hard stop;
native time limits and Python alarms do not guarantee blocking-call preemption.

`attempt01` is exclusive-create. Master/case receipts start incomplete, and final
publication replaces only their own placeholders. Keep candidate-pool ledger,
physical inventory, movement-bounds ledger, one native capture, event stream and
plan/replay as separate artifacts, not nested duplicate capture histories.
Receipt-inclusive `accepted_within_offline120` requires independently checked,
durable physical witness and total case elapsed<=120. Preserve late/no-incumbent/
extraction/replay failures. Complete diagnostic/zero exit does not mean both cases
were feasible; neither a failed pool nor missing incumbent proves infeasibility.
The parent's prospective competence gate in `RESOURCE_DECISION.md` additionally
requires admitted fleet<=3 on40 trips and<=5 on80 trips before expansion. The
parent derives this separately from diagnostic completion; failure causes
diagnosis, not an adaptive pool change or resumed attempt.

Record route-only path counts, declared matrix dimensions, retained movement
counts, physical incumbent, pool-bound scope, total/stage CPU/wall/RSS, policies
and versions. Hash once in the metered process only consumed `run.py`, `pool.py`,
this protocol, `RESOURCE_DECISION.md`, case lock and actual imported project-source
closure. No repeated old asset audit or actual model/old-route reads. A separate
60CPU/90wall finalization provision permits one compact result summary and
lossless large-artifact archive; this driver does not perform that phase.

All outcomes are exposed synthetic-development evidence. Apparent differences
from old greedy/full/GNN outcomes are unmatched context, not paired improvement,
generalization, novelty or tariff-learning claims. Further experiments need
prospectively matched candidate budgets, paid construction/search/replay and
independent timetable groups. Failure is retained without automatic retuning.
