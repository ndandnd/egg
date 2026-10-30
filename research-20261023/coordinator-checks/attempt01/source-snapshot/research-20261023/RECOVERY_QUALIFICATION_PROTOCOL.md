# Recovery engineering qualification — 23 October 2026

Prospective specification, not evidence of execution. The complete 17 October 360-cell
screen qualifies recovery development; its economic outcomes do not choose cases,
splits or retries here. This document authorizes no substantive study launch, training,
cluster work, sealed data access, or model promotion. Freeze implementation and manifest
before numerical qualification. Preserve the older qualification ledgers unchanged.

## Resources and accounting

Hard ceiling: **900 process-tree CPU seconds (0.25 CPUh)** cumulative across this
qualification's freeze, fixtures, numerical attempts, monitoring, analysis and repairs.
One local worker, one native/BLAS/OpenMP/Torch thread, process-tree RSS <=5 GiB. Monitor
RSS/CPU at <=0.25 s and system pressure at <=1 s; fail closed on monitor failure. Stop
dispatch on RSS breach or sustained <10% free memory for 5 s; terminate owned descendants.
No cluster. Stop dispatch at 720 charged CPU seconds; reserve 180 for shutdown/audit.
Before every launch require room for its entire 32.5 s outer allocation plus shutdown.
A missing final CPU record is conservatively charged elapsed allocation, never zero.
No automatic retry; all revisions share this ceiling and carry forward immutable receipt
hashes and measured charges. Budget exhaustion is an incomplete qualification, not a pass.

## Required integration interface

Adapt the v3 receipt/ownership mechanisms in `src/experiments/codex_local_campaign.py`,
not its hard-coded 0.5 CPUh ceiling or two-worker loop. Separate new output namespace
and source lock; do not mutate screenv3 results or frozen workers. Expose qualification
`freeze`, `self-test` (solver-free), `run`, and `analyze` entry points or equivalent
explicit arguments. Freeze hashes sources/models, case generation, market, movement
order, split/reserves, faults, task IDs, environment and native backend versions.

The common planner must accept an absolute monotonic `deadline`, optional binary start
and separately retained physical fallback. Worker receives supervisor `parent_monotonic`
before interpreter launch; D=t0+30 s, prefix cutoff=t0+15 s, finalization reserve=3 s,
cumulative completion reserve=3 s inside the remaining planner allowance. Prefix reserve
is 3 s for extraction/completion/lift before cutoff, hence prefix integer search ends
by t0+12 s. Unused prefix time is not a new budget. Full recovery may start only after
an independently replayed full-case witness is durably saved, and before D-6 s. No
prefix witness means cold unrestricted continuation with the actual remainder, recorded
as such. No remaining time means finalize fallback without a solver call. No stage,
retry, model build, native call, completion or artifact write gets a fresh 30 seconds.
Every native limit is clamped to both its stage cutoff and common deadline/reserves.

Use immutable `attempt.json`, append-only `native.jsonl` and `ledger.jsonl`, result,
plan/replay artifacts, fsynced result then hashed `completion.json`, and supervisor receipt.
Receipt endpoint is completed result materialization minus parent anchor, independent
of cleanup. Late/missing/malformed completion is censored; 2 s kill grace plus 0.5 s
TERM escalation is accounting only. Completed failures are skipped on resume; incomplete
attempts block resume pending audited reconciliation. Include supervisor CPU in ledger.

## Solver-free tests required before native dispatch

1. Permute movement order and restore edges which split elementary charging intervals.
   Build a full-model binary vector keyed by unique movement ID: selected=1, every
   other full movement=0. Assert exact binary inventory, no continuous starts, no
   source `(j,k)` copies, unchanged bounds/constraints. Reject duplicate/unknown IDs,
   missing selected edges, and same-ID changed physics. Replay source then full witness;
   recompute full-market bill including a changed tariff rather than copy cached bill.
2. Inject start setter exception, native rejection/unknown status, no incumbent, timeout,
   extraction/completion failure and later replay rejection. Previously admitted full
   fallback survives with its own exact bill; invalid fallback is rejected. Same-prefix
   selected bill never worsens. Contradictory full infeasibility is visible, not certified.
3. Feed an artificially high restricted MIP and fixed-route LP bound: neither enters
   global lower-bound state. Only an admitted full unrestricted native bound may do so;
   objective guard remains unchanged. Fallback objective cannot be replaced by a later
   solver candidate's objective to manufacture certification.
4. Fake the shared clock across import, loading, prefix build, lift, start and finalization.
   Verify no solver starts after its cutoff, no deadline reset, charged failed work,
   late serialization censorship, cleanup independence and no-time fallback. Test parent
   death, descendant shutdown, resource stop, missing/corrupt receipts and resume skip.

## Deferred phase 1: tiny native matrix

First qualify the handwritten six-task phase 0 in `RECOVERY_NATIVE_PRIMITIVE_PROTOCOL.md`.
The following phase 1 matrix is deferred; it is not today's launch and shares the same
900 CPU-second cumulative ceiling with phase 0 and every repair.

Freeze two nonsealed TRAIN-derived qualification cases, one each 40/80 trips, using
new independent base IDs disjoint from all screen, training and study bases. Case choice
uses identities only. Use frozen nonlearned ranking, the existing 30% plus top-three
coverage rule, solver seed 17, target day tariff; no economic comparison or tuning.
Eight tasks at 30 s each: each case runs static pruning, normal recovery, cold full
control, and recovery with an injected start-setter exception after durable lift.
Thus at most 240 nominal worker CPU seconds, leaving at most 660 seconds before phase-0/prior charges inside the hard ceiling
for fixtures, monitoring, setup and any prospectively frozen repair attempt. Do not use
spare capacity for extra seeds or longer solves. If either case fails to acquire a witness,
record the natural no-plan result; fallback-native coverage remains unqualified until a
new bounded revision supplies it. Never replace a case because its bill is unfavorable.

Normal recovery must log the actual native start vector inventory/hash, unset continuous
variables, and native processing evidence. `submitted` alone is not `accepted`; parse
native evidence as accepted/rejected/unknown with log offsets. Acceptance is not guaranteed
and is not an economic gate. At least one native recovery task must show native start
processing and independently admitted fallback; inability to observe processing blocks
that interface claim. Native failure injection must preserve any acquired fallback.

## Gate and runner output

Pass only with every scheduled task terminal/accounted, no accepted invalid witness,
no mapping or bound-scope violation, passing clock/resource/receipt tests, native partial
start processing observed, and fallback fault path exercised. Correctly recorded natural
no-plan outcomes are allowed but cannot stand in for unexercised required paths. Require
all uncensored endpoints <=30 s and no unexplained overrun; censored engineering endpoints
block passing. No ranking inference follows from these eight tasks.

Emit a machine-readable gate table with test evidence paths, all counts/denominators,
CPU by attempt and overhead, RSS/pressure, timing and censoring; native submitted/accepted/
rejected/unknown counts; prefix/fallback/final bills; selected witness identity; unrestricted
bound provenance; and unresolved requirements. A failure stops numerical dispatch. Repair
requires a new prospective source lock/output with all prior attempts and spend preserved.
