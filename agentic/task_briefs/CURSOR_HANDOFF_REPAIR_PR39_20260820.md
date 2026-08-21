# Cursor handoff: repair PR #39 (strict two-cycle witness)

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

Continue PR #39 in place on `cursor/strict-cycle-minimizer-4a64`, current
head `3666f914ab7c589437684523af3dae065642f457`. Do not open another PR.

Independent audit findings to repair:

1. **CBC replay failure from backend degeneracy.** The committed witness
   requires exact nested equality for non-unique feasible LP realizations,
   so equivalent charging optima (e.g. slot 12 versus slot 13) fail replay
   under CBC. Reproduce this failure independently first.

2. **The degeneracy is not only a serialization problem — it threatens
   well-definedness of the cycle map itself.** If the best-response *load*
   at either cycle price vector is non-unique (interchangeable charging
   across equal-priced slots), then `p^{k+1}` depends on the solver's
   arbitrary tie-break and the "strict 2-cycle" may not survive a different
   backend. You must do one of:
   - certify load-uniqueness at both cycle states — for example, for each
     slot `t`, minimize and maximize `L_t` over the optimal face of the
     fixed-partition charging LP and require zero width beyond tolerance; or
   - prove and test that the cycle is invariant across the entire
     optimal-charging polytope at both states (every optimal load selection
     maps to the same successor structure with the same strict margin).
   State in the witness doc which of the two certificates the witness
   carries. If neither holds for the current 4-trip core, the construction
   must be perturbed (e.g. slot-price asymmetry) until one does — a witness
   whose cycle depends on solver tie-breaking is not a witness.

3. **For nonwinning/nonunique structures** (the enumeration inventory, not
   the two selected cycle states): serialize and compare invariant
   certificate fields (structure identity, objective value, feasibility)
   rather than arbitrary optimizer-selected charge vectors — unless you
   implement and prove a backend-independent lexicographic canonicalization.
   Preserve exact physical replay for the two selected cycle states.

4. **Correct the fixed-point objective everywhere** to
   `ops + (a + B U) . L + 0.5 L^T B L`, not `ops + a . L + 0.5 L^T B L`.
   The current `U = 0` witness remains valid, but the general lemma text and
   any code implementing it must include the base-load term. Add a test with
   `U != 0` proving the corrected form.

5. Add: a backend-degeneracy regression fixture with two equivalent charge
   realizations; a standalone CLI replay run under CBC; tampering tests
   proving the invariant comparison was not weakened into accepting
   arbitrary edits; explicit wording that "irreducible" means 1-minimal on
   the tested deletion axes only.

6. **Artifact protocol:** regenerate `result/strict_two_cycle/WITNESS.json`
   only after all tests pass, in a separate artifact-only commit whose
   manifest/summary names the exact analysis-code commit it was generated
   from (code-first, artifact-second).

## Report

Focused and full test counts, the reproduced-then-fixed CBC replay
demonstration, which uniqueness/invariance certificate the witness now
carries and its margins, and the two commit SHAs (code, artifact). Leave the
PR draft for independent review.
