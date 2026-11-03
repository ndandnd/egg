# Independent preflight of native path-flow energy V2

27 September 2026. **PASS at the candidate hashes below after one repaired implementation defect.** No optimizer was run. The reviewer contributed to the arithmetic-band derivation and independently reviewed the implementation; this is independence from the code author, not from the complete research project. A newly frozen twenty-control physical qualification and independent result audit must precede the newly versioned eight-cell compact-hull qualification. The archived V1 physical, hull and public-pilot outcomes remain unchanged.

## Reviewed scientific change

The new formulation `egg-native-pathflow-v2-energy-band` adds exactly two aggregate-energy inequalities and no variables. Its coefficients use the same per-mode floating leg sums and common efficiency as the existing SOC rows. One band encloses intended full-recharge conservation on individually stored service/leg inputs; a second encloses the selected integer points of the existing normalized stored SOC rows. Their union is materialized outward. This is a derived arithmetic enclosure, not an enlarged empirical solver or physical tolerance.

The proof and independent criteria are in `NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md` and `NATIVE_ENERGY_ROW_PREFLIGHT_CRITERIA_20260927.md`. Every complete service cover has N+K selected modes with K<=N, so the implementation's at-most-2N sums of the most extreme signed per-mode defects are conservative. Terminal residual signs are reversed before telescoping. Both the exact per-leg aggregation difference and the native constant-assembly difference are accounted for; a single rounded global equality would not provide that guarantee.

The implementation records service and mode aggregation defects, existing mode energies/M values, residual and normalized-row constants, both exact bands, their union, outward endpoints and the two row indices. Runtime checks compare actual service-row constants, movement residual constants, normalized big-M constants, aggregate coefficient maps and final normalized energy endpoints with the proof profile. Unsupported library constant elision or altered assembly fails closed before optimization. Thus the stored-matrix statement applies to the supported, checked assembly path, not arbitrary numerical-library behavior. The native solver's accepted feasibility-tolerance neighborhood is not claimed to be identical across formulations.

An independent AST comparison against compact V1 at `72a1f715` found changes only to `build_feasible_model` and `capture_incumbent`, plus the new `energy_balance_spec` helper. Pricing/planner drivers, extraction/path recovery, objectives and normalization/replay/bound admission are unchanged. Variable creation/order is unchanged; two physical rows are inserted before market load-link rows. The shared hull algorithm and its master, rational polishing and certificate calculations are unchanged. The adapter derives the new oracle identity and the existing retained-version boundary rejects V1 pools.

## Independent arithmetic and regression checks

Independent exact calculations on all twenty frozen synthetic inputs and both full public variants match the candidate's union endpoints. All twenty synthetic bands have zero width. Both public exact bands are

`[250264333071608001/281474976710656, 250264333071609185/281474976710656]`,

or the exact service sum plus/minus `37/17592186044416` kWh (approximately 2.1032064978498966e-12). Outward floats contain these exact values. The public service aggregation ledger has sign `exact_sum - float_sum`; it agrees with the independently computed opposite-sign diagnostic. No public optimization occurred.

The independently constructed fractional nominal witness passes 57 scalar old-model checks with integrality relaxed and lacks exactly 25/2 kWh of necessary recharge. The candidate fake-model test confirms only the new lower energy row excludes it. This demonstrates actual LP tightening without misrepresenting a fractional point as a physical schedule. The full mathematical construction and its executable standard-library check are retained beside the independent aggregation diagnostics.

All twenty physical case JSON objects, targets and budgets remain unchanged. All eight hull definitions, targets, market coefficients, dependencies and budgets remain unchanged except their explicitly versioned oracle/state identities. New versioned protocol identifiers, source dependency lists and exclusive attempt2 destinations preserve earlier attempt1 evidence.

## Defect found and repaired before freeze

The first candidate read `.const` directly from a movement residual. Real Python-MIP can return a bare variable from `Var - 0`. A valid pullout consuming exactly the full battery makes `B-energy=0`, so the original guard would raise `AttributeError` before optimization despite a feasible zero-energy service and terminal recharge. The original fake expression class did not reproduce this alias behavior.

The author repaired the candidate by normalizing each residual with `mip.xsum([residual])` before inspecting its constant. This changes representation, not mathematical coefficients or existing constraints. The added regression uses an aliasing variable without `.const`, a 20-kWh full-battery pullout, zero-energy service, and feasible 20-kWh terminal replenishment. It verifies construction and physical replay without a native solve. The independent re-review found the normalization preserves the compared constants and big-M rows.

