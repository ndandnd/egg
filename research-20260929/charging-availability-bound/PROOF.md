# Charging-availability bound for the two declared public cases

This is a reporting-only exact bound for the stored-input ideal model. It changes
neither the native solver nor any historical outcome. All cited feasibility and
two-bus energy facts inherit the pinned lineage in `analytic_energy_floor.py`.

## Universal availability, not a selected schedule

In the pinned model, charging is permitted only within declared intermediate
depot visits and terminal pullin visits. The vehicle begins full; parked depot
auxiliary consumption is zero. Pullout/direct movements admit no charging.
Take the union of every declared depot/pullin window, including windows that
cannot coexist in one fleet. This union contains every selected charging window
of every feasible complete fleet. Intersect the union with each market period
and the single-connector resource intervals, and integrate the smaller of grid
and vehicle power. The resulting hourly energy cap C_t is valid for every
physical fleet and hence every point in its convex hull.

The first possible charging times are 405.5 and 408.5 minutes for depots15/16.
Both cap vectors have six initial zeros, then 87 or 69 kWh in period[360,420],
then 360 kWh in each remaining period. The partial seventh hour is treated
through its energy cap. It is NOT replaced by a fractional weight in F: the
declared supply function penalizes hourly energy, not instantaneous power.

## Capped Fenchel certificate

Let E2 be the reviewed two-bus energy floor, Es the mandatory service-energy
floor, f>0 the used-bus fee, and p>=0 a uniform test price. One bus is impossible.
Every complete plan satisfies

    c + p sum(e_t) >= m(p) = min(2f+p E2, 3f+p Es).

The same inequality holds for convex mixtures. With

    g_t*(p) = max_{0<=u<=C_t} [(p-a_t)u - b_t u^2/2],

Fenchel's inequality yields CH >= m(p) - sum_t g_t*(p). The maximizer in each
conjugate is clip((p-a_t)/b_t,0,C_t). `compute.py` maximizes the concave bound
over all nonnegative p by evaluating its rational breakpoints and stationary
points. This also works when the two-bus line ceases to be the smaller line.
Crossing f=p(E2-Es) changes the bounding argument, not the proven best physical
fleet cardinality. The sensitivity rows are analytical bounds only.

For f=100 and the two archived markets, only the 24 positive-cap periods
contribute. The optimizing p is mean(a over those24)+b E2/24; every implied
load is strictly below its positive cap and the two-bus line is smaller.
Thus the cap values validate the certificate but add no further tightening
beyond excluding the six unavailable periods in these four cases.

| Depot | Market | Previous floor | Availability floor | Improvement |
|---|---|---:|---:|---:|
|15|original|424.36|429.22|4.86|
|15|changed|418.96|430.29|11.33|
|16|original|435.67|440.99|5.32|
|16|changed|430.27|442.30|12.03|

Floors are rounded downward; displayed improvements are approximate differences
of unrounded values. Exact fractions and all inputs/hashes are in `bounds.json`.
No positive physical-hull gap follows from this lower-bound improvement.

## Pricing inequalities and implementation scope

The physical constraints E>=Es and, for integer fleet count k>=2,

    E >= E2 - (E2-Es)(k-2)

are valid here. At k=2 the latter enforces E2; at k>=3 it is no stronger than
the universal Es floor. They can be used with any pricing objective after
appropriate native coefficient/tolerance handling. The existing compact model
already contains an aggregate energy-balance row and individual interval charger
caps; their implied inequalities should not be advertised as new solver cuts.
A separately tested conditional energy inequality may strengthen its relaxation.
This package makes no native-model change or solver-speed claim.

## Independent check

The manuscript Sol reviewer independently enumerated the archived windows and
recomputed the 24-period closed form with exact fractions. All four exact bounds
match. The largest implied loads are about42.69/65.19 kWh at depot15 and
44.67/67.17 kWh at depot16, below even the partial-hour caps. The review covers
the four manuscript floors; the full analytical parameter grid is prospective
scenario context rather than computational optimization evidence.

Reproduce from the repository root with
`python3 research-20260929/charging-availability-bound/compute.py`.
