# Independent half-minute qualification audit

27 September 2026. **PASS for all 19 frozen controls under the declared native
numerical witness policy.** No author implementation was imported and no native
optimizer was invoked. Original native recharge attempt 1's three failures
remain separately failed; this audit does not relabel them.

## Evidence identity and coverage

- Executed source: `46fd6af573a240d54abb8ea8d7cf7b79cc0af0ee`.
- Original raw manifest SHA-256:
  `3531585498785e5c10cec2aa20ce73bb35e5310dc2fd4a1bf93d38e2f7f2a6f1`.
- All 135 raw files, 772,735 bytes, matched their original hashes and sizes before
  and after auditing. The original manifest and raw files were not changed.
- All six source/dependency hashes in the frozen record matched the committed
  source. All fifteen inherited control JSON objects matched the pinned CBC V2
  control archive exactly; the four new case identities and all input timestamps
  on the bounded exact half-minute lattice were independently checked.
- All 19 declared cells passed: 15 certified controls and four analytically
  infeasible controls. All 34 native calls returned: 30 OPTIMAL and four
  INFEASIBLE. Saved runtime receipts identify CBC, one thread and the fixed phase
  caps; a different backend is rejected by the audit.

The immutable raw manifest excludes this derived `review/` directory. Its
separate manifest covers the auditor, independent helper, report and audit JSON.
The helper is a byte-for-byte copy of the previously published independent
fixture auditor. The new wrapper extends its physical projection proofs and
raw-incumbent reconstruction; it imports only that helper and standard-library
modules. It never imports the research source or a solver.

## Reconstruction and new fixture proofs

The auditor reconstructs the complete physical projections of these specific
small fixtures, independently minimizes every saved linear or piecewise-linear
objective using exact binary-rational arithmetic, and checks the native global
bounds against those minima. It checks all 30 raw incumbent snapshots (1,075
variable values): index/mapping completeness, bounds/integrality, exact service
coverage, path flow, vehicle use, SOC and inactive big-M conditions, charge
selection, common interval capacity, period loads and saved epigraph rows. It
then independently applies the declared correction/endpoint rules and physically
replays all 30 saved fleet witnesses: 64 sessions and 233 SOC events.

| New fixture | Independent argument | Exact objective / result |
|---|---|---:|
| Halved-time multileg route | Every timestamp is halved, kW doubled, and driving cost per minute doubled. The complete physical energy/cost problem is unchanged: 14 grid kWh plus intrinsic cost 22. | 36 |
| Half-minute terminal window, 60 kW | A single service uses 0.5 kWh; the exact interval `[0.5,1]` supplies precisely 0.5 kWh, restoring the required terminal SOC. Fleet cost is 7. | 7.5 |
| Same window, 59 kW | Capacity is exactly `59/120 < 1/2` kWh, while terminal replenishment requires `1/2`. | Infeasible |
| Charge completion / instantaneous movement coincidence | One bus must cover both services via its only joining mode. After consuming 1 kWh, it charges 1 in `[0.5,1.5]`, consumes 1 in the instantaneous outbound leg at 1.5, then restores 1 in `[2,2.5]`. Fleet cost 7 plus 2 grid kWh. | 9 |

The coincidence service with zero energy is deliberately an event-ordering
regression fixture. It is not an operational use case or new positive-gap
research example. The replay checks charge completion before the coincident
energy-consuming leg, retains the exact saved charge energies and verifies every
SOC event, including full recharge at the terminal horizon.

## Numerical findings and conventions

The 15 certified interval widths range from
`1.999999966528776e-6` to `2.0199999983816497e-6`.
The widest interval belongs to the coincidence case: native objective and lower
bound `8.99999998`, exact physical optimum `9`, final guarded interval
`[8.99999898,9.000001]`. The discrepancy is preserved in the evidence, checked
against the fixed native objective policy and enclosed by the existing bound
guard. It is not rounded into a claim of exact native arithmetic.

There is one negative-to-zero charge correction, in cyclic own-price pricing,
with total magnitude `5.166411062336897e-15` kWh. Seven incumbents have nonzero
combined correction budgets; the maximum is exactly
`1/140737488355328 = 7.105427357601002e-15` kWh. The maximum interval aggregate
capacity excess is `3.552713678800501e-15` kWh. The maximum reconstructed SOC
residual is `1.1013412404281553e-13` kWh. The maximum raw model constraint residual
is `4.343192472333612e-12` in mixed constraint units; it is not a fleet kWh total.
All declared checks stay within their previously frozen limits.

No physical witness is rationalized, rounded, rescheduled or repaired by this
auditor. Exact fractions reconstruct stored float values and correction ledgers;
physical replay uses the unchanged raw floating sessions and the declared energy
and time tolerances. In raw model reconstruction, interval capacity coefficients
are the actual rounded native products `rate_kw * stored_float_hours`, converted
to exact rationals afterward. The physical correction ledger separately uses
exact stored minute endpoints and power. These two conventions must not be
confused for fractional-minute intervals. The earlier auditor's assumption that
the multiplication was exact was corrected in this derived extension before the
final audit; no scientific source or raw evidence changed.

This audit supports numerical qualification of these specific fixtures. It does
not prove feasibility for every future operational instance, exact global MILP
bounds independent of solver assumptions, or empirical performance at scale.

## Corruption controls and reproduction

All 22 deliberate mutations of in-memory copies were rejected. They cover raw
SOC/assignment, missing snapshots, numeric representations, duplicate semantic
mappings, interval coefficients, correction ledgers, omitted positive energy,
spilled endpoints, objective accounting, saved SOC traces, lower/upper bounds,
tangent history, half-minute endpoint/capacity changes, removed instantaneous-leg
energy, relabelled infeasibility and lost scaled driving cost. Originals were
never edited by these controls.

From the repository root:

```sh
python3 -B result/native_halfminute/20260927-attempt1/review/audit_native_halfminute.py
```

The default output is an exclusively created report in the system temporary
directory. For an explicit portable invocation from another working directory:

```sh
python3 -B /path/to/repository/result/native_halfminute/20260927-attempt1/review/audit_native_halfminute.py --repository /path/to/repository --attempt /path/to/repository/result/native_halfminute/20260927-attempt1 --out /tmp/new-halfminute-audit.json
```

The repository must retain the frozen Git commit and the pinned CBC V2
`result/native_recharge/20260927-attempt2/frozen.json` used for input-preservation
comparison. Explicit outputs must be new files outside every detected Git
repository. Existing files and symlinks are refused. Scientific output is
recomputed; reruns do not replace this derived packaged report.
