# Eberbach adapter review

**Verdict: reviewed; no blocking contract issue found in the frozen intake.**
The adapter keeps `hildenbrand` as the default operator and output, selects a
separate Eberbach output, preserves the 105 mandatory services and all 196
directed matrix arcs, and retains exact timestamp, reference, and matrix
checks. The Eberbach vehicle, energy, charger, full-replenishment deadline,
and synthetic cost are labeled as EGG assumptions; the note does not present
them as operator observations or publisher results. The pure witness is
reported as a feasible 105-bus construction, not an optimum. No native model
or optimizer is allocated by this intake.

The dimension figures are clearly separated: the note reports the current
compact estimate of 291,637 variables and about 312,316 rows. The machine
receipt's 29,508,990 `candidate_charge_variables_at_max_vehicles` belongs to
the legacy per-vehicle candidate count, not the compact formulation. The
artifact and intake note do not conflate these counts.

The focused test file covers Eberbach source semantics, directedness, pure
case compilation, the recorded witness result, and distinct default/output
paths. The author’s separate pure regeneration performed the physical replay. Sol
reports 11 focused adapter/regression tests passed and byte-identical default
Hildenbrand regeneration; this reviewer did not rerun the suite or preflight.
The conclusion is limited to source intake and pure construction, not solver
performance, fleet optimality, or operational validity of the assumed
vehicle/charging policy.

## Reviewed pins

- `src/experiments/sistig_native_case.py` — SHA-256
  `4610ae956ae5300904f99d961f6437f0a7384047e5645304b92e00b1e3252bcc`
- `src/tests/test_eberbach_native_case.py` — SHA-256
  `4f4390af47a01060e400aa41d2a0ccd61dfa25a5953046959dd5b8d5257c84b0`
- `data/public/sistig_26088190_v1/eberbach_native_case.json` — SHA-256
  `5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19`
- `research-20260928/benchmark-intake/EBERBACH_INTAKE.md` — SHA-256
  `a6abf28e61391c67bc1ffe34f64c166fa839f8566d8ded465498c93507705a16`
- `research-20260928/benchmark-intake/EBERBACH_PREFLIGHT.json` — SHA-256
  `6457d3264cb929e8c780fadfcc4945756c8c4e39557f0d6bdff5b2915b3fd3b6`
- Existing Hildenbrand artifact remained byte-identical — SHA-256
  `af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6`.
