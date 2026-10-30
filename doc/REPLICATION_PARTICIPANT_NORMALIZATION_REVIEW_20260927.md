# Independent review: participant normalization in the cyclic replication

27 September 2026. Bounded exact-arithmetic review of
`REPLICATION_PARTICIPANT_NORMALIZATION_20260927.md`. No optimizer was run and
no experiment, source, or manuscript file was changed.

## Verdict

**PASS for the stated synthetic institution and price-taking definition.** The
reserved-connector interpretation supports the full individual opportunity
set used in the derivation. Exact Fraction checks reproduce the individual
regret bound and the equality between its sum and the archived whole-fleet
regret on all 88 physical-optimum records at the 86 archived sizes. Both
planner ties at n=20 and n=60 are preserved and reconcile exactly.

This result is specific to one A/B service pair per participant with its own
reserved early and terminal connector rights. It must not be generalized to
firms competing for an unreserved shared charger or to participants able to
trade, pool, or lose those rights.

## Exact archived-record check

The immutable replication output is
`result/cyclic_replication/20260927-attempt1/results.json`, SHA-256
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`. The
independent audit output is
`result/cyclic_replication/20260927-attempt1/review/audit-result.json`, SHA-256
`3c12d292d07893d5e247a3dc48c9a0d957bc97a5a56837bf3f0164d38dfc362c`. The
audit reports PASS, 86 sizes, and 88 physical optima including both ties; its
`raw_result_sha256` matches the archived result.

I separately parsed the stored rational strings with Python `Fraction`,
without importing the author experiment or invoking an optimizer. For all 88
optimizer records I verified:

- the archived price is exactly `(4+2m/n, 6−2m/n)`, the archived early load
  is `10m`, and the archived `delta` is exactly `m−27n/40`;
- `m/n≥1/2`, so `p_E−p_T=4m/n−2≥0`;
- the participant's one-bus and continuous two-bus price-response values
  differ by exactly `40m/n−27=40delta/n`;
- each currently assigned participant's regret is at most `20/n`; and
- summing those individual regrets over the m one-bus and n−m two-bus owners
  equals the archived whole-fleet own-price regret exactly.

The independent audit's per-optimizer regret records also match all 88
author-result regrets. The two recorded planner ties are the only ties in this
finite grid:

| n | Optimal m | Assigned participants with positive regret | Individual regret | Sum / archived whole-fleet regret |
|---:|---:|---:|---:|---:|
| 20 | 13 | 7 two-bus participants | 1 | 7 |
| 20 | 14 | 14 one-bus participants | 1 | 14 |
| 60 | 40 | 20 two-bus participants | 1/3 | 20/3 |
| 60 | 41 | 41 one-bus participants | 1/3 | 41/3 |

At n=2, the only optimum has m=1 and `m/n=1/2`, giving `p_E=p_T`. The two-bus
participant is indifferent across its continuous early-charge interval but
still prefers switching to the one-bus schedule by 7; its regret is 7, below
the bound `20/n=10`. At delta=0 (n divisible by 40), the one- and two-bus
private values coincide, so every assigned participant has zero regret.

## Complete pair-level opportunity set and connector rights

For one participant, the mandatory pair is one A service in [0,1] and one B
service in [2,3], each consuming 15 kWh. A used bus must cover at least one
service. The complete service-cover choices are therefore one bus for A then
B, or two buses with one service on each; a third bus would be unused and is
excluded. Each participant has an explicitly reserved 10 kW early connector
for [1,2] and a separate 30 kW terminal connector for [3,4]. These are private
rights, so the participant does not rely on another operator leaving charger
capacity available.

The one-bus path has the SOC trace `20 → 5 → 15 → 0 → 20`: service A consumes
15 kWh, the early connector supplies exactly 10 kWh, service B consumes 15
kWh, and the terminal connector supplies 20 kWh. The bus costs 7. The early
and terminal sessions fit within their reserved connector limits.

With two buses, let x be the early charge to the A-only bus. Its trace is
`20 → 5 → 5+x → 20`; the B-only bus follows `20 → 5 → 20`. The complete range is
`0≤x≤10`: the early connector bounds x above, and each state stays within
[0,20]. At the terminal connector, charge the A bus by `15−x` and the B bus by
15, sequentially at 30 kW. Their total terminal energy is `30−x≤30` kWh, so
the two sessions fit in the one-hour terminal window. The two-bus structure
has intrinsic cost 14 in total (cost units). Both structures consume 30 kWh and return every used bus to its
starting 20 kWh inventory. This establishes the full continuous two-bus
branch, not merely its x=0 endpoint.

At posted prices, the one-bus value is

`v_1 = 7 + 10 p_E + 20 p_T`.

For the complete two-bus branch, the value is

`v_2(x) = 14 + x p_E + (30−x) p_T`, for `x∈[0,10]`.

When `p_E≥p_T`, its minimum is at x=0; when prices are equal every x in the
interval is a minimizer. In either case the minimum value is
`14+30p_T`. Therefore

`v_1−min_x v_2(x) = −7+10(p_E−p_T) = 40m/n−27 = 40delta/n`.

The sign gives the current-plan regret: if delta is positive, an owner assigned
one bus regrets `40delta/n` and a two-bus owner regrets zero; if delta is
negative, a two-bus owner regrets `−40delta/n` and a one-bus owner regrets
zero. At delta zero both structures are best responses. Since every physical
optimizer has `|delta|≤1/2`, each participant's regret is at most `20/n`.
This is a per-participant bound, not a per-bus bound.

The reserved rights also make all of these deviations jointly feasible: every
operator keeps its own early and terminal plug, and the facility is provisioned
with n connectors of each type. Price-taking holds the posted price fixed
during deviations; this is not a strategic calculation that reprices supply
after a large aggregate deviation.

## Why the regret sum matches, and why convexification is not contradicted

Let `r=40delta/n`. The price-response value is separable across owners at the
fixed posted price, and their independently selected best responses fit their
reserved connectors. Thus the total of realized participant regrets is

`m max(0,r) + (n−m) max(0,−r)`.

For positive delta this equals `m·40delta/n`; for negative delta it equals
`(n−m)·40(−delta)/n`; for zero delta it is zero. These are exactly the
whole-fleet own-price regret cases stored in the archived physical optimizer
records. The equality follows from this matched partition, separable private
costs, common fixed price, and reserved connector rights. It is not an identity
for arbitrary participant partitions or shared-resource games.

The equality does not refute large-market convexification. It shows a
normalization distinction: along `n=40k+1`, there are `m=(27n+13)/40`
one-bus owners, each with regret `13/n`; their sum is
`351/40+169/(40n)`, which approaches 8.775 even as every individual's regret
vanishes. Meanwhile the physical-versus-hull planning gap remains at most
`5/n` and vanishes. In the original interpretation, one price-taking operator
owns a service set whose size grows with n, so its nonconvex opportunity set
also grows. In the alternative interpretation, that set is split into n
bounded pair-level opportunity sets. Neither calculation implies a generic
convergence theorem for real independently owned fleets, and the whole-fleet
regret sum is not itself a convexification-gap claim.

The derivation's all-n price-sign statement also checks out. The audited
physical minima have m a nearest integer to `27n/40`: for n≥3, the nearest
integer is at least `27n/40−1/2 ≥ n/2`; n=1 has m=1 and n=2 has m=1 by direct
branch comparison: for n=1 the m=0,1 branch costs are 99,97, and for n=2 the
m=0,1,2 branch costs are 198,191,194. At n≡20 (mod 40), both nearest integers
are retained; the archive includes both in-range instances n=20 and n=60.

## Minor clarity recommendation

No formula correction is needed. For a stand-alone reader, the participant
normalization note would be even clearer if it included the pair-level SOC and
sequential terminal-connector construction above. That proof is already
consistent with the audited physical templates, and this suggestion does not
alter the archived experiment or the scope of its result.
