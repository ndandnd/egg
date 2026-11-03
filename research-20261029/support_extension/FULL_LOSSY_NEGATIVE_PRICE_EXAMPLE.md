# Complete projection versus the efficient set at a negative price

PASS. Symbolic analytical check only, without execution, data, imports, hashes or tests. Parameters are n=1, B=1, a=b=3/4, alpha=1/2, delta=1, K=2, H=3, f=2, with the full finite-cycling assumptions. The query is the fixed posted price p=(−3,1), with symmetric signed early settlement. It is not a positive planner-gap example.

## A finite physical witness

For the paired one-bus assignment, choose C=11/6 and X=1/6. Then

`Q=C/2−X=3/4`, `E=C−X=5/3`, `L=3−2Q=3/2`, `c=2`.

Early gross energy is2. After A, inventory is1/4. First purchase1/3 grid units, storing1/6, then export1/6, returning inventory to1/4. This neutral cycle stays within capacity. Next purchase3/2 grid units, storing3/4 and reaching full. B leaves inventory1/4, and terminal purchase3/2 restores full. The three early action durations at grid power2 sum to one; terminal charging at power3 takes half its window. Thus the witness is finite, respects the shared connector, and does not rely on simultaneous import/export or inventory credit.

## Exact minimization over both complete polygons

For m=1, the polygon is

`C>=1`, `X>=0`, `C+X<=2`, `1/2<=C/2−X<=3/4`.

The private score c−3E+L is `5−4C+5X`. At fixed C it is minimized by the smallest feasible export,

`X=max(0,C/2−3/4)`.

For1<=C<=3/2 this is0, and for3/2<=C<=11/6 it is C/2−3/4. These choices satisfy the lower-Q bound; gross power supplies the final upper endpoint11/6. On the two pieces the objective has slopes−4 and−3/2 in C, respectively. It therefore has its exact minimum at the displayed witness, with value−3/2.

For m=0, the two-bus polygon has C>=0 and0<=C/2−X<=3/4, with the same gross constraint. The terminal cap, rather than the raw T=−1/2 bound, gives Q>=0. Its objective is `7−4C+5X`. The same minimum-export choices are feasible on0<=C<=11/6; both pieces decrease strictly and give minimum1/2. Consequently the complete whole-problem price-response value is exactly−3/2, attained on m=1. Capped identical idles add no alternatives outside this full projection by the reviewed deletion corollary.

## What the efficient reduction misses

The previously reviewed efficient curves are m=0 with E in[0,3/2], L=3−E,c=4, and m=1 with E in[1,3/2], L=3−E,c=2. Their scores are7−4E and5−4E. Their minima are1 and−1, respectively, so minimizing only over Z gives−1 instead of−3/2. The extra neutral cycle raises net early purchases while leaving Q and terminal refill fixed; the negative early rate rewards precisely the action that monotone economics would discard.

This verifies the need to retain the full polygons for negative prices. It does not contradict the earlier monotone-objective theorem. Since the query objective is linear, minimizing it over the complete physical union or its complete-plan hull gives the SAME value−3/2: D=CH for this objective. No positive-gap, tariff-equilibrium, empirical or public-V2G conclusion is being made.

## Current TeX statement review

The current `full_lossy_projection.tex` accurately includes the essential assumptions: B>0/nonempty fleet, common availability and both-direction acceptance, arbitrary finite action count, zero switching/minimum-session/throughput/degradation costs, and economics depending only on period aggregates and vehicle cost. Its necessity and finite-cycle construction cover empty/full early inventory and zero-power cases; terminal nonnegativity follows from Q<=P<S under the inherited positive B-service assumptions. Replacing the two fixed Q lower bounds by their maximum is legitimate. There are exactly five planar halfspaces, so the compact polygon/at-most-five-vertices statement and affine-image hull construction are valid, including lossless dimensional collapse. The idle corollary correctly retains zero-transition and identical-access assumptions.

No mathematical correction or missing premise requiring TeX edits was found. The section's inheritance of the preceding common-loss model is important: terminal charging remains charge-only with the same efficiency and common full-refill access, and the cycle construction is not a claim about time-resolved intrawindow objectives. The stated lack of fresh full-polygon implementation qualification and public-timetable V2G evidence is appropriate.
