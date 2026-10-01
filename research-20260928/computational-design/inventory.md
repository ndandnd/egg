# Computational research inventory

**LOCAL PLANNING NOTE — 2026-09-27.** This is a read-only inventory for experiment design. It contains no private GIRO data or outcomes. Counts other than the Hildenbrand case are metadata-only size indicators and are not EGG-qualified input records.

## Public fixed-service candidates

The pinned public source is Sistig et al., *Dataset for Evaluating Costs and Operations of Public Bus Fleet Electrification*, Figshare v1, DOI [10.6084/m9.figshare.26088190.v1](https://doi.org/10.6084/m9.figshare.26088190.v1), publisher-stated CC BY 4.0. The locally retained archive is `/Users/nadan/Documents/ChatGPT/egg/research-20260927/agent-notes/public-data/sistig-26088190-v1.zip` (267,312,231 bytes; publisher MD5 `89b04ee5e8cd54997df51211d2c264d2`; intake SHA-256 `3c6c2ed7c45fc441f4cb6108d830769b60c0de5e44e1a3a6fc72bed4f5f07317`). Attribution and adaptation notes are in [`ATTRIBUTION.md`](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/data/public/sistig_26088190_v1/ATTRIBUTION.md).

The prior archive audit found 20 selected-operator timetable folders with fixed services and finite directed stop-to-stop movement matrices. This inventory reports their workbook-declared service-row extents only; for the 19 larger bases it does not repeat cell-level parsing, data semantics, or native admission. The prior audit's smallest-five list is in `/Users/nadan/Documents/ChatGPT/egg/research-20260927/agent-notes/public-data/sistig-26088190-audit-report.md`.

| Public base timetable | Metadata-declared service rows | Current EGG status |
|---|---:|---|
| Hildenbrand | 37 | Qualified public native case; two separate one-depot variants (depot 15 and depot 16) are development cases from one source timetable. |
| Stadtwerke Eberbach | 105 | Candidate scale expansion; not yet EGG-admitted. |
| Dreieich | 131 | Candidate scale expansion; not yet EGG-admitted. |
| Bad Nauheim | 137 | Candidate scale expansion; not yet EGG-admitted. |
| Pfaffenhofen | 323 | Source candidate; not yet EGG-admitted. |
| Nahverkehrsgesellschaft Jerichower Land | 616 | Source candidate; not yet EGG-admitted. |
| Stadtverkehr Euskirchen | 664 | Source candidate; not yet EGG-admitted. |
| Weimar | 839 | Source candidate; not yet EGG-admitted. |
| Stadtbus Konstanz | 936 | Source candidate; not yet EGG-admitted. |
| Stadtwerke Passau | 984 | Source candidate; not yet EGG-admitted. |
| OVB Offenbach | 1,034 | Source candidate; not yet EGG-admitted. |
| Landkreis Gotha | 1,096 | Source candidate; not yet EGG-admitted. |
| Kombus | 2,030 | Source candidate; not yet EGG-admitted. |
| DVG Duisburg | 2,141 | Source candidate; not yet EGG-admitted. |
| Vetter Verkehrsbetriebe | 2,422 | Source candidate; not yet EGG-admitted. |
| Stadtwerke Bonn | 2,895 | Source candidate; not yet EGG-admitted. |
| wupsi | 3,315 | Source candidate; not yet EGG-admitted. |
| NIAG | 3,909 | Source candidate; not yet EGG-admitted. |
| ASEAG | 5,147 | Source candidate; not yet EGG-admitted. |
| Kölner Verkehrsbetriebe | 6,281 | Source candidate; not yet EGG-admitted. |

The current Hildenbrand native input contains 37 mandatory service records, a complete directed 5×5 stop movement matrix, and two one-depot variants. It is a fixed-service timetable, not a customer-routing benchmark. The variants are restricted EGG scenarios, not the paper's original two-depot problem. Service and deadhead energy are modeled from an explicitly selected vehicle concept, not source-observed energy. The source calendar date and measured energy/charging are absent. Do not treat publisher-generated schedules or charge plans as EGG outcomes. Preserve the source operating-day offsets and directed movement data. The two depot variants are one timetable group and both remain development-only.

## First screening and later evaluation split

Use the already selected diagnostic set: synthetic `cyclic2` and `multivisit3`, plus the two Hildenbrand 37-service one-depot variants (depot 15 and depot 16). Treat all four as development diagnostics; they check small cyclic/multiple-visit behavior and one real fixed-service base under two explicitly different depot restrictions. They are not four independent timetable samples and should not support held-out generalization claims.

For scale follow-up, put the 105-, 131-, and 137-service public bases on the roadmap as the first larger public inputs, after individual adapter and physics qualification. Keep all variants derived from one operator/timetable together. Before running any larger grouped evaluation, freeze a split keyed by a canonical base-timetable fingerprint, not by scenario or vehicle-type folder. Stratify the base groups by service-count bands, assign groups with a recorded deterministic seed/hash, and only then create train/dev/test membership. Keep the Hildenbrand family in development because it is already selected and studied; if the three scale candidates are used for tuning, they belong in development too. The remaining groups can supply train and held-out test groups after qualification. If two source records prove to be the same base timetable, merge them into a single group before splitting. Never distribute depot variants, scenarios, or generated parameter variants from the same base across folds.

## Existing iterative synthetic workload

The reusable generator is [`synthetic_instance`](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/src/egglab/instance.py:73). It creates a seeded two-terminal-plus-depot instance, with directed data represented symmetrically, generated 40–60 minute services, 14–22 kWh service-energy draws, a 60 kWh battery, 10% minimum/end SOC, and 150 kW charging by default. Its docstring explains the intended charging pressure: a vehicle's service energy can exceed its usable battery, so midday charging can respond to prices. It is a synthetic solver workload, not a representative bus timetable or directed-network surrogate.

Existing iterative entry points include [`run_phase1.py`](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/src/experiments/run_phase1.py) (seed × trip count × price shape × curvature × damping factor, with a damped taker fixed-point loop) and [`run_b2a2_pilot.py`](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/src/experiments/run_b2a2_pilot.py) (seeds 0/11/15, 8/12 services, curvature 0.01/0.05, certified column generation with a 240-pricing-call budget). These can support iterative algorithm-development examples, but keep a separate label from timetable-based evidence. A later scalable synthetic family should vary workload size and seed under a frozen generator version, and retain every attempted cell and failure.

**Model boundary:** this older synthetic generator and its phase-1/B2-A2 experiments require at least 10% battery SOC at the end; the current native complete-replenishment screen uses a different terminal inventory rule. Do not pool their results or compare their costs as one benchmark without an explicit adapter, reconciled terminal policy, and consistent energy accounting. The historical 240-call B2-A2 budget is not a prerequisite or qualification gate for the new pathflow screen.

## Compute and tool availability

One fresh read-only Unicorn snapshot showed no running user jobs; displayed pending user entries were held. The default CPU partition reported 225 nodes and 5,995 idle CPUs out of 14,498 total at that instant. This is a transient snapshot, not a reservation or capacity guarantee. The inventory request permits planning one serial job of at most 1 CPU, 8 GB, and 2 hours; no job was submitted, changed, or signaled. The explicitly excluded node `scaglione-compute-01` was excluded from consideration.

The check sourced `/etc/profile.d/slurm.sh` over a fresh SSH session with multiplexing disabled and read `squeue`, `sinfo`, and a node summary filtered to exclude `scaglione-compute-01`. It did not enumerate or record job IDs. On the local Mac, `tectonic` was found at `/opt/homebrew/bin/tectonic`; `latexmk`, `pdflatex`, and `lualatex` were not found on PATH. On Unicorn, none of those four commands was available on PATH. No packages were installed.

## Qualification boundaries and next work

The next priority is the small diagnostic set, then the 105/131/137 scale candidates as roadmap inputs. Do not count any larger public base as an EGG case until its timetable semantics, time/day-offset representation, directed movement fields, units, energy derivation, depot/terminal policy, and exact source/member fingerprints are checked. The existing 37-service Hildenbrand case is the only current public base with a prepared native case and a complete qualification trail. Synthetic results answer solver-behavior questions, not empirical timetable claims.

Checks for this inventory: no `AGENTS.md` was found under `/Users/nadan/Documents/ChatGPT/egg`; public workbook cell content and publisher schedules were not re-read for this task; no private GIRO data was accessed; no experiment, optimization, queue mutation, submission, Google Doc write, or Git operation was performed.
