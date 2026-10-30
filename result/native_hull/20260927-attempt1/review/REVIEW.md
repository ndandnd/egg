# Independent audit of the failed first native hull qualification

27 September 2026. **The audit reconstructs the evidence successfully; the
scientific qualification remains FAILED: two certified cells, four master-cap
failures and two blocked retained dependencies.** Nothing here reclassifies an
exhausted state, loosens its stopping criterion or resumes the original attempt.
No author implementation was imported and no native optimizer was executed.

## Immutable evidence and independent coverage

Executed source: `f549100587cdf561c978e145e73e86dbadc9f27e`.
Original manifest SHA-256:
`1326245d395c01226d44543e6479799a997fa523e9a4d3fe84272a1cc37a73de`.
All **62 raw files / 9,912,912 bytes** matched their original hashes and sizes
before and after auditing; the original raw manifest remains unchanged. The
seven dependency/source hashes matched the frozen Git commit. All eight inputs,
case/market/state identities, declared dependencies and budgets matched their
frozen records. The supervisor exited 1 after 14.2354 seconds without an outer
timeout; all independent cells and both blocked successor cells have receipts.

The standard-library auditor imports only two colocated independent audit
helpers, copied unchanged from the earlier CBC V2 audit. Those helpers are not
the author's native implementation. The reviewer independently reconstructed:

- All 14 native complete-fleet pricing calls and their exact fixture-specific
  global minima, 532 raw native variable values, correction ledgers, objective
  accounting and physical witnesses: 30 sessions and 114 SOC events.
- All 266 master calls, 2,654 raw LP variable values, mappings, current pool
  order, simplex links, epigraph rows, tangent histories and raw objective
  values. Every executed master has one or two columns; exact enumeration of
  all affine-envelope breakpoints therefore gives its complete global PWL LP
  minimum without invoking any optimizer.
- All exact simplex corrections, aggregate supply objectives, serialized
  gradient prices, restricted-pool gaps, native-lower Fenchel calculations,
  selected final bounds, loop/cap accounting, preserved failures and retained
  predecessor blocks. All 280 native calls returned OPTIMAL; pricing/master
  status names and backend receipts were retained, not inferred from targets.
- Eighteen deliberate corruptions of in-memory evidence copies were rejected.
  They cover statuses, blocked call counts, missing returns, raw weights,
  mappings, LP bounds, backend identity, tangent coefficients/history, exact
  simplex weights, mixture cost, pool gap, conjugate and global lower arithmetic,
  column cost, physical SOC, cumulative counts and final interval corruption.

Raw runtime receipts identify CBC (`SolverCbc`, `mip.cbc`), one thread and the
fixed phase cap. The reported CBC library fingerprint is checked against this
attempt's known binary identity; this is not a new inspection of a remote or
reinstalled solver. The audit uses no wall-time result to claim a performance
advantage.

## Preserved outcomes

Intervals below are rounded displays of the source's saved, reconstructed
bounds. Exact rational values are in `audit-result.json`.

| Cells | Original outcome | Master / pricing calls | Saved interval |
|---|---|---:|---|
| Nominal cold state 0 | Master cap exhausted | 64 / 2 | `[76.99999899999997, 104.00000000000003]` |
| Nominal cold state 1, tariff 4.2 | Certified | 6 / 3 | `[96.18749899999997, 96.18750000000003]` |
| Nominal cold state 2 | Master cap exhausted | 64 / 2 | `[76.99999899999997, 104.00000000000003]` |
| Nominal retained state 0 | Master cap exhausted | 64 / 2 | `[76.99999899999997, 104.00000000000003]` |
| Nominal retained states 1 and 2 | Blocked by failed predecessor | 0 / 0 each | No bound claimed |
| Joint reserve/loss case | Master cap exhausted | 64 / 2 | `[86.0138494155125, 110.56509695290865]` |
| Fixed-capacity reserve case | Certified | 4 / 3 | `[98.99999899999999, 99.0]` |

The two certificates' exact stored-number widths are approximately
`1.0000000414400745e-6` and `9.999999930343506e-7`. The failed nominal intervals
have width `27.000001000000047`; the joint interval has width
`24.55124753739614`. A successful reconstruction of these wide intervals does
not make the corresponding algorithmic qualification successful.

## Complete analytical hull and pricing reference

The two mandatory sequential services each consume 15 battery kWh. At most two
used buses, zero-energy directed movements, full start/end SOC and the fixed
shared early/late windows leave two possible fleet structures: one bus covers
both services through its charging depot visit, or two buses cover one service
each. A direct one-bus join without early charging is infeasible here. Different
vehicle labels do not create a different load/cost projection.

Write `T=30/eta` and let `x` be early grid energy. For these fixtures, each
structure's complete projection is an interval with late grid energy `T-x`:

- Two buses: intrinsic cost 14 and lower endpoint `max(0,T-30)`.
- One bus: intrinsic cost 7 and lower endpoint
  `max(0,T-30,(30+reserve-battery)/eta)`.
- Both upper endpoints: `min(early_capacity,15/eta)`; empty intervals are
  infeasible. This common upper limit respects the A-service energy headroom.

