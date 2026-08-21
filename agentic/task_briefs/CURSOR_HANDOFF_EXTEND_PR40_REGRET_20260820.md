# Cursor handoff: extend PR #40 with best-response regret accounting

Date: 2026-08-20 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` is unusable in this environment: Cursor agents authenticate
with a GitHub App integration token, which cannot call the `/user` endpoint.
The remote check plus dry-run push is the operative access gate.)

Do not push if the remote check or the dry-run push fails. No cluster commands, no
campaigns, no live B3/A6 outcome inspection, no seeds >= 16, no rebases,
no force-pushes, no merges. Synthetic/tiny local fixtures only; live solves
only in tests on burned seeds {0, 11, 15}, n_trips <= 8, CBC backend. Keep
the PR draft.

## Task

Continue PR #40 in place on `cursor/uplift-settlement-1d7b`, current head
`71468ed38153b130d8d9a468bfb0ee38d53f37a4`. Do not open another PR and do
not create a parallel settlement module — extend the existing
`src/experiments/uplift_settlement.py` schema so the project has exactly one
settlement evidence contract.

Additions:

1. **Versioned best-response evidence record** (extend the existing strict
   endpoint-only schema; bump its schema version): bind instance hash, full
   price vector and its hash, objective convention, the feasible
   schedule/load witness, solver identity, incumbent, certified dual bound,
   replay result, and evidence tier. Restricted-pool or heuristic evidence
   must never be representable as a global certificate — make the tier field
   structurally incapable of it (e.g. global bounds require the exact-oracle
   tier, enforced by validation).

2. **Price-conditioned regret.** For target schedule `s*`, prices `p`, and
   best-response value `V(p)` held as a certified interval `[LB, UB]`:

   ```text
   regret(s*, p) = max(0, private_cost(s*, p) - V(p))
   emitted interval: [max(0, target - UB), max(0, target - LB)]
   ```

   with `target = private_cost(s*, p)` computed from primitives, raw
   endpoints preserved alongside the clamped presentation values (same
   raw-versus-tightened convention the module already uses).

3. **Validation:** against complete tiny enumeration and against wrapped
   `regimes.solve_taker` calls on burned seeds; both must agree with the
   interval within the module's declared tolerance policy.

4. **A committed counterexample (as a test fixture, not prose):** an
   explicit tiny case demonstrating that internal uplift `z_D - z_CH` is
   NOT generally equal to price-conditioned regret at convex-hull prices —
   the test must exhibit the two differing intervals and assert the
   documented relation between them.

5. **Scope guards:** do not allocate payments per vehicle and do not claim
   individual rationality — single-fleet accounting only; say so in the
   module docstring. Adversarial tests for tampered hashes, bounds, and
   witnesses; deterministic JSON output.

6. **Cleanup:** move the committed `CURSOR_HANDOFF_UPLIFT_SETTLEMENT_20260820.md`
   out of the repository root — either delete it from the branch or fold its
   normative content into a proper `doc/SETTLEMENT_SPEC.md`. Task-prompt
   files are not repository documentation.

## Report

Focused and full test counts, the schema version bump and new record fields,
the counterexample's two intervals, and confirmation that no committed
result population was read and no new module was created. Leave the PR draft
for independent review.
