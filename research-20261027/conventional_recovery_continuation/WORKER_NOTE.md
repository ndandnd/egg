# Repaired conventional recovery continuation: source only

The continuation worker is a minimal adaptation of the frozen pilot worker.
The pilot sources and outputs are preserved. The fixture is an identical copy:
constructor ID `conventional-recovery-v1`, original construction token, seeds
62001–62004, sizes 12/24, source quotes, graph, physics, resources, and cost
constants are unchanged. No descriptor values have been generated here.

The only algorithm-entry repair is an explicit `import gurobipy as gp` in the
shared UN/UD branch, replacing its lookup in `sys.modules`. The backend import
now occurs in the consuming union process before the existing model creation.
The solver, builder, physical checker, and original pricing-workload helpers
remain references to their original sources. No solver implementation is copied.

All 40 assignments remain declared. The first 62001/12 F, N, and D producers
are reuse-only: the continuation worker rejects direct execution of those
three states. Its other 37 states belong to this directory's fresh `attempt01`
namespace. The failed old UN is not reusable and receives no old-data authority.

The sole old-data exception is the three literal producer folders under
`research-20261027/conventional_recovery_pilot/attempt01`, with source revision
`234668a879f31c3a49254adf6e313f8fbdfaa1a6`. Every other dependency is derived from
the new continuation namespace and must have the continuation's source revision.
Caller-supplied paths never choose a file. Old dependencies are chosen only
when seed is exactly 62001, size exactly 12, and phase exactly F, N, or D.

The frozen launch `reuse_contract` has exactly these outer fields:
`master_path`, `expected_master_sha256`, `source_revision`, `control_revision`,
and `rows`. The master path is the literal pilot `attempt01/receipt.json`;
its hash must be a valid frozen SHA256 pin. Old source revision is the literal
above and old control revision is `c7c69a75`. `rows` has exactly keys
`B62001-N12-F`, `B62001-N12-N`, and `B62001-N12-D`. Each row has exactly the
unchanged dependency fields: `folder`, `spec_sha256`, `receipt_sha256`,
`selected_sha256`, `bank_sha256`, `strict_delivery`, `physical_valid`, and
`bank_qualified`. All four producer file pins are required; flags remain typed
booleans. A consumer's reused dependency must equal its frozen row exactly.

The parent performs the separately metered master metadata binding/admission
and freezes the row packets. The child validates the contract and each consumed
producer's pinned spec/receipt identity, source revision, timeliness, paths,
flags, and file hashes through the existing once-read input path. It does not
read the old master or rehash a whole old-source inventory. Only each necessary
spec, receipt, selected fleet, and whole journal is consumed; no arbitrary old
artifacts are admitted. Original record realization/cost admission and common,
candidate, and retained joint physical validation remain inside each consumer's
paid clock. No input buffer is reread for a second hash pass.

The original F/N/D discovery policy, whole-bank qualification without a selected
endpoint, completed-D final post-dive digest authority, canonical union
membership, F protection, strict fresh-candidate delivery semantics, objective,
native parameters, model rows, budgets, signal caveat, and resource ceilings are
unchanged. In particular, a valid timely native candidate can establish strict
delivery while the keeper retains a tied or cheaper F common; fallback alone
cannot establish strict delivery. NoSelection does not itself disqualify an
otherwise timely, fully admitted producer bank.

This is source preparation only. No worker or fixture import, execution,
compilation, test, hash computation, backend call, bank or old-artifact read,
campaign repeat, or commit was performed. These files establish no runtime
qualification claim. Frozen control and review gates still govern execution.
