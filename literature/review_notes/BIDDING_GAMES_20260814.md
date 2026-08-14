# EV Aggregator Bidding and Game Models: Research Handoff

Date: 2026-08-14

## Scope and evidence

These notes are based only on a full-text review of the three local PDFs listed below, with the model and results pages also checked visually. No web search or secondary source was used. "Novelty killed" means that the named claim is already occupied by at least one of these papers; it is not a comprehensive or legal prior-art conclusion. Any proposed "first" claim for EVSP still requires a broader literature search.

The cross-paper conclusion is sharp: endogenous electricity prices, strategic EV aggregators, bilevel market clearing, multi-aggregator games, risk-aware bidding, V2G arbitrage, and nodal LMP feedback are not themselves open novelty. The defensible EVSP boundary is the executable scheduling layer: trip coverage, vehicle-to-duty assignment, route and SOC feasibility, charging visits, and possibly charger capacity embedded inside the market-facing best response.

## 1. Gonzalez Vaya and Andersson (2015)

Source: `lit reviews/Optimal_Bidding_Strategy_of_a_Plug-In_Electric_Vehicle_Aggregator_in_Day-Ahead_Electricity_Markets_Under_Uncertainty.pdf`

### Actual method and game structure

- This is a single strategic aggregator model, not a game among multiple strategic firms.
- The upper level minimizes the aggregator's cost of buying day-ahead charging energy subject to an aggregate representation of EV flexibility.
- The lower level clears the electricity market by maximizing supplier and consumer surplus over the aggregator's demand bid and the other participants' supply and demand bids.
- Other participants' bids are treated as fixed inputs. Their strategic reaction to the aggregator is not modeled. The authors assume that the flexible aggregator can affect the clearing outcome but that other agents do not readily exercise countervailing market power.
- The lower-level linear program is replaced by its KKT conditions. Complementarity is linearized with binary variables and large constants, and strong duality linearizes the upper-level payment term. The result is a MILP.
- The optimization returns accepted charging volumes and bid prices. In implementation, the accepted volume is used as the submitted volume and a markup is added to the computed bid price. A maximum-price bid is the conservative choice that guarantees the intended daily energy purchase.
- Market bids that are unavailable ex ante are forecast using the previous week's bids for the same weekday and hour.

### Fleet representation and assumptions

- The aggregator submits demand bids only. Vehicle-to-grid discharge is explicitly excluded.
- Individual MATSim driving patterns are aggregated into a virtual battery with time-varying charging-power and stored-energy bounds.
- The lower energy bound represents charging deadlines; arrivals and departures change aggregate stored energy; a cyclic daily-energy condition prevents shifting required energy outside the horizon.
- Travel uncertainty is represented through samples of departure times, trip durations, and trip energy. A joint chance constraint is replaced by a distribution-free robust hyperrectangle obtained from sampled realizations. The uncertain equality is centered using a sample median.
- The method covers aggregate flexibility and day-ahead scheduling, but not the third-stage real-time dispatch of individual vehicles. The authors explicitly note that aggregate schedules can deviate from individually realizable schedules.
- There is no trip-to-vehicle assignment, service routing, station-level charger-capacity model, or executable vehicle-duty construction.

### Experiments and reported evidence

- Market data: 2012 hourly EEX aggregate bid curves for Germany/Austria.
- Fleet scale: 2% PEV penetration, approximately one million vehicles.
- Mobility data: Swiss weekday MATSim patterns, acknowledged as unsuitable for a quantitative German/Austrian impact estimate but used for a qualitative strategy test.
- Vehicle assumptions: 3.7 kW maximum charging power, 90% charging efficiency, 0.2 kWh/km, mean daily consumption 5.8 kWh with 7.3 kWh standard deviation, and a fleet split evenly between 16 and 24 kWh batteries.
- Chance-constraint settings: violation parameter 0.08, very small confidence-failure probability, and about 2,290 sampled driving patterns.
- Benchmarks: exogenous-price optimization, surplus-maximizing central dispatch, and uncontrolled/inflexible charging.
- Average daily purchase cost in the perfect-information case was EUR 32.55/MWh for strategic bidding, EUR 35.56/MWh for the exogenous-price model, and EUR 33.18/MWh for central dispatch.
- With market-bid uncertainty, the corresponding strategic and exogenous-price costs were EUR 35.03/MWh and EUR 37.52/MWh; uncontrolled charging cost EUR 48.50/MWh.
- With driving uncertainty only, costs were EUR 33.11/MWh for strategic bidding, EUR 36.97/MWh for exogenous prices, and EUR 33.78/MWh for central dispatch.
- With both uncertainties, strategic bidding cost EUR 35.49/MWh versus EUR 38.83/MWh under exogenous prices.
- The mean penalty from bid uncertainty was EUR 2.48/MWh and could reach EUR 40.07/MWh on the worst day; the mean penalty from driving uncertainty was EUR 0.57/MWh.
- At the simulated penetration, EV demand was less than 1% of traded volume but still visibly affected market prices. Treating prices as exogenous caused excessive concentration in predicted cheap hours.
- The strategic result under perfect information was only slightly cheaper for the aggregator than central dispatch, leading the authors to describe market-power potential as limited at moderate penetration.

