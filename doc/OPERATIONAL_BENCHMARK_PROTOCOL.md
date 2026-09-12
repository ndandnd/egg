# Operational benchmark protocol — design for review

Date: 2026-09-12. Code baseline: `44a152e2914ae7f06940259e2c8df0128ad4f40d`.
This document defines the next model-validation work. It contains no operational
data, new solve results, seed allocation, or launch authorization.

## Research question and staged claim

Test whether the certified gap between implementable fleet coordination and
schedule convexification survives credible charging physics and price-impact
scales. Keep this separate from the repeated-solve acceleration pilot in
[REOPTIMIZATION_PILOT_DESIGN.md](REOPTIMIZATION_PILOT_DESIGN.md).

The current `Instance`/`EVSP` model has homogeneous batteries and constant vehicle
charging power, depot charging, a vehicle cap, and a fixed terminal-SOC rule.
It does not enforce a shared charger count or depot power cap. The affine market
uses energy per slot; its synthetic duck shape is not solar generation or a
market-clearing calibration. Do not label a larger run of this model an
operational validation.

Stage A is a fully disclosed synthetic depot benchmark, separating each added
physical constraint from the baseline. Stage B is a source-validated operational
subset. A source dataset cannot establish endogenous price impact by itself;
the electricity-supply interpretation needs a separate calibration.

## Data readiness and reuse of existing work

The repository's [GIRO handoff](../ref/context/GIRO_DATASET_HANDOFF_20260814.md)
identifies concrete blockers: exports describe solved blocks rather than raw
day-specific demand; weekday alternatives must be selected; deadheads may be
directed and time-dependent; exact-place and reference-place models differ;
charging curves and finite resource counts matter. It also labels source
material C1 Internal. Use the technical paraphrase here; do not publish raw
files, source correspondence, or identifying records without data-sharing
review. No raw operational files were accessed for this protocol.

[PR #41](https://github.com/ndandnd/egg/pull/41), pinned at
`2530ec8fb3b8e40a2080b7fcccabe832931df623`, already implements a manifest-checked
freeze/load path. Review and reuse it before introducing a competing loader.
A manifest is necessary but does not repair source ambiguity or validate the
physical abstraction.

Public literature gives a second benchmark route. Gerbaux, Desaulniers and
Cappart evaluate large Montreal-derived artificial bus instances, while Löbel,
Borndörfer and Weider evaluate anonymous real-life instances and show how
charging approximations affect feasibility. Availability and redistribution
rights of those instance files are unresolved; paper access is not data access.
Sources: [Gerbaux institutional record](https://research.dial.uclouvain.be/entities/publication/ce60f346-f699-41e0-b2d3-d0d7744d91aa),
[Löbel et al., selected full text §§4–7](https://arxiv.org/html/2407.14446v1).

## Minimum manifest before a data freeze

Record source-file digests and access terms; day/variant choice; exact source-row
membership and duplicate policy; elapsed-minute convention beyond 24:00;
directed deadhead and missing-link policy; energy lineage; battery types and SOC
limits; initial/terminal energy policy; charging increment curve and efficiency;
charger count and site power limit; grid-cost assumptions; objective units and
all translation limitations. Source geometry, deadhead simplifications, and
fleet ownership must be separate fields, not inferred from instance names.

Validate the translated historical blocks where available. Failure means the
translation or model may disagree with the source; it does not prove the
historical operation was infeasible. Historical blocks provide a feasible
reference only after validation, not a proof of optimality or a restricted
deviation set for economic regret.

## Physical qualification before comparative solves

1. Independently replay time, directed travel, SOC and energy on every accepted
   schedule. Include trips extending beyond midnight and charger overlaps.
2. Check a one-charger conflict with two simultaneous buses and a depot power
   cap with staggered versus overlapping charging. Infinite-resource behavior
   must be an explicit ablation, not a silent default.
3. Verify a small charging-curve example analytically, then compare the model's
   interpolation against the chosen curve at SOC knots and between knots.
   State whether the approximation is conservative for feasibility and how its
   error enters objective/certificate bounds.
4. Verify initial and terminal energy accounting. Starting full and ending at
   reserve represents depletion of stored energy; a repeated-day claim needs
   replenishment or explicit valuation. Avoid silently adding end charging to
   the established laboratory model.
5. Use an independently enumerated small case to check the complete feasible
   schedule set and the master projection. PR #39's existing witness is a
   reference, not a substitute for validating new shared-resource constraints.

## Economic scale and unit conversion

For slot duration h hours and energy L_t in kWh, power is L_t/h kW.
`p_t = a_t + b_t(U_t + L_t)` has price in currency/kWh, so b has units
currency/kWh² and the convex supply increment is
`(a_t + b_t U_t)L_t + b_t L_t²/2`. The strategic bill has a different gradient.

For a supply slope beta quoted in `(currency/MWh)/MW`, convert to the
energy-slot coefficient as `b = beta/(1,000,000 h)`. Also convert the intercept
from currency/MWh to currency/kWh. Thus a shorter slot changes b for the same
power-based supply curve. Do not copy an hourly b into 15-minute slots or add a
second duration factor to an energy-valued objective.

Report `b * delta_L / p_ref` with a stated positive reference price, and report
absolute currency and relative-to-system-cost gaps. Include zero-impact and
weak-impact controls as well as stronger impact. Use a depot/microgrid marginal
cost model only if its supplier, cost curve and compensation interpretation are
specified. A demand charge, fixed tariff or fitted wholesale bid curve is not
automatically the same model. Multiple independent fleets require separate
convexity blocks and a corresponding pricing-bound derivation; raising trip
count within one block does not create more price-taking participants.

## Deliverables and stop conditions

The first acceptable output is a reviewed data/physics manifest plus independent
replay and small-instance checks, followed by a frozen comparative design. Halt
the operational claim if day membership, material missing travel links, charging
feasibility, source rights, or economic units remain unresolved. Synthetic
sensitivity work may proceed under its own disclosed assumptions.

Report every unresolved cell and model mismatch. Do not replace an inconvenient
day, seed or charger configuration after observing the scientific outcome.
Protected A6/B3 evidence and confirmation seeds are outside this protocol.
