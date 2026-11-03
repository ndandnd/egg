# Interpretation review of the single frozen cycle

Verdict: **The saved cycle qualifies the exact implementation comparison under
the declared synthetic model. It does not establish a complete publishable
paper, operational prevalence, or external replication.**

Scope: selective read-only inspection of cycle01/results.json, its source
manifest and owner/worker receipts, owner-time.txt, and the inline table, together
with the prior source/proof review recorded in REVIEW.md. No test, native
backend, replay, import, hash recomputation, or export was performed for this
review. Only this interpretation document was written.

## Saved evidence and consistency

The manifest identifies source revision
2407a28f7773ede756a9b17d87d60ca59163a3e5, seven consumed source/configuration
files, Python 3.12.2, and stdlib-only execution. These are recorded provenance,
not independently recomputed hashes. The owner receipt records child 65741,
exit zero, reaped true, no failure, and PASS. All 20 assigned cases were
attempted and passed, including two infeasible cases; no case was unattempted
and failures is empty. Twelve negative controls were rejected, separately from
the successful nominal arithmetic smoke check.

The saved nominal case gives D=97, CH=7591/80, and own-price regret 13. At
K=30, fee=5, both physical partitions attain D=95, while their regrets are
15 and 5 respectively. This is a substantive reason to retain every planner
optimum rather than report an arbitrary selected optimum. Zero-fee cases retain
the full flat two-bus response interval, and equality-boundary cases retain
cross-partition response ties.

The external POSIX meter records real 0.74 seconds, user 0.25, sys 0.19
(displayed CPU 0.44 seconds). Owner inclusive observed CPU is 0.440232 seconds;
worker inclusive observed CPU is 0.35183 seconds. Worker observed peak RSS is
23,052,288 bytes. These are consistent with the declared acceptance allowances
and positive receipt gates. They are observations from one execution, not
performance estimates or hard aggregate OS containment. Nested CPU receipts
must not be summed with the external whole-command charge.

## What is established and what is not

The continuous fee/capacity theorem follows from the reviewed physical
projection, convex-hull geometry and strict-convexity proof. The 20 exact cases
qualify implementation at declared boundaries and interiors; they do not prove
a continuum theorem by sampling. The physical-polytope reference is independently
formulated relative to the closed-form candidate, and both agreed using exact
rational arithmetic. They share the declared physical assumptions, language,
arithmetic library and comparison harness. Thus this is an exact internal
cross-check between independently formulated methods, not external replication
by an independent research group or operational validation.

The scope remains one whole-fleet owner evaluating deviations at a fixed posted
own-load marginal tariff. The conclusions do not establish strategic behavior
under endogenous tariff resets, an implemented payment institution, support
for independent owners without reserved rights, or prevalence in public
timetables. The full fee/capacity characterization strengthens the analytical
paper, but significance, relationship to existing theory, practical magnitude
and public optimal-fleet support remain unresolved. This cycle alone is not
enough for the paper.

## Preserved presentation defect

The raw inline TABLE.md contains unescaped A|B labels inside Markdown table
cells, so those rows can render with spurious column boundaries. This is a
presentation defect, not a discrepancy in the JSON scientific data. Preserve
the frozen source and raw output; results.json remains authoritative. Record
escaping pipe characters as a next-version formatting correction. No rerun,
silent raw-table edit or numerical promotion is warranted by this defect.

No new mathematical or numerical validity blocker was identified in the saved
evidence reviewed here. This conclusion has the stated model and review limits.
