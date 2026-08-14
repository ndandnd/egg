# Price-Maker EV Fleet Research Handoff

Date: 2026-08-14  
Repository: `https://github.com/ndandnd/egg`  
Local root: `/Users/nathan.cho/Documents/egg`

## 1. Start here: repository boundary

This is a new, independent research repository. Do not place its notes, code,
experiments, or paper archive inside `demandResponse` or `EVSP-DR`. Those are
adjacent source projects that may be inspected when needed, but they are not
the working tree for this project.

The user stopped the prior task specifically to enforce this boundary. Treat
it as a hard constraint.

Current repository state at handoff time:

- The GitHub remote is reachable and currently has no commits.
- The local repository contains an untracked `lit reviews/` directory with the
  supplied articles and an untracked `.DS_Store`.
- This handoff, the `context/` archive, and three detailed full-text review
  appendices under `literature/review_notes/` are local and uncommitted. No
  implementation code, commit, or push has been created.
- Do not delete duplicate source files without explicit approval. Record them
  as aliases in the literature index first.

### 1.1 Archived prior context

The following files were copied byte-for-byte from the adjacent EVSP-DR
working tree so the new project does not lose its lineage:

- `context/CLAUDE_HANDOFF_PRICE_MAKER_20260813.md`: Claude's original
  price-maker handoff, preserved verbatim.
- `context/evsp_dr/CURRENT_RESEARCH_PLAN_20260810.md`: corrected EVSP-DR
  research claims and modeling caveats.
- `context/evsp_dr/HANDOFF_20260810.md`: dated EVSP-DR operational handoff.
- `context/README.md`: explains the boundary and snapshot status.

SHA-256 comparison against the source files was performed after copying; all
three archive copies matched their sources. Treat operational job identifiers
in the dated EVSP-DR handoff as historical, not as current Unicorn state.

### 1.2 Detailed literature audit trail

The concise findings in Section 4 are backed by paper-level notes under
`literature/review_notes/`:

- `README.md` (coverage map);
- `BIDDING_GAMES_20260814.md`;
- `MARKET_MECHANISMS_AND_BUS_DR_20260814.md`;
- `ROUTE_AND_RESPONSE_LEARNING_20260814.md`.

Those notes preserve model structure, assumptions, reported experiment
results, limitations, novelty threats, and the exact atomic-EVSP opening. The
PDF/HTML files remain in `lit reviews/` as the primary sources.

## 2. Research goal

The initial idea was the price-maker or "chicken-and-egg" interaction:

`price -> fleet route/charge schedule -> load -> market/grid price -> price`

The user wants a thesis-scale idea, not merely another conference paper. Keep
the research direction open to game theory, mechanism design, market design,
machine learning of route/schedule response, strategic bidding, performative
prediction, and other economic applications. The immediate practical goal is
to begin controlled experiments, eventually on the Unicorn cluster, while
using the existing exact/column-generation EVSP machinery as a response oracle.

The user can delegate substantial coding to Cursor at high quality. First
settle the scientific question, benchmarks, experimental contract, and
falsification tests; then write a bounded implementation specification.

## 3. Main conclusion from the literature search so far

Do not present generic iterative price feedback as the novelty. Prior work
already covers several pieces:

- aggregate EV charging games and damped/fixed-point convergence;
- price-making EV aggregators through MPEC, Stackelberg, and price-quota-curve
  models;
- coupled traffic-power equilibria and price-responsive route/charging flow;
- learned price-to-flow or bid-to-price response;
- multi-agent reinforcement learning for strategic electricity bidding;
- machine-learning acceleration of routing and electric-bus column generation;
- VCG, core-selecting, convex-hull, minimum-uplift, and baseline-related
  settlement mechanisms.

The strongest defensible intersection found so far is:

> Exact atomic trip/duty feasibility + endogenous market-price response +
> learning or strategic equilibrium + a settlement mechanism appropriate for
> nonconvex fleet flexibility.

A useful working thesis is a **certified, learning-augmented atomic bilevel
market**. A learned model proposes prices, bids, or promising duty columns;
the exact EVSP follower/pricing oracle verifies feasibility and provides bounds
or optimality certificates. Experiments should target discontinuous schedule
switch boundaries rather than merely fitting average load response.

This remains a hypothesis, not a settled novelty claim. The new repository's
first job is to falsify or sharpen it.

### 3.1 What survives from Claude's original handoff

Claude's handoff remains useful as the project seed. It identified two
complementary tracks:

1. **Iterative/endogenous-price scheduling.** A posted price produces an EVSP
   schedule and charging load; the load changes the price; the process repeats.
   Damping, regularization, or trust regions may be needed because an atomic
   schedule response is discontinuous and can cycle.
2. **Learning the response map.** Sample price vectors, solve the EVSP, learn
   the resulting load/value/route response, and use the learned response to
   accelerate an outer pricing, bidding, or equilibrium calculation.

It also correctly separated three economic regimes that must never be mixed:

- **Price taker:** the fleet minimizes its operating cost at an exogenous
  price vector.
- **Strategic price maker:** the fleet minimizes its bill or maximizes profit
  while recognizing its own effect on clearing prices.
- **Integrated planner:** the system minimizes true incremental production
  cost plus fleet operating cost.

The old two-fidelity idea also survives: use fixed-route charging
re-realization for inexpensive local responses and invoke full column
generation periodically or at the final candidate.

### 3.2 What the deeper review changes

The deeper review removes several possible novelty claims:

- A generic price/load fixed point is not new.
- A learned price-quantity response for a strategic storage asset is not new.
- Continuous EV charging games, EPEC/MPEC storage equilibria, aggregate
  demand-shifting uplift, and storage VCG settlements are not new.
- Learning to accelerate column generation is not new.

The important correction to the old price-parametric column idea is this:

> Trip-sequence feasibility may be tariff-independent, but a stored column's
> charging realization and cost are tariff-specific.

Simply applying a new tariff to the old charging events does **not** solve the
best charging problem for that trip sequence, and it cannot certify a complete
best response. The present exact pricer also deduplicates candidate columns by
trip set in places (search for `frozenset(trips)` around the k-best and pool
update logic in `src/exact_pricer_expanded.py`), which can discard distinct
charging realizations of the same trip set. A rigorous price-parametric method
must therefore do at least
one of the following:

- re-realize every reused trip sequence at the new tariff;
- retain multiple nondominated charging realizations per trip sequence;
- store a valid parametric cost/value representation; or
- rerun exact pricing and use the old pool only as a warm start.

