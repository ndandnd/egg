# Independent certified-price integration review

Scoped source PASS on mathematical/API integration after the owner repair below, with one small worker failure-evidence ordering adjustment requested from the parent before freeze. Read only new worker/run/protocol/draft control; existing frozen flow/checker/verifier interfaces were already reviewed. No actual gzip, input data, imports, execution, hashes, tests, native calls or commits.

## Transfer and exact algebra

Fixed-path packet source `0cb3…`, independent transfer authority `3cbb…`, original case `253c…` and computational callbacks `3278…` agree across source and protocol. Producer source/control, case identity, packet paths/pointers, one replay, all strict flags, candidate field contract and exact primal/dual/checker value equality are required. Authority paths are compared, not followed. The transferred incumbent is explicitly not a newly delivered response candidate; no old replay/recovery is called.

Exact loads/ops/objective and prices are cross-checked against the producer replay and original binary coefficients. `p=a+b*e`, physical objective `c+a.e+sum b*e²/2`, private score `c+p.e` and `F*(p)=sum (p-a)²/(2b)` give the correct Fenchel identity, including zero-load coordinates. The fixed quadratic has strictly positive b. Q0's `(0,2),c=1` known value, three altered-gradient/cost/sign controls and equal/loose/contradictory bound comparisons exercise the stated algebra without a repeated native probe.

## Response and scientific gates

Exactly one cold full-graph continuous linear LP (60 native/build seconds) and one full-graph integer linear MIP (180 seconds) use the identical exact transferred vector. Both use the original graph and admitted fleet range, with the independently valid minimum-fleet cut; no two-bus-only restriction or old nonlinear higher-fleet exclusion is introduced. Only the MIP gets a binary movement start, whose acceptance remains unknown.

The LP checker reconstructs the intended rational objective and requires `V_lower==lower_bound`. A lower equal to the admitted private score proves zero global own-price regret and hence support/global physical-hull equality under the established framework. A lower below it gives a regret upper, not support failure; a larger lower is a preserved fatal contradiction. Native OPTIMAL/status/gap never substitutes for that test.

A fresh MIP candidate is independently screened once and must pass all strict physical/upper flags before its exact private score supplies a regret lower. A failed screen is not repaired or replaced with the external incumbent. A strict score below the LP lower is a fatal contradiction. Even a positive incumbent regret would concern the transferred plan, not every physical planner optimum. Bound/screen results remain method-specific.

## Accounting and preservation

Cached byte admission and one consumed-buffer hash occur inside the owner-funded worker; callbacks execute their admitted buffers. There are no duplicate source entries or extra numerical export/replay passes. Complete stage clocks cover build, native solve, exact check/screen and gzip serialization. CPU/wall funding reserves, one thread, observed RSS, outer process-group cleanup/reaping and all three assigned identities are present. Late stages prevent successful owner exit; incomplete/fatal states retain their denominator. Nested resource observations precede final receipt serialization, so the complete external meter remains authoritative and observations overlap.

Minimal `run.py` repair now validates row terminal statuses, Boolean resource/timeliness flags and consistency of `all_assigned_timely` with the row ledger inside malformed-master handling. Previously missing fields could abort after the guard and before durable receipt. Parent was notified; no helper was edited.

One evidence-preservation adjustment is pending parent integration: construct the native packet and reset `packet_published=False` **before** testing exported price equality. Otherwise a price mismatch occurs before the existing failed-packet handler has the native result to preserve. Mathematical rejection is already correct; this changes only preservation of the diagnostic. Parent is reviewing/editing worker in parallel, so no competing worker edit was made here.

Subject to that ordering adjustment, no remaining integration blocker found. Source/control freeze and actual complete external closure remain required; this review establishes no numerical support result.

## Pre-freeze resolution

Parent reports the requested exact preservation move was applied: native packet construction and `packet_published=False` now precede the exported-price comparison, with no other worker mutation. This resolves the outstanding evidence-ordering item. Integration verdict is scoped PASS; no runtime result was inferred by this source-only acknowledgement.
