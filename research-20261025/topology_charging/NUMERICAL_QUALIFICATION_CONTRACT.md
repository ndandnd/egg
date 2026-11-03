# Numerical qualification contract for the topology/charging pilot

Source-only review, 2026-10-25. No data, receipts, rows or model values were read; no imports, hashes, tests or solver calls were executed. Proposed caller/report policy only: the existing helper remains unchanged, and parent freezes actual numerical interpretation before dispatch.

## What the existing helper establishes

Use the source-bound [warm-replication helper API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:85). It validates the supplied case/market and fallback, fixes all route binaries, copies original indexed rows/bounds/objective, and optimizes a continuous fixed-route QP once. The copied matrix/objective contract has an explicit `passed` flag [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:286). It accepts generic NativeCase data; a successful run on a new case is still required, not implied by this source review.

Actual settings are Method0, Threads1, declared seed, NonConvex0, FeasibilityTol1e−9, OptimalityTol1e−9 and BarConvTol1e−10. Settings are checked; native TimeLimit is the remaining time until the absolute native cutoff. The original Python-MIP model is only the matrix source; the helper calls `qp.optimize()` once. After native return it uses the later admission deadline for extraction/replay. Caller owns inclusive process-return/publication admission [settings](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:167), [one call/deadlines](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:317).

`qp_success=True` requires native `OPTIMAL` **and** a fully admitted physical candidate. TIME_LIMIT, SUBOPTIMAL, ITERATION_LIMIT, INTERRUPTED and WORK_LIMIT can supply a provisional incumbent with `SolCount≥1`; they do not yield `qp_success`. Raw finite values go through unchanged extraction and independent replay. Selected IDs, fleet and identity are checked. Failures/disposal failures prevent final candidate admission. Preserve exact status and failure stage rather than collapsing these cases to “solved” [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:347).

## Exact fields available—not guaranteed runtime values

`_attribute` calls `getAttr`, retains finite numeric values (or converts nonnumeric values to strings), and returns **None on exception/nonfinite numeric values** [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:75). Preserve nulls and do not coerce unsupported attributes to zero.

| Packet | Fields to preserve |
|---|---|
| Native point/status | `stats.Status`, `SolCount`, `ObjVal`, `native_optimal` |
| Attempted bound attributes | `stats.ObjBound`, `native_lower_bound`, `lower_bound_scope` |
| Attempted quality | `MaxVio`, `ConstrVio`, `BoundVio`, `DualVio`, `ComplVio`, `ConstrResidual`, `DualResidual` |
| Work/cost | `Runtime`, `Work`, `IterCount`, `BarIterCount`, `entered_monotonic`, `returned_monotonic`, `wall_s`, `cpu_s`, `native_overrun_s` |
| Actual settings/identity | `solver`, `package_version`, `native_version`, `threads`, `seed`, `Method`, `FeasibilityTol`, `OptimalityTol`, `BarConvTol`, `TimeLimit` |
| Cost agreement | `raw_objective_exact`, `replay_objective_exact`, `native_to_physical_cost_delta`, `raw_to_physical_cost_delta_exact` |
| Candidate/retention | `candidate_bill_exact` if admitted, `fallback_bill_exact`, `true_bill_exact`, `selected_source`, `used_fallback`, `qp_success`, `qp_candidate_admitted` |
| Admission/failures | `copy_contract`, `failures`, `config_failure`, `fatal_contract`, `native_calls`, `native_call_attempts`, `status`, `admitted_monotonic`, `returned_monotonic` |

`ObjBound` and `native_lower_bound` are two attempted reads of the same attribute, **not independent evidence**. This source does not establish that ObjBound is supported for the installed continuous-QP Method0/status, nor that a finite value is a rigorous bound on exact physical costs. Existing top-level `global_lower_bound` is always null and `certificate_claim=False` [initial packet](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:92), [attribute collection](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:336). Keep these unchanged. Do not invent a bound from ObjVal or native OPTIMAL, and do not import a MIP-gap assumption into this continuous QP.

## What the source objective guards mean

