# Prospective fixed-topology exact charging qualification

Status SOURCE REVIEWED/runtime PENDING: no authority to dispatch until parent source review, the helper's independent review and prospective source/control freeze. This is a new classical diagnostic prompted by an unadmitted native charging proposal; it is not a retry of the earlier phase or a global planning certificate.

Source closure: this worker/run/protocol, `public_support_resolution/exact_fixed_topology.py`, `energy_flow.py`, `exact_dual.py`, `independent_verify.py`, and `src/egglab/{__init__,native_recharge}.py`. Load only cached byte-verified sources. Backend is gurobipy12.0.1, one thread; no mip/native_pathflow import. Input case comes from253c1e29295e766b3889fc8f5c28d9808e00b3d6. Read the pinned f8a043132863db5ce631d5691d35b5d788bdf256 gzip MIQP packet once only to extract selected movement IDs, then discard its decoded contents. Never reuse or replay its charging vector. Input paths are fixed in source, never artifact-controlled. Byte-compare each cached input to its pinned Git revision and hash that cached buffer once.

Assigned states, in order:

1. Q0: one service `[0,30]`, energy10, battery20, fee7, zero-energy pullout/pull-in, one20kW connector through120min and hourly markets. One cold charge-only QP <=20s, then one exact recovery <=30s. Known exact binary-coefficient optimum is `7+10*Fraction(.2)+25*Fraction(1/900)` (display9.027777...). Require exact objective equality, helper certificate and strict original physical replay. No generic old qualification is repeated and no artificial face-proposal corruption is claimed to be rejectable: a valid helper may legitimately recover from a changed proposal. Independent helper review is separately required.
2. FIXED_QP_RECOVERY: reconstruct the selected full public topology with all its original charging opportunities. One cold charge-only QP <=60s, then one helper attempt with limits dimension250,2million rational operations,16384bits,30s checkpoints. Native primal-simplex method0 is frozen for both literal and public charge-only QPs; no method fallback. Every original prefix SOC, shared-capacity row and full-refill equation remains in certification. Proposed zero/active faces use the helper's one frozen1e-7 rule; exact acceptance has no tolerance. The helper alone calls the independent original physical replay once if its exact primal/dual equality succeeds.
3. OWN_PRICE_LP: only after successful exact recovery, fix prices at the new certificate's exact binary-market gradient. One cold full-graph continuous energy-flow price solve <=60s, followed by independent exact dual reconstruction. Compare exported prices to the caller's exact vector. Full graph/all admitted fleet counts remain. Native status is no exact certificate.
4. OWN_PRICE_MIP: at those same fixed prices, one full-graph energy-flow integer price solve <=120s, with the recovered topology as binary-only start; acceptance UNKNOWN. Replay its new raw returned candidate exactly once. No automatic construction, terminal adjustment, price reset, or substitution of the recovered incumbent for this method's output.

If public recovery fails, preserve its stage/reason and mark both price states UNATTEMPTED with a dependency reason. Failure does not prove topology infeasibility. Successful fixed charging optimization does not prove global physical optimality. An exact full-graph response lower bound equal to the recovered candidate's exact private score would establish support; a native integer OPTIMAL status alone cannot do so.

Budget: package1200 inclusive CPU/1800wall seconds, worker1100CPU/1600wall, owner30soft CPU/1200hard CPU and1797wall cleanup boundary, one native thread and observed per-process RSS <=5GiB. Full source admission, construction, checker work, gzip serialization and publication are paid inside the worker/owner; external meter is authoritative for complete package cost. Helper wall checkpoints are not a process-level hard timer. No new process monitoring or automatic extension.

Detailed native/problem/recovery packets are streamed directly into gzip. Durable compact stage receipts and master assigned-state ledger preserve completed, failed and dependent-unattempted states. External previously certified witnesses are not method fallback successes. Stop on Q0 failure or fatal source/resource errors; no native or face retries. All inputs, command and remaining source revision remain subject to parent review/freeze.

Exact command after reviewed source and separate FROZEN control are pushed:
```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p .venv-local/bin/python -I -B research-20261029/public_fixed_topology/run.py --run-id attempt01 > research-20261029/public_fixed_topology/process-time-and-owner.txt 2>&1
```
Workingdirectory `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`.
Pre-packageprefix22195.75displayedCPU/23079.93elapsed-sum/22196.76retainedCPU.
Nooldpreparationreadoption. Legacyconditionalguard2546.091499549272separate;
actualtool/review/staticCPU UNKNOWN. Preserveeveryfailed/unknownstateandcharge.
Parent metadata-only helper adjustment beforefreeze retains any failed new
physicalreplay/candidate, and separates proposedactive rows from finaltight
dualrows. It does not change the face, native calls or acceptance conditions.
