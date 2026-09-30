# Stage 2 launch review

**Disposition: no launch blocker.** This is a delta-only review of the Stage 2 package, relying on the Stage 1 review for unchanged campaign and receipt behavior.

The frozen profile has six training groups (two each at 12, 20, and 28 services) and two development groups (20 and 28 services). Its 44-cell schedule runs all training cells, then both development source-pool pairs, then fits once before any development target arm. The reserved test seeds 2004 and 2005 are outside the active profile and rejected by the case builder; no test labels or features enter training.

The new paired-duty timetable generator includes a complete feasibility witness for every profile case. Root reports the focused Stage 2 checks passed, including replay of all eight witnesses, profile and order guards, and the single-fit-after-development-sources guard. The wrapper requests one CPU and 8 GiB for 100 minutes, caps native threads at one, excludes `scaglione-compute-01`, and disables Slurm requeue. The controller's 5,400-second guard is below the two-hour ceiling and the wrapper timeout is below the Slurm allocation.

These checks support a bounded Stage 2 launch. They do not establish model quality, fleet physical optimality, or performance; those require the resulting receipts and comparisons.
