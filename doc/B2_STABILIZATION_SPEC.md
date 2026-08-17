# B2 stabilized column generation: mathematical specification (A3-A5)

Status: prespecified BEFORE implementation and before any stabilization run,
per `MEASUREMENT_RESULTS.md` Section 8. This file is the normative reference
for `src/egglab/b2a345.py`. The A2 (plain CG) machinery, certification
contract, and transactional architecture are unchanged from
`src/egglab/b2a2.py`.

## 0. Common ground

Master (identical for all methods; one fleet convexity block):

    z_CH = min   sum_j lambda_j c_j + DeltaC(L)
           s.t.  sum_j lambda_j e_jt - L_t = 0     (link_t, dual pi_t)
                 sum_j lambda_j = 1                 (conv,  dual sigma)
                 lambda >= 0, L >= 0,

with DeltaC the true convex quadratic system-cost increment,
DeltaC_t(L) = c1_t L + b_t L^2 / 2, c1_t = a_t + b_t U_t.

**Certified dual (Lagrangian) value.** For ANY price vector p (= -pi),
weak duality gives the certificate-grade value

    Theta_cert(p) = pricing_bound(p) - sum_t conj_t(p_t),
    conj_t(p)     = max(0, p_t - c1_t)^2 / (2 b_t)      (b_t > 0),

where `pricing_bound(p)` is the CERTIFIED dual bound of the exact taker
EVSP MILP at prices p (never the incumbent). Theta_cert(p) <= z_CH for every
p; it drives serious/null decisions only (see the certification contract).

**One oracle call** = one invocation of the exact taker EVSP MILP at one
full price vector. Clean certification pricing and stabilized candidate
pricing each count as one call, are separately logged (`regime`
`cg-pricing` vs `cg-stab-pricing`), and both draw down the same 240-call
budget.

**Iteration skeleton (all of A3-A5).** Each master iteration performs:

1. Solve the CLEAN, ordinary, unstabilized RMP over every generated column
   (tangent refinement to `pwl_tol`), yielding `UB_CH` (exact evaluation)
   and clean duals `(pi, sigma)`. `UB_CH` never comes from any stabilized,
   penalized, smoothed, or box surrogate.
2. Clean certification pricing at `p = -pi`:
   `LB_CH = z_model + min(0, pricing_bound(p) - sigma)`, `LB_best`
   monotone. Certified iff `UB_CH - LB_best <= epsilon = 1e-2`.
3. If not certified and budget remains: ONE stabilized candidate step
   (method-specific below) produces candidate prices `p_cand`; one
   candidate oracle call at `p_cand`; the incumbent schedule enters the
   column pool if novel; `Theta_cert(p_cand)` decides serious vs null.

**Serious/null step (common rule).** Let `Theta_best` be the best
`Theta_cert` observed at any priced point so far (initialized at the first
clean call). A candidate step is SERIOUS iff

    Theta_cert(p_cand) > Theta_best + 1e-9,

in which case the stability center moves to the candidate dual point
(`pi_hat <- -p_cand`) and `Theta_best` updates; otherwise it is a NULL step
and the center stays. Method parameters update as specified per method.

**Stability center initialization (all methods):**
`pi_hat^0 = -(a + b*U)` — the posted marginal price at zero fleet load.

**Broadcast-price trajectory** (doc metric 3): the sequence of price
vectors the negotiation posts to the fleet — for A2 the clean-dual prices
of successive iterations; for A3-A5 the CANDIDATE prices `p_cand` of
successive iterations. Reported per cell as the maximum L-infinity step and
the total variation `sum_k ||p_{k+1} - p_k||_1` over that sequence (clean
certification prices are additionally logged on every call).

**Certification contract (binding).** Stabilization only guides which
columns are generated. `UB_CH` is always the clean RMP objective over all
generated columns with exact cost evaluation; `LB_CH` for certification is
built ONLY from clean-dual certification calls (their certified pricing
bounds via the Lasdon formula). `Theta_cert` of stabilized calls is logged
as a diagnostic lower-bound witness but is NEVER folded into `LB_best`.
Certification: `UB_CH - LB_best <= 1e-2`. Uplift interval unchanged:
`[(z_D_ub - tol_D) - UB_CH, z_D_ub - LB_best]`.

