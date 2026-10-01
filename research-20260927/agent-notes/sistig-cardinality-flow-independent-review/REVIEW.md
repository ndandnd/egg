# Independent preflight review: cardinality-gated Sistig flow

27 September 2026. **PASS** for the frozen-source design and synthetic
implementation preflight. The **public-case algorithm not run**. No optimizer
or public flow calculation was invoked.

## Reduction and exact certificate

The path-cover reduction is correct for the stated ideal full-replenishment
flat-price model. For each service, the baseline charges its service energy,
one vehicle, and the least-cost declared pullout and pullin. A connection
`i→j` replaces the pullin at `i`, pullout at `j`, and one vehicle, so its exact
increment is `w(i,j) - h(i) - o(j) - f`. Movement cost uses every stored leg's
energy divided by the declared charging efficiency and every leg's duration
at the declared deadhead rate. Stored floats are converted to exact binary
rationals; parallel modes use the same exact `(cost, movement_id)` tie-break
as the existing reduction. The author-written verifier independently repeats
this cost construction from the frozen payload without importing either the
new flow algorithm or the V1 reduction.

The network sends 37 units. Source-row capacities force each service row to
choose exactly one real successor or its own unmatched arc. Unit-capacity
successor columns enforce indegree at most one, and the gate capacity 35
limits real edges to 35. The pinned one-bus obstruction establishes at least
two paths for the declared graphs; every feasible physical path cover with
two or more buses is therefore retained by this relaxation. All allowed
connection arcs advance in strictly increasing service time, so any integral
matching is a path cover without cycles. Relaxing SOC, charger, and maximum
fleet constraints can only lower the ideal stored-input flat-price objective.
This is not a native-matrix bound or a physical optimum.

The successive shortest augmentations are deterministic: exact `Fraction`
costs, a fixed arc order, Bellman–Ford residual shortest paths, strict-only
distance updates, and a per-case relaxation ceiling. The initial network is
acyclic even with signed connection costs; shortest residual augmentation
preserves min-cost flow, and a negative residual cycle is rejected. The final
potentials use the convention `outflow - inflow = b`, with `pi_t=0`. The
verifier checks every expected arc and capacity, integer flow, all balances,
forward/reverse residual reduced-cost signs, and exact primal-dual equality
`sum_v b_v*pi_v + sum_a u_a*min(0,r_a)`. Those conditions certify the exact
minimum of the declared fixed-flow network. The direct decoded movement
objective is checked against baseline plus flow cost.

## Inputs, provenance, and execution evidence

The pinned payload SHA-256 is
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`. I
read-only parsed and validated both single-depot variants: each has 37
services; depot 15 has 1,370 declared movement modes and case identity
`1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`; depot 16
has 1,335 declared movement modes and case identity
`216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d`. The
payload and case identities are checked again by the runner and the verifier.
The adjacent attribution file identifies the source dataset DOI and CC BY 4.0
license; its SHA-256 is recorded below.

The pinned one-bus proof note, exact diagnostic input/result, independent
one-bus proof review, and prior native frozen input all match the runner's
`PINNED` hashes. The proof establishes only a lower bound of two buses. The
prior two-bus references are tolerance-qualified numerical replays; this
preflight does not combine them into an exact minimum-fleet or exact physical
gap claim.

The normal supervised path applies the 150-second child cap, records stdout
and stderr, writes a receipt, and hashes the attempt files into a manifest.
The changed-source error paths now preserve the receipt and manifest while
returning a nonzero supervisor exit. The five focused mocked cases passed
(changed pin, deleted pin, other source drift, child failure, and timeout).
The 13 small synthetic flow/verifier tests also passed before this
supervisor-only change. The CLI still exposes `run` for the supervised child;
calling it directly is **not protocol-compliant**. Admit no result without
the actual `supervisor_launch.json`, receipt, timeout accounting, and manifest.
The author-written verifier is a separate implementation, not the later
independent post-run result audit. That audit must reconstruct both public
certificates anew from the pinned payload without importing either author
implementation.

## Reviewed SHA-256 fingerprints

| File | SHA-256 |
|---|---|
| `doc/SISTIG_CARDINALITY_FLOW_PROTOCOL_20260927.md` | `14abfc0a9100d11626416a589bf1d7b13cd7f42be7035d03d711b6051f541e73` |
| `src/egglab/cardinality_flow.py` | `511b9d5ed25da22641019f2d91558b5c30a9254315163ffaa59bffe7cb2e3b45` |
| `src/egglab/cardinality_flow_verify.py` | `2ff64a436201962ec93db7ed623691c219ab00942bf81dea5b6b5f6fdddc0efa` |
| `src/experiments/sistig_cardinality_flow.py` | `1504904e190e7f408b4a4aef032ead2282f01471cfa824e4753f0267329d7eeb` |
| `src/tests/test_cardinality_flow.py` | `1939beaf5865db513012024707b60c8fb3ee90b2cc9e488bbede16e212dbb038` |
| `src/egglab/flat_energy_relaxation.py` | `5f3e9e2047abc1b4af586b062966334ae737fae2cb0d5cbea98a87a6026b71cb` |
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/experiments/sistig_native_case.py` | `f47a7a926d102f948d73e6d450f25a46fe7ad84fc93e4ff7e877da76ffe0e3c9` |
| `data/public/sistig_26088190_v1/hildenbrand_native_cases.json` | `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6` |
| `data/public/sistig_26088190_v1/ATTRIBUTION.md` | `96810c5e6a30eaa390a5b919de15fe40e02fad4d2072740d72779e816786722c` |
| `doc/SISTIG_FLEET_CARDINALITY_RELAXATION_DESIGN_20260927.md` | `3c4e132439547c5827f54f96952cd52e2d28f1169cb5799e91bc622d874b00a2` |
| `doc/SISTIG_FLEET_CARDINALITY_RELAXATION_REVIEW_20260927.md` | `f45507cf3db3493b1dc4bc561a1b8b61a3d5692d51e365c716b06a54f8dd7c90` |
| `doc/SISTIG_ONE_BUS_OBSTRUCTION_20260927.md` | `a2c4badf085d9d67c205170f8b7460e7efc1b40ac8b87aab4aa846c1815d8bdb` |
| `research-20260927/agent-notes/sistig-one-bus-postpilot/diagnostic.py` | `fada2a1ef1fc2b1aa0f54f8c847d0f84cfa6659f56f8638f02ed9550094d4b5f` |
| `research-20260927/agent-notes/sistig-one-bus-postpilot/result.json` | `cdc2603b1e53dba7fdff757e63c2f64265b0d190aef1174f4792d607ecf2b3e9` |
| `research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md` | `7b1d55d1d20fce676ded6aaeb6ae0965cd70fc464581290ad792f2056bce53a2` |
| `result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json` | `35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b` |

No public-case flow calculation has been run. Any later result must be admitted
only from the frozen commit and a complete supervised attempt; it must be
reported as an ideal stored-input lower bound, separate from the archived V1
matching bounds and tolerance-qualified native witnesses.
