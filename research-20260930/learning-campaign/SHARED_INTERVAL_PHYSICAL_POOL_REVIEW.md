# Shared-interval 2016 physical pool review

Fresh physical replay verifies all 10 columns from the two new 2016 hull
receipts and all five archived cheapest-bill control columns. The best
new column costs **515.648054** (shared_interval_cost_learned, column
4). The archived control remains stronger at
**515.515556** (column 3).
Thus the report's historical physical incumbent is still the best
individual plan in these compared receipts.

At that incumbent's exact own-load gradient `a + b × load`, the best
linearized response among the 15 replayed plans is archived column
4 (plan `6dd94a8936cbee691c6eefac782664d2bbed5b3535d422be6c270aab7f36fe73`). The witnessed
regret is **0.724020** cost units:
the incumbent's linearized cost minus that response's. The exact
fraction, gradient prices, plan hashes, provenance and per-column costs
are in [the JSON review](SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.json).

The incumbent uses 4 buses and has true target cost
515.515556; the 4-bus price-taking
response has **higher** true target cost 516.505682.
At the incumbent's prices their energy bills are
137.638890 and
136.914870; adding operations cost gives
linearized costs 537.638890
and 536.914870.

The strongest fresh saved global lower certificate is
515.356816. The feasible incumbent
is within **0.158740** cost
units of the physical optimum under that certificate; the gap is open.

This is a lower bound on oracle regret **at the archived incumbent**
because the oracle could choose at least that replayed response. It does
not establish support failure of the unknown physical optimum; the
physical optimality gap remains open.

Reproduce with:

```sh
PYTHONPATH=src python3 research-20260930/learning-campaign/review_shared_interval_physical_pool.py --check
```