### Novelty this paper kills

This paper rules out an unqualified claim of being first to:

- model a day-ahead EV aggregator as a price-maker;
- couple flexible EV charging to endogenous bid-based market clearing through a bilevel MPEC/MILP;
- show that cheap-hour charging concentration changes prices and makes an exogenous-price schedule suboptimal;
- combine strategic bidding with probabilistic aggregate EV flexibility; or
- compare strategic bidding, exogenous-price scheduling, central dispatch, and uncontrolled charging under market and mobility uncertainty.

### Atomic EVSP gap that remains

The precise missing object is a price-making best response whose feasible set is an exact EVSP rather than a virtual battery. The contribution would be to make all market-facing load decisions arise from trip-covering vehicle duties with route, timing, charging-location, and SOC feasibility, and then quantify how that executable response differs from the aggregate-battery equilibrium.

## 2. Wu et al. (2016)

Source: `lit reviews/A_Game_Theoretic_Approach_to_Risk-Based_Optimal_Bidding_Strategies_for_Electric_Vehicle_Aggregators_in_Electricity_Markets_With_Variable_Wind_Energy_Resources.pdf`

### Actual method and game structure

- The paper combines two related constructions rather than solving one monolithic multi-player EPEC.
- For a focal aggregator, the upper level maximizes the lower-tail expected payoff measured by CVaR. Decisions include preferred charging operating points, day-ahead energy, real-time energy deviations, and up/down regulation offers.
- The lower level is a two-stage stochastic security-constrained economic dispatch. It co-clears energy and regulation while enforcing system balance, DC network-flow limits, reserve requirements, thermal-unit limits, ramping, wind availability, and scenario redispatch.
- The bilevel nonlinear problem is converted to a single-level stochastic MILP using the primal and dual lower-level models, strong duality, and piecewise linear approximations of quadratic payoff and upper/lower-level bilinear products.
- Progressive hedging decomposes the stochastic MILP by scenario and enforces non-anticipativity through increasing penalties.
- Competition among several aggregators is represented as a Bayesian incomplete-information supply-function game using a Harsanyi transformation. An aggregator's type is defined by the coefficients of its demand curve.
- Each player changes the intercept markup of a fixed-slope linear demand curve. The slope is held fixed because the authors report that manipulating both slope and intercept rarely yields a unique solution.
- Awarded energy and LMP sensitivities to a markup are not derived exactly. They are approximated with linear regressions fitted to historical data, followed by gradient updates and iterative best responses until no aggregator changes its bid.
- The authors state that the procedure finds an equilibrium if one exists; with multiple equilibria, a good initial bid may be needed to reach the global equilibrium.

### Fleet representation and assumptions

- Power flow between grid and vehicles is unidirectional. Regulation is supplied by moving charging above or below a preferred operating point, not by exporting stored battery energy.
- Each EV fleet is represented by aggregate charging power, energy requirements, and SOC bounds over flexible charging periods.
- The aggregator buys energy from a pool market and earns a concave fleet demand payoff minus energy costs plus a fixed share of regulation revenue.
- EV energy bids are linear downward-sloping demand curves; regulation offers are flat; generators and load-serving entities bid at marginal cost and payoff.
- Unit-commitment states are treated as known ex ante in market clearing.
- EV demand, arrival/departure time, and fleet size errors are truncated normal variables. Wind forecast error uses an ARMA process; load error and random generator/line outages are also sampled.
- Latin hypercube sampling and scenario reduction are used before stochastic optimization.
- Opponent types and their probability distribution are assumed inferable from published historical information.
- There is no individual trip assignment, route construction, charger scheduling, or proof that the aggregate fleet decisions are executable by individual vehicles.

