# Prospective compact path-flow attempt 3: audited orphan projection

27 September 2026. Protocol
`native-pathflow-qualification-20260927-v3-orphan-projection` is **unexecuted**.
The first energy-band attempt at frozen `66b7054510a8b90471d6abe07d32a9f7f509182d`
remains failed 19/20, including its complete immutable
`result/native_pathflow/20260927-attempt2` archive. This proposed run needs an
independent implementation preflight, published source freeze and a new
exclusive `result/native_pathflow/20260927-attempt3` directory. No prior result
is upgraded or overwritten.

The native constraint matrix and two aggregate-energy rows retain the V2
energy-band design. The compact post-solve extractor alone has prospective
identity `native-pathflow-orphan-projection-v1`, carried by formulation/oracle
tag `egg-native-pathflow-v3-energy-band-orphan-projection`. The shared indexed
negative normalizer remains `native-roundoff-qualification-v2` and its
behavior is unchanged. The new extractor may zero strictly positive charge
only on an unselected movement within one exact incumbent-wide 1e-8 kWh
budget. It preserves selected positive charge, reports all raw/projected
values and per-period native load, raw charge sum, materialized load and replay
load, and requires the original independent physical replay and objective/
bound guards. See `NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_DESIGN_20260927.md`
and its independent design review for the correction equation and failure
conditions.

## Frozen question and controls

Run the exact same twenty synthetic cases, targets and ordering as attempt2:
sixteen expected numerical certificates and four expected infeasibilities.
The independent preflight must compare serialized input/case identities and
target fields against attempt2's `frozen.json` and ensure no scientific input,
budget, backend or target has drifted. The failed joint-planner cell remains a
normal attempted control, not a special solver seed or bespoke acceptance
case. Keep CBC, one thread, ten seconds per native phase, 45-second routine
wall cap, 60-second subprocess hard cap, at most 48 planner rounds, 1e-4
certificate width and 2e-4 analytical-target agreement. No warm start,
retry, tuning or extra qualification cell is permitted in attempt3.

Before running, pure/fake tests must cover cumulative positive orphan,
negative plus orphan combined budget, exact boundary, native load-row residual
versus raw charge sum, materialized/replay load residuals, interval and session
capacity accounting, unchanged retention of tiny positive selected charge,
invalid keys and unavailable visits, replay failure, linear/tangent/true-cost
objective deltas and compact-hull oracle identity. Imports of CBC/Gurobi are
unnecessary for these checks. Independently review code and pure-test behavior
at the frozen source hashes; this design review alone is not implementation
preflight approval.

## Execution and result admission

After the root researcher publishes the reviewed source freeze, invoke the
existing worker/supervisor runner once with `--output
result/native_pathflow/20260927-attempt3`, the actual commit as
`--freeze-label`, and `--backend CBC`. The runner hashes all source, tests,
energy-band proof, extraction design/review and this protocol. Require an
exclusive absent output directory; if a controller or worker fails, retain
its raw prefix and continue only the other predefined cells as the runner
already specifies. Manifest all original files after completion. Do not
modify any raw numerical file in review.

The independent no-author-import result audit must reconstruct every native
row and objective/bound, the selected path graph, every charge correction and
exact whole-incumbent budget, native `L` versus raw `R`, physical/replay loads,
serial sessions and unchanged physical replay. It must reject deliberately
corrupted copies. A native `OPTIMAL` label does not bypass extraction. A
passing 20/20 attempt qualifies only the declared synthetic compact policy;
floating physical witnesses and guarded solver bounds remain numerical and
tolerance-conditional. An incomplete or failed attempt remains failed and
blocks the eight compact-hull V2 controls and public pilot 2. Those later
campaigns require their own versioned source/protocol, new oracle/state
identity, independent review and separate immutable attempts.
