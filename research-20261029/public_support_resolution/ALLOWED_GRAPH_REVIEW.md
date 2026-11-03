# Independent review of fixed allowed bipartite successor graphs

Verdict: **Mathematical PASS under the stated fixed-compatibility assumptions.**
Read ALLOWED_GRAPH_EXTENSION.md and the relevant shared-connector theorem and
proof. No numerical execution, data access, import, hash or commit. No sparse-
graph implementation qualification or public-timetable coverage is established.

## Why the extension is valid

Every allowed partial matching still specifies a complete fleet: its matched
edges share buses and every unmatched service uses its retained standalone bus.
No bus can cover two services from the same simultaneous positive-duration
batch. Thus all declared assignments, rather than an outcome-selected bank,
are represented. A maximum matching of size nu yields matchings of every
size0,...,nu by deletion; larger cardinalities do not exist.

For each allowed matching the individual early intervals are unchanged:
[r_ij,a_i] for a matched A service and[0,a_i] otherwise. Their sum has common
upper endpoint sum A, independent of the graph. Serial common-window early
and terminal charging then imposes exactly E<=K and S-E<=H. No forbidden
edge is used in this physical construction. The empty matching still covers
every service, proving feasibility iff L<=U even with isolated vertices or
nu=0. Removing standalone options or lowering the2n fleet cap would invalidate
that sufficiency argument and is not part of the extension.

Nonnegative matching costs give monotonicity by edge deletion. Bipartite
unit-capacity min-cost flow using only allowed edges remains integral at
integer cardinalities and has a convex continuous RHS value function. Thus
r_m remains discretely convex on0,...,nu without complete crossmatching.
The old clipped-frontier argument applies on that finite domain: m0 is the
last threshold<=L, mmax is the last resource-feasible threshold<=U, and the
first retained horizontal increment is shortened by clipping. Its slope is
therefore no larger than the next one, and later slopes retain the original
discrete-convex order. Nonexistent and resource-infeasible cardinalities add
no fictitious endpoint. Collinear intermediate physical thresholds remain.

The support/value criterion follows unchanged for f>0 and strictly convex
continuous load-restricted supply. The empty graph has one physical operating
cost2nf over the whole feasible interval and therefore zero gap. At f=0,
the empty matching has zero operating cost for every feasible load, also
giving zero gap; the positive-fee interior criterion is not extended to it.
Admissible-price support still needs the framework's separate qualification.

## Important exclusions and a counterexample to the shortcut

The sorted-smallest/opposite-pairing formula is only a complete-graph result.
For A=(5,15),B=(14,15),capacity20 and corresponding-index edges only, the
full matching needs10 early energy. The complete graph can cross the pairs
and need9. The sorted shortcut would introduce a forbidden edge, so it must
not be used to evaluate the arbitrary-graph theorem. This is a hand logical
counterexample, not a new empirical or numerical result.

Nonzero transition time can destroy common windows; transition consumption
can make total energy depend on matching. Neither is handled by simply
supplying a public directed timetable graph. Bus-specific powers, omitted
singleton duties, extra shared resources and outcome-selected graph restriction
also require new arguments. The theorem is not generic EVSP or matching novelty.

## Minimal manuscript integration

Modified only heterogeneous.tex and heterogeneous_proofs.tex. The fixed shared-
resource theorem now defines a declared graph Gamma, nu and thresholds only
through nu; its proof uses the allowed-edge flow network and retains singleton
feasibility. The sorted corollary explicitly requires the complete graph.
The adequate-resource n-connector specialization is unchanged. The fourteen
completed shared-connector cases are expressly complete-graph qualifications;
the allowed-sparse-graph extension has proof review only. The closing scope
paragraph no longer implies both classes require unrestricted crosslinks.
No main narrative, numerical source, frozen result or qualification outcome
was changed. Parent will adjust main.tex separately.
