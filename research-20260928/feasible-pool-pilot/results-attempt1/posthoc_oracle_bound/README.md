# Re-evaluating a saved physical pricing bound

The matched pilot discards previous-market lower certificates. A separate
posthoc calculation shows that a saved **physical pricing bound**, evaluated
at its original price vector, can support a new-market lower bound. This is an
additional analysis of saved evidence; the pilot's outcomes and timings are
unchanged. No optimization was performed.

Let the unchanged physical feasible set be $\mathcal X$, operational cost
$c(x)$, and load $L(x)$. A saved pricing solve provides a numerical lower
bound $\underline\phi(p)$ for

$$
\phi(p)=\inf_{x\in\mathcal X}\{c(x)+p^\top L(x)\}.
$$

For a new convex supply cost $F_1$, Fenchel's inequality gives

$$
\inf_{(\bar c,\bar L)\in\operatorname{conv}\{(c(x),L(x)):x\in\mathcal X\}}
 \{\bar c+F_1(\bar L)\}
 \;\ge\;\underline\phi(p)-F_1^*(p).
$$

The physical pricing problem depends on the physical case and posted vector
$p$, so its bound remains applicable when only the supply cost changes.
The new conjugate must be evaluated; the old market's hull lower value cannot
simply be relabelled. For nonnegative loads and positive quadratic curvature,

$$
F_1^*(p)=\sum_t\frac{\max(p_t-a_{1,t},0)^2}{2b_t}.
$$

Both initial public solves reported solver status `OPTIMAL` at $p_t=0.20$
under the configured numerical tolerances.
For the shifted market, $a_{1,t}=0.18$ in its first 15 periods and 0.22 in
the last 15, with $b_t=1/900$. The new conjugate is approximately 2.70.
The diagnostic uses exact arithmetic on stored input numbers and outward
floating-point endpoints, retaining the native solver's tolerance qualification.

| Same physical case, shifted market | Recorded target lower | Re-evaluated lower | Recorded mixture upper | Recorded width | Posthoc width |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hildenbrand, depot 15 | 315.76 | 405.83 | 469.89 | 154.12 | 64.06 |
| Hildenbrand, depot 16 | 329.22 | 420.45 | 490.67 | 161.44 | 70.21 |

Displayed lower endpoints round down, upper endpoints and widths round up;
widths are computed before display rounding of the endpoints.
The original target uppers are replayed convex mixtures of fleet plans, not
single executable schedules. Both original target statuses remain
`budget_exhausted`. Re-evaluation neither closes their gaps nor establishes an
ideal-model exact optimum or a measured online acceleration.

The diagnostic verifies the unchanged attempt seal and source hashes, matches
each saved pricing lower to its original pricing-result event, checks physical,
oracle and extraction identities, and recomputes the target conjugate in two
ways. Luna independently reproduced the arithmetic and the scope of the
inequality. The elapsed diagnostic function time is recorded in
[`diagnostic.json`](diagnostic.json), separately from every pilot time; it
includes input reads and algebra, excludes imports/startup/output, and is not
a runtime benchmark.

A prospective baseline should retain both feasible plans and price-indexed
physical pricing bounds, with their provenance and preparation costs. It can
re-evaluate those bounds under the new supply cost while still requiring fresh
target-market pricing before certification. Physical changes, another timetable,
or an unverified oracle invalidate automatic reuse. The rational-polishing stop
also remains a separate numerical issue to address before a larger sweep.

Reproduce from the complete private archived attempt with:

```bash
python research-20260928/feasible-pool-pilot/cached_oracle_bound_diagnostic.py \
  --attempt /path/to/complete/feasible_pool_pilot/20260928-attempt1 \
  --out /new/output/diagnostic.json
```

The small public evidence subset excludes the full event logs. It contains the
original witnesses and saved certificates; this derived JSON also includes the
matching pricing statistics and original event-log hashes. Full original logs
remain preserved privately.
