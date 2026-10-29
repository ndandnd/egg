# Independent fourteen-case source delta review

Scoped PASS after the narrow owner identity repair. Read `cases.json`, `verify.py`, `run.py`, `PROTOCOL.md` and `LAUNCH.DRAFT.json`; candidate/reference remain unchanged and were not reaudited. No source execution, imports, tests, hashes, native calls, data reads or commits.

## Defect and repair

The owner `IDS` still contained twelve names although its receipt and draft control declared fourteen. Consequently even a correct fourteen-case worker result would be rejected as an incomplete/changed ledger, and administrative fallback would preserve only twelve unknown states. Appended the two exact prospective IDs to owner `IDS`: `collinear-physical-threshold` and `clipped-first-edge-lower-boundary`. Also require frozen `assigned_cases == 14` before dispatch and master `assigned == 14` during result admission. No mathematical code was changed. Parent was notified.

## Independent identity/denominator check

- The fourteen JSON case IDs and order agree with `verify.py`'s fourteen `IDS`. Owner `IDS` now agrees exactly, including the two appended names. All original twelve JSON literals remain aligned with the first twelve worker `LITERALS`.
- New case 13 has A=B=(15,15,15), capacity20, K30, H90, fee20/3 in both JSON and literal gate. New case 14 has A=(3,11,17), B=(8,12,13), capacity20, K10, H59, fee6/5 in both. These are declared pre-run coverage intentions; no outcome is inferred here.
- Worker `admit` requires length fourteen, exact ordered identities and every exact rational parameter. Source admission includes `cases.json` and all six source-closure files. The worker loops every admitted spec, pads missing fatal-stage outcomes, reports assigned14, unattempted14-minus-attempted and requires fourteen rows for PASS. Owner compares the complete sorted identity list, thereby rejecting missing, extra or duplicate case identities; its unknown fallback now has fourteen rows.
- Protocol and draft launch both declare fourteen mandatory cases. Their commands/resources remain unchanged. Existing corruption indices still target their original cases because new cases are appended. The unchanged source defines fourteen targeted corruptions plus ten domain rejections (five per implementation), totaling twenty-four negative controls, and one arithmetic smoke check. This delta adds cases, not negative controls.

The existing comparator checks each complete assignment set, raw/candidate allocation polytope, sorted thresholds against unclipped raw SOC vertices, exact D/CH/gap, all physical optimum labels/prices/regrets, hull optimizer and full response continua. Thus the new cases pass through the same substantive comparison, rather than only a new nominal count. Actual collinearity/boundary outcomes and all PASS claims remain pending the separately authorized frozen execution.

No further delta blocker found. The stale paper limitation is outside this source delta and is being corrected by the parent. Frozen source/control and independent final external resource closure remain required.
