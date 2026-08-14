# GIRO/Transdev dataset handoff for EVSP research

> Provenance: supplied by the project owner on 2026-08-14 (authored in the
> `evsp-dr` repository context; the `README.md` / `EMAIL_EXCHANGE.md` links at
> the bottom refer to that repository, github.com/ndandnd/evsp-dr, not this
> one). Stored here because `egg` experiments may freeze a subset of this
> data. **Confidentiality: the source material is labeled C1 - Internal.** Do
> not publish raw workbooks, PDFs, notes, email text, or contact details
> without a separate data-sharing review; this document paraphrases technical
> content only. Body below preserved as supplied.

## Read this first

This repository contains two electric-bus scheduling exports supplied by GIRO and
Transdev:

- **Partille (`Par`)**, a Monday-Thursday schedule from December 2023; and
- **Frölunda (`FDL`)**, a Monday-Thursday schedule from November 2024.

The files are useful for electric vehicle scheduling problems (EVSPs), but they
are not a ready-made benchmark. Most importantly, `VehicleDetails` is an export
of an already solved GIRO/HASTUS vehicle schedule, not a raw unscheduled
timetable. A researcher can recover the fixed passenger-trip demand from it,
but must make explicit choices about weekday variants, deadhead completion,
vehicle physics, and charging rules.

The source correspondence labels the material **C1 - Internal/Intern**. Do not
publish the raw workbooks, PDFs, notes, email text, or contact details without a
separate data-sharing review. This handoff paraphrases the technical content.

## What was supplied

| Source file | What it contains | How it can support an EVSP |
| --- | --- | --- |
| `Par_VehicleDetails.xlsx` | Partille's solved vehicle blocks: 2,204 activity rows, including 987 `Regular` rows | Fixed passenger trips, observed block assignments, service energy, charging activities, SOC traces, and a feasible reference schedule |
| `FDL_VehicleDetails.xlsx` | Frölunda's solved vehicle blocks: 2,559 activity rows, including 1,393 `Regular` rows | Same uses as Partille, with more vehicle heterogeneity and route-dependent energy assumptions |
| `Par_DHD.xlsm` | 3,713 directed deadhead records among 272 exact places | Deadhead time and distance, including time-of-day overrides |
| `FDL_DHD.xlsm` | 3,865 directed deadhead records among 277 exact places | Same, covering all Partille pairs plus additional Frölunda-related pairs |
| `Par_Notes.docx`, `FDL_Notes.docx` | Vehicle, battery, charger, SOC, resource, recharge, blocking, and route-specific settings | Model assumptions that are not present in the trip CSVs |
| `Transdev Electric Partille Mon-Thu december 2023.pdf`, `Transdev Electric Frölunda Mon-Thu November 2024.pdf` | Narrative descriptions and screenshots of the schedules | Operational context, fleet availability, charger geometry, and scheduling rules |

The `.xlsm` deadhead files contain no VBA project. Their data can be read as
ordinary workbooks. The `VehicleDetails` workbooks retain broken links to
creator-local Windows resources, but their displayed values are materialized;
there is no need to refresh the links.

## Recovering the trip set

GIRO/Transdev's explicit instruction was:

1. disregard columns A-H of `VehicleDetails`; and
2. retain rows for which column I, `Identifier`, is `Regular`.

Those rows are the fixed in-service trips. Other identifiers describe activities
in GIRO's solution, such as preparation, pull-out, pull-in, deadheading, waiting,
and recharging. They are useful for reconstructing and validating the historical
blocks, but they are not additional passenger trips.

The common 24-column schema is:

| Columns | Meaning |
| --- | --- |
| `VehicleTask` | GIRO block/duty label in the supplied solution; useful as a historical assignment, not as a property of the trip itself |
| `From`, `Start`, `End`, `To`, `Duration`, `Distance`, `Garage` | Repeated block-level summary (columns A-H); do not use these fields as the individual trip record |
| `Identifier` | Activity type; `Regular` selects passenger-service trips |
| `Route`, `Direction` | Route and direction for a service activity |
| `From1`, `Refer.` | Exact start place and its shared GIRO reference place |
| `Start1`, `End1` | Activity start and end times |
| `To1`, `Refer.1` | Exact end place and its shared GIRO reference place |
| `Duration1` | Activity duration in GIRO's hours-and-minutes display |
| `Lay` | Actual following layover in the exported solution, not a general minimum connection time |
| `SOC before`, `SOC after` | State of charge percentages in the solved schedule |
| `Recharge kWh` | Energy added during a recharge activity |
| `Distance1` | Activity distance in km |
| `Usage kWh` | Energy consumed by the activity |

