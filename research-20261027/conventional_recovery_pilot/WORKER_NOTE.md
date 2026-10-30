# Conventional recovery worker source contract

This change adds source only. No worker, fixture generator, import, compilation,
test, native solve, data read, journal read, hash computation, or commit has been
performed to validate it. Execution requires the parent's separate frozen
control and PASS review. This document is not runtime qualification evidence.

The fixture is the old pricing-workload recipe copied verbatim except for
`FIXTURE_ID = 'conventional-recovery-v1'` and seeds 62001–62004. Its original
`capacity-workload-v1|...` construction token, sizes 12/24, both supported quote
descriptors, resources, graph recipe, and costs are retained. Actual states all
use `source_shape`; no generated values have been materialized.

The worker loads the original pricing-workload worker helper by exact source
path only after gate admission. It binds `helper.HERE` to this directory solely
for the helper's fixture lookup. `helper.ROOT` remains original. Bootstrap,
record admission, original physical realization and joint fleet screen, value,
witness identity, and cache residual checks are reused by reference. The sibling
runner and its simple dive are called by reference; none of their implementation
is copied here. The adjacent bank builder and projector remain original.

There are eight seed/size cells and five phases per cell. The task ID is
`B{base_seed}-N{services}-{phase}`, in literal `HERE/attempt01/{task_id}`.
The exact spec fields are `task_id`, `phase`, `base_seed`, `services`, `arm`,
`quote`, `descriptor_sha256`, and `dependencies`. Arms are F=`fixed_duty`,
N=`full`, D=`full_dive`, UN=`union_n`, and UD=`union_d`. F has no dependencies.
N/D may have no dependency or one operationally accepted F. UN requires F+N;
UD requires F+D. Every dependency has exactly `folder`, `spec_sha256`,
`receipt_sha256`, nullable `selected_sha256`, nullable `bank_sha256`,
`strict_delivery`, `physical_valid`, and `bank_qualified`. Files are always read
from the worker's own literal expected path; supplied paths never select files.

CLI: `--worker ABS --parent-anchor FLOAT --spec-sha256 SHA256`.
`LAUNCH.json` must say mode FROZEN and review_disposition PASS and agree exactly
with exported `NATIVE_PARAMETERS` and environment. Source inventory is admitted
by the parent once per paid phase; worker checks required inventory entries and
actual imported module paths without rehashing every source file. This relies
on frozen source immutability while a paid worker is running. Input spec,
dependency receipt/spec/selected files, and journals are hashed once on their
single bounded read/admission; no second journal hash pass is used.

F is an independent fixed-duty native recovery. N uses the full native graph
without a dive. D uses the full graph and native simple dive with theta .7.
No phase supplies seed columns; integer pricing is disabled; partition is true.
F/N nominal native allowances are CG50 + MIP50 seconds; D is CG50 + dive25 +
MIP25. Multiply every allowance by `min(1, remaining_to_parent150 / 100)`.
UN/UD make exactly one binary finite-journal optimize call, at most 100 seconds
and clipped to parent+150. Every worker has parent-inclusive outer180 wall,
hard120 CPU, observed5GiB RSS, and one thread. The unchanged runner can request
internal300-second LP closure calls, and Python signal interruption of native
code may be deferred. The parent must enforce its outer deadline; nominal100
allowances are not asserted to be a hard native duration.

All native master rows use grid terminal160, fleet cap4, and exact service once;
the union's realized terminal row is inactive at zero. Every selected and common
fleet independently passes the original physical screen: both grid and realized
terminal160, four vehicles, exact service once, shared grid and realized plugs.
Stored record costs must agree with their original `source_shape` quote. There
is no flat-cost revaluation seam. A native status and bound concern its source
model or finite pool and are reported separately from physical admission.

Complete F/N journals are admitted against the runner's returned producer
digest, even when no selected endpoint exists. The native simple dive can append
CG columns after the runner has computed its initial digest. Therefore D has a
narrow additional authority: after a normal, timely, complete runner return,
the wrapper streams and physically admits its own exact final D journal once,
computes its digest during that same read, and publishes it with
`bank_source = 'wrapper_admitted_final_post_dive_journal'`. The untouched
`source_initial_columns_sha256` is explicitly pre-dive and is not asserted to
match the final journal. Interrupted/nonreturning D has no final-bank authority.
No count-based trust, column dropping, deduplication, or stale-pin fallback is
allowed. Any invalid record is fatal. Oversized/unavailable complete journals
remain unavailable rather than truncated.

UN/UD require both complete qualified banks plus the operational admitted F
common fleet. Records retain distinct origin/index identities, including
duplicates. The F common is canonically matched in the consumed F bank, then
used as the MIP start and protected retained endpoint. Union candidates are
selected directly from the consumed records and checked for canonical record
membership. N/D may retain the common F even when their own bank is unavailable.
A fallback is operational protection; it never creates strict method delivery.

Receipts distinguish candidate, fallback, and retained components/values;
strict delivery, physical validity, native optimality, complete-bank admission,
native statuses/bounds, failures, source bindings, input pins, and observed
resources are separate. Native source summary telemetry is retained. Full
recovery, CG/LP/pricing and reported fleet-MIP timings are recorded; absent
native dive and charging-MIP durations remain unknown. Final selected digest
identifies the retained operational endpoint, which may be F. Source certificates
are never promoted into continuous-cost or full-integer-space certificates.
