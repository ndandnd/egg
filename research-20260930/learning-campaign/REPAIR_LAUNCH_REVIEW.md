# Route-fixed repair pilot launch review

**Disposition: no launch blocker in the final package.** The pilot is limited to the frozen Stage 2 development cases 2016 (20 services) and 2017 (28 services); it uses the existing frozen model and reads neither reserved test case data nor a retrained model. Input and source hashes pin the model, both case/market identities, archived controls, and the selection records used by the fallback.

The repair path separates learned route selection, bounded path-cover MILP, fixed-route charging, independent physical replay, and fresh target-hull verification. The hull receives only the replayed repaired fleet. If repair fails, the runner preserves the failure and uses the independently replayed archived cheapest source fleet, verifies its recorded selection key, and labels its lineage `archived_source_fallback`. No source or repair bound is carried into the target hull.

The resource guards are serial: one CPU, 8 GiB, one native thread, 30-minute Slurm allocation; 5-second route MILP, 55-second charging cap, 70-second target-hull cap, 240-second per-child cap, 900-second controller guard, and 1,100-second shell timeout. The exclusive attempt path, controller lock, no-requeue setting, and preserved unreceipted-cell behavior guard against duplicate or silent retry execution.

Root reports 11 focused tests passed, the shell syntax check passed, frozen design/source/input hash checks passed, and both actual source-fallback replays selected the archived candidates at target costs 553.4747744980671 and 724.6600417695474. The fallback column provenance distinguishes those imports from newly repaired plans. These checks support launching the bounded pilot; they make no repair-success, speedup, physical-optimality, or learning-benefit claim.
