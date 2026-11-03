# Independent bounded review

**Disposition: pass for the reviewed six-cell development calibration.** The scope remains the new cold screen only; the frozen retrieval attempt is separate and untouched. The design uses the three pinned `seed1006` development cases (`n08`, `n16`, `n24`) crossed with `source0` and `target`. They are nested variants of one generated timetable family, not six independent cases or held-out data. Market identity is frozen per physical case, and execution order alternates by case size.

All cells share cold complete-fleet hull optimization, compact path-flow pricing, native-LP master, GRB seed 0 / one thread, 16 pricing requests, 8192 rational bits, master/pool cap 64, and no starts, cache, or retained columns. The worker checks case/market, budget, arm, state index, and reserve against the frozen design. It assesses returned results through the existing physical replay and global certificate checks. Only on-time, complete, allow-listed assessments can populate bounds; failed, late, missing, incomplete, or unknown-status rows retain null bounds. Partial supervision reconstructs all six declared cell rows.

The timing envelope is internally consistent: six children at the 210-second hard limit plus 10-second TERM and 2-second KILL grace require at most 1332 seconds, leaving 168 seconds under the 1500-second controller cap. The 1600-second outer timeout and 1800-second single-CPU/8-GB Slurm allocation provide the stated outer margins; the excluded node and no-requeue setting are present. Freeze and seed/runtime preflight precede optimization, and the wrapper records freeze, preflight, supervise, setup, and elapsed outcomes even on preflight failure. Source hashes cover the runner, wrapper, tests, design/readme, selected helpers, case generator/preflight, and native model/oracle files. No change to the earlier frozen retrieval protocol is part of this package.

Interpretation caveat: any reported `_exact` fields are rationalized stored native values. The resulting enclosures remain conditional on native solver and physical replay tolerances; they are not exact ideal-hull bounds. Component solver times are reported only when event traces are complete and agree with native call counts; construction time remains unknown, not zero.

The implementer reports seven focused/adjacent pure tests and `bash -n` passing; I did not rerun tests or any optimization/cluster command.

## Reviewed source hashes

- `src/experiments/cold_baseline_viability.py`: `79c933b365d7f7ff10ca430212db060a5bd5ecb8cf6dfcfaaed8ed7607c7d55a`
- `src/tests/test_cold_baseline_viability.py`: `1989693f6a537a76fc0bbc92d2f24db6b5c7200e3d8e0cd3bcc4fcc0fcb24564`
- `src/cluster/cold_baseline_viability.sbatch`: `71eca4cfc886286896e9e2008e78c530606fde4bfe59c11320348b352c170829`
- `research-20260929/cold-baseline-viability/DESIGN.md`: `7c0b52fcffd71eca8940875e3dfcf3d89e8a35eb65694df676c695a259355dfa`
- `research-20260929/cold-baseline-viability/README.md`: `14da0906babc88c5e7b8439d30d68b5d08816dcd22f5b1f26a49b43d3baa3f8f`
