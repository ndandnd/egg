# Initial OPF qualification

**Decision.** The feeder computes the correct physical marginal prices on the qualified two-bus fixtures. The scaled German experiment and the native 33-bus benchmark have no reportable result from this attempt. H1–H4 are untested. Reviewed frozen sources 853967d5, control 2042fb04. Inputs previously frozen by 66121c09. This is a model validation result.

| Prespecified check | Result |
|---|---|
| Unlimited ideal feeder with affine source | Direct conic price €52/MWh, cost €23 at 1 MW for half an hour. Agrees with the analytic solution. |
| History of the original price loop | All 416 assignments, 30,217 updates, maximum price error 0 in archive currency/kWh. The replay obtained the original first stopping iterations and classifications, including 284 cycles, 66 fixed points and 66 capped runs. Fleet loads and optimizer tie choices came from the original records. No fresh historical fleet MILPs. |
| Resistive two-bus AC circuit | A 1 MW load required about 1.020842 MW of import. Depot price €54.474505/MWh. Across the base point and both perturbation sizes, the native prices matched the derivative of the independent high-voltage AC solution within €0.001/MWh. |
| Piecewise linear supply kink | Analytic left and right marginal prices €30 and €70/MWh. The solver returned €36.08923/MWh at the kink. Perturbed dispatches agreed with the prescribed slopes. |
| Binding import with local backup | The source imported 0.75 MW and backup supplied the remainder at €70/MWh. The limit stayed binding on both sides, and both one-sided slopes equaled €70/MWh to the frozen tolerance. |
| MATPOWER-derived 33-bus feeder | Unqualified. The isolated interpreter could not import pandapower because its required packaging module was outside its search path. No grid solve or AC replay occurred in this case. |
| Day-level signed export and artificial-loss rejection | The evaluation reached JSON publication and failed on a NumPy Boolean. It delivered no result packet, so the numerical assertions and the negative-price diagnostic remain unqualified. |
| German inputs | All three official-source acquisitions failed TLS validation before any data were admitted. The ex ante dates and feeder selection stand. |

Each accepted small native case met its balance, voltage, limit and cone-residual screens. The 16 native dispatches in the four passing fixtures and their finite differences are accounted for inside their owner's meter. Independent mathematical checking used the analytical high-voltage solution for the resistive two-bus network. A separate AI reviewer checked the result interpretation. This is not external replication. No fleet support gap on a realistic feeder has been computed.

## Inclusive measured work

| Worker | Exit | User + system CPU s | Elapsed s | Observed RSS bytes |
|---|---:|---:|---:|---:|
| Public input acquisition 16197 | 1 | .08 + .07 | 2.48 | unknown |
| Ideal replay 72584 | 0 | .72 + .09 | 1.14 | 43,958,272 |
| Native feeder qualification 31972 | 1 | 1.26 + .45 | 4.84 | 126,451,712 |
| Day diagnostics 24092 | 1 | .68 + .25 | 1.43 | 92,110,848 |

Total displayed 3.60 CPU s and 9.89 elapsed-sum s. Preparation, static reviews and desktop/source-reading overhead have no complete resource meter. All four worker commands exited, none left an unresolved numerical child. Three independent source reviewers completed their assignments. The original JSON records, process statuses and error traces are retained in this directory and attempt01. No duplicate launches, field observations or calibrated welfare claims.

## Next decision

For an exact feeder test the voltage, losses and flows must agree with the independent solver, then the welfare bounds for the physical fleet and its convexification must refer to the same grid and service set. Proceed to the realistic experiment only when the dependency, output and acquisition gates are qualified. A focused repair preserves these failures and reuses every passed qualification. The prepared continuation needs separate approval under the project's no-automatic-retry rule.

## Engineering continuation, 3 November 2026

The project owner gave standing approval for ordinary engineering repairs. Fix and check dependencies, serialization and public-download transport directly while preserving earlier failed results. Freeze the scientific inputs, comparisons, decision thresholds and analysis before seeking approval for a new scientific run. Reusing passing checks and admitted data avoids duplicate work.

The 33-bus conic calculation passed the frozen comparisons against an independent Newton AC power flow. Both give 0.202677 MW of loss, 3.917677 MW imported, and a minimum voltage of 0.913090 p.u. at bus 18. Maximum voltage discrepancy was 2.46 × 10⁻¹² p.u. The lossless linear baseline discarded 0.202677 MW and its largest voltage difference was 0.002844 p.u. These are checks at a single passive operating point. The day-level diagnostic also passed all ten checks. It priced import/export at 52/57 EUR/MWh in the two artificial periods and detected nonphysical artificial losses when the upstream price was negative, even though the relaxed solver returned optimal.

The frozen acquisition admitted the January price day, then encountered HTTP 429 on July and a timeout on the feeder archive. Each remaining input was retrieved individually with system HTTPS verification. Energinet requested a 182-second cooldown on the next July request. We waited 192 seconds before making the successful request. All 48 delivered rows have PriceArea=DE (24 per Berlin-local day, 17 January and 17 July 2024), consecutive UTC timestamps and finite EUR/MWh values. These are upstream spot prices. The pinned rural SimBench archive passed its table checks. Copies are retained locally under src/runs/opf-inputs-20261103. A subsequent transport regression covers cooldown handling, certificate failure and rejection of a single non-German record. [Energinet dataset](https://api.energidataservice.dk/meta/dataset/Elspotprices) · [Rate limits](https://www.energidataservice.dk/guides/api-guides) · [SimBench data and licenses](https://simbench.de/en/download/)

For scale, choose the two-peak, charge-only whole-bus model as the primary controlled experiment. A separate bus-indexed HiGHS MILP passed 19 solves on small artificial fixtures, including objective/bound checks, fixed covers, physical witnesses, a tie between different fleet sizes and three infeasibilities. Four exact-arithmetic unit tests separately covered enumeration and bus-level reconstruction. Ratings on the two native supply paths support synthetic depot designs from 0.75 to 7.875 MW. The engineering calculation checks whole-bus feasibility before any price observations are used. It supplies no empirical support-gap, hosting-capacity or cycling verdict. [Sizing assumptions, proof and table](../../doc/opf/DEPOT_SCALE.md) · [Download and zone readback](repair02/input_recovery.json)

The three frozen repair processes exited 0, 0 and 1. Their meters total 3.66 displayed CPU seconds and 40.76 elapsed-sum seconds. Selective recovery consumed a further 0.53 displayed CPU and 110.34 elapsed-sum seconds across the first summer request, complete feeder transfer and successful summer request, excluding the deliberate cooldown. The original 3.60 CPU seconds and all prior failures remain recorded. Separate unit checks and desk work are outside those totals. No large fleet optimization, cluster job or scientific evaluation was dispatched.

The remaining network gate is validating native SimBench line shunts, transformer taps/losses, background load and PV profiles against independent AC power flow. Then the scientific comparison can be frozen for approval. Its first question is whether feasible depot requests move the price spread across any fleet switching price, with grid-infeasible requests retained. No reinforcement of the depot is assumed.
