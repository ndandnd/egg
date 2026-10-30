# Native-v7: engineering qualification passed

24 October 2026. Bounded read-only interpretation of V7 gates and terminal
result/completion/supervisor scalars. No raw capture variables, trained assets or
sealed data were inspected; no runtime, solver, test or retry was executed. Parent
owns final accounting and archival. This note changes no source or old result.

## What passed

V7 completed all eight planned tasks and its analyzer reports `passed=true`,
with no unresolved rows. Both40 and80 independently satisfy normal native-start
processing and durable-fallback setter-fault coverage. Counts show two accepted,
processed partial starts, two exercised setter faults, eight retained fallbacks,
and zero invalid witnesses, mapping violations, bound-scope violations or censored
outputs. All task issue/failure lists are empty. This is an engineering pass for
the prospectively frozen anytime policy, not a retroactive pass for V1–V6.

## The80-trip target overruns genuinely met admission deadlines

Recovery task `85710efee4db820ff4bc` returned after both13/25 planner targets.
Those targets remain native/planner budgets; the hard independent-admission
endpoints are15/27. Its recorded elapsed timeline is:

| Event | Seconds after supervisor anchor |
| --- | ---: |
| Prefix planner return | 13.333859583 |
| Independent prefix lift entry / exit | 13.333887375 /13.634060333 |
| First fallback durably saved and admitted | 13.659089792 |
| Full planner dispatch | 13.659788250 |
| Full planner return | 26.267178333 |
| Independent full-candidate lift entry / exit | 26.267217000 /26.671340167 |
| Pre-materialization endpoint | 26.867918417 |
| Result fsync/output endpoint | 27.522493999 |

The prefix's required durable admission finished before15. Full admission began
with0.732783s remaining before27 and completed its independent lift with0.328660s
remaining. Witness-copy and full-bound admission checks occur subsequently in
the coordinator, before the recorded26.867918417 pre-materialization endpoint.
They therefore completed before27 as well. No hard-cutoff failure was suppressed.

The selected full witness replaced the earlier fallback only after successful
independent admission. Its provenance identifies the full case as both source
and target; its exact bill equals its source replay bill at the target market.
The fallback provenance identifies the restricted source and the same full
target/market. Both exact bills match the gate rows. The first prefix fallback
remains separately persisted; an improved selected witness is then persisted in
the final artifacts, by the separate30-second output deadline. A second first-
fallback save is not required by this policy.

This evidence is stronger than merely observing27.522494<30: actual independent
admission finished within15/27. It demonstrates success on this execution, not a
guaranteed two-second reserve or a worst-case latency bound. In V6 the same kind
of late planner return was forbidden by its strict handoff contract; V7 cannot
alter that historical failure.

## Bills, fleets and bound quality

Displayed bills and lower bounds are rounded. Decisions and analyzer comparisons
use the stored exact rational `true_bill_exact` and independent replay, not these
rounded values. Fleet counts are lengths of the saved selected vehicle lists.

| Trips | Arm | Selected bill | Vehicles | Global lower bound | Output seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| 80 | Static restricted | 3642.529856 | 27 | none | 25.318093 |
| 80 | Recovery | 3628.913816 | 27 | −1e100 | 27.522494 |
| 80 | Cold full | 3386.201202 | 24 | 199.999999 | 26.916834 |
| 80 | Injected setter fault | 3642.529856 | 27 | none | 16.101316 |
| 40 | Static restricted | 658.684691 | 4 | none | 22.360253 |
| 40 | Recovery | 658.684691 | 4 | 562.536728 | 22.940247 |
| 40 | Cold full | 658.706825 | 4 | 563.806375 | 22.913122 |
| 40 | Injected setter fault | 658.684691 | 4 | none | 10.775487 |

The80 recovery selected bill improves on its own3642.5298555555555 prefix
fallback by13.61603950617291, with the same27 vehicles. But the cold full solve
is cheaper still and uses24 vehicles. The40 recovery retains its original exact
fallback bill; its small advantage over this cold outcome is not an improvement
caused by the recovery stage. Different fleet counts also prevent reading total
bill differences as charging-efficiency differences alone.

Three claims must stay separate:

- Independent lift/replay plus exact billing validates each admitted witness
  under the declared routing, battery and charger model. The analyzer repeats
  this check; it is not merely a native incumbent/status assertion.
- Attributable native logs and binary inventories establish that normal partial
  starts were submitted, processed and accepted at each size. Acceptance alone
  proves neither optimality nor benefit over a cold solve. The injected-fault
  paths separately demonstrate retention of their timely valid fallbacks.
- Promoted lower bounds have `full_unrestricted_mip` provenance. Restricted
  prefix bounds and fixed-topology completion bounds are not global bounds.
  The80 recovery's−1e100 bound is practically uninformative; the other reported
  bounds leave gaps. No task has `certified` status, so this pass establishes no
  optimality or small-gap result.

## Scientific interpretation

The ranking was nonlearned; no learned ranking inference occurred. These are
eight engineering tasks on only two synthetic base timetables—one per size—with
seed17 and one declared tariff/resource policy. They establish the tested
clock, replay, mapping, start-processing and fallback paths. They do not establish
ML value, a general recovery advantage, statistical significance or generalization.
The cheaper80 cold outcome is direct evidence against claiming recovery dominance
from this qualification. Any later method comparison needs its own frozen study
design and remaining-budget decision; this pass does not authorize extra cases,
seeds, native retries or a comparison campaign.
