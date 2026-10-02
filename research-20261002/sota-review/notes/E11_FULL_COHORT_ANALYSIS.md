# E11 full-cohort analysis — 2 October 2026

All 96 existing array tasks are now reconciled to the original 96-row command manifest: eight case/size combinations × four arms × three seeds. Every expected case/arm/keep/seed key has exactly one collected e3.json; no missing or duplicate result keys were found. Day tariff and 60-second configured allowance match the manifest. All stdout logs identify expected source prefix 711c3d7; no source-version mismatch was found. Archive/member hashes, exact mappings, scalar outputs, failure records and accounting are preserved in [E11_FINAL_COLLECTION_20261002.json](../evidence/E11_FINAL_COLLECTION_20261002.json).

This is an analysis of project outputs, not independent physical verification. Archives were inspected in memory, without extraction or archived-code execution. No solver run, replay, rerun or duplicate job submission was performed. Scheduler COMPLETED/0:0 does not mean a fleet succeeded.

## Failure-aware paired results

Each comparison has 24 expected and observed case/seed pairs. Finite-versus-null ranking is a retrospective reporting convention, not specified in the original protocol. Both-finite metrics are reported separately to avoid conflating bill gains with failures. A finite reported bill beats a null bill; a null learned bill loses to a finite reference. Two null bills remain joint failures, not ties or dropped observations. Finite-bill ties use the historical relative 1e-6 rule.

| Learned keep | Reference | Wins | Ties | Losses | Joint failures | Both-finite wins/ties/losses (denominator) |
|---|---|---:|---:|---:|---:|---|
| 0.15 | cold | 23 | 0 | 1 | 0 | 20/0/0 (20) |
| 0.15 | cold4 | 23 | 0 | 1 | 0 | 8/0/0 (8) |
| 0.3 | cold | 24 | 0 | 0 | 0 | 21/0/0 (21) |
| 0.3 | cold4 | 24 | 0 | 0 | 0 | 9/0/0 (9) |

| Arm | Finite bill / 24 | Null bill / 24 | Reported statuses |
|---|---:|---:|---|
| cold | 21 | 3 | {'bounded': 21, 'unresolved': 2, None: 1} |
| cold4 | 9 | 15 | {'bounded': 9, 'unresolved': 15} |
| learned4 keep 0.15 | 23 | 1 | {'bounded': 23, None: 1} |
| learned4 keep 0.3 | 24 | 0 | {'bounded': 24} |

Full-cohort outputs strengthen the descriptive seed-repeatability finding on these eight synthetic case/size combinations. They do not establish independent-timetable generalization, optimality, or matched end-to-end savings. Both-finite counts distinguish bill improvements from wins caused by reference failures. The historical summarizer was not used: its duplicate overwrite and joint-failure omission are avoided here.

## Per-cell bill summaries

Min/median/max use finite reported bills only; denominator retains all three seeds.

