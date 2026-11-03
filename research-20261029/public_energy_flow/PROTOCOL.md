# Prospective exact energy-flow bound diagnostic

29 October 2026. New formulation and independent certificate checker for the
already exposed public depot15 case; not a repetition of a closed solve or a
new independent timetable. Runtime qualification remains PENDING until the
single frozen owner completes. This protocol, source closure and LAUNCH.json
must be frozen at separate exact Git revisions before execution.

## Scientific question and fixed assignments

Can a per-leg perspective energy-flow relaxation and its exact rational dual
certificate materially tighten the complete-fleet public lower bound? Can a
competent classical integer solve or response at the already certified plan's
own marginal prices provide an independently admissible new candidate? Preserve
all outcomes, including weak bounds, unavailable certificates, time limits,
unadmitted candidates, failed qualification and unattempted later states.

Five assigned states, in this immutable order:

1. Q0: literal two-service continuous QP, native allowance30s inside45s stage
   allowance. Services A[0,20] and B[30,50], each15kWh; battery20, fee7,
   direct A→B plus independent pullout/pullin arcs, maxfleet2; one40kW
   connector on[0,120], markets[0,60,120]. Derived minfleet2. The exact optimum
   is14+30*a+225*b, displayed20.25, with a=Fraction(float(.2)) and
   b=Fraction(float(1/900)). Require native objective agreement within1e-7,
   independent exact lower no greater than this value and within1e-7, and
   rejection of changed row RHS, finite variable bound, minimum-fleet proof
   metadata and objective. Failed qualification stops all public work.
2. ROOT_QP: continuous energy-flow quadratic model,90s native/build allowance;
   independent exact semantic-ledger and box-residual dual bound.
3. MIQP: integer energy-flow quadratic model,300s native/build allowance;
   transferred selected movement IDs as partial start; independently replay
   a newly returned integer candidate once under original physical rules.
4. PRICE_LP: continuous model at the fixed transferred own-price vector,60s;
   independently reconstructed exact linear lower certificate.
5. PRICE_MIP: same fixed-price integer model,240s; same partial route start;
   independent physical replay of a newly returned candidate once.

Public descriptor and every coefficient/movement/resource remain unchanged.
All allowed fleet counts remain; the derived minimum-fleet row is independently
proved from overlap or the consecutive-connection/no-recharge obstruction.
The physical optimum2 result is NOT used to restrict hull components or price
responses. There is no V2G, learned model, recovery solve, parameter sweep,
new query instrumentation, acquisition-free baseline or support-sign assertion.

## Exact input and source authority

The four source-defined paths and exact commits in LAUNCH.json are mandatory.
Case descriptor comes from253c1e29295e766b3889fc8f5c28d9808e00b3d6. The newly
qualified candidate, independent replay and TRANSFER_AUTHORITY come together
from929bd0052b064c2aa9ef10b77fa067b70c7653af. Worker compares each consumed
cached buffer to `git show REV:fixedpath` and hashes that buffer once; it never
follows metadata-supplied paths or separately repeats a hash audit.

The passed upper is transferred using the reviewed producer source ef0b0881,
control6ed44942, exact case identity, candidate field contract, strict physical
and objective flags and closed resource/exit metadata. No duplicate physical
replay of that passed candidate occurs. Its original cost stays paid. It is an
external protected upper and partial route start, never a new method delivery.
Every new native integer candidate needs a new independent strict admission.

Prices are computed once as a+b*certified_load from the transferred exact load
vector and original binary-float coefficients. They stay fixed for both price
states even if this run finds a lower quadratic candidate. The worker checks
the exported linear prices exactly against this vector before certificate use.

Cached local import closure: this worker.py/run.py/PROTOCOL.md;
public_support_resolution/{energy_flow.py,exact_dual.py,independent_verify.py};
src/egglab/{__init__.py,native_recharge.py}. Gurobipy12.0.1 is the only native
package. No native_pathflow/mip module or copied sibling solver is imported.
Every closure buffer is version-compared and hashed once inside the meter.
Native source may round coefficients; exact lower proof uses independently
reconstructed rational rows and finite boxes, including residual corrections.
Native OPTIMAL/status/gap does not certify exact feasibility or support.

## Exact execution and resource contract

Working directory `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`.
Exact parent command (once, only after FROZEN control is pushed):

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p .venv-local/bin/python -I -B research-20261029/public_energy_flow/run.py --run-id attempt01 > research-20261029/public_energy_flow/process-time-and-owner.txt 2>&1
```

The new package ceiling is1800CPU/2400wall seconds inclusive of source admission,
input loading, cold imports, construction, all native stages, exact checking,
gzip serialization, complete parent reads and publication. Worker ceiling
1700CPU/2200wall, parent CPU soft30/hard1800; parent2397s alarm and3s owned
cleanup inside total. At each stage require its complete allowance plus120CPU
and180wall closure reserve. One native thread, observed RSS<=5GiB. Observed
limits are not instantaneous containment. Full owner/self+waited-child meter
is authoritative at closure; children overlap that meter and are not added.

Build elapsed clips each native time allowance. A stage is timely only when
full construction, solve, checking and complete compressed packet serialization
finishes within native/build allowance+45s. Native time controls may overrun;
outer worker/owner ownership is decisive. Late state is preserved; no retry.
No-optimize status is distinct from a delivered native solve. Every assigned
state remains in master or administrative fallback, including source fatal,
worker failure and unattempted states. Failure never substitutes the protected
upper into the method result. Detailed new ledgers/candidates/checks are written
directly as gzip once; compact per-state/master receipts support closeout. No
separate numerical readout, export, finalizer, replay or audit follows.

Pre-package prefix:22020.27 displayedCPU/22901.21 elapsed-sum/22021.20 retainedCPU.
Separate legacy conditional guard2546.091499549272; static/tool/review actual
CPU UNKNOWN. This new package adopts no previous preparation again. Preserve
all old spending/failures; no reset/refund/exact-session accounting claim.

## Interpretation

Administrative completion, native method delivery, exact lower certification
and strict physical delivery are separate. A valid exact relaxation lower
bounds CH and D. A valid physical candidate upper bounds D. Neither alone
resolves strict D>CH. Any next construction/branch certificate must be a new
prospectively reviewed/frozen scope, with the failed/unadmitted current states
and their costs preserved. No automatic follow-on numerical call is authorized
by this manifest. Parent continues independent proof/draft work during execution.
