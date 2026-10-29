# Self-study outline: what EGG currently establishes

Historical preparation outline. The completed22-slide deck, GUIDE.md and
DECK_CONTENT.json supersede this outline's pending status and original count.

Prepared 29 October 2026. Eighteen slides; teach the model before interpreting results. Sources below are repository-relative to `ml-prediction-20261017`. This outline reads archived conclusions; it does not independently reproduce computations. The 28 October capacity/fee characterization is completed evidence. The richer-duty support extension being developed on 29 October is pending integration and must not be presented as proved from this outline.

## 1. The question in one sentence

Can a physically feasible electric-bus fleet be optimal for the system, yet want to change its schedule when offered the marginal electricity prices associated with its own load? Yes, in an explicit model. Whether this occurs materially in operational fleets remains open.

Visual: timetable → complete fleet → electricity load → marginal tariff → fleet response.

Source: `paper/latex/main.tex`; `research-20261028/paper_core_verification/STATE.md`.

## 2. What EVSP decides, and what the grid decides

EVSP means electric vehicle scheduling problem: assign mandatory services to buses, connect them with feasible movements, and schedule charging within battery and shared-charger limits. A duty is one bus's work; a complete fleet covers all services together. The grid supplies the fleet's time-indexed energy load, at a cost that can depend on total demand. V2G would allow energy export; it is not implemented in the inspected current experimental path.

Visual: separate transport decisions from supply-cost calculation, joined by hourly energy.

Source: `paper/latex/model_theory.tex`; `research-20261028/paper_core_verification/STATE.md`.

## 3. Keep four objects distinct

- Plan x: actual assignments, movements and charging for every bus.
- e(x): its vector of purchased grid energy, in kWh per market interval.
- c(x): intrinsic operating cost, such as a fee per used bus.
- F(e): incremental electricity provision cost, conditional on background demand.

The fleet set X must be the same in planning, posted-price response and convexification. Feasible-looking separate duties may violate fleet-wide charger capacity when combined.

Source: `paper/latex/model_theory.tex`.

## 4. Three objectives answer different questions

Planner: minimize c(x)+F(e(x)). Posted-price fleet: minimize c(x)+p·e(x), holding the announced p fixed across alternatives. Strategic fleet: anticipate how its choice changes the eventual price and bill; an illustrative objective is c(x)+p_x·e(x), but an actual strategic model requires a settlement rule.

System supply cost is not automatically the fleet's bill. Calling a fleet “large” does not turn a fixed-price deviation test into strategic behavior.

Source: `paper/latex/model_theory.tex`.

## 5. Background U and quadratic coefficients

U denotes background grid demand in the learning pilot, not bus battery inventory. Curvature b describes how strongly marginal supply cost rises with load. The manuscript's separable convention is F(e)=Σ(a_t e_t+b_t e_t²/2), so p_t=a_t+b_t e_t. In a background-load model, the incremental cost is C(U+e)−C(U); U can therefore change the effective linear coefficient. Distinguish predicting U from choosing a route, and distinguish a coefficient from an observed market price.

The pilot RESULTS establishes explicit background U and curvature b, but does not reproduce its full formula or numerical coefficient table. Do not invent those values or silently transfer manuscript coefficients into that experiment. The half-factor is a notation convention that must be checked before comparing formulas.

Source: `paper/latex/model_theory.tex`; `research-20261027/grid_information_pilot/RESULTS.md`.

## 6. Why full replenishment matters

Every used bus starts and ends full. Otherwise a cheap horizon might consume initial battery inventory without paying to replace it. In the lossless two-service example, both fleet structures buy exactly 30 kWh; the issue is timing and vehicle count, not free initial energy.

Visual: initial inventory → service consumption → charging → identical terminal inventory.

Source: `paper/latex/exact_results.tex`.

## 7. Build the two-service example

