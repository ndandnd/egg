# Prospective V3 compact-hull extraction-policy integration

27 September 2026. **Pure integration patch only; no optimizer or public case
was run for this note.** The compact physical V3 formulation retains the V2
native matrix and aggregate-energy band, but changes charge extraction to
`native-pathflow-orphan-projection-v1`. Its sealed twenty-control attempt
reports 20/20; independent result audit is a separate gate. The earlier
compact-hull attempt and its raw evidence remain unchanged.

The shared hull coordinator previously labeled all columns, retained pools,
state identities and results with indexed
`native-roundoff-qualification-v2`, even when its compact oracle returned a
V3 plan. A different formulation ID kept some predecessor states apart but
did not make column provenance truthful. The opt-in hull path now receives
the compact extractor identity explicitly from `native_pathflow_hull`.
Every admitted compact pricing result and plan must carry that identity.
`native_hull` writes it on columns and results, validates it on replay and
retained import, and includes it in state digests. Missing or old tags fail
closed. The default indexed call still uses its original policy and exact
digest payload; no default algorithm, objective or budget changes.

The prospective attempt is exclusively
`result/native_pathflow_hull/20260927-attempt2` under protocol
`native-pathflow-hull-qualification-20260927-v3-orphan-projection`. It retains
the same eight source controls, analytical targets and CBC budgets: 16
pricing requests, 64 masters, 48 columns, 10 seconds per native phase,
60 seconds per state, 75 seconds per child and 650 seconds for the outer
supervisor, with the existing exact-polish limits. The source manifest now
names `src/egglab/native_hull.py` explicitly and includes the new policy
tests and this note. Frozen control manifests also name the V3 extraction
policy. The worker checks it before pricing and rejects a result or column
with the wrong policy.

Pure tests check unchanged indexed digests; V2-to-V3 state separation;
eight fake V3 control outputs with column and plan tags; later pricing calls
with missing or wrong policy; replay and retained-pool rejection in both
directions; and worker admission. The old compact fake fixture in
`src/tests/test_native_pathflow_hull.py` predates policy tags and belongs to
the physical attempt-3 source manifest. Do not edit that frozen dependency
while the physical result audit is in progress. Before V3 hull source freeze,
update that fixture prospectively to tag fake result and plan policies,
exclude the new policy field only in the unchanged-scientific-control
comparison, and include the policy in its fake frozen worker input and
result. Then rerun the full pure hull suite and obtain independent code
review. Source freeze, one bounded attempt and independent hull-result audit
remain manager-owned; this note does not authorize execution.
