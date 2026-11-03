# Union backend import repair: source-only review

The reported owner63025 attempt is CLOSED with exit 1. Its F/N/D states for
62001-N12 delivered strict, physically valid endpoints. The first UN state
failed at `union_native` with `KeyError: 'gurobipy'` before any optimize call;
the remaining 36 states were unattempted. These outcome facts were supplied by
the parent; no campaign outputs or banks were read for this diagnosis.

The frozen worker's union branch retrieves `sys.modules['gurobipy']` immediately
after admitting its inputs. Each state has a fresh Python process. Bootstrap
loads the sibling runner, but that runner imports Gurobi lazily inside `run`.
F/N/D invoke `run` before their backend lookup; UN/UD directly construct the
finite-bank model and never invoke `run`. A successful producer state therefore
cannot populate the union process's module registry. The union's direct lookup
raises the reported KeyError when that backend has not yet been imported.

The original pricing-workload worker's independent cache branch explicitly
uses `import gurobipy as gp` before constructing its model. The separate
`IMPORT_REPAIR.patch` makes the same one-line replacement in the union branch.
It leaves the surrounding model construction, parameters, budgets, bank
admission, physical checks, fallback, and optimize-call policy unchanged.

This is sufficient to remove this specific missing-registry-entry assumption:
Python imports the backend into the current union process and binds `gp` before
the existing `gp.Model(...)` call. It does not establish that import, licensing,
model construction, solving, timing, or downstream receipt admission will
succeed. Both UN and UD share this repaired branch. No solver implementation
is copied or changed.

The patch is a review artifact only. It has not been applied to the frozen
worker. No import, execution, compilation, test, hash, backend call, raw-bank
read, campaign repetition, or commit was performed. The closed attempt remains
closed; these files neither retry a failed state nor replay completed states.
Any future repair application and qualification require a separately reviewed
source/control identity and an explicitly authorized prospective run. This
source-only diagnosis provides no repaired-runtime or completed-campaign claim.