Two time conventions matter:

- Service-day times may exceed 24 hours. For example, `24:06` is 00:06 on the
  following civil day but remains part of the same service day.
- A duration displayed as `0.06` means 6 minutes, not 0.06 decimal hours.

For a reusable trip identifier, retain the source row number and a day/variant
manifest. A tuple such as `(Route, Direction, From1, Start1, End1, To1)` is a
useful audit signature, but should not be assumed globally unique without
checking. `VehicleTask` should not be embedded as a permanent trip attribute if
the research question permits reblocking.

## The weekday-variant trap

The Partille workbook is not one unambiguous operating day. It contains 42
literal `VehicleTask` labels but only 40 base block IDs. Two pairs are weekday
variants:

- `13316m` and `13316uwt`; and
- `13324muw` and `13324t`.

The 987 `Regular` rows across all labels contain only 949 unique service-trip
signatures; 38 rows are duplicated through these alternatives. Therefore,
simply taking every `Regular` row constructs a union of weekday alternatives,
not a defensible single-day demand set. The suffix definitions were not supplied
in the files and should ideally be confirmed with GIRO.

For a general EVSP benchmark, choose one variant from each pair, save a manifest
of source rows and chosen variants, and report the resulting trip count. Better
still, request a raw day-specific timetable export. Do not treat
`Practice_43bus.csv` as a canonical full day: it contains the combined 987-row
multiset and its filename does not match the 40 base blocks or 42 literal labels.

## Deadhead data and time intervals

The original DHD workbooks are sparse, directed operational matrices. Duration
is in minutes and distance is in km. A row has base values and may have Peak,
Morning, or Night overrides. The interval rules embedded in the workbooks are:

| Interval | Deadhead start time |
| --- | --- |
| Peak / 1st | 06:30-08:40 or 15:00-18:30 |
| Morning / 2nd | 08:41-09:30 or 14:30-14:59 |
| Night / 3rd | 00:00-05:59 or 21:00-23:59 |
| Base | Other times, or when the selected override is blank |

Apply the interval clock modulo 24. Thus a deadhead at service time `24:06`
uses the 00:06 Night value. This explains the supplied `GMV_G -> PARX` pull-in:
GIRO used reference link `7581 -> PARX`, whose Night duration is 11 minutes
rather than its 13-minute base duration. The sender asked GIRO to validate that
explanation, but the supplied thread contains no later confirmation.

Do not assume symmetry or the triangle inequality. In Partille, hundreds of
reverse-direction pairs differ. Do not interpret a missing pair as proven
infeasibility either: the shared Gothenburg matrix was curated over more than 20
years for four independently scheduled contracts. Some irrelevant cross-contract
pairs were never created, and some useful within-contract pairs may also be
absent. Important links were often estimated with GIS and bus test runs;
less-important links could use GIS alone.

## The "zipcode" reference abstraction and teleportation

`Refer.` and `Refer.1` group several exact places under one shared GIRO reference
place. They behave roughly like a zipcode, zone, or complex rather than an exact
stop. Examples include:

- `PC_3`, `PC_5`, `PC_6`, `PC_7`, `PC_9`, `PC_10` -> `13215`;
- `HED_D`, `HED_E`, `3127L` -> `3127`;
- `ÖS_H`, `ÖS_J`, `7880C` -> `7880`; and
- `JON_A`, `JON_B` -> `13410`.

Transdev explicitly approved substituting the shared reference place when an
exact-place deadhead link is missing. That supports a reference-level fallback.
It does **not** establish that all motion within a reference takes zero time and
zero energy.

The derived EVSP-DR data goes further: exact places are mapped to references,
movement between places sharing a reference is treated as `(0 minutes, 0 kWh)`,
and cross-reference pairs are made unordered/symmetric. This is the project's
accepted **zipcode teleportation** simplification. It can connect, for example,
`HED_E` to `HED_D` for free even though the historical schedule records a
2-minute, 0.05-km movement using about 0.1 kWh.

A generic dataset user should choose and disclose one of these fidelity levels:

1. **Highest fidelity:** exact, directed, time-dependent DHD arcs.
2. **Reference fallback:** use exact arcs when available and a directed
   reference-place arc only when the exact arc is missing.
3. **Zone abstraction:** map every endpoint to a reference, allow free internal
   movement, and optionally symmetrize cross-zone arcs.

