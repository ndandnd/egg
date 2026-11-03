# Prospective heterogeneous-support qualification

Status: SOURCE REVIEWED, runtime PENDING. No execution or launch authority is supplied by
this document alone. Parent review, a committed source closure and a separate frozen
LAUNCH.json must precede the single authorized attempt.

Question: does the independently reviewed complete heterogeneous two-batch
projection/hull/support theorem agree with independently implemented raw
physical SOC enumeration? Exactly the eight cases in cases.json are assigned,
in their fixed order. No additions, replacement, scan, statistical denominator
or empirical interpretation. f>0, n<=3, all crossmatchings, full initial/final
20kWh, n10kW early/n30kW terminal connectors, grid10n/30n and no movement,
reserve/loss/taper/switching time. Supply is4E+(E²+L²)/(10n).

reference.py directly enumerates every partial crossmatching and vertices of
raw per-bus SOC/power polytopes, constructs charging witnesses and replays
them. It computes physical and hull minima continuously using generic hull
geometry. candidate.py independently obtains matching thresholds with subset
dynamic programming and uses the proved threshold/interpolation formulas.
It separately retains every assignment, all physical optimum ties and full
continuous fixed-price response argmins. No reference import is permitted.

Compare D, CH, gap/sign, all projected hull minimizers, every labeled optimal
assignment, prices, regret, full per-assignment response intervals and each
optimal assignment's entire continuous early-allocation polytope. The latter
comparison enumerates exact vertices of the raw reference constraints plus
the optimum sum equality, versus analytic coordinate bounds plus that equality.
Every assignment's entire early-allocation box is also compared against its
raw physical vertices, so response intervals do not hide different individual
allocation possibilities. Matching-threshold minima are extracted from the reference's
physical interval endpoints by cardinality. Every matching and its interval
and operating cost must also match; no candidate-selected bank is substituted.

Negative controls must reject corrupt objective/thresholds, an erased optimal
assignment, a collapsed flat response interval, a changed allocation set,
invalid physics/domain and corrupted charging/service/power witnesses. Controls
operate only on copies: exactly18 negative controls plus one smoke check.
A literal hand-derived smoke anchor checks the first
case's D2681/20, CH434201/3240, gap121/3240 and regret11/10. Finite agreement
qualifies implementation of a continuum theorem; the proof is in the reviewed
structural extension and focused paper, not supplied by eight sampled points.

New source closure is reference.py,candidate.py,verify.py,run.py,cases.json,
PROTOCOL.md. A sole worker caches each once, checks git bytes at the frozen
source revision and hashes consumed bytes once, then executes only cached
reference/candidate buffers. Isolated stdlib Python -I -S -B, assertions on,
single-thread environment. No native solver, old artifact/data import, replay
of historical runs, export pass or automatic retry. All outputs are new and
exclusive. Keep failures and every unattempted case; no outcome-driven edits.

Fixed NEW package acceptance60CPU/90wall seconds, worker self40CPU cap,
observed inclusive45CPU/60wall and RSS512MiB. Owner soft5/hard50CPU, worker
process-group wait60wall, alarm87wall and3seconds cleanup reserve. Timeouts
kill/reap the owned process group. Git checks are serial with .5s timeout.
These are practical containment and observed gates, not exact aggregate OS
CPU limits or instantaneous RSS caps. /usr/bin/time -p observes whole owner
startup/shutdown. Parent verifies the external meter before CLOSED_PASS.
Child CPU overlaps owner CPU and is never added again. Static/tool costs are
UNKNOWN. Any excess, mismatch, missing receipt or unresolved child blocks
promotion; the paid attempt is not retried or refunded.

Exact command, only after the separate source/control freeze is pushed:
```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p .venv-local/bin/python -I -S -B research-20261029/heterogeneous_support/run.py --run-id cycle01 > research-20261029/heterogeneous_support/process-time-and-owner.txt 2>&1
```
Workingdirectory `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`.
Pre-packageprefix22194.01displayedCPU/23077.85elapsed-sum/22194.96retainedCPU.
Legacyconditionalguard2546.091499549272 remainsseparate; static/tool/reviewCPU
UNKNOWN. Allpreviousspend/failurespreserved. No priorpreparation readopted.

Independent formulation and internal exact agreement are not external
replication, originality clearance, public-timetable support evidence, a
generic EVSP algorithm or new ML evidence. No execution is claimed here.
