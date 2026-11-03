# EV scheduling, decomposition, and learned restriction: transfer review

Search date: 23 October 2026. Scope: EGG's movement-candidate pruning, exact optimization on a restricted graph, shared charging, electricity tariffs/supply, and prospective full-graph recovery. This is a targeted primary-source review, not an exhaustive systematic review. Direct Google Scholar queries were inaccessible through this agent’s web backend; the parent researcher successfully accessed Scholar in the in-app browser and supplied two additional leads; the companion ledger records this and the fallback searches. Full text was selectively inspected for four central papers; other entries explicitly state abstract-level access. No solver runs or claims of replication are made.

## Assessment

The closest overlap is **Gerbaux, Desaulniers, and Cappart (2025)**: supervised GNN selection of network arcs before a column-generation heuristic for electric buses, including charger capacity and nonlinear charging representation. A claim that learning identifies useful connections so an exact optimizer searches a smaller graph would be too broad. Moreover, a restricted model's exact solve does not establish full-model optimality. A general recovery-and-certification workflow is also established territory in heuristic pricing and learned MIP acceleration. EGG needs an identifiable contribution in the interaction of scarce shared electricity/charging resources, movement choices, and certified computational performance.

The supplied EGG result—68% median bill improvement against a weak heuristic at 80 trips, with 92% of aggregate savings attributable to fleet count—is evidence of better fleet assignment, not yet evidence of tariff responsiveness. Treat this as the starting observation for experiments. The most revealing comparisons preserve timetable, fleet count, energy consumption, and charger infrastructure while varying prices and supply. This review's proposed experiments are recommendations, not reported literature findings.

## Twelve sources and concrete transfers

### 1. Direct learned EVSP overlap

