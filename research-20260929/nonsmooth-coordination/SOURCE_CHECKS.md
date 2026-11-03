# Source checks: coupled EV pricing and Shapley–Folkman aggregation

Read-only verification of the supplied note’s literature claims. The checked
full text for Alizadeh et al. is the authors’ arXiv version; the Hreinsson et al.
author-page entry links to BibTeX but, in the current SINE page, exposes no
manuscript PDF or e-print. No paywalled PDF was accessed.

## Alizadeh et al.: verified model and update

Full text: [arXiv:1511.03611](https://arxiv.org/abs/1511.03611), v3 (2016).
Title: *Optimal Pricing to Manage Electric Vehicles in Coupled Power and
Transportation Networks*. Authors: Alizadeh, Wai, Chowdhury, Goldsmith,
Scaglione, and Javidi. Journal version: IEEE TCNS 4(4), 863–875 (2017), DOI
[10.1109/TCNS.2016.2590259](https://doi.org/10.1109/TCNS.2016.2590259).

**Source-derived synopsis (under 180 words).** Section III-C: each driver's
charge-and-route choice is a shortest path on the extended graph. Section
IV-A: nonnegative real path-flow rates $f_q^k$ sum to class demand $m_q$;
Remark I.1 restricts analysis to time-invariant static conditions, which
remove the full dynamic model's nonconvexity. Section IV-C, eq. 17, derives
LMPs as $p = gamma 1 + H^T mu$. Section V-A's oscillation is greedy/disjoint
pricing. Section V-B, Proposition V.1, eqs. 23–26, separates flow and dispatch
after dualizing balance and line limits: $gamma$ is free and $mu$ is projected
nonnegative. It asserts convergence for sufficiently small steps. Section
V-C, eqs. 29–30, bounds dual-gradient infeasibility for $alpha <= 1/L_d$.
Section VI uses constant $alpha=20$ (not $0.5/sqrt(k)$), reports about 100
iterations and approximate feasibility, and observes $O(1/sqrt(k))$
infeasibility decay; its example uses 25,000 EVs per epoch and two OD classes.

**Our inference for EGG.** Alizadeh et al. are a precedent for coordinating
continuous convex flow and dispatch, not an analysis of an atomic whole-fleet
oracle. The source does not establish an EGG convex-hull price, primal schedule
convergence, or the same Fenchel certificate under integer fleet choices.
Any 0.5/sqrt(k) replay or 20,000-query result should be labeled as an
independent EGG experiment, not the paper's result.

## Hreinsson et al.: what the public sources support

Hreinsson et al., “New Insights From the Shapley-Folkman Lemma on Dispatchable
Demand in Energy Markets,” *IEEE Transactions on Power Systems*, 36(5),
4028–4041 (2021), DOI
[10.1109/TPWRS.2021.3065913](https://doi.org/10.1109/TPWRS.2021.3065913). The
[IEEE record](https://ieeexplore.ieee.org/document/9376954/) has the abstract
and citation metadata. The [SINE page](https://sinelab.tech.cornell.edu/research/publication/)
lists BibTeX but no PDF/e-print; I did not verify the full theorem statements
or constants.

**Source-derived synopsis (under 120 words).** The abstract says the authors
apply Shapley–Folkman to aggregates of common convex and nonconvex individual
demand-response models for responsive loads. It reports approximate convexity
in aggregate action space and cost, and strict convexity under mild conditions.
It also discusses reduced-order convex aggregate models, including polytope
and ellipsoidal representations, and reports numerical comparisons with
conventional virtual-generator approximations.

**Our inference for EGG.** “Many small resources/participants versus one large
atomic participant” is a reasonable SF framing; “many small operators” is
misleading if operator means a system operator. Standard finite-dimensional SF
bounds depend on dimension and component size/nonconvexity. Under appropriate
scaling, many small components can yield small normalized aggregate defects; a
large atomic component can dominate. This does not imply universal additive
$O(1)$ regret, per-pair support, or a quantitative EGG rate. The checked
abstract and citation record also do not establish a MISO-ELMP connection
through coauthor Yonghong Chen; verify that claim separately.

## Correct the supplied Parvania attribution

The supplied [NSF PAR PDF URL](https://par.nsf.gov/servlets/purl/10019538) is
the author manuscript of Masood Parvania and Roohallah Khatami, “Continuous-Time
Marginal Pricing of Electricity,” *IEEE Transactions on Power Systems*, 32(3),
1960–1969 (2017), DOI
[10.1109/TPWRS.2016.2597288](https://doi.org/10.1109/TPWRS.2016.2597288). It is
not a Parvania–Scaglione unit-commitment paper. The separate Parvania–Scaglione
paper is “Unit Commitment With Continuous-Time Generation and Ramping
Trajectory Models,” DOI [10.1109/TPWRS.2015.2479644](https://doi.org/10.1109/TPWRS.2015.2479644).

## Verified BibTeX

```bibtex
@article{alizadeh2016coupled,
  author = {Alizadeh, Mahnoosh and Wai, Hoi-To and Chowdhury, Mainak and
            Goldsmith, Andrea and Scaglione, Anna and Javidi, Tara},
  title = {Optimal Pricing to Manage Electric Vehicles in Coupled Power and
           Transportation Networks},
  journal = {IEEE Transactions on Control of Network Systems},
  volume = {4},
  number = {4},
  pages = {863--875},
  year = {2017},
  doi = {10.1109/TCNS.2016.2590259},
  note = {arXiv:1511.03611, version 3 posted 2016}
}

@article{hreinsson2021,
  author = {Hreinsson, K{\'a}ri and Scaglione, Anna and Alizadeh, Mahnoosh
            and Chen, Yonghong},
  title = {New Insights From the Shapley-Folkman Lemma on Dispatchable Demand
           in Energy Markets},
  journal = {IEEE Transactions on Power Systems},
  volume = {36},
  number = {5},
  pages = {4028--4041},
  year = {2021},
  doi = {10.1109/TPWRS.2021.3065913}
}

@misc{scaglione2016marginal,
  author = {Scaglione, Anna},
  title = {Continuous-time Marginal Pricing of Power Trajectories in Power
           Systems},
  year = {2016},
  eprint = {1607.03802},
  archivePrefix = {arXiv},
  primaryClass = {math.OC},
  doi = {10.48550/arXiv.1607.03802},
  note = {Information Theory and Applications Workshop, 2016}
}
```