This correction should be treated as a first-class modeling issue, not a minor
implementation detail.

## 4. Supplied source inventory and duplicates

All supplied files currently live under `lit reviews/`.

### 4.1 Newly supplied batch: 13 files, 8 unique papers

The five ScienceDirect HTML files are incomplete publisher previews. Their
body text contains roughly 2,000-3,000 words, whereas the paired printed PDFs
contain roughly 8,000-10,000 words. For these pairs, use the PDF as the full
source and retain the HTML only as a searchable metadata/access alias.

| Canonical paper | Full source | Duplicate/preview alias |
|---|---|---|
| Deori, Margellos, Prandini (2018), *Price of anarchy in electric vehicle charging control games: When Nash equilibria achieve social welfare*, DOI `10.1016/j.automatica.2018.06.043` | `1251251.pdf` | `S0005109818303352.html` |
| Zoltowska (2016), *Demand shifting bids in energy auction with non-convexities and transmission constraints*, DOI `10.1016/j.eneco.2015.05.016` | `1245125.pdf` | `S0140988315001681.html` |
| Gonzalez Vaya, Andersson (2015), *Optimal Bidding Strategy of a Plug-In Electric Vehicle Aggregator in Day-Ahead Electricity Markets Under Uncertainty*, DOI `10.1109/TPWRS.2014.2363159` | `Optimal_Bidding_Strategy_of_a_Plug-In_Electric_Vehicle_Aggregator_in_Day-Ahead_Electricity_Markets_Under_Uncertainty.pdf` | none |
| Zou et al. (2016), *Pool equilibria including strategic storage*, DOI `10.1016/j.apenergy.2016.05.105` | `523523.pdf` | `S0306261916307097.html` |
| Fang et al. (2022), *An efficient and incentive-compatible market design for energy storage participation*, DOI `10.1016/j.apenergy.2022.118731` | `525.pdf` | `S030626192200188X.html` |
| Toquica, De Oliveira-De Jesus, Cadena (2020), *Power market equilibrium considering an EV storage aggregator exposed to marginal prices - A bilevel optimization approach*, DOI `10.1016/j.est.2020.101267` | `main3234.pdf` | `S2352152X19308837.html` |
| Xie, Xu (2025), *Strategic bidding of price-maker energy storage systems in electricity markets with limited information*, DOI `10.1016/j.apenergy.2025.125824` | `1-s2.0-S0306261925005549-main.pdf` | none |
| Wu et al. (2016), *A Game Theoretic Approach to Risk-Based Optimal Bidding Strategies for Electric Vehicle Aggregators in Electricity Markets With Variable Wind Energy Resources*, DOI `10.1109/TSTE.2015.2498200` | `A_Game_Theoretic_Approach_to_Risk-Based_Optimal_Bidding_Strategies_for_Electric_Vehicle_Aggregators_in_Electricity_Markets_With_Variable_Wind_Energy_Resources.pdf` | none |

### 4.2 Earlier supplied batch: 9 additional unique papers

| Canonical paper | Full source | Duplicate/preview alias |
|---|---|---|
| Wu et al. (2019), *Evaluating grid-interactive electric bus operation and demand response with load management tariff*, DOI `10.1016/j.apenergy.2019.113798` | `5.pdf` | `S0306261919314850.html` |
| Lu et al. (2021), *Operational scheduling of intercity passenger transportation company participating in energy and reserve markets*, DOI `10.1016/j.ijepes.2020.106541` | `4.pdf` | `134.pdf`; `S0142061520313685.html` |
| Wang et al. (2024), *Joint optimization of bidding and pricing strategy for electric vehicle aggregator considering multi-agent interactions*, DOI `10.1016/j.apenergy.2024.122810` | `3.pdf` | none |
| Ding, Li, Jian (2022), *Optimal pricing and fleet management for shared electric vehicle in coupled power and transport networks*, DOI `10.1016/j.trc.2022.103727` | `main2.pdf` | none |
| Subramanian et al. (2022), *A bilevel conic optimization model for routing and charging of EV fleets serving long distance delivery networks*, DOI `10.1016/j.energy.2022.123808` | `main1.pdf` | none |
| Chen et al. (2026), *Learning the Price Response of Spatiotemporal EV Charging Flow: A Graph-Attentive Surrogate Model*, DOI `10.1109/TTE.2026.3657374` | `Learning_the_Price_Response_of_Spatiotemporal_EV_Charging_Flow_A_Graph-Attentive_Surrogate_Model.pdf` | none |
| Wei et al. (2018), *Network Equilibrium of Coupled Transportation and Power Distribution Systems*, DOI `10.1109/TSG.2017.2723016` | `Network_Equilibrium_of_Coupled_Transportation_and_Power_Distribution_Systems.pdf` | none |
| Song et al. (2025), *Dynamic equilibrium of the coupled transportation and power networks considering electric vehicles charging behavior*, DOI `10.1016/j.tra.2025.104590` | `12.pdf` | `S0965856425002186.html` |
| Afentoulis, Vagropoulos (2025), *Are current demand response baseline designs suitable for electric vehicles? Policy insights from the independent aggregation business model*, DOI `10.1016/j.apenergy.2025.126281` | `11.pdf` | none |

Total currently identified: **26 supplied source files representing 17 unique
papers and 9 duplicate/preview aliases**.

### 4.3 Future HTML policy

The user may send HTML instead of printing a PDF. Accept it. Check whether the
saved HTML contains the complete article, including methods, results,
references, equations, figures, and tables. If it is only a publisher preview,
request the PDF. Do not ask the user to print a duplicate until this check is
complete.

### 4.4 Full-text findings that materially change the project

The following conclusions came from end-to-end review of the supplied PDFs,
not from abstracts alone.

#### Deori, Margellos, and Prandini (2018)

The paper studies continuous individual EV charging with affine prices. Each
vehicle recognizes its price impact; Nash equilibria are minimizers of a
strictly convex auxiliary potential, and the price of anarchy approaches one
as the number of independent vehicles grows. It also characterizes equilibrium
as a fixed point of tie-broken and proximal best-response maps. That is **not**
a proof that arbitrary undamped price iteration converges.

Novelty killed: generic affine-price EV charging games, potential formulations,
unique continuous equilibrium, and asymptotic efficiency.

Gap retained: a transit fleet is one concentrated player with binary duties,
shared trip-cover constraints, charging-location constraints, and possibly
charger conflicts. The Cartesian product and convexity supporting Deori's
results disappear. Comparing a discrete potential optimum, exact social
optimum, and reachable best-response equilibria is therefore meaningful.

