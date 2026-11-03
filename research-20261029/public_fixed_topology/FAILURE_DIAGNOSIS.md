# Public exact-recovery failure

The public charge-only native QP returned status 2 and objective 441.53291205116824. The exact helper rejected its recovered certificate at `ALL_COORDINATE_BOX_CERTIFICATE`, reason `Recovered multiplier has wrong sign`, after 12,728 monitored exact-operation checkpoints and about 0.0123 helper seconds. There is no indication in the compact report of a resource exhaustion or source/administrative failure.

This identifies the failing certificate condition, not a proof that valid signed multipliers do not exist. The frozen single-face/seed recovery can choose an inadmissible multiplier from a degenerate family, or otherwise fail to recover an exact admissible optimum from a floating proposal. Compact evidence does not distinguish these explanations or identify a particular row. No raw packet was opened to pursue them.

Acceptance correctly remained fail-closed: exact objective/lower are null, no new physical upper is promoted, and no own-price vector or response solves were produced. Native OPTIMAL is insufficient to override the exact sign condition. Failure does not establish topology infeasibility, failure of the mathematical fixed-topology formulation, or global unsupportedness.

No automatic alternate face, dual feasibility solve, terminal adjustment or retry occurred. Any further recovery method requires its own explicit source design and prospective qualification; this closed result supplies no authority for such computation.
