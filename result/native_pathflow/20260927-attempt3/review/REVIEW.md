# Independent compact attempt-3 result audit

**PASS: all 20 frozen controls are independently accounted for.** The run has
16 certified synthetic results and four expected infeasibilities, across 35
returned native calls (31 `OPTIMAL`, four `INFEASIBLE`). The audit imported no
project implementation module and invoked no optimizer.

The audit pinned source commit `dd5ad1659248b93d53f7f1515282d9530343567f`
and verified all 15 frozen source hashes against both that commit and the
unchanged working files. The attempt-3 control JSON, CBC/phase budgets, and
target tolerance match attempt 2 exactly. Its original archive is intact:
142 manifested files, 1,309,561 bytes, manifest SHA-256
`c855d220a34b931804cf43c7aedf89d432aae41746c4169f3b87888120b2081a`.

Using exact stored-float fractions, the raw audit reconstructed all 31
incumbents and 589 variable values, including the unchanged V2 native matrix,
the two energy-band rows, all physical constraints, path selections, and raw
objectives. The largest raw-row residual is `7.38e-12` kWh. Across every
incumbent it independently reconstructed the negative correction `N`, positive
unselected-mode projection `O`, native-load/raw-charge residual `L-R`,
materialized-load/projected-charge residual `H-P`, interval and session
capacity excesses, and replay-load residual `T-H`. The largest complete
whole-incumbent correction is `1.2261e-12` kWh against the single `1e-8` kWh
budget. The one nonzero orphan is `1.2214e-12` kWh in `joint_planner`, round 1;
its exact key, mode, unselected status, zero projection, and period accounting
all match the saved ledger. Each final plan repeats the final projection,
negative-normalization, and serial-decoding records consistently.

The independent physical replay checked 31 witnesses, 69 charging sessions,
and 253 SOC events. The maximum replay SOC residual is `2.13e-12` kWh.
Pricing deltas were reconstructed as `price · (T-L)`; planner PWL and true-cost
deltas were separately recomputed from raw and replay loads. Native lower
bounds, replayed upper bounds, all 16 analytical targets, and final intervals
were checked. Certified widths range from `1.99998296e-6` to `2.00000007e-6`,
within the frozen `1e-4` gate.

The four infeasible controls remain exactly `fixed_reserve_one_bus`,
`terminal_capacity_failure`, `partial_overlap_failure`, and
`halfminute_capacity_failure`. Each has one returned `INFEASIBLE` call, an
`infeasible` result, and no fabricated incumbent or projection record. All 25
deliberately corrupted copies were rejected, covering raw matrix/mapping,
policy identity, the orphan record and exact ledgers, decoder/capacity data,
objective deltas, replay SOC, certificates, and infeasibility preservation.

The calculation reuses the preserved independent attempt-2 raw-matrix,
fixture-optimum, and energy-band auditors, locally updating only the expected
V3 extractor identity. It does not import `egglab` or `experiments`. The
machine-readable details and corruption results are in `audit-report.json`;
the standalone auditor and independent helper sources are adjacent.

This pass qualifies only the declared synthetic compact attempt-3 policy.
The bounds and replay checks remain numerical and tolerance-conditional. This
result does not qualify compact-hull integration, operational use, or a public
pilot.