#### Zoltowska (2016)

The paper clears multiperiod demand-shifting bids with unit-commitment and
transmission nonconvexities, then solves a direct minimum-uplift pricing model.
The uplift covers the gap between a dispatched load schedule and the load's
best attainable response at the proposed price. Its flexible load is divisible
and summarized by horizon-wide energy bounds; it is not a route/duty problem.

Novelty killed: minimum-uplift pricing for intertemporally shiftable demand.

Gap retained: replace the simple energy-shifting deviation calculation with
an exact EVSP separation oracle. At prices \(\pi\), require each dispatched
fleet schedule plus uplift to dominate **every** feasible trip-covering
schedule. Column generation can find a violated no-deviation constraint
without enumerating the schedule set. This creates an exact operational and
economic certificate that the prior paper cannot supply for mobile fleets.

#### Zou et al. (2016)

The paper models thermal, hydro, renewable, and storage firms as strategic
leaders over a common market-clearing follower. It converts each leader's
problem to an MPEC and combines their stationarity systems into an EPEC, then
uses a local nonlinear solver. Multiple solutions are possible and are selected
ex post; there is no uniqueness, global certificate, or general convergence
result for best-response iteration.

Novelty killed: continuous multi-period storage market power and EPEC/MPEC as
a generic strategic-flexibility formulation.

Gap retained: the KKT conversion fails for an integer EVSP response. Exact
fleet-deviation oracles, branch-and-price equilibrium search, duty-package
bids, and certified equilibrium-gap bounds are genuine methodological needs.

#### Fang et al. (2022)

The paper centrally dispatches continuous storage, pays the storage coalition
an aggregate VCG amount, and allocates it with asymmetric Nash bargaining over
LMP disagreement payments. Its important welfare and individual-rationality
arguments rely on convex continuous clearing. The paper's broad
"incentive-compatible" label should be used cautiously: aggregate VCG
truthfulness does not automatically make the internal Nash-bargaining split
dominant-strategy truthful for independent storage owners.

Novelty killed: storage VCG, degradation/terminal-value bidding, coalition
settlement, and Nash-bargaining allocation in a convex model.

Gap retained: an EV fleet has binary duties and mandatory service, so the
outside option cannot simply be "remove the battery." Possible counterfactuals
include fixed nonresponsive service, a replacement operator, a diesel/reserve
fleet, or procurement of trip coverage. Defining that counterfactual and
computing payments with branch-and-price are economic contributions in their
own right.

#### Xie and Xu (2025)

This is the closest full-text precedent for learning price impact from limited
market information. A 120 MW/120 MWh strategic storage asset co-optimizes
energy and three reserve products in Singapore. The authors estimate a
stochastic price-quota curve from historical demand and prices, use its
conditional mean, locally linearize it, and solve a sequence of trust-region
QPs. Their year-long backtest reports much smaller forecast-versus-simulated
income error than price-taking or a linear price curve, but the algorithm is
local and has no global certificate.

The learned relation is observational conditioning, not a causal estimate of
the price effect of inserting a new large asset. Validation draws realized
curves from the learned statistical model, the asset offers at zero price and
is assumed accepted, decisions are continuous, and there is only one strategic
actor. Reproducibility details such as KDE bandwidth, smoothing thresholds,
scenario count, finite-difference step, initial trust radii, and code are not
reported.

Novelty killed: "learn price impact from public demand/price data, then iterate
a strategic asset schedule against that response" as a standalone idea.

Gap retained: learn an atomic fleet response and a grid response jointly, use
active queries near schedule switches, correct every candidate with exact
pricing, distinguish observational from causal price impact, and extend to
networks or multiple strategic fleets.

For adapting Xie-Xu to a charging buyer, reverse the response sign. Extra
charging raises residual load and normally raises price. Also distinguish:

