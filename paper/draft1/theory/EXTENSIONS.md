# Extensions of the two-batch projection: slots, plugs, embedding, characterization

Branch `wp/theory-ext-20261112`. Notation follows `paper/draft1/main.tex`
(Sections 3-6). Every claim below is proved here or checked by exact
enumeration in `paper/draft1/code/test_extensions.py` (library
`extensions.py`, log `test_extensions_log.txt`). Unproved statements are
labelled **Conjecture** or **Open**. No statement of the paper is changed. No
error in the paper's existing theory was found (Section 8 lists what was
re-derived).

## Status

| Task | Claim | Status |
|---|---|---|
| T1(a) | Slot-load projection of a matching (pooled connector, charge-only, common efficiency) | **proved** (Thm 1) |
| T1(a) | One matching per cardinality suffices; layers nested in m | **proved** (Thm 1) |
| T1(a) | One-fee bound D - CH <= f(t - floor t) < f for every convex slot cost | **proved** (Lemma A, Thm 1) |
| T1(a) | Bidirectional (V2G) slots | not attempted (intra-window arbitrage needs per-bus state-of-charge headroom) |
| T1(b) | Exact cut description of attainable slot vectors with per-bus limit p and C plugs | **proved** (Thm 2); cross-validated against an independent max-flow check |
| T1(b) | One dominating matching per cardinality | **refuted**. Smallest counterexample, adequate terminal: 5 services (path graph), 2 early slots, m = 2 (Ex. 1). With binding terminal per-bus limits: 4 services, 1 early slot, m = 1 (Ex. 2) |
| T1(b) | "Window length x p >= largest per-bus need" suffices | **refuted** (Ex. 1 satisfies it) |
| T1(b) | Right condition: compare phi_M(y) = sum_M (a_i+b_j-B-y)_+ at all subset sums y of per-bus slot caps | **proved** sufficient; necessary when the aggregate caps do not truncate (Thm 3) |
| T1(b) | Every slot cap >= largest edge requirement => any r_m-minimizer dominates | **proved** (Cor 3.1) |
| T1(b) | Complete graph, adequate terminal => paper's sorted matching dominates, for every slot structure | **proved** (Cor 3.2) |
| T1(b) | Complete graph, binding terminal limits => sorted matching dominates | **Conjecture 3.2'** (random check, 0 failures) |
| T1(b) | Refined ordering (min r_m, then majorization) restores dominance | **refuted** (in Ex. 1 no size-2 matching dominates) |
| T1(b) | One-fee bound under Cor 3.1 or Cor 3.2 | **proved** (Cor 3.3) |
| T1(b) | Strict one-fee bound in general | **refuted**: D - CH = f in Ex. 1, also for the smooth cost c\|d - z\|^2 with c >= 8f |
| T1(b) | D - CH <= f in general | **Conjecture 3.4** (random check, no violation); proved: D - CH <= f t <= f nu |
| T2 | Embedding: one tripper class with the mixing property + convex rest of depot, coupled through aggregate slot loads and convex constraints | **proved** (Thm 4) |
| T2 | Couplings that break it | identified and checked: per-bus tripper coupling (binding plug limits), a second nonconvex class with a different window (D - CH = 2f(1-eps), Ex. 3), nonconvex rest of depot |
| T3 | Linear prices: price-independent iff conv S_M* contains every S_M (common fee); general fees; representative families | **proved** (Thm 5) |
| T3 | Convex costs: iff S_M* contains every S_M and has minimal fee; family version is a union condition | **proved** (Thm 5) |
| T4 | Homogeneous energies, time-compatibility graph, pooled connector: FIFO matching dominates each layer and the one-fee bound holds | **proved** (Thm 6) |
| T4 | Heterogeneous energies, complete compatibility: dominating matching | **refuted**: 3 services, 1 early slot (Ex. 4); worst commitment regret min(\|spread\|, f) |
| T4 | One-fee bound with staggering | **refuted**: D - CH = k(1-eps) f with k pairs and k slots (Ex. 5; k = 2 has complete compatibility) |
| T4 | Bound on D - CH with staggering | proved D - CH <= f t <= f nu; whether D - CH <= f min(nu, T1) is **Open** |
| T5 | Shapley-Folkman relation | **proved** (Prop 7): SF gives the sum of the min(k, T) largest fees for k independent classes, attained in the limit by Ex. 3; SF does not imply the one-fee bound for one fleet |

---

## 0. The mixing lemma

A *layer family* is a sequence of convex sets Lambda_0, ..., Lambda_nu in R^d
(slot-load vectors) with vehicle cost f(N - m) on layer m, f > 0. Empty layers
are allowed.

**Mixing property (MP).** For finitely many z_k in Lambda_{m_k} and weights
mu_k >= 0 summing to one, with t = sum_k mu_k m_k, the point sum_k mu_k z_k
lies in Lambda_{floor t}.

