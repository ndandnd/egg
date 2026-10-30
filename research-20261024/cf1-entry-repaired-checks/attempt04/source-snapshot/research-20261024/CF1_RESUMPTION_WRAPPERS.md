# CF1 resumption wrapper bindings

`run_cf1_resumption_checks.py` reuses the reviewed
`run_cf1_entry_repaired_checks.py` supervision, ownership, cleanup, audit and
charge logic. Bindings change to revision5/policy `cf1-entry-repaired-v5`,
exclusive `cf1-entry-repaired-checks/attempt04`, and `attempt04-design`.
Its sole executed test is `src/tests/test_cf1_entry_repaired.py`; the eight
qualified test dependencies are hashed only. Current full
`q.campaign.sources()` remains required. Source work10s, outer12.5s,
inclusive15s and parent closure5s share the20s source endpoint
2446.723449631016s.

The driver requires `cf1-resumption/accepted-carry.json`: policy
`cf1-budget-resumption-v1`, phase `approved_historical_guard_adoption`, accepted
conservative guard2426.723449631016s, complete historical guard, unknown prior
actual CPU, unavailable actual CPU measurement and incomplete historical
accounting observations. Acceptance of this guard never converts it into an
actual historical CPU measurement. Its immutable inherited proof closure is
verified separately. The new `cf1-resumption/approval.json` binds the explicit
human reply and the same inspected50997/40 CF1 seed17/day/no-fault scope.

Both new runners enforce the approved process-local global3000s,
dispatch2820s/shutdown180s policy and the new175s package endpoint
2601.723449631016s. No new administration allowance or automatic retry is
introduced. The package retains analysis/finalization30s, supervision45s,
worker62.5s and owner entry7.5s. One thread and5GiB apply. Prior wrappers and
historical artifacts remain unchanged.

The source inventory binds both new runners up front, the three retained
monitor helpers, the original v5 source notes, all four
`CF1_RESUMPTION_{PROTOCOL,BINDINGS,REVIEW,WRAPPERS}.md` notes, the new approval
and accepted-carry roots, and prospective budget/command. The parent creates
that command manifest after static review. Its `command` is the absolute
two-element source-wrapper invocation; the actual pytest command and sole
test identities are recorded separately in the source attempt/result. The
manifest excludes only its own digest from its frozen source hashes; the
attempt inventory records that digest. Hashing occurs inside the actual
metered driver, never in a peer verification loop.

`run_cf1_resumption_freeze.py` adapts the reviewed
`run_cf1_small_approved_freeze.py` with revision5/package/path bindings. It
requires the new passing `attempt04` receipt, unchanged checked closure,
complete fresh source observations, and parent-reconciled
`cf1-entry-repaired-checks/attempt04-accounting.json`. That reconciliation must
retain the accepted guard and unknown historical actual CPU explicitly.
Its only child command is same-interpreter
`-m experiments.cf1_entry_repaired freeze`. The actual fresh native namespace
is `research-20261024/cf1-entry-repaired-v5`, with exclusive
`freeze-attempt01`; metadata work5s/outer7.5s/inclusive10s. The parent creates
its design and freeze command only after the fresh source gate passes.
The freezer verifies the new approval root and retains the actual reconciled
carry. Before dispatch it reserves metadata10 + worker62.5 + owner7.5 +
supervision45 + analysis/finalization30 within the package. No solver or
numerical task runs during metadata freeze.

The inherited helper bodies retain absolute monitor deadlines, maximum0.25s
complete-sample gaps, detached child registration, RSS/memory pressure checks,
bounded owned-group cleanup, leader reaping and failure evidence. The source
driver keeps its10s monitor and freezer its5s monitor. Fresh accounting remains
maximum(elapsed allocation, sampled tree CPU, reaped children CPU) plus
supervisor CPU; unknown fresh accounting or ownership cannot pass. Parent
reconciliation retains positive whole-wrapper/closure charges. All locked
sources stay immutable during a worker. No old test matrix, alpha-quality
campaign or prior numerical package is rerun by these bindings.

Preparation of these wrappers performs no imports, checks, hash loops, data
reads, metadata freeze, native dispatch, cluster activity or commits.
