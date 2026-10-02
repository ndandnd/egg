# Adaptive pruning and numerical reliability — research note, 2 October 2026

Scope: handoff Section 5 questions 3 and 6. Research only; no solves, jobs, sealed-data reads, branch changes, commits, or pushes. Local evidence read: `doc/GPT_HANDOFF_20261002.md` and E7, E8, E10 results. Estimates below are prospective engineering estimates, not measured runtimes. Sources were checked on 2 October 2026; ten source groups are recorded below, distinguishing full text, official documentation, and abstract-only evidence.

## Decision

Prioritize **route-fixed charging repair and numerical diagnosis**, then **recoverable adaptive pruning with a retained replay-valid reference**. Treat conformal keep sets as an exploratory statistical control. Do not describe them as safe optimization pruning under synthetic-to-public shift. Reduced costs can support rigorous screening only with a valid full-model dual bound and incumbent cutoff; ordinary restricted-LP reinsertion is a useful heuristic, not an integer-optimum certificate.

E10 reports m5/m8 beating cold in 27/30 and 28/30 cells, but four of six per-trip Eberbach runs fail replay, including every 1800-second run. Its corresponding ten global-fraction Eberbach runs have no replay rejection. E8's best fraction changes from about 5% on 80-trip synthetic cases to 30% on public cases; public 5% pruning loses roughly 17–19%. E7 improves some large synthetic cases but loses on all six public cells. These are descriptive, mostly single-run comparisons. They motivate recovery and reliability work; they do not identify a causal numerical mechanism or establish transfer guarantees.

## Verified sources and what they actually establish

### P1 — Predict-and-search

