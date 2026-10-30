# One source-bound admission-reserve regression check

24 October2026. Prospective implementation/check package, not execution evidence. Parent owns one deliberate check in exclusive `admission-reserve-checks/attempt01`, source freeze, receipt review and subsequent accounting. No automatic retry, fixture generation or native qualification is authorized by this document.

Carry exactly **912.8922626277902 charged seconds** from `recovery-phase1-v5/accounting.json`, retaining all failed revisions, check/freeze charges, monitor/supervisor spend and final analysis. **ADMIN=0**: the existing single20s allowance is already carried. Preserve1800s total ceiling,1620s dispatch stop,180s shutdown reserve, one numerical-library thread and5GiB owned-tree RSS.

## Tested allocation

Hard upper endpoints remain anchored12/15/24/27/30s, outer allocation32.5s. Planned integer search ends10/22s; planner handoffs13/25s leave2s for independent physical admission before15/27s. Earlier handoff rejection applies even to no-plan/bound-only returns. Exact handoff is allowed; post-lift/copy/durable work after15/27 is rejected. A first fallback is published only after successful timely save; rejected durable artifacts remain evidence. Earlier admitted fallback remains intact through later failed/late candidate work. Typed gate evidence distinguishes effective search cutoff from original integer upper cap. The unchanged eight tasks are ordered80 trips first, with unchanged task identities.

The new check launcher is a policy-only copy of `run_freeze_v2_checks.py`: supervision helpers remain unchanged. Changes are prior carry/path, namespace, eight-module inventory and descriptive fields. The coordinator module is included because its runtime changed. Retain original helper tests without parametrizing them over every launcher copy.

## Exactly191 expected cases

```sh
.venv-local/bin/python -m pytest -q \
  src/tests/test_recovery_qualification.py \
  src/tests/test_recovery_supervision_repair.py \
  src/tests/test_recovery_integer_cutoff.py \
  src/tests/test_recovery_admission_capture.py \
  src/tests/test_check_supervision_v2.py \
  src/tests/test_recovery_freeze_v2.py \
  src/tests/test_recovery_coordinator.py \
  src/tests/test_recovery_admission_reserve.py
```

Static case counts are41+13+33+26+12+11+34+21=191. The added reserve module uses symbolic cases, fake clocks/planners/lifts/storage and guarded native imports; no timetable generation or numerical model is involved. Existing bound ownership/watchdog test remains the only real process integration test; every new-session group must be immediately registered, flushed and fsynced for parent cleanup.

Before Popen freeze transitive egglab/experiments sources, all eight tests, the launcher and reviewed helper/dependency closure, implementation/review, this protocol, V6 protocol, approval and command metadata. Verify inherited v5 evidence hashes rather than replacing previous source evidence. The command JSON omits its own hash; the actual attempt hashes it too. Parent environment sets numerical-library threads to1 and disables bytecode writes.

Retain30s work/32.5s absolute outer cleanup,0.05s target cadence and strict0.25s completed-sample policy. Shared query deadlines, permission-denied unknown ownership, primary/secondary error retention and missing-observation failure remain unchanged. No changed assertion/source during the attempt. Passing requires successful exit, complete accounting, unchanged hashes, all owned groups confirmed absent and leader reaped. Pytest success alone is insufficient.

Charge max(elapsed allocation, sampled owned-tree CPU, total reaped-child CPU) plus supervisor CPU. Monitor-child diagnostics are already included in total children and must not be added again. The complete pending allocation plus reserve fits current cumulative policy; actual costs remain additional. One failed/incomplete check stops this package and survives in evidence. Passing is only a software regression gate; parent separately reviews fresh freeze and any deliberate V6 native task/environment lock. No ML or performance claim follows.