A runs during [0,1], B during [2,3]; each uses 15 kWh. Batteries hold 20 kWh. Early charging [1,2] has 10 kW capacity; terminal charging [3,4] has 30 kW. A single bus must buy (10,20) kWh across the windows. Two buses can buy (q,30−q), q∈[0,10]. Each bus costs 7 synthetic units.

Supply cost F(q,z)=4q+(q²+z²)/10. These are declared synthetic units and simplified physics, not calibrated tariffs.

Source: `paper/latex/exact_results.tex`.

## 8. Physical optimum 97; hull optimum 94.8875

The best one-bus physical plan costs 97; the best two-bus physical plan costs 99. Thus D=97. The complete-fleet hull permits convex mixtures of whole feasible plans and achieves CH=94.8875; Δ=D−CH=2.1125.

Its mixture weights are 27/40 on one bus at (10,20) and 13/40 on two buses at (0,30). The mean is a bounding object, not an executable fractional fleet. Alternating those plans across days costs 99.275 on average: F(mean load) differs from mean F(load).

Source: `paper/latex/exact_results.tex`.

## 9. Where the regret 13 comes from

At the physical optimum, marginal prices are p=(6,4). The one-bus private objective is 7+6·10+4·20=147. At that same fixed price, two buses charging (0,30) cost 14+4·30=134. Regret is 147−134=13. This is not the planning gap 2.1125 or a measured compensation payment.

Learner question: Why can the planner prefer one bus while the fleet prefers two? Answer: the planner compares nonlinear supply cost, whereas the posted-price fleet compares a linear bill at one fixed price.

Source: `paper/latex/exact_results.tex`; `paper/latex/model_theory.tex`.

## 10. The general support logic is established theory

Define V(p)=min over X of c(x)+p·e(x), and r(x;p)=c(x)+p·e(x)−V(p). Under the stated compactness, common-model and duality assumptions, an own marginal price gives r(x;p)≥c(x)+F(e(x))−CH≥Δ. A positive physical/hull gap therefore rules out own-price support. Zero gap permits support under the theorem's attainment qualifications.

Where supply is nonsmooth, test existence over the admissible price set. One solver-selected multiplier cannot rule out another supporting price. This is a specialization of existing convexification and price-support theory.

Source: `paper/latex/model_theory.tex`; `research-20261028/paper_core_verification/PRIOR_ART.md`.

## 11. What the closest prior work already does

Hümbs et al.: integral participants and supporting linear prices. Hua–Baldick: convex hulls, duality and lost opportunity costs, including ramps. Andrianesis et al.: entire feasible schedules as columns, self-scheduling pricing and column generation. Zoltowska–Lin: detailed bus charging aggregation and auction disaggregation, allowing terminal inventory at minimum.

The plausible narrow distinction is explicit endogenous bus assignments with mandatory full replenishment and carefully stated participant rights. There is no verified “first” claim. The current Hreinsson comparison is abstract-only, so absence of a coalition-regret theorem there is unverified.

Source: `research-20261028/paper_core_verification/PRIOR_ART.md` (contains primary links and inspection scope).

## 12. Completed extension: capacity and vehicle fee jointly matter

Here K is terminal charging power in kW, not battery capacity. For the one-hour terminal window its numerical energy limit is K kWh. For 20<K≤30, set l=30−K and d=K−20. At positive fee f, the completed characterization gives Δ>0 exactly when max(0,(2/5)d(l−5))<f<2d. Boundaries and zero-fee cases require their separately stated handling.

Increasing terminal capacity can create support failure while never increasing the planner's optimal cost. More flexibility does not worsen welfare; it can change whether a linear tariff supports the optimum. The 20 exact comparisons qualify implementation, not prevalence or proof by sampling.

Source: `research-20261028/paper_core_verification/RESULTS.md`.

## 13. Ownership changes the relevant deviation

In the replicated family, the planning gap is at most 5/n and tends to zero. Along n=40k+1, absolute whole-owner regret tends to 351/40. A single owner can change all its buses together. With separate owners each controlling one service pair and reserved connector rights, each owner's incentive is at most 20/n and vanishes.

