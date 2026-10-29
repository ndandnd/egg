# Independent parent review of the three-batch boundary

Reviewed the reduction separately from its author. No instance construction,
solver, enumeration, import, hash or new numerical qualification was executed.

PASS after making the encoding convention explicit: all service energies and
usable capacity are positive integers encoded in binary; the fixed connector
power is1 and times are rational/integer encoded quantities. The strong-hard
source restriction has polynomially bounded numerical magnitudes. The claim
must not classify an unspecified real-number input model as NP-complete.

Within each of the three batches, n positive-duration simultaneous services
and fleetcap n force exactly n buses and one service per bus per batch. With
no intermediate energy exchange, each duty consumes its three prescribed
energies and is feasible exactly when their sum is<=B. Positive consumption
makes prefix SOC constraints redundant given that total. The global sum nB
then forces every duty's inequality to equality. Conversely each numerical
three-dimensional matching gives a full feasible fleet, then one serial
terminal refill of B per bus over a length nB window. Initial battery energy
is fully repaid; terminal charging is not discarded from feasibility.

The source prechecks can be made a many-one reduction: map an unbalanced input
or an element>B to the fixed balanced NO instance n2,B4,A=(1,1),C=(1,1),E=(1,3).
Its total is8 but its only possible triple sums are3 or5. Thus restricting to
balanced positive inputs with each element<=B does not turn a source NO into
a spurious YES. The fixed obstruction is a proof example, not an executed
experimental case or evidence of empirical frequency.

The schedule certificate consists of two permutations; exact triple sums and
the explicit terminal serialization can be checked in polynomial time for
this restricted model. This does not assert NP membership of arbitrary
nonlinear charging or real-input scheduling problems.

The proposition supplies a concise explanation of why a third mandatory batch
can defeat pairwise matching, even with complete compatibility and ample
terminal charging. It is a classical scope boundary, not a new general EVSP
hardness claim, a hardness theorem for price support, or an ML contribution.
It should occupy a short appendix proposition and one body sentence, not
compete with the actual frontier/support result in the contribution list.