### Experiments and reported evidence

- Modified 6-bus system: three thermal units, seven lines, one 40 MW wind plant, 256 MW peak inflexible demand, 4,985 MWh total daily demand, and 478 MWh forecast wind generation, or 9.6% penetration.
- Three aggregators are colocated at Bus 5. Vehicles use 12 kW maximum charging power and 90% efficiency.
- Risk confidence is 95%, and the aggregator receives 50% of regulation revenue.
- The study generates 1,800 Monte Carlo scenarios and reduces them to 185.
- A single aggregator's expected payoff is $1,741 with a $305 standard deviation. Energy markup contributes $641, or 36.8%; regulation contributes $1,100, or 63.2%.
- Inflexible charging raises average load cost from $31.2/MWh under the proposed strategy to $37.1/MWh, an 18.9% increase.
- Changing CVaR confidence from 0 to 0.99 reduces expected payoff from $2,023 to $1,647, an 18.6% decrease, while payoff standard deviation falls from $488 to $277, a 43.2% decrease.
- The three-player 6-bus Nash calculation takes 164 iterations and 4,728 seconds. Daily payoffs are approximately $1,682, $1,121, and $501; the largest fleet has the largest energy and reserve awards.
- Modified IEEE 118-bus system: 54 thermal units, 186 branches, 91 load buses, three wind farms, 22,845 MWh daily wind, 113,506 MWh load, and 20.1% wind penetration.
- The 118-bus study reduces 625 scenarios to 80. Its Nash calculation takes 148 iterations and 9,044 seconds, about 2.5 hours, with daily payoffs of approximately $3,321, $1,859, and $998.

### Novelty this paper kills

This paper rules out an unqualified claim of being first to:

- formulate competition among multiple EV aggregators as a Nash or Bayesian incomplete-information game;
- combine endogenous LMPs, strategic EV bidding, and CVaR risk management;
- jointly bid EV energy and regulation services under wind, load, mobility, and component-outage uncertainty;
- transform the stochastic bilevel aggregator problem into a MILP and apply progressive hedging; or
- show that fleet size affects aggregator market power and that risk aversion trades expected payoff for lower payoff variance.

### Atomic EVSP gap that remains

The strategic response is a smooth aggregate fleet program augmented by regression-based price and quantity sensitivities. The remaining EVSP question is an equilibrium in which each player's best response is a combinatorial, trip-serving vehicle schedule. A scalable contribution could replace the aggregate response with exact or certified price-parametric column generation and compare that executable equilibrium with the smooth fleet approximation.

## 3. Toquica et al. (2020)

Source: `lit reviews/main3234.pdf`, titled *Power market equilibrium considering an EV storage aggregator exposed to marginal prices - A bilevel optimization approach*.

### Actual method and game structure

- A single firm controlling EV storage is the Stackelberg leader; a benevolent system operator is the follower. Although the paper sometimes uses oligopoly language, the modeled market-facing EV side is a monopoly aggregator, not competition among several profit-maximizing aggregators.
- The leader chooses hourly power purchases and injections at each node to maximize 24-hour energy-arbitrage profit at endogenous nodal prices.
- Stored energy follows an hourly balance, is bounded between a capacity floor and the time-varying available capacity, and returns to its initial value at the end of the day.
- The follower consists of 24 hourly AC optimal-power-flow/economic-dispatch problems. It minimizes generation cost subject to system and nodal active/reactive balance, line-flow limits, voltage limits, and generator active/reactive limits.
- LMPs are the dual variables on nodal active-power balance and feed back into the leader's profit.
- The leader is solved heuristically with an ant-colony evolutionary algorithm. Each follower OPF is solved with PyPower. The formulation is not converted to an exact single-level MPEC.
- The leader chooses physical purchases and injections, not an explicit price-quantity bid curve.

### Fleet representation and assumptions

