# CF1 v5 canonical-path expectation: independent source review

24 October 2026. Static review of the diagnosed path assertion, narrow test and
checker changes, new path-check driver, protocol and wrapper note. No project
imports, tests, native work, research-data work, cluster work or commits were
performed. This review does not predict a passing invocation.

## Diagnosis and correction

The retained attempt02 trace reports one failure, 19 passing tests and 61 passing
subtests in0.76s. The failure compares the expected `/var/folders/...` owner-root
path with the actual `/private/var/folders/...` path. Production
`OwnerSupervisor.__init__` intentionally resolves its directory, and `run` builds
the root path from that resolved directory. The displayed argv suffix otherwise
matches, including root digest and nonce. Assertions following this equality
were not reached; their behavior remains unestablished by attempt02.

The test correction applies `.resolve()` only to its independently constructed
expected root path. Full argv equality remains intact. Production owner source,
canonicalization, capacity, ownership, time, permit, process-creation, funding
and charge guards remain unchanged. The previously corrected capacity8 fake OS
and handwritten root bindings remain in place.

Positive source-receipt fixtures identify attempt03; mismatched IDs identify the
closed attempt02. The old attempt01 directory remains a rejection case. The
production wrapper has only the fresh source-check namespace, required attempt
and result IDs, and future `attempt03-accounting.json` input path changes. Exact
namespace equality rejects both old source-check directories. Owner lifecycle
paths named `entry-owner-attempt01` remain distinct and unchanged.

## Closed predecessor and retained bounds

Selected authoritative account scalars confirm carry1538.9434496310162,
`failed_v5_capacity_source_check`, `check_passed=false`, complete accounting and
owned groups absent/reaped. The closed current charge4.723806792007565 preserves
internal2.888311333676517, measured preservation1.0854954583310485 and closure0.75.
The parent reports all1111 retained proof hashes verified. Attempts01/02, their
source snapshots, logs, commands, designs and spending remain preserved; no
failure is relabeled as passing qualification or credited back.

The new driver explicitly binds that failed closed predecessor and its result's
unchanged sources, absent groups, reaped leader and empty survivor list. It
verifies the inherited proof closure before launching. Its exact new directory
is attempt03, created exclusively, with separate attempt03-design metadata and
future attempt03-accounting.json. It offers no automatic retry or resume.

Work4.5, outer6, inclusive6 and parent closure2 agree across driver, protocol and
wrapper. Carry+6+2 ends1546.9434496310162, below the retained capacity-phase
end1547.2196428390087, original source-phase end1547.8351450899538 and campaign
end1702.8351450899538. The new8s cap stays inside those existing bounds. ADMIN0,
global1920/1740/180, thread environment1 and5GiB remain unchanged. Actual and
conservative internal, external, preservation and closure charges must fit all
ends; no new allocation or credit is inferred.

The shared sample helper uses its anchor only for its `anchor+10` deadline.
The new caller's `anchor-5.5` therefore enforces actual anchor+4.5 for that sample.
Attempt, elapsed/CPU accounting, ownership and cleanup anchors remain actual;
cleanup ends at actual anchor+6. The unchanged2.5s active finalization allowance
can stop work earlier than the wall cap. Monitor, ownership, cleanup/reaping,
output-audit and conservative accounting bodies remain inherited. No native
clock changes.

Only `src/tests/test_cf1_entry_repaired.py` executes. Eight qualified historical
test files remain hash-only dependencies, with the full current source closure
and old/new source notes bound. No historical test matrix is repeated.

## Decision and limits

No static source blocker was found for this separately diagnosed manual source
decision. Execution is not cleared by this note alone: the actual new manifest,
exact command, complete source/evidence hashes, all cap fields and absent
attempt03 directory must be checked before the sole invocation. Preserve every
failure and stop on failure; there is no automatic rerun.

A source pass establishes only behavior actually exercised. It cannot establish
real ownership/timing, real lock qualification, native entry, CF1 mechanics,
global certification or later-phase permission. The still-unreached assertions
are not assumed to pass.