**Lemma A (one-fee bound for layer families with MP).** Let F be proper,
closed and convex on R^d (value +inf allowed). Let the rest of the depot be
described by decisions y, a convex set Kc of pairs (z, y) (its own constraints
and any convex coupling with the tripper's slot vector z), a convex cost c(y),
and an affine load map w(y). Put D = inf over m, z in Lambda_m, (z, y) in Kc of
f(N - m) + c(y) + F(z + w(y)), and CH the same infimum over the convex hull of
the image {(z + w(y), f(N-m) + c(y))}. Every hull point with mean count t is
matched by a physical plan with the same total load and cost at most the hull
cost plus f(t - floor t). Hence D - CH <= f(t - floor t) < f whenever CH is
attained at a mean count t, and D - CH <= f in general.

*Proof.* A hull point is sum mu_k (z_k + w(y_k), f(N - m_k) + c(y_k)) with
z_k in Lambda_{m_k} and (z_k, y_k) in Kc. Put z = sum mu_k z_k and
y = sum mu_k y_k. MP gives z in Lambda_{floor t}; convexity of Kc gives
(z, y) in Kc; convexity of c gives c(y) <= sum mu_k c(y_k); w is affine, so the
total load is unchanged and so is F. The fee at floor t exceeds the mixed fee
f(N - t) by f(t - floor t) < f. []

*Remark (fees that differ by cardinality).* With fee phi(m) nonincreasing and
convex in m, the same proof gives D - CH <= phi(floor t) - sum mu_k phi(m_k)
<= phi(floor t) - phi(floor t + 1), the largest one-step fee decrement.

**Lemma B (sufficient conditions for MP).** Let Lambda_m = {z in Q :
z(J) >= L_m(J) and z(J) <= U_m(J) for every J in a fixed index set}, with Q
convex, m -> L_m(J) nondecreasing and discretely convex and m -> U_m(J)
nonincreasing and discretely concave for each J. Then MP holds.
*Proof.* Let L^ be the piecewise-linear interpolation of m -> L_m(J); it is
convex and nondecreasing. For the mixture, z(J) = sum mu_k z_k(J) >=
sum mu_k L_{m_k}(J) >= L^(t) >= L_{floor t}(J) (Jensen, then monotonicity).
Symmetrically z(J) <= U_{floor t}(J), and z is in Q by convexity. So the
mixture lies in Lambda_{floor t}. []
The threshold form Lambda_m = {z in Q : a^T z >= q_m} is the case of one J.

---

## 1. T1(a): many slots, pooled connector

**Setting.** Early slots t = 1..T1, terminal slots s = 1..T2. Data (a, b, B,
Gamma, f) as in the paper. All buses are at the depot for the whole early
window and the whole terminal window. In early slot t the shared connector
delivers at most K_t >= 0 grid energy and any single bus can absorb the full
connector power (the paper's assumption); in terminal slot s at most H_s >= 0.
Charge-only, common efficiency alpha in (0, 1]. Load vector d = (e, l) in
R^{T1} x R^{T2}; cost f N_m + F(e, l) with F proper, closed and convex.

**Theorem 1 (slot projection, pooled connector).** For a matching M with
R_M = sum_{(i,j) in M} (a_i + b_j - B)_+, the attainable load vectors are
exactly
  Lambda(M) = { (e,l) : 0 <= e_t <= K_t, 0 <= l_s <= H_s,
                R_M <= alpha 1^T e <= P, alpha (1^T e + 1^T l) = S_0 }.
Consequently
 (i) a matching attaining r_m realizes the union of Lambda(M) over |M| = m,
     namely Lambda_m = {... alpha 1^T e >= r_m ...};
 (ii) Lambda_{m+1} is contained in Lambda_m;
 (iii) the layers have MP, so D - CH <= f(t - floor t) < f for every proper
     closed convex cost of the slot vector (Lemma A).

*Proof.* Necessity. With charging only, a bus's net early battery gain is
x_v = alpha c_v, where c_v is its early grid purchase. It lies in
[(a_i + b_j - B)_+, a_i] for a paired bus, [0, a_i] for an A-only bus and
[0, 0] for a B-only bus, which is full. The upper bound is the no-overcharge
condition at the end of the early window: state of charge never decreases
while charging. The lower bound is the afternoon service. Summing gives
R_M <= alpha 1^T e <= P. Every bus ends full, so alpha times all purchases
equals S_0. The slot caps are the connector limits.
Sufficiency. Given (e, l) in Lambda(M), choose x_v in its interval with
sum x_v = alpha 1^T e: start at the lower ends, which sum to R_M, and fill the
headroom, since the upper ends sum to P. A matrix c_{v,t} >= 0 with row sums
x_v / alpha and column sums e_t exists (transportation problem with equal
totals and no cell bounds; north-west corner rule). In slot t serve the buses
serially at full connector power; the slot total e_t <= K_t fits. The terminal
deficits s_v - x_v >= 0 (s_v is the bus's daily draw) sum to alpha 1^T l and
are split over terminal slots the same way. Each bus ends the early window at
B - a_i + x_v, which lies in [b_j, B] for a paired bus, and ends the day full.
Nonnegative service draw keeps intermediate states feasible, as in the paper.
(i), (ii): only R_M depends on M, and only through alpha 1^T e >= R_M; r_m is
nondecreasing (paper, App. A). (iii): Lemma B with one constraint
alpha 1^T e >= r_m; r_m is nondecreasing and discretely convex by the paper's
min-cost-flow argument, which does not use completeness of Gamma. []

*Attacks.* K_t = 0 for some or all t (the transportation step never uses
such a slot because e_t = 0). Empty layers (r_m above alpha min(P, sum K), or
too little terminal capacity): Lemma B handles them. Unequal batch sizes and
incomplete Gamma: the proof uses neither. Ties in r_m: any minimizer works.
alpha < 1: the constraints stay linear. Bidirectional exchange is **not**
claimed: with several slots a bus must hold energy before it discharges it,
so per-bus state-of-charge paths matter.
Exact check: `test_T1a_pooled_projection` (300 random instances, zero caps
and incomplete graphs included). The cut description of Thm 2 with per-bus
cap equal to the connector cap reproduces Lambda(M) at every test point. The
r_m-minimizer dominates every layer, layers are nested, and MP holds.

---

## 2. T1(b): per-bus power limit and C identical plugs

**Within-slot assumption.** Slot t has length h_t. A bus charges at power at
most p, at most C buses charge at once, and the site cap is K_t. Charging is
preemptive with zero switching time (the paper's serial assumption). By
McNaughton's wrap-around rule, per-bus slot energies c_{v,t} are realizable in
slot t iff c_{v,t} <= pi_t := p h_t and sum_v c_{v,t} <= kappa_t :=
min(C p h_t, K_t). Terminal slots likewise have pi'_s and kappa'_s. The pooled
model is pi_t = kappa_t. We take unit efficiency, since a common alpha rescales
every battery-side quantity by the same factor.

A bus v of a matching is (s_v, lam_v, hi_v, W_v): daily draw, minimum and
maximum early gain, and available early slots (all early slots in the
common-window class; Section 5 uses windows). Paired: (a_i + b_j,
(a_i + b_j - B)_+, a_i); A-only: (a_i, 0, a_i); B-only: (b_j, 0, 0).

**Theorem 2 (cut description).** For a matching M, d = (e, l) is attainable
iff 0 <= d <= kappa (both windows), d(T) = S_0, and for every set D of slots
d(D) <= G_M(D) := sum_v g_v(D), where, with D1 the early and D2 the terminal
part of D,
  g_v(D) = min( s_v, min(hi_v, pi(D1 n W_v)) + min(s_v - lam_v, pi'(D2)) ).
*Proof.* Network: source -> bus v (capacity s_v); v -> early hub E_v
(capacity hi_v); v -> terminal hub T_v (capacity s_v - lam_v; together with
the bus total s_v this encodes early gain >= lam_v); E_v -> early slot t in W_v
(capacity pi_t); T_v -> terminal slot s (capacity pi'_s); slot -> sink
(capacity d_slot). Per-bus feasibility, with state of charge handled as in
Thm 1, says exactly that bus v ships s_v with early part in [lam_v, hi_v]
within the slot caps. So d is attainable iff 0 <= d <= kappa, d(T) = S_0, and
the max flow equals S_0. Let D be the set of slot nodes on the sink side of a
cut. The other slots contribute d(T \ D). Each bus gadget contributes its own
cheapest separation of the source from D. By max-flow/min-cut on the gadget,
which is a tree, that equals the largest flow it can send into D, namely the
nested minimum g_v(D). Hence min cut = min_D [d(T \ D) + G_M(D)], which is
>= d(T) iff d(D) <= G_M(D) for all D. []
Equivalently, A(M) is the base polytope of the polymatroid G_M truncated by the
box. The maximum of d(D) over A(M) is Gk_M(D) = min over Y in D of
[G_M(Y) + kappa(D \ Y)], and A(M') is contained in A(M) iff Gk_{M'} <= Gk_M
pointwise; both sets have total S_0.
*Cross-validation* (`test_T1b_cut_vs_flow`): an independent exact
integer network-simplex feasibility check (networkx; per-bus network with lower
bounds, no cut formula) agrees with the formula at every test point. In
development, 400 instances and 90,255 points gave 0 disagreements; the
committed test repeats this on 150 instances (counts in the log).

**Terminal adequacy.** The terminal window is *adequate* if pi'_s >= B for
every terminal slot, so each terminal slot alone can refill any bus. The
aggregate caps kappa'_s are arbitrary.

**Theorem 3 (what depends on the matching).** Common early window, adequate
terminal. For D2 nonempty, G_M(D) = S_0 - phi_M(pi(D1)) with
  phi_M(y) = sum_{(i,j) in M} (a_i + b_j - B - y)_+,
the r-cost of M with battery B + y. For D2 empty, G_M(D) =
sum_i min(a_i, pi(D1)) does not depend on M. Let Y = {pi(D1) : D1 a set of
early slots} be the subset sums of the per-bus slot caps.
 (a) If phi_{M*}(y) <= phi_M(y) for all y in Y, then A(M*) contains A(M).
 (b) If the aggregate caps do not truncate (Gk = G, for example
     kappa = +inf), the converse holds.
*Proof.* If D2 is nonempty, pi'(D2) >= B >= s_v - lam_v = min(s_v, B), so
g_v = min(s_v, min(hi_v, pi(D1)) + s_v - lam_v) = s_v - (lam_v - pi(D1))_+,
using lam_v <= hi_v. If D2 is empty, g_v = min(hi_v, pi(D1)), and hi_v is
a_i for every A-bus and 0 for every B-only bus, whatever M is.
(a) follows from Thm 2, since all other constraints coincide and S_0 is the
same. (b) The constraint of M* at D = D1 u T2 reads
e(T1 \ D1) >= phi_{M*}(pi(D1)). If Gk = G, then by polymatroid tightness the
minimum of e(T1 \ D1) over A(M) is S_0 - G_M(D1 u T2) = phi_M(pi(D1)). So
phi_{M*}(y) > phi_M(y) yields a point of A(M) outside A(M*). []

The paper's r_m is phi(0). Per-bus limits add the values phi(y) for
y in Y \ {0}: the energy that pairs must receive beyond what fits in the
complementary slots.

**Corollary 3.1 (the limit never binds).** If pi_min = min_t pi_t is at least
the largest requirement of some r_m-minimizer M* (in particular, if
pi_min >= max over edges of Gamma of (a_i + b_j - B)_+), then M* dominates
layer m.
*Proof.* Every y in Y \ {0} is at least pi_min, so phi_{M*}(y) = 0, and
phi_{M*}(0) = r_m <= phi_M(0). Apply Thm 3(a). []
The condition pi(T1) >= max lam ("p times window length covers the largest
need") is **not** sufficient: Ex. 1 has pi(T1) = 4 >= 3.

**Corollary 3.2 (complete graph).** If Gamma is complete and the terminal is
adequate, the paper's sorted matching M*_m dominates layer m for every slot
structure (any pi, kappa, T1). M*_m pairs the m smallest draws of each batch in
opposite order.
*Proof.* Fix M with |M| = m. The following moves do not depend on h, and none
of them increases sum over M of h(a_i + b_j) for any convex nondecreasing h.
(1) Replace a used A-service by an unused one with a smaller draw, keeping its
partner; this is fine because h is nondecreasing. Repeat until the used A-set
is the m smallest (fixed tie-break), then do the same for B. (2) In order of
increasing a, whenever two adjacent pairs have B-partners in increasing order,
swap the partners. With u <= u' and v <= v', the arguments u + v' and u' + v
lie between u + v and u' + v' and have the same sum, so convexity gives
h(u + v') + h(u' + v) <= h(u + v) + h(u' + v'). Each swap removes one
inversion, so step (2) ends at the opposite order, which is M*_m. Taking
h(x) = (x - B - y)_+ for each y >= 0 gives phi_{M*_m}(y) <= phi_M(y) for all y,
and Thm 3(a) applies. []

**Conjecture 3.2'.** Cor 3.2 holds without terminal adequacy. Evidence:
`test_T1b_complete_graph`, random complete instances (n_A, n_B <= 3,
T1, T2 <= 3, binding terminal per-bus caps in about 60%), with no layer in
which the sorted matching fails (counts in the log). In development, 6,000
instances also gave 0 failures. The proof above does not cover this case,
because terminal per-bus limits see pair sums and not only requirements.

**Corollary 3.3 (one-fee bound under 3.1 or 3.2).** Suppose the terminal is
adequate and either pi_min >= max edge requirement, or Gamma is complete.
Then D - CH <= f(t - floor t) < f for every proper closed convex slot cost.
*Proof.* Each A(M) lies in its representative's set, so the hull of all
physical points equals the hull of the representatives' sets. By Thm 3 the
representative's set is {box, total, e(T1 \ D1) >= phi*_m(pi(D1)),
upper constraints independent of m}, where phi*_m(y) = min over |M| = m of
phi_M(y). Here the representative attains the minimum for every y in Y.
Under Cor 3.1 both sides are 0 for y >= pi_min, and r_m at y = 0. Under
Cor 3.2 this holds for all y. For fixed y, m -> phi*_m(y) is the min-cost
matching value of cardinality m with battery B + y, so it is nondecreasing
and discretely convex by the paper's App. A argument with B replaced by
B + y. Lemma B and Lemma A finish the proof. Checked by
`test_T1b_cor31_and_mixing` and `test_T1b_complete_mixing`. []

### Counterexamples

**Example 1 (no dominating matching; adequate terminal; smallest).**
B = 10, A draws a = (5, 7), B draws b = (7, 5, 6). Gamma is the path
B1-A1-B2-A2-B3, with edges (A1,B1), (A1,B2), (A2,B2), (A2,B3) and edge
requirements 2, 0, 2, 3. Two early slots with per-bus cap pi = (2, 2), for
example p = 2 kW and 1 h slots; aggregate caps 10 (C = 5 plugs). One terminal
slot with per-bus cap 10 = B and aggregate cap 100. Then S_0 = 30. The size-2
matchings are
 M1 = {(A1,B1), (A2,B2)}: requirements (2, 2), r = 4;
 M2 = {(A1,B2), (A2,B3)}: requirements (3, 0), r = 3 = r_2;
 M3 = {(A1,B1), (A2,B3)}: requirements (3, 2), r = 5.
Here Y = {0, 2, 4}, phi_{M1} = (4, 0, 0) and phi_{M2} = (3, 1, 0) on Y. The
point (e1, e2, l) = (4, 0, 26) lies in A(M1) but not in A(M2): the 3-unit bus
needs at least 1 in each early slot. The point (2, 1, 27) lies in A(M2) but
not in A(M1), whose early total must be at least 4. Both memberships are also
confirmed by the flow check. M3 is dominated by both. So no size-2 matching
dominates, and since the r_2-minimizer M2 does not, no refinement of the r_m
order can help.
Linear prices (e1, e2, l) = (0, 10, 1) give minimal energy bills
M1: 26, M2: 35, M3: 35. Prices (5, 5, 0) give M1: 20, M2: 15, M3: 25 (see
the log). Each of M1 and M2 is strictly worse than the other at some price,
so no size-2 duty set is price-independent even for linear prices (Thm 5).
*Minimality (adequate terminal).* (i) For m = 1, phi_M(y) = (lam - y)_+
increases in the scalar lam, so the edge with the smallest requirement
dominates. (ii) With one early slot every feasible bus has lam_v <= pi_1, so
phi(pi_1) = 0 and only r_m matters. (iii) With n_A + n_B = 4 and m = 2 the
graph must be K_{2,2}, where Cor 3.2 applies; the other 4-service graphs have
at most one size-2 matching. So a counterexample needs m >= 2, T1 >= 2 and at
least 5 services, and Ex. 1 meets all three bounds.

**Example 2 (binding terminal limits; 4 services; one early slot).**
B = 6, a = (4, 1), b = (1, 6), Gamma = {(A1,B1), (A1,B2), (A2,B2)} (a path).
One early slot with pi = 1 and kappa = 10. Two terminal slots with per-bus caps
(5, 1) and aggregate caps (9, 11). The feasible size-1 matchings are
{(A2,B2)} (pair draw 7, requirement 1) and {(A1,B1)} (pair draw 5,
requirement 0). {(A1,B2)} needs 4 > pi. Neither set contains the other;
witness points are in the log and are confirmed by the flow check. In
development, a random search of 20,000 instances with n_A + n_B <= 4 found
failures only with 4 services.
Three services cannot work when n_A = 1: pairing the smallest feasible b
dominates (proof: the requirement is smaller; the A bus keeps its early
profile; the terminal profiles u of the paired bus and v of the B-only bus
are replaced by theta u + (1 - theta) v and theta v + (1 - theta) u with
theta = (a - x)/(a - x + b2 - b1), which have the required sums and respect
every per-slot cap). Checked by `test_T1b_nA1`. For n_A = 2, n_B = 1 an
exhaustive grid (B <= 3, all draws, T1, T2 <= 2, all per-bus caps <= B,
aggregate caps in {B, 2B, 3B}; 156,528 instances, `test_T1b_small_exhaustive`)
found no failure. That is evidence, not a proof, so the claim is "smallest
found".

**One-fee bound in Example 1.** Mixing (4, 0, 26) from M1 and (2, 1, 27) from
M2 with weights 1/2 gives z = (3, 1/2, 53/2) at mean count t = 2. z lies in no
size-2 set (checked exhaustively) but in the size-1 set of edge (A1,B2), which
has requirement 0. With F the indicator of {z}, which the paper's
Prop. onefee allows, D = f N_1 and CH = f N_2, so D - CH = f. For the smooth
strictly convex cost F_c(d) = c |d - z|^2: violated cuts show that the squared
distance from z to each size-2 set is at least 1/8 (values 1/4, 1/8, 9/4 in the
log). So for c >= 8f we get D_c = f N_1 (attained at z with m = 1) and
CH_c = f N_2 (the mixture). Hence D_c - CH_c = f exactly. The strict
inequality D - CH < f therefore fails for every f > 0, even for smooth
strictly convex supply costs.
**Surviving bounds.** (i) Always D - CH <= f t <= f nu. Splitting a pair into
two singles raises g pointwise; casework on whether pi'(D2) >= b gives
g_A + g_B >= g_pair for every D. So A(empty matching) contains every A(M)
(`test_T1b_pair_split`, any terminal and windows), and Lemma A applies to
the trivially nested family. (ii) Under Cor 3.3 the bound is < f.
**Conjecture 3.4.** In the plug model with a common window, D - CH <= f.
Evidence: `test_T1b_gap_search` (random two-point mixtures, n <= 8 services,
T1 <= 4). The largest t - kmax(z) observed is at most 1. Development runs
(6,000 + 3,000 instances) gave a maximum of 7/8 for fractional t, and exactly 1
only for integer t, as in Ex. 1.

---

## 3. T2: embedding in a depot

**Theorem 4 (embedding).** Let the tripper sub-fleet be a two-batch class
whose per-cardinality slot sets Lambda_m have MP (Thm 1; Cor 3.3; Thm 6). Let
the rest of the depot have decisions y in a convex set, convex cost c(y) and
affine slot load w(y). Examples: a base fleet with fixed duties and convex
charging constraints; fixed stationary loads; PV with curtailment; a
stationary battery in the usual LP form with efficiencies, where simultaneous
charge and discharge in a slot is realized by intra-slot alternation as in the
paper. Let the coupling be any convex constraint on (z, y). Examples:
per-slot site or transformer caps on z + w(y); a pooled connector shared with
base buses, z_t + w^bus_t(y) <= K_t; shared serial connector time
z_t / P + sum_b w_{b,t}(y) / p_b <= h_t when every tripper bus accepts the
connector power P. Add a proper closed convex grid cost F(z + w(y)). Then
 (a) for every fixed y the tripper's attainable z at cardinality m is
     Lambda_m intersected with the coupling, so restricting to the
     representative matching loses nothing, for every price or cost;
 (b) for the whole system, D - CH <= f(t - floor t) < f.
*Proof.* (a) The coupling and F see the tripper only through z, and for each
cardinality the attainable z form the representative's set. (b) Lemma A with
Kc = {(z, y): coupling}. The pooled connector cap is moved from Lambda_m into
the coupling: Thm 1 holds with K_t = +inf, and the cap becomes a convex
coupling constraint. []

**What breaks it (verified).**
1. *Coupling through per-bus tripper quantities.* If tripper buses have
   acceptance limits that bind (shared plugs with per-bus limit p and pi_t
   below the requirements), the tripper class itself loses dominance and the
   strict one-fee bound (Ex. 1, Ex. 2). Embedding cannot repair this. Serial
   connector time is harmless exactly when it is linear in the aggregate
   tripper energy.
2. *A second nonconvex class with a different window* (Example 3,
   `test_T2_two_classes`). Two tripper classes each have one A and one B
   service of draw 1 and battery 1. Class 1 can pair-charge only in early slot
   1 and class 2 only in early slot 2; there are no cross pairs. The cost is
   F = 0 if e_1, e_2 <= 1 - eps and +inf otherwise, with a free terminal. Each
   class alone satisfies the one-fee bound. Hull: each class mixes its paired
   plan (weight 1 - eps) with its two-singles plan, for a total fee
   2f(1 + eps) above the common 2f. Physical: every plan with a pair has
   e_t >= 1 in that pair's slot (checked), so no class can pair, and the
   physical fee is 4f. Hence D - CH = 2f(1 - eps), which exceeds f for
   eps < 1/2 and tends to the Shapley-Folkman bound 2f of Section 6.
3. *A nonconvex rest of depot* (binary battery modes, minimum stable power,
   unit commitment): the gap then includes the rest's own nonconvexity.

---

## 4. T3: when can duties be chosen before prices?

Let Mcal be a finite family of duty sets. Duty set M has a compact nonempty
set S_M in R^T of attainable load vectors and a fee phi_M. For a cost F put
V(F; R) = min over M in R of [phi_M + min over S_M of F]. A subfamily R is
*sufficient* for a class of costs if V(F; R) = V(F; Mcal) for every F in the
class. Write X_M = S_M x {phi_M}.

**Theorem 5.**
(a) *Linear prices on all of R^T.* R is sufficient iff for every M,
    X_M lies in conv(union over M' in R of X_{M'}) + ({0} x R_+).
    A single M* is sufficient iff phi_{M*} <= phi_M and S_M is contained in
    conv S_{M*} for every M. At a common fee this reads: conv S_{M*} contains
    every S_M.
(a') *Nonnegative prices* (p >= 0): the same, with {0} x R_+ replaced by
    R^T_+ x R_+. M* must then match every load of M componentwise from below.
(b) *Convex costs.* This covers any class containing c |. - e0|^2 for all
    c > 0 and e0, for example all finite convex costs or all strictly convex
    quadratics. R is sufficient iff for every M and every e0 in S_M there is
    M' in R with e0 in S_{M'} and phi_{M'} <= phi_M. A single M* is
    sufficient iff phi_{M*} <= phi_M and S_M is contained in S_{M*} for all M.
    For nondecreasing separable convex costs, replace "e0 in S_{M'}" by
    "S_{M'} meets e0 - R^T_+".
(c) *Cardinality structure.* Let phi depend only on |M| = m, strictly
    decreasing, and let R hold one M*_m per m. For convex costs R is
    sufficient iff every S_M with |M| = m is covered by the union of
    S_{M*_{m'}} over m' >= m. When the representatives are nested, as in
    Thm 1, this is exactly S_M contained in S_{M*_m}: per-cardinality
    dominance is necessary and sufficient. For linear prices the condition is
    weaker, because mixtures of neighbouring representatives with mean fee
    phi_m may cover S_M. The exception is the largest cardinality, where it is
    again S_M contained in conv S_{M*_nu}.
*Proof.* (a) Let X_R = conv(union over R of X_{M'}) + {0} x R_+; it is closed
and convex (a compact hull plus a closed cone). For p in R^T,
V(p; R) = min over X_R of p.e + c. A linear function attains its minimum over a
hull at a generating point, and upward cost directions do not lower it. If
every X_M lies in X_R then V(p; Mcal) >= V(p; R), and R in Mcal gives
equality. Conversely, let e0 be in S_M with (e0, phi_M) outside X_R. Strict
separation gives (p, beta) and gamma with p.e0 + beta phi_M < gamma <=
p.e + beta c on X_R. The cone {0} x R_+ forces beta >= 0. If beta > 0, scale to
beta = 1: V(p; Mcal) <= p.e0 + phi_M < V(p; R). If beta = 0, then p.e0 is
below the minimum of p.e over conv(union over R of S_{M'}). At price lambda p,
V(lambda p; Mcal) <= lambda p.e0 + phi_M, while V(lambda p; R) >=
lambda min p.e + min over R of phi, which is larger for large lambda. Either
way R is not sufficient. For a single M*: X_M lies in
conv(X_{M*}) + {0} x R_+ iff S_M lies in conv S_{M*} and phi_M >= phi_{M*}.
(a') Same proof; the separating (p, beta) now lies in the dual cone of
R^T_+ x R_+, so p >= 0.
(b) Sufficiency: an optimal (M, e0) for F is matched by some M' in R with the
same load and a fee no larger. Necessity: suppose (M, e0) has no such M'. For
each M' in R, either phi_{M'} > phi_M, or e0 is not in S_{M'}, and then
dist(e0, S_{M'}) >= delta > 0 because there are finitely many closed sets.
With F_c = c |. - e0|^2, V(F_c; Mcal) <= phi_M, while V(F_c; R) is at least
min( min{phi_{M'} : phi_{M'} > phi_M}, min over R of phi + c delta^2 ), which
exceeds phi_M for large c. For the monotone version use
F_c(e) = c sum_t ((e_t - e0_t)_+)^2.
(c) By (b), the M' must have fee <= phi_m, that is, m' >= m. With nested
representatives the union is S_{M*_m}. For linear prices at the top
cardinality, any mixture with fee <= phi_nu uses only generators with fee
phi_nu. []

*Consequences for the paper.* Under Thm 1 every S_M is convex. So at a common
fee, "price-independent for linear prices" and "for convex costs" coincide.
Theorem projection gives the "if"; Thm 5(c) gives the "only if": without
per-cardinality containment, some smooth strictly convex cost makes every fixed
representative family strictly suboptimal. In the plug model (Ex. 1) the
sets are convex and incomparable, so no size-2 duty set is optimal for every
linear price.

---

## 5. T4: staggered availability

*Model.* The A runs still share a common instant, as do the B runs, so a bus
serves at most one of each. A run i ends at slot boundary e_i and B run j
starts at s_j. A paired bus (i, j) can charge only in early slots
e_i <= t < s_j, and an A-only bus in slots t >= e_i. Compatibility is
e_i <= s_j. The connector is pooled (per-bus cap = K_t) and the terminal
window is common. Thm 2 applies with windows W_v. With pi = kappa the per-bus
caps are redundant (each c_{v,t} <= e_t <= K_t), and the description reads
e(J) >= sum over paired v with W_v in J of lam_v and
e(D1) <= sum over A-buses v with W_v meeting D1 of hi_v, plus the box and the
total.

**Theorem 6 (homogeneous energies).** Let all A draws equal a and all B draws
equal b, so lam = (a + b - B)_+, and let Gamma be the time-compatibility
graph (e_i <= s_j). For each m with a compatible size-m matching, let FIFO_m
pair the m earliest-ending A runs with the m latest-starting B runs,
earliest end with earliest start among them. Then
 (i) A(FIFO_m) contains the set of every compatible size-m matching;
 (ii) the representatives have MP, so D - CH <= f(t - floor t) < f for every
     convex slot cost (pooled connector, so the terminal needs no adequacy
     condition).
*Proof.* Let cont_J(W) = 1[W in J], which is supermodular in W, and
meet_J(W) = 1[W meets J], which is submodular in W. Then
Low_M(J) = lam times the sum of cont_J over paired windows, and
Up_M(D1) = a times the sum of meet_{D1} over A-bus windows. It suffices to
show that the following moves keep compatibility, weakly lower every Low,
weakly raise every Up, and reach FIFO_m from any compatible M.
(1) Replace a paired B run j by an unused j' with s_{j'} >= s_j. The paired
window grows, so cont goes down and meet goes up.
(2) Replace a paired A run i by an unused i' with e_{i'} <= e_i, keeping the
partner. The windows I1 = [e_i, s_j) and I2 = [e_{i'}, T1) become
I1' = [e_{i'}, s_j) and I2' = [e_i, T1), with I1' u I2' = I2 = I1 u I2 and
I1' n I2' = I1 = I1 n I2. Submodularity of meet gives meet(I1') + meet(I2')
>= meet(I1) + meet(I2), and the paired window grows.
(3) Uncross nested pairs. If e_i <= e_{i'} and s_{j'} < s_j, replace (i, j)
and (i', j') by (i, j') and (i', j). The windows X = [e_i, s_j) and
Y = [e_{i'}, s_{j'}), with Y in X, become X' = [e_i, s_{j'}) and
Y' = [e_{i'}, s_j), with X' u Y' = X and X' n Y' = Y (using e_{i'} <= s_{j'}).
Supermodularity of cont and submodularity of meet give the inequalities. Each
swap removes one inversion of the partners' start times in end order.
(ii) Sort A by end and B by start. FIFO_m gives pair k the window
[e_k, s_{n_B - m + k}). For a maximal run [x, y] of J in boundary coordinates,
the number of FIFO windows inside it is
#{k : e_k >= x, n_B - m + k <= beta(y)} = (m - (n_B - beta(y)) - k0(x) + 1)_+,
which is convex and nondecreasing in m. Distinct runs are disjoint, so Low_m(J)
is convex and nondecreasing. Empty windows can only matter when lam = 0,
because a nonempty layer with lam > 0 has none; FIFO windows shrink as m grows,
so a smaller cardinality has none either. For Up, count the A-bus windows that
miss D1, that is, lie inside a maximal run of its complement, with degenerate
runs at boundaries between two slots of D1. Runs not touching T1 contain only
paired windows, a count that is convex in m as above. The final run [z, T1]
contains the paired windows with e_k >= z and k <= m and the A-only windows
with e_k >= z and k > m, together #{k : e_k >= z}, which does not depend on m.
So Up_m is concave and nonincreasing, and Lemma B gives MP. []
Checked by `test_T4_homogeneous` (random instances with general staggering,
zero caps allowed): FIFO dominates every nonempty layer and MP holds. The
rule earliest-end-with-latest-start fails (it is incompatible or not
dominating) in a positive number of layers (log).

**Example 4 (heterogeneous energies, no dominating matching; smallest).**
One A run (a = 1, ending at boundary 0) and two B runs b = (1, 2) starting at
boundaries 0 and 1. B = 2, one early slot with K = 5, adequate terminal.
Compatibility is complete (0 <= 0 and 0 <= 1). Pairing with B1: requirement 0,
but the window is empty, so the A bus cannot charge before the afternoon and
the early load is 0. Pairing with B2: requirement 1 in the single slot, so the
early load is 1. The two size-1 sets are disjoint. Smallest: a single A and a
single B have only one matching, and two size-1 matchings need a second
service in one batch, so at least 3 services and 1 slot are needed.
*Loss.* Commit to one size-1 matching before prices, and choose between it and
the all-singles plan (which contains everything) after prices. At early-minus-
terminal spread pi, with fee f, the worst regret of the better commitment is
exactly min(|pi|, f) (checked at spreads -3, -1/2, 1/3, 2 with f = 1). The loss
grows with the price spread until it reaches one fee, and fee fallback caps it
at f. Mixing the two size-1 points gives e = 1/2, which lies only in the
size-0 layer, so D - CH = f.
Random search (`test_T4_complete_compat_search`): with heterogeneous energies
and complete time-compatibility, a positive fraction of nonempty layers have
no dominating matching (log); in development, 318 of 3,645.

**Example 5 (staggering breaks the one-fee bound by any multiple).** For
k >= 1 let B = 2k + 2. A run i ends at boundary i - 1 and B run j starts at
boundary j, for i, j = 1..k. Draws are a_i = B/2 - (1 - delta) i and
b_j = B/2 + 1 + (1 - delta) j with 0 < delta < eps. Slot caps are 10 and the
terminal is adequate. Gamma is the time-compatibility graph, which is complete
for k <= 2. The requirement of (i, j) is 1 + (1 - delta)(j - i). Pair (i, i)
needs 1 in its own slot. Pair (i, j) with j > i needs more than
(j - i + 1)(1 - eps) in its j - i + 1 slots. Pair (i, i - 1) has an empty
window and requirement delta > 0, so it is infeasible. The hull point mixes the
k-pair diagonal plan (each pair charging 1 in its slot) with weight 1 - eps and
the no-pair plan with weight eps. That point has e_t = 1 - eps in every slot
and lies in no layer except m = 0. So with F the indicator of that point,
D - CH = k(1 - eps) f. `test_T4_example5` checks k = 1..4 with eps = 1/10 and
delta = 1/20 exhaustively over all matchings: (D - CH)/f = 9/10, 9/5, 27/10,
18/5. Hence, with staggering, D - CH is not bounded by any fixed multiple of
f; the general bound D - CH <= f t <= f nu holds (pair splitting).
**Open.** Whether D - CH <= f min(nu, T1) under staggering.

---

## 6. T5: relation to Shapley-Folkman

**Shapley-Folkman lemma (Starr).** Let S_1, ..., S_k lie in translates of a
common d-dimensional linear subspace, and let z be in conv(S_1 + ... + S_k)
= conv S_1 + ... + conv S_k. Then z = sum z_i with z_i in conv S_i, and at most
d indices have z_i outside S_i.
*Proof.* Write z = sum_i sum_j mu_ij s_ij, with sum_j mu_ij = 1. After
translation, the vector (z, 1, ..., 1) in R^{d+k} is a nonnegative combination
of the vectors (s_ij, e_i). By Caratheodory's theorem for cones, it is a
nonnegative combination of at most d + k of them, still with sum_j mu_ij = 1
for each i. Each i uses at least one, so at most d use two or more. []

**Proposition 7.**
(a) Let k independent two-batch classes, each with its own windows, connector
and fleet, and with per-cardinality layers that have MP and fee f_i, be
coupled only through a proper closed convex cost F of the total slot vector
in R^T. Then D - CH is at most the sum of the min(k, T) largest f_i. Example 3
(k = 2, T = 3) attains 2f in the limit, so the bound is sharp.
(b) For one fleet, the Shapley-Folkman route gives nothing beyond the one-fee
bound and does not imply it.
*Derivation.* (a) Class i's image P_i (load, cost closed upward) lies in
{1^T u = S_{0,i}/alpha} x R, a translate of a T-dimensional subspace, because
each class's total energy is fixed. So d = T. Write the hull optimum as
(u, c) = sum (u_i, c_i) with (u_i, c_i) in conv P_i; by the lemma at most T
classes have (u_i, c_i) outside P_i. For each of them, Lemma A applied to the
class alone gives a physical point with the same u_i and cost below c_i + f_i.
This per-unit excess is the Aubin-Ekeland nonconvexity rho_i of the class.
Summing gives the bound; the loads, and hence F, are unchanged.
(b) The lemma needs units whose images add up to the plan set, and a per-unit
nonconvexity rho_i: the cost of replacing a unit's hull point by a physical
point with the same coupling coordinates. For one two-batch fleet the only
such unit is the fleet itself, and its rho is exactly what the one-fee bound
estimates; SF takes rho as an input. Splitting the fleet into buses or duties
does not help. Those units are coupled by the n_A + n_B service-coverage
equalities, which become coupling coordinates, so d = T + n_A + n_B. A duty's
coverage vector takes only the values 0 and 1, so a fractional hull point
cannot be replaced by a physical one with the same coverage coordinates:
rho_i = +inf, and the estimate is vacuous. The one-fee bound comes instead from
the integrality of the bipartite min-cost-flow structure: r_m is the integer
restriction of a convex function, so mixing cardinalities costs at most one
fractional pair. Combining SF with that per-class fact gives (a), which is
sharp. Example 5 also shows that inside one staggered fleet the gap can grow
like k f: there the fleet is a single non-separable unit whose rho is no
longer below f. []

---

## 7. Attacks and exact checks performed

Edge cases exercised in the tests: empty layers (requirements above window
capacity; infeasible pairs with empty windows); zero capacities (K_t = 0,
small pi_t); ties in draws and requirements; unequal batch sizes (n_A != n_B
in every random family); incomplete graphs (random edge sets). The code uses
alpha = 1; a common alpha is a rescaling, as argued in the text. Randomized
families use fixed seeds; counts are printed in the log. The cut formula used
by most tests is validated against an independent flow computation, so the
dominance tests do not rest on the formula they test.

## 8. Re-checks of the paper

Re-derived while building on them, and found correct: Theorem projection
(charge-only reduction); discrete convexity of r_m via min-cost flow (used
here with B + y); the sorted-matching exchange argument (used here for every
B + y in Cor 3.2); Prop. onefee and its sharpness example (Lemma A abstracts
it). No error was found.