| Case | Arm | Min / median / max | Finite / 3 |
|---|---|---|---:|
| scale:50000:60 | cold | 786.71 / 788.56 / 790.42 | 2 / 3 |
| scale:50000:60 | cold4 | 2002.33 / 2005.70 / 2009.35 | 3 / 3 |
| scale:50000:60 | learned4 keep 0.15 | 736.52 / 742.30 / 751.04 | 3 / 3 |
| scale:50000:60 | learned4 keep 0.3 | 741.90 / 744.50 / 744.85 | 3 / 3 |
| scale:50000:80 | cold | 3276.59 / 3279.53 / 3295.46 | 3 / 3 |
| scale:50000:80 | cold4 | none | 0 / 3 |
| scale:50000:80 | learned4 keep 0.15 | 887.14 / 889.06 / 896.06 | 3 / 3 |
| scale:50000:80 | learned4 keep 0.3 | 904.33 / 940.02 / 940.87 | 3 / 3 |
| scale:50001:60 | cold | 3198.21 / 3201.56 / 3207.58 | 3 / 3 |
| scale:50001:60 | cold4 | 3198.21 / 3202.89 / 3207.58 | 2 / 3 |
| scale:50001:60 | learned4 keep 0.15 | 888.42 / 898.22 / 981.63 | 3 / 3 |
| scale:50001:60 | learned4 keep 0.3 | 909.03 / 911.75 / 923.55 | 3 / 3 |
| scale:50001:80 | cold | 4065.23 / 4078.11 / 4091.00 | 2 / 3 |
| scale:50001:80 | cold4 | none | 0 / 3 |
| scale:50001:80 | learned4 keep 0.15 | 1101.73 / 1116.77 / 1121.56 | 3 / 3 |
| scale:50001:80 | learned4 keep 0.3 | 1890.24 / 2035.87 / 2107.13 | 3 / 3 |
| scale:50002:60 | cold | 1047.99 / 1053.11 / 1060.93 | 3 / 3 |
| scale:50002:60 | cold4 | 1053.81 / 2235.94 / 2239.42 | 3 / 3 |
| scale:50002:60 | learned4 keep 0.15 | 927.89 / 930.08 / 932.26 | 2 / 3 |
| scale:50002:60 | learned4 keep 0.3 | 943.39 / 950.11 / 1034.65 | 3 / 3 |
| scale:50002:80 | cold | 4468.99 / 4480.01 / 4491.65 | 3 / 3 |
| scale:50002:80 | cold4 | none | 0 / 3 |
| scale:50002:80 | learned4 keep 0.15 | 1261.42 / 1274.92 / 1300.32 | 3 / 3 |
| scale:50002:80 | learned4 keep 0.3 | 1205.60 / 1342.72 / 1402.53 | 3 / 3 |
| scale:50003:60 | cold | 807.02 / 809.81 / 814.99 | 3 / 3 |
| scale:50003:60 | cold4 | 774.11 / 774.11 / 774.11 | 1 / 3 |
| scale:50003:60 | learned4 keep 0.15 | 749.15 / 757.03 / 762.39 | 3 / 3 |
| scale:50003:60 | learned4 keep 0.3 | 748.99 / 751.07 / 755.51 | 3 / 3 |
| scale:50003:80 | cold | 1280.97 / 2569.36 / 3857.75 | 2 / 3 |
| scale:50003:80 | cold4 | none | 0 / 3 |
| scale:50003:80 | learned4 keep 0.15 | 923.67 / 926.49 / 932.43 | 3 / 3 |
| scale:50003:80 | learned4 keep 0.3 | 935.01 / 970.37 / 1000.18 | 3 / 3 |

## Failure and accounting receipts

Reported null-bill outcomes: cold has two unresolved no-plan records and one charge-projection refusal (3/24); cold4 has 15 unresolved no-plan records (15/24); learned4 keep .15 has one charge-projection refusal (1/24); learned4 keep .30 has none (0/24). Refusals are tasks 50 (learned4 .15, scale50002:60, seed 2) and 64 (cold, scale50000:60, seed 3), both reporting “Whole-incumbent charge projection exceeds roundoff budget.” These diagnostics do not independently prove a physical infeasibility mechanism.

Scoped accounting at 15:02:49 UTC reports all 96 COMPLETED/0:0; the queue was empty at 15:02:19 UTC. Scheduler elapsed/allocation, result total_seconds and wrapper runtime remain separate in the receipt. Allocated CPU counts cannot verify solver threads or actual CPU consumption; actual CPU was not read.

Seeds are repeated solver measurements. The parent's separate exact-source review confirms each same-ID 60-trip case is a prefix of its 80-trip case: four progenitor groups and eight correlated size cells, not 24 independent timetables or model samples. No retrospective threshold is assigned to the protocol's “large majority” phrase. E11 has no matched greedy/random control identifying learned-specific causal benefit. The parent's separate source review also identifies different round policies, timer exclusions and possible extraction overruns; reported failures remain failures even if an internal incumbent existed earlier. Thus a configured 60-second allowance is not a matched end-to-end cap. No earlier scientific summary is silently rewritten by this note.

Reproduce archive checks and summaries with `python3 research-20261002/sota-review/evidence/analyze_e11_archives.py`. Default output is JSON on stdout; the script reads only the three named archives in memory and writes no files.
