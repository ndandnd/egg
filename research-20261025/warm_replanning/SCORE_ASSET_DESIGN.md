# Frozen scoring adapters for warm tariff replanning

Static prospective design, 25 October 2026. No imports, inference, fitting, tests,
asset hashing, solver calls or execution were performed to prepare these files.
The parent owns cohort, tariff construction, warm incumbent, budgets, actual byte
verification and numerical driver. Only movement IDs from the prospectively
acquired common prior are accepted; no old outcome-selected plan or saved score
is an input here.

## API and fixed decisions

`scoring.select(case, a, b, arm, *, root, asset_lock, case_key, random_seed,
common_prior_ids=None, verified_asset_sha256=None, check=lambda: None)` returns original-order scores
where applicable, retained IDs/mask, base B/warm Bw/original K, source selection ledger and paid timings.
Canonical arms: **GNN, CatBoost, CA1, CoverCA1, random, full**. Exceptions fail the
decision; no model substitution, adaptive quota, rescoring retry or fitting.

`asset_lock` is the already-read `research-20261017/local-assets-v3.json`.
`expected_assets(asset_lock, root)` returns the five path/digest expectations and
checks their agreement with that lock. This checks metadata, **not asset bytes**.
The caller must hash the used model/preprocessing/metadata files in its one
metered preflight batch and pass that resulting absolute-path mapping as
`verified_asset_sha256`. Learned calls refuse absent/mismatched verification.
There is no recursive artifact discovery, historical source audit or training
data access. Verify the current scoring source separately in the parent's source
inventory; old training-source hashes are provenance, not hashes of current code.

Each learned decision invokes the existing API anew. Preprocessing and model
objects are loaded again, even if the other tariff/seed just used that arm.
Python-library imports and OS file caches can remain warm; “cold load” here means
fresh file-backed model/preprocessor objects, not an asserted cold OS cache.
The decision clock must begin before adapter import/call. Adapter totals include
lazy imports inside the call, feature generation, loading, inference and selection;
the caller additionally charges initial adapter import. Existing
CatBoost sub-timings have their original narrower definitions. GNN exposes one
combined load/features/graph/inference time; no invented breakdown is provided.

## Selected asset expectations copied from existing lock metadata

These digests were read as text from `local-assets-v3.json`, not recomputed.

| Asset | Expected SHA256 |
| --- | --- |
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/graph_attention_selected.npz` | `2ce500d711540284e62f0f365475892aa318d79601b5f74b5f10a7caed749f6d` |
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/fit_only_preprocessing_and_groups.json` | `f4a5145f9b89ca487f52905d2cda153dd6bc1d1a930d441b577ec9357eae8095` |
| `research-20261017/classical-training/attempt1/catboost/model.cbm` | `1b3d6e00149aa4f712d84b8ba0e859496b295f9f266c593cf62164f92bbac237` |
| `research-20261017/classical-training/attempt1/catboost/metadata.json` | `9f1fef8b98993e461d58d4ddb3e6bc061ac692159c922171ac0f09de8cc62c73` |
| `research-20261017/classical-training/attempt1/catboost/preprocessing.json` | `5c0ac1277ab68024ddc58ad468cf35d2fca18959906ae739bd946b21512f1ea6` |

The CatBoost root is relative to the supplied worktree; the historical lock uses
this worktree's absolute path. The GNN root is the exact historical external
selected-model folder above. The adapter rejects substituted roots/digests. The
CatBoost model metadata records seed17, selected candidate1/depth6, and historical
fit/inner-group selection; none is reselected using replanning outcomes.

## Exact unchanged learned transform

GNN delegates to
`experiments.codex_local_campaign.v8_scores(case, a, lock['v8_root'])`.
CatBoost delegates to
`experiments.codex_train_classical.score_case(case, a, lock['classical_root'], 'catboost')`.
Both use `egglab.learned_proposals.edge_features` in original movement order,
with these seventeen columns:

`pullout, direct, depot, pullin, start_time, end_time, duration, movement_energy,
before_energy, after_energy, charge_window, window_price_mean, window_price_min,
market_mean, market_spread, same_place, intercept`.

