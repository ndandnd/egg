# Cursor handoff: harden PR #38 (tiny branch-and-price exactness laboratory)

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
no force-pushes, no merges. Synthetic/tiny local fixtures only. Keep the PR
draft.

## Task

Continue PR #38 in place on `cursor/tiny-branch-price-lab-352b`, current
head `0f796c722ac0bf40a5bab08fc642bef11444fbfe`. Do not open another PR and
do not expand into a campaign.

Independent audit findings to repair:

1. **Revert the `gurobipy>=13.0` line in `src/requirements.txt`.** The
   repository's design is CBC fallback with Gurobi optional and enforced
   only via `EGGLAB_REQUIRE_GRB` on the cluster; a hard gurobipy dependency
   contradicts that and breaks CBC-only CI installs. If the lab needs to
   document Gurobi as optional, do it in prose in the lab doc.

2. **One explicit tolerance ledger** covering: master/PWL error; pricing MIP
   bound; integrality; physical-load reconstruction; charge extraction;
   SOC/physics replay; the final global optimality gap. A claimed
   certificate must be wider than every propagated numerical error — the
   current claimed 1e-5 certificate is inconsistent with the 1e-4 physical
   replay tolerance. Require
   `pricing_bound <= physically reconstructed incumbent + declared allowance`
   and account explicitly for any dropped small charges instead of silently
   dropping them. Follow the EI-026/EI-027 lesson: one coherent
   operand-scaled tolerance policy, stated once.

3. **Expand validation beyond the single fixture** to:
   - burned seeds 0, 11, and 15 at n=4;
   - direct equality with the canonical compact dictator MILP
     (`regimes.solve_dictator` certificate) and tiny exhaustive enumeration;
   - **root-node cross-check against `b2a2.certified_cg`:** on at least one
     instance/market, the lab's root relaxation interval must intersect the
     `certified_cg` outcome interval (`lb_best`, `ub_ch`) at matching
     epsilon — the root IS `z_CH`, and this is the check that ties the lab
     to the B3 uplift object;
   - a tree deeper than one split;
   - a genuinely infeasible child node;
   - degenerate/tied pricing;
   - near-integral branching values;
   - interruption/resume during seed, master, and pricing phases, not only
     between complete nodes.

4. **Strengthen `audit_tree`** to reconstruct or cross-check node masters,
   dual pricing evidence, node bounds, the branching partition, the
   incumbent, and the global terminal bound from serialized evidence alone.
   If full reconstruction is impossible from what is serialized, downgrade
   the claim wording from "independently certified" to "solver-attested" —
   never let prose outrun the evidence.

5. Keep the result explicitly a tiny exactness laboratory, not a scalable
   exact solver; the lab doc must say so.

## Report

Focused and full test counts, the final tolerance ledger table, the observed
cross-validation intervals on seeds {0, 11, 15}, whether audit_tree achieves
full reconstruction or the claim was downgraded, and confirmation the
requirements.txt change is reverted. Leave the PR draft for independent
review.
