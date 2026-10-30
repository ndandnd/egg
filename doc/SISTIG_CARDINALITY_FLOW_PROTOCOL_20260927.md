# Prospective exact cardinality-flow experiment

27 September 2026. **Preflight implementation only. No public-case flow calculation
has been run under this protocol.** The original matching attempt and both native
pilot archives remain immutable. This is a post-pilot ideal stored-input lower
bound, conditional on the independently reviewed exact one-bus obstruction.

The case is the complete 37-service single-depot graph for each of depot 15
and depot 16 in `data/public/sistig_26088190_v1/hildenbrand_native_cases.json`.
The full payload SHA-256 is
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`.
Native case identities, in that order, are
`1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`
and `216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d`.
The original native pilot frozen-input SHA-256 is
`35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b`.
The exact one-bus proof result, diagnostic source, proof note and independent
review SHA-256 values are pinned in the prospective runner's `PINNED` map.
The independent review passes the lower bound of two buses in both exact
declared graphs. The existing two-bus upper witnesses are numerical replays
under the native tolerance policy; they are not exact rational certificates.

For each source case, the author runner uses the frozen V1 path-cover cost
reduction but a new min-cost-flow algorithm. It sends 37 units from `s` to
`t`, one through each row. A row may use its own unmatched arc or one allowed
real successor column. Each column has unit exit capacity. The `g→t` gate
has capacity 35. All selected real connection costs are exact rational
`a_ij=w(i,j)-h(i)-o(j)-f`; signed values remain signed. Parallel modes are
reduced by exact `(cost, movement_id)` order. Equal shortest paths use fixed
arc order and only strict distance updates. Bellman-Ford shortest
augmentations have a hard eight-million-relaxation cap per case. The solver
then computes exact residual potentials with `pi_t=0`. Its certificate stores
every arc, capacity, rational cost, integral flow, potential, and exact network
objective.

The separate certificate verifier, authored alongside the flow algorithm,
recomputes the complete arc set, cheapest parallel mode for every ordered
pair, pullout/pullin minima, baseline and direct decoded movement objective
from the original frozen payload. It never imports the flow algorithm or the
V1 cost reduction. This separation permits an independent implementation
check, but it is not the later independent result review. For every node it checks **outflow
minus inflow = supply** (`b_s=37`, `b_t=-37`). On each original arc it checks
`r=c-pi_tail+pi_head`: an available forward residual arc requires `r≥0`, and
an available reverse residual arc requires `-r≥0`. It checks exact equality
of primal network cost and
`sum_v b_v*pi_v + sum_a u_a*min(0,r_a)`, then adds the exact baseline.
It also verifies real-edge and unmatched counts, gate flow, decoded movement
IDs, path count and published objective fractions. This check does not trust
the saved arc list, costs or baseline. The implementation does not call a
native or nonlinear optimizer.

The sole prospective attempt directory is
`result/sistig_cardinality_flow/20260927-attempt1`. The `freeze` step creates
it exclusively and checks every listed source, original payload, proof and
review file against a published `HEAD` blob. It records source commit/hashes,
full case data and identities, Python/platform identity, exact `.2` binary
float price, two algorithm calls, a 120-second complete-run cap, an eight
million-relaxation per-case cap and a 150-second external child cap. The
`supervise` step creates an exclusive launch sentinel, invokes one bounded
child, records stdout/stderr and a supervisor receipt on success or failure,
and seals a SHA-256 manifest of all prior files. A changed or missing source
after child exit is recorded in the receipt and makes supervisor completion
nonzero, even when the child exited successfully. The `run` step creates a
`STARTED` sentinel, writes each raw depot result exclusively after immediate
author-written certificate verification, and writes a summary only after both
results and source/frozen-input rechecks pass. Every attempt file is write-once.

Launch is gated on an **independent code and synthetic-test review** and
publication of all listed sources in a committed tree. The independent
review receipt must be committed at
`research-20260927/agent-notes/sistig-cardinality-flow-independent-review/REVIEW.md`
and contain `**PASS**` and `public-case algorithm not run`; freeze and child
execution enforce this gate. The research lead owns the commit, attempt
freeze and launch. Preflight permits only small
synthetic graph tests: empty and sparse graphs; signed and multiple negative
arcs; binding/nonbinding gate; ties; brute-force minima; malformed proof
identity; corrupt arc sets, capacities, flow, potential and objective. Do not
invoke the public algorithm, optimizer, or any campaign in preflight.

After an authorized public run, a reviewer independent of the algorithm and
its author-written certificate verifier should verify both certificates anew
from the pinned payload, compare the exact bounds with the archived V1
matching values, and preserve every failure. Report the new
values solely as ideal stored-input lower bounds. Do not combine them with
the rounded native solver lower endpoints or tolerance-qualified two-bus
witnesses into an exact physical gap, physical optimum or nonlinear claim.
