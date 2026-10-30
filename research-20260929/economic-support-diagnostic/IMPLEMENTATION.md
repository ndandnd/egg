# Implementation notes

The QP hull source is the curated attempt-1 `summary.json`,
`frozen_identity.json`, `COLLECTION_RECEIPT.json`, and integrity receipts.
Hashes in the collection receipt must match the curated files. The runner
requires all six QP rows to be unique, on time, complete, certified and
bounded; it checks their case/market identities against locally reconstructed
development inputs before freezing their exact interval text. No QP hull
optimization or archived event-log read occurs.

Planner and fixed-price response use existing `native_pathflow` functions
and the existing physical replay assessment. The response price is formed
from the replayed incumbent load and saved before its call. A returned
stage becomes admissible only with an on-time receipt, compatible physical
identity, replayed plan, finite global bounds and a matching assessment.
The summary keeps raw native bounds and statuses separate from derived
`D-CH` and own-price-regret intervals. With compatible admitted stages,
it strengthens `D`'s lower endpoint to `max(D_L,CH_L)` and `CH`'s upper
endpoint to `min(CH_U,D_U)` before forming the nonnegative gap enclosure;
the original raw `D` and imported `CH` intervals remain visible. A hull
lower endpoint above a physical upper witness is flagged inconsistent,
never silently clamped. It reports component solver time
only when present, without assigning unmeasured construction time.
