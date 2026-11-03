## Ordered solver comparison launched — 28 September 2026

The prospective development screen compares four methods in a fixed order: reserve-cold hull solving, retained feasible fleet plans, a numerical restricted master with retained plans, and that method with checked physical pricing-bound reuse. It declares four cases across two market states for 32 calculations. The two public depot variants share one Hildenbrand development timetable.

After CI run 36408897677 passed all required gates, one serial Slurm job (575215) was submitted from the frozen source. Slurm accepted it with a request for one CPU, 8 GB and a two-hour limit; the submission receipt observed it pending for scheduler priority. Every method pays for its own source preparation and validation, and failed runs and all time spent remain in the accounting. No scientific outcomes have been read, and this development comparison makes no machine-learning claim.

Source-frozen protocol: [protocol at commit f4b342d](https://github.com/ndandnd/egg/blob/f4b342dc85799d01d9313baeaf8c9ec527759d59/doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md).
Index: [comparison index at commit f4b342d](https://github.com/ndandnd/egg/blob/f4b342dc85799d01d9313baeaf8c9ec527759d59/research-20260928/solver-baseline-comparison/README.md).
