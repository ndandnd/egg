# Energy-flow campaign: focused source integration review

29 October 2026. Read the new `worker.py`, `run.py`, draft `LAUNCH.json` and completed `PROTOCOL.md`, plus changed minimum-fleet logic in `energy_flow.py`/`exact_dual.py`. Prior `ENERGY_FLOW_SOURCE_REVIEW.md` supplies the broader formulation/checker review. No data/raw packets, imports, execution, tests, hashes, native solves or commits. Reviewer actual CPU is UNKNOWN.

## Decision: scoped PASS pending actual freeze and Q0

No launch-blocking scientific/source defect found in the reviewed integration. The control remains DRAFT/PENDING and correctly cannot execute until its actual source revision and FROZEN authority are recorded. This is not a qualification result or approval to bypass the frozen procedure.

One minimal authorized source repair was made: the worker's compact summary now preserves `optimize_called` and `inclusive_elapsed_s`. This exposes no-call native states without opening compressed detailed packets or interpreting native LOADED status as a completed solve. The parent acknowledged this change. No model, objective or certificate arithmetic changed.

## Source-bound transferred upper and prices

The four fixed input paths are checked against their declared revisions: case descriptor at253c1e29 and new candidate/replay/transfer authority together at929bd005. The worker does not follow paths supplied inside metadata. It requires the expected producer source ef0b0881, control6ed44942, case identity, field contract and strict-admission/closure flags. This is explicit reuse of a source-bound passed certificate, not a new independent provenance audit.

The protected upper is never substituted for a failed native method delivery. No duplicate physical replay of that already passed witness occurs. Its exact certified load determines a+b*load prices once. Both price states hold that vector fixed; the caller checks exported prices exactly before invoking the linear bound checker. This closes the linear-price authority caveat from the earlier source review. New integer candidates are independently replayed once, with failed admission retained and no adjustment/repair fallback.

## New minimum-fleet row

The builder's lower row is derived from mandatory service overlap or a one-bus chronological obstruction. Half-open intervals ensure services meeting at an endpoint are not falsely treated as overlapping. If all services are disjoint, a single bus must use links between consecutive services in chronological order; a missing link excludes one bus. If every such option is direct, no intermediate recharge is available, so service energy alone exceeding B−reserve also excludes one bus under nonnegative movement consumption.

The exact checker independently derives the same floor using an event sweep and graph/service data, checks its proof metadata and reconstructs the row. It does not import the builder. The row is valid for every physical fleet and therefore for its hull; it is not an upper-cardinality restriction imported from the separate physical optimum2 result. Every allowed larger fleet remains in the relaxation and price-response problems.

For a one-service case, the direct-only predicate is vacuous, but source validation bounds that service's energy by B−reserve, so it cannot accidentally trigger the energy obstruction. Overlap counts already handle simultaneous services. I found no counterexample to the changed floor logic under the validated DAG/no-unlisted-charging assumptions.

## Q0 hand check and fail-closed controls

The literal has two15kWh services and a direct A→B link without charging. One bus cannot supply30kWh from usable20, so the independently derived floor2 is justified. Two buses can each recharge15kWh: A's bus charges15 before the first market boundary, B's bus charges15 afterward; one40kW connector accommodates both. Thus load(15,15), operations14 attains the convex quadratic lower of equal hourly loads. The known value14+30*a+225*b is correct, with a,b exact binary-stored rationals; display20.25 is ancillary.

Q0 requires native OPTIMAL plus objective agreement and an independently semantically validated exact lower within1e−7 from below. The minimum-fleet metadata must report2. Changed RHS, finite variable bound, fleet proof metadata and objective must each reject. Failure prevents every public stage. This is an appropriate bounded runtime gate; its outcome is PENDING, not supplied by the hand proof or source review.

## Execution scope, timing and closure

The five immutable states and allowances in code agree with the protocol: Q0, ROOT_QP, MIQP, PRICE_LP, PRICE_MIP. No OA retry, extra case, learned component or automatic follow-on call appears. Cached scientific modules match the declared closure; installed gurobipy12.0.1 is the only native package. The initializer has no import expansion. Source/bootstrap trust and actual revision admission remain prospective.

Funding checks reserve120CPU/180wall beyond each full next allowance. Worker hardCPU1700 and wall2200 sit inside the1800CPU/2400wall package, with owner cleanup boundaries and single native thread. Complete gzip serialization is included in stage timing; compact status writing/event/garbage collection and final publication remain part of package accounting. Stage DELIVERED is administrative, not exact feasibility or optimality. A LATE state is retained and prevents CLOSED success even if later funded stages continue.

Worker exceptions retain active FAILED and unattempted rows; owner missing/unreadable-result handling preserves a five-state administrative ledger, validates statuses and requires a valid CLOSED master for success. Timeout kills/reaps the owned worker group; unresolved closure is explicitly marked. Native no-call raw status may remain LOADED in detailed packets, but `optimize_called=False` is now visible in compact summaries. Exact checker Pi absence returns UNAVAILABLE, not a fabricated certificate.

## Claim boundary

An accepted exact residual certificate can bound CH and D for the independently reconstructed intended model even when the native matrix was rounded. It need not be strong enough to improve the previous lower bound. A new strict physical candidate can improve the upper; native OPTIMAL, MIP gap or packet delivery alone cannot do so. Neither a relaxation lower nor a physical upper by itself settles strict D>CH. The protocol correctly preserves these distinctions and requires a new frozen scope for any later construction or branch certificate.
