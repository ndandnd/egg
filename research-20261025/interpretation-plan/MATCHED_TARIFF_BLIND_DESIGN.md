# Conditional matched tariff-aware versus tariff-blind study

25 October 2026. Prospective interpretation/design note only, conditional on a
qualified new eight-group study and the readiness gate below. This is neither a
manuscript claim nor an approved training/evaluation run. No current assets,
rows, labels, outcomes or sealed indexes were accessed; no code, model or frozen
protocol was changed. No import, test, hash, computation, solver call, cluster
access or literature survey was performed for this note.

## Question and smallest informative intervention

The current frozen GNN receives linear tariff a, but no curvature b. GNN_day uses
the **same weights** with day-a features while the target optimizer still sees
late a/b. That tests sensitivity/adaptation of a fixed model; it is not a matched
trained-blind comparator.

The question is **the marginal value of conditioning the proposal on current-case
a**, beyond the same physical information and price-aware downstream optimizer.
Train one GNN architecture twice: aware with current-a features; blind means
**current-case tariff-blind proposal inputs**, with those price-derived paths
removed. Both models learn from the same historically price-influenced labels,
and both downstream optimizers see current prices. This does not compare all
policy price knowledge. Keep b fixed; learning b information needs a separate
feature/data design. Both pipelines receive exactly the same examples and labels.

## Data and labels are an admission gate

The available model metadata declare128 TRAIN groups:80 fit,16 inner and32
historical outer. Preserve that partition for development unless a later protocol
explicitly changes it. All timetables, sizes, tariffs, resource variants, teacher
seeds, source plans and derived rows of a base group remain together. Resolve
canonical group/variant aliases before splitting; a different filename or numeric
namespace is not proof of independence. Train-only fit statistics apply to every
derived variant of the held-out groups.

**Our chosen strong identification design** uses the same physical TRAIN
timetable under at least two prospectively fixed tariffs, assigned independently
of group identity. This within-timetable pairing limits price–regime confounding;
it is not a universal mathematical necessity. One price per group could in
principle support other well-supported randomized or observational designs.
Current TRAIN tariff variation is **unknown until readiness inspection**. Keep
physics unchanged and align the target with fixed-fleet replanning evaluation.
Teacher effort, candidate availability, failure recording and source-plan policy
must be identical across tariffs and available to both students.

Labels are movements from observed replay-valid feasible incumbents, not optimal
routes. Freeze the teacher/selection policy and disclose that limitation. A
qualified TRAIN-only fixed witness catalog can provide cheapest-observed-plan
labels under each tariff, but only if this restricted-label meaning is explicit;
it does not establish globally optimal supervision or charging reoptimization.
Keep ties deterministic and retain teacher failures rather than replacing groups.

If every training example uses one universal constant tariff, those labels
alone provide no support for current-tariff sensitivity. Adding a column,
permuting inference prices or masking features cannot supply that missing support.
If tariffs vary but labels/plans barely change, that is a readiness finding about
available signal; do not search variants until a favorable contrast appears.
Identical binary edge-incumbency labels across tariffs do not supply a
conditional binary target. Other cost-sensitive targets could use different
information, but require a separately specified label design.

## Matched fitting and selection

Use one fixed architecture, loss, example weighting, batch policy and stopping
rule. Do not add model families. Use the same small frozen hyperparameter menu,
number of trials, training-seed pairs and CPU allowances for aware/blind. Two
predeclared initialization seeds would expose some fitting variability; neither
arm may select its best seed after evaluation. Any selected configuration uses
the same16 inner groups and the same predeclared metric/aggregation rule, with
equal search opportunities and compute. Freeze selections before confirmation.
Report unsuccessful/censored fits and actual effort, not only surviving models.

Identical architecture with constant-zero tariff slots is a practical capacity
control; removing those slots entirely is also possible but must be frozen as a
different input schema. In either case, blind normalization is fit on blind FIT
inputs only. Mask price features **before** preprocessing, graph construction or
any learned transformation. Do not pass current-case prices through reused
normalization or embeddings. A common prospectively chosen neutral initialization
is our matching control, not a claim that the trained blind model lacks historical
price knowledge: its shared supervision remains price-influenced.

The leakage audit must cover more than the explicit tariff vector:

