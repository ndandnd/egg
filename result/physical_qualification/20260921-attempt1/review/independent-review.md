# Independent code and result review: physical qualification

**Disposition: PASS for the eight frozen engineering controls.** No blocking mathematical, physical-formulation, replay or result-accounting issue was found. This does not qualify a general operational EVSP extension or turn numerical enclosures into formal floating-point proofs.

Reviewed frozen commit: `8e9c7df9bd10066150ec09b459340ab5e74e55f9` in `physical-reuse-qualification-work`. The inspected code and protocol are unchanged from that commit. Their SHA-256 hashes agree with the saved environment record:

- Source: `9f2927a01512f232ae9fc99868313aefcc5c7581eac8e23b5981c6ef098b5863`.
- Protocol: `0dc5fe5c6d83df2f0f2c84bdd6b1b8687c28450ce8c7a0ab2efbcf6c71a521a1`.

Outputs reviewed: `physical-reuse-qualification-work/result/physical_qualification/20260921-attempt1`. The independent audit used system Python with isolated mode, disabled site initialization and bytecode, and imported neither the experiment nor a numerical solver. No new physical solves were performed by the reviewer. The reviewer wrote [independent_audit.py](independent_audit.py), and the machine-readable checks and output hashes are in [independent-audit-results.json](independent-audit-results.json).

## Findings

The independent checker reconstructed all **31 complete fleet structures** from trip times using separate combinatorial logic. Counts and feasible/infeasible classifications match the analytic derivations in [design-review.md](design-review.md). All **169 recorded solver calls** report OPTIMAL or INFEASIBLE and one thread. The supervisor reports successful exit without timeout; every recorded case remains below its 40-second budget and the process remains below its 240-second cap. These logs establish the recorded execution and resource settings, not an external operating-system measurement of every solver thread.

Every saved charging event was replayed independently against trip coverage, depot availability, per-bus power, SOC, battery capacity, terminal requirements, and shared power. The checker rebuilt aggregate loads and operating/system costs, verified the lower/upper and gap arithmetic, and checked that the exact analytic optima lie inside the reported numerical intervals. It also checked saved input records against both the frozen configuration and independently specified fixture parameters.

| Fixture | Exact analytic D / CH | Reported gap interval | Review |
|---|---:|---:|---|
| linear_split | 8 / 8 | [-0.0000016000, 0.0000016000] | Contains 0 |
| convex_split | 13 / 12.2 | [0.7999957634, 0.8000103401] | Strictly positive; contains 0.8 |
| forced_one_bus | 13 / 13 | [-0.0000073684, 0.0000073684] | Contains 0 |
| capacity_filters_structure | 14 / 14 | [-0.0000028000, 0.0000028000] | Contains 0; rejects aggregate-only cap interpretation |
| replenished_terminal | 0.5 / 0.5 | [-0.0000078294, 0.0000078294] | Contains 0 |
| replenished_infeasible | Both infeasible | Undefined, correctly omitted | Independent energy deficit proves infeasibility |
| two_bus_uncapped | 36 / 36 | [-0.0000072000, 0.0000119684] | Contains 0 |
| two_bus_shared_power | 36.8 / 36.8 | [-0.0000073600, 0.0000073600] | Contains 0; aggregate 8/12 cap active |

These intervals are displayed rounded; exact saved values were audited without display rounding. A numerical interval containing zero is consistent with the independent zero-gap calculation; the interval alone would not prove exact equality. The 0.8 gap is independently derived analytically and also separated from zero by the reported numerical enclosure.

## Normalized physical witnesses and numerical scope

Scaled replay is appropriate for checking the homogeneous master constraints, but a tiny positive structure weight can conceal a larger residual after normalization. The independent audit therefore also divided every positive-weight charging component by its weight and replayed it as a unit-weight physical structure. All **19 positive components** across the master and physical solves passed; the smallest observed positive weight was approximately **0.3994140625**, so there was no problematic tiny-weight normalization in these results. All zero-weight blocks had exactly zero recorded charge.

