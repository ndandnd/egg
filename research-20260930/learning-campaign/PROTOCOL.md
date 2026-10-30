# First synthetic learning campaign protocol

The first allocation runs exactly 17 bounded native-hull cells: three independent
eight-service base timetables, each with two source tariffs and one target tariff.
Base timetable seeds 2001 and 2002 are training groups; 2003 is development.
Seeds 2004 and 2005 are reserved test groups before training and are not
materialized, solved, exported, or inspected in this job. All variants of a
timetable share its split. This is a synthetic development exercise; it does not
use A6, B3, protected holdouts, or private timetable data.

Within each training group the order is source0, source1, target cold, target
retained, target nearest-price. The development group adds target cheapest-bill
and learned after these arms. The source calls produce complete native fleets.
Every imported fleet is replayed against the exact physical case. Retained uses
all unique source projections. Learned, nearest-price, and cheapest-bill see
the same one-best-fleet-per-source catalog pool. Nearest-price picks the source
fleet whose source-market tariff vector has the smallest exact squared distance to target
prices; cheapest-bill picks its minimum exact target cost.
The native target solver then receives the replayed feasible pool. No source
lower bound is imported as a target certificate. The cold arm receives no pool.
All target arms use the same physical case, target market, compact oracle,
QP master, and bounded solver controls. Direct feasible proposal cost, source
acquisition time, target solver time, statuses, and failure receipts are retained.

The bounded CPU trainer runs after the development source1 receipt and before
the development cold target solve. It fits training groups only, derives the
development target input from the frozen design, and replays the projected
complete proposal against the development physical case. A failed trainer
gets its own receipt and does not stop the native baseline cells. Directly
ranking same-case source plans by
their computable target cost is a diagnostic control, not evidence of learning
or saved online optimization. Test groups remain unused until a later frozen
method and evaluation protocol exist.

Each child has a 70-second native budget and a 100-second hard process cap.
The trainer has a 45-second hard cap.
The controller has a 2,100-second elapsed guard; its shell has a 2,200-second
external cap. One CPU, one native thread, 8 GB, 45-minute Slurm wall time,
no requeue, and exclusion of `scaglione-compute-01` are mandatory. Each
completed child has an immutable launch and receipt. A failed child is recorded
in the catalog with its spent wall time and native status; a partial result is
never silently promoted to a certified label. An interrupted unreceipted child
is preserved and stops the resume path for manual postmortem.

The attempt directory is `result/learning_campaign/20260930-attempt1`.
Freeze pins the commit, source hashes, runtime, native backend probe, cases,
split, markets, and budgets. The controller holds an exclusive file lock and
only appends catalog records absent from the prior complete prefix. Resume
requires matching source, runtime, and design identities. Final scientific
admission remains pending independent result review.
