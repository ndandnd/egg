# First verification cycle — prospective frozen comparison

Question: in the manuscript's fully replenished two-service family, precisely
which terminal powers and vehicle fees permit marginal-price support?
Expected artifact: a complete parametric derivation and a trusted, independently
implemented exact benchmark. Acceptance: all 20 assigned cases agree exactly
on feasibility, D, CH, every planner optimum, its complete price-response
argmin set and regret; nominal arithmetic smoke and corruption controls pass.
Disagreement or resource failure is retained and stops promotion. No retry.

Baseline: reference.py directly enumerates vertices of both physical SOC
polytopes with Fraction Gaussian elimination, then minimizes continuous quadratic
objectives on all physical segments and the convex hull's edges. Every reported
physical endpoint/optimizer has a chronological serial-charging witness.
Change: candidate.py replaces generic enumeration with the derived piecewise
capacity/fee formula in PROOF.md. Both receive the identical cases and arithmetic.
No speedup, statistical effect or new general optimization method is claimed.
This is a complete baseline/change/correctness cycle, not a replay of old runs.

Fixed model: A occupies [0,1], B [2,3], each 15 kWh; battery20, reserve0,
efficiency1, full initial/final20, at most2 buses. Early window[1,2] has one
10kW shared/per-bus connector; terminal[3,4] one K-kW shared/per-bus connector.
No other charging, travel, auxiliary draw, degradation, taper or switching time.
F(x,z)=4x+(x^2+z^2)/10, ops=f per used bus. V2G absent. Exactly both unlabeled
partitions AB and A|B permitted. Every comparison uses the same full deviation
set and fixed posted own-load marginal prices. Fraction arithmetic, no tolerances,
native solver or random seed. Invalid domain K outside[0,30] or f<0 rejected.

cases.json binds all 20 rational cases before outcomes: infeasibility, capacity
boundary, zero fees, lower/upper gap boundaries, both planner-tie regimes,
flat response intervals, nominal anchor and one rational interior case.
No additions, exclusions, outcome-driven sensitivity or denominators as prevalence.
The smoke anchor (K30,f7) is D97, CH7591/80, gap169/80, regret13. It is executed
once as part of the same case loop. Correctness mutations must reject a changed
objective, erased planner tie, omitted flat response interval, missing terminal
charge, wrong service-bus identity and excessive charge power. These checks run
on copies only and cannot alter saved original outcomes.

Change authority: new files only in research-20261028/paper_core_verification;
parent may update paper/README.md, paper/CLAIM_EVIDENCE_LEDGER.md and
research-20261023/CONTINUATION.md as navigation/evidence records. Historical
manuscripts, solvers, datasets, configurations and raw results are immutable.
After source freeze, no consumed source/protocol/cases edits. LAUNCH.json is
separate frozen control, then records/results/reviews can be added.

Execution: NEW20 CPU seconds/30 wall seconds inclusive acceptance allowance;
sole stdlib worker15CPU/20wall including its source checks, owner remainder.
Worker RLIMIT_CPU10 for self, seven serial local git-show calls each .5wall
timeout and configured pack.threads1; parent soft CPU2 and branch check .5wall.
The parent owns the child group and kills/reaps on20wall, reserves3s cleanup,
and alarms at27s after interpreter imports. Full process startup/shutdown is
measured externally. These are practical containment controls, not an exact
aggregate OS CPU limit or an instantaneous whole-command wall guarantee.
Any observed aggregate CPU>=20 or elapsed>=30 rejects the run, retains charges
and blocks promotion. CPU controls retain reserve for source children and cleanup.
No native backend; environment thread counts1; observed peakRSS ceiling512MiB
checked after exit, not instantaneous memory containment. Single serial task,
bounded20cases, no retry/resume. /usr/bin/time -p records whole-command CPU/wall.
Child/source checks are included once. External meter plus .02CPU rounding
allowance retained; static/tool/review costs UNKNOWN, not zero. Old globalprefix
21340.92 displayedCPU/22031.57elapsed-sum/21341.77retainedCPU remains paid.

Source/command: use .venv-local/bin/python -I -S -B on run.py --run-id cycle01.
LAUNCH.json pins source revision, control parameters and exact command before
dispatch. Worker reads each consumed source buffer once, checks git bytes at
the frozen revision, hashes once, and executes reference/candidate from those
cached buffers. No project source imports or old artifact inputs. Python/platform
recorded. Output directory must not exist; files use exclusive creation.
Worker writes results.json, TABLE.md, source_manifest.json and worker_receipt.json
inline; owner writes owner_receipt.json. No separate readout/export/hash pass.
All failures and unattempted cases represented. Final review inspects code,
proof and saved outputs. Agents' agreement is not numerical reproduction.

Reproduction command uses a fresh explicit run-id and a deliberately new frozen
control; the archived cycle never reruns or overwrites. A runnable source-pinned
command is preserved in LAUNCH.json and HANDOFF.md. No unattended infrastructure
or automation is created by this cycle.
