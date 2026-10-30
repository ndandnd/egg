# New stored-energy descriptive question

25 October2026. Freeze `energy_diagnostic.py` for one new compact export; do not rerun or alter `analyze.py`, its output, or the completed workers. Question: relative to CoverCA1, CA1 and random, do the frozen GNN endpoints consume less total grid energy, and how does that difference accompany their cost advantage? This follows the QP diagnosis but changes no model, topology, endpoint, acceptance rule or continuation threshold.

Read `warm_replanning/summary.json` exactly once. Access only its eight prior records and 168 operational decomposition/identity/status fields. Export all seven arms ×eight variants ×three seeds with stored grid energy, E0, cost and operating/fleet/deadhead/linear/quadratic/electricity components. Compute stored-number rational differences only; no plan, model, selection, capture, replay, hash, archive, inference or optimizer access.

For each of CoverCA1, CA1 and random, retain all24 pairs. Define energy fraction as `(energy_GNN-energy_control)/energy_control`; zero control energy yields an explicit undefined value, never a dropped pair or free zero. Define cost advantage as `(cost_control-cost_GNN)/E0`, with E0 the common prior's late-tariff electricity cost. Report paired signs, full-denominator means/medians, and four group medians over six nested size/seed cells each. Export each arm's energy fraction versus prior too. A descriptive 3×3 sign table associates GNN-minus-control energy and cost changes; it does not identify causal tariff information, charging timing or route-versus-charging mechanisms. Four exposed base units remain four units, not24 independent timetables.

Provision **10CPU/20wall inside the SAME1800CPU/2700wall QP package**, body8CPU/18wall plus publication reserve2. Closed package cost before this export is48.84CPU/50.59elapsed; closed numerical-process cumulative7053.19CPU/7227.81elapsed already includes v1 carry, corrected v2 and the0.04CPU/0.06elapsed analysis. Add this export's external meter once; do not double-count prior charges. Self measurements stop before publication/exit; no whole-session exact CPU claim or historical guard reset.

Parent inspected the stable source, exact stored-field schema and denominator
logic, and added only a compact rounded stdout view within the same metered
publication reserve. Exact rational output remains authoritative. Static review
is complete; freeze this source with the following once-only command:

`PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -p -o research-20261025/fixed_route_qp/energy-diagnostic-time.txt .venv-local/bin/python research-20261025/fixed_route_qp/energy_diagnostic.py`

Output `energy-diagnostic.json` opens exclusively and preserves failures. No automatic retry, extra data, fitting, new solver call or broader experiment follows from this export. Existing scientific results remain immutable.
