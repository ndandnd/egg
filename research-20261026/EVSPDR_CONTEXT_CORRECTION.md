# Correction: EVSP-DR already supplies the operational modeling foundation

26 October 2026, following the human's correction. The earlier conclusion that
fleet/service commitments, charging restrictions or an operating-model anchor
were unavailable was too broad. It arose from restricting inspection to recent
EGG pilot notes and then treating that local absence as a project-wide absence.
The resulting blanket stop and deletion of the hourly research follow-up were
not justified by the project's actual context. The human's correction supersedes
that stop. Historical numerical results and failed practical ML gates remain.

## What already exists

EGG's own [README](../README.md) identifies EVSP-DR as the adjacent exact
price-taking scheduling oracle using Swedish bus data. The historical integration
handoff explicitly calls for wrapping the adjacent oracle and retaining its
fixed-sequence re-realization and full-pricing hierarchy. The current sibling
root is `/Users/nadan/Documents/projects/demandresponse`; its registered capacity
implementation is `.codex-work/capacity-packed-20261001`, not the old top-level
`src`. This inspection read source and compact model/experiment notes only; no
raw GIRO records, sealed EGG banks, model weights, replay or numerical job.

| Existing component | Source evidence | Interpretation |
|---|---|---|
| Mandatory service | `src/run_capacity_terminal_cg.py:67–70` in the registered capacity checkout | Trip covering or optional exactly-once partition rows; the selected mode matters. |
| Fleet scope | Same rows and integer stages at `:334–360` | Fleet cap and fleet-first integer optimization, then charging within attained cap; not automatically the same as EGG's exact-N equality. |
| Fixed duties | `src/run_fixed_duty_terminal.py:1–9,39–52,115–118` | Original GIRO trip sequences are fixed, checked to partition service, and one charging realization is selected per duty. Stations/times may remain free. |
| Battery and temporal feasibility | `src/event_pricer_network.py:151,480–527` | SOC/reserve, consumption, travel/arrival/departure windows and station-rate charging transitions are modeled. |
| Charger power | `src/station_power.py:1–46`; sibling `AGENTS.md:9–13` | Station overrides and aliases are explicit; Partille PARX depot uses 60 kW in GIRO-matched comparisons. |
| Shared plugs | `src/run_capacity_terminal_cg.py:118–123` | Station-minute occupancy is constrained by plug count. This is not automatically a shared-transformer kW cap. |
| Fixed-visit charging | `outputs/capacity_rebuild_20261001/step2_plug_retiming/plug_retime.py:79–125` in the sibling root | Battery/reserve, power, dwell windows, contiguous sessions, terminal requirements and plug constraints are modeled. |

Partille/GIRO is already a documented benchmark/model anchor. It need not be a
new named legal customer with a dispatch contract before methodological research
can proceed. Modeled commitments and empirically observed operating commitments
are different evidence levels, but the latter are not a universal prerequisite
for a well-specified optimization study.

Calibration cautions still matter. The sibling register says some plug counts
are tested configurations consistent with recorded occupancy, not independently
verified hardware inventories. Unlimited PARX plugs are an explicit assumption.
Some historical campaigns use uniform 240/350 kW, zero reserve, covering masters
or different terminal conditions. Do not silently call every prior result
GIRO-matched or combine incompatible physics. These are specific model-bridge
questions, not evidence that the charging model does not exist.

## A second scope correction: the economic models exist too

EGG `src/egglab/market.py:1–16,41–55` already distinguishes posted prices,
strategic fleet payment and incremental system cost with background load U:

- strategic payment: `sum((a+b*(U+L))*L)`;
- system-cost increment: `sum((a+b*U)*L + .5*b*L**2)`.

`src/egglab/regimes.py:1–9,116–133` includes the strategic solve path. The recent
native-pilot objective `ops+a'L+.5L'BL` is system cost; that valid local
interpretation must not be generalized to say EGG lacks a price-maker model or
has confused these objectives everywhere. Existence of a formal model still does
not establish empirical price impact, a deployed clearing institution or novelty.

## Correct scientific disposition and next action

Withdraw the blanket claim that EGG cannot progress without finding an entirely
new operator/charging-restriction source, and withdraw the forced redirection of
the whole research program to disruptions. The original price-formation and
useful-prediction questions remain open. Both learned families' frozen negative
continuation results remain valid for their actual tested cohorts, objectives
and pipelines; source reuse does not turn those into positive results.

Next make one explicit EVSP-DR-to-EGG model correspondence: trip/time/day and
group identities; exactly-once versus covering service; fixed-duty versus fleet
cap versus exact N; SOC/reserve/terminal-energy rules; station-specific power,
plugs and any aggregate grid cap; permitted charging windows and transfers;
and exogenous versus strategic versus planner objective units. Determine which
differences are deliberate abstractions and which make the recent pilots
unrepresentative of the intended question. Use the existing adjacent interfaces
without copying or modifying the sibling solver. This is a concrete integration
question, not another literature survey or an assumption that a larger model
will produce an ML gain.

Then define a bounded, model-consistent experiment against competent classical
and fixed-duty charging controls, with complete paid budgets and denominators.
No automatic retry of old experiments, training sweep or opening of sealed
GIRO/DEV/TEST/A6/B3/confirmation banks follows from this source inspection.
Prospective exact input/source/command/resource design still applies. Local
work only; no cluster monitoring/jobs, and no changes to the sibling project.

## Accountability

### Clarification after the human's neural-prediction question

The failed warm replication is a negative continuation decision for the specified
frozen learned policies, not a permanent prohibition on neural route prediction.
For the GNN, the mean advantage over CoverCA1 was positive .0386688% of common
prior electricity E0 but below the predeclared >1% rule. Seven of eight group
medians were positive. Its larger gains over fixed-route QP and bounded full
search do not isolate learned information because conventional restriction also
helped. No zero-effect/equivalence test or global architecture conclusion follows.

The evaluated network ranked movement candidates inside a hybrid optimization
pipeline. It was not a test of every neural route constructor, route/column
proposal target, operational model or training procedure. The eight timetable
groups and repeated size/seed cells are development evidence. Earlier positive
four-group evidence cannot rescue the failed replication, but neither result
settles all future settings. Models receive a/notb, binary labels represent one
observed teacher plan, and historical GNN pool lineage is incomplete.

The correct next ML question may be whether a specifically diagnosed, costly
EVSP-DR decision/search step benefits from learned proposals at equal complete
budgets. First establish model/target correspondence and a reason classical
controls leave useful residual work, then record one bounded experiment with
grouped evaluation and all failures. Keep original gates immutable and avoid
outcome-driven model/cohort selection. This permits justified revisiting; it
does not authorize an immediate training sweep or assume learning will succeed.

Two bounded GPT-6.1 Sol source/context checks corroborated the correction. No
imports, tests, hashes, inference, fitting, replay, native jobs or source changes
were needed. The numerical ledger is unchanged: displayed19923.95 CPU seconds,
20520.60 elapsed-sum, retained tracking19924.31 CPU; separate legacy conditional
guard2546.091499549272 and historical actual review CPU UNKNOWN. These remain
process sums, not exact whole-session CPU or continuous elapsed.

The erroneous stop is preserved with supersession notes, not erased. Hourly
research follow-up was restored as ACTIVE automation
`advance-egg-local-prediction-research`, around the model correspondence under
the standing human instruction to keep useful research moving. Unrelated paused
schedules and all historical failures/outcomes remain untouched.
