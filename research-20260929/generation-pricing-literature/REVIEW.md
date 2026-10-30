# Generation-side pricing: citation trace and implications for EGG

29 September 2026. Literature and formulation assessment, not a computational result.
Prepared under the user's request to trace Scaglione's references and assess their
use in EGG. Luna traced citations; Sol inspected the current model and checked the
proposed dual and support formulas; root synthesized the assessment. No cluster
job, solver experiment, automation restart or manuscript claim was made.

## Finding

Yes: generator dispatch can give EGG a more interpretable, time-coupled supply
cost and endogenous electricity prices. Convex-hull pricing also supplies useful
decomposition and price-selection ideas. However, EGG already uses the analogous
whole-fleet convexification, and generation-side methods do not eliminate its
global discrete fleet-pricing problem. The exact paper Anna sent remains unknown.

The closest new recognition candidate is Wang et al. (2013), **An Extreme-Point
Subdifferential Method for Convex Hull Pricing in Energy and Reserve Markets—Part
I: Algorithm Structure**. Its price computation maximizes a Lagrangian dual; an
auxiliary QP supplies ascent directions. Gribik–Hogan–Pope (2007), with cost/hull
diagrams and a dual maximization, is another strong candidate. These are fits to
the remembered description, not evidence about which paper was sent.

## What was actually traced

The three early Scaglione/Parvania papers checked were:

