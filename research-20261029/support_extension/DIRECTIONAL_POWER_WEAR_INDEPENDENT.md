# Directional powers and affine wear: independent analytical review

**PASS with an essential extended-coordinate qualification.** Common unequal charge/export powers and common affine throughput wear preserve the exact minimum-requirement polygon reduction. In the lossless case, however, wear cannot generally be inferred from net loads alone. This is an independent analytical check without execution, data, imports, tests, hashes, other agents' notes or numerical qualification.

## Exact polygon and assumptions

Retain the full finite-cycling model's battery/endpoint boxes, B>0, a nonempty used fleet, common0<alpha,delta<=1, zero switching/session time and no positive minimum session. Every bus is available for the entire early window and accepts grid-side charging power K_c>0 and export power K_e>0. One shared connector serializes both directions. Terminal charging retains its common charge-only access/efficiency and budget H. Costs of actions depend only on their aggregate purchased/exported/terminal energies, with coefficients common to all buses and clocks.

For a fixed matching, define R,T,P,S,N as in the full-projection proof. Its complete early aggregate polygon is exactly

`C>=R/alpha`, `X>=0`, `C/K_c+X/K_e<=1`,

`max(T,S−alpha H)<=Q=alpha C−X/delta<=P`.

These are five halfspaces in(C,X). They give C,X>=0 and boundedness C<=K_c, X<=K_e; the polygon may be empty, a point or a segment. Necessity follows from individual endpoint SOC, mandatory purchases, full replenishment and total connector time. The lower terminal inequality already includes L<=H, while L=(S−Q)/alpha>=0 follows from the box upper endpoints (in the stated positive-B-service model, P<S).

For sufficiency, choose the same independent one-direction exchange vector at Q with positive battery total A=max(R,Q). It uses C0=A/alpha and X0=delta(A−Q). Every proposed polygon point has z=C−C0>=0 and X−X0=alpha delta z. Neutral cycles on one existing bus realize these residuals; then execute all baseline actions. At charge power K_c and export power K_e, the resulting COMPLETE action list takes precisely C/K_c+X/K_e<=1. Thus unequal directions require no new SOC restriction. Terminal refill is unchanged and serializes independently. This construction uses actual directional durations, not the incorrect surrogate gross bound C+X<=max(K_c,K_e).

At a fixed cardinality, only R changes between matchings; the other statistics and fee do not. The matching attaining r_m reproduces exactly the SAME C,X,Q,E,L as every other matching. The complete union over cardinalities and its exact convex hull therefore remain correct. For a common transition consumption d, the same statement applies cardinality by cardinality with S_m=S+md and admissible b_j+d<=B; no minimum-R substitution between different cardinalities is being asserted.

## Common affine wear

With vehicle fee fN, replace the cost image by

`c=fN+w_c C+w_d X+w_t L`, `E=C−X`, `L=(S−Q)/alpha`.

This is an affine image of the SAME polygon. Consequently its at-most-five vertices generate the full projected load/cost polygon, and the finite union of their images generates the complete-plan hull. The common affine wear values are reproduced exactly by the minimum-R matching because it reproduces the same C,X,L. Nonnegative wear coefficients are physically natural, but the algebraic equality itself holds for any fixed finite coefficients; it does not rely on economic monotonicity. Convex supply planning remains convex on each affine-image polygon and on the hull.

The claim fails without the appropriate common-cost assumption: heterogeneous per-bus wear, session fees, degradation depending on SOC/path or cycle count, different directional acceptance/availability, or time-varying intrawindow coefficients can make aggregate C,X insufficient. A fixed action-count restriction below the constructive bound discussed below also needs a new feasibility argument.

## Lossless load/cost ambiguity

When alpha delta=1 under the admitted efficiency range, alpha=delta=1, Q=E and L=S−E. Neutral cycles change C and X equally, leaving both loads fixed, but change wear by `(w_c+w_d)z`. Thus net loads determine wear only when w_c+w_d=0, or when another restriction selects a unique gross allocation. With nonnegative wear coefficients this normally requires both early wear coefficients to vanish. Terminal wear remains determined by L.

A concrete example is n=1, B=1, a=b=1/4, alpha=delta=1, K_c=K_e=1, H=1, with one paired bus and w_c=w_d=1. Both C=X=0 and C=X=1/4 are feasible. The latter uses a finite depth1/4 cycle starting at post-A SOC3/4, takes early time1/2, and returns to that SOC. Both points have E=0 and L=1/2 and the same fleet, but their wear costs differ by1/2. Therefore a proposed lossless formulation keeping only E,L and the constant vehicle fee would be FALSE. Keeping the affine COST IMAGE of the C/X polygon is exact, even when its load-only image collapses to a line. Replacing it by minimum wear would preserve some monotone-in-cost objective values, not the COMPLETE joint projection.

## Explicit finite action bound

Use the conservative construction that cycles on one bus initially at s. If s<=B/2, charge first; otherwise discharge first. Every cycle with battery depth at most B/2 is feasible and returns to s, including s=0 or B. The residual battery throughput is alpha z, with z<=C<=K_c. It needs no more than

`J=ceil(2 alpha K_c/B)`

cycles (zero residual needs none), hence at most2J cycle actions. Each of the N buses needs at most one nonzero baseline early action, and at most one terminal charge. Therefore a uniform bound valid for EVERY attainable aggregate point is

`early actions <= N+2 ceil(2 alpha K_c/B)`,

`all charging/export actions <= 2N+2 ceil(2 alpha K_c/B)`.

With total fleet cap2n, replace N by2n to obtain bounds4n+2ceil(2alpha K_c/B) for all actions and2n+2ceil(2alpha K_c/B) for early actions. Mandatory service/transition tasks are not counted as charge/export sessions. Zero-energy actions are omitted; adjacent actions could be merged, but the upper bound does not require doing so. The absence of K_e from the COUNT bound is legitimate: it changes export duration, while the feasible time inequality already enforces that the constructed list fits. It does not bound computational effort or the description bit length of all schedules.

Enforcing a global EARLY-action cap at least the stated early bound preserves the complete aggregate projection: every formerly attainable point has the explicit schedule within that cap, and restricting schedules cannot add a point. The analogous statement holds for an all-charge/export-action cap at least the total bound. It does not preserve every original literal schedule, nor does it claim that the bound is minimal. The cap must be fixed using the instance's parameters (and N or its fleet upper bound), not chosen as a small universal constant across growing instances. Positive switching time, minimum duration, or a cost per action is a different model and does not follow from this count argument.

These are exact constructive results under the ideal shared-window model. They introduce no new numerical qualification, runtime advantage, empirical battery-wear calibration, public V2G or general scheduling-hardness claim.