Juliette Gerbaux, Guy Desaulniers, Quentin Cappart (2025), **A machine-learning-based column generation heuristic for electric bus scheduling**, *Computers & Operations Research* 173, 106848. [DOI](https://doi.org/10.1016/j.cor.2024.106848); [institutional full text](https://research.dial.uclouvain.be/bitstreams/6bd29199-00d3-46c3-a27a-38bcc31ecf17/download). Access: full text, especially §§5–6.

The paper's network restriction is exceptionally close to EGG. Its randomized greedy construction and learned arc scores are combined by union. The greedy construction ignores station capacity; the subsequent optimization enforces it. Charging and other protected arcs remain available. This supplies both a baseline and a warning: individually attractive connections can fail to compose into globally useful schedules. Labels come from good heuristic solutions, so absence from one label is not proof an arc is dispensable.

**Reuse:** chronological randomized insertion, union of its selected connections, per-node incoming/outgoing score budgets, and a hybrid budget. **Mismatch:** EGG's tariff/supply coupling must be explicitly compared rather than presumed absent from all EV literature. **Experiment:** equal retained-arc budgets and wall time for greedy union, GNN, hybrid, and EGG; report fleet count separately from charging expenditure, infeasibility, and recovery time.

### 2. Shared chargers without learning

Marelot de Vos, Rolf van Lieshout, Twan Dollevoet (2024), **Electric Vehicle Scheduling in Public Transit with Capacitated Charging Stations**, *Transportation Science* 58(2), 279–294. [DOI](https://doi.org/10.1287/trsc.2022.0253); [institutional record](https://research.tue.nl/en/publications/electric-vehicle-scheduling-in-public-transit-with-capacitated-ch/). Access: publisher-linked institutional abstract; published March 2024, online December 2023.

A connection network expanded with state of charge yields path variables; column generation supports price-and-branch and diving. The published record reports real concession instances up to 816 trips. **Reuse:** charger-capacity rows in a path master and a diving comparator, with full-master relaxation bounds. **Mismatch:** its discretization and charging representation need alignment with EGG; its published gaps cannot be compared to EGG's heuristic savings. **Experiment:** on an identical modest instance set, compare compact full-graph MIP, path-based CG/diving, and restricted MIP at matched time limits. Measure whether pruning helps a weak formulation more than a strong formulation.

### 3. TOU pricing is already inside exact bus scheduling

Le Zhang, Yadong Wang, Weihua Gu, Yu Han, Edward Chung, Xiaobo Qu (2024 issue; accepted 2023), **On the role of time-of-use electricity price in charge scheduling for electric bus fleets**, *Computer-Aided Civil and Infrastructure Engineering* 39, 1218–1237. [DOI](https://doi.org/10.1111/mice.13134); [institutional PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/103520/1/Zhang_Role_Time-of-use_Electricity.pdf). Access: full text, problem assumptions and formulation inspected.

It jointly considers TOU price, partial charging, and limited chargers, using an equivalent set-partitioning formulation and specialized branch-and-price. Its single terminal and round trips are important restrictions. **Reuse:** an economic baseline and a controlled single-terminal special case of EGG. **Mismatch:** geographically distributed movements and supply allocation may add coupling beyond this setting; that must be demonstrated. **Experiment:** replicate the structural special case, then add multiple terminals or binding site supply one feature at a time. At fixed fleet size, compare flat, actual, permuted, and amplified tariff profiles; report charging-cost regret and shifted load.

### 4. Recent TOU fleet/charging comparator

Zhaoyang Lu, Tianyi Xing, Yanfeng Li (2025), **Optimization of electric bus vehicle scheduling and charging strategies under Time-of-Use electricity price**, *Transportation Research Part E* 196, 104021. [Publisher record](https://www.sciencedirect.com/science/article/pii/S1366554525000626). Access: publisher-indexed abstract/highlights; direct page returned 403, so internal algorithm details were not inspected.

The record identifies joint fleet-size, charging, and scheduling decisions, an MIP, and dynamic label-setting branch-and-price. **Reuse:** direct economic and exact-method comparator; request full text before implementation. **Mismatch:** charger, depot, and tariff assumptions remain to be audited. **Experiment:** separate the value of fleet resizing from price-aware scheduling using the same fleet count and identical infrastructure. The publication prevents positioning TOU plus joint bus scheduling alone as a new problem.

### 5. Strong nonlearned network reduction

Axel Parmentier, Rafael Martinelli, Thibaut Vidal (2023), **Electric Vehicle Fleets: Scalable Route and Recharge Scheduling Through Column Generation**, *Transportation Science* 57(3), 631–646. [DOI](https://doi.org/10.1287/trsc.2023.1199); [arXiv](https://arxiv.org/abs/2104.03823). Access: February 2023 preprint full text selectively inspected; final metadata verified against the authors’ institutional research record.

The method combines nondominated charging arcs, bidirectional pricing with backward bounds, graph sparsification, and diving. **Reuse:** dominance-based charging alternatives and nonlearned sparsification before paying for labels/training. **Mismatch:** feasibility and dominance rules cannot automatically survive shared charger occupancy or time-dependent electricity opportunity costs. **Experiment:** safe dominance alone, heuristic sparsification alone, learned restriction alone, and combinations. Charge preprocessing and certification against the same total budget. Check whether apparently expensive arcs become essential under congestion or cheap-price windows.

### 6. Exact subpath decomposition and public implementation

Alexandre Jacquillat, Sean Lo (2024 preprint, revised September 2026), **Subpath-Based Column Generation for Electric Vehicle Routing Problems**; initial title **Subpath-Based Column Generation for the Electric Routing-Scheduling Problem**. [Versioned arXiv record](https://arxiv.org/abs/2407.02640); [authors' ElectricRouting.jl repository](https://github.com/sean-lo/ElectricRouting.jl). Access: current abstract, original indexed abstract, and repository README; attempted original HTML timed out.

The current abstract establishes a domination framework for subpaths between charging stations and their assembly into routes, including nonlinear charging. The original abstract explicitly discusses heterogeneous charging costs. Version changes matter: do not silently cite the old title and new results as one unchanged paper. **Reuse:** exact pricing architecture, open Julia implementation, and benchmark-generation scaffolding after license/version inspection. **Mismatch:** routing time windows differ from mandatory timetabled trip coverage; joint station capacity is not established by the inspected abstract. **Experiment:** compare subpath caching versus learned movement pruning as charger density and charging-cost heterogeneity vary, including total memory and exact recovery effort.

### 7. Crew scheduling teaches adaptive pricing restriction

Mouad Morabit, Guy Desaulniers, Andrea Lodi (2022 preprint), **Machine-learning-based arc selection for constrained shortest path problems in column generation**. [arXiv/full text](https://arxiv.org/abs/2201.02535). Access: full text, introduction and application descriptions selectively inspected.

This targets vehicle/crew scheduling and routing pricing networks, rather than directly producing a final assignment. Its discussion includes nonlearned reduced-cost arc selection and exact final pricing to establish LP termination. **Reuse:** cheap reduced-cost rankings and an adaptive restricted-pricing ladder. **Mismatch:** a final pricing certificate proves a master LP bound, not integer optimality without the required branch-and-price machinery. Crew duty resources also differ from shared chargers. **Experiment:** static learned scores versus dual-conditioned reranking, both followed by identical exact pricing. Track negative-reduced-cost columns missed, bound improvement, and end-to-end integer gap; classification accuracy is secondary.

### 8. Column selection is a different bottleneck

Mouad Morabit, Guy Desaulniers, Andrea Lodi (2021), **Machine-Learning–Based Column Selection for Column Generation**, *Transportation Science* 55(4), 815–831. [DOI/publisher abstract](https://doi.org/10.1287/trsc.2021.1045). Access: publisher abstract.

The model selects among generated columns to reduce restricted-master reoptimization time, with vehicle/crew scheduling and VRPTW applications. **Reuse:** keep pricing unrestricted while managing the master pool; this distinguishes graph-search savings from master-size savings. **Mismatch:** useful only if EGG adopts path formulations and master reoptimization is material. **Experiment:** instrument runtime first. Cross arc pruning on/off with column-pool selection on/off. If the pricing phase dominates entirely, column selection has little leverage; if the master dominates, an arc predictor may attack the wrong bottleneck.

### 9. Unit commitment: repeated-instance learning with guarantees

Álinson S. Xavier, Feng Qiu, Shabbir Ahmed (2021 journal; 2019 preprint), **Learning to Solve Large-Scale Security-Constrained Unit Commitment Problems**, *INFORMS Journal on Computing* 33(2), 739–756. [DOI](https://doi.org/10.1287/ijoc.2020.0976); [primary preprint](https://arxiv.org/abs/1902.01697). Access: full text selectively inspected; journal metadata cross-checked.

It learns constraint relevance, initial solutions, and likely solution subspaces for repeatedly solved power-system MIPs, explicitly distinguishing guaranteed and heuristic acceleration. **Reuse:** nearest-neighbor starts and conservative restrictions as inexpensive learning baselines, plus a clear guarantee taxonomy. **Mismatch:** repeated nearby load instances favor transfer; synthetic graph/topology shifts may be harder. Removing constraints enlarges a feasible set, whereas deleting EGG arcs shrinks it: the direction of bound validity reverses. **Experiment:** chronological or topology-held-out splits, ordinary warm starts, learned restriction, and restoration. Report the time to a full-model bound, not just restricted optimum.

### 10. Partial assignments as a learned restriction control

Vinod Nair and 18 coauthors (2020 preprint; revised 2021), **Solving Mixed Integer Programs Using Neural Networks**. [Primary arXiv record, full author list](https://arxiv.org/abs/2012.13349). Access: primary abstract.

Neural Diving generates partial integer assignments; SCIP completes the remaining variables. **Reuse:** a general partial-fixing comparator against EGG's structured arc elimination. **Mismatch:** completion on a fixed subproblem produces an incumbent, not a full-model certificate; training resources and instance distribution need matching. **Experiment:** compare equal numbers of free binaries and equal end-to-end budgets for partial fixing, arc restriction, and solver-native diving. Restore the full model for every certification comparison.

### 11. Direct recovery overlap, documented in 2026

Albert Brincker Olson, Richard Martin Lusby, Stefan Røpke (2026), **Graph Neural Network Enhanced Column Generation for Electric Bus Scheduling**, ROUTE 2026, 17–21 May. [DTU primary record and complete conference abstract](https://orbit.dtu.dk/en/publications/graph-neural-network-enhanced-column-generation-for-electric-bus-/). Access: complete conference abstract reproduced by institution; **preliminary conference evidence, not a full journal evaluation**.

It describes GNN edge thresholds, solving reduced pricing graphs until stagnation, lowering thresholds, and eventually restoring the full graph. It also predicts edge frequency in the basis. **Reuse:** stagnation-triggered relaxation and basis-frequency labels. **Mismatch:** an abstract's exactness claim is insufficient to audit integer certification. **Experiment:** compare fixed-time, stagnation, and resource-dual-triggered restoration with identical final full-graph search. Progressive restoration alone is not a safe novelty claim.

### 12. Recent nonlearned EVSP competitor

Yoann Sabatier Montanaro, Thomas Jacquet, Quentin Cappart, Guy Desaulniers (2025), **A Column Generation Heuristic for Multi-depot Electric Bus Scheduling**, CPAIOR 2025, LNCS 15763, 103–118. [DOI/publisher abstract](https://doi.org/10.1007/978-3-031-95976-9_7); [institutional record](https://research.dial.uclouvain.be/entities/publication/9ade952a-eef7-4c33-9299-d32682858e8f). Access: publisher/institutional abstracts; proceedings PDF exceeded backend size limit.

Its graph preselects charging opportunities; GRASP and further pruning reduce pricing subproblems without historical labels. The abstract reports performance comparable to Gerbaux et al. **Reuse:** GRASP-generated arc pools are a mandatory modern nonlearned baseline. **Mismatch:** charging-opportunity preselection may alter the feasible universe. **Experiment:** match opportunities, pool size, and preprocessing budgets, then compare GRASP, learned pools, and their union.

## Baselines and experiments that could change the research direction

A minimum serious comparison includes full-graph optimization with a good incumbent; chronological randomized greedy union; shortest-deadhead or earliest-compatible per-node budgets; reduced-cost ranking where available; nonlearned sparsification/dominance; GNN-only and greedy/GNN union; and a recovery schedule shared across all restrictions. Use a common feasible arc universe, retain necessary structural arcs, and count construction, inference, recovery, and proof time. A weak greedy schedule alone is insufficient.

Three experiments offer the best discrimination. First, fix fleet count at the best common feasible value and vary prices and shared supply while holding trips constant. This tests the energy-economics mechanism. Second, create instances where cheap charging windows collide and where a longer movement unlocks scarce charging; compare local ranks to globally coordinated selections. This tests whether learning captures coupling rather than chronology. Third, progressively restore omitted arcs and continue on the full graph. Plot incumbent cost and valid full-model lower bound over total elapsed time. This tests whether an early restricted solution actually accelerates certification.

For minimization, a feasible restricted solution supplies a full-model upper bound; its restricted lower bound generally does not supply a full-model lower bound. A completed full-graph solve or valid decomposition proof is necessary for certification. Recovery is useful engineering, but a publishable contribution requires a new justified restoration rule, a meaningful complexity/quality result, or robust evidence that resource-aware ranking changes the cost-versus-proof frontier on credible scales. FT50 aspiration should follow that contribution and economic mechanism, rather than lead to a generic ML architecture claim.
