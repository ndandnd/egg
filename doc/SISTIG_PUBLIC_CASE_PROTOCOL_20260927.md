# Sistig public timetable NativeCase protocol

Status: local public-data adapter/preflight; no optimizer, solver, benchmark, or
scientific campaign has run. The derived input and adapter are prepared as a
candidate EGG case. Time/graph admission is exact; physical, fleet, price, and
case-selection assumptions below are explicit EGG scenario choices, not source
observations.

## Source and attribution

Input source: Sistig, Sinhuber, Rogge, and Sauer (2025), *Dataset for
Evaluating Costs and Operations of Public Bus Fleet Electrification*, Figshare
v1, DOI [10.6084/m9.figshare.26088190.v1](https://doi.org/10.6084/m9.figshare.26088190.v1),
licensed CC BY 4.0. Primary paper:
[Evaluating costs and operations of public bus fleet electrification](https://doi.org/10.1038/s44333-025-00030-y).
Attribution, requested change statement, and the exact derived-scope notice are
in `data/public/sistig_26088190_v1/ATTRIBUTION.md`.

The source archive is kept outside this project tree. It is not copied into
`data/public` or committed. The derived JSON records the source archive size,
the MD5 supplied by Figshare, our SHA-256 intake fingerprint, all six
Hildenbrand member paths and their member sizes/CRCs/SHA-256 values. The
SHA-256 is not labeled as a publisher-supplied checksum. The parent audit script and report under
`research-20260927/agent-notes/public-data` contain the broader local intake
record.

The paper says it uses DELFI-curated GTFS, picks the day with the most regular
service trips, estimates missing service distances as air distance ×1.1, and
estimates non-revenue deadhead distances/times from geocoordinates and routing
(Methods, §§“Selection of transport operators”). Thus the source tables are
curated/modelled planning inputs, not vehicle telemetry. The exact calendar
date and original GTFS feed license are not carried per record in this
supplement. Although the supplement states CC BY 4.0, check any underlying
feed terms before a journal release of an extracted or adapted case.

## Case selection and retained source facts

Hildenbrand is the smallest complete operator timetable in the bundle:
**37 unique mandatory service trips**, 2 routes, 5 stops, and 2 source-flagged
depots. The data contains one `day_type_id` value but no calendar date. All
37 source trip rows are retained in workbook order with physical row numbers;
source trip, itinerary, route, and endpoint references reconcile.

All source `trip_set.xlsx` departure/arrival strings use `dd:HH:MM:SS`, with
seconds fields; durations use `HH:MM:SS`. For these 37 services, every event
and duration happens to lie on a whole-minute boundary and the timestamp text
reconciles exactly with numeric seconds and duration. A service arrival uses
day offset 1, so the selected-day offset is preserved rather than wrapped to
minute zero.

`deadhead_trip_matrix.mat` supplies the full source-ordered 5×5 directed
matrix: distance in metres, time in seconds, elevation difference in metres.
All 25 cells, including diagonals, are retained; all 20 off-diagonal arcs are
finite and nonnegative. Ten unordered pairs have asymmetric distance values;
six have asymmetric time values. No reverse edge, average, shortest-path
fallback, or missing value is manufactured. Fifteen of the 20 off-diagonal
travel times are not whole minutes; they are exact half-minute values. Their
source second values remain authoritative in JSON, and NativeCase times are
converted to integer or half-minute values without rounding. The `itineraries_course.mat`
member is fingerprinted but not parsed: it is a MATLAB MCOS table opaque to
`scipy.io.loadmat` and is unnecessary for endpoint/timetable modeling.

The raw service rows contain no energy field (`source_energy_kwh` is null).
The directed deadhead matrix contains time/distance/elevation but no energy.
The input bus type is zero-coded; it is not used as an electric-bus type.
Publisher-generated solved vehicle schedules and charge plans are not used.
In particular, no `vehicle_type_4117` result is treated as EB-7; the dataset
output identifier and Table 2's printed EB-7 identifier do not match, and no
authoritative mapping was found.

## NativeCase physical baseline

The named energy rates come from paper Table 2's **EB-3 (paper ID 4103)**, which
the authors call a typical market electric bus:

| Driver | EGG input value | Meaning |
|---|---:|---|
| Usable battery | 400 kWh | Maximum usable inventory; installed 600 kWh retained as reference only |
| Service traction rate | 1.20 kWh/km | Multiplied by the source service distance |
| Deadhead traction rate | 0.96 kWh/km | Multiplied by each directed source movement distance |
| Auxiliary rate | 16 kWh/h | Applied during service time, deadhead travel time, and explicit off-depot stationary waits |
| Reserve | 0 kWh | Additional reserve constraint in this EGG baseline |
| Charge efficiency | 1.0 | Idealized EGG baseline |
| Charge rate | 360 kW | Constant EGG per-bus and shared grid-side cap; 450 kW installed rate is reference only |
| Connectors | 1 | EGG shared-connector idealization |

For source service (i), modelled energy is

\[
E_i^{\mathrm{model}}=1.20\,d_i^{\mathrm{service}}[\mathrm{km}]
  +16\,\Delta_i^{\mathrm{service}}[\mathrm{h}].
\]

For source deadhead movement (a\to b), modelled energy is

\[
E_{ab}^{\mathrm{model}}=0.96\,d_{ab}^{\mathrm{DHD}}[\mathrm{km}]
  +16\,\Delta_{ab}^{\mathrm{DHD}}[\mathrm{h}].
\]

An off-depot stationary wait in a direct mode is represented as an explicit
same-place leg with zero traction and (16\) kWh/h auxiliary draw. Auxiliary
draw while parked at a depot is assumed off. The source supplies none of these
energy values as observations; `source_energy_kwh` and `modeled_energy_kwh` are
separate fields. No temperature, occupancy, grade correction, charging taper,
or battery degradation is added.

This is not a reproduction of the publisher's charging layout. The article
states a depot-charging study and discusses one charger with four outputs for
overnight operation. The EGG variant instead uses one connector and a constant
360 kW shared/per-bus cap as an explicit idealization. There is no off-depot
charging option in this baseline. The source charging-plan table, when present,
is an optimized planning output in kWh and timestamps, not an observed session;
it is excluded here.

## One-depot variants and enumerated movement modes

The source has two flagged depots. Because `NativeCase` currently accepts one
depot, generate **two distinct restricted scenarios**, one selecting each
source depot. These are not the full two-depot source problem, and no path may
start at one depot and end at the other. Each variant includes all 37
mandatory services, permits up to 37 used buses (one per service as a loose
cap), starts every used bus full, and requires it to return full by a 30:00
deadline (1,800 minutes after the selected-day boundary). The horizon is 00:00
through 30:00; terminal charging is open from 00:00, so every post-pull-in
minute is available. Hourly market boundaries divide the 30-hour horizon.

For each fixed source service pair (i,j), the adapter evaluates the exact
directed movement arcs under the following single timing policy per mode:

| Mode | Fixed timing encoded in the movement | Notes |
|---|---|---|
| Pull-out | Selected depot departure is the latest time that reaches the first service start exactly | Same directed matrix; only if departure is in the 00:00–30:00 horizon |
| Direct | Leave immediately after service (i); travel to service (j)'s origin; if early, wait there until (j)'s start | Off-depot wait is a same-place leg with explicit 16 kWh/h modeled auxiliary use |
| Depot detour | Travel into selected depot immediately after (i); leave as late as possible to arrive at (j)'s start exactly | The arrival/departure pair fixes a depot recharge window; depot parked auxiliary is assumed off |
| Pull-in | Return immediately after the final service | Depot arrival opens the terminal recharge window until 30:00 |

Only modes passing these explicit time tests are emitted. They retain fixed
departures/arrivals; this graph does **not** give the model a continuous choice
of movement departure time, path, stopover, or routing. The generated counts
are recorded per depot variant in JSON. For this exact input, all 37 service
endpoints are at non-depot stops, and the extractor confirms no direct-mode
stationary wait occurs at either flagged depot. There are 648 positive
off-depot direct waits and 18 exact-arrival direct modes in each variant. The
adapter fails closed if a future
case has a direct wait at a depot, because the declared policy turns depot
auxiliary load off and that situation needs explicit treatment. No connection
times or arcs are imputed.

## Constructive feasibility and preflight dimensions

Pure validation, compilation, and event replay (no solver) construct one
source-qualified full-service witness per depot variant: 37 buses, one
mandatory service per bus, the fixed source-directed pullout and pull-in, and
one serialized terminal charge per bus. Each bus starts at 400 kWh; its charge
equals its modeled service plus pullout/pull-in energy. At 360 kW on one
connector, all charging finishes well before 30:00. This demonstrates
feasibility of the 37-service baseline under these narrow assumptions, not a
fleet-size result, optimum, publisher outcome, or operational claim.

| Selected source depot | Direct modes | Depot-detour modes | Pull-outs / pull-ins | Last service arrival | Latest immediate depot return | Total modeled service energy | Pull-out + pull-in energy in witness | Combined witness energy | Max one-trip bus energy | Terminal charging complete | Compiled intervals | Eligible mode-interval pairs per bus | Candidate charge variables at 37 buses |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 666 | 630 | 37 / 37 | 24:24 (1464 min) | 24:43:30 (1483.5 min) | 889.118 kWh | 1200.759 kWh | 2089.876 kWh | 59.335 kWh | 24:50:31.4 (1490.524 min) | 102 | 20,322 | 751,914 |
| 16 | 666 | 595 | 37 / 37 | 24:24 (1464 min) | 24:50:30 (1490.5 min) | 889.118 kWh | 1880.697 kWh | 2769.814 kWh | 81.365 kWh | 25:01:07.4 (1501.123 min) | 101 | 19,062 | 705,294 |

Both terminal charging completion times precede the explicit 30:00 (1800 min)
deadline. The replay's measured maximum shared rate is 360 kW up to floating
arithmetic noise (less than 3e-12 kW above 360), inside the native replay's
1e-6 kWh tolerance. The candidate-variable count is a schema/compiler
dimension estimate: 37 vehicles multiplied by every charge-eligible movement
and compiled interval pair. It is not an instantiated MIP or a solver result;
it signals that a future solve may need a smaller defensible connection menu
or a more compact exact formulation.

The intrinsic objective input is `vehicle_cost=100` in the explicitly
synthetic unit “f100 synthetic currency per used bus”; deadhead cost is 0.
These are schema fixtures, not published operator costs or calibrated prices.

## Files and reproducible checks

- `src/experiments/sistig_native_case.py`: checksum-pinned, in-memory source
  extractor and deterministic NativeCase adapter; uses Python, NumPy,
  `openpyxl`, and `scipy.io` only for source intake/regeneration; imports are
  lazy, with no upstream code or solver imports.
- `data/public/sistig_26088190_v1/hildenbrand_native_cases.json`: 37 source
  services, full 25-cell directed matrix, two depot-specific NativeCase
  variants, modelled energy, and source member hashes. No large source archive.
- `data/public/sistig_26088190_v1/ATTRIBUTION.md`: DOI, license, citation, and
  adaptation statement.
- `src/tests/test_sistig_native_case.py`: source preservation, unit/precision,
  exact mode provenance, depot restrictions, candidate dimension accounting,
  and schema-only checks, including replay of the labeled witness.

Regenerate from the locally held archive with:

```sh
python3 src/experiments/sistig_native_case.py
```

The adapter runs pure case validation and event-grid compilation, and its
preflight replays the labeled constructive witness, without solving:

```sh
python3 src/experiments/sistig_native_case.py --validate-native
PYTHONPATH=src python3 -m pytest -q src/tests/test_sistig_native_case.py
```

No optimizer, solver, cluster, publisher run, or public benchmark was executed
as part of this adapter preparation.

## Outstanding scientific choices before any campaign

1. **Two-depot restriction:** determine whether results should be reported for
   both depot variants separately or whether one is selected as the public
   microcase. Combining them would require a multidepot physical schema.
2. **Energy sensitivity:** EB-3 is a transparent paper baseline, not measured
   bus energy. Vary traction/auxiliary assumptions and determine whether
   stationary auxiliary load should apply at terminals or during depot dwell.
   Current input applies it only to service, travel, and explicit off-depot
   wait; depot parking is set to zero load.
3. **Charging assumptions:** one 360 kW shared connector, efficiency 1.0,
   reserve 0 kWh, and 30:00 full-return deadline are EGG choices. Sensitivity
   to connection count/power, charging efficiency, reserve, and deadline is
   needed before operational claims; do not treat the one-connector model as
   the publisher's four-output overnight infrastructure.
4. **Movement timing:** current modes use immediate direct/inbound/pull-in and
   latest-feasible pullout/outbound timing. These policies are fixed and not
   optimized. Assess whether another finite timing menu is needed for a
   research claim, and list each added option explicitly.
5. **Operating-day boundary:** the input's day-type and encoded day offsets
   preserve timetable sequencing but not a calendar date. The 30-hour horizon
   is a stated EGG availability policy, not a source operating-day boundary.
6. **Costs/objective:** f100 per used bus and zero deadhead cost are synthetic
   parser/schema values only. Define the economic or coordination objective
   and report price/cost assumptions before any hull or schedule experiment.
7. **Underlying feed rights:** preserve CC BY attribution/change notices and
   check the source GTFS feed terms before packaging a journal release. This
   source is curated input with some estimated distance/movement values, not
   empirical telemetry.

The only physical-feasibility finding is the narrow 37-vehicle constructive
witness above under the declared model assumptions. No fewer-vehicle result,
best-case result, optimum, economic conclusion, operational claim, or
publisher-outcome reproduction may be claimed from this input-only protocol.
