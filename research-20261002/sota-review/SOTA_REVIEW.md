# EGG: literature review and a research plan for reliable learning-assisted fleet optimization

**Research date:** 2 October 2026. **Status:** first synthesis; source challenges and mathematical review continue through 13:00 America/New_York (17:00 UTC). **Branch:** `codex/sota-review-20261002`, based on Claude's handoff commit `c560378adc84ef010afe5c4b1bfce0408dd1704b`. No cluster jobs, optimization experiments or sealed-data inspection were performed for this report.

## 1. Assessment and recommendation

Claude's new results justify continuing the computational research. They change the useful role of learning: a movement scorer can reduce the search problem while an optimizer retains control of routes and charging. That is a much stronger direction than requiring independently predicted edges to constitute an executable fleet. However, **neither learned electric-bus arc pruning nor per-trip top-m selection is a new contribution by itself**.

The closest prior work is Gerbaux, Desaulniers and Cappart's *A machine-learning-based column generation heuristic for electric bus scheduling*, **Computers & Operations Research 173, 106848 (2025)**. It combines GNN and greedy arc selection, learns from good feasible incumbents, includes charging constraints, and studies hundreds to thousands of trips. Its per-trip rule keeps high-scoring incoming and outgoing arcs. It therefore overlaps with the central idea behind E3 and E10, although its route-column formulation and cost model differ from EGG. [Published paper](https://research.dial.uclouvain.be/bitstreams/6bd29199-00d3-46c3-a27a-38bcc31ecf17/download), [DOI](https://doi.org/10.1016/j.cor.2024.106848).

**The promising research question is more specific:** can learning reduce the time needed both to construct economical, physically executable fleets and to determine whether those fleets are supported by electricity prices, while preserving valid bounds under distribution shift and incomplete optimization?

That question connects the existing theory to the computations. It does not yet establish an Operations Research–level paper. A compelling paper would need a clearly distinguished algorithmic or theoretical contribution, serious comparisons against the closest EV methods, reliable numerical results, and evidence on independent operational regimes. More architectures or additional runs of the present pruning rule would not by themselves meet that standard.

Recommended order:

1. Resolve replay failures and preserve the best valid incumbent throughout solving.
2. Make learned restrictions recoverable and compare them with simple greedy/score widening.
3. Allocate hull computation between cheap candidate generation and valid unrestricted pricing bounds.
4. Improve labels through diverse, cost-aware solution pools before expanding the neural architecture.
5. Prototype a charging-aware route relaxation/pricing method if full-domain pricing remains dominant.

## 2. Evidence being used—and its limits

This review reads Claude's handoff and permitted result summaries. It does **not** independently reproduce the cluster results. The following are project-reported observations, not new experimental findings:

| Evidence | What it supports | What it does not establish |
|---|---|---|
| E3/E5: learned pruning improves bills at fixed solving budgets on larger synthetic and public timetables | A useful solver-guidance signal and an operational target beyond the easy 20–28-trip bank | Optimality, general public-network reliability, or novelty of learned pruning |
| E4: tariff-diverse labels improve the withheld-tariff experiment | Training labels need economically relevant variation | A universal causal explanation of v7, or generalization to new public networks |
| E7/E8: tariff-aware and more aggressive pruning gains reverse on public cases | Adaptation to timetable/price regime matters | A public-data coverage guarantee or a universally best keep fraction |
| E0: four development timetables have positive physical-minus-hull lower gaps | Tolerance-qualified evidence of non-support under the stated price-taking institution | Exact rational proofs, economically large effects, or support/non-support on the larger public cases |
| E9: learned seed plans improve ten hull enclosures | Promising warm-start value for this implementation | A fully matched cold-start saving unless seed acquisition is included; large-case gap signs remain unresolved |
| E10: per-trip rules often give good bills but four of six Eberbach runs fail replay | A strong reason to investigate extraction/charging reliability | Deployable reliability or justification for loosening replay rules |
| E11: interim seed-paired results favor learned pruning in 17–18 of 18 comparisons; 72/96 runs complete at handoff | Encouraging repeatability on the completed subset | Final seed robustness; the remaining 24 runs must be retained and analyzed before that claim |

Sources: [handoff](../../doc/GPT_HANDOFF_20261002.md), [E0](../../research-20261001/e0-support/E0_RESULTS.md), [E9](../../research-20261001/e9-seeded-hull/E9_RESULTS.md), [E10](../../research-20261001/e10-per-trip/E10_RESULTS.md).