A separate direct trajectory calculation found the largest normalized SOC shortfall to be about **1.78e-15 kWh**; battery overfill, per-bus power excess and shared-power excess were zero at the recorded precision. Thus feasibility of these particular witnesses does not depend materially on the adapter's 1e-7 kWh replay tolerance. Optimal charging splits and CH weights are nevertheless approximate: for example, the analytic convex-split one-bus weight is 0.6, while the returned near-optimal weight is approximately 0.6005859375. It would be inaccurate to call the numerical witness an exact recovery of the analytic weight.

The adapter's operand-scaled objective allowance is explicitly a numerical guard. It is not a derived worst-case correction mapping an arbitrary infeasible floating-point point to an exactly feasible point or correcting a solver dual bound under arbitrary numerical failure. The protocol correctly limits its claim to CBC and replay-tolerance-conditional enclosures. The independent analytic calculations strengthen the eight fixtures specifically; they do not remove that limitation for future instances.

## Adversarial coverage and code assessment

The separate checker rejected seven intentionally corrupted output copies: an omitted structure, an out-of-window charge, a forged aggregate load, a forged exact objective, a forged gap endpoint, an unresolved solver status presented in a physical result, and removal of a frozen shared-capacity specification. The root-authored focused tests additionally cover negative and duplicate charges, excessive power, insufficient SOC and terminal energy, wrong operating cost, actual shared-capacity violation, off-grid event times, and an unresolved solve. The reviewer inspected those tests; their reported 19-pass run was performed by the implementer, not rerun as new physical experiments by this reviewer.

The most consequential formulation choice is correct: the shared cap is enforced inside every complete lambda-scaled fleet structure. The capacity-filter control consequently gives CH=14, rather than incorrectly preserving the unconstrained 12.2 master point. The adapter also preserves continuous charging, records a lower model value and true quadratic evaluation, refuses unresolved statuses, retains infeasible structures, and performs per-structure physical optimization before reporting a complete dictator interval.

Remaining limitations are explicit and do not block this qualification: full-slot availability only; linear charging power and lossless energy accounting; shared power rather than a finite plug count; all-depot zero-deadhead controls; depleted-terminal inventory in the positive-gap example; and a constructed zero-energy marker for the closed-energy control. Production model code is unchanged. Production A2 has not acquired these shared-capacity constraints and cannot be used as an equivalent capped-model comparator without a corresponding pricing/model extension.

**Recommended advancement:** proceed to the simple reuse and analytic-price baseline qualification on a declared compatible model. Preserve these eight results and their runtime provenance. Treat the positive-gap control as a successful physical-model demonstration, not evidence that learning helps or that the empirical project has gained a new operational dataset.

## Final synthesis review addendum

Reviewed `doc/PHYSICAL_REUSE_QUALIFICATION_RESULTS_20260921.md` before final packaging. **PASS: no interpretive blocker.** The synthesis faithfully distinguishes the depleted-terminal positive-gap example from the zero-gap replenishment marker; correctly places shared capacity inside each fleet structure before convexification; and preserves the numerical, solver-conditional scope of the objective allowance. It reports the approximate stored CH weight separately from the exact analytic minimizer and does not turn the subsecond physical qualification into a performance benchmark.

The reuse table's call totals, transition counts, rounded subprocess times and maximum certificate width agree with the saved `summary.json`. Its closed-form optimum costs and loads agree with the frozen one-bus fixture parameters (fixed cost 10, linear coefficient 0.3, slope 0.2, required charge 10 and tilts 0, 0, 0.2, -0.2). The statement that the optimal charging-slot marginal prices stay at 1.3 follows directly from those parameters. This limited documentary consistency check supplements, rather than replaces, the separate reuse code/result review. No new solves were run for this addendum.
