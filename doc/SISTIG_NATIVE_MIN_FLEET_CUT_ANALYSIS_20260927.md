# A two-bus cut for the stored native V3 public matrices

27 September 2026. Independent review is pending. **Design analysis only; no cut was inserted and no optimizer
was run.** For each of the two fixed, complete 37-service single-depot cases,
the inequality

\[
\sum_{j:\;m_j\text{ is pullout}} x_j \;\geq\; 2
\]

is valid for the *mathematical integer feasible set of the currently stored
native V3 path-flow matrix*. This is stronger in scope than simply transferring
the ideal-physics one-bus proof: the selected big-M rows below are interpreted
using their exact binary-stored floating coefficients and normalized RHS.
It does **not** certify how a numerical solver will treat near-integer values
or feasibility tolerances, nor does it change any archived solve bound.

## Flow premise and forced rows

The V3 builder has one incoming and one outgoing selected movement for each
mandatory service, equal pullout/pullin counts, and binary movement variables.
In these two frozen graphs, all movement arcs go forward in service time, all
37 services have positive, nonoverlapping duration, and exactly one mode joins
each chronological pair of consecutive services: a direct mode. The
independently passed [one-bus review](../research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md)
checks those graph facts against the complete frozen input. Thus an integer
solution with at most one selected pullout must put every service on the single
chronological path, selecting all 36 consecutive direct modes. A zero-pullout
cycle cannot cover services in this acyclic graph. `compile_case` gives charging
windows only to depot and pullin modes; direct modes have no charge variable.
Terminal pullin charging occurs after the last mandatory service. An initial
pullout cannot raise service SOC above its explicit 400-kWh upper bound.

Write `b_i,a_i` for SOC before/after service `i`, `e_i` for its stored service
energy, and `E_i=fl(sum(leg.energy_kwh))` for the stored aggregate energy of
forced direct mode `i`. The service row is `a_i=b_i-e_i`; its assembled constant
is checked equal to `e_i` in the builder. The direct residual is
`b_(i+1)-a_i+E_i`. The builder computes `M_i=fl(400+E_i)`, then normalizes its
two big-M inequalities with stored constants `P_i=fl(E_i+M_i)` and
`N_i=fl(E_i-M_i)`. At binary `x_i=1`, these stored rows imply the exact-real
inequality on their **stored** numbers

\[
  E_i+M_i-P_i \;\leq\; b_{i+1}-a_i+E_i
  \;\leq\; E_i-M_i-N_i =: u_i.
\]

The builder explicitly checks these normalized constants against its
`energy_balance_spec` ledger before adding the rows. This calculation does
not silently replace `fl(E_i\pm M_i)` by exact `E_i\pm M_i`.

Telescoping the 37 exact service rows and the upper side of the 36 selected
direct rows gives

\[
 b_1-a_{37}\;\geq\;
 \sum_{i=1}^{37}e_i+\sum_{i=1}^{36}E_i-\sum_{i=1}^{36}u_i.
\]

But the variable bounds give `b_1<=400` and `a_37>=0`. Reading each JSON
number as the binary float used by Python, then using exact rational arithmetic
on those stored floats, yields the same quantities in both depot cases:

| Stored-row quantity (kWh) | Exact value |
|---|---:|
| 37 service energies | `250264333071608593/281474976710656` |
| 36 direct aggregate energies | `12835258938005913/140737488355328` |
| Sum of 36 normalized-row upper defects `u_i` | `9/140737488355328` |
| Required first-to-last SOC loss | `275934850947620401/281474976710656` |
| Excess over the 400-kWh upper bound | `163344860263358001/281474976710656` |

The required loss is about 980.3175 kWh, an exact contradiction for the
stored-coefficient integer matrix. As an earlier check, the first 16 service
rows and 15 direct rows alone require
`7540666400094779/17592186044416` kWh, exceeding 400 by
`503791982328379/17592186044416` kWh (about 28.6373). The full-path defect
allowance is only about `6.4e-14` kWh. Pullout energy, any nonnegative
movement consumption outside the forced segment, and the V3 aggregate-energy
band are unnecessary for the contradiction; those additional constraints
cannot create a one-bus integer feasible point.

## Scope and recommendation

The cut is row-valid for the two named case identities only:
depot 15 `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`
and depot 16 `216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d`.
The checked frozen input SHA-256 is
`35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b`;
the analyzed V3 path-flow source SHA-256 is
`9b8f5017b5a5cded27ff3d23b047ecb40b5994dc83b75df7d50add96d4dc9682`
and native recharge source SHA-256 is
`0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`.
The frozen input case identities match the current public-payload case
identities. The prior [obstruction note](SISTIG_ONE_BUS_OBSTRUCTION_20260927.md)
and its independent review establish graph and ideal-energy facts; the
stored-row upper-defect calculation here is a separate extension.

If a later version inserts this inequality, pin the two case/source identities,
publish the exact selected-row defect ledger, and independently review the
new model and solver receipts. A mathematical cut does not make tolerance-
conditional two-bus witnesses exact, or retroactively strengthen existing
native bounds. The already selected 34-minute nonlinear pilot remains
unchanged. No claim is made for another graph, depot policy, battery size, or
general minimum-fleet theorem.