- Anna Scaglione, **Continuous-time Marginal Pricing of Power Trajectories in
  Power Systems** (2016), [author preprint](https://arxiv.org/abs/1607.03802).
- Masood Parvania and Anna Scaglione, **Generation Ramping Valuation in Day-Ahead
  Electricity Markets** (2016), [institutional record](https://certs.lbl.gov/publications/generation-ramping-valuation-day.html),
  DOI 10.1109/HICSS.2016.292.
- Parvania and Scaglione, **Unit Commitment With Continuous-Time Generation and
  Ramping Trajectory Models** (2016), [institutional record](https://certs.lbl.gov/publications/unit-commitment-continuous-time.html),
  DOI 10.1109/TPWRS.2015.2479644.

Their checked bibliographies do not establish a direct citation to the principal
convex-hull-pricing papers below. The Bernstein convex-hull property in the latter
two papers bounds continuous-time generation/ramp trajectories through polynomial
control coefficients; it is not a convex hull of electricity prices. Their spline
reference is P. Dierckx, *Curve and Surface Fitting with Splines* ([22] in Ramping
Valuation; [23] in Unit Commitment). A direct pricing reference is T. Li and
M. Shahidehpour, **Price-Based Unit Commitment: A Case of Lagrangian Relaxation
Versus Mixed Integer Programming** (2005), DOI
[10.1109/TPWRS.2005.857391](https://doi.org/10.1109/TPWRS.2005.857391)
([26] and [28], respectively).

A useful **related-paper bridge, not a claimed forward citation by Scaglione**, is
Masood Parvania and Roohallah Khatami, **Continuous-Time Marginal Pricing of
Electricity** (2017), IEEE TPWRS 32(3), 1960–1969:
[NSF author manuscript](https://par.nsf.gov/servlets/purl/10019538),
[DOI](https://doi.org/10.1109/TPWRS.2016.2597288).
Its bibliography on printed p. 10 cites the Scaglione UC paper as [29] and Ramping
Valuation as [31], together with Schweppe et al. [4], O'Neill et al. [17],
Gribik–Hogan–Pope [18], Wang Part I [22], and Schiro et al. [23]. Its own method
prices continuous-time dispatch with commitment fixed; it is distinct from CHP.
The NSF PDF endpoint failed direct web extraction during this pass; the source's
indexed full text and the author-posted manuscript text provided the reference
trace. Do not describe this as an independently downloaded/hashed PDF.

## Reading shortlist and recognition clues

| Paper | Method and recognition clue | Use in EGG / limits |
|---|---|---|
| Gui Wang, Uday V. Shanbhag, Tongxin Zheng, Eugene Litvinov, Sean Meyn (2013), **An Extreme-Point Subdifferential Method for Convex Hull Pricing in Energy and Reserve Markets—Part I: Algorithm Structure**, TPWRS 28(3), 2111–2120. [Primary institutional record](https://pure.psu.edu/en/publications/an-extreme-point-subdifferential-method-for-convex-hull-pricing-i/), DOI 10.1109/TPWRS.2012.2229302. | Global maximization of the UC Lagrangian dual; extreme-point/subdifferential geometry; QP-generated ascent. Strong new match to the memory. | Alternative dual algorithm, not a way around exact/global subproblem bounds. Algorithm description verified from primary abstract; a CiteSeerX PDF link was located, but root's retrieval failed. Detailed algorithm not audited. |
| Same authors (2013), **Part II: Convergence Analysis and Numerical Performance**, 2121–2127. [Primary record](https://pure.psu.edu/en/publications/an-extreme-point-subdifferential-method-for-convex-hull-pricing-i-2), DOI 10.1109/TPWRS.2012.2229303. | Finite termination and comparisons with subgradient methods under the paper's setting. | Useful algorithm follow-up; abstract verified, no full-text audit. Part II is not separately listed in the bridge's references. |
| Paul R. Gribik, William W. Hogan, Susan L. Pope (2007), **Market-Clearing Electricity Prices and Energy Uplift**. [Harvard record](https://hepg.hks.harvard.edu/publications/market-clearing-electricity-prices-and-energy-uplift), [full paper](https://www.tse-fr.eu/sites/default/files/medias/doc/conf/eem/papers_2008/hogan.pdf). | Pictures of nonconvex aggregate cost and its convex hull; dual maximization and minimum uplift. | Strong conceptual foundation. Price-only support can fail; hull pricing does not necessarily remove compensation. Already in EGG's catalog and current theory citations. |
| Richard P. O'Neill, Paul M. Sotkiewicz, Benjamin F. Hobbs, Michael H. Rothkopf, William R. Stewart Jr. (2005), **Efficient market-clearing prices in markets with nonconvexities**, EJOR 164(1), 269–285. [Publisher](https://www.sciencedirect.com/science/article/pii/S0377221703009196), DOI 10.1016/j.ejor.2003.12.011. | Associated LP after a MIP; dual prices include integral activities. | Particularly close to the LP clue, but an expanded settlement mechanism. It does not prove that time-only energy prices support EGG's integer fleet. Already cited by EGG. |
| Dane A. Schiro, Tongxin Zheng, Feng Zhao, Eugene Litvinov (2016), **Convex Hull Pricing in Electricity Markets: Formulation, Analysis, and Implementation Challenges**, TPWRS 31(5), 4068–4075. [DOI](https://doi.org/10.1109/TPWRS.2015.2486380). | Market interpretation and examples, with implementation caveats. | Relevant for settlement definitions and avoiding overclaims about uplift. Verified citation trail; no new full technical audit in this pass. Already cited by EGG. |
| Bowen Hua and Ross Baldick (2017), **A Convex Primal Formulation for Convex Hull Pricing**, TPWRS 32(5), 3814–3823. [Author manuscript](https://arxiv.org/abs/1605.05002), DOI 10.1109/TPWRS.2016.2637718. | Explicit generator feasible hulls and cost envelopes: LP for piecewise-linear costs, SOCP for quadratic costs. | Useful generator formulation. The explicit exact result does not automatically cover arbitrary ramp-constrained units; the paper discusses ramping approximations. Not verified as a citation in the early Scaglione seeds/bridge. Already in EGG's catalog. |
| Panagiotis Andrianesis, Dimitris Bertsimas, Michael Caramanis, William Hogan (2022), **Computation of Convex Hull Prices in Electricity Markets with Non-Convexities using Dantzig-Wolfe Decomposition**, TPWRS 37(4), 2578–2589. [Author manuscript](https://arxiv.org/abs/2012.13331), DOI 10.1109/TPWRS.2021.3122000. | Master over complete unit schedules; generator profit maximization supplies columns. | Closest computational analogy to EGG's whole-fleet columns. Heuristic/learned columns may enter the master, but global pricing bounds remain necessary for certification. Already in EGG's catalog. |
| Bernard Knueven, James Ostrowski, Anya Castillo, Jean-Paul Watson (2022), **A Computationally Efficient Algorithm for Computing Convex Hull Prices**, C&IE 163, 107806. [Author preprint](https://optimization-online.org/wp-content/uploads/2019/09/7370.pdf), DOI 10.1016/j.cie.2021.107806. | Benders approach to a large generator hull formulation. | Motivation for structural inequalities/decomposition; their generator structure and speedups cannot simply be transferred to fleet routing. Related lead, not a verified Scaglione citation. |

Two Scaglione connections matter for positioning. Kari Hreinsson, Anna Scaglione,
Mahnoosh Alizadeh and Yonghong Chen's **New Insights From the Shapley-Folkman Lemma
on Dispatchable Demand in Energy Markets** (2021), DOI
[10.1109/TPWRS.2021.3065913](https://doi.org/10.1109/TPWRS.2021.3065913), studies
approximate convexity of aggregate dispatchable demand. Only its abstract was
verified here; aggregation should be discussed alongside EGG's distinction between
total and per-pair regret. Yao, Liu, Scaglione, Bekhor and Zhang's **Integrated
equilibrium model for electrified logistics and power systems** (2025),
[public manuscript](https://arxiv.org/abs/2505.04532), couples convex power dispatch
to a continuous fleet-flow model. Its grid module is relevant; its fleet
convexification does not resolve our complete, discrete-fleet question. No internal
protected outcomes were accessed. Coordinate positioning before manuscript claims.

## How the remembered geometry could work

There are three different objects: a hull of generation trajectories (Bernstein
geometry), a convex envelope of a nonconvex commitment cost (CH pricing), and a
dual polyhedron whose optimum gives dispatch prices. The last two most closely
match the price/maximization clue. One should not take an arbitrary hull of price
vectors and maximize the electricity bill.

For a linear generation model, write demand as a vector across times/nodes:

\[
H(d)=\min_{g\ge0}\{a^\top g:Ag=d,\;Bg\le h\}.
\]

Capacities, ramp limits and linear network constraints can be represented in this
form, with free variables split where necessary. When the LP is feasible with a
finite optimum, strong LP duality gives

\[
H(d)=\max_{\substack{p\ \mathrm{free},\;\mu\ge0\\
A^\top p-B^\top\mu\le a}}
\{p^\top d-h^\top\mu\}.
\]

Here the optimal balance multipliers are the marginal prices. This is literally
a maximization over a polyhedron; the intercept term matters. With ramps, prices
are determined jointly across time. Generator startup/on-off costs make the
physical value function nonconvex: then the analogous Lagrangian dual supports
its convex envelope and need not reproduce the integer dispatch cost. This
formulation is our synthesis of the standard primal/dual connection, not a new
theorem claimed from the citation search.

## Proposed model extension, separate from algorithm changes

Let background demand be b and fleet energy be L, with consistent interval units.
Replace the current synthetic quadratic supply function by incremental generation
cost

\[
G(L)=H(b+L)-H(b).
\]

For convex dispatch, G is convex and may be nonsmooth or infinite outside its
feasible domain. Capacity/ramp/network assumptions and baseline H(b) must be
declared. If supply cannot serve some fleet alternatives, either define appropriate
grid-feasible deviation rights or explicitly model emergency supply/curtailment;
do not silently compare different opportunity sets.

The physical planner and fleet-hull problem become

\[
D_G=\min_{x\in\mathcal X}\{c(x)+G(e(x))\},\qquad
CH_G=\min_{(L,c)\in\operatorname{conv}\{(e(x),c(x)):x\in\mathcal X\}}
\{c+G(L)\}.
\]

This can be implemented by placing generation variables and balance equations in
the master, or by adding generation dual cuts. A dual-feasible pair (p,mu) gives
the global affine lower cut

\[
G(L)\ge p^\top(b+L)-h^\top\mu-H(b).
\]

At an optimal dispatch dual this is a supporting cut. A Benders implementation
also needs feasibility cuts if generation can be infeasible. Stored dual-feasible
cuts can be reused under unchanged costs/constraints; validity must be rechecked
when those data change. With PWL generation the restricted master can be an LP;
quadratic generation gives a convex QP. Networked pricing needs node-time fleet
loads and prices, not the present aggregate time vector alone.

The fleet response remains

\[
V(p)=\min_{x\in\mathcal X}\{c(x)+p^\top e(x)\}.
\]

For any valid global lower bound on V(p), subtracting G*(p) gives a hull lower
bound. A restricted fleet pool alone supplies no global pricing certificate.
Generator schedules decompose by unit in the cited Dantzig-Wolfe method; EGG's
shared chargers/service coverage mean whole feasible fleets remain the safe
column object. Separate bus-path convexifications need their own proof.

## Price multiplicity changes what must be tested

The current paper assumes differentiable supply on a neighborhood of feasible
loads (paper/latex/model_theory.tex). A dispatch LP can have several optimal
balance-price vectors. Failure at one arbitrarily selected dual price does not
show failure at all admissible marginal prices.

For a named feasible fleet x, let P(e(x)) be the projection of the optimal
generation-dual solutions onto balance prices. A useful proposed diagnostic is

\[
\inf_{p\in P(e(x))}\big[c(x)+p^\top e(x)-V(p)\big].
\]

An attained zero gives a compatible price supporting that fleet. A certified
positive lower bound excludes all prices in that specified set for that fleet.
The objective is convex piecewise linear when fleet columns are finite, and
fleet-response separation can enforce its epigraph constraints. This is a
proposed adaptation, not a demonstrated speedup or novelty claim. Never interpret
regret at a bounded physical incumbent as a statement about every optimal fleet.

Mathematically, one can use the full subdifferential of G. Its boundary normals
may include prices introduced by an artificial restriction L>=0; the actual
generator dual set is the clearer market definition. Extending the paper's
equivalence D=CH iff there is a supporting physical plan requires attained
physical/hull optima, strong Fenchel duality and dual-price attainment (for
example an appropriate relative-interior constraint qualification). Equality of
infima alone is insufficient. With nonconvex generator commitment, a separate
generator hull/envelope is needed; separately convexifying fleet and generator
sets does not automatically construct the hull of their coupled feasible set.

## What to do next

1. **Same-model computational improvement:** compare a native convex MIQP/MISOCP
   planner against the current repeated tangent MILPs, using the identical
   quadratic F, physical constraints, cases, and total budget. Code inspected:
   src/egglab/native_pathflow.py around lines 562–635. Avoid attributing any
   improvement to new generation economics. Speedup is a hypothesis: the existing
   diagnostics show expensive native MIP work, not expensive restricted-master
   polishing, and a direct MIQP may still be difficult. The fixed-price fleet
   oracle remains a MIP. This does not replace the previously recommended check
   of cardinality/energy-cut nonredundancy; both are formulation candidates.
2. **Small generation-side validation:** an enumeratable four-period fleet case
   and two convex generators, with capacity and a binding ramp. Check primal/dual
   equality, baseline subtraction, price multiplicity, cut validity, and the
   fleet certificate. Compare independent-time supply with time-coupled supply
   under a stated common experimental question. Only after this succeeds should
   one development timetable receive a bounded extension. No launch budget is
   created by this literature note.
3. **Later UC extension:** add commitment only if it answers a clear research
   question. Separate fleet discreteness from generator discreteness in the
   comparisons; differences of hull gaps are not automatically additive causal
   decompositions. O'Neill's prices for integral activities would change the
   settlement/deviation question, not merely accelerate the present test.
4. **Learning:** compare cold solving, retained fleet columns and nearest-neighbor
   retrieval first. Reuse of valid generation cuts is another transparent
   baseline. Learned fleet/route proposals can supply feasible candidates, but
   direct prediction, repair and global verification remain separately timed.
   Do not use approximate price prediction as an exact regret certificate.

A useful paper figure would show the same small fleet under uncoupled and
ramp-coupled generation: dispatch trajectories, marginal-price ranges, whole-fleet
response and D_G−CH_G bounds. This tests the actual pricing question rather than
adding an unrelated solver benchmark. The existing eight public sensitivity
intervals all contain zero; this review does not change those results or the
reviewed v0.8 draft. Automation remains paused.
