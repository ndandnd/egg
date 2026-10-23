# Proposed recovery study — 23 October 2026

**Proposal only; no automatic launch.** Implement and pass
`RECOVERY_QUALIFICATION_PROTOCOL.md`, then freeze a separate study manifest, source/asset
lock and spending authorization before any cohort scoring or solving. Existing 360-cell
screen supports eligibility, not confirmation on reused timetables. Sealed DEV/TEST/A6/B3/
confirmation/GIRO remain unopened. No training, model selection, cluster or blind sweep.
The FT50 research ambition is a goal, not an achieved evidential standard.

## Question and fixed treatments

Does restoring the full connection graph after a pruned acquisition stage improve
finite-budget replay-valid bills versus static pruning, and does that increment depend
on the frozen ranking source? Use exactly the existing graph-v8 task00, fitted 17 October
CatBoost, frozen nonlearned score, and matched random source. Same 30% global/top-three
incoming/outgoing coverage and movement-ID ties; actual retained cardinalities reported.
For each source run static and recovery (eight arms), plus one unrestricted cold-full
control with the historical native eight-round-cap policy (nine arms total). Full cold8
is the grounded solver-native alternative: it previously found 59/60 valid endpoints,
compared with 44/60 for full4. Do not use full4 alone as the decisive unrestricted control.
No claim that cold8 exhausts solver-native strategies. The existing bill decomposition shows 91.916% of summed graph/nonlearned saving
at 80 trips comes from vehicle cost (graph median 4 versus 27.5 vehicles); both methods
use median 3 vehicles at 40 trips. This prioritizes a constructive minimum-fleet,
charging-feasible warm-start control before substantive launch. Its construction and
charging validation must pay the common clock; its source/selection/ties must be frozen
without new-cohort outcomes. It is not implemented or validated yet, so nine-arm scope
is provisional: either add it with a prospective manifest/budget recomputation under
the same 8 CPUh ceiling, or explicitly retain this baseline limitation before launch.
Report vehicle counts and exact fleet/electricity bill components per pair; compare
full restoration to static graphs to distinguish search assistance from restriction
of the feasible set. A price-blind minimum-fleet route proposal plus native charging
completion is a concrete candidate, not an established feasible incumbent until replay.

Static and recovery use identical ranking, acquisition schedule, objective/completion
and admission rules until the fixed halfway boundary. Static continues on the restricted
model; recovery lifts the prefix witness and restores all original alternatives using
binary-only partial starts on every tangent rebuild. Continue native optimization of
static's model at the boundary where supported; do not impose a gratuitous rebuild to
hide recovery construction cost. Document any common tangent rebuild separately.
Static can use its entire remaining search allowance; retention alone guarantees only
nonworsening versus the same prefix, not superiority versus static's terminal solution.
If prefix is absent, recovery attempts cold full search with actual remaining time;
no-time cases return an admitted fallback or explicit no-plan. Include every such cell.

One total clock begins before interpreter/model/scorer loading and ends after final
replay, exact bill and materialization. T=60 s primary, T=120 s robustness. Prefix cutoff
is t0+T/2, fixed before outcomes. Finalization reserve=max(3,.10T), cumulative completion
reserve=max(2,.10T); prefix extraction/completion/lift reserve=max(3,.05T) precedes cutoff.
Recovery begins after lift at the boundary with remaining time; full search only while
reserves permit. No split search, adaptive timetable exclusion, free preprocessing or
unrecorded repair. Native integer-search cumulative allowance is explicitly recorded;
at most four rounds per restricted stage and eight total recovery rounds (four prefix,
four full); cold8 retains its eight-round cap. Stage phase limits divide only actual
available search time, never an assumed fresh T/2. Freeze exact allocation implementation.

## Small cohort and bounded cost

Propose twelve new synthetic base timetables: six at 40 and six at 80 trips, each base
at exactly one size. Base IDs must be disjoint from historical training/inner/outer,
all 17 October screen/qualification bases and new engineering qualification. Verify
namespaces and identity hashes before inference; new IDs still share generator physics
and are not evidence of public-network generalization. Seeds 17,41,73 repeat within
base and across every arm. Primary: 12×3×9=324 decisions at 60 s, 5.4 nominal CPUh.
A later separately authorized 120 s robustness stage may use four of these bases
(two per size) selected by salted identity hash before any primary outcomes: 4×3×9=108
decisions, 3.6 nominal CPUh. Freeze these identities now, without authorizing execution. This subset estimates paired
budget sensitivity, not a second independent confirmation population. No outcome-chosen
size transition study or extra favorable-case extension.

