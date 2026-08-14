# Is price-load feedback novel *within EVSP*? Independent verification

Date: 2026-08-14

Status: web-search evidence (abstracts and publisher pages). Same evidence
tier as `EXTERNAL_DEEP_DIVE_20260814.md`; full-text confirmation required
before manuscript use. Non-English-indexed work (especially Chinese-language
transit journals) may be undersampled.

## Question

The handoff asserts "generic price-load feedback is not novel." That was
established mostly from *non-EVSP* domains (traffic equilibria, aggregate EV
batteries, storage). This note verifies the claim specifically for the
electric vehicle scheduling problem: timetabled trips, vehicle-duty chaining,
set-partitioning structure, exact methods.

## Definitions used

"Price-load feedback" = the electricity price faced by the fleet depends on
the fleet's own decisions. Two channels must be distinguished:

- **Market-mediated feedback:** the price is formed by a market or supply
  curve shared with other consumers; the fleet's load shifts that price for
  everyone (p_t = g_t(U_t + L_t)). This creates strategic, equilibrium, and
  welfare content.
- **Tariff-structural own-cost nonlinearity:** the fleet's own bill is a
  nonlinear function of its own load (demand charges on peak kW, peak-load
  penalty terms), with no market, no other participants, and no external
  price movement.

## Findings

### 1. Within EVSP proper, prices are exogenous (price-taking + TOU)

The exact-methods EVSP literature that involves electricity prices uses
fixed time-of-use tariffs:

- Wu, Lin, Liu, Jin (2021), *The multi-depot electric vehicle scheduling
  problem with power grid characteristics*, Transp. Res. Part B 155, DOI
  `10.1016/j.trb.2021.11.007`. Branch-and-price MDEVSP under TOU tariffs
  with a *second objective* minimizing peak charging load (lexicographic).
- Zhang et al. (2024), *On the role of time-of-use electricity price in
  charge scheduling for electric bus fleets*, Computer-Aided Civil and
  Infrastructure Eng., DOI `10.1111/mice.13134`. Set-partitioning
  reformulation, tailored branch-and-price, TOU + partial charging + limited
  chargers; reports up to 22% cost saving from TOU-aware scheduling.
- TRE 2025 (Transp. Res. Part E 196), *Optimization of electric bus vehicle
  scheduling and charging strategies under Time-of-Use electricity price*:
  MIP + dynamic-label-setting branch-and-price.
- Multiple further TOU/charger-limit scheduling papers (ALNS Beijing 2024;
  MILP/heuristic depot studies) and the CLP-EVSP-CSP co-optimization line
  (arXiv:2403.09763) with time-of-day pricing.

In all of these the price vector is a constant of the instance. None models
the fleet moving the price.

### 2. Own-load-dependent *costs* do exist inside EVSP/depot charging

- Demand-charge / peak-power-charge scheduling exists in several depot
  charging studies (e.g., 2025 depot MILPs with notified-maximum-demand or
  time-of-day demand charges; peak-load + battery-degradation charger
  scheduling).
- Wu et al. (2021) minimize peak charging load as an objective.

Mathematically these make the fleet's bill a nonlinear (max-type) function
of its own load, which is a *degenerate, market-free* form of "price depends
on my load." This is squarely occupied territory.

### 3. Market-mediated feedback exists only *adjacent to* EVSP, never inside it

- Lu et al. (2021), IJEPES 125 (audited in full): price-making transport
  company with routes + energy/reserve bids, but service is minimum
  departures on stylized hourly arcs — not trip-covering EVSP.
- Wu et al. (2019), Applied Energy 255 (audited in full): bus operations
  coupled to DLMPs, but tactical frequency planning; service itself is
  elastic; no atomic duties.
- Iterative EV-routing/DLMP work exists for *delivery* VRPs (e.g., an Aalto
  dissertation: parcel-delivery EV routing + DLMP-based market clearing,
  iterative multistage) — VRP with elastic timing, not timetabled VSP.
- Traffic-equilibrium and aggregate-battery feedback loops (Wei 2018, Wang
  2024, Song 2025, Gonzalez Vaya 2015, Xie-Xu 2025) — no vehicle duties at
  all.

### 4. Reviews corroborate the gap

The e-bus scheduling reviews found (Energies 2022 review of EBS/timetabling/
grid impact; the Perumal et al. 2022 EJOR survey as cited by follow-on work;
Zhou et al. 2024 TRE review of charging facility planning/scheduling) list
TOU integration, charger limits, and grid impact as active topics and
identify integration gaps; none cites an EVSP with endogenous market prices.

## Verdict

1. **"Generic price-load feedback is not novel" — TRUE.** Confirmed
   independently: the loop is abundant outside EVSP (traffic equilibria,
   aggregate EV fleets, storage, delivery VRP + DLMP).
2. **Within EVSP proper, market-mediated price feedback appears to be
   unoccupied.** No timetabled, trip-covering, duty-based scheduling model
   was found in which the fleet's load moves a shared market price —
   exogenous TOU is the universal assumption, and the nearest neighbors
   (Lu 2021; Wu 2019) relax exactly the service structure that defines EVSP.
3. **Claim-discipline consequence.** Because demand charges and peak-load
   objectives already exist inside EVSP, the project must NOT phrase its
   novelty as "first EVSP where cost depends on the fleet's own load." The
   defensible phrasing is: *first EVSP embedded in market-mediated price
   formation* — a shared price moved by the fleet's load, with the
   strategic/equilibrium/welfare structure that entails (price-taker vs
   strategic vs planner separation, market power, settlement design).
   A demand charge is a private nonlinearity; a market price is a shared
   externality. The economics lives in the second one.

## Follow-ups

- Acquire and skim Wu et al. (2021) TRB and Zhang et al. (2024) MICE as the
  EVSP-side baselines closest to our machinery (both branch-and-price, both
  price-aware); added to `../READING_QUEUE.md`.
- When drafting any claim, cite the demand-charge line explicitly and
  distinguish the channels as above.
