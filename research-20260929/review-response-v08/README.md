# Manuscript revision v0.8: source-only evidence merge

This revision uses archived scalar evidence and exact arithmetic. It runs no
optimization and does not modify the v0.7 PDF or its evidence reconstruction.

`build_joint_table.py` reads the reviewed v0.7 `analytic-bounds/bounds.json`
and writes `paper/latex/joint_support_table.tex`. It presents both original
and changed markets from the September 28 development screen. For the public
rows it uses the independently derived charging-availability floors in
`research-20260929/charging-availability-bound/bounds.json` with conditional
native screen uppers. For depot 15's original market only, it further uses
the independently reviewed exact rational two-bus witness with objective
512.7694256264009, giving the outward displayed upper 512.77 and gap cap
83.55 with the stronger floor. Regret intervals remain tied to
named time-limited planner incumbents and saved machine-rounded prices.

`paper/make_cyclic_price_update.py` draws the nominal two-service undamped
best-response cycle directly from the exact example in Proposition 2:
one-bus load (10,20), price (6,4), bills 147 versus 134; two-bus load
(0,30), price (4,6), current-plan bills 194 versus 167 (the best recharged two-bus alternative costs174). Both branches fully replenish.
The output figure replaces the historical flat-price pilot figure in the
main manuscript.

Open scientific questions remain: no public row certifies a positive
physical-versus-hull gap or regret at a physical optimum. The v0.8 table does
not improve the underlying optimization bounds or test other price-update
rules. The public floor combines a universal charging-window envelope with
the previously proved fleet-cardinality energy floor. It is an analytical
lower bound, not a feasible schedule or a new solver result.
