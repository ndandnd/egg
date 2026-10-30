# Screening, verification and learning-augmented optimization

23 October 2026. Primary-source follow-through accompanying the interdisciplinary review. These are seven source entries, including two publications from the same Gap Safe research line. Full-text access means selective inspection, not reproduction of every proof. No optimization or training run was performed.

## Seven sources

| Primary source | Inspected evidence | What EGG can borrow; what it cannot |
|---|---|---|
| Eugène Ndiaye, Olivier Fercoq, Alexandre Gramfort, Joseph Salmon (2015), **GAP Safe screening rules for sparse multi-task and multi-class models**, NeurIPS. [Paper](https://proceedings.neurips.cc/paper/2015/file/69421f032498c97020180038fddb8e24-Paper.pdf). | Full PDF opened; model, smooth convex losses, dual strong concavity and screening construction inspected. | A primal/dual gap defines a region containing the optimal dual variable, enabling certified exclusion for the specified sparse convex models. Separate proved deletion from heuristic working sets. The spherical test and its assumptions do not apply directly to integral bus connections. |
| Ndiaye, Fercoq, Gramfort, Salmon (2017), **Gap Safe Screening Rules for Sparsity Enforcing Penalties**, JMLR 18(128):1–33. [Record](https://jmlr.org/papers/v18/16-577.html). | Publisher abstract and bibliography. This is an extended framework, not an independent EGG replication. | A broader reference for safe screening in sparsity-regularized regression. Use it to state the distinction between prediction and proof, rather than claiming that a high-confidence classifier can safely remove routes. |
| Cássio F. Dantas, Emmanuel Soubies, Cédric Févotte (2021), **Expanding Boundaries of Gap Safe Screening**, JMLR 22(236):1–57. [Record](https://jmlr.org/papers/v22/21-0179.html). | Publisher abstract and bibliography; proofs not audited. | Extends screening beyond global strong concavity using local regularity. This illustrates that broader guarantees require additional analysis; it does not supply a generic theorem for arbitrary nonconvex fleet models. |
| Mathurin Massias, Alexandre Gramfort, Joseph Salmon (2017), **From safe screening rules to working sets for faster Lasso-type solvers**, arXiv:1703.07285v2. [Primary record](https://arxiv.org/abs/1703.07285v2). | Author abstract and version history. | Nested working-set selection and inner optimization already combine aggressive search with safe tests. The “small problem, expand, solve again” architecture is mature. In EGG, whether an expansion criterion is certified depends on full-model bounds or exact pricing, not on its resemblance to this algorithm. |
| Étienne Bamas, Andreas Maggiori, Ola Svensson (2020), **The Primal-Dual method for Learning Augmented Algorithms**, NeurIPS. [Paper](https://proceedings.neurips.cc/paper/2020/file/e834cb114d33f729dbc9c7fb0c6bb607-Paper.pdf). | Full PDF opened; online covering formulation and consistency/robustness bound inspected. | Measures advice value together with worst-case protection when advice is poor. Borrow good-advice/bad-advice stress tests and a classical fallback comparison. Its online covering assumptions and competitive guarantees do not transfer to offline, finite-time, integral EVSP. Keeping one acquired witness is not a competitive-ratio result. |
| Rajiv Sambharya, Georgina Hall, Brandon Amos, Bartolomeo Stellato (2023), **End-to-End Learning to Warm-Start for Real-Time Quadratic Optimization**, PMLR 211:220–234. [Record](https://proceedings.mlr.press/v211/sambharya23a.html); [paper](https://proceedings.mlr.press/v211/sambharya23a/sambharya23a.pdf). | Full PDF opened; architecture and parametric convex-QP setting inspected. | Learns an initialization through a fixed number of downstream splitting iterations. A possible EGG use is repeated continuous charging completion after routes are fixed, if that subproblem actually has the required QP structure. It does not make an integral route decoder differentiable or certified. Profile charging time before building this module. |
| Edmund Clarke, Orna Grumberg, Somesh Jha, Yuan Lu, Helmut Veith (2000), **Counterexample-guided Abstraction Refinement**, CAV, LNCS 1855:154–169. [Author-hosted paper](https://web.stanford.edu/class/cs357/cegar.pdf); [DOI](https://doi.org/10.1007/10722167_15). | Full PDF opened; abstraction/refinement framework inspected; [author bibliography](https://www.cs.cmu.edu/~emc/papers.htm) corroborates metadata. | A failed abstract verification can identify what an abstraction omitted. Borrow failure-driven refinement and explicit counterexamples. Crucial reversal: CEGAR's abstraction overapproximates behaviors, whereas deleting EGG edges underapproximates feasible plans. Its proof-transfer direction therefore cannot be imported. |

## Two elementary facts worth implementing, not advertising as novelty

Let \(\mathcal F\) be the full feasible fleet set and \(U=f(\bar x)\) the objective of a replay-valid feasible witness. All quantities below use the same physical instance and objective.

**Certified exclusion.** For a binary edge \(e\), suppose \(L_e\) is a valid lower bound on
\[
\min\{f(x):x\in\mathcal F,\ x_e=1\}.
\]
If \(L_e>U\), no plan costing at most \(U\) can use that edge. Proof: any such plan would have cost at least \(L_e>U\). This is elementary bounding/variable fixing, not a new EGG theorem. A valid full-model relaxation can supply \(L_e\). A restricted-graph lower bound, LP zero, neural score or empirical absence cannot. Strict inequality preserves all incumbent-quality alternatives; numerical margins must cover bound/replay tolerances. Separate per-edge solves may be too expensive, so learning might prioritize which *checks* to purchase rather than make unproved deletions.

**Witness retention.** If an algorithm starts with a valid witness, keeps it unchanged until a newly verified plan has no higher true objective, and returns the stored witness at the deadline, its returned objective cannot exceed that initial witness's objective. Proof is induction over accepted replacements. This assumes the stored witness stays valid for the same constraints and tariff, and the return mechanism survives failures. It says nothing about how quickly the initial witness was found, or how the method compares with giving the whole budget to a different solver. Actual replay is tolerance-qualified physical evidence, not an exact-arithmetic theorem about the implementation.

These two facts protect opposite ends of the computation: one justifies excluding an option, the other protects a feasible answer. The unresolved scientific question is whether learned allocation of search and bound checks produces a better cost–time–certification tradeoff than strong classical allocation.

## Where an apparently transferable result breaks

| Tempting inference | Correct scope |
|---|---|
| A screened regression feature is provably irrelevant, so a high-confidence low-score route edge is safe to remove. | The convex screening certificate relies on a particular dual problem and regularity. A classifier provides no corresponding fleet bound. |
| An exact solve of the restricted graph provides a global lower bound. | It lower-bounds that restricted optimum; deleting alternatives generally increases the minimum. The full problem needs a valid relaxation, full search, or exact pricing argument. |
| No negative reduced-cost column means integer optimality. | Under the master/pricing assumptions it proves continuous-master optimality. Integrality requires further reasoning or search. |
| A retained fallback gives robustness against a full-budget classical solver. | It only protects the acquired fallback under its stated model. The budget spent acquiring and improving it must be compared fairly. |
| Warm-start theory for convex QPs proves whole-fleet generalization. | The theorem's model family and loss concern the continuous solver layer; the discrete route choices remain separate. |
| A few failed replay examples characterize all omitted possibilities. | They identify specific defects. Completeness requires a suitable exhaustive search, separation oracle, or explicit bounded claim. |

## Priority

Use the bound/witness interfaces immediately in research design. Test selective bound checks only on small, fully specified cases before considering amortized models. Treat QP warm-starting as a conditional option: it is low priority unless continuous completion consumes a material fraction of measured time. CEGAR and online learning-augmented results currently supply vocabulary and stress tests, not additional guarantees.