Qingyu Han, Linxin Yang, Qian Chen, Xiang Zhou, Dong Zhang, Akang Wang, Ruoyu Sun, Xiaodong Luo. **“A GNN-Guided Predict-and-Search Framework for Mixed-Integer Linear Programming.” ICLR 2023.** Full text read: Section 3.2, Proposition 1, experimental discussion. [Author full text](https://arxiv.org/html/2302.05636v4); [conference PDF](https://openreview.net/pdf?id=pHMpgT5xWaE). Verified repository DOI: [10.48550/arXiv.2302.05636](https://doi.org/10.48550/arXiv.2302.05636); conference DOI not verified.

Learns binary marginals, constructs a partial assignment, then solves the original constraints inside a Hamming/L1 neighborhood. The paper reports smaller primal gaps than SCIP and Gurobi on its benchmarks. Proposition 1 is set inclusion: the neighborhood's optimum cannot be worse than hard fixing the same partial assignment **when both subproblems are optimized**. It neither preserves the full optimum nor proves better results at equal time limits. Map to EGG: permit a bounded number of excluded movements rather than permanent zero fixing. Benchmark evidence does not establish performance on EGG's large continuous charging blocks or synthetic-to-public shift.

### P2 — Uncertainty-guided prediction/correction

Haoyang Liu, Jie Wang, Zijie Geng, Xijun Li, Yuxuan Zong, Fangzhou Zhu, Jianye Hao, Feng Wu. **“Apollo-MILP: An Alternating Prediction-Correction Neural Solving Framework for Mixed-Integer Linear Programming.” ICLR 2025.** [Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ebcdb4d0372ebbdd0e6a7dce9662b6b4-Abstract-Conference.html); [conference full text](https://proceedings.iclr.cc/paper_files/paper/2025/file/ebcdb4d0372ebbdd0e6a7dce9662b6b4-Paper-Conference.pdf); [readable author full text](https://arxiv.org/html/2503.01129). DOI: [10.48550/arXiv.2503.01129](https://doi.org/10.48550/arXiv.2503.01129), repository DOI; conference DOI not verified.

Full-text Sections 4.2–4.3 and Appendix C show iterative prediction, trust-region correction, and fixing prediction/reference-consistent variables as a practical proxy for UEBO uncertainty. The precision theorem assumes explicit consistency inequalities. Appendix C.4's feasibility argument starts with an existing feasible correction solution and fixes values agreeing with it, so that solution remains feasible. An added strict objective-improvement cutoff can exclude that reference. None of these arguments proves every fixing preserves a global optimum. Reported gap gains are benchmark evidence; some competing methods were reimplemented. Map: preserve accepted reference edges, unlock disagreements, and widen if correction fails. Novelty cannot be “first uncertainty-guided predict/correct/fix.”

### P3 — Adaptive conformal classification sets

Yaniv Romano, Matteo Sesia, Emmanuel J. Candès. **“Classification with Valid and Adaptive Coverage.” NeurIPS 2020, Advances in Neural Information Processing Systems 33.** [Official record](https://proceedings.nips.cc/paper_files/paper/2020/hash/244edd7e85dc81602b7615cd705545f5-Abstract.html); [full paper](https://papers.nips.cc/paper/2020/file/244edd7e85dc81602b7615cd705545f5-Paper.pdf), read construction and coverage statements. Repository DOI: [10.48550/arXiv.2006.02544](https://doi.org/10.48550/arXiv.2006.02544); proceedings DOI not verified.

Adaptive prediction sets vary with estimated class difficulty while providing marginal coverage under the required sampling/symmetry assumptions. Experiments concern classification, not MILP pruning. Treat a trip's selected outgoing movement as a categorical label only after defining a consistent labeling policy and candidate universe. EGG edge scores are independent binary scores, not automatically a categorical softmax. Marginal trip/edge coverage is not simultaneous fleet coverage, feasible routing, or retention of an optimum. This is transferable statistical machinery, not verified evidence of safe electric-fleet pruning.

### P4 — What shift correction requires

Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas. **“Conformal Prediction Under Covariate Shift.” NeurIPS 2019, Advances in Neural Information Processing Systems 32.** [Official record](https://proceedings.neurips.cc/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html); [full paper](https://proceedings.neurips.cc/paper/2019/file/8fb21ee7a2207526da55a679f0332de2-Paper.pdf), read weighting assumptions and theorem. DOI: [10.48550/arXiv.1904.06019](https://doi.org/10.48550/arXiv.1904.06019), repository DOI; proceedings DOI not verified.

Weighted conformal can correct changed covariate distributions under covariate shift, with the requisite likelihood ratio. This does not address arbitrary changes in the conditional label distribution. For EGG, timetable structure, feasible movement options, charging windows, and the reference-solver policy may change together. There is no evidence here of stable label conditionals or adequate support overlap. Estimated importance weights are not the same as known weights. Use target-like calibration groups when available; otherwise state that synthetic calibration gives no certified public coverage.

### P5 — Direct conformal/MIO prior art, but a different application

Stefan Clarke, Bartolomeo Stellato. **“Conformal Prediction for Early Stopping in Mixed Integer Optimization.” arXiv:2602.01476v2, 29 May 2026.** [Record](https://arxiv.org/abs/2602.01476); [full text](https://arxiv.org/html/2602.01476v2), read Section 4.1/Theorem 4.1. DOI: [10.48550/arXiv.2602.01476](https://doi.org/10.48550/arXiv.2602.01476). Preprint; peer-reviewed venue not verified.

Calibrates a solver stopping threshold at the **instance/trajectory** level, including repeated-callback selection. The theorem samples calibration and new instances independently from the same distribution. Authors report more than 60% time savings on five distributional MIPLIB families with probabilistic near-optimality. This is not an edge-pruning or exact-replay guarantee. It establishes relevant recent prior art and the need to calibrate the actual adaptive policy, rather than repeatedly applying pointwise confidence thresholds. Early stopping is lower priority for EGG, where short budgets and weak incumbents are often already the issue.

### P6 — Safe reduced-cost strengthening

Lukas Schürmann, Petra Mutzel. **“A Reduced Cost-based Model Strengthening Method.” SIAM Conference on Applied and Computational Discrete Algorithms (ACDA23), 2023, pp. 75–86.** DOI: [10.1137/1.9781611977714.7](https://doi.org/10.1137/1.9781611977714.7). [Publisher record](https://epubs.siam.org/doi/10.1137/1.9781611977714.7). **Abstract-only for this paper**: PDF link redirects to access page. The abstract verifies alternate dual solutions for strengthening domains, including fractional/implicitly bounded variables, and heterogeneous-VRP experiments; numerical gains and implementation details not verified.

For a simple binary-at-zero case, the underlying bound logic is stated below as an algebraic derivation, not as a claim extracted from this inaccessible full text. Start with standard full-relaxation reduced-cost screening; do not implement the advanced method based on the abstract alone. Its optimization validity depends on the relaxation and cutoff, unlike ML thresholding.

### P7 — Independently checked rational MIP proofs

Kevin K. H. Cheung, Ambros Gleixner, Daniel E. Steffy. **“Verifying Integer Programming Results.” IPCO 2017, pp. 148–160.** DOI: [10.1007/978-3-319-59250-3_13](https://doi.org/10.1007/978-3-319-59250-3_13), verified in [author arXiv record](https://arxiv.org/abs/1611.08832). [Full author text](https://arxiv.org/html/1611.08832v2), read certificate construction and Section 5.

VIPR certificates separate solver search from checking simple inference steps. Experiments on 107 benchmark instances demonstrate practical checking, with substantial solving/storage costs on some cases. Map to EGG: small rational charging-repair LPs and selected linear outer-approximation diagnostics before attempting full MIP proofs. An exact certificate proves the encoded rational model's result; it does not validate input semantics, event decoding, or the true quadratic objective.

### P8 — Gurobi official numerical guidance

**Gurobi Optimizer Reference Manual, “Tolerances and User-Scaling,” “Solver Parameters to Manage Numerical Issues,” and “Does my Model have Numerical Issues?”** Official documentation; no DOI. [Tolerances/scaling](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/tolerances_scaling.html), [parameters](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/numeric_parameters.html), [diagnostics](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/modelissues.html). Full relevant documentation read.

Primal/dual feasibility tolerances default to 1e-6 and integrality to 1e-5; they are absolute, so the physical significance changes with units. The guide prefers reformulation/scaling to parameter-only fixes; it suggests constraint coefficients within roughly six orders of magnitude, ideally [1e-3,1e6]. Tightening FeasibilityTol to 1e-9 is a diagnostic, not an exactness certificate. NumericFocus 1–3 adds numerical care with performance cost. Compare presolved ranges and test Aggregate=0 or simplex only when diagnostics indicate trouble. Retain original-unit residuals; solver-scaled residuals alone are insufficient for charging validation.

### P9 — Gurobi integer rounding and trickle flow

**Gurobi Help Center, “Why does Gurobi sometimes return non-integral values for integer variables?”** Official article, updated 9 February 2026; no DOI. [Full article](https://support.gurobi.com/hc/en-us/articles/360012237872-Why-does-Gurobi-sometimes-return-non-integral-values-for-integer-variables).

Rounding an accepted integer-tolerance solution can destroy feasibility. IntegralityFocus=1 checks rounded-solution feasibility and branches further for the big-M trickle-flow case. It is a mitigation, not a universal exact-feasibility guarantee. EGG should test whether tiny movement/bus binaries enable appreciable charging through linking constraints; that mechanism has not yet been diagnosed in E10. Re-solving continuous charging after rounding route decisions is the proposed application, not a result demonstrated in the article.

### P10 — Current exact-solving implementation

**SCIP 10 official documentation, “How to use the numerically exact solving mode,” and FAQ question on exact MIPs/certification.** No DOI; official implementation documentation. [Exact mode](https://scipopt.org/doc-10.0.0/html/EXACT.php), [FAQ](https://www.scipopt.org/doc/html/FAQ.php). Relevant full indexed documentation read; direct exact-mode fetch also encountered HTTP 429.

SCIP 10 supports rational/safe arithmetic and optional VIPR proof logging, enabled before reading the instance. Required builds include rational/extended-precision support and an exact LP solver. The FAQ states that proof logs certify branch-and-bound **after presolve**; disable presolve or separately account for it when certifying the original instance. Cutting-plane logs need completion with viprcomp before checking. This is now an available diagnostic route, but not evidence that exact solving will be affordable on EGG's full charging MILPs.

## Guarantees that must stay separate

| Claim | Sufficient evidence/assumptions | What does not suffice |
|---|---|---|
| A new label lies in a conformal set with marginal probability at least 1-alpha | Matching exchangeable calibration/new units, fixed trained model, correct construction; shift correction needs its additional assumptions | AP, calibrated soft probabilities, or successful public examples |
| All movements in one labeled fleet remain available with probability at least 1-alpha | An instance-level score covering the whole reference fleet | 95% edge-wise/trip-wise marginal coverage |
| Reduced model is feasible | Preserve a fully feasible reference and its continuous completion, with unchanged physical constraints | Top-m incoming/outgoing floors; they do not resolve flow, fleet, SOC, or charger coupling |
| Global optimum is retained | Deterministic safe screening or retention of a proved optimum; statistical analog needs labels that actually are optimal | Coverage of single feasible-incumbent labels; prediction/correction agreement |
| Plan is physically accepted | Independent replay after rounding/repair, original units and semantics | Gurobi status/gap/tolerances or a small decoder residual |
| Hull/pricing lower bound is global | Full-domain pricing lower bound or independently valid safe omissions | Bound from an ML-pruned pricing minimization MIP |

### A usable conformal prototype (our proposed adaptation)

Use **physical timetable groups**, not movements, seeds, or seven tariffs of one timetable, as independent calibration units. Define a deterministic reference-policy label: one replay-valid incumbent fleet. For timetable i, take `s_i = max over its used movements e of (1 - p_e)`; if simultaneous tariff coverage is required, include all specified tariff labels inside that maximum. For n calibration units use the order statistic at `ceil((n+1)*(1-alpha))`, with +infinity when the rank exceeds n. Keep movements with `1-p_e <= q`, plus required depot/connectivity floors and any retained reference edges.

The rank argument can give simultaneous inclusion of **the new reference label's used movements** under matching exchangeability. It says nothing about an unseen better fleet. If labels are feasible incumbents, call the target “reference-fleet retention,” not “optimal-edge recall.” Do not silently discard replay-rejected reference-generation cases and then claim coverage of all instances; either restrict and state the eligible population or count policy failures. Groupwise conditioning and public transfer require separate evidence. High-dimensional maxima may produce very wide keep sets; measure retained size and CPU cost. Do not tune alpha/q using the same public cells used to report transfer performance. This construction is an adaptation of P3/P4 principles, not a claim of prior published EGG results.

### Reduced-cost recovery: useful, but easy to overclaim

Algebraic illustration: minimize `x1 + x2 + 1.6*y`, subject to `2*x1 + 2*x2 + 3*y >= 3`, all variables binary. Retain only x1,x2 initially. Its LP optimum is 1.5 with row dual 0.5, so omitted y has **positive** reduced cost 1.6-3*0.5=0.1. No negative-cost column is needed to improve that LP. Nevertheless the retained integer optimum is 2 and the full integer optimum is 1.6, using y. Therefore “all omitted reduced costs nonnegative” can certify the full LP optimum, but not retention of the integer optimum.

For a full-model dual-feasible relaxation certificate with bound L and a binary at lower bound zero with nonnegative reduced cost r_e, solutions using that binary have relaxation cost at least L+r_e. If `L+r_e > U` for a validated incumbent objective U, the binary cannot occur in a solution of cost <=U. Use strict inequalities or preserve the incumbent explicitly; directed rounding/rational checks and a conservative numerical margin are necessary for certification. Upper-bound variables require the corresponding bound-aware sign/dual contribution. A reduced-cost score from a restricted model must first be made dual feasible for **every omitted full-model column**.

EGG complication: a movement can activate charging variables and constraints. Restore/check the whole associated model block, not only the movement objective coefficient or graph edge. Restricted infeasibility calls for phase-I/Farkas or direct feasibility repair, not ordinary optimal-LP reduced costs. Negative reduced-cost reinsertion is a natural discovery heuristic; it needs full-model LP structure and is not a substitute for branch-and-price or full-model branch-and-bound. Recompute duals after tangent/cost changes. For convex-hull certification, pruned pricing can generate good complete-fleet columns but cannot replace global pricing lower bounds without safe exclusions.

## Numerical repair protocol (proposed engineering)

1. Log the raw incumbent, rounded route/bus decisions, original-unit row residuals, SOC at every event, charge-window capacities, terminal energy deficit, and objective before/after decoding. Retain every intermediate round's accepted plan. Diagnose model-versus-replay mismatches separately from arithmetic tolerance and solver infeasibility.
2. Round integer route decisions only when sufficiently near an integer; check path/coverage/depot invariants. Fix the resulting topology and re-optimize continuous charging under all original shared limits and terminal replenishment. Use a feasibility LP first, then the fixed-route convex QP or existing supply-cost approximation. Never repair by independently clipping individual charges: SOC and shared power couple them.
3. Replay the repaired plan again and recompute the physical bill. Keep the earlier replay-valid reference if repair fails. Small physical slack margins may help reserve/capacity inequalities, but change the feasible region and must be measured; do not demand impossible excess SOC above a terminal full-battery equality.
4. On selected route-fixed failures, reconstruct rational coefficients from the authoritative decimal/unit specification and check feasibility with rational/interval arithmetic. A rationalized IEEE float certifies that float encoding, not necessarily the intended decimal model. A large deficit cannot be declared roundoff merely because tightening tolerances changes the outcome.

The repair protocol is our proposed EGG adaptation of P7–P10. Neither a tighter tolerance nor successful fixed-route repair certifies global optimality. A rational linear outer approximation remains an approximation to the nonlinear supply bill.

## Three prospective experiments, ranked

All protocols must be written before later authorized compute. Use only allowed synthetic development/training and public cases; sealed DEV/TEST/A6/B3/GIRO remain excluded. Preserve the same four-round policy, seeds, tariff definition, and all overhead within the wall-time comparison. CPU-hour estimates assume **one solver thread** and must be multiplied by thread count if allocated otherwise. E10's 30 case/budget cells consume about 2.3 solver-hours per arm/seed (1.2 synthetic + 1.1 public), before setup overhead.

### 1. Reliability gate: rounding/charging repair versus tolerance mitigation

**Mapping/sources:** native decoding, continuous charging completion, event replay; P7–P10. **Effort:** 24–40 engineering hours; add 8–16 hours only if exact LP export is needed. **Compute:** four arms x three seeds x 30 cells = about 27.6 CPUh; allow 35–50 CPUh including diagnostics and selected rational LPs. No compute performed here.

Arms: existing settings; tolerance/scaling diagnosis with one predeclared parameter package; topology-fixed charging repair; combined repair/mitigation. Use m5 as the fixed pruning rule and include existing global-fraction controls for context. Count repair within budget. Inspect every Eberbach 600/1800-second seed and deliberately retain failed intermediate candidates for forensic comparison. A feasibility-relaxation optimum is diagnostic and never accepted as a plan.

**Go:** zero accepted-plan replay failures on all public long-budget runs, at least 90% recovery of historically reproducible small-residual failures, <=20% median completion overhead, and <=0.2% median bill degradation versus the earlier valid plan where comparable. **Stop/reformulate:** any repaired plan still fails exact replay; deficits remain physically material; a rounding rule changes topology illegally; or fixes only work by relaxing original physical requirements. Report unrepaired outcomes as losses. Passing this pilot is not a rare-failure reliability bound.

### 2. Recoverable adaptive keep sets and prediction/correction

**Mapping/sources:** scorer, top-m selector, solver-round orchestration; P1–P5. **Effort:** 24–48 hours with the current trained scorer; no neural retraining required for the pilot. **Compute:** five arms x three seeds x 30 cells = 34.5 CPUh; allow 40–50 CPUh including grouped calibration/replay overhead.

Start with m5; retain a replay-valid fallback fleet. Compare fixed m5, fixed m8, predeclared global fraction, uncertainty-adaptive per-trip m, and a correction arm allowing a capped number of movements outside the initial keep set. Predeclare widening triggers: no accepted incumbent, prediction/reference disagreement, or objective stall. Enlarge m/escape budget in stages, with a final full-domain stage only if time permits. Retain reference used edges, charge completion and earlier best accepted candidates. Entropy is a heuristic ranking; agreement with a correction fleet is not an optimality label. Include an offline instance-max conformal set as a candidate controller only after calibration units/label policy are fixed; if sets are too large, stop that controller rather than weakening the guarantee.

**Go:** no new replay failures; >=10% reduction in median time to the frozen valid quality target, or >=1% median paired bill improvement at equal budget; at least one substantive public improvement and no public regression >2%. **Stop:** overhead consumes the gain; >50% of public cases widen immediately to near-full size; numerical failures increase; or benefit disappears against simple predeclared m5-to-m8 widening. Public repeated seeds assess solver variation, not exchangeability of public timetables. Do not claim public coverage unless its calibration assumptions are defended independently.

### 3. LP-guided reinsertion with a safe-screening audit

**Mapping/sources:** movement/charging model blocks and pricing oracle; P6–P8. **Effort:** 28–50 hours, potentially more if whole-column coefficients are not readily exposed. **Compute:** five arms x three seeds x 30 cells = 34.5 CPUh; add 5–20 CPUh for full/recovery LPs and a small certification audit; reserve 45–65 CPUh. Memory overhead must also be recorded.

Compare fixed pruning, score widening, omitted-block negative reduced-cost reinsertion, hybrid reinsertion plus score/feasibility widening, and a full-domain control. First verify on small authorized cases that omitted-column scans and LP recovery reproduce the full LP bound. Use safe `L+r>U` screening only where full dual validity and incumbent replay pass are established. Evaluate against heuristic widening at equal total wall time; keep global pricing for any claimed hull lower bound. Do not silently present the restricted MIP gap as a full-model gap.

**Go:** LP recovery/check overhead <=20% of budget, no replay failures, and >=10% time-to-quality improvement or >=1% median physical-bill improvement over widening alone, with a meaningful public benefit. **Stop:** omitted movement blocks cannot be represented correctly; dual bound validity fails; the full charging LP dominates runtime/memory; or integer gains require many positive-cost omitted movements while the reinsertion rule never adds them. Then retain reduced costs as a heuristic feature, not a safety certificate.

## Do not pursue as a primary claim

- “Top-m ensures feasible fleets”: it supplies local options, not a globally consistent charged path cover.
- “Conformal 95% edge coverage preserves the optimum”: wrong statistical unit and generally wrong labels; synthetic-to-public exchangeability is also absent.
- “Apollo's uncertainty bound proves our fixings optimal”: its conditional precision and reference-feasibility arguments do not provide that theorem.
- “No negative reduced-cost omitted edges certifies the pruned MILP”: the counterexample above refutes it.
- Full exact MIP migration as the first numerical fix: diagnose route-fixed completion first; rational proofs do not automatically validate nonlinear cost or replay semantics.
- Loosening the independent replay acceptance threshold to erase E10 failures: retain original acceptance criteria and attribute each failure.

Literature-search limitation: no direct primary paper on conformal **movement pruning for coupled electric-fleet MILPs** was verified in this search. That is a search result, not a novelty proof. A plausible OR contribution would need a precise safe-screening/recovery theorem or a carefully evaluated fleet-level adaptive policy under shift, beyond applying existing predict-and-search mechanisms.
