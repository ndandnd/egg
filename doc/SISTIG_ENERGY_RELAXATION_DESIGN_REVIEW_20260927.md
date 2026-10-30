# Independent review: flat-price energy matching relaxation

27 September 2026. **PASS for mathematical reduction, exact assignment
certificate logic, and the prospective runner/protocol as currently stated.**
This is a preflight only: I did not run the matching calculation on either
public depot case, invoke an optimizer, or use cluster resources.

The reduction is valid for the specified ideal full-recharge model at one flat
price. For a bus path, full initial and terminal usable inventory, common
charging efficiency `eta`, no V2G, and accounting for every modeled service and
movement consumption imply total grid energy is total battery-side consumption
divided by `eta`. At a single scalar price, the charging time and period do not
change that energy cost. This identity would not justify the same reduction
with time-varying prices, incomplete replenishment, variable efficiency, or
energy omitted from the case.

Each service begins as a singleton path with the fixed service-energy cost and
the minimum declared pullout, pullin, and used-bus cost. Replacing the pullin
after service `i` and pullout before service `j` with a declared connection
changes the objective by

`connection_cost(i,j) - pullin_cost(i) - pullout_cost(j) - vehicle_cost`.

The implementation uses this as the connection's incremental cost; its
negative is the saving. It keeps the cheapest declared movement for each
directed pair and rejects any case missing an endpoint mode. Each physical
vehicle schedule induces a predecessor/successor matching over services.
Relaxing battery/SOC, recharge-window and shared-connector constraints, and
the maximum fleet count enlarges that set. Because every selected connection
respects service chronology and each service has positive duration, the
connection graph is acyclic. Degree at most one on each side therefore gives
disjoint paths without cycles. The minimum matching value plus the singleton
baseline is a lower bound for the stated ideal physical model; the relaxed
path count and selected modes are not asserted physically feasible.

For `n` services, the code builds `n` left-service rows, `n` real successor
columns and `n` zero-cost unmatched columns. Assigning each row to one distinct
column enforces at most one successor per service; real successor columns
enforce at most one predecessor, while dummy columns mean no successor. The
rectangular primal is minimum cost with row sums equal to one and column sums
at most one. Its dual has unrestricted row potentials `u_i`, nonpositive
column potentials `v_j`, and `u_i + v_j <= a_ij` on each allowed edge. The
verifier checks allowed distinct assignments, every dual inequality, the
column-potential signs, and exact equality between the primal objective and
`sum(u)+sum(v)`. By weak duality, that equality certifies the exact assignment
minimum, including the dummy columns. The decoded path-cost consistency check
then ties that certificate back to the movement IDs and baseline.

Arithmetic is exact over the numeric values held by the Python input objects.
In particular, JSON numeric literals are parsed as Python floats first and
`Fraction(float)` preserves the exact binary value; the configured `0.2` is
therefore not silently replaced by `1/5`. This is a well-defined exact
stored-binary-input relaxation, not exact arithmetic over the publisher's
original decimal text and not a certificate for the native solver's rounded
matrix or its feasibility/integrality tolerances. The separate numerical-scope
review correctly requires the matching lower bound to remain distinct from
native lower endpoints and tolerance-conditional physical witnesses.

The pure test suite passed locally: `PYTHONPATH=src python3 -m pytest -q
src/tests/test_flat_energy_relaxation.py` — 16 passed. It exhausts all 4,096
sparse signed 2-by-3 assignment matrices against independent permutation
enumeration, checks larger augmentations and corrupted certificates, and
exercises path costs, missing endpoint rejection, fleet-cap relaxation,
parallel modes and efficiency. I also exercised the supervisor wrapper with
mock successful and timed-out child completions: it recorded exit/timeout
status and included stdout, stderr, and the receipt in each manifest. That
mock checks receipt and archive behavior, not operating-system process-kill
semantics; `subprocess.run(timeout=45)` supplies the kill-and-wait behavior in
the real wrapper.

The prospective protocol now requires committed dependency hashes and a
source/input freeze, exact Python/platform match, one exclusive `supervise`
launch, two case calls, a 30-second routine cap and 45-second subprocess cap.
It preserves raw outputs and manifests completed or failed attempts. The
runner does not import or call a solver in the matching path. These controls
are adequate for the proposed bounded calculation once the code, tests,
protocol and reviews are committed and the named freeze is created. The
preflight is not a numeric result audit; any later public certificate still
needs an independent reconstruction from the frozen payload.

## Files reviewed

- `src/egglab/flat_energy_relaxation.py`
- `src/experiments/sistig_matching_relaxation.py`
- `src/tests/test_flat_energy_relaxation.py`
- `doc/SISTIG_MATCHING_PROTOCOL_20260927.md`
- `doc/SISTIG_MATCHING_NUMERICAL_SCOPE_REVIEW_20260927.md`
- `src/egglab/native_recharge.py` (objective and energy equations only)
