# Reusing physical pricing bounds across electricity markets

The matched pilot showed why retained plans alone are an incomplete baseline:
they improved public upper costs, while the new pricing lower bounds weakened.
A cached physical pricing bound can remain useful when the electricity supply
cost changes. This package implements that baseline separately from plan reuse.
It does not change the completed pilot or measure an online speedup.

For a fixed physical feasible set, operating cost and load mapping, write

$$
\phi(p)=\inf_{x\in X}\{c(x)+p^\top L(x)\}.
$$

A saved numerical lower bound $\underline\phi(p)$ gives a target-market bound
$\underline\phi(p)-F_{\mathrm{target}}^*(p)$. The posted price $p$ remains
exactly the original one, and the target conjugate is recomputed. The old
market's transformed hull lower must not be copied. Every accepted price-bound
pair can contribute; the best pair can change with the supply cost.

The earlier [saved-evidence calculation](../feasible-pool-pilot/results-attempt1/posthoc_oracle_bound/README.md)
gave target lower bounds near 405.83 and 420.46 and remaining gaps near 64.05
and 70.21. Those remain posthoc observations, outside the timed pilot.

## Interface and evidence boundary

The opt-in coordinator interface uses `bound_cache_policy="physical_pricing"`,
`cached_from` and `expected_cached_state`; the compact-pricing wrapper exposes
the same controls. This first interface accepts the immediately preceding
state as its source. Cache import is independent of retained physical-column
import. Default behavior and the frozen legacy arms remain unchanged.

An enabled source retains compact evidence for every valid physical pricing
call: original price and numerical lower, physical/oracle/extraction identity,
source state and market, native numerical provenance, and a digest of the
record. These are the source state's own successful pricing calls. A target checks these identities and records each recomputed bound's
lineage. An explicitly supplied incompatible or corrupted cache fails closed.
The digest checks record integrity and consistency; it does not independently
prove a native optimizer's lower bound. Solver tolerance qualifications remain.
A future experiment runner must also pin the source file, original on-time
receipt and source code, rather than relying on a self-reported digest alone.

Certification still requires a successful fresh physical pricing call in the
target state, a replayed feasible target mixture and the usual numerical gap
criterion. A cached lower can improve a bounded result even when fresh pricing
cannot complete, but cannot on its own establish certification. The original
posted cache price is not represented as the target mixture's marginal price.

## Accounting and next experiment

Validation and target-conjugate evaluation belong inside the target's measured
wall budget. Source coordinator time and native pricing time remain visible;
full child startup, data preparation and receipt-checking costs are not assumed
to be zero when unknown. Source costs must be paid once, with explicit lineage
to prevent double-counting shared preparation in a later paired comparison.

This code package uses focused tests and an independent change review. It does
not launch a cluster job, broaden the timetable set or train a predictor. After
this baseline is checked, address the separately identified rational-polishing
limit with the numerical restricted-master proposal. A new frozen comparison
must include the unchanged reserve-cold and feasible-plan baselines, cache
policies, complete paired timing, failures, and a common quality target where
attainable. All existing cases remain development data. Broader timetable and
retrieval/learning comparisons follow these stronger baselines.

## Validation status

The focused cache and existing feasible-reuse suite passed 26 tests without
native optimization. An independent [change review](../agent-notes/pricing-bound-cache/REVIEW.md)
found no remaining mathematical or admission blocker. Invalid cache exceptions
must be preserved by the later runner's failure receipts. Full CI is pending
the implementation backup; native performance validation is a later experiment.
