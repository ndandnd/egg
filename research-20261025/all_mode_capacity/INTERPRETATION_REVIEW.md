# Interpretation review — all-declared-mode capacity outer cuts

Reviewed only `stdout.txt` and `attempt01/receipt.json`. No earlier inputs,
specifications, TRAIN data, native outputs, plans, source imports, numerical
recalculation, scripts or hashes were used. This is interpretation of the closed
diagnostic, not a new source proof or experiment.

All eight planned group/resource controls are available; none is unavailable.
The body and receipt are complete, with no failures or structural findings.
Exactly two controls violate an ideal outer necessary condition:

| Control | Fixed fleet | Controlling term | Exact capacity-minus-required margin (kWh) |
|---|---:|---|---|
| 10009, 45 kW | 4 | Pre-opening SOC requirement | −5910524150961036721/64851834634135144 |
| 10005, 45 kW | 3 | Total energy minus post-opening capacity | −481614944151000139/16212958658533786 |

The parent-supplied approximate shortfalls are 91.1 and 29.7 kWh respectively;
the exact represented fractions above remain primary. No new conversion or
calculation was performed here. All four 90-kW controls and both resource levels of
10001 and 10006 have nonnegative margins. There is no known admitted-control
contradiction; this review did not independently reopen or revalidate those
witnesses. The eight paired controls still describe **four exposed development
groups**, not eight independent population observations.

## Why this is stronger than a reference-route cut

The diagnostic allows every declared depot mode when forming its preterminal
window union. Its movement-energy lower bound is the larger of incoming and
outgoing partition minima, not their sum. Independent minima need not form one
consistent route set: that makes the demand bound optimistic, not a constructed
feasible plan. Likewise, the all-mode window union can offer charging access
that no single path cover simultaneously uses. These are outer relaxations.
If even their optimistic capacity is below a necessary demand lower bound,
changing the reference topology within the declared universe cannot cure that
ideal-model obstruction at the same fixed fleet N.

For **10009/45**, the preterminal union spans 399 minutes with capacity 1197/4
kWh. The all-mode-early condition is true, so the full declared-consumption lower
bound contributes to the pre-opening SOC requirement after aggregate usable
battery is accounted for. That requirement exceeds the optimistic preterminal
capacity. The separate total-energy/post-opening term passes; merely checking
total charging energy would miss this exclusion. All necessary early energy
must be available before the later terminal charging opportunity can help.

For **10005/45**, the all-mode union spans 395 minutes with capacity 1185/4 kWh.
The SOC term passes, but the minimum total grid energy still required after
allowing 540 kWh of post-opening charging exceeds preterminal capacity. Here
the overall energy-plus-time capacity restriction, rather than the stronger
pre-opening reserve requirement, determines the negative combined margin.
The two controls therefore have different limiting necessary terms.

## Exact claim and limits

Conditional on the inherited physical assumptions, declared movement universe,
complete fixed-N path-cover interpretation and represented parameters, these
two negative margins exclude a feasible solution of the corresponding **ideal
declared-universe fixed-fleet problem**. This is no longer merely rejection of
one timed witness or one selected topology. The fixed fleets are N=4 and N=3;
the result does not settle a different fleet, resources, movement universe,
charging technology or unrestricted electric-vehicle scheduling problem.

The conditions include full initial and terminal batteries, reserve at opening,
nonnegative consumption, constant efficiency, no unmodeled consumption,
grid-to-battery-only charging and no terminal charging before 1080. Their source
and case provenance are inherited; this projection does not independently
re-establish them. All records report the all-declared-consumption-early
condition true. The exact rational arithmetic describes represented model
quantities; no reporting epsilon becomes a floating native feasibility guard.

The earlier native `INF_OR_UNBD` classifications remain unchanged. An analytical
conditional ideal exclusion is separate evidence, not a retrospective native
`INFEASIBLE` status, a native-precision certificate, or evidence about numerical
unboundedness. Nonnegative controls remain unresolved by these cuts alone:
they do not construct routes, allocate charging, establish SOC-prefix/headroom
consistency, prove sufficiency or optimize cost. In particular, the available
10006/45 control is not excluded, which is consistent with a known admitted
adaptive witness; the cut is not the reason that witness is feasible.

## Scientific disposition

The diagnostic distinguishes two restricted-resource cases with an ideal
fixed-fleet outer obstruction from a case where a reference-topology obstruction
can be removed by routing. That is a useful classical mechanism distinction.
It does not complete the missing economic comparisons, establish an ideal route
cost gap, strengthen the earlier bounded classical cost comparator, or provide
ML value, learned-information causality, a new theorem or population evidence.

The appropriate action from this readout is to preserve these conditional
exclusions and the unchanged native labels together, while keeping the
nonexcluded cases and missing economic endpoints explicit. No automatic retry,
capacity scan, fleet relaxation, new cohort, model fit or further experiment is
proposed or authorized by this review. Existing stopping decisions and recorded
cost points remain unchanged.
