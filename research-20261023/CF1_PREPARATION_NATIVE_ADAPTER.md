# Single repaired-CF1 native policy adapter

24 October 2026. NEW `experiments.cf1_preparation_preflight` supplies explicit
freeze/run/analyze/worker CLI commands under policy `cf1-preparation-native-v2`.
This is a separately prospectively budgeted single-CF1 preflight, not an automatic
retry, a fresh timetable or comparative-quality evidence. No native execution,
runtime import, test, fixture/model access or cluster job was performed here.

`task_matrix(cases=None)` contains exactly CF1, inspected base50999/80,
seed17/day,60 seconds, fault null and protocol_revision2. Its canonical hash
therefore differs from both v1 task IDs. Any supplied case list must contain only
the same engineering identity/scale. Existing source/asset/environment/library,
fixture/market, exact-selector, check and accounting verification is delegated.

`revision2()` holds the reviewed adapter's original serialization lock while
installing policy-only globals. An owner-thread single-delegate lock permits the
unchanged bound60 body to run once inside the configured scope, rejects nesting
and other threads, and keeps unconfigured old use from racing global changes.
Finally restores every adapter/worker setting and original lock, even on error
or interruption. Worker policy and task_matrix are configured too; its lazy
comparison_native_preflight.verify_lock import sees the configured adapter.
The new checked-source guard additionally requires the new module/test hashes.

Only default-preserving parameterization was made in comparison_native_preflight:
ANALYSIS_FINAL_RESERVE_S defaults5, SUPERVISION_RESERVE_S defaults40 and
WORKER_ARGV_PREFIX defaults the v1 worker module. Every old analysis5 use is now
that default constant, including freeze budget validation/admission, freeze
receipt admission, active cleanup reserve and prelaunch gate; both old40 uses
are the supervision constant. V1 behavior is unchanged outside revision2.

Revision2 sets combined analysis/finalization reserve30 (analysis20/final10),
supervision reserve45 and worker prefix
`-m experiments.cf1_preparation_preflight worker`. Endpoint60, supervisor exit/
drain stop61 and outer cleanup62.5 stay unchanged. Package start is
1416.3727097992353, additional hard cap165 and absolute end1581.3727097992353;
global1800/1620/180 policy and ADMIN0 remain unchanged. Before worker creation,
actual carry/charges must fit62.5+45+30. During work, the inherited gate preserves
2.5 cleanup plus30 combined reserve. All resumed/worker/monitor/supervisor costs
retain the original deduplication and no-double-charge rules.

Freeze/run/analyze delegate reviewed machinery; freeze normalizes its cosmetic
task count to1, run already derives the frozen count, and analyze normalizes only
the report's descriptive scope before the exclusive durable write. Every
independent capture/inventory/replay/exact-bill/bounds/start-processing/ACK/
ownership check remains. Freeze receipt phase remains comparison_native_freeze
with the NEW policy. charged_cpu_s is TOTAL including supervisor, not allocation
plus a second supervisor addition. An external passing source-bound freeze
receipt remains mandatory before native launch.

A directly diagnosed companion worker change hoists mapped_set once per
verify_capture_reference call. Uniqueness and unmapped-continuous membership
reuse it instead of rebuilding set(mapped) for every variable. All signatures,
checks, errors, capture parsing/hash/identity/round/phase validation and duplicate
verification calls remain. This removes the same repeated-set complexity that
previously made preparation expensive; it does not weaken evidence or add a
performance/native success claim.

The focused configuration-only gate is new test_cf1_preparation_preflight.py;
older test dependencies may be hashed transparently without being executed.
Parent alone freezes exact sources/protocol/resources and decides whether to
perform its one check, external freeze and separate single native cohort. Failure
is preserved and does not trigger an automatic retry. Passing this source gate
alone does not qualify actual CF1 timing, feasibility or native starts.
