# Independent nonlinear pilot failure audit

**Outcome: the sealed failed attempt and its partial planner trace pass this integrity audit; the scientific pilot did not pass and is not admitted.** No optimizer was run by this audit, no retry was made, and the hull and own-price stages remain unstarted.

The audited source commit is `80eb69544f568a7ed346f0d603004a10f61c481a`. The exclusive attempt is `result/sistig_nonlinear/20260927-attempt1`; its sealed manifest SHA-256 is `796a9c26b968a35a616269043708ba71f95defe1848547ce191d12ecc11f0c2d`. I independently checked the frozen payload/case and source hashes against Git, the manifest file set and byte hashes, the supervisor and post-seal wrapper receipts, stage order, GRB runtime identity, raw compact matrix/primal, charge-projection ledgers, replayed plan and SOC, and the controller's failed/unstarted-stage record. Three copy-only corruptions of the raw variable representation, final correction ledger, and replayed terminal SOC were all rejected. The original attempt was not modified.

## Why the run stopped

The planner worker recorded `TimeoutError: Scientific routine/admission cap exceeded` at **242.315 s**, exceeding its declared **240 s routine cap by 2.315 s**. Its child process returned after **243.218 s**, below the **255 s child hard stop**; the stage receipt records `hard_timeout: false`. The controller then returned 1, the Slurm wrapper returned 1, and job 559683 ended `FAILED` / `1:0` after `00:04:22`. Thus the saved cause is the routine-cap check, not a child or outer timeout.

Two native GRB calls started and returned with complete event accounting. The first was `OPTIMAL`; the second was `FEASIBLE`. The second call's dynamically recorded phase cap was 144.582273 s and its reported wall time was 144.591168 s, an 0.008895 s excess. That small telemetry discrepancy is retained here; it does not change the recorded worker exception or convert this failed routine into an admitted result.

## Partial planner evidence

`planner/raw_result.json` preserves a `bounded` result and physical plan, but there is no `planner/result.json` assessment package. Independent reconstruction of both 21,826-variable native snapshots verified their compact rows, objective values, V3 policy tags, raw energy and load, exact charge-correction ledgers, materialized sessions, physical path cover, connector limits, SOC traces, and round-by-round bound propagation. Maximum reconstructed raw row residuals were below `5.0e-11`; the largest replayed SOC residual was below `2.6e-11 kWh`. The exact whole-incumbent correction totals were `1/17592186044416` and `1/140737488355328 kWh`, both within the frozen `1e-8 kWh` correction budget.

| Round | GRB status | Reconstructed widened interval | Solver wall / recorded cap |
|---|---|---:|---:|
| 0 | OPTIMAL | [408.53313488387835, 552.3588966728554] | 88.970 / 180 s |
| 1 | FEASIBLE | [403.76922888387793, 514.5263116550285] | 144.591 / 144.582 s |

The preserved planner result takes the strongest round lower endpoint and best replayed upper endpoint, yielding `[408.53313488387835, 514.5263116550285]` (width 105.99317677115016). Its two-vehicle, 12-session upper witness independently replays at 360 kW maximum charging power and returns to full usable inventory. This is a **partial, solver-conditioned planner trace**. Because the routine exceeded its cap, it is not an admitted pilot bound or a final experimental result. It does not establish a minimum fleet size, hull value, pricing response, gap, or regret.

The controller recorded `hull` and `own_price` in `unstarted_stages`; neither has a folder or result. No full-pilot interval report was produced. The accounting records requested 1 CPU and 8 GB; final SACCT shows 2 allocated CPUs, `MaxRSS=351628K`, `FAILED 1:0`, and no requeue. The frozen batch directives exclude the reserved node `scaglione-compute-01`. The saved SCONTROL snapshot was still `PENDING`, so I used it only for requested TRES, not final allocation. The audit verified log hashes through the manifest but did not read or reproduce stdout/stderr contents.

## Audit artifacts and reproduction

The machine-readable audit is [audit-report.json](./audit-report.json). The self-contained read-only driver is [audit_nonlinear_pilot.py](./audit_nonlinear_pilot.py), with its copied independent matrix, projection, physical replay, and hull helpers alongside it. It uses Python's standard library and Git; it does not import project code or solver packages. Its result status explicitly says **failed/incomplete attempt; no scientific pass**.

This driver verifies the complete original sealed attempt: its exact-file-set check requires every path named by the original manifest, including the declared stdout/stderr files, plus `MANIFEST.json` and the later wrapper receipt. A public copy that omits declared licensing-only stdout files is not a valid input to this driver. The complete private archive is required for byte-for-byte reproduction; the public-subset manifest is a separate publication record and does not weaken this check. The portable scheduler evidence is copied to [scheduler-evidence.json](./scheduler-evidence.json), avoiding reliance on the original outer cluster directory. The original attempt and manifest remain unchanged.

Reproduce the audit from the repository root with:

```sh
python3 research-20260927/agent-notes/nonlinear-pilot-result-review/audit_nonlinear_pilot.py \
  --repository /Users/nadan/Documents/ChatGPT/egg/journal-research-work \
  --attempt /Users/nadan/Documents/ChatGPT/egg/journal-research-work/result/sistig_nonlinear/20260927-attempt1 \
  --manifest-sha256 796a9c26b968a35a616269043708ba71f95defe1848547ce191d12ecc11f0c2d \
  --scheduler-json /Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260927/agent-notes/nonlinear-pilot-result-review/scheduler-evidence.json \
  --out /Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260927/agent-notes/nonlinear-pilot-result-review/audit-report-reproduced.json
```

The output path must be a new filename directly inside the review directory; the driver refuses to overwrite a report. `python3 .../audit_nonlinear_pilot.py --help` lists these flags. A copy of the sealed attempt in another repository layout is out of scope because the driver pins the original attempt-relative path and Git source commit.
