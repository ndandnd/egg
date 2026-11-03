# Matched numerical-QP master diagnosis

This is a separate six-cell **development** run against the already reviewed
cold native-LP baseline. It uses the same seed-1006 synthetic physical cases
(8, 16 and 24 services), `source0` and `target` price-only markets, case and
market identities, and alternating cell order. The cases form one nested
development family, not independent validation networks or ML test data.
The old frozen retrieval attempt and the completed native-LP attempt remain
unchanged.

The only method change is the existing `numerical_qp_proposal` restricted
master, with fixed exact-replay denominator `10^9` and at most 500 proposal
iterations. Physical pricing remains compact path-flow GRB, seed 0, one
thread, from a fresh cold start in every cell. No retained pool, bound cache,
MIP start, nearest-neighbor proposal or learned component enters. Every cell
keeps 16 pricing calls, 8192 projected rational bits, 64 master calls and
64 columns, epsilon `1e-4`, pool tolerance `1e-6`, 64 polishing steps and
20 s soft polishing allowance. The 10 s pricing reserve, 160 s native phase
and 180 s coordinator wall are identical to the native-LP baseline.

One subprocess per cell has a 210 s hard cap with up to 10 s TERM and 2 s
KILL grace. The 1500 s controller, 1600 s outer timeout and 1800 s Slurm
allocation bound the six cells even at worst-case child time. Request one
CPU/8 GB, exclude `scaglione-compute-01`, do not requeue or retry. Freeze
on the compute node before optimization. Pin portable NumPy and SciPy
versions in addition to the established Python/MIP/Gurobi/runtime and native
backend/seed identity; keep hostname as separate environment evidence.

Preserve all six outcomes, failures and spent time. Report replayed global
native enclosures only for on-time complete evidence; record pricing calls,
QP proposals/non-successes, proposal/replay time, rational bits, polishing
counts/time, native pricing time and full child wall. Native-LP master time
is *not applicable* to the QP arm and must not be read as zero total master
work. The existing cold pricing path does not separately time physical model
construction; leave it unknown. Compare status, bound quality and all paid
costs with the prior baseline, at common targets if available. Sequential
single-seed elapsed differences are exploratory, not speedup estimates.