- Remove window-price means/minima, global price means/spreads, tariff-weighted
  costs, price-derived ranks, bins, embeddings and all indirect a/b encodings.
- Make blind graph edges, node/message features, sampling/pruning, feature
  normalization and attention biases independent of tariff. A common physical
  graph/backbone may remain. Match the aware path except for the declared inputs.
- Exclude tariff names/IDs, source filenames, variant ordinals, teacher-objective
  metadata, selected-plan identities and cached price-aware scores from inputs.
  Physical times/windows may remain, but varying tariffs must prevent time of
  day or case identity from acting as a deterministic tariff lookup.
- Keep label values separate from features. Price-dependent teacher labels are
  intentional shared supervision, not permission to expose teacher cost or
  outcome-derived preprocessing. Record the complete blind input dependency list.

## Evaluation after model freeze

Use the **same price-aware downstream optimizer** and current target a/b in both
arms. Hold original physics, prior plan, fleet count, base backbone B, original
quota K, prior-protected warm backbone, boundary modes, native seeds, solver
schedule, start/hint policy and fallback retention fixed. Compute each fresh
ranking and fill only its remaining K slots. A protected set exceeding K is a
recorded design failure, never an arm-specific quota increase.
Acquire the prior before assigning the target tariff; no shared fallback, mask
or hint may be retrospectively selected using target costs.

Use identical inclusive online clocks paying cold model objects, feature work,
inference, selection, model construction, all native calls, extraction, replay
and publication. Report prior acquisition separately for warm replanning; do not
call it cold speedup. Keep every assigned endpoint, including missing prior,
failure, late output and operational fallback, with method success distinct from
availability. Apply original physical replay and objective guards unchanged.

Retain competent frozen classical controls, unchanged-prior and qualified
fixed-route charging controls as context. A raw QP optimum without a replayable
witness is not a physical ceiling. Use integrated system cost, fleet/deadhead/
electricity decomposition, energy quantity and charging timing. Report absolute
paired differences and prior-electricity-normalized differences with zero/missing
denominators explicit. Fixed fleet alone does not fix route energy.

The primary comparison is blind minus aware downstream cost, aggregated within
each independent base group across paired tariffs, sizes and solver/training
seeds. Those repetitions are not independent timetable observations. Freeze the
minimum useful effect, group count, uncertainty/readout rule and stop conditions
before confirmation outcomes. Report both directions, ties and failures. An
observed blind tie or win means **no demonstrated benefit under the frozen rule**.
It does not establish equivalence, global information irrelevance or a causal
rejection of need without prespecified precision/equivalence analysis. Do not
respond with evaluation-driven feature/menu expansion.

The old32 outer groups and the current eight-group development study cannot be
rebranded as fresh confirmation. They can diagnose readiness and inform the next
frozen design. A newly specified confirmation cohort must be frozen **later**,
after input schemas, model selection and analysis are locked. This note opens
none of the existing sealed DEV/TEST/A6/B3/confirmation/GIRO sources.

## Bounded readiness and conditional resource direction

First require a whitelisted metadata manifest linking group/variant IDs, FIT/
inner/outer membership, tariff conditions, label-source policy and source-plan
provenance. Record source/model/split/preprocessing and label-manifest identities
in one future frozen verification batch; no repeated historical hash audits.
If mapping or the price-varying labels required by this chosen paired design are
absent, stop this protocol's information-value claim rather than generalizing
that limitation to every possible design.

An initial **budget direction**, not resource approval or launch authority, is:
up to10 CPU minutes for metadata readiness; if warranted, a separately frozen
TRAIN-only label/readiness pilot capped at1 CPU hour on a small predetermined
fit/inner subset; then at most two configurations ×two paired initialization
seeds ×two input policies, initially capped at4 CPU hours/6 wall hours with equal
per-policy effort. Use one computational thread and observed5GiB initially.
Record actual costs and failed work; do not extend one arm or replace cases.

Full price-varying label production, if needed, is **not** funded by that pilot
direction. Its source/data coverage and practical cost must be estimated and
frozen separately. Confirmation size and total online evaluation cost likewise
need a later concrete manifest. Proceed only if a complete matched comparison
is feasible under the chosen allowance; otherwise report the data/budget blocker.
No training command, new asset access, numerical experiment or model promotion
is authorized by this document.
