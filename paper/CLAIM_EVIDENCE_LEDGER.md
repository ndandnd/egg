# Manuscript claim and evidence ledger

Working title: **When marginal electricity prices cannot coordinate electric-bus
schedules: complete-fleet certificates and a replenished-fleet counterexample**.
Working target: Transportation Research Part C, conditional on a credible
transportation case and substantive managerial findings. Public Transport is a
plausible narrower alternative. This is positioning, not a submission decision.

| Claim | Evidence | Strength and remaining obligation |
|---|---|---|
| A positive complete-schedule planning gap lower-bounds every physical schedule's regret at its own marginal price | PR52 mathematical derivation, compactness/attainment and objective matching explicit | Classical convexification principle specialized to EGG; not a new general welfare theorem. Incorporate a self-contained proof and source attribution. |
| Continuous charging and full terminal replenishment do not guarantee a zero gap | New exact four-period construction; frozen7bf913a; D97, CH7591/80 | Hand-constructed proof witness; independent all-case/physical audit passed, including10corruption controls. Not empirical prevalence or production-adapter qualification. |
| A positive gap can coexist with reserve, charging loss and one finite terminal connector | Frozen bd022ac joint case: reserve 1 kWh, efficiency 19/20, early individual/shared power 12 kW, terminal connector 30 kW; exact gap 94249/28880; [independent robustness review](../result/cyclic_robustness/20260927-attempt1/review/INDEPENDENT_ROBUSTNESS_REVIEW.md) | All 16 fixed cases independently pass: 9 positive, 6 zero, 1 infeasible. The unchanged 10 kW early hardware loses its one-bus branch under reserve or loss. The joint model has 8/19 grid-kWh early headroom; strict inequalities support a neighborhood within the admissible hardware model. Zero switching time and no taper remain essential declared assumptions. |
| A single terminal connector's adequacy depends on its power and charging horizon | Same robustness audit; nominal reserve 0, efficiency 1 and early power 10 kW | Exact continuous threshold: infeasible below 20 terminal kW, zero gap from 20 through 23.5, positive gap above 23.5 through 30. Gap is 5/64 at 24 kW. This conditional threshold is not a claim that any single charger suffices. |
| A vanishing absolute planning gap need not imply vanishing whole-operator own-price regret along every subsequence | Frozen ce84e9e replication; 86 sizes, 6,448 continuous branch minima, 88 physical optima; [independent replication review](../result/cyclic_replication/20260927-attempt1/review/REVIEW.md) | Along n=40k+1, gap=169/(80n) while regret tends to 351/40. Regret per actual used bus and relative regret vanish; multiples of 40 have exactly zero gap and regret. Both tied optima are retained. Supply curvature/resources scale with demand. This is one whole-fleet price-taking operator, not independent firms or strategic market power. |
| Fleet LOC at a hull price differs from own-price regret and from total fleet+supply LOC | Nominal exact price decomposition: own-price regret13, hull-price fleetLOC0, supplyLOC169/80 | Distinct prices and same physical dispatch must be identified in every table/figure. No budget-balance or strategic-equilibrium claim. |
| Applying shared capacity only after convexification can weaken the intended model | PR55 capacity control and PR54 shared-resource witness | Resource rights/deviations and physical scopes differ; retain exact assumptions. |
| Reusing feasible columns can remove pricing discovery work on a small trajectory | PR55 12 cells, cold12/retained6/shift9 calls | Seed-free diagnostic; all costs count. No general runtime speedup/ML claim. |
| Harder competing structures leave discovery work beyond reuse | New 45-cell frontier and 15 separate reference cells, frozen 7d3d764; [independent review](../result/reuse_frontier/20260927-attempt1/review/REVIEW.md) | 44/45 cells certified; one cold return-state failed because pricing returned FEASIBLE at its configured cap, not because of a subprocess timeout. Exact rational pricing/dual bounds independently support all 44 successful cells; numerical physical replay passed. Retained transitions require 17 clean calls against 12 mandatory checks; five extra calls show remaining work, not learnability. |
| A shifted-price proposal need not reduce clean discovery work | Same frozen frontier, independent replay of all 223 pricing attempts and complete purpose accounting | All matched cells have identical clean-call counts for retention and shifted retention; the latter adds 12 proposal calls and 3 projection-novel columns. Descriptive negative result on three synthetic trajectories, not a general impossibility claim. |
| Operational benefits on a real timetable | GIRO local readiness audit and public benchmark intake | Not established. Required for intended journal scope; private raw data cannot be a public artifact. |
| The native recharge model reproduces the predefined analytical controls on two backends | Corrected CBC V2 frozen 997575d and identical GRB replication at execution commit 24c7e4e, job 557318; separate independent audits | All 15 controls pass on each backend: 12 numerical certificates and three analytically confirmed infeasibilities. Raw variables, constraints, correction ledgers, physical sessions and bounds independently reconstructed; 16 CBC/18 GRB corruptions rejected. Solver-conditional, small synthetic qualification only. First CBC attempt remains FAILED 12/15; no retrospective repair. Timing extension, native hull and public timetable are separate gates. |
| Stabilization outperforms baseline | Prior B2 reports do not support this | Do not claim. Same16-seed-block population; B3 is retrospective, not replication. |
| Learned proposals help | No eligible experiment yet | Do not claim or train before useful remaining work and frozen evaluation design. |

