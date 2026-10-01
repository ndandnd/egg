# Independent review of the first compact native-hull qualification

**PASS:** all eight fixed compact hull states have reconstructed numerical certificates under the unchanged 1e-4 width rule. Scientific source is frozen at `72a1f715e9e6714746f9c0638c50d2cba6bfcfdb`. The immutable original archive contains 62 files and 750,529 bytes; original manifest SHA-256 is `5e8f4c234c79002c864299bfdba999349d2658b1f1f0b321f6f87e7acb8e7272`. All original bytes and the raw manifest were verified before and after this audit. This derived review has its own manifest.

The reviewer did not author the compact hull integration, import any scientific implementation, instantiate a native model or execute an optimizer. The hull/LP/simplex/Fenchel/transfer reconstruction is independently authored by this reviewer. The flat compact raw-variable decoder is reused from the earlier independent compact physical-model audit and was inspected here. Its author independently reviewed the root-authored physical model, and later authored this integration's small dispatch adapter; this provenance is disclosed rather than describing every helper as newly authored by the present reviewer. Physical SOC/session replay comes from the same independently authored fixture core used for the indexed audits. The four included scripts use only Python's standard library and each other.

## Complete result and accounting checks

All 36 native calls were reconstructed: 21 compact complete-fleet pricing calls and 15 restricted LP masters, with 378 raw compact variable values and 145 raw master values. All native statuses in this archive are OPTIMAL and the recorded backend identity is CBC. The audit checks 21 complete physical witnesses, 45 charging sessions and 171 SOC events. It independently reconstructs all 21 global linear pricing minima and all 15 exact restricted PWL LP minima.

Every one of nine accepted rational pairwise transfers, 24 pool checks and 15 polishing phase lifecycles is checked. Weights, positive mass, deterministic entering/leaving indices, exact gradient/scores, direction, line minimizer, quadratic decrease identity, serialized-price conjugate, bit count and time/step caps must all reconstruct. Raw and polished feasible upper candidates are streamed into the independently reconstructed best upper; every global lower has fresh current-state native pricing provenance. Complete worker/controller/supervisor receipts and unchanged dependency hashes are checked. No inherited bound is used as a new-state lower bound.

| State | Known hull value, displayed | Pricing calls | LP masters | Transfers | Saved exact width, displayed |
|---|---:|---:|---:|---:|---:|
| nominal_cold_s0 | 94.8875 | 3 | 2 | 1 | 1.0000000189558377e-6 |
| nominal_cold_s1 | 96.1875 | 3 | 2 | 1 | 1.0000000000287557e-6 |
| nominal_cold_s2 | 94.8875 | 3 | 2 | 1 | 1.0000000189558377e-6 |
| nominal_retained_s0 | 94.8875 | 3 | 2 | 1 | 1.0000000189558377e-6 |
| nominal_retained_s1 | 96.1875 | 1 | 1 | 1 | 1.0000000000287557e-6 |
| nominal_retained_s2 | 94.8875 | 1 | 1 | 1 | 1.0000000189558377e-6 |
| joint_cold | 103.45952216066482 | 4 | 3 | 2 | 9.9999998151409050e-7 |
| fixed_reserve_cold | 99 | 3 | 2 | 1 | 9.9999999747524270e-7 |

The exact binary-rational width range displays as **9.999999815140905e-7 to 1.0000000189558377e-6**. Maximum rational numerator/denominator length was 372 bits, below the fixed 8,192-bit cap. Exact endpoints, weights, supporting-price references and per-step details appear in `audit-result.json`.

Compact formulation identity is checked in state identities, state/pricing trace metadata, returned results, physical plans, raw flat snapshots and column source metadata. Both retained transitions import exactly the preceding two-column compact pool; predecessor success, exit, non-timeout status and complete nonzero accounting are rechecked. Every imported column is physically replayed. Only complete physical columns are retained; prices, bounds, simplex weights and tangent history are fresh. New-state oracle identity cannot silently cross the indexed/compact boundary.

## Independent mathematical references

These are the unchanged synthetic two-service fixtures. One used bus joins both 15-kWh services; two used buses split them. For efficiency eta, complete recharge is T=30/eta. With early grid energy x, both branches require

`max(0,T-late_capacity) <= x <= min(early_capacity,15/eta)`.

