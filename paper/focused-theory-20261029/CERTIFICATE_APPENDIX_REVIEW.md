# Independent algebra review of the certificate appendix

Reviewed `certificates.tex` as manuscript mathematics only. No checker/source reaudit, numerical work, imports, tests, hashes, execution or commits were performed.

**Outcome: algebra and scope are correct; no required mathematical correction found.**

For a symmetric positive-semidefinite Q, convexity gives the tangent plane c0−zᵀQz/2+(c+Qz)ᵀx at any rational z. The point need not be feasible. With Ax≥b and λ≥0, subtracting λᵀ(Ax−b) lowers that plane on feasible points; the equality term νᵀ(Ex−d) vanishes for arbitrary signed ν. The remaining coefficients are exactly r=c+Qz−Aᵀλ−Eᵀν. Minimizing each r_j x_j independently on its finite interval gives min(r_jℓ_j,r_j u_j). Thus the displayed constant, row-multiplier signs and finite-box correction are correct without exact stationarity or optimal multipliers. Taking Q=0 yields the linear specialization.

For infeasibility, multiplying the inequalities by λ≥0 and adding unrestricted equality multiples gives (Aᵀλ+Eᵀν)ᵀx≥bᵀλ+dᵀν. A strict contradiction against the maximum over the finite box excludes every feasible point. The direction and strictness of this comparison are correct. A native status alone supplies no such proof.

The binary 0/1 children cover their parent's integer domain. Complete inherited-domain coverage plus a valid bound or contradiction for every fringe region gives the minimum fringe lower as an integer-plan lower. It need not identify an optimum, and weak complete coverage does not imply target separation. These distinctions are stated correctly.

The exactly-two-bus tree is correctly restricted to its physical root domain. The separate low-count obstruction and three-plus floor are needed before calling the result global physical D. Neither that tree nor its fleet-count exclusion constrains convexified fleets to two buses. An admitted complete-plan mixture supplies a CH upper, and only a strict global physical lower above it proves D>CH. The appendix does not incorrectly promote the quadratic tree lower into a CH lower.

Optional clarity only: “Q≽0” conventionally denotes a symmetric PSD matrix; adding “symmetric” is harmless if the intended audience may not know this convention. Likewise, “sign-invalid multiplier cannot be accepted” should be understood as referring to the accepted λ after any explicit sign normalization/projection, rather than an assertion that raw native multipliers themselves must all pass. Neither point changes the formulas.

The independent-implementation paragraph appropriately distinguishes exact internal checks from external replication and empirical calibration. Attribution as a classical construction is proportionate.
