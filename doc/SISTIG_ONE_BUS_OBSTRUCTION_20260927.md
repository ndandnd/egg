# Post-pilot proof: one bus is infeasible in both declared public graphs

27 September 2026. This is a separately dated **post-pilot structural analysis**
of the two complete 37-service scenarios frozen at
`282e00b80b6fd9457006429b089269b2a9e2be92`. It does not amend the original native
solver bounds, statuses, selected schedules, protocol or raw results. No native
optimizer, matching solver or experiment-author module was imported or called.

**Result:** a single bus cannot serve all 37 mandatory services in either
single-depot scenario under the declared graph and battery policy. The proof
uses chronological order and a no-recharge energy obstruction. This is an exact lower bound of two buses for the ideal stored-input graphs.
Together with the independently replayed two-bus witnesses, it supports a
minimum cardinality of two **under the declared numerical feasibility policy
for these two modeled graphs**; the upper witnesses are not exact rational
physical certificates.
It does not establish minimum operating/electricity cost, reproduce the source
publisher's problem, or describe an unrestricted real bus network.

## Forced chronological route and absent recharge opportunities

All mandatory services have positive duration, and sorting them by departure
puts each preceding service's arrival no later than the next departure. Every
interservice movement respects that time direction. Therefore a one-path cover
of all mandatory services must visit them in this unique chronological order.
The 666 direct modes include jumps over services, but a one-bus mandatory cover
cannot use such a jump and later return to the skipped earlier service.

There are 36 forced consecutive transitions. An exact scan of each full frozen
graph finds **exactly one available movement at every such transition, and it
is direct**. Neither depot variant has any declared depot movement between two
chronologically adjacent mandatory services. Thus there is no eligible native
charging visit between the first service at 06:07 and the last arrival at 24:24.
This statement inspects all potential consecutive modes, not just the modes
chosen by a saved solver witness.

Initial battery inventory is at most 400 kWh and reserve is zero. Pre-service
charging cannot increase an already full battery beyond capacity. Terminal
recharge occurs after the final mandatory service and cannot cure an earlier
negative inventory. Only declared depot/terminal visits admit charging in this
model; no implicit off-depot stop or access to the other source-flagged depot
may be inserted into a direct mode.

## Exact energy obstruction

Using rational arithmetic on the stored input energies, both cases have the
same mandatory-service energy and same consecutive direct/wait energy:

| Quantity | Exact stored-number kWh | Approximate kWh |
|---|---|---:|
| All mandatory services | `250264333071608593/281474976710656` | 889.1175194194 |
| All 36 forced consecutive movements | `12835258938005913/140737488355328` | 91.2 |
| First service through last service | `275934850947620419/281474976710656` | 980.3175194194 |
| Excess over 400 kWh inventory | `163344860263358019/281474976710656` | 580.3175194194 |

Service consumption alone already exceeds battery capacity. Including every
represented leg strengthens the obstruction; waiting auxiliary energy is not
added twice. The calculation deliberately excludes the initial pullout and
final pullin, whose nonnegative energy could only strengthen it.

A shorter, deterministic prefix also shows the violation well before the end
of the route. By the end of the first 16 mandatory services, at 14:07, service
plus forced consecutive-leg consumption is exactly
`15081332800189559/35184372088832 = 428.6372586702089` kWh. No allowed charging
opportunity precedes that point along a one-bus full cover. Even granting a full
400 kWh immediately before the first service, its inventory must therefore
violate the lower bound by more than 28.6 kWh. This margin is far larger than
any qualified numerical replay or coefficient-aggregation tolerance.

## Scope and how later work may use the result

The proof is combinatorial and energetic; it makes no inference from a native
incumbent being two buses or a one-bus relaxation being weak. It respects all
37 mandatory services and the complete declared graphs. A different depot
access policy, larger battery, permitted off-depot charging or a different
movement graph could remove the obstruction. Two internal counterchecks increase
battery capacity to 2000 kWh and correctly make this particular obstruction
unproved; they do not claim feasibility in that altered scenario.

The archived first pilot remains two wide, bounded price-oracle outcomes. Its
original note that two-bus feasibility alone does not prove minimum fleet size
remains correct; this new proof provides the additional argument afterward.
Any strengthened relaxation or optimizer using a fleet lower bound of two
requires a separately declared subsequent version/protocol. No original native
interval is overwritten or silently tightened. Cardinality optimality alone
also leaves the cost-optimality question open.

The derivation must be distinguished from the separate exact flat-price
matching relaxation: no matching call or result is used here. An objective
lower bound assembled from these facts must state its own coefficient and
numerical conventions and retain its provenance as post-pilot analysis.

## Reproduction and evidence identity

The standard-library reproduction and all 36 transition/leg records per case
are saved at
`research-20260927/agent-notes/sistig-one-bus-postpilot/diagnostic.py` and
`result.json` in the same directory. The script verifies the original frozen
input before and after reading, reconstructs each case identity, checks all
movement time directions and uses exact fractions throughout the energy proof.
A new output path is required; existing evidence is never overwritten.

Frozen input SHA-256:
`35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b`.
Post-pilot result SHA-256:
`cdc2603b1e53dba7fdff757e63c2f64265b0d190aef1174f4792d607ecf2b3e9`.
The result records the exact script hash. Independent proof review is a separate
step before using this analysis in a public research claim or future model.

Independent review has now passed: `research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md`. Its exact lower-bound and numerical-upper-witness scopes remain distinct.
