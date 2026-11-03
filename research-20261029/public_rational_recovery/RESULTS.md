# Rational recovery attempt01: admitted physical point and exact fixed-topology optimum

Source `425bf35452eb3f5444f20058ad6fd6b540ffed88`; control `869cae89` (parent-supplied). All three assigned states were DELIVERED, with no fatal exception and resource pass. Owner 73359 exited zero (parent-supplied); worker 54988 exited zero and was reaped.

| State | Scientific result |
|---|---|
| Q0 | PASS, ten literal checks and eight negative controls |
| PUBLIC_PRIMAL | ADMITTED_PRIMAL, exactly one independent physical replay |
| PUBLIC_DUAL | CERTIFIED_FIXED_TOPOLOGY_OPTIMUM, exact lower equals admitted physical upper |

The shared exact value is

`15487225773558335836678536516523969405935273717647515 / 35076039295941670036888435985190792471742381031424`.

This is a new exact physical upper for the original public case, and an exact charging optimum conditional on the selected topology. Its lower bound applies to that fixed topology only. It is not a lower bound for unrestricted physical planning or the complete-fleet hull, and it does not establish global own-price support. No native solve or price response was part of this package. The prior failed seeded-dual attempt remains failed and unchanged.

External meter reports 0.95 user + 0.10 sys = **1.05 CPU**, **1.14 wall**. Owner rusage is slightly larger at 1.061451 CPU; retained **1.07 CPU** covers both. These overlapping observations are not additive. The separate concurrent PDF render is excluded from this package and left to the parent for combined accounting.

Read only compact results/receipts and external meter; no public gzip, replay, hash or scientific recomputation. Ten/eight qualification success is asserted by the admitted worker's compact denominator and PASS gate; individual compressed Q0 records were not reopened.
