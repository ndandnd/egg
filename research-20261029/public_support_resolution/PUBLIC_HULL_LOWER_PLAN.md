# One fixed-price all-fleet hull-lower certificate: prospective assessment

Source-only mathematical/API plan, not implementation or dispatch authority. Uses the already reviewed tree checker/producer and energy-flow contracts; no complete source reaudit, actual artifact/gzip, numerical calculation, hash, import, test, backend call, commit or new agent.

## Correct certificate and attainable goal

Let the already qualified complete-plan mixture have mean load ubar, mean operating cost cbar, and admitted upper H=cbar+F(ubar). Freeze `p=gradient F(ubar)` and `k=F(ubar)-p·ubar` exactly from the original stored binary coefficients. For every physical plan x,

`c(x)+F(u(x)) >= k+c(x)+p·u(x)`.

The same affine inequality holds on the complete-plan hull. Thus any certified **all-fleet** lower L_V for `V(p)=min_physical[c+p·u]` gives

`L_CH=k+L_V <= CH <= H`.

For the unrestricted quadratic formula, k equals `-sum b_t*ubar_t^2/2`; no new hull optimizer is needed. A prospectively fixed accuracy goal epsilon=1/10000 can require `H-L_CH<=epsilon`. Equivalently the linear oracle must certify `L_V>=H-k-epsilon`. Exact equality is unnecessary, and outward decimal displays must not control this comparison.

**A material limitation:** p from the best point on an existing two-plan segment need not be a global hull-optimal price. Even an exact V(p) may leave `H-[k+V(p)]>epsilon`. Therefore this one frozen-price exercise cannot promise the requested accuracy. Failure to close may be an intrinsic limitation of that price/mixture, not poor branch search or loose arithmetic. A strictly admitted physical response below the threshold would prove this fixed-price target unattainable; a merely weak relaxation lower would not. Changing p or the mixture would be a separate optimization task, not an automatic continuation.

## Smallest sound new oracle

Use a fresh continuous energy-flow model on the entire original graph and admitted fleet range. Retain the independently valid minimum-fleet-two cut, **omit the exact-two equality**, and impose no higher-fleet exclusion by default. Set the objective to intrinsic operations plus `p·loads` (`a=p,b=0`), identically in the native proposal and exact checker.

Branch only on original movement binaries, retain both children and every unresolved fringe, and independently check each linear finite-box residual lower or positive infeasibility contradiction. A complete bound fringe gives `L_V=min leaf lower` even when search remains open below the requested threshold. Nodes can stop at any depth once their exact lower reaches the frozen V threshold. An all-infeasible tree would contradict the admitted physical components and must be treated as a diagnostic contradiction, not promoted into an infinite useful hull lower.

The unchanged checker already supports `prepare(...,mode='linear',prices=exact_p,fleet_count=None)`, exact linear `verify_node`, and complete `verify_tree`. Its global scope is V(p); it does not incorrectly call a linear tree a direct nonlinear physical lower. Unlike quadratic branching, linear minimization over complete physical plans equals minimization over their hull. The final external operation `k+L_V` is what yields the nonlinear CH lower.

The energy-flow builder supplies a full continuous model and `solve(method='linear',prices=p)` can export one exact-ledger/Pi proposal. Existing all-fleet exact_dual verification is suitable for a root lower. A reused linear native model and the tree checker can then handle branch proposals, provided row names/finite boxes match the fresh semantic reconstruction. A single LP per node with its prescribed infeasibility evidence suffices; no native QP or old quadratic root is required.

The current producer cannot be reused unchanged: it hardcodes quadratic objective, exact-two fleet equation, typed physical>=3 floor, and target as a hull upper to separate from D. The minimal new producer must explicitly parameterize or narrowly replace those parts with all-fleet linear semantics and a V threshold. It must not silently feed a quadratic certificate or physical-only floor into this plan. No such producer change is implemented here.

Optional count exclusions would need fresh exact-price-specific service floors, such as `N*fee+min(p)*service/eta` under all nonnegativity assumptions, and explicit coverage of every omitted count. With no strong necessity demonstrated, retaining all counts is simpler and safer. The old nonlinear477.82 floor cannot be reused at these prices.

## Separate source-bound metadata admission

A prospective paid extractor, frozen separately before use, may consume only the already qualified mixture's source-bound authority/packet at fixed commits/paths. It should emit:

- case identity, descriptor path/revision and original binary a/b coefficients;
- producer source/control/namespace, actual packet revision and exact mixture-check/physical-component admission requirements;
- exact ubar, cbar, H, mixture weights and component identities, plus dimension and nonnegative-load checks;
- exact p, k and the identities `H=cbar+F(ubar)` and `k=F(ubar)-p·ubar`;
- exact epsilon, linear oracle target `H-k-epsilon`, and fixed full-fleet domain;
- completed producer/reaping/resource provenance, extractor closure and explicit no-replay/no-hull-reoptimization scope.

Future consumers must byte-admit this actual committed transfer record, compare fixed paths/identities, recompute cheap exact algebra once inside their paid package, and never follow artifact-provided paths. Neither an arbitrary load vector nor the mixture's existing physical-D exclusion record is sufficient authority. Extraction is new paid metadata/algebra work; it must not be described as already performed here.

## Bounded resource proposal and stopping rule

For parent consideration only: a single prospective package ceiling of **900 inclusive CPU/1200 wall**, one native thread, observed5GiB RSS, at most255 total tree nodes/300 native LP calls, each LP at most10seconds including setup/reoptimization, with **180CPU/240wall reserved** for independent final semantic coverage/audit/publication. Debit source admission, extractor/qualification and model construction before deriving actual search funding; require full next-call/check/closure allowances. Counts and ceilings are concurrent constraints, not promises that all nodes receive their maximum time. No automatic extension or changed-price retry.

Freeze a small new linear-objective qualification including all-fleet versus exact-two distinction, altered p/k/target rejection, exact direct-value scalar anchors, inherited branch coverage, open/resource-failed states and final `k+L_V` identity. Give the final checker explicit node/depth/operation/fraction limits sized for the declared cap, not an accidentally smaller default. Complete package clocks include metadata parsing, exact checks, materialization, compression and shutdown; external meter is authoritative.

A closed result should report admitted H, exact p/k, global L_V and L_CH, exact residual interval width, and whether the predeclared epsilon was met. If no complete valid lower is available, report unresolved with every paid state retained. This could materially tighten the current magnitude interval, but the existing small positive-gap sign certificate remains unchanged whether or not this optional precision goal succeeds.
