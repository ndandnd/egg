# Physical context feature v9 review

**Verdict: the input-only feature package passes review. Training needs a separate prospective experiment and resource budget.** The API accepts only a validated `NativeCase` and prospective `Market`; it appends 21 declared context columns to the exact historical 17-column extractor. The features are derived from declared movements, service trips, resource windows, battery/reserve/efficiency, and market curvature. No source plan, label, observed charge, SOC, solver result, or fitted transform enters the extractor.

The charging-window quantities are appropriately qualified as local context. The isolated stored-energy estimate assumes one bus has all offered capacity and does not account for shared occupancy or SOC headroom; candidate-window overlap counts even mutually exclusive alternatives. Neither quantity establishes route or fleet feasibility. Trip bursts also have unknown entering SOC. The protocol preserves those limits and keeps outer labels sealed while transformations and model selection use fit/inner groups.

The proposed zero-padded 17-feature comparator is a new matched 38-input model, not a replay of historical v6. Padding keeps tensor shapes and parameter counts matched, but leaves 2,688 baseline input weights inactive and does not match active information capacity. The protocol states this distinction and requires a new fit/time budget and fit-fold range inventory before training.

One data-scope limit matters for interpreting any later ablation: the declared generator fixes efficiency at 0.9, per-bus/grid power at 90 kW, connector count at one, and market curvature `b` at 1/900. The present bank therefore cannot teach responses to changes in those inputs. Battery/reserve profiles and movement/resource-window structure do vary. A separate prospective generator would be needed to study changed charger ratings, efficiency, or curvature.

Focused validation: `PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_context_features_v9.py` passed all 14 fixtures. This review covers feature semantics and the proposed comparison only; it makes no result or training claim.
