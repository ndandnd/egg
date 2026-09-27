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

Reviewed working PDF 0.2 has 14 pages and five figures; its immutable hash and
all-page author visual check appear in the manuscript review record. Source 0.3
is in preparation and is not yet a new reviewed PDF. The excellent-first-draft
goal remains incomplete.

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
with complete directed deadheads is being translated into separately declared
one-depot, one-connector scenarios. Traction/auxiliary rates, usable inventory,
constant efficiency, charger cap and synthetic costs are assumptions, not
measured energy or reproduction of the publisher's optimization. No operational
benefit or pricing result is established by data intake alone.