Free same-zone travel, symmetrization, averaging reverse directions, and dropping
time intervals are four separate assumptions. GIRO/Transdev approved only the
reference substitution, so do not attribute the stronger choices to GIRO.

## CSVs in `data/`

The original evidence is in this directory's workbooks/documents. The CSVs one
level above are derived artifacts of different ages and reliability.

| File or family | Meaning and recommended use |
| --- | --- |
| `Par_VehicleDetails_Updated.csv` | Near-source Partille activity export: all 2,204 rows and 24 source columns, plus `count_trip_id` and `Ordered_Trip_ID`. Use for convenient analysis, but audit against the workbook when exact-place lineage matters. `count_trip_id` is only populated on a historical subset. |
| `Par_VehicleDetails_1bus.csv` | Early all-activity extract for historical task `13301`. This is a one-block diagnostic, not a contract-wide input. |
| `Par_Routes_For_Code.csv` | Early 987-row `Regular`-trip extraction with start/end reference-like fields and service energy. It lacks the richer source context and stable lineage fields. Legacy only. |
| `Par_Routes_Overhauled.csv` | Early ordered trip table with normalized columns. Legacy only; at least one exact-place value is text-corrupted. |
| `Par_DHD_original.csv` | Old CSV export of the original Partille DHD base fields. The workbook remains authoritative. |
| `Par_DHD_for_code.csv` | Near row-for-row base-DHD conversion: renamed endpoints/duration and `Energy used = Base Distance x 2.0 kWh/km`. It drops time-of-day overrides; four missing distances became zero energy. |
| `Par_DHD_Updated.csv` | Later exact-place base-DHD table with additional/updated links. Its additions are derived, not a new GIRO source export. |
| `Par_DHD_Relevant.csv` | Small filtered subset of derived Partille DHD links. Useful only with the experiment that created it, not as a complete matrix. |
| `Ref_dict.csv` | Partille exact-place to reference-place mapping, with depot/charging annotations. This implements the zipcode-like geographic layer. |
| `Par_dhd_refref_pairs.csv` | Intermediate aggregation from exact-place DHD to reference-pair DHD, with count and min/max diagnostics. |
| `par_ref_dhd.csv` | Compact reference-pair lookup used by EVSP-DR. It is base-time, unordered/symmetric, aggregated data—not the original directed time-dependent matrix. |
| `Unique_Locations.csv` | Convenience list of locations used while constructing the Partille-derived model. |
| `Practice_1bus.csv`, `Practice_2bus.csv`, ..., `Practice_43bus.csv` | Historical Partille trip subsets assembled from GIRO duties. These are solver regression instances, not independent raw samples. Some larger files combine weekday variants. |
| `Practice_2minus1.csv` | Historical diagnostic containing the second duty from the two-duty construction. It is not a standard benchmark family. |
| `Practice_Custom_SingleDuty_*.csv` | All `Regular` trips from one literal GIRO `VehicleTask`; useful for route-feasibility diagnostics. The adjacent manifest records task identity, variant group, trip count, and hash. |
| `Practice_Custom_TwoDuty_*`, `duty_pairs/*` | Two-duty unions generated for small exact-pricing/partition tests. The manifests define their source duties and hashes. |
| `Practice_Selected_*` | Hand-selected or historical multi-duty subsets. Treat their filenames as experiment labels; inspect source-row membership before using them as samples. |
| `duty_unions/*` | Seeded generated unions of GIRO duties for controlled small-instance experiments. Use the manifest for duties, trip count, lower bound, and hash. |
| `peel_tmp/*`, `exact_dive_tmp/*` | Temporary residual instances created by algorithms. Not benchmark inputs and not source data. |
| `Toy_Routes.csv`, `Toy_DHD.csv`, `Toy_Prices.csv` | Synthetic test data unrelated to the GIRO observations. |
| `Hourly Charge.csv` | Legacy hourly SEK/kWh table. It is **not** a faithful copy of the email: hours 17-19 and 23 differ materially. Do not use it as the Transdev profile. |
| `hourly_prices_transdev_sek.csv` | Correct two-column transcription of the rough hourly profile supplied by Transdev. It is exploratory, not an actual tariff. |
| `hourly_prices.csv`, `hourly_prices_flat.csv`, `hourly_prices_duck.csv`, `hourly_prices_odd.csv`, `hourly_prices_single_peak_*.csv` | Research price scenarios. They are synthetic controls, not GIRO or Transdev observations. |
| `spatiotemporal_prices.csv`, `spatiotemporal_single_peak_*.csv` | Long-form station-by-hour research scenarios. These are synthetic and should not be described as measured station tariffs. |
| `Changing_Costs.csv` | A 15-minute price-like historical table whose units and provenance are not adequately documented in the repository. Do not use without resolving them. |
| `delta.csv` | A separate time-series table with power, PV/solar, and delta fields. Its provenance and relationship to the GIRO schedules are not adequately documented. Treat it as unrelated experimental data unless independently established. |

