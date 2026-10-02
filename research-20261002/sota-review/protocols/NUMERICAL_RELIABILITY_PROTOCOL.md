# Prospective numerical reliability protocol

Status: design only, 2 October 2026. No execution is authorized by this document. This operationalizes ranked experiment 1 in [SOTA_REVIEW.md](../SOTA_REVIEW.md), Sections 2, 3.6, 4 and 6, with [numerical guidance](../notes/ADAPTIVE_PRUNING_AND_NUMERICS.md). The main report governs where the older note differs: all four historical E10 Eberbach failures remain in the recovery denominator, regardless of diagnosed cause.

## Question and comparison

Can scaling and fixed-topology charging completion eliminate extraction/replay failures under unchanged physical rules, within acceptable overhead? Compare a paired 2×2 design:

| Arm | Model scaling | Candidate completion |
|---|---|---|
| A | Existing | Existing extraction |
| B | Improved, invertible unit/row/column scaling | Existing extraction |
| C | Existing | Fixed-topology charge repair |
| D | Same scaling as B | Same repair as C |

Use the existing 30 case/budget cells, three identical predeclared solver seeds per cell, and four arms: 360 runs. Keep scorer/checkpoint, pruning policy, tariff, tangent-round allocation, solver version, numerical tolerance settings and physical constraints identical. Scaling changes representation only; record transformations and translate residuals back to original units. Do not add parameter tightening to B/D. Any such diagnostic is separate and cannot substitute for the four-arm comparison.

Scaling must preserve integer/binary domains exactly: keep binary variables in {0,1}, scale continuous units/rows by default, and keep replay thresholds in original physical units.

All arms use the identical accepted-incumbent retention policy: independently replay each eligible candidate, retain the lowest recomputed true-bill accepted plan, and return it when later search, extraction or repair fails. Use identical supplied fallback information, if available, and record its acquisition cost. Without an accepted fallback, return explicit failure. A retained fallback does not erase failed candidates.

## Freeze before launch

Unknown inputs are launch blockers, not values to infer from results. Freeze a versioned manifest containing the exact 30 cells and their timetable-group nesting; budgets; three seeds; pruning configuration; checkpoint/input hashes; solver/hardware/thread settings; round allocation; original units; authoritative physical constraints; replay implementation and acceptance tolerances; integer-rounding qualification; scaling maps; repair algorithm, objective, time cap and tie-breaking; common wall-clock caps; fallback policy; and overhead definition.

Freeze the identities and raw artifact hashes of **all four archived E10 Eberbach failures**. Their raw IDs are currently unknown; this document invents none. Before launch, an authorized custodian must supply the complete cohort, raw incumbents and decoding context. No topology is removed after infeasibility diagnosis. Missing or irreproducible artifacts remain unresolved cohort outcomes, not successes. Do not open sealed DEV/TEST/A6/B3/GIRO; only already permitted training/development-generation and exploratory public cells are eligible.

Predeclare the best-known replay-valid bill reference, target-quality convention and any before-feasibility penalty. If a run improves the observed reference, update it consistently across arms. It is not an optimum. Freeze paired-run order/randomization and reporting code before the measured grid. A later separately authorized tiny implementation check must precede protocol lock and full launch; record any revisions before measurement.

## Candidate processing and repair

Archive each raw candidate before modification. Record integer distance, original-unit model residuals, route/depot/trip-coverage invariants, event SOC, charge windows, shared charger/power violations, terminal replenishment and decoded objective. Reject unqualified integer values; never silently round an arbitrary value into a new topology.

For C/D, fix every qualified discrete decision defining routing, bus usage and charging access. Preserve all original constraints and shared coupling. First solve continuous charging feasibility, then optimize charging using the frozen fixed-topology supply-cost formulation and completion allowance. A feasibility relaxation may diagnose violations but cannot produce an accepted plan. Do not independently clip charges, alter topology, relax reserve/terminal/charger rules, or introduce unreported margins.

Replay the completed plan in original units through the same independent validator used for A/B. Recompute the full physical bill, including intrinsic fleet costs and the true supply objective, from replayed events/load; a tangent objective or solver status is insufficient. Accept only when all frozen physical and decoding checks pass and the bill is finite and consistent within the frozen accounting tolerance. Keep a higher-cost valid candidate in the audit trail without replacing a better accepted incumbent. Repair timeout/infeasibility/replay rejection preserves the earlier accepted incumbent.

For historical recovery, apply each arm's extraction/completion to the same archived raw candidate and topology context; fresh-run success or fallback substitution does not count as recovering that historical candidate. Report this paired forensic outcome separately from fresh-grid reliability.

## Artifacts and failure taxonomy

Produce one run record plus an append-only candidate/event table. Required fields: manifest/version/hash; group/cell/budget/seed/arm; input and cohort references; solver status and termination reason; raw and qualified discrete values/topology hash; scaling maps; residual vectors and worst offending row/event; solver objective and independently recomputed bill; repair status/objective; every replay decision; accepted-incumbent provenance; fallback use; stage timestamps, CPU usage, thread count and peak memory; warnings; failure category and evidence links. Preserve native logs, raw candidates and repaired plans with checksums.

Use nonexclusive cause tags plus one primary disposition: missing/corrupt artifact; no candidate/search timeout; unqualified integrality; invalid route/coverage/depot topology; original-model numerical residual; model/replay semantic mismatch; fixed-topology charging infeasibility; repair timeout/error; SOC/reserve violation; charge-window/shared-capacity violation; terminal-energy failure; bill/accounting mismatch; unresolved. Numerical causation is a hypothesis until supported by residual/encoding evidence. Record failed intermediate candidates even when final fallback succeeds.

## Timing, gates and interpretation

Start wall time before loading/scoring and stop after final replay/bill/artifact finalization. Log loading, scoring, construction, presolve/root, each tangent round, extraction, repair, replay and reporting separately. Repair shares the common end-to-end cap; it does not receive free time after search. CPU accounting includes failures and diagnostics. One solver thread gives approximately 27.6 solver CPUh (2.3 per arm/seed); reserve **35–50 CPUh total** prospectively. Freeze diagnostic allocation and stop at the authorized envelope; report incomplete cells explicitly.

Define median overhead as the paired percentage increase in full pipeline wall time against A on the frozen comparable set, with zero-denominator handling specified before launch. Report capped/censored runs and failures separately; do not omit them from reliability denominators. Also report stage overhead so faster search cannot conceal expensive completion.

Advance only if no accepted plan fails unchanged replay, the promoted arm recovers **all four** historical failures (≥90% of four requires four), and median overhead is ≤20%. Report bills and retained-fallback frequency without treating reliability as optimality. No-go if success requires weakened physical rules, illegal topology changes, inconsistent bill accounting, or any accepted-plan replay failure. Unrecovered/infeasible historical cases count against recovery and motivate reformulation. Optional rational fixed-route diagnostics remain outside arm comparisons and cannot certify nonlinear bills or event semantics by themselves.

Summarize paired outcomes by timetable group; budgets and seeds are nested repetitions. Public evidence remains exploratory. Passing this pilot supplies no population reliability guarantee.
