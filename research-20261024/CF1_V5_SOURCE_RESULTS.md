# Fresh CF1 source gate failed in its test double

24 October 2026. The sole frozen cf1-entry-repaired-checks/attempt01 invocation
exited1:26 failures,16 passing tests and36 passing subtests in1.46s. Source review
had cleared this invocation prospectively; it did not establish execution success.
The failed receipt, logs, exact sources and all spending are retained. No retry,
source patch, real metadata freeze, controller or numerical worker followed.

All26 retained error lines report the same AttributeError: the inert test OS
object lacks cpu_count, which the production EntryClient identity check requires.
The handwritten root also lacks its matching capacity_cpu_count. The failure
occurs while constructing the harness before the intended owner scenarios,
including the fake OwnerSupervisor.run call. Read CF1_V5_SOURCE_FAILURE_DIAGNOSIS.md
for exact locations and the narrow proposed correction. This is observed evidence
of a test-double defect, not proof that all remaining code would pass once fixed.
Do not weaken the production capacity/owner checks or claim their scenarios were
exercised. No CF1, replay, timing, native-start, model-quality or economic result.

Supervision completed normally: PGID71595 absent and reaped, no surviving groups,
changed sources, stderr, secondary errors or unresolved accounting observations.
The primary failure is pytest_exit. Historical tests were hash dependencies only;
the single new fake-execution file was selected. No fixture/model/sealed/private
data or cluster work occurred. The historical failed v4 remains immutable.

Original closed source account: cf1-entry-repaired-checks/accounting.json, explicitly
check_passed=false and phase failed_v5_source_check. Carry1527.8351450899538s
plus internal3.6579306243831518s, measured source preservation1.2265671246716976s
and conservative materialization closure0.5s equals1533.2196428390087s. Whole
wrapper2.91s wall/3.47s CPU plus0.02s precision was below the internal charge;
no positive external top-up or subtraction. All charges/failures remain in the
1088-path proof closure.187 bound source entries are preserved as174 new exact
snapshots and13 reused prior snapshots; no new mutable source proof roots.
Independent compact receipt/proof verification found no mismatches.

The latest authoritative root is accounting-final.json. It preserves that original
account and adds a nonrefundable conservative1s for independent proof verification
and postcheck metadata/handoff finalization, recorded in postcheck-finalization.json.
The final total is1534.2196428390087s with1090 proof paths. No charge is removed,
old account overwritten, new check invoked or administration credit introduced.

Source-phase spend is6.38449774905485s of20s, below its original absolute end
1547.8351450899538. The prospective175s package end1702.8351450899538 and global
1920/1740/shutdown180 remain unchanged; ADMIN0. No later phase is cleared.

Next bounded work: correct only the diagnosed fake OS/root contract, update a
fresh source-attempt identity consistently in checker/test/driver and prospectively
freeze that affected check. Do not reuse or overwrite attempt01 or its manifest.
A proposed13s follow-up from the current carry would end1547.2196428390087, inside
the original20s source-phase ceiling; it still needs its own reviewed clocks,
command and hashes before execution. This arithmetic is not a launch manifest.
Do not reset the phase ledger, repeat qualified historical matrices, assume the
unreached owner paths pass, or use this failed receipt for native clearance.
