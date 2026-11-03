# CF1 v5 path-alias source wrapper bindings

`run_cf1_entry_repaired_path_checks.py` adapts the closed capacity source driver
by changing only predecessor/design/source identities and deadline bindings.
The capacity driver, notes, attempt02, snapshots, design files and consolidated
account remain immutable. This is one explicitly diagnosed source qualification
under the current wake's existing 13 s cap and the original 20 s source cap;
it creates no new allowance and provides no automatic retry.

The authoritative predecessor is
`cf1-entry-repaired-checks/attempt02-accounting.json`, carrying
1538.9434496310162. Preflight requires policy `cf1-entry-repaired-v5`, phase
`failed_v5_capacity_source_check`, `check_passed=false`, complete accounting,
owned groups absent and reaped, and false native dispatch, metadata freeze,
research-data analysis, original-v4 retry and automatic retry flags. Its full
inherited proof closure is hash verified. The bound attempt02/result.json must
retain attempt02/revision 5/policy, `passed=false`, `source_changes=[]`, a reaped
leader, absent owned groups and no surviving PGIDs. Attempt02 remains a closed
failure: one macOS temporary-path alias assertion failed, with 19 tests and
61 subtests passing; PGID 80495 was absent and reaped. No exception is treated as
a pass and no native permission follows from its partial test coverage.

The new 8 s phase ends at 1546.9434496310162: ADMIN 0, work 4.5, outer 6, inclusive 6,
parent finalization/closure 2. It remains inside the earlier capacity phase's hard
end 1547.2196428390087, original source-phase hard end 1547.8351450899538 and
prospective campaign end 1702.8351450899538. Those three inherited ends are
required in both the predecessor account and prospective design; the new phase
end is required in the prospective design. Global 1920/1740/180, one thread and
5 GiB remain unchanged. Parent reconciliation must preserve the 2 s closure reserve
and all three source-phase bounds.

The sole shared-monitor adaptation is
`reviewed.sample_owned(proc, groups, registry, anchor-5.5, last_completed)`.
The retained helper uses its anchor solely in the sample deadline `anchor+10.`;
the adapter therefore yields the real parent anchor+4.5. Real attempt, elapsed,
CPU and ownership anchors remain unchanged. Initial monitoring and launch/work
checks use anchor+4.5; cleanup uses anchor+6. Inclusive checks use carry+6 with
parent closure 2. The retained 2.5 s active finalization allowance and all complete
sample-gap, owned-row/registry, RSS/CPU, memory, cleanup/reaping, output-audit and
conservative charge mathematics remain unchanged. No historical helper is
edited or copied.

The exact new attempt is `cf1-entry-repaired-checks/attempt03`, created
exclusively at invocation. Revision 5/policy `cf1-entry-repaired-v5`, the sole
`src/tests/test_cf1_entry_repaired.py` selection, eight hash-only qualified test
dependencies and complete current `q.campaign.sources()` remain unchanged. All
old source and capacity notes remain in the source inventory; the four new
`CF1_V5_PATH_ALIAS_PROTOCOL.md`, `CF1_V5_PATH_ALIAS_FIX.md`,
`CF1_V5_PATH_ALIAS_REVIEW.md` and this wrapper note join them with the new driver.

Only `cf1-entry-repaired-checks/attempt03-design/prospective-budget.json` and
`cf1-entry-repaired-checks/attempt03-design/command.json` supply the new
prospective design. The parent creates them after review. The command binds
every inventory byte except its own digest, which is recorded by the attempt.
No old root or attempt02 prospective file is reused as the new design.

The parent owns new whole-wrapper output/time logs under attempt03-design and
future consolidated `cf1-entry-repaired-checks/attempt03-accounting.json`, without
overwriting closed receipts. Source preparation creates no attempt directory or
prospective manifest. Failed, interrupted or incomplete work remains charged;
this gate grants no native, real metadata-freeze, research-data or cluster phase.