The first four are kind indicators. Start/end/duration divide by
`max(recharge_deadline_min,1)`; movement and adjacent-trip energies divide by
`max(battery_kwh,1)`. Charge-window duration divides by the same horizon. Depot
windows use the declared depot-split gap; pullin windows span terminal arrival
to recharge deadline. Prices in those windows use overlap-duration-weighted
means and the minimum among positive-overlap periods. Empty/noncharging windows
use zero duration, global arithmetic mean and global minimum. The remaining
features are global arithmetic price mean, max-minus-min spread, first-leg
origin equals last-leg destination, and constant one. No clipping, refitting,
new price normalization or curvature feature is added.

Both standardize exactly as `(x - mean_fit_only) / scale_fit_only` using their
own pinned preprocessing file. GNN builds the existing sorted-trip graph with
separate depot source/sink, preserves parallel movement modes and float64
tensors, configures deterministic one-thread torch execution, and returns raw
logits under `no_grad`. CatBoost retains its frozen feature-order check and
returns `RawFormulaVal` with `thread_count=1`. Raw logits are ranked directly;
no calibration or probability transform is introduced.

**Both learned scorers observe a, not b.** Therefore curvature-only changes
cannot change their scores with the same case/a/model. The downstream charging
solver may still respond to b; that response is not learned-score adaptation.
Day→late a changes are supplied by the caller on each fresh call.

## Exact common B/K and nonlearned arms

Warm protection policy is `warm-replanning-fixed-model-prior-protected-Bw-exact-K-v2`.
Every restricted arm preserves the original universe and all boundary modes.
`classical_controls.select_connections` constructs common price-blind B from
the existing `codex_offline_rank.heuristic`: descending score then movement ID,
with up to three incoming/outgoing choices per trip. With M original flexible
direct/depot modes, `K=min(M,max(ceil(0.3*M),len(B)))`. B is protected and exactly
K flexible modes are retained. `ordinary_selector_ledger` preserves that unchanged
base selector result. No previous selected pool or old score is reused.

The caller must explicitly supply the **known common physically valid prior's
movement IDs** for every restricted warm arm. Acquisition supplies `[]`; omission
(`None`) is refused for restricted arms. Let `P` be those IDs intersected with the
original flexible modes. Protect **Bw=B union P** in every restricted arm, without
changing original K. Record `base_backbone_ids`, `warm_backbone_ids`,
`prior_protected_flexible_ids`, `rank_fill_ids` and `ordinary_selector_ledger`.
`backbone_ids` aliases warm Bw so the driver's cross-arm contract checks the
actual common warm protection. If Bw exceeds K, preserve
`design_failure_warm_backbone_exceeds_K`; there is no native dispatch or larger
quota. Every successful selection contains the entire known prior, since all
boundaries are also retained. This uses the prospectively permitted operational
prior, not old outcome-selected plans. The prior is not used to alter scores.

- **GNN/CatBoost/random:** get original B/K and fresh rank order from the common
  selector, protect Bw, then fill that order to exactly original K.
- **CA1:** call the unchanged `classical_controls.ca1_score`, get the common base
  selector ledger, protect Bw, then fill in CA1 order. CA1 consumes current a and b
  and preserves the stress/proportional-charging proxy used by density_control.
- **CoverCA1:** also freshly compute
  `matching_pool/pool.py:candidate_pool`. Protect Bw union the three frozen
  route-only cover pools C, then fill in CA1 order to unchanged K. If Bw fits but
  Bw union C exceeds K, return `design_failure_cover_union_exceeds_K` and prohibit native
  dispatch. Do not enlarge K or fall back to another arm. The cover helper still
  admits only 40/80 trips; it is not generalized here. It is not a GRASP replica.
- **random:** freshly order SHA256 keys of
  `warm-replanning-priceblind-random-v1|case_key|random_seed|movement_id`, breaking
  hash ties by ID, and assign scores `-rank`. Tariff, stage, ordinal and previous
  outcomes are absent, so a fixed case/seed has the same pool across day/late.
- **full:** retain the entire original universe, without a quota or backbone
  construction. Report `K=None`/`B=None`; it is explicitly unrestricted.

The parent must compare base B, warm Bw, original K, prior protection and
boundaries across restricted arm receipts and stop on disagreement. The adapter
no longer imports density_control/selector.py: it reuses the same existing CA1
scorer/common selector and frozen cover helper while adding only this distinct
warm-protection layer. Selection is a candidate mask, not a new feasibility or
full-problem bound certificate. Prior replay, native mask enforcement, hints,
durable deadlines and all charging physics remain the driver's duties.