One finite late connector can sequentially supply the necessary nonnegative
individual recharge amounts within its 30-kWh shared limit. Its capacity and
full recharge conditions are included before taking the hull. These branches
therefore give all physical projected points for the declared graph. Their
endpoints generate the entire hull. At fixed early energy, minimizing intrinsic
cost lies on a lower polygon edge supported by at most two endpoints; independent
exact pairwise quadratic minimization over all such endpoints is complete.

The analytical decimal-valued targets and aggregate loads reproduce:
nominal base `7591/80` at `(27/4,93/4)`, tilted `1539/16` at `(25/4,95/4)`,
joint `2987911/28880` at `(573/76,1827/76)`, and fixed reserve `99` at `(5,25)`.
The auditor separately evaluates the stored binary coefficients and compares
with those decimal analytical targets under a `1e-10` reference comparison.
This distinction is necessary because 0.2 and 0.95 are stored finite floats.

## Cause of the failed loops

The evidence supports a **repeated tangent-point plateau at native LP numerical
resolution**, rather than an exhausted pricing search or an invalid global
Fenchel formula.

In each of the three failed nominal states, the last **47** master solutions
have the same exact normalized mixture, with early load
`6.75018310538372`. Its true restricted-pool objective exceeds the exact
restricted-pool optimum by only `6.7055163093045646e-9`, but its first-order
restricted-pool certificate gap is `0.0004943979470712689`, above the fixed
`1e-6` gate. The source repeatedly appends the same point; the last master
contains 63 point entries but only 18 distinct points. A repeated row cannot
provide a new exact tangent constraint.

In the joint case, the last **15** masters repeat early load
`7.46845767378672`; true restricted-pool suboptimality is
`1.908874972111593e-8`, while the restricted-pool certificate gap remains
`0.0005599893611356335`. The last master has 63 point entries, 19 distinct.
Its current pool lacks the complete hull's necessary supporting boundary
column. Its near-optimal restricted value around 103.6271 consequently remains
above the complete hull value `2987911/28880`, approximately 103.4595222.
A further globally valid pricing call is still necessary; closeness to the
restricted objective does not prove the complete hull certificate.

Across all calls, the largest discrepancy between the saved native PWL
incumbent and the independently exact PWL LP minimum is
`7.450648125815301e-9`. The largest reconstructed raw master constraint residual
is `1.011401097300267e-8`: below the source's fixed `1e-6` reconstruction gate,
although slightly above the configured `1e-8` native feasibility setting.
Consequently, an OPTIMAL native return at the declared numerical resolution is
compatible with a repeated point whose true first-order pool gap is still too
large. The audit does not reinterpret OPTIMAL as exact arithmetic or blame a
mathematically invalid tangent. Every saved tangent weakening was independently
verified conservative on the relevant pool box.

## Improved upper bounds omitted from final summaries

The final summary updates its best mixture only when the inner master routine
returns successfully. An inner cap therefore leaves improved feasible mixtures
in `master_replay` records without retaining them as the final reported upper
bound. The best observed nominal mixture objective is
`94.88750000298026`, compared with saved final upper `104.00000000000003`.
The best observed joint mixture is `103.62710280497645`, compared with saved
final upper `110.56509695290865`. These are valid stored-projection diagnostic
upper bounds under the same physical witness policy; they were not the source's
reported result. This report preserves both facts rather than silently replacing
the historical final bounds or declaring convergence.

A prospective implementation can stream every replayed feasible upper bound
and add a separately specified, bounded feasible simplex improvement routine
before repeating a tangent. It must retain the declared actual-price pool-gap
and global native-pricing certificate tests. That change requires a new source
freeze/protocol and a separate attempt, not an increased cap or hidden retry of
this archive.

## Numerical and independence limits

Maximum raw pricing-model residual: `2.1316282072803006e-14` in mixed model
constraint units. Maximum combined physical charge correction:
`1.5661892642874546e-14` kWh, below the fixed fleet-wide `1e-8` budget.
No stored physical session is rationalized, rescheduled or altered. Exact
fractions concern stored projections, weights, coefficient arithmetic and
correction ledgers; physical replay remains conditional on the stated native
energy/time/correction tolerances. A stored mixture can differ by tiny amounts
from an exactly feasible ideal-physics point. These are numerical certificates
under that policy, not a claim that exact rational arithmetic repairs physical
feasibility or eliminates native global-bound assumptions.

The global pricing and complete-hull reference proofs are specific to these
small fixtures. The exact master solver-free audit is complete because every
executed pool has one or two columns. It does not provide a generic exact LP
solver for larger future pools or an operational performance claim. No retained
successor actually ran, so this attempt establishes no retained-pool benefit.

## Reproduction

From the repository root:

```sh
python3 -B result/native_hull/20260927-attempt1/review/audit_native_hull.py
```

The default report path is an exclusively created temporary file. From another
working directory, supply the repository and full immutable attempt explicitly:

```sh
python3 -B /path/to/repository/result/native_hull/20260927-attempt1/review/audit_native_hull.py --repository /path/to/repository --attempt /path/to/repository/result/native_hull/20260927-attempt1 --out /tmp/new-native-hull-audit.json
```

The frozen Git commit and all 62 raw files are required. Existing output files,
symlinks and output anywhere inside a detected Git repository are refused.
The original manifest excludes `review/`; the separate derived manifest covers
this auditor, its independent helpers and the final report without changing raw
evidence. Typical local solver-free audit time is approximately 13 seconds;
that number is audit overhead, not native algorithm performance.
