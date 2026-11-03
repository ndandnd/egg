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

### Native German network cross-check

The next engineering check used the downloaded MV1 archive with all native static load and renewable injections, no bus depot, a fixed 1.025 p.u. source voltage, and the recorded neutral transformer taps. An isolated SimBench 1.5.3 converter fed pandapower 2.14.11 (module version 2.14.10). Its independent Newton AC solution converged in one run, covered all 299 native node IDs, and respected the native voltage and current limits. It exported 8.088519 MW at the substation, lost 0.220481 MW and had a voltage range of 1.003016–1.044624 p.u. Peak equipment loading was 54.52%. This is a reproducible electrical snapshot, not the observed load or generation on either German price day.

On the conic side the comparison covered 101 distinct connected bus-voltage classes and both ends of all 99 lines and two transformers. It checked real and reactive terminal flows, currents, active loss, and upstream real and reactive power against that one independent reference. The standard series model was extended to preserve cable terminal shunts, no-load transformer losses, and separate terminal ratings. The fixed phase shifts permit positive-sequence radial angle recovery; there is no claim of phase-angle validation here.

| Native conic representation | Electrical comparison at a tolerance of 0.0001 in the reported units | Strict solver and residual gate |
|---|---|---|
| General relaxation, 10 MVA base | Passed. Maximum voltage discrepancy 5.90 × 10⁻¹² p.u. | Failed. Four open cable ends exceeded the relative cone threshold of 10⁻⁵, maximum 6.77 × 10⁻⁴. Native status optimal. |
| Exact passive-end equations, 10 MVA base | Passed. Maximum terminal-current difference 7.96 × 10⁻¹⁰ kA. | Failed. The relative residual fell to 6.57 × 10⁻⁷, but the native status was optimal_inaccurate. |
| Same passive-end equations on pandapower's native 1 MVA base | Passed. Maximum terminal-flow error below 4.51 × 10⁻¹⁰ MW and 2.22 × 10⁻¹⁰ Mvar. | Failed. Native status optimal, relative residual 2.27 × 10⁻⁷, but absolute squared-power residual 3.05 × 10⁻⁷ exceeded 10⁻⁷ in this representation. |

The reduced formulation uses topology alone. At the six native unoccupied open-switch line terminals, Kirchhoff's law fixes series current to the terminal shunt current. Substituting its squared magnitude leaves cable charging in the model and preserves the original AC-feasible plans. The lossless open terminal is unavailable as a priced injection port. These runs reuse the one AC solution, use the same fixed positive upstream price, and retain the original tolerances. At 1 MVA the last absolute residual is 3.05 × 10⁻⁷ MVA², equivalent to 3.05 × 10⁻⁹ on the original 10 MVA squared-power base. A per-unit absolute threshold changes its physical meaning with the base. Any prospective qualification must specify common physical audit units. **All three raw strict verdicts remain unqualified.** The tested engineering conclusion is that electrical quantities agree at this static point. No empirical depot price, sensitivity, support gap, or H1–H4 outcome is asserted.

The independent AC run took 1.88 displayed CPU/3.46 elapsed seconds. General, reduced and reference-base conic checks took 1.24/1.70, 1.35/1.68 and 1.14/1.41 seconds respectively (CPU/elapsed). The isolated compatible converter wheel was SimBench 1.5.3, SHA-256 4728e7d5894e34715436f4e73b6bb479045f37df97188f835330af6c5982b260. Full raw arrays remain in the ignored local src/runs/opf-native-static directory. To reproduce, use a Python 3.12 environment with the versions in the AC receipt. Call qualify_simbench_static.py on the pinned archive, save stdout, then call compare_simbench_static.py with the archive and that saved reference. The variants add --reduce-open-ends and then --base-mva 1. [AC receipt](repair02/simbench_ac_reference_summary.json) · [General](repair02/simbench_static.json) · [Reduced](repair02/simbench_static_open_ends.json) · [Native power base](repair02/simbench_static_native_base.json)