The packaged [reuse auditor](../result/reuse_frontier/20260927-attempt1/review/audit_reuse_frontier.py)
uses no author imports or native optimizer. Continuous linear-pricing optima
follow from an independently enumerated, integral inventory-flow formulation
specific to these aligned, integer-capacity, zero-deadhead fixtures. Exact
binary-rational Fenchel lower bounds use only each state's completed clean
prices; their numerical widths against replayed upper bounds range from
0.000025334433885859653 to 0.0009124833710245639, below 0.01. The physical
weights/charges remain stored binary64 values checked at explicit tolerances;
they are not rationalized, normalized or repaired. Do not call these exact
rational physical certificates.

All 15 reference structure sets and 420 scaled witness blocks independently pass,
and reference interval arithmetic/overlap is reproduced. The audit does not
independently prove their tighter native PWL lower bounds: its separate
gradient-support widths are 0.0019611186460863905–0.022598356017276444.
It checks final KKT for 190 returned masters, not every unsaved inner LP primal.
The 145 mutable tangent snapshots are reconstructed by the proven frozen
control-flow rule; original evidence remains unchanged and the prospective
repair is separately recorded. All 19 corrupted-copy controls are rejected.

## Audited cyclic extension identities and limits

Robustness source/design/protocol are pinned to
`bd022ac32ef680446ee17bc4400843a764acb9f6`; raw
`result/cyclic_robustness/20260927-attempt1/results.json` has SHA-256
`3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29`.
The non-author audit reconstructs 32 complete physical intervals, 46 endpoint
witnesses, 100 saved schedules, 161 individual bus/session replays, 805 SOC
events and 26 complete price/LOC accounts. All 22 corruption controls are
rejected. Its canonical machine report is `review/independent-audit-v2.json`;
the derived review manifest is separate from the immutable raw manifest.

Replication source/protocol are pinned to
`ce84e9e62b8e3f33d32010d381fd845415eff458`; raw
`result/cyclic_replication/20260927-attempt1/results.json` has SHA-256
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.
The non-author audit reconstructs all 86 cases and rejects 21 corrupted copies.
It also completes the general nearest-integer proof by excluding the lower
branch regime, with n=1 and n=2 checked separately. The complete projected
hull is a triangle; the stored `hull_vertices` field records its lower boundary,
not all triangle vertices. Physical ties at n=20 and n=60 have different
own-price regrets, and both remain in the evidence and figure.

Both extensions use exact rational physical constructions and arithmetic;
neither uses a native optimizer or operational data. Deterministic grid counts
are not population frequencies. Replication's relative gap divides by CH,
while its relative regret divides by D. Its nonzero whole-operator regret
limit applies only to the stated subsequence, not to all integer sizes.
The extension figure script records these sample scopes and input hashes.

The previous reviewed working PDF 0.3 had 17 pages and six figures. Its immutable identity
and independent all-page visual check appear in
`MANUSCRIPT_V03_LAYOUT_REVIEW_20260927.md`. This is layout review, not an
independent review of all scientific prose. The excellent-first-draft goal
remains incomplete.

## Reviewer audit before a first draft is called excellent

- Common complete feasible set and costs in planner, oracle and convexification.
- Battery energy, horizons, terminal charging, deadheads, charger resources and
  departure/arrival timing stated and independently replayed.
- Price-taking, strategic response and resource-constrained deviations separated.
- Correct lower/upper bound directions, numerical allowances and unresolved cases.
- Physical dispatch distinguished from fractional averages and randomization.
- Equal certification and complete costs across reoptimization comparators.
- Fresh versus retrospective data, deterministic constructions versus samples,
  and exploratory versus held-out experiments labeled explicitly.
- Primary references checked at the actual available version; novelty narrowed
  against direct fleet-scheduling and convex-hull-pricing precedents.
- Figures regenerated from archived data, readable in grayscale/print, with
  units and sample scope in captions; no decorative unsupported diagrams.
- No private GIRO sources, personal contacts or unrestricted holdouts in GitHub.

## Native and source-admission update

The corrected CBC V2 and separate GRB qualification share identical native
source hashes and all fifteen physical/objective/target definitions. Each has
30 returned calls and 27 raw finite incumbents; independent fixture minima
contain all twelve numerical certificate intervals. Differences in session
counts reflect alternative valid numerical witnesses, not changed physics.
Cross-environment timing is not a speed comparison. The original failed CBC
attempt and its independently checked three exceptions remain visible.

