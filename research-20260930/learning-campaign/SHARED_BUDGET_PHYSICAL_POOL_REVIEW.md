# Shared-budget 2017 physical pool and target bounds

Fresh replay of 21 saved columns finds a new five-bus physical plan
at **685.695043** (cost-only hull, pricing call
0). It improves the best archived target-control
plan (685.788696) by
**0.093654** cost units. Both new
candidate plans also independently replay; this best plan is a later
saved hull column.

The strongest fresh target-market global lower certificate is
**597.829694**, improving the strongest archived target
lower by 11.915836. The best replayed
physical plan is within 87.865349
cost units of the physical optimum under that certificate, so the
optimality gap is still wide. Source-market lower certificates were
excluded from this target-market bound comparison.

At this new incumbent's exact own-load gradient, the best response
among the 21 replayed plans is retained column
4, witnessing regret of at least
**5.092135** cost units at this
specific incumbent. Its true target cost is
685.788696; the price-taking comparison does not
establish support failure of the unknown physical optimum.

The [JSON review](SHARED_BUDGET_PHYSICAL_POOL_REVIEW.json) gives exact
fractions, plan hashes, source provenance, gradient prices and every
replayed cost. Reproduce with:

```sh
PYTHONPATH=src python3 research-20260930/learning-campaign/review_shared_budget_pool.py --check
```
