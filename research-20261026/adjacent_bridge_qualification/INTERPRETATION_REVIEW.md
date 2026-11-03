# Closed comparison: interpretation review

**The by-reference capacity-aware seam worked on one synthetic six-trip fixture at one fixed posted quote.** Both planned arms were attempted, returned timely physical endpoints, and reported no failures: **2/2 arms, one independent fixture, one quote**. Each selected two vehicles with exact service coverage, no reported grid or continuous shared-plug violations, and aggregate terminal energy above the target of 80 kWh. This is operational qualification of this connection and fixture, not general EVSP-DR/EGG physical equivalence or a learned-method result.

| Returned quantity | Fixed duty | Full |
|---|---:|---:|
| Event-grid charging cost | 39 | 39 |
| Continuously realized charging cost | 29.5 | 29 |
| Event-grid delivered energy (kWh) | 280 | 280 |
| Continuously realized delivered energy (kWh) | 212 | 208 |
| Event-grid / continuous terminal energy (kWh) | 82 / 90 | 82 / 90 |
| Cumulative pricing time (seconds) | 0.04764920845627785 | 0.08661850355565548 |

The fixed duties remained `(0,2,4)` and `(1,3,5)`; the full arm returned `(0,3,5)` and `(1,2,4)`. Thus the full search actually used duty-reassignment freedom. Nevertheless, its returned event-grid objective tied the fixed-duty result. The continuously realized full endpoint cost and delivered energy were lower. These are comparisons of the two returned witnesses, not proof that duty reassignment is necessary for that continuous improvement: the fixed arm was optimized under the grid objective, not a globally optimized continuous objective, and tied grid columns can realize differently. Different route/movement choices, selected columns and realization details are not isolated causal treatments here.

The reported 280 kWh grid quantity versus 212/208 kWh realized quantities, and grid terminal 82 versus continuous 90, show that conservative energy discretization/realization is materially visible in this fixture. Grid quantities cannot be substituted for physical energy use or continuous cost. Equal fleet size and aggregate final energy make the delivered-energy contrast informative, but the compact readout does not separately export all traction/movement/rounding balance terms; it does not identify a pure timing effect or a specific cause of the energy difference. The identical grid objective also does not establish equal continuous route value.

Both source summaries report certified pricing for the **conservative event-graph capacity LP**, with weighted LP value **200038.6**. Both finite-generated-pool charging MIPs report cost and bound **39**, conditional on the attained two-vehicle fleet. These scopes are distinct: the finite-pool MIP bound is not a full integer-route certificate, and neither grid lower bound is a lower bound for the continuously realized problem. In particular, the continuous full costs **200029.5/200029** must not be compared against **200038.6** as lower/upper bounds for one optimization problem. `continuous_cost_pricing_certified` is false for both arms. No ideal-physical optimum, equivalence, or infeasibility conclusion follows.

**Neural direction remains conditional.** This run exposes a legitimate capacity-aware column/pricing interface and shows that full routing can change duties; it does not expose an expensive pricing bottleneck—reported cumulative pricing is tiny in both arms. A neural route/column proposal is therefore a possible future interface, not an earned acceleration or value claim. Its next gate would be a separately frozen set of meaningful routing/quote contexts where a competent classical pricing/column control has measurable paid-clock difficulty; original physical admission, correct reduced-cost/dual context, held-out groups and exact/classical fallback must remain. No result here authorizes training, selection of favorable examples, or revival of the existing models.

This experiment held the quote fixed. It tested neither iterative price/route feedback nor convergence/cycling. The separate `ITERATION_AND_NEURAL_DIRECTION.md` counterexample and conditional convergence discussion remain mathematical statements, not observations from these two calls. This review used only the new compact readout; no new computations, exports, replay, solves, retries or tuning were performed.