- Vehicle-to-grid operation is allowed: the aggregator acts as a prosumer that buys energy to charge and sells stored energy.
- One company controls all EV storage in the modeled region.
- Available fleet capacity and charging demand are deterministic forecasts obtained from travel surveys and three representative vehicle categories.
- The default IEEE case sets the capacity floor at 90%, allowing the aggregator to use 10% of available battery capacity.
- The storage balance has no explicit charging/discharging efficiency or trip-energy withdrawal term. Mobility affects the time-varying available capacity and the separately forecast demand profile.
- EV discharge has zero marginal production cost, so available injections are always dispatched at the nodal price.
- Loads are inelastic. Ancillary services, uncertainty, battery degradation, cycling cost, individual charger capacity, and ramp limits are omitted.
- The authors explicitly acknowledge that unconstrained fast charging/discharging creates unrealistic steep ramps and identify ramp constraints as future work.
- The 24 follower dispatches do not include a vehicle-level service schedule or trip-to-vehicle feasibility.

### Experiments and reported evidence

- IEEE 24-bus Reliability Test System with 410,000 EVs distributed proportionally across 17 PQ load buses.
- Uncoordinated EV charging raises peak demand from about 2,000 MW to about 2,500 MW and gives a valley-to-peak ratio of 0.59.
- At night, the connected fleet represents more than 17 GWh of storage; even at the 5 p.m. travel peak, 88.5% of vehicles are assumed parked.
- Uniform-price case: network losses and congestion are ignored. The aggregator raises the valley-to-peak ratio from 0.59 to 0.75, a 26.7% flattening factor, and earns approximately $760,792/day.
- LMP case: network losses and congestion are modeled. Overall flattening is 33.7%, and profit falls to approximately $527,113/day. Effects are strongly nodal: Bus 5 has a 64.3% flattening factor, while Bus 15 has only 2.7%.
- The LMP case produces lower aggregator revenue but better aggregate flattening than uniform pricing. Both cases raise marginal prices relative to the no-aggregator market, implying short-run welfare loss despite potential long-run network benefits.
- Colombian case: 400,000 EVs, 53 generators, and a uniform-price market modeled without network losses or congestion. At peak traffic hours, 83% of vehicles are assumed parked and about 14 GW of storage remains available.
- The Colombian aggregator uses 30% of available battery capacity for maximum benefit, raises the valley-to-peak ratio from 0.63 to 0.76, produces a 21.8% flattening factor, and earns approximately $615,405/day.
- Total generation cost in the Colombian case is reported as 0.8% above the case without EVs.
- Caution: the Colombian section says 30% of capacity is required for maximum benefit, while the conclusion broadly states that a low 10% share suffices in both cases.

### Novelty this paper kills

This paper rules out an unqualified claim of being first to:

- model a monopoly EV-storage aggregator as a Stackelberg leader against a system operator;
- couple V2G arbitrage with endogenous uniform or nodal marginal prices;
- connect an EV aggregator's physical injections to AC-OPF market clearing;
- study the regulatory consequences of concentrated EV-storage market power; or
- show that a profit-maximizing aggregator can flatten demand while increasing short-run prices and reducing static market efficiency.

### Atomic EVSP gap that remains

The modeled fleet is a deterministic storage envelope. The unfilled question is whether its arbitrage profit, LMP effects, and load flattening survive when every hourly purchase or injection must be generated by a feasible bus-duty schedule with exact trip service, vehicle SOC, charging locations, charging rates, and concurrency constraints.

## Cross-paper claim discipline

An unsafe headline is: "We introduce endogenous electricity prices for EV fleets."

A defensible candidate contribution, conditional on a wider prior-art check, is:

> Embed an exact, trip-covering electric-vehicle scheduling and charging problem as the flexible-load best response in an endogenous-price equilibrium, and exploit price-independent route feasibility and price-parametric column generation to compute executable equilibria on real duty data.

Important qualification: only the physical feasibility of a trip sequence may
be tariff-independent. Its charging realization is price-specific, so a reused
sequence must be re-realized, represented parametrically, or subjected to new
exact pricing before the result can be called a complete new-price best
response.

None of these three papers uses price-parametric column generation, a cached-route EVSP best-response oracle, or damped schedule-load-price iteration. That observation preserves those as candidate method gaps, but these three papers alone do not establish that fixed-point iteration or damping is novel in the wider charging-game literature.
