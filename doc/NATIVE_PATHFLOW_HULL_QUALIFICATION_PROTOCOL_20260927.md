# Compact-oracle native hull qualification protocol

27 September 2026. Prospective protocol
`native-pathflow-hull-qualification-20260927-v2-energy-band`, shared result schema
`egg-native-hull-v2`, explicit pricing identity `egg-native-pathflow-v2-energy-band`.
**No V2 energy-band compact-hull optimizer execution has occurred at protocol preparation.**
The first compact-hull attempt remains preserved at `72a1f715e9e6714746f9c0638c50d2cba6bfcfdb`,
with its original oracle identity and outcomes. This V2 gate uses the same eight
scientific definitions and budgets under a new oracle/version identity and
requires the separate V2 twenty-control physical qualification first.
The indexed V2 eight-cell attempt remains frozen at `186c987`. Its saved source,
results and independent audit are separate evidence. The compact native physical
oracle passed its separate twenty-control gate; this does not automatically
qualify integration with the hull coordinator.

## Scope and fixed mathematical contract

This gate requalifies the same explicit compact-oracle integration after adding
two valid aggregate-energy inequalities to the compact physical model. The
shared hull coordinator, master/polishing algorithm and objective are unchanged.
The exact band covers intended physical energy conservation and exact
binary-stored V1 integer row points, with both rounding ledgers recorded; see
`NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md`. No native tolerance is changed.
This does not assert identical fractional relaxations or numerical execution.
The compact integer path-flow model represents
the same complete physical set and cost/load projection as the qualified indexed
model, under the homogeneous fleet, positive-duration service DAG, declared
directed movement modes, native terminal replenishment and one finite connector
assumptions documented in `NATIVE_PATHFLOW_EQUIVALENCE_REVIEW_20260927.md`.
It makes no claim about equality of LP relaxations or comparative speed.

The objective, conjugate, exact stored-number mixture arithmetic, fully
corrective master, rational pairwise polishing, retained-pool semantics and
certificate admission are unchanged from
`NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md` and
`NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md`. The target is

`CH = min_(L,cbar in conv{(e(x),c(x)):x in X}) cbar + F(L)`.

Each column is a complete physically replayed fleet. A mixture is a planning
relaxation, not an executable fractional fleet. The fresh global enclosure is
`q_lower(p) - F_+*(p) <= CH <= cbar + F(L)`, using the actual serialized pricing
vector and the admitted global native lower bound, never the pricing incumbent
or a restricted-master bound. Exact rational arithmetic applies to stored finite
numbers; native bounds and physical witnesses remain tolerance-conditional.
No learned prices, known supporting columns or analytical targets enter the
optimization algorithm.

## Explicit integration and identity boundary

`native_hull.certify(..., pricing_oracle=None, oracle_id=None)` uses the original
indexed pricing callable when both arguments are omitted. Its previous digest
payload, result fields and numerical algorithm remain unchanged on that path.
An opt-in call requires a callable plus a nonempty identity. The new
`native_pathflow_hull` adapter supplies the qualified compact callable and its
fixed formulation identity without mutating any module global or copying the
certificate coordinator.

The compact driver identifies its raw-variable snapshots and
decoded plans but does not tag top-level results. The adapter rejects a
contradictory top-level tag, checks the existing plan tag for an admitted status,
then adds the explicit dispatch identity to its return. Before every admission,
the shared coordinator verifies that both result and plan identify the requested
oracle. Existing physical identity, submitted-price equality, complete replay,
objective consistency, backend identity and native-bound checks still apply.
An unresolved/infeasible result or any mismatch fails this all-feasible gate.
Identity tags are provenance checks on the frozen code path, not cryptographic
proof that an arbitrary caller-provided implementation solves the declared set.

Compact state identities, state/pricing metadata, column source receipts and
results include the oracle identity. Retained import requires an identical
oracle identity as well as the existing immediate-predecessor state identity,
certified result, passing controller receipt, zero exit code, no timeout or
evidence issues, complete nonzero native accounting, complete polishing
accounting, matching phase counts and replay of every column. Indexed and
compact retained states cannot cross this boundary. Imported columns preserve
their witnesses; old prices, bounds, lambdas and tangent points are discarded.

## Eight prospective controls

The new runner explicitly imports the unchanged V2 `controls()` definitions.
All case dataclasses, market coefficients, state order, predecessor links,
targets and expected feasible outcomes are identical. Only protocol/oracle
metadata and resulting state identities differ. Native terminal opening is zero,
with the existing resource windows; an A-only bus retains early-window access.

