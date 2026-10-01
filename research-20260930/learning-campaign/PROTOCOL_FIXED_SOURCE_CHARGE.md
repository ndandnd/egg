# Fixed-source-route charging response baseline

This eight-cell development control asks whether changing only charging
on an already feasible source fleet captures target-market gains without
a new route-cover MILP. It uses four previously observed development
timetables, 2016–2019, and each one's two archived *pre-target* best
source fleets. The 2016/2017 inputs come from frozen stage 2; 2018/2019
from the frozen independent-transfer attempt. No target cold or learned
final incumbent is an input to charging or selection. Reserved 2004/2005
and 2020/2021 test cases remain unmaterialized. The exclusive attempt is
`result/learning_repair/20260930-fixed-source-charge-attempt1`.

Each cell first independently replays the archived source plan and
records its exact curved target-market bill under its *original* charging
schedule. The selected physical movement set is then fixed completely.
The existing one-thread native GRB fixed-route charging/SOC subproblem
minimizes the **linear** target tariff `market.a`, with 45-second phase
and 55-second wall caps. A returned complete plan must pass a second
independent native physical replay and exact nonlinear target-bill
recalculation using both `market.a` and `market.b`. Solver status,
runtime, physical plan/hash, charge schedule, replay, and typed failures
are preserved. The LP is not a target quadratic optimizer; its curved
bill may be worse than the original source schedule, and no global fleet
bound or target optimality claim follows from an LP result.
If a worker fails before its direct-rescore receipt, selection recomputes
that exact bill from the pinned archived source plan and flags the missing
receipt. A fixed-charge plan written before a later worker failure is
admitted only after fresh source-topology, identity, hash, physical-replay,
and exact-cost checks; its failed or timed-out receipt stays attached and
its status remains provisional.

After both sources for a timetable have receipts, exact target cost
chooses the best of the two recharged plans, and separately the best of
all four original/recharged choices. The latter protects against a
linear-objective recharge increasing the curved bill. Two prespecified
single-LP controls select a source *before* seeing recharged outcomes:
the exact cheapest original target bill and the frozen learned source
proposal. Those controls pay only their selected LP, while the
best-of-two-recharged rule pays both LPs. Every method also reports
historical paid acquisition for both source fleets, direct rescoring,
selection, LP, and independent replay time separately. Archived cold,
retained, nearest, cheapest-bill, and learned native target outcomes are
read only as historical development comparators; their bounds are not
new certificates. There is no matched-runtime speedup claim across the
archived and new jobs.

The falsifiable comparison is whether the single-LP cheapest-direct or
frozen-learned source choice gives a replayed lower exact target cost
than its unchanged source schedule, and how much of the previous native
target improvement a route-fixed charge response can explain. Failures
stay typed and costed; a source's original replayed schedule remains a
valid direct-cost control when its charging LP has no incumbent. This
control precedes further CPU model training and is not a new training
or test-set evaluation.

Eight serial children have 100-second hard caps, below a 1,200-second
controller guard and 1,350-second external shell cap. Slurm requests
one CPU, 8 GB, 30 minutes, one native thread, no requeue, and excludes
`scaglione-compute-01`. The exact source frozen/catalog/summary, learned
proposal and inference receipts, per-source archived receipts, physical
and market identities, execution commit, source hashes, runtime/native
probe, cell order, and budgets are frozen before launch. One exclusive
controller lock and immutable per-cell receipts preserve interruption
evidence; an unreceipted partial cell halts automatic resume.

Pure local checks use archived replay and mocks only, with no local GRB:

```sh
PYTHONPATH=src python3 -m pytest -q src/tests/test_fixed_source_charge_campaign.py
bash -n src/cluster/fixed_source_charge.sbatch
```