The private 17-service candidate is blocked by off-depot charging and missing
explicit movement records. A licensed public 37-service Hildenbrand timetable
with complete directed deadheads has been independently translated into two
separately declared one-depot, one-connector scenarios. Traction/auxiliary rates, usable inventory,
constant efficiency, charger cap and synthetic costs are assumptions, not
measured energy or reproduction of the publisher's optimization. No operational
benefit or pricing result is established by data intake alone.

The nineteen-control exact source-time extension and twenty-control compact
formulation each passed independent numerical/raw/physical audits (22 and25
corruptions rejected). Compact integer feasible-set equivalence does not imply
identical LP relaxations or solver performance. The corrected native-hull V2
returned8/8 certificates and passed independent result review (31 corruptions
rejected;21 pricing minima,15 LP minima and all9 polishing transfers checked). First-run
hull failure2certified/4exhausted/2blocked remains unchanged.

The reserved-pair participant derivation was independently checked against all88
archived physical optima: each pair's regret is at most20/n, and its aggregate
reproduces the whole-operator regret under these specific connector rights.
No general shared-resource-game or large-market contradiction follows.
The radius-dependent quadratic regret bound passed two independent mathematical
reviews and is in manuscript source0.4. The current reviewed working PDF is
version0.4 (22 pages, seven figures; SHA-256
acae4e1bc915fdf7e7a4cafcd997b91aa6941afe73a9075b37cb6b50514663ca). This
metadata/layout review does not close the public nonlinear evidence gate.


The first full37-service public flat-price pilot is independently audited as
bounded/FEASIBLE for both depots, with two-bus witnesses and wide objective
intervals. This establishes feasible schedules under declared EGG assumptions,
not cost optimality or an operational benefit. Both original scientific traces
remain unchanged. The compact-hull integration separately passed8/8 controls
with independent reconstruction and42 corruption controls. No public nonlinear
physical-versus-hull gap is established yet. Figure7 plots both pilot witnesses,
including235 saved SOC points (four initial plus231 subsequent events).


The exact post-pilot flat-price matching diagnostic passed independent result
audit for both public cases (freeze3014d04). The stored-input rational lower
bounds display301.315344/305.633808 and each relaxation has one path. All
2,035 allowed-edge dual inequalities per case and12 corruptions were checked.
This relaxes physical constraints and does not prove a feasible one-bus plan,
a native-matrix lower bound or a public nonlinear planning gap.

The separately frozen energy-band V2 first qualification (66b7054) passed19/20
and failed joint_planner extraction on positive charge of about1.22e-12kWh
associated with an unselected movement. All142 original files remain manifested;
independent audit confirmed the failed 19/20 gate. No downstream V2 hull/public experiment is
admitted. Pure preflight and hosted CI success are not substitutes for this
failed execution gate. The public Figure7 review passed with byte-identical PNG
reproduction. Source0.4 now explains the actual certificate loop and compact
model, gives the strict robustness inequalities, and separates repair history
in an appendix. The reviewed working PDF is version0.4 (22 pages, seven figures;
SHA-256 acae4e1bc915fdf7e7a4cafcd997b91aa6941afe73a9075b37cb6b50514663ca).
The nonlinear public timetable study remains pending; no public nonlinear
physical-versus-hull gap is established.

## Newly audited compact and public-case evidence — 27 September 2026

The published evidence freeze is [b502e85](https://github.com/ndandnd/egg/commit/b502e85f4e76ad2fc297199b7c51a0f0022f23d5), with both result audits included in
[PR #56](https://github.com/ndandnd/egg/pull/56). The [compact physical attempt 3
review](../result/native_pathflow/20260927-attempt3/review/REVIEW.md) passes 20/20
controls (16 numerical certificates and four expected infeasibilities) in 35
native calls and 24.707 seconds. Its independent review checks 589 raw incumbent
variables, 31 physical witnesses, and 25 corruption controls; the largest
whole-incumbent numerical correction is 1.2261e-12 kWh, below the 1e-8 policy
ceiling. This qualifies only the declared synthetic compact-model policy.
Attempt 3 prospectively corrects the issue exposed by failed attempt 2; the
original attempt 2 remains an unchanged failure and is not retroactively passed.
The new eight-control CBC hull run also passed independent result audit
(21 pricing calls, 15 masters and 48 corruption checks), qualifying its
declared synthetic fixtures only.

The [independent exact cardinality-flow
review](../result/sistig_cardinality_flow/20260927-attempt1/review/REVIEW.md)
reconstructs both full 37-service single-depot networks. Its
ideal stored-input lower bounds are 404.924239883878 for P15 and
414.394469217211 for P16. The earlier exact one-path matching relaxation gave
301.315343883878 and 305.633807883878, respectively. Separate
tolerance-qualified two-bus numerical upper witnesses are 408.533137 and
433.746086. These are distinct evidence types: they establish neither an exact
physical optimum nor an exact physical optimum gap, and no such gap is claimed.
The compact and cardinality result directories retain their independent reports
and raw artifacts. These results are research evidence for the next bundled
manuscript revision; manuscript source and the reviewed working PDF have not
been updated with them.
