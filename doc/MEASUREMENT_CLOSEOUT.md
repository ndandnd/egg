# Measurement closeout: legacy replay revalidation campaign

Date: 2026-08-16. Status: policy document for the revalidation of legacy
`replay_ok=false` records. This is a **revalidation campaign, not a new
scientific experiment** — no scientific grid, parameter, instance, price
model, or outcome is changed by it.

## Why this exists

All Unicorn compute for the Phase 1/2 program completed (Phase 1: 128/128
checkpoints; damping frontier: 288/288; fine boundary: 64/64; all solver
records GRB/OPTIMAL). But 18 Phase-1 and 163 damping-frontier loop records
carry `replay_ok=false`. They were produced before PR #11, when the extractor
rounded energy values to 6 decimals and the replay audit used a 1e-6 kWh
tolerance — rounding and solver feasibility residuals accumulated along
vehicle chains until tight constraints appeared violated by ~1e-5 kWh.

Two compounding facts make this a closeout task rather than a rerun task:

1. `egglab/loops.py` appended those records and advanced the checkpoint
   without checking `replay_ok`, so the bad records were never failed work
   units — the completed reruns did not replace them. (Fixed: fail-fast
   ordering, regression-tested.)
2. The affected iterations are part of otherwise complete, scientifically
   valid trajectories. Deleting or rewriting them would falsify the
   append-only evidence trail; waiving them because their commit predates
   PR #11 would assume exactly what must be shown.

## What revalidation establishes, per record

For each failing record, identified by the SHA-256 of its complete original
JSON line:

1. the synthetic instance is reconstructed from the record's own metadata and
   its hash must equal the stored instance hash (guards against silent
   generator drift);
2. the record's exact trip partition is re-realized at its recorded prices by
   the current full-precision fixed-sequence oracle (no new EVSP is solved —
   the partition is fixed; only charging/arc-kind realization is recomputed);
3. the re-realization must pass the current replay validator
   (`REPLAY_TOL_KWH = 1e-4` kWh); and
4. its economics must match the legacy record within documented tolerances:
   objective within 1e-2 (the adaptive-certification scale, which also
   absorbs the 6-decimal price rounding stored in records), total energy
   within 1e-3 kWh, identical schedule hash; per-slot loads within 1e-3 kWh
   for `certified_equivalent`, otherwise `certified_alternative_realization`
   (a degenerate, economically equivalent charging allocation).

Outcomes that do NOT satisfy this — `materially_different` or
`reconstruction_failed` — are never accepted and fail the audit; they would
indicate a real modeling or data problem, not a precision artifact.

## Evidence rules

- Original JSONL is never overwritten or edited.
- One atomic sidecar JSON per record under `<runs>/revalidation/`, containing
  the original hash and violation text, source and revalidation commits,
  solver statistics, current replay result, comparison residuals, tolerances,
  and the final disposition. Sidecars are idempotent and parallel-safe.
- Audits (`experiments/audit_runs.py`) and the collector (`egglab.collect`)
  report BOTH the raw stored failures and the effective status after
  exact-hash sidecar matching. The raw count is never hidden.
- New records now carry `arc_kinds`, `replay_policy_version`, and
  `replay_tol_kwh`, so future audits can rerun the independent validator
  from the record alone, without solving any MILP.

## Success criterion

The campaign is closed when the three-root audit (`runs/phase1`, the damping
frontier, the fine boundary) exits zero: complete checkpoints, zero
unresolved replay failures, zero failed revalidations, all solves OPTIMAL
with converged certifications. Operational commands: `UNICORN_RUNBOOK.md`,
section "Legacy replay revalidation".
