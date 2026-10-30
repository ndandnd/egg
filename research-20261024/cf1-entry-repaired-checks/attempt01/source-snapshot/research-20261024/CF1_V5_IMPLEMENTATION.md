# CF1 v5 serialized wrapper implementation

24 October 2026. Source implementation only. This note records no import,
test execution, source-check result, metadata freeze, research-data access,
numerical call, controller/worker launch, or native clearance.

`src/experiments/cf1_entry_repaired.py` supplies the fresh singleton revision5
policy and the prospective 1527.8351450899538 + 175 = 1702.8351450899538 package.
It retains the 1920/1740/180 global policy, 30-second analysis/final reserve,
45-second supervision reservation, 60/61/62.5 clocks and inherited one-thread,
5-GiB native policy. Historical v3/v4 sources and clearance bindings are unchanged.

The outer configuration acquires its own lock and the original v4 lock, saves
each v4 binding before mutation, installs an owner-thread delegate and restores
all bindings on exit. The unchanged v4 context supplies the inherited adapter,
worker and ACK observer. Its worker argv is overridden inside that context so
the only prospective child module is `experiments.cf1_entry_repaired`.
Analysis calls the unchanged v4 analyzer under only the outer configuration,
allowing the analyzer to enter its own original context and retain its original
ACK transport checks and exclusive observation publication.

The source consumer accepts only
`research-20261024/cf1-entry-repaired-checks/attempt01`, revision5/attempt01 and
the single `test_cf1_entry_repaired.py` command in both attempt and result.
It retains the inherited v3 receipt/dependency chain, binds every current
`q.campaign.sources()` entry and hashes the eight qualified historical test
dependencies. It never executes those historical tests.

`run_prepared(args, *, roots, owner_gate)` requires independent preparation
roots and an external owner implementing `entry_scope`, `precharge` and
`launch_guard`. It prepares inside a temporary `adapter.bound60()`, validates
that the owner appended exactly one durable, nonrefundable 7.5-second whole-entry
charge, verifies real resume consumes exactly postfreeze total + 7.5, exits that
temporary context and only then invokes `adapter.run`. A scoped adapter-launch
wrapper requires one task and the owner gate. Funding is checked before the
owner permit and again at final Popen using current wrapper CPU and monitor CPU,
without crediting their overlap with the conservative entry charge. The final
check requires the unchanged prelaunch prefix accepted by real resume plus the
original sole launch-intent tail, whose hash chain is revalidated. An incomplete
launch cannot be resumed through the historical consumer and is never retried.

All entrypoint paths use the fixed fresh design/lock/check/freeze/account/run/
report layout. CLI run additionally requires explicit independent hashes,
cumulative total, inherited owner FD, owner-root hash and nonce, then constructs
the real owner client. Missing roots/control have no fallback. Actual frozen
source gates, independently rooted receipts, owner evidence and inherited lock
consumers remain required before a future phase can proceed. This implementation
does not create those inputs or authorize their execution.

The owning-supervisor implementation and sole combined fake-execution test are
separate work products; no qualification claim follows from this wrapper note.