**Backend and tolerances.** python-mip over Gurobi (Unicorn; enforced by
`EGGLAB_REQUIRE_GRB`) or CBC (local tests). All masters are pure LPs.
`epsilon = 1e-2`, `pwl_tol = 1e-3`, `rc_tol = 1e-6`, replay tolerance and
oracle settings unchanged from A2. python-mip supports NO quadratic
objectives on either backend — see the A5 note.

## 1. A3 — du Merle 5-piece box + linear penalty

**Stabilized master** (du Merle et al. 1999; 5-piece dual penalty as in Ben
Amor-Desrosiers-Frangioni 2009). The dual penalty around center `pi_hat_t`:

    psi_t(pi) = 0                                   |pi - pi_hat_t| <= D1_t
                zeta1 * (|pi - pi_hat_t| - D1_t)    D1_t < |.| <= D2_t
                zeta1*(D2_t-D1_t) + (zeta1+zeta2)*(|.| - D2_t)   beyond D2_t

(five linear pieces: slopes -(z1+z2), -z1, 0, +z1, +(z1+z2)). Primal
realization: four auxiliary variables per link row t, appended INSIDE the
link constraint `sum_j lambda_j e_jt - L_t + y1p - y1m + y2p - y2m = 0`:

    y1p >= 0, ub zeta1, cost (pi_hat_t + D1_t)
    y2p >= 0, ub zeta2, cost (pi_hat_t + D2_t)
    y1m >= 0, ub zeta1, cost -(pi_hat_t - D1_t)
    y2m >= 0, ub zeta2, cost -(pi_hat_t - D2_t)

(each bound is a penalty slope, each cost a breakpoint; standard LP-duality
correspondence). Candidate prices: `p_cand = -pi_stab` where `pi_stab` are
the link duals of this stabilized LP. The stabilized LP's objective and
primal solution are NEVER used for bounds.

**Prespecified parameters** (recorded in the resume identity):

    D1_t^0 = 0.05 * (1 + |pi_hat_t^0|),   D2_t = 10 * D1_t,
    zeta1  = 0.1,  zeta2 = 100            (kWh-scale penalty slopes).

**Updates.** On a SERIOUS step: center moves (common rule) and the box
shrinks, `D1_t <- max(D1_min_t, D1_t / 2)` with
`D1_min_t = 1e-4 * (1 + |pi_hat_t^0|)`, `D2_t = 10 * D1_t` throughout.
On a NULL step: no parameter change. `zeta1, zeta2` are constant.

## 2. A4 — Wentges dual smoothing + automatic alpha

**No stabilized master.** Candidate duals are the Wentges (1997) convex
combination of the stability center and the current clean RMP dual (the
"out" point):

    pi_tilde = alpha * pi_hat + (1 - alpha) * pi_out,
    p_cand   = -pi_tilde.

**Automatic alpha (Pessoa-style; see under-specification note).** After
each candidate call, compute the dual-function subgradient at the smoothed
point,

    g_t = e_t(S_tilde) - Lstar_t(p_cand),
    Lstar_t(p) = max(0, (p_t - c1_t) / b_t),

(`S_tilde` = the candidate call's incumbent schedule; `Lstar` = the
Lagrangian load minimizer). With direction `d = pi_out - pi_tilde`:

    if <g, d> > 0 :  alpha <- max(0,    alpha - 0.1)          (less smoothing:
                                                the dual function still rises
                                                toward the out point)
    else          :  alpha <- min(0.99, alpha + (1-alpha)/10)  (more smoothing:
                                                the out point overshoots)

Initial `alpha = 0.5`, bounds `[0, 0.99]`. Serious step: common rule
(center <- pi_tilde on Theta_cert improvement). Mispricing needs no special
sequence here: the clean certification call at `pi_out` happens every
iteration by construction, so a smoothed misprice can never stall
certification.

