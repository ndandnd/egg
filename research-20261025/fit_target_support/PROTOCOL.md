# FIT paired-target support audit — prospective 25 October 2026

Question: do the fixed declared FIT examples contain different binary movement
targets under their two source-price contexts, with consistent physical and
market/plan identity? This follows the completed metadata audit, not a refit,
attempt to rescue the warm-study gate, or a new model-performance evaluation.

## Exact inputs and access authorization

The only data inputs are:

1. Completed selected metadata receipt:
   `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/train_readiness/attempt01/receipt.json`.
2. `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl`,
   expected original-byte SHA256
   `faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6`.
3. `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl`,
   expected original-byte SHA256
   `7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5`.

Parent explicitly adopts **routing-only transient JSON decoding of mixed TRAIN
tables** under the human's standing authority for practical rigorous research.
No additional permission question is pending. Whole-file hashing reads every
TRAIN byte. Standard-library `json.loads` temporarily decodes each complete row;
this is not FIT-only byte access or identifier-only parsing. On non-FIT rows,
consult only top-level `base_group` (and base_id if needed for routing) and
immediately discard the object. No other non-FIT value may be semantically
inspected, compared, retained, exported or used for selection. No historical
model outer performance, outcome table or sealed bank is opened. This limited
routing authorization does not open general non-FIT label analysis.

The exact FIT IDs come from BOTH selected preprocessing projections inside the
completed receipt. Require their lists to reconcile to the same80 unique groups;
do not choose an intersection or a new subset. Expected sources:79 complete
source0/source1 pairs and one incomplete group, physical_v2_s10037/source1 only,
159 observed source records. Preserve all80 intended groups and every unexpected
missing, duplicate or invalid record. No replacement or automatic retry.

The only extra identity inputs are the reviewed audit source, this protocol and
LAUNCH.json. Do not follow paths from metadata/rows, import a training loader,
regenerate cases, load model weights, fit, infer, solve or physically replay.

## FIT semantic field contract

Cases: `base_group, base_id, split, generator, physical_profile, case_identity`
and the stored `case` dataclass fields needed to bind its identity and movement
universe. The precise nested field/default contract is in IDENTITY_SOURCE_MAP.md
and ROW_SOURCE_CONTRACT.md; unknown fields are not silently discarded.
Exclude `witness_hash` from semantic analysis. Require TRAIN group/base joins;
no call to a case generator or make_witness.

Source inputs: `key, base_group, base_id, case_identity, market_identity,
market_kind, source, source_plan_hash, selected_movements`. Inside source_plan,
semantically inspect only schema/case identity and each vehicle's ID, trips and
movement membership. Do not inspect costs, charges, loads, raw variables, replay,
roundoff evidence or `source_replay`. Composite provenance extras do not expand
the whitelist. **The whole unmodified FIT source_plan may be serialized for its
canonical digest only**, including auxiliary fields; hashing a projection would
not reproduce its identity. No raw plan or membership vector is published.

Use the original default-spaced sorted-key JSON SHA256 convention without float
coercion, rounding, compact separators or array reordering. Case identity includes
`schema=egg-native-recharge-v1` and reconstructed stored dataclass values/defaults;
market identity includes exactly name/a/b. Construct the source-defined market
dictionary on the stored case name/grid, not a new case: source0 a=.20;
source1 a=.10 at periods18–21/.30 otherwise; both b=1/900,30 periods. Require its
identity and the common physical grid to match before reporting source-bound
price differences. These are internal stored-contract checks, not verification
of historical solver execution or real-world market observations.

Require a unique ordered movement universe, unique selected IDs and no unknown
IDs, with selected_movements agreeing with the vehicle-movement membership.
Preserve parallel movement modes. No charge feasibility or optimality claim.

## Once-only descriptive output and interpretation

After whole-table pins pass, publish compact group-level identities/counts and
statuses for all80 intended groups. Expected79 complete pairs are the planned
paired denominator; the incomplete group is a missing comparison, never zero
disagreement. Report every mismatch and actual admitted denominator. No
available-only positive readiness/promotion gate.

For each internally admitted pair in the same universe M, compute positive-set
sizes, intersection/union, directional/symmetric differences, Hamming D/M and
positive-set Jaccard disagreement D/union. Include movement-kind counts and the
flexible direct/depot subset so boundary positives and many negatives cannot
conceal relevant target variation. A zero positive union has undefined Jaccard,
with its own denominator, not a rejected physical source or forced zero fraction.
Record the two source vehicle counts/equality so movement changes are not
mistaken for a fixed-fleet price contrast. Report identical/different pair counts and
equal-group mean/median descriptions; do not treat all edges as independent
observations. No significance test, useful-effect threshold or model selection.

Different labels under price contexts establish observed conditional target
variation once identities agree. They do not separate price response from
teacher search noise, budgets, initialization or incumbent quality. Identical
binary labels do not rule out cost/charging changes or other targets. No result
establishes information value, optimal supervision, matched teacher comparability,
new-population transfer, GNN pool lineage, or permission for an aware/blind fit.
The failed warm-study margin and its cohorts remain unchanged.

## Practical resource/receipt contract

Total300CPU/600wall seconds, body270CPU/540wall and30CPU/60wall closure reserve,
inclusive of startup, byte admission, identity checks, summaries, publication and
exit. One standard-library process/thread, observed peak RSS<=5GiB. JSONL files
are capped at512MiB each and lines at16MiB; prior receipt/identity files at8MiB.
Streaming retains only needed FIT data; no unbounded row/raw-plan captures.
Check original file stability and hash original bytes once during the same
filtering pass, not independent repeated hash audits. Canonical object identity
hashes are distinct from original-file hashes and are recorded as such.

Fresh exclusive `attempt01` owns its placeholder/final receipt. Preserve a
failed/incomplete attempt and every charge; do not retry automatically. No source
editing while it runs. One focused static review, then freeze exact source,
input/field allowlist, command and output namespace in LAUNCH.json before dispatch.
No test matrix or new timing/transport/parser framework. This protocol alone is
not an executable launch manifest.

Prior displayed process sums19638.14CPU/20223.92elapsed-sum and retained tracking
19638.16CPU (metadata rounding charge included) are carried without resetting.
Legacy conditional guard2546.091499549272 and unknown historical review CPU remain
separate. Add the new external meter once; do not claim exact whole-session CPU,
continuous elapsed or restored historical compliance. No cluster/sealed-data
permission follows. No Google Doc update for preparation; append later verified
science only if substantive.
