# Gate and failure review

25 October 2026. Bounded scientific review of `RESULTS_VIEW.json`, its existing
decimal stdout view, the frozen protocol and the post-study decision map only.
No underlying receipts, captures, models or data were opened; no metrics were
recomputed, and no tests, imports, hashes, inference, replay or solver work ran.
Decimal values below reproduce the existing stdout display; exact signs and
counts were checked against the JSON view where rounding matters.

## Decision: valid negative practical-margin result

Both prescribed learned-family gates correctly return **do_not_continue**.
This is decision-map path B, not an incomplete-study or unqualified-QP result.
The view reports campaign/finalization/export complete and passed, all
continuation eligibility checks true, no fatal rows or invalid admissions, and
no stop signal or unresolved child reserve. `scientific_qualification=false`
therefore does not mean the campaign failed its execution/admission checks.

| Family | Gate control | Defined pairs | Positive group medians | Mean d | Decision |
|---|---|---:|---:|---:|---|
| GNN, primary | CoverCA1 | 48/48 | 7/8 | 0.000386688 | Fails mean >0.01 |
| GNN, primary | fixed_route_QP | 48/48 | 8/8 | 0.087352508 | Passes both criteria |
| CatBoost, secondary | CoverCA1 | 48/48 | 7/8 | 0.001997028 | Fails mean >0.01 |
| CatBoost, secondary | fixed_route_QP | 48/48 | 8/8 | 0.088962848 | Passes both criteria |

Each family must pass **both** comparisons. Both meet the group-count criterion
against CoverCA1 but fail the prespecified practical margin there; neither can
be rescued by its much larger advantage over fixed-route charging. CatBoost
cannot replace primary GNN after observing these results. CatBoost's CoverCA1
median for group50610 is exactly positive in JSON although it rounds to zero in
stdout; retaining seven strictly positive medians is correct. Do not replace
the gate's exact sign rule with the separate conditioning near-zero convention.

This negative decision is **not evidence of zero effect or equivalence**.
The observed CoverCA1 means favor each learned family, and seven group medians
are positive. They do not achieve the fixed margin. Positive group medians and
a small paired mean are compatible: medians and a mean summarize different
features of six repeated observations per group. The view does not justify a
post hoc story about the cell-level tails causing their difference. No new
significance, equivalence or promotion threshold should be introduced.

## Denominators and retained failures

The ledger is complete: 16/16 acquired priors admitted, 384/384 active rows
recorded and attempted, and 384 operational costs defined. Method acceptance is
382, strict method success is371, and attempted-without-success is13. These
counts reconcile as **371 successful methods +11 accepted endpoints with a
method failure +2 unaccepted/crashed method packets**. All384 nevertheless have
an operational endpoint. There are no missing-prior cells, unattempted cells,
parent-late/timeouts, fatal configuration flags or invalid admissions in the view.

The two external operational fallbacks are exactly:

- `scale:50607:40`, seed73, GNN;
- `scale:50607:40`, seed73, GNN_day.

Both exited with return code−6, were reaped, had no accepted method endpoint,
and use `preexisting_fallback`. Their operational cost is not free or missing.
The view does not identify the abort's cause; null worker/planner fields cannot
establish a model, memory, solver or infrastructure diagnosis.

The other eleven non-success rows retained accepted earlier physical candidates.
They comprise the two later-round candidate-admission failures shown in the
view—GNN_day50604/80/41 (charge projection/insufficient completion time) and
full50606/40/41 (energy-conservation rejection/insufficient completion time)—plus
nine later planner-deadline failures: CatBoost50607/80 seeds17,73;
GNN_day50607/80 seeds17,73; GNN50607/80 seeds41,73; and CA1 50608/80 all three seeds.
Rejected later candidates are not admitted-invalid operational plans. An
internal planner deadline can be recorded while parent admission still finishes
within60 seconds, so these rows do not contradict zero parent-late/timeouts.
Keep their strict method-success flags false and their retained operational
costs in all comparisons; neither erase failures nor discard usable witnesses.

## Strong control and all comparator context

QP diagnostics support the full prerequisite in this compact view: 48 assigned,
recorded and attempted; 48 accepted parent endpoints, strict method successes,
new helper physical candidates, parent-timely candidates and native OPTIMAL
statuses; zero provisional candidates. The qualification record is48/48 true.
Thus the learned gate did not fail because the strong charging control failed
to materialize. These are numerical, physically admitted **fixed-topology** QP
results, not an unrestricted routing optimum or exact physical certificate.

The remaining reported comparisons must accompany the gate. All have48/48
defined operational pairs; positive d favors the learned family.

| Comparator | GNN mean d | GNN positive groups | CatBoost mean d | CatBoost positive groups |
|---|---:|---:|---:|---:|
| CA1 | 0.002464893 | 7/8 | 0.004075233 | 4/8 |
| random | 0.001706251 | 8/8 | 0.003316591 | 6/8 |
| full | 0.034760564 | 8/8 | 0.036370904 | 7/8 |
| unchanged prior | 0.234267235 | 8/8 | 0.235877575 | 8/8 |

GNN's mean against CatBoost is−0.001610340 despite five positive group medians;
CatBoost is better in the paired mean, not a universally superior selected
family. GNN loses the CoverCA1 and CA1 group median on50607; CatBoost loses the
CoverCA1 group median on50611. CatBoost's CA1 comparison has four positive
medians, losses on50607/50608/50611 and an exact tie on50604. These patterns
reinforce heterogeneity rather than a universal ranking. Full's worse outcome
under this clock does not certify the restricted pool or show unrestricted
optimization is intrinsically worse. Benefits over unchanged/fixed-route QP
support the operational value of replanning with route flexibility in this
setting, but do not isolate learning, charging timing or demand mechanisms.

## Conditioning evidence and limits of this view

GNN versus GNN_day has48 defined operational pairs, mean d0.001206672, and an
overall median that rounds to zero. The descriptive counts are23 GNN wins,
15 GNN_day wins and10 near-zero pairs; group counts under the prespecified
near-zero convention are4/2/2. Exact-positive group count is five, illustrating
why exact sign and near-zero summaries must stay separate. All47 observed pool
pairs differ, with ranking room present; one pool pair is missing at the same
50607/40/73 crash. Complete overlap means/medians correctly remain null rather
than treating47 available pairs as48. No identical-pool mechanism is observed
among defined pairs. This is mixed, modest inference-conditioning evidence,
not a trained-information causal result, and cannot reverse the failed primary
gate. No automatic conditioning threshold exists.

The view omits the complete per-cell pairwise loss tails and detailed
operating/deadhead/electricity/grid-energy decomposition needed to explain cost
mechanisms. Do not reconstruct those from raw material here or label d as energy
savings or a reduction in comparator total bill: its denominator is the common
prior's late electricity cost. This review also cannot independently verify
physical replay, individual native traces or source/asset identities from the
compact aggregate fields. Those are reported campaign contracts, not new audits.

The scientific concession is precise: **this fixed learned policy did not meet
the prospectively required incremental practical margin over CoverCA1 on these
eight new development groups**. It can still have positive effects under this
clock. The four older development groups do not rescue the gate, and48 size/seed
blocks are not48 independent timetables. Stop automatic ML expansion; any next
mechanism experiment needs a specific unresolved question and a new prospective
decision. No generic pruning novelty, price-learning causality, population
transfer, timing-isolation or broad optimality claim follows.