The first authorized proposal is **324 decisions, 5.4 nominal CPUh**, with a hard
**8 CPUh ceiling** including freeze, scoring, all attempts/failures, monitoring, analysis
and closeout. Qualification remains separate at <=0.25 CPUh cumulative across phases
and revisions. One local worker, one native/library thread, <=5 GiB process-tree RSS,
same fail-closed monitoring as qualification. Stop dispatch at 7.5 charged CPUh, reserve
0.5 for shutdown/audit and require the whole next allocation before launch. Saved
capacity buys no extra cases, seeds, splits or time. The 120 s stage requires a new
separate budget and explicit launch decision after reporting the complete 60 s stage;
its 3.6 nominal CPUh is excluded from the first-stage authorization.

Random scores are keyed by base and solver seed, identical between static/recovery and
between 60/120 s runs. Interleave by (base,seed,budget), hash-sort blocks and rotate nine-arm
order, alternating direction. Robustness identities and design must be frozen before primary results;
if later authorized, launch order cannot depend on observed effects. Record temperature/load context if
available; resource interruption is missingness, never a replacement opportunity.

## Estimands and decision reporting

Primary comparison: graph recovery versus graph static at 60 s. Prespecified attribution
comparisons: recovery-minus-static within each other source, graph versus nonlearned
and CatBoost within each mode, and each mode versus cold8. Keep these labels fixed;
recovery gains alone do not establish learned value. For positive both-valid paired bills,
gain=(B_static-B_recovery)/B_static. Median the three seed gains within base; report
median of base medians separately by size. Equal weights per base and size; pooled
estimate secondary. Report direct paired ranking comparisons rather than differences
of unrelated percentage summaries. Native seeds are repeated trials, not independent
population units. Give group bootstrap intervals stratified by size (10,000 draws,
fixed analysis seed 20261023); n=6/size is exploratory with wide uncertainty.

Validity is a co-primary practical endpoint: count attempted, valid, no-plan, internal
replay rejection, infrastructure failure, censored and undispatched separately, with
both-valid denominators beside every cost comparison. Exactly-one-valid pairs favor
that arm in failure-aware wins; both-invalid ties; never invent a finite missing-plan
bill. Report base medians only from available pairs and also a complete-three-pair view;
missing groups never silently vanish from denominators or count as evidence of benefit.
Show all paired regressions, worst regression, per-size valid-plan rates, and trajectories
at prefix/terminal time. Prefix witnesses across matched treatments should agree under
identical prefix execution; investigate divergence rather than force equality.

Report paired 120-versus-60 sensitivity only on its four frozen bases. No retrospective
split selection or p-value promotion. A complete study with no engineering violations
can support a further proposal if recovery improves median group bills in both sizes,
loses no valid endpoints per size versus its matched static arm, and has no >5% both-valid
regression. These are exploratory practical criteria, not a journal acceptance threshold
or automatic launch gate. If either size differs, report the interaction and uncertainty;
never mask it with pooling. Graph complexity needs direct evidence against CatBoost.

## Invariants, stop conditions and evidence

Only full unrestricted admitted native lower bounds may accompany full physical uppers;
restricted/completion bounds retain their own scope. Native start acceptance, physical
replay and certification are distinct. Any admitted invalid plan, same-ID physics mismatch,
false bound/certificate, deadline reset, incomplete spend receipt, resource failure or
lost owned process stops dispatch and triggers audit. Favorable cost results never stop
or expand the study. Ordinary correctly recorded no-incumbent outcomes remain endpoints;
a systematic unexplained infrastructure failure blocks further dispatch. All versions,
failed attempts and censored outputs survive. Any engineering repair requires a frozen
amendment; never rerun failed cells invisibly or pool versions without disclosure.

Archive case/model/source hashes; random order/retained graph hashes; raw native events;
submitted start inventory and native status; prefix and lifted full replay artifacts;
all admitted/rejected candidates; exact bills; scoped bounds; stage CPU/wall; shared
anchor/deadlines; materialization markers; supervisor receipts/resource samples and
charged ledgers. Independently replay all accepted endpoints on original full cases.
The principal risks are recovery overhead, unreliable start acceptance, short-horizon
solver variability, tiny per-size population, and shared synthetic physics/tariff. A
positive result motivates external/physical-shift validation and stronger charging-aware
alternatives; it does not resolve those risks.
