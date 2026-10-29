# DRAFT: complete-fleet responses at the newly certified physical plan's prices

Independent source review and separate source/control freeze are pending.
One new attempt01, assigned Q0, PRICE_LP, PRICE_MIP. No automatic follow-on
query, alternate price, repair or fixed-QP retry. Preparation involved no
actual gzip read, backend, import, execution, hash, test or commit.

## Protected transfer and input pins

Descriptor remains253c1e29295e766b3889fc8f5c28d9808e00b3d6 at the original
public_support_resolution/attempt01/case_descriptor.json. The new qualified
primal and dual packets are public_rational_recovery/attempt01/
PUBLIC_PRIMAL.json.gz and PUBLIC_DUAL.json.gz, both at
0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee. Their separate TRANSFER_AUTHORITY.json
is pinned to3cbb8c9d965e9222ef8a98191bf775b4925382a1. All paths are constants
in worker.py; authority paths/pointers are compared as metadata, never followed.

The source-bound producer is425bf35452eb3f5444f20058ad6fd6b540ffed88/control
869cae89. Require ADMITTED_PRIMAL, original strict physical/upper flags, exactly
one producer replay, CERTIFIED_FIXED_TOPOLOGY_OPTIMUM, independent certificate
check and exact equality of upper/lower/objectives across authority and packets.
Transfer only its certified physical upper, exact loads/ops/prices and route
selection. Do not rerun physical replay, rational recovery or dual phase I.
This is an external incumbent, never a new response-method fallback delivery.
Its fixed-topology lower is not a global response/hull lower certificate.

Reconstruct p_t=a+b*load_t exactly using original binary-stored a=.2,b=1/900.
Check transferred gradients, loads and exact cost against replay. Compute the
exact private score c+p.e and verify score-F*(p)=c+F(e). The vector remains
fixed for both response states regardless of any later candidate improvement.

## Qualification and response states

Q0 is new pure-stdlib transfer/certificate-identity algebra, no backend probe or
repeat of an earlier native Q0. Literal loads(0,2),ops1 exercise the zero-load
gradient and Fenchel identity with original binary coefficients. Three negative
controls alter the gradient, cost and load sign. Compare exact response bounds
equal to, below and above the private score: respectively exact support,
unresolved upper regret and contradiction. These are literal algebra outcomes,
not public support results.

PRICE_LP: one cold full declared-graph continuous energy-flow linear response,
60 seconds native/build cap. PRICE_MIP: one full declared-graph integer linear
response,180 seconds, with transferred movement IDs as binary-only start;
start acceptance UNKNOWN. No SOC/charge start or incumbent substitution.
Use unchanged energy_flow.py/native_recharge parameters, one Gurobi12.0.1
thread, all original arcs and all fleet counts allowed by the original case
and its independently proved minimum-fleet cut. No restriction to two buses,
selected plan bank, fixed topology, or additional cardinality exclusion.

The frozen exact_dual checker reconstructs the intended rational linear LP
and returns V_lower, or explicit unavailable/rejected outcome. Native Pi is
only a proposal; finite-box residual compensation supplies an exact bound.
Only exact V_lower==certified private_score proves support and D=CH. Native
OPTIMAL, native bound/gap or decimal equality cannot replace that criterion.
V_lower above the physical bill is a contradiction, retained as fatal, never
a negative regret or success. Loose bounds give score-V_lower as a regret
upper bound and leave support unresolved.

A fresh PRICE_MIP raw candidate, if returned, is saved and screened once by
the unchanged original independent verifier. Strict admission permits an exact
private score and possible regret lower bound; failures stay failed without
dropping reported fields, terminal adjustment, new QP or any repair. A
strict candidate score below an exact LP lower is a contradiction. Keep every
raw proposal, screen, certificate and failure in directly compressed packets.

## Authority, clocks and closure

Own worker.py/run.py/PROTOCOL.md bind to new source_revision. Cached immutable
energy_flow.py/exact_dual.py/independent_verify.py and src/egglab/{__init__,
native_recharge}.py bind to3278d50f8323618bd36809b1bbb1a0da081e23ff. All
source/input buffers are read once, git-byte-compared at their exact pins,
hashed on consumption once and then used from cached buffers. No alternate
source/data path or separate verification/export pass. The only native
dependency is Gurobi12.0.1, used in the two declared response calls.

Proposed NEW600CPU/900wall inclusive. Worker self530CPU cap, observed
inclusive550CPU/780wall/RSS5GiB; owner self soft30/hard600CPU, group timeout
780wall, alarm897wall and3seconds cleanup reserve. Before each native state
require its allowance plus120CPU and180wall closure reserve. Full LP state
cap150wall and MIP270wall include construction, native work, exact checking,
screening and completed gzip publication. Late/missing states are retained
and block successful closure; solver time alone is not the full stage clock.

Source admission, transfer parsing, cold imports, all construction/checking,
complete compressed/compact output, parent compact read and shutdown are paid
by outer POSIX time-p. Children overlap that inclusive charge. Local numerical
limits are not exact aggregate OS CPU or instantaneous memory containment.
Static/review/tool CPU is UNKNOWN. Parent inserts current global prefix at
freeze; no refund/reset or previous preparation adoption.

Intended command, pending reviewed exact frozen control and fresh console/time
paths: env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/time -p
.venv-local/bin/python -I -B
research-20261029/public_certified_price/run.py --run-id attempt01

Do not infer empirical prevalence, strategic tariff behavior, global support
failure, new ML evidence or operational savings from this single synthetic
public scenario. A valid support equality would establish only the declared
ideal-model support result at this stated posted-price institution.