The one-bus branch additionally requires `x >= (30+reserve-B)/eta`; exclude an empty interval. These bounds follow from the event SOC and full replenishment balances. The A-service bus alone can use the early window. The remaining individual terminal deficits are nonnegative and their total fits the common finite late connector; serial terminal charging constructs each branch point. Positive-duration services and the declared DAG leave no other complete used-fleet structure. Thus every linear pricing optimum occurs at an endpoint, and the full projected hull is the convex hull of these physical branch endpoints. The analytical nonlinear optimum is attained on a lower hull edge in (early energy,intrinsic cost), so exact endpoint-pair minimization is complete. The auditor derives exact supporting prices and checks global minimum-score minus conjugate equals the analytical hull optimum for binary-stored market coefficients.

For actual saved columns, floating projections are not assumed to lie on an ideal total-energy line. One/two-column PWL minima are reconstructed by all breakpoints and endpoints. The joint state's three-column master is checked by eliminating the third weight and enumerating all exact feasible vertices of the resulting four-variable LP (two weights and early/late epigraphs). The two other epigraphs are identically zero. Restricted quadratic minima additionally check the interior stationary point and every simplex edge. This is exact finite linear algebra and continuous convex minimization, not a sampled charging grid.

The flat raw decoder independently partitions selected movement arcs into service-covering paths and checks path-count, in/out flow, selected-mode SOC equalities, inactive big-M inequalities, reserve/battery constraints, terminal recharge, charge ownership, shared elementary-interval capacity, load links, variable domains/integrality and complete row/variable counts. It reconstructs raw objective values and exact normalization/serial-decoding ledgers, then the separate physical replay checks all sessions and event SOCs.

## Numerical scope

No physical schedule is repaired, rounded to an ideal solution or rationalized. Fraction arithmetic is exact arithmetic on saved finite binary values, not an exact native physical solver. The unchanged physical/objective tolerance is 1e-6, time tolerance 1e-7, and the explicit fleet normalization/capacity-excess budget is 1e-8 kWh. The displayed maximum raw compact constraint residual is 1.3322676295501878e-14; maximum raw LP residual is 2.0240559557177756e-14. These diagnostic maxima span different constraint units. Maximum native PWL objective discrepancy against the independently exact LP minimum is 3.898927808787501e-14. Maximum combined physical correction is 1.7763568394002505e-15 kWh.

Some nominal physical projections give saved upper objectives about 3e-14 below the ideal analytical optimum, which is possible under the existing floating witness policy. Known analytical target comparison therefore uses the same explicit 1e-10 comparison allowance as the indexed audit; it is not a changed physical tolerance and does not modify bounds or final width. Numerical certificate claims remain solver-conditioned and tolerance-conditional. Exact ideal cyclic theory, exact stored-number accounting and native floating physical feasibility are distinct claims.

This gate establishes correct small-fixture compact integration and retained-state accounting. It is not a general convergence, speedup or operational-data hull result. The original indexed V1 failures and V2 success remain unchanged separate evidence. Observed wall times are consistent with the frozen caps; this audit reconstructs their records rather than independently authenticating clock readings.

## Corruption controls and reproduction

All **42 in-memory corruption controls** were rejected. They include unsupported bounds, raw LP mappings/weights, tangent changes, false pool/global certificates, SOC corruption, altered pairwise updates/caps/phase ownership, incomplete or stale predecessors, wrong compact result/state/request/raw identities, invalid flat service coverage/SOC/interval capacities, deleted positive sessions, correction-ledger changes and foreign-oracle retained imports. No raw files were altered. Separate output-safety checks refused both a repository documentation path and an existing external report without changing them.

Run from any working directory with a new report path outside all repositories:

```sh
python3 -B /path/to/egg/result/native_pathflow_hull/20260927-attempt1/review/audit_native_pathflow_hull.py \
  --attempt /path/to/egg/result/native_pathflow_hull/20260927-attempt1 \
  --repository /path/to/egg \
  --out /tmp/egg-compact-hull-new-audit.json
```

The repository must retain frozen commit `72a1f715e9e6714746f9c0638c50d2cba6bfcfdb`. Current scientific working-tree source is never imported. A portable run from `/private/tmp` passed in about 0.41 seconds. The CLI refuses existing outputs, symlink outputs and outputs inside any detected Git repository. This review's separate manifest covers the four scripts, report and review text, excluding itself; the original raw manifest remains untouched.