Learner question: Does a small planning gap imply negligible incentives? Answer: not for the absolute gain of an owner controlling the whole fleet; per-bus and separately resourced individual gains do vanish here. Shared capacity rights are part of the model.

Source: `paper/latex/exact_results.tex`.

## 14. Public timetable: useful bounds, unresolved support

The manuscript studies 37 services in two separate one-depot variants of one public timetable. Energy, fee and supply-cost inputs include synthetic assumptions. Flat-price optimization cannot exhibit a physical/hull gap. For the nonlinear depot-15 case, 429.22≤CH≤D≤512.77, giving 0≤Δ≤83.55.

Learner question: Has the public case confirmed support failure? Answer: no; the gap interval includes zero. A feasible incumbent or its positive regret does not settle the optimal fleet's support. Two depot variants are not independent timetable replication.

Source: `paper/latex/public_case.tex`; `research-20261028/paper_core_verification/STATE.md`.

## 15. Conventional recovery: failure is part of the evidence

Independent fixed-duty F delivered all eight cases. Full discovery N and simple diving D each strictly delivered only four; all their larger 24-service selections failed despite physical fleets being available through F. Ordinary joint finite-bank completion delivered all eight per variant, but retained no improved larger-case value. Its approximately 0.225% mean paired grid-electricity gain does not imply the same realized saving.

This closes learned selection acceleration on those tested finite banks. It does not prove that omitted routes have no value, nor that unrestricted EVSP is solved. Include acquisition and physical admission costs when discussing speed.

Source: `research-20261027/conventional_recovery_continuation/RESULTS.md`.

## 16. Learning pilot: information helped; neural increment was absent

The new synthetic pilot used eight evaluation timetable groups with eight contexts each, not 768 independent instances. Conditional background information improved on unconditional policy by about 0.995% mean paired electricity cost. A fixed-route information reference matched the joint-routing reference, so no added route-value mechanism appeared.

Quadratic ridge had the best fitted expected cost, 71.352922 versus the conditional-mean reference 71.276929. Larger neural MSE reached 71.368882; same-size decision-focused training reached 71.621344. Operations 400 are excluded. These results support useful information but no learned advantage over the strongest classical baseline.

Source: `research-20261027/grid_information_pilot/RESULTS.md`.

## 17. Capacity mattered; “just enlarge the model” is insufficient

The 128×128 MSE network improved over 32×32 in seven of eight group means. A separate privileged noiseless fit diagnostic passed its interpolation criterion. Neither establishes convergence or generalization of all models: main fitting hit the 500-update ceiling, and the diagnostic used different labels. The old GNN's architecture/input/supervision diagnosis remains unresolved.

The decision-focused recipe also excluded epoch 0 from checkpoint selection and used a finite-bank surrogate. Its loss is evidence about that recipe, not a universal failure of decision-focused learning. A stronger model still needs meaningful residual decision value beyond classical controls.

Source: `research-20261027/grid_information_pilot/RESULTS.md`.

## 18. What would materially strengthen the research

The main obstacle is significance and distinctiveness. A structural result could specify when extra physically admissible duties preserve or erase the obstruction. Any richer-duty extension now being developed must be inserted only after its statement, assumptions and proof have passed review; this outline does not establish it. Operational evidence would require an explicit participant/tariff institution, independent timetables and informative global support bounds. ML work would need a distinct decision with attainable value beyond strong controls and complete end-to-end comparison.

Current evidence: analytical mechanism and completed capacity/fee characterization. Open: practical prevalence, calibrated magnitude, public optimal-fleet support and a competitive neural method. The research guide should let the learner explain these boundaries, not merely repeat the headline.

Source: `research-20261028/paper_core_verification/STATE.md`; `research-20261028/paper_core_verification/RESULTS.md`; `paper/latex/main.tex`.
