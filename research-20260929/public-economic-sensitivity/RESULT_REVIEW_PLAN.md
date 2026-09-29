# Result review plan for the public economic sensitivity block

Run `summarize.py` only after the exclusive attempt has been collected and
sealed. It reads `frozen.json`, `summary.json` (or a partial postmortem),
supervisor/wrapper receipts and small per-stage receipts/assessments. It does
not read event logs or call a solver. It writes eight ordered rows to
`compactrows.json`, `compactrows.csv` and `TABLE.md`. Every declared planner,
cold hull and response stage remains present in the JSON even if unstarted,
ineligible, late, failed or incomplete. Stage-level paid child time, stop
reason and available scalar counters remain visible for those outcomes.

Admission has two gates. Every declared raw payload file must match the sealed
manifest's path, byte count and SHA-256, with no missing or additional files or
symlinks, and the global source seal, supervisor and wrapper must be sound;
then each stage needs matching on-time receipt, assessment and
declared case/market. A failed gate leaves native intervals blank while
retaining the observed stage status and cost. A completed cell reports raw
native physical and hull intervals. The combined native interval uses only
same-case evidence: raise the physical lower endpoint to the hull lower,
lower the hull upper endpoint to the physical upper, then compute
`[max(0,D_L-CH_U), D_U-CH_L]`. An incompatible pair is flagged, never
silently clamped. The fixed-price regret belongs to the named replayed
planner incumbent; its interval needs a matching planner plan hash.

The availability/cardinality analytical floor is a separate exact
stored-input ideal-model lower bound. It is *not* substituted into a native
solver certificate, a response optimum or an unconditional ideal gap.
The current curator does not verify ideal-model witness feasibility, so
`conditional_ideal_gap_upper_exact` and related ideal upper fields remain null.
The analytical floor is displayed separately. A future conditional ideal gap
upper bound would require verified ideal feasibility of the physical upper
witness; this package makes no such claim. An upper witness below the
analytical floor is reported as an inconsistency.

For interpretation, compare all eight declared scenarios without selecting
only positive-gap or certified cells. State which fee/curvature cells have a
positive native gap lower endpoint after outward rounding, which contain
zero, and which lack admitted evidence. Report own-incumbent regret separately
from gap and planner uncertainty. Compare depot variants as two formulations
of one 37-service public timetable, not independent samples or an estimated
fee crossover. If a cap binds, report stage stops and paid time rather than
calling the cell zero-gap. Keep exact-ideal claims, native tolerance-qualified
findings and conditional mixed bounds distinct. No speedup, prevalence or ML
claim follows from this single development block.

The script accepts the sealed attempt directory as its first argument and an
optional output directory as its second. No result values are filled into
this plan before collection.