- price-taking cost: optimize at posted \(p_t\);
- strategic bill: minimize \(L_t g_t(L_t)\), with marginal signal
  \(g_t(L_t)+L_tg_t'(L_t)\);
- planner cost: minimize incremental generation cost
  \(\int_{U_t}^{U_t+L_t}g_t(q)\,dq\).

The fleet's bill and the system's production cost are not interchangeable.

#### Gonzalez Vaya and Andersson (2015)

One strategic PEV aggregator minimizes day-ahead charging expenditure against
a surplus-maximizing market-clearing follower. Other participants' bids are
fixed. KKT conditions, complementarity linearization, and strong duality turn
the MPEC into a MILP. Individual MATSim travel is aggregated into a virtual
battery with distribution-free chance-constraint tightening; V2G is excluded.
In the EEX-based experiment, even a fleet below 1% of traded volume visibly
changes prices.

Novelty killed: a price-making EV aggregator, day-ahead bilevel/MPEC clearing,
and uncertainty-aware strategic aggregate charging.

Gap retained: the optimized object is an hourly aggregate profile. Individual
dispatch is deferred to a real-time stage, and the authors acknowledge that
the aggregate plan may not realize exactly. Making the market-facing best
response an executable trip-covering EVSP remains materially different.

#### Wu et al. (2016)

For one aggregator, the paper combines CVaR bidding with a two-stage stochastic
security-constrained energy/reserve dispatch, reformulated through primal-dual
conditions and solved with progressive hedging. For several aggregators, it
uses a Bayesian supply-function/demand-curve game: players shift bid-curve
intercepts, estimate award and LMP sensitivities by regression, and iterate best
responses. Regulation is delivered by moving unidirectional charging around a
preferred point; fleets are aggregate power/SOC/energy envelopes.

Novelty killed: risk-aware endogenous-LMP EV bidding, joint energy/regulation
participation, and multi-aggregator Bayesian/Nash competition.

Gap retained: the fleet response is a smooth aggregate envelope, not a
combinatorial vehicle-duty solution. A multi-fleet atomic game needs exact
best-response oracles and equilibrium-gap accounting rather than an assumed
smooth regression response.

#### Toquica et al. (2020)

A monopoly EV-storage aggregator chooses nodal hourly purchases and injections
against 24 AC-OPF followers and is solved with ant-colony search plus PyPower.
It reports profitable V2G arbitrage and load flattening in IEEE-24 and Colombian
systems, but uses deterministic aggregate storage availability, cyclic energy,
zero discharge marginal cost, and omits degradation, uncertainty, ancillary
services, and explicit trip-energy withdrawals.

Novelty killed: a monopoly EV-storage Stackelberg model coupled to endogenous
nodal prices and the result that market-power behavior can flatten load while
reducing short-run welfare.

Gap retained: every injection and withdrawal must be shown to arise from a
feasible service schedule, vehicle SOC path, charging location, and realistic
power/concurrency constraint. Whether the reported arbitrage and welfare
effects survive atomic service feasibility is open.

### 4.5 Earlier supplied papers: full-text implications

#### Wu et al. (2019): grid-interactive bus operations

This bilevel/MPCC study lets a bus operator change route frequency and
opportunity-charging use in response to distribution locational marginal
prices from a lossy DCOPF. Its Shenzhen/RBTS case reports lower charging cost,
peak bus load, and losses, but part of the response comes from reducing service
vehicle-kilometers and daytime charging while increasing required battery
capacity.

Novelty killed: tactical bus-service planning plus endogenous DLMP response.

Gap retained: the model has no atomic timetabled trips, duty chaining,
deadheads, depot pull-out/in, or charger occupancy. A credible transit result
must hold every trip mandatory and measure flexibility that remains after
service cannot be sacrificed.

#### Lu et al. (2021): the closest price-making transportation precedent

This is a major novelty threat. A strategic intercity passenger company uses a
time-space network to choose vehicle locations/routes, charging/discharging,
energy bid prices and quantities, and reserve bids. A network-constrained ISO
is the follower; KKT conditions, big-M complementarity, and strong duality
produce a single MILP. The paper includes 36-vehicle IEEE-39 and 180-vehicle
large Chinese-grid cases and shows congestion-driven relocation and substantial
reserve-market value.

Novelty killed: generic price-making electric transportation company, route
changes under endogenous grid prices, joint energy/reserve bidding, and a
bilevel ISO/fleet MILP.

Gap retained: service is minimum departures on stylized one-hour city arcs,
not exact coverage of fixed trips and timestamps. It omits realistic duties,
deadheads, depots, fine-grained charging conflicts, multiple strategic fleets,
scalable branch/column generation, equilibrium certificates, and payment
design. The thesis cannot be sold as simply "routing plus LMPs."

#### Wang et al. (2024): the chicken-and-egg iteration already exists

The paper explicitly alternates charging loads, AC-based DLMPs, differentiated
retail charging prices, and price-sensitive traffic/station choice. It combines
a stochastic SOCP-relaxed power problem with robust semi-dynamic traffic
assignment. Brouwer is invoked under continuity assumptions, but convergence
of the implemented alternation is not proven; damping is used and the
highest-profit iterate is retained on failure. Reported examples require hours
and include material relaxation error.

Novelty killed: a generic price-to-route/load-to-price fixed-point loop, joint
wholesale bidding and retail pricing, and endogenous route/station response.

Gap retained: users form a nonatomic traffic equilibrium, not a fleet of
identified vehicles serving mandatory trips. There is no combinatorial
schedule, discontinuous/set-valued response treatment, exact equilibrium gap,
or settlement mechanism. This paper directly redirects us from iteration as
the contribution toward certification for an atomic response.

#### Afentoulis and Vagropoulos (2025): EV baseline gaming

This rolling 15-minute MILP schedules individual charging sessions and mFRR
bids under four real baseline rules using two real fleet datasets and French
and Greek prices. It shows that meter-before/meter-after and real-time
declarative baselines can manufacture apparent flexibility; reported claimed
flexibility can greatly exceed actual charging energy.

Novelty killed: the broad claim that EV aggregators can game conventional
demand-response baselines.

Gap retained: availability sessions are exogenous, prices are taken as given,
and routes/service do not exist. An EVSP oracle can enforce a same-service
counterfactual and test whether a claimed reduction is operationally
additional, but an optimizer-generated baseline is still manipulable if the
agent controls its inputs. Baseline-free products or a mechanism with a clearly
specified counterfactual are stronger directions than better baseline
prediction alone.

#### Ding, Li, and Jian (2022): platform-DNO pricing game

A ride-sourcing platform and a DNO compete for EV drivers who may transport
passengers or provide V2G. Drivers and travelers follow logit choice models;
the DNO chooses discharge rewards and the platform chooses fares/commissions.
The authors formulate Nash and DNO-leader Stackelberg games over a simplified
power model and multi-period fleet flows.

Novelty killed: game-theoretic incentives connecting an EV mobility platform,
travel behavior, and a distribution operator; Nash/Stackelberg formulations of
mobile EVs as storage and spatial flexibility.

Gap retained: ride-hailing service is elastic and optional, not mandatory
timetable cover. A scheduled operator's response should be an exact duty/SOC/
charger-feasible EVSP, not a smooth logit fleet flow.

#### Subramanian et al. (2022): routing with endogenous LMPs

The upper level chooses long-haul truck paths and charging while a lower-level
SOCP-relaxed ACOPF returns LMPs affected by fleet load. KKT and big-M methods
yield a mixed-integer conic MPEC. The Sioux-Falls/PJM experiment directly
demonstrates the route-load-LMP chicken-and-egg interaction, but some parameter
settings retain 6-9% gaps after eight hours.

Novelty killed: a bilevel commercial-EV routing/charging model with endogenous
electricity prices.

Gap retained: identical truck cohorts choose OD paths; there is no exact
timetable, vehicle chaining, fleet minimization, or column-generation
certificate. The known-market centralized MPEC also does not solve limited
information, strategic settlement, or scalable atomic equilibrium.

#### Chen et al. (2026): graph-attentive price-response learning

A GCN, bidirectional cross-attention, and transformer learn station charging
flows from network, OD, temporal, and service-fee inputs. Synthetic labels come
from a centralized multitemporal traffic-power optimizer. The paper reports
very accurate and fast inference on its synthetic system and good tracking on
five Nanjing stations, but the field data do not establish counterfactual
response to a price intervention.

Novelty killed: "use a graph neural network to learn price-responsive EV
charging flow" and surrogate-accelerated coupled-network optimization.

Gap retained: learn a discrete scheduled fleet's value, duty class, fleet
size, and load; target switch boundaries; detect uncertainty/OOD; and use exact
EVSP correction. Jointly learning market response and atomic fleet response is
still distinct.

#### Wei et al. (2018): static coupled-network fixed point

Nonatomic gasoline/EV traffic reaches Wardrop equilibrium on a road network
with charging links, while SOCP-relaxed radial ACOPF produces LMPs. A
best-response decomposition alternates traffic assignment and OPF. Existence
and local-stability conditions rely on continuous sensitivities; the authors
warn that poor initialization or instability can break convergence and suggest
limiting inter-iteration changes.

Novelty killed: the static
\(p\rightarrow\text{route/load}\rightarrow\text{OPF}\rightarrow p\) loop,
fixed-point interpretation, path generation, and damping motivation.

Gap retained: the population is static and nonatomic with a fixed charge per
EV. Atomic scheduling introduces a discontinuous, possibly set-valued best
response, integer fleet jumps, and different equilibrium/cycling questions.

#### Song et al. (2025): dynamic equilibrium and charger spillback

This stochastic dynamic user-equilibrium model includes departure time, path
and station choice, multiclass propagation, finite chargers and waiting areas,
queue spillback, and dynamic ACOPF LMP feedback. Its adaptive fixed-point method
is empirical; the paper states that monotonicity and strong convergence are not
available.

Novelty killed: dynamic price-traffic fixed points, coupled equilibrium with
charger capacity, and charging-queue spillback.

Gap retained: homogeneous travelers and fixed OD demand still do not create a
strategic scheduled fleet or executable trip-covering duties. Exact discrete
oracles, learning, payments, and certified equilibrium gaps remain open.

## 5. Closest external papers already identified

These should be entered into the literature index even if their files are not
yet stored locally.

### Price/route feedback and learning

- Luan et al. (2026), *Statistical regression-powered optimization methods
  for path-based congestion pricing at scale*, DOI
  `10.1016/j.trc.2025.105414`. Closest known precedent to learned
  price-to-route response with a surrogate-and-user-equilibrium loop. It is
  nonatomic and does not enforce integer fleet duties.
- Liu et al. (2024), *Contextual Bayesian optimization of congestion pricing
  with day-to-day dynamics*, DOI `10.1016/j.tra.2023.103927`. Strong baseline
  for active price experimentation.
- Bae, Kulcsar, Gros (2024), *Personalized dynamic pricing policy for electric
  vehicles: Reinforcement learning approach*, DOI
  `10.1016/j.trc.2024.104540`. EV station choice and dynamic pricing via RL,
  without exact fleet feasibility.
- Liu, Yin (2025), *End-to-End Learning of User Equilibrium: Expressivity,
  Generalization, and Optimization*, DOI `10.1287/trsc.2023.0489`.
- Perdomo et al. (2020), *Performative Prediction*, ICML/PMLR 119. Use as
  feedback-loop theory, not as a routing solution.

### Learning plus exact combinatorial optimization

- Gerbaux, Desaulniers, Cappart (2025), *A machine-learning-based column
  generation heuristic for electric bus scheduling*, DOI
  `10.1016/j.cor.2024.106848`.
- Morabit, Desaulniers, Lodi (2023), *Machine-Learning-Based Arc Selection for
  Constrained Shortest Path Problems in Column Generation*, DOI
  `10.1287/ijoo.2022.0082`. Reduced-network ML followed by full-network
  pricing preserves the LP certificate.
- Xia, Zhang (2024), *A Neural Column Generation Approach to the Vehicle
  Routing Problem with Two-Dimensional Loading and Last-In-First-Out
  Constraints*, DOI `10.24963/ijcai.2024/218`.
- You et al. (2026), *Two-Stage Learning to Branch in Branch-Price-and-Cut
  Algorithms for Solving Vehicle Routing Problems Exactly*, DOI
  `10.1287/opre.2023.0615`.
- Dumouchelle et al. (2024), *Neur2BiLO: Neural Bilevel Optimization*, DOI
  `10.52202/079017-2752`.

### Market design, payments, and bid languages

- Perez-Diaz, Gerding, McGroarty (2018), *Coordination and payment mechanisms
  for electric vehicle aggregators*, DOI
  `10.1016/j.apenergy.2017.12.036`. Price-making EV procurement plus VCG and
  redistribution; exposes truthfulness versus budget-balance tension.
- Karaca, Kamgarpour (2020), *Core-Selecting Mechanisms in Electricity
  Markets*, DOI `10.1109/TSG.2019.2958710`.
- Andrianesis et al. (2022), *Computation of Convex Hull Prices in Electricity
  Markets with Non-Convexities using Dantzig-Wolfe Decomposition*, DOI
  `10.1109/TPWRS.2021.3122000`. EV duties might serve naturally as resource
  columns.
- Bichler, Knorr, Maldonado (2023), *Pricing in Nonconvex Markets: How to Price
  Electricity in the Presence of Demand Response*, DOI
  `10.1287/isre.2022.1139`.
- Hubner, Hug (2026), *Package Bids in Combinatorial Electricity Auctions:
  Selection, Welfare Losses, and Alternatives*, DOI
  `10.1287/opre.2024.0777`. Important for representing a finite set of atomic
  fleet schedules as XOR package bids.
- De Vivero-Serrano, Bruninx, Delarue (2019), *Implications of bid structures
  on the offering strategies of merchant energy storage systems*, DOI
  `10.1016/j.apenergy.2019.113375`.
- Zhang, Zavala (2022), *Remunerating space-time, load-shifting flexibility
  from data centers in electricity markets*, DOI
  `10.1016/j.apenergy.2022.119187`. The virtual-link concept is a useful
  economic analogy for trip/duty-linked flexible demand.

### Baselines and incentive design

- Muthirayan et al. (2020), *Mechanism Design for Demand Response Programs*,
  DOI `10.1109/TSG.2019.2917396`.
- Vuelvas, Ruiz, Gruosso (2018), *Limiting gaming opportunities on
  incentive-based demand response programs*, DOI
  `10.1016/j.apenergy.2018.05.050`.
- Satchidanandan, Roozbehani, Dahleh (2022), *A Two-Stage Mechanism for Demand
  Response Markets*, DOI `10.1109/LCSYS.2022.3186654`.
- Ziras, Heinrich, Bindner (2021), *Why baselines are not suited for local
  flexibility markets*, DOI `10.1016/j.rser.2020.110357`. Capacity-limit
  products may be more defensible than counterfactual baseline payments.
- Askeland, Bjarghov (2026), *Strategic baseline manipulation in local
  flexibility markets: Market design and policy implications*, DOI
  `10.2139/ssrn.7050528`.

## 6. Candidate thesis directions to keep alive

These are alternatives, not commitments.

### Direction A - Certified atomic price-maker fleet market

Embed exact trip-covering fleet schedules in market clearing. The fleet
anticipates endogenous prices, but a learned surrogate is never trusted for
feasibility: an exact EVSP response/pricing oracle verifies schedules and
produces bounds. This is the current leading direction.

### Direction B - Fleet duties as a bid language

Treat complete feasible duties or load profiles as package/XOR bids. Study how
many bids are needed to approximate the fleet's nonconvex flexibility, how to
generate them by column generation, welfare loss from bid limits, and payment
rules. This connects EVSP directly to combinatorial market design.

### Direction C - Counterfactual-free flexibility products

Avoid paying against a manipulable baseline. Derive feasible capacity-limit,
energy-envelope, or schedule-right products from the exact fleet model and
compare them with conventional baseline demand response. Study truthfulness,
budget balance, cost recovery, and operational deliverability.

### Direction D - Active learning at schedule-switch boundaries

The price-to-schedule map is discontinuous and often set-valued. Adaptively
query price space near changes in the optimal duty set, rather than minimizing
average prediction error. The surrogate proposes; exact solves label and
certify. Include out-of-distribution detection and fallback.

### Direction E - Competition and mitigation

Extend from one strategic fleet to multiple fleet aggregators, generators, or
charging networks. Compare EPEC, multi-agent learning, core-selecting payments,
market-power mitigation, welfare, and distributional outcomes.

### 6.1 Current recommended umbrella thesis

The most coherent thesis-sized program is **exact markets and incentives for
nonconvex mobile flexibility**. Its mathematical object is not an aggregate
battery; it is the set of complete, feasible, trip-covering fleet schedules.

A working thesis question is:

> How should a power market clear and compensate mandatory, indivisible
> electric-fleet schedules so that operations remain exact, selected fleets
> have no profitable feasible rescheduling deviation, and prices/payments are
> economically defensible under endogenous prices and market power?

This can support four connected chapters rather than unrelated algorithm
papers:

1. **Atomic response and equilibrium.** Characterize the discontinuous
   price-to-duty response; compute or bound strategic and multi-fleet
   equilibria with exact deviation oracles.
2. **Learning with correction.** Learn grid price impact and fleet response,
   actively sample schedule-switch boundaries, and retain exact fallback and
   certificates.
3. **Bid language and clearing.** Express feasible duties/load profiles as
   XOR/package bids or generated columns; quantify welfare loss from limited
   menus and clearing approximations.
4. **Prices and payments.** Compute minimum-uplift, convex-hull/core-selecting,
   or carefully defined VCG-like settlements using the EVSP as the no-deviation
   and counterfactual oracle.

The common computational contribution is a reusable branch/column-generation
oracle that supplies feasible packages, best responses, violated incentive
constraints, and counterfactuals. The common economic contribution is to show
where continuous-storage intuition fails because service obligations and
integer fleet schedules create lumpy, concentrated flexibility.

### 6.2 Brainstorm ideas worth preserving

- **Exact no-deviation pricing.** Given a dispatched fleet schedule and prices,
  solve the EVSP to find the best deviation; add a cut until no profitable
  deviation remains or report a certified incentive gap.
- **Discrete potential game.** Under affine residual prices, test whether a
  finite potential representation survives for fleets, then quantify
  equilibrium multiplicity and price of integrality.
- **Atomic convex-hull prices.** Use Dantzig-Wolfe duty columns to construct a
  convexified fleet flexibility set and compare uplift with LMP.
- **XOR duty packages.** Let a fleet offer mutually exclusive complete service
  plans. Learn which packages matter, but restore full pricing when the
  restricted menu misses a welfare-improving plan.
- **Switch-boundary active learning.** Allocate exact Unicorn solves where a
  small price change alters a trip sequence or fleet size, not where the
  response is already smooth.
- **Joint response learning.** Learn both
  \(F_\theta(p,z)\rightarrow(\text{load},\text{value},\text{schedule class})\)
  and \(G_\phi(L,z)\rightarrow p\), then exact-correct the coupled fixed point.
- **Causal price impact.** Separate observational demand-price conditioning
  from the counterfactual effect of adding fleet load; use public supply stacks
  or a structural market simulator when possible.
- **Counterfactual-free products.** Sell an exact capacity limit, feasible
  charging envelope, or service-linked flexibility right rather than pay
  against a manipulable baseline.
- **Market-power onset.** Identify a threshold in fleet scale and nodal
  concentration at which price-taking ceases to be an acceptable
  approximation.
- **Strategic bid compression.** Study the tradeoff between revealing a large
  schedule menu and using a compact, strategically chosen bid language.
- **Multiple fleets.** Compute exact unilateral deviations and an equilibrium
  gap even when a full EPEC cannot be converted to KKT conditions.
- **Distribution and fairness.** Track who funds uplift or VCG deficits, how
  fixed consumers are affected, and whether market-power mitigation shifts
  costs without improving welfare.

## 7. EVSP-DR algorithmic inheritance

The new repository should call or wrap EVSP-DR as an adjacent oracle; it should
not copy active solver code into `egg` until an interface and licensing/version
policy are deliberately chosen.

Verified adjacent source at handoff time:

- repository: `/Users/nathan.cho/Documents/demandResponse/EVSP-DR`;
- branch: `peel-and-price`;
- commit: `b50d648` (`Handoff for the price-maker (chicken-and-egg) project`).

Re-verify the branch and commit before implementation because EVSP-DR can
continue to change independently.

At handoff time the adjacent checkout also contained unrelated untracked
single-duty audit/generation files. They belong to the user's EVSP-DR work and
were neither copied nor modified for `egg`.

### 7.1 The old dynamic-programming column pricer

The relevant historical implementation is `src/pricing_dp_og.py`, not
`src/pricing_dp.py`. Git history records the original Claude DP work and later
queue/dominance fixes. Its core design is reusable:

- a forward-labeling resource-constrained shortest-path problem;
- a mostly static compatibility/DAG structure built once and reused across
  column-generation iterations;
- resources for time, SOC, visited trips/incidence, charging stops, deadhead
  energy, and other route state;
- reduced cost consisting of fixed bus cost, movement/charging cost, and
  negative trip-cover dual contributions;
- pricing entry points `solve_pricing_dp` and `make_dp_pricer`;
- time-ordered or reduced-cost queues, alternative dominance modes, label
  caps, and time limits.

Useful historical grep anchors in EVSP-DR include:

- `2db2c67` - first DP push from Claude;
- `1838bb0` - DP reported as working well;
- `8f891c6` - heap/queue ordering work;
- `4d8606c` - working `duck10` lineage;
- `ecb8a31` - first-trip fair pricing queue.

These are provenance anchors, not recommendations to check out an old commit.
The live branch contains later corrections.

This is exactly the architecture that makes repeated price experiments
plausible: physical feasibility changes slowly or not at all, while tariffs and
master duals change frequently. But it must be labeled correctly. The old DP
is exhaustive only when no time limit and no label-cap eviction cuts off the
search. In the research lineage it is a high-value heuristic/response engine,
not the preferred certification oracle.

Operationally, each outer price or column-generation iteration should keep the
static feasibility graph but refresh every price-dependent charging arc cost
and every trip-cover dual contribution before solving reduced cost. Existing
code also contains conceptual placeholders for station-capacity and discharge
dual terms; those should be treated as unfinished interfaces until their signs,
units, and master constraints are verified end to end.

### 7.2 The current exact discretized pricer

`src/exact_pricer_expanded.py` constructs an SOC-by-time expanded network and
solves ordinary shortest paths rather than relying on heuristic label
dominance. When it completes and its minimum reduced cost is nonnegative within
tolerance, it certifies that no improving column exists in the **discretized
expanded route space**. It supports delayed price-responsive charging,
conservative SOC rounding, journals, snapshots, and resume.

That certificate is bounded by the discretization and the modeled physics. It
is not a claim of exactness for every continuous charging trajectory or for
model features not represented in the network.

### 7.3 Master problem and inexpensive re-realization

- `src/master.py` is the restricted master used with duty columns and includes
  hour-split charging cost consistent with the pricing math.
- `src/master_lp_scipy.py` supplies an LP master path useful for duals and
  lightweight experimentation.
- `src/rerealize_routes.py` fixes a trip sequence and re-optimizes its charging
  decisions under a target tariff/physics model, then replay-validates the
  result. This is the natural cheap inner oracle for repeated prices.
- `src/run_exact_pool_mip.py` selects an integer schedule from a generated
  column pool. A pool optimum is not a proof that no omitted duty would improve
  the integer schedule.

### 7.4 Correct two-fidelity price-response architecture

A safe initial outer loop is:

1. Start from a validated EVSP schedule and price vector.
2. Re-realize the selected trip sequences at the candidate price.
3. Re-solve the restricted master over re-realized/warm-start columns.
4. Update the market price response with damping or a trust region.
5. Detect schedule-hash cycling and objective non-improvement.
6. Invoke the old DP for fast discovery of materially different duties.
7. Periodically, and always for headline/final candidates, invoke the expanded
   exact pricer to search the full discretized route space.
8. Record the final reduced-cost certificate, discretization, and any
   time/label limits.

Warm-start reuse is valuable, but the following hierarchy must be explicit:

| Result | Honest label |
|---|---|
| Old charging events merely re-costed | Exposure of a fixed realization |
| Fixed trip sequence re-realized | Exact/validated charging response for that sequence, subject to its model |
| Restricted pool re-optimized | Finite-pool optimum |
| Old DP with caps/time limit | Heuristic duty response |
| Expanded pricer completed with no negative reduced cost | LP pricing certificate in the discretized route space |
| Pool MIP solved | Integer optimum over the current pool only |

### 7.5 Corrected EVSP-DR factual baseline

The archived corrected plan records the state that should be inherited:

- small exact-pricing cases were validated and delayed charging is native;
- journals and recoverable snapshots exist;
- a constructed `k=40` union produced validated 39-bus schedules versus a
  40-bus GIRO reference, but this is a finite-pool result and was not verified
  as one real service day;
- shared charger capacity was not modeled in that result;
- reported costs are lower bounds under the modeled infrastructure;
- a prior 0.07% "savings" statement was withdrawn because the compared tariffs
  differed; repricing is exposure, not savings;
- terminal-energy policy, a possible charge-start fee, and station-specific
  power versus a synthetic 300 kW rate remain modeling choices.

Do not turn any of those qualified results into stronger claims in the new
project.

## 8. Initial experiment ladder

Do not write implementation code until the experimental contract has been
reviewed with the user.

### 8.1 Phase 0 - Freeze the oracle and data contract

Start with small Partille cases such as `k=8` and `k=13`, not unresolved large
pool-MIP claims. Before any learning, produce one normalized record for every
solve/iteration containing:

- instance, service date if known, and input hash;
- price vector, base-load vector, node/station mapping, and market model;
- fleet multiplier and charger assumptions;
- selected trip sequences and stable schedule hash;
- charging realization, station-hour kWh, aggregate MW, and peak-window kWh;
- fleet size, deadhead, charge starts/visits, initial SOC, and terminal SOC;
- objective decomposed into bus, deadhead, electricity, degradation, and
  settlement terms;
- oracle tier: fixed-realization exposure, re-realization, restricted pool,
  capped DP, or completed expanded pricing;
- feasibility/replay status, LP reduced-cost bound, integer pool gap, solver
  status, wall time, random seed, code commit, and artifact paths.

The existing hourly-load aggregation in EVSP-DR's
`src/analyze_peak_shift.py` can seed the data extraction, but its output should
be re-validated against the final schedule schema.

### 8.2 Phase 1 - Synthetic response with known ground truth

Use a transparent monotone response first, for example

\[
p_t(L_t)=a_t+b_tL_t,
\]

then add smooth nonlinear and piecewise curves. Sweep fleet/load multiplier,
market-depth slope \(b_t\), price initialization, damping, trust-region radius,
and oracle tier. Compare:

1. exogenous price taker;
2. undamped posted-price/fleet-response iteration;
3. damped or proximal iteration;
4. Xie-Xu-style trust-region response optimization;
5. strategic fleet-bill optimum;
6. integrated generation-cost planner optimum.

Do not call price convergence schedule convergence. Log schedule hashes and
load vectors so fixed points, two-cycles, longer cycles, and price tolerance
artifacts can be separated.

### 8.3 Phase 2 - Map atomic switch boundaries

Perturb one hour/node at a time, then use low-dimensional directional and
random perturbations. Record:

- intervals over which the same trip sequence remains optimal;
- charging-only versus trip-sequence versus fleet-size changes;
- objective margin to the next schedule;
- number and identity of near-optimal alternative columns;
- local Lipschitz behavior of aggregate load away from switches;
- discontinuity size at a switch;
- hysteresis/cycling under the outer price update.

This phase answers whether a smooth aggregate response is adequate. If almost
all relevant variation is charging-only, the thesis should lean toward market
design or causal price impact rather than overselling route learning. If duty
switches are frequent and economically material, active boundary learning and
atomic equilibrium become stronger.

### 8.4 Phase 3 - Two-fidelity outer iteration

Use route re-realization at most iterations. Trigger the old DP or exact
expanded pricing when any of the following occurs:

- the outer objective fails to improve;
- a schedule cycle is detected;
- the candidate moves outside the sampled price region;
- restricted-pool reduced costs deteriorate;
- a fixed number of cheap iterations has elapsed;
- the run is a reported final candidate.

Compare cold full solves, pool warm starts, re-realization plus restricted
master, capped-DP discovery, and exact audits. The scientific outcome is the
speed/certificate frontier, not merely runtime reduction.

### 8.5 Phase 4 - Learn market and fleet responses

For the market side, first replicate a simple conditional expected
price-quantity curve using a strictly rolling training window. Compare KDE,
monotone splines/GAMs, monotone boosting, and a structural supply-stack model
if bid data are available. Label historical conditioning as observational
unless the identification design justifies a causal claim.

For the fleet side, begin with targets that are stable enough to learn:

- objective/value and exactness status;
- aggregate and station-hour load;
- schedule class or trip-set signature;
- promising arcs/columns for restricted pricing.

Do not begin by asking a neural network to emit a fully feasible duty schedule.
Use ML to rank or propose, then re-realize and exact-price. Compare random,
space-filling, Bayesian, uncertainty-based, and switch-boundary active sampling.

### 8.6 Phase 5 - Economic experiments

Once the response oracle is trustworthy:

- scale fleet size and nodal concentration to find the onset of economically
  material market power;
- compare strategic bill minimization with true system welfare;
- clear finite XOR duty menus and quantify welfare loss versus bid budget;
- compute LMP-plus-uplift, minimum-uplift, convex-hull/core-selecting, and
  carefully defined VCG-like payments;
- use the EVSP as a separation oracle for profitable schedule deviations;
- introduce a second fleet or strategic generator and report a certified
  unilateral-deviation/equilibrium gap even if global equilibrium is unknown;
- report consumer payments, generator surplus, fleet profit, uplift/deficit,
  budget balance, emissions if modeled, and operational feasibility.

### 8.7 Decision gates and falsification tests

Stop or redirect a line of work if:

- price-taking and strategic solutions remain operationally and economically
  indistinguishable across credible scale and market-depth ranges;
- duty switches are rare and re-realization explains nearly all response;
- a smooth aggregate model plus standard trust-region optimization performs as
  well as the exact-corrected atomic method;
- exact audits frequently overturn surrogate candidates without a learnable
  uncertainty signal;
- a proposed payment rule depends on an indefensible transit-service
  counterfactual;
- the contribution reduces to applying an existing MPEC/RL/BO method to a new
  dataset without an atomic-feasibility or economic theorem/certificate.

For every run, retain provenance: instance hash, code commit, price/model
parameters, random seed, solver status, bound/gap, and exact-versus-heuristic
label.

## 9. Files the next task should create

This handoff contains the complete review state and implications for all 17
unique supplied papers. The next organizational pass should normalize that
material into these files under this repository, not elsewhere:

- `literature/LITERATURE_INDEX.md`: canonical deduplicated bibliography and
  structured paper notes.
- `literature/NOVELTY_MATRIX.md`: rows as papers, columns as atomic routing,
  endogenous price, learning, strategic actors, network clearing, settlement,
  exactness/certificates, and data realism.
- `literature/RESEARCH_DIRECTIONS.md`: live hypotheses, threats, falsification
  tests, and decisions.
- `literature/READING_QUEUE.md`: available, reviewed, needs PDF, and deprioritized.
- `literature/papers.csv`: stable machine-readable metadata keyed by DOI.
- `.gitignore`: at minimum ignore `.DS_Store`; decide with the user whether
  article binaries should be committed or kept local/LFS-only before adding a
  PDF rule.

Use one canonical DOI/title entry per paper and retain all filenames as aliases.

## 10. Next PDFs to request from the user

Ask for article PDFs only. Do not ask for inaccessible datasets or
supplementary files.

Priority:

1. Liu and Yin (2025), *End-to-End Learning of User Equilibrium*, DOI
   `10.1287/trsc.2023.0489`.
2. You et al. (2026), *Two-Stage Learning to Branch in Branch-Price-and-Cut
   Algorithms for Solving Vehicle Routing Problems Exactly*, DOI
   `10.1287/opre.2023.0615`.
3. De Vivero-Serrano, Bruninx, Delarue (2019), *Implications of bid structures
   on the offering strategies of merchant energy storage systems*, DOI
   `10.1016/j.apenergy.2019.113375`.

If Cornell cannot provide one, skip it and use an author manuscript or the
verified metadata. Do not repeatedly ask for the same inaccessible item.

## 11. Immediate next-task instructions

1. Confirm the working directory is `/Users/nathan.cho/Documents/egg`.
2. Read this handoff and `context/README.md` completely.
3. Read Claude's archived handoff for provenance, but use this document's
   corrections when the two differ.
4. Inspect an actual PDF before quoting a paper or relying on a fine numerical
   detail; the summaries here are a research map, not a substitute for source
   verification in a manuscript.
5. Deduplicate by DOI/title without deleting source files.
6. Build the literature index and novelty matrix before proposing a final
   thesis claim.
7. Keep brainstorming alternatives. State clearly which literature kills a
   proposed novelty and which assumptions create a defensible gap.
8. Present the formal single-fleet model, exactness hierarchy, and logging
   contract to the user before implementation.
9. After approval, give Cursor a bounded Phase-0/Phase-1 implementation task
   with acceptance tests; independently audit its output before any Unicorn
   launch.
10. Do not push or merge until the user has reviewed what will enter the empty
    `egg` remote.

## 12. User preferences and guardrails

- Evidence first: inspect the real paper/repository before claiming novelty.
- Be critical; do not agree merely to be agreeable.
- Keep claims narrow and distinguish exact certificates, finite-pool
  optimality, heuristic solutions, and simulations.
- This should be a core PhD-thesis idea with several coherent chapters, not a
  broad collection of unrelated algorithms.
- Starting experiments early is encouraged, but data collection must be
  designed to discriminate among research hypotheses.
- Existing EVSP-DR and dynamic-pricing algorithms may be reused as baselines or
  oracles, but their repository remains separate.
- Heavy implementation can be delegated to Cursor after the method and
  acceptance tests are specified.
