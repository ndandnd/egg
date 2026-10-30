# Full lossy polygon: bounded primary-source comparison

**Conclusion:** the proposed polygon is not the same feasible-set formula as the two inspected sources. Its linear charge/discharge bookkeeping is familiar; the defensible new candidate remains the **exact assignment/cardinality/cost-labelled physical projection under common windows and a shared gross resource**, including a constructive serial realization. This bounded check neither certifies originality nor proves the new theorem.

## Primary text actually inspected

**Al Taha–Bitar, *When are Lossy Energy Storage Optimization Models Convex?*, v2, 19 November 2024:** [full text](https://arxiv.org/html/2403.14010v2). Section II, equations (1)–(6), uses one signed power `u_t` per discrete period, with positive/negative parts determining SOC. Its footnote 1 identifies the equivalent separate-variable model **with complementarity**. Section III, Theorems 1–2/equations (7)–(9), gives an invertible power/SOC transformation and an exact SOC polytope. Section I explicitly calls dropping complementarity an outer relaxation. Theorem 3 gives objective conditions for convex reformulation. These establish important prior physics and convexity tools, but the inspected statements do not retain gross intraperiod charge/export totals as independent controls.

**Mukhi–Loho–Abate, *Exact Characterization of Aggregate Flexibility via Generalized Polymatroids*, v2, 17 June 2025:** [full text](https://arxiv.org/html/2503.23458v2). Section II-E expressly assumes perfect round-trip efficiency for bidirectional devices; it explains why charging-only conversion efficiency can be absorbed. Sections II-B and III-C concern prescribed device populations and exact Minkowski aggregation. No claim that its stated lossy bidirectional model is the proposed polygon is justified.

## Cycling and time resolution: the material distinction

In the proposed new model, C and X are **integrals of distinct positive and negative actions during one common access window**. C>0 and X>0 need not mean simultaneous charging and exporting. They may represent successive actions on a bus or different buses, subject to the same gross occupation budget. Finite battery-neutral cycles change gross purchases/exports without changing final battery exchange Q. This time-sharing interpretation must remain explicit.

Consequently a coarse-window endpoint SOC does not uniquely determine its grid energy: different finite action sequences can share Q. That is why the proposed full image can be two-dimensional and why the single-signed-action power/SOC bijection cannot simply be applied to that window unchanged. Refining a signed-control time grid can represent reversals across subperiods, but doing so is not the same as an already stated exact elimination of all finite switching schedules, individual inventories and fleet assignments into five inequalities.

The converse warning is equally important: a linear model with separate C/X and no complementarity is not automatically physically exact. Here exactness must come from the new **serial realization and SOC argument**, with no switching penalty, minimum session, taper or lower action duration. The broader class of batteries with restricted switching or distinct individual access windows does not inherit the result. Convexity obtained by permitting time sharing should not be marketed as discovering convexity of a single lossy battery.

## What the candidate actually adds, if its proof holds

For fixed cardinality, the proposed bounds

`C>=r_m/alpha`, `X>=0`, `max(S-NB,S-alpha H)<=alpha C-X/delta<=P`, `C+X<=K`

are five halfspaces in gross-total coordinates. The map to `(E,L,c)` retains net grid purchase, terminal refill and vehicle fee. The vertex bound is elementary planar geometry, not a new polyhedral algorithm. The substantive step is showing that the **minimum matching statistic r_m suffices for the entire physical polygon**, including additional cycling, rather than just its monotone efficient boundary, and that no further per-bus constraint is lost.

Keeping full polygons would permit negative-price and nonmonotone convex objectives because it preserves physical alternatives rather than discarding dominated ones. This removes the earlier monotonicity restriction only for this expressly broadened complete projection. It is not a generic guarantee that every lossy storage relaxation is exact or that arbitrary intraperiod price variation is represented: one price/load coordinate per declared market window must still be the settlement convention.

## Honest novelty and wording

The exact polygon formula was not located in these inspected primary sections. This is not evidence that no equivalent formula exists elsewhere. Call the conversion relations, SOC accounting, time sharing, box aggregation and five-vertex geometry classical. Lead instead with endogenous matching and paid fleet size collapsing to an exact finite **joint load–vehicle-cost image** under fixed common resources. Explicitly distinguish the full-image result from the earlier efficient two-segment reduction and distinguish serial cycling from simultaneous physical operation. A broader novelty claim would require further evidence; none is supplied by this check.
