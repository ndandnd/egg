# Prospective master-trace snapshot repair — 27 September 2026

## Finding and scope

The first reuse-frontier attempt was frozen at
`7d3d76472ddf412e7af9e3b533d2d1fdcdac73ac` and saved under
`result/reuse_frontier/20260927-attempt1`. An independent auditor identified an
aliasing defect in its detailed trace: the driver appended the returned `rmp`
dictionary directly to `master_events`, assigned its `tangent_points` list to
local `tangents`, and could later append the current load to that same list
when continuing column generation. Consequently, an earlier recorded master
could appear to contain one tangent added **after** that master had been solved.
Its recorded objective and duals refer to the earlier solved constraint set.

This is an audit-trace snapshot defect. The finding does not by itself show
that the executed optimization, physical witnesses, reported bounds or call
counts are wrong. The independent audit must check those claims against the
actual solved tangent sets. Conversely, a reader must not assume the literal
legacy `tangent_points` arrays always describe the solve that produced the
associated objective and duals.

## Prospective repair

The sole experiment-code change is to append `copy.deepcopy(rmp)` to
`master_events`. The local `rmp` and `tangents` references remain unchanged.
Column admission, tangent addition, next-solve inputs, pricing calls, tolerances,
budgets, proposals, certificates and stopping rules are unchanged. The copied
trace still records all fields, including nested physical-replay evidence.
Snapshot copying can have a small logging-time cost in future executions;
there is no claim of timing identity.

A new two-iteration fake-oracle regression exercises the actual continuing
iteration branch. A replay-valid novel charging load causes the first iteration
to continue. The test verifies that the second master receives the newly added
tangent while the first logged master retains its original empty tangent set,
both in memory and in persisted JSON. It then mutates nested data in the fake
returned master and verifies that the logged snapshot is unaffected. The test
failed on the original implementation at the first snapshot assertion and
passes with this repair. All 43 focused frontier/prior-reuse tests pass. No
native optimizer or scientific experiment was run for this regression.

## Historical evidence and audit treatment

The frozen protocol and every original result remain unchanged. No scientific
rerun, retuning, result replacement or revised historical success label is part
of this repair. The original run remains 44 of 45 certified/reference-checked
comparison cells, with the prescribed unresolved-pricing failure preserved;
all 15 complete-structure reference cells finished.

The auditor reconstructs legacy solved tangent sets from the frozen control
flow and iteration/pricing records. In that version, `solve_rmp` copies its
incoming tangent list. After a returned master is logged, a continuing iteration
that takes the explicit `tangents.append(list(rmp['L']))` branch adds exactly
one final entry to that master's aliased list. The derived audit representation
must remove that post-solve entry only when the recorded execution path proves
this branch occurred. Certification, an error before append, and the pricing-gap
tightening branch do not imply such an addition. Blindly deleting the last
tangent from every record would be incorrect.

Any reconstruction belongs in a separately named derived audit artifact, with
its reasoning and association to the original record documented. It must not
rewrite the raw JSON. The audit should independently check objective/dual
consistency against the reconstructed solved set and distinguish any further
substantive finding from this snapshot defect. This note records the identified
caveat and prospective fix; it does not pre-empt the auditor's verdict.