## 3. A5 — quadratic proximal (bundle-style)

**Stabilized master.** Dual proximal objective
`Theta_R(pi) - ||pi - pi_hat||^2 / (2 t)` with stepsize parameter `t`
(larger `t` = weaker pull to the center). Primal realization: a free
deviation variable `d_t` in each link row with convex cost
`pi_hat_t d_t + d_t^2 / (2 t)`.

**Backend constraint (documented deviation).** python-mip cannot express
quadratic objectives on either backend, so the quadratic penalty is
represented by its chord piecewise-linear model: K = 16 pieces per side,
half-width `W_t = 2 * (1 + |pi_hat_t^0|)`, piece width `h_t = W_t / K`;
piece k in {0..K-1} contributes primal variables (same duality pattern as
A3) with breakpoint offsets `u_k = k * h_t` and incremental slopes
`h_t / t` each, i.e. penalty derivative `~ (pi - pi_hat)/t` sampled at the
breakpoints; beyond `W_t` the final slope `K h_t / t = W_t / t` continues.
The chord model over-penalizes by at most `h_t^2 / (8 t)` per row — a
candidate-quality effect only; certificates never touch the stabilized
master. The QUADRATIC parameter dynamics below are exact.

**Prespecified parameters:** `t^0 = 1.0`, `t_min = 1e-4`, K = 16, `W_t` as
above (recorded in the resume identity).

**Updates.** SERIOUS step: center moves (common rule), `t` unchanged. NULL
step: `t <- max(t_min, t / 2)` — the doc's "parameter halved on null
steps", read as the proximal stepsize/trust parameter (see
under-specification note).

## 4. Genuine under-specifications (reported, not silently resolved)

1. **A3 box geometry.** `MEASUREMENT_RESULTS.md` prespecifies "du Merle box
   + linear penalty (5-piece), center updated on serious steps" but no
   widths or slopes. The values in Section 1 are project-prespecified here,
   before any stabilization run, and enter the resume identity; they were
   NOT tuned on any evaluation cell.
2. **A4 automatic rule.** The cited Pessoa et al. automation is implemented
   as the subgradient in-out test above with increments
   `alpha - 0.1` / `alpha + (1-alpha)/10`. This is the standard form of
   their alpha-schedule, but the exact published constants have not been
   verified against the paper's full text (it is on the reading queue). The
   implemented rule is therefore normative for this project and is stated
   exactly; any post-audit correction would be a new prespecification, not
   a silent change.
3. **A5 "parameter halved on null steps".** The doc line does not say
   whether the halved parameter is the penalty WEIGHT (u, halving = weaker
   stabilization) or the proximal STEPSIZE/trust (t = 1/u, halving =
   stronger stabilization). Standard proximal-bundle practice tightens
   after null steps, so t-halving is adopted. This interpretation is
   normative here and recorded in the identity.
4. **A5 quadratic penalty via PWL.** python-mip exposes no quadratic
   objective for either CBC or Gurobi; the exact-QP master would require a
   direct gurobipy model, forking the implementation across backends and
   breaking local determinism tests. The chord-PWL realization above (with
   documented over-penalty bound) is used on BOTH backends. Certificates
   are unaffected by construction.

## 5. What is logged (per cell, superset of A2)

- Every oracle call: stable cell-local id `a{M}-oc{n}`, kind
  (clean/stabilized), full record (status, incumbent, certified bound,
  gap, sizes, backend, threads, wall, replay evidence).
- Every master solve (clean, and stabilized for A3/A5): stable cell-local
  id, status, objective, bound, n_vars, n_int, n_constrs, wall, threads;
  stabilized master solves are marked `stabilized: true` and are never
  counted as clean solves.
- Every iteration: phase (`clean` / `stabilized` / `terminal`), UB/LB,
  certificate gap, Theta_cert, serious/null decision, parameter values
  before/after, candidate price stats, novelty.
- Outcome: certified / budget_exhausted (valid but distinct), final gap,
  uplift interval, broadcast-price L-infinity max step and total variation,
  oracle-call split (clean vs stabilized).
