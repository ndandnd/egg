# Independent audit of public Sistig matching attempt 1

**Verdict: PASS.** This audit independently rebuilt both frozen cost matrices
from the serialized cases and verified both exact primal/dual assignment
certificates. It did not import the author's adapter, matching implementation,
native model, or optimizer, and did not rerun the matching algorithm. It left
all original attempt files unchanged; the review artifacts live only in this
new `review/` directory.

The frozen attempt uses commit
`3014d04a043d5c6b99433fc5458271a3076d16b5`. Its frozen input SHA-256 is
`084938d9d526710f19f75d544ac6c8ae26ba42c341744978f6447d0874f86742`, and the
derived public case payload SHA-256 is
`af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`. All
nine frozen dependencies matched both the current files and their Git blobs at
the pinned commit. I recomputed each case identity and compared all 37 native
service records, every directed movement mode and leg, resource row, and
market edge to the pinned public payload.

For each mode, I independently computed its weight as
`deadhead_cost_per_min × sum(leg durations) + flat_price × sum(leg energies) / efficiency`,
using exact rational representations of the parsed stored numbers. I selected
the cheapest declared pullout and pullin for every service, collapsed parallel
directed connection modes by exact cost and movement ID, and rebuilt the
singleton baseline and 37-by-74 assignment matrix. Each case has 666 distinct
directed service-pair edges and 1,369 zero-cost dummy edges, for 2,035 allowed
primal edges checked. The 666 pair edges retain the minimum among the
source-declared parallel movement modes; no missing arc or reverse-direction
substitute was introduced.

| Depot restriction | Baseline | Assignment primal = dual | Exact lower bound | Decimal display |
|---|---:|---:|---:|---:|
| 15 | `10440307691622779244267870777729591/2535301200456458802993406410752` | `-19352765077116066834932685494348613/5070602400912917605986812821504` | `1527850306129491653603056061110569/5070602400912917605986812821504` | 301.3153438838777 |
| 16 | `21570154473263258087687455045970013/5070602400912917605986812821504` | `-5005101738301777607548666398990435/1267650600228229401496703205376` | `1549747520056147657492789450008273/5070602400912917605986812821504` | 305.6338078838777 |

For each certificate I checked all 37 row assignments, column uniqueness,
forbidden-edge exclusion, all 2,035 dual inequalities, all 74 nonpositive
column potentials, the exact integer scale, and exact equality of the primal,
dual, and declared objective. Selected edges are tight; all 37 unused columns
have zero potential. Reconstructing the chosen movement IDs from the matching
and cheapest endpoints reproduces the same objective from the service
constant, vehicle costs, and selected mode weights. Each assignment joins 36
service pairs into one **relaxation path** and selects 38 movement modes.
Chronology makes that graph acyclic and its path cover includes all 37
services. The one-path result is not a claim of battery, charging, or physical
feasibility: those constraints are deliberately relaxed in this bound.

Six independent corruption controls per case rejected a duplicate assignment
column, a forbidden selected edge, a violated row dual inequality, a positive
column potential, a changed objective, and a nonzero dual on an unused
column. The complete outcomes are in `audit-report.json`.

The original attempt manifest's nine file sizes and SHA-256 hashes all match.
The runner receipt records two calls, 0.204274 seconds for the routine,
0.280112 seconds under supervision, exit code zero, no timeout, unchanged
source hashes, and empty stdout/stderr. The launcher's Python 3.12.2 and
platform matched the frozen runtime exactly. The saved status flags state that
no native optimizer was invoked and make no physical-feasibility or
native-matrix optimality claim.

The exact fractions certify the matching relaxation for the stored-binary
input values and frozen price. They do not certify an optimum of the original
physical case, of the rounded native matrix, or of the publisher's two-depot
problem. The matching's one-path decomposition may be infeasible under SOC,
recharge-window, or shared-connector constraints.

## Review artifacts

- `reconstruct_matching.py` independently rebuilds inputs, checks certificates,
  tests corruption controls, and verifies frozen source/archive hashes using
  only the Python standard library.
- `audit-report.json` records exact results, counts, identities, runtime and
  integrity checks.
- `MANIFEST.json` hashes these review artifacts; it intentionally excludes
  itself.