One known lineage discrepancy illustrates why the workbook should remain the
source of truth: Partille task `13301`, route `5517`, direction 1, 13:45-13:57
ends at `PC_3` in the original workbook and `Par_Routes_For_Code.csv`, but at
`PC_7` in `Par_VehicleDetails_Updated.csv`; `Par_Routes_Overhauled.csv` contains
a corrupted string for the same endpoint. Both exact places map to reference
`13215`, so a zipcode-level model hides the discrepancy.

## What the emails establish

- Electricity price was **not** considered in the supplied GIRO optimization.
- The `Regular` filtering rule above defines the passenger-trip rows.
- GIRO's mathematical objective and soft-preference weights were not supplied.
- The exports appear EV-only even though the wider operations include non-EVs;
  mixed-fleet research requires additional data.
- The hourly SEK/kWh profile was a rough estimate based on only a few spring
  months and was offered for exploration, not as a formal tariff.
- Actual network charges may depend on monthly maximum 15-minute kW or a power
  threshold, but no subscriptions, thresholds, or rates were supplied. Do not
  invent a demand-charge coefficient and call it observed.
- Reference-place substitution for missing exact deadheads is acceptable.
- The DHD matrix is sparse and operationally curated, not a complete road metric.

## Physical and operational context worth preserving

The exports and notes support more detail than a basic homogeneous EVSP:

- Partille usable battery capacity is about 236-239 kWh; Frölunda also has
  vehicles with about 359 kWh usable capacity.
- The normal minimum SOC is 15%; Frölunda blocks longer than 20 hours have a
  documented 20% rule.
- Partille service consumption is approximately 2.0 kWh/km. Frölunda's default
  is 1.9 kWh/km with route/direction exceptions.
- Opportunity charging is SOC-dependent/tapered; depot charging is described as
  60 kW. It is not a universal constant-power system.
- Opportunity chargers have finite resource counts, and some locations also
  have arrival/departure/FIFO conflicts.
- The notes contain route-specific linking, interlining, and layover rules.
- Idle draw is 0.10 kW. Crew scheduling is a later layer, but some long gaps in
  the solved blocks may reflect crew constraints rather than freely usable time.

Researchers need not reproduce every GIRO rule, but should distinguish a chosen
EVSP abstraction from what the source data actually says.

## Recommended neutral EVSP build

1. Preserve and hash the original files; never overwrite them during cleaning.
2. Select one contract and one defensible service day/variant combination.
3. Extract `Identifier == Regular` rows and assign auditable trip IDs tied to
   source rows.
4. Convert all service times to elapsed minutes while retaining the original
   strings and allowing values above 24:00.
5. Choose an explicit deadhead fidelity level. If using time intervals, select
   them with the deadhead start clock modulo 24.
6. Decide whether service `Usage kWh` is accepted as observed/model-provided
   energy or recomputed consistently from distance and vehicle type.
7. Freeze battery capacity, SOC reserve, terminal SOC, charger power curve,
   charger capacity, and missing-link policy in a dataset manifest.
8. Validate each historical GIRO block under those translated assumptions.
   A failure can indicate translation/model mismatch; it does not by itself mean
   GIRO's route was physically infeasible.
9. Use the historical blocks as a feasible reference schedule, not as proof of
   optimality or as the only acceptable route partition.
10. Keep routing metrics, charging cost, fleet count, feasibility violations,
    and solver optimality/certification evidence separate in reported results.

## Important data gaps

The supplied material does not provide a clean raw one-day timetable, GIRO's
formal objective weights, a complete deadhead metric, actual electricity/network
tariff contracts, or enough non-EV data for mixed-fleet optimization. Frölunda
also contains suspicious source values (for example, a `7506 <-> KEX` base
distance of `7300` with a 13-minute duration) that must be confirmed rather than
silently corrected.

For deeper project-specific provenance, see the `evsp-dr` repository's
`README.md` and `EMAIL_EXCHANGE.md`.
