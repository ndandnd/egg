# Physical context v9: fit-only input inventory

The reviewed38-column featurizer has valid finite fit inputs for all four
predefined folds of each32/64/128TRAIN prefix. Efficiency and charger ratings
do not vary physically; curvature does not vary beyond arithmetic roundoff.
Battery/span and declared movement-window context vary. These are descriptive
input results, not fitted-model, target-domain or generalization results.

The new script `inventory_physical_context_v9.py` ran once in44.108s with local
Python3.12.2/NumPy1.26.4 on macOS ARM64, BLAS/OpenMP1. It did not fit a transform
or model, run a solver/native probe, read target features, or access reserved
DEV/TEST/A6/B3 data. Machine output is
`PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json`, SHA256
`1e096c5e34edab7a142fe0afa9f43f1b5e3b24f07658894967b06f8bc3447963`.

## Per-fold input scope and identity

Each reported fold constructs NativeCase and source0/source1 Market only AFTER
its FIT-group gate. INNER/OUTER groups appear only as excluded identifiers for
that fold. A timetable can legitimately be FIT for another fold; envelopes
below are across overlapping fit-only inventories, not independent pooled
samples or extra training groups. Seeds17/29/43 share these input partitions,
so the inventory is computed once per fold, not counted three times.

The pool's source_inputs embeds source plans and selected movements. The reader
does not call any model loader or decode those values. It byte-hashes the pinned
tables, then whitelist-decodes only top-level scalar registry/identity fields;
excluded values are lexically skipped without JSON materialization. Case
payloads are likewise never decoded. Fit cases/markets are regenerated from the
frozen declared generator, and each exact case/market identity must match its
input-registry header before feature extraction. No observed label, plan topology,
charges, load, SOC, solver status/cost or fitted normalization enters this report.
Source counts describe registered input presence, not label values.

| Prefix | Pool manifest SHA256 | FIT/INNER/OUTER groups per fold |
| --- | --- | --- |
| 32 | 35251cbc8c81787263b51f6259820299e862fba97efa6b8d09c9b1f9c8211842 | 20/4/8 |
| 64 | 64791ec33307612bd8ad7f3c2396c42e0ffdc44717d2c865fe268f61bdab5eb0 | 40/8/16 |
| 128 | d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d | 80/16/32 |

| Prefix/fold | FIT source inputs | Movement rows | Positive-window rows |
| --- | ---: | ---: | ---: |
| 32/0 | 40 | 19734 | 9184 |
| 32/1 | 40 | 18156 | 8446 |
| 32/2 | 40 | 20652 | 9752 |
| 32/3 | 40 | 19734 | 9264 |
| 64/0 | 79 | 40778 | 19114 |
| 64/1 | 80 | 37164 | 17378 |
| 64/2 | 79 | 41002 | 19356 |
| 64/3 | 79 | 38306 | 17898 |
| 128/0 | 159 | 83096 | 39176 |
| 128/1 | 160 | 75146 | 35152 |
| 128/2 | 159 | 83922 | 39634 |
| 128/3 | 159 | 79640 | 37412 |

The registered missing10037/source0 contributes no fabricated input sample.
Machine output binds table/header hashes, every fit/excluded group list, source
sample counts, regenerated identities, feature-matrix hashes and units. It
reports raw population mean/variance(ddof0), equal-group/source/movement weighted
mean/variance, min/max/range, exact/roundoff-constant flags, unique counts,
missing/nonfinite/negative counts and unclipped usable-span ratios above one.
Positive-window statistics renormalize weights on that support. No data from
different prefixes/folds is combined to fit normalization or select features.

## Physical variation and structural zeros

All38columns have zero missing/nonfinite values in every fit inventory. Exact
all-row constants in every fold are intercept1, charging_efficiency0.9,
market_curvature_mean1/900 and market_curvature_spread0. The protocol's units
are retained; reserve_fraction is reserve divided by the operational battery
ceiling, not physical nameplate SOC.

The following are envelopes across the12overlapping fit-only inventories:

| Input/context | Range | Interpretation |
| --- | --- | --- |
| battery_upper_kwh | 100–261.36 kWh | Operational ceiling, three declared profiles |
| usable_span_kwh | 80–232.32 kWh | Positive battery ceiling minus reserve |
| reserve_fraction | 0.111111–0.25 | Relative to operational ceiling |
| movement_energy_over_usable | 0–0.19675 | Local movement consumption only |
| movement_and_next_trip_over_usable | 0.012397–0.587 | Local consumption, no full-route certificate |
| pre/post window bursts over usable | 0–0.47175 | Unknown entering SOC |
| window_connector_hours, positive W | 1/60–12 connector-hours | Declared window duration, not actual use |
| isolated stored capacity, positive W | 1.35–972 kWh | Optimistic single-bus resource opportunity |
| isolated capacity/usable span, positive W | 0.005811–12.15 | Not capped by actual headroom or shared occupancy |
| other candidate overlap, positive W | 15–181 alternatives | Includes mutually exclusive declared modes |

Conditional on a positive charging window, enabled_fraction is exactly1 and
both declared power means are exactly90kW in every fold. Their all-row0/1 or
0/90variation comes from absent/zero windows. Curvature_min is exactly1/900 on
this support. Window_curvature_mean differs by at most4.336808689942018e-19,
with conditional population variance at most5.145672096943624e-38; it is flagged
as roundoff-only, using a descriptive range threshold, without changing any
training/replay tolerance. Its all-row0/bvariation is structural, not changed
supply curvature. Shared connector/grid competition and realized charging still
remain unresolved by these input proxies. Large capacity and alternative counts
do not establish vehicle SOC, fleet demand, route feasibility or an optimum.

## Prospective comparison implications and checks

The planned NEW zero-padded38-input control versus physical38-input model can
study added battery/span and static movement/window information within this
generator. It cannot teach a response to charger-rating, efficiency or curvature
changes absent from its fit inputs. Constant columns should be recorded and
handled with a fit-only unit scale under the separately frozen transform policy;
this inventory neither changes the38-column schema nor drops a column.
Keep the original17prefix exact and its preprocessing identical between arms;
resolve intercept handling explicitly before that future freeze. As already
reviewed, dimensions/declared parameter counts match within the new comparison,
but2688padded-control input weights are inactive, and fan-in initialization differs
from historical17-input v6/v8 models. Historical scores/epochs are contextual
references only. A new resource/parameter budget and prospective feature/architecture
selection protocol remain required; this inventory authorizes no training launch.

Focused command:
`PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_context_v9_inventory.py`
passed14fixtures in0.33s. Tests cover plan-value decode opacity, malformed or
nonscalar registry rejection, exact partition agreement with frozen function
source, fit-only constructor gating, case/market identity failures, structural-zero
versus positive-window statistics, weighted variance/missing/roundoff cases,
exclusive persistence and pinned-table tamper detection. No fixture reads a real
pool, outcome or source plan. No inventory execution failed or required a retry.

SHA256 at completion (also recorded in machine source identity):

- script: `d2c28004bfab9518e944dffaee5bd78aa39c3571b6a55a39893726c4e487c979`
- fixtures: `6a9b7f4aaf1d8fe9b8bb2235b4d61a2e26088ef044ac9be9343f933ac252c19b`
- unchanged reviewed featurizer: `a83c629902a6e704010b02c0c3b22e0ebbdb99351126af20fa78055ee208c33f`

The new report/JSON/script/tests are the only deliverables; existing feature,
model, result, queue, state, handoff and document sources were not edited.
