# Manuscript claim and evidence ledger

Working title: **When marginal electricity prices cannot coordinate electric-bus
schedules: complete-duty certificates and a replenished-fleet counterexample**.
Working target: Transportation Research Part C, conditional on a credible
transportation case and substantive managerial findings. Public Transport is a
plausible narrower alternative. This is positioning, not a submission decision.

| Claim | Evidence | Strength and remaining obligation |
|---|---|---|
| A positive complete-schedule planning gap lower-bounds every physical schedule's regret at its own marginal price | PR52 mathematical derivation, compactness/attainment and objective matching explicit | Classical convexification principle specialized to EGG; not a new general welfare theorem. Incorporate a self-contained proof and source attribution. |
| Continuous charging and full terminal replenishment do not guarantee a zero gap | New exact four-period construction; frozen7bf913a; D97, CH7591/80 | Hand-constructed proof witness; independent all-case/physical audit passed, including10corruption controls. Not empirical prevalence or production-adapter qualification. |
| Fleet LOC at a hull price differs from own-price regret and from total fleet+supply LOC | Nominal exact price decomposition: own-price regret13, hull-price fleetLOC0, supplyLOC169/80 | Distinct prices and same physical dispatch must be identified in every table/figure. No budget-balance or strategic-equilibrium claim. |
| Applying shared capacity only after convexification can weaken the intended model | PR55 capacity control and PR54 shared-resource witness | Resource rights/deviations and physical scopes differ; retain exact assumptions. |
| Reusing feasible columns can remove pricing discovery work on a small trajectory | PR55 12 cells, cold12/retained6/shift9 calls | Seed-free diagnostic; all costs count. No general runtime speedup/ML claim. |
| Harder competing structures leave discovery work beyond reuse | New 45-cell frontier and 15 separate reference cells, frozen 7d3d764; [independent review](../result/reuse_frontier/20260927-attempt1/review/REVIEW.md) | 44/45 cells certified; one cold return-state failed because pricing returned FEASIBLE at its configured cap, not because of a subprocess timeout. Exact rational pricing/dual bounds independently support all 44 successful cells; numerical physical replay passed. Retained transitions require 17 clean calls against 12 mandatory checks; five extra calls show remaining work, not learnability. |
| A shifted-price proposal need not reduce clean discovery work | Same frozen frontier, independent replay of all 223 pricing attempts and complete purpose accounting | All matched cells have identical clean-call counts for retention and shifted retention; the latter adds 12 proposal calls and 3 projection-novel columns. Descriptive negative result on three synthetic trajectories, not a general impossibility claim. |
| Operational benefits on a real timetable | GIRO local readiness audit and public benchmark intake | Not established. Required for intended journal scope; private raw data cannot be a public artifact. |
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