Four evaluation issues deserve particular attention. First, all reported public outcomes are now exploratory: they have helped select models, fractions and policies. Second, solver seeds are repeated measurements of a timetable, not additional independent timetables. Third, a bill advantage against an unpruned solver that has found a poor fleet is real at that budget, but may reflect initialization or round allocation more than prediction accuracy. Fourth, E9's 600-second hull phase starts after its learned seed plans have been obtained. Report that conditional acceleration separately from a cold-start end-to-end comparison and an amortized repeated-query comparison.

The six historical Google Doc entries were appended **verbatim and in order**, as requested. Their text remains Claude's historical account; this review's qualifications do not silently rewrite those entries. See [append receipt](GOOGLE_DOC_APPEND_RECEIPT.json).

## 3. What the literature says about each component

### 3.1 MILP primal search: allow the optimizer to correct predictions

Neural Diving samples partial integer assignments and lets a solver complete them. Predict-and-search instead allows a bounded number of disagreements with selected predicted zeros/ones. For EGG, the latter is a direct extension of existing scores: hard pruning is the zero-disagreement special case. A larger neighborhood contains more feasible candidates but is also harder to solve; set inclusion is **not** a theorem about better answers at equal time. [Nair et al., author paper](https://arxiv.org/abs/2012.13349); [Han et al., ICLR 2023](https://arxiv.org/abs/2302.05636).

Apollo-MILP adds alternating prediction and correction with uncertainty-guided fixing. Its feasibility argument preserves agreement with an existing feasible reference; it does not prove retention of a global optimum. Borrow the correction mechanism before reproducing its entire model. A full-model Hamming region retains excluded variables and may sacrifice the model-size reduction that currently makes EGG fast. Compare that approach with staged reinsertion into the compact model. [Apollo-MILP, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ebcdb4d0372ebbdd0e6a7dce9662b6b4-Abstract-Conference.html).

Incumbent-based large-neighborhood search is also relevant. Destroy coherent route segments, including depot visits and charging opportunities, while retaining a valid fallback. Test random/coherent neighborhoods and an online bandit before paying for a learned destroy policy. Sonnerat et al. include large continuous models, so this literature is not restricted to pure binary problems; nevertheless, leaving EGG's charging variables free may retain most of its runtime. Balans provides a recent no-offline-training adaptive baseline, but its advantages are not universal and its longer search horizon may not fit a 60-second budget. [Sonnerat et al.](https://arxiv.org/abs/2107.10201); [Balans, IJCAI 2025](https://doi.org/10.24963/ijcai.2025/286).

Gasse et al.'s *Exact Combinatorial Optimization with Graph Convolutional Neural Networks* is **NeurIPS 2019**, by Gasse, Chételat, Ferroni, Charlin and Lodi; no proceedings DOI was verified. It learns branching decisions from strong branching in SCIP, rather than predicting an executable solution or permanently deleting arcs. Its four-family study and solver settings do not establish an EGG/Gurobi speedup. Treat it as the foundation for graph-based solver decisions, not the first implementation priority. [Primary full paper, §§4–5](https://proceedings.neurips.cc/paper/2019/file/d14c2267d848abeb81fd590f371d39bd-Paper.pdf).

### 3.2 Training: learn economical alternatives, not one arbitrary incumbent

Single-incumbent edge labels confuse “not selected by this solver run” with “undesirable.” Deduplicate several replay-valid **route topologies**, retain their optimized charging and true supply bills, and compare uniform pools with instance-normalized cost weights. Do not compare tangent objectives from different rounds as if they were the same physical cost.

Contrastive Predict-and-Search uses high-quality positives and poor/infeasible negatives. The final ICML 2024 paper—Huang, Ferber, Zharmagambetov, Tian and Dilkina, PMLR 235:19757–19771—was retrieved and inspected, including its transfer tests, ablations and Gurobi appendix. Its headline gap reductions are against SCIP-based baselines; the Gurobi evidence has dataset/settings qualifications, and the mixed-instance experiment has only 33 continuous variables. It supports testing economic negatives, not assuming an EGG-scale gain. The authors also distinguish ranking accuracy from downstream search quality. A replay failure caused by numerical extraction should be quarantined or repaired, not automatically labeled physically infeasible. [Final proceedings and paper](https://proceedings.mlr.press/v235/huang24f.html).

A first self-improvement cycle should mix unrestricted, greedy/LP and learned proposals. Relabeling only the learner's retained graph can reinforce its omissions. Freeze the architecture and decoder so label diversity is identifiable. RoME (NeurIPS 2025) motivates domain-balanced or worst-group training, but a mixture-of-experts network is a larger intervention than the evidence currently calls for; robust training does not itself provide calibrated public-case coverage. [RoME primary paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3071ed272658c4418309962ba7b94ec8-Abstract-Conference.html).

### 3.3 Adaptive pruning: three different meanings of “safe”

Keep these statements distinct:

- A reduced model has **a feasible schedule** if a validated reference schedule and its continuous completion are retained under unchanged constraints.
- A statistical keep set can retain **a reference label** with a specified marginal probability under its calibration assumptions.
- Deterministic screening retains **all solutions capable of beating a cutoff** only when the optimization bound used to discard a variable is valid for the full model.

Per-trip floors alone establish none of these. Conformal classification requires appropriate exchangeability; weighted covariate-shift results need additional assumptions, including the relevant distribution ratio and unchanged label conditional. Synthetic-to-public fleet transfer changes more than a covariate histogram. Calibrate at the timetable level if simultaneous reference-fleet retention is the target. Coverage of feasible-incumbent labels is not coverage of an unknown optimal fleet. [Romano, Sesia and Candès, NeurIPS 2020](https://proceedings.nips.cc/paper_files/paper/2020/hash/244edd7e85dc81602b7615cd705545f5-Abstract.html); [Tibshirani et al., NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html).

Reduced-cost reinsertion has a narrower deterministic role. Full omitted-column checks can recover the full **LP** relaxation, but a positive-reduced-cost omitted variable can still improve the integer optimum. A simple counterexample and the conditions for cutoff-based screening are in [the pruning note](notes/ADAPTIVE_PRUNING_AND_NUMERICS.md). Reinsertion must restore each movement's associated charging variables and constraints, not just a graph edge. Infeasibility needs a feasibility-restoration mechanism, not ordinary optimal-LP reduced costs.

### 3.4 Electric-fleet pricing: promising algorithms, different feasible sets

Parmentier, Martinelli and Vidal provide scalable route/recharge column generation with specialized resource extension, backward bounds, dominance and sparsification. Klein and Schiffer's charging-price-aware label functions are a closer match to tariff-responsive charging. Both are important algorithmic references; neither can be installed unchanged into EGG's shared-charger complete-fleet oracle. [Parmentier et al., Transportation Science 2023](https://doi.org/10.1287/trsc.2023.1199); [Klein and Schiffer, Transportation Science 2023](https://doi.org/10.1287/trsc.2022.0272).

At a fixed price vector, EGG's pricing objective is linear in energy even when the outer supply objective is convex. This makes specialized charge-aware route pricing worth testing. Shared charger capacity, complete trip coverage and fleet consistency must remain represented in the master or in valid relaxations. Prove how every original feasible fleet maps into a proposed route relaxation before using its objective as a global lower bound. A route LP may be a valuable relaxation without equaling the convex hull of complete coupled fleets.

The de Vos–van Lieshout–Dollevoet electric-bus work offers a relevant precedent: conservative discretization generates feasible duties, while an optimistic network supplies lower bounds. The inspected author version explicitly separates these roles. For EGG, the mapping must also preserve or lower the price-dependent objective; moving charging between price intervals cannot be justified by SOC feasibility alone. See [the domain comparison and precise version/access record](notes/BOUND_DOMAIN_COMPARISON.md); [Transportation Science 2024 publication](https://doi.org/10.1287/trsc.2022.0253).

Morabit, Desaulniers and Lodi's 2021 work selects already generated columns to reduce master work; their 2023 work prunes pricing graphs and returns to full-network pricing. These are different interventions. Master column selection has low priority if EGG spends its time in the single difficult fleet oracle. The heuristic-then-full pricing pattern is directly relevant. [Column selection, Transportation Science](https://doi.org/10.1287/trsc.2021.1045); [arc selection, INFORMS Journal on Optimization](https://doi.org/10.1287/ijoo.2022.0082).

### 3.5 Convex-hull pricing: cheap candidates and valid certificates

Andrianesis, Bertsimas, Caramanis and Hogan compute convex-hull prices through Dantzig–Wolfe decomposition. Their complete participant trajectories correspond, in EGG, to **complete coupled fleet plans**, not independent bus routes. Many easy generator subproblems do not imply that a single fleet subproblem will be easy. [IEEE Transactions on Power Systems 37(4):2578–2589, 2022](https://doi.org/10.1109/TPWRS.2021.3122000).

Learning dual warmstarts is also existing work: Sugishita, Grothey and McKinnon compare learned prices with cold starts, LP initialization and column prepopulation in unit commitment. Their quadratic dual regularization helps retain useful initial prices. This is a useful baseline and a novelty constraint, not evidence that simply learning EGG prices will solve the expensive oracle. [INFORMS Journal on Computing 36(4):1129–1146, 2024](https://doi.org/10.1287/ijoc.2022.0140); [full author manuscript](https://arxiv.org/html/2110.06872v2).

Stabilization can reduce price oscillation and unproductive columns, but it cannot correct invalid pricing bounds. EGG already has a quadratic supply term; additional stabilization should be measured against this existing geometry. Ben Amor, Desrosiers and Frangioni provide full-text evidence for explicit stabilization. Pessoa et al.'s automated stabilization and de Oliveira–Sagastizábal's on-demand oracle accuracy are relevant, but only their primary abstracts were inspected here. Their convergence results cannot be assigned to an arbitrary EGG timeout policy. [Explicit stabilization](https://doi.org/10.1016/j.dam.2008.06.021); [automated stabilization](https://doi.org/10.1287/ijoc.2017.0784); [on-demand accuracy](https://doi.org/10.1080/10556788.2013.871282).

The source gap was closed for Kiwiel–Lemaréchal's *An inexact bundle variant suited to column generation* through an institutional deposit of the Springer-layout text. It is direct prior art for approximate columns paired with global pricing certificates; its feasibility and convergence conclusions depend on Slater, error and algorithmic conditions. It does not establish the proposed timeout policy's convergence. The de Oliveira–Sagastizábal full-text gap remains after a bounded access search. [Kiwiel–Lemaréchal source and theorem-scope audit](notes/INEXACT_CG_SOURCE.md); [on-demand source-access record](notes/ON_DEMAND_ORACLE_SOURCE.md).

Recent searches include Tanji et al.'s 2025 dual-method benchmark and Chen et al.'s 2026 hybrid participant-classification method. The former uses exact unit oracles; the latter's retrieved evidence is partial primary text. Neither presently warrants replacing EGG's master while leaving its oracle unchanged. [Tanji et al. preprint](https://arxiv.org/abs/2504.01474); [Chen et al., EJOR 329(1):308–320](https://doi.org/10.1016/j.ejor.2025.09.036).

The core accounting is simple. Define \(V(p)=\inf_{x\in X}\{c(x)+p^Te(x)\}\). An unrestricted bound \(\ell(p)\le V(p)\) gives
\[
\ell(p)-F^*(p)\le CH.
\]
A replayed fleet generated on a reduced graph is a candidate column and pricing **upper** bound. Its restricted-model lower bound is not interchangeable with \(\ell\). These bounds require finite values and valid full-model/numerical enclosures. If the conjugate is computed rather than analytic, subtract a verified **upper** enclosure of \(F^*\), not an incumbent from its maximization. For a fixed feasible fleet, regret satisfies
\[
\max\{0,c(x)+p^Te(x)-v(p)\}\le r(x;p)
\le c(x)+p^Te(x)-\ell(p),
\]
where \(v(p)\) is any feasible response objective. Finding a profitable deviation and proving that no important deviation exists require different oracle performance. See [derivations and a candidate cached-price bound](notes/ECONOMIC_CERTIFICATES_AND_NOVELTY.md). These standard inequalities are implementation requirements, not our novelty claim.

The same pricing interval yields a usable inexact-oracle error bound: \(\varepsilon=v-\ell\). With an exact supply subgradient, it gives an \(\varepsilon\)-subgradient of \(F^*-V\); a constraint formulation also admits a strictly feasible point from one valid pricing lower bound. This is an explicit mathematical interface, not a completed implementation. Target attainment at a queried price, requested oracle accuracy, and the final global hull gap must be recorded separately. A timeout certifies none of them by itself. [Interface, proof and supply-gradient counterexample](notes/ORACLE_ERROR_INTERFACE.md).

A further mathematical check gives a stronger way to reuse previous certificates. If \(\ell_k\le V(p_k)\) and a proven load set \(\mathcal E\) contains all fleet loads, combine the inequalities \(c+p_k^Te\ge\ell_k\) in one outer cost/load model. Its price-query lower bound dominates using each cached certificate separately; a hand-derived example improves the bound from 0 to 0.5 with no new oracle value. With a convex load set this also gives a valid outer relaxation for the hull cost. These are mathematical examples, not measured fleet improvements. Concavity-based combination has direct prior art in Geoffrion and Nauss (1977), so the possible research contribution lies in inexpensive, stronger fleet-specific load constraints and useful computational savings. See [joint-bound proofs, limitations and primary references](notes/JOINT_PRICE_BOUND_REVIEW.md).

The next structure check supplies conditional stock, interval-energy and charging-opportunity constraints. Mandatory trips occupy buses that cannot charge simultaneously; terminal replenishment forces purchased energy to replace traction and losses. Retaining fleet count as an outer-model variable preserves its coupling to charging opportunity and intrinsic cost. A hand example raises a joint bound from 0.5 to 1 by adding mandatory energy, but the actual computational value is untested. These constraints may already be implied by a full continuous relaxation; integer-oracle certificate cuts are a separate potential source of strength. [Derivation and assumptions](notes/FLEET_LOAD_OUTER_RELAXATION.md).

Aggregate-load approximation is itself established: Barot–Taylor and Al Taha–Vincent–Bitar distinguish outer from inner battery models, while Mukhi–Loho–Abate give exact fixed-device aggregation through generalized polymatroids. Their prescribed device windows do not become exact descriptions of endogenous fleet routes and shared charging access. Even tight power/prefix bounds can admit a nondisaggregable load, as the companion counterexample shows. This motivates a cheap outer-model baseline for future certificate experiments, not an executable charging policy or a first-aggregation claim. [Five inspected primary sources and containment directions](notes/AGGREGATE_LOAD_PRIOR_ART.md).

### 3.6 Numerical reliability comes before faster reported schedules

Gurobi's tolerances are absolute. Their physical meaning depends on units and coefficient scaling; tightening them is a diagnostic, not a proof. Integer rounding can destroy continuous feasibility, especially through large linking coefficients. Preserve raw values and original-unit residuals, round only qualified integer decisions, fix the resulting topology, and solve charging feasibility again under the original limits. Then replay and recompute the true bill. Keep earlier accepted incumbents when a later round or repair fails. [Official numerical guide](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/tolerances_scaling.html); [official integrality guidance](https://support.gurobi.com/hc/en-us/articles/360012237872-Why-does-Gurobi-sometimes-return-non-integral-values-for-integer-variables).

Exact rational verification is useful for selected failures and small price-support claims. VIPR and SCIP's exact mode provide relevant tools, with restrictions involving model encoding, presolve and proof completion. An exact proof for a linear tangent model does not automatically certify the nonlinear supply bill or the event replay. Diagnose fixed-route charging first; do not begin by migrating the whole large MILP to a new exact solver. [Cheung, Gleixner and Steffy, IPCO 2017](https://doi.org/10.1007/978-3-319-59250-3_13); [SCIP exact mode](https://scipopt.org/doc-10.0.0/html/EXACT.php).

## 4. Ranked top five experiments

**All estimates and thresholds below are proposed by this review, not results or budgets reported in the papers. No experiment has been launched.** CPU-hours assume one solver thread and include failed attempts; actual allocations and peak memory must be recorded. These are staged pilots, not a request to launch every grid. All use permitted TRAIN/development-generation and already explored public stress cases; sealed DEV/TEST/A6/B3/GIRO remain closed.

| Rank | Experiment and component | Sources | Engineering effort | Prospective compute | Go/no-go target |
|---|---|---|---:|---:|---|
| **1** | **Reliable topology extraction and charging completion.** Diagnose tolerances/scaling; compare fixed-route charging repair with the present extractor, under unchanged physical rules. | Gurobi numerical guidance; VIPR | **24–40 h**, optional exact-LP export +8–16 h | **35–50 CPUh** for four arms × three seeds on the existing 30 case/budget cells, including diagnostics | No accepted plan may fail the original replay; recover ≥90% of the frozen historical failure cohort; median overhead ≤20%. Stop and reformulate if success requires relaxed reserve/terminal/charger constraints. |
| **2** | **Recoverable learned pruning.** Compare unpruned solving, the current rule, simple widening, full-model predict-and-search and compact reinsertion; preserve a valid fallback and depot/charge alternatives. | Gerbaux; Han; Apollo; Morabit arc selection | **24–48 h** | **40–50 CPUh** for these five arms × three seeds; no new model fitting required | ≥10% median time-to-quality reduction or ≥1% paired bill improvement over simple widening, with no increased failure rate, a substantive public benefit and no public regression >2%. Stop if gains disappear after model-build/repair overhead. |
| **3** | **Separate candidate generation from global pricing certification.** Compare seeded full pricing, fixed learned/full allocation, adaptive learned/full allocation, and adaptive allocation with additional stabilization; add an unseeded full-pricing control with the same total allowance. | Andrianesis; Morabit; Sugishita; Ben Amor; on-demand-oracle literature | **20–40 h** | **45–55 CPUh** for ten cases × three seeds: four seeded policies at 600 s, common seed acquisition up to 900 s, and one unseeded control at 1,500 s; includes overhead | ≥25% reduction in median final hull width, or ≥20% reduction in time to a frozen certificate tolerance, over the strongest matched-budget baseline. All bounds must remain globally valid. Stop if a new price policy saves iterations but not end-to-end time. |
| **4** | **Tariff-diverse, cost-aware topology pools.** Single labels vs uniform pools vs cost-weighted pools; same architecture and search policy; one self-improvement cycle with unrestricted exploration. | Nair; Han; ConPaS; E4 hypothesis | **24–40 h** for first cycle | **55–70 CPUh**, including 32 CPUh label collection, 16.2 CPUh online screen and a 6.8–21.8 CPUh training/data/replay allowance; any GPU budget separate | ≥10% improvement in median primal integral over single labels, paired group benefit and stable public tails/replay. Require uniform-pool ablation. AP-only gains or self-confirming omissions are no-go. |
| **5** | **Charging-aware route pricing as a full-fleet relaxation.** First prove model mapping; then test resource-extension/backward bounds and shared-capacity dualization as a source of stronger unrestricted pricing bounds. | Parmentier; Klein–Schiffer; Gerbaux | **60–120 h** for a scoped prototype | **20–40 CPUh** initial pricing-only comparison, not a full branch-and-price campaign | On exactly solved small cases, reduce median normalized lower-bound error ≥20%; on larger cases, reduce time to the same prespecified valid bound ≥25%, including master overhead. Stop if the mapping relaxes the wrong model, labels explode, or its bound is too weak to improve E9. |

The rank-1/2 estimates use E10's approximately 2.3 solver-hours per arm/seed over its 30 budget cells; repeated budgets are not independent instances. Rank 3's seeded grid costs 20 solver CPUh; shared seed acquisition adds up to 7.5 and the unseeded total-budget control adds 12.5, giving 40 before overhead. Rank 4's 32-hour collection is 32 TRAIN timetables × 4 tariffs × 3 proposal policies × 300 seconds. These calculations make the proposed resource envelopes reviewable; they are not guaranteed runtime predictions. The main table's rank-3 budget supersedes the narrower oracle-stage estimate in the companion note.

For rank 1, freeze the identities and raw artifacts of all four recorded E10 Eberbach failures before intervention; a ≥90% recovery target therefore requires all four. Do not remove a failed topology from the denominator after discovering infeasibility. Classify its cause separately. The four arms are existing extraction, improved scaling with the same tolerances, fixed-route charging repair, and scaling plus repair. All receive the same incumbent-retention policy. Optional exact-LP diagnosis is outside this four-arm comparison.

Rank 3 uses identical acquired seeds across seeded policies, charges their measured acquisition to each end-to-end algorithm, and records actual shared experimental spend separately. Freeze an end-to-end wall-clock cap that also charges scoring, construction, repair and replay; the solver allowances above are resource estimates, not permission to exceed that cap. The unseeded control can use the entire common cap for its own search. Report both shared-seed oracle comparisons and independent cold-start comparisons. Cached-bound reuse is a subsequent ablation only after its definitions and validity are established. Rank 4's online screen is 18 permitted stress cells × 3 seeds × 3 label policies × (60 + 300) seconds = 16.2 CPUh; it is not 18 independent timetables. For rank 5, normalized error means \((V^*-\ell)/\max\{1,|V^*|\}\) where the full pricing optimum \(V^*\) is certified; large cases use a common frozen valid-bound target and retain unreached targets as censored observations.

These thresholds are exploratory advancement screens. In particular, improvement on already explored public cases does not count as independent evaluation or establish a population-level no-regression guarantee. Any promoted method still needs a separately frozen evaluation on additional authorized groups.

For each pilot, first run a tiny implementation check after compute is separately resumed, then freeze the full protocol. Use original physical acceptance rules throughout. A fallback returned after failed search counts as a valid final plan, but its search and repair failures remain visible. A pipeline without a fallback returns failure, not a missing row silently omitted from averages.

Concrete prospective protocols now accompany ranks 1, 3 and 4: [numerical reliability](protocols/NUMERICAL_RELIABILITY_PROTOCOL.md), [matched oracle allocation](protocols/MATCHED_ORACLE_PROTOCOL.md), and [learning signals](protocols/LEARNING_SIGNAL_PROTOCOL.md). They specify comparison arms, artifact fields, failure classification, unchanged physical acceptance, timing and promotion rules. The oracle-stage allowances include cumulative one-thread CPU across every solver call, including completion, master and optimization-based verification; native per-call time limits alone do not enforce the budget. The label comparison shares collection across all arms and distinguishes benefits of multiple topologies from benefits of cost weighting. Missing case identities, allocation parameters and numerical enclosure conventions must be frozen before any launch. These documents are designs, not executed experiments.

## 5. A credible Operations Research contribution

A useful working title is **“Learning-assisted fleet scheduling with certified price-support bounds.”** It states an objective, not a result already achieved.

| Proposed contribution | Already known / closest threat | What EGG must add |
|---|---|---|
| Learned network reduction for electric buses | Gerbaux2025 already covers this, including incoming/outgoing per-trip selection and greedy hybrids | A distinctive economic objective/certification problem; direct comparison with the closest method, not only generic Gurobi |
| Recoverable prediction-guided search | Han, Apollo and learned LNS already allow correction/neighborhood search | A fleet-specific policy or analysis exploiting coupled charging and price response, plus reliable transfer evidence |
| Learned warmstarts for convex-hull computation | Sugishita learns dual warmstarts; heuristic/full pricing and stabilization are established | A materially better oracle or allocation rule for one difficult coupled fleet, supported by valid bounds and total-cost comparisons |
| Distinguishing planning gap from own-price regret | Existing EGG theory already provides the mechanism in exact constructions | A generalizable operational finding about when this distinction matters, under defensible institutions and quantitatively meaningful scales |

The most promising unifying insight is that **fast operational optimization and fast economic certification require different information**. Learning can find good primal schedules while being unhelpful—or dangerous if misused—for lower bounds. A method that decides when to exploit learned restrictions, when to restore options, and when to pay for global pricing could connect that distinction to a practical algorithm. Its ingredients are known. The contribution must be the specific structure, analysis and evidence, not a claim that their combination has never appeared.

The existing tiny exact examples can motivate and test the economic mechanism. They cannot compensate for weak computational baselines. Conversely, a speedup on a few public schedules does not establish market-design significance. Report absolute monetary/incentive scales alongside percentages; E0's small positive gaps should not be promoted into a large operational concern without further evidence.

### Evidence required before claiming the paper is ready

- **A statement that survives the closest-paper comparison.** Explicitly identify what Gerbaux, Morabit, Han/Apollo and Sugishita do not establish. Search failure alone is not proof of originality.
- **At least one substantive theoretical result or general algorithmic insight beyond standard bound bookkeeping.** Cached-price inequalities and weak-duality separation are useful, but currently elementary.
- **A matched, failure-aware computational comparison.** Same solver, same round allocation, same available seed information, all overhead charged. Include greedy/LP/random pruning, retained plans/columns and a serious charging-aware alternative where the models are comparable.
- **Independent operational coverage.** Multiple genuinely different timetables/regimes, tariff and charging stress, more than a model-selected public pair, solver-seed dispersion, and a final evaluation protocol frozen before opening any reserved data.
- **Economic outcomes, not only solver metrics.** Physical cost, fleet count, certified hull width, own-price-regret intervals, time to a specified economic tolerance, and the incidence and magnitude of positive support gaps.
- **Numerical credibility.** Every accepted plan passes unchanged replay; positive tiny gaps exceed the complete stated numerical uncertainty allowance. Native tolerance-qualified evidence and exact certificates remain distinctly labeled.

These conditions are a research assessment, not a promise of journal acceptance. If only primal speedups survive, a focused learning-assisted EV scheduling paper may be more coherent. If robust economic certificates and structural results survive but learning adds little, a theory/computation paper on price support may be stronger. We should allow either outcome.

## 6. Common evaluation protocol for the next stage

1. **Freeze the units and regimes.** Timetable groups are independent units; tariff variants, budget cells and solver seeds are nested. Keep the current public set labeled exploratory. Do not select thresholds on its outcomes and then call it untouched transfer evaluation.
2. **Measure the actual decision process.** Log model loading/scoring, graph/model construction, presolve/root relaxation, each tangent round, repair, replay and full pricing. Reduced binaries do not imply a cheap continuous charging model.
3. **Use both operational and certification curves.** Plot accepted incumbent bill versus elapsed time and valid hull-width/regret bounds versus elapsed time. Where a target is unreached, retain censoring; do not impute a successful runtime. Report failures separately from finite gaps.
4. **Define references in advance.** An observed best-known replay-valid bill is a comparison reference, not an optimum. If any arm improves it, update the reference consistently for all arms. For primal integrals before first feasibility, specify a common penalty/fallback convention before results are inspected.
5. **Separate three cost scenarios.** Cold-start cost includes training/label acquisition amortization policy and seed generation as appropriate; repeated-query online cost may reuse past artifacts but states that information; oracle-only comparisons explicitly condition on identical supplied seeds. Do not collapse them into a single speedup number.
6. **Predeclare promotion.** Pilot thresholds in Section4 screen candidates; they are not statistical guarantees. Use group-level paired summaries and uncertainty intervals where the number of independent groups permits them. Three seeds do not solve the small-sample problem.

## 7. Do not pursue first

- **Another GNN/attention/MoE merely because it is newer.** Current limitations include labels, numerical reliability and pricing lower bounds. A larger architecture changes the wrong component if those dominate.
- **Conformal “safe optimal pruning” as a headline now.** Current labels are feasible incumbents, public shift is not exchangeable, and complete-fleet coverage is a different target from edge accuracy.
- **A full Neural Diving/learned-LNS reproduction before simple recovery and classical LNS.** Expert generation and solver integration can cost more than the pilot question warrants.
- **Learned branching as the first Gurobi intervention.** Gasse's result addresses a different solver control and representation; use it as background until profiling shows branching, not charging/presolve, dominates.
- **ML column selection when the master is cheap.** It reduces a component that may not be the bottleneck.
- **Replace the hull master with ADMM, Benders or a newer dual method without strengthening its oracle.** Generator-specific separability and explicit hull formulations are not properties of an arbitrary coupled fleet.
- **Full exact-MIP migration before diagnosing fixed-route charging.** Exact proof scope is valuable, but expensive and narrower than complete physical/model correctness.
- **Call all-public success or a smaller restricted MIP gap a certificate.** Success on repeated exploratory cases is empirical evidence; restricted bounds have the wrong domain for global claims.

## 8. Source verification and remaining review work

The brief's starting points were checked rather than accepted from memory: Neural Diving is an author preprint without a peer-reviewed venue verified here; Han is ICLR 2023; ConPaS is ICML 2024 and its final full text was inspected after resolving an initial retrieval failure; Gasse is NeurIPS 2019; Morabit's column and arc papers are distinct; Andrianesis is Dantzig–Wolfe, while Knueven et al.'s related 2022 paper uses Benders; Parmentier et al. is Transportation Science 2023.

Detailed titles, authors, venues, DOIs where verified, methods, evidence limitations and additional experiments are recorded in:

- [ML primal heuristics and training signals](notes/ML_PRIMAL_AND_TRAINING.md)
- [Electric-fleet pricing and hull methods](notes/EV_PRICING_AND_HULL.md)
- [Adaptive pruning and numerical reliability](notes/ADAPTIVE_PRUNING_AND_NUMERICS.md)
- [Economic certificates and candidate bound reuse](notes/ECONOMIC_CERTIFICATES_AND_NOVELTY.md)
- [Independent mathematical challenge](notes/CERTIFICATE_REVIEW.md)
- [Adversarial novelty and OR positioning review](notes/OR_POSITIONING_REVIEW.md)
- [Joint price-bound reuse and direct parametric-optimization prior art](notes/JOINT_PRICE_BOUND_REVIEW.md)
- [Conditional fleet stock, energy and charging-opportunity constraints](notes/FLEET_LOAD_OUTER_RELAXATION.md)
- [Aggregate-load prior art and disaggregation counterexample](notes/AGGREGATE_LOAD_PRIOR_ART.md)
- [Comparison of pricing, route and complete-fleet relaxation domains](notes/BOUND_DOMAIN_COMPARISON.md)
- [Inexact column-generation primary-source audit](notes/INEXACT_CG_SOURCE.md)
- [On-demand oracle access limits](notes/ON_DEMAND_ORACLE_SOURCE.md)
- [Fleet-oracle error and bundle-method interface](notes/ORACLE_ERROR_INTERFACE.md)

Full-text review means the relevant method/theorem/experiment sections were inspected; it does not mean results were reproduced. An abstract-only source is usable for identifying a direction, not for borrowing a theorem's hypotheses or a detailed implementation. No DOI was guessed. Newer preprints are distinguished from published papers. This is a targeted primary-literature review, not a claim of exhaustive coverage or a universal ranking of algorithms across all MILPs.

The independent mathematical challenge found the displayed bound directions correct and identified implementation conditions now made explicit: finite conjugates, globally valid oracle bounds, compatible cache definitions and nonnegative consistent certificate widths. The adversarial novelty review confirmed the direct top-m overlap with Gerbaux's Algorithm 2. The subsequent structure package derived conditional fleet energy/opportunity constraints and located direct aggregation precedents; it did not establish their applicability or performance on EGG. Two prospective protocols are now written and reviewed. The inexact-oracle source check establishes a concrete error/feasibility interface and another strong novelty precedent, while preserving the remaining source-access limit. Further work before the deadline should address only a material unresolved issue or consolidate the final assessment; none requires cluster access.