**108 pure/fake tests passed in 0.50 seconds** with native imports externally blocked before test collection. They cover the old physical/hull/integration suites, unchanged 20+8 definitions, outward/profile arithmetic, the LP-tightening witness, raw ledger/row mappings, hidden constant/coefficient elision, formulation/retained separation and the repaired bare-variable case. No scientific optimizer or native model was instantiated.

## Execution and claim boundary

The reviewed runners retain the old solver, phase, routine, worker and supervisor caps, source-change guards, failure-prefix preservation and independent-cell continuation. Twenty-control V2 execution and audit come first, then eight-control hull V2 execution and audit. Each needs its own frozen source and immutable attempt. Every admitted raw incumbent must be checked against both added rows and the full old physical model; expected infeasibilities remain subject to their unchanged analytical controls. Passing this source review does not establish successful native qualification or improved operational bounds.

The matching relaxation remains a separate exact ideal-input lower bound. Adding this band does not automatically justify combining it with a tolerance-conditional native endpoint as an exact proof. Native results remain solver-conditioned numerical evidence; the ideal physical conservation theorem and exact stored-number row accounting are separate statements.

## Reviewed source dependencies

The union of the two reviewed runners' dependency lists follows. Individual attempt freezes should retain their own complete source lists.

- `src/egglab/native_recharge.py`: `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3`
- `src/egglab/native_pathflow.py`: `878484858dfe04b060833ddd8bb528c6c4e2169714b487adcbdd327138c9d093`
- `src/experiments/native_recharge_qualification.py`: `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e`
- `src/experiments/native_halfminute_qualification.py`: `1ca683c897828c7033d7d21862aae49aa25f0244c10e12abbd2c19065aa90c63`
- `src/experiments/native_pathflow_qualification.py`: `0c5c7fb46a1ab33ce8517abeb77e9b089b6a58a6aeae39bd797941c9391294c6`
- `src/tests/test_native_pathflow.py`: `203bef274806123a9991b4b13c7b0a8b24be9e9b4793b5dc4a2fb5e35b81531b`
- `doc/NATIVE_PATHFLOW_QUALIFICATION_PROTOCOL_20260927.md`: `4e7721233e42fe83d85d36ea18abb719bd1d57591dbb870a3019e8341e2fb84d`
- `src/tests/test_native_pathflow_energy_band.py`: `5c6feef4515e1ce46233bcd2f1aa65bc9cd8889836e16f5b4d7e6f3c1515afb3`
- `doc/NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md`: `b14913957f199662808483d052ad2fec778f69f71b14363667c40623c6f8276d`
- `doc/NATIVE_PATHFLOW_EQUIVALENCE_REVIEW_20260927.md`: `3592c5331540502269a782d99957dcc0819596c9e5c02e65a01e2342869f2336`
- `src/egglab/native_hull.py`: `335143dc4bdfff71193962038de0b74f77b6b5c6f4955ba2d56713c3c75a19d1`
- `src/experiments/native_hull_qualification.py`: `4129080d33dd474e4296a02fcc4af5feb18051be814bde016edf3f5450eb8d30`
- `src/tests/test_native_hull.py`: `9a7c5ab571b35b407d393f03bf38eb6e5f0e8381ee163fead37a3439c7943f32`
- `doc/NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md`: `4a88398af643902ff7a25c0a0008612eae79300a5347c87a9c9dc7d70785bd4a`
- `doc/NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md`: `690fdbdafe65102a845d4f052f737cf1a9ec938562b360bfa1a06e12f4114a0f`
- `src/egglab/native_pathflow_hull.py`: `60ed3a30cbce990649efad26405354cfa6c343a1c0b5bdaf010c3338b42a8686`
- `src/experiments/native_pathflow_hull_qualification.py`: `10e33fdfba943da63bd0dbc9e9695ada97909e42804490d759c2c8e1ccdb7196`
- `src/tests/test_native_pathflow_hull.py`: `3cc9dab5b4790311a30911d0607e8b5156077f307c4d93639446ad3edd2713a9`
- `doc/NATIVE_PATHFLOW_HULL_QUALIFICATION_PROTOCOL_20260927.md`: `30326fd3d8b22818605b836b1ba47c2189b598d76cff2b80137a9094c9ba3537`
- `doc/NATIVE_PATHFLOW_HULL_INTEGRATION_DESIGN_20260927.md`: `30f56dc593a7d0afb725d46e4ecc2e8ac35c45c3f8ed5f15526b3b749e694cbb`