| Cells | Case and early linear coefficient | Exact hull target | Exact early/late aggregate grid kWh |
|---|---|---:|---|
| nominal cold/retained state 0 | Battery 20, reserve 0, efficiency 1, early 10 kW; `a=4` | `7591/80` | `(27/4,93/4)` |
| nominal cold/retained state 1 | Same physical case; `a=21/5` | `1539/16` | `(25/4,95/4)` |
| nominal cold/retained state 2 | Return to `a=4` | `7591/80` | `(27/4,93/4)` |
| joint cold | Battery 20, reserve 1, efficiency 19/20, early 12 kW; `a=4` | `2987911/28880` | `(573/76,1827/76)` |
| fixed-reserve cold | Battery 20, reserve 1, efficiency 1, early 10 kW; `a=4` | `99` | `(5,25)` |

Early/late curvature is `1/5`; late linear coefficient is zero. The two
unavailable periods retain zero charging and zero coefficients. Cold states and
retained state zero start with the counted seed price `p=a`. Retained states one
and two import only their immediate successful predecessor; failed dependencies
produce `blocked_by_predecessor`, not a cold restart. Independent cells continue.
The certificate width must be at most `1e-4`, restricted-pool gap at most `1e-6`,
and target comparison tolerance is `2e-4`. Load errors remain descriptive.

## Fixed resources and failure-preserving evidence

Initial backend is CBC, one thread. All inherited V2 budgets remain unchanged:
16 pricing requests including the seed, 64 master requests, 48 columns, ten
seconds per native phase, 60 seconds per state, and the remaining-time cap on
each phase. Master admission remains OPTIMAL-only; pricing may admit a qualified
FEASIBLE global bound under the unchanged physical/objective checks. Per state,
polishing allows 256 accepted transfers, 8,192 numerator/denominator bits and
five cumulative seconds, also subject to the state deadline. A cap or stalled
open gap remains failure/bounded evidence, never assumed exact optimality.

Each sequential worker has a 75-second external cap. The new supervisor owns a
new process group and 650-second outer cap, followed by TERM and at most ten
seconds before KILL of remaining group members. The new runner invokes only
`experiments.native_pathflow_hull_qualification` as its worker/controller module.
It creates an exclusive attempt directory; no existing attempt is overwritten,
resumed, retried or relabeled. A later backend replication is separate evidence.

Before any worker solve, save all eight inputs, exact analytical targets,
identities, predecessor links, budgets, environment and source hashes. Hash the
hook-bearing hull module, compact physical model, compact adapter, both runners,
native physics/replay and fixture helpers, original/new tests, original/new
protocols and energy-band/integration design documents as enumerated in `SOURCES`. Workers verify those
hashes and the protocol/oracle identity. A commit label alone is insufficient;
the principal researcher must publish the full reviewed execution state first.

Retain the compact raw-variable mappings and additional aggregate-energy
row/rounding ledger, backend/runtime
identities, phase starts/statuses, dimensions, bound/objective data, complete
decoded plans, replay and normalization evidence. Retain immutable master column
orders/tangents/raw weights, exact simplex corrections and mixture arithmetic,
all polishing step equations/caps/times, all Fenchel bounds, stdout/stderr,
exceptions, worker receipts and supervisor receipt. Counts include seed,
unsuccessful native calls and all polishing work. Shared parsing/accounting
helpers preserve valid prefixes of truncated files, record evidence defects and
continue independent cells. Passing receipt counts must match the saved trace.

## Review and execution gates

Pure/fake tests must cover all original 64 V2 tests, unchanged eight scientific
definitions/budgets and default digests, explicit compact-only dispatch, rejection
of missing/incorrect identities on later calls, both retained-boundary directions,
own worker module dispatch and continued accounting of failed controls. Block
native solver imports during this preflight. An independent reviewer checks the
hook, adapter, runner and protocol before a new source freeze and one attempt.

After that freeze, the principal researcher may execute:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m experiments.native_pathflow_hull_qualification --output result/native_pathflow_hull/20260927-attempt2 --freeze-label COMMIT_ID --backend CBC
```

Use the actual published full commit in place of `COMMIT_ID`. Independently audit
all admitted compact fleet columns and raw constraints, exact mixtures, native
global bounds, Fenchel arithmetic, target enclosures and complete receipts.
Success qualifies this synthetic integration only. Public-timetable admission,
resource budgets and interpretation require their own prospective protocol.
Any repair needs a separate version/freeze/attempt; no existing raw outcome is
reclassified.
