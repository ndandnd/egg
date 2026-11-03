# 3 November extensions

The research source and final compact outcomes are pinned at **d185f153** on origin/codex/opf-loop-20261102. The paper branch is paper/draft1-20261030. The committed evidence copy is paper/draft1/results/dutyfirst_20261103. This file and the PDF contain no new private export.

Read results/dutyfirst_20261103/READOUT.md for the full denominator, engineering and measurement record. Sources and controls on the research branch are doc/opf/NEXT_COMPARISONS.md, doc/OPF_LOOP_SPEC.md and doc/opf/SUPPORT_BOUND.md. Exact run sources are preserved in Git, so check out the listed revision when repeating a frozen command. All data inputs are the prior admitted DE and SimBench downloads, draft1/data/peak_runs.json, and the original 64-row A2 development roster. The price/input acquisition URLs and digests are in result/opf_qualification/repair02/input_recovery.json and doc/opf/INPUT_FREEZE.md. Dependencies include Python 3.12.2, CVXPY 1.6, Clarabel 0.9, the local Gurobi installation, the prior research environment's python-mip, SimBench 1.5.3 and pandapower. Native worker launchers set one thread and use an external process meter.

| Package | Source/control commit | Launcher |
|---|---|---|
| Original 144 matched assignments, 73 strict hulls | e93fdd68 | doc/opf/run_matched01.sh |
| Whole-bus lift of original outcomes | ff0f15ac | doc/opf/run_lift01.sh |
| First Gurobi continuation of 25 inaccurate hulls | a78294f0 | doc/opf/run_gurobi01.sh |
| Practical barrier target on 17 remaining calls | 30da33ca | doc/opf/run_gurobi02.sh |
| Zero-price duty commitment | 6abeaa66 (import failed), faad27a0 (environment repair) | doc/opf/run_flagship_repair01.sh |
| Grid-price iteration, fixed original 73-cell cohort | 6df49835 | doc/opf/run_loops01.sh |
| Stronger price-blind energy tie | b3252f07 | doc/opf/run_energytie01.sh |
| New physical upper costs on 25 repaired hulls | f5c73e65 | doc/opf/run_lift02.sh |
| Capacity formula and rates | b3252f07 | src/experiments/pairing_capacity.py, fresh output directory |
| Corrected summaries and cached-only loop completion | 4ad2f77a | src/experiments/close_dutyfirst_checks.py, fresh output directory |

These launchers use the prior isolated package locations in private/tmp and therefore need those declared dependencies installed in the reproduction host's own environment. The frozen scripts refuse an existing scientific output directory. Do not overwrite the archived attempts when adapting paths. The merged02 input packet directory is assembled mechanically from the original descriptor roster, preferring the first qualifying Gurobi result and otherwise the second. The 25-row lift never repeats the original 73 physical replays.

The original detector's near-fixed approximate cycle labels were withdrawn, and only cached price arithmetic was extended. The final summary archive contains both the retained original labels and the corrected outcomes. An initial summary's capacity selection required a size-filter repair before the final outcome copy. The raw failed/intermediate summaries remain on the research host, while the final committed outcomes are authoritative. The raw electricity-denominator field in the flagship packets is unused because it is not the joint plan's electricity bill. All percentages in the manuscript use total original joint cost.

The native price loop remains unresolved for 22/73 assignments on grid admission, and eight fleet responses are grid-infeasible. Step .1 has sixteen additional finite-budget stops across the two designs. Two primary hull cost brackets have widths near €0.70 and €0.81. Exact-arithmetic AC dual bounds and an independent external review of novelty/significance remain open. The two-window one-fee proposition is a mathematical result under its stated hypotheses; the feeder comparisons are numerical brackets.

A separate direct arithmetic evaluation checked all 128 fixed-duty upper objectives, regret interval endpoints and the zero-price operating-cost cap for the energy tie. All passed, with maximum objective discrepancy 9.1e-13 SEK. Physical replay is also in each solver packet. The already verified 37-service certificates and original peak-run sweep were not rerun. Only the typeset PDF was rebuilt. Render review covered all pages at thumbnail scale and the new bound, boundary comparison, grid and tariff pages at reading scale.
