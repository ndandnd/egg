# Directional early power and affine throughput wear

**Status: PROVED under the full finite-action/common-window law, pending independent review.** Analytical source-only result; no numerical execution, tests, data, code, manifests or manuscript edits. The extension uses the same physical aggregation and classical affine-image/hull tools, not new generic storage or scheduling machinery.

## Precise model and projection

Keep the complete common-loss theorem's service graph, common capacity B>0, common alpha,delta in(0,1], full initial/terminal inventory, assigned nonempty fleet and common windows. Normalize the early window to duration1. Purchases use a common admissible connector power K_c>0 and exports K_d>0, with every bus accepting the corresponding directional power. One connector serializes both directions, with no switching time, setup/minimum session or finite cycle cap. Terminal charging retains its common resource budget H and efficiency alpha. This is a positive-directional-power corollary; it neither replaces nor silently divides by zero in the original zero-budget cases.

For cardinality m, N_m=2n−m, S=sum a+sum b, P=sum a and r_m the minimum matching requirement. The exact purchase/export polygon is

    C>=r_m/alpha,  X>=0,
    max(S−N_mB,S−alpha*H)<=Q=alpha*C−X/delta<=P,
    C/K_c+X/K_d<=1.

Let w_c,w_d,w_t be fixed common affine wear coefficients per GRID-energy unit. Nonnegative coefficients give their natural wear-cost interpretation; exactness itself does not require a sign restriction. The complete joint projection is the union of the affine images

    (E,L,c)=(C−X,(S−Q)/alpha,
             f*N_m+w_c*C+w_d*X+w_t*L).

The polygon still has five halfspaces, hence at most five vertices, with point/segment/empty degeneracies retained. Its affine image generates the complete-plan hull by ordinary vertex weights. This holds for arbitrary objectives on the projected quantities, including negative-price net-energy value queries, without imposing monotonicity to discard schedules. Bounded positive K_c,K_d make the feasible totals compact even if a coefficient is signed.

## Constructive proof and matching nesting

The endpoint battery boxes are unchanged. Therefore every physical allocation obeys C>=R/alpha and the displayed Q bounds for its actual matching. Shared occupancy is NECESSARY: purchases at power no greater than K_c occupy at least C/K_c time, exports at power no greater than K_d occupy at least X/K_d, and those periods cannot overlap on one connector.

Conversely, the same box allocation at a feasible Q realizes minimum-direction totals C0=max(R,Q)/alpha and X0=delta*(max(R,Q)−Q). Feasible C,X imply residuals z=C−C0>=0 and X−X0=alpha*delta*z. On any existing bus, choose charge-first cycles if its SOC<=B/2 and export-first otherwise. Chunks of battery depth at most B/2 return to that SOC without violating capacity. The finite total alpha*z requires finitely many chunks; z=0 requires none. Execute these cycles and the minimum-direction exchanges at their respective directional powers. Total early duration is EXACTLY C/K_c+X/K_d<=1, irrespective of the order and grouping of the finite actions. Thus all actions fit the common window while individual SOC remains feasible. No simultaneous charging/export or hidden switch time is assumed. Terminal refill is the unchanged serial construction, using total L<=H.

At fixed cardinality only the matching requirement R varies. All other polygon constraints, total energy and fee are common, so a matching attaining r_m contains every other matching's polygon at the SAME C,X. The constructed replacement therefore preserves E,L AND affine wear c exactly, not merely a lower net bill. This proves complete joint-set equality and its convex-hull consequence. If the common compulsory transition task d is also retained, the same proof uses S_m=S+md and the restricted graph b_j+d<=B; nothing else changes. Edge-dependent task energy would again break fixed-cardinality total-energy invariance.

## Wear must stay in the joint projection

It would be incorrect to keep c=fN and merely announce that throughput wear is covered by a net-energy objective. With alpha=delta=1, battery-neutral residual cycles add equal z to C and X, leave E and L unchanged, but change intrinsic wear by (w_c+w_d)z. Thus physical plans with the same loads can have different costs even at a fixed fleet size. The affine c coordinate above retains those layers; a net-load-only projection does not. The five-vertex conclusion concerns that FULL affine image, including any higher-cost points. They can be discarded only under a separately stated objective monotonicity/dominance argument. With genuine losses C,X can be recovered from E,L in this two-period model, but retaining their explicit affine map avoids relying on a nonexistent lossless inverse.

The convex hull must average actual complete-plan wear costs along with loads. It must not compute wear on a fictitious aggregate action after netting purchases and exports, drop an export term, or add a nonlinear cycle cost to averaged loads. Vehicle fee and wear are intrinsic to each physical plan; the convex supply term is evaluated at its mean grid load, as in the established planning framework.

## Limits

The result assumes common direction-specific powers, identical access and adequate directional bus acceptance; bus-dependent acceptance or efficiency needs new analysis. It covers affine ENERGY-throughput wear, not SOC/depth/rate-dependent degradation, charging-session fees, finite switching constraints, nonlinear wear, heat or other state history. A common power asymmetry changes occupancy geometry but does not model taper or charging competition at multiple stations. Intrawindow prices would require retaining timing, and asymmetric purchase/export settlement must retain the distinct C/X terms rather than claim it is a net-price query. The complete-set exactness does not imply the old efficient-envelope formula remains valid with these powers/costs; that would require a new derivation. No implementation qualification, empirical V2G relevance, runtime improvement, lossless scalar support transfer or broad novelty claim is supplied here.
