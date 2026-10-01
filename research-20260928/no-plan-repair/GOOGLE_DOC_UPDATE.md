## Handling incomplete pricing calls — 28 September 2026

The three failures in the completed 32-calculation comparison exposed the same
software assumption: a physical pricing call was expected to return a new fleet
plan even when the solver had found none. The repair addresses this path in the
compact wrapper and shared coordinator. A correctly identified unresolved call
without a plan can end normally, preserving earlier verified bounds and feasible
mixtures. It supplies no new plan or certificate. Successful returns still need
a valid witness, and invalid present witnesses remain rejected.

The repair passed 156 focused regression tests, including preservation of an
earlier bound, no certification from cached evidence alone, and compatibility
with the strict bound-reuse checker. An unresolved call keeps its full result in
a separate event record; it cannot masquerade as a successful pricing call.

The original comparison retains all three failed outcomes and their spent time.
This source repair establishes neither a speedup nor a public-case optimum, and
uses no additional cluster allocation. Next we will assess a prospectively
defined comparison that supplies a known feasible fleet to the physical solver
as an initial solution, before expanding to independent timetables and retrieval
or learned proposals.

[Repair, validation and next research step](https://github.com/ndandnd/egg/blob/2343d492fe629af2fe2b70b2bbbc79b123fecbb3/research-20260928/no-plan-repair/README.md).
