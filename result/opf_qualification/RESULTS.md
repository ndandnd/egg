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
