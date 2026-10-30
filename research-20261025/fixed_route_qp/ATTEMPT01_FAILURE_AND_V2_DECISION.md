# First QP diagnostic stopped before optimization; deliberate v2 correction

25 October 2026. Attempt01 is CLOSED and immutable. Its first case,50600/40,
failed the combined bound/index/type clone readback before optimize. The helper
reported zero native calls and zero attempted native calls; all seven later
cases were undispatched. Worker22815 was reaped. External meter:0.92 elapsed,
0.63 user+0.09 system=0.72 CPU seconds. The valid common prior remains available.
This is a copy-contract failure, not physical infeasibility or model evidence.

V1 did not record the offending bound/index/type. Static inspection suggests
equivalent infinity representations could fail its exact raw-float test, but
does not establish that as the observed cause. The original protocol already
required semantic unboundedness. Gurobi documents LB<=-1e20 as negative infinity
and UB>=1e20 as positive infinity:
https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html

Parent chooses a NEW source-bound correction, not resumption or automatic retry:
qp_control_v2.py normalizes ONLY those side-specific unbounded sentinels at API
entry and readback. Every other finite bound, index/type, row coefficient/RHS,
objective, fixed topology and replay tolerance remains unchanged. Record bounded
examples and a detailed offending variable if a contract fails. No claim that
the cause is confirmed before reading this new diagnostic.

run_v2.py accepts fresh attempt02 only. Reuse the frozen predecessor preflight's
source/prior bindings under the continuing freeze assumption; hash that record
once plus only five new v2 source/protocol/resource/launch files. Do not rehash
unchanged prior plans/project sources/models. Full prior identity/replay checks
remain. One focused static delta review precedes a separately recorded launch.

Keep the SAME QP package1800CPU/2700wall,dispatch1620/reserve180 and all previous
charges. Nonrefundable attempt01 carry0.72CPU/0.92elapsed participates in funding
and final totals. Earlier cumulative7004.35/7177.22 becomes7005.07CPU/7178.14
elapsed-sum before v2. The separate legacy conditional guard2546.091499549272
and UNKNOWN actual historical review CPU remain. No comparison/training/cluster/
sealed-data scope follows. If v2 fails, preserve it and diagnose before a new
decision; never loop retries or silently weaken the copy/replay guards.