Let `R` be `raw_objective_exact` (the copied objective evaluated exactly on stored native variable values), `N` the native ObjVal point, and `C` the independently replayed physical candidate bill. Source checks are:

1. `abs(float(R)-float(N)) <= nr.OBJECTIVE_TOL` using Python float subtraction; violation is `CopyContractError`.
2. `abs(C-R) <= Fraction(nr.OBJECTIVE_TOL)` using exact represented-value arithmetic; violation rejects the candidate.

`nr.OBJECTIVE_TOL` is float `1e−6`. Its Fraction conversion is the **exact binary-float value**, not the separately chosen decimal `Fraction('0.000001')` fixed-column reporting band. Both objective guards are in generator cost units. Physical ENERGY_TOL/TIME_TOL and extraction correction budgets remain unchanged and serve different checks [constants](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:20), [agreement checks](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:365).

For reporting, retain the actual exact `C−R` and `C−Fraction.from_float(N)` when N is finite. A conservative **source-agreement envelope** between C and N can include both source guards plus float-conversion/subtraction residuals: with `Q` the exact Fraction of a float, `f=float(R)`, `s=f−N`, `ρ_R=|R−Q(f)|`, `ρ_s=|Q(s)−(Q(f)−Q(N))|`, use `ε_agree=2*Q(nr.OBJECTIVE_TOL)+ρ_R+ρ_s`. This only bounds agreement among those reported points when both guards passed. It is **not an optimization-error bound** on `C−V_r`, and must never become an automatic route-ordering certificate.

OptimalityTol and dual/primal violation attributes describe numerical termination/quality; this source supplies no conversion of them into an absolute objective-gap bound. The earlier exact fixed-column `10⁻⁶` classification band therefore cannot establish the accuracy of QP route preferences. The generic `nr.admit_bound` helper is **not called here**; its finite-bound/guard checks cannot manufacture a missing QP bound [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:696).

## Retention discrepancies and caller checks

The helper returns the lower of fallback and admitted candidate. Thus `qp_success=True` can coexist with `used_fallback=True`; `true_bill_exact` alone is not the QP candidate value [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/qp_control.py:399). Proposed caller policy: save `C`, original fallback `B`, selected physical bill `U`, and `N` separately. Record `C−B`. If native OPTIMAL candidate exceeds its already feasible fallback by more than the source-agreement envelope above, flag `optimal_candidate_fallback_discrepancy` and mark the optimum estimate unresolved; do not silently qualify the retained fallback as V. Even a smaller discrepancy must remain visible and is not proof of exact optimality. No retry/helper patch follows from the flag.

Independently replay the selected returned plan; compare its physical identity, fleet, exact recomputed bill and canonical ordered paths with the fixed witness. Canonical paths should be sorted collections of `(tuple(trips), tuple(movements))`, ignoring only vehicle-label permutation. The helper checks selected-ID sets/fleet; it does not itself compare full path collections. `pf.recover_paths` rejects branching/disconnected/duplicate selected flow [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:109); the prior warm caller already adds path comparison/replay [source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/warm_replication/run.py:434). Same-membership controls must have canonical identity checked, not presumed.

## Preference policy to freeze

Default report: numerical native-OPTIMAL/physical-admission status, retained feasible costs and exact **point differences**, with route ordering explicitly unresolved wherever optimization/admission uncertainty lacks a justified bound. Do not call unresolved differences exact ties or infer an error bar from OptimalityTol. If an actually supported fixed-route lower-bound attribute and its numerical meaning can be justified prospectively, parent may freeze a numerical interval-separation rule with source/replay uncertainty included. A finite attribute alone is insufficient; no exact/global routing certificate follows. Unsupported bounds remain null and cannot be replaced by arbitrary point±epsilon intervals.

Identical canonical routes have the same ideal fixed-route value at a given tariff. Above-envelope discrepancies between their admitted results are unresolved numerical/qualification findings, **not tariff-dependent route preference**. Different fallback charging witnesses and retention must remain separately visible. Preserve all planned cells, failures and incomplete comparisons; no new performance threshold, adaptive solver call or automatic scientific promotion is authorized by this contract.
