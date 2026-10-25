# Conditional next decision: two-witness catalog coherence

Prospective design only, 2026-10-25. Based solely on the completed [target-support receipt](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fit_target_support/attempt01/receipt.json) and [identity source map](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fit_target_support/IDENTITY_SOURCE_MAP.md). No original tables, charge/load/cost values or models were accessed; no replay, hashing, computation or solver was run for this note.

## Smallest next question

The support audit admitted all **79 expected pairs**: 48 have differing selected-movement sets and 31 identical sets, both for all movements and the flexible subset. Paired fleet counts are equal in all 79. The intended population remains 80 FIT groups; incomplete `physical_v2_s10037` retains only its observed `source1`, with no imputation or replacement. The receipt explicitly does not establish physical replay, teacher optimality or tariff causality.

Before any new labels or fitting, ask: **among these two already observed full schedules, does each source-context teacher witness minimize the declared objective at its own tariff?** This is a finite-catalog consistency check. Use all 79 pairs, including the 31 identical membership pairs, because their charge schedules can differ. Do not select only cases whose routing changed or whose costs look interesting.

## Fixed witnesses and four valuations

For group `g`, independently replay the two unmodified stored plans `P0,P1` against the **same stored physical case**, using the unchanged physical replay API. Retain their fixed vehicle paths and charge sessions. Recompute their grid loads and operating components; do not trust cached `source_replay`, stored plan load or stored objective. No schedule repair or optimization is allowed. An invalid replay becomes an explicit invalid witness/pair finding; preserve it without replacement or zero cost. Analyze each valid incomplete source witness only for identity/replay bookkeeping, not a fabricated pair.

At source tariff `t∈{0,1}`, evaluate each replayed schedule `j∈{0,1}` as:

`F_t(P_j) = c_j + Σ_h a_th L_jh + ½ Σ_h b_th L_jh²`.

This is integrated supply/planner cost plus operations, **not atomic clearing-price payments**. The two markets have different `a` and the same `b`; verify their previously bound case/grid/market identities again within the new source-bound admission pass. Cross-valuing changes neither schedule nor physics. Keep all four costs and define `D_t = F_t(P1) − F_t(P0)`; positive means `P0` is cheaper at tariff `t`.

Freeze classification tolerance prospectively at **τ = 10⁻⁶ generator cost units**, applied to the exact represented-value cost difference: `+` if `D_t>τ`, `−` if `D_t<−τ`, otherwise a numerical tie. Preserve exact differences even inside the tie band. This is a reporting convention, not a widening of physical replay tolerances or a material-benefit threshold. Parent should confirm consistency with the existing cost/replay API guards before freezing the command. Report:

- Own-context preference reversal: `(sign D0, sign D1)=(+,−)`; each witness wins at its own tariff within the two-schedule catalog.
- Opposite reversal: `(−,+)`; each own-context witness is worse than the other observed schedule at its own tariff.
- Uniform preference: `(+,+)` favors `P0`; `(−,−)` favors `P1`.
- All remaining sign pairs explicitly, including one-sided and two-sided numerical ties.

Additionally flag `P0` own-context dominated when `D0<−τ`, and `P1` own-context dominated when `D1>τ`. These flags can overlap. Record nonnegative **two-witness** own-context gaps `R0=max(0,−D0)`, `R1=max(0,D1)`; neither is a global optimality gap. No new acceptance or training gate follows from their values.

## Components, scale and denominator

For each fixed witness, report fleet count, vehicle-cost component, deadhead minutes/cost, and grid energy in kWh; for each tariff valuation, report linear electricity, quadratic electricity, total electricity and total cost in generator cost units. Preserve absolute differences as the primary result. For an optional common within-group normalization, use `Ebar_g = ¼ Σ_t Σ_j electricity_t(P_j)` and report `D_t/Ebar_g` and `R_t/Ebar_g` only when finite and strictly positive; otherwise mark normalized quantities undefined with no arbitrary epsilon floor. This symmetric scale is descriptive, not the warm study's prior-electricity endpoint or a relative percentage of a control's total bill.

Tabulate the nine tariff-sign combinations and own-context-dominance counts over valid pairs, with 79 expected and every replay/identity failure visible. Summaries weight physical groups equally, not edges or four valuations as independent observations. Keep the incomplete group separate among the 80 intended groups. A descriptive breakdown by the already frozen 48 differing / 31 identical membership strata is permitted, with the full result primary. Do not compute significance, tune tolerance after seeing results, or introduce a winner threshold.

## Exact proposed access expansion and bindings

Candidate row files remain exactly:

- `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl` — expected whole-file SHA256 `faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6`.
- `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl` — expected whole-file SHA256 `7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5`.

These are **copied receipt pins, not hashes computed for this note**. Parent must freeze the new protocol, actual source/API closure, receipt identity and command separately. One future streamed whole-file hash/filter pass reads all TRAIN bytes; transient JSON decoding is allowed solely to route non-FIT rows by group/base, then discard them without semantic inspection. No inner/outer outcome analysis, extra tables or referenced-path following.

For FIT cases retain the existing whitelist: `base_group, base_id, split, generator, physical_profile, case_identity, case` and all nested case fields specified in the identity map. For FIT sources retain `key, base_group, base_id, case_identity, market_identity, market_kind, source, source_plan_hash, selected_movements, source_plan`. **New semantic permission is the unmodified `source_plan` full witness passed to the unchanged physical replay**, in addition to its canonical hash. Independent target-set inspection remains restricted to schema/case identity and vehicle paths. Permit stored load/cost fields only as consistency assertions if the existing replay checks them; derive valuation from recomputed replay output. Do not independently inspect/export raw-solver fields, nested cached replay/roundoff diagnostics, or the separate `source_replay`. The exact charging-record child keys and any additional consistency fields consumed by replay are **not established by the allowed inputs to this note**: the narrow source review below must enumerate and freeze them before any original plan values are opened. This is an explicit remaining admission dependency, not authority for an adaptive field expansion.

The needed prospective source review is narrow: `nr.replay_native` and its pure validation/session/resource helpers, canonical case/plan digests, `physical.market(stored_case,source_kind)`, and `nh.supply` for exact `aL+½bL²`. Confirm their actual return types, charge keys and component accounting; preserve existing tolerances and distinguish exact arithmetic on stored binary-float values from a real-number certificate. Do not import the full training loader, regenerate cases, use cached teacher objectives, or add solver dependencies merely for this audit.

## Interpretation and resource direction

A coherent own-context reversal would show tariff-dependent preference **within this fixed two-witness catalog**, not the benefit of supplying tariff features to a learned proposal. Dominated own-context labels would expose a weakness of these observed incumbents; they would not identify whether stochastic search, budgets, initialization, stopping or another teacher mechanism caused it. Equal memberships can still yield different charging witnesses. Different witnesses confound routing and charging effects, and revaluing fixed schedules is **not** optimized fixed-route QP. Neither successful replay nor catalog minimality proves global optimality. No new theorem is claimed.

Direction only: a single-process CPU-only pass, provisionally at most **5 CPU minutes / 10 wall minutes**, with bounded memory and compact group outputs, should be sufficient to consider after source/file-size review. All parsing, integrity checks and 159 prospective replays must be paid. Parent chooses actual limits and authorization; a timeout/failure is preserved without automatic retry or scope expansion. No MIP/QP call, teacher generation, fitting, inference, new family or replication is included. The endpoint is a small coherence report that informs the next scientific decision, not an automatic launch gate.
