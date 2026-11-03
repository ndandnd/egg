# Fixed-fleet warm tariff replanning: diagnostic result

25 October 2026. The single frozen campaign completed under
[PROTOCOL.md](PROTOCOL.md); [COMPACT_RESULTS.json](COMPACT_RESULTS.json) records
the finalized denominators and readouts. All eight predetermined day priors were
valid. All 168 assigned active cells were attempted and accepted within their
60-second clocks: seven arms ×eight variants ×three native seeds. There were
167 `method_success` outcomes; one CatBoost cell retained an accepted physical
endpoint without that success flag. No cell was excluded. Late/timed-out cells,
configuration failures, missing-acquisition cells and invalid admissions were
all zero. Campaign and frozen finalization checks passed.

The cohort has **four base groups**, 50600–50603. Each contributes two nested
timetable sizes and three repeated solver seeds, giving six paired cells per
group and 24 per arm. These are not 24 independent timetables. The same prior,
fixed active-fleet count, original physics, prior-protected common backbone and
exact candidate quota were shared within each block. Full and fixed_route had
their declared unpruned/fixed-topology meanings. Fleet cost was held constant
and deadhead cost was zero, so paired cost differences are electricity-cost
differences; changed energy demand and charging timing are not separated here.

## Prespecified continuation rule

For learned family L versus control C, the protocol defines
`d = (cost_C − cost_L) / E0`, with E0 the common prior's **late-tariff electricity
cost**. Each group median uses its six cells. The rule requires positive medians
in at least three of four groups and mean d above 0.01 against **both** CoverCA1
and fixed_route, with complete valid inputs.

| Learned family / comparator | Mean d, 24/24 pairs | Positive group medians | Criterion |
| --- | ---: | ---: | --- |
| GNN / CoverCA1 | 0.012318882 | 4/4 | Pass |
| GNN / fixed_route | 0.120116748 | 4/4 | Pass |
| CatBoost / CoverCA1 | −0.010282453 | 2/4 | Fail |
| CatBoost / fixed_route | 0.097515413 | 4/4 | Pass |

Thus **GNN passes the diagnostic continuation rule; CatBoost does not**. For
example, the GNN–CoverCA1 contrast is 1.2318882 percentage points on the scale
normalized by prior electricity cost. It is not a percentage reduction using
CoverCA1's bill as denominator. The fixed_route contrast is 12.0116748 points
on that same E0 scale. These are means of paired ratios, not ratios of pooled
mean costs or percentage reductions in the total prior bill.

## Descriptive cost context

The compact export additionally supplies these **post hoc descriptive** means,
with equal weight for all 24 cells per arm, in generator cost units:

| Arm | Mean integrated system cost |
| --- | ---: |
| GNN | 924.670389 |
| CatBoost | 946.224409 |
| CA1 | 934.199323 |
| CoverCA1 | 931.252184 |
| random | 936.924875 |
| full | 988.395833 |
| fixed_route | 1010.152190 |

This finite-budget ordering is not an optimality or superiority certificate.
The objective is operating cost plus integrated supply cost
`a'L + 0.5 L'BL`, not atomic uniform-price payment. No dollar interpretation is
assigned. Parent-reported external process measurements were 6,796.46 CPU /
6,952.21 wall seconds for the campaign, including prior acquisition and failed
work, and 1.54 CPU /1.64 wall seconds for finalization. The small compact export
is separate administrative work; the parent reconciles it in the resource
ledger. These are process measurements, not exact whole-session review costs.

The result supports a narrowly specified next research step: a separately frozen
follow-up on additional groups, retaining both conventional controls and both
learned-family results. It does not establish price-information causality,
generalization, state-of-the-art performance, cold-start speedup or a full-problem
certificate. Both learned models see a but not b; a comparably selected trained
tariff-blind model and fixed-pool interventions remain missing. The generator
shares TRAIN-derived regimes, and its 40/80 variants scale charging power from
180 to270 kW. Prior-use checks were not globally exhaustive. Preserve all raw
data, the unsuccessful method flag and the original frozen gate without retry
or retrospective threshold changes. No new computation was performed to write
this note.
