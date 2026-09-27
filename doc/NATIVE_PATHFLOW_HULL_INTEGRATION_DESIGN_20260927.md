# Compact pricing integration into native hull: minimal prospective design

Status: approved narrow hook and isolated adapter implemented prospectively;
pure/fake tests only, no integration optimizer execution yet.
The indexed native-hull V2 run is frozen at `186c987`; its eight-control result
is undergoing independent audit. The compact native physical gate has passed
its separate twenty-control audit. Neither result qualifies their integration
automatically.

## Approved narrow interface

The existing hull coordinator closes its pricing callback over
`native_recharge.solve_pricing`. A wrapper alone cannot replace that closure
without global mutation, copying the coordinator, or executing transformed
source. None of those is an appropriate dependency mechanism. The smallest
maintainable change is the narrowly approved optional injection hook:

- `native_hull.certify(..., pricing_oracle=None, oracle_id=None)` chooses the
  original indexed function when both are omitted, or requires an explicit
  callable and nonempty identity when both are provided.
- `state_identity(..., oracle_id=None)` preserves the old digest payload when
  omitted; an explicit oracle adds its identity to the payload. Results and
  trace metadata identify the injected oracle. Retained import requires the
  expected predecessor and matching oracle identity.
- A new `native_pathflow_hull` adapter supplies the already qualified compact
  pricing function and `egg-native-pathflow-v1` identity. Its qualified V1
  pricing driver already tags raw-variable snapshots and plans, but omits the
  top-level result tag. The adapter verifies the returned plan tag, rejects any
  contradictory top-level tag, and attaches the explicit dispatch identity.
  The shared coordinator then verifies result and plan identities before
  **every** pricing admission, including later calls rather than only the seed.

The hook changes only dispatch and provenance. Pricing inputs, remaining-time
budgets, native status/global-bound admission, complete physical replay, exact
simplex/polishing, conjugate calculation, global certificate width and failure
semantics remain in one shared implementation. Historical source/result hashes
remain preserved; a new freeze qualifies the new opt-in path. No module-global
function is replaced, including in scientific runners.

The indexed default must retain its old state identities and numerical logic.
The new compact option gets distinct state identities even though both integer
physical sets and cost/load projections are mathematically equivalent. This
keeps qualification receipts and retained-sequence dependencies unambiguous.
No certified bounds cross oracle/version boundaries through retained import.

## Integration gate

Use a separate eight-cell compact-hull runner, not another twenty-cell physical
gate. Reuse the exact V2 hull control definitions (six cold/retained tariff-path
cells, joint cold, fixed-reserve cold), targets, seed policy and caps. The
physical twenty-control gate already validates the compact oracle itself;
the eight controls exercise hull integration, reused columns and fresh bounds.
The runner must own its worker module name, new protocol identity, exclusive
attempt directory and full dependency hashes. It may reuse the qualified
read-evidence/accounting/assessment helpers as explicit imports.

Freeze the adapter, runner, tests, protocol, hook-bearing hull module, compact
pricing module, native physics/replay module and all imported fixture/helper
sources. The runner records requested/actual native backend and raw compact
variable maps through the existing nested pricing trace. No public timetable,
private data or changed scientific targets belong in this gate.

Pure tests must prove dispatch reaches the compact callable without touching
the indexed callable, the default indexed route/identity is preserved, missing
or mismatched oracle identity fails closed, compact formulation fallback is
rejected, retained dependencies cannot silently cross oracle identity, and
existing V2 cap/trace/mixture checks still pass. Then independent preflight,
source freeze, one preserved attempt and independent full-fleet/Fenchel audit
are required before any larger public-input hull experiment.

## Ownership and evidence boundary

The principal researcher approved this hook in `native_hull.py` plus the new
adapter, runner, pure tests and prospective protocol. The existing compact
physical module is unchanged. The certificate coordinator is shared; only the
new runner's process lifecycle is separate, with its own module dispatch and
attempt namespace. The indexed V2 result must be audited against frozen source
`186c987`, not this later prospective working tree. Source hashing includes all
imported runtime and fixture helpers. Independent preflight and a new published
freeze remain mandatory before the first compact-hull scientific execution.
