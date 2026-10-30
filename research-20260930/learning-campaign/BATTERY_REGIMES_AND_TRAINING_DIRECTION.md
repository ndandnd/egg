# Battery regimes and training direction

30 September 2026. The user requests broader battery and synthetic-route settings,
questions whether the model has enough training, and asks for the current state.
This records the direction for the next dataset version. It is not an executed
experiment or a frozen launch protocol. Job 700498 remains unchanged.

## Physical calibration

The current synthetic generator fixes a 100-kWh upper inventory and a 20-kWh
reserve, giving an 80-kWh operating span. Its 18–28-kWh services, one shared
90-kW connector, 0.9 charging efficiency and terminal replenishment constraints
form a demanding synthetic regime; the 80-kWh value is not a universal bus limit.
The earlier 91.33–241.63-kWh violations concern 14 selected route segments, not
the whole fleet problem. Existing fully feasible source plans show that the
original timetables themselves can be operated.

Hyundai's Korean Elec City specification lists a 290.4-kWh battery:
https://www.hyundai.com/kr/ko/c/products/bus/elec-city

The publisher's accessible text for Son, Im and Kim (2025), *Urban transit
optimization: Efficient electric bus operations and vehicle-to-grid integration*,
reports a baseline 20–80% SOC range. The accessible text did not establish its
exact Hyundai pack choice, so do not attribute that detail to the paper yet:
https://www.sciencedirect.com/science/article/pii/S0360835225003158

Treat nameplate capacity, maximum allowed inventory and reserve separately.
Proposed versioned profiles are:

| Profile | Nameplate kWh | Model upper kWh | Model reserve kWh | Operating span kWh |
|---|---:|---:|---:|---:|
| Original synthetic control | 100 | 100 | 20 | 80 |
| Elec City sized, 20–80% SOC | 290.4 | 232.32 | 58.08 | 174.24 |
| Elec City sized, 10–90% SOC sensitivity | 290.4 | 261.36 | 29.04 | 232.32 |

These are modeling profiles, not claims that Hyundai recommends those SOC
windows. This mapping assumes the quoted capacity is usable over the modeled
0–100% scale; any additional BMS restriction or degradation should be explicit.
The last two profiles still cannot accommodate a 241.63-kWh uncharged segment.
Charging opportunities and route structure therefore remain relevant. Passing
a segment-energy test is necessary, not sufficient: finite dwell, shared power,
charger occupancy, losses and terminal replenishment must also replay.

The next generator should define distance, travel time and energy consistently,
with transparent consumption assumptions, and include shorter duty chains and
scheduled intermediate depot opportunities. Vary these independently of model
outcomes. Include loose, moderately constrained and tight energy regimes rather
than altering each failed route just until a learned proposal passes. Use new
versioned identities; all variants of a base timetable stay in the same split.
Check constructive feasible fleets before spending solver time on new training
cases. Preserve old attempts and all four reserved test identities.

## Learning maturity and next scale

The current charge-response model is an eight-coefficient ridge regression fit
once by a linear-system solve, with penalty 1.0. It uses 12 charging outcomes
from six independent training timetables, all under one target tariff. It
predicts the cost change from recharging one of two already solved source
fleets. It does not generate routes or replace the global fleet solver.

Its four development choices all selected source 1. A constant source-1 rule
matched every choice, so sufficient predictive training and adaptive benefit
have not been established. More optimization epochs on these same data have
no purpose: the current ridge fit is already solved. More diverse independent
training timetables are the useful next investment. Regularization does not
remove the risk from six groups or from repeatedly tuning to four development
groups. No learning-curve saturation or reliable generalization estimate exists.

After collecting and reviewing job 700498, implement the new physical profiles
and construct several dozen independent training timetables in bounded serial
batches. Record a prospective sample count, grouped split and resource budget
before each launch. Increase independent training groups in stages and compare
validation cost/feasibility curves against constant selection, direct rescoring,
retrieval and cold solving. Keep a separate set of whole timetables untouched
until model selection is frozen. Target-tariff variations are correlated samples,
not extra independent timetables. Do not promise that simply adding data will
make the current features adequate.

## Current research status

Draft 0.10 is a 23-page coauthor discussion draft with checked theory and figures;
it is not a completed computational journal submission. Public-timetable optimal
fleet support remains unresolved. The computational infrastructure now collects
solver plans, bounds, fixed-route charging labels, training/inference artifacts,
and controlled comparisons with reproducible costs and timing. No learned
end-to-end speedup or global optimality result has been established.

At the scoped check on 30 September, job 700498 was RUNNING after 17 minutes,
using one CPU and requesting 8 GB on snavely-cpu-01. It tests four new development
groups under three tariff variants with frozen models and prospective constant
controls. This check did not inspect partial scientific outcomes. The next
heartbeat should collect its complete evidence before choosing the next launch.
